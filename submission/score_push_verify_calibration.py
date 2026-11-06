# /// script
# requires-python = ">=3.12"
# dependencies = ["pyarrow", "numpy", "threadpoolctl", "pandas"]
# ///
# How to run: python submission/score_push_verify_calibration.py
"""Independently verify scalar fits, transferred predictions and selection."""
from __future__ import annotations

import json
import sys
from datetime import timedelta
from math import fsum, isclose, isfinite

import pyarrow as pa
import pyarrow.parquet as pq

from autoresearch_verify_final import metrics
from score_push_verify_calibration_data import ROOT, OUT, sha

sys.path.insert(0, str(ROOT / "submission/score_push_renew"))
from cal_common import ensure_terminal


def temperature(row) -> int:
    value = row["wa_temp"]
    return -1 if value is None or not isfinite(value) else sum(value >= boundary for boundary in (0, 10, 20, 30))


def snowy(row) -> bool:
    value = row["extra_wa_snow"]
    return value is not None and isfinite(value) and value >= .001


def verify_factor(rows, selected, saved, multipliers) -> float:
    active = [(row, row["p_reference"] * multiplier) for row, keep, multiplier in zip(rows, selected, multipliers, strict=True)
              if keep and row["p_reference"] > 0 and row["smp"] * row["k"] > 0]
    days = len({(row["ts"] - timedelta(hours=1)).date() for row, _ in active})
    mass = fsum(row["smp"] * row["k"] * p for row, p in active)
    assert saved["support_rows"] == len(active) and saved["support_days"] == days
    assert isclose(saved["weight_mass"], mass, rel_tol=1e-12, abs_tol=1e-7)
    supported = len(active) >= 150 and days >= 20 and mass > 0
    assert saved["supported"] == supported
    if not supported:
        assert saved["factor"] == 1 and saved["raw_median"] is None
        return 1.
    ratios = sorted((row["y"] / p, row["smp"] * row["k"] * p) for row, p in active)
    cumulative, median = 0., 0.
    for ratio, weight in ratios:
        cumulative += weight
        if cumulative >= mass / 2:
            median = ratio
            break
    bounded = min(1.15, max(.85, median))
    assert isclose(saved["raw_median"], median, rel_tol=1e-12, abs_tol=1e-12)
    assert isclose(saved["factor"], bounded, rel_tol=1e-12, abs_tol=1e-12)
    optimum_loss = fsum(row["smp"] * row["k"] * abs(row["y"] - p * bounded) for row, p in active)
    actual_loss = fsum(row["smp"] * row["k"] * abs(row["y"] - p * saved["factor"]) for row, p in active)
    assert isclose(actual_loss, optimum_loss, rel_tol=1e-12, abs_tol=1e-5)
    return bounded


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = json.loads((OUT / "protocol.json").read_text())
    checked_data = json.loads((OUT / "independent_data_check.json").read_text())
    assert checked_data["status"] == "PASS" and checked_data["protocol_sha256"] == sha(OUT / "protocol.json")
    assert checked_data["prepared_manifest_sha256"] == sha(OUT / "prepared_manifest.json")
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
    coefficients = json.loads((OUT / "coefficients.json").read_text())
    assert coefficients["fit_period"] == ["2023-06-01", "2024-06-01"]
    assert coefficients["target_source"] == "data/primary/rows.parquet"
    assert coefficients["target_source_sha256"] == sha(OUT / "data/primary/rows.parquet")
    factors = coefficients["factors"]
    primary = pq.read_table(OUT / "data/primary/rows.parquet").to_pylist()
    bins = [temperature(row) for row in primary]
    ones = [1.] * len(primary)
    temp = [verify_factor(primary, [b == i for b in bins], saved, ones) for i, saved in enumerate(factors["temperature"])]
    assert len(temp) == 5
    snow_mask = [snowy(row) for row in primary]
    snow = verify_factor(primary, snow_mask, factors["snow"], ones)
    adjustments = [1. if b == -1 else temp[b] for b in bins]
    conditional_snow = verify_factor(primary, snow_mask, factors["conditional_snow"], adjustments)
    result = json.loads((OUT / "results.json").read_text())
    assert result["candidate_count"] == 3 and result["tree_model_fits"] == 0 and result["primary_fit_partly_in_sample"]
    assert not result["confirmation_loaded"] and not result["test_loaded"] and not result["loaded_existing_coefficients"]
    assert {r["arm"] for r in result["records"]} == {"snow_only", "temperature_only", "temperature_then_snow"}
    checked = []
    for record in result["records"]:
        arm, scores = record["arm"], {}
        assert record["fixed_shrink"] == .5 and not record["alpha_optimization"]
        for fold in ("primary", "recent"):
            base = pq.read_table(OUT / "data" / fold / "rows.parquet").to_pylist()
            original = {(r["ts"], r["grp"]): r for r in base}
            directory = OUT / "comparisons" / arm / fold
            rows = pq.read_table(directory / "predictions.parquet").to_pylist()
            assert len(rows) == len(original) and {(r["ts"], r["grp"]) for r in rows} == set(original)
            clipped = 0
            for row in rows:
                previous = original[(row["ts"], row["grp"])]
                assert all(row[n] == previous[n] for n in ("y", "smp", "k", "p_reference", "static_capacity"))
                bin_index, is_snow = temperature(previous), snowy(previous)
                t = 1. if bin_index == -1 else temp[bin_index]
                raw = snow if is_snow else 1.
                if arm == "temperature_only":
                    raw = t
                elif arm == "temperature_then_snow":
                    raw = t * (conditional_snow if is_snow else 1.)
                bounded = max(.85, min(1.15, raw))
                effective = 1 + .5 * (bounded - 1)
                before = previous["p_reference"] * effective
                prediction = max(0., min(previous["static_capacity"], before))
                assert row["temperature_bin"] == bin_index and row["snow_condition"] == is_snow
                for name, expected in (("raw_factor", raw), ("bounded_factor", bounded), ("effective_factor", effective),
                                       ("before_capacity_clip", before), ("p", prediction)):
                    assert isclose(row[name], expected, rel_tol=1e-12, abs_tol=1e-8), name
                assert row["capacity_clipped"] == (before > previous["static_capacity"])
                clipped += row["capacity_clipped"]
                assert .925 - 1e-12 <= row["effective_factor"] <= 1.075 + 1e-12
                assert 0 <= row["p"] <= row["static_capacity"]
                assert previous["p_reference"] != 0 or row["p"] == 0
            scores[fold] = {name: metrics(rows, name) for name in ("p", "p_reference")}
            for name, measurements in scores[fold].items():
                for metric, value in measurements.items():
                    assert isclose(value, record["scores"][fold][name][metric], rel_tol=1e-12, abs_tol=1e-4)
            receipt = json.loads((directory / "application.json").read_text())
            assert receipt["passed"] and receipt["exact_replay"] and receipt["allnight_zero"]
            assert receipt["rows"] == len(rows) and receipt["capacity_clip_count"] == clipped
            assert receipt["prediction_sha256"] == sha(directory / "predictions.parquet")
            assert receipt["coefficient_sha256"] == sha(OUT / "coefficients.json")
        eligible = all(scores[f]["p"]["W"] < scores[f]["p_reference"]["W"] for f in scores)
        relative = fsum(scores[f]["p"]["W"] / scores[f]["p_reference"]["W"] for f in scores) / 2
        assert record["eligible"] == eligible and isclose(record["mean_relative_W"], relative, rel_tol=1e-12)
        checked.append({"arm": arm, "scores": scores, "eligible": eligible})
    candidates = [r for r in result["records"] if r["eligible"]]
    selected = min(candidates, key=lambda r: r["mean_relative_W"]) if candidates else None
    assert result["selected"] == selected and result["reference_retained"] == (selected is None)
    controller = json.loads((OUT / "controller_receipt.json").read_text())
    assert controller["exit_code"] == 0 and controller["tree_model_fits"] == 0
    identity = controller["identity"]
    assert identity["priority_class"] == 32 and identity["pyarrow_cpu"] == identity["pyarrow_io"] == 4
    assert all(pool["num_threads"] == 16 for pool in identity["threadpools"])
    ensure_terminal(identity)
    evidence = {"status": "PASS", "factors": {"temperature": temp, "snow": snow, "conditional_snow": conditional_snow},
                "records": checked, "selected": selected, "protected_files": len(protocol["protected_sha256"]),
                "limitations": "Primary calibration performance partly in-sample; historical/adaptive exposure; no official score or final confirmation."}
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
