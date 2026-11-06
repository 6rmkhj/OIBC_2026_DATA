# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow"]
# ///
# Run: python submission/autoresearch_verify_final.py
"""Independently recompute final comparison from raw exported predictions."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timedelta, timezone
from math import fsum, isclose, isfinite
from pathlib import Path
from typing import Final, Literal, TypedDict
from zipfile import ZipFile

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

ROOT: Final = Path(__file__).resolve().parent.parent
OUT: Final = ROOT / "analysis_outputs/autoresearch_20261103/final"
CANDIDATE: Final = ROOT / "submission/autoresearch_candidate"
KST: Final = timezone(timedelta(hours=9))
HOUR: Final = timedelta(hours=1)


class Row(TypedDict):
    ts: datetime
    grp: str
    y: float
    p_bu: float
    p_previous: float
    p_candidate: float
    smp: float
    k: float


class Metric(TypedDict):
    W: float
    W_pct: float
    revenue: float
    S: float
    rows: int


def metrics(rows: list[Row], prediction: Literal["p_previous", "p_candidate"]) -> Metric:
    penalty = fsum(row["smp"] * row["k"] * abs(row[prediction] - row["y"]) for row in rows)
    denominator = fsum(row["smp"] * row["k"] * row["y"] for row in rows)
    revenue = fsum(row["smp"] * row["y"] for row in rows)
    return {"W": penalty, "W_pct": 100 * penalty / denominator,
            "revenue": revenue, "S": revenue - .1 * penalty, "rows": len(rows)}


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    rows: list[Row] = pq.read_table(OUT / "outer_predictions.parquet").to_pylist()
    start = datetime(2024, 6, 1, tzinfo=KST)
    end = datetime(2025, 6, 1, tzinfo=KST)
    jan = datetime(2025, 1, 1, tzinfo=KST)
    expected = {(start + i * HOUR, group) for i in range(1, 8761) for group in ("G1", "G2")}
    assert len(rows) == 17520 and {(row["ts"], row["grp"]) for row in rows} == expected
    for row in rows:
        assert row["k"] == (3 if 11 <= row["ts"].hour <= 15 else 1)
        assert all(isfinite(row[name]) and row[name] >= 0
                   for name in ("y", "p_bu", "p_previous", "p_candidate", "smp", "k"))
    subsets = {"all": rows, "2025_Jan_May": [row for row in rows if jan < row["ts"] <= end],
               "k11_15": [row for row in rows if row["k"] == 3]}
    assert len(subsets["2025_Jan_May"]) == 7248
    for row in rows:
        subsets.setdefault((row["ts"] - HOUR).strftime("%Y-%m"), []).append(row)
    assert len(subsets) == 15
    computed = {(name, prediction): metrics(subset, prediction)
                for name, subset in subsets.items() for prediction in ("p_previous", "p_candidate")}
    with (OUT / "outer_metrics.json").open(encoding="utf-8") as stream:
        reported = json.load(stream)
    for prediction, result in reported.items():
        for metric, value in computed["all", prediction].items():
            assert isclose(value, result[metric], rel_tol=1e-11, abs_tol=1e-5), (prediction, metric)
    assert set(reported) == {"p_previous", "p_candidate"}
    assert isclose(computed["all", "p_previous"]["W_pct"], 11.552586472040375, abs_tol=1e-7)
    assert isclose(computed["2025_Jan_May", "p_previous"]["W_pct"], 10.223466677873294, abs_tol=1e-7)
    with (OUT / "diagnostics.csv").open(encoding="utf-8", newline="") as stream:
        diagnostics = list(csv.DictReader(stream))
    assert len(diagnostics) == len(computed)
    assert {(item["subset"], item["recipe"]) for item in diagnostics} == set(computed)
    for item in diagnostics:
        for metric, value in computed[item["subset"], item["recipe"]].items():
            assert isclose(value, float(item[metric]), rel_tol=1e-11, abs_tol=1e-5), (item, metric)
    with (OUT / "bootstrap.json").open(encoding="utf-8") as stream:
        intervals = json.load(stream)
    assert set(intervals) == {"all", "2025_Jan_May"}
    for name, result in intervals.items():
        daily = {}
        for row in subsets[name]:
            key = (row["ts"] - HOUR).date()
            weight = row["smp"] * row["k"]
            delta = weight * (abs(row["p_candidate"] - row["y"]) - abs(row["p_previous"] - row["y"]))
            daily.setdefault(key, []).append((delta, weight * row["y"]))
        sums = np.array([(fsum(x[0] for x in daily[day]), fsum(x[1] for x in daily[day]))
                         for day in sorted(daily)])
        assert len(sums) == result["blocks"]
        assert result["replicates"] == 2000
        indices = np.random.default_rng(result["seed"]).integers(0, len(sums),
                    size=(result["replicates"], len(sums)))
        sampled = sums[indices].sum(axis=1)
        for key, values in (("W_delta_95CI", sampled[:, 0]),
                            ("W_pct_delta_95CI", 100 * sampled[:, 0] / sampled[:, 1])):
            assert np.allclose(np.quantile(values, [.025, .975]), result[key], rtol=1e-10, atol=1e-5), key
    for directory in (CANDIDATE, ROOT / "submission/award_candidate"):
        with (directory / "manifest.json").open(encoding="utf-8") as stream:
            manifest = json.load(stream)
        for name, expected_hash in manifest["files_sha256"].items():
            assert digest(directory / name) == expected_hash, (directory, name)
    with ZipFile(CANDIDATE / "submission_files.zip") as archive:
        assert sorted(archive.namelist()) == ["composition.csv", "forecast.csv"]
        for name in archive.namelist():
            assert archive.read(name) == (CANDIDATE / name).read_bytes(), name
    print(json.dumps({"status": "PASS", "method": "raw Parquet, stdlib fsum, independent day bootstrap",
        "outer_rows": len(rows), "complete_fleet_rows": len(subsets["2025_Jan_May"]),
        "diagnostic_rows": len(diagnostics), "bootstrap": intervals,
        "artifact_hashes_and_zip": "PASS", "previous_candidate_hashes": "PASS",
        "metrics": [{"subset": name, "recipe": prediction, **value}
                    for (name, prediction), value in computed.items()]}, indent=2))


if __name__ == "__main__":
    main()
