# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow"]
# ///
# How to run: python submission/score_push_verify_cloud_data.py
"""Independent observation, forward-lineage and capacity-aggregation checks."""
from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from math import isfinite
from typing import Final

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from score_push_verify import ROOT, digest

OUT: Final = ROOT / "analysis_outputs/renew_20261105/cloud_wave"
DATA: Final = ROOT / "analysis_outputs/score_push_gpu_20261104/data"
RAW: Final = ROOT / "handover 2/01_participant_dataset"
KST: Final = timezone(timedelta(hours=9))
TIME_TYPE: Final = pa.timestamp("ns", tz="Asia/Seoul")


def timestamps(table: pa.Table) -> pa.Table:
    return table.set_column(table.schema.get_field_index("ts"), "ts", table["ts"].cast(TIME_TYPE))


def same_columns(left: pa.Table, right: pa.Table, names: list[str]) -> None:
    assert len(left) == len(right)
    for name in names:
        np.testing.assert_array_equal(left[name].to_numpy(), right[name].to_numpy())


def match_cloud(used: pa.Table, oracle: pa.Table, station: str) -> None:
    actual = timestamps(used.select([station, "ts", "p_cloud"]))
    expected = timestamps(oracle.select([station, "ts", "p_cloud"]))
    expected = expected.rename_columns([station, "ts", "expected_cloud"])
    expected = expected.append_column("matched", pa.array(np.ones(len(expected), dtype=np.int8)))
    joined = actual.join(expected, keys=[station, "ts"], join_type="left outer")
    assert len(joined) == len(actual) and joined["matched"].null_count == 0
    np.testing.assert_array_equal(joined["p_cloud"].to_numpy(), joined["expected_cloud"].to_numpy())


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = json.loads((OUT / "protocol.json").read_text())
    dates = protocol["cutoffs"]
    cutoffs = [datetime.fromisoformat(date).replace(tzinfo=KST) for date in dates]
    checked_models = []
    for provider in ("wa", "wb"):
        station, target = f"{provider}_station", f"{provider}_cloud"
        schema = json.loads((OUT / "data" / f"{provider}_schema.json").read_text())
        assert digest(OUT / "data" / f"{provider}_forecast.parquet") == schema["sha256"]
        assert station in schema["features"] and "ts" not in schema["features"]
        assert all(name == station or name.startswith(("base_", "r10_", "rev_")) or name in ("missing17", "missing10", "hour_sin", "hour_cos", "doy_sin", "doy_cos") for name in schema["features"])
        assert not {"y", "cf", "energy", "smp", "k", target} & set(schema["features"])
        for index, cutoff in enumerate(cutoffs):
            directory = OUT / "auxiliary" / provider / dates[index]
            config = json.loads((directory / "config.json").read_text())
            original = pq.read_table(RAW / "train" / f"observed_{provider}.parquet", columns=[station, "ts", target], filters=[("ts", "<=", cutoff - timedelta(days=1))])
            values = original[target].to_numpy()
            valid = np.isfinite(values) & (values >= 0) & (values <= 100)
            expected = original.filter(pa.array(valid))
            saved = pq.read_table(directory / "labels.parquet")
            same_columns(expected, saved, [station, "ts", target])
            assert len(saved) == config["training_rows"] == config["observation_read"]["valid_rows"]
            assert config["observation_read"]["invalid_excluded"] == int((~valid).sum())
            assert datetime.fromisoformat(config["training_max"]) <= cutoff - timedelta(days=1)
            assert datetime.fromisoformat(config["observation_read"]["read_filter_max"]) == cutoff - timedelta(days=1)
            assert digest(directory / "labels.parquet") == config["labels_sha256"]
            assert config["features"] == schema["features"] and config["categorical"] == [station]
            assert config["panel_sha256"] == schema["sha256"]
            assert config["parameters"]["task_type"] == "GPU" and config["parameters"]["random_seed"] == 0
            assert config["parameters"]["iterations"] == 1000 and config["parameters"]["depth"] == 6
            end = cutoffs[index + 1] if index + 1 < len(cutoffs) else datetime(2025, 3, 1, tzinfo=KST)
            if cutoff == datetime(2023, 6, 1, tzinfo=KST):
                end = datetime(2024, 6, 1, tzinfo=KST)
            prediction = pq.read_table(directory / "predictions.parquet")
            forecast_keys = pq.read_table(OUT / "data" / f"{provider}_forecast.parquet", columns=[station, "ts"], filters=[("ts", ">", cutoff), ("ts", "<=", end)])
            same_columns(prediction, forecast_keys, [station, "ts"])
            raw = prediction["p_raw"].to_numpy()
            assert np.isfinite(raw).all()
            np.testing.assert_array_equal(prediction["p_cloud"].to_numpy(), np.clip(raw, 0, 100))
            assert all(value == cutoff for value in prediction["model_cutoff"].to_pylist())
            assert all(value == 0 for value in prediction["warmup"].to_pylist())
            checked_models.append({"provider": provider, "cutoff": dates[index], "training_rows": len(saved), "prediction_rows": len(prediction), "invalid_targets_excluded": int((~valid).sum()), "exact_raw_observation_rows_preserved": True})
    with (RAW / "sites.csv").open(encoding="utf-8-sig", newline="") as stream:
        sites = {row["site_id"]: row for row in csv.DictReader(stream)}
    assignment = json.loads((ROOT / protocol["assignment_source"]).read_text())
    checked_features = []
    for fold in ("primary", "recent"):
        cutoff = datetime(2023 if fold == "primary" else 2024, 6, 1, tzinfo=KST)
        for kind in ("train", "evaluation"):
            key_rows = pq.read_table(DATA / fold / f"{kind}.parquet", columns=["ts", "grp"]).to_pylist()
            keys = [(row["ts"], row["grp"]) for row in key_rows]
            key_index = {key: index for index, key in enumerate(keys)}
            assert len(keys) == len(key_index)
            features = pq.read_table(OUT / "data" / fold / f"{kind}_features.parquet")
            assert list(zip(features["ts"].to_pylist(), features["grp"].to_pylist(), strict=True)) == keys
            source = pq.read_table(ROOT / protocol["night_source"], columns=["site_id", "ts", "night", "capacity_kw"], filters=[("ts", ">=", min(ts for ts, _ in keys)), ("ts", "<=", max(ts for ts, _ in keys)), ("night", "==", False)])
            for provider in ("wa", "wb"):
                station = f"{provider}_station"
                used = pq.read_table(OUT / "data" / fold / f"{kind}_{provider}_lineage.parquet")
                times = used["ts"].to_pylist()
                actual_cutoffs = used["model_cutoff"].to_pylist()
                expected_cutoffs = [cutoff] * len(used) if kind == "evaluation" else [max((value for value in cutoffs if value < ts), default=None) for ts in times]
                assert actual_cutoffs == expected_cutoffs
                expected_warmup = np.array([value is None for value in expected_cutoffs], dtype=np.int8)
                np.testing.assert_array_equal(used["warmup"].to_numpy(), expected_warmup)
                for origin in set(expected_cutoffs):
                    part = used.filter(pa.array([value == origin for value in expected_cutoffs]))
                    if origin is None:
                        warmup = pq.read_table(OUT / "data" / f"{provider}_forecast.parquet", columns=[station, "ts", f"base_{provider}_cloud"], filters=[("ts", "<=", cutoffs[0])])
                        oracle = warmup.select([station, "ts"]).append_column("p_cloud", pa.array(np.clip(warmup[f"base_{provider}_cloud"].to_numpy(), 0, 100)))
                    else:
                        oracle = pq.read_table(OUT / "auxiliary" / provider / origin.strftime("%Y-%m-%d") / "predictions.parquet", columns=[station, "ts", "p_cloud"])
                    match_cloud(part, oracle, station)
                lookup = {(sid, ts): value for sid, ts, value in zip(used[station].to_pylist(), times, used["p_cloud"].to_pylist(), strict=True)}
                assert len(lookup) == len(used)
                levels = sorted({row[station] for row in sites.values()})
                level_index = {value: index for index, value in enumerate(levels)}
                total = np.zeros(len(keys))
                available = np.zeros(len(keys))
                numerator = np.zeros(len(keys))
                contributions = np.zeros((len(keys), len(levels)))
                present = np.zeros_like(contributions, dtype=np.int64)
                known = np.zeros_like(present)
                touched = set()
                for batch in source.to_batches(max_chunksize=65536):
                    for row in batch.to_pylist():
                        key = row["ts"], assignment[row["site_id"]]
                        if key not in key_index:
                            continue
                        index = key_index[key]
                        sid = sites[row["site_id"]][station]
                        position = level_index[sid]
                        value = lookup[sid, row["ts"]]
                        capacity = row["capacity_kw"]
                        assert isfinite(capacity) and capacity > 0
                        total[index] += capacity
                        present[index, position] += 1
                        touched.add((sid, row["ts"]))
                        if value is not None and isfinite(value):
                            numerator[index] += capacity * value
                            available[index] += capacity
                            contributions[index, position] += capacity * value
                            known[index, position] += 1
                assert touched == set(lookup) and (total > 0).all()
                means = np.divide(numerator, available, out=np.full(len(keys), np.nan), where=available > 0)
                contributions /= total[:, None]
                contributions[(present > 0) & (known == 0)] = np.nan
                np.testing.assert_allclose(features[f"aux_{provider}_mean"].to_numpy(), means, rtol=1e-12, atol=1e-9, equal_nan=True)
                for position, sid in enumerate(levels):
                    np.testing.assert_allclose(features[f"aux_{provider}_{sid}_p_cloud"].to_numpy(), contributions[:, position], rtol=1e-12, atol=1e-9, equal_nan=True)
                flags = np.array([int(kind == "train" and ts <= cutoffs[0]) for ts, _ in keys])
                np.testing.assert_array_equal(features[f"aux_{provider}_warmup"].to_numpy(), flags)
                checked_features.append({"fold": fold, "kind": kind, "provider": provider, "group_rows": len(keys), "lineage_rows": len(used), "station_columns": len(levels)})
    evidence = {"status": "PASS", "auxiliary_models": checked_models, "feature_checks": checked_features, "observed_rows_including_duplicates_preserved": True, "embargo_days": 1, "fixed_outer_cutoffs_verified": True, "independent_capacity_aggregation": True}
    (OUT / "independent_data_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
