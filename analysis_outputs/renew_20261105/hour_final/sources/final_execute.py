"""Freeze once, confirm without tuning, then full refit and local export."""
from wave_common import ROOT, OUT, configure, digest, save_json, receipt
from final_build import DEST, OLD, CACHE, MARCH, JUNE, sidecars, enrich
from final_infer import ALPHA, WEIGHTS, STATION, inference, compose, fit_all
from final_metrics import metrics
from datetime import datetime, timezone
from pathlib import Path
import gc
import json
import shutil
import subprocess
import sys
import time
import zipfile
import numpy as np
import pandas as pd

CANDIDATE = ROOT / "submission/score_push_candidate"


def freeze() -> None:
    assert not (DEST / "freeze.json").exists()
    DEST.mkdir(exist_ok=True)
    (DEST / "cache").mkdir(exist_ok=True)
    sources = DEST / "sources"
    sources.mkdir()
    paths = list((ROOT / "submission/score_push").glob("*.py")) + list((ROOT / "submission/autoresearch").glob("*.py"))
    for path in paths:
        shutil.copyfile(path, sources / (path.parent.name + "_" + path.name))
    preserve = set()
    for root in (OUT, OLD.parent, ROOT / "analysis_outputs/award_run", ROOT / "submission/award_candidate", ROOT / "submission/autoresearch_candidate", ROOT / "submission/autoresearch"):
        preserve.update(p for p in root.rglob("*") if p.is_file() and not p.is_relative_to(DEST) and "__pycache__" not in p.parts)
    preserve.update(p for p in (ROOT / "submission/score_push").glob("*.py") if not p.name.startswith("final_"))
    preserve.update(ROOT.glob("*.csv"))
    preserve.update((ROOT / "submission").glob("*.csv"))
    development = OUT / "closing_wave/recent/selected/predictions.parquet"
    save_json(DEST / "freeze.json", {
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "recipe": {"rich_alpha": ALPHA, "refined_weights": WEIGHTS, "station_weight": STATION, "closing_weights": [1, 0, 0], "lightgbm_seeds": [None, 1, 2], "mlp_seeds": [0, 1, 2], "trees": 400, "rich_leaves": 31, "normalized_station_leaves": 63, "station_mask": "train-only constant mask refitted on full training", "mlp_mask": "none; train-only median and standard scaling"},
        "decision_rule": "No tuning, reselection, weight changes or additional model families after freeze. Confirmation is reporting only.",
        "development_recent_prediction": {"path": str(development.relative_to(ROOT)), "column": "p", "sha256": digest(development)},
        "source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in paths},
        "preserved_before_sha256": {str(p.relative_to(ROOT)): digest(p) for p in sorted(preserve)},
        "input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in [CACHE / "feat_train.parquet", CACHE / "feat_test.parquet", OLD / "outer_predictions.parquet", OLD / "full_train.parquet", OLD / "test_features.parquet", OLD / "test_labels_bu.parquet"]},
        "historical_exposure": "Development and prior historical experiments are not pristine holdout evidence; no official test score available."
    })
    print("IMMUTABLE FREEZE WRITTEN", flush=True)


def check_recent(outer: pd.DataFrame) -> None:
    comparisons = {"p_candidate": ("closing_wave/recent/selected/predictions.parquet", "p"), "rich": ("recent/rich_fixed_alpha/predictions.parquet", "p_dir"), "normalized": ("refinement_wave/recent/leaves63_trees400/ensemble/pure/predictions.parquet", "p_new"), "mlp": ("learner_wave/recent/mlp_cf/ensemble/pure/predictions.parquet", "p_new"), "station": ("profile_wave/recent/stations_lgb/ensemble/pure/predictions.parquet", "p_new")}
    evidence = {}
    for name, (path, column) in comparisons.items():
        expected = pd.read_parquet(OUT / path, columns=["ts", "grp", column]).rename(columns={column: "expected"})
        joined = outer.loc[outer.ts.le(MARCH), ["ts", "grp", name]].merge(expected, on=["ts", "grp"], validate="one_to_one")
        assert len(joined) == 13104
        np.testing.assert_allclose(joined[name], joined.expected, rtol=1e-10, atol=1e-6)
        evidence[name] = {"rows": len(joined), "max_absolute_error": float(np.max(np.abs(joined[name]-joined.expected))), "passed": True}
    save_json(DEST / "development_replay.json", evidence)


def report(outer: pd.DataFrame) -> None:
    slices = {"all": outer, "recent": outer[outer.ts.le(MARCH)], "confirmation": outer[outer.ts.gt(MARCH)], "2025_Jan_May": outer[outer.ts.gt(pd.Timestamp("2025-01-01", tz="Asia/Seoul"))]}
    monthly = {month: values for month, values in outer.groupby((outer.ts-pd.Timedelta(hours=1)).dt.strftime("%Y-%m"))}
    scores = {name: {p: metrics(rows, p) for p in ("p_previous", "p_candidate")} for name, rows in slices.items()}
    save_json(DEST / "outer_metrics.json", scores)
    pd.DataFrame([{"slice": name, "recipe": p, **metrics(rows, p)} for name, rows in {**slices, **monthly}.items() for p in ("p_previous", "p_candidate")]).to_csv(DEST / "diagnostics.csv", index=False)
    boot = {}
    for name in ("all", "confirmation", "2025_Jan_May"):
        rows = slices[name]
        weight = rows.smp*rows.k
        daily = pd.DataFrame({"day": (rows.ts-pd.Timedelta(hours=1)).dt.floor("D"), "delta": weight*((rows.p_candidate-rows.y).abs()-(rows.p_previous-rows.y).abs()), "denominator": weight*rows.y}).groupby("day").sum()
        ix = np.random.default_rng(20261104).integers(0, len(daily), size=(2000, len(daily)))
        delta = daily.delta.to_numpy()[ix].sum(axis=1)
        pct = 100*delta/daily.denominator.to_numpy()[ix].sum(axis=1)
        boot[name] = {"seed": 20261104, "replicates": 2000, "blocks": len(daily), "W_delta_95CI": np.quantile(delta, [.025,.975]).tolist(), "W_pct_delta_95CI": np.quantile(pct, [.025,.975]).tolist()}
    save_json(DEST / "bootstrap.json", boot)
    print("CONFIRMATION REPORTED", json.dumps(scores), flush=True)


def worker() -> None:
    configure()
    started = time.monotonic()
    weather, stations = sidecars("train")
    selection, names, profile_names = enrich(pd.read_parquet(OLD / "outer_features.parquet"), weather, stations)
    base = pd.read_parquet(OLD / "outer_predictions.parquet", columns=["ts", "grp", "p_bu", "p_candidate"]).rename(columns={"p_candidate": "p_previous"})
    outer = compose(base, inference(selection, names, False))
    check_recent(outer)
    labels = pd.read_parquet(OLD / "outer_predictions.parquet", columns=["ts", "grp", "y", "smp", "k", "site_count"])
    outer = outer.merge(labels, on=["ts", "grp"], validate="one_to_one")
    assert len(outer) == 17520
    outer.to_parquet(DEST / "outer_predictions.parquet", index=False)
    report(outer)
    del selection, base, labels, outer
    gc.collect()
    train, train_names, train_profile_names = enrich(pd.read_parquet(OLD / "full_train.parquet"), weather, stations)
    assert train.ts.max() <= JUNE and names == train_names and profile_names == train_profile_names
    del weather, stations
    gc.collect()
    weather, stations = sidecars("test")
    test, test_names, test_profile_names = enrich(pd.read_parquet(OLD / "test_features.parquet"), weather, stations)
    assert names == test_names and profile_names == test_profile_names and test.ts.min() > JUNE
    del weather, stations
    gc.collect()
    save_json(DEST / "features.json", {"base": names, "station_candidates": profile_names})
    fit_all(train, test, names, profile_names)
    del train
    gc.collect()
    components = inference(test, names, True)
    replay = {}
    from final_infer import locations
    for member, paths in locations(True).items():
        raws = [pd.read_parquet(p / "daylight_raw.parquet") for p in paths]
        raw = pd.concat(raws).groupby(["ts", "grp"], as_index=False).p_raw.mean()
        joined = components.merge(raw, on=["ts", "grp"], validate="one_to_one")
        np.testing.assert_allclose(joined[member], joined.p_raw.clip(lower=0), rtol=1e-10, atol=1e-6)
        replay[member] = {"passed": True, "max_absolute_error": float(np.abs(joined[member]-joined.p_raw.clip(lower=0)).max())}
    save_json(DEST / "full_model_replay.json", replay)
    prediction = compose(pd.read_parquet(OLD / "test_labels_bu.parquet"), components)
    assert len(prediction) == 17520
    prediction.to_parquet(DEST / "test_predictions.parquet", index=False)
    CANDIDATE.mkdir(exist_ok=False)
    shutil.copyfile(ROOT / "submission/autoresearch_candidate/composition.csv", CANDIDATE / "composition.csv")
    export = prediction.sort_values(["grp", "ts"])
    pd.DataFrame({"group": export.grp, "ts": export.ts.astype(str), "forecast_kwh": np.round(export.p_candidate, 3)}).to_csv(CANDIDATE / "forecast.csv", index=False)
    with zipfile.ZipFile(CANDIDATE / "submission_files.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name in ("composition.csv", "forecast.csv"):
            archive.write(CANDIDATE / name, name)
    result = subprocess.run([sys.executable, str(ROOT / "submission/validate_artifacts.py"), str(CANDIDATE), "--self-check"], capture_output=True, text=True, check=False)
    (DEST / "export_validation.log").write_text(result.stdout+result.stderr, encoding="utf-8")
    assert result.returncode == 0, result.stdout+result.stderr
    frozen = json.loads((DEST / "freeze.json").read_text())
    after = {p: digest(ROOT / p) for p in frozen["preserved_before_sha256"]}
    assert after == frozen["preserved_before_sha256"]
    save_json(DEST / "preservation.json", {"unchanged": True, "files": len(after)})
    receipt(DEST / "runtime.json", [time.monotonic()-started])
    save_json(CANDIDATE / "manifest.json", {"freeze_sha256": digest(DEST / "freeze.json"), "files_sha256": {n: digest(CANDIDATE / n) for n in ("composition.csv", "forecast.csv", "submission_files.zip")}, "models_sha256": {str(p.relative_to(DEST)): digest(p) for p in (DEST / "models").rglob("*") if p.is_file()}, "metrics": json.loads((DEST / "outer_metrics.json").read_text()), "input_sha256": frozen["input_sha256"], "recipe": frozen["recipe"]})
    (DEST / "REPRODUCTION.txt").write_text("Invocation: python submission/score_push/final_execute.py\nOne immutable freeze; saved recent models confirm without fitting; 12 sequential full fits through 2025-06-01. No post-confirmation tuning.\nEvidence: development_replay.json, outer_predictions.parquet, outer_metrics.json, bootstrap.json, full_model_replay.json, test_predictions.parquet, export_validation.log, preservation.json, runtime.json.\nNo temporary directories created. No upload or official leaderboard claim.\n", encoding="utf-8")
    print("FINAL COMPLETE", flush=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        worker()
    else:
        freeze()
        with (DEST / "run.log").open("w", encoding="utf-8") as stream:
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"], stdout=stream, stderr=subprocess.STDOUT, creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW, check=False)
        save_json(DEST / "controller_receipt.json", {"exit_code": result.returncode})
        assert result.returncode == 0, "See final/run.log"
