# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "joblib", "scikit-learn"]
# ///
# How to run: python submission/score_push_verify_mlp_data.py BEFORE real MLP fits.
"""Verify original station inputs and all train-only neural preprocessing."""
from __future__ import annotations

import json
from datetime import datetime
from math import fsum, isclose, isfinite
from typing import Final
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from score_push_verify import ROOT, digest
from score_push_verify_renew_final_data import equal_source, scale

OUT: Final = ROOT / "analysis_outputs/renew_20261105/mlp_wave"
RENEW: Final = OUT.parent
GPU: Final = ROOT / "analysis_outputs/score_push_gpu_20261104/data"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def keyed(table):
    result = {(r["ts"], r["grp"]): r for r in table.to_pylist()}
    assert len(result) == len(table)
    return result


def scaler_check(scaler, values):
    count = len(values)
    assert scaler.n_samples_seen_ == count and scaler.with_mean and scaler.with_std
    np.testing.assert_allclose(scaler.mean_, values.mean(axis=0), rtol=1e-12, atol=1e-9)
    np.testing.assert_allclose(scaler.var_, values.var(axis=0), rtol=1e-11, atol=1e-10)
    error_bound = count * np.finfo(float).eps * scaler.var_ + (count * scaler.mean_ * np.finfo(float).eps) ** 2
    expected_scale = np.where(scaler.var_ <= error_bound, 1., np.sqrt(scaler.var_))
    np.testing.assert_allclose(scaler.scale_, expected_scale, rtol=1e-12, atol=0)


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = read(OUT / "protocol.json")
    for name, record in protocol["own_sources"].items():
        assert digest(OUT / "sources/own" / name) == record["sha256"]
    active_sources = protocol["own_sources"].copy()
    amendment_path = OUT / "source_amendment.json"
    if amendment_path.exists():
        amendment = read(amendment_path)
        assert amendment["original_protocol_sha256"] == digest(OUT / "protocol.json")
        active_sources.update(amendment["own_sources"])
    for name, record in active_sources.items():
        assert digest(ROOT / record["original"]) == record["sha256"]
        assert digest(OUT / record.get("snapshot", "sources/own/" + name)) == record["sha256"]
    for name, record in protocol["snapshots"].items():
        assert digest(ROOT / record["original"]) == digest(OUT / "sources" / f"{name}.py") == record["sha256"]
    for path, expected in protocol["input_sha256"].items():
        assert digest(ROOT / path) == expected, path
    for path, expected in read(OUT / "prepared_manifest.json").items():
        assert digest(OUT / path) == expected, path
    for stage, previous in (("weather", "calibration_wave"), ("hour", "hour_wave"), ("cloud", "sky_wave")):
        assert (OUT / f"original_{stage}_coefficients.json").read_bytes() == (RENEW / previous / "coefficients.json").read_bytes()
    checked = []
    for fold, date in (("primary", "2023-06-01"), ("recent", "2024-06-01")):
        cutoff = datetime.fromisoformat(date).replace(tzinfo=ZoneInfo("Asia/Seoul"))
        directory = OUT / "data" / fold
        train, evaluation = [pq.read_table(directory / f"{name}.parquet") for name in ("train", "evaluation")]
        for name, table in (("train", train), ("evaluation", evaluation)):
            original = pq.read_table(GPU / fold / f"{name}.parquet")
            assert len(table) == len(original) and table.select(["ts", "grp"]).to_pylist() == original.select(["ts", "grp"]).to_pylist()
            equal_source(table, original)
        candidates = read(GPU / fold / "features.json")["station"]
        assert set(train.column_names) == {"ts", "grp", "cf", *candidates}
        assert set(evaluation.column_names) == {"ts", "grp", "capacity_kw", *candidates}
        selected = [name for name in candidates if len(np.unique(train[name].to_numpy()[~np.isnan(train[name].to_numpy())])) > 1]
        spec = read(directory / "feature_mask.json")
        assert spec["candidate_columns"] == candidates and spec["selected_columns"] == selected
        assert spec["fitted_on"] == "training only" and spec["selected_cast_dtype"] == "float64"
        assert not {"smp", "k", "y", "energy", "cf"} & set(selected)
        matrices = [np.column_stack([table[name].to_numpy() for name in selected]).astype(np.float64) for table in (train, evaluation)]
        transform = joblib.load(directory / "input_preprocessing.joblib")
        imputer, scaler = transform[0], transform[1]
        assert imputer.strategy == "median" and imputer.keep_empty_features
        assert list(imputer.feature_names_in_) == selected
        median = np.nanmedian(matrices[0], axis=0)
        np.testing.assert_array_equal(imputer.statistics_, median)
        imputed = [np.where(np.isnan(matrix), median, matrix) for matrix in matrices]
        scaler_check(scaler, imputed[0])
        for name, matrix in zip(("train", "evaluation"), imputed, strict=True):
            saved = np.load(directory / f"x_{name}.npy", mmap_mode="r", allow_pickle=False)
            assert saved.dtype == np.float64 and saved.shape == matrix.shape
            np.testing.assert_array_equal(saved, (matrix - scaler.mean_) / scaler.scale_)
        times = train["ts"].to_pylist()
        assert all(ts <= cutoff for ts in times) and all(ts > cutoff for ts in evaluation["ts"].to_pylist())
        normalizer = scale(train["cosz"].to_numpy())
        target = train["cf"].to_numpy().astype(np.float64) / normalizer
        age = np.array([(cutoff - ts).total_seconds() / 86400 for ts in times])
        base, decay = normalizer ** 2, np.exp2(-age / 180)
        constant = fsum(base) / fsum(base * decay)
        weights = base * decay * constant
        target_scaler = joblib.load(directory / "target_scaler.joblib")
        scaler_check(target_scaler, target.reshape(-1, 1))
        scaled = (target - target_scaler.mean_[0]) / target_scaler.scale_[0]
        for name, expected in (("y_train.npy", scaled), ("sample_weight.npy", weights)):
            saved = np.load(directory / name, allow_pickle=False)
            assert saved.dtype == np.float64 and saved.shape == expected.shape and np.isfinite(saved).all()
            np.testing.assert_allclose(saved, expected, rtol=1e-12, atol=1e-12)
        assert (weights > 0).all() and isclose(fsum(weights), fsum(base), rel_tol=1e-12)
        training = pq.read_table(directory / "training_transform.parquet")
        assert training.select(["ts", "grp"]).to_pylist() == train.select(["ts", "grp"]).to_pylist()
        for name, expected in (("normalizer", normalizer), ("age_days", age), ("base_weight", base), ("decay", decay), ("weight_normalization", np.full(len(train), constant)), ("sample_weight", weights), ("target_normalized", target), ("target_scaled", scaled)):
            np.testing.assert_allclose(training[name].to_numpy(), expected, rtol=1e-12, atol=1e-12, err_msg=name)
        inverse = pq.read_table(directory / "evaluation_transform.parquet")
        assert inverse.select(["ts", "grp"]).to_pylist() == evaluation.select(["ts", "grp"]).to_pylist()
        eval_normalizer = scale(evaluation["cosz"].to_numpy())
        for name, expected in (("normalizer", eval_normalizer), ("capacity_kw", evaluation["capacity_kw"].to_numpy()), ("inverse_kwh", eval_normalizer * evaluation["capacity_kw"].to_numpy())):
            np.testing.assert_allclose(inverse[name].to_numpy(), expected, rtol=1e-12, atol=1e-12, err_msg=name)
        original = keyed(pq.read_table(RENEW / "sky_wave/comparisons/cloud_bias" / fold / "predictions.parquet"))
        labels = keyed(pq.read_table(directory / "labels.parquet"))
        assert set(labels) == set(original)
        for key, row in labels.items():
            assert row["p_reference"] == original[key]["p"] and all(row[n] == original[key][n] for n in ("y", "smp", "k"))
        coverage = keyed(pq.read_table(directory / "coverage.parquet"))
        original_night = keyed(pq.read_table(RENEW / "recency_wave/data" / fold / "night_coverage.parquet"))
        assert coverage == original_night
        application = pq.read_table(directory / "application_inputs.parquet")
        assert set(application.column_names) == {"ts", "grp", "wa_temp", "extra_wa_snow", "wb_cloud", "static_capacity"}
        weather = keyed(evaluation.select(["ts", "grp", "wa_temp", "extra_wa_snow", "wb_cloud"]))
        assert set(keyed(application)) == set(original)
        for row in application.to_pylist():
            key = row["ts"], row["grp"]
            assert row["static_capacity"] == original[key]["static_capacity"]
            assert (key not in weather) == coverage[key]["night"]
            for name in ("wa_temp", "extra_wa_snow", "wb_cloud"):
                expected = weather.get(key, {}).get(name)
                assert row[name] == expected or ((row[name] is None or not isfinite(row[name])) and (expected is None or not isfinite(expected)))
        checked.append({"fold": fold, "train_rows": len(train), "evaluation_rows": len(evaluation), "selected_features": len(selected), "sum_base_weight": fsum(base), "sum_sample_weight": fsum(weights), "weight_normalization": constant})
    assert not list(OUT.rglob("model.joblib"))
    evidence = {"status": "PASS", "records": checked, "protocol_sha256": digest(OUT / "protocol.json"),
                "prepared_manifest_sha256": digest(OUT / "prepared_manifest.json"),
                "scope": "Every raw feature/key, train-only mask/median/input and target scales, float64 matrices, physical normalization/recency/mass weights, inverse and full label-free application data. No real neural fits."}
    (OUT / "independent_data_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
