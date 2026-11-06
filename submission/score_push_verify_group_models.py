# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "lightgbm", "pandas"]
# ///
# How to run: imported by score_push_verify_group.py after the wave is terminal.
"""Independent saved-tree sample replay and signed-site aggregation checks."""
from __future__ import annotations

import json
from math import isclose
from typing import Final

import lightgbm as lgb
import numpy as np
import pyarrow.parquet as pq

from score_push_verify_group_data import OUT, sha, table_keys

ARMS: Final = {"group_l01": .1, "group_l1": 1., "site_control": .1}


def verify_models(arm: str, fold: str) -> tuple[dict, list]:  # noqa: DICT_OK -- numerical evidence keyed by timestamp/group
    directory = OUT / "data" / fold
    info = json.loads((directory / "features.json").read_text())
    evaluation = pq.read_table(directory / "evaluation.parquet")
    keys = ["ts", "site_id", "grp", "capacity_kw", "night"]
    night = evaluation["night"].to_numpy()
    day_indices = np.flatnonzero(~night)
    sample = day_indices[np.unique(np.linspace(0, len(day_indices) - 1, 2048, dtype=int))]
    sample_features = evaluation.take(sample).select(info["features"]).to_pandas()
    cap = evaluation["capacity_kw"].to_numpy()
    group_keys = sorted(set(table_keys(evaluation, "grp")))
    group_map = {key: i for i, key in enumerate(group_keys)}
    group_ids = np.array([group_map[key] for key in table_keys(evaluation, "grp")])
    groups = pq.read_table(directory / "groups.parquet")
    train_rows = pq.read_table(directory / "rows.parquet", columns=["weight", "cf"])
    target, wg = groups["target"].to_numpy(), groups["group_weight"].to_numpy()
    weight = train_rows["weight"].to_numpy()
    cf = train_rows["cf"].to_numpy().astype(np.float64)
    first_l1 = np.dot(wg, abs(target))
    regularizer = ARMS[arm]
    if arm == "site_control":
        first_smooth = np.dot(weight, np.hypot(cf, .05) - .05)
    else:
        first_smooth = np.dot(wg, np.hypot(target, .05) - .05)
    first_smooth += regularizer / 2 * np.dot(weight, cf ** 2)
    predictions, evidence = [], []
    for seed in range(3):
        trial = OUT / "trials" / arm / fold / f"seed{seed}"
        raw = pq.read_table(trial / "site_raw.parquet")
        assert raw.select(keys).equals(evaluation.select(keys))
        values = raw["cf_raw"].to_numpy()
        assert np.isfinite(values).all() and (values[night] == 0).all()
        np.testing.assert_array_equal(raw["energy_raw"].to_numpy(), values * cap)
        np.testing.assert_array_equal(np.load(trial / "replay_raw.npy"), values[~night])
        group_raw = pq.read_table(trial / "group_raw.parquet")
        assert table_keys(group_raw, "grp") == group_keys
        np.testing.assert_allclose(group_raw["p_raw"].to_numpy(), np.bincount(group_ids, weights=values * cap), rtol=1e-12, atol=1e-7)
        model = lgb.Booster(model_file=str(trial / "model.txt"))
        assert model.current_iteration() == model.num_trees() == 1000
        assert model.feature_name() == info["features"]
        assert model.pandas_categorical == [info["categories"][name] for name in ("site_id", "wa_station", "wb_station")]
        parameters = model.params
        for name, expected in (("objective", "custom"), ("num_threads", 16), ("num_leaves", 127), ("min_data_in_leaf", 200),
                               ("bagging_fraction", 1), ("bagging_freq", 0), ("seed", seed), ("feature_fraction_seed", seed),
                               ("lambda_l1", 0), ("lambda_l2", 0), ("max_bin", 255), ("device_type", "cpu")):
            assert parameters[name] == expected, (name, parameters[name], expected)
        for name, expected in (("learning_rate", .08), ("feature_fraction", .8), ("min_sum_hessian_in_leaf", .001)):
            assert isclose(parameters[name], expected, rel_tol=1e-12)
        assert parameters["force_col_wise"] and parameters["deterministic"]
        np.testing.assert_array_equal(model.predict(sample_features, raw_score=True, num_threads=1), values[sample])
        replay = json.loads((trial / "replay.json").read_text())
        assert replay["passed"] and replay["max_absolute_error"] == 0 and replay["night_exact_zero"]
        assert replay["negative_cf_rows"] == int((values < 0).sum())
        assert replay["model_sha256"] == sha(trial / "model.txt") and replay["raw_sha256"] == sha(trial / "site_raw.parquet")
        iterations = json.loads((trial / "iteration.json").read_text())
        assert iterations["actual_iteration"] == iterations["requested_iteration"] == iterations["objective_calls"] == 1000
        assert not iterations["loaded_existing_model"]
        diagnostics = json.loads((trial / "diagnostics.json").read_text())
        assert [r["iteration"] for r in diagnostics] == list(range(0, 1001, 100))
        assert isclose(diagnostics[0]["group_weighted_L1"], first_l1, rel_tol=1e-12)
        assert isclose(diagnostics[0]["declared_smooth_objective"], first_smooth, rel_tol=1e-12)
        losses = np.array([r["declared_smooth_objective"] for r in diagnostics])
        assert np.isfinite(losses).all() and losses[-1] < losses[0]
        evidence.append({"trial": str(trial.relative_to(OUT)), "root_sample_replay_rows": len(sample), "root_sample_replay_exact": True,
                         "full_saved_replay_values_verified": len(day_indices), "negative_site_rows": int((values < 0).sum()),
                         "initial_smooth_loss": float(losses[0]), "final_smooth_loss": float(losses[-1]),
                         "largest_logged_smooth_increase": float(np.diff(losses).max())})
        predictions.append(values)
    average = np.mean(predictions, axis=0)
    saved = pq.read_table(OUT / "comparisons" / arm / "ensemble" / fold / "signed_site_ensemble.parquet")
    assert saved.select(keys).equals(evaluation.select(keys))
    np.testing.assert_array_equal(saved["cf_raw"].to_numpy(), average)
    np.testing.assert_array_equal(saved["energy_raw"].to_numpy(), average * cap)
    summed = np.bincount(group_ids, weights=average * cap)
    coverage = pq.read_table(directory / "coverage.parquet")
    night_keys = {key for key, is_night in zip(table_keys(coverage, "grp"), coverage["night"].to_pylist(), strict=True) if is_night}
    assert all(summed[group_map[key]] == 0 for key in night_keys)
    return dict(zip(group_keys, np.maximum(summed, 0), strict=True)), evidence
