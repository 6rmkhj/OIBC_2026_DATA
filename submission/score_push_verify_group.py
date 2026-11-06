# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "lightgbm", "pandas", "threadpoolctl"]
# ///
# How to run: python submission/score_push_verify_group.py after the wave is terminal.
"""Audit group-loss model evidence, primary-only blends and paired decisions."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from math import fsum, isclose, isfinite

import pyarrow as pa
import pyarrow.parquet as pq

from autoresearch_verify_final import metrics
from score_push_verify_group_data import ROOT, OUT, sha
from score_push_verify_group_models import ARMS, verify_models

sys.path.insert(0, str(ROOT / "submission/score_push_renew"))
from group_common import ensure_terminal


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = json.loads((OUT / "protocol.json").read_text())
    result = json.loads((OUT / "results.json").read_text())
    data = json.loads((OUT / "independent_data_check.json").read_text())
    mathematics = json.loads((OUT / "independent_math_check.json").read_text())
    assert data["status"] == mathematics["status"] == "PASS"
    assert data["protocol_sha256"] == sha(OUT / "protocol.json")
    assert data["prepared_manifest_sha256"] == sha(OUT / "prepared_manifest.json")
    assert mathematics["objective_source_sha256"] == sha(ROOT / "submission/score_push_renew/group_objective.py")
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
    assert result["real_model_fit_count"] == 18 and not result["confirmation_loaded"] and not result["test_loaded"]
    records = result["records"]
    assert len(records) == 3 and {r["arm"] for r in records} == set(ARMS)
    checked, model_evidence = [], []
    for record in records:
        arm, alpha = record["arm"], record["alpha_primary_only"]
        assert record["seeds"] == [0, 1, 2] and isfinite(alpha) and 0 <= alpha <= 1
        scores = {}
        for fold in ("primary", "recent"):
            values, models = verify_models(arm, fold)
            model_evidence.extend(models)
            labels = pq.read_table(OUT / "data" / fold / "labels.parquet").to_pylist()
            oracle = {(r["ts"], r["grp"]): r for r in labels}
            rows = pq.read_table(OUT / "comparisons" / arm / "ensemble" / fold / "predictions.parquet").to_pylist()
            assert len(oracle) == len(rows) == len(values) == (17568 if fold == "primary" else 13104)
            assert {(r["ts"], r["grp"]) for r in rows} == set(oracle) == set(values)
            for row in rows:
                key = row["ts"], row["grp"]
                assert all(row[name] == oracle[key][name] for name in ("y", "smp", "k", "p_reference"))
                assert row["alpha"] == alpha
                assert isclose(row["p_new"], values[key], rel_tol=1e-12, abs_tol=1e-7)
                assert isclose(row["p"], (1 - alpha) * row["p_reference"] + alpha * values[key], rel_tol=1e-12, abs_tol=1e-7)
                assert all(isfinite(row[name]) and row[name] >= 0 for name in ("p", "p_reference", "p_new", "y", "smp"))
            scores[fold] = {name: metrics(rows, name) for name in ("p", "p_reference", "p_new")}
            for name, values_score in scores[fold].items():
                for metric, value in values_score.items():
                    assert isclose(value, record["scores"][fold][name][metric], rel_tol=1e-12, abs_tol=1e-4)
            assert isclose(scores[fold]["p_reference"]["W_pct"], protocol["reference_scores"][fold], abs_tol=1e-10)
            if fold == "primary":
                ratios = sorted(((r["y"] - r["p_reference"]) / (r["p_new"] - r["p_reference"]), r["smp"] * r["k"] * abs(r["p_new"] - r["p_reference"])) for r in rows if r["p_new"] != r["p_reference"])
                half, cumulative, optimum = fsum(weight for _, weight in ratios) / 2, 0., 0.
                for ratio, weight in ratios:
                    cumulative += weight
                    if cumulative >= half:
                        optimum = min(1., max(0., ratio))
                        break
                loss = fsum(r["smp"] * r["k"] * abs(r["y"] - ((1 - optimum) * r["p_reference"] + optimum * r["p_new"])) for r in rows)
                assert isclose(loss, scores[fold]["p"]["W"], rel_tol=1e-12, abs_tol=1e-4)
        both = all(scores[fold]["p"]["W"] < scores[fold]["p_reference"]["W"] for fold in scores)
        relative = fsum(scores[fold]["p"]["W"] / scores[fold]["p_reference"]["W"] for fold in scores) / 2
        assert record["both_folds_improve"] == both and record["eligible"] == (both and alpha >= .02)
        assert isclose(record["mean_relative_W"], relative, rel_tol=1e-12)
        checked.append({"arm": arm, "alpha": alpha, "scores": scores, "eligible": record["eligible"]})
    eligible = [r for r in records if r["eligible"]]
    selected = min(eligible, key=lambda r: r["mean_relative_W"]) if eligible else None
    assert result["selected"] == selected and result["reference_retained"] == (selected is None)
    intervals = []
    for trial in sorted((OUT / "trials").glob("*/*/seed*")):
        runtime = json.loads((trial / "runtime.json").read_text())
        receipt = json.loads((trial / "controller_receipt.json").read_text())
        assert runtime["model_threads"] == 16 and runtime["priority_class"] == 32 and runtime["parallel_fits"] == 1
        assert runtime["pyarrow_cpu"] == runtime["pyarrow_io"] == 4
        assert all(pool["num_threads"] == 16 for pool in runtime["threadpools"])
        assert receipt["exit_code"] == 0 and receipt["exact_worker_absent"]
        ensure_terminal(receipt["identity"])
        intervals.append((datetime.fromisoformat(receipt["started_utc"]), datetime.fromisoformat(receipt["finished_utc"])))
    intervals.sort()
    assert len(intervals) == 18 and all(start < end for start, end in intervals)
    assert all(left[1] <= right[0] for left, right in zip(intervals, intervals[1:]))
    controller = json.loads((OUT / "controller_receipt.json").read_text())
    assert controller["exit_code"] == 0
    ensure_terminal(controller["identity"])
    evidence = {"status": "PASS", "records": checked, "selected": selected, "models": model_evidence,
                "serial_intervals": len(intervals), "protected_files": len(protocol["protected_sha256"]),
                "limitations": "Historically exposed development; worker full saved inference replays and root 2048-row sample per model. No official score measurement."}
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "selected": selected, "records": checked, "models": len(model_evidence), "serial_intervals": len(intervals)}, indent=2))


if __name__ == "__main__":
    main()
