# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow"]
# ///
# How to run: python submission/score_push_verify_total_data.py
"""Reconstruct portfolio summaries, full targets and allocation without fitting."""
from __future__ import annotations

import json
from datetime import datetime
from math import fsum, isclose
from typing import Final
from zoneinfo import ZoneInfo

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from score_push_verify_group_data import ROOT, sha, table_keys

OUT: Final = ROOT / "analysis_outputs/renew_20261105/total_wave"
DATA: Final = ROOT / "analysis_outputs/score_push_gpu_20261104/data"
GROUP: Final = ROOT / "analysis_outputs/renew_20261105/group_wave"
REF: Final = ROOT / "analysis_outputs/renew_20261105/recency_wave/comparisons/decay180/ensemble"


def verify_summary(groups: pa.Table, total: pa.Table, names: list[str]) -> None:
    times = groups["ts"].to_pylist()
    unique = sorted(set(times))
    assert total["ts"].to_pylist() == unique
    mapping = {ts: i for i, ts in enumerate(unique)}
    indices = np.array([mapping[ts] for ts in times])
    capacity = groups["capacity_kw"].to_numpy()
    assert np.isfinite(capacity).all() and (capacity > 0).all()
    np.testing.assert_allclose(total["capacity_kw"].to_numpy(), np.bincount(indices, weights=capacity), rtol=1e-12)
    for name in names:
        values = groups[name].to_numpy().astype(np.float64)
        assert not np.isinf(values).any()
        valid = ~np.isnan(values)
        numerator = np.bincount(indices, weights=np.where(valid, values * capacity, 0.))
        denominator = np.bincount(indices, weights=np.where(valid, capacity, 0.))
        expected = np.divide(numerator, denominator, out=np.full(len(unique), np.nan), where=denominator > 0)
        np.testing.assert_allclose(total[name].to_numpy(), expected, rtol=1e-12, atol=1e-12, equal_nan=True, err_msg=name)


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = json.loads((OUT / "protocol.json").read_text())
    for name, digest in protocol["input_sha256"].items():
        assert sha(ROOT / name) == digest, name
    for name, record in protocol["own_sources"].items():
        assert sha(ROOT / record["original"]) == sha(OUT / "sources/own" / name) == record["sha256"]
    for name, digest in json.loads((OUT / "prepared_manifest.json").read_text()).items():
        assert sha(OUT / name) == digest, name
    checked_group = json.loads((GROUP / "independent_data_check.json").read_text())
    assert checked_group["status"] == "PASS" and checked_group["prepared_manifest_sha256"] == sha(GROUP / "prepared_manifest.json")
    group_manifest = json.loads((GROUP / "prepared_manifest.json").read_text())
    records = []
    for fold in ("primary", "recent"):
        cutoff = datetime(2023 if fold == "primary" else 2024, 6, 1, tzinfo=ZoneInfo("Asia/Seoul"))
        end = datetime(2024, 6, 1, tzinfo=ZoneInfo("Asia/Seoul")) if fold == "primary" else datetime(2025, 3, 1, tzinfo=ZoneInfo("Asia/Seoul"))
        directory = OUT / "data" / fold
        info = json.loads((directory / "features.json").read_text())
        original_info = json.loads((DATA / fold / "features.json").read_text())
        candidates = {f"total_{name}": [n for n in original_info[name] if n != "grp_code"] for name in ("rich", "station")}
        assert candidates == info["candidates"]
        names = candidates["total_station"]
        assert set(candidates["total_rich"]) <= set(names) and len(names) == 903
        assert not {"ts", "grp", "grp_code", "cf", "y", "energy", "smp", "k", "capacity_kw"} & set(names)
        capacities_path = GROUP / "data" / fold / "groups.parquet"
        full_path = GROUP / "data" / fold / "complete_training_groups.parquet"
        for path in (capacities_path, full_path):
            assert sha(path) == group_manifest[str(path.relative_to(GROUP))]
        capacities = pq.read_table(capacities_path, columns=["ts", "grp", "day_capacity"])
        cap_map = dict(zip(table_keys(capacities, "grp"), capacities["day_capacity"].to_numpy(), strict=True))
        for split in ("train", "evaluation"):
            source_columns = ["ts", "grp", *names] + (["capacity_kw"] if split == "evaluation" else [])
            source = pq.read_table(DATA / fold / f"{split}.parquet", columns=source_columns)
            saved = pq.read_table(directory / f"group_{split}_inputs.parquet")
            assert saved.select(source_columns).equals(source)
            assert len(set(table_keys(saved, "grp"))) == len(saved)
            if split == "train":
                assert set(table_keys(saved, "grp")) == set(cap_map)
                np.testing.assert_array_equal(saved["capacity_kw"].to_numpy(), [cap_map[key] for key in table_keys(saved, "grp")])
                assert all(ts <= cutoff for ts in saved["ts"].to_pylist())
            else:
                assert all(cutoff < ts <= end for ts in saved["ts"].to_pylist())
            total = pq.read_table(directory / f"{split}.parquet")
            assert not {"cf", "y", "energy", "smp", "k", "grp", "grp_code"} & set(total.column_names)
            verify_summary(saved, total, names)
            if split == "train":
                for arm, proposed in candidates.items():
                    selected = [n for n in proposed if len(np.unique(total[n].to_numpy()[~np.isnan(total[n].to_numpy())])) > 1]
                    assert selected == info["features"][arm]
        train = pq.read_table(directory / "train.parquet")
        targets = pq.read_table(directory / "targets_weights.parquet")
        assert targets["ts"].to_pylist() == train["ts"].to_pylist()
        original_full = pq.read_table(full_path, columns=["ts", "grp", "full_energy"])
        saved_full = pq.read_table(directory / "full_training_groups.parquet")
        assert original_full.equals(saved_full) and all(ts <= cutoff for ts in original_full["ts"].to_pylist())
        energies = {}
        for ts, value in zip(original_full["ts"].to_pylist(), original_full["full_energy"].to_numpy(), strict=True):
            energies.setdefault(ts, []).append(value)
        energy = np.array([fsum(energies[ts]) for ts in train["ts"].to_pylist()])
        cap = train["capacity_kw"].to_numpy()
        cosz = np.maximum(train["cosz"].to_numpy(), 0.)
        exponent = np.divide(-.059, cosz, out=np.zeros(len(cosz)), where=cosz > 0)
        normalizer = np.maximum(1.098 * cosz * np.exp(exponent), .05)
        age = np.array([(cutoff - ts).total_seconds() / 86400 for ts in train["ts"].to_pylist()])
        decay = np.exp2(-age / 180)
        decay /= fsum(decay) / len(decay)
        for name, values in (("capacity_kw", cap), ("full_total_energy", energy), ("cf", energy / cap), ("normalizer", normalizer),
                             ("age_days", age), ("decay", decay), ("sample_weight", normalizer * decay), ("target", energy / cap / normalizer)):
            np.testing.assert_allclose(targets[name].to_numpy(), values, rtol=1e-12, atol=1e-10, err_msg=name)
        labels = pq.read_table(directory / "labels.parquet")
        reference = pq.read_table(REF / fold / "predictions.parquet", columns=["ts", "grp", "y", "smp", "k", "p"])
        assert labels.equals(reference.rename_columns(["ts", "grp", "y", "smp", "k", "p_reference"]))
        allocation = pq.read_table(directory / "allocation_template.parquet").to_pylist()
        oracle = {(r["ts"], r["grp"]): r for r in labels.to_pylist()}
        eval_groups = pq.read_table(directory / "group_evaluation_inputs.parquet", columns=["ts", "grp", "capacity_kw"])
        cap_map = dict(zip(table_keys(eval_groups, "grp"), eval_groups["capacity_kw"].to_numpy(), strict=True))
        assert len(allocation) == len(oracle) == (17568 if fold == "primary" else 13104)
        assert {(r["ts"], r["grp"]) for r in allocation} == set(oracle)
        for row in allocation:
            ts, group = row["ts"], row["grp"]
            refs = [oracle[(ts, g)]["p_reference"] for g in ("G1", "G2")]
            caps = [cap_map.get((ts, g), 0.) for g in ("G1", "G2")]
            expected = oracle[(ts, group)]["p_reference"] / fsum(refs) if fsum(refs) > 0 else (cap_map.get((ts, group), 0.) / fsum(caps) if fsum(caps) > 0 else 0.)
            assert row["p_reference"] == oracle[(ts, group)]["p_reference"]
            assert row["capacity_kw"] == cap_map.get((ts, group), 0.)
            assert isclose(row["ratio"], expected, rel_tol=1e-12, abs_tol=1e-12)
            assert row["p_total"] == (1. if fsum(caps) > 0 else 0.)
            assert row["capacity_fallback"] == (fsum(refs) == 0 and fsum(caps) > 0)
            assert isclose(row["p_new"], expected, rel_tol=1e-12, abs_tol=1e-12)
        records.append({"fold": fold, "train_timestamps": len(train), "evaluation_timestamps": pq.ParquetFile(directory / "evaluation.parquet").metadata.num_rows,
                        "features": info["retained_counts"], "allocation_rows": len(allocation)})
    result = {"status": "PASS", "protocol_sha256": sha(OUT / "protocol.json"), "prepared_manifest_sha256": sha(OUT / "prepared_manifest.json"),
              "records": records, "original_raw_group_target_proof": str((GROUP / "independent_data_check.json").relative_to(ROOT)),
              "available_group_capacity_summary_verified": True, "targets_and_weights_verified": True, "allocation_label_free": True}
    (OUT / "independent_data_check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
