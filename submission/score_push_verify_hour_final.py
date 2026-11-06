# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow"]
# ///
# How to run: python submission/score_push_verify_hour_final.py AFTER export terminal.
"""Independently reconstruct the frozen hour stage and submitted CSV/ZIP."""
from __future__ import annotations

import csv
import json
import zipfile
from datetime import datetime, timedelta
from math import isclose
from typing import Final
from zoneinfo import ZoneInfo

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from autoresearch_verify_final import metrics
from score_push_verify import ROOT, digest
from score_push_verify_calibration import ensure_terminal

RENEW: Final = ROOT / "analysis_outputs/renew_20261105"
OUT: Final = RENEW / "hour_final"
CANDIDATE: Final = ROOT / "submission/renew_hour_candidate_20261105"
COEFFICIENT: Final = "7c7702086192c6882f5c2c25408aeaf45aa5d2a70706218eda96d255f038f28e"
COMPOSITION: Final = "68216d1f6b8b6f9c026703e3bfaf7b0470cc8e018580826c866ee0f7357cc141"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    assert read(RENEW / "hour_wave/independent_check.json")["status"] == "PASS"
    assert digest(OUT / "selected_hour_coefficients.json") == COEFFICIENT
    assert digest(RENEW / "hour_wave/coefficients.json") == COEFFICIENT
    factors = [r["factor"] for r in read(OUT / "selected_hour_coefficients.json")["factors"]["hours"]]
    assert len(factors) == 5
    protocol = read(OUT / "protocol.json")
    for name, record in protocol["own_sources"].items():
        assert digest(ROOT / record["original"]) == digest(OUT / "sources/own" / name) == record["sha256"]
    for name, record in protocol["snapshots"].items():
        assert digest(ROOT / record["original"]) == digest(OUT / "sources" / f"{name}.py") == record["sha256"]
    for mapping in (protocol["input_sha256"], protocol["protected_sha256"]):
        for path, expected in mapping.items():
            assert digest(ROOT / path) == expected, path
    for path, expected in read(OUT / "terminal_manifest.json").items():
        assert digest(OUT / path) == expected, path
    freeze = read(OUT / "prediction_freeze.json")
    assert freeze["before_diagnostic_labels"] and freeze["coefficient_sha256"] == COEFFICIENT
    for receipt in read(OUT / "evidence/diagnostic_label_reads.json"):
        assert receipt["prediction_freeze_sha256"] == digest(OUT / "prediction_freeze.json")
        assert datetime.fromisoformat(receipt["label_read_started_utc"]) >= datetime.fromisoformat(freeze["utc"])
    diagnostic = read(OUT / "diagnostic_metrics.json")
    scores, test = {}, {}
    for split in ("old_cutoff_march_may", "latest_cutoff_march_may", "test"):
        source_path = RENEW / "final/predictions" / split / "predictions.parquet"
        previous = {(r["ts"], r["grp"]): r for r in pq.read_table(source_path, columns=["ts", "grp", "p", "static_capacity"]).to_pylist()}
        directory = OUT / "predictions" / split
        assert digest(directory / "predictions.parquet") == freeze["sha256"][split]
        table = pq.read_table(directory / "predictions.parquet")
        assert set(table.column_names) == {"ts", "grp", "p_reference", "static_capacity", "hour_bin", "bounded_hour_factor", "effective_hour_factor", "before_capacity_clip", "p", "capacity_clipped"}
        rows = table.to_pylist()
        assert len(rows) == len(previous) and {(r["ts"], r["grp"]) for r in rows} == set(previous)
        predicted = {}
        for row in rows:
            key = row["ts"], row["grp"]
            base = previous[key]
            hour = row["ts"].astimezone(ZoneInfo("Asia/Seoul")).hour
            index = sum(hour >= boundary for boundary in (10, 12, 14, 16))
            effective = 1 + .5 * (factors[index] - 1)
            before = base["p"] * effective
            expected = min(base["static_capacity"], max(0., before))
            assert row["p_reference"] == base["p"] and row["static_capacity"] == base["static_capacity"]
            assert row["hour_bin"] == index and row["bounded_hour_factor"] == factors[index]
            assert row["effective_hour_factor"] == effective and row["before_capacity_clip"] == before
            assert row["p"] == expected and row["capacity_clipped"] == (before > base["static_capacity"])
            assert 0 <= row["p"] <= base["static_capacity"] and (base["p"] != 0 or row["p"] == 0)
            predicted[key] = row["p"]
        if split == "test":
            test = predicted
            continue
        labels = {(r["ts"], r["grp"]): r for r in pq.read_table(RENEW / "final/predictions" / split / "scored_predictions.parquet", columns=["ts", "grp", "y", "smp", "k"]).to_pylist()}
        scored = pq.read_table(directory / "scored_predictions.parquet").to_pylist()
        assert len(scored) == len(rows) == 4416
        assert {(r["ts"], r["grp"]) for r in scored} == set(labels) == set(previous)
        for row in scored:
            key = row["ts"], row["grp"]
            assert row["p"] == predicted[key] and row["p_reference"] == previous[key]["p"]
            assert all(row[n] == labels[key][n] for n in ("y", "smp", "k"))
        scores[split] = {name: metrics(scored, name) for name in ("p", "p_reference")}
        for column, values in scores[split].items():
            for metric, value in values.items():
                assert isclose(value, diagnostic["scores"][split][column][metric], rel_tol=1e-12, abs_tol=1e-4)
    start = datetime(2025, 6, 1, 1, tzinfo=ZoneInfo("Asia/Seoul"))
    keys = {(start + timedelta(hours=i), group) for i in range(8760) for group in ("G1", "G2")}
    assert set(test) == keys and len(test) == 17520
    with (CANDIDATE / "forecast.csv").open(encoding="utf-8", newline="") as handle:
        exported = list(csv.DictReader(handle))
    actual = {(datetime.fromisoformat(row["ts"]), row["group"]): float(row["forecast_kwh"]) for row in exported}
    assert len(actual) == len(exported) == 17520 and set(actual) == keys
    assert all(value == float(np.round(test[key], 3)) for key, value in actual.items())
    assert [(r["group"], datetime.fromisoformat(r["ts"])) for r in exported] == sorted((g, t) for t, g in keys)
    assert digest(CANDIDATE / "composition.csv") == COMPOSITION
    assert (CANDIDATE / "composition.csv").read_bytes() == (ROOT / "submission/autoresearch_candidate/composition.csv").read_bytes()
    with zipfile.ZipFile(CANDIDATE / "submission_files.zip") as archive:
        assert sorted(archive.namelist()) == ["composition.csv", "forecast.csv"] and archive.testzip() is None
        assert all(archive.read(name) == (CANDIDATE / name).read_bytes() for name in archive.namelist())
    manifest = read(CANDIDATE / "manifest.json")
    assert not manifest["official_score_available"] and manifest["no_reselection"]
    for name, expected in manifest["files_sha256"].items():
        assert digest(CANDIDATE / name) == expected, name
    assert digest(ROOT / "submission/renew_candidate_20261105/submission_files.zip") == "ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434"
    receipt = read(OUT / "export_receipt.json")
    assert receipt["passed"] and receipt["validator_exit_code"] == 0
    assert receipt["scalar_fits"] == receipt["tree_fits"] == 0 and not receipt["uploaded"]
    for name, expected in read(OUT / "candidate_artifact_hashes.json").items():
        assert digest(CANDIDATE / name) == expected, name
    controller = read(OUT / "controller_receipt.json")
    assert controller["exit_code"] == controller["scalar_fits"] == controller["tree_fits"] == 0
    identity = controller["identity"]
    assert identity["priority_class"] == 32 and identity["pyarrow_cpu"] == identity["pyarrow_io"] == 4
    assert all(pool["num_threads"] == 16 for pool in identity["threadpools"])
    ensure_terminal(identity)
    assert not (OUT / "tmp").exists()
    evidence = {"status": "PASS", "rows": len(actual), "formula_exact": True, "zip_exact": True,
                "composition_sha256": COMPOSITION, "zip_sha256": digest(CANDIDATE / "submission_files.zip"),
                "scores": scores, "protected_files": len(protocol["protected_sha256"]),
                "limits": "Descriptive historical comparisons; new official score unknown; original official-best ZIP unchanged."}
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
