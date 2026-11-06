# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow"]
# ///
# How to run: python submission/score_push_verify_extra_data.py BEFORE forest fits.
"""Verify rich inputs and normalized square-loss weights against original data."""
from __future__ import annotations

import json
from datetime import datetime
from math import fsum, isfinite, isclose
from typing import Final
from zoneinfo import ZoneInfo

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from score_push_verify_mlp_data import ROOT, read, digest, keyed
from score_push_verify_renew_final_data import equal_source, scale

RENEW: Final = ROOT / "analysis_outputs/renew_20261105"
OUT: Final = RENEW / "extra_wave"
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
    assert not list(OUT.rglob("model.joblib"))
    assert (OUT / "original_weather_coefficients.json").read_bytes() == (RENEW / "calibration_wave/coefficients.json").read_bytes()
    checked = []
    for fold, date in (("primary", "2023-06-01"), ("recent", "2024-06-01")):
        directory = OUT / "data" / fold
        cutoff = datetime.fromisoformat(date).replace(tzinfo=ZoneInfo("Asia/Seoul"))
        names = read(GPU / fold / "features.json")["rich"]
        assert len(names) == 100 and not {"cf", "y", "smp", "k", "energy"} & set(names)
        train, evaluation = [pq.read_table(directory / f"{name}.parquet") for name in ("train", "evaluation")]
        for name, table, extra in (("train", train, "cf"), ("evaluation", evaluation, "capacity_kw")):
            original = pq.read_table(GPU / fold / f"{name}.parquet", columns=["ts", "grp", extra, *names])
            assert table.column_names == original.column_names and len(table) == len(original)
            assert table.select(["ts", "grp"]).to_pylist() == original.select(["ts", "grp"]).to_pylist()
            equal_source(table, original)
        spec = read(directory / "features.json")
        assert spec["rich"] == names and spec["train_rows"] == len(train) and spec["evaluation_rows"] == len(evaluation)
        times = train["ts"].to_pylist()
        assert all(ts <= cutoff for ts in times) and all(ts > cutoff for ts in evaluation["ts"].to_pylist())
        normalizer = scale(train["cosz"].to_numpy())
        target = train["cf"].to_numpy().astype(np.float64) / normalizer
        age = np.array([(cutoff - ts).total_seconds() / 86400 for ts in times])
        base, decay = normalizer ** 2, np.exp2(-age / 180)
        constant = fsum(base) / fsum(base * decay)
        weights = base * decay * constant
        transform = pq.read_table(directory / "training_transform.parquet")
        old = pq.read_table(RENEW / "mlp_wave/data" / fold / "training_transform.parquet")
        assert transform.select(["ts", "grp"]).to_pylist() == train.select(["ts", "grp"]).to_pylist()
        assert "target_scaled" not in transform.column_names
        for name, expected in (("normalizer", normalizer), ("age_days", age), ("base_weight", base), ("decay", decay), ("weight_normalization", np.full(len(train), constant)), ("sample_weight", weights), ("target_normalized", target)):
            np.testing.assert_allclose(transform[name].to_numpy(), expected, rtol=1e-12, atol=1e-12, err_msg=name)
            np.testing.assert_array_equal(transform[name].to_numpy(), old[name].to_numpy())
        assert np.isfinite(target).all() and (weights > 0).all() and isclose(fsum(weights), fsum(base), rel_tol=1e-12)
        inverse = pq.read_table(directory / "evaluation_transform.parquet")
        assert (directory / "evaluation_transform.parquet").read_bytes() == (RENEW / "mlp_wave/data" / fold / "evaluation_transform.parquet").read_bytes()
        assert inverse.select(["ts", "grp"]).to_pylist() == evaluation.select(["ts", "grp"]).to_pylist()
        np.testing.assert_allclose(inverse["inverse_kwh"].to_numpy(), scale(evaluation["cosz"].to_numpy()) * evaluation["capacity_kw"].to_numpy(), rtol=1e-12, atol=1e-12)
        reference = keyed(pq.read_table(RENEW / "calibration_wave/comparisons/temperature_then_snow" / fold / "predictions.parquet"))
        labels = keyed(pq.read_table(directory / "labels.parquet"))
        assert set(labels) == set(reference)
        for key, row in labels.items():
            assert row["p_reference"] == reference[key]["p"] and all(row[n] == reference[key][n] for n in ("y", "smp", "k"))
        coverage = keyed(pq.read_table(directory / "coverage.parquet"))
        assert (directory / "coverage.parquet").read_bytes() == (RENEW / "mlp_wave/data" / fold / "coverage.parquet").read_bytes()
        application = pq.read_table(directory / "application_inputs.parquet")
        assert application.column_names == ["ts", "grp", "wa_temp", "extra_wa_snow", "static_capacity"]
        assert set(keyed(application)) == set(labels)
        weather = keyed(evaluation.select(["ts", "grp", "wa_temp", "extra_wa_snow"]))
        for row in application.to_pylist():
            key = row["ts"], row["grp"]
            assert (key not in weather) == coverage[key]["night"] and row["static_capacity"] == reference[key]["static_capacity"]
            for name in ("wa_temp", "extra_wa_snow"):
                actual, expected = row[name], weather.get(key, {}).get(name)
                assert actual == expected or ((actual is None or not isfinite(actual)) and (expected is None or not isfinite(expected)))
        checked.append({"fold": fold, "train_rows": len(train), "evaluation_rows": len(evaluation),
                        "features": len(names), "sample_weight_sum": fsum(weights), "normalization": constant})
    evidence = {"status": "PASS", "records": checked, "protocol_sha256": digest(OUT / "protocol.json"),
                "prepared_manifest_sha256": digest(OUT / "prepared_manifest.json"),
                "scope": "All native rich inputs and NaNs, normalized target and temporal square-loss weights, inverse, weather-only official-best references and label-free calibration inputs; zero forest fits."}
    (OUT / "independent_data_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
