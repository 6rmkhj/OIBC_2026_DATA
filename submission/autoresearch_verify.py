#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyarrow"]
# ///
# How to run: python submission/autoresearch_verify.py
"""Independently check the autoresearch journal, frozen inputs and selection scores."""
from __future__ import annotations

import csv
import hashlib
import json
from math import fsum, isclose, isfinite
from pathlib import Path
from typing import Final

import pyarrow as pa
import pyarrow.parquet as pq

ROOT: Final = Path(__file__).resolve().parent.parent
OUT: Final = ROOT / "analysis_outputs" / "autoresearch_20261103"
CACHE: Final = OUT / "cache"
SOURCE: Final = ROOT / "submission" / "autoresearch"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    with (CACHE / "manifest.json").open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    for name, expected in manifest["cache_sha256"].items():
        assert digest(CACHE / name) == expected, name
    for name, expected in manifest["fixed_sources"].items():
        assert digest(SOURCE / name) == expected, name
    assert manifest["threads_per_trial"] == 2 and manifest["parallel_trials"] == 2
    with (OUT / "resource_policy.json").open(encoding="utf-8") as stream:
        resource_policy = json.load(stream)
    assert resource_policy["max_concurrent_trials"] == 1
    assert resource_policy["threads_per_trial"] == 2 and resource_policy["blas_threads"] == 1
    labels = pq.read_table(CACHE / "selection_labels.parquet").to_pylist()
    keys = {(row["ts"], row["grp"]) for row in labels}
    assert len(keys) == len(labels) == 17568
    denominator = fsum(float(row["smp"]) * float(row["k"]) * float(row["y"]) for row in labels)
    assert denominator > 0
    with (OUT / "results.tsv").open(newline="", encoding="utf-8") as stream:
        ledger = list(csv.DictReader(stream, delimiter="\t"))
    successful = []
    failures = []
    for record in ledger:
        if int(record["exit_code"]) != 0:
            failures.append(record["id"])
            continue
        trial = OUT / "trials" / record["id"]
        assert digest(trial / "train.py") == record["source_sha256"]
        assert digest(trial / "config.json") == record["config_sha256"]
        with (trial / "config.json").open(encoding="utf-8") as stream:
            configuration = json.load(stream)
        if configuration.get("spatial", False):
            spatial_path = OUT / "spatial" / "manifest.json"
            assert digest(spatial_path) == configuration["spatial_manifest_sha256"]
            with spatial_path.open(encoding="utf-8") as stream:
                spatial = json.load(stream)
            assert digest(CACHE / "assignment.json") == spatial["assignment_sha256"]
            assert digest(ROOT / "submission" / "autoresearch_spatial.py") == spatial["builder_sha256"]
            for output in spatial["outputs"].values():
                assert digest(ROOT / output["path"]) == output["sha256"]
        direct_weight = float(configuration["direct_weight"])
        assert 0 <= direct_weight <= 1
        predictions = pq.read_table(trial / "predictions.parquet").to_pylist()
        direct = {(row["ts"], row["grp"]): float(row["p_dir"]) for row in predictions}
        assert len(direct) == len(predictions) == len(keys) and set(direct) == keys
        assert all(isfinite(value) and value >= 0 for value in direct.values())
        weighted_error = fsum(
            float(row["smp"]) * float(row["k"]) * abs(
                (1 - direct_weight) * float(row["p_bu"])
                + direct_weight * direct[(row["ts"], row["grp"])] - float(row["y"])
            ) for row in labels
        )
        percentage = 100 * weighted_error / denominator
        assert isclose(weighted_error, float(record["W"]), rel_tol=1e-12, abs_tol=0.001), record["id"]
        assert isclose(percentage, float(record["W_pct"]), rel_tol=1e-12), record["id"]
        successful.append({"id": record["id"], "W": weighted_error, "W_pct": percentage})
    assert successful
    with (OUT / "best.json").open(encoding="utf-8") as stream:
        best = json.load(stream)
    independent_best = min(successful, key=lambda result: result["W"])
    assert isclose(independent_best["W"], best["W"], rel_tol=1e-12)
    print(json.dumps({"status": "PASS", "method": "PyArrow plus stdlib math.fsum, no training/evaluator imports",
                      "successful_trials": len(successful), "failed_trial_ids": failures,
                      "fixed_sources_and_cache": "PASS", "all_scores_and_trial_snapshots": "PASS",
                      "selection_rows": len(labels), "threads_per_trial": 2,
                      "historical_prepared_parallel_trials": manifest["parallel_trials"],
                      "current_max_concurrent_trials": resource_policy["max_concurrent_trials"],
                      "best": independent_best, "scores": successful}, indent=2))


if __name__ == "__main__":
    main()
