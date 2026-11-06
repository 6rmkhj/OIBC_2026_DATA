# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow"]
# ///
# Run only AFTER recipe freeze and final export: python submission/score_push_verify_final.py
"""Independent final scoring, paired day bootstrap and submission checks."""
from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from math import fsum, isclose, isfinite
from typing import Final
from zipfile import ZipFile

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from autoresearch_verify_final import metrics
from score_push_verify import OLD, OUT, ROOT, digest

FINAL: Final = OUT / "final"
CANDIDATE: Final = ROOT / "submission/score_push_candidate"
KST: Final = timezone(timedelta(hours=9))
HOUR: Final = timedelta(hours=1)


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    assert (FINAL / "freeze.json").is_file(), "Do not open confirmation before recipe freeze"
    freeze = json.loads((FINAL / "freeze.json").read_text())
    frozen_recent = freeze["development_recent_prediction"]
    frozen_path = (ROOT / frozen_recent["path"]).resolve()
    assert frozen_path.is_relative_to(ROOT) and digest(frozen_path) == frozen_recent["sha256"]
    previous_development = pq.read_table(frozen_path).to_pylist()
    frozen_values = {(r["ts"], r["grp"]): r[frozen_recent["column"]] for r in previous_development}
    rows = pq.read_table(FINAL / "outer_predictions.parquet").to_pylist()
    incumbent = pq.read_table(OLD / "final/outer_predictions.parquet").to_pylist()
    oracle = {(r["ts"], r["grp"]): r for r in incumbent}
    start = datetime(2024, 6, 1, tzinfo=KST)
    end = datetime(2025, 6, 1, tzinfo=KST)
    march = datetime(2025, 3, 1, tzinfo=KST)
    january = datetime(2025, 1, 1, tzinfo=KST)
    expected = {(start + i * HOUR, g) for i in range(1, 8761) for g in ("G1", "G2")}
    assert len(rows) == len(incumbent) == len(oracle) == 17520
    assert {(r["ts"], r["grp"]) for r in rows} == set(oracle) == expected
    for row in rows:
        old = oracle[row["ts"], row["grp"]]
        assert all(row[k] == old[k] for k in ("y", "smp", "k", "site_count"))
        assert row["p_previous"] == old["p_candidate"]
        assert row["k"] == (3 if 11 <= row["ts"].hour <= 15 else 1)
        assert all(isfinite(row[k]) and row[k] >= 0 for k in ("p_previous", "p_candidate", "y", "smp", "k"))
    subsets = {"all": rows, "recent_development": [r for r in rows if r["ts"] <= march],
        "confirmation": [r for r in rows if march < r["ts"] <= end],
        "2025_Jan_May": [r for r in rows if january < r["ts"] <= end],
        "k11_15": [r for r in rows if r["k"] == 3]}
    assert len(subsets["recent_development"]) == 13104
    assert len(previous_development) == len(frozen_values) == 13104
    assert {(r["ts"], r["grp"]) for r in subsets["recent_development"]} == set(frozen_values)
    assert all(isclose(r["p_candidate"], frozen_values[r["ts"], r["grp"]], rel_tol=1e-10, abs_tol=1e-6)
               for r in subsets["recent_development"])
    assert len(subsets["confirmation"]) == 4416
    assert len(subsets["2025_Jan_May"]) == 7248
    for row in rows:
        subsets.setdefault((row["ts"] - HOUR).strftime("%Y-%m"), []).append(row)
    computed = {name: {p: metrics(group, p) for p in ("p_previous", "p_candidate")}
                for name, group in subsets.items()}
    assert isclose(computed["all"]["p_previous"]["W_pct"], 11.04884280137099, abs_tol=1e-8)
    assert isclose(computed["2025_Jan_May"]["p_previous"]["W_pct"], 9.663307434927248, abs_tol=1e-8)
    intervals = {}
    for name in ("all", "confirmation", "2025_Jan_May"):
        daily = {}
        for row in subsets[name]:
            key = (row["ts"] - HOUR).date()
            weight = row["smp"] * row["k"]
            delta = weight * (abs(row["p_candidate"] - row["y"]) - abs(row["p_previous"] - row["y"]))
            daily.setdefault(key, []).append((delta, weight * row["y"]))
        values = np.array([(fsum(x[0] for x in daily[d]), fsum(x[1] for x in daily[d])) for d in sorted(daily)])
        indices = np.random.default_rng(20261104).integers(0, len(values), size=(2000, len(values)))
        sampled = values[indices].sum(axis=1)
        intervals[name] = {"blocks": len(values), "replicates": 2000, "seed": 20261104,
            "W_delta_95CI": np.quantile(sampled[:, 0], [.025, .975]).tolist(),
            "W_pct_delta_95CI": np.quantile(100 * sampled[:, 0] / sampled[:, 1], [.025, .975]).tolist()}
    test_rows = pq.read_table(FINAL / "test_predictions.parquet").to_pylist()
    test_values = {(r["ts"], r["grp"]): r["p_candidate"] for r in test_rows}
    expected_test = {(end + i * HOUR, g) for i in range(1, 8761) for g in ("G1", "G2")}
    assert len(test_rows) == len(test_values) == 17520 and set(test_values) == expected_test
    assert all(isfinite(value) and value >= 0 for value in test_values.values())
    with (CANDIDATE / "forecast.csv").open(encoding="utf-8", newline="") as stream:
        exported = list(csv.DictReader(stream))
    actual = {(datetime.fromisoformat(r["ts"]), r["group"]): float(r["forecast_kwh"]) for r in exported}
    assert len(exported) == len(actual) == 17520 and set(actual) == set(test_values)
    assert all(isfinite(value) and value >= 0 and isclose(value, float(np.round(test_values[key], 3)), abs_tol=1e-9)
               for key, value in actual.items())
    assert (CANDIDATE / "composition.csv").read_bytes() == (ROOT / "submission/autoresearch_candidate/composition.csv").read_bytes()
    for folder in (CANDIDATE, ROOT / "submission/award_candidate", ROOT / "submission/autoresearch_candidate"):
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        for name, expected_hash in manifest["files_sha256"].items():
            assert digest(folder / name) == expected_hash, name
    for name, expected_hash in freeze["preserved_before_sha256"].items():
        assert digest(ROOT / name) == expected_hash, name
    with ZipFile(CANDIDATE / "submission_files.zip") as archive:
        assert sorted(archive.namelist()) == ["composition.csv", "forecast.csv"]
        assert all(archive.read(name) == (CANDIDATE / name).read_bytes() for name in archive.namelist())
    result = {"status": "PASS", "method": "Raw Parquet, stdlib math.fsum, independent daily paired bootstrap",
        "incumbent_predictions_and_labels_exact": True, "confirmation_rows": 4416,
        "export_rows": 17520, "composition_matches_confirmed_submission": True,
        "metrics": computed, "bootstrap": intervals,
        "limitations": ["Both development periods informed selection; all historical periods had prior exposure.",
                       "Official leaderboard score of this new artifact remains unmeasured."]}
    output = FINAL / "independent_check.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(output),
        "all": computed["all"], "confirmation": computed["confirmation"]}, indent=2))


if __name__ == "__main__":
    main()
