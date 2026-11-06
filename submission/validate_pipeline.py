# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "joblib"]
# ///
# Run: python submission/validate_pipeline.py
"""Lock a recipe on an earlier year, evaluate once, then fit the submission."""
import contextlib
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- explicitly preserve existing model interface

import make_submission as model
from award_metrics import bootstrap, metrics, report, self_check

ROOT: Final = Path(__file__).resolve().parent
OUT: Final = ROOT.parent / "analysis_outputs" / "award_run"
CANDIDATE: Final = ROOT / "award_candidate"
INNER: Final = pd.Timestamp("2023-06-01", tz=model.TZ)
WEIGHTS: Final = [0., .25, .5, .75, 1.]


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def site_predictions(train: pd.DataFrame, evaluation: pd.DataFrame) -> pd.DataFrame:
    """Fit only observed daylight rows; retain observed zero/night targets."""
    daylight = train[~train.night]
    model.log("fit pooled", len(daylight), "rows", train.ts.min(), train.ts.max())
    pools = [model.fit_pooled(daylight, seed) for seed in model.SEEDS]
    sites = model.fit_site(daylight)
    day = ~evaluation.night.to_numpy()
    predictions = np.zeros(len(evaluation), dtype=np.float64)
    predictions[day] = model.predict_bottom_up(pools, sites, evaluation[day])
    result = evaluation[["site_id", "ts"]].copy()
    result["p"] = predictions
    if "energy" in evaluation:
        result["y"] = evaluation.energy.to_numpy()
    assert np.isfinite(predictions).all() and (predictions >= 0).all()
    model.log("site predictions", len(result), "site models", len(sites))
    return result


def group_predictions(frames: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame], assignment: dict[str, str]) -> pd.DataFrame:
    """Aggregate exactly the sites whose targets exist at each evaluation hour."""
    train, evaluation, site = frames
    direct = model.predict_direct(model.fit_direct(train[~train.night], assignment),
                                  evaluation[~evaluation.night], assignment)
    aggregates = ["p"] + (["y"] if "y" in site else [])
    result = site.assign(grp=site.site_id.map(assignment)).groupby(["ts", "grp"], as_index=False)[aggregates].sum()
    result = result.rename(columns={"p": "p_bu"}).merge(direct.rename(columns={"p": "p_dir"}),
                                                       on=["ts", "grp"], how="left", validate="one_to_one")
    result["p_dir"] = result.p_dir.fillna(0.)
    return result


def main() -> None:
    self_check()
    settings = {"inner_train_end": str(INNER), "inner_selection_end": str(model.T1),
                "outer_end": str(model.T2), "weights": WEIGHTS, "seeds": model.SEEDS,
                "pool": model.POOL, "site": model.SITE, "group": model.GROUP,
                "site_weight": model.SITE_W, "missing_targets": "exclude absent generation rows, never zero-fill targets",
                "twin_missing_residuals": "zero for absent/unseen sites only in correlation matrix; not scoring"}
    inputs = sorted(p for p in Path(model.DATA).rglob("*") if p.is_file() and p.suffix in {".csv", ".parquet"})
    fingerprints = {str(p.relative_to(ROOT.parent)): digest(p) for p in inputs}
    fingerprints.update({p.name: digest(p) for p in [Path(model.__file__), Path(__file__), ROOT / "award_metrics.py", ROOT / "composition.csv"]})
    provenance = {"inputs_sha256": fingerprints, "settings": settings, "python": platform.python_version(),
                  "versions": {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "joblib"]}}
    key = hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()
    cache = OUT / "cache" / key
    cache.mkdir(parents=True, exist_ok=True)
    marker = cache / "provenance.json"
    if marker.exists():
        assert json.loads(marker.read_text(encoding="utf-8")) == provenance
        for name, expected in json.loads((cache / "feature_hashes.json").read_text()).items():
            assert digest(cache / name) == expected, "Feature cache content mismatch"
    else:
        assert not any(cache.iterdir()), "Incomplete cache: preserve for diagnosis and use a fresh directory"
        model.CACHE = str(cache)
        model.features()
        save_json(cache / "feature_hashes.json", {p.name: digest(p) for p in cache.glob("*.parquet")})
        save_json(marker, provenance)
    model.CACHE = str(cache)
    save_json(OUT / "provenance.json", {**provenance, "cache_key": key})
    data = pd.read_parquet(cache / "feat_train.parquet")
    smp = pd.read_parquet(cache / "smp.parquet")[["ts", "smp", "k"]]
    assert not data.duplicated(["site_id", "ts"]).any()
    assert np.isfinite(data.energy).all()
    inner_train = data[data.ts <= INNER]
    inner_valid = data[(data.ts > INNER) & (data.ts <= model.T1)]
    outer_train = data[data.ts <= model.T1]
    outer_valid = data[(data.ts > model.T1) & (data.ts <= model.T2)]
    assert inner_train.ts.max() < inner_valid.ts.min() <= inner_valid.ts.max() < outer_valid.ts.min()
    assert outer_train.ts.max() < outer_valid.ts.min()
    boundaries = {name: {"rows": len(rows), "start": str(rows.ts.min()), "end": str(rows.ts.max()),
                         "sites": int(rows.site_id.nunique())}
                  for name, rows in [("inner_train", inner_train), ("inner_selection", inner_valid),
                                     ("outer_train", outer_train), ("outer_validation", outer_valid)]}
    save_json(OUT / "boundaries.json", boundaries)
    coverage = data.assign(month=data.ts.dt.strftime("%Y-%m")).groupby("month").agg(
        observed_rows=("energy", "size"), hours=("ts", "nunique"), sites=("site_id", "nunique"))
    coverage["possible_site_hours"] = coverage.hours * model.N
    coverage["observed_fraction"] = coverage.observed_rows / coverage.possible_site_hours
    coverage.to_csv(OUT / "coverage.csv")
    inner_site = site_predictions(inner_train, inner_valid)
    inner_site.to_parquet(OUT / "inner_site_predictions.parquet", index=False)
    residuals = inner_site.assign(error=inner_site.p - inner_site.y).pivot(index="ts", columns="site_id", values="error")
    residuals = residuals.reindex(columns=model.IDS).fillna(0.)
    residuals = residuals[(residuals.abs().sum(axis=1) > 0)]
    split, pairs = model.twin_split(residuals.to_numpy(np.float64))
    twins = {site: "G1" if split[i] == 1 else "G2" for i, site in enumerate(model.IDS)}
    assignments = {"reference": model.ref_assign(), "inner_twins": twins}
    scores = []
    for name, assignment in assignments.items():
        group = group_predictions((inner_train, inner_valid, inner_site), assignment).merge(smp, on="ts", validate="many_to_one")
        for weight in WEIGHTS:
            group["p"] = (1 - weight) * group.p_bu + weight * group.p_dir
            scores.append({"composition": name, "direct_weight": weight, **metrics(group, "p")})
    pd.DataFrame(scores).to_csv(OUT / "inner_selection.csv", index=False)
    winner = min(scores, key=lambda row: row["W"])
    assignment = assignments[winner["composition"]]
    selected_weight = winner["direct_weight"]
    locked = {"composition": winner["composition"], "direct_weight": selected_weight,
              "selected_by": "minimum inner W only; ties prefer reference then smaller direct weight",
              "inner_metrics": winner, "assignment": assignment,
              "unseen_inner_sites": sorted(set(model.IDS) - set(inner_valid.site_id)), "twin_pairs": len(pairs)}
    save_json(OUT / "locked_configuration.json", locked)
    model.log("LOCKED", winner)
    outer_site = site_predictions(outer_train, outer_valid)
    outer_site.to_parquet(OUT / "outer_site_predictions.parquet", index=False)
    selected = group_predictions((outer_train, outer_valid, outer_site), assignment)
    selected["p_candidate"] = (1 - selected_weight) * selected.p_bu + selected_weight * selected.p_dir
    selected["p_selected50"] = .5 * selected.p_bu + .5 * selected.p_dir
    outer = selected[["ts", "grp", "y", "p_candidate", "p_selected50"]]
    original = pd.read_csv(ROOT / "composition.csv").set_index("site_id").group.to_dict()
    for name, alternate in [("reference", assignments["reference"]), ("original", original)]:
        group = group_predictions((outer_train, outer_valid, outer_site), alternate)
        group[f"p_{name}50"] = .5 * (group.p_bu + group.p_dir)
        group = group.rename(columns={"y": f"y_{name}"})
        outer = outer.merge(group[["ts", "grp", f"y_{name}", f"p_{name}50"]], on=["ts", "grp"], validate="one_to_one")
    outer = outer.merge(smp, on="ts", validate="many_to_one").rename(columns={"grp": "group"})
    outer.to_csv(OUT / "outer_predictions.csv", index=False)
    results = report(outer, OUT)
    save_json(OUT / "outer_metrics.json", results)
    save_json(OUT / "bootstrap.json", bootstrap(outer))
    model.log("OUTER", results)
    test = pd.read_parquet(cache / "feat_test.parquet")
    assert test.ts.min() > data.ts.max()
    test_site = site_predictions(data, test)
    test_site.to_parquet(OUT / "test_site_predictions.parquet", index=False)
    forecast = group_predictions((data, test, test_site), assignment)
    forecast["forecast_kwh"] = ((1 - selected_weight) * forecast.p_bu + selected_weight * forecast.p_dir).clip(lower=0).round(3)
    forecast = forecast.rename(columns={"grp": "group"}).sort_values(["group", "ts"])
    forecast["ts"] = forecast.ts.dt.strftime("%Y-%m-%d %H:%M:%S") + "+09:00"
    composition = pd.DataFrame({"site_id": model.IDS, "group": [assignment[s] for s in model.IDS]})
    capacities = composition.merge(model.SITES, on="site_id").groupby("group").capacity_kw.sum()
    assert capacities.ge(20000).all()
    assert np.isfinite(forecast.forecast_kwh).all() and forecast.forecast_kwh.ge(0).all()
    expected = pd.read_csv(Path(model.DATA) / "smp.csv").ts.tolist()
    for group in ["G1", "G2"]:
        assert len(expected) == 8760 and forecast.loc[forecast.group == group, "ts"].tolist() == expected
    CANDIDATE.mkdir(parents=True, exist_ok=True)
    composition.to_csv(CANDIDATE / "composition.csv", index=False)
    forecast[["group", "ts", "forecast_kwh"]].to_csv(CANDIDATE / "forecast.csv", index=False)
    save_json(CANDIDATE / "manifest.json", {"locked_configuration": locked, "cache_key": key,
        "capacities_kw": capacities.to_dict(), "forecast_rows": len(forecast), "outer": results,
        "files_sha256": {p.name: digest(p) for p in CANDIDATE.glob("*.csv")},
        "limitations": ["Historical recipe itself was previously explored on outer year; no absolute untouched-holdout claim",
                        "Sparse commissioned fleet; observed targets only", "Original composition outer result is contaminated diagnostic",
                        "Test labels unavailable; outer score is not competition score"]})
    save_json(OUT / "verification.json", {"scenario": "chronological selection, evaluation, full fit, export",
        "invocation": "python submission/validate_pipeline.py", "passed": True,
        "observables": {"disjoint_windows": True, "finite_predictions": True, "both_capacity_ge_20000": True,
                        "8760_keys_per_group": True, "metric_self_check": True},
        "artifacts": [str(OUT / "outer_predictions.csv"), str(CANDIDATE / "forecast.csv"), str(CANDIDATE / "manifest.json")]})
    model.log("COMPLETE", CANDIDATE)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "run.log").open("w", encoding="utf-8", buffering=1) as log:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            main()
