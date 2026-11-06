# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow"]
# ///
# How to run: python submission/score_push_verify_group_data.py
"""Rebuild bounded raw group targets and monetary weights independently."""
from __future__ import annotations

import csv
import gc
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Final
from zoneinfo import ZoneInfo

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ROOT: Final = Path(__file__).resolve().parents[1]
OUT: Final = ROOT / "analysis_outputs/renew_20261105/group_wave"
KST: Final = ZoneInfo("Asia/Seoul")


def sha(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def table_keys(table: pa.Table, second: str) -> list[tuple[datetime, str]]:
    return list(zip(table["ts"].to_pylist(), table[second].to_pylist(), strict=True))


def verify_fold(fold: str, protocol: dict[str, str]) -> dict[str, int | float | str]:
    cutoff = datetime(2023 if fold == "primary" else 2024, 6, 1, tzinfo=KST)
    end = datetime(2024, 6, 1, tzinfo=KST) if fold == "primary" else datetime(2025, 3, 1, tzinfo=KST)
    assignment = json.loads((ROOT / protocol["assignment"]).read_text())
    with (ROOT / protocol["metadata"]).open(encoding="utf-8", newline="") as handle:
        metadata = list(csv.DictReader(handle))
    capacity = {r["site_id"]: float(r["capacity_kw"]) for r in metadata}
    with (ROOT / protocol["smp"]).open(encoding="utf-8", newline="") as handle:
        prices = {datetime.fromisoformat(r["ts"]): float(r["smp"]) for r in csv.DictReader(handle)}
    directory = OUT / "data" / fold
    features = json.loads((directory / "features.json").read_text())
    for category in ("site_id", "wa_station", "wb_station"):
        assert features["categories"][category] == sorted({r[category] for r in metadata})
    expected_features = json.loads((ROOT / "analysis_outputs/autoresearch_20261103/cache/features.json").read_text())
    expected_features += ["capacity_kw", "lat", "lon", "site_id", "wa_station", "wb_station", "site_humidity_clear", "site_dew_spread", "site_uv_clear"]
    assert features["features"] == expected_features
    assert not {"ts", "cf", "energy", "y", "smp", "k", "grp", "group_id", "night"} & set(expected_features)
    train = pq.read_table(directory / "train.parquet")
    old_train = pq.read_table(ROOT / "analysis_outputs/score_push_20261104/site_wave/cache" / fold / "train.parquet")
    assert train.select(old_train.column_names).equals(old_train)
    rows = pq.read_table(directory / "rows.parquet")
    assert table_keys(rows, "site_id") == table_keys(train, "site_id")
    assert len(rows) == features["train_rows"] == (521423 if fold == "primary" else 1203117)
    np.testing.assert_array_equal(rows["row_id"].to_numpy(), np.arange(len(rows)))
    np.testing.assert_array_equal(rows["cf"].to_numpy(), train["cf"].to_numpy())
    caps = np.array([capacity[site] for site in train["site_id"].to_pylist()])
    np.testing.assert_array_equal(caps, train["capacity_kw"].to_numpy())
    assert rows["grp"].to_pylist() == [assignment[site] for site in train["site_id"].to_pylist()]
    assert all(ts <= cutoff for ts in train["ts"].to_pylist()) and not pc.any(train["night"]).as_py()
    del old_train
    raw = pq.read_table(ROOT / protocol["raw"], columns=["ts", "site_id", "energy"], filters=[("ts", "<=", cutoff)]).sort_by([("ts", "ascending"), ("site_id", "ascending")])
    original = pq.read_table(ROOT / protocol["original"], columns=["ts", "site_id", "energy", "night"], filters=[("ts", "<=", cutoff)]).sort_by([("ts", "ascending"), ("site_id", "ascending")])
    assert table_keys(raw, "site_id") == table_keys(original, "site_id")
    assert len(set(table_keys(raw, "site_id"))) == len(raw)
    np.testing.assert_array_equal(raw["energy"].to_numpy().astype(np.float32), original["energy"].to_numpy())
    assert set(table_keys(raw.filter(pc.invert(original["night"])), "site_id")) == set(table_keys(train, "site_id"))
    raw_groups = pa.array([assignment[site] for site in raw["site_id"].to_pylist()])
    grouped = raw.append_column("grp", raw_groups).append_column("night_energy", pc.if_else(original["night"], raw["energy"], 0.))
    full = grouped.group_by(["ts", "grp"], use_threads=False).aggregate([("energy", "sum"), ("energy", "count"), ("night_energy", "sum")]).sort_by([("ts", "ascending"), ("grp", "ascending")])
    complete = pq.read_table(directory / "complete_training_groups.parquet").sort_by([("ts", "ascending"), ("grp", "ascending")])
    assert table_keys(full, "grp") == table_keys(complete, "grp")
    np.testing.assert_allclose(full["energy_sum"].to_numpy(), complete["full_energy"].to_numpy(), rtol=1e-12, atol=1e-7)
    np.testing.assert_array_equal(full["energy_count"].to_numpy(), complete["observed_sites"].to_numpy())
    np.testing.assert_allclose(full["night_energy_sum"].to_numpy(), complete["night_energy"].to_numpy(), rtol=1e-12, atol=1e-10)
    day = rows.select(["ts", "grp", "capacity_kw"]).group_by(["ts", "grp"], use_threads=False).aggregate([("capacity_kw", "sum"), ("capacity_kw", "count")]).sort_by([("ts", "ascending"), ("grp", "ascending")])
    groups = pq.read_table(directory / "groups.parquet")
    assert table_keys(groups, "grp") == table_keys(day, "grp")
    np.testing.assert_array_equal(groups["group_id"].to_numpy(), np.arange(len(groups)))
    day_capacity = day["capacity_kw_sum"].to_numpy()
    np.testing.assert_allclose(groups["day_capacity"].to_numpy(), day_capacity, rtol=1e-12)
    np.testing.assert_array_equal(groups["day_sites"].to_numpy(), day["capacity_kw_count"].to_numpy())
    full_map = dict(zip(table_keys(full, "grp"), full["energy_sum"].to_numpy(), strict=True))
    target = np.array([full_map[key] for key in table_keys(groups, "grp")]) / day_capacity
    np.testing.assert_allclose(groups["target"].to_numpy(), target, rtol=1e-12, atol=1e-12)
    group_map = dict(zip(table_keys(groups, "grp"), range(len(groups)), strict=True))
    group_ids = np.array([group_map[key] for key in table_keys(rows, "grp")])
    np.testing.assert_array_equal(group_ids, rows["group_id"].to_numpy())
    share = caps / day_capacity[group_ids]
    np.testing.assert_allclose(rows["share"].to_numpy(), share, rtol=1e-12)
    np.testing.assert_allclose(np.bincount(group_ids, weights=share), 1., rtol=1e-12)
    times = rows["ts"].to_pylist()
    smp = np.array([prices[ts] for ts in times])
    k = np.array([3. if 11 <= ts.hour <= 15 else 1. for ts in times])
    assert np.isfinite(smp).all() and (smp >= 0).all()
    weight_raw = caps * smp * k
    normalization = weight_raw.sum(dtype=np.float64) / len(weight_raw)
    assert normalization > 0 and abs(normalization - features["normalization"]) <= 1e-9
    for name, expected in (("smp", smp), ("k", k), ("weight_raw", weight_raw), ("weight", weight_raw / normalization)):
        np.testing.assert_allclose(rows[name].to_numpy(), expected, rtol=1e-12, atol=1e-12)
    expected_group_weight = np.array([prices[ts] * (3 if 11 <= ts.hour <= 15 else 1) for ts in groups["ts"].to_pylist()]) * day_capacity / normalization
    np.testing.assert_allclose(groups["group_weight"].to_numpy(), expected_group_weight, rtol=1e-12)
    evaluation = pq.read_table(directory / "evaluation.parquet")
    old_evaluation = pq.read_table(ROOT / "analysis_outputs/score_push_20261104/site_wave/cache" / fold / "selection.parquet")
    assert evaluation.select(old_evaluation.column_names).equals(old_evaluation)
    assert all(cutoff < ts <= end for ts in evaluation["ts"].to_pylist())
    assert not {"cf", "y", "energy", "smp", "k"} & set(evaluation.column_names)
    labels = pq.read_table(directory / "labels.parquet")
    reference = pq.read_table(ROOT / "analysis_outputs/renew_20261105/recency_wave/comparisons/decay180/ensemble" / fold / "predictions.parquet", columns=["ts", "grp", "y", "smp", "k", "p"])
    assert labels.equals(reference.rename_columns(["ts", "grp", "y", "smp", "k", "p_reference"]))
    coverage = evaluation.select(["ts", "grp", "night"]).group_by(["ts", "grp"], use_threads=False).aggregate([("night", "all"), ("night", "count")]).sort_by([("ts", "ascending"), ("grp", "ascending")])
    saved_coverage = pq.read_table(directory / "coverage.parquet").sort_by([("ts", "ascending"), ("grp", "ascending")])
    assert table_keys(saved_coverage, "grp") == table_keys(coverage, "grp")
    np.testing.assert_array_equal(saved_coverage["night"].to_numpy(), coverage["night_all"].to_numpy())
    np.testing.assert_array_equal(saved_coverage["sites"].to_numpy(), coverage["night_count"].to_numpy())
    assert set(table_keys(labels, "grp")) == set(table_keys(coverage, "grp"))
    return {"fold": fold, "training_rows": len(rows), "groups": len(groups), "complete_training_groups": len(full),
            "raw_generation_rows": len(raw), "night_energy": float(pc.sum(full["night_energy_sum"]).as_py()),
            "zero_weight_rows": int((weight_raw == 0).sum()), "evaluation_rows": len(evaluation),
            "allnight_evaluation_groups": int(pc.sum(pc.cast(saved_coverage["night"], pa.int64())).as_py())}


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = json.loads((OUT / "protocol.json").read_text())
    for path, digest in json.loads((OUT / "prepared_manifest.json").read_text()).items():
        assert sha(OUT / path) == digest, path
    records = []
    for fold in ("primary", "recent"):
        records.append(verify_fold(fold, protocol))
        gc.collect()
    result = {"status": "PASS", "protocol_sha256": sha(OUT / "protocol.json"), "prepared_manifest_sha256": sha(OUT / "prepared_manifest.json"),
              "records": records, "target_precision": "original raw float64; exact raw-to-cache float32 projection verified",
              "bounded_target_reads": True, "night_contributions_preserved": True, "feature_labels_excluded": True}
    (OUT / "independent_data_check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
