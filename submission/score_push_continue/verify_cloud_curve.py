"""Independent cloud-curve reconstruction and LP optimality verification; no fits.

This verifier imports no production calibration code and never invokes a solver.
It reconstructs the complete optimization problem, checks a saved primal/dual
certificate, and recomputes each published prediction from original sources.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from math import fsum
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
from scipy import sparse

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis_outputs/renew_20261107/cloud_curve"
SOURCE = ROOT / "analysis_outputs/renew_20261106/poisson_wave/data"
KEYS = ["ts", "grp"]
KNOTS = np.array([0., 25., 50., 75., 100.])
CUTOFF = pd.Timestamp("2024-02-01", tz="Asia/Seoul")


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
    assert all(np.isfinite(values).all() for values in (y, p, smp, k))
    assert (smp * k >= 0).all()
    penalty = fsum(float(a * b * abs(t - v)) for t, v, a, b in zip(y, p, smp, k, strict=True))
    denominator = fsum(float(a * b * t) for t, a, b in zip(y, smp, k, strict=True))
    revenue = fsum(float(a * t) for t, a in zip(y, smp, strict=True))
    return dict(W=penalty, W_pct=100 * penalty / denominator, revenue=revenue, S=revenue - .1 * penalty, rows=len(frame))


def hat_basis(values):
    """Five endpoint-clamped hat functions, independently constructed per knot."""
    values = np.clip(np.asarray(values, dtype=float), 0., 100.)
    assert np.isfinite(values).all()
    result = np.zeros((len(values), 5))
    for j in range(5):
        if j == 0:
            result[:, j] = np.maximum(0., (25. - values) / 25.)
        elif j == 4:
            result[:, j] = np.maximum(0., (values - 75.) / 25.)
        else:
            result[:, j] = np.maximum(0., 1. - np.abs(values - KNOTS[j]) / 25.)
    np.testing.assert_allclose(result.sum(axis=1), 1., rtol=0., atol=5e-16)
    return result


def original_fold(fold):
    data = SOURCE / fold
    labels = pd.read_parquet(data / "labels.parquet")
    application = pd.read_parquet(data / "application_inputs.parquet")
    coverage = pd.read_parquet(data / "coverage.parquet")
    cloud = pd.read_parquet(data / "evaluation.parquet", columns=KEYS + ["wb_cloud"])
    equal_keys(labels, application)
    equal_keys(labels, coverage)
    frame = labels.merge(application[KEYS + ["static_capacity"]], on=KEYS, how="left", sort=False, validate="one_to_one")
    frame = frame.merge(coverage, on=KEYS, how="left", sort=False, validate="one_to_one")
    frame = frame.merge(cloud, on=KEYS, how="left", sort=False, validate="one_to_one")
    equal_keys(labels, frame)
    assert frame.loc[frame.night, "p_reference"].eq(0.).all()
    assert frame.p_reference.ge(0).all() and (frame.p_reference <= frame.static_capacity).all()
    stored = pd.read_parquet(OUT / "data" / fold / "inputs.parquet")
    assert list(stored) == ["ts", "grp", "p_reference", "wb_cloud", "static_capacity", "night"]
    pd.testing.assert_frame_equal(stored, frame[list(stored)], check_exact=True)
    return frame


def reconstruct_lp(rows):
    n = len(rows)
    basis = sparse.csr_matrix(hat_basis(rows.wb_cloud.to_numpy()))
    identity_n, identity_five = sparse.eye(n, format="csr"), sparse.eye(5, format="csr")
    d2 = sparse.csr_matrix([[1., -2., 1., 0., 0.], [0., 1., -2., 1., 0.], [0., 0., 1., -2., 1.]])
    zero_n5, zero_n3 = sparse.csr_matrix((n, 5)), sparse.csr_matrix((n, 3))
    zero_5n, zero_53 = sparse.csr_matrix((5, n)), sparse.csr_matrix((5, 3))
    zero_3n, zero_35 = sparse.csr_matrix((3, n)), sparse.csr_matrix((3, 5))
    matrix = sparse.vstack([
        sparse.hstack([basis, -identity_n, zero_n5, zero_n3]),
        sparse.hstack([-basis, -identity_n, zero_n5, zero_n3]),
        sparse.hstack([identity_five, zero_5n, -identity_five, zero_53]),
        sparse.hstack([-identity_five, zero_5n, -identity_five, zero_53]),
        sparse.hstack([d2, zero_3n, zero_35, -sparse.eye(3)]),
        sparse.hstack([-d2, zero_3n, zero_35, -sparse.eye(3)])], format="csr")
    residual = rows.y.to_numpy() / rows.p_reference.to_numpy() - 1.
    mass = rows.smp.to_numpy() * rows.k.to_numpy() * rows.p_reference.to_numpy()
    weight = mass / fsum(float(w) for w in mass)
    c = np.r_[np.zeros(5), weight, np.full(5, .01 / 5), np.full(3, .01 / 3)]
    b = np.r_[residual, -residual, np.zeros(16)]
    lower = np.r_[np.full(5, -.15), np.zeros(n + 8)]
    upper = np.r_[np.full(5, .15), np.full(n + 8, np.inf)]
    return c, matrix, b, lower, upper, mass, weight, residual, d2


def verify_fit(name, original):
    directory = OUT / "fits" / name
    frame = original if name == "primary" else original.loc[original.ts <= CUTOFF]
    active = np.isfinite(frame.wb_cloud.to_numpy()) & frame.p_reference.gt(0).to_numpy() & (frame.smp * frame.k).gt(0).to_numpy()
    rows = frame.loc[active].reset_index(drop=True)
    stored = pd.read_parquet(directory / "fit_rows.parquet")
    equal_keys(stored, rows)
    for column in ("p_reference", "y", "smp", "k", "wb_cloud"):
        np.testing.assert_array_equal(stored[column].to_numpy(), rows[column].to_numpy())
    c, matrix, b, lower, upper, mass, weight, residual, d2 = reconstruct_lp(rows)
    for column, expected in (("ratio_residual", residual), ("monetary_prediction_weight", mass), ("normalized_weight", weight)):
        np.testing.assert_allclose(stored[column], expected, rtol=1e-13, atol=1e-13)
    with np.load(directory / "lp.npz", allow_pickle=False) as saved:
        assert set(saved.files) == {"c", "b_ub", "lower", "upper", "A_data", "A_indices", "A_indptr", "A_shape"}
        saved_matrix = sparse.csr_matrix((saved["A_data"], saved["A_indices"], saved["A_indptr"]), shape=tuple(saved["A_shape"]))
        assert saved_matrix.shape == matrix.shape
        difference = (saved_matrix - matrix).tocsr()
        assert not difference.nnz or np.max(np.abs(difference.data)) <= 1e-14
        for key, expected in (("c", c), ("b_ub", b), ("lower", lower), ("upper", upper)):
            np.testing.assert_allclose(saved[key], expected, rtol=1e-13, atol=1e-13)
    with np.load(directory / "solution.npz", allow_pickle=False) as saved:
        solution = {key: saved[key].copy() for key in saved.files}
    x = solution["x"]
    inequality = solution["ineqlin_marginals"]
    lower_dual = solution["lower_marginals"]
    upper_dual = solution["upper_marginals"]
    assert x.shape == c.shape and inequality.shape == b.shape
    assert lower_dual.shape == upper_dual.shape == c.shape
    assert all(np.isfinite(v).all() for v in (x, inequality, lower_dual, upper_dual))
    slack = b - matrix @ x
    low_slack, up_slack = x - lower, upper - x
    np.testing.assert_allclose(solution["ineqlin_residual"], slack, rtol=1e-10, atol=2e-8)
    np.testing.assert_allclose(solution["lower_residual"], low_slack, rtol=1e-10, atol=2e-8)
    np.testing.assert_allclose(solution["upper_residual"], up_slack, rtol=1e-10, atol=2e-8)
    finite_upper = np.isfinite(upper)
    primal_error = max(float(np.maximum(-slack, 0).max()), float(np.maximum(-low_slack, 0).max()),
                       float(np.maximum(-up_slack[finite_upper], 0).max()))
    dual_error = max(float(np.maximum(inequality, 0).max()), float(np.maximum(-lower_dual, 0).max()),
                     float(np.maximum(upper_dual, 0).max()), float(np.abs(upper_dual[~finite_upper]).max()))
    stationarity = c - matrix.T @ inequality - lower_dual - upper_dual
    stationarity_error = float(np.max(np.abs(stationarity)))
    complementarity = max(float(np.max(np.abs(inequality * slack))), float(np.max(np.abs(lower_dual * low_slack))),
                          float(np.max(np.abs(upper_dual[finite_upper] * up_slack[finite_upper]))))
    primal_value = float(c @ x)
    dual_value = float(b @ inequality + lower @ lower_dual + upper[finite_upper] @ upper_dual[finite_upper])
    gap = abs(primal_value - dual_value)
    assert primal_error <= 2e-7, primal_error
    assert dual_error <= 2e-7, dual_error
    assert stationarity_error <= 2e-7, stationarity_error
    assert complementarity <= 2e-7, complementarity
    assert gap <= 2e-7, (primal_value, dual_value, gap)
    optimization = read(directory / "optimization.json")
    assert optimization["status"] == 0 and optimization["success"] is True
    assert optimization["name"] == name and optimization["fit_count"] == 1
    assert optimization["input_rows"] == len(frame) and optimization["active_rows"] == len(rows)
    assert pd.Timestamp(optimization["minimum_ts"]) == rows.ts.min()
    assert pd.Timestamp(optimization["maximum_ts"]) == rows.ts.max()
    if name == "early":
        assert rows.ts.max() <= CUTOFF
    np.testing.assert_allclose(optimization["fun"], primal_value, rtol=1e-11, atol=2e-8)
    coefficients = read(directory / "coefficients.json")
    np.testing.assert_array_equal(coefficients["knots"], KNOTS)
    np.testing.assert_array_equal(coefficients["delta"], x[:5])
    assert coefficients["shrink"] == .5
    assert coefficients["fit_name"] == name and coefficients["optimizer_status"] == 0
    assert coefficients["missing_identity"] and coefficients["constant_endpoint_extrapolation"]
    for field, filename in (("fit_rows_sha256", "fit_rows.parquet"), ("lp_sha256", "lp.npz"), ("solution_sha256", "solution.npz")):
        assert coefficients[field] == digest(directory / filename)
    delta = x[:5]
    assert np.max(np.abs(delta)) <= .15 + 2e-7
    actual_residual = residual - hat_basis(rows.wb_cloud.to_numpy()) @ delta
    explicit_value = float(weight @ np.abs(actual_residual) + .01 * np.abs(delta).mean() + .01 * np.abs(d2 @ delta).mean())
    np.testing.assert_allclose(primal_value, explicit_value, rtol=1e-10, atol=2e-8)
    # The neutral curve is a feasible reference for the regularized objective.
    assert explicit_value <= float(weight @ np.abs(residual)) + 2e-7
    certificate = dict(fit=name, rows=len(rows), variables=len(c), constraints=len(b),
        primal_value=primal_value, dual_value=dual_value, duality_gap=gap, primal_error=primal_error,
        dual_sign_error=dual_error, stationarity_error=stationarity_error, complementarity_error=complementarity,
        independently_reconstructed_problem=True, optimization_refits=0)
    return delta, certificate


def expected_prediction(frame, delta):
    cloud = frame.wb_cloud.to_numpy(dtype=float)
    valid = np.isfinite(cloud)
    adjustment = np.zeros(len(frame))
    # np.interp supplies an independent endpoint-clamped application path.
    adjustment[valid] = np.interp(cloud[valid], KNOTS, delta)
    factor = 1 + .5 * adjustment
    prediction = np.clip(frame.p_reference.to_numpy() * factor, 0, frame.static_capacity.to_numpy())
    assert np.array_equal(prediction[~valid], frame.p_reference.to_numpy()[~valid])
    assert np.array_equal(prediction[frame.p_reference.eq(0)], np.zeros(int(frame.p_reference.eq(0).sum())))
    assert factor.min() >= .925 - 1e-7 and factor.max() <= 1.075 + 1e-7
    return prediction, factor, adjustment


def main():
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = read(OUT / "protocol.json")
    assert protocol["arm"] == "regularized_cloud_curve"
    assert protocol["knots"] == KNOTS.tolist() and protocol["delta_bounds"] == [-.15, .15]
    assert protocol["shrink_once"] == .5 and protocol["coefficient_penalty"] == protocol["curvature_penalty"] == .01
    assert protocol["second_difference"] == [[1., -2., 1., 0., 0.], [0., 1., -2., 1., 0.], [0., 0., 1., -2., 1.]]
    assert protocol["fit_names"] == ["primary", "early"] and protocol["real_calibration_fit_budget"] == 2
    assert pd.Timestamp(protocol["early_cutoff"]) == CUTOFF
    assert protocol["identity_for_nonfinite_cloud"] and protocol["extrapolation"] == "constant endpoint"
    assert protocol["model_threads"] == protocol["blas_threads"] == 1
    assert protocol["all_history_exposed"] and protocol["primary_fit_partly_in_sample"]
    assert not protocol["confirmation_loaded"] and not protocol["test_loaded"]
    assert "already fitted on full PRIMARY" in protocol["diagnostic_limitation"]
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
    assert preparation["status"] == "PASS" and preparation["actual_optimizer_fits"] == 0
    assert not preparation["primary_targets_loaded"] and not preparation["recent_targets_loaded"]
    assert read(OUT / "self_check.json")["status"] == "PASS"
    assert sorted(p.name for p in (OUT / "fits").iterdir() if p.is_dir()) == ["early", "primary"]
    originals = {fold: original_fold(fold) for fold in ("primary", "recent")}
    delta, primary_certificate = verify_fit("primary", originals["primary"])
    early_delta, early_certificate = verify_fit("early", originals["primary"])
    intervals = read(OUT / "fit_intervals.json")
    assert len(intervals) == 2
    assert intervals[0] == read(OUT / "fits/primary/optimization.json")
    assert intervals[1] == read(OUT / "fits/early/optimization.json")
    assert datetime.fromisoformat(intervals[0]["finished_utc"]) <= datetime.fromisoformat(intervals[1]["started_utc"])
    for interval in intervals:
        assert datetime.fromisoformat(interval["started_utc"]) <= datetime.fromisoformat(interval["finished_utc"])
    fixed = read(OUT / "predictions_fixed.json")
    assert not fixed["recent_targets_loaded"]
    assert fixed["full_coefficients_sha256"] == digest(OUT / "fits/primary/coefficients.json")
    assert fixed["early_coefficients_sha256"] == digest(OUT / "fits/early/coefficients.json")
    assert datetime.fromisoformat(intervals[1]["finished_utc"]) <= datetime.fromisoformat(fixed["utc"])
    label_loads = read(OUT / "label_loads.json")
    assert len(label_loads) == 1 and label_loads[0]["fold"] == "recent"
    assert datetime.fromisoformat(label_loads[0]["loaded_utc"]) >= datetime.fromisoformat(fixed["utc"])
    assert label_loads[0]["predictions_fixed_sha256"] == digest(OUT / "predictions_fixed.json")
    scores = {}
    for fold in ("primary", "recent", "diagnostic"):
        original = originals[fold] if fold != "diagnostic" else originals["primary"].loc[originals["primary"].ts > CUTOFF].reset_index(drop=True)
        coefficient = delta if fold != "diagnostic" else early_delta
        expected, factor, adjustment = expected_prediction(original, coefficient)
        application_path = OUT / fold / "application_predictions.parquet"
        assert digest(application_path) == fixed["hashes"][fold]
        application = pd.read_parquet(application_path)
        assert list(application) == ["ts", "grp", "p_reference", "wb_cloud", "static_capacity", "night",
                                     "delta", "effective_factor", "before_capacity_clip", "p"]
        equal_keys(application, original)
        for name in ("p_reference", "wb_cloud", "static_capacity", "night"):
            np.testing.assert_array_equal(application[name], original[name])
        for name, values in (("delta", adjustment), ("effective_factor", factor),
                             ("before_capacity_clip", original.p_reference.to_numpy() * factor), ("p", expected)):
            np.testing.assert_allclose(application[name], values, rtol=1e-13, atol=2e-9)
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
    assert result["real_calibration_fit_count"] == 2 and result["real_generation_fit_count"] == result["real_alpha_fit_count"] == 0
    assert not result["diagnostic_used_for_adoption"]
    assert result["all_history_exposed"] and result["primary_fit_partly_in_sample"]
    assert result["recent_predictions_fixed_before_target_load"]
    assert not any(result[name] for name in ("confirmation_loaded", "test_loaded", "exported"))
    for fold in ("primary", "recent"):
        assert result["scores"][fold] == read(OUT / fold / "metrics.json")
    assert result["diagnostic_scores"] == read(OUT / "diagnostic/metrics.json")["scores"]
    completed = read(OUT / "completed.json")
    assert completed["real_calibration_fit_count"] == 2 and completed["best_zip_unchanged"] and completed["prepared_inputs_unchanged"]
    evidence = dict(status="PASS", checked_utc=datetime.now(timezone.utc).isoformat(),
        fits=[primary_certificate, early_certificate], scores=scores, eligible=both,
        rows_replayed={fold: len(pd.read_parquet(OUT / fold / "predictions.parquet")) for fold in scores},
        optimization_refits=0, generation_fits=0, all_prediction_rows_reconstructed=True,
        recent_prediction_seal_checked=True, original_inputs_and_best_zip_unchanged=True,
        terminal_manifest_sha256=digest(OUT / "terminal_manifest.json"), verifier_sha256=digest(__file__),
        limits="All history exposed; full-primary fit partly in-sample. Early correction diagnostic uses a baseline already calibrated on full PRIMARY; not an independent holdout or official score.")
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(evidence, indent=2, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
