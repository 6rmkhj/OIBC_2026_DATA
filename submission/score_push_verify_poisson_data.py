# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow"]
# ///
# How to run: python submission/score_push_verify_poisson_data.py BEFORE Poisson fits.
"""Verify native station inputs, positive targets and temporal quasi-loss weights."""
from __future__ import annotations

import json
from datetime import datetime
from math import fsum
from typing import Final
from zoneinfo import ZoneInfo

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from score_push_verify_mlp_data import ROOT, digest, keyed, read
from score_push_verify_renew_final_data import equal_source, scale

OUT: Final = ROOT / "analysis_outputs/renew_20261106/poisson_wave"
OLD: Final = ROOT / "analysis_outputs/renew_20261105"
GPU: Final = ROOT / "analysis_outputs/score_push_gpu_20261104/data"


def hashes() -> None:
    protocol = read(OUT / "protocol.json")
    for mapping in (protocol["input_sha256"], protocol["protected_sha256"]):
        for path, expected in mapping.items():
            assert digest(ROOT / path) == expected, path
    for name, record in protocol["own_sources"].items():
        assert digest(ROOT / record["original"]) == digest(OUT / "sources/own" / name) == record["sha256"]
    for name, record in protocol["snapshots"].items():
        assert digest(ROOT / record["original"]) == digest(OUT / "sources" / f"{name}.py") == record["sha256"]
    for path, expected in read(OUT / "prepared_manifest.json").items():
        assert digest(OUT / path) == expected, path


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    hashes()
    assert not list((OUT / "trials").glob("**/model.txt"))
    assert (OUT / "original_weather_coefficients.json").read_bytes() == (OLD / "calibration_wave/coefficients.json").read_bytes()
    checked = []
    for fold, date in (("primary", "2023-06-01"), ("recent", "2024-06-01")):
        directory = OUT / "data" / fold
        cutoff = datetime.fromisoformat(date).replace(tzinfo=ZoneInfo("Asia/Seoul"))
        candidates = read(GPU / fold / "features.json")["station"]
        assert len(candidates) == 904 and not {"cf", "y", "smp", "k", "energy"} & set(candidates)
        train, evaluation = [pq.read_table(directory / f"{name}.parquet") for name in ("train", "evaluation")]
        for name, table in (("train", train), ("evaluation", evaluation)):
            original = pq.read_table(GPU / fold / f"{name}.parquet")
            assert table.column_names == original.column_names and len(table) == len(original)
            assert table.select(["ts", "grp"]).to_pylist() == original.select(["ts", "grp"]).to_pylist()
            equal_source(table, original)
        selected = [name for name in candidates if len(np.unique(train[name].to_numpy()[~np.isnan(train[name].to_numpy())])) > 1]
        spec = read(directory / "feature_mask.json")
        assert spec["candidate_columns"] == candidates and spec["selected_columns"] == selected
        assert len(selected) == (460 if fold == "primary" else 790)
        assert spec["train_rows"] == len(train) and spec["evaluation_rows"] == len(evaluation)
        times = train["ts"].to_pylist()
        assert all(ts <= cutoff for ts in times) and all(ts > cutoff for ts in evaluation["ts"].to_pylist())
        normalizer = scale(train["cosz"].to_numpy())
        target = train["cf"].to_numpy().astype(np.float64) / normalizer
        age = np.array([(cutoff - ts).total_seconds() / 86400 for ts in times])
        decay = np.exp2(-age / 180)
        multiplier = decay / (fsum(decay) / len(decay))
        weights = normalizer * multiplier
        transform = pq.read_table(directory / "training_transform.parquet")
        previous = pq.read_table(OLD / "mono_wave/data" / fold / "training_transform.parquet")
        assert transform.select(["ts", "grp"]).to_pylist() == train.select(["ts", "grp"]).to_pylist()
        for name, expected in (("normalizer", normalizer), ("age_days", age), ("decay", decay),
                               ("recency_multiplier", multiplier), ("sample_weight", weights), ("target_normalized", target)):
            np.testing.assert_allclose(transform[name].to_numpy(), expected, rtol=1e-12, atol=1e-12, err_msg=name)
            np.testing.assert_array_equal(transform[name].to_numpy(), previous[name].to_numpy())
        assert np.isfinite(target).all() and (target >= 0).all() and fsum(target) > 0 and (weights > 0).all()
        inverse = pq.read_table(directory / "evaluation_transform.parquet")
        assert inverse.select(["ts", "grp"]).to_pylist() == evaluation.select(["ts", "grp"]).to_pylist()
        np.testing.assert_allclose(inverse["inverse_kwh"].to_numpy(), scale(evaluation["cosz"].to_numpy()) * evaluation["capacity_kw"].to_numpy(), rtol=1e-12, atol=1e-12)
        equal_source(inverse, pq.read_table(OLD / "mono_wave/data" / fold / "evaluation_transform.parquet"))
        reference = keyed(pq.read_table(OLD / "calibration_wave/comparisons/temperature_then_snow" / fold / "predictions.parquet"))
        labels = keyed(pq.read_table(directory / "labels.parquet"))
        assert set(labels) == set(reference)
        for key, row in labels.items():
            assert row["p_reference"] == reference[key]["p"] and all(row[n] == reference[key][n] for n in ("y", "smp", "k"))
        coverage = keyed(pq.read_table(directory / "coverage.parquet"))
        assert set(coverage) == set(labels)
        application = pq.read_table(directory / "application_inputs.parquet")
        assert application.column_names == ["ts", "grp", "wa_temp", "extra_wa_snow", "static_capacity"]
        equal_source(application, pq.read_table(OLD / "extra_wave/data" / fold / "application_inputs.parquet"))
        daylight = set(keyed(evaluation.select(["ts", "grp"])))
        assert len(daylight) == len(evaluation) and daylight <= set(coverage)
        for key, row in coverage.items():
            assert row["night"] == (key not in daylight)
            assert not row["night"] or labels[key]["p_reference"] == 0
        checked.append({"fold": fold, "train_rows": len(train), "evaluation_rows": len(evaluation),
                        "features": len(selected), "sample_weight_sum": fsum(weights), "nonnegative_target": True})
    evidence = {"status": "PASS", "records": checked, "protocol_sha256": digest(OUT / "protocol.json"),
                "prepared_manifest_sha256": digest(OUT / "prepared_manifest.json"),
                "scope": "Original inputs and train-only masks, nonnegative normalized targets, exact temporal weights/inverse, weather-only reference and label-free application; no Poisson fits."}
    (OUT / "independent_data_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
