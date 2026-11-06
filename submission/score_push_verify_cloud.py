# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "catboost", "lightgbm"]
# ///
# How to run: analysis_outputs/score_push_gpu_20261104/environment/Scripts/python.exe submission/score_push_verify_cloud.py
"""Verify frozen cloud-wave models, generation inputs and primary-only selection."""
from __future__ import annotations

import csv
import json
from datetime import datetime
from math import fsum, isclose, isfinite
from typing import Final

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from catboost import CatBoostRegressor
import lightgbm as lgb

from autoresearch_verify_final import metrics
from score_push_verify import ROOT, digest
from score_push_verify_cloud_data import same_columns

OUT: Final = ROOT / "analysis_outputs/renew_20261105/cloud_wave"
TEMPORAL: Final = ROOT / "analysis_outputs/renew_20261105/recency_wave"
DATA: Final = ROOT / "analysis_outputs/score_push_gpu_20261104/data"
BASE: Final = {"primary": 12.033226215978063, "recent": 11.059225184100658}


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    assert json.loads((OUT / "independent_data_check.json").read_text())["status"] == "PASS"
    protocol = json.loads((OUT / "protocol.json").read_text())
    result = json.loads((OUT / "results.json").read_text())
    assert result["auxiliary_fit_count"] == 14 and result["generation_fit_count"] == 12
    assert result["upstream_seeds"] == [0] and not result["robust_adoption"]
    assert not result["confirmation_loaded"] and not result["test_loaded"]
    assert json.loads((OUT / "controller_receipt.json").read_text())["exit_code"] == 0
    for mapping in (protocol["input_sha256"], protocol["protected_sha256"]):
        for path, expected in mapping.items():
            assert digest(ROOT / path) == expected, path
    for name, record in protocol["own_sources"].items():
        assert digest(OUT / "sources/own" / name) == record["sha256"]
    amendment = json.loads((OUT / "source_amendment.json").read_text())
    assert amendment["original_protocol_sha256"] == digest(OUT / "protocol.json")
    for name, record in {**protocol["own_sources"], **amendment["own_sources"]}.items():
        assert digest(ROOT / record["original"]) == record["sha256"]
        assert digest(OUT / record.get("snapshot", f"sources/own/{name}")) == record["sha256"]
    for path, expected in json.loads((OUT / "artifact_hashes.json").read_text()).items():
        assert digest(OUT / path) == expected, path
    records = result["records"]
    assert len(records) == 2 and {r["variant"] for r in records} == {"means", "profiles"}
    checked = []
    for record in records:
        variant, alpha = record["variant"], record["alpha_primary_only"]
        assert record["seeds"] == [0, 1, 2] and record["stage"] == "ensemble"
        assert isfinite(alpha) and 0 <= alpha <= 1
        paired = {}
        for fold in BASE:
            source = pq.read_table(DATA / fold / "train.parquet")
            extra = pq.read_table(OUT / "data" / fold / "train_features.parquet")
            same_columns(source, extra, ["ts", "grp"])
            old_names = json.loads((DATA / fold / "features.json").read_text())["station"]
            added = [name for name in extra.column_names if name not in ("ts", "grp") and (variant == "profiles" or name.endswith(("_mean", "_warmup")))]
            candidates = [*old_names, *added]
            selected = []
            for name in candidates:
                values = (source if name in old_names else extra)[name].to_numpy()
                if len(np.unique(values[~np.isnan(values)])) > 1:
                    selected.append(name)
            weights_path = OUT / "data" / variant / fold / "training_weights.parquet"
            weights = pq.read_table(weights_path)
            control_weights = pq.read_table(TEMPORAL / "data/decay180" / fold / "training_weights.parquet")
            same_columns(weights, control_weights, control_weights.column_names)
            members = []
            daylight = pq.read_table(DATA / fold / "evaluation.parquet", columns=["ts", "grp"]).to_pylist()
            daylight_keys = {(r["ts"], r["grp"]) for r in daylight}
            for seed in range(3):
                trial = OUT / "trials" / variant / fold / f"seed{seed}"
                config = json.loads((trial / "config.json").read_text())
                assert config["candidate_features"] == candidates and config["features"] == selected
                assert config["training_rows"] == len(source) and config["half_life_days"] == 180
                assert config["weights_sha256"] == digest(weights_path)
                assert config["parameters"]["random_state"] == (None if seed == 0 else seed)
                assert config["parameters"]["n_estimators"] == 400 and config["parameters"]["num_leaves"] == 63
                model = lgb.Booster(model_file=str(trial / "model.txt"))
                assert model.current_iteration() == 400 and model.feature_name() == selected
                raw = pq.read_table(trial / "daylight_raw.parquet").to_pylist()
                member = {(r["ts"], r["grp"]): r["p_raw"] for r in raw}
                assert len(member) == len(raw) and set(member) == daylight_keys
                assert all(isfinite(value) for value in member.values())
                members.append(member)
            reference = pq.read_table(TEMPORAL / "comparisons/decay180/ensemble" / fold / "predictions.parquet").to_pylist()
            oracle = {(r["ts"], r["grp"]): r for r in reference}
            rows = pq.read_table(OUT / "comparisons" / variant / "ensemble" / fold / "predictions.parquet").to_pylist()
            assert len(rows) == len(oracle) and {(r["ts"], r["grp"]) for r in rows} == set(oracle)
            for row in rows:
                key = row["ts"], row["grp"]
                assert all(row[name] == oracle[key][name] for name in ("y", "smp", "k", "p_incumbent"))
                assert row["p_reference"] == oracle[key]["p"] and row["alpha"] == alpha
                assert row["p_noaux"] == oracle[key]["p_new"]
                pure = max(0., fsum(member[key] for member in members) / 3) if key in daylight_keys else 0.
                assert isclose(pure, row["p_new"], rel_tol=1e-12, abs_tol=1e-7)
                assert isclose(row["p"], (1 - alpha) * row["p_reference"] + alpha * pure, rel_tol=1e-12, abs_tol=1e-7)
                assert all(isfinite(row[name]) and row[name] >= 0 for name in ("y", "smp", "p", "p_reference", "p_new"))
            computed = {arm: metrics(rows, arm) for arm in ("p", "p_reference", "p_new", "p_incumbent", "p_noaux")}
            for arm, values in computed.items():
                for name, value in values.items():
                    assert isclose(value, record["scores"][fold][arm][name], rel_tol=1e-12, abs_tol=1e-5)
            assert isclose(computed["p_reference"]["W_pct"], BASE[fold], abs_tol=1e-10)
            paired[fold] = computed
            if fold == "primary":
                ratios = sorted(((r["y"] - r["p_reference"]) / (r["p_new"] - r["p_reference"]), r["smp"] * r["k"] * abs(r["p_new"] - r["p_reference"])) for r in rows if r["p_new"] != r["p_reference"])
                half, cumulative, optimum = fsum(weight for _, weight in ratios) / 2, 0., 0.
                for ratio, weight in ratios:
                    cumulative += weight
                    if cumulative >= half:
                        optimum = min(1., max(0., ratio))
                        break
                loss = fsum(r["smp"] * r["k"] * abs(r["y"] - ((1 - optimum) * r["p_reference"] + optimum * r["p_new"])) for r in rows)
                assert isclose(loss, computed["p"]["W"], rel_tol=1e-12, abs_tol=1e-4)
        both = all(paired[fold]["p"]["W_pct"] < BASE[fold] for fold in BASE)
        assert record["both_folds_improve"] == both and record["eligible"] == (both and alpha >= .02)
        assert isclose(record["mean_relative_W"], fsum(paired[fold]["p"]["W_pct"] / BASE[fold] for fold in BASE) / 2, rel_tol=1e-12)
        checked.append({"variant": variant, "alpha": alpha, "scores": paired, "eligible": record["eligible"]})
    eligible = [r for r in records if r["eligible"]]
    selected = min(eligible, key=lambda r: r["mean_relative_W"]) if eligible else None
    assert result["selected"] == selected and result["temporal_reference_retained"] == (selected is None)
    auxiliary = sorted(p for p in (OUT / "auxiliary").glob("*/*") if p.is_dir())
    generation = sorted((OUT / "trials").glob("*/*/seed*"))
    assert len(auxiliary) == 14 and len(generation) == 12
    intervals, gpu = [], []
    for trial in [*auxiliary, *generation]:
        receipt = json.loads((trial / "controller_receipt.json").read_text())
        replay = json.loads((trial / "replay.json").read_text())
        runtime = json.loads((trial / "runtime.json").read_text())
        assert receipt["exit_code"] == 0 and receipt["exact_worker_absent"]
        assert replay["passed"] and replay["max_absolute_error"] == 0
        assert runtime["priority_class"] == 32 and runtime["parallel_fits"] == 1 and runtime["pyarrow_cpu"] == 4
        assert all(pool["num_threads"] == 16 for pool in runtime["threadpools"])
        intervals.append((datetime.fromisoformat(receipt["started_utc"]), datetime.fromisoformat(receipt["finished_utc"])))
        is_aux = trial in auxiliary
        assert digest(trial / ("model.cbm" if is_aux else "model.txt")) == replay["model_sha256"]
        assert digest(trial / ("predictions.parquet" if is_aux else "daylight_raw.parquet")) == replay["raw_sha256"]
        if is_aux:
            model = CatBoostRegressor()
            model.load_model(str(trial / "model.cbm"))
            parameters = model.get_all_params()
            assert parameters["task_type"] == "GPU" and parameters["depth"] == 6 and model.tree_count_ == 1000
            assert parameters["random_seed"] == 0
            config = json.loads((trial / "config.json").read_text())
            assert model.feature_names_ == config["features"] and model.get_cat_feature_indices() == [0]
            with (trial / "gpu_samples.csv").open(encoding="utf-8", newline="") as stream:
                samples = list(csv.reader(stream))
            assert samples and all("RTX 5090 Laptop" in row[1] for row in samples)
            gpu.append({"trial": str(trial.relative_to(OUT)), "max_utilization": max(float(row[2]) for row in samples), "max_memory_mib": max(float(row[3]) for row in samples)})
    intervals.sort()
    assert all(start < end for start, end in intervals)
    assert all(left[1] <= right[0] for left, right in zip(intervals, intervals[1:]))
    evidence = {"status": "PASS", "records": checked, "selected": selected, "auxiliary_models": 14, "generation_models": 12, "serial_intervals": len(intervals), "protected_files": len(protocol["protected_sha256"]), "gpu": gpu, "robust_adoption": False, "limitations": "Historically exposed development; one auxiliary seed; no official score or final confirmation."}
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
