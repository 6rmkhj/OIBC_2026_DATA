"""A fixed shallow weather residual calibrator on the immutable strong baseline.

--prepare performs no model fits. --run performs exactly two serial fits:
full PRIMARY for adoption and early PRIMARY for a descriptive forward check.
"""
from __future__ import annotations

import argparse
import fcntl
import os
from pathlib import Path
import shutil
import time
import warnings

os.environ.update(OMP_NUM_THREADS="4", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
                  NUMEXPR_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")

import joblib
import numpy as np
import pandas as pd
import pyarrow as pa
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from shift_linux import (ROOT, POISSON, FOLDS, KEYS, EXPECTED_REFERENCE, sha, read,
                        save, now, assert_keys, check_hashes, metric, historical_hashes)

OUT = ROOT / "analysis_outputs/renew_20261107/weather_residual"
FEATURES = ["wa_cloud", "wb_cloud", "cosz", "wa_temp", "wa_humidity", "wb_rel_hum"]
INPUT_COLUMNS = [*KEYS, "p_reference", *FEATURES, "static_capacity", "night"]
SHRINK, DELTA_LIMIT = .5, .15
EARLY_CUTOFF = pd.Timestamp("2024-02-01", tz="Asia/Seoul")
PARAMS = dict(loss="absolute_error", learning_rate=.03, max_iter=100, max_leaf_nodes=4,
    max_depth=2, min_samples_leaf=300, l2_regularization=10., max_bins=32,
    early_stopping=False, random_state=0)


def apply_delta(inputs, raw_delta):
    """Apply only forecast inputs and a bounded supplemental multiplicative delta."""
    assert list(inputs) == INPUT_COLUMNS, "No labels or prices allowed in application"
    assert not inputs.duplicated(KEYS).any() and inputs.ts.notna().all()
    raw_delta = np.asarray(raw_delta, dtype=np.float64)
    assert raw_delta.shape == (len(inputs),) and np.isfinite(raw_delta).all()
    reference = inputs.p_reference.to_numpy(dtype=np.float64)
    capacity = inputs.static_capacity.to_numpy(dtype=np.float64)
    assert np.isfinite(reference).all() and np.isfinite(capacity).all()
    assert (reference >= 0).all() and (capacity > 0).all() and (reference <= capacity + 1e-8).all()
    assert inputs.night.notna().all()
    delta = np.clip(raw_delta, -DELTA_LIMIT, DELTA_LIMIT)
    factor = 1 + SHRINK * delta
    before_cap = reference * factor
    prediction = np.clip(before_cap, 0, capacity)
    prediction[inputs.night.to_numpy(dtype=bool)] = 0.
    return inputs.assign(raw_delta=raw_delta, delta=delta, effective_factor=factor,
                         before_capacity_clip=before_cap, p=prediction)


def apply_residual(inputs, model):
    assert list(inputs) == INPUT_COLUMNS
    assert model.feature_names_in_.tolist() == FEATURES
    assert not np.isinf(inputs[FEATURES].to_numpy(dtype=float)).any()
    return apply_delta(inputs, model.predict(inputs[FEATURES]))


def fit_rows(inputs, labels):
    assert_keys(inputs, labels)
    frame = inputs.merge(labels[[*KEYS, "y", "smp", "k"]], on=KEYS, sort=False, validate="one_to_one")
    assert_keys(frame, inputs)
    assert np.isfinite(frame[["p_reference", "y", "smp", "k"]].to_numpy()).all()
    assert frame.p_reference.ge(0).all() and frame.smp.ge(0).all() and frame.k.ge(0).all()
    monetary = (frame.smp * frame.k).to_numpy()
    active = frame.p_reference.gt(0).to_numpy() & (monetary > 0)
    rows = frame.loc[active, [*KEYS, "p_reference", "y", "smp", "k", *FEATURES]].copy()
    assert len(rows) > 0 and not np.isinf(rows[FEATURES].to_numpy(dtype=float)).any()
    rows["ratio_residual"] = rows.y.to_numpy() / rows.p_reference.to_numpy() - 1
    rows["target_clipped"] = np.clip(rows.ratio_residual, -DELTA_LIMIT, DELTA_LIMIT)
    rows["monetary_prediction_weight"] = (rows.smp * rows.k * rows.p_reference).to_numpy()
    rows["sample_weight"] = rows.monetary_prediction_weight / rows.monetary_prediction_weight.mean()
    assert np.isfinite(rows[["ratio_residual", "target_clipped", "sample_weight"]].to_numpy()).all()
    assert rows.sample_weight.gt(0).all()
    np.testing.assert_allclose(rows.sample_weight.mean(), 1., rtol=1e-14)
    return rows.reset_index(drop=True)


def self_check():
    # For any bounded decision, clipping the label only subtracts a constant.
    raw = np.array([-10., -.3, -.15, -.01, 0., .03, .15, .4, 20.])
    target = np.clip(raw, -DELTA_LIMIT, DELTA_LIMIT)
    for delta in (-.15, -.07, 0., .08, .15):
        np.testing.assert_allclose(np.abs(raw - delta), np.abs(target - delta) + np.abs(raw - target), rtol=1e-14, atol=1e-14)
    inputs = pd.DataFrame(dict(ts=pd.date_range("2024-01-01", periods=5, freq="h", tz="Asia/Seoul"),
        grp="G1", p_reference=[100., 100., 100., 0., 100.], static_capacity=103., night=[False, False, False, True, True]))
    for name in FEATURES:
        inputs[name] = [1., np.nan, 3., np.nan, 5.]
    inputs = inputs[INPUT_COLUMNS]
    applied = apply_delta(inputs, [-2., .10, .80, .15, .15])
    np.testing.assert_array_equal(applied.delta, [-.15, .1, .15, .15, .15])
    np.testing.assert_allclose(applied.p, [92.5, 103., 103., 0., 0.], rtol=0, atol=1e-12)
    labels = inputs[KEYS].assign(y=[105., 90., 115., 0., 95.], smp=[1., 2., 0., 1., 0.], k=1.)
    rows = fit_rows(inputs, labels)
    assert len(rows) == 2 and rows[FEATURES].iloc[1].isna().all()
    np.testing.assert_array_equal(rows.sample_weight, [2/3, 4/3])
    np.testing.assert_allclose(rows.target_clipped, [.05, -.1], atol=1e-15, rtol=0)
    scaled = fit_rows(inputs, labels.assign(smp=labels.smp * 17))
    np.testing.assert_array_equal(scaled.sample_weight, rows.sample_weight)
    try:
        apply_delta(inputs.assign(y=999.), np.zeros(5))
    except AssertionError:
        pass
    else:
        raise AssertionError("Label input accepted")
    assert not np.isclose(1 + SHRINK * SHRINK * .1, applied.effective_factor.iloc[1])
    return dict(status="PASS", actual_model_fits=0, tests=["bounded-decision LAD target-clipping equivalence",
        "active p/monetary mask", "native NaNs retained", "mean1 weight scale invariance",
        "delta bounds then single shrink", "capacity/night handling", "label rejection", "double-shrink mutation rejected"])


def prepare():
    assert not OUT.exists(), "Preserve prior residual experiment"
    old = {k.replace("\\", "/"): v for k, v in read(POISSON / "prepared_manifest.json").items()}
    names = [f"data/{fold}/{name}" for fold in FOLDS for name in
             ("application_inputs.parquet", "labels.parquet", "coverage.parquet", "evaluation.parquet")]
    lineage = historical_hashes(POISSON, {name: old[name] for name in names})
    current = {name: sha(POISSON / name) for name in names}
    best = ROOT / "submission/renew_candidate_20261105/submission_files.zip"
    assert sha(best) == "ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434"
    independent = OUT.parent / "independent_input_check.json"
    assert read(independent)["status"] == "PASS"
    OUT.mkdir(parents=True)
    (OUT / "sources").mkdir()
    sources = {}
    for source in (Path(__file__), Path(__file__).with_name("shift_linux.py")):
        shutil.copyfile(source, OUT / "sources" / source.name)
        sources[str(source.relative_to(ROOT))] = sha(source)
    save(OUT / "protocol.json", dict(created_utc=now(), arm="shallow_weather_residual", features=FEATURES,
        parameters=PARAMS, delta_bounds=[-DELTA_LIMIT, DELTA_LIMIT], shrink_once=SHRINK,
        target="clip(y/p_reference-1,-.15,.15)", weights="SMP*k*p_reference divided by active-row mean",
        fit_active="p_reference>0 and SMP*k>0; keep native weather NaNs", feature_imputation="none",
        label_clipping_proof="For each final bounded delta: abs(r-delta)=abs(clip(r)-delta)+abs(r-clip(r)); second term does not depend on delta",
        fit_names=["primary", "early"], real_model_fit_budget=2, early_cutoff=str(EARLY_CUTOFF),
        adoption_rule="full-primary model strictly improves W on primary and recent; no alpha or parameter tuning",
        diagnostic="fit only PRIMARY ts<=2024-02-01; descriptive later PRIMARY; does not gate adoption",
        diagnostic_limitation="Only supplemental model is chronological; baseline weather coefficients used full PRIMARY",
        historical_duplicate_check="Earlier HGB models directly predicted CF; no prior six-feature bounded residual calibrator found",
        inputs_sha256=current, historical_lineage=lineage, source_sha256=sources,
        independent_input_check_sha256=sha(independent), best_zip=str(best.relative_to(ROOT)), best_zip_sha256=sha(best),
        versions=dict(numpy=np.__version__, pandas=pd.__version__, sklearn=sklearn.__version__, joblib=joblib.__version__),
        omp_threads=4, blas_threads=1, parallel_fits=1, all_history_exposed=True,
        primary_fit_partly_in_sample=True, recent_targets_loaded_during_preparation=False,
        confirmation_loaded=False, test_loaded=False))
    save(OUT / "self_check.json", self_check())
    receipts = []
    for fold in FOLDS:
        source = POISSON / "data" / fold
        directory = OUT / "data" / fold
        directory.mkdir(parents=True)
        reference = pd.read_parquet(source / "labels.parquet", columns=[*KEYS, "p_reference"])
        capacity = pd.read_parquet(source / "application_inputs.parquet", columns=[*KEYS, "static_capacity"])
        coverage = pd.read_parquet(source / "coverage.parquet")
        weather = pd.read_parquet(source / "evaluation.parquet", columns=[*KEYS, *FEATURES])
        assert_keys(reference, capacity)
        assert_keys(reference, coverage)
        assert not weather.duplicated(KEYS).any()
        joined = reference.merge(capacity, on=KEYS, sort=False, validate="one_to_one").merge(
            coverage, on=KEYS, sort=False, validate="one_to_one").merge(
            weather, on=KEYS, how="left", sort=False, validate="one_to_one", indicator=True)
        assert_keys(joined, reference)
        assert joined._merge.eq("left_only").eq(joined.night).all()
        assert joined.loc[joined.night, "p_reference"].eq(0).all()
        assert not np.isinf(joined[FEATURES].to_numpy()).any()
        joined = joined[INPUT_COLUMNS]
        joined.to_parquet(directory / "inputs.parquet", index=False)
        np.testing.assert_array_equal(apply_delta(joined, np.zeros(len(joined))).p, reference.p_reference)
        receipts.append(dict(fold=fold, rows=len(joined), night_rows=int(joined.night.sum()),
            native_nan_count=int(joined[FEATURES].isna().sum().sum()), target_columns_read=False))
    check_hashes(POISSON, current)
    save(OUT / "preparation.json", dict(status="PASS", records=receipts, actual_model_fits=0,
        recent_targets_loaded=False, primary_targets_loaded=False))
    save(OUT / "prepared_manifest.json", {str(p.relative_to(OUT)): sha(p) for p in sorted((OUT / "data").rglob("*")) if p.is_file()})
    print("WEATHER RESIDUAL PREPARED", receipts, flush=True)


def fit_residual(name, inputs, labels):
    directory = OUT / "fits" / name
    directory.mkdir(parents=True, exist_ok=False)
    rows = fit_rows(inputs, labels)
    rows.to_parquet(directory / "fit_rows.parquet", index=False)
    save(directory / "config.json", dict(parameters=PARAMS, features=FEATURES, target="target_clipped",
        sample_weight="sample_weight", fit_name=name, shrink=SHRINK, delta_bounds=[-DELTA_LIMIT, DELTA_LIMIT],
        fit_rows_sha256=sha(directory / "fit_rows.parquet"), input_schema=INPUT_COLUMNS,
        minimum_ts=str(rows.ts.min()), maximum_ts=str(rows.ts.max()), rows=len(rows)))
    started, tick = now(), time.monotonic()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model = HistGradientBoostingRegressor(**PARAMS)
        model.fit(rows[FEATURES], rows.target_clipped.to_numpy(), sample_weight=rows.sample_weight.to_numpy())
    assert model.n_iter_ == 100 and not model.do_early_stopping_
    assert model.feature_names_in_.tolist() == FEATURES
    joblib.dump(model, directory / "model.joblib")
    raw_delta = model.predict(rows[FEATURES])
    assert np.isfinite(raw_delta).all()
    restored = joblib.load(directory / "model.joblib")
    np.testing.assert_array_equal(restored.predict(rows[FEATURES]), raw_delta)
    delta = np.clip(raw_delta, -DELTA_LIMIT, DELTA_LIMIT)
    rows[KEYS].assign(raw_delta=raw_delta, delta=delta).to_parquet(directory / "training_predictions.parquet", index=False)
    original_loss = float((rows.sample_weight.to_numpy() * np.abs(rows.ratio_residual.to_numpy() - delta)).sum())
    clipped_loss = float((rows.sample_weight.to_numpy() * np.abs(rows.target_clipped.to_numpy() - delta)).sum())
    constant = float((rows.sample_weight.to_numpy() * np.abs(rows.ratio_residual.to_numpy() - rows.target_clipped.to_numpy())).sum())
    np.testing.assert_allclose(original_loss, clipped_loss + constant, rtol=1e-12, atol=1e-10)
    record = dict(name=name, started_utc=started, finished_utc=now(), seconds=time.monotonic() - tick,
        pid=os.getpid(), fit_count=1, iterations=int(model.n_iter_), input_rows=len(inputs), active_rows=len(rows),
        minimum_ts=str(rows.ts.min()), maximum_ts=str(rows.ts.max()), native_replay_exact=True,
        warnings=[dict(category=w.category.__name__, message=str(w.message)) for w in caught],
        original_bounded_loss=original_loss, clipped_label_loss=clipped_loss, label_only_constant=constant,
        model_sha256=sha(directory / "model.joblib"), config_sha256=sha(directory / "config.json"))
    save(directory / "receipt.json", record)
    print("WEATHER RESIDUAL FIT COMPLETE", name, record["seconds"], flush=True)
    return model, record


def run():
    assert not (OUT / "results.json").exists(), "Preserve completed experiment"
    protocol = read(OUT / "protocol.json")
    check_hashes(ROOT, protocol["source_sha256"])
    check_hashes(POISSON, protocol["inputs_sha256"])
    check_hashes(OUT, read(OUT / "prepared_manifest.json"))
    assert read(OUT / "preparation.json")["status"] == "PASS"
    inputs = {fold: pd.read_parquet(OUT / "data" / fold / "inputs.parquet") for fold in FOLDS}
    labels_primary = pd.read_parquet(POISSON / "data" / "primary" / "labels.parquet", columns=[*KEYS, "y", "smp", "k"])
    assert_keys(inputs["primary"], labels_primary)
    model, full_record = fit_residual("primary", inputs["primary"], labels_primary)
    early = inputs["primary"].ts.le(EARLY_CUTOFF).to_numpy()
    early_model, early_record = fit_residual("early", inputs["primary"].loc[early].reset_index(drop=True),
        labels_primary.loc[early].reset_index(drop=True))
    assert full_record["finished_utc"] <= early_record["started_utc"]
    save(OUT / "fit_intervals.json", [full_record, early_record])
    predictions, hashes = {}, {}
    saved = joblib.load(OUT / "fits/primary/model.joblib")
    for fold in FOLDS:
        directory = OUT / fold
        directory.mkdir(exist_ok=False)
        predictions[fold] = apply_residual(inputs[fold], model)
        replay = apply_residual(inputs[fold], saved)
        pd.testing.assert_frame_equal(predictions[fold], replay, check_exact=True)
        predictions[fold].to_parquet(directory / "application_predictions.parquet", index=False)
        hashes[fold] = sha(directory / "application_predictions.parquet")
    (OUT / "diagnostic").mkdir(exist_ok=False)
    diagnostic = apply_residual(inputs["primary"].loc[~early].reset_index(drop=True), early_model)
    replay = apply_residual(inputs["primary"].loc[~early].reset_index(drop=True), joblib.load(OUT / "fits/early/model.joblib"))
    pd.testing.assert_frame_equal(diagnostic, replay, check_exact=True)
    diagnostic.to_parquet(OUT / "diagnostic" / "application_predictions.parquet", index=False)
    hashes["diagnostic"] = sha(OUT / "diagnostic" / "application_predictions.parquet")
    save(OUT / "predictions_fixed.json", dict(utc=now(), hashes=hashes, recent_targets_loaded=False,
        full_model_sha256=sha(OUT / "fits/primary/model.joblib"), early_model_sha256=sha(OUT / "fits/early/model.joblib"),
        all_saved_model_predictions_replay_exact=True))
    scores, label_loads = {}, []
    for fold in FOLDS:
        if fold == "primary":
            labels = labels_primary
        else:
            label_loads.append(dict(fold=fold, loaded_utc=now(), predictions_fixed_sha256=sha(OUT / "predictions_fixed.json")))
            labels = pd.read_parquet(POISSON / "data" / fold / "labels.parquet", columns=[*KEYS, "y", "smp", "k"])
        assert_keys(predictions[fold], labels)
        frame = predictions[fold].merge(labels, on=KEYS, sort=False, validate="one_to_one")
        assert_keys(frame, predictions[fold])
        frame.to_parquet(OUT / fold / "predictions.parquet", index=False)
        scores[fold] = {name: metric(frame, name) for name in ("p", "p_reference")}
        assert abs(scores[fold]["p_reference"]["W_pct"] - EXPECTED_REFERENCE[fold]) < 1e-10
        save(OUT / fold / "metrics.json", scores[fold])
        assert sha(OUT / fold / "application_predictions.parquet") == hashes[fold]
    diagnostic_labels = labels_primary.loc[~early].reset_index(drop=True)
    assert_keys(diagnostic, diagnostic_labels)
    diagnostic = diagnostic.merge(diagnostic_labels, on=KEYS, sort=False, validate="one_to_one")
    diagnostic.to_parquet(OUT / "diagnostic" / "predictions.parquet", index=False)
    diagnostic_scores = {name: metric(diagnostic, name) for name in ("p", "p_reference")}
    save(OUT / "diagnostic/metrics.json", dict(scores=diagnostic_scores, used_for_adoption=False,
        correction_training_end=str(EARLY_CUTOFF), evaluation_start=str(diagnostic.ts.min()),
        evaluation_end=str(diagnostic.ts.max()), baseline_already_exposed=True))
    both = all(scores[fold]["p"]["W"] < scores[fold]["p_reference"]["W"] for fold in FOLDS)
    result = dict(arm="shallow_weather_residual", scores=scores, eligible=both, both_folds_improve=both,
        diagnostic_scores=diagnostic_scores, diagnostic_used_for_adoption=False, real_calibration_fit_count=2,
        real_residual_fit_count=2, real_generation_fit_count=0, real_alpha_fit_count=0,
        all_history_exposed=True, primary_fit_partly_in_sample=True,
        recent_predictions_fixed_before_target_load=True, confirmation_loaded=False, test_loaded=False, exported=False)
    save(OUT / "label_loads.json", label_loads)
    save(OUT / "results.json", result)
    check_hashes(ROOT, protocol["source_sha256"])
    check_hashes(POISSON, protocol["inputs_sha256"])
    check_hashes(OUT, read(OUT / "prepared_manifest.json"))
    assert sha(ROOT / protocol["best_zip"]) == protocol["best_zip_sha256"]
    save(OUT / "completed.json", dict(utc=now(), pid=os.getpid(), real_residual_fit_count=2,
        best_zip_unchanged=True, prepared_inputs_unchanged=True))
    save(OUT / "terminal_manifest.json", {str(p.relative_to(OUT)): sha(p) for p in sorted(OUT.rglob("*"))
        if p.is_file() and p.name not in {"controller.lock", "terminal_manifest.json", "run.log", "prepare.log"}})
    print(result, flush=True)


def main():
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare", action="store_true")
    action.add_argument("--run", action="store_true")
    action.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    pa.set_cpu_count(2)
    pa.set_io_thread_count(2)
    with threadpool_limits(limits=1, user_api="blas"), threadpool_limits(limits=4, user_api="openmp"):
        if args.prepare:
            prepare()
        elif args.self_check:
            print(self_check())
        else:
            with (OUT / "controller.lock").open("a+b") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                run()


if __name__ == "__main__":
    main()
