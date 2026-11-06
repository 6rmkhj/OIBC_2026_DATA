# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "joblib", "scikit-learn", "threadpoolctl"]
# ///
# How to run: python submission/score_push_verify_mlp.py AFTER all six models and terminal manifest.
"""Replay every saved neural model and independently verify its final decision."""
from __future__ import annotations

import json
from datetime import datetime
from math import fsum, isclose, isfinite

import joblib
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import sklearn
from threadpoolctl import threadpool_limits

from autoresearch_verify_final import metrics
from score_push_verify_mlp_data import OUT, ROOT, digest, read, keyed
from score_push_verify_refresh import apply_stages
from score_push_verify_calibration import ensure_terminal


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol, prefit = read(OUT / "protocol.json"), read(OUT / "independent_data_check.json")
    assert prefit["status"] == "PASS" and prefit["protocol_sha256"] == digest(OUT / "protocol.json")
    assert prefit["prepared_manifest_sha256"] == digest(OUT / "prepared_manifest.json")
    assert sklearn.__version__ == read(OUT / "evidence/environment.json")["sklearn_version"]
    amendment = read(OUT / "source_amendment.json")
    assert amendment["original_protocol_sha256"] == digest(OUT / "protocol.json")
    for name, record in (protocol["own_sources"] | amendment["own_sources"]).items():
        assert digest(ROOT / record["original"]) == record["sha256"]
        assert digest(OUT / record.get("snapshot", "sources/own/" + name)) == record["sha256"]
    for name, record in protocol["snapshots"].items():
        assert digest(ROOT / record["original"]) == digest(OUT / "sources" / f"{name}.py") == record["sha256"]
    for mapping in (protocol["input_sha256"], protocol["protected_sha256"]):
        for path, expected in mapping.items():
            assert digest(ROOT / path) == expected, path
    for manifest in ("prepared_manifest.json", "terminal_manifest.json"):
        for path, expected in read(OUT / manifest).items():
            assert digest(OUT / path) == expected, path
    release = read(OUT / "release.json")
    assert release["approved"]
    for field, name in (("protocol_sha256", "protocol.json"), ("prepared_manifest_sha256", "prepared_manifest.json"), ("source_amendment_sha256", "source_amendment.json")):
        assert release[field] == digest(OUT / name)
    factors = {stage: read(OUT / f"original_{stage}_coefficients.json")["factors"] for stage in ("weather", "hour", "cloud")}
    for stage in factors:
        assert digest(OUT / f"original_{stage}_coefficients.json") == protocol["original_coefficients_sha256"][stage]
    result = read(OUT / "results.json")
    assert result["candidate_count"] == 1 and result["real_model_fit_count"] == 6 and result["real_calibration_fit_count"] == 0
    assert not result["confirmation_loaded"] and not result["test_loaded"] and not result["exported"]
    assert len(result["records"]) == 1
    record = result["records"][0]
    alpha = record["alpha_primary_only"]
    assert isfinite(alpha) and 0 <= alpha <= 1 and record["seeds"] == [0, 1, 2]
    intervals, model_records, computed = [], [], {}
    for fold in ("primary", "recent"):
        data = OUT / "data" / fold
        mask = read(data / "feature_mask.json")
        future = np.load(data / "x_evaluation.npy", allow_pickle=False)
        scaler = joblib.load(data / "target_scaler.joblib")
        inverse = pq.read_table(data / "evaluation_transform.parquet")
        members = []
        for seed in range(3):
            directory = OUT / "trials" / fold / f"seed{seed}"
            config = read(directory / "config.json")
            assert config["parameters"] == {**protocol["parameters"], "random_state": seed}
            assert config["prepared_manifest_sha256"] == digest(OUT / "prepared_manifest.json")
            assert config["train_rows"] == mask["train_rows"] and config["evaluation_rows"] == len(future)
            assert config["feature_count"] == len(mask["selected_columns"]) == future.shape[1]
            assert config["dtype"] == "float64" and config["sample_weight_used"]
            for name, expected in config["matrix_sha256"].items():
                assert digest(data / name) == expected, name
            model = joblib.load(directory / "model.joblib")
            for name, value in config["parameters"].items():
                assert getattr(model, name) == (tuple(value) if name == "hidden_layer_sizes" else value), name
            assert model.loss == "squared_error" and model.out_activation_ == "identity" and model.n_outputs_ == 1
            assert model.n_layers_ == 4 and model.n_features_in_ == future.shape[1]
            assert [layer.shape for layer in model.coefs_] == [(future.shape[1], 64), (64, 32), (32, 1)]
            assert [bias.shape for bias in model.intercepts_] == [(64,), (32,), (1,)]
            assert all(value.dtype == np.float64 and np.isfinite(value).all() for value in [*model.coefs_, *model.intercepts_])
            assert 1 <= model.n_iter_ <= 400 and model.t_ == config["train_rows"] * model.n_iter_
            convergence = read(directory / "convergence.json")
            assert convergence["iterations"] == model.n_iter_ and convergence["all_seeds_retained"]
            np.testing.assert_array_equal(model.loss_curve_, convergence["loss_curve"])
            assert len(model.loss_curve_) == model.n_iter_ and np.isfinite(model.loss_curve_).all()
            assert model.loss_ == convergence["last_loss"] == model.loss_curve_[-1]
            with threadpool_limits(limits=16):
                prediction = scaler.inverse_transform(model.predict(future).reshape(-1, 1)).ravel() * inverse["inverse_kwh"].to_numpy()
            raw = pq.read_table(directory / "daylight_raw.parquet")
            assert raw.select(["ts", "grp"]).to_pylist() == inverse.select(["ts", "grp"]).to_pylist()
            np.testing.assert_array_equal(prediction, raw["p_raw"].to_numpy())
            members.append(keyed(raw))
            replay = read(directory / "replay.json")
            assert replay["passed"] and replay["max_absolute_error"] == 0 and replay["inverse_target_scaler_once"]
            assert replay["model_sha256"] == digest(directory / "model.joblib") and replay["raw_sha256"] == digest(directory / "daylight_raw.parquet")
            runtime = read(directory / "runtime.json")
            assert not runtime["loaded_existing_model"] and runtime["priority_class"] == 32
            assert runtime["pyarrow_cpu"] == runtime["pyarrow_io"] == 4
            assert all(pool["num_threads"] == 16 for pool in runtime["threadpools"])
            receipt = read(directory / "controller_receipt.json")
            assert receipt["exit_code"] == 0 and receipt["exact_worker_absent"]
            ensure_terminal(receipt["identity"])
            intervals.append((datetime.fromisoformat(receipt["started_utc"]), datetime.fromisoformat(receipt["finished_utc"])))
            model_records.append({"fold": fold, "seed": seed, "iterations": model.n_iter_, "warnings": convergence["warnings"], "full_replay_exact": True})
        inputs = pq.read_table(data / "application_inputs.parquet").to_pylist()
        labels = keyed(pq.read_table(data / "labels.parquet"))
        coverage = keyed(pq.read_table(data / "coverage.parquet"))
        means, pure_rows = {}, []
        for row in inputs:
            key = row["ts"], row["grp"]
            assert all((key not in member) == coverage[key]["night"] for member in members)
            mean = fsum(member[key]["p_raw"] if key in member else 0. for member in members) / 3
            means[key] = mean
            pure_rows.append({**row, "p_reference": min(row["static_capacity"], max(0., mean))})
        stages = {(r["ts"], r["grp"]): r for r in apply_stages(pure_rows, factors)}
        rows = pq.read_table(OUT / "comparisons" / fold / "predictions.parquet").to_pylist()
        assert len(rows) == len(labels) and {(r["ts"], r["grp"]) for r in rows} == set(labels) == set(stages)
        for row in rows:
            key = row["ts"], row["grp"]
            expected = stages[key]
            assert all(row[n] == labels[key][n] for n in ("y", "smp", "k", "p_reference"))
            assert row["alpha"] == alpha and row["static_capacity"] == expected["static_capacity"]
            values = {"signed_seed_mean": means[key], "p_component": expected["p_reference"], "p_weather": expected["p_weather"], "p_hour": expected["p_hour"], "p_new": expected["p_cloud"], "p": (1 - alpha) * row["p_reference"] + alpha * expected["p_cloud"]}
            for name, value in values.items():
                assert isclose(row[name], value, rel_tol=1e-12, abs_tol=1e-8), (key, name)
            assert 0 <= row["p_new"] <= row["static_capacity"] and (not coverage[key]["night"] or row["p_new"] == row["p"] == 0)
        computed[fold] = {name: metrics(rows, name) for name in ("p", "p_reference", "p_new")}
        saved = read(OUT / "comparisons" / fold / "metrics.json")
        for name, values in computed[fold].items():
            for metric, value in values.items():
                assert isclose(value, saved[name][metric], rel_tol=1e-12, abs_tol=1e-4)
                assert saved[name][metric] == record["scores"][fold][name][metric]
        if fold == "primary":
            ratios = sorted(((r["y"] - r["p_reference"]) / (r["p_new"] - r["p_reference"]), r["smp"] * r["k"] * abs(r["p_new"] - r["p_reference"])) for r in rows if r["p_new"] != r["p_reference"] and r["smp"] * r["k"] > 0)
            half, cumulative, optimum = fsum(w for _, w in ratios) / 2, 0., 0.
            for ratio, weight in ratios:
                cumulative += weight
                if cumulative >= half:
                    optimum = min(1., max(0., ratio))
                    break
            minimum = fsum(r["smp"] * r["k"] * abs(r["y"] - ((1 - optimum) * r["p_reference"] + optimum * r["p_new"])) for r in rows)
            assert isclose(minimum, computed[fold]["p"]["W"], rel_tol=1e-12, abs_tol=1e-4)
    both = all(computed[f]["p"]["W"] < computed[f]["p_reference"]["W"] for f in computed)
    eligible = both and alpha >= .02
    assert record["both_folds_improve"] == both and record["eligible"] == result["eligible"] == eligible
    assert result["selected"] == (record if eligible else None) and result["reference_retained"] == (not eligible)
    intervals.sort()
    assert len(model_records) == len(intervals) == 6 and all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:]))
    controller = read(OUT / "controller_receipt.json")
    assert controller["exit_code"] == 0 and controller["real_model_fit_count"] == 6 and controller["real_calibration_fit_count"] == 0
    ensure_terminal(controller["identity"])
    assert not (OUT / "tmp").exists()
    evidence = {"status": "PASS", "models": model_records, "models_fully_replayed": 6, "serial_intervals": len(intervals),
                "alpha_primary_only": alpha, "scores": computed, "eligible": eligible, "primary_blend_fits": 1,
                "frozen_calibration_refits": 0, "protected_files": len(protocol["protected_sha256"]),
                "terminal_manifest_sha256": digest(OUT / "terminal_manifest.json"),
                "limits": "Historically exposed development; no confirmation/test/export or new official score."}
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
