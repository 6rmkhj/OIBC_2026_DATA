# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow"]
# ///
# How to run: python submission/score_push_verify_smooth.py AFTER terminal seal.
"""Reconstruct fixed clear-sky temporal smoothing without the production helper."""
from __future__ import annotations

import json
from datetime import timedelta
from math import exp, fsum, isclose, isfinite
from typing import Final

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from autoresearch_verify_final import metrics
from score_push_verify_calibration import ensure_terminal
from score_push_verify_mlp_data import ROOT, digest, keyed, read

OUT: Final = ROOT / "analysis_outputs/renew_20261106/smooth_wave"
OLD: Final = ROOT / "analysis_outputs/renew_20261105"
GPU: Final = ROOT / "analysis_outputs/score_push_gpu_20261104/data"


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
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
    results = read(OUT / "results.json")
    assert results["real_model_fit_count"] == results["real_calibration_fit_count"] == 0
    assert results["real_alpha_fit_count"] == results["candidate_count"] == 1
    assert not any(results[name] for name in ("confirmation_loaded", "test_loaded", "exported"))
    assert len(results["records"]) == 1
    record = results["records"][0]
    alpha = record["alpha_primary_only"]
    assert isfinite(alpha) and 0 <= alpha <= 1
    computed, checked = {}, []
    for fold in ("primary", "recent"):
        reference = keyed(pq.read_table(OLD / "calibration_wave/comparisons/temperature_then_snow" / fold / "predictions.parquet"))
        weather = keyed(pq.read_table(GPU / fold / "evaluation.parquet", columns=["ts", "grp", "cosz", "capacity_kw"]))
        data = OUT / "data" / fold
        application = pq.read_table(data / "application_inputs.parquet")
        assert application.column_names == ["ts", "grp", "p_reference", "cosz", "capacity_kw", "static_capacity", "night"]
        inputs, labels = keyed(application), keyed(pq.read_table(data / "labels.parquet"))
        coverage = keyed(pq.read_table(data / "coverage.parquet"))
        assert set(inputs) == set(labels) == set(reference) == set(coverage)
        inverse, q = {}, {}
        for key, row in inputs.items():
            original = reference[key]
            assert row["p_reference"] == original["p"] and row["static_capacity"] == original["static_capacity"]
            assert labels[key]["p_reference"] == original["p"]
            assert all(labels[key][name] == original[name] for name in ("y", "smp", "k"))
            assert row["night"] == coverage[key]["night"] == (key not in weather)
            if row["night"]:
                assert row["p_reference"] == 0
                assert all(row[name] is None or not isfinite(row[name]) for name in ("cosz", "capacity_kw"))
                inverse[key] = q[key] = 0.
            else:
                assert row["cosz"] == weather[key]["cosz"] and row["capacity_kw"] == weather[key]["capacity_kw"]
                assert isfinite(row["cosz"]) and row["capacity_kw"] > 0
                c = max(0., row["cosz"])
                n = max(.05, 1.098 * c * exp(-.059 / c)) if c > 0 else .05
                inverse[key] = n * row["capacity_kw"]
                q[key] = row["p_reference"] / inverse[key]
        directory = OUT / "comparisons" / fold
        rows = pq.read_table(directory / "predictions.parquet").to_pylist()
        assert len(rows) == len(inputs) and {(r["ts"], r["grp"]) for r in rows} == set(inputs)
        support_count, changes = 0, 0
        for row in rows:
            key = row["ts"], row["grp"]
            neighbors = [(row["ts"] + timedelta(hours=h), row["grp"]) for h in (-1, 0, 1)]
            supported = all(k in inputs and not inputs[k]["night"] and isfinite(inputs[k]["cosz"])
                            and inputs[k]["cosz"] >= .15 and inputs[k]["capacity_kw"] > 0
                            and k[0].date() == row["ts"].date() for k in neighbors)
            expected_q = fsum(w * q[k] for w, k in zip((.25, .5, .25), neighbors, strict=True)) if supported else q[key]
            prediction = min(inputs[key]["static_capacity"], max(0., expected_q * inverse[key])) if supported else inputs[key]["p_reference"]
            assert row["supported"] == supported and row["alpha"] == alpha
            assert all(row[n] == labels[key][n] for n in ("y", "smp", "k", "p_reference"))
            for name, expected in (("inverse_kwh", inverse[key]), ("q_before", q[key]),
                                   ("q_smoothed", expected_q), ("p_new", prediction),
                                   ("p", (1 - alpha) * row["p_reference"] + alpha * prediction)):
                assert isclose(row[name], expected, rel_tol=1e-12, abs_tol=1e-8), (key, name)
            if not supported:
                np.testing.assert_array_equal(np.array(row["p_new"]).view(np.uint64), np.array(row["p_reference"]).view(np.uint64))
            assert 0 <= row["p_new"] <= inputs[key]["static_capacity"]
            assert not inputs[key]["night"] or row["p"] == row["p_new"] == 0
            support_count += supported
            changes += row["p_new"] != row["p_reference"]
        assert support_count == (6252 if fold == "primary" else 4480)
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
        checked.append({"fold": fold, "rows": len(rows), "supported_rows": support_count, "changed_candidate_rows": changes})
    both = all(computed[f]["p"]["W"] < computed[f]["p_reference"]["W"] for f in computed)
    eligible = both and alpha >= .02
    assert record["both_folds_improve"] == both and record["eligible"] == eligible
    assert results["eligible"] == eligible and results["reference_retained"] == (not eligible)
    assert results["selected"] == (record if eligible else None)
    controller = read(OUT / "controller_receipt.json")
    assert controller["exit_code"] == 0 and controller["real_model_fit_count"] == 0
    assert controller["real_alpha_fit_count"] == 1
    ensure_terminal(controller["identity"])
    assert not (OUT / "tmp").exists()
    evidence = {"status": "PASS", "records": checked, "alpha": alpha, "scores": computed,
                "eligible": eligible, "protected_files": len(protocol["protected_sha256"]),
                "terminal_manifest_sha256": digest(OUT / "terminal_manifest.json"),
                "scope": "All original inputs, exact neighbor/group/day support, independent normalization/kernel/caps, unsupported bits, primary alpha and metrics; zero model fits.",
                "limits": "All history exposed; primary blending partly in-sample; no new official score or independent holdout."}
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
