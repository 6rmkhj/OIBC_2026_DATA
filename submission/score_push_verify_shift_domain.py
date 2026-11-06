# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "joblib", "scikit-learn"]
# ///
# How to run: imported by score_push_verify_shift.py after all fits are terminal.
"""Replay held-day logits and reconstruct every normalized density weight."""
from __future__ import annotations

from datetime import datetime
from math import fsum, isclose

import joblib
import numpy as np
import pyarrow.parquet as pq

from score_push_verify_calibration import ensure_terminal
from score_push_verify_mlp_data import digest, read
from score_push_verify_shift_data import COLUMNS, OUT


def verify_domains() -> tuple[list[tuple[datetime, datetime]], list[dict[str, str | int | float]]]:
    intervals, checks = [], []
    parameters = {"C": .01, "solver": "lbfgs", "max_iter": 1000, "tol": 1e-6,
                  "class_weight": "balanced", "random_state": 0}
    assert read(OUT / "protocol.json")["domain_parameters"] == parameters
    for fold in ("primary", "recent"):
        data = OUT / "data" / fold
        source = np.load(data / "domain_train_matrix.npy", allow_pickle=False)
        target = np.load(data / "domain_evaluation_matrix.npy", allow_pickle=False)
        partition = pq.read_table(data / "domain_fold.parquet")
        folds = partition["domain_fold"].to_numpy()
        ordinals = partition["date_ordinal"].to_numpy()
        keys = partition.select(["ts", "grp"]).to_pylist()
        combined = np.full(len(source), np.nan)
        for split in range(3):
            trial = OUT / "domain_trials" / fold / f"split{split}"
            config = read(trial / "config.json")
            assert config["parameters"] == parameters and config["domain_columns"] == COLUMNS
            assert config["prepared_manifest_sha256"] == digest(OUT / "prepared_manifest.json")
            assert not config["generation_labels_accessed"] and not config["future_energy_accessed"]
            for name, expected in config["input_sha256"].items():
                assert digest(data / name) == expected, name
            held = folds == split
            rows = np.flatnonzero(held)
            assert config["source_fit_rows"] == int((~held).sum()) and config["held_source_rows"] == len(rows)
            assert config["future_fit_rows"] == len(target)
            assert not set(ordinals[held]) & set(ordinals[~held])
            saved = joblib.load(trial / "classifier.joblib")
            assert saved["preprocessing"] == read(data / "preprocessing.json")
            model = saved["classifier"]
            assert model.__class__.__name__ == "LogisticRegression"
            assert all(model.get_params()[name] == value for name, value in parameters.items())
            assert model.fit_intercept and model.l1_ratio == 0.
            np.testing.assert_array_equal(model.classes_, [0, 1])
            assert model.n_features_in_ == 20 and model.coef_.shape == (1, 20) and model.intercept_.shape == (1,)
            native = model.decision_function(source[held])
            algebra = source[held] @ model.coef_[0] + model.intercept_[0]
            np.testing.assert_allclose(native, algebra, rtol=1e-12, atol=1e-12)
            oof = pq.read_table(trial / "oof.parquet")
            assert oof.column_names == ["row_index", "ts", "grp", "domain_fold", "logit"]
            np.testing.assert_array_equal(oof["row_index"].to_numpy(), rows)
            assert oof.select(["ts", "grp"]).to_pylist() == [keys[i] for i in rows]
            np.testing.assert_array_equal(oof["domain_fold"].to_numpy(), folds[held])
            np.testing.assert_allclose(oof["logit"].to_numpy(), native, rtol=1e-12, atol=1e-12)
            assert np.isnan(combined[held]).all()
            combined[held] = oof["logit"].to_numpy()
            # The balanced logistic optimum independently checks the claimed training rows and labels.
            fit_x = np.concatenate([source[~held], target])
            fit_y = np.concatenate([np.zeros(int((~held).sum())), np.ones(len(target))])
            count = len(fit_y)
            weights = np.where(fit_y == 0, count / (2 * (~held).sum()), count / (2 * len(target)))
            logits = fit_x @ model.coef_[0] + model.intercept_[0]
            probabilities = np.exp(-np.logaddexp(0., -logits))
            residual = weights * (probabilities - fit_y)
            gradient = (fit_x.T @ residual + model.coef_[0] / .01) / count
            gradient_max = max(float(np.max(np.abs(gradient))), abs(fsum(residual) / count))
            assert gradient_max <= 1e-4, (fold, split, gradient_max)
            convergence = read(trial / "convergence.json")
            assert convergence["n_iter"] == model.n_iter_.tolist() and convergence["max_iter"] == 1000
            assert not convergence["retuned"] and not any(w["category"] == "ConvergenceWarning" for w in convergence["warnings"])
            replay = read(trial / "replay.json")
            assert replay["passed"] and replay["held_rows"] == len(rows)
            assert replay["classifier_sha256"] == digest(trial / "classifier.joblib")
            assert replay["oof_sha256"] == digest(trial / "oof.parquet")
            runtime = read(trial / "runtime.json")
            assert runtime["new_model_fits"] == runtime["new_domain_fits"] == 1 and runtime["new_generation_fits"] == 0
            assert runtime["priority_class"] == 32 and runtime["pyarrow_cpu"] == runtime["pyarrow_io"] == 4
            assert all(pool["num_threads"] == 16 for pool in runtime["threadpools"])
            receipt = read(trial / "controller_receipt.json")
            assert receipt["exit_code"] == 0 and receipt["exact_worker_absent"]
            ensure_terminal(receipt["identity"])
            intervals.append((datetime.fromisoformat(receipt["started_utc"]), datetime.fromisoformat(receipt["finished_utc"])))
            checks.append({"fold": fold, "split": split, "held_rows": len(rows), "n_iter": int(model.n_iter_[0]),
                           "max_native_logit_difference": float(np.max(np.abs(oof["logit"].to_numpy() - native))),
                           "balanced_logistic_gradient_max": gradient_max})
        assert np.isfinite(combined).all()
        stored = pq.read_table(data / "domain_weights.parquet")
        assert stored.select(["ts", "grp"]).to_pylist() == keys
        np.testing.assert_array_equal(stored["row_index"].to_numpy(), np.arange(len(source)))
        np.testing.assert_array_equal(stored["domain_fold"].to_numpy(), folds)
        np.testing.assert_array_equal(stored["logit"].to_numpy(), combined)
        base = pq.read_table(data / "training_transform.parquet")["sample_weight"].to_numpy()
        np.testing.assert_array_equal(stored["base_weight"].to_numpy(), base)
        ratio = np.exp(combined)
        modifier = np.sqrt(np.minimum(4., np.maximum(.25, ratio)))
        weights = base * modifier * fsum(base) / fsum(base * modifier)
        for name, expected in (("ratio", ratio), ("modifier", modifier), ("sample_weight", weights)):
            np.testing.assert_allclose(stored[name].to_numpy(), expected, rtol=1e-12, atol=1e-12)
        assert np.isfinite(weights).all() and (weights > 0).all()
        assert isclose(fsum(weights), fsum(base), rel_tol=1e-12)
    return intervals, checks
