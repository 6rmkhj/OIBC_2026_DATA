# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "joblib"]
# ///
# Run: python submission/autoresearch/final_run.py
"""Freeze selection, evaluate outer once, then refit and export sequentially."""
import ctypes
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from common import ROOT, OUT, CACHE, SOURCE, digest, save_json

FINAL = OUT / "final"
CANDIDATE = ROOT / "submission/autoresearch_candidate"


def preserved_hashes() -> dict[str, str]:
    paths = list((ROOT / "submission/award_candidate").rglob("*"))
    paths += [ROOT / "submission/composition.csv", ROOT / "submission/forecast.csv"]
    return {str(path.relative_to(ROOT)): digest(path) for path in paths if path.is_file()}


def fit_stage(name: str, config: Path, split: str):
    import pandas as pd  # noqa: PANDAS_OK -- frozen interface
    job = FINAL / name
    job.mkdir()
    train = FINAL / ("full_train.parquet" if split == "test" else "outer_train.parquet")
    features = FINAL / f"{split}_features.parquet"
    save_json(job / "job.json", {"config": str(config), "train": str(train), "features": str(features)})
    start = time.monotonic()
    with (job / "run.log").open("w", encoding="utf-8") as log:
        result = subprocess.run([sys.executable, str(SOURCE / "final_fit.py"), str(job)], stdout=log, stderr=subprocess.STDOUT, timeout=600, creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW, check=False)
    save_json(job / "process.json", {"exit_code": result.returncode, "elapsed_seconds": time.monotonic()-start, "timeout_seconds": 600, "concurrency": 1})
    assert result.returncode == 0, f"Fit stage failed: {job / 'run.log'}"
    prediction = pd.read_parquet(job / "direct.parquet")
    keys = pd.read_parquet(features, columns=["ts", "grp"])
    check = keys.merge(prediction, on=["ts", "grp"], how="outer", validate="one_to_one", indicator=True)
    assert len(check) == len(keys) and check._merge.eq("both").all()
    assert prediction.p_dir.notna().all() and prediction.p_dir.ge(0).all()
    return prediction


def worker() -> None:
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- exact original aggregation
    import pyarrow as pa
    from final_data import PRIOR, feature_cache, load_frozen, original, prepare_outer_train, prepare_prediction
    from final_metrics import metrics, report, self_check
    pa.set_cpu_count(2)
    pa.set_io_thread_count(2)
    start = time.monotonic()
    freeze = json.loads((FINAL / "freeze.json").read_text())
    correction_path = FINAL / "diagnostic_correction.json"
    correction = json.loads(correction_path.read_text()) if correction_path.exists() else None
    expected_code = correction["corrected_code_sha256"] if correction else freeze["final_code_sha256"]
    for name, expected in expected_code.items():
        assert digest(SOURCE / name) == expected
    assert digest(Path(original.__file__)) == freeze["original_aggregation_source_sha256"]
    source = load_frozen()
    config = source.Config(**json.loads((FINAL / "config.json").read_text()))
    assert config.learner == "lightgbm" and not config.spatial
    assignment = json.loads((CACHE / "assignment.json").read_text())
    assert digest(CACHE / "assignment.json") == freeze["assignment_sha256"]
    cache_hashes = json.loads((feature_cache() / "feature_hashes.json").read_text())
    for name, expected in cache_hashes.items():
        assert digest(feature_cache() / name) == expected
    reuse = {name: digest(PRIOR / name) for name in ["outer_site_predictions.parquet", "test_site_predictions.parquet"]}
    save_json(FINAL / "input_hashes.json", {"feature_cache": cache_hashes, "bottom_up": reuse})
    self_check()
    if correction:
        assert digest(FINAL / "outer_predictions.parquet") == correction["outer_predictions_sha256_before"]
        outer = pd.read_parquet(FINAL / "outer_predictions.parquet")
        print("RESUME identical saved outer predictions; no repeated outer fits", flush=True)
    else:
        print("FROZEN; beginning outer preparation", flush=True)
        prepare_outer_train(assignment)
        prepare_prediction("outer", assignment)
        previous = fit_stage("outer_previous", FINAL / "baseline_config.json", "outer")
        selected = fit_stage("outer_selected", FINAL / "config.json", "outer")
        outer = pd.read_parquet(FINAL / "outer_labels_bu.parquet")
        outer = outer.merge(previous.rename(columns={"p_dir": "previous_direct"}), on=["ts", "grp"], how="left", validate="one_to_one")
        outer = outer.merge(selected.rename(columns={"p_dir": "candidate_direct"}), on=["ts", "grp"], how="left", validate="one_to_one").fillna({"previous_direct": 0., "candidate_direct": 0.})
        outer["p_previous"] = .5*(outer.p_bu+outer.previous_direct)
        outer["p_candidate"] = (1-config.direct_weight)*outer.p_bu+config.direct_weight*outer.candidate_direct
    assert len(outer) == 17520 and not outer.duplicated(["ts", "grp"]).any()
    assert np.isfinite(outer[["y", "p_bu", "p_previous", "p_candidate", "smp", "k"]].to_numpy()).all()
    reproduced = metrics(outer, "p_previous")
    assert abs(reproduced["W_pct"]-11.552586472040375) < 1e-7, reproduced
    fleet = outer[outer.ts > pd.Timestamp("2025-01-01", tz=original.TZ)]
    expected_sites = pd.Series(assignment).value_counts()
    assert len(fleet) == 7248 and fleet.site_count.eq(fleet.grp.map(expected_sites)).all()
    if not correction:
        outer.to_parquet(FINAL / "outer_predictions.parquet", index=False)
    report(outer, FINAL)
    print("OUTER", json.dumps(json.loads((FINAL / "outer_metrics.json").read_text())), flush=True)
    outer_finished = time.monotonic()
    # The fixed winner is refitted after evaluation without any outer-dependent choice.
    full = pd.concat([pd.read_parquet(FINAL / "outer_train.parquet"), pd.read_parquet(FINAL / "outer_as_train.parquet")], ignore_index=True)
    assert not full.duplicated(["ts", "grp"]).any()
    full.to_parquet(FINAL / "full_train.parquet", index=False)
    del full
    prepare_prediction("test", assignment)
    direct = fit_stage("full_selected", FINAL / "config.json", "test")
    forecast = pd.read_parquet(FINAL / "test_labels_bu.parquet").merge(direct, on=["ts", "grp"], how="left", validate="one_to_one").fillna({"p_dir": 0.})
    forecast["forecast_kwh"] = ((1-config.direct_weight)*forecast.p_bu+config.direct_weight*forecast.p_dir).clip(lower=0).round(3)
    assert len(forecast) == 17520 and np.isfinite(forecast.forecast_kwh).all()
    forecast = forecast.rename(columns={"grp": "group"}).sort_values(["group", "ts"])
    forecast["ts"] = forecast.ts.dt.strftime("%Y-%m-%d %H:%M:%S")+"+09:00"
    composition = pd.DataFrame({"site_id": original.IDS, "group": [assignment[site] for site in original.IDS]})
    assert len(composition) == 253
    CANDIDATE.mkdir(exist_ok=False)
    composition.to_csv(CANDIDATE / "composition.csv", index=False)
    forecast[["group", "ts", "forecast_kwh"]].to_csv(CANDIDATE / "forecast.csv", index=False)
    with zipfile.ZipFile(CANDIDATE / "submission_files.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in ["composition.csv", "forecast.csv"]:
            archive.write(CANDIDATE / name, arcname=name)
    with (FINAL / "export_validation.log").open("w", encoding="utf-8") as log:
        subprocess.run([sys.executable, str(ROOT / "submission/validate_artifacts.py"), str(CANDIDATE), "--self-check"], stdout=log, stderr=subprocess.STDOUT, check=True)
    preserved = preserved_hashes()
    assert preserved == freeze["preserved_before_sha256"]
    save_json(FINAL / "preservation.json", {"before": freeze["preserved_before_sha256"], "after": preserved, "unchanged": True})
    kernel = ctypes.windll.kernel32
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    kernel.GetPriorityClass.argtypes = [ctypes.c_void_p]
    priority = kernel.GetPriorityClass(kernel.GetCurrentProcess())
    assert priority == 0x4000
    receipt = {"elapsed_seconds": time.monotonic()-start, "through_outer_seconds": outer_finished-start, "refit_export_seconds": time.monotonic()-outer_finished, "pid": os.getpid(), "priority_class": priority, "concurrent_fit_processes": 1, "threads_per_fit": 2, "pyarrow_cpu_threads": pa.cpu_count(), "pyarrow_io_threads": pa.io_thread_count(), "validation": json.loads((FINAL / "export_validation.log").read_text()), "baseline_reproduced": reproduced, "outer_rows": len(outer), "full_fleet_rows": len(fleet)}
    save_json(FINAL / "execution_receipt.json", receipt)
    manifest = {"frozen_selection": freeze, "selection_metrics": json.loads((OUT / "trials/w5_lgb_calibrated/score.json").read_text()), "configuration": json.loads((FINAL / "config.json").read_text()), "files_sha256": {name: digest(CANDIDATE / name) for name in ["composition.csv", "forecast.csv", "submission_files.zip"]}, "models_sha256": {str(p.relative_to(FINAL)): digest(p) for p in FINAL.glob("*/*.txt")}, "input_hashes": json.loads((FINAL / "input_hashes.json").read_text()), "outer_metrics": json.loads((FINAL / "outer_metrics.json").read_text()), "splits": {"selection": "2023-06-01 < ts <= 2024-06-01 KST", "outer_train": "ts <= 2024-06-01 KST", "outer": "2024-06-01 < ts <= 2025-06-01 KST", "full_train": "ts <= 2025-06-01 KST", "test": "2025-06-01 < ts <= 2026-06-01 KST"}, "versions": {name: importlib.metadata.version(name) for name in ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "joblib"]}, "execution": receipt, "limitations": ["Adaptive inner-selection search and calibrated blend; outer not used for further tuning", "Historical baseline and assignment were previously explored; no pristine holdout claim", "Observed-site historical coverage; strict full-fleet January-May sensitivity reported separately", "Missing generation rows excluded, never zero-imputed", "Competition test labels unavailable"]}
    if correction:
        unchanged = digest(FINAL / "outer_predictions.parquet") == correction["outer_predictions_sha256_before"]
        assert unchanged
        manifest["diagnostic_correction"] = {**correction, "outer_predictions_sha256_after": digest(FINAL / "outer_predictions.parquet"), "outer_unchanged": unchanged}
    save_json(CANDIDATE / "manifest.json", manifest)
    print("COMPLETE", json.dumps(receipt), flush=True)


def main() -> None:
    from evaluate import verify_frozen
    verify_frozen()
    assert json.loads((OUT / "best.json").read_text())["id"] == "w5_lgb_calibrated"
    files = ["final_run.py", "final_data.py", "final_fit.py", "final_metrics.py"]
    resume = sys.argv[1:] == ["--resume"]
    if resume:
        assert not (FINAL / "diagnostic_correction.json").exists(), "A diagnostic correction is already recorded"
        freeze = json.loads((FINAL / "freeze.json").read_text())
        assert digest(FINAL / "train_snapshot.py") == freeze["current_snapshot_sha256"]
        assert digest(FINAL / "config.json") == freeze["config_sha256"]
        shutil.copy2(FINAL / "run.log", FINAL / "failed_run.log")
        shutil.copy2(FINAL / "controller_receipt.json", FINAL / "failed_controller_receipt.json")
        corrected = FINAL / "corrected_sources"
        corrected.mkdir()
        for name in files:
            shutil.copy2(SOURCE / name, corrected / name)
        save_json(FINAL / "diagnostic_correction.json", {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "reason": "Pandas GroupBy keys mapping conversion failed; use explicit month comprehension and resume saved outer predictions", "original_code_sha256": freeze["final_code_sha256"], "corrected_code_sha256": {name: digest(SOURCE / name) for name in files}, "outer_predictions_sha256_before": digest(FINAL / "outer_predictions.parquet"), "model_config_unchanged": True, "outer_refits": 0})
    else:
        FINAL.mkdir(exist_ok=False)
        shutil.copy2(SOURCE / "train.py", FINAL / "train_snapshot.py")
        shutil.copy2(OUT / "trials/w5_lgb_calibrated/config.json", FINAL / "config.json")
        shutil.copy2(OUT / "trials/baseline/config.json", FINAL / "baseline_config.json")
        shutil.copy2(OUT / "trials/w5_lgb_calibrated/train.py", FINAL / "selected_fitted_parent_source.py")
        sources = FINAL / "sources"
        sources.mkdir()
        for name in files:
            shutil.copy2(SOURCE / name, sources / name)
        freeze = {"frozen_at_utc": datetime.now(timezone.utc).isoformat(), "winner": "w5_lgb_calibrated", "outer_decision_rule": "No tuning or reselection after this freeze", "current_snapshot_sha256": digest(FINAL / "train_snapshot.py"), "selected_fitted_parent_source_sha256": digest(FINAL / "selected_fitted_parent_source.py"), "config_sha256": digest(FINAL / "config.json"), "assignment_sha256": digest(CACHE / "assignment.json"), "scientific_manifest_sha256": digest(CACHE / "manifest.json"), "original_aggregation_source_sha256": digest(ROOT / "submission/make_submission.py"), "final_code_sha256": {name: digest(SOURCE / name) for name in files}, "preserved_before_sha256": preserved_hashes(), "resource_policy": json.loads((OUT / "resource_policy.json").read_text())}
        save_json(FINAL / "freeze.json", freeze)
    env = os.environ.copy()
    temp = Path("C:/Users/slowg/AppData/Local/Temp/oibc-autoresearch-rkFdavwf/engine/final")
    temp.mkdir(parents=True, exist_ok=True)
    env.update({"TMPDIR": str(temp), "TMP": str(temp), "TEMP": str(temp), "NODE_COMPILE_CACHE": str(temp / "node"), "BUN_INSTALL_CACHE_DIR": str(temp / "bun"), "OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"})
    start = time.monotonic()
    with (FINAL / "run.log").open("w", encoding="utf-8") as log:
        result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"], env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW, check=False)
    prior_seconds = json.loads((FINAL / "failed_controller_receipt.json").read_text())["elapsed_seconds"] if resume else 0
    save_json(FINAL / "controller_receipt.json", {"exit_code": result.returncode, "elapsed_seconds": time.monotonic()-start, "prior_attempt_seconds": prior_seconds, "combined_process_seconds": time.monotonic()-start+prior_seconds, "resumed": resume, "worker_concurrency": 1})
    assert result.returncode == 0, f"Final worker failed: {FINAL / 'run.log'}"


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        worker()
    else:
        main()
