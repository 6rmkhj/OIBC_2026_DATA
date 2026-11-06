# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "lightgbm"]
# ///
# How to run: python submission/score_push_verify_mono.py AFTER the wave is terminal.
"""Replay matched fair models and independently verify their constrained forecasts."""
from __future__ import annotations

import json
from datetime import datetime
from math import fsum, isclose

import lightgbm as lgb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from autoresearch_verify_final import metrics
from score_push_verify_calibration import ensure_terminal
from score_push_verify_mlp_data import read, digest, keyed
from score_push_verify_mono_data import OUT, direction, hashes
from score_push_verify_refresh import apply_stages


def coordinate_check(model, train, names: list[str], constrained: bool):
    signs = np.array([direction(name) for name in names])
    matrix = np.column_stack([train[name].to_numpy() for name in names]).astype(np.float64)
    anchors = matrix[np.linspace(0, len(matrix) - 1, 8, dtype=int)]
    blocks = []
    for column in np.flatnonzero(signs):
        low, high = anchors.copy(), anchors.copy()
        low[:, column] = np.nanmin(matrix[:, column])
        high[:, column] = np.nanmax(matrix[:, column])
        blocks.extend((low, high))
    predictions = model.predict(np.vstack(blocks), num_threads=1).reshape(-1, 2, len(anchors))
    violations = -signs[signs != 0, None] * (predictions[:, 1] - predictions[:, 0])
    assert np.isfinite(violations).all()
    maximum = float(violations.max())
    if constrained:
        assert maximum <= 1e-12, maximum
    return {"coordinates": int((signs != 0).sum()), "anchors": len(anchors),
            "violations_above_tolerance": int((violations > 1e-12).sum()),
            "maximum_violation": maximum, "scope": "Finite train-range coordinate endpoints; no global physical guarantee."}


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
    factors = {stage: read(OUT / f"original_{stage}_coefficients.json")["factors"] for stage in ("weather", "hour", "cloud")}
    results = read(OUT / "results.json")
    assert results["real_model_fit_count"] == 12 and not results["confirmation_loaded"] and not results["test_loaded"] and not results["exported"]
    assert len(results["records"]) == 2 and {r["arm"] for r in results["records"]} == {"fair_control", "fair_monotone"}
    intervals, checks, model_checks = [], [], []
    for record in results["records"]:
        arm, alpha = record["arm"], record["alpha_primary_only"]
        assert record["seeds"] == [0, 1, 2] and np.isfinite(alpha) and 0 <= alpha <= 1
        computed = {}
        for fold in ("primary", "recent"):
            data = OUT / "data" / fold
            train, evaluation = [pq.read_table(data / f"{name}.parquet") for name in ("train", "evaluation")]
            names = read(data / "feature_mask.json")["selected_columns"]
            vector = [direction(name) if arm == "fair_monotone" else 0 for name in names]
            inverse = pq.read_table(data / "evaluation_transform.parquet")["inverse_kwh"].to_numpy()
            members = []
            for seed in range(3):
                trial = OUT / "trials" / arm / fold / f"seed{seed}"
                config = read(trial / "config.json")
                assert config["features"] == names
                assert config["training_rows"] == len(train) and config["prediction_rows"] == len(evaluation)
                assert config["prepared_manifest_sha256"] == digest(OUT / "prepared_manifest.json")
                for name, expected_hash in config["input_sha256"].items():
                    assert digest(data / name) == expected_hash, name
                params = config["parameters"]
                assert params == {**protocol["parameters"], "random_state": None if seed == 0 else seed, "monotone_constraints": vector}
                assert params["random_state"] == (None if seed == 0 else seed)
                assert params["monotone_constraints"] == vector
                model = lgb.Booster(model_file=str(trial / "model.txt"))
                assert model.current_iteration() == model.num_trees() == 400 and model.feature_name() == names
                for name, value in (("objective", "fair"), ("num_threads", 16), ("seed", seed), ("num_leaves", 63), ("min_data_in_leaf", 50), ("bagging_freq", 1), ("monotone_constraints_method", "basic")):
                    assert model.params[name] == value, (arm, fold, seed, name)
                for name, value in (("fair_c", .1), ("learning_rate", .03), ("bagging_fraction", .8), ("feature_fraction", .8)):
                    assert isclose(model.params[name], value, rel_tol=1e-12), name
                assert not model.params["linear_tree"]
                assert model.dump_model()["monotone_constraints"] == vector
                prediction = model.predict(evaluation.select(names).to_pandas(), num_threads=1) * inverse
                raw = pq.read_table(trial / "daylight_raw.parquet")
                assert raw.select(["ts", "grp"]).to_pylist() == evaluation.select(["ts", "grp"]).to_pylist()
                np.testing.assert_array_equal(raw["p_raw"].to_numpy(), prediction)
                members.append(keyed(raw))
                sweep = coordinate_check(model, train, names, arm == "fair_monotone")
                model_checks.append({"arm": arm, "fold": fold, "seed": seed, **sweep})
                replay = read(trial / "replay.json")
                assert replay["passed"] and replay["model_sha256"] == digest(trial / "model.txt")
                assert replay["raw_sha256"] == digest(trial / "daylight_raw.parquet")
                runtime = read(trial / "runtime.json")
                assert runtime["priority_class"] == 32 and runtime["pyarrow_cpu"] == runtime["pyarrow_io"] == 4
                assert not runtime["loaded_existing_model"] and all(pool["num_threads"] == 16 for pool in runtime["threadpools"])
                receipt = read(trial / "controller_receipt.json")
                assert receipt["exit_code"] == 0 and receipt["exact_worker_absent"]
                ensure_terminal(receipt["identity"])
                intervals.append((datetime.fromisoformat(receipt["started_utc"]), datetime.fromisoformat(receipt["finished_utc"])))
            inputs = pq.read_table(data / "application_inputs.parquet").to_pylist()
            labels = keyed(pq.read_table(data / "labels.parquet"))
            coverage = keyed(pq.read_table(data / "coverage.parquet"))
            means, pure = {}, []
            for row in inputs:
                key = row["ts"], row["grp"]
                assert all((key not in member) == coverage[key]["night"] for member in members)
                mean = fsum(member[key]["p_raw"] if key in member else 0. for member in members) / 3
                means[key] = mean
                pure.append({**row, "p_reference": min(row["static_capacity"], max(0., mean))})
            stages = {(r["ts"], r["grp"]): r for r in apply_stages(pure, factors)}
            directory = OUT / "comparisons" / arm / fold
            rows = pq.read_table(directory / "predictions.parquet").to_pylist()
            assert len(rows) == len(labels) and {(r["ts"], r["grp"]) for r in rows} == set(labels) == set(stages)
            for row in rows:
                key = row["ts"], row["grp"]
                stage = stages[key]
                assert all(row[n] == labels[key][n] for n in ("y", "smp", "k", "p_reference"))
                assert row["alpha"] == alpha and row["static_capacity"] == stage["static_capacity"]
                expected = {"signed_seed_mean": means[key], "p_component": stage["p_reference"], "p_weather": stage["p_weather"], "p_hour": stage["p_hour"], "p_new": stage["p_cloud"], "p": (1 - alpha) * row["p_reference"] + alpha * stage["p_cloud"]}
                for name, value in expected.items():
                    assert isclose(row[name], value, rel_tol=1e-12, abs_tol=1e-8), (key, name)
                assert 0 <= row["p_new"] <= row["static_capacity"] and (not coverage[key]["night"] or row["p"] == row["p_new"] == 0)
            computed[fold] = {name: metrics(rows, name) for name in ("p", "p_reference", "p_new")}
            saved = read(directory / "metrics.json")
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
        relative = fsum(computed[f]["p"]["W"] / computed[f]["p_reference"]["W"] for f in computed) / 2
        assert record["both_folds_improve"] == both and record["eligible"] == (both and alpha >= .02)
        assert isclose(record["mean_relative_W"], relative, rel_tol=1e-12)
        checks.append({"arm": arm, "alpha": alpha, "scores": computed, "eligible": record["eligible"]})
    eligible = [r for r in results["records"] if r["eligible"]]
    selected = min(eligible, key=lambda r: r["mean_relative_W"]) if eligible else None
    assert results["selected"] == selected and results["reference_retained"] == (selected is None)
    assert results["eligible"] == bool(eligible) and results["real_calibration_fit_count"] == 0
    compared = {record["arm"]: record["scores"] for record in checks}
    for fold in ("primary", "recent"):
        for kind in ("p_new", "p"):
            control = compared["fair_control"][fold][kind]
            monotone = compared["fair_monotone"][fold][kind]
            saved = results["matched_fair_comparison"][fold][kind]
            expected = {"control_W": control["W"], "monotone_W": monotone["W"], "monotone_minus_control_W": monotone["W"] - control["W"], "control_W_pct": control["W_pct"], "monotone_W_pct": monotone["W_pct"]}
            for name, value in expected.items():
                assert isclose(saved[name], value, rel_tol=1e-12, abs_tol=1e-4), (fold, kind, name)
    intervals.sort()
    assert len(intervals) == 12 and all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:]))
    controller = read(OUT / "controller_receipt.json")
    assert controller["exit_code"] == 0 and controller["real_model_fit_count"] == 12
    ensure_terminal(controller["identity"])
    assert not (OUT / "tmp").exists()
    evidence = {"status": "PASS", "models_fully_replayed": len(model_checks), "serial_intervals": len(intervals),
                "coordinate_checks": model_checks, "records": checks, "selected_arm": selected["arm"] if selected else None,
                "protected_files": len(protocol["protected_sha256"]), "terminal_manifest_sha256": digest(OUT / "terminal_manifest.json"),
                "limits": "Historically exposed development; partial finite-coordinate constraints only; no confirmation/test/export or new official score."}
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
