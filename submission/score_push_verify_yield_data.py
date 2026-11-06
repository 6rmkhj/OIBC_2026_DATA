# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "lightgbm"]
# ///
# How to run: python submission/score_push_verify_yield_data.py
"""Verify bounded original site projections without fitting any yield quantiles."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime
from math import fsum, isclose
from typing import Final
from zoneinfo import ZoneInfo

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from score_push_verify_renew_final_data import ROOT, digest, equal_source

OUT: Final = ROOT / "analysis_outputs/renew_20261105/yield_wave"
SITE: Final = ROOT / "analysis_outputs/score_push_20261104/site_wave/cache"
GPU: Final = ROOT / "analysis_outputs/score_push_gpu_20261104/data"


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = json.loads((OUT / "protocol.json").read_text())
    assert protocol["site_coefficient_fits"] == 2 and protocol["generation_model_fit_budget"] == 6
    for path, expected in protocol["input_sha256"].items():
        assert digest(ROOT / path) == expected, path
    for path, expected in json.loads((OUT / "prepared_manifest.json").read_text()).items():
        assert digest(OUT / path) == expected, path
    assert json.loads((OUT.parent / "group_wave/independent_data_check.json").read_text())["status"] == "PASS"
    assignment = json.loads((ROOT / "analysis_outputs/autoresearch_20261103/cache/assignment.json").read_text())
    with (ROOT / "handover 2/01_participant_dataset/sites.csv").open(encoding="utf-8-sig", newline="") as handle:
        metadata = {r["site_id"]: float(r["capacity_kw"]) for r in csv.DictReader(handle)}
    saved_sites = pq.read_table(OUT / "data/sites.parquet").to_pylist()
    assert len(saved_sites) == len(metadata) == len(assignment) == 253
    for row in saved_sites:
        assert row["capacity_kw"] == metadata[row["site_id"]] and row["grp"] == assignment[row["site_id"]]
    checked = []
    for fold, dates in {"primary": ("2023-06-01", "2024-06-01"), "recent": ("2024-06-01", "2025-03-01")}.items():
        cutoff, end = [datetime.fromisoformat(d).replace(tzinfo=ZoneInfo("Asia/Seoul")) for d in dates]
        directory = OUT / "data" / fold
        spec = json.loads((directory / "features.json").read_text())
        source_spec = json.loads((GPU / fold / "features.json").read_text())
        assert spec["candidates"] == source_spec["station"]
        for split in ("train", "evaluation"):
            frame = pq.read_table(directory / f"{split}.parquet")
            original = pq.read_table(GPU / fold / f"{split}.parquet")
            assert len(frame) == len(original)
            assert frame.select(["ts", "grp"]).to_pylist() == original.select(["ts", "grp"]).to_pylist()
            equal_source(frame, original)
            names = ["ts", "site_id", "capacity_kw"]
            if split == "train":
                names = ["ts", "site_id", "cf", "cosz", "wa_cloud", "wb_cloud", "capacity_kw"]
            filters = [("ts", "<=", cutoff), ("night", "==", False)] if split == "train" else [("ts", ">", cutoff), ("ts", "<=", end), ("night", "==", False)]
            source_path = SITE / fold / ("train.parquet" if split == "train" else "selection.parquet")
            sites = pq.read_table(directory / f"site_{split}.parquet")
            source = pq.read_table(source_path, columns=names, filters=filters)
            assert set(sites.column_names) == set(names) and len(sites) == len(source)
            assert sites.select(["ts", "site_id"]).to_pylist() == source.select(["ts", "site_id"]).to_pylist()
            for name in names:
                np.testing.assert_array_equal(sites[name].to_numpy(), source[name].to_numpy(), err_msg=name)
            rows = sites.select(["ts", "site_id", "capacity_kw"]).to_pylist()
            assert len({(r["ts"], r["site_id"]) for r in rows}) == len(rows)
            grouped = defaultdict(list)
            for row in rows:
                assert row["capacity_kw"] == metadata[row["site_id"]]
                grouped[(row["ts"], assignment[row["site_id"]])].append(row["capacity_kw"])
            group_capacity = {key: fsum(values) for key, values in grouped.items()}
            expected_keys = {(r["ts"], r["grp"]) for r in frame.select(["ts", "grp"]).to_pylist()}
            assert set(group_capacity) == expected_keys
            capacities = pq.read_table(directory / f"{split}_capacity.parquet").to_pylist()
            assert len(capacities) == len(expected_keys) and {(r["ts"], r["grp"]) for r in capacities} == expected_keys
            source_capacity = pq.read_table(OUT.parent / "group_wave/data" / fold / "groups.parquet", columns=["ts", "grp", "day_capacity"]).to_pylist() if split == "train" else frame.select(["ts", "grp", "capacity_kw"]).to_pylist()
            source_name = "day_capacity" if split == "train" else "capacity_kw"
            original_capacity = {(r["ts"], r["grp"]): r[source_name] for r in source_capacity}
            for row in capacities:
                key = row["ts"], row["grp"]
                assert isclose(row["capacity_kw"], group_capacity[key], rel_tol=1e-12, abs_tol=1e-8)
                assert row["capacity_kw"] == original_capacity[key]
            if split == "train":
                assert all(r["ts"] <= cutoff for r in rows)
                selected = []
                for name in source_spec["station"]:
                    values = frame[name].to_numpy()
                    if len(np.unique(values[~np.isnan(values)])) > 1:
                        selected.append(name)
                assert spec["features"] == selected
                assert not {"y", "cf", "energy", "smp", "k", "gain", "group_gain"} & set(selected)
            else:
                assert all(cutoff < r["ts"] <= end for r in rows)
                assert not {"y", "cf", "energy", "smp", "k", "gain", "group_gain"} & set(frame.column_names)
            checked.append({"fold": fold, "split": split, "site_rows": len(sites), "group_rows": len(frame), "capacity_keys_exact": True})
        labels = pq.read_table(directory / "labels.parquet").to_pylist()
        canonical = pq.read_table(OUT.parent / "calibration_wave/comparisons/temperature_then_snow" / fold / "predictions.parquet", columns=["ts", "grp", "p", "y", "smp", "k"]).to_pylist()
        reference = {(r["ts"], r["grp"]): r for r in canonical}
        assert len(labels) == len(reference) and {(r["ts"], r["grp"]) for r in labels} == set(reference)
        for row in labels:
            original = reference[(row["ts"], row["grp"])]
            assert row["p_reference"] == original["p"] and all(row[n] == original[n] for n in ("y", "smp", "k"))
        assert not (OUT / "coefficients" / f"{fold}.json").exists()
        assert not (directory / "training_transform.parquet").exists()
    evidence = {"status": "PASS", "records": checked, "protocol_sha256": digest(OUT / "protocol.json"),
                "prepared_manifest_sha256": digest(OUT / "prepared_manifest.json"),
                "scope": "Exact original group and bounded site targets/forecast projections, static assignment, independent capacity sums and feature masks. No real quantile/coefficient fit or model fit."}
    (OUT / "independent_data_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
