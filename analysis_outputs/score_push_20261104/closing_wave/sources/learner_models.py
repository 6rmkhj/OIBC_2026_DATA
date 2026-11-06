# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "joblib"]
# ///
"""Four bounded group learners with train-only numerical preprocessing."""
from wave_common import receipt, save_json
from site_features import normalizer
from pathlib import Path
import time
import warnings
import joblib
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen group contract
import lightgbm as lgb
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.kernel_approximation import Nystroem
from sklearn.svm import LinearSVR


def preprocessing(train: pd.DataFrame, selection: pd.DataFrame):
    """Fit medians/scales on training only; preserve entirely missing columns."""
    transform = make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler())
    x_train = transform.fit_transform(train)
    x_selection = transform.transform(selection)
    assert np.isfinite(x_train).all() and np.isfinite(x_selection).all()
    return transform, x_train, x_selection


def self_check() -> None:
    train = pd.DataFrame({"x": [1., 2., 3.], "missing": [np.nan, np.nan, np.nan]})
    selection = pd.DataFrame({"x": [np.nan, 1e12], "missing": [np.nan, 2.]})
    transform, x, future = preprocessing(train, selection)
    expected = np.array([-np.sqrt(1.5), 0., np.sqrt(1.5)])
    np.testing.assert_allclose(x[:, 0], expected)
    assert future[0, 0] == 0. and np.isfinite(future).all() and future.shape == (2, 2)
    medians = transform[0].statistics_.copy()
    means = transform[1].mean_.copy()
    transform.transform(selection*1e8)
    np.testing.assert_array_equal(transform[0].statistics_, medians)
    np.testing.assert_array_equal(transform[1].mean_, means)
    scale = normalizer(np.array([0., .5, 1.]))
    target = np.array([.02, .4, .7])
    normalized_prediction = np.array([.5, .6, 1.])
    np.testing.assert_allclose(scale*np.abs(target/scale-normalized_prediction), np.abs(target-scale*normalized_prediction), rtol=1e-12)
    np.testing.assert_allclose(scale**2*(target/scale-normalized_prediction)**2, (target-scale*normalized_prediction)**2, rtol=1e-12)
    scaler = StandardScaler().fit((target/scale).reshape(-1, 1))
    scaled_error = scaler.transform((target/scale).reshape(-1, 1)).ravel()-scaler.transform(normalized_prediction.reshape(-1, 1)).ravel()
    np.testing.assert_allclose(scale**2*scaled_error**2*scaler.scale_[0]**2, (target-scale*normalized_prediction)**2, rtol=1e-12)
    print("PASS train-only imputation/scaling, unseen/all-column NaN handling, group normalized CF-L1/CF-MSE equivalence", flush=True)


def fit(variant: str, seed: int, train: pd.DataFrame, selection: pd.DataFrame, names: list[str], directory: Path) -> pd.DataFrame:
    """Fit one member; keep signed raw daylight output for correct seed averaging."""
    directory.mkdir(parents=True, exist_ok=False)
    assert not {"energy", "cf", "y", "smp", "k"} & set(names)
    normalized = variant in {"lgb_normalized", "mlp_normalized"}
    train_n = normalizer(train.cosz.to_numpy()) if normalized else np.ones(len(train))
    eval_n = normalizer(selection.cosz.to_numpy()) if normalized else np.ones(len(selection))
    target = train.cf.to_numpy()/train_n
    started = time.monotonic()
    details = {}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if variant == "lgb_normalized":
            params = {"n_estimators": 400, "learning_rate": .03, "num_leaves": 31, "min_child_samples": 50, "objective": "regression_l1", "subsample": .8, "subsample_freq": 1, "colsample_bytree": .8, "random_state": None if seed == 0 else seed, "n_jobs": 2, "verbose": -1}
            model = lgb.LGBMRegressor(**params)
            model.fit(train[names], target, sample_weight=train_n)
            prediction = model.predict(selection[names])
            model.booster_.save_model(str(directory / "model.txt"))
        else:
            transform, x_train, x_selection = preprocessing(train[names], selection[names])
            target_scaler = StandardScaler()
            scaled_target = target_scaler.fit_transform(target.reshape(-1, 1)).ravel()
            joblib.dump(transform, directory / "input_preprocessing.joblib")
            joblib.dump(target_scaler, directory / "target_scaler.joblib")
            if variant.startswith("mlp_"):
                params = {"hidden_layer_sizes": (64, 32), "activation": "relu", "solver": "adam", "alpha": .1, "batch_size": 128, "learning_rate_init": .001, "max_iter": 400, "tol": 1e-5, "n_iter_no_change": 20, "early_stopping": False, "random_state": seed}
                model = MLPRegressor(**params)
                model.fit(x_train, scaled_target, sample_weight=train_n**2 if normalized else None)
                prediction = model.predict(x_selection)
                details = {"iterations": model.n_iter_, "loss_curve": model.loss_curve_, "last_loss": model.loss_}
            else:
                assert variant == "kernel_l1"
                kernel = Nystroem(kernel="rbf", n_components=512, gamma=1/len(names), random_state=seed, n_jobs=2)
                z_train = kernel.fit_transform(x_train)
                z_selection = kernel.transform(x_selection)
                assert np.isfinite(z_train).all() and float(np.var(z_train)) > 1e-12
                joblib.dump(kernel, directory / "kernel.joblib")
                params = {"epsilon": 0., "C": 1., "dual": "auto", "max_iter": 10000, "tol": 1e-4, "random_state": seed}
                model = LinearSVR(**params)
                model.fit(z_train, scaled_target)
                prediction = model.predict(z_selection)
                details = {"iterations": model.n_iter_, "kernel_components": 512, "kernel_gamma": 1/len(names), "kernel_train_variance": float(np.var(z_train))}
            prediction = target_scaler.inverse_transform(prediction.reshape(-1, 1)).ravel()
            joblib.dump(model, directory / "model.joblib")
    warning_records = [{"category": warning.category.__name__, "message": str(warning.message)} for warning in caught]
    for warning in caught:
        warnings.showwarning(warning.message, warning.category, warning.filename, warning.lineno)
    elapsed = time.monotonic()-started
    result = selection[["ts", "grp"]].copy()
    result["p_raw"] = prediction*eval_n*selection.capacity_kw.to_numpy()
    assert np.isfinite(result.p_raw).all()
    result.to_parquet(directory / "daylight_raw.parquet", index=False)
    save_json(directory / "config.json", {"variant": variant, "seed": seed, "parameters": params, "features": names, "normalization": normalized, "training_rows": len(train), "prediction_rows": len(selection), "train_end": str(train.ts.max()), "evaluation_start": str(selection.ts.min()), "evaluation_end": str(selection.ts.max()), "input_preprocessing_train_only": variant != "lgb_normalized", "target_standardized_train_only": variant != "lgb_normalized"})
    save_json(directory / "convergence.json", {"warnings": warning_records, **details})
    receipt(directory / "runtime.json", [elapsed], model_threads=2 if variant in {"lgb_normalized", "kernel_l1"} else 1)
    print("FIT", variant, seed, elapsed, "warnings", warning_records, flush=True)
    return result
