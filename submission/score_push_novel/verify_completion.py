"""Independent terminal verifier for the frozen transport experiments.

This program never fits, resumes, publishes or rewrites a candidate.  It checks
process termination before opening research data, and replays only saved
coefficients.  A verified empty shortlist is not verified model improvement.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import zipfile

os.environ.update(OMP_NUM_THREADS="4", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1")
sys.dont_write_bytecode = True
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis_outputs/research_novel_20261108"
BEST = ROOT / "submission/renew_candidate_20261105/submission_files.zip"
BEST_SHA = "ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434"
DEADLINE = "2026-11-08T14:00:00Z"
KEYS = ["ts", "grp"]
EARLIEST = pd.Timestamp("2023-06-01", tz="Asia/Seoul")
CUTOFF = pd.Timestamp("2024-06-01", tz="Asia/Seoul")
RECENT_END = pd.Timestamp("2025-03-01", tz="Asia/Seoul")
GATES = {"primary_max": 1.0, "recent_max": .9999, "recent_quarter_max": 1.005, "recent_group_max": 1.001}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def contained(root, relative):
    path = Path(relative)
    path = path if path.is_absolute() else Path(root) / path
    assert path.resolve().is_relative_to(Path(root).resolve()), f"Path escapes campaign repository: {relative}"
    assert not path.is_symlink(), f"Symbolic link is not a pinned regular artifact: {relative}"
    return path


def verify_mapping(root, mapping):
    assert isinstance(mapping, dict)
    for name, expected in mapping.items():
        assert isinstance(expected, str) and len(expected) == 64
        assert sha(contained(root, name)) == expected, f"Pinned bytes changed: {name}"
    return len(mapping)


def process_snapshot(proc_root=Path("/proc")):
    """Read only stat, never process environments or credentials."""
    boot = (proc_root / "sys/kernel/random/boot_id").read_text().strip()
    live, errors = {}, []
    for path in proc_root.iterdir():
        if not path.name.isdigit():
            continue
        try:
            parts = (path / "stat").read_text().rsplit(")", 1)[1].split()
        except (FileNotFoundError, ProcessLookupError):
            continue
        except (PermissionError, OSError) as exc:
            errors.append({"pid": int(path.name), "error": type(exc).__name__})
            continue
        if parts[0] not in {"Z", "X"}:
            live[int(path.name)] = {"pid": int(path.name), "pgid": int(parts[2]),
                "start_ticks": int(parts[19]), "boot_id": boot}
    return boot, live, errors


def terminal_gate(directory, root=ROOT, out=OUT, proc_reader=process_snapshot):
    directory, root, out = Path(directory), Path(root), Path(out)
    state_path = directory / "state.json"
    if not state_path.exists():
        return False, {"reason": "Controller state does not exist"}, None
    state = read(state_path)
    if state.get("phase") != "finished":
        return False, {"reason": "Controller has not finished", "phase": state.get("phase")}, state
    assert state["controller_sha256"] == sha(root / "submission/score_push_novel/controller.py")
    manifest_path = out / "controller_manifest.json"
    assert sha(manifest_path) == state["manifest_sha256"]
    manifest = read(manifest_path)
    assert pd.Timestamp(state["deadline_utc"]) == pd.Timestamp(manifest["deadline_utc"]) == pd.Timestamp(DEADLINE)
    requested = manifest.get("jobs", []) + manifest.get("completion_jobs", [])
    expected = {item["id"] for item in requested}
    assert len(expected) == len(requested), "Duplicate controller job identifiers"
    finalizer = manifest.get("finalizer")
    allowed = expected | ({finalizer["id"]} if finalizer else set())
    assert expected.issubset(state["jobs"]) and set(state["jobs"]).issubset(allowed)
    identities = [state["controller_identity"]]
    identities += [item["wrapper_identity"] for item in state["jobs"].values() if item.get("wrapper_identity")]
    for path in sorted((directory / "jobs").glob("*/started.json")):
        started = read(path)
        assert path.parent.name in state["jobs"]
        assert started["manifest_sha256"] == state["manifest_sha256"]
        assert started["nonce"] == state["jobs"][path.parent.name]["nonce"]
        identities += [started[key] for key in ("identity", "worker_identity") if started.get(key)]
    boot, live, errors = proc_reader()
    groups = {item["pgid"] for item in identities if item["boot_id"] == boot}
    owned = sorted({item["pid"] for item in identities if item["pid"] in live and
        all(item[key] == live[item["pid"]][key] for key in ("pid", "pgid", "start_ticks", "boot_id"))})
    group_alive = sorted(pid for pid, item in live.items() if item["pgid"] in groups)
    evidence = {"controller_phase": "finished", "recorded_identities": len(identities),
        "live_recorded_identity_pids": owned, "live_recorded_group_pids": group_alive,
        "controller_manifest_sha256": state["manifest_sha256"]}
    if errors:
        return False, {**evidence, "reason": "Incomplete process scan", "unreadable_processes": len(errors)}, state
    if owned or group_alive:
        return False, {**evidence, "reason": "Recorded owned process still alive"}, state
    statuses = {"completed", "failed", "interrupted", "time_limit", "stopped", "deferred_budget", "skipped_dependency", "pending"}
    receipt_count = 0
    for identifier, item in state["jobs"].items():
        assert item["status"] in statuses, f"Unresolved terminal job: {identifier}"
        if item.get("receipt_sha256"):
            path = directory / "jobs" / identifier / "receipt.json"
            assert sha(path) == item["receipt_sha256"]
            receipt = read(path)
            for key, expected_value in (("nonce", item["nonce"]), ("manifest_sha256", state["manifest_sha256"]),
                    ("status", item["status"]), ("exit_code", item.get("exit_code"))):
                assert receipt[key] == expected_value, (identifier, key)
            receipt_count += 1
    evidence["controller_receipts_verified"] = receipt_count
    evidence["controller_input_pins_verified"] = verify_mapping(root, manifest.get("input_sha256", {}))
    if any(item["status"] == "pending" for item in state["jobs"].values()):
        return False, {**evidence, "reason": "Pending jobs remain; incomplete checkpoint"}, state
    if any(state["jobs"][item["id"]]["status"] != "completed" for item in manifest.get("completion_jobs", [])):
        return False, {**evidence, "reason": "Completion job did not finish successfully"}, state
    if finalizer and (finalizer["id"] not in state["jobs"] or state["jobs"][finalizer["id"]]["status"] != "completed"):
        return False, {**evidence, "reason": "Reporting finalizer did not finish successfully"}, state
    return True, evidence, state


def score(frame, prediction):
    y = frame.y.to_numpy(float)
    price = frame.smp.to_numpy(float)
    weight = price * frame.k.to_numpy(float)
    p = np.asarray(prediction, dtype=float)
    assert len(p) == len(frame) and np.isfinite(np.column_stack((y, price, weight, p))).all()
    assert (weight >= 0).all() and np.dot(weight, y) > 0
    W, revenue = float(np.dot(weight, np.abs(p-y))), float(np.dot(price, y))
    return {"W": W, "W_pct": 100 * W / float(np.dot(weight, y)),
        "revenue": revenue, "S": revenue - .1 * W, "rows": len(frame)}


def compare_numbers(actual, expected):
    if isinstance(expected, dict):
        assert set(actual) == set(expected), (set(actual), set(expected))
        for key in expected:
            compare_numbers(actual[key], expected[key])
    elif isinstance(expected, (list, tuple)):
        assert len(actual) == len(expected)
        for left, right in zip(actual, expected):
            compare_numbers(left, right)
    elif isinstance(expected, (float, int)) and not isinstance(expected, bool):
        np.testing.assert_allclose(actual, expected, rtol=1e-11, atol=1e-6)
    else:
        assert actual == expected, (actual, expected)


def keys(frame):
    assert not frame.duplicated(KEYS).any() and not frame[KEYS].isna().any().any()
    assert str(frame.ts.dt.tz) == "Asia/Seoul", "Timestamps must preserve KST alignment"
    return frame[KEYS]


def physical(frame, prediction, family):
    p, original = np.asarray(prediction, float), frame.p_reference.to_numpy(float)
    cap, night = frame.static_capacity.to_numpy(float), frame.night.to_numpy(bool)
    assert np.isfinite(p).all() and np.isfinite(original).all() and np.isfinite(cap).all()
    assert (cap >= 0).all() and (p >= -1e-7).all() and (p <= cap + 1e-7).all()
    assert np.all(p[night] == 0)
    check = frame[KEYS].copy()
    check["reference"], check["candidate"] = original, p
    if family == "temporal":
        check["day"] = (frame.ts.dt.tz_convert("Asia/Seoul") - pd.Timedelta(hours=1)).dt.date
        sums = check.groupby(["day", "grp"])[["reference", "candidate"]].sum()
    elif family == "spatial":
        sums = check.groupby("ts")[["reference", "candidate"]].sum()
    else:
        raise AssertionError("Unknown conservation family")
    np.testing.assert_allclose(sums.candidate, sums.reference, rtol=1e-10, atol=1e-6)
    return {"finite_nonnegative_capacity_night": True, "conservation": True,
        "maximum_conservation_error": float(np.abs(sums.candidate-sums.reference).max())}


def development(primary, recent, primary_p, recent_p, gates=GATES):
    assert gates == GATES, "Unexpected development gate change"
    metrics = {}
    for name, frame, p in (("primary", primary, primary_p), ("recent", recent, recent_p)):
        ref, cand = score(frame, frame.p_reference), score(frame, p)
        metrics[name] = {"reference": ref, "candidate": cand, "ratio": cand["W"] / ref["W"]}
    quarters = {}
    for label, start, end in (("jun_aug", "2024-06-01", "2024-09-01"),
                             ("sep_nov", "2024-09-01", "2024-12-01"),
                             ("dec_feb", "2024-12-01", "2025-03-01")):
        mask = recent.ts.gt(pd.Timestamp(start, tz="Asia/Seoul")) & recent.ts.le(pd.Timestamp(end, tz="Asia/Seoul"))
        assert mask.any()
        quarters[label] = score(recent.loc[mask], np.asarray(recent_p)[mask])["W"] / score(recent.loc[mask], recent.loc[mask].p_reference)["W"]
    groups = {}
    for group in ("G1", "G2"):
        mask = recent.grp.eq(group)
        assert mask.any()
        groups[group] = score(recent.loc[mask], np.asarray(recent_p)[mask])["W"] / score(recent.loc[mask], recent.loc[mask].p_reference)["W"]
    flags = {"primary": metrics["primary"]["ratio"] <= gates["primary_max"],
             "recent": metrics["recent"]["ratio"] <= gates["recent_max"],
             "recent_quarters": max(quarters.values()) <= gates["recent_quarter_max"],
             "recent_groups": max(groups.values()) <= gates["recent_group_max"], "physical": True}
    return metrics, quarters, groups, flags


def training_risk(frame, prediction, fitmeta):
    weight = (frame.smp * frame.k).to_numpy(float)
    baseline = weight * np.abs(frame.p_reference.to_numpy(float)-frame.y.to_numpy(float))
    candidate = weight * np.abs(np.asarray(prediction, float)-frame.y.to_numpy(float))
    assert fitmeta["risk_allowance"] == .001 and fitmeta["coefficient_penalty"] == .0005
    assert fitmeta["application_labels_read"] is False
    local = frame.ts.dt.tz_convert("Asia/Seoul").dt.tz_localize(None)-pd.Timedelta(hours=1)
    environments = local.dt.strftime("%Y-%m") + "/" + frame.grp
    work = pd.DataFrame({"environment": environments, "baseline": baseline, "candidate": candidate})
    grouped = work.groupby("environment")[["baseline", "candidate"]].sum()
    assert (grouped.candidate <= grouped.baseline*1.001 + max(1e-5, baseline.sum()*2e-8)).all()
    compare_numbers(fitmeta["baseline_W"], float(baseline.sum()))
    compare_numbers(fitmeta["fitted_W"], float(candidate.sum()))
    if fitmeta["identity_fallback"]:
        np.testing.assert_array_equal(prediction, frame.p_reference)
    else:
        expected = [{"environment": name, "reference_W": float(row.baseline), "candidate_W": float(row.candidate),
            "ratio": None if row.baseline == 0 else float(row.candidate/row.baseline)} for name, row in grouped.iterrows()]
        compare_numbers(fitmeta["environment_risks"], expected)


def check_weekly_bootstrap(frame, recorded):
    assert recorded["replicates"] == 2000 and recorded["random_seed"] == 20261108
    assert recorded["selection_use"] is False and recorded["conditional_on_saved_model_and_development_selection"]
    weeks = (frame.ts.dt.tz_convert("Asia/Seoul").dt.tz_localize(None)-pd.Timedelta(hours=1)).dt.to_period("W-SUN")
    codes, names = pd.factorize(weeks, sort=True)
    weight = (frame.smp*frame.k).to_numpy(float)
    before = weight*np.abs(frame.p_reference.to_numpy(float)-frame.y.to_numpy(float))
    after = weight*np.abs(frame.p.to_numpy(float)-frame.y.to_numpy(float))
    wb = np.bincount(codes, weights=before, minlength=len(names))
    wc = np.bincount(codes, weights=after, minlength=len(names))
    counts = np.random.default_rng(20261108).multinomial(len(names), np.full(len(names), 1/len(names)), size=2000)
    baseline, candidate = counts @ wb, counts @ wc
    assert (baseline > 0).all()
    low, high = np.quantile(100*(candidate/baseline-1), [.025, .975])
    assert recorded["weeks"] == len(names)
    compare_numbers(recorded["relative_W_change_pct"], 100*(after.sum()/before.sum()-1))
    compare_numbers(recorded["CI95"], [float(low), float(high)])
    assert recorded["zero_in_CI"] == bool(low <= 0 <= high)


def load_transport(protocol, root=ROOT):
    relative = "submission/score_push_novel/transport.py"
    path = Path(root) / relative
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == protocol["source_sha256"][relative]
    spec = importlib.util.spec_from_file_location("independently_replayed_frozen_transport", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    exec(compile(raw, str(path), "exec"), mod.__dict__)
    return mod


def aligned_output(prepared, path, replay, family):
    output = pd.read_parquet(path)
    pd.testing.assert_frame_equal(keys(prepared), keys(output), check_exact=True)
    for column in ("p_reference", "static_capacity", "night", "y", "smp", "k"):
        if column in prepared:
            pd.testing.assert_series_equal(prepared[column], output[column], check_names=True, check_exact=True)
    np.testing.assert_array_equal(output.p.to_numpy(float), np.asarray(replay, float))
    physical(prepared, output.p, family)
    return output


def verify_zip(candidate, predicted, best=BEST):
    candidate = Path(candidate)
    with zipfile.ZipFile(best) as original, zipfile.ZipFile(candidate / "submission_files.zip") as exported:
        assert sorted(exported.namelist()) == ["composition.csv", "forecast.csv"]
        assert exported.read("composition.csv") == original.read("composition.csv") == (candidate / "composition.csv").read_bytes()
        assert exported.read("forecast.csv") == (candidate / "forecast.csv").read_bytes()
        new = pd.read_csv(io.BytesIO(exported.read("forecast.csv")))
        old = pd.read_csv(io.BytesIO(original.read("forecast.csv")))
    assert list(new) == ["group", "ts", "forecast_kwh"] and len(new) == len(predicted) == 17520
    for frame in (new, old):
        frame["ts"] = pd.to_datetime(frame.ts).dt.tz_convert("Asia/Seoul")
        frame.rename(columns={"group": "grp"}, inplace=True)
        frame.sort_values(KEYS, inplace=True, ignore_index=True)
    expected = predicted.sort_values(KEYS).reset_index(drop=True)
    pd.testing.assert_frame_equal(keys(new), keys(expected), check_exact=True)
    pd.testing.assert_frame_equal(keys(old), keys(expected), check_exact=True)
    np.testing.assert_array_equal(old.forecast_kwh.to_numpy(), np.round(expected.p_reference.to_numpy(), 3))
    np.testing.assert_array_equal(new.forecast_kwh.to_numpy(), np.round(expected.p.to_numpy(), 3))
    assert np.isfinite(new.forecast_kwh).all() and new.forecast_kwh.ge(0).all()
    assert (new.forecast_kwh.to_numpy() <= expected.static_capacity.to_numpy() + .0005 + 1e-7).all()
    assert new.loc[expected.night.to_numpy(bool), "forecast_kwh"].eq(0).all()
    return sha(candidate / "submission_files.zip")


def main(controller_directory=OUT / "controller_state", root=ROOT, out=OUT):
    root, out = Path(root), Path(out)
    report = {"utc": datetime.now(timezone.utc).isoformat(), "actual_model_fits": 0,
        "saved_weight_prediction_replays": 0, "improvement_verified": False,
        "official_improvement_verified": False, "uploaded": False,
        "all_history_previously_exposed": True, "late_targets_loaded": False,
        "verifier_sha256": sha(Path(__file__))}
    ready, terminal, state = terminal_gate(controller_directory, root, out)
    report["terminal_gate"] = terminal
    if not ready or not (out / "completion/result.json").exists():
        return {**report, "status": "CHECKPOINT_ONLY", "verification_status": "CHECKPOINT_ONLY",
            "outcome": "INCOMPLETE", "reason": terminal.get("reason", "Completion artifact absent")}
    protocol = read(out / "protocol.json")
    assert pd.Timestamp(protocol["deadline_utc"]) == pd.Timestamp(DEADLINE)
    assert protocol["status"] == "FROZEN" and protocol["gates"] == GATES
    assert protocol["primary_in_sample"] and protocol["recent_is_development_selection"]
    assert protocol["scalar_alpha_fits"] == 0 and protocol["all_history_previously_exposed"]
    assert sha(out / "configs.json") == protocol["configs_sha256"]
    report["source_pins_verified"] = verify_mapping(root, protocol["source_sha256"])
    report["input_pins_verified"] = verify_mapping(root, protocol["input_sha256"])
    report["prepared_data_pins_verified"] = verify_mapping(out / "data", protocol["prepared_data_sha256"])
    assert sha(root / BEST.relative_to(ROOT)) == BEST_SHA
    report.update(protocol_sha256=sha(out / "protocol.json"), protected_best_sha256=BEST_SHA, official_best_preserved=True)
    configs = read(out / "configs.json")
    transport = load_transport(protocol, root)
    assert configs == transport.configurations() and len(configs) == 12
    frames = {name: pd.read_parquet(out / "data" / f"{name}.parquet") for name in ("primary", "recent")}
    for frame in frames.values():
        keys(frame)
    assert frames["primary"].ts.min() > EARLIEST and frames["primary"].ts.max() <= CUTOFF
    assert frames["recent"].ts.min() > CUTOFF and frames["recent"].ts.max() <= RECENT_END
    checked, models = {}, {}
    for config in configs:
        identifier = config["id"]
        folder = out / "trials" / identifier
        if not (folder / "result.json").exists():
            continue
        result = read(folder / "result.json")
        assert identifier in state["jobs"] and state["jobs"][identifier]["status"] == "completed"
        assert result["status"] == "PASS" and result["id"] == identifier and result["config"] == config
        assert result["real_model_fits"] == 1
        record = read(folder / "receipt.json")
        assert sha(folder / "receipt.json") == result["receipt_sha256"]
        assert record["status"] == "PASS" and record["id"] == identifier and record["config"] == config and record["real_model_fits"] == 1
        assert record["source_sha256"] == protocol["source_sha256"]
        assert record["input_sha256"] == protocol["input_sha256"]
        assert record["prepared_data_sha256"] == protocol["prepared_data_sha256"]
        assert record["protocol_sha256"] == report["protocol_sha256"]
        assert record["saved_model_replay_exact"] and record["primary_in_sample"]
        assert record["recent_used_for_fit"] is False and record["late_targets_loaded"] is False
        assert record["scalar_alpha_fits"] == 0
        verify_mapping(folder, record["files_sha256"])
        wrapper = read(folder / "model.json")
        assert sha(folder / "model.json") == result["model_sha256"]
        assert wrapper["config"] == config and wrapper["training"] == record["training"]
        training = wrapper["training"]
        assert training["fold"] == "primary" and pd.Timestamp(training["training_cutoff"]) == CUTOFF
        assert pd.Timestamp(training["train_min_ts"]) == frames["primary"].ts.min()
        assert pd.Timestamp(training["train_max_ts"]) == frames["primary"].ts.max()
        assert training["rows"] == len(frames["primary"])
        assert pd.Timestamp(training["fit_started_utc"]) <= pd.Timestamp(training["fit_finished_utc"])
        model = wrapper["transport_model"]
        assert model["config"] == config
        replay = {name: transport.predict(frame.drop(columns=["y", "smp", "k"]), config, model) for name, frame in frames.items()}
        for name in frames:
            aligned_output(frames[name], folder / f"{name}.parquet", replay[name], config["family"])
            report["saved_weight_prediction_replays"] += 1
        training_risk(frames["primary"], replay["primary"], wrapper["fitmeta"])
        metrics, quarters, groups, flags = development(frames["primary"], frames["recent"], replay["primary"], replay["recent"])
        compare_numbers(result["metrics"], metrics)
        compare_numbers(result["recent_quarter_ratios"], quarters)
        compare_numbers(result["recent_group_ratios"], groups)
        assert result["gate_checks"] == flags and result["eligible"] == all(flags.values())
        rank = [metrics["recent"]["ratio"], max(quarters.values()), identifier]
        compare_numbers(result["rank"], rank)
        checked[identifier] = {"eligible": all(flags.values()), "rank": rank, "result_sha256": sha(folder / "result.json")}
        models[identifier] = wrapper
    completion = read(out / "completion/result.json")
    verify_mapping(out / "completion", completion["files_sha256"])
    assert completion["completed_trials"] == len(checked)
    report.update(completed_trials_verified=len(checked), eligible_trials=sum(item["eligible"] for item in checked.values()),
        completed_but_uncommitted_trial_ids=[config["id"] for config in configs if config["id"] not in checked and
            (out / "trials" / config["id"] / "receipt.json").exists()],
        completion_result_sha256=sha(out / "completion/result.json"), outcome=completion["status"])
    if len(checked) != len(configs):
        if completion["status"] == "INSUFFICIENT_COMPLETED_COVERAGE":
            assert not completion["exported"] and not completion["late_targets_loaded"]
            assert not (out / "completion/selection_frozen.json").exists()
            return {**report, "status": "PASS", "verification_status": "PASS",
                "reason": "Terminal insufficient coverage outcome checked; not all arms completed and no improvement inferred"}
        return {**report, "status": "CHECKPOINT_ONLY", "verification_status": "CHECKPOINT_ONLY",
            "reason": "Not all declared deterministic arms have committed verified results"}
    qualifying = sorted((identifier for identifier, item in checked.items() if item["eligible"]), key=lambda identifier: checked[identifier]["rank"])
    shortlist = read(out / "completion/shortlist.json")
    assert shortlist["completed"] == len(checked) and shortlist["eligible_ids"] == qualifying
    assert shortlist["selected"] == (qualifying[0] if qualifying else None) and shortlist["before_late_targets"]
    if not qualifying:
        assert completion["status"] == "NO_QUALIFYING_RECIPE" and not completion["exported"] and not completion["late_targets_loaded"]
        assert not (out / "completion/selection_frozen.json").exists()
        assert sha(root / BEST.relative_to(ROOT)) == BEST_SHA
        return {**report, "status": "PASS", "verification_status": "PASS",
            "reason": "All deterministic arms replayed and no qualifying recipe independently confirmed; no candidate exported"}
    assert completion["status"] == "EXPORTED_UNSCORED_CANDIDATE" and completion["exported"]
    selected = read(out / "completion/selection_frozen.json")
    identifier = qualifying[0]
    config = next(item for item in configs if item["id"] == identifier)
    assert selected["id"] == identifier and selected["config"] == config and selected["before_late_targets"]
    assert selected["model_sha256"] == sha(out / "trials" / identifier / "model.json")
    assert selected["result_sha256"] == checked[identifier]["result_sha256"]
    assert selected["protocol_sha256"] == report["protocol_sha256"]
    assert selected["model_path"] == str((out / "trials" / identifier / "model.json").relative_to(root))
    assert selected["no_refit_after_selection"]
    assert pd.Timestamp(models[identifier]["training"]["fit_finished_utc"]) <= pd.Timestamp(selected["created_utc"])
    selection_sha = sha(out / "completion/selection_frozen.json")
    frozen = read(out / "completion/predictions_frozen.json")
    assert frozen["selection_sha256"] == selection_sha and frozen["before_late_targets"]
    assert pd.Timestamp(selected["created_utc"]) <= pd.Timestamp(frozen["created_utc"])
    verify_mapping(out / "completion", frozen["files_sha256"])
    outputs = {}
    for name in ("latest", "test"):
        frame = pd.read_parquet(out / "data" / f"{name}.parquet")
        assert not {"y", "smp", "k", "energy", "cf"} & set(frame.columns), "Deployment input contains labels"
        replay = transport.predict(frame, config, models[identifier]["transport_model"])
        outputs[name] = aligned_output(frame, out / "completion" / f"{name}_predictions.parquet", replay, config["family"])
        report["saved_weight_prediction_replays"] += 1
    audit = read(out / "completion/audit.json")
    assert audit["selection_sha256"] == selection_sha
    assert audit["predictions_frozen_sha256"] == sha(out / "completion/predictions_frozen.json")
    assert pd.Timestamp(frozen["created_utc"]) <= pd.Timestamp(audit["created_utc"])
    labels_path = contained(root, audit["labels_source"])
    assert audit["labels_source_sha256"] == sha(labels_path) == protocol["input_sha256"][str(labels_path.relative_to(root))]
    labels = pd.read_parquet(labels_path, columns=KEYS + ["y", "smp", "k"])
    keys(labels)
    scored = outputs["latest"].merge(labels, on=KEYS, how="left", validate="one_to_one", sort=False)
    assert not scored[["y", "smp", "k"]].isna().any().any()
    pd.testing.assert_frame_equal(scored, pd.read_parquet(out / "completion/latest_scored_predictions.parquet"), check_exact=True)
    assert scored.ts.min() > RECENT_END and scored.ts.max() <= pd.Timestamp("2025-06-01", tz="Asia/Seoul")
    late_reference, late_candidate = score(scored, scored.p_reference), score(scored, scored.p)
    compare_numbers(audit["metrics"]["reference"], late_reference)
    compare_numbers(audit["metrics"]["candidate"], late_candidate)
    late_ratio = late_candidate["W"] / late_reference["W"]
    compare_numbers(audit["metrics"]["ratio"], late_ratio)
    assert audit["used_for_selection"] is False and audit["coefficients_changed"] is False and audit["real_model_fits"] == 0
    check_weekly_bootstrap(scored, audit["weekly_bootstrap"])
    if late_ratio >= 1:
        assert str(completion["recommendation"]).startswith("NOT_RECOMMENDED")
    candidate = contained(root, completion["candidate"])
    assert candidate == root / "submission/research_novel_candidate_20261108"
    candidate_sha = verify_zip(candidate, outputs["test"], root / BEST.relative_to(ROOT))
    assert completion["candidate_sha256"] == candidate_sha
    manifest = read(candidate / "manifest.json")
    if "files_sha256" in manifest:
        verify_mapping(candidate, manifest["files_sha256"])
    assert manifest.get("uploaded", False) is False
    assert manifest["selection"] == selected and manifest["late_audit"] == audit
    assert manifest["original_best_sha256"] == BEST_SHA
    assert completion["manifest_sha256"] == sha(candidate / "manifest.json")
    assert sha(root / BEST.relative_to(ROOT)) == BEST_SHA
    report.update(status="PASS", verification_status="PASS", late_targets_loaded=True,
        selected_id=identifier, selection_sha256=selection_sha, candidate=str(candidate), candidate_sha256=candidate_sha,
        descriptive_late_ratio=late_ratio, improvement_verified=True,
        improvement_scope="Frozen primary/recent development gates only; primary is fitted and all historical periods already exposed",
        reason="Saved coefficients, fixed selection, descriptive late audit and unsubmitted candidate ZIP independently checked")
    return report


def persist_terminal(result, out=OUT):
    if result["verification_status"] != "PASS":
        return None
    destination = Path(out) / "independent_completion_check.json"
    if destination.exists():
        old = read(destination)
        assert {k: v for k, v in old.items() if k != "utc"} == {k: v for k, v in result.items() if k != "utc"}, "Existing verification receipt differs"
    else:
        data = (json.dumps(result, indent=2, allow_nan=False) + "\n").encode()
        with destination.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controller-state-dir", type=Path, default=OUT / "controller_state")
    args = parser.parse_args()
    try:
        assert args.controller_state_dir.resolve() == (OUT / "controller_state").resolve()
        answer = main(args.controller_state_dir)
        persist_terminal(answer)
        print(json.dumps(answer, indent=2, allow_nan=False))
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "verification_status": "FAIL", "actual_model_fits": 0,
            "exception": type(exc).__name__, "reason": str(exc)}, indent=2))
        raise SystemExit(1)
