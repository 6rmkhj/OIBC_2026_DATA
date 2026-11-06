# /// script
# requires-python = ">=3.12"
# dependencies = ["pyarrow"]
# ///
# How to run: python submission/score_push_verify_sky.py AFTER the sky wave is terminal.
"""Independently check projected cloud data, four scalar fits and transfer."""
from __future__ import annotations

import json
from math import isclose, isfinite
from typing import Final

import pyarrow as pa
import pyarrow.parquet as pq

from autoresearch_verify_final import metrics
from score_push_verify import ROOT, digest
from score_push_verify_calibration import verify_factor, ensure_terminal

OUT: Final = ROOT / "analysis_outputs/renew_20261105/sky_wave"
RENEW: Final = OUT.parent


def read(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8-sig"))


def bin_index(row) -> int:
    cloud = row["wb_cloud"]
    return -1 if cloud is None or not isfinite(cloud) else sum(cloud >= edge for edge in (20, 50, 80))


def same_missing(a, b) -> bool:
    return a == b or ((a is None or not isfinite(a)) and (b is None or not isfinite(b)))


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = read("protocol.json")
    for mapping in (protocol["input_sha256"], protocol["protected_sha256"]):
        for path, expected in mapping.items():
            assert digest(ROOT / path) == expected, path
    for name, record in protocol["own_sources"].items():
        assert digest(ROOT / record["original"]) == digest(OUT / "sources/own" / name) == record["sha256"]
    for name, record in protocol["snapshots"].items():
        assert digest(ROOT / record["original"]) == digest(OUT / "sources" / f"{name}.py") == record["sha256"]
    for manifest in ("prepared_manifest.json", "terminal_manifest.json"):
        for path, expected in read(manifest).items():
            assert digest(OUT / path) == expected, path
    prepared, above100 = {}, {}
    for fold in ("primary", "recent"):
        previous = {(r["ts"], r["grp"]): r for r in pq.read_table(RENEW / "hour_wave/comparisons/hour_bias" / fold / "predictions.parquet", columns=["ts", "grp", "p", "y", "smp", "k", "static_capacity"]).to_pylist()}
        weather = {(r["ts"], r["grp"]): r["wb_cloud"] for r in pq.read_table(ROOT / "analysis_outputs/score_push_gpu_20261104/data" / fold / "evaluation.parquet", columns=["ts", "grp", "wb_cloud"]).to_pylist()}
        night = {(r["ts"], r["grp"]): r["night"] for r in pq.read_table(RENEW / "recency_wave/data" / fold / "night_coverage.parquet").to_pylist()}
        table = pq.read_table(OUT / "data" / fold / "rows.parquet")
        assert set(table.column_names) == {"ts", "grp", "p_reference", "y", "smp", "k", "static_capacity", "night", "wb_cloud"}
        rows = table.to_pylist()
        assert len(rows) == len(previous) and {(r["ts"], r["grp"]) for r in rows} == set(previous) == set(night)
        inputs = pq.read_table(OUT / "data" / fold / "apply_inputs.parquet")
        assert set(inputs.column_names) == {"ts", "grp", "p_reference", "wb_cloud", "static_capacity"}
        assert inputs.to_pylist() == table.select(inputs.column_names).to_pylist()
        for row in rows:
            key = row["ts"], row["grp"]
            base = previous[key]
            assert row["ts"].tzinfo is not None
            assert all(row[n] == base[n] for n in ("y", "smp", "k", "static_capacity"))
            assert row["p_reference"] == base["p"] and row["night"] == night[key]
            assert same_missing(row["wb_cloud"], weather.get(key))
            assert (key not in weather) == row["night"]
            assert not row["night"] or row["p_reference"] == 0
        prepared[fold] = rows
        above100[fold] = sum(r["wb_cloud"] is not None and isfinite(r["wb_cloud"]) and r["wb_cloud"] > 100 for r in rows)
    coefficients = read("coefficients.json")
    assert coefficients["fit_period"] == ["2023-06-01", "2024-06-01"]
    assert coefficients["target_source"] == "data/primary/rows.parquet"
    assert coefficients["target_source_sha256"] == digest(OUT / coefficients["target_source"])
    primary = prepared["primary"]
    assert len(coefficients["factors"]["clouds"]) == 4
    bins, ones = [bin_index(row) for row in primary], [1.] * len(primary)
    factors = [verify_factor(primary, [b == i for b in bins], saved, ones)
               for i, saved in enumerate(coefficients["factors"]["clouds"])]
    assert above100["primary"] == 55 and all(bin_index(r) == 3 for r in primary if r["wb_cloud"] is not None and r["wb_cloud"] > 100)
    result = read("results.json")
    assert result["candidate_count"] == 1 and result["real_scalar_fit_count"] == 4 and result["tree_fits"] == 0
    assert not result["loaded_existing_coefficients"] and not result["confirmation_loaded"] and not result["test_loaded"]
    assert result["primary_fit_partly_in_sample"] and len(result["records"]) == 1
    record = result["records"][0]
    assert record["arm"] == "cloud_bias" and not record["alpha_optimization"]
    scores = {}
    for fold, source in prepared.items():
        original = {(r["ts"], r["grp"]): r for r in source}
        directory = OUT / "comparisons/cloud_bias" / fold
        rows = pq.read_table(directory / "predictions.parquet").to_pylist()
        assert len(rows) == len(original) and {(r["ts"], r["grp"]) for r in rows} == set(original)
        clipped = 0
        for row in rows:
            base = original[(row["ts"], row["grp"])]
            assert all(row[n] == base[n] for n in ("y", "smp", "k", "p_reference", "static_capacity"))
            assert same_missing(row["wb_cloud"], base["wb_cloud"])
            index = bin_index(base)
            factor = 1. if index == -1 else factors[index]
            effective = 1 + .5 * (factor - 1)
            before = base["p_reference"] * effective
            prediction = max(0., min(base["static_capacity"], before))
            assert row["cloud_bin"] == index
            for name, value in (("bounded_cloud_factor", factor), ("effective_cloud_factor", effective), ("before_capacity_clip", before), ("p", prediction)):
                assert isclose(row[name], value, rel_tol=1e-12, abs_tol=1e-8), name
            assert row["capacity_clipped"] == (before > base["static_capacity"])
            assert 0 <= row["p"] <= base["static_capacity"] and (base["p_reference"] != 0 or row["p"] == 0)
            clipped += row["capacity_clipped"]
        scores[fold] = {name: metrics(rows, name) for name in ("p", "p_reference")}
        saved = read(f"comparisons/cloud_bias/{fold}/metrics.json")
        for name, measurements in scores[fold].items():
            for metric, value in measurements.items():
                assert isclose(value, record["scores"][fold][name][metric], rel_tol=1e-12, abs_tol=1e-4)
                assert saved[name][metric] == record["scores"][fold][name][metric]
    eligible = all(scores[f]["p"]["W"] < scores[f]["p_reference"]["W"] for f in scores)
    assert record["eligible"] == eligible and read("comparisons/cloud_bias/decision.json") == record
    assert result["selected"] == (record if eligible else None) and result["reference_retained"] == (not eligible)
    controller = read("controller_receipt.json")
    assert controller["exit_code"] == 0 and controller["real_scalar_fit_count"] == 4 and controller["tree_fits"] == 0
    identity = controller["identity"]
    assert identity["priority_class"] == 32 and identity["pyarrow_cpu"] == identity["pyarrow_io"] == 4
    assert all(pool["num_threads"] == 16 for pool in identity["threadpools"])
    ensure_terminal(identity)
    assert not (OUT / "tmp").exists()
    evidence = {"status": "PASS", "factors": factors, "scores": scores, "eligible": eligible,
                "roundoff_above100_included": above100, "protected_files": len(protocol["protected_sha256"]),
                "coefficient_sha256": digest(OUT / "coefficients.json"),
                "terminal_manifest_sha256": digest(OUT / "terminal_manifest.json"),
                "limits": "Primary partly in-sample and all history exposed; no confirmation/test or official score."}
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
