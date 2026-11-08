"""Bounded primary-fit energy transport experiments in an isolated namespace.

The previous campaigns and champion are immutable inputs. No existing model is
retrained: each arm fits one small transport coefficient vector on PRIMARY.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

os.environ.update(OMP_NUM_THREADS="4", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1")
import numpy as np
import pandas as pd
import pyarrow as pa
from threadpoolctl import threadpool_limits
import transport

pa.set_cpu_count(4)
pa.set_io_thread_count(1)
ROOT = Path(__file__).resolve().parents[2]
CODE = Path(__file__).resolve().parent
OUT = ROOT / "analysis_outputs/research_novel_20261108"
CANDIDATE = ROOT / "submission/research_novel_candidate_20261108"
OLD = ROOT / "analysis_outputs/research_23kst_20261108"
FINAL = ROOT / "analysis_outputs/renew_20261105/final"
BEST = ROOT / "submission/renew_candidate_20261105/submission_files.zip"
BEST_SHA = "ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434"
LATE_LABELS = FINAL / "predictions/latest_cutoff_march_may/scored_predictions.parquet"
DEADLINE = "2026-11-08T14:00:00Z"
SEARCH_STOP = "2026-11-08T12:00:00Z"
KEYS = ["ts", "grp"]
FEATURES = ["wa_cloud", "wb_cloud", "cosz"]
GATES = {"primary_max": 1.0, "recent_max": .9999, "recent_quarter_max": 1.005, "recent_group_max": 1.001}
RECENT_QUARTERS = {"jun_aug": ("2024-06-01", "2024-09-01"), "sep_nov": ("2024-09-01", "2024-12-01"), "dec_feb": ("2024-12-01", "2025-03-01")}


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def plain(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return [plain(x) for x in value.tolist()]
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    return value


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(plain(value), ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    os.replace(temporary, path)


def parquet(path, frame):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    frame.to_parquet(temporary, index=False)
    os.replace(temporary, path)


def relative(path):
    return str(Path(path).relative_to(ROOT))


def kst(value):
    stamp = pd.Timestamp(value)
    return stamp.tz_localize("Asia/Seoul") if stamp.tz is None else stamp.tz_convert("Asia/Seoul")


@contextmanager
def locked():
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "engine.lock").open("a+b") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def stop_exists():
    return (OUT / "STOP").exists() or (OUT / "controller_state/STOP").exists()


def guard(deadline=SEARCH_STOP, estimate=30, require_space=True):
    if stop_exists():
        raise RuntimeError("EXPLICIT_STOP: no automatic resume")
    end = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
    if (end - datetime.now(timezone.utc)).total_seconds() < max(15, estimate):
        raise RuntimeError("TIME_BUDGET_EXHAUSTED")
    if require_space and shutil.disk_usage(ROOT).free < 2 * 1024 ** 3:
        raise RuntimeError("STORAGE_BUDGET_EXHAUSTED")


def no_other_training():
    targets = [ROOT / "submission" / folder / "engine.py" for folder in ("score_push_10h", "score_push_22h", "score_push_23kst", "score_push_novel")]
    targets.append(ROOT / "submission/autoresearch/train.py")
    live = []
    for path in Path("/proc").iterdir():
        if not path.name.isdigit() or int(path.name) == os.getpid():
            continue
        try:
            fields = (path / "stat").read_text().rsplit(")", 1)[1].split()
            if fields[0] == "Z":
                continue
            argv = (path / "cmdline").read_bytes().split(b"\0")
            if any(str(target).encode() in argv for target in targets):
                live.append(int(path.name))
        except FileNotFoundError:
            continue
    assert not live, "Another learning entrypoint is alive: " + str(live)


def source_paths():
    names = ["engine.py", "transport.py", "controller.py", "verify_completion.py", "test_engine_nofit.py", "test_transport.py", "test_verify_completion.py"]
    return [CODE / name for name in names if (CODE / name).exists()] + [ROOT / "submission/validate_artifacts.py"]


def input_paths():
    paths = [BEST, ROOT / "submission/renew_candidate_20261105/manifest.json", OLD / "shared/search_data_manifest.json", OLD / "shared/features.parquet", OLD / "shared/primary.parquet", OLD / "shared/recent.parquet", FINAL / "selected_coefficients.json", FINAL / "protocol.json", FINAL / "prepared_manifest.json", LATE_LABELS]
    for split, part in (("latest_cutoff_march_may", "march_may"), ("test", "test")):
        paths += [FINAL / "predictions" / split / "predictions.parquet", FINAL / "data" / part / "evaluation.parquet", FINAL / "data" / part / "coverage.parquet"]
    for name in ("CAMPAIGN.md", "authorization.json"):
        if (OUT / name).exists():
            paths.append(OUT / name)
    return paths


def validate_keys(frame):
    assert set(frame.grp) == {"G1", "G2"}
    assert not frame.duplicated(KEYS).any()
    assert str(frame.ts.dt.tz) == "Asia/Seoul"
    assert frame.groupby("ts").size().eq(2).all()
    assert frame.ts.dt.minute.eq(0).all() and frame.ts.dt.second.eq(0).all()


def sidecar(frame, features):
    assert not features.duplicated(KEYS).any()
    result = frame.merge(features[KEYS + FEATURES], on=KEYS, how="left", sort=False, validate="one_to_one")
    assert result.loc[~result.night, FEATURES].notna().all().all()
    # No future labels enter this sidecar; night references are identically zero.
    result.loc[result.night, "cosz"] = result.loc[result.night, "cosz"].fillna(0.)
    return result.sort_values(KEYS).reset_index(drop=True)


def data_frame(split):
    if split in ("primary", "recent"):
        columns = KEYS + ["y", "smp", "k", "night", "static_capacity", "p_reference"]
        frame = pd.read_parquet(OLD / "shared" / (split + ".parquet"), columns=columns)
        features = pd.read_parquet(OLD / "shared/features.parquet", columns=KEYS + FEATURES)
    else:
        old_split, part = ("latest_cutoff_march_may", "march_may") if split == "latest" else ("test", "test")
        # Explicit column projection excludes every late label and price.
        frame = pd.read_parquet(FINAL / "predictions" / old_split / "predictions.parquet", columns=KEYS + ["p", "static_capacity"]).rename(columns={"p": "p_reference"})
        coverage = pd.read_parquet(FINAL / "data" / part / "coverage.parquet", columns=KEYS + ["night"])
        frame = frame.merge(coverage, on=KEYS, how="left", sort=False, validate="one_to_one")
        assert frame.night.notna().all()
        features = pd.read_parquet(FINAL / "data" / part / "evaluation.parquet", columns=KEYS + FEATURES)
    result = sidecar(frame, features)
    validate_keys(result)
    assert np.isfinite(result[["p_reference", "static_capacity"]]).all().all()
    assert result.p_reference.ge(0).all() and (result.p_reference <= result.static_capacity + 1e-7).all()
    assert result.loc[result.night, "p_reference"].eq(0).all()
    if split in ("latest", "test"):
        assert not set(result) & {"y", "smp", "k"}
    return result


def prepare():
    if (OUT / "protocol.json").exists():
        return verify_protocol()
    guard(DEADLINE, 30)
    no_other_training()
    assert sha(BEST) == BEST_SHA
    assert read(OLD / "controller_state/state.json")["phase"] == "finished"
    configs = transport.configs()
    assert len(configs) == 12 and len({c["id"] for c in configs}) == 12
    inputs = {relative(path): sha(path) for path in input_paths()}
    sources = {relative(path): sha(path) for path in source_paths()}
    data = {}
    for split in ("primary", "recent", "latest", "test"):
        frame = data_frame(split)
        path = OUT / "data" / (split + ".parquet")
        parquet(path, frame)
        data[split + ".parquet"] = sha(path)
    save(OUT / "configs.json", configs)
    jobs = [{"id": config["id"], "argv": [sys.executable, str(CODE / "engine.py"), "trial", "--id", config["id"]], "estimated_seconds": 120} for config in configs]
    completion = [{"id": "completion", "argv": [sys.executable, str(CODE / "engine.py"), "complete", "--deadline-utc", DEADLINE], "estimated_seconds": 120, "requires_success": []}]
    finalizer = {"id": "report", "argv": [sys.executable, str(CODE / "engine.py"), "report"], "estimated_seconds": 15}
    save(OUT / "jobs.json", jobs)
    save(OUT / "completion_jobs.json", completion)
    save(OUT / "finalizer_job.json", finalizer)
    protocol = {"status": "FROZEN", "version": 1, "created_utc": now(), "deadline_utc": DEADLINE, "search_stop_utc": SEARCH_STOP,
                "configs_sha256": sha(OUT / "configs.json"), "jobs_sha256": sha(OUT / "jobs.json"), "completion_jobs_sha256": sha(OUT / "completion_jobs.json"), "finalizer_job_sha256": sha(OUT / "finalizer_job.json"),
                "source_sha256": sources, "input_sha256": inputs, "prepared_data_sha256": data, "gates": GATES, "evaluation_folds": ["primary", "recent"], "required_prediction_files": ["primary.parquet", "recent.parquet"],
                "fit_scope": "One constrained weighted-L1 transport LP per arm fitted only on PRIMARY 2023-06-01<ts<=2024-06-01 KST; coefficients never refit on recent or late labels",
                "primary_in_sample": True, "recent_is_development_selection": True, "scalar_alpha_fits": 0,
                "selection_rule": "All 12 predefined arms must finish successfully. Eligible arms only; smallest recent W/reference ratio, then worst recent-quarter ratio, then fixed ID. At most one arm.",
                "required_completed_trials": 12,
                "late_policy": "Freeze selected config/model and latest/test prediction hashes before reading March-May labels; descriptive late audit never changes selected coefficients; late nonimprovement marks NOT_RECOMMENDED",
                "baseline_notes": "Champion weather coefficients were fitted on full PRIMARY. This is supplementary PRIMARY-fit development, not all-lineage chronological OOF. All historical periods already exposed; period overlap remains.",
                "deployment_provenance": {"latest_reference_cutoff": "2025-03-01", "test_reference_cutoff": "2025-06-01", "supplementary_coefficients_cutoff": "2024-06-01", "reference_column": "final/predictions/... p is champion; its p_reference is NOT champion"},
                "resources": {"parallel_model_fits": 1, "cpu_threads": 4, "blas_threads": 1}, "original_best_sha256": BEST_SHA,
                "actual_model_fits_during_preparation": 0, "late_target_values_loaded_during_preparation": False, "all_history_previously_exposed": True, "official_score_available": False, "uploaded": False}
    # Hash-only pinning of the late label file is not decoding its target values.
    for name, expected in inputs.items():
        assert sha(ROOT / name) == expected
    save(OUT / "protocol.json", protocol)
    return protocol


def verify_protocol():
    p = read(OUT / "protocol.json")
    assert p["deadline_utc"] == DEADLINE and p["search_stop_utc"] == SEARCH_STOP and p["gates"] == GATES
    for field in ("source_sha256", "input_sha256"):
        for name, expected in p[field].items():
            assert sha(ROOT / name) == expected, name
    for name, expected in p["prepared_data_sha256"].items():
        assert sha(OUT / "data" / name) == expected, name
    for name in ("configs", "jobs", "completion_jobs", "finalizer_job"):
        assert sha(OUT / (name + ".json")) == p[name + "_sha256"]
    assert sha(BEST) == BEST_SHA
    return p


def metric(frame, column="p"):
    values = frame[[column, "y", "smp", "k"]].to_numpy(float)
    assert np.isfinite(values).all()
    weights = values[:, 2] * values[:, 3]
    assert (weights >= 0).all()
    W = float(np.sum(weights * np.abs(values[:, 0] - values[:, 1])))
    denominator = float(np.sum(weights * values[:, 1]))
    assert denominator > 0
    revenue = float(np.sum(values[:, 2] * values[:, 1]))
    return {"W": W, "W_pct": 100 * W / denominator, "revenue": revenue, "S": revenue - .1 * W, "rows": len(frame)}


def physical(frame, prediction, config):
    pred = np.asarray(prediction, dtype=float)
    assert pred.shape == (len(frame),) and np.isfinite(pred).all()
    assert (pred >= -1e-7).all() and (pred <= frame.static_capacity.to_numpy() + 1e-7).all()
    assert np.all(pred[frame.night.to_numpy(bool)] == 0)
    temp = frame[KEYS + ["p_reference"]].assign(p=pred)
    family = config["family"]
    if "temporal" in family:
        temp["day"] = (temp.ts - pd.Timedelta(hours=1)).dt.date
        sums = temp.groupby(["grp", "day"])[["p_reference", "p"]].sum()
        kind = "group_day_energy"
    else:
        assert "spatial" in family
        sums = temp.groupby("ts")[["p_reference", "p"]].sum()
        kind = "hourly_total_energy"
    error = np.abs(sums.p.to_numpy() - sums.p_reference.to_numpy())
    assert np.all(error <= 1e-6 + 1e-10 * np.abs(sums.p_reference.to_numpy()))
    return {"status": "PASS", "finite": True, "nonnegative_within_1e-7": True, "own_capacity_within_1e-7": True, "night_exact_zero": True, "conservation": kind, "maximum_energy_difference": float(error.max(initial=0))}


def compare(frame):
    reference, candidate = metric(frame, "p_reference"), metric(frame)
    assert reference["W"] > 0
    return {"reference": reference, "candidate": candidate, "ratio": candidate["W"] / reference["W"]}


def evaluate(frames, checks):
    metrics = {name: compare(frame) for name, frame in frames.items()}
    recent = frames["recent"]
    quarters = {name: compare(recent.loc[recent.ts.gt(kst(begin)) & recent.ts.le(kst(end))])["ratio"] for name, (begin, end) in RECENT_QUARTERS.items()}
    groups = {group: compare(recent.loc[recent.grp.eq(group)])["ratio"] for group in ("G1", "G2")}
    gates = {"primary": metrics["primary"]["ratio"] <= GATES["primary_max"], "recent": metrics["recent"]["ratio"] <= GATES["recent_max"],
             "recent_quarters": max(quarters.values()) <= GATES["recent_quarter_max"], "recent_groups": max(groups.values()) <= GATES["recent_group_max"], "physical": all(item["status"] == "PASS" for item in checks.values())}
    return {"metrics": metrics, "recent_quarter_ratios": quarters, "recent_group_ratios": groups, "physical_checks": checks, "gate_checks": gates, "eligible": bool(all(gates.values()))}


def files_checked(folder, record):
    for name, expected in record["files_sha256"].items():
        assert sha(folder / name) == expected, str(folder / name)


def trial(identifier):
    protocol = verify_protocol()
    config = next(c for c in read(OUT / "configs.json") if c["id"] == identifier)
    folder = OUT / "trials" / identifier
    if (folder / "result.json").exists():
        record = read(folder / "receipt.json")
        files_checked(folder, record)
        result = read(folder / "result.json")
        assert result["receipt_sha256"] == sha(folder / "receipt.json") and result["config"] == config
        return result
    guard(SEARCH_STOP, 60)
    no_other_training()
    folder.mkdir(parents=True, exist_ok=True)
    if (folder / "fit_started.json").exists():
        raise RuntimeError("PARTIAL_FIT_EXISTS: automatic retraining prohibited")
    primary = pd.read_parquet(OUT / "data/primary.parquet")
    assert primary.ts.min() > kst("2023-06-01") and primary.ts.max() <= kst("2024-06-01")
    started = now()
    save(folder / "fit_started.json", {"id": identifier, "config": config, "created_utc": started, "training_cutoff": "2024-06-01T00:00:00+09:00"})
    with threadpool_limits(limits=1, user_api="blas"):
        model, fitmeta = transport.fit(primary, config)
    finished = now()
    training = {"fold": "primary", "training_cutoff": "2024-06-01T00:00:00+09:00", "train_min_ts": str(primary.ts.min()), "train_max_ts": str(primary.ts.max()), "rows": len(primary), "fit_started_utc": started, "fit_finished_utc": finished}
    wrapper = {"version": 1, "config": config, "training": training, "transport_model": model, "fitmeta": fitmeta}
    save(folder / "model.json", wrapper)
    loaded = read(folder / "model.json")
    frames, checks = {}, {}
    # RECENT labels are not passed to fit; the saved PRIMARY model is applied unchanged.
    for split in ("primary", "recent"):
        frame = primary if split == "primary" else pd.read_parquet(OUT / "data/recent.parquet")
        inputs = frame.drop(columns=["y", "smp", "k"])
        pred = transport.predict(inputs, config, model)
        replay = transport.predict(inputs, config, loaded["transport_model"])
        np.testing.assert_array_equal(pred, replay)
        checks[split] = physical(inputs, pred, config)
        output = frame[KEYS + ["y", "smp", "k", "night", "static_capacity", "p_reference"]].assign(p=pred)
        parquet(folder / (split + ".parquet"), output)
        frames[split] = output
    evidence = evaluate(frames, checks)
    record = {"status": "PASS", "id": identifier, "config": config, "created_utc": now(), "real_model_fits": 1, "training": training,
              "protocol_sha256": sha(OUT / "protocol.json"), "source_sha256": protocol["source_sha256"], "input_sha256": protocol["input_sha256"],
              "prepared_data_sha256": protocol["prepared_data_sha256"], "files_sha256": {name: sha(folder / name) for name in ("model.json", "primary.parquet", "recent.parquet")},
              "saved_model_replay_exact": True, "primary_in_sample": True, "recent_used_for_fit": False, "scalar_alpha_fits": 0, "late_targets_loaded": False}
    save(folder / "receipt.json", record)
    result = {"status": "PASS", "id": identifier, "config": config, "created_utc": now(), "real_model_fits": 1, **evidence,
              "rank": [evidence["metrics"]["recent"]["ratio"], max(evidence["recent_quarter_ratios"].values()), identifier], "model_sha256": sha(folder / "model.json"), "receipt_sha256": sha(folder / "receipt.json"),
              "primary_in_sample": True, "recent_is_development_selection": True, "all_history_previously_exposed": True, "official_improvement_verified": False}
    save(folder / "result.json", result)
    return result


def completed_results():
    rows = []
    for config in read(OUT / "configs.json"):
        folder = OUT / "trials" / config["id"]
        if (folder / "result.json").exists():
            result = read(folder / "result.json")
            assert result["config"] == config and result["status"] == "PASS"
            record = read(folder / "receipt.json")
            files_checked(folder, record)
            assert sha(folder / "receipt.json") == result["receipt_sha256"]
            rows.append(result)
    return rows


def bootstrap(frame, replicates=2000, seed=20261108):
    week = (frame.ts.dt.tz_localize(None) - pd.Timedelta(hours=1)).dt.to_period("W-SUN")
    weights = frame.smp.to_numpy() * frame.k.to_numpy()
    b = weights * np.abs(frame.p_reference.to_numpy() - frame.y.to_numpy())
    c = weights * np.abs(frame.p.to_numpy() - frame.y.to_numpy())
    totals = pd.DataFrame({"week": week, "b": b, "c": c}).groupby("week")[["b", "c"]].sum().to_numpy()
    rng = np.random.default_rng(seed)
    counts = rng.multinomial(len(totals), np.full(len(totals), 1 / len(totals)), size=replicates)
    samples = counts @ totals
    assert (samples[:, 0] > 0).all()
    low, high = np.quantile(100 * (samples[:, 1] / samples[:, 0] - 1), [.025, .975])
    return {"replicates": replicates, "random_seed": seed, "weeks": len(totals), "relative_W_change_pct": 100 * (c.sum() / b.sum() - 1), "CI95": [float(low), float(high)], "zero_in_CI": bool(low <= 0 <= high),
            "unit": "KST whole calendar week, same resampled blocks across both groups and baseline/candidate", "selection_use": False, "conditional_on_saved_model_and_development_selection": True}


def export(test, selection, audit):
    if (CANDIDATE / "manifest.json").exists():
        record = read(CANDIDATE / "manifest.json")
        files_checked(CANDIDATE, record)
        assert record["selection"] == selection
        return record
    assert not CANDIDATE.exists(), "Partial candidate preserved; manual review required"
    with zipfile.ZipFile(BEST) as archive:
        composition = archive.read("composition.csv")
        original = pd.read_csv(io.BytesIO(archive.read("forecast.csv")))
    original["ts"] = pd.to_datetime(original.ts).dt.tz_convert("Asia/Seoul")
    original = original.rename(columns={"group": "grp"}).sort_values(["grp", "ts"]).reset_index(drop=True)
    test = test.sort_values(["grp", "ts"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(test[KEYS], original[KEYS], check_exact=True)
    np.testing.assert_array_equal(np.round(test.p_reference, 3), original.forecast_kwh)
    assert len(test) == 17520
    physical(test, test.p.to_numpy(), selection["config"])
    CANDIDATE.mkdir()
    (CANDIDATE / "composition.csv").write_bytes(composition)
    pd.DataFrame({"group": test.grp, "ts": test.ts.astype(str), "forecast_kwh": np.round(test.p, 3)}).to_csv(CANDIDATE / "forecast.csv", index=False, lineterminator="\r\n")
    with zipfile.ZipFile(CANDIDATE / "submission_files.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name in ("composition.csv", "forecast.csv"):
            archive.write(CANDIDATE / name, arcname=name)
    check = subprocess.run([sys.executable, str(ROOT / "submission/validate_artifacts.py"), str(CANDIDATE), "--self-check"], capture_output=True, text=True, timeout=90)
    (CANDIDATE / "validation.log").write_text(check.stdout + check.stderr)
    assert check.returncode == 0, "Artifact validation failed"
    validation = json.loads(check.stdout)
    assert validation["rows_above_own_capacity"] == 0
    record = {"created_utc": now(), "selection": selection, "late_audit": audit, "validation": validation, "original_composition_bytes_preserved": True,
              "original_best_sha256": BEST_SHA, "files_sha256": {name: sha(CANDIDATE / name) for name in ("composition.csv", "forecast.csv", "submission_files.zip")},
              "all_history_previously_exposed": True, "official_score_available": False, "uploaded": False, "recommendation": "NOT_RECOMMENDED" if audit["metrics"]["ratio"] >= 1 else "UNSCORED_CANDIDATE_REQUIRES_OFFICIAL_EVALUATION"}
    save(CANDIDATE / "manifest.json", record)
    return record


def complete(deadline=DEADLINE):
    protocol = verify_protocol()
    folder = OUT / "completion"
    if (folder / "result.json").exists():
        result = read(folder / "result.json")
        files_checked(folder, result)
        if result["exported"]:
            assert sha(CANDIDATE / "manifest.json") == result["manifest_sha256"]
            assert sha(CANDIDATE / "submission_files.zip") == result["candidate_sha256"]
            files_checked(CANDIDATE, read(CANDIDATE / "manifest.json"))
        return result
    guard(deadline, 120)
    no_other_training()
    folder.mkdir(parents=True, exist_ok=True)
    rows = completed_results()
    expected_ids = {config["id"] for config in read(OUT / "configs.json")}
    assert len(expected_ids) == 12
    if {row["id"] for row in rows} != expected_ids:
        result = {"status": "INSUFFICIENT_COMPLETED_COVERAGE", "created_utc": now(), "completed_trials": len(rows), "required_completed_trials": 12,
                  "missing_ids": sorted(expected_ids - {row["id"] for row in rows}), "exported": False, "late_targets_loaded": False,
                  "real_model_fits": 0, "files_sha256": {}, "official_improvement_verified": False}
        save(folder / "result.json", result)
        return result
    candidates = sorted([row for row in rows if row["eligible"]], key=lambda row: tuple(row["rank"]))
    shortlist = {"completed": len(rows), "eligible_ids": [r["id"] for r in candidates], "selected": candidates[0]["id"] if candidates else None, "before_late_targets": True}
    if (folder / "shortlist.json").exists():
        existing = read(folder / "shortlist.json")
        assert all(existing[key] == value for key, value in shortlist.items())
    else:
        save(folder / "shortlist.json", {"created_utc": now(), **shortlist})
    if not candidates:
        result = {"status": "NO_QUALIFYING_RECIPE", "created_utc": now(), "completed_trials": len(rows), "exported": False, "late_targets_loaded": False, "real_model_fits": 0,
                  "files_sha256": {"shortlist.json": sha(folder / "shortlist.json")}, "official_improvement_verified": False}
        save(folder / "result.json", result)
        return result
    chosen = candidates[0]
    model_path = OUT / "trials" / chosen["id"] / "model.json"
    wrapper = read(model_path)
    selection_path = folder / "selection_frozen.json"
    if selection_path.exists():
        selection = read(selection_path)
        assert selection["id"] == chosen["id"] and selection["model_sha256"] == sha(model_path)
    else:
        selection = {"created_utc": now(), "id": chosen["id"], "config": chosen["config"], "model_path": relative(model_path), "model_sha256": sha(model_path),
                     "result_sha256": sha(OUT / "trials" / chosen["id"] / "result.json"), "protocol_sha256": sha(OUT / "protocol.json"), "selection_rule": protocol["selection_rule"], "before_late_targets": True, "no_refit_after_selection": True}
        save(selection_path, selection)
    predictions = {}
    freeze_path = folder / "predictions_frozen.json"
    for split in ("latest", "test"):
        inputs = pd.read_parquet(OUT / "data" / (split + ".parquet"))
        assert not set(inputs) & {"y", "smp", "k"}
        prediction = transport.predict(inputs, chosen["config"], wrapper["transport_model"])
        physical(inputs, prediction, chosen["config"])
        output = inputs[KEYS + ["night", "static_capacity", "p_reference"]].assign(p=prediction)
        destination = folder / (split + "_predictions.parquet")
        if freeze_path.exists():
            pd.testing.assert_frame_equal(pd.read_parquet(destination), output, check_exact=True)
        else:
            parquet(destination, output)
        predictions[split] = output
    if freeze_path.exists():
        frozen = read(freeze_path)
        files_checked(folder, frozen)
        assert frozen["selection_sha256"] == sha(selection_path)
    else:
        frozen = {"created_utc": now(), "selection_sha256": sha(selection_path), "files_sha256": {split + "_predictions.parquet": sha(folder / (split + "_predictions.parquet")) for split in ("latest", "test")}, "before_late_targets": True, "supplementary_real_model_fits": 0}
        save(freeze_path, frozen)
    # The first late-label decode is below both persisted immutable barriers.
    assert frozen["before_late_targets"] and selection["before_late_targets"]
    assert sha(LATE_LABELS) == protocol["input_sha256"][relative(LATE_LABELS)]
    audit_path = folder / "audit.json"
    if audit_path.exists():
        audit = read(audit_path)
        assert audit["selection_sha256"] == sha(selection_path) and audit["predictions_frozen_sha256"] == sha(freeze_path)
        assert audit["labels_source_sha256"] == sha(LATE_LABELS)
        assert audit["latest_scored_predictions_sha256"] == sha(folder / "latest_scored_predictions.parquet")
    else:
        labels = pd.read_parquet(LATE_LABELS, columns=KEYS + ["y", "smp", "k"])
        scored = predictions["latest"].merge(labels, on=KEYS, how="left", sort=False, validate="one_to_one")
        assert scored[["y", "smp", "k"]].notna().all().all()
        assert scored.ts.min() > kst("2025-03-01") and scored.ts.max() <= kst("2025-06-01")
        parquet(folder / "latest_scored_predictions.parquet", scored)
        audit = {"created_utc": now(), "labels_source": relative(LATE_LABELS), "labels_source_sha256": sha(LATE_LABELS), "selection_sha256": sha(selection_path), "predictions_frozen_sha256": sha(freeze_path), "latest_predictions_sha256": sha(folder / "latest_predictions.parquet"),
                 "latest_scored_predictions_sha256": sha(folder / "latest_scored_predictions.parquet"), "metrics": compare(scored), "weekly_bootstrap": bootstrap(scored), "used_for_selection": False,
                 "coefficients_changed": False, "real_model_fits": 0, "all_history_previously_exposed": True}
        save(audit_path, audit)
    guard(deadline, 120)
    manifest = export(predictions["test"], selection, audit)
    result = {"status": "EXPORTED_UNSCORED_CANDIDATE", "created_utc": now(), "selected_id": chosen["id"], "completed_trials": len(rows), "exported": True, "candidate": str(CANDIDATE), "candidate_sha256": sha(CANDIDATE / "submission_files.zip"), "manifest_sha256": sha(CANDIDATE / "manifest.json"), "recommendation": manifest["recommendation"], "late_targets_loaded": True, "late_W_ratio": audit["metrics"]["ratio"], "real_model_fits": 0, "official_improvement_verified": False, "uploaded": False,
              "files_sha256": {name: sha(folder / name) for name in ("shortlist.json", "selection_frozen.json", "predictions_frozen.json", "latest_predictions.parquet", "test_predictions.parquet", "latest_scored_predictions.parquet", "audit.json")}}
    save(folder / "result.json", result)
    return result


def report():
    rows = completed_results()
    result = {"created_utc": now(), "planned_trials": len(read(OUT / "configs.json")), "completed_trials": len(rows), "eligible_trials": sum(row["eligible"] for row in rows), "real_model_fits": sum(row["real_model_fits"] for row in rows),
              "primary_in_sample": True, "recent_is_development_selection": True, "all_history_previously_exposed": True, "official_score_available": False, "original_best_preserved": sha(BEST) == BEST_SHA, "results": rows,
              "completion": read(OUT / "completion/result.json") if (OUT / "completion/result.json").exists() else None}
    save(OUT / "report.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "trial", "complete", "report"])
    parser.add_argument("--id")
    parser.add_argument("--deadline-utc", default=DEADLINE)
    args = parser.parse_args()
    with locked():
        if args.command == "prepare":
            result = prepare()
        elif args.command == "trial":
            assert args.id
            result = trial(args.id)
        elif args.command == "complete":
            result = complete(args.deadline_utc)
        else:
            result = report()
    print(json.dumps(plain(result), ensure_ascii=False, indent=2, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
