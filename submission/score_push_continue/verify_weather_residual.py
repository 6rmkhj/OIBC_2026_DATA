"""Independently replay fixed weather-residual calibrators without retraining.

Reconstructs fit rows, clipped ratio targets, normalized monetary weights, every
saved model prediction (also by traversing tree nodes), output and decision.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from math import fsum
import os
from pathlib import Path

os.environ.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")

import joblib
import numpy as np
import pandas as pd
import pyarrow as pa
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis_outputs/renew_20261107/weather_residual"
SOURCE = ROOT / "analysis_outputs/renew_20261106/poisson_wave/data"
KEYS = ["ts", "grp"]
FEATURES = ["wa_cloud", "wb_cloud", "cosz", "wa_temp", "wa_humidity", "wb_rel_hum"]
INPUT_COLUMNS = [*KEYS, "p_reference", *FEATURES, "static_capacity", "night"]
CUTOFF = pd.Timestamp("2024-02-01", tz="Asia/Seoul")
PARAMETERS = dict(loss="absolute_error", learning_rate=.03, max_iter=100, max_leaf_nodes=4,
                  max_depth=2, min_samples_leaf=300, l2_regularization=10., max_bins=32,
                  early_stopping=False, random_state=0)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def digest(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def equal_keys(left, right):
    assert not left.duplicated(KEYS).any() and not right.duplicated(KEYS).any()
    pd.testing.assert_frame_equal(left[KEYS].reset_index(drop=True), right[KEYS].reset_index(drop=True), check_exact=True)


def metric(frame, prediction):
    y, p, smp, k = (frame[name].to_numpy(dtype=float) for name in ("y", prediction, "smp", "k"))
    assert all(np.isfinite(values).all() for values in (y, p, smp, k)) and (smp*k >= 0).all()
    penalty = fsum(float(a*b*abs(t-v)) for t,v,a,b in zip(y,p,smp,k, strict=True))
    denominator = fsum(float(a*b*t) for t,a,b in zip(y,smp,k, strict=True))
    revenue = fsum(float(a*t) for t,a in zip(y,smp, strict=True))
    return dict(W=penalty, W_pct=100*penalty/denominator, revenue=revenue, S=revenue-.1*penalty, rows=len(frame))


def original_fold(fold):
    data = SOURCE / fold
    labels = pd.read_parquet(data / "labels.parquet")
    application = pd.read_parquet(data / "application_inputs.parquet")
    coverage = pd.read_parquet(data / "coverage.parquet")
    features = pd.read_parquet(data / "evaluation.parquet", columns=KEYS + FEATURES)
    equal_keys(labels, application)
    equal_keys(labels, coverage)
    frame = labels.merge(application[KEYS + ["static_capacity"]], on=KEYS, sort=False, validate="one_to_one")
    frame = frame.merge(coverage, on=KEYS, sort=False, validate="one_to_one")
    frame = frame.merge(features, on=KEYS, how="left", sort=False, validate="one_to_one", indicator=True)
    equal_keys(labels, frame)
    assert frame._merge.eq("left_only").eq(frame.night).all()
    assert frame.loc[frame.night, "p_reference"].eq(0).all()
    assert not np.isinf(frame[FEATURES].to_numpy(dtype=float)).any()
    stored = pd.read_parquet(OUT / "data" / fold / "inputs.parquet")
    assert list(stored) == INPUT_COLUMNS
    pd.testing.assert_frame_equal(stored, frame[INPUT_COLUMNS], check_exact=True)
    return frame.drop(columns="_merge")


def tree_algebra(model, frame):
    """Direct node traversal is separate from sklearn's native predictor."""
    values = frame[FEATURES].to_numpy(dtype=np.float64)
    assert not np.isinf(values).any()
    raw = np.full(len(frame), float(np.asarray(model._baseline_prediction).ravel()[0]))
    assert len(model._predictors) == 100
    for iteration in model._predictors:
        assert len(iteration) == 1
        nodes = iteration[0].nodes
        assert nodes["is_leaf"].sum() <= 4 and nodes["depth"].max() <= 2
        assert not nodes["is_categorical"].any()
        assert (nodes["count"][nodes["is_leaf"].astype(bool)] >= 300).all()
        positions = np.zeros(len(frame), dtype=np.int64)
        for _ in range(3):
            leaf = nodes["is_leaf"][positions].astype(bool)
            if leaf.all():
                break
            rows = np.flatnonzero(~leaf)
            current = positions[rows]
            feature = nodes["feature_idx"][current].astype(int)
            assert ((feature >= 0) & (feature < 6)).all()
            x = values[rows, feature]
            go_left = np.where(np.isnan(x), nodes["missing_go_to_left"][current].astype(bool),
                               x <= nodes["num_threshold"][current])
            positions[rows] = np.where(go_left, nodes["left"][current], nodes["right"][current])
        assert nodes["is_leaf"][positions].all()
        raw += nodes["value"][positions]
    return raw


def replay(model, frame):
    native = model.predict(frame[FEATURES])
    algebra = tree_algebra(model, frame)
    assert np.isfinite(native).all() and np.isfinite(algebra).all()
    np.testing.assert_allclose(native, algebra, rtol=1e-12, atol=1e-12)
    return native, float(np.max(np.abs(native-algebra)))


def verify_fit(name, original):
    directory = OUT / "fits" / name
    frame = original if name == "primary" else original.loc[original.ts <= CUTOFF]
    active = frame.p_reference.gt(0).to_numpy() & (frame.smp * frame.k).gt(0).to_numpy()
    rows = frame.loc[active].reset_index(drop=True)
    stored = pd.read_parquet(directory / "fit_rows.parquet")
    equal_keys(stored, rows)
    for column in ["p_reference", "y", "smp", "k", *FEATURES]:
        np.testing.assert_array_equal(stored[column], rows[column])
    residual = rows.y.to_numpy() / rows.p_reference.to_numpy() - 1.
    target = np.clip(residual, -.15, .15)
    mass = rows.smp.to_numpy() * rows.k.to_numpy() * rows.p_reference.to_numpy()
    weight = mass / (fsum(float(w) for w in mass) / len(mass))
    for column, expected in (("ratio_residual", residual), ("target_clipped", target),
                             ("monetary_prediction_weight", mass), ("sample_weight", weight)):
        np.testing.assert_allclose(stored[column], expected, rtol=1e-13, atol=1e-12)
    assert np.isfinite(weight).all() and (weight > 0).all()
    np.testing.assert_allclose(weight.mean(), 1., rtol=1e-14, atol=1e-14)
    model = joblib.load(directory / "model.joblib")
    assert isinstance(model, HistGradientBoostingRegressor)
    parameters = model.get_params()
    assert all(parameters[name] == value for name,value in PARAMETERS.items())
    assert not model.do_early_stopping_ and model.n_iter_ == 100 and not model.warm_start
    assert model.n_features_in_ == 6 and model.n_trees_per_iteration_ == 1
    np.testing.assert_array_equal(model.feature_names_in_, FEATURES)
    assert not len(model.validation_score_)
    order = np.argsort(target, kind="stable")
    median_index = np.searchsorted(np.cumsum(weight[order]), weight.sum() * .5, side="left")
    median = target[order[min(median_index, len(order)-1)]]
    np.testing.assert_allclose(np.asarray(model._baseline_prediction).ravel(), [median], rtol=1e-12, atol=1e-12)
    prediction, error = replay(model, rows)
    training = pd.read_parquet(directory / "training_predictions.parquet")
    equal_keys(training, rows)
    np.testing.assert_array_equal(training.raw_delta, prediction)
    np.testing.assert_array_equal(training.delta, np.clip(prediction, -.15, .15))
    config = read(directory / "config.json")
    assert config["parameters"] == PARAMETERS and config["features"] == FEATURES
    assert config["target"] == "target_clipped" and config["sample_weight"] == "sample_weight"
    assert config["fit_name"] == name and config["shrink"] == .5 and config["delta_bounds"] == [-.15, .15]
    assert config["input_schema"] == INPUT_COLUMNS and config["rows"] == len(rows)
    assert config["fit_rows_sha256"] == digest(directory / "fit_rows.parquet")
    receipt = read(directory / "receipt.json")
    assert receipt["name"] == name and receipt["fit_count"] == 1 and receipt["iterations"] == 100
    assert receipt["input_rows"] == len(frame) and receipt["active_rows"] == len(rows)
    assert receipt["native_replay_exact"] and receipt["model_sha256"] == digest(directory / "model.joblib")
    assert receipt["config_sha256"] == digest(directory / "config.json")
    for record in (config, receipt):
        assert pd.Timestamp(record["minimum_ts"]) == rows.ts.min()
        assert pd.Timestamp(record["maximum_ts"]) == rows.ts.max()
    delta = np.clip(prediction, -.15, .15)
    original_loss = float(weight @ np.abs(residual-delta))
    clipped_loss = float(weight @ np.abs(target-delta))
    constant = float(weight @ np.abs(residual-target))
    np.testing.assert_allclose(original_loss, clipped_loss+constant, rtol=1e-12, atol=1e-9)
    for field, expected in (("original_bounded_loss", original_loss), ("clipped_label_loss", clipped_loss), ("label_only_constant", constant)):
        np.testing.assert_allclose(receipt[field], expected, rtol=1e-12, atol=1e-9)
    certificate = dict(fit=name, rows=len(rows), model_sha256=digest(directory / "model.joblib"),
        fit_targets_weights_reconstructed=True, native_training_replay_exact=True,
        tree_algebra_max_difference=error, iterations=100, model_refits=0)
    return model, certificate


def expected_prediction(frame, model):
    raw, error = replay(model, frame)
    delta = np.clip(raw, -.15, .15)
    factor = 1 + .5 * delta
    before = frame.p_reference.to_numpy() * factor
    prediction = np.clip(before, 0, frame.static_capacity.to_numpy())
    prediction[frame.night.to_numpy(dtype=bool)] = 0.
    assert (factor >= .925).all() and (factor <= 1.075).all()
    return prediction, factor, delta, raw, before, error


def main():
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = read(OUT / "protocol.json")
    assert protocol["arm"] == "shallow_weather_residual"
    assert protocol["features"] == FEATURES and protocol["parameters"] == PARAMETERS
    assert protocol["delta_bounds"] == [-.15,.15] and protocol["shrink_once"] == .5
    assert protocol["target"] == "clip(y/p_reference-1,-.15,.15)" and protocol["feature_imputation"] == "none"
    assert protocol["fit_names"] == ["primary", "early"] and protocol["real_model_fit_budget"] == 2
    assert pd.Timestamp(protocol["early_cutoff"]) == CUTOFF
    assert protocol["omp_threads"] == 4 and protocol["blas_threads"] == protocol["parallel_fits"] == 1
    assert protocol["all_history_exposed"] and protocol["primary_fit_partly_in_sample"]
    assert not protocol["confirmation_loaded"] and not protocol["test_loaded"]
    assert "baseline weather coefficients used full PRIMARY" in protocol["diagnostic_limitation"]
    for name, expected in protocol["source_sha256"].items():
        assert digest(ROOT / name) == digest(OUT / "sources" / Path(name).name) == expected
    for name, expected in protocol["inputs_sha256"].items():
        assert digest(SOURCE.parent / name) == expected, name
    for name, expected in read(OUT / "prepared_manifest.json").items():
        assert digest(OUT / name) == expected, name
    terminal = read(OUT / "terminal_manifest.json")
    for name, expected in terminal.items():
        assert digest(OUT / name) == expected, name
    assert digest(ROOT / protocol["best_zip"]) == protocol["best_zip_sha256"] == "ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434"
    independent = OUT.parent / "independent_input_check.json"
    assert digest(independent) == protocol["independent_input_check_sha256"] and read(independent)["status"] == "PASS"
    preparation = read(OUT / "preparation.json")
    assert preparation["status"] == "PASS" and preparation["actual_model_fits"] == 0
    assert not preparation["primary_targets_loaded"] and not preparation["recent_targets_loaded"]
    assert read(OUT / "self_check.json")["status"] == "PASS"
    assert sorted(p.name for p in (OUT / "fits").iterdir() if p.is_dir()) == ["early", "primary"]
    originals = {fold: original_fold(fold) for fold in ("primary", "recent")}
    model, primary_certificate = verify_fit("primary", originals["primary"])
    early_model, early_certificate = verify_fit("early", originals["primary"])
    intervals = read(OUT / "fit_intervals.json")
    assert len(intervals) == 2
    assert intervals[0] == read(OUT / "fits/primary/receipt.json")
    assert intervals[1] == read(OUT / "fits/early/receipt.json")
    assert datetime.fromisoformat(intervals[0]["finished_utc"]) <= datetime.fromisoformat(intervals[1]["started_utc"])
    for interval in intervals:
        assert datetime.fromisoformat(interval["started_utc"]) <= datetime.fromisoformat(interval["finished_utc"])
    fixed = read(OUT / "predictions_fixed.json")
    assert not fixed["recent_targets_loaded"] and fixed["all_saved_model_predictions_replay_exact"]
    assert fixed["full_model_sha256"] == digest(OUT / "fits/primary/model.joblib")
    assert fixed["early_model_sha256"] == digest(OUT / "fits/early/model.joblib")
    assert datetime.fromisoformat(intervals[1]["finished_utc"]) <= datetime.fromisoformat(fixed["utc"])
    label_loads = read(OUT / "label_loads.json")
    assert len(label_loads) == 1 and label_loads[0]["fold"] == "recent"
    assert datetime.fromisoformat(label_loads[0]["loaded_utc"]) >= datetime.fromisoformat(fixed["utc"])
    assert label_loads[0]["predictions_fixed_sha256"] == digest(OUT / "predictions_fixed.json")
    scores, replay_errors = {}, {}
    for fold in ("primary", "recent", "diagnostic"):
        original = originals[fold] if fold != "diagnostic" else originals["primary"].loc[originals["primary"].ts > CUTOFF].reset_index(drop=True)
        estimator = model if fold != "diagnostic" else early_model
        expected, factor, delta, raw, before, error = expected_prediction(original, estimator)
        replay_errors[fold] = error
        application_path = OUT / fold / "application_predictions.parquet"
        assert digest(application_path) == fixed["hashes"][fold]
        application = pd.read_parquet(application_path)
        assert list(application) == [*INPUT_COLUMNS, "raw_delta", "delta", "effective_factor", "before_capacity_clip", "p"]
        equal_keys(application, original)
        for name in INPUT_COLUMNS[2:]:
            np.testing.assert_array_equal(application[name], original[name])
        for name, values in (("raw_delta", raw), ("delta", delta), ("effective_factor", factor),
                             ("before_capacity_clip", before), ("p", expected)):
            np.testing.assert_array_equal(application[name], values)
        assert application.loc[application.night, "p"].eq(0.).all()
        assert (application.p >= 0).all() and (application.p <= application.static_capacity).all()
        combined = pd.read_parquet(OUT / fold / "predictions.parquet")
        pd.testing.assert_frame_equal(combined[list(application)], application, check_exact=True)
        for name in ("y", "smp", "k"):
            np.testing.assert_array_equal(combined[name], original[name])
        scores[fold] = {name: metric(combined, name) for name in ("p", "p_reference")}
        saved = read(OUT / fold / "metrics.json")
        if fold == "diagnostic":
            assert not saved["used_for_adoption"] and saved["baseline_already_exposed"]
            assert pd.Timestamp(saved["correction_training_end"]) == CUTOFF
            assert pd.Timestamp(saved["evaluation_start"]) == combined.ts.min()
            assert pd.Timestamp(saved["evaluation_end"]) == combined.ts.max()
            saved = saved["scores"]
        for name, values in scores[fold].items():
            for key, value in values.items():
                np.testing.assert_allclose(saved[name][key], value, rtol=1e-12, atol=1e-4)
    result = read(OUT / "results.json")
    both = all(scores[f]["p"]["W"] < scores[f]["p_reference"]["W"] for f in ("primary", "recent"))
    assert result["eligible"] == result["both_folds_improve"] == both
    assert result["real_calibration_fit_count"] == result["real_residual_fit_count"] == 2
    assert result["real_generation_fit_count"] == result["real_alpha_fit_count"] == 0
    assert not result["diagnostic_used_for_adoption"]
    assert result["all_history_exposed"] and result["primary_fit_partly_in_sample"]
    assert result["recent_predictions_fixed_before_target_load"]
    assert not any(result[name] for name in ("confirmation_loaded", "test_loaded", "exported"))
    for fold in ("primary", "recent"):
        assert result["scores"][fold] == read(OUT / fold / "metrics.json")
    assert result["diagnostic_scores"] == read(OUT / "diagnostic/metrics.json")["scores"]
    completed = read(OUT / "completed.json")
    assert completed["real_residual_fit_count"] == 2 and completed["best_zip_unchanged"] and completed["prepared_inputs_unchanged"]
    evidence = dict(status="PASS", checked_utc=datetime.now(timezone.utc).isoformat(),
        fits=[primary_certificate, early_certificate], scores=scores, eligible=both,
        rows_replayed={fold: len(pd.read_parquet(OUT / fold / "predictions.parquet")) for fold in scores},
        maximum_tree_algebra_error=replay_errors, model_refits=0, generation_fits=0,
        all_prediction_rows_reconstructed=True, recent_prediction_seal_checked=True,
        original_inputs_and_best_zip_unchanged=True, terminal_manifest_sha256=digest(OUT / "terminal_manifest.json"),
        verifier_sha256=digest(__file__),
        limits="All history exposed; full-primary fit partly in-sample. Early residual diagnostic uses a baseline already calibrated on full PRIMARY; not an independent holdout or official score.")
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(evidence, indent=2, allow_nan=False), flush=True)


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
