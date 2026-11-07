"""Two pre-specified weighted-LAD cloud-by-solar calibrations with complete LP evidence.

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
OUT = ROOT / "analysis_outputs/renew_20261107/cloud_solar_surface"
KNOTS = np.array([0., 50., 100.])
SOLAR_KNOTS = np.array([0., .5, 1.])
SECOND_DIFFERENCE = np.zeros((6, 9))
for _axis_index in range(3):
    SECOND_DIFFERENCE[_axis_index, [_axis_index, 3 + _axis_index, 6 + _axis_index]] = [1., -2., 1.]
    SECOND_DIFFERENCE[3 + _axis_index, [3 * _axis_index, 3 * _axis_index + 1, 3 * _axis_index + 2]] = [1., -2., 1.]
SHRINK = .5
PENALTY = .01
DELTA_LIMIT = .15
EARLY_CUTOFF = pd.Timestamp("2024-02-01", tz="Asia/Seoul")
INPUT_COLUMNS = [*KEYS, "p_reference", "wb_cloud", "cosz", "static_capacity", "night"]
SOLVER_OPTIONS = dict(threads=1, presolve=True, primal_feasibility_tolerance=1e-9,
                      dual_feasibility_tolerance=1e-9, ipm_optimality_tolerance=1e-10)


def hat_basis(values, knots):
    """One-dimensional hat functions with constant endpoint extrapolation."""
    values = np.asarray(values, dtype=np.float64)
    assert values.ndim == 1
    finite = np.isfinite(values)
    output = np.zeros((len(values), len(knots)), dtype=np.float64)
    clipped = np.clip(values[finite], knots[0], knots[-1])
    left = np.clip(np.searchsorted(knots, clipped, side="right") - 1, 0, len(knots) - 2)
    fraction = (clipped - knots[left]) / (knots[left + 1] - knots[left])
    rows = np.flatnonzero(finite)
    output[rows, left] = 1 - fraction
    output[rows, left + 1] = fraction
    assert (output >= 0).all()
    np.testing.assert_array_equal(output.sum(axis=1), finite.astype(float))
    return output


def basis(cloud, cosz):
    """Bilinear cloud-major tensor basis; either missing input means identity."""
    cloud = np.asarray(cloud, dtype=np.float64)
    cosz = np.asarray(cosz, dtype=np.float64)
    assert cloud.ndim == 1 and cloud.shape == cosz.shape
    first, second = hat_basis(cloud, KNOTS), hat_basis(cosz, SOLAR_KNOTS)
    output = (first[:, :, None] * second[:, None, :]).reshape(len(cloud), 9)
    finite = np.isfinite(cloud) & np.isfinite(cosz)
    np.testing.assert_allclose(output.sum(axis=1), finite.astype(float), rtol=0, atol=3e-16)
    return output


def apply_curve(inputs, delta):
    """Export-compatible application: only baseline, cloud and solar geometry are used."""
    assert list(inputs) == INPUT_COLUMNS, "Application accepts only declared inputs, never labels"
    assert not inputs.duplicated(KEYS).any() and inputs.ts.notna().all()
    delta = np.asarray(delta, dtype=np.float64)
    assert delta.shape == (9,) and np.isfinite(delta).all()
    assert np.max(np.abs(delta)) <= DELTA_LIMIT + 1e-10
    reference = inputs.p_reference.to_numpy(dtype=float)
    capacity = inputs.static_capacity.to_numpy(dtype=float)
    night = inputs.night.to_numpy(dtype=bool)
    assert inputs.night.notna().all() and np.isfinite(reference).all() and np.isfinite(capacity).all()
    assert (reference >= 0).all() and (capacity > 0).all() and (reference <= capacity + 1e-8).all()
    adjustment = basis(inputs.wb_cloud.to_numpy(), inputs.cosz.to_numpy()) @ delta
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
    mask = np.isfinite(frame.wb_cloud.to_numpy()) & np.isfinite(frame.cosz.to_numpy()) & frame.p_reference.gt(0).to_numpy() & (monetary > 0)
    rows = frame.loc[mask, [*KEYS, "p_reference", "y", "smp", "k", "wb_cloud", "cosz"]].copy()
    rows["ratio_residual"] = rows.y.to_numpy() / rows.p_reference.to_numpy() - 1
    rows["monetary_prediction_weight"] = (rows.smp * rows.k * rows.p_reference).to_numpy()
    mass = rows.monetary_prediction_weight.sum()
    assert mass > 0 and len(rows) > 0
    rows["normalized_weight"] = rows.monetary_prediction_weight / mass
    assert np.isfinite(rows[["ratio_residual", "normalized_weight"]].to_numpy()).all()
    np.testing.assert_allclose(rows.normalized_weight.sum(), 1., rtol=1e-14)
    return rows.reset_index(drop=True)


def lp_problem(rows):
    """Variables: delta9, residual_absN, delta_abs9, curvature_abs6."""
    n, nodes, curvature = len(rows), 9, 6
    hats = sparse.csr_matrix(basis(rows.wb_cloud.to_numpy(), rows.cosz.to_numpy()))
    eye_n, eye_nodes, eye_curvature = (sparse.eye(k, format="csr") for k in (n, nodes, curvature))
    z_nn, z_nc = sparse.csr_matrix((n, nodes)), sparse.csr_matrix((n, curvature))
    z_noden, z_nodec = sparse.csr_matrix((nodes, n)), sparse.csr_matrix((nodes, curvature))
    z_curn, z_curnode = sparse.csr_matrix((curvature, n)), sparse.csr_matrix((curvature, nodes))
    d2 = sparse.csr_matrix(SECOND_DIFFERENCE)
    matrix = sparse.vstack([
        sparse.hstack([hats, -eye_n, z_nn, z_nc]),
        sparse.hstack([-hats, -eye_n, z_nn, z_nc]),
        sparse.hstack([eye_nodes, z_noden, -eye_nodes, z_nodec]),
        sparse.hstack([-eye_nodes, z_noden, -eye_nodes, z_nodec]),
        sparse.hstack([d2, z_curn, z_curnode, -eye_curvature]),
        sparse.hstack([-d2, z_curn, z_curnode, -eye_curvature]),
    ], format="csr")
    residual = rows.ratio_residual.to_numpy(dtype=float)
    rhs = np.concatenate([residual, -residual, np.zeros(2 * nodes + 2 * curvature)])
    objective = np.concatenate([np.zeros(nodes), rows.normalized_weight.to_numpy(dtype=float),
                                np.full(nodes, PENALTY / nodes), np.full(curvature, PENALTY / curvature)])
    lower = np.concatenate([np.full(nodes, -DELTA_LIMIT), np.zeros(n + nodes + curvature)])
    upper = np.concatenate([np.full(nodes, DELTA_LIMIT), np.full(n + nodes + curvature, np.inf)])
    assert matrix.shape == (2 * n + 30, n + 24)
    return objective, matrix, rhs, lower, upper


def self_check():
    # Exact nodes prove cloud-major ordering and all six axial differences.
    cloud = np.repeat(KNOTS, 3)
    cosz = np.tile(SOLAR_KNOTS, 3)
    np.testing.assert_array_equal(basis(cloud, cosz), np.eye(9))
    interior = basis(np.array([25.]), np.array([.25]))[0]
    expected = np.zeros(9)
    expected[[0, 1, 3, 4]] = .25
    np.testing.assert_array_equal(interior, expected)
    endpoints = basis(np.array([-1., 101., np.nan, 50., np.inf]), np.array([-.1, 1.1, .5, np.inf, .5]))
    np.testing.assert_array_equal(endpoints[:2], np.eye(9)[[0, 8]])
    np.testing.assert_array_equal(endpoints[2:], np.zeros((3, 9)))
    affine = (cloud / 100 + cosz).reshape(-1)
    np.testing.assert_array_equal(SECOND_DIFFERENCE @ affine, np.zeros(6))
    single_center = np.zeros(9)
    single_center[4] = 1
    np.testing.assert_array_equal(SECOND_DIFFERENCE @ single_center, [0., -2., 0., 0., -2., 0.])
    inputs = pd.DataFrame(dict(ts=pd.date_range("2024-01-01", periods=9, freq="h", tz="Asia/Seoul"),
        grp="G1", p_reference=100., wb_cloud=cloud, cosz=cosz, static_capacity=103., night=False))[INPUT_COLUMNS]
    inputs.loc[0, "night"] = True
    inputs.loc[7, "wb_cloud"] = np.nan
    inputs.loc[8, "cosz"] = np.inf
    applied = apply_curve(inputs, np.full(9, .10))
    np.testing.assert_array_equal(applied.p, [0., 103., 103., 103., 103., 103., 103., 100., 100.])
    np.testing.assert_allclose(applied.effective_factor.iloc[1:7], 1.05, atol=1e-15, rtol=0)
    try:
        apply_curve(inputs.assign(y=1e9), np.zeros(9))
    except AssertionError:
        pass
    else:
        raise AssertionError("Label-bearing application was accepted")
    labels = inputs[KEYS].assign(y=110., smp=2., k=3.)
    rows = active_rows(inputs, labels)
    c, matrix, rhs, lower, upper = lp_problem(rows)
    delta = np.full(9, .10)
    x = np.concatenate([delta, np.abs(rows.ratio_residual - basis(rows.wb_cloud, rows.cosz) @ delta),
                        np.abs(delta), np.abs(SECOND_DIFFERENCE @ delta)])
    assert (matrix @ x <= rhs + 1e-12).all() and (x >= lower).all() and (x <= upper).all()
    np.testing.assert_allclose(c @ x, .001, atol=1e-12, rtol=0)
    assert not np.isclose(1 + SHRINK * SHRINK * .10, applied.effective_factor.iloc[1])
    return dict(status="PASS", actual_optimizer_fits=0, tests=["all9 nodes and cloud-major ordering",
        "bilinear interior", "both-axis endpoint clamping", "either nonfinite input gives identity",
        "all6 second differences", "single half shrink", "capacity and night zero",
        "labels excluded from application", "sparse LP synthetic primal/objective", "double-shrink mutation rejected"])


def prepare():
    assert not OUT.exists(), "Preserve prior cloud-solar surface experiment"
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
    save(OUT / "protocol.json", dict(created_utc=now(), arm="regularized_cloud_solar_surface", cloud_knots=KNOTS.tolist(), solar_knots=SOLAR_KNOTS.tolist(),
        delta_bounds=[-DELTA_LIMIT, DELTA_LIMIT], shrink_once=SHRINK, coefficient_penalty=PENALTY,
        curvature_penalty=PENALTY, second_difference=SECOND_DIFFERENCE.tolist(),
        objective="sum(normalized SMP*k*p_reference * abs(y/p_reference-1-B*delta)) + .01*mean(abs(delta)) + .01*mean(abs(D2*delta))",
        fit_active="finite wb_cloud and finite cosz and p_reference>0 and SMP*k>0", identity_for_either_nonfinite_covariate=True, basis_order="cloud-major; index=3*cloud_index+solar_index",
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
        clouds = pd.read_parquet(source / "evaluation.parquet", columns=[*KEYS, "wb_cloud", "cosz"])
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
        assert_keys(apply_curve(joined, np.zeros(9)), joined)
        np.testing.assert_array_equal(apply_curve(joined, np.zeros(9)).p, reference.p_reference)
        records.append(dict(fold=fold, rows=len(joined), finite_pair_rows=int((np.isfinite(joined.wb_cloud) & np.isfinite(joined.cosz)).sum()),
            night_rows=int(joined.night.sum()), labels_projected=False, reference_projection=[*KEYS, "p_reference"]))
    check_hashes(POISSON, current)
    save(OUT / "preparation.json", dict(status="PASS", records=records, actual_optimizer_fits=0,
        recent_targets_loaded=False, primary_targets_loaded=False))
    save(OUT / "prepared_manifest.json", {str(p.relative_to(OUT)): sha(p) for p in sorted((OUT / "data").rglob("*")) if p.is_file()})
    print("CLOUD SOLAR SURFACE PREPARED", records, flush=True)


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
    delta = x[:9]
    np.testing.assert_allclose(c @ x, optimized.fun, rtol=1e-11, atol=1e-12)
    assert np.max(matrix @ x - rhs) < 1e-7
    assert np.max(lower - x) < 1e-7 and np.max(x - upper) < 1e-7
    stationarity = c - matrix.T @ optimized.ineqlin.marginals - optimized.lower.marginals - optimized.upper.marginals
    assert np.max(np.abs(stationarity)) < 1e-7
    finite_upper = np.isfinite(upper)
    dual = rhs @ optimized.ineqlin.marginals + lower @ optimized.lower.marginals + upper[finite_upper] @ optimized.upper.marginals[finite_upper]
    assert abs(float(dual) - optimized.fun) < 1e-7
    direct_objective = (rows.normalized_weight.to_numpy() * np.abs(rows.ratio_residual.to_numpy() - basis(rows.wb_cloud, rows.cosz) @ delta)).sum()
    direct_objective += PENALTY * np.abs(delta).mean() + PENALTY * np.abs(SECOND_DIFFERENCE @ delta).mean()
    np.testing.assert_allclose(direct_objective, optimized.fun, rtol=1e-9, atol=1e-10)
    save(directory / "coefficients.json", dict(cloud_knots=KNOTS.tolist(), solar_knots=SOLAR_KNOTS.tolist(), delta=delta.tolist(), shrink=SHRINK,
        shape=[3, 3], basis_order="cloud-major; index=3*cloud_index+solar_index",
        input_schema=INPUT_COLUMNS, missing_identity=True, constant_endpoint_extrapolation=True,
        fit_name=name, direct_objective=float(direct_objective), dual_objective=float(dual),
        maximum_stationarity_error=float(np.max(np.abs(stationarity))), optimizer_status=0,
        fit_rows_sha256=sha(directory / "fit_rows.parquet"), lp_sha256=sha(directory / "lp.npz"),
        solution_sha256=sha(directory / "solution.npz")))
    print("CLOUD SOLAR SURFACE FIT COMPLETE", name, delta.tolist(), record["seconds"], flush=True)
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
    result = dict(arm="regularized_cloud_solar_surface", scores=scores, eligible=both, both_folds_improve=both,
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
