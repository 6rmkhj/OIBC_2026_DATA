# /// script
# requires-python = ">=3.12"
# dependencies = ["pyarrow"]
# ///
# How to run: python submission/score_push_verify_refresh.py AFTER the refresh wave is terminal.
"""Independent chronological data, sequential calibration and six-comparison audit."""
from __future__ import annotations

import json
from datetime import datetime
from math import isclose, isfinite
from typing import Final
from zoneinfo import ZoneInfo

import pyarrow as pa
import pyarrow.parquet as pq

from autoresearch_verify_final import metrics
from score_push_verify import ROOT, digest
from score_push_verify_calibration import temperature, snowy, verify_factor, ensure_terminal

RENEW: Final = ROOT / "analysis_outputs/renew_20261105"
OUT: Final = RENEW / "refresh_wave"
KST: Final = ZoneInfo("Asia/Seoul")
FEATURES: Final = ("wa_temp", "extra_wa_snow", "wb_cloud")
INPUTS: Final = ("ts", "grp", "p_reference", *FEATURES, "static_capacity")


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rows(path, columns=None):
    return pq.read_table(path, columns=columns).to_pylist()


def keyed(records):
    result = {(r["ts"], r["grp"]): r for r in records}
    assert len(result) == len(records)
    return result


def same(a, b) -> bool:
    return a == b or ((a is None or isinstance(a, float) and not isfinite(a)) and (b is None or isinstance(b, float) and not isfinite(b)))


def hour(row) -> int:
    return sum(row["ts"].astimezone(KST).hour >= edge for edge in (10, 12, 14, 16))


def cloud(row) -> int:
    value = row["wb_cloud"]
    return -1 if value is None or not isfinite(value) else sum(value >= edge for edge in (20, 50, 80))


def apply_stages(records, factors):
    temperatures = [r["factor"] for r in factors["weather"]["temperature"]]
    snow = factors["weather"]["conditional_snow"]["factor"]
    hours = [r["factor"] for r in factors["hour"]["hours"]]
    clouds = [r["factor"] for r in factors["cloud"]["clouds"]]
    result = []
    for row in records:
        t, c = temperature(row), cloud(row)
        raw = (1. if t == -1 else temperatures[t]) * (snow if snowy(row) else 1.)
        p_weather = min(row["static_capacity"], max(0., row["p_reference"] * (1 + .5 * (min(1.15, max(.85, raw)) - 1))))
        p_hour = min(row["static_capacity"], max(0., p_weather * (1 + .5 * (hours[hour(row)] - 1))))
        p_cloud = min(row["static_capacity"], max(0., p_hour * (1 + .5 * ((1. if c == -1 else clouds[c]) - 1))))
        result.append({**row, "p_weather": p_weather, "p_hour": p_hour, "p_cloud": p_cloud, "p": p_cloud})
    return result


def canonical():
    capacities = read(RENEW / "final/static_capacity.json")
    sources, references = {}, {}
    for cohort in ("primary", "recent", "latest"):
        latest = cohort == "latest"
        if latest:
            directory = RENEW / "final/predictions/latest_cutoff_march_may"
            base = rows(directory / "scored_predictions.parquet", ["ts", "grp", "y", "smp", "k", "p_reference"])
            feature_directory = RENEW / "final/data/march_may"
            coverage_path = feature_directory / "coverage.parquet"
            stage_paths = {"weather": directory / "predictions.parquet", "hour": RENEW / "hour_final/predictions/latest_cutoff_march_may/predictions.parquet", "cloud": RENEW / "sky_final/predictions/latest_cutoff_march_may/predictions.parquet"}
        else:
            base = rows(RENEW / "recency_wave/comparisons/decay180/ensemble" / cohort / "predictions.parquet", ["ts", "grp", "y", "smp", "k", "p"])
            base = [{**{k: v for k, v in r.items() if k != "p"}, "p_reference": r["p"]} for r in base]
            feature_directory = ROOT / "analysis_outputs/score_push_gpu_20261104/data" / cohort
            coverage_path = RENEW / "recency_wave/data" / cohort / "night_coverage.parquet"
            stage_paths = {"weather": RENEW / "calibration_wave/comparisons/temperature_then_snow" / cohort / "predictions.parquet", "hour": RENEW / "hour_wave/comparisons/hour_bias" / cohort / "predictions.parquet", "cloud": RENEW / "sky_wave/comparisons/cloud_bias" / cohort / "predictions.parquet"}
        feature = keyed(rows(feature_directory / "evaluation.parquet", ["ts", "grp", *FEATURES]))
        night = keyed(rows(coverage_path))
        joined = []
        for r in base:
            key = r["ts"], r["grp"]
            assert (key not in feature) == night[key]["night"]
            joined.append({**r, **{n: feature.get(key, {}).get(n) for n in FEATURES}, "static_capacity": capacities[r["grp"]], "night": night[key]["night"]})
        sources[cohort] = keyed(joined)
        references[cohort] = {stage: keyed(rows(path, ["ts", "grp", "p"])) for stage, path in stage_paths.items()}
        saved = keyed(rows(OUT / "data/sources" / cohort / "rows.parquet"))
        assert set(saved) == set(sources[cohort])
        for key, expected in sources[cohort].items():
            assert all(same(saved[key][name], value) for name, value in expected.items()), key
        saved_refs = keyed(rows(OUT / "data/sources" / cohort / "frozen_references.parquet"))
        assert set(saved_refs) == set(saved)
        for key, record in saved_refs.items():
            assert all(record["p_" + stage] == references[cohort][stage][key]["p"] for stage in stage_paths)
    return sources, references


def verify_factors(training, factors):
    ones = [1.] * len(training)
    bins = [temperature(r) for r in training]
    weather = factors["weather"]
    assert len(weather["temperature"]) == 5
    temp = [verify_factor(training, [b == i for b in bins], item, ones) for i, item in enumerate(weather["temperature"])]
    snow_mask = [snowy(r) for r in training]
    verify_factor(training, snow_mask, weather["snow"], ones)
    verify_factor(training, snow_mask, weather["conditional_snow"], [1. if b == -1 else temp[b] for b in bins])
    stages = apply_stages(training, factors)
    adjusted = [{**r, "p_reference": r["p_weather"]} for r in stages]
    assert len(factors["hour"]["hours"]) == 5 and len(factors["cloud"]["clouds"]) == 4
    for i, item in enumerate(factors["hour"]["hours"]):
        verify_factor(adjusted, [hour(r) == i for r in adjusted], item, ones)
    adjusted = [{**r, "p_reference": r["p_hour"]} for r in stages]
    for i, item in enumerate(factors["cloud"]["clouds"]):
        verify_factor(adjusted, [cloud(r) == i for r in adjusted], item, ones)
    return stages


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = read(OUT / "protocol.json")
    for mapping in (protocol["input_sha256"], protocol["protected_sha256"]):
        for path, expected in mapping.items():
            assert digest(ROOT / path) == expected, path
    for name, record in protocol["own_sources"].items():
        assert digest(ROOT / record["original"]) == digest(OUT / "sources/own" / name) == record["sha256"]
    for name, record in protocol["snapshots"].items():
        assert digest(ROOT / record["original"]) == digest(OUT / "sources" / f"{name}.py") == record["sha256"]
    for manifest in ("prepared_manifest.json", "terminal_manifest.json"):
        for path, expected in read(OUT / manifest).items():
            assert digest(OUT / path) == expected, path
    sources, references = canonical()
    original_factors = {"weather": read(RENEW / "calibration_wave/coefficients.json")["factors"], "hour": read(RENEW / "hour_wave/coefficients.json")["factors"], "cloud": read(RENEW / "sky_wave/coefficients.json")["factors"]}
    for cohort, source in sources.items():
        expected = keyed(apply_stages(list(source.values()), original_factors))
        replay = keyed(rows(OUT / "old_replay" / cohort / "predictions.parquet"))
        assert set(expected) == set(replay)
        for key, row in expected.items():
            for stage in ("weather", "hour", "cloud"):
                assert isclose(row["p_" + stage], references[cohort][stage][key]["p"], rel_tol=1e-12, abs_tol=1e-8)
                assert replay[key]["p_" + stage] == references[cohort][stage][key]["p"]
    pooled = sources["primary"] | sources["recent"]
    assert len(pooled) == len(sources["primary"]) + len(sources["recent"])
    checked, all_pass = [], True
    for fold, cutoff_text, end_text, evaluation_cohort in (("late_recent", "2024-12-01", "2025-03-01", "recent"), ("latest", "2025-03-01", "2025-06-01", "latest")):
        cutoff, end = [datetime.fromisoformat(t).replace(tzinfo=KST) for t in (cutoff_text, end_text)]
        expected_train = {key: r for key, r in pooled.items() if key[0] <= cutoff}
        expected_eval = {key: r for key, r in sources[evaluation_cohort].items() if cutoff < key[0] <= end}
        assert not set(expected_train) & set(expected_eval)
        directory = OUT / "data" / fold
        training = rows(directory / "train.parquet")
        assert set(keyed(training)) == set(expected_train)
        for row in training:
            assert all(same(row[n], v) for n, v in expected_train[(row["ts"], row["grp"])].items())
        evaluation = pq.read_table(directory / "evaluation.parquet")
        assert set(evaluation.column_names) == set(INPUTS)
        eval_rows = evaluation.to_pylist()
        assert set(keyed(eval_rows)) == set(expected_eval)
        for row in eval_rows:
            assert all(same(row[n], expected_eval[(row["ts"], row["grp"])][n]) for n in INPUTS)
        labels = keyed(rows(directory / "labels.parquet"))
        assert set(labels) == set(expected_eval)
        for key, row in labels.items():
            assert all(row[n] == expected_eval[key][n] for n in ("y", "smp", "k"))
        coefficients = read(OUT / "coefficients" / f"{fold}.json")
        assert coefficients["train_source_sha256"] == digest(directory / "train.parquet") and coefficients["fit_scalar_count"] == 16
        assert datetime.fromisoformat(coefficients["cutoff_inclusive"]) == cutoff and coefficients["train_rows"] == len(training)
        assert coefficients["original_replay_receipt_sha256"] == digest(OUT / "old_replay/receipt.json")
        stages = keyed(verify_factors(training, coefficients["factors"]))
        saved_stages = keyed(rows(OUT / "training_stages" / f"{fold}.parquet"))
        assert set(saved_stages) == set(stages)
        for key, row in saved_stages.items():
            assert all(isclose(row[n], stages[key][n], rel_tol=1e-12, abs_tol=1e-8) for n in ("p_weather", "p_hour", "p_cloud"))
        expected = keyed(apply_stages(eval_rows, coefficients["factors"]))
        compared = rows(OUT / "comparisons" / fold / "predictions.parquet")
        assert set(keyed(compared)) == set(expected)
        for row in compared:
            key = row["ts"], row["grp"]
            assert all(isclose(row[n], expected[key][n], rel_tol=1e-12, abs_tol=1e-8) for n in ("p_weather", "p_hour", "p_cloud", "p"))
            assert all(row[n] == labels[key][n] for n in ("y", "smp", "k"))
            assert all(row["frozen_" + stage] == references[evaluation_cohort][stage][key]["p"] for stage in ("weather", "hour", "cloud"))
        scores = {n: metrics(compared, n) for n in ("p", "frozen_weather", "frozen_hour", "frozen_cloud")}
        saved_metrics = read(OUT / "comparisons" / fold / "metrics.json")
        for name, values in scores.items():
            for metric, value in values.items():
                assert isclose(value, saved_metrics[name][metric], rel_tol=1e-12, abs_tol=1e-4)
        eligible = all(scores["p"]["W"] < scores["frozen_" + stage]["W"] for stage in ("weather", "hour", "cloud"))
        all_pass &= eligible
        checked.append({"fold": fold, "train_rows": len(training), "evaluation_rows": len(compared), "scores": scores, "eligible": eligible})
    result = read(OUT / "results.json")
    assert result["eligible"] == all_pass and result["real_scalar_fit_count"] == 32 and result["tree_fits"] == 0
    assert not result["loaded_existing_coefficients"] and not result["test_loaded"] and not result["exported"] and not result["full_refit"]
    assert result["candidate_count"] == 1 and len(result["records"]) == 1
    assert result["selected"] == (result["records"][0] if all_pass else None) and result["reference_retained"] == (not all_pass)
    assert len(result["gate_comparisons"]) == 6
    score_map = {record["fold"]: record["scores"] for record in checked}
    for gate in result["gate_comparisons"]:
        actual = score_map[gate["fold"]]
        assert isclose(gate["new_W"], actual["p"]["W"], rel_tol=1e-12)
        assert isclose(gate["reference_W"], actual[gate["reference"]]["W"], rel_tol=1e-12)
        assert gate["strictly_improves"] == (actual["p"]["W"] < actual[gate["reference"]]["W"])
    controller = read(OUT / "controller_receipt.json")
    assert controller["exit_code"] == 0 and controller["real_scalar_fit_count"] == 32 and controller["tree_fits"] == 0
    identity = controller["identity"]
    assert identity["priority_class"] == 32 and identity["pyarrow_cpu"] == identity["pyarrow_io"] == 4
    assert all(pool["num_threads"] == 16 for pool in identity["threadpools"])
    ensure_terminal(identity)
    assert not (OUT / "tmp").exists()
    evidence = {"status": "PASS", "records": checked, "eligible": all_pass, "real_scalar_fits_verified": 32,
                "protected_files": len(protocol["protected_sha256"]), "terminal_manifest_sha256": digest(OUT / "terminal_manifest.json"),
                "limits": "Both periods historically exposed; no production refit, test prediction, new export or official score."}
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
