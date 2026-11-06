# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "joblib"]
# ///
# Run: python submission/score_push/run.py (one sequential, below-normal process)
"""Bounded richer-issued-weather family using the frozen predictor/evaluator."""
import os
for name, value in {"OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"}.items():
    os.environ[name] = value
import ctypes
from ctypes import wintypes
ctypes.windll.kernel32.GetCurrentProcess.restype = wintypes.HANDLE
ctypes.windll.kernel32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
ctypes.windll.kernel32.GetPriorityClass.argtypes = [wintypes.HANDLE]
import importlib.util
import json
from dataclasses import asdict, replace
from pathlib import Path
import shutil
import sys
import time
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact frozen numerical/model interface
import pyarrow as pa
from features import OLD, OUT, ROOT, build, trajectory
from check_features import main as self_check

sys.path.insert(0, str(ROOT / "submission/autoresearch"))
from common import digest, save_json
import evaluate
from calibrate import optimal_weight


def trial(config, train: pd.DataFrame, selection: pd.DataFrame, extra: list[str], predictor, best: float = float("inf")) -> float:
    """Fit one configuration; freeze models, raw predictions, score and diagnostics."""
    directory = OUT / "trials" / config.id
    directory.mkdir(parents=True, exist_ok=False)
    save_json(directory / "config.json", asdict(config))
    predictor.BASE_FEATURES = tuple(json.loads((OLD / "features.json").read_text())) + tuple(extra)
    save_json(directory / "features.json", list(predictor.BASE_FEATURES))
    started = time.monotonic()
    prediction, models, timings = predictor.predict_frames(train, selection, config)
    keys = pd.read_parquet(OLD / "selection_labels.parquet", columns=["ts", "grp"])
    assert len(keys) == 17568
    prediction = keys.merge(prediction, on=["ts", "grp"], how="left", validate="one_to_one").fillna({"p_dir": 0.})
    assert np.isfinite(prediction.p_dir).all()
    prediction.to_parquet(directory / "predictions.parquet", index=False)
    for name, model in models.items():
        assert model.n_jobs == 2
        model.booster_.save_model(str(directory / f"{name}.txt"))
    score = evaluate.evaluate(directory, config.direct_weight)
    save_json(directory / "runtime.json", {"fit_seconds": timings, "total_seconds": time.monotonic()-started, "pid": os.getpid(), "priority_class": ctypes.windll.kernel32.GetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess()), "parallel_fits": 1, "model_n_jobs": 2, "environment": {n: os.environ[n] for n in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}, "pyarrow_cpu": pa.cpu_count(), "pyarrow_io": pa.io_thread_count()})
    with (OUT / "journal.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"id": config.id, **score, "direct_weight": config.direct_weight, "seeds": config.seeds, "decision": "keep" if score["W_pct"] < best else "discard", "improves_incumbent": score["W_pct"] < 12.695950143757269, "model_fits": len(models), "source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in Path(__file__).parent.glob("*.py")}, "predictions_sha256": digest(directory / "predictions.parquet")}) + "\n")
    print(config.id, score, timings, flush=True)
    return score["W_pct"]


def main() -> None:
    assert ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    pa.set_cpu_count(2)
    pa.set_io_thread_count(2)
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / "journal.jsonl").exists(), "Run already exists; never overwrite trials"
    sources = OUT / "sources"
    sources.mkdir(exist_ok=True)
    for path in Path(__file__).parent.glob("*.py"):
        shutil.copyfile(path, sources / path.name)
    snapshot = ROOT / "analysis_outputs/autoresearch_20261103/final/train_snapshot.py"
    shutil.copyfile(snapshot, sources / "train_snapshot.py")
    for name in ("common.py", "evaluate.py", "calibrate.py"):
        shutil.copyfile(ROOT / "submission/autoresearch" / name, sources / name)
    spec = importlib.util.spec_from_file_location("push_frozen_predictor", sources / "train_snapshot.py")
    assert spec is not None and spec.loader is not None
    predictor = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = predictor
    spec.loader.exec_module(predictor)
    evaluate.verify_frozen()
    evaluate.self_check()
    self_check()
    original = predictor.Config(**json.loads((ROOT / "analysis_outputs/autoresearch_20261103/final/config.json").read_text()))
    train = pd.read_parquet(OLD / "train.parquet")
    selection = pd.read_parquet(OLD / "selection_features.parquet")
    cutoff = pd.Timestamp("2023-06-01", tz="Asia/Seoul")
    end = pd.Timestamp("2024-06-01", tz="Asia/Seoul")
    assert train.ts.max() <= cutoff < selection.ts.min() and selection.ts.max() <= end
    baseline = replace(original, id="baseline_exact", parent_id=original.id, hypothesis="Exact primary incumbent reproduction before new features")
    score = trial(baseline, train, selection, [], predictor)
    frozen = pd.read_parquet(ROOT / "analysis_outputs/autoresearch_20261103/trials/w5_lgb_calibrated/predictions.parquet")
    replay = pd.read_parquet(OUT / "trials/baseline_exact/predictions.parquet")
    pd.testing.assert_frame_equal(frozen, replay, check_exact=True)
    assert abs(score-12.695950143757269) < 1e-7
    save_json(OUT / "baseline_exact.json", {"prediction_values_exact": True, "W_pct": score, "original_prediction_sha256": digest(ROOT / "analysis_outputs/autoresearch_20261103/trials/w5_lgb_calibrated/predictions.parquet"), "snapshot_sha256": digest(snapshot)})
    sidecar, families, inputs = build()
    frames = []
    for frame in (train, selection):
        joined = frame.merge(sidecar, on=["ts", "grp"], how="left", validate="one_to_one", indicator=True)
        assert joined._merge.eq("both").all() and len(joined) == len(frame)
        frames.append(joined.drop(columns="_merge"))
    train, selection = frames
    assert len(sidecar) == len(train)+len(selection)
    for frame in frames:
        frame["phys_humidity_clear"] = frame.wa_humidity * frame.csa
        frame["phys_dew_spread"] = frame.wb_temp - frame.wb_dew_point
        frame["phys_uv_clear"] = frame.wb_uv_idx * frame.csb
    physics = [name for name in selection if name.startswith("phys_")]
    train, selection = trajectory(train), trajectory(selection)
    trajectories = [name for name in selection if name.startswith("traj_")]
    train.to_parquet(OUT / "cache/train.parquet", index=False)
    selection.to_parquet(OUT / "cache/selection.parquet", index=False)
    inputs += [OLD / name for name in ("train.parquet", "selection_features.parquet", "selection_labels.parquet", "features.json", "manifest.json")]
    save_json(OUT / "cache/manifest.json", {"inputs_sha256": {str(p.relative_to(ROOT)): digest(p) for p in inputs}, "cache_sha256": {p.name: digest(p) for p in (OUT / "cache").glob("*.parquet")}, "source_sha256": {p.name: digest(p) for p in sources.glob("*.py")}, "families": families, "physics": physics, "trajectory": trajectories, "coverage_keys": len(sidecar), "train_rows": len(train), "selection_daylight_rows": len(selection), "train_end": str(cutoff), "selection_end": str(end), "round_policy": "Raw round17 new fields; independent round10 means and raw17-minus10; available-capacity weighted; all-missing NaN", "evaluation_label_sha256": digest(OLD / "selection_labels.parquet")})
    combined = families["expanded"] + families["rounds"]
    hypotheses = [("expanded17", families["expanded"]), ("bothround_core", families["rounds"]), ("combined", combined), ("combined_physics", combined+physics), ("combined_trajectory", combined+physics+trajectories)]
    results = [(score, baseline, [])]
    for name, extra in hypotheses:
        config = replace(original, id=name, parent_id=baseline.id, hypothesis=f"Richer issued-weather family: {name}; fixed incumbent blend")
        results.append((trial(config, train, selection, extra, predictor, min(item[0] for item in results)), config, extra))
    winner = min(results, key=lambda item: item[0])
    if winner[0] < score:
        config = replace(winner[1], id="capacity63_600", parent_id=winner[1].id, hypothesis="Conditional capacity followup on improving features", num_leaves=63, n_estimators=600)
        results.append((trial(config, train, selection, winner[2], predictor, winner[0]), config, winner[2]))
    winner = min(results, key=lambda item: item[0])
    labels = pd.read_parquet(OLD / "selection_labels.parquet")
    winning_predictions = pd.read_parquet(OUT / "trials" / winner[1].id / "predictions.parquet")
    aligned = evaluate.align(winning_predictions, labels)
    alpha = optimal_weight(aligned, winner[1].direct_weight)
    calibrated = OUT / "trials/winner_calibrated"
    calibrated.mkdir(exist_ok=False)
    shutil.copyfile(OUT / "trials" / winner[1].id / "predictions.parquet", calibrated / "predictions.parquet")
    config = replace(winner[1], id="winner_calibrated", parent_id=winner[1].id, direct_weight=alpha, hypothesis="One analytical weighted-median blend on selection only; no model refit")
    save_json(calibrated / "config.json", asdict(config))
    calibrated_score = evaluate.evaluate(calibrated, alpha)
    shutil.copyfile(OUT / "trials" / winner[1].id / "features.json", calibrated / "features.json")
    save_json(calibrated / "calibration.json", {"model_fits": 0, "method": "frozen calibrate.optimal_weight", "source_trial": winner[1].id, "alpha": alpha})
    with (OUT / "journal.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"id": config.id, **calibrated_score, "direct_weight": alpha, "model_fits": 0, "decision": "keep" if calibrated_score["W_pct"] < winner[0] else "discard", "predictions_sha256": digest(calibrated / "predictions.parquet"), "config_sha256": digest(calibrated / "config.json"), "features_sha256": digest(calibrated / "features.json"), "calibrator_sha256": digest(sources / "calibrate.py")}) + "\n")
    save_json(OUT / "ranking.json", {"ranking_fixed_alpha": [{"id": c.id, "W_pct": s, "features": f} for s,c,f in sorted(results, key=lambda item: item[0])], "winner_fixed_alpha": winner[1].id, "calibrated": {"alpha": alpha, **calibrated_score}, "outer_evaluated": False, "test_loaded": False})
    print("COMPLETE", winner[1].id, calibrated_score, "alpha", alpha, flush=True)


if __name__ == "__main__":
    main()
