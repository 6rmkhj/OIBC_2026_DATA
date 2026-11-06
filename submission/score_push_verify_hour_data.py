# /// script
# requires-python = ">=3.12"
# dependencies = ["pyarrow"]
# ///
# How to run: python submission/score_push_verify_hour_data.py BEFORE real hour fits.
"""Check that hour calibration receives only the canonical development predictions."""
from __future__ import annotations

import json
from datetime import datetime
from math import isfinite
from typing import Final
from zoneinfo import ZoneInfo

import pyarrow as pa
import pyarrow.parquet as pq

from score_push_verify import ROOT, digest

OUT: Final = ROOT / "analysis_outputs/renew_20261105/hour_wave"
KST: Final = ZoneInfo("Asia/Seoul")


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = json.loads((OUT / "protocol.json").read_text())
    for path, expected in protocol["input_sha256"].items():
        assert digest(ROOT / path) == expected, path
    for path, expected in json.loads((OUT / "prepared_manifest.json").read_text()).items():
        assert digest(OUT / path) == expected, path
    capacities = json.loads((OUT / "static_capacity.json").read_text())
    checked = []
    for fold, dates in {"primary": ("2023-06-01", "2024-06-01"), "recent": ("2024-06-01", "2025-03-01")}.items():
        start, end = [datetime.fromisoformat(d).replace(tzinfo=KST) for d in dates]
        directory = OUT / "data" / fold
        table = pq.read_table(directory / "rows.parquet")
        assert set(table.column_names) == {"ts", "grp", "y", "smp", "k", "p_reference", "night", "static_capacity"}
        rows = table.to_pylist()
        previous = pq.read_table(OUT.parent / "calibration_wave/comparisons/temperature_then_snow" / fold / "predictions.parquet", columns=["ts", "grp", "y", "smp", "k", "p"]).to_pylist()
        reference = {(r["ts"], r["grp"]): r for r in previous}
        night = {(r["ts"], r["grp"]): r["night"] for r in pq.read_table(OUT.parent / "recency_wave/data" / fold / "night_coverage.parquet").to_pylist()}
        assert len(rows) == len(reference) and {(r["ts"], r["grp"]) for r in rows} == set(reference) == set(night)
        inputs = pq.read_table(directory / "apply_inputs.parquet")
        assert set(inputs.column_names) == {"ts", "grp", "p_reference", "static_capacity"}
        assert inputs.to_pylist() == table.select(inputs.column_names).to_pylist()
        for row in rows:
            key = row["ts"], row["grp"]
            source = reference[key]
            assert row["ts"].tzinfo is not None and start < row["ts"] <= end
            assert all(row[n] == source[n] for n in ("y", "smp", "k")) and row["p_reference"] == source["p"]
            assert all(isfinite(row[n]) and row[n] >= 0 for n in ("y", "smp", "p_reference"))
            assert row["night"] == night[key] and row["static_capacity"] == capacities[row["grp"]]
            assert 0 <= row["p_reference"] <= row["static_capacity"]
            assert not row["night"] or row["p_reference"] == 0
        checked.append({"fold": fold, "rows": len(rows), "pure_application_columns": inputs.column_names})
    assert not (OUT / "coefficients.json").exists()
    evidence = {"status": "PASS", "records": checked, "protocol_sha256": digest(OUT / "protocol.json"),
                "prepared_manifest_sha256": digest(OUT / "prepared_manifest.json"),
                "scope": "Canonical calibrated reference and bounded original labels/night flags, exact static capacities, strictly label-free apply projection. No real calibration fit."}
    (OUT / "independent_data_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
