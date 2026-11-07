"""Independently replay the fixed cloud-by-solar surface export and validate its CSV/ZIP contract.

No production application, exporter, validator, estimator, or optimizer is
imported. Writes only a new independent_export_check.json receipt.
"""
from __future__ import annotations

import ast
import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import io
import json
from math import fsum
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd
import pyarrow as pa

ROOT = Path(__file__).resolve().parents[2]
WAVE = ROOT / "analysis_outputs/renew_20261107/cloud_solar_surface"
OUT = ROOT / "analysis_outputs/renew_20261107/cloud_solar_surface_final"
FINAL = ROOT / "analysis_outputs/renew_20261105/final"
CANDIDATE = ROOT / "submission/renew_cloud_solar_candidate_20261107"
BEST = ROOT / "submission/renew_candidate_20261105/submission_files.zip"
PARTICIPANT = ROOT / "handover 2/01_participant_dataset"
KEYS = ["ts", "grp"]
SPLITS = ("old_cutoff_march_may", "latest_cutoff_march_may", "test")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def keys_equal(left, right):
    assert not left.duplicated(KEYS).any() and not right.duplicated(KEYS).any()
    pd.testing.assert_frame_equal(left[KEYS].reset_index(drop=True), right[KEYS].reset_index(drop=True), check_exact=True)


def independent_apply(frame, delta):
    cloud = frame.wb_cloud.to_numpy(dtype=float)
    solar = frame.cosz.to_numpy(dtype=float)
    valid = np.isfinite(cloud) & np.isfinite(solar)
    adjustment = np.zeros(len(frame))
    # Four-corner bilinear interpolation, independent of production tensor hats.
    x = np.minimum(100., np.maximum(0., cloud[valid]))
    z = np.minimum(1., np.maximum(0., solar[valid]))
    i = np.minimum(1, np.floor(x / 50.).astype(int))
    j = np.minimum(1, np.floor(z / .5).astype(int))
    u, v = (x - i * 50.) / 50., (z - j * .5) / .5
    grid = np.asarray(delta).reshape(3, 3)
    lower = grid[i, j] + u * (grid[i + 1, j] - grid[i, j])
    upper = grid[i, j + 1] + u * (grid[i + 1, j + 1] - grid[i, j + 1])
    adjustment[valid] = lower + v * (upper - lower)
    factor = 1. + .5 * adjustment
    before_clip = frame.p_reference.to_numpy() * factor
    prediction = np.minimum(frame.static_capacity.to_numpy(), np.maximum(0., before_clip))
    prediction[frame.night.to_numpy()] = 0.
    assert np.isfinite(prediction).all()
    assert factor.min() >= .925 - 1e-12 and factor.max() <= 1.075 + 1e-12
    assert np.array_equal(prediction[~valid], frame.p_reference.to_numpy()[~valid])
    return adjustment, factor, before_clip, prediction


def metrics(frame, name):
    y, p, smp, k = (frame[column].to_numpy(dtype=float) for column in ("y", name, "smp", "k"))
    assert all(np.isfinite(values).all() for values in (y, p, smp, k))
    penalty = fsum(float(s * g * abs(t - v)) for s, g, t, v in zip(smp, k, y, p, strict=True))
    denominator = fsum(float(s * g * t) for s, g, t in zip(smp, k, y, strict=True))
    revenue = fsum(float(s * t) for s, t in zip(smp, y, strict=True))
    return dict(W=penalty, W_pct=100 * penalty / denominator, revenue=revenue, S=revenue - .1 * penalty, rows=len(frame))


def read_csv_bytes(content):
    with io.StringIO(content.decode("utf-8-sig"), newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames, list(reader)


def main():
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = read(OUT / "protocol.json")
    manifest = read(CANDIDATE / "manifest.json")
    check = read(OUT / "export_check.json")
    assert check["status"] == "PASS" and check["validator_exit_code"] == 0
    assert protocol["new_fits"] == 0 and protocol["diagnostics_do_not_select"]
    assert protocol["all_history_exposed"] and not protocol["official_score_available"] and not protocol["uploaded"]
    assert not manifest["official_score_available"] and not manifest["uploaded"] and manifest["primary_fit_partly_in_sample"]
    assert manifest["protocol_sha256"] == sha(OUT / "protocol.json")
    for name, expected in protocol["source_sha256"].items():
        assert sha(ROOT / name) == expected, name
    for name, expected in protocol["inputs_sha256"].items():
        assert sha(ROOT / name) == expected, name
    for name, expected in protocol["protected_sha256"].items():
        assert sha(ROOT / name) == expected, name
    assert sha(OUT / "export_cloud_solar_surface.py") == sha(ROOT / "submission/score_push_continue/export_cloud_solar_surface.py")
    assert sha(WAVE / "results.json") == protocol["development_results_sha256"]
    assert sha(WAVE / "independent_check.json") == protocol["independent_check_sha256"]
    assert read(WAVE / "independent_check.json")["status"] == "PASS" and read(WAVE / "results.json")["eligible"]
    coefficient = WAVE / "fits/primary/coefficients.json"
    assert sha(coefficient) == sha(OUT / "coefficients.json") == protocol["coefficient_sha256"] == manifest["coefficient_sha256"]
    fitted = read(coefficient)
    assert fitted["cloud_knots"] == [0., 50., 100.] and fitted["solar_knots"] == [0., .5, 1.]
    assert fitted["shrink"] == .5 and fitted["shape"] == [3, 3]
    assert fitted["basis_order"] == "cloud-major; index=3*cloud_index+solar_index"
    delta = np.asarray(fitted["delta"], dtype=float)
    assert delta.shape == (9,) and np.isfinite(delta).all() and np.max(np.abs(delta)) <= .15 + 1e-12
    assert manifest["cloud_knots"] == fitted["cloud_knots"] and manifest["solar_knots"] == fitted["solar_knots"]
    assert manifest["delta"] == fitted["delta"] and manifest["shrink"] == .5
    assert sha(BEST) == manifest["source_best_zip_sha256"] == "ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434"
    seal = read(OUT / "predictions_fixed.json")
    assert seal["before_diagnostic_label_reads"] and seal["coefficient_sha256"] == sha(coefficient)
    assert datetime.fromisoformat(protocol["created_utc"]) <= datetime.fromisoformat(seal["utc"])
    assert datetime.fromisoformat(read(WAVE / "fits/primary/optimization.json")["finished_utc"]) <= datetime.fromisoformat(protocol["created_utc"])
    # Verify the frozen exporter source places the seal before diagnostic reads.
    source = (OUT / "export_cloud_solar_surface.py").read_text()
    tree = ast.parse(source)
    source_lines = source.splitlines()
    seal_lines = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Constant) and node.value == "predictions_fixed.json"]
    diagnostic_read_lines = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute) and node.func.attr == "read_parquet"
        and "scored_predictions.parquet" in ast.get_source_segment(source, node)]
    assert len(seal_lines) == 1 and len(diagnostic_read_lines) == 1 and seal_lines[0] < diagnostic_read_lines[0]
    predictions = {}
    diagnostics = {}
    for split in SPLITS:
        feature_split = "test" if split == "test" else "march_may"
        reference = pd.read_parquet(FINAL / "predictions" / split / "predictions.parquet", columns=KEYS + ["p", "static_capacity"]).rename(columns={"p": "p_reference"})
        coverage = pd.read_parquet(FINAL / "data" / feature_split / "coverage.parquet")
        cloud = pd.read_parquet(FINAL / "data" / feature_split / "evaluation.parquet", columns=KEYS + ["wb_cloud", "cosz"])
        joined = reference.merge(coverage, on=KEYS, how="left", sort=False, validate="one_to_one")
        joined = joined.merge(cloud, on=KEYS, how="left", sort=False, validate="one_to_one", indicator=True)
        keys_equal(reference, joined)
        assert joined.night.notna().all() and np.array_equal(joined._merge.eq("left_only"), joined.night)
        assert joined.loc[joined.night, "p_reference"].eq(0).all()
        columns = KEYS + ["p_reference", "wb_cloud", "cosz", "static_capacity", "night"]
        inputs = joined[columns]
        pd.testing.assert_frame_equal(pd.read_parquet(OUT / split / "inputs.parquet"), inputs, check_exact=True)
        path = OUT / split / "predictions.parquet"
        assert sha(path) == seal["prediction_sha256"][split]
        saved = pd.read_parquet(path)
        pd.testing.assert_frame_equal(saved[columns], inputs, check_exact=True)
        adjustment, factor, before_clip, prediction = independent_apply(inputs, delta)
        for name, expected in (("delta", adjustment), ("effective_factor", factor), ("before_capacity_clip", before_clip), ("p", prediction)):
            np.testing.assert_allclose(saved[name], expected, rtol=1e-14, atol=2e-9)
        assert len(saved) == (17520 if split == "test" else 4416)
        assert saved.loc[saved.night, "p"].eq(0).all()
        predictions[split] = saved.assign(independent_prediction=prediction)
        if split != "test":
            labels = pd.read_parquet(FINAL / "predictions" / split / "scored_predictions.parquet", columns=KEYS + ["y", "smp", "k"])
            keys_equal(saved, labels)
            scored = pd.read_parquet(OUT / split / "scored_predictions.parquet")
            pd.testing.assert_frame_equal(scored[list(saved)], saved, check_exact=True)
            for name in ("y", "smp", "k"):
                np.testing.assert_array_equal(scored[name], labels[name])
            diagnostics[split] = {name: metrics(scored, name) for name in ("p_reference", "p")}
    diag = read(OUT / "diagnostics.json")
    assert diag["descriptive_only"] and not diag["used_for_reselection"] and diag["label_read_after_prediction_freeze"]
    for split, result in diagnostics.items():
        for name, values in result.items():
            for metric_name, value in values.items():
                np.testing.assert_allclose(diag["scores"][split][name][metric_name], value, rtol=1e-12, atol=1e-4)
    assert manifest["deployment_diagnostics"] == diag["scores"]
    assert manifest["development_scores"] == read(WAVE / "results.json")["scores"]
    assert manifest["supplemental_forward_diagnostic"] == read(WAVE / "results.json")["diagnostic_scores"]
    with zipfile.ZipFile(BEST) as baseline, zipfile.ZipFile(CANDIDATE / "submission_files.zip") as candidate:
        assert sorted(baseline.namelist()) == sorted(candidate.namelist()) == ["composition.csv", "forecast.csv"]
        assert candidate.testzip() is None
        assert candidate.read("composition.csv") == baseline.read("composition.csv") == (CANDIDATE / "composition.csv").read_bytes()
        assert candidate.read("forecast.csv") == (CANDIDATE / "forecast.csv").read_bytes()
        baseline_forecast = pd.read_csv(io.BytesIO(baseline.read("forecast.csv"))).rename(columns={"group": "grp"})
        forecast_bytes = candidate.read("forecast.csv")
    headers, composition = read_csv_bytes((CANDIDATE / "composition.csv").read_bytes())
    assert headers == ["site_id", "group"] and len(composition) == 253
    _, sites = read_csv_bytes((PARTICIPANT / "sites.csv").read_bytes())
    _, smp_rows = read_csv_bytes((PARTICIPANT / "smp.csv").read_bytes())
    site_capacity = {row["site_id"]: Decimal(row["capacity_kw"]) for row in sites}
    assert len(site_capacity) == len(sites) == 253
    assert len({row["site_id"] for row in composition}) == 253
    assert {row["site_id"] for row in composition} == set(site_capacity)
    assert {row["group"] for row in composition} == {"G1", "G2"}
    capacities = {group: sum((site_capacity[row["site_id"]] for row in composition if row["group"] == group), Decimal(0)) for group in ("G1", "G2")}
    assert all(Decimal("20000") <= cap <= Decimal("22655.4") for cap in capacities.values())
    headers, rows = read_csv_bytes(forecast_bytes)
    assert headers == ["group", "ts", "forecast_kwh"] and len(rows) == 17520
    times = {datetime.fromisoformat(row["ts"]) for row in smp_rows}
    actual = [(row["group"], datetime.fromisoformat(row["ts"])) for row in rows]
    assert len(times) == 8760 and len(set(actual)) == len(actual)
    assert set(actual) == {(group, stamp) for group in ("G1", "G2") for stamp in times}
    assert all(stamp.utcoffset() == timedelta(hours=9) for _, stamp in actual)
    for row in rows:
        value = Decimal(row["forecast_kwh"])
        assert value.is_finite() and Decimal(0) <= value <= capacities[row["group"]]
        assert value * 1000 == (value * 1000).to_integral_value()
    forecast = pd.read_csv(io.BytesIO(forecast_bytes)).rename(columns={"group": "grp"})
    forecast["ts"] = pd.to_datetime(forecast.ts).dt.tz_convert("Asia/Seoul")
    baseline_forecast["ts"] = pd.to_datetime(baseline_forecast.ts).dt.tz_convert("Asia/Seoul")
    test = predictions["test"].sort_values(["grp", "ts"]).reset_index(drop=True)
    baseline_forecast = baseline_forecast.sort_values(["grp", "ts"]).reset_index(drop=True)
    keys_equal(forecast, test)
    keys_equal(baseline_forecast, test)
    np.testing.assert_array_equal(np.round(test.p_reference, 3), baseline_forecast.forecast_kwh)
    np.testing.assert_array_equal(np.round(test.independent_prediction, 3), forecast.forecast_kwh)
    assert np.max(np.abs(forecast.forecast_kwh - test.independent_prediction)) <= .0005 + 1e-9
    for name in ("composition.csv", "forecast.csv", "submission_files.zip"):
        assert sha(CANDIDATE / name) == manifest["files_sha256"][name] == check["files_sha256"][name]
    report = dict(status="PASS", checked_utc=datetime.now(timezone.utc).isoformat(),
        candidate=str(CANDIDATE), rows_replayed={split: len(value) for split, value in predictions.items()},
        sites=253, forecast_rows=17520, hours_per_group=8760,
        composition_bytes_identical_to_best_zip=True, original_submitted_forecast_reconstructed_exactly=True,
        independently_rounded_forecast_exact=True, zip_members_exact=True, all_capacity_and_timestamp_checks=True,
        protocol_and_source_order_freeze_before_diagnostic_labels_verified=True,
        deployment_diagnostics=diagnostics, deployment_diagnostics_both_worsen=all(diagnostics[split]["p"]["W"] > diagnostics[split]["p_reference"]["W"] for split in diagnostics),
        original_inputs_and_prior_candidates_unchanged=True, new_fits=0,
        files_sha256=manifest["files_sha256"], exporter_protocol_sha256=sha(OUT / "protocol.json"),
        verifier_sha256=sha(__file__), official_score_available=False, uploaded=False,
        limitation="Export fidelity verified. Descriptive diagnostics are reported separately; development gains do not establish an official-score gain.")
    (OUT / "independent_export_check.json").write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(report, indent=2, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
