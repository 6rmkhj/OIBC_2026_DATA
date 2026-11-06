# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "joblib", "scikit-learn", "threadpoolctl"]
# ///
# How to run: python submission/score_push_verify_incbound.py AFTER terminal sealing.
"""Verify all incumbent neural replays and a fixed-weight component substitution."""
from __future__ import annotations

import json
from datetime import datetime
from math import fsum, isclose

import joblib
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from threadpoolctl import threadpool_limits

from autoresearch_verify_final import metrics
from score_push_verify_calibration import ensure_terminal
from score_push_verify_mlp_data import read, digest, keyed
from score_push_verify_incbound_data import OUT, OLD, hashes, effective_weight
from score_push_verify_refresh import apply_stages


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    hashes()
    prefit = read(OUT / "independent_data_check.json")
    assert prefit["status"] == "PASS" and prefit["protocol_sha256"] == digest(OUT / "protocol.json")
    assert prefit["prepared_manifest_sha256"] == digest(OUT / "prepared_manifest.json")
    for path, expected in read(OUT / "terminal_manifest.json").items():
        assert digest(OUT / path) == expected, path
    factors = {stage: read(OUT / f"original_{stage}_coefficients.json")["factors"] for stage in ("weather", "hour", "cloud")}
    weight = effective_weight()
    results = read(OUT / "results.json")
    assert results["real_model_fit_count"] == results["real_calibration_fit_count"] == 0
    assert results["native_model_inferences"] == 12 and results["native_worker_count"] == 6
    assert not results["confirmation_loaded"] and not results["test_loaded"] and not results["exported"]
    assert results["new_weight_fits"] == results["new_alpha_fits"] == 0 and len(results["records"]) == 1
    record = results["records"][0]
    assert record["effective_mlp_weight"] == weight and record["seeds"] == [0, 1, 2]
    computed, intervals, checks = {}, [], []
    for fold in ("primary", "recent"):
        data = OUT / "data" / fold
        x_original = np.load(data / "x_evaluation_original.npy", allow_pickle=False)
        x_bounded = np.load(data / "x_evaluation_bounded.npy", allow_pickle=False)
        unchanged_inputs = (x_original == x_bounded).all(axis=1)
        inverse = pq.read_table(data / "evaluation_transform.parquet")
        members = []
        for seed in range(3):
            source = OLD / "learner_wave" / fold / f"mlp_cf/seed{seed}"
            trial = OUT / "trials" / fold / f"seed{seed}"
            model = joblib.load(source / "model.joblib")
            target = joblib.load(source / "target_scaler.joblib")
            with threadpool_limits(limits=1):
                original = target.inverse_transform(model.predict(x_original).reshape(-1, 1)).ravel() * inverse["capacity_kw"].to_numpy()
                bounded = target.inverse_transform(model.predict(x_bounded).reshape(-1, 1)).ravel() * inverse["capacity_kw"].to_numpy()
            source_raw = pq.read_table(source / "daylight_raw.parquet")
            assert source_raw.select(["ts", "grp"]).to_pylist() == inverse.select(["ts", "grp"]).to_pylist()
            np.testing.assert_array_equal(original, source_raw["p_raw"].to_numpy())
            np.testing.assert_array_equal(original[unchanged_inputs], bounded[unchanged_inputs])
            for filename, prediction in (("original_raw.parquet", original), ("bounded_raw.parquet", bounded)):
                saved = pq.read_table(trial / filename)
                assert saved.select(["ts", "grp"]).to_pylist() == inverse.select(["ts", "grp"]).to_pylist()
                np.testing.assert_array_equal(saved["p_raw"].to_numpy(), prediction)
            members.append(keyed(pq.read_table(trial / "bounded_raw.parquet")))
            replay = read(trial / "replay.json")
            assert replay["original_full_exact"] and replay["original_max_absolute_error"] == 0
            assert replay["source_model_sha256"] == digest(source / "model.joblib")
            assert replay["source_original_raw_sha256"] == digest(source / "daylight_raw.parquet")
            for filename in ("original_raw", "bounded_raw"):
                assert replay[filename + "_sha256"] == digest(trial / (filename + ".parquet"))
            assert replay["native_model_inferences"] == 2 and replay["new_model_fits"] == 0
            config = read(trial / "config.json")
            assert config["new_model_fits"] == 0 and config["native_model_inferences"] == 2
            assert config["prepared_manifest_sha256"] == digest(OUT / "prepared_manifest.json")
            for name, path in (("source_model_sha256", source / "model.joblib"), ("source_preprocessor_sha256", source / "input_preprocessing.joblib"), ("source_target_scaler_sha256", source / "target_scaler.joblib"), ("source_config_sha256", source / "config.json"), ("original_matrix_sha256", data / "x_evaluation_original.npy"), ("bounded_matrix_sha256", data / "x_evaluation_bounded.npy"), ("capacity_inverse_sha256", data / "evaluation_transform.parquet")):
                assert config[name] == digest(path), name
            runtime = read(trial / "runtime.json")
            assert runtime["priority_class"] == 32 and runtime["pyarrow_cpu"] == runtime["pyarrow_io"] == 4
            assert runtime["historical_inference_blas_threads"] == 1
            assert all(pool["num_threads"] == 1 if pool["user_api"] == "blas" else 1 <= pool["num_threads"] <= 16 for pool in runtime["threadpools"])
            receipt = read(trial / "controller_receipt.json")
            assert receipt["exit_code"] == 0 and receipt["exact_worker_absent"]
            ensure_terminal(receipt["identity"])
            intervals.append((datetime.fromisoformat(receipt["started_utc"]), datetime.fromisoformat(receipt["finished_utc"])))
        lineage = keyed(pq.read_table(data / "lineage.parquet"))
        labels = keyed(pq.read_table(data / "labels.parquet"))
        coverage = keyed(pq.read_table(data / "coverage.parquet"))
        inputs = pq.read_table(data / "application_inputs.parquet").to_pylist()
        new_mlp, raw_candidates, stage_inputs = {}, {}, []
        for row in inputs:
            key = row["ts"], row["grp"]
            assert all((key not in member) == coverage[key]["night"] for member in members)
            mean = fsum(member[key]["p_raw"] if key in member else 0. for member in members) / 3
            new_mlp[key] = max(0., mean)
            raw = lineage[key]["p_raw_temporal"] + weight * (new_mlp[key] - lineage[key]["p_old_mlp"])
            assert raw >= -1e-8
            raw_candidates[key] = raw
            stage_inputs.append({**row, "p_reference": raw})
        stages = {(r["ts"], r["grp"]): r for r in apply_stages(stage_inputs, factors)}
        directory = OUT / "comparisons" / fold
        rows = pq.read_table(directory / "predictions.parquet").to_pylist()
        assert len(rows) == len(labels) and {(r["ts"], r["grp"]) for r in rows} == set(labels) == set(stages)
        assert "alpha" not in rows[0]
        changed = 0
        for row in rows:
            key = row["ts"], row["grp"]
            old = lineage[key]
            assert all(row[n] == labels[key][n] for n in ("y", "smp", "k", "p_reference"))
            assert row["p_old_mlp"] == old["p_old_mlp"] and row["p_raw_temporal"] == old["p_raw_temporal"]
            expected = {"p_bounded_mlp": new_mlp[key], "mlp_delta": new_mlp[key] - old["p_old_mlp"],
                        "p_raw_candidate": raw_candidates[key], "p_weather": stages[key]["p_weather"],
                        "p_hour": stages[key]["p_hour"], "p": stages[key]["p_cloud"]}
            for name, value in expected.items():
                assert isclose(row[name], value, rel_tol=1e-12, abs_tol=1e-8), (key, name)
            assert 0 <= row["p"] <= row["static_capacity"] and (not coverage[key]["night"] or row["p"] == 0)
            if row["mlp_delta"] == 0:
                assert row["p_raw_candidate"] == old["p_raw_temporal"] and row["p"] == row["p_reference"]
            changed += row["p"] != row["p_reference"]
        computed[fold] = {name: metrics(rows, name) for name in ("p", "p_reference")}
        saved = read(directory / "metrics.json")
        for name, values in computed[fold].items():
            for metric, value in values.items():
                assert isclose(value, saved[name][metric], rel_tol=1e-12, abs_tol=1e-4)
                assert saved[name][metric] == record["scores"][fold][name][metric]
        checks.append({"fold": fold, "rows": len(rows), "changed_predictions": changed,
                       "native_original_replays_exact": 3, "native_bounded_replays_exact": 3})
    both = all(computed[f]["p"]["W"] < computed[f]["p_reference"]["W"] for f in computed)
    assert results["eligible"] == both and results["reference_retained"] == (not both)
    assert record["eligible"] == record["both_folds_improve"] == both
    assert results["selected"] == (record if both else None)
    intervals.sort()
    assert len(intervals) == 6 and all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:]))
    controller = read(OUT / "controller_receipt.json")
    assert controller["exit_code"] == 0 and controller["real_model_fit_count"] == 0 and controller["native_model_inferences"] == 12
    ensure_terminal(controller["identity"])
    assert not (OUT / "tmp").exists()
    evidence = {"status": "PASS", "records": checks, "effective_mlp_weight": weight, "scores": computed,
                "eligible": both, "models_fitted": 0, "native_inferences_replayed": 12, "serial_intervals": len(intervals),
                "terminal_manifest_sha256": digest(OUT / "terminal_manifest.json"),
                "limits": "Historically exposed development; frozen weight substitution, no new fit or official score."}
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
