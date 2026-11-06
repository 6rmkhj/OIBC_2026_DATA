# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "lightgbm", "scikit-learn", "joblib"]
# ///
"""Two profile learners using persisted train-only constant-column masks."""
from wave_common import save_json, receipt
from learner_models import preprocessing
from profile_features import column_mask
from site_features import normalizer
from pathlib import Path
import time
import warnings
import joblib
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- original group interface
import lightgbm as lgb
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler


def fit(learner: str, seed: int, train: pd.DataFrame, selection: pd.DataFrame, names: list[str], directory: Path) -> pd.DataFrame:
    directory.mkdir(parents=True, exist_ok=False)
    selected = column_mask(train, names)
    assert selected and not {"energy", "cf", "y", "smp", "k"} & set(selected)
    save_json(directory / "feature_mask.json", {"candidate_columns": names, "selected_columns": selected, "dropped_columns": [n for n in names if n not in selected], "fitted_on": "training only", "train_end": str(train.ts.max())})
    started = time.monotonic()
    details = {}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if learner == "lgb":
            params = {"n_estimators": 400, "learning_rate": .03, "num_leaves": 63, "min_child_samples": 50, "objective": "regression_l1", "subsample": .8, "subsample_freq": 1, "colsample_bytree": .8, "random_state": None if seed == 0 else seed, "n_jobs": 2, "verbose": -1}
            model = lgb.LGBMRegressor(**params)
            scale = normalizer(train.cosz.to_numpy())
            model.fit(train[selected], train.cf.to_numpy()/scale, sample_weight=scale)
            prediction = model.predict(selection[selected])*normalizer(selection.cosz.to_numpy())
            model.booster_.save_model(str(directory / "model.txt"))
        else:
            assert learner == "mlp"
            transform, x_train, x_selection = preprocessing(train[selected], selection[selected])
            scaler = StandardScaler()
            target = scaler.fit_transform(train.cf.to_numpy().reshape(-1, 1)).ravel()
            params = {"hidden_layer_sizes": (64, 32), "activation": "relu", "solver": "adam", "alpha": .1, "batch_size": 128, "learning_rate_init": .001, "max_iter": 400, "tol": 1e-5, "n_iter_no_change": 20, "early_stopping": False, "random_state": seed}
            model = MLPRegressor(**params)
            model.fit(x_train, target)
            prediction = scaler.inverse_transform(model.predict(x_selection).reshape(-1, 1)).ravel()
            joblib.dump(transform, directory / "input_preprocessing.joblib")
            joblib.dump(scaler, directory / "target_scaler.joblib")
            joblib.dump(model, directory / "model.joblib")
            details = {"iterations": model.n_iter_, "loss_curve": model.loss_curve_}
    for warning in caught:
        warnings.showwarning(warning.message, warning.category, warning.filename, warning.lineno)
    raw = selection[["ts", "grp"]].copy()
    raw["p_raw"] = prediction*selection.capacity_kw.to_numpy()
    assert np.isfinite(raw.p_raw).all()
    raw.to_parquet(directory / "daylight_raw.parquet", index=False)
    save_json(directory / "config.json", {"learner": learner, "seed": seed, "parameters": params, "feature_count": len(selected), "train_end": str(train.ts.max()), "evaluation_start": str(selection.ts.min()), "evaluation_end": str(selection.ts.max())})
    save_json(directory / "convergence.json", {"warnings": [{"category": w.category.__name__, "message": str(w.message)} for w in caught], **details})
    receipt(directory / "runtime.json", [time.monotonic()-started], model_threads=2 if learner == "lgb" else 1)
    print("PROFILE FIT", str(directory), len(names), "->", len(selected), flush=True)
    return raw
