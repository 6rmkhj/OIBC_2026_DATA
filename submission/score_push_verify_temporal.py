# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow"]
# ///
# How to run: python submission/score_push_verify_temporal.py
"""Independently verify temporal weights, selection and saved trial evidence."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from math import fsum, isclose, isfinite
from typing import Final

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from autoresearch_verify_final import metrics
from score_push_verify import ROOT, digest

OUT: Final = ROOT / "analysis_outputs/renew_20261105/recency_wave"
DATA: Final = ROOT / "analysis_outputs/score_push_gpu_20261104/data"
CPU: Final = ROOT / "analysis_outputs/score_push_20261104"
BASE: Final = {"primary": 12.041603595410752, "recent": 11.064366712650248}
DECAY: Final = {"decay180": 180, "decay365": 365, "decay730": 730, "window365": 0}
KST: Final = timezone(timedelta(hours=9))


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = json.loads((OUT / "protocol.json").read_text(encoding="utf-8"))
    results = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
    controller = json.loads((OUT / "controller_receipt.json").read_text(encoding="utf-8"))
    assert controller["exit_code"] == 0
    assert results["model_fit_count"] == 24
    assert not results["confirmation_loaded"] and not results["test_loaded"]
    for path, expected in protocol["protected_sha256"].items():
        assert digest(ROOT / path) == expected, path
    for path, expected in protocol["input_sha256"].items():
        assert digest(ROOT / path) == expected, path
    for name, record in protocol["own_sources"].items():
        assert digest(OUT / "sources/own" / name) == record["sha256"]
    amendment = json.loads((OUT / "source_amendment.json").read_text())
    assert amendment["original_protocol_sha256"] == digest(OUT / "protocol.json")
    active_sources = {**protocol["own_sources"], **amendment["own_sources"]}
    for name, record in active_sources.items():
        assert digest(ROOT / record["original"]) == record["sha256"]
        assert digest(OUT / record.get("snapshot", f"sources/own/{name}")) == record["sha256"]
    assert "temporal_fit.py" not in amendment["own_sources"] and "temporal_score.py" not in amendment["own_sources"]
    for path, expected in json.loads((OUT / "artifact_hashes.json").read_text()).items():
        assert digest(OUT / path) == expected, path
    checked_weights = []
    assignment = json.loads((ROOT / protocol["assignment_source"]).read_text())
    for fold in BASE:
        cutoff = datetime(2023 if fold == "primary" else 2024, 6, 1, tzinfo=KST)
        end = datetime(2024, 6, 1, tzinfo=KST) if fold == "primary" else datetime(2025, 3, 1, tzinfo=KST)
        coverage = {}
        site_flags = pq.read_table(ROOT / protocol["night_source"], columns=["site_id", "ts", "night"], filters=[("ts", ">", cutoff), ("ts", "<=", end)])
        for batch in site_flags.to_batches(max_chunksize=65536):
            for row in batch.to_pylist():
                key = row["ts"], assignment[row["site_id"]]
                coverage[key] = coverage.get(key, True) and row["night"]
        saved_night = pq.read_table(OUT / "data" / fold / "night_coverage.parquet").to_pylist()
        assert len(saved_night) == len(coverage)
        assert {(r["ts"], r["grp"]): r["night"] for r in saved_night} == coverage
        day_rows = pq.read_table(DATA / fold / "evaluation.parquet", columns=["ts", "grp"]).to_pylist()
        assert {(r["ts"], r["grp"]) for r in day_rows} == {key for key, night in coverage.items() if not night}
        feature_info = json.loads((DATA / fold / "features.json").read_text())
        source = pq.read_table(DATA / fold / "train.parquet")
        times = source["ts"].to_pylist()
        groups = source["grp"].to_pylist()
        assert all(ts <= cutoff for ts in times)
        for variant, half_life in DECAY.items():
            keep = np.array([ts > cutoff - timedelta(days=365) for ts in times]) if variant == "window365" else np.ones(len(times), dtype=bool)
            retained = source.filter(pa.array(keep))
            keys = [(ts, grp) for ts, grp, present in zip(times, groups, keep, strict=True) if present]
            age = np.array([(cutoff - ts).total_seconds() / 86400 for ts, _ in keys])
            cosz = np.maximum(retained["cosz"].to_numpy(), 0.)
            exponent = np.divide(-.059, cosz, out=np.zeros(len(cosz)), where=cosz > 0)
            normalizer = np.maximum(1.098 * cosz * np.exp(exponent), .05)
            decay = np.exp2(-age / half_life) if half_life else np.ones(len(age))
            decay /= fsum(decay) / len(decay)
            weights = pq.read_table(OUT / "data" / variant / fold / "training_weights.parquet").to_pylist()
            assert [(r["ts"], r["grp"]) for r in weights] == keys
            for index, row in enumerate(weights):
                expected = {"normalizer": normalizer[index], "age_days": age[index], "recency_multiplier": decay[index], "sample_weight": normalizer[index] * decay[index]}
                assert all(isfinite(row[name]) and isclose(row[name], value, rel_tol=1e-12, abs_tol=1e-12) for name, value in expected.items())
                assert row["sample_weight"] > 0 and row["age_days"] >= 0
            selected = []
            for name in feature_info["station"]:
                values = retained[name].to_numpy()
                if len(np.unique(values[~np.isnan(values)])) > 1:
                    selected.append(name)
            assert selected and not {"y", "cf", "energy", "smp", "k"} & set(selected)
            for seed in range(3):
                trial = OUT / "trials" / variant / fold / f"seed{seed}"
                config = json.loads((trial / "config.json").read_text())
                assert config["features"] == selected and config["training_rows"] == len(keys)
                assert config["parameters"]["n_jobs"] == 16
                assert config["parameters"]["random_state"] == (None if seed == 0 else seed)
                assert config["parameters"]["n_estimators"] == 400 and config["parameters"]["num_leaves"] == 63
                assert config["weights_sha256"] == digest(OUT / "data" / variant / fold / "training_weights.parquet")
            checked_weights.append({"variant": variant, "fold": fold, "rows": len(keys), "features": len(selected), "minimum_weight": min(r["sample_weight"] for r in weights)})
    records = results["records"]
    assert len(records) == 4 and {r["variant"] for r in records} == set(DECAY)
    checked_scores = []
    for record in records:
        assert record["stage"] == "ensemble" and record["seeds"] == [0, 1, 2]
        alpha = record["alpha_primary_only"]
        assert isfinite(alpha) and 0 <= alpha <= 1
        paired = {}
        for fold in BASE:
            original = pq.read_table(DATA / fold / "labels.parquet").to_pylist()
            oracle = {(r["ts"], r["grp"]): r for r in original}
            cpu = pq.read_table(CPU / "closing_wave" / fold / "selected/predictions.parquet", columns=["ts", "grp", "p"]).to_pylist()
            cpu_values = {(r["ts"], r["grp"]): r["p"] for r in cpu}
            assert set(oracle) == set(cpu_values) and len(oracle) == (17568 if fold == "primary" else 13104)
            daylight = pq.read_table(DATA / fold / "evaluation.parquet", columns=["ts", "grp"]).to_pylist()
            daylight_keys = {(r["ts"], r["grp"]) for r in daylight}
            members = []
            for seed in range(3):
                raw = pq.read_table(OUT / "trials" / record["variant"] / fold / f"seed{seed}/daylight_raw.parquet").to_pylist()
                values = {(r["ts"], r["grp"]): r["p_raw"] for r in raw}
                assert len(raw) == len(values) and set(values) == daylight_keys
                assert all(isfinite(v) for v in values.values())
                members.append(values)
            rows = pq.read_table(OUT / "comparisons" / record["variant"] / "ensemble" / fold / "predictions.parquet").to_pylist()
            assert len(rows) == len(oracle) and {(r["ts"], r["grp"]) for r in rows} == set(oracle)
            for row in rows:
                key = row["ts"], row["grp"]
                assert all(row[name] == oracle[key][name] for name in ("y", "smp", "k", "p_incumbent"))
                assert row["p_reference"] == cpu_values[key] == oracle[key]["p_reference"]
                assert row["alpha"] == alpha and row["k"] == (3 if 11 <= row["ts"].hour <= 15 else 1)
                pure = max(0., fsum(member[key] for member in members) / 3) if key in daylight_keys else 0.
                assert isclose(row["p_new"], pure, rel_tol=1e-12, abs_tol=1e-7)
                assert isclose(row["p"], (1 - alpha) * row["p_reference"] + alpha * pure, rel_tol=1e-12, abs_tol=1e-7)
                assert all(isfinite(row[name]) and row[name] >= 0 for name in ("y", "smp", "p", "p_reference", "p_new"))
            computed = {arm: metrics(rows, arm) for arm in ("p", "p_reference", "p_new", "p_incumbent")}
            for arm, values in computed.items():
                for name, value in values.items():
                    assert isclose(value, record["scores"][fold][arm][name], rel_tol=1e-12, abs_tol=1e-5)
            assert isclose(computed["p_reference"]["W_pct"], BASE[fold], abs_tol=1e-10)
            paired[fold] = computed
            if fold == "primary":
                ratios = sorted(((r["y"] - r["p_reference"]) / (r["p_new"] - r["p_reference"]), r["smp"] * r["k"] * abs(r["p_new"] - r["p_reference"])) for r in rows if r["p_new"] != r["p_reference"])
                half = fsum(weight for _, weight in ratios) / 2
                cumulative, optimum = 0., 0.
                for ratio, weight in ratios:
                    cumulative += weight
                    if cumulative >= half:
                        optimum = min(1., max(0., ratio))
                        break
                loss = fsum(r["smp"] * r["k"] * abs(r["y"] - ((1 - optimum) * r["p_reference"] + optimum * r["p_new"])) for r in rows)
                assert isclose(loss, computed["p"]["W"], rel_tol=1e-12, abs_tol=1e-4)
        both = all(paired[fold]["p"]["W_pct"] < BASE[fold] for fold in BASE)
        assert record["both_folds_improve"] == both and record["eligible"] == (both and alpha >= .02)
        mean_relative = fsum(paired[fold]["p"]["W_pct"] / BASE[fold] for fold in BASE) / 2
        assert isclose(mean_relative, record["mean_relative_W"], rel_tol=1e-12)
        checked_scores.append({"variant": record["variant"], "alpha": alpha, "scores": paired, "eligible": record["eligible"]})
    eligible = [r for r in records if r["eligible"]]
    selected = min(eligible, key=lambda r: r["mean_relative_W"]) if eligible else None
    assert results["selected"] == selected and results["cpu_reference_retained"] == (selected is None)
    intervals = []
    trials = sorted((OUT / "trials").glob("*/*/seed*"))
    assert len(trials) == 24
    for trial in trials:
        runtime = json.loads((trial / "runtime.json").read_text())
        replay = json.loads((trial / "replay.json").read_text())
        receipt = json.loads((trial / "controller_receipt.json").read_text())
        assert runtime["model_thread_count"] == 16 and runtime["priority_class"] == 32
        assert runtime["parallel_fits"] == 1 and runtime["pyarrow_cpu"] == 4
        assert all(pool["num_threads"] == 16 for pool in runtime["threadpools"])
        assert receipt["exit_code"] == 0 and replay["passed"] and replay["max_absolute_error"] == 0
        assert digest(trial / "model.txt") == replay["model_sha256"]
        assert digest(trial / "daylight_raw.parquet") == replay["raw_sha256"]
        assert receipt["exact_worker_absent"]
        intervals.append((datetime.fromisoformat(receipt["started_utc"]), datetime.fromisoformat(receipt["finished_utc"])))
    intervals.sort()
    assert all(start < end for start, end in intervals)
    assert all(left[1] <= right[0] for left, right in zip(intervals, intervals[1:]))
    evidence = {"status": "PASS", "weights": checked_weights, "records": checked_scores, "selected": selected, "models": len(trials), "serial_intervals": len(intervals), "protected_files": len(protocol["protected_sha256"]), "limitations": "Adaptive historically exposed development; no official score measurement."}
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
