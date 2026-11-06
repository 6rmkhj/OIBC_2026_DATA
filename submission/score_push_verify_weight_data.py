# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "lightgbm"]
# ///
# How to run: python submission/score_push_verify_weight_data.py
"""Independently check train-only monetary weights against protected source data."""
from __future__ import annotations

import json
from datetime import datetime
from math import fsum, isclose
from typing import Final
from zoneinfo import ZoneInfo

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from score_push_verify import ROOT, digest
from score_push_verify_renew_final_data import equal_source, scale

OUT: Final = ROOT / "analysis_outputs/renew_20261105/weight_wave"
GPU: Final = ROOT / "analysis_outputs/score_push_gpu_20261104/data"
RENEW: Final = OUT.parent


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = json.loads((OUT / "protocol.json").read_text())
    for path, expected in protocol["input_sha256"].items():
        assert digest(ROOT / path) == expected, path
    for path, expected in json.loads((OUT / "prepared_manifest.json").read_text()).items():
        assert digest(OUT / path) == expected, path
    checked = []
    for fold, date in (("primary", "2023-06-01"), ("recent", "2024-06-01")):
        cutoff = datetime.fromisoformat(date).replace(tzinfo=ZoneInfo("Asia/Seoul"))
        directory = OUT / "data" / fold
        train = pq.read_table(directory / "train.parquet")
        original = pq.read_table(GPU / fold / "train.parquet")
        assert len(train) == len(original)
        assert train.select(["ts", "grp"]).to_pylist() == original.select(["ts", "grp"]).to_pylist()
        equal_source(train, original)
        source_features = json.loads((GPU / fold / "features.json").read_text())["station"]
        assert set(train.column_names) == {"ts", "grp", "cf", *source_features}
        context = pq.read_table(directory / "train_context.parquet")
        assert len(context) == len(train)
        np.testing.assert_array_equal(context["row_id"].to_numpy(), np.arange(len(train)))
        assert context.select(["ts", "grp"]).to_pylist() == train.select(["ts", "grp"]).to_pylist()
        raw = pq.read_table(RENEW / "group_wave/data" / fold / "groups.parquet", columns=["ts", "grp", "day_capacity", "smp", "k"])
        assert len(raw) == len(context)
        assert {(r["ts"], r["grp"]) for r in raw.select(["ts", "grp"]).to_pylist()} == {(r["ts"], r["grp"]) for r in context.select(["ts", "grp"]).to_pylist()}
        equal_source(context, raw)
        times = train["ts"].to_pylist()
        assert all(ts <= cutoff for ts in times)
        normalizer = scale(train["cosz"].to_numpy())
        age = np.array([(cutoff - ts).total_seconds() / 86400 for ts in times])
        decay = np.exp2(-age / 180)
        decay /= fsum(decay) / len(decay)
        base = normalizer * decay
        for name, expected in (("normalizer", normalizer), ("age_days", age), ("decay", decay), ("base_weight", base)):
            np.testing.assert_allclose(context[name].to_numpy(), expected, rtol=1e-12, atol=1e-12, err_msg=name)
        peak = np.array([3. if 11 <= ts.hour <= 15 else 1. for ts in times])
        np.testing.assert_array_equal(context["k"].to_numpy(), peak)
        cap, price = context["day_capacity"].to_numpy(), context["smp"].to_numpy()
        assert np.isfinite(cap).all() and np.isfinite(price).all() and (cap > 0).all() and (price >= 0).all()
        for arm, modifier in (("peak_k", peak), ("scored", cap * price * peak)):
            saved = pq.read_table(OUT / "data" / arm / fold / "weights.parquet")
            assert saved.select(["row_id", "ts", "grp"]).to_pylist() == context.select(["row_id", "ts", "grp"]).to_pylist()
            constant = fsum(base) / fsum(base * modifier)
            expected = base * modifier * constant
            assert np.isfinite(expected).all() and (expected >= 0).all()
            for field, value in (("base_weight", base), ("modifier", modifier), ("normalization", np.full(len(train), constant)), ("sample_weight", expected)):
                np.testing.assert_allclose(saved[field].to_numpy(), value, rtol=1e-12, atol=1e-12, err_msg=field)
            assert isclose(fsum(saved["sample_weight"].to_pylist()), fsum(base), rel_tol=1e-12)
            np.testing.assert_array_equal(saved["sample_weight"].to_numpy() == 0, modifier == 0)
            checked.append({"arm": arm, "fold": fold, "rows": len(train), "zero_weights": int((expected == 0).sum()),
                            "normalization": constant, "sum_weights": fsum(expected), "sum_baseline": fsum(base)})
        spec = json.loads((directory / "features.json").read_text())
        selected = []
        for name in source_features:
            values = train[name].to_numpy()
            if len(np.unique(values[~np.isnan(values)])) > 1:
                selected.append(name)
        assert spec["candidates"] == source_features and spec["features"] == selected
        assert not {"smp", "k", "cf", "y", "energy", "day_capacity"} & set(selected)
        evaluation = pq.read_table(directory / "evaluation.parquet")
        original_eval = pq.read_table(GPU / fold / "evaluation.parquet")
        assert len(evaluation) == len(original_eval)
        assert evaluation.select(["ts", "grp"]).to_pylist() == original_eval.select(["ts", "grp"]).to_pylist()
        equal_source(evaluation, original_eval)
        assert set(evaluation.column_names) == {"ts", "grp", "capacity_kw", *source_features}
        labels = pq.read_table(directory / "labels.parquet").to_pylist()
        selected_reference = pq.read_table(RENEW / "calibration_wave/comparisons/temperature_then_snow" / fold / "predictions.parquet", columns=["ts", "grp", "p", "y", "smp", "k"]).to_pylist()
        reference = {(r["ts"], r["grp"]): r for r in selected_reference}
        assert len(labels) == len(reference) and {(r["ts"], r["grp"]) for r in labels} == set(reference)
        for row in labels:
            expected = reference[(row["ts"], row["grp"])]
            assert row["p_reference"] == expected["p"] and all(row[n] == expected[n] for n in ("y", "smp", "k"))
    evidence = {"status": "PASS", "weights": checked, "protocol_sha256": digest(OUT / "protocol.json"),
                "prepared_manifest_sha256": digest(OUT / "prepared_manifest.json"),
                "scope": "All train/eval source values, exact capacity/price/peak joins, train-only normalized weights and zero retention, feature masks, canonical calibrated reference. No fit or confirmation read."}
    (OUT / "independent_data_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
