# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "pandas", "lightgbm", "threadpoolctl"]
# ///
# How to run: python submission/score_push_verify_total.py after the wave is terminal.
"""Re-run saved total predictors and independently verify blends and resources."""
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
from score_push_verify_total_data import ROOT, OUT, sha

sys.path.insert(0, str(ROOT / "submission/score_push_renew"))
from total_common import ensure_terminal


def verify_predictions(arm: str, fold: str) -> tuple[dict, list]:  # noqa: DICT_OK -- timestamp-indexed numerical evidence
    directory = OUT / "data" / fold
    specification = json.loads((directory / "features.json").read_text())
    evaluation = pq.read_table(directory / "evaluation.parquet")
    names = specification["features"][arm]
    matrix = evaluation.select(names).to_pandas()
    times = evaluation["ts"].to_pylist()
    capacity = evaluation["capacity_kw"].to_numpy()
    cosz = np.maximum(evaluation["cosz"].to_numpy(), 0.)
    exponent = np.divide(-.059, cosz, out=np.zeros(len(cosz)), where=cosz > 0)
    inverse = np.maximum(1.098 * cosz * np.exp(exponent), .05) * capacity
    members, evidence = [], []
    for seed in range(3):
        trial = OUT / "trials" / arm / fold / f"seed{seed}"
        config = json.loads((trial / "config.json").read_text())
        assert config["features"] == names and config["candidates"] == specification["candidates"][arm]
        assert config["prepared_manifest_sha256"] == sha(OUT / "prepared_manifest.json")
        assert config["parameters"]["random_state"] == (None if seed == 0 else seed)
        model = lgb.Booster(model_file=str(trial / "model.txt"))
        assert model.feature_name() == names and model.current_iteration() == model.num_trees() == 400
        assert model.pandas_categorical == []
        for name, expected in (("objective", "regression_l1"), ("num_threads", 16), ("num_leaves", 63), ("min_data_in_leaf", 50),
                               ("bagging_freq", 1), ("seed", seed), ("device_type", "cpu")):
            assert model.params[name] == expected, (name, model.params[name], expected)
        for name, expected in (("learning_rate", .03), ("feature_fraction", .8), ("bagging_fraction", .8)):
            assert isclose(model.params[name], expected, rel_tol=1e-12)
        raw = pq.read_table(trial / "total_raw.parquet")
        assert raw["ts"].to_pylist() == times
        np.testing.assert_array_equal(raw["capacity_kw"].to_numpy(), capacity)
        np.testing.assert_allclose(raw["inverse"].to_numpy(), inverse, rtol=1e-12)
        normalized = model.predict(matrix, raw_score=True, num_threads=1)
        np.testing.assert_array_equal(normalized, raw["normalized_raw"].to_numpy())
        np.testing.assert_array_equal(normalized, np.load(trial / "replay_raw.npy"))
        np.testing.assert_allclose(raw["p_raw"].to_numpy(), normalized * inverse, rtol=1e-12, atol=1e-8)
        replay = json.loads((trial / "replay.json").read_text())
        assert replay["passed"] and replay["max_absolute_error"] == 0 and replay["actual_iteration"] == 400
        assert replay["model_sha256"] == sha(trial / "model.txt") and replay["raw_sha256"] == sha(trial / "total_raw.parquet")
        assert replay["negative_total_raw"] == int((raw["p_raw"].to_numpy() < 0).sum())
        members.append(raw["p_raw"].to_numpy())
        evidence.append({"trial": str(trial.relative_to(OUT)), "root_full_replay_exact": True, "rows": len(normalized), "features": len(names)})
    average = np.mean(members, axis=0)
    pure = np.maximum(average, 0.)
    ensemble = pq.read_table(OUT / "comparisons" / arm / "ensemble" / fold / "signed_total_ensemble.parquet")
    assert ensemble["ts"].to_pylist() == times
    np.testing.assert_array_equal(ensemble["signed_seed_mean"].to_numpy(), average)
    np.testing.assert_array_equal(ensemble["p_total"].to_numpy(), pure)
    totals = dict(zip(times, pure, strict=True))
    template = pq.read_table(directory / "allocation_template.parquet").to_pylist()
    values = {(r["ts"], r["grp"]): totals.get(r["ts"], 0.) * r["ratio"] for r in template}
    allocation = pq.read_table(OUT / "comparisons" / arm / "ensemble" / fold / "allocation.parquet").to_pylist()
    assert len(allocation) == len(values)
    for actual, expected in zip(allocation, template, strict=True):
        assert all(actual[n] == expected[n] for n in ("ts", "grp", "p_reference", "capacity_kw", "ratio", "capacity_fallback"))
        assert actual["p_total"] == totals.get(actual["ts"], 0.)
        assert isclose(actual["p_new"], values[(actual["ts"], actual["grp"])], rel_tol=1e-12, abs_tol=1e-8)
    for ts in {r["ts"] for r in template}:
        assert isclose(values[(ts, "G1")] + values[(ts, "G2")], totals.get(ts, 0.), rel_tol=1e-12, abs_tol=1e-8)
    return values, evidence


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = json.loads((OUT / "protocol.json").read_text())
    data = json.loads((OUT / "independent_data_check.json").read_text())
    assert data["status"] == "PASS" and data["protocol_sha256"] == sha(OUT / "protocol.json")
    assert data["prepared_manifest_sha256"] == sha(OUT / "prepared_manifest.json")
    for mapping in (protocol["input_sha256"], protocol["protected_sha256"]):
        for path, expected in mapping.items():
            assert sha(ROOT / path) == expected, path
    for name, record in protocol["own_sources"].items():
        assert sha(ROOT / record["original"]) == sha(OUT / "sources/own" / name) == record["sha256"]
    for name, record in protocol["snapshots"].items():
        assert sha(OUT / "sources" / f"{name}.py") == record["sha256"]
    for manifest in ("prepared_manifest.json", "artifact_hashes.json"):
        for path, expected in json.loads((OUT / manifest).read_text()).items():
            assert sha(OUT / path) == expected, path
    result = json.loads((OUT / "results.json").read_text())
    assert result["real_model_fit_count"] == 12 and not result["confirmation_loaded"] and not result["test_loaded"]
    assert len(result["records"]) == 2 and {r["arm"] for r in result["records"]} == {"total_rich", "total_station"}
    checked, models = [], []
    for record in result["records"]:
        arm, alpha = record["arm"], record["alpha_primary_only"]
        assert record["seeds"] == [0, 1, 2] and isfinite(alpha) and 0 <= alpha <= 1
        scores = {}
        for fold in ("primary", "recent"):
            values, evidence = verify_predictions(arm, fold)
            models.extend(evidence)
            labels = pq.read_table(OUT / "data" / fold / "labels.parquet").to_pylist()
            oracle = {(r["ts"], r["grp"]): r for r in labels}
            rows = pq.read_table(OUT / "comparisons" / arm / "ensemble" / fold / "predictions.parquet").to_pylist()
            assert len(rows) == len(oracle) == len(values)
            assert {(r["ts"], r["grp"]) for r in rows} == set(oracle)
            for row in rows:
                key = row["ts"], row["grp"]
                assert all(row[n] == oracle[key][n] for n in ("y", "smp", "k", "p_reference"))
                assert row["alpha"] == alpha and isclose(row["p_new"], values[key], rel_tol=1e-12, abs_tol=1e-8)
                assert isclose(row["p"], (1 - alpha) * row["p_reference"] + alpha * values[key], rel_tol=1e-12, abs_tol=1e-8)
                assert all(isfinite(row[n]) and row[n] >= 0 for n in ("p", "p_reference", "p_new"))
            scores[fold] = {name: metrics(rows, name) for name in ("p", "p_reference", "p_new")}
            for name, measurements in scores[fold].items():
                for metric, value in measurements.items():
                    assert isclose(value, record["scores"][fold][name][metric], rel_tol=1e-12, abs_tol=1e-4)
            if fold == "primary":
                ratios = sorted(((r["y"] - r["p_reference"]) / (r["p_new"] - r["p_reference"]), r["smp"] * r["k"] * abs(r["p_new"] - r["p_reference"])) for r in rows if r["p_new"] != r["p_reference"])
                half, running, optimum = fsum(w for _, w in ratios) / 2, 0., 0.
                for ratio, weight in ratios:
                    running += weight
                    if running >= half:
                        optimum = min(1., max(0., ratio))
                        break
                expected_loss = fsum(r["smp"] * r["k"] * abs(r["y"] - ((1 - optimum) * r["p_reference"] + optimum * r["p_new"])) for r in rows)
                assert isclose(expected_loss, scores[fold]["p"]["W"], rel_tol=1e-12, abs_tol=1e-4)
        both = all(scores[f]["p"]["W"] < scores[f]["p_reference"]["W"] for f in scores)
        relative = fsum(scores[f]["p"]["W"] / scores[f]["p_reference"]["W"] for f in scores) / 2
        assert record["both_folds_improve"] == both and record["eligible"] == (both and alpha >= .02)
        assert isclose(record["mean_relative_W"], relative, rel_tol=1e-12)
        checked.append({"arm": arm, "alpha": alpha, "scores": scores, "eligible": record["eligible"]})
    eligible = [r for r in result["records"] if r["eligible"]]
    selected = min(eligible, key=lambda r: r["mean_relative_W"]) if eligible else None
    assert result["selected"] == selected and result["reference_retained"] == (selected is None)
    intervals = []
    for trial in sorted((OUT / "trials").glob("*/*/seed*")):
        runtime = json.loads((trial / "runtime.json").read_text())
        receipt = json.loads((trial / "controller_receipt.json").read_text())
        assert runtime["model_threads"] == 16 and runtime["priority_class"] == 32 and runtime["parallel_fits"] == 1
        assert runtime["pyarrow_cpu"] == runtime["pyarrow_io"] == 4 and all(p["num_threads"] == 16 for p in runtime["threadpools"])
        assert receipt["exit_code"] == 0 and receipt["exact_worker_absent"]
        ensure_terminal(receipt["identity"])
        intervals.append((datetime.fromisoformat(receipt["started_utc"]), datetime.fromisoformat(receipt["finished_utc"])))
    intervals.sort()
    assert len(intervals) == 12 and all(start < end for start, end in intervals)
    assert all(left[1] <= right[0] for left, right in zip(intervals, intervals[1:]))
    controller = json.loads((OUT / "controller_receipt.json").read_text())
    assert controller["exit_code"] == 0
    ensure_terminal(controller["identity"])
    evidence = {"status": "PASS", "records": checked, "selected": selected, "models": models, "serial_intervals": len(intervals),
                "protected_files": len(protocol["protected_sha256"]), "limitations": "Historically exposed adaptive development; no official score or final confirmation."}
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "records": checked, "selected": selected, "models": len(models)}, indent=2))


if __name__ == "__main__":
    main()
