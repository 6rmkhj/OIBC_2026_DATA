"""Descriptive terminal audit of committed predictions. Never fit or select.

This helper reads saved outputs only after the pinned independent verifier's
process identity gate confirms termination. Its new audit file cannot alter
selected coefficients, development gates, shortlist, or candidate artifacts.
"""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

os.environ.update(OMP_NUM_THREADS="4", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1")
sys.dont_write_bytecode = True
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis_outputs/research_novel_20261108"
KEYS = ["ts", "grp"]


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def pinned_verifier(root, protocol):
    name = "submission/score_push_novel/verify_completion.py"
    path = root / name
    assert sha(path) == protocol["source_sha256"][name]
    spec = importlib.util.spec_from_file_location("novel_audit_pinned_verifier", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def statistics(frame):
    values = frame[["p_reference", "p", "y", "smp", "k"]].to_numpy(float)
    assert np.isfinite(values).all()
    reference, candidate, target, price, factor = values.T
    weights = price * factor
    assert (weights >= 0).all()
    b = float(np.sum(weights * np.abs(reference - target)))
    c = float(np.sum(weights * np.abs(candidate - target)))
    denominator = float(np.sum(weights * target))
    revenue = float(np.sum(price * target))
    return {"rows": len(frame), "reference_W": b, "candidate_W": c, "delta_W": c-b,
            "relative_W_change_pct": 100*(c/b-1) if b > 0 else None,
            "reference_W_pct": 100*b/denominator if denominator > 0 else None,
            "candidate_W_pct": 100*c/denominator if denominator > 0 else None,
            "reference_S": revenue-.1*b, "candidate_S": revenue-.1*c,
            "zero_reference_error": b == 0, "positive_change_means_worse": True}


def paired_week_bootstrap(frame, replicates=2000, seed=20261108):
    weeks = (frame.ts.dt.tz_localize(None)-pd.Timedelta(hours=1)).dt.to_period("W-SUN")
    weights = frame.smp.to_numpy(float)*frame.k.to_numpy(float)
    b = weights*np.abs(frame.p_reference.to_numpy(float)-frame.y.to_numpy(float))
    c = weights*np.abs(frame.p.to_numpy(float)-frame.y.to_numpy(float))
    totals = pd.DataFrame({"week": weeks, "reference": b, "candidate": c}).groupby("week")[["reference", "candidate"]].sum().to_numpy()
    assert len(totals) > 0
    rng = np.random.default_rng(seed)
    counts = rng.multinomial(len(totals), np.full(len(totals), 1/len(totals)), size=replicates)
    samples = counts @ totals
    valid = samples[:, 0] > 0
    changes = 100*(samples[valid, 1]/samples[valid, 0]-1)
    ci = [float(x) for x in np.quantile(changes, [.025, .975])] if len(changes) else None
    return {"weeks": len(totals), "replicates": replicates, "valid_replicates": int(valid.sum()), "random_seed": seed,
            "CI95_relative_W_change_pct": ci, "zero_in_CI": bool(ci[0] <= 0 <= ci[1]) if ci else None,
            "sampling_unit": "KST hour-ending whole calendar week; identical blocks for G1/G2 and reference/candidate",
            "selection_use": False, "conditional_on_fitted_coefficients_and_development_selection": True,
            "not_adjusted_for_twelve_arm_search": True}


def joined_features(saved, features):
    assert not saved.duplicated(KEYS).any() and not features.duplicated(KEYS).any()
    assert saved.ts.dt.tz is not None
    result = saved.merge(features[KEYS + ["wa_cloud"]], on=KEYS, how="left", sort=False, validate="one_to_one")
    assert len(result) == len(saved)
    # These are fixed descriptive bins, never learned from target/error values.
    cloud = result.wa_cloud.to_numpy(float)
    weather = np.where(np.isnan(cloud), "missing_forecast", np.where(cloud <= 20, "clear_le20", np.where(cloud <= 80, "mixed_20_to80", "overcast_gt80")))
    result["weather"] = np.where(result.night.to_numpy(bool), "night", weather)
    local = result.ts.dt.tz_convert("Asia/Seoul").dt.tz_localize(None)-pd.Timedelta(hours=1)
    result["month"] = local.dt.to_period("M").astype(str)
    return result


def summarize(saved, features):
    data = joined_features(saved, features)
    slices = {}
    for name, columns in (("month", ["month"]), ("group", ["grp"]), ("weather", ["weather"]), ("month_group", ["month", "grp"])):
        rows = []
        for key, part in data.groupby(columns, sort=True, dropna=False):
            key = key if isinstance(key, tuple) else (key,)
            rows.append({"slice": dict(zip(columns, map(str, key))), **statistics(part)})
        slices[name] = rows
    return {"overall": statistics(data), "slices": slices, "weekly_block_bootstrap": paired_week_bootstrap(data),
            "weather_definition": "wa_cloud forecast <=20 clear, (20,80] mixed, >80 overcast; missing forecast separate; night separate",
            "month_definition": "KST hour-ending timestamp minus one hour"}


def run(root=ROOT, out=OUT):
    root, out = Path(root), Path(out)
    protocol_path = out / "protocol.json"
    protocol = read(protocol_path)
    verifier = pinned_verifier(root, protocol)
    terminal, gate, _ = verifier.terminal_gate(out / "controller_state", root=root, out=out)
    if not terminal:
        return {"status": "CHECKPOINT_ONLY", "reason": gate.get("reason"), "data_read": False, "model_fits": 0}
    verification_path = out / "independent_completion_check.json"
    verification = read(verification_path)
    assert verification["verification_status"] == "PASS"
    assert verification["protocol_sha256"] == sha(protocol_path)
    verifier.verify_mapping(root, protocol["source_sha256"])
    verifier.verify_mapping(root, protocol["input_sha256"])
    verifier.verify_mapping(out / "data", protocol["prepared_data_sha256"])
    assert sha(out / "configs.json") == protocol["configs_sha256"]
    pins = {str(protocol_path.relative_to(root)): sha(protocol_path), str(verification_path.relative_to(root)): sha(verification_path),
            str(Path(__file__).resolve().relative_to(ROOT)): sha(Path(__file__)),
            str((out / "configs.json").relative_to(root)): sha(out / "configs.json")}
    for mapping in (protocol["input_sha256"], protocol["source_sha256"]):
        pins.update(mapping)
    features = {name: pd.read_parquet(out / "data" / (name + ".parquet"), columns=KEYS + ["wa_cloud"]) for name in ("primary", "recent")}
    for name, expected in protocol["prepared_data_sha256"].items():
        pins[str((out / "data" / name).relative_to(root))] = expected
    records, missing = [], []
    configs = read(out / "configs.json")
    for config in configs:
        folder = out / "trials" / config["id"]
        if not (folder / "result.json").exists():
            missing.append(config["id"])
            continue
        result, receipt = read(folder / "result.json"), read(folder / "receipt.json")
        assert result["id"] == config["id"] and result["config"] == config and result["status"] == "PASS"
        assert sha(folder / "receipt.json") == result["receipt_sha256"]
        assert receipt["protocol_sha256"] == sha(protocol_path)
        verifier.verify_mapping(folder, receipt["files_sha256"])
        for name in ("result.json", "receipt.json", *receipt["files_sha256"]):
            pins[str((folder / name).relative_to(root))] = sha(folder / name)
        folds = {name: summarize(pd.read_parquet(folder / (name + ".parquet")), features[name]) for name in ("primary", "recent")}
        records.append({"id": config["id"], "config": config, "eligible_under_frozen_gates": result["eligible"], "folds": folds})
    completion_path = out / "completion/result.json"
    completion = read(completion_path)
    assert verification["completion_result_sha256"] == sha(completion_path)
    assert completion["completed_trials"] == len(records)
    verifier.verify_mapping(out / "completion", completion["files_sha256"])
    pins[str(completion_path.relative_to(root))] = sha(completion_path)
    late = None
    if completion.get("exported"):
        folder = out / "completion"
        selected, frozen, old_audit = (read(folder / name) for name in ("selection_frozen.json", "predictions_frozen.json", "audit.json"))
        assert selected["id"] == completion["selected_id"] and selected["before_late_targets"] and frozen["before_late_targets"]
        assert old_audit["selection_sha256"] == frozen["selection_sha256"] == sha(folder / "selection_frozen.json")
        assert old_audit["predictions_frozen_sha256"] == sha(folder / "predictions_frozen.json")
        assert old_audit["latest_scored_predictions_sha256"] == sha(folder / "latest_scored_predictions.parquet")
        verifier.verify_mapping(folder, completion["files_sha256"])
        for name in completion["files_sha256"]:
            pins[str((folder / name).relative_to(root))] = sha(folder / name)
        late_features = pd.read_parquet(out / "data/latest.parquet", columns=KEYS + ["wa_cloud"])
        late = {"id": selected["id"], "summary": summarize(pd.read_parquet(folder / "latest_scored_predictions.parquet"), late_features),
                "already_scored_saved_labels_only": True, "used_for_selection": False}
    # Detect concurrent edits before writing a new immutable audit artifact.
    for name, expected in pins.items():
        path = root / name
        assert sha(path) == expected, name
    stamp = datetime.now(timezone.utc)
    answer = {"status": "PASS", "created_utc": stamp.isoformat(), "model_fits": 0, "predictions_computed": 0,
              "completed_trial_count": len(records), "missing_trial_ids": missing, "source_and_input_sha256": pins,
              "trials": records, "selected_late": late, "selection_changed": False, "coefficients_changed": False,
              "primary_is_fitted_in_sample": True, "recent_is_development_selection": True,
              "all_historical_periods_previously_exposed": True, "period_overlap": True,
              "official_improvement_verified": False,
              "interpretation": "Descriptive sensitivity only. Primary is fitted; recent selected among twelve arms; intervals condition on fixed coefficients and selection. CI containing zero cannot establish stable improvement."}
    destination = out / "audits" / ("saved_prediction_audit_" + stamp.strftime("%Y%m%dT%H%M%S%fZ") + ".json")
    destination.parent.mkdir(exist_ok=True)
    with destination.open("x") as stream:
        json.dump(answer, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    return {"status": "PASS", "audit": str(destination), "sha256": sha(destination), "completed_trial_count": len(records), "late_audit_included": late is not None, "model_fits": 0, "predictions_computed": 0}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, allow_nan=False))
