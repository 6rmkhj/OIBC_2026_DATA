#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
# How to run: python submission/verify_run.py
"""Recompute exported model scores without importing the training or scoring code."""
from __future__ import annotations

import csv
import hashlib
import json
import struct
from collections import defaultdict
from datetime import datetime
from math import fsum, isclose, isfinite
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parent.parent
OUT: Final = ROOT / "analysis_outputs" / "award_run"
CANDIDATE: Final = ROOT / "submission" / "award_candidate"


def observed_value(value: str) -> float:
    # CSV stores shortest float32 strings; restore the recorded target dtype.
    return struct.unpack("f", struct.pack("f", float(value)))[0]


def main() -> None:
    with (OUT / "outer_predictions.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 17520
    assert len({(row["group"], row["ts"]) for row in rows}) == 17520
    assert {row["group"] for row in rows} == {"G1", "G2"}
    with (OUT / "outer_metrics.json").open(encoding="utf-8") as stream:
        recorded = json.load(stream)
    with (OUT / "locked_configuration.json").open(encoding="utf-8") as stream:
        locked = json.load(stream)
    with (OUT / "inner_selection.csv").open(newline="", encoding="utf-8") as stream:
        selected = min(csv.DictReader(stream), key=lambda row: float(row["W"]))
    assert locked["composition"] == selected["composition"]
    assert locked["direct_weight"] == float(selected["direct_weight"])
    with (OUT / "boundaries.json").open(encoding="utf-8") as stream:
        boundaries = json.load(stream)
    assert datetime.fromisoformat(boundaries["inner_train"]["end"]) < datetime.fromisoformat(boundaries["inner_selection"]["start"])
    assert datetime.fromisoformat(boundaries["inner_selection"]["end"]) < datetime.fromisoformat(boundaries["outer_validation"]["start"])
    assert datetime.fromisoformat(boundaries["outer_train"]["end"]) < datetime.fromisoformat(boundaries["outer_validation"]["start"])

    weights = [float(row["smp"]) * float(row["k"]) for row in rows]
    assert all(isfinite(w) and w >= 0 for w in weights)
    assert all(int(float(row["k"])) == (3 if 11 <= datetime.fromisoformat(row["ts"]).hour <= 15 else 1) for row in rows)
    independently_computed = {}
    for prediction, target in (("p_candidate", "y"), ("p_selected50", "y"),
                               ("p_reference50", "y_reference"), ("p_original50", "y_original")):
        values = [float(row[prediction]) for row in rows]
        actuals = [observed_value(row[target]) for row in rows]
        assert all(isfinite(p) and p >= 0 for p in values)
        penalty = fsum(w * abs(p - y) for w, p, y in zip(weights, values, actuals, strict=True))
        revenue = fsum(float(row["smp"]) * y for row, y in zip(rows, actuals, strict=True))
        denominator = fsum(w * y for w, y in zip(weights, actuals, strict=True))
        result = {"W": penalty, "W_pct": 100 * penalty / denominator,
                  "revenue": revenue, "S": revenue - 0.1 * penalty}
        for key, value in result.items():
            assert isclose(value, recorded[prediction][key], rel_tol=1e-12, abs_tol=0.001), (prediction, key)
        independently_computed[prediction] = result

    totals = defaultdict(lambda: [0.0, 0.0, 0.0])
    for row in rows:
        for i, target in enumerate(("y", "y_reference", "y_original")):
            totals[row["ts"]][i] += observed_value(row[target])
    # Separate float32 group sums can differ by a few milliwatt-hours.
    assert all(isclose(a, b, rel_tol=1e-12, abs_tol=0.01) and isclose(a, c, rel_tol=1e-12, abs_tol=0.01)
               for a, b, c in totals.values()), "Different compositions must retain the same fleet actuals"
    with (CANDIDATE / "manifest.json").open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    for name, expected in manifest["files_sha256"].items():
        with (CANDIDATE / name).open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == expected, name
    with (OUT / "provenance.json").open(encoding="utf-8") as stream:
        provenance = json.load(stream)
    for name, expected in provenance["inputs_sha256"].items():
        path = ROOT / name if "/" in name or "\\" in name else ROOT / "submission" / name
        with path.open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == expected, name
    complete_rows = [row for row in rows if datetime.fromisoformat("2025-01-01T00:00:00+09:00")
                     < datetime.fromisoformat(row["ts"]) <= datetime.fromisoformat("2025-06-01T00:00:00+09:00")]
    assert len(complete_rows) == 7248
    complete_metrics = {}
    for prediction, target in (("p_candidate", "y"), ("p_reference50", "y_reference")):
        penalty = fsum(float(row["smp"]) * float(row["k"]) *
                       abs(float(row[prediction]) - observed_value(row[target])) for row in complete_rows)
        denominator = fsum(float(row["smp"]) * float(row["k"]) * observed_value(row[target]) for row in complete_rows)
        complete_metrics[prediction] = {"W": penalty, "W_pct": 100 * penalty / denominator}
    print(json.dumps({"status": "PASS", "independent_math": "stdlib math.fsum; no model imports",
                      "rows": len(rows), "hours": len(totals), "selection_minimum_matches": True,
                      "chronological_boundaries": "PASS", "composition_targets": "PASS",
                      "max_fleet_rounding_kwh": max(max(v) - min(v) for v in totals.values()),
                      "complete_fleet_rows": len(complete_rows), "complete_fleet_metrics": complete_metrics,
                      "input_and_output_hashes": "PASS", "metrics": independently_computed}, indent=2))


if __name__ == "__main__":
    main()
