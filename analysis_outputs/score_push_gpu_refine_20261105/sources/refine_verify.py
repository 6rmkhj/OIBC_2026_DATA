# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "joblib"]
# ///
# Run after refine_wave.py exits: python submission/score_push/refine_verify.py
"""No-fit model replay, simplex feasibility and reproducible selected recipe."""
from wave_common import configure, OUT, ROOT, save_json, digest, metrics
from refine_wave import DEST, FOLDS
from learner_wave import data
from site_features import normalizer
import json
import joblib
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen numerical contract
import lightgbm as lgb


def main() -> None:
    configure()
    evidence = DEST / "evidence"
    evidence.mkdir(exist_ok=True)
    records = []
    for fold in FOLDS:
        train, selection, labels, names = data(fold)
        for path in (DEST / fold).glob("*/seed*/config.json"):
            directory = path.parent
            config = json.loads(path.read_text())
            assert config["features"] == names and not {"energy", "cf", "y", "smp", "k"} & set(names)
            if config["variant"] == "mlp_cf":
                transform = joblib.load(directory / "input_preprocessing.joblib")
                scaler = joblib.load(directory / "target_scaler.joblib")
                model = joblib.load(directory / "model.joblib")
                prediction = scaler.inverse_transform(model.predict(transform.transform(selection[names])).reshape(-1, 1)).ravel()
            else:
                assert config["variant"] == "lgb_normalized"
                model = lgb.Booster(model_file=str(directory / "model.txt"))
                prediction = model.predict(selection[names], num_threads=2)*normalizer(selection.cosz.to_numpy())
            raw = pd.read_parquet(directory / "daylight_raw.parquet")
            pd.testing.assert_frame_equal(raw[["ts", "grp"]], selection[["ts", "grp"]].reset_index(drop=True), check_exact=True)
            np.testing.assert_allclose(raw.p_raw, prediction*selection.capacity_kw.to_numpy(), rtol=1e-12, atol=1e-8)
            runtime = json.loads((directory / "runtime.json").read_text())
            assert runtime["priority_class"] == 16384 and runtime["parallel_fits"] == 1 and runtime["model_n_jobs"] <= 2
            assert runtime["pyarrow_cpu"] == runtime["pyarrow_io"] == 2
            assert runtime["environment"] == {"OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"}
            records.append({"path": str(directory.relative_to(DEST)), "serialized_replay_passed": True, "peak_working_set_bytes": runtime["peak_working_set_bytes"], "artifact_sha256": {p.name: digest(p) for p in directory.iterdir() if p.is_file()}})
        raws = [pd.read_parquet(OUT / "learner_wave" / fold / "mlp_cf" / f"seed{s}/daylight_raw.parquet") for s in (0, 1, 2)]
        raws += [pd.read_parquet(DEST / fold / "mlp_cf" / f"seed{s}/daylight_raw.parquet") for s in (3, 4)]
        averaged = pd.concat(raws).groupby(["ts", "grp"], as_index=False).p_raw.mean()
        expected = labels[["ts", "grp"]].merge(averaged, on=["ts", "grp"], how="left", validate="one_to_one")
        saved = pd.read_parquet(DEST / fold / "mlp5/pure/predictions.parquet")
        np.testing.assert_array_equal(np.clip(expected.p_raw.fillna(0.), 0., None), saved.p_new)
    recipes = []
    for directory in (DEST / "weights").iterdir():
        optimization = json.loads((directory / "optimization.json").read_text())
        weights = np.array(optimization["weights"])
        names = optimization["members"]
        assert optimization["solver_success"] and optimization["solver_status"] == 0
        assert optimization["solver_options"]["threads"] == 2 and optimization["model_fits"] == 0
        assert weights.min() >= 0 and abs(weights.sum()-1) < 1e-9
        assert optimization["max_primal_residual"] <= 1e-7 and abs(optimization["scaled_dual_gap"]) < 1e-7
        primary = pd.read_parquet(directory / "primary_fit_matrix.parquet")
        assert primary.ts.min() > pd.Timestamp("2023-06-01", tz="Asia/Seoul") and primary.ts.max() <= pd.Timestamp("2024-06-01", tz="Asia/Seoul")
        assert digest(directory / "primary_fit_matrix.parquet") == optimization["fit_matrix_sha256"]
        for fold in FOLDS:
            recipe = DEST / fold / "recipes" / directory.name
            frame = pd.read_parquet(recipe / "predictions.parquet")
            keys = pd.read_parquet(OUT / "learner_wave" / fold / "reference.parquet", columns=["ts", "grp"])
            assert len(frame) == len(keys) and not frame.duplicated(["ts", "grp"]).any()
            assert keys.merge(frame[["ts", "grp"]], on=["ts", "grp"], how="outer", indicator=True)._merge.eq("both").all()
            assert frame.ts.max() <= pd.Timestamp("2024-06-01" if fold == "primary" else "2025-03-01", tz="Asia/Seoul")
            assert np.isfinite(frame.p).all() and frame.p.ge(0).all()
            np.testing.assert_array_equal(frame.p, frame[names].to_numpy()@weights)
            recorded = json.loads((recipe / "score.json").read_text())
            assert abs(metrics(frame)["W_pct"]-recorded["W_pct"]) < 1e-12
            if fold == "primary":
                pd.testing.assert_frame_equal(primary, frame[primary.columns], check_exact=True)
        recipes.append({"id": directory.name, "primary_only_weights_verified": True, "weight_sum": float(weights.sum()), "solver_warnings": optimization["warnings"]})
    manifest = json.loads((DEST / "manifest.json").read_text())
    for name, expected in manifest["input_sha256"].items():
        assert digest(ROOT / name) == expected
    for name, expected in manifest["output_sha256"].items():
        assert digest(DEST / name) == expected
    for name, expected in json.loads((DEST / "sources/hashes.json").read_text()).items():
        assert digest(DEST / "sources" / name) == expected
    result_path = DEST / "clarified_results.json" if (DEST / "clarified_results.json").exists() else DEST / "results.json"
    results = json.loads(result_path.read_text())
    selected = results["selected_recipe"]
    if selected is not None:
        identifier = selected["id"]
        norm = "learner_wave/{fold}/lgb_normalized/screen/pure/predictions.parquet"
        mlp = "learner_wave/{fold}/mlp_cf/ensemble/pure/predictions.parquet"
        if identifier == "three_default_mlp5" or (identifier.endswith("_ensemble") and results["mlp_seed_count_for_three_way"] == 5):
            mlp = "refinement_wave/{fold}/mlp5/pure/predictions.parquet"
        if identifier.endswith("_ensemble"):
            norm = "refinement_wave/{fold}/"+identifier.removesuffix("_ensemble")+"/ensemble/pure/predictions.parquet"
        sources = {"p_reference": ("learner_wave/{fold}/reference.parquet", "p_reference"), "norm": (norm, "p_new"), "mlp": (mlp, "p_new"), "norm_mlp": ("learner_wave/{fold}/mlp_normalized/screen/pure/predictions.parquet", "p_new"), "kernel": ("learner_wave/{fold}/kernel_l1/screen/pure/predictions.parquet", "p_new")}
        for fold in FOLDS:
            recipe = pd.read_parquet(DEST / fold / "recipes" / identifier / "predictions.parquet")
            for name in selected["members"]:
                pattern, column = sources[name]
                member = pd.read_parquet(OUT / pattern.format(fold=fold), columns=["ts", "grp", column]).rename(columns={column: "source_value"})
                aligned = recipe.merge(member, on=["ts", "grp"], validate="one_to_one")
                np.testing.assert_array_equal(aligned[name], aligned.source_value)
        save_json(DEST / "chosen_recipe.json", {**selected, "member_artifacts_relative_to_score_push_output": {name: {"path_pattern": sources[name][0], "column": sources[name][1]} for name in selected["members"]}, "reference_definition": {"rich_direct_weight": .7642694482340047, "bottom_up_weight": 1-.7642694482340047}, "weights_fit_on": "primary only", "confirmation_loaded": False})
    save_json(evidence / "verification.json", {"model_fits": records, "recipes": recipes, "new_model_count": len(records), "all_group_keys_and_cutoffs_verified": True, "five_seed_mean_verified": True, "all_model_replays_passed": True, "simplex_feasibility_and_primary_only_origin_verified": True, "input_output_executed_source_hashes_verified": True, "chosen_recipe_sources_exact": True, "confirmation_loaded": False, "test_loaded": False})
    print("PASS all new model replays, five-seed mean, simplex/dual evidence, primary-only weights, exact group keys/cutoffs and chosen member provenance", flush=True)


if __name__ == "__main__":
    main()
