"""Frozen chronological data for the bounded OIBC research campaign.

Only observed labels at or before 2025-03-01 KST are read during search
preparation. The March--May 2025 audit remains outside this module's search
tables. Existing source files are never modified, and no estimator is fitted.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis_outputs/research_10h_20261107"
DATA = OUT / "data"
SEARCH_END = "2025-03-01"
FOLDS = {
    "early2022": {"origin": "2022-06-01", "end": "2023-06-01"},
    "primary": {"origin": "2023-06-01", "end": "2024-06-01"},
    "winter": {"origin": "2023-12-01", "end": "2024-12-01"},
    "spring": {"origin": "2024-03-01", "end": "2025-03-01"},
    "recent": {"origin": "2024-06-01", "end": "2025-03-01"},
}
KEYS = ["ts", "grp"]
FULL_FEATURES = ROOT / "analysis_outputs/renew_20261107/runtime_inputs/test_train.parquet"
FEATURE_SPEC = ROOT / "analysis_outputs/score_push_gpu_20261104/data/primary/features.json"
SITE_LABELS = ROOT / "submission/cache/feat_train.parquet"
SMP = ROOT / "submission/cache/smp.parquet"
ASSIGNMENT = ROOT / "analysis_outputs/autoresearch_20261103/cache/assignment.json"
STATIC_CAPACITY = ROOT / "analysis_outputs/renew_20261105/final/static_capacity.json"
REFERENCE = ROOT / "analysis_outputs/renew_20261106/shift_wave/data"
BEST_ZIP = ROOT / "submission/renew_candidate_20261105/submission_files.zip"
BEST_SHA = "ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434"


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def kst(value: str) -> pd.Timestamp:
    return pd.Timestamp(value, tz="Asia/Seoul")


def assert_keys(frame: pd.DataFrame) -> None:
    assert frame[KEYS].notna().all().all()
    assert not frame.duplicated(KEYS).any()


def checked_join(left: pd.DataFrame, right: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Add a complete one-to-one sidecar without changing left key order."""
    assert_keys(left)
    assert_keys(right)
    result = left.merge(right[KEYS + columns], on=KEYS, how="left", sort=False,
                        validate="one_to_one", indicator=True)
    pd.testing.assert_frame_equal(result[KEYS], left[KEYS].reset_index(drop=True), check_exact=True)
    assert result._merge.eq("both").all()
    return result.drop(columns="_merge")


def current_sources() -> dict[str, str]:
    files = [FULL_FEATURES, FEATURE_SPEC, SITE_LABELS, SMP, ASSIGNMENT,
             STATIC_CAPACITY, BEST_ZIP, Path(__file__)]
    files += [REFERENCE / fold / "labels.parquet" for fold in ("primary", "recent")]
    return {str(path.relative_to(ROOT)): sha(path) for path in files}


def verify_ready(directory: Path = DATA) -> dict:
    manifest = read(directory / "manifest.json")
    assert manifest["status"] == "PASS" and manifest["folds"] == FOLDS
    assert manifest["search_end_kst"] == str(kst(SEARCH_END))
    assert current_sources() == manifest["source_sha256"], "Search inputs/source changed"
    assert sha(BEST_ZIP) == BEST_SHA
    for name, expected in manifest["data_sha256"].items():
        path = directory / name
        assert path.resolve().is_relative_to(directory.resolve())
        assert sha(path) == expected, name
    return manifest


def _prepare(staging: Path) -> None:
    pa.set_cpu_count(2)
    pa.set_io_thread_count(2)
    source_hashes = current_sources()
    assert source_hashes[str(BEST_ZIP.relative_to(ROOT))] == BEST_SHA
    end = kst(SEARCH_END)
    filters = [("ts", "<=", end)]
    specification = read(FEATURE_SPEC)
    rich, station = specification["rich"], specification["station"]
    assert len(rich) == len(set(rich)) == 100
    assert len(station) == len(set(station)) == 904 and set(rich) <= set(station)
    assert not {"cf", "energy", "y", "smp", "k", "ts", "grp", "capacity_kw"} & set(station)
    reads = []

    # Even the label-free projection is bounded to the search window. CF is a
    # separate projected read with the SAME Arrow predicate, never a full file read.
    columns = [*KEYS, "capacity_kw", *station]
    features = pq.read_table(FULL_FEATURES, columns=columns, filters=filters).to_pandas()
    cf = pq.read_table(FULL_FEATURES, columns=[*KEYS, "cf"], filters=filters).to_pandas()
    reads.extend([{"source": str(FULL_FEATURES.relative_to(ROOT)), "columns": columns,
                   "filters": [["ts", "<=", str(end)]], "target_columns": [], "rows": len(features)},
                  {"source": str(FULL_FEATURES.relative_to(ROOT)), "columns": [*KEYS, "cf"],
                   "filters": [["ts", "<=", str(end)]], "target_columns": ["cf"], "rows": len(cf)}])
    assert_keys(features)
    assert features.ts.max() <= end and features.capacity_kw.gt(0).all()
    features = checked_join(features, cf, ["cf"])
    assert np.isfinite(features.cf).all()
    assert not np.isinf(features[station].to_numpy()).any()
    assert len(features) == 37743

    # Energy is aggregated over ALL reporting sites, including locally night
    # sites. The daylight model's energy/CF is intentionally not used as y.
    site = pq.read_table(SITE_LABELS, columns=["ts", "site_id", "energy", "night"], filters=filters).to_pandas()
    reads.append({"source": str(SITE_LABELS.relative_to(ROOT)),
                  "columns": ["ts", "site_id", "energy", "night"],
                  "filters": [["ts", "<=", str(end)]], "target_columns": ["energy"], "rows": len(site)})
    assert site.ts.max() <= end and not site.duplicated(["ts", "site_id"]).any()
    assert np.isfinite(site.energy).all() and site.night.notna().all()
    assignment, capacities = read(ASSIGNMENT), read(STATIC_CAPACITY)
    assert len(assignment) == 253 and set(assignment.values()) == {"G1", "G2"}
    site["grp"] = site.site_id.map(assignment)
    assert site.grp.notna().all()
    labels = site.groupby(KEYS, as_index=False, sort=True).agg(y=("energy", "sum"), night=("night", "all"))
    del site
    assert_keys(labels)
    prices = pq.read_table(SMP, columns=["ts", "smp", "k"], filters=filters).to_pandas()
    reads.append({"source": str(SMP.relative_to(ROOT)), "columns": ["ts", "smp", "k"],
                  "filters": [["ts", "<=", str(end)]], "target_columns": ["smp", "k"], "rows": len(prices)})
    assert not prices.ts.duplicated().any()
    labels = labels.merge(prices, on="ts", how="left", sort=False, validate="many_to_one")
    assert np.isfinite(labels[["y", "smp", "k"]].to_numpy()).all()
    labels = labels.merge(features[KEYS + ["capacity_kw"]], on=KEYS, how="left", sort=False,
                          validate="one_to_one", indicator=True)
    assert labels._merge.eq("left_only").equals(labels.night)
    labels["daylight"] = ~labels.night
    labels["static_capacity"] = labels.grp.map(capacities)
    labels = labels.drop(columns="_merge")
    assert labels.capacity_kw.notna().equals(labels.daylight)
    assert labels.static_capacity.gt(0).all()
    features = checked_join(features, labels, ["y", "smp", "k"])
    labels.to_parquet(staging / "search_labels.parquet", index=False)
    features.to_parquet(staging / "search_features.parquet", index=False)
    save(staging / "features.json", {"rich": rich, "station": station,
         "static_capacity": capacities, "search_end": str(end),
         "scoring_target": "Observed float32 energy summed over every reporting assigned site, including night sites",
         "training_cf": "Original daylight aggregate CF; differs slightly from all-site y/capacity at twilight",
         "night_capacity_semantics": "capacity_kw is NaN on all-night rows because it comes from the daylight feature table; static_capacity remains defined",
         "missing_generation_semantics": "No timestamp reindexing and no zero filling; only observed source rows are aggregated"})

    records = []
    for name, dates in FOLDS.items():
        origin, limit = kst(dates["origin"]), kst(dates["end"])
        assert origin < limit <= end
        train = features.loc[features.ts.le(origin)].reset_index(drop=True)
        evaluation = features.loc[features.ts.gt(origin) & features.ts.le(limit), columns].reset_index(drop=True)
        truth = labels.loc[labels.ts.gt(origin) & labels.ts.le(limit)].reset_index(drop=True)
        assert len(train) > 0 and len(evaluation) > 0 and len(truth) > 0
        assert train.ts.max() <= origin < evaluation.ts.min() <= evaluation.ts.max() <= limit
        assert not {"cf", "energy", "y", "smp", "k"} & set(evaluation)
        joined = truth[KEYS + ["night"]].merge(evaluation[KEYS], on=KEYS, how="outer", validate="one_to_one", indicator=True)
        assert joined._merge.eq("left_only").equals(joined.night)
        reference_check = None
        if name in ("primary", "recent"):
            reference = pq.read_table(REFERENCE / name / "labels.parquet",
                                     columns=[*KEYS, "y", "smp", "k", "p_reference"],
                                     filters=[("ts", ">", origin), ("ts", "<=", limit)]).to_pandas()
            reads.append({"source": str((REFERENCE / name / "labels.parquet").relative_to(ROOT)),
                          "columns": [*KEYS, "y", "smp", "k", "p_reference"],
                          "filters": [["ts", ">", str(origin)], ["ts", "<=", str(limit)]],
                          "target_columns": ["y", "smp", "k"], "rows": len(reference)})
            canonical = truth[KEYS + ["y", "smp", "k"]].sort_values(KEYS).reset_index(drop=True)
            original = reference[KEYS + ["y", "smp", "k"]].sort_values(KEYS).reset_index(drop=True)
            pd.testing.assert_frame_equal(canonical, original, check_exact=True)
            truth = checked_join(truth, reference, ["p_reference"])
            assert truth.loc[truth.night, "p_reference"].eq(0).all()
            reference_check = {"exact_original_keys_and_targets": True,
                               "source_sha256": source_hashes[str((REFERENCE / name / "labels.parquet").relative_to(ROOT))]}
        folder = staging / name
        folder.mkdir()
        train.to_parquet(folder / "train.parquet", index=False)
        evaluation.to_parquet(folder / "evaluation.parquet", index=False)
        truth.to_parquet(folder / "labels.parquet", index=False)
        selected = {family: [col for col in names if train[col].nunique(dropna=True) > 1]
                    for family, names in (("rich", rich), ("station", station))}
        save(folder / "features.json", {"rich": rich, "station": station, "selected": selected,
             "selected_rich": selected["rich"], "selected_station": selected["station"],
             "origin": str(origin), "end": str(limit), "train_only_feature_selection": True,
             "static_capacity": capacities})
        records.append({"name": name, "origin": str(origin), "end": str(limit),
            "train_rows": len(train), "daylight_evaluation_rows": len(evaluation),
            "scoring_rows": len(truth), "night_rows": int(truth.night.sum()),
            "night_rows_with_nonzero_observed_y": int((truth.night & truth.y.ne(0)).sum()),
            "train_feature_counts": {family: len(names) for family, names in selected.items()},
            "reference_check": reference_check})
    assert current_sources() == source_hashes, "Source changed during preparation"
    save(staging / "read_receipts.json", reads)
    manifest = {"status": "PASS", "created_utc": datetime.now(timezone.utc).isoformat(),
        "folds": FOLDS, "search_end_kst": str(end), "source_sha256": source_hashes,
        "records": records, "search_daylight_rows": len(features), "search_scoring_rows": len(labels),
        "search_night_rows_with_nonzero_observed_y": int((labels.night & labels.y.ne(0)).sum()),
        "real_model_fits": 0, "march_may_2025_targets_loaded": False,
        "all_history_previously_exposed": True,
        "data_sha256": {str(path.relative_to(staging)): sha(path) for path in sorted(staging.rglob("*")) if path.is_file()}}
    save(staging / "manifest.json", manifest)
    verify_ready(staging)


def ensure_prepare() -> Path:
    """Prepare once transactionally, or verify and return an existing snapshot."""
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "data_prepare.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if DATA.exists():
            verify_ready(DATA)
            return DATA
        staging = OUT / "data.preparing"
        assert not staging.exists(), "Interrupted preparation retained at data.preparing; inspect before resuming"
        staging.mkdir()
        _prepare(staging)
        os.rename(staging, DATA)
        return DATA


def prepare_deployment_data() -> Path:
    """The late-audit/full-refit path must be separately frozen after selection."""
    raise NotImplementedError("Deployment/audit preparation is deliberately separate; freeze selected search recipe first")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        result = verify_ready()
    else:
        result = verify_ready(ensure_prepare())
    print(json.dumps({key: result[key] for key in ("status", "records", "search_daylight_rows", "search_scoring_rows", "real_model_fits", "march_may_2025_targets_loaded")}, indent=2))
