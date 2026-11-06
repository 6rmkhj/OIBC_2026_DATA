# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "lightgbm"]
# ///
# How to run: python submission/score_push_verify_group_math.py
"""Independent finite-difference and matrix checks of the group objective."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Final

import lightgbm as lgb
import numpy as np

ROOT: Final = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "submission/score_push_renew"))
from group_objective import GroupLoss

OUT: Final = ROOT / "analysis_outputs/renew_20261105/group_wave"


def main() -> None:
    group = np.array([1, 0, 2, 0, 1, 2], dtype=np.int64)
    share = np.array([.8, .3, .4, .7, .2, .6])
    target = np.array([.47, .25, .8])
    group_weight = np.array([4., 1.7, 0.])
    weight = group_weight[group] * share
    actual = np.array([.12, .73, .6, .22, .4, .7])
    prediction = np.array([.2, .5, .3, .1, .7, .9])
    rng = np.random.default_rng(20261105)
    records = []
    for grouped, regularizer in ((True, .1), (True, 1.), (False, .1)):
        delta = .05
        objective = GroupLoss(group, share, target, actual, weight, group_weight, delta, regularizer, grouped)

        def loss(values: np.ndarray) -> float:
            total = 0.
            if grouped:
                for index in range(3):
                    residual = sum(share[j] * values[j] for j in range(6) if group[j] == index) - target[index]
                    total += group_weight[index] * (np.sqrt(residual * residual + delta * delta) - delta)
            else:
                for j in range(6):
                    residual = values[j] - actual[j]
                    total += weight[j] * (np.sqrt(residual * residual + delta * delta) - delta)
            return total + sum(regularizer / 2 * weight[j] * (values[j] - actual[j]) ** 2 for j in range(6))

        gradient, bound = objective.derivatives(prediction)
        epsilon = 1e-6
        numerical = np.empty(6)
        for j in range(6):
            step = np.eye(6)[j] * epsilon
            numerical[j] = (loss(prediction + step) - loss(prediction - step)) / (2 * epsilon)
        np.testing.assert_allclose(gradient, numerical, rtol=1e-7, atol=1e-9)
        np.testing.assert_allclose(objective.value(prediction), loss(prediction), rtol=1e-13)
        np.testing.assert_array_equal(gradient[group == 2], 0.)
        np.testing.assert_array_equal(bound[group == 2], 0.)
        largest_violation = -np.inf
        minimum_eigenvalue = np.inf
        for _ in range(100):
            point = rng.normal(.4, .6, 6)
            grad, diagonal = objective.derivatives(point)
            hessian = np.diag(regularizer * weight)
            if grouped:
                for index in range(3):
                    row_share = np.where(group == index, share, 0.)
                    residual = row_share @ point - target[index]
                    curvature = delta ** 2 / (residual ** 2 + delta ** 2) ** 1.5
                    hessian += group_weight[index] * curvature * np.outer(row_share, row_share)
            else:
                hessian += np.diag(weight * delta ** 2 / ((point - actual) ** 2 + delta ** 2) ** 1.5)
            eigenvalue = np.linalg.eigvalsh(np.diag(diagonal) - hessian).min()
            minimum_eigenvalue = min(minimum_eigenvalue, eigenvalue)
            assert eigenvalue >= -1e-10
            step = rng.normal(0., .5, 6)
            violation = loss(point + step) - loss(point) - grad @ step - .5 * diagonal @ (step ** 2)
            largest_violation = max(largest_violation, violation)
            assert violation <= 1e-10
        dataset = lgb.Dataset(np.arange(12).reshape(6, 2), label=actual, params={"num_threads": 1, "verbosity": -1}).construct()
        callback_gradient, callback_bound = objective(prediction, dataset)
        np.testing.assert_array_equal(callback_gradient, gradient)
        np.testing.assert_array_equal(callback_bound, bound)
        rejected = []
        for name, invalid in (("row_order", lgb.Dataset(np.arange(12).reshape(6, 2), label=actual[::-1])),
                              ("external_weights", lgb.Dataset(np.arange(12).reshape(6, 2), label=actual, weight=np.full(6, 2.))),
                              ("external_initial_score", lgb.Dataset(np.arange(12).reshape(6, 2), label=actual, init_score=np.ones(6)))):
            invalid.params = {"num_threads": 1, "verbosity": -1}
            invalid.construct()
            try:
                objective(prediction, invalid)
            except AssertionError:
                rejected.append(name)
            else:
                raise AssertionError(f"Accepted invalid callback contract: {name}")
        records.append({"grouped": grouped, "lambda": regularizer, "gradient_max_error": float(abs(gradient - numerical).max()),
                        "majorizer_min_eigenvalue": float(minimum_eigenvalue), "upper_bound_max_violation": float(largest_violation),
                        "invalid_callbacks_rejected": rejected, "zero_price_derivatives_exact": True})
    all_zero_rejected = False
    try:
        GroupLoss(group, share, target, actual, np.zeros(6), np.zeros(3), .05, .1, True)
    except AssertionError:
        all_zero_rejected = True
    assert all_zero_rejected, "All-zero monetary weights must be rejected"
    with (ROOT / "submission/score_push_renew/group_objective.py").open("rb") as handle:
        source_hash = hashlib.file_digest(handle, "sha256").hexdigest()
    result = {"status": "PASS", "objective_source_sha256": source_hash, "records": records, "all_zero_weight_rejected": all_zero_rejected,
              "models_fitted": 0, "limitation": "These fixtures validate the mathematics and callback contract, not predictive performance."}
    (OUT / "independent_math_check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
