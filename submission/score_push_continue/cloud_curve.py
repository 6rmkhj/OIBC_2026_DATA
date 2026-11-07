"""Two fixed, serial weighted-LAD cloud calibrations with complete LP evidence.

--prepare freezes inputs and tests algebra without fitting. --run fits the full
PRIMARY curve and one early-PRIMARY descriptive curve. Only the full curve is
eligible for adoption; recent labels are read after its predictions are sealed.
"""
from __future__ import annotations

import argparse
import fcntl
import os
from pathlib import Path
import shutil
import time
import warnings

os.environ.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
                  NUMEXPR_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")

import numpy as np
import pandas as pd
import pyarrow as pa
import scipy
from scipy import sparse
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits

from shift_linux import (ROOT, POISSON, FOLDS, KEYS, EXPECTED_REFERENCE, sha, read,
                        save, now, assert_keys, check_hashes, metric, historical_hashes)

os.environ["OMP_NUM_THREADS"] = "1"
OUT = ROOT / "analysis_outputs/renew_20261107/cloud_curve"
KNOTS = np.array([0., 25., 50., 75., 100.])
SECOND_DIFFERENCE = np.array([[1., -2., 1., 0., 0.], [0., 1., -2., 1., 0.], [0., 0., 1., -2., 1.]])
SHRINK = .5
PENALTY = .01
DELTA_LIMIT = .15
EARLY_CUTOFF = pd.Timestamp("2024-02-01", tz="Asia/Seoul")
INPUT_COLUMNS = [*KEYS, "p_reference", "wb_cloud", "static_capacity", "night"]
SOLVER_OPTIONS = dict(threads=1, presolve=True, primal_feasibility_tolerance=1e-9,
                      dual_feasibility_tolerance=1e-9, ipm_optimality_tolerance=1e-10)


def basis(cloud):
    """Linear hat basis; missing inputs produce zero adjustment, endpoints clamp."""
    cloud = np.asarray(cloud, dtype=np.float64)
    assert cloud.ndim == 1
    finite = np.isfinite(cloud)
    result = np.zeros((len(cloud), len(KNOTS)), dtype=np.float64)
    clipped = np.clip(cloud[finite], KNOTS[0], KNOTS[-1])
    left = np.clip(np.searchsorted(KNOTS, clipped, side="right") - 1, 0, len(KNOTS) - 2)
    fraction = (clipped - KNOTS[left]) / (KNOTS[left + 1] - KNOTS[left])
    row = np.flatnonzero(finite)
    result[row, left] = 1 - fraction
    result[row, left + 1] = fraction
    assert (result >= 0).all()
    np.testing.assert_array_equal(result.sum(axis=1), finite.astype(float))
    return result


def apply_curve(inputs, delta):
    """Export-compatible application: only baseline and provided cloud are used."""
    assert list(inputs) == INPUT_COLUMNS, "Application accepts only declared inputs, never labels"
    assert not inputs.duplicated(KEYS).any() and inputs.ts.notna().all()
    delta = np.asarray(delta, dtype=np.float64)
    assert delta.shape == (5,) and np.isfinite(delta).all()
    assert np.max(np.abs(delta)) <= DELTA_LIMIT + 1e-10
    reference = inputs.p_reference.to_numpy(dtype=float)
    capacity = inputs.static_capacity.to_numpy(dtype=float)
    night = inputs.night.to_numpy(dtype=bool)
    assert inputs.night.notna().all() and np.isfinite(reference).all() and np.isfinite(capacity).all()
    assert (reference >= 0).all() and (capacity > 0).all() and (reference <= capacity + 1e-8).all()
    adjustment = basis(inputs.wb_cloud.to_numpy()) @ delta
    factor = 1 + SHRINK * adjustment
    before_cap = reference * factor
    prediction = np.clip(before_cap, 0, capacity)
    prediction[night] = 0.
    assert np.isfinite(prediction).all() and (prediction >= 0).all() and (prediction <= capacity).all()
    return inputs.assign(delta=adjustment, effective_factor=factor, before_capacity_clip=before_cap, p=prediction)


def active_rows(inputs, labels):
    assert_keys(inputs, labels)
    frame = inputs.merge(labels[[*KEYS, "y", "smp", "k"]], on=KEYS, sort=False, validate="one_to_one")
    assert_keys(frame, inputs)
    assert np.isfinite(frame[["p_reference", "y", "smp", "k"]].to_numpy()).all()
    assert frame.p_reference.ge(0).all() and frame.smp.ge(0).all() and frame.k.ge(0).all()
    monetary = (frame.smp * frame.k).to_numpy()
    mask = np.isfinite(frame.wb_cloud.to_numpy()) & frame.p_reference.gt(0).to_numpy() & (monetary > 0)
    rows = frame.loc[mask, [*KEYS, "p_reference", "y", "smp", "k", "wb_cloud"]].copy()
    rows["ratio_residual"] = rows.y.to_numpy() / rows.p_reference.to_numpy() - 1
    rows["monetary_prediction_weight"] = (rows.smp * rows.k * rows.p_reference).to_numpy()
    mass = rows.monetary_prediction_weight.sum()
    assert mass > 0 and len(rows) > 0
    rows["normalized_weight"] = rows.monetary_prediction_weight / mass
    assert np.isfinite(rows[["ratio_residual", "normalized_weight"]].to_numpy()).all()
    np.testing.assert_allclose(rows.normalized_weight.sum(), 1., rtol=1e-14)
    return rows.reset_index(drop=True)


def lp_problem(rows):
    """Variables: delta5, residual_absN, delta_abs5, curvature_abs3."""
    n = len(rows)
    hats = sparse.csr_matrix(basis(rows.wb_cloud.to_numpy()))
    eye_n, eye_5, eye_3 = sparse.eye(n, format="csr"), sparse.eye(5, format="csr"), sparse.eye(3, format="csr")
    z_n5, z_n3 = sparse.csr_matrix((n, 5)), sparse.csr_matrix((n, 3))
    z_5n, z_53 = sparse.csr_matrix((5, n)), sparse.csr_matrix((5, 3))
    z_3n, z_35 = sparse.csr_matrix((3, n)), sparse.csr_matrix((3, 5))
    d2 = sparse.csr_matrix(SECOND_DIFFERENCE)
    matrix = sparse.vstack([
        sparse.hstack([hats, -eye_n, z_n5, z_n3]),
        sparse.hstack([-hats, -eye_n, z_n5, z_n3]),
        sparse.hstack([eye_5, z_5n, -eye_5, z_53]),
        sparse.hstack([-eye_5, z_5n, -eye_5, z_53]),
        sparse.hstack([d2, z_3n, z_35, -eye_3]),
        sparse.hstack([-d2, z_3n, z_35, -eye_3]),
    ], format="csr")
    residual = rows.ratio_residual.to_numpy(dtype=float)
    rhs = np.concatenate([residual, -residual, np.zeros(16)])
    objective = np.concatenate([np.zeros(5), rows.normalized_weight.to_numpy(dtype=float),
                                np.full(5, PENALTY / 5), np.full(3, PENALTY / 3)])
    lower = np.concatenate([np.full(5, -DELTA_LIMIT), np.zeros(n + 8)])
    upper = np.concatenate([np.full(5, DELTA_LIMIT), np.full(n + 8, np.inf)])
    assert matrix.shape == (2 * n + 16, n + 13)
    return objective, matrix, rhs, lower, upper


def self_check():
    clouds = np.array([-10., 0., 12.5, 25., 50., 75., 100., 110., np.nan, np.inf, -np.inf])
    hats = basis(clouds)
    np.testing.assert_array_equal(hats[1:8:2], np.eye(5)[[0, 1, 3, 4]])
    np.testing.assert_array_equal(hats[2], [.5, .5, 0., 0., 0.])
    np.testing.assert_array_equal(hats[8:], np.zeros((3, 5)))
    inputs = pd.DataFrame(dict(ts=pd.date_range("2024-01-01", periods=len(clouds), freq="h", tz="Asia/Seoul"),
        grp="G1", p_reference=100., wb_cloud=clouds, static_capacity=103., night=False))[INPUT_COLUMNS]
    inputs.loc[0, "night"] = True
    applied = apply_curve(inputs, np.full(5, .10))
    np.testing.assert_array_equal(applied.p, [0., 103., 103., 103., 103., 103., 103., 103., 100., 100., 100.])
    np.testing.assert_allclose(applied.effective_factor.iloc[1:8], 1.05, atol=1e-15, rtol=0)
    try:
        apply_curve(inputs.assign(y=1e9), np.zeros(5))
    except AssertionError:
        pass
    else:
        raise AssertionError("Label-bearing application was accepted")
    labels = inputs[KEYS].assign(y=110., smp=2., k=3.)
    rows = active_rows(inputs, labels)
    c, matrix, rhs, lower, upper = lp_problem(rows)
    delta = np.full(5, .10)
    x = np.concatenate([delta, np.abs(rows.ratio_residual - basis(rows.wb_cloud) @ delta),
                        np.abs(delta), np.abs(SECOND_DIFFERENCE @ delta)])
    assert (matrix @ x <= rhs + 1e-12).all() and (x >= lower).all() and (x <= upper).all()
    np.testing.assert_allclose(c @ x, .001, atol=1e-12, rtol=0)
    duplicated = rows.copy()
    duplicated["monetary_prediction_weight"] *= 37
    duplicated["normalized_weight"] = duplicated.monetary_prediction_weight / duplicated.monetary_prediction_weight.sum()
    np.testing.assert_allclose(lp_problem(duplicated)[0], c, atol=1e-15, rtol=0)
    # Deliberate double shrink gives 1.025, which must not match the specified 1.05.
    assert not np.isclose(1 + SHRINK * SHRINK * .10, applied.effective_factor.iloc[1])
    return dict(status="PASS", actual_optimizer_fits=0, tests=["linear interpolation and clamped endpoints",
        "nonfinite identity", "single half shrink", "capacity and night zero", "labels excluded from application",
        "sparse LP synthetic primal/objective", "weight-scale invariance", "double-shrink mutation rejected"])


def prepare():
    assert not OUT.exists(), "Preserve prior cloud-curve experiment"
    original = {k.replace("\\", "/"): v for k, v in read(POISSON / "prepared_manifest.json").items()}
    names = [f"data/{fold}/{name}" for fold in FOLDS for name in
             ("application_inputs.parquet", "labels.parquet", "coverage.parquet", "evaluation.parquet")]
    historical = historical_hashes(POISSON, {name: original[name] for name in names})
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
    save(OUT / "protocol.json", dict(created_utc=now(), arm="regularized_cloud_curve", knots=KNOTS.tolist(),
        delta_bounds=[-DELTA_LIMIT, DELTA_LIMIT], shrink_once=SHRINK, coefficient_penalty=PENALTY,
        curvature_penalty=PENALTY, second_difference=SECOND_DIFFERENCE.tolist(),
        objective="sum(normalized SMP*k*p_reference * abs(y/p_reference-1-B*delta)) + .01*mean(abs(delta)) + .01*mean(abs(D2*delta))",
        fit_active="finite wb_cloud and p_reference>0 and SMP*k>0", identity_for_nonfinite_cloud=True,
        extrapolation="constant endpoint", solver="scipy.optimize.linprog(method=highs)", solver_options=SOLVER_OPTIONS,
        fit_names=["primary", "early"], real_calibration_fit_budget=2, early_cutoff=str(EARLY_CUTOFF),
        primary_fit_period="2023-06-01 < ts <= 2024-06-01 Asia/Seoul",
        adoption_rule="full-primary curve strictly improves W on primary and recent; no alpha or other selection",
        diagnostic="early curve fit on PRIMARY ts<=2024-02-01; descriptive only on remaining PRIMARY; no gating or coefficient tuning",
        diagnostic_limitation="Baseline weather coefficients were already fitted on full PRIMARY; only supplemental correction is chronological",
        inputs_sha256=current, historical_lineage=historical, source_sha256=sources,
        independent_input_check_sha256=sha(independent), best_zip=str(best.relative_to(ROOT)), best_zip_sha256=sha(best),
        versions=dict(numpy=np.__version__, pandas=pd.__version__, scipy=scipy.__version__),
        model_threads=1, blas_threads=1, all_history_exposed=True, primary_fit_partly_in_sample=True,
        recent_targets_loaded_during_preparation=False, confirmation_loaded=False, test_loaded=False))
    save(OUT / "self_check.json", self_check())
    records = []
    for fold in FOLDS:
        source = POISSON / "data" / fold
        directory = OUT / "data" / fold
        directory.mkdir(parents=True)
        reference = pd.read_parquet(source / "labels.parquet", columns=[*KEYS, "p_reference"])
        inputs = pd.read_parquet(source / "application_inputs.parquet", columns=[*KEYS, "static_capacity"])
        coverage = pd.read_parquet(source / "coverage.parquet")
        clouds = pd.read_parquet(source / "evaluation.parquet", columns=[*KEYS, "wb_cloud"])
        assert_keys(reference, inputs)
        assert_keys(reference, coverage)
        assert not clouds.duplicated(KEYS).any()
        joined = reference.merge(inputs, on=KEYS, sort=False, validate="one_to_one").merge(
            coverage, on=KEYS, sort=False, validate="one_to_one").merge(
            clouds, on=KEYS, how="left", sort=False, validate="one_to_one", indicator=True)
        assert_keys(joined, reference)
        assert joined._merge.eq("left_only").eq(joined.night).all()
        assert joined.loc[joined.night, "p_reference"].eq(0).all()
        joined = joined[INPUT_COLUMNS]
        joined.to_parquet(directory / "inputs.parquet", index=False)
        assert_keys(apply_curve(joined, np.zeros(5)), joined)
        np.testing.assert_array_equal(apply_curve(joined, np.zeros(5)).p, reference.p_reference)
        records.append(dict(fold=fold, rows=len(joined), finite_cloud_rows=int(np.isfinite(joined.wb_cloud).sum()),
            night_rows=int(joined.night.sum()), labels_projected=False, reference_projection=[*KEYS, "p_reference"]))
    check_hashes(POISSON, current)
    save(OUT / "preparation.json", dict(status="PASS", records=records, actual_optimizer_fits=0,
        recent_targets_loaded=False, primary_targets_loaded=False))
    save(OUT / "prepared_manifest.json", {str(p.relative_to(OUT)): sha(p) for p in sorted((OUT / "data").rglob("*")) if p.is_file()})
    print("CLOUD CURVE PREPARED", records, flush=True)


def fit_curve(name, inputs, labels):
    directory = OUT / "fits" / name
    directory.mkdir(parents=True, exist_ok=False)
    rows = active_rows(inputs, labels)
    rows.to_parquet(directory / "fit_rows.parquet", index=False)
    c, matrix, rhs, lower, upper = lp_problem(rows)
    np.savez(directory / "lp.npz", c=c, b_ub=rhs, lower=lower, upper=upper,
        A_data=matrix.data, A_indices=matrix.indices, A_indptr=matrix.indptr, A_shape=np.array(matrix.shape))
    started, tick = now(), time.monotonic()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        optimized = linprog(c, A_ub=matrix, b_ub=rhs, bounds=list(zip(lower, upper)), method="highs", options=SOLVER_OPTIONS)
    warning_records = [dict(category=w.category.__name__, message=str(w.message)) for w in caught]
    record = dict(name=name, success=bool(optimized.success), status=int(optimized.status), message=str(optimized.message),
        fun=None if optimized.fun is None else float(optimized.fun), nit=int(optimized.nit),
        crossover_nit=int(getattr(optimized, "crossover_nit", 0)), warnings=warning_records,
        started_utc=started, finished_utc=now(), seconds=time.monotonic() - tick, pid=os.getpid(), fit_count=1,
        input_rows=len(inputs), active_rows=len(rows), minimum_ts=str(rows.ts.min()), maximum_ts=str(rows.ts.max()))
    save(directory / "optimization.json", record)
    assert optimized.success and optimized.status == 0, record
    solution = {"x": optimized.x}
    for field in ("ineqlin", "lower", "upper", "eqlin"):
        for part in ("marginals", "residual"):
            solution[f"{field}_{part}"] = np.asarray(getattr(optimized, field)[part], dtype=float)
    np.savez(directory / "solution.npz", **solution)
    x = optimized.x
    delta = x[:5]
    np.testing.assert_allclose(c @ x, optimized.fun, rtol=1e-11, atol=1e-12)
    assert np.max(matrix @ x - rhs) < 1e-7
    assert np.max(lower - x) < 1e-7 and np.max(x - upper) < 1e-7
    stationarity = c - matrix.T @ optimized.ineqlin.marginals - optimized.lower.marginals - optimized.upper.marginals
    assert np.max(np.abs(stationarity)) < 1e-7
    finite_upper = np.isfinite(upper)
    dual = rhs @ optimized.ineqlin.marginals + lower @ optimized.lower.marginals + upper[finite_upper] @ optimized.upper.marginals[finite_upper]
    assert abs(float(dual) - optimized.fun) < 1e-7
    direct_objective = (rows.normalized_weight.to_numpy() * np.abs(rows.ratio_residual.to_numpy() - basis(rows.wb_cloud) @ delta)).sum()
    direct_objective += PENALTY * np.abs(delta).mean() + PENALTY * np.abs(SECOND_DIFFERENCE @ delta).mean()
    np.testing.assert_allclose(direct_objective, optimized.fun, rtol=1e-9, atol=1e-10)
    save(directory / "coefficients.json", dict(knots=KNOTS.tolist(), delta=delta.tolist(), shrink=SHRINK,
        input_schema=INPUT_COLUMNS, missing_identity=True, constant_endpoint_extrapolation=True,
        fit_name=name, direct_objective=float(direct_objective), dual_objective=float(dual),
        maximum_stationarity_error=float(np.max(np.abs(stationarity))), optimizer_status=0,
        fit_rows_sha256=sha(directory / "fit_rows.parquet"), lp_sha256=sha(directory / "lp.npz"),
        solution_sha256=sha(directory / "solution.npz")))
    print("CLOUD CURVE FIT COMPLETE", name, delta.tolist(), record["seconds"], flush=True)
    return delta, record


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
    full_delta, full_record = fit_curve("primary", inputs["primary"], labels_primary)
    early = inputs["primary"].ts.le(EARLY_CUTOFF).to_numpy()
    early_delta, early_record = fit_curve("early", inputs["primary"].loc[early].reset_index(drop=True),
                                        labels_primary.loc[early].reset_index(drop=True))
    assert full_record["finished_utc"] <= early_record["started_utc"]
    save(OUT / "fit_intervals.json", [full_record, early_record])
    predictions = {}
    hashes = {}
    for fold in FOLDS:
        directory = OUT / fold
        directory.mkdir(exist_ok=False)
        predictions[fold] = apply_curve(inputs[fold], full_delta)
        predictions[fold].to_parquet(directory / "application_predictions.parquet", index=False)
        hashes[fold] = sha(directory / "application_predictions.parquet")
    (OUT / "diagnostic").mkdir(exist_ok=False)
    diagnostic = apply_curve(inputs["primary"].loc[~early].reset_index(drop=True), early_delta)
    diagnostic.to_parquet(OUT / "diagnostic" / "application_predictions.parquet", index=False)
    hashes["diagnostic"] = sha(OUT / "diagnostic" / "application_predictions.parquet")
    save(OUT / "predictions_fixed.json", dict(utc=now(), hashes=hashes, recent_targets_loaded=False,
        full_coefficients_sha256=sha(OUT / "fits/primary/coefficients.json"),
        early_coefficients_sha256=sha(OUT / "fits/early/coefficients.json")))
    scores = {}
    label_loads = []
    for fold in FOLDS:
        if fold == "primary":
            labels = labels_primary
        else:
            # Deliberately after the immutable prediction seal above.
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
    save(OUT / "diagnostic" / "metrics.json", dict(scores=diagnostic_scores, used_for_adoption=False,
        correction_training_end=str(EARLY_CUTOFF), evaluation_start=str(diagnostic.ts.min()),
        evaluation_end=str(diagnostic.ts.max()), baseline_already_exposed=True))
    both = all(scores[fold]["p"]["W"] < scores[fold]["p_reference"]["W"] for fold in FOLDS)
    result = dict(arm="regularized_cloud_curve", scores=scores, eligible=both, both_folds_improve=both,
        diagnostic_scores=diagnostic_scores, diagnostic_used_for_adoption=False, real_calibration_fit_count=2,
        real_generation_fit_count=0, real_alpha_fit_count=0, all_history_exposed=True,
        primary_fit_partly_in_sample=True, recent_predictions_fixed_before_target_load=True,
        confirmation_loaded=False, test_loaded=False, exported=False)
    save(OUT / "label_loads.json", label_loads)
    save(OUT / "results.json", result)
    check_hashes(ROOT, protocol["source_sha256"])
    check_hashes(POISSON, protocol["inputs_sha256"])
    check_hashes(OUT, read(OUT / "prepared_manifest.json"))
    assert sha(ROOT / protocol["best_zip"]) == protocol["best_zip_sha256"]
    save(OUT / "completed.json", dict(utc=now(), pid=os.getpid(), real_calibration_fit_count=2,
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
    with threadpool_limits(limits=1):
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
