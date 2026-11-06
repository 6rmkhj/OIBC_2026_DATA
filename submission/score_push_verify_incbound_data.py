# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "joblib", "scikit-learn"]
# ///
# How to run: python submission/score_push_verify_incbound_data.py BEFORE new inference.
"""Verify incumbent neural TRAIN bounds and frozen nested ensemble lineage."""
from __future__ import annotations

import json
from math import fsum, isclose
from typing import Final

import joblib
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from score_push_verify_mlp_data import ROOT, digest, read, keyed, scaler_check
from score_push_verify_renew_final_data import equal_source
from score_push_verify_refresh import apply_stages

RENEW: Final = ROOT / "analysis_outputs/renew_20261105"
OLD: Final = ROOT / "analysis_outputs/score_push_20261104"
GPU: Final = ROOT / "analysis_outputs/score_push_gpu_20261104/data"
OUT: Final = RENEW / "incbound_wave"


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


def effective_weight() -> float:
    temporal = read(RENEW / "recency_wave/comparisons/decay180/ensemble/decision.json")["alpha_primary_only"]
    station = read(OLD / "profile_wave/selected_recipe.json")["profile"]["alpha_primary_only"]
    refinement = read(OLD / "refinement_wave/chosen_recipe.json")
    assert refinement["members"] == ["p_reference", "norm", "mlp"]
    return (1 - temporal) * (1 - station) * refinement["weights_primary_only"][2]


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    hashes()
    assert not (OUT / "trials").exists()
    weight = effective_weight()
    assert weight == .13263687875028513
    factors = {}
    for stage, previous in (("weather", "calibration_wave"), ("hour", "hour_wave"), ("cloud", "sky_wave")):
        filename = f"original_{stage}_coefficients.json"
        assert (OUT / filename).read_bytes() == (RENEW / previous / "coefficients.json").read_bytes()
        factors[stage] = read(OUT / filename)["factors"]
    records = []
    for fold in ("primary", "recent"):
        data = OUT / "data" / fold
        names = read(GPU / fold / "features.json")["rich"]
        assert len(names) == 100 and not {"cf", "y", "smp", "k", "energy"} & set(names)
        frames = []
        for name in ("train", "evaluation"):
            frame = pq.read_table(data / f"projected_{name}.parquet")
            original = pq.read_table(GPU / fold / f"{name}.parquet", columns=["ts", "grp", *(["capacity_kw"] if name == "evaluation" else []), *names])
            assert frame.column_names == original.column_names and len(frame) == len(original)
            assert frame.select(["ts", "grp"]).to_pylist() == original.select(["ts", "grp"]).to_pylist()
            equal_source(frame, original)
            frames.append(frame)
        train, evaluation = frames
        original_model = OLD / "learner_wave" / fold / "mlp_cf/seed0"
        transform = joblib.load(original_model / "input_preprocessing.joblib")
        assert list(transform.feature_names_in_) == names
        for seed in (1, 2):
            for name in ("input_preprocessing.joblib", "target_scaler.joblib"):
                assert (original_model / name).read_bytes() == (original_model.parent / f"seed{seed}" / name).read_bytes()
        matrices = [np.column_stack([frame[name].to_numpy() for name in names]).astype(np.float64) for frame in frames]
        imputer, scaler = transform[0], transform[1]
        assert imputer.strategy == "median" and imputer.keep_empty_features
        median = np.nanmedian(matrices[0], axis=0)
        np.testing.assert_array_equal(imputer.statistics_, median)
        imputed = [np.where(np.isnan(matrix), median, matrix) for matrix in matrices]
        scaler_check(scaler, imputed[0])
        x_train, x_future = [(matrix - scaler.mean_) / scaler.scale_ for matrix in imputed]
        for filename, expected in (("x_train.npy", x_train), ("x_evaluation_original.npy", x_future)):
            saved = np.load(data / filename, allow_pickle=False)
            assert saved.dtype == np.float64 and saved.shape == expected.shape
            np.testing.assert_array_equal(saved, expected)
        lower, upper = x_train.min(axis=0), x_train.max(axis=0)
        assert (lower < upper).all()
        np.testing.assert_array_equal(np.clip(x_train, lower, upper), x_train)
        np.testing.assert_array_equal(np.load(data / "x_evaluation_bounded.npy", allow_pickle=False), np.clip(x_future, lower, upper))
        bounds = pq.read_table(data / "bounds.parquet")
        assert bounds["feature"].to_pylist() == names and bounds["feature_index"].to_pylist() == list(range(len(names)))
        below, above = x_future < lower, x_future > upper
        for name, expected in (("lower", lower), ("upper", upper), ("below_count", below.sum(axis=0)), ("above_count", above.sum(axis=0)), ("clipped_count", (below | above).sum(axis=0))):
            np.testing.assert_array_equal(bounds[name].to_numpy(), expected)
        inverse = pq.read_table(data / "evaluation_transform.parquet")
        assert inverse.column_names == ["ts", "grp", "capacity_kw"]
        assert inverse.to_pylist() == evaluation.select(inverse.column_names).to_pylist()
        for name in ("labels.parquet", "coverage.parquet", "application_inputs.parquet"):
            assert (data / name).read_bytes() == (RENEW / "mlp_wave/data" / fold / name).read_bytes()
        lineage = keyed(pq.read_table(data / "lineage.parquet"))
        raw_temporal = keyed(pq.read_table(RENEW / "recency_wave/comparisons/decay180/ensemble" / fold / "predictions.parquet"))
        old_mlp = keyed(pq.read_table(OLD / "learner_wave" / fold / "mlp_cf/ensemble/pure/predictions.parquet"))
        seeds = [keyed(pq.read_table(original_model.parent / f"seed{seed}/daylight_raw.parquet")) for seed in range(3)]
        inputs = pq.read_table(data / "application_inputs.parquet").to_pylist()
        stages = apply_stages([{**row, "p_reference": raw_temporal[(row["ts"], row["grp"])]["p"]} for row in inputs], factors)
        stage_sources = [keyed(pq.read_table(RENEW / directory / fold / "predictions.parquet")) for directory in ("calibration_wave/comparisons/temperature_then_snow", "hour_wave/comparisons/hour_bias", "sky_wave/comparisons/cloud_bias")]
        assert set(lineage) == set(raw_temporal) == set(old_mlp)
        for row in stages:
            key = row["ts"], row["grp"]
            saved = lineage[key]
            assert saved["p_raw_temporal"] == raw_temporal[key]["p"] and saved["p_old_mlp"] == old_mlp[key]["p_new"]
            signed = fsum(member[key]["p_raw"] if key in member else 0. for member in seeds) / 3
            assert isclose(saved["p_old_mlp"], max(0., signed), rel_tol=1e-12, abs_tol=1e-8)
            assert saved["p_raw_temporal"] + 1e-8 >= weight * saved["p_old_mlp"]
            for name, expected_stage, source in zip(("p_weather_reference", "p_hour_reference", "p_sky_reference"), ("p_weather", "p_hour", "p_cloud"), stage_sources, strict=True):
                assert saved[name] == source[key]["p"]
                assert isclose(saved[name], row[expected_stage], rel_tol=1e-12, abs_tol=1e-8)
        records.append({"fold": fold, "train_rows": len(train), "evaluation_rows": len(evaluation),
                        "features": len(names), "clipped_rows": int((below | above).any(axis=1).sum()),
                        "clipped_entries": int((below | above).sum()), "training_identity_exact": True})
    evidence = {"status": "PASS", "records": records, "effective_mlp_weight": weight,
                "protocol_sha256": digest(OUT / "protocol.json"), "prepared_manifest_sha256": digest(OUT / "prepared_manifest.json"),
                "scope": "All projected features, original train-only preprocessing, exact matrices and TRAIN bounds, raw stored MLP lineage and unchanged three-stage references; no native model inference or new fit."}
    (OUT / "independent_data_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
