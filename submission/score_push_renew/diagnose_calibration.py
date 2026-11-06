# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow"]
# ///
# How to run: python submission/score_push_renew/diagnose_calibration.py
"""Describe the frozen calibration gain with paired calendar-block resampling."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from datetime import timedelta
from math import fsum, isclose
from pathlib import Path
from typing import Final

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

ROOT: Final = Path(__file__).resolve().parents[2]
BASE: Final = ROOT / "analysis_outputs/renew_20261105"
OUT: Final = BASE / "calibration_diagnostics"


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    OUT.mkdir(parents=True, exist_ok=True)
    hashes, results, monthly = {}, [], []
    for fold in ("primary", "recent"):
        paths = (
            BASE / "calibration_wave/comparisons/temperature_then_snow" / fold / "predictions.parquet",
            BASE / "recency_wave/comparisons/decay180/ensemble" / fold / "predictions.parquet",
        )
        for path in (*paths, Path(__file__)):
            with path.open("rb") as handle:
                hashes[str(path.relative_to(ROOT))] = hashlib.file_digest(handle, "sha256").hexdigest()
        rows = pq.read_table(paths[0], columns=["ts", "grp", "y", "smp", "k", "p"]).to_pylist()
        previous = pq.read_table(paths[1], columns=["ts", "grp", "y", "smp", "k", "p", "p_reference", "p_incumbent"]).to_pylist()
        reference = {(r["ts"], r["grp"]): r for r in previous}
        assert len(reference) == len(previous) == len(rows)
        assert {(r["ts"], r["grp"]) for r in rows} == set(reference)
        for name, column in (("cpu", "p_reference"), ("temporal", "p"), ("official_incumbent_recipe", "p_incumbent")):
            days, months = defaultdict(list), defaultdict(list)
            for row in rows:
                old = reference[(row["ts"], row["grp"])]
                assert all(row[n] == old[n] for n in ("y", "smp", "k"))
                weight = row["smp"] * row["k"]
                calibrated_loss = weight * abs(row["p"] - row["y"])
                old_loss = weight * abs(old[column] - row["y"])
                record = (calibrated_loss - old_loss, weight * row["y"], calibrated_loss, old_loss)
                date = (row["ts"] - timedelta(hours=1)).date()
                days[date].append(record)
                months[date.strftime("%Y-%m")].append(record)
            ordered = sorted(days)
            assert all((b - a).days == 1 for a, b in zip(ordered, ordered[1:]))
            daily = np.array([[fsum(r[i] for r in days[d]) for i in range(4)] for d in ordered])
            delta = 100 * fsum(daily[:, 0]) / fsum(daily[:, 1])
            assert isclose(delta, 100 * (fsum(daily[:, 2]) - fsum(daily[:, 3])) / fsum(daily[:, 1]), abs_tol=1e-10)
            for length in (1, 7):
                rng = np.random.default_rng(20261105)
                count = len(daily)
                starts = rng.integers(0, count, size=(4000, (count + length - 1) // length))
                indices = ((starts[:, :, None] + np.arange(length)) % count).reshape(4000, -1)[:, :count]
                samples = daily[indices]
                draws = 100 * samples[:, :, 0].sum(axis=1) / samples[:, :, 1].sum(axis=1)
                assert np.isfinite(draws).all()
                results.append({
                    "fold": fold, "reference": name, "days": count, "block_days": length,
                    "delta_W_pct": delta, "delta_W": fsum(daily[:, 0]),
                    "delta_proxy_S": -.1 * fsum(daily[:, 0]),
                    "paired_bootstrap_95pct_pp": np.quantile(draws, [.025, .975]).tolist(),
                    "replicates": 4000, "seed": 20261105,
                })
            for month, part in sorted(months.items()):
                denominator = fsum(r[1] for r in part)
                monthly.append({
                    "fold": fold, "reference": name, "month": month,
                    "W_pct": 100 * fsum(r[2] for r in part) / denominator,
                    "reference_W_pct": 100 * fsum(r[3] for r in part) / denominator,
                    "delta_W_pct": 100 * fsum(r[0] for r in part) / denominator,
                    "delta_W": fsum(r[0] for r in part),
                })
    with (OUT / "monthly.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(monthly[0]))
        writer.writeheader()
        writer.writerows(monthly)
    evidence = {
        "status": "PASS", "input_sha256": hashes, "model_fits": 0, "results": results,
        "method": "Paired circular moving-block bootstrap of whole calendar days, preserving both groups together.",
        "limitations": "Descriptive only. Primary calibration fitted on these rows. All periods historically exposed. Intervals condition on fitted predictions and do not correct adaptive selection or calibration estimation. Proxy S is not an official score.",
    }
    (OUT / "results.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "results": results}, indent=2))


if __name__ == "__main__":
    main()
