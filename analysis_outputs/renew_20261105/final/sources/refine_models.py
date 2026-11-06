# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "scipy", "lightgbm", "pyarrow"]
# ///
"""Primary-only simplex optimization and bounded normalized-tree refinement."""
from wave_common import save_json, digest, receipt
from site_features import normalizer
from pathlib import Path
import time
import warnings
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen group interface
import lightgbm as lgb
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, hstack, vstack, eye


def convex_weights(primary: pd.DataFrame, names: list[str], directory: Path) -> np.ndarray:
    """Solve weighted absolute loss over a nonnegative unit-sum primary simplex."""
    assert primary.ts.min() > pd.Timestamp("2023-06-01", tz="Asia/Seoul")
    assert primary.ts.max() <= pd.Timestamp("2024-06-01", tz="Asia/Seoul")
    directory.mkdir(parents=True, exist_ok=False)
    primary[["ts", "grp", "y", "smp", "k", *names]].to_parquet(directory / "primary_fit_matrix.parquet", index=False)
    forecasts = primary[names].to_numpy()
    actual = primary.y.to_numpy()
    weight = (primary.smp*primary.k).to_numpy()
    assert np.isfinite(forecasts).all() and np.isfinite(actual).all() and np.isfinite(weight).all() and (weight >= 0).all()
    scale = max(float(np.abs(forecasts).max()), float(np.abs(actual).max()), 1.)
    x = forecasts/scale
    y = actual/scale
    count, members = x.shape
    constraints = vstack([hstack([csr_matrix(x), -eye(count)]), hstack([-csr_matrix(x), -eye(count)])], format="csc")
    rhs = np.concatenate([y, -y])
    equality = hstack([csr_matrix(np.ones((1, members))), csr_matrix((1, count))], format="csc")
    costs = np.concatenate([np.zeros(members), weight/weight.sum()])
    options = {"threads": 2, "primal_feasibility_tolerance": 1e-8, "dual_feasibility_tolerance": 1e-8}
    started = time.monotonic()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = linprog(costs, A_ub=constraints, b_ub=rhs, A_eq=equality, b_eq=np.ones(1), bounds=(0., None), method="highs", options=options)
    warning_records = [{"category": w.category.__name__, "message": str(w.message)} for w in caught]
    for warning in caught:
        warnings.showwarning(warning.message, warning.category, warning.filename, warning.lineno)
    assert result.success and result.status == 0, result.message
    weights = result.x[:members]
    residual = float(np.max(constraints@result.x-rhs))
    dual = float(rhs@result.ineqlin.marginals+result.eqlin.marginals[0])
    assert weights.min() >= 0 and abs(weights.sum()-1) < 1e-9 and residual <= 1e-7
    assert abs(result.fun-dual) < 1e-7
    measured = float(np.sum(weight*np.abs(forecasts@weights-actual)))
    objective = float(result.fun*scale*weight.sum())
    assert abs(objective-measured) <= max(1e-5, measured*1e-7)
    save_json(directory / "optimization.json", {"members": names, "weights": weights.tolist(), "weight_sum": float(weights.sum()), "minimum_weight": float(weights.min()), "solver_success": bool(result.success), "solver_status": int(result.status), "solver_message": result.message, "solver_iterations": int(result.nit), "solver_options": options, "warnings": warning_records, "max_primal_residual": residual, "scaled_dual_gap": float(result.fun-dual), "solver_W": objective, "recomputed_W": measured, "fit_rows": len(primary), "fit_min_ts": str(primary.ts.min()), "fit_max_ts": str(primary.ts.max()), "fit_matrix_sha256": digest(directory / "primary_fit_matrix.parquet"), "model_fits": 0})
    receipt(directory / "solver_runtime.json", [time.monotonic()-started])
    return weights


def normalized_fit(seed: int, leaves: int, trees: int, train: pd.DataFrame, selection: pd.DataFrame, names: list[str], directory: Path) -> pd.DataFrame:
    """Only tree count/leaf count differ from the default normalized member."""
    directory.mkdir(parents=True, exist_ok=False)
    params = {"n_estimators": trees, "learning_rate": .03, "num_leaves": leaves, "min_child_samples": 50, "objective": "regression_l1", "subsample": .8, "subsample_freq": 1, "colsample_bytree": .8, "random_state": None if seed == 0 else seed, "n_jobs": 2, "verbose": -1}
    scale = normalizer(train.cosz.to_numpy())
    model = lgb.LGBMRegressor(**params)
    started = time.monotonic()
    model.fit(train[names], train.cf.to_numpy()/scale, sample_weight=scale)
    result = selection[["ts", "grp"]].copy()
    result["p_raw"] = model.predict(selection[names])*normalizer(selection.cosz.to_numpy())*selection.capacity_kw.to_numpy()
    assert np.isfinite(result.p_raw).all()
    result.to_parquet(directory / "daylight_raw.parquet", index=False)
    model.booster_.save_model(str(directory / "model.txt"))
    save_json(directory / "config.json", {"variant": "lgb_normalized", "seed": seed, "parameters": params, "features": names, "normalization": True, "train_end": str(train.ts.max()), "evaluation_start": str(selection.ts.min()), "evaluation_end": str(selection.ts.max())})
    receipt(directory / "runtime.json", [time.monotonic()-started])
    print("NORMALIZED FIT", leaves, trees, seed, flush=True)
    return result
