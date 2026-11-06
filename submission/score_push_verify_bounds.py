# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "joblib", "scikit-learn", "threadpoolctl"]
# ///
# How to run: python submission/score_push_verify_bounds.py AFTER the bounds wave is terminal.
"""Verify TRAIN-only feature bounds, six reused models and primary-only selection."""
from __future__ import annotations

import json
from datetime import datetime
from math import fsum, isclose
from typing import Final

import joblib
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from threadpoolctl import threadpool_limits

from autoresearch_verify_final import metrics
from score_push_verify_mlp_data import ROOT, digest, read, keyed
from score_push_verify_refresh import apply_stages
from score_push_verify_calibration import ensure_terminal

RENEW: Final = ROOT / "analysis_outputs/renew_20261105"
OUT: Final = RENEW / "bounds_wave"
OLD: Final = RENEW / "mlp_wave"


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    previous = read(OLD / "independent_check.json")
    assert previous["status"] == "PASS" and previous["models_fully_replayed"] == 6
    protocol = read(OUT / "protocol.json")
    for mapping in (protocol["input_sha256"], protocol["protected_sha256"]):
        for path, expected in mapping.items():
            assert digest(ROOT / path) == expected, path
    for name, record in protocol["own_sources"].items():
        assert digest(ROOT / record["original"]) == digest(OUT / "sources/own" / name) == record["sha256"]
    for name, record in protocol["snapshots"].items():
        assert digest(ROOT / record["original"]) == digest(OUT / "sources" / f"{name}.py") == record["sha256"]
    for manifest in ("prepared_manifest.json", "terminal_manifest.json"):
        for path, expected in read(OUT / manifest).items():
            assert digest(OUT / path) == expected, path
    factors = {}
    for stage in ("weather", "hour", "cloud"):
        name = f"original_{stage}_coefficients.json"
        assert (OUT / name).read_bytes() == (OLD / name).read_bytes()
        factors[stage] = read(OUT / name)["factors"]
    result = read(OUT / "results.json")
    assert result["real_model_fit_count"] == 0 and result["real_inference_count"] == 6 and result["bounds_transform_count"] == 2
    assert not result["confirmation_loaded"] and not result["test_loaded"] and not result["exported"]
    assert len(result["records"]) == 1
    record = result["records"][0]
    alpha = record["alpha_primary_only"]
    assert np.isfinite(alpha) and 0 <= alpha <= 1 and record["seeds"] == [0, 1, 2]
    computed, checked, intervals = {}, [], []
    for fold in ("primary", "recent"):
        data, old_data = OUT / "data" / fold, OLD / "data" / fold
        train = np.load(old_data / "x_train.npy", mmap_mode="r", allow_pickle=False)
        future = np.load(old_data / "x_evaluation.npy", mmap_mode="r", allow_pickle=False)
        lower, upper = train.min(axis=0), train.max(axis=0)
        assert np.isfinite(lower).all() and np.isfinite(upper).all() and (lower < upper).all()
        np.testing.assert_array_equal(np.clip(train, lower, upper), train)
        expected = np.clip(future, lower, upper)
        bounded = np.load(data / "x_evaluation_bounded.npy", allow_pickle=False)
        assert bounded.dtype == np.float64 and bounded.shape == future.shape
        np.testing.assert_array_equal(bounded, expected)
        bounds = pq.read_table(data / "bounds.parquet")
        names = read(old_data / "feature_mask.json")["selected_columns"]
        assert bounds["feature"].to_pylist() == names
        np.testing.assert_array_equal(bounds["feature_index"].to_numpy(), np.arange(len(names)))
        below, above = future < lower, future > upper
        for name, values in (("lower", lower), ("upper", upper), ("below_count", below.sum(axis=0)), ("above_count", above.sum(axis=0)), ("clipped_count", (below | above).sum(axis=0))):
            np.testing.assert_array_equal(bounds[name].to_numpy(), values, err_msg=name)
        inverse = pq.read_table(old_data / "evaluation_transform.parquet")
        scaler = joblib.load(old_data / "target_scaler.joblib")
        members = []
        for seed in range(3):
            model_path = OLD / "trials" / fold / f"seed{seed}/model.joblib"
            assert protocol["input_sha256"][str(model_path.relative_to(ROOT))] == digest(model_path)
            model = joblib.load(model_path)
            with threadpool_limits(limits=16):
                prediction = scaler.inverse_transform(model.predict(bounded).reshape(-1, 1)).ravel() * inverse["inverse_kwh"].to_numpy()
            trial = OUT / "trials" / fold / f"seed{seed}"
            raw = pq.read_table(trial / "daylight_raw.parquet")
            assert raw.select(["ts", "grp"]).to_pylist() == inverse.select(["ts", "grp"]).to_pylist()
            np.testing.assert_array_equal(raw["p_raw"].to_numpy(), prediction)
            members.append(keyed(raw))
            runtime = read(trial / "runtime.json")
            assert runtime["priority_class"] == 32 and runtime["pyarrow_cpu"] == runtime["pyarrow_io"] == 4
            assert all(pool["num_threads"] == 16 for pool in runtime["threadpools"])
            receipt = read(trial / "controller_receipt.json")
            assert receipt["exit_code"] == 0 and receipt["exact_worker_absent"] and receipt["new_model_fits"] == 0
            ensure_terminal(receipt["identity"])
            intervals.append((datetime.fromisoformat(receipt["started_utc"]), datetime.fromisoformat(receipt["finished_utc"])))
        for name in ("labels.parquet", "coverage.parquet", "application_inputs.parquet"):
            assert (data / name).read_bytes() == (old_data / name).read_bytes()
        labels = keyed(pq.read_table(data / "labels.parquet"))
        coverage = keyed(pq.read_table(data / "coverage.parquet"))
        inputs = pq.read_table(data / "application_inputs.parquet").to_pylist()
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
            expected_stage = stages[key]
            assert all(row[n] == labels[key][n] for n in ("y", "smp", "k", "p_reference"))
            assert row["alpha"] == alpha and row["static_capacity"] == expected_stage["static_capacity"]
            values = {"signed_seed_mean": means[key], "p_component": expected_stage["p_reference"], "p_weather": expected_stage["p_weather"], "p_hour": expected_stage["p_hour"], "p_new": expected_stage["p_cloud"], "p": (1 - alpha) * row["p_reference"] + alpha * expected_stage["p_cloud"]}
            for name, value in values.items():
                assert isclose(row[name], value, rel_tol=1e-12, abs_tol=1e-8), (key, name)
            assert 0 <= row["p_new"] <= row["static_capacity"] and (not coverage[key]["night"] or row["p"] == row["p_new"] == 0)
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
        checked.append({"fold": fold, "features": len(names), "rows_clipped": int((below | above).any(axis=1).sum()), "entries_clipped": int((below | above).sum()), "training_identity_exact": True, "native_replays_exact": 3})
    both = all(computed[f]["p"]["W"] < computed[f]["p_reference"]["W"] for f in computed)
    eligible = both and alpha >= .02
    assert record["both_folds_improve"] == both and record["eligible"] == result["eligible"] == eligible
    assert result["selected"] == (record if eligible else None) and result["reference_retained"] == (not eligible)
    controller = read(OUT / "controller_receipt.json")
    assert controller["exit_code"] == 0 and controller["real_model_fit_count"] == 0 and controller["real_inference_count"] == 6
    ensure_terminal(controller["identity"])
    intervals.sort()
    assert len(intervals) == 6 and all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:]))
    assert not (OUT / "tmp").exists() and not list(OUT.rglob("model.joblib"))
    evidence = {"status": "PASS", "records": checked, "models_fitted": 0, "models_replayed": 6, "serial_intervals": len(intervals),
                "alpha_primary_only": alpha, "scores": computed, "eligible": eligible,
                "protected_files": len(protocol["protected_sha256"]), "terminal_manifest_sha256": digest(OUT / "terminal_manifest.json"),
                "limits": "Historically exposed development; no confirmation/test/export or new official score."}
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
