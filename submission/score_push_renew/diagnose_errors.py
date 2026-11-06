# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow"]
# ///
# How to run: python submission/score_push_renew/diagnose_errors.py
"""Describe exposed development errors without fitting or selecting a model."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime
from math import fsum, isfinite
from pathlib import Path
from typing import Final, TypedDict

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

ROOT: Final = Path(__file__).resolve().parents[2]
OUT: Final = ROOT / "analysis_outputs/renew_20261105/error_diagnostics"
DATA: Final = ROOT / "analysis_outputs/score_push_gpu_20261104/data"
REFERENCE: Final = ROOT / "analysis_outputs/renew_20261105/recency_wave/comparisons/decay180/ensemble"
FIELDS: Final = ("capacity_kw", "cosz", "wa_cloud", "wb_cloud", "wa_temp", "extra_wa_snow", "extra_wb_snow", "cdis")


class PredictionRow(TypedDict):
    ts: datetime
    grp: str
    y: float
    p: float
    smp: float
    k: float


def bucket(value: float, thresholds: tuple[float, ...]) -> str:
    if not isfinite(value):
        return "missing"
    index = int(np.searchsorted(thresholds, value, side="right"))
    lower = "-inf" if index == 0 else str(thresholds[index - 1])
    upper = "+inf" if index == len(thresholds) else str(thresholds[index])
    return f"[{lower},{upper})"


def summarize(rows: list[PredictionRow], total_loss: float) -> dict[str, float]:
    weight = [float(r["smp"]) * float(r["k"]) for r in rows]
    loss = fsum(w * abs(float(r["p"]) - float(r["y"])) for w, r in zip(weight, rows, strict=True))
    target = fsum(w * float(r["y"]) for w, r in zip(weight, rows, strict=True))
    signed = fsum(w * (float(r["p"]) - float(r["y"])) for w, r in zip(weight, rows, strict=True))
    return {"rows": len(rows), "W": loss, "loss_share_pct": 100 * loss / total_loss,
            "W_pct": 100 * loss / target if target else 0., "signed_pct": 100 * signed / target if target else 0.,
            "weighted_target": target}


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    OUT.mkdir(parents=True, exist_ok=True)
    all_results = []
    hashes = {}
    for fold in ("primary", "recent"):
        paths = (REFERENCE / fold / "predictions.parquet", DATA / fold / "evaluation.parquet")
        for path in paths:
            with path.open("rb") as handle:
                hashes[str(path.relative_to(ROOT))] = hashlib.file_digest(handle, "sha256").hexdigest()
        rows = pq.read_table(paths[0], columns=["ts", "grp", "y", "p", "smp", "k"]).to_pylist()
        weather = pq.read_table(paths[1], columns=["ts", "grp", *FIELDS]).to_pylist()
        feature_map = {(r["ts"], r["grp"]): r for r in weather}
        assert len(feature_map) == len(weather)
        assert len({(r["ts"], r["grp"]) for r in rows}) == len(rows)
        total_loss = fsum(r["smp"] * r["k"] * abs(r["p"] - r["y"]) for r in rows)
        slices = defaultdict(list)
        for row in rows:
            slices[("hour", str(row["ts"].hour))].append(row)
            slices[("group", str(row["grp"]))].append(row)
            extra = feature_map.get((row["ts"], row["grp"]))
            if extra is None:
                assert row["p"] == 0.
                slices[("coverage", "all_night")].append(row)
                continue
            slices[("coverage", "daylight")].append(row)
            for field, cuts in (("cosz", (.2, .5, .8)), ("wa_cloud", (20., 50., 80.)), ("wb_cloud", (20., 50., 80.)),
                                ("wa_temp", (0., 10., 20., 30.)), ("capacity_kw", (5000., 10000., 15000., 20000.)),
                                ("extra_wa_snow", (.001, .1, 1.)), ("extra_wb_snow", (.001, .1, 1.)), ("cdis", (10., 30., 50.))):
                value = float(extra[field]) if extra[field] is not None else float("nan")
                slices[(field, bucket(value, cuts))].append(row)
        all_results.extend({"fold": fold, "axis": axis, "bin": label, **summarize(part, total_loss)}
                           for (axis, label), part in sorted(slices.items()))
        for axis in ("hour", "group", "coverage", *FIELDS):
            axis_loss = fsum(r["W"] for r in all_results if r["fold"] == fold and r["axis"] == axis)
            if axis in FIELDS:
                axis_loss += fsum(r["W"] for r in all_results if r["fold"] == fold and r["axis"] == "coverage" and r["bin"] == "all_night")
            assert abs(axis_loss - total_loss) < 1e-5, axis
    with (OUT / "slices.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_results[0]))
        writer.writeheader()
        writer.writerows(all_results)
    manifest = {"status": "PASS", "input_sha256": hashes, "model_fits": 0,
                "limitations": "Descriptive analysis of historically exposed development only; no causal or official-score claim."}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    for record in all_results:
        if record["axis"] in ("wa_temp", "cdis", "extra_wa_snow", "coverage"):
            print(json.dumps(record))


if __name__ == "__main__":
    main()
