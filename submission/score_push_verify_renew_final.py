# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: python submission/score_push_verify_renew_final.py
"""Independently replay final models, frozen recipe, diagnostics and exported bytes."""
from __future__ import annotations

import csv
import json
import sys
import zipfile
from datetime import datetime
from math import fsum, isclose, isfinite
from typing import Final

import lightgbm as lgb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from autoresearch_verify_final import metrics
from score_push_verify_renew_final_data import ROOT, OUT, CPU, RENEW, digest, scale

sys.path.insert(0, str(ROOT / "submission/score_push_renew"))
from temporal_common import ensure_terminal

CANDIDATE: Final = ROOT / "submission/renew_candidate_20261105"


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = json.loads((OUT / "protocol.json").read_text())
    prepared = json.loads((OUT / "independent_data_check.json").read_text())
    assert prepared["status"] == "PASS" and prepared["protocol_sha256"] == digest(OUT / "protocol.json")
    assert prepared["prepared_manifest_sha256"] == digest(OUT / "prepared_manifest.json")
    amendment = json.loads((OUT / "source_amendment.json").read_text())
    for name, record in {**protocol["own_sources"], **amendment["own_sources"]}.items():
        assert digest(ROOT / record["original"]) == record["sha256"]
        assert digest(OUT / record.get("snapshot", f"sources/own/{name}")) == record["sha256"]
    for name, record in protocol["snapshots"].items():
        assert digest(OUT / "sources" / f"{name}.py") == record["sha256"]
    for path, expected in protocol["protected_sha256"].items():
        assert digest(ROOT / path) == expected, path
    for manifest in ("prepared_manifest.json", "artifact_hashes.json"):
        for path, expected in json.loads((OUT / manifest).read_text()).items():
            assert digest(OUT / path) == expected, path
    intervals, model_count = [], 0
    for split, evaluation in (("latest", "march_may"), ("test", "test")):
        frame = pq.read_table(OUT / "data" / evaluation / "evaluation.parquet")
        spec = json.loads((OUT / "data" / split / "features.json").read_text())
        inverse = scale(frame["cosz"].to_numpy()) * frame["capacity_kw"].to_numpy()
        for seed in range(3):
            directory = OUT / "models" / split / f"seed{seed}"
            config = json.loads((directory / "config.json").read_text())
            assert config["features"] == spec["features"] and config["cutoff"] == spec["cutoff"]
            assert config["parameters"] == {**protocol["parameters"], "random_state": None if seed == 0 else seed}
            assert config["prepared_manifest_sha256"] == digest(OUT / "prepared_manifest.json")
            model = lgb.Booster(model_file=str(directory / "model.txt"))
            assert model.current_iteration() == 400 and model.num_trees() == 400
            assert model.feature_name() == config["features"]
            assert model.params["objective"] == "regression_l1" and model.params["num_leaves"] == 63
            assert model.params["num_threads"] == 16 and isclose(model.params["learning_rate"], .03)
            assert model.params["min_data_in_leaf"] == 50 and model.params["bagging_freq"] == 1
            assert model.params["seed"] == seed
            assert isclose(model.params["bagging_fraction"], .8) and isclose(model.params["feature_fraction"], .8)
            prediction = model.predict(frame.select(config["features"]).to_pandas(), num_threads=1) * inverse
            saved = pq.read_table(directory / "daylight_raw.parquet")
            assert frame.select(["ts", "grp"]).to_pylist() == saved.select(["ts", "grp"]).to_pylist()
            np.testing.assert_array_equal(prediction, saved["p_raw"].to_numpy())
            replay = json.loads((directory / "replay.json").read_text())
            assert replay["passed"] and replay["rows"] == len(frame)
            assert replay["model_sha256"] == digest(directory / "model.txt") and replay["raw_sha256"] == digest(directory / "daylight_raw.parquet")
            runtime = json.loads((directory / "runtime.json").read_text())
            assert not runtime["loaded_existing_model"] and runtime["priority_class"] == 32
            assert runtime["pyarrow_cpu"] == runtime["pyarrow_io"] == 4
            assert all(pool["num_threads"] == 16 for pool in runtime["threadpools"])
            receipt = json.loads((directory / "controller_receipt.json").read_text())
            assert receipt["exit_code"] == 0 and receipt["exact_worker_absent"]
            ensure_terminal(receipt["identity"])
            intervals.append((datetime.fromisoformat(receipt["started_utc"]), datetime.fromisoformat(receipt["finished_utc"])))
            model_count += 1
    intervals.sort()
    assert model_count == 6 and all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:]))
    factors = json.loads((OUT / "selected_coefficients.json").read_text())["factors"]
    temperatures = [r["factor"] for r in factors["temperature"]]
    snow_factor = factors["conditional_snow"]["factor"]
    capacity = json.loads((OUT / "static_capacity.json").read_text())
    freeze = json.loads((OUT / "prediction_freeze.json").read_text())
    assert freeze["before_confirmation_labels"]
    diagnostic = json.loads((OUT / "diagnostic_metrics.json").read_text())
    scores = {}
    for name, split in (("old_cutoff_march_may", "march_may"), ("latest_cutoff_march_may", "march_may"), ("test", "test")):
        directory = OUT / "predictions" / name
        assert digest(directory / "predictions.parquet") == freeze["sha256"][name]
        frame = pq.read_table(OUT / "data" / split / "evaluation.parquet", columns=["ts", "grp", "wa_temp", "extra_wa_snow"]).to_pylist()
        weather = {(r["ts"], r["grp"]): r for r in frame}
        seeds = pq.read_table(directory / "signed_seeds.parquet").to_pylist()
        pure = {(r["ts"], r["grp"]): max(0., fsum(r[f"seed{s}_raw"] for s in range(3)) / 3) for r in seeds}
        for seed in range(3):
            model_dir = RENEW / "recency_wave/trials/decay180/recent" / f"seed{seed}" if name == "old_cutoff_march_may" else OUT / "models" / ("latest" if split == "march_may" else "test") / f"seed{seed}"
            if name == "old_cutoff_march_may":
                full = pq.read_table(OUT / "data/march_may/evaluation.parquet")
                config = json.loads((model_dir / "config.json").read_text())
                model = lgb.Booster(model_file=str(model_dir / "model.txt"))
                pred = model.predict(full.select(config["features"]).to_pandas(), num_threads=1) * (scale(full["cosz"].to_numpy()) * full["capacity_kw"].to_numpy())
                np.testing.assert_array_equal(pred, np.array([r[f"seed{seed}_raw"] for r in seeds]))
            else:
                raw = pq.read_table(model_dir / "daylight_raw.parquet").to_pylist()
                assert {(r["ts"], r["grp"]): r["p_raw"] for r in raw} == {(r["ts"], r["grp"]): r[f"seed{seed}_raw"] for r in seeds}
        base_split = "latest" if name == "latest_cutoff_march_may" else split
        base = {(r["ts"], r["grp"]): r["p_cpu"] for r in pq.read_table(OUT / "data" / base_split / "cpu_base.parquet").to_pylist()}
        rows = pq.read_table(directory / "predictions.parquet").to_pylist()
        assert len(rows) == len(base) and {(r["ts"], r["grp"]) for r in rows} == set(base)
        for row in rows:
            key = row["ts"], row["grp"]
            temporal = pure.get(key, 0.)
            reference = (1 - protocol["alpha"]) * base[key] + protocol["alpha"] * temporal
            feature = weather.get(key)
            factor = 1.
            if feature is not None:
                temp, snow = feature["wa_temp"], feature["extra_wa_snow"]
                if temp is not None and isfinite(temp):
                    factor *= temperatures[sum(temp >= cut for cut in (0, 10, 20, 30))]
                if snow is not None and isfinite(snow) and snow >= .001:
                    factor *= snow_factor
            effective = 1 + .5 * (max(.85, min(1.15, factor)) - 1)
            prediction = max(0., min(capacity[row["grp"]], reference * effective))
            assert row["p_cpu"] == base[key]
            for field, expected in (("p_temporal", temporal), ("p_reference", reference), ("raw_factor", factor), ("effective_factor", effective), ("p", prediction)):
                assert isclose(row[field], expected, rel_tol=1e-12, abs_tol=1e-8), (key, field)
            assert 0 <= row["p"] <= capacity[row["grp"]] and (feature is not None or row["p"] == 0)
        if name != "test":
            labelled = pq.read_table(directory / "scored_predictions.parquet").to_pylist()
            original = pq.read_table(CPU / ("deployment_check/paired_predictions.parquet" if name == "latest_cutoff_march_may" else "final/outer_predictions.parquet"), columns=["ts", "grp", "y", "smp", "k", "p_previous"]).to_pylist()
            labels = {(r["ts"], r["grp"]): r for r in original}
            assert len(labelled) == 4416 and len(labelled) == len(rows)
            forecasts = {(r["ts"], r["grp"]): r["p"] for r in rows}
            for row in labelled:
                key = row["ts"], row["grp"]
                assert row["p"] == forecasts[key] and all(row[n] == labels[key][n] for n in ("y", "smp", "k"))
                row["p_previous"] = labels[key]["p_previous"]
            scores[name] = {p: metrics(labelled, p) for p in ("p_cpu", "p_reference", "p", "p_previous")}
            for column in ("p_cpu", "p_reference", "p"):
                for metric, value in scores[name][column].items():
                    assert isclose(value, diagnostic["scores"][name][column][metric], rel_tol=1e-12, abs_tol=1e-4)
    forecast = {(r["ts"].isoformat(), r["grp"]): r["p"] for r in pq.read_table(OUT / "predictions/test/predictions.parquet").to_pylist()}
    with (CANDIDATE / "forecast.csv").open(encoding="utf-8", newline="") as handle:
        exported = list(csv.DictReader(handle))
    assert len(exported) == len(forecast) == 17520
    actual = {(datetime.fromisoformat(r["ts"]).isoformat(), r["group"]): float(r["forecast_kwh"]) for r in exported}
    assert len(actual) == len(exported) and set(actual) == set(forecast)
    assert all(value == float(np.round(forecast[key], 3)) for key, value in actual.items())
    assert digest(CANDIDATE / "composition.csv") == protocol["composition_sha256"]
    with zipfile.ZipFile(CANDIDATE / "submission_files.zip") as archive:
        assert sorted(archive.namelist()) == ["composition.csv", "forecast.csv"] and archive.testzip() is None
        assert all(archive.read(name) == (CANDIDATE / name).read_bytes() for name in archive.namelist())
    manifest = json.loads((CANDIDATE / "manifest.json").read_text())
    assert not manifest["official_score_available"] and manifest["no_confirmation_reselection"]
    for path, expected in manifest["files_sha256"].items():
        assert digest(CANDIDATE / path) == expected
    controller = json.loads((OUT / "controller_receipt.json").read_text())
    assert controller["exit_code"] == 0 and controller["new_model_fit_count"] == 6
    ensure_terminal(controller["identity"])
    evidence = {"status": "PASS", "new_models_replayed": model_count, "old_cutoff_models_replayed": 3,
                "serial_intervals": len(intervals), "protected_files": len(protocol["protected_sha256"]),
                "forecast_rows": len(exported), "zip_exact": True, "scores": scores,
                "limitations": "Historically exposed descriptive confirmation; no new official score or upload. Inherited one-row CPU precision bridge documented in final/evidence."}
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
