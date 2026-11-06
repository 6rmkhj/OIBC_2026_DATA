# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "lightgbm"]
# ///
# How to run: python submission/score_push_verify_poisson.py AFTER terminal seal.
"""Replay six Poisson boosters and independently verify the frozen complement."""
from __future__ import annotations

import json
from datetime import datetime
from math import fsum, isclose

import lightgbm as lgb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from autoresearch_verify_final import metrics
from score_push_verify_calibration import ensure_terminal, snowy, temperature
from score_push_verify_mlp_data import digest, keyed, read
from score_push_verify_poisson_data import OUT, hashes


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    hashes()
    protocol = read(OUT / "protocol.json")
    prefit = read(OUT / "independent_data_check.json")
    assert prefit["status"] == "PASS" and prefit["protocol_sha256"] == digest(OUT / "protocol.json")
    assert prefit["prepared_manifest_sha256"] == digest(OUT / "prepared_manifest.json")
    for path, expected in read(OUT / "terminal_manifest.json").items():
        assert digest(OUT / path) == expected, path
    factors = read(OUT / "original_weather_coefficients.json")["factors"]
    results = read(OUT / "results.json")
    assert results["real_model_fit_count"] == 6 and results["candidate_count"] == 1
    assert results["real_calibration_fit_count"] == 0
    assert not any(results[name] for name in ("confirmation_loaded", "test_loaded", "exported"))
    assert len(results["records"]) == 1
    record = results["records"][0]
    assert record["arm"] == "poisson_normalized_station_decay180" and record["seeds"] == [0, 1, 2]
    alpha = record["alpha_primary_only"]
    assert np.isfinite(alpha) and 0 <= alpha <= 1
    computed, intervals, checks = {}, [], []
    for fold in ("primary", "recent"):
        data = OUT / "data" / fold
        evaluation = pq.read_table(data / "evaluation.parquet")
        spec = read(data / "feature_mask.json")
        names = spec["selected_columns"]
        inverse = pq.read_table(data / "evaluation_transform.parquet")["inverse_kwh"].to_numpy()
        members = []
        for seed in range(3):
            trial = OUT / "trials" / fold / f"seed{seed}"
            config = read(trial / "config.json")
            params = {**protocol["parameters"], "random_state": None if seed == 0 else seed}
            assert config["parameters"] == params and config["features"] == names
            assert config["training_rows"] == spec["train_rows"] and config["prediction_rows"] == len(evaluation)
            assert config["prepared_manifest_sha256"] == digest(OUT / "prepared_manifest.json")
            for name, expected in config["input_sha256"].items():
                assert digest(data / name) == expected, name
            model = lgb.Booster(model_file=str(trial / "model.txt"))
            assert model.current_iteration() == model.num_trees() == 400 and model.feature_name() == names
            for name, value in (("objective", "poisson"), ("seed", seed), ("num_threads", 16),
                                ("num_leaves", 63), ("min_data_in_leaf", 50), ("bagging_freq", 1)):
                assert model.params[name] == value, name
            for name, value in (("learning_rate", .03), ("bagging_fraction", .8),
                                ("feature_fraction", .8), ("poisson_max_delta_step", .7)):
                assert isclose(model.params[name], value, rel_tol=1e-12), name
            future = evaluation.select(names).to_pandas()
            response = model.predict(future, num_threads=1, validate_features=True)
            raw_score = model.predict(future, raw_score=True, num_threads=1, validate_features=True)
            np.testing.assert_allclose(response, np.exp(raw_score), rtol=1e-13, atol=0)
            prediction = response * inverse
            assert np.isfinite(prediction).all() and (prediction > 0).all()
            raw = pq.read_table(trial / "daylight_raw.parquet")
            assert raw.select(["ts", "grp"]).to_pylist() == evaluation.select(["ts", "grp"]).to_pylist()
            np.testing.assert_array_equal(raw["p_raw"].to_numpy(), prediction)
            members.append(keyed(raw))
            replay = read(trial / "replay.json")
            assert replay["passed"] and replay["inverse_once"] and replay["negative_raw"] == 0
            assert replay["model_sha256"] == digest(trial / "model.txt")
            assert replay["raw_sha256"] == digest(trial / "daylight_raw.parquet")
            runtime = read(trial / "runtime.json")
            assert runtime["new_model_fits"] == 1 and not runtime["loaded_existing_model"]
            assert runtime["priority_class"] == 32 and runtime["pyarrow_cpu"] == runtime["pyarrow_io"] == 4
            assert all(pool["num_threads"] == 16 for pool in runtime["threadpools"])
            receipt = read(trial / "controller_receipt.json")
            assert receipt["exit_code"] == 0 and receipt["exact_worker_absent"]
            ensure_terminal(receipt["identity"])
            intervals.append((datetime.fromisoformat(receipt["started_utc"]), datetime.fromisoformat(receipt["finished_utc"])))
            checks.append({"fold": fold, "seed": seed, "rows_replayed": len(prediction),
                           "native_response_exact": True, "log_link_checked": True, "warnings": runtime["warnings"]})
        inputs = keyed(pq.read_table(data / "application_inputs.parquet"))
        labels = keyed(pq.read_table(data / "labels.parquet"))
        coverage = keyed(pq.read_table(data / "coverage.parquet"))
        directory = OUT / "comparisons" / fold
        rows = pq.read_table(directory / "predictions.parquet").to_pylist()
        assert len(rows) == len(labels) and {(r["ts"], r["grp"]) for r in rows} == set(labels) == set(inputs)
        for row in rows:
            key = row["ts"], row["grp"]
            source = inputs[key]
            assert all((key not in member) == coverage[key]["night"] for member in members)
            assert all(row[n] == labels[key][n] for n in ("y", "smp", "k", "p_reference"))
            mean = fsum(member[key]["p_raw"] if key in member else 0. for member in members) / 3
            clipped = min(source["static_capacity"], max(0., mean))
            bin_index = temperature(source)
            temp_factor = 1. if bin_index == -1 else factors["temperature"][bin_index]["factor"]
            snow_factor = factors["conditional_snow"]["factor"] if snowy(source) else 1.
            correction = 1. + .5 * (min(1.15, max(.85, temp_factor * snow_factor)) - 1.)
            weather = min(source["static_capacity"], max(0., clipped * correction))
            expected = {"signed_seed_mean": mean, "p_component": clipped, "p_weather": weather,
                        "p_new": weather, "p": (1 - alpha) * row["p_reference"] + alpha * weather}
            assert row["alpha"] == alpha and row["static_capacity"] == source["static_capacity"]
            for name, value in expected.items():
                assert isclose(row[name], value, rel_tol=1e-12, abs_tol=1e-8), (key, name)
            assert 0 <= row["p_new"] <= row["static_capacity"]
            assert not coverage[key]["night"] or row["p"] == row["p_new"] == 0
        computed[fold] = {name: metrics(rows, name) for name in ("p", "p_reference", "p_new")}
        saved = read(directory / "metrics.json")
        for name, values in computed[fold].items():
            for metric, value in values.items():
                assert isclose(value, saved[name][metric], rel_tol=1e-12, abs_tol=1e-4)
                assert saved[name][metric] == record["scores"][fold][name][metric]
        if fold == "primary":
            ratios = sorted(((r["y"] - r["p_reference"]) / (r["p_new"] - r["p_reference"]),
                             r["smp"] * r["k"] * abs(r["p_new"] - r["p_reference"]))
                            for r in rows if r["p_new"] != r["p_reference"] and r["smp"] * r["k"] > 0)
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
    assert record["both_folds_improve"] == both and record["eligible"] == eligible
    assert results["eligible"] == eligible and results["reference_retained"] == (not eligible)
    assert results["selected"] == (record if eligible else None)
    intervals.sort()
    assert len(intervals) == 6 and all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:]))
    controller = read(OUT / "controller_receipt.json")
    assert controller["exit_code"] == 0 and controller["real_model_fit_count"] == 6
    ensure_terminal(controller["identity"])
    assert not (OUT / "tmp").exists()
    evidence = {"status": "PASS", "models_fully_replayed": 6, "native_tree_count": 2400,
                "serial_intervals": 6, "model_checks": checks, "alpha": alpha, "scores": computed,
                "eligible": eligible, "protected_files": len(protocol["protected_sha256"]),
                "terminal_manifest_sha256": digest(OUT / "terminal_manifest.json"),
                "limits": "All history exposed; no independent holdout, new official score, confirmation/test or export."}
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
