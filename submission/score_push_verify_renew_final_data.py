# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "lightgbm"]
# ///
# How to run: python submission/score_push_verify_renew_final_data.py
"""Check final temporal training boundaries, frozen inputs and canonical replay."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from math import fsum
from typing import Final
from zoneinfo import ZoneInfo

import lightgbm as lgb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from score_push_verify import ROOT, digest

OUT: Final = ROOT / "analysis_outputs/renew_20261105/final"
OLD: Final = ROOT / "analysis_outputs/autoresearch_20261103/final"
CPU: Final = ROOT / "analysis_outputs/score_push_20261104"
RENEW: Final = OUT.parent
KST: Final = ZoneInfo("Asia/Seoul")


def equal_source(actual: pa.Table, source: pa.Table) -> None:
    source_keys = list(zip(source["ts"].to_pylist(), source["grp"].to_pylist(), strict=True))
    lookup = {key: i for i, key in enumerate(source_keys)}
    assert len(lookup) == len(source_keys)
    keys = list(zip(actual["ts"].to_pylist(), actual["grp"].to_pylist(), strict=True))
    aligned = source.take(pa.array([lookup[key] for key in keys]))
    for name in set(actual.column_names) & set(source.column_names) - {"ts", "grp"}:
        np.testing.assert_array_equal(actual[name].to_numpy(), aligned[name].to_numpy(), err_msg=name)


def scale(values: np.ndarray) -> np.ndarray:
    cosz = np.maximum(values, 0.)
    exponent = np.divide(-.059, cosz, out=np.zeros(len(cosz)), where=cosz > 0)
    return np.maximum(1.098 * cosz * np.exp(exponent), .05)


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = json.loads((OUT / "protocol.json").read_text())
    assert protocol["alpha"] == .07794876465304705 and protocol["new_model_budget"] == 6
    assert digest(OUT / "selected_coefficients.json") == protocol["coefficient_sha256"]
    assert digest(OUT / "static_capacity.json") == protocol["static_capacity_sha256"]
    assert (OUT / "selected_coefficients.json").read_bytes() == (RENEW / "calibration_wave/coefficients.json").read_bytes()
    for path, expected in protocol["input_sha256"].items():
        assert digest(ROOT / path) == expected, path
    for path, expected in json.loads((OUT / "prepared_manifest.json").read_text()).items():
        assert digest(OUT / path) == expected, path
    base_columns = [n for n in pq.ParquetFile(OLD / "outer_features.parquet").schema_arrow.names if n not in ("cf", "energy", "y", "smp", "k")]
    checked = []
    for split, date in (("latest", "2025-03-01"), ("test", "2025-06-01")):
        cutoff = datetime.fromisoformat(date).replace(tzinfo=KST)
        directory = OUT / "data" / split
        frame = pq.read_table(directory / "train.parquet")
        weights = pq.read_table(directory / "weights.parquet")
        features = json.loads((directory / "features.json").read_text())
        source = pq.read_table(OLD / "full_train.parquet", columns=[*base_columns, "cf"], filters=[("ts", "<=", cutoff)])
        assert len(source) == len(frame) == features["train_rows"]
        actual_keys = {(r["ts"], r["grp"]) for r in frame.select(["ts", "grp"]).to_pylist()}
        source_keys = {(r["ts"], r["grp"]) for r in source.select(["ts", "grp"]).to_pylist()}
        assert actual_keys == source_keys and len(actual_keys) == len(frame)
        equal_source(frame, source)
        for kind in ("weather", "stations"):
            equal_source(frame, pq.read_table(CPU / "final/cache" / f"train_{kind}.parquet", filters=[("ts", "<=", cutoff)]))
        assert frame.select(["ts", "grp"]).to_pylist() == weights.select(["ts", "grp"]).to_pylist()
        timestamps = frame["ts"].to_pylist()
        assert all(ts <= cutoff for ts in timestamps)
        age = np.array([(cutoff - ts).total_seconds() / 86400 for ts in timestamps])
        normalizer = scale(frame["cosz"].to_numpy())
        decay = np.exp2(-age / 180)
        decay /= fsum(decay) / len(decay)
        expected_weights = {"age_days": age, "normalizer": normalizer, "decay": decay,
                            "sample_weight": normalizer * decay, "target": frame["cf"].to_numpy() / normalizer}
        for name, values in expected_weights.items():
            np.testing.assert_allclose(weights[name].to_numpy(), values, rtol=1e-12, atol=1e-12, err_msg=name)
        assert len(features["candidates"]) == 904
        selected = []
        for name in features["candidates"]:
            values = frame[name].to_numpy()
            if len(np.unique(values[~np.isnan(values)])) > 1:
                selected.append(name)
        assert selected == features["features"] and not {"cf", "y", "smp", "k", "energy"} & set(selected)
        checked.append({"split": split, "cutoff": date, "train_rows": len(frame), "selected_features": len(selected)})
    assignment = json.loads((ROOT / "analysis_outputs/autoresearch_20261103/cache/assignment.json").read_text())
    for split, dates in {"recent": ("2024-06-01", "2025-03-01"), "march_may": ("2025-03-01", "2025-06-01"), "test": ("2025-06-01", "2026-06-01")}.items():
        start, end = [datetime.fromisoformat(date).replace(tzinfo=KST) for date in dates]
        filters = [("ts", ">", start), ("ts", "<=", end)]
        side = "test" if split == "test" else "train"
        directory = OUT / "data" / split
        frame = pq.read_table(directory / "evaluation.parquet")
        assert not {"cf", "y", "smp", "k", "energy"} & set(frame.column_names)
        source = pq.read_table(OLD / ("test_features.parquet" if split == "test" else "outer_features.parquet"), columns=base_columns, filters=filters)
        assert len(source) == len(frame)
        equal_source(frame, source)
        for kind in ("weather", "stations"):
            equal_source(frame, pq.read_table(CPU / "final/cache" / f"{side}_{kind}.parquet", filters=filters))
        coverage = {}
        raw = pq.read_table(ROOT / protocol["night_cache"] / f"feat_{side}.parquet", columns=["ts", "site_id", "night"], filters=filters)
        for batch in raw.to_batches(max_chunksize=65536):
            for row in batch.to_pylist():
                key = row["ts"], assignment[row["site_id"]]
                coverage[key] = coverage.get(key, True) and row["night"]
        saved_coverage = pq.read_table(directory / "coverage.parquet").to_pylist()
        assert {(r["ts"], r["grp"]): r["night"] for r in saved_coverage} == coverage
        assert {(r["ts"], r["grp"]) for r in frame.select(["ts", "grp"]).to_pylist()} == {key for key, night in coverage.items() if not night}
        cpu = pq.read_table(directory / "cpu_base.parquet").to_pylist()
        original = pq.read_table(CPU / "final" / ("test_predictions.parquet" if split == "test" else "outer_predictions.parquet"), columns=["ts", "grp", "p_candidate"], filters=filters).to_pylist()
        assert {(r["ts"], r["grp"]): r["p_cpu"] for r in cpu} == {(r["ts"], r["grp"]): r["p_candidate"] for r in original}
        assert len(cpu) == len(coverage) and all(r["p_cpu"] == 0 for r in cpu if coverage[(r["ts"], r["grp"])])
        expected_keys = {(start + timedelta(hours=i), group) for i in range(1, int((end-start).total_seconds()/3600)+1) for group in ("G1", "G2")}
        assert set(coverage) == expected_keys
    latest = pq.read_table(OUT / "data/latest/cpu_base.parquet").to_pylist()
    prior = pq.read_table(CPU / "deployment_check/frozen_predictions.parquet", columns=["ts", "grp", "p_candidate"]).to_pylist()
    assert {(r["ts"], r["grp"]): r["p_cpu"] for r in latest} == {(r["ts"], r["grp"]): r["p_candidate"] for r in prior}
    recent = pq.read_table(OUT / "data/recent/evaluation.parquet")
    original_recent = pq.read_table(ROOT / "analysis_outputs/score_push_gpu_20261104/data/recent/evaluation.parquet")
    assert len(recent) == len(original_recent)
    equal_source(recent, original_recent)
    inverse = scale(recent["cosz"].to_numpy()) * recent["capacity_kw"].to_numpy()
    saved = pq.read_table(OUT / "evidence/recent_temporal_raw.parquet")
    for seed in range(3):
        directory = RENEW / "recency_wave/trials/decay180/recent" / f"seed{seed}"
        names = json.loads((directory / "config.json").read_text())["features"]
        model = lgb.Booster(model_file=str(directory / "model.txt"))
        prediction = model.predict(recent.select(names).to_pandas(), num_threads=1) * inverse
        np.testing.assert_array_equal(prediction, saved[f"seed{seed}_raw"].to_numpy())
        original = pq.read_table(directory / "daylight_raw.parquet")
        np.testing.assert_array_equal(prediction, original["p_raw"].to_numpy())
    evidence = {"status": "PASS", "training": checked, "recent_model_replays": 3,
                "protocol_sha256": digest(OUT / "protocol.json"), "prepared_manifest_sha256": digest(OUT / "prepared_manifest.json"),
                "scope": "Frozen source projections, both cutoff masks/weights, full coverage/night flags and CPU predictions, exact three-seed recent model replay. No new fit or confirmation scoring."}
    (OUT / "independent_data_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
