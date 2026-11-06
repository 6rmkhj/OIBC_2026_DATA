# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: python submission/score_push_verify_yield.py
"""Verify site-yield models, once-calibrated ensembles and blend selection."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from math import fsum, isclose, isfinite

import lightgbm as lgb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from autoresearch_verify_final import metrics
from score_push_verify_yield_data import OUT, ROOT, digest

sys.path.insert(0, str(ROOT / "submission/score_push_renew"))
from temporal_common import ensure_terminal


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = json.loads((OUT / "protocol.json").read_text())
    prefit = json.loads((OUT / "independent_data_check.json").read_text())
    assert prefit["status"] == "PASS" and prefit["protocol_sha256"] == digest(OUT / "protocol.json")
    assert prefit["prepared_manifest_sha256"] == digest(OUT / "prepared_manifest.json")
    transformed = json.loads((OUT / "independent_transform_check.json").read_text())
    assert transformed["status"] == "PASS" and transformed["transform_manifest_sha256"] == digest(OUT / "transform_manifest.json")
    for mapping in (protocol["protected_sha256"], protocol["input_sha256"]):
        for path, expected in mapping.items():
            assert digest(ROOT / path) == expected, path
    amendment = json.loads((OUT / "source_amendment.json").read_text())
    assert amendment["original_protocol_sha256"] == digest(OUT / "protocol.json")
    for name, record in {**protocol["own_sources"], **amendment["own_sources"]}.items():
        assert digest(ROOT / record["original"]) == digest(OUT / record.get("snapshot", f"sources/own/{name}")) == record["sha256"]
    for name, record in protocol["snapshots"].items():
        assert digest(OUT / "sources" / f"{name}.py") == record["sha256"]
    for manifest in ("prepared_manifest.json", "transform_manifest.json"):
        for path, expected in json.loads((OUT / manifest).read_text()).items():
            assert digest(OUT / path) == expected, path
    terminal = json.loads((OUT / "terminal_manifest.json").read_text())
    for path, expected in terminal["sha256"].items():
        assert digest(OUT / path) == expected, path
    assert digest(OUT / "selected_coefficients.json") == protocol["coefficient_sha256"]
    assert digest(OUT / "static_capacity.json") == protocol["static_capacity_sha256"]
    factors = json.loads((OUT / "selected_coefficients.json").read_text())["factors"]
    temperature = [r["factor"] for r in factors["temperature"]]
    snow_factor = factors["conditional_snow"]["factor"]
    capacities = json.loads((OUT / "static_capacity.json").read_text())
    results = json.loads((OUT / "results.json").read_text())
    assert results["real_model_fit_count"] == 6 and results["real_site_gain_fit_count"] == 2
    assert not results["confirmation_loaded"] and not results["test_loaded"]
    assert len(results["records"]) == 1 and {r["arm"] for r in results["records"]} == {"site_yield"}
    checked, intervals, model_count = [], [], 0
    for record in results["records"]:
        arm, alpha = record["arm"], record["alpha_primary_only"]
        assert record["seeds"] == [0, 1, 2] and isfinite(alpha) and 0 <= alpha <= 1
        computed = {}
        for fold in ("primary", "recent"):
            directory = OUT / "data" / fold
            frame = pq.read_table(directory / "evaluation.parquet")
            spec = json.loads((directory / "features.json").read_text())
            weight_file = directory / "training_transform.parquet"
            zero_weights = int((pq.read_table(weight_file, columns=["sample_weight"])["sample_weight"].to_numpy() == 0).sum())
            evaluation_transform = pq.read_table(directory / "evaluation_transform.parquet")
            assert evaluation_transform.select(["ts", "grp"]).to_pylist() == frame.select(["ts", "grp"]).to_pylist()
            inverse = evaluation_transform["new_normalizer"].to_numpy() * frame["capacity_kw"].to_numpy()
            members = []
            for seed in range(3):
                trial = OUT / "trials" / arm / fold / f"seed{seed}"
                config = json.loads((trial / "config.json").read_text())
                assert config["features"] == spec["features"] and config["train_rows"] == spec["train_rows"]
                assert config["weights_sha256"] == digest(weight_file) and config["zero_weight_rows"] == zero_weights == 0
                assert config["coefficient_sha256"] == digest(OUT / "coefficients" / f"{fold}.json")
                assert config["transform_manifest_sha256"] == digest(OUT / "transform_manifest.json")
                assert config["parameters"] == {**protocol["parameters"], "random_state": None if seed == 0 else seed}
                model = lgb.Booster(model_file=str(trial / "model.txt"))
                assert model.current_iteration() == model.num_trees() == 400 and model.feature_name() == config["features"]
                assert model.params["objective"] == "regression_l1" and model.params["num_leaves"] == 63
                assert model.params["num_threads"] == 16 and model.params["seed"] == seed
                assert model.params["min_data_in_leaf"] == 50 and model.params["bagging_freq"] == 1
                for name, expected in (("learning_rate", .03), ("bagging_fraction", .8), ("feature_fraction", .8)):
                    assert isclose(model.params[name], expected)
                prediction = model.predict(frame.select(config["features"]).to_pandas(), num_threads=1) * inverse
                raw = pq.read_table(trial / "daylight_raw.parquet")
                np.testing.assert_array_equal(prediction, raw["p_raw"].to_numpy())
                assert frame.select(["ts", "grp"]).to_pylist() == raw.select(["ts", "grp"]).to_pylist()
                members.append({(r["ts"], r["grp"]): r["p_raw"] for r in raw.to_pylist()})
                replay = json.loads((trial / "replay.json").read_text())
                assert replay["passed"] and replay["model_sha256"] == digest(trial / "model.txt")
                assert replay["raw_sha256"] == digest(trial / "daylight_raw.parquet")
                runtime = json.loads((trial / "runtime.json").read_text())
                assert not runtime["loaded_existing_model"] and runtime["priority_class"] == 32
                assert runtime["pyarrow_cpu"] == runtime["pyarrow_io"] == 4
                assert all(pool["num_threads"] == 16 for pool in runtime["threadpools"])
                receipt = json.loads((trial / "controller_receipt.json").read_text())
                assert receipt["exit_code"] == 0 and receipt["exact_worker_absent"]
                ensure_terminal(receipt["identity"])
                intervals.append((datetime.fromisoformat(receipt["started_utc"]), datetime.fromisoformat(receipt["finished_utc"])))
                model_count += 1
            weather = {(r["ts"], r["grp"]): r for r in frame.select(["ts", "grp", "wa_temp", "extra_wa_snow"]).to_pylist()}
            labels = {(r["ts"], r["grp"]): r for r in pq.read_table(directory / "labels.parquet").to_pylist()}
            coverage = {(r["ts"], r["grp"]): r["night"] for r in pq.read_table(directory / "coverage.parquet").to_pylist()}
            rows = pq.read_table(OUT / "comparisons" / arm / "ensemble" / fold / "predictions.parquet").to_pylist()
            assert len(rows) == len(labels) and {(r["ts"], r["grp"]) for r in rows} == set(labels) == set(coverage)
            for row in rows:
                key = row["ts"], row["grp"]
                assert all(row[n] == labels[key][n] for n in ("y", "smp", "k", "p_reference"))
                mean = fsum(member.get(key, 0.) for member in members) / 3
                assert (key not in members[0]) == coverage[key]
                pure = max(0., min(capacities[row["grp"]], mean))
                feature = weather.get(key)
                factor = 1.
                if feature is not None:
                    temp, snow = feature["wa_temp"], feature["extra_wa_snow"]
                    if temp is not None and isfinite(temp):
                        factor *= temperature[sum(temp >= cut for cut in (0, 10, 20, 30))]
                    if snow is not None and isfinite(snow) and snow >= .001:
                        factor *= snow_factor
                effective = 1 + .5 * (max(.85, min(1.15, factor)) - 1)
                candidate = max(0., min(capacities[row["grp"]], pure * effective))
                mixed = (1 - alpha) * row["p_reference"] + alpha * candidate
                for field, expected in (("signed_seed_mean", mean), ("component_before_calibration", pure), ("raw_factor", factor), ("effective_factor", effective), ("p_new", candidate), ("p", mixed)):
                    assert isclose(row[field], expected, rel_tol=1e-12, abs_tol=1e-8), (key, field)
                assert row["alpha"] == alpha and 0 <= row["p_new"] <= capacities[row["grp"]]
                assert not coverage[key] or row["p_new"] == row["p"] == 0
            computed[fold] = {name: metrics(rows, name) for name in ("p", "p_reference", "p_new")}
            for name, values in computed[fold].items():
                for metric, value in values.items():
                    assert isclose(value, record["scores"][fold][name][metric], rel_tol=1e-12, abs_tol=1e-4)
            if fold == "primary":
                ratios = sorted(((r["y"] - r["p_reference"]) / (r["p_new"] - r["p_reference"]), r["smp"] * r["k"] * abs(r["p_new"] - r["p_reference"])) for r in rows if r["p_new"] != r["p_reference"] and r["smp"] * r["k"] > 0)
                half, cumulative, optimum = fsum(w for _, w in ratios) / 2, 0., 0.
                for ratio, weight in ratios:
                    cumulative += weight
                    if cumulative >= half:
                        optimum = max(0., min(1., ratio))
                        break
                loss = fsum(r["smp"] * r["k"] * abs(r["y"] - ((1-optimum)*r["p_reference"] + optimum*r["p_new"])) for r in rows)
                assert isclose(loss, computed[fold]["p"]["W"], rel_tol=1e-12, abs_tol=1e-4)
        both = all(computed[f]["p"]["W"] < computed[f]["p_reference"]["W"] for f in computed)
        relative = fsum(computed[f]["p"]["W"] / computed[f]["p_reference"]["W"] for f in computed) / 2
        assert record["both_folds_improve"] == both and record["eligible"] == (both and alpha >= .02)
        assert isclose(relative, record["mean_relative_W"], rel_tol=1e-12)
        checked.append({"arm": arm, "alpha": alpha, "scores": computed, "eligible": record["eligible"]})
    eligible = [r for r in results["records"] if r["eligible"]]
    selected = min(eligible, key=lambda r: r["mean_relative_W"]) if eligible else None
    assert results["selected"] == selected and results["reference_retained"] == (selected is None)
    intervals.sort()
    assert model_count == len(intervals) == 6 and all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:]))
    controller = json.loads((OUT / "controller_receipt.json").read_text())
    assert controller["exit_code"] == 0 and controller["real_model_fit_count"] == 6 and controller["real_site_gain_fit_count"] == 2
    ensure_terminal(controller["identity"])
    index = json.loads((OUT / "terminal_index.json").read_text())
    evidence = {"status": "PASS", "models_fully_replayed": model_count, "serial_intervals": len(intervals),
                "protected_files": len(protocol["protected_sha256"]), "records": checked, "selected": selected,
                "lifecycle_limitation": index["lifecycle_limitation"],
                "external_controller_os_exit_code": index["external_controller_os_exit_code"],
                "limitations": "Historically exposed development. Frozen calibration transferred without refitting. No new confirmation or official score."}
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
