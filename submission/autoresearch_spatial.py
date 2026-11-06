#!/usr/bin/env python
# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
# How to run (existing project environment, no installs):
# python submission/autoresearch_spatial.py --self-check
# python submission/autoresearch_spatial.py
"""Weather-only capacity-weighted spatial features for frozen selection splits."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Final

for _variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_variable] = "1"

import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- preserve the existing group_frame interface
import pyarrow as pa

ROOT: Final = Path(__file__).resolve().parents[1]
OUT: Final = ROOT / "analysis_outputs/autoresearch_20261103/spatial"
CACHE: Final = OUT.parent / "cache"
WEATHER: Final = ("wa_cloud", "wb_cloud", "wb_uv_idx", "csa", "csb")
COLUMNS: Final = ("site_id", "ts", "night", "capacity_kw", *WEATHER)
FEATURES: Final = tuple(f"sp_{field}_sd" for field in WEATHER) + tuple(
    f"sp_{field}_{fraction}" for field in WEATHER[:2] for fraction in ("clear", "overcast")
)
TRAIN_END: Final = pd.Timestamp("2023-06-01", tz="Asia/Seoul")
SELECTION_END: Final = pd.Timestamp("2024-06-01", tz="Asia/Seoul")


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def aggregate_spatial(frame: pd.DataFrame, assignment: Mapping[str, str]) -> pd.DataFrame:
    """Aggregate daylight rows; missing observations exclude their capacity weight."""
    assert set(frame.columns) == set(COLUMNS), "Input must contain only the approved weather columns"
    assert frame.ts.dt.tz is not None, "Timestamps must be timezone-aware"
    assert frame[["site_id", "ts", "night", "capacity_kw"]].notna().all().all()
    assert pd.api.types.is_bool_dtype(frame.night), "night must be boolean"
    assert not frame.duplicated(["site_id", "ts"]).any()
    assert np.isfinite(frame.capacity_kw).all() and frame.capacity_kw.gt(0).all()
    assert set(frame.site_id).issubset(assignment), "Every site needs a frozen assignment"
    assert all(isinstance(group, str) and group for group in assignment.values())
    daylight = frame.loc[~frame.night].copy()
    daylight["ts"] = daylight.ts.dt.tz_convert("Asia/Seoul")
    daylight["grp"] = daylight.site_id.map(assignment)
    moments = daylight[["ts", "grp"]].copy()
    for field in WEATHER:
        values = daylight[field].astype("float64")
        assert np.isfinite(values.dropna()).all(), field
        weight = daylight.capacity_kw.where(values.notna(), 0.0)
        moments[f"{field}_weight"] = weight
        moments[f"{field}_sum"] = weight * values.fillna(0.0)
        moments[f"{field}_square"] = weight * values.fillna(0.0).pow(2)
        if field in WEATHER[:2]:
            moments[f"{field}_clear"] = weight * values.lt(20)
            moments[f"{field}_overcast"] = weight * values.gt(80)
    totals = moments.groupby(["ts", "grp"], sort=True, observed=True).sum()
    result = pd.DataFrame(index=totals.index)
    for field in WEATHER:
        denominator = totals[f"{field}_weight"].replace(0.0, np.nan)
        mean = totals[f"{field}_sum"] / denominator
        variance = totals[f"{field}_square"] / denominator - mean.pow(2)
        result[f"sp_{field}_sd"] = np.sqrt(variance.clip(lower=0.0))
        if field in WEATHER[:2]:
            for fraction in ("clear", "overcast"):
                result[f"sp_{field}_{fraction}"] = totals[f"{field}_{fraction}"] / denominator
    return result.loc[:, list(FEATURES)].reset_index()


def self_check() -> None:
    """Hand-computed unequal-weight, missing-value, daylight, and trust-boundary cases."""
    stamp = pd.Timestamp("2023-05-01 12:00", tz="Asia/Seoul")
    frame = pd.DataFrame({
        "site_id": ["a", "b", "c", "d", "e"], "ts": [stamp] * 5,
        "night": [False, False, False, False, True], "capacity_kw": [1., 3., 2., 5., 999.],
        "wa_cloud": [0., 100., np.nan, 50., 500.], "wb_cloud": [20., 80., np.nan, np.nan, 500.],
        "wb_uv_idx": [2., 6., 1., np.nan, 500.], "csa": [7., 7., 9., 9., 500.],
        "csb": [np.nan, 8., np.nan, np.nan, 500.],
    })
    assignment = {"a": "G1", "b": "G1", "c": "G2", "d": "G2", "e": "G3"}
    actual = aggregate_spatial(frame, assignment).set_index("grp")
    expected = pd.DataFrame([
        [np.sqrt(1875), np.sqrt(675), np.sqrt(3), 0., 0., .25, .75, 0., 0.],
        [0., np.nan, 0., 0., np.nan, 0., 0., np.nan, np.nan],
    ], columns=FEATURES, index=pd.Index(["G1", "G2"], name="grp"))
    pd.testing.assert_frame_equal(actual[list(FEATURES)], expected)
    assert len(aggregate_spatial(frame.loc[frame.night], assignment)) == 0
    for label in ("energy", "cf", "actual", "y"):
        try:
            aggregate_spatial(frame.assign(**{label: 1.0}), assignment)
        except AssertionError as error:
            assert "approved weather columns" in str(error)
        else:
            raise AssertionError(f"Label column accepted: {label}")
    print(json.dumps({"self_check": "PASS", "scenarios": [
        "unequal capacity weighted SD and strict cloud thresholds",
        "feature-specific NaN denominators, all-missing NaN, constant SD zero",
        "night-only groups omitted and label-bearing input rejected",
    ], "actual": json.loads(actual[list(FEATURES)].to_json(orient="index"))}), flush=True)


def main() -> None:
    pa.set_cpu_count(2)
    pa.set_io_thread_count(2)
    self_check()
    if "--self-check" in sys.argv:
        return
    assert len(sys.argv) == 1, "Only --self-check is supported"
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / "manifest.json").exists(), "Spatial features already frozen"
    previous = ROOT / "analysis_outputs/award_run"
    provenance_path = previous / "provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    source = previous / "cache" / provenance["cache_key"] / "feat_train.parquet"
    hashes = json.loads((source.parent / "feature_hashes.json").read_text(encoding="utf-8"))
    input_sha = digest(source)
    assert input_sha == hashes[source.name], "Original cache digest mismatch"
    frozen = json.loads((CACHE / "manifest.json").read_text(encoding="utf-8"))
    assert input_sha == frozen["inputs"]["feat_train"]
    assignment_path = CACHE / "assignment.json"
    assignment_sha = digest(assignment_path)
    assert assignment_sha == frozen["cache_sha256"]["assignment.json"]
    assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
    frame = pd.read_parquet(source, columns=list(COLUMNS), filters=[("ts", "<=", SELECTION_END)])
    assert frame.ts.max() <= SELECTION_END
    print(json.dumps({"projected_rows": len(frame), "projected_columns": list(frame.columns),
                      "max_ts": str(frame.ts.max())}), flush=True)
    features = aggregate_spatial(frame, assignment)
    outputs = {}
    for name, subset, key_source in (
        ("train", features.loc[features.ts <= TRAIN_END], CACHE / "train.parquet"),
        ("selection", features.loc[features.ts > TRAIN_END], CACHE / "selection_features.parquet"),
    ):
        assert digest(key_source) == frozen["cache_sha256"][key_source.name]
        expected_keys = pd.read_parquet(key_source, columns=["ts", "grp"])
        assert not expected_keys.duplicated(["ts", "grp"]).any()
        pd.testing.assert_frame_equal(subset[["ts", "grp"]].reset_index(drop=True),
                                      expected_keys.reset_index(drop=True), check_dtype=False)
        path = OUT / f"{name}.parquet"
        subset.to_parquet(path, index=False)
        restored = pd.read_parquet(path)
        pd.testing.assert_frame_equal(restored, subset.reset_index(drop=True))
        outputs[name] = {"path": str(path.relative_to(ROOT)), "sha256": digest(path),
                         "rows": len(subset), "keys_exact": True,
                         "min_ts": str(subset.ts.min()), "max_ts": str(subset.ts.max()),
                         "missing": {field: int(subset[field].isna().sum()) for field in FEATURES}}
    manifest = {
        "input_path": str(source.relative_to(ROOT)), "input_sha256": input_sha,
        "provenance_sha256": digest(provenance_path), "assignment_sha256": assignment_sha,
        "builder_sha256": digest(Path(__file__)), "feature_names": list(FEATURES),
        "projection": list(COLUMNS), "filter": "ts <= 2024-06-01 00:00:00+09:00",
        "train_end": str(TRAIN_END), "selection_end": str(SELECTION_END),
        "input_rows": len(frame), "daylight_rows": int((~frame.night).sum()),
        "threads": {"arrow_cpu": pa.cpu_count(), "arrow_io": pa.io_thread_count(), "blas": 1},
        "outputs": outputs,
    }
    manifest_path = OUT / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"manifest_sha256": digest(manifest_path), "outputs": outputs}), flush=True)


if __name__ == "__main__":
    main()
