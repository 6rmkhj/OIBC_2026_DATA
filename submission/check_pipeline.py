#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "joblib"]
# ///
# How to run: python submission/check_pipeline.py
"""Run numerical boundary checks through the actual legacy pipeline functions."""
from __future__ import annotations

from datetime import datetime
from math import isclose

import pyarrow as pa

import make_submission as pipeline


def main() -> None:
    site = pipeline.SITES.iloc[0]
    timestamp = datetime.fromisoformat("2024-06-01T12:00:00+09:00")
    first = pa.Table.from_pylist([
        {**{c: 1.0 for c in pipeline.A6}, "wa_station": site.wa_station,
         "ts": timestamp, "wa_temp": float("nan")},
    ]).to_pandas()
    fallback = first.copy()
    fallback[pipeline.A6] = 9.0
    second = pa.Table.from_pylist([
        {**{c: 2.0 for c in pipeline.B9}, "wb_station": site.wb_station, "ts": timestamp},
    ]).to_pandas()
    base = pa.Table.from_pylist([{"site_id": site.site_id, "ts": timestamp}]).to_pandas()
    original_loader = pipeline.load_fc
    try:
        pipeline.load_fc = lambda split, rnd: (first, second) if rnd == 17 else (fallback, second)
        actual = pipeline.panel(base, "test")
    finally:
        pipeline.load_fc = original_loader
    assert actual.wa_cloud.iloc[0] == 1.0, "Valid round-17 cloud must survive partial fallback"
    assert actual.wa_temp.iloc[0] == 9.0, "Missing temperature must use round-10 value"
    print("PASS partial-field fallback preserves round-17 values")

    ids = pipeline.IDS[:2]
    predictions = pa.Table.from_pylist([
        {"site_id": ids[0], "ts": timestamp, "y": 10.0, "p": 14.0},
        {"site_id": ids[1], "ts": timestamp, "y": 20.0, "p": 17.0},
    ]).to_pandas()
    metric = pipeline.score(predictions, dict(zip(ids, ["G1", "G2"])), "numerical self-check")
    assert isclose(metric["W_pct"], 100 * 7 / 30, rel_tol=1e-6)
    assert isclose(metric["W_pool_pct"], 100 / 30, rel_tol=1e-6)
    print("PASS group absolute errors precede summation; portfolio cancellation is not scored")


if __name__ == "__main__":
    main()
