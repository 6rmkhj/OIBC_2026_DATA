# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "joblib"]
# ///
# Run after learner_wave.py exits: python submission/score_push/learner_verify.py
"""No-fit replay, train-only preprocessing and primary-only blend evidence."""
from wave_common import configure, ROOT, save_json, digest, metrics, optimal_weight
from learner_wave import DEST, FOLDS, REFERENCE, data
import learner_models
from site_features import normalizer
import inspect
import json
import joblib
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- original numerical interface
import lightgbm as lgb


def main() -> None:
    configure()
    evidence = DEST / "evidence"
    evidence.mkdir(exist_ok=True)
    learner_models.self_check()
    source = inspect.getsource(learner_models.preprocessing)
    mutation = source.replace("transform.fit_transform(train)", "transform.fit_transform(pd.concat([train, selection])).copy()[:len(train)]")
    assert mutation != source
    namespace = {"pd": pd, "np": np, "make_pipeline": learner_models.make_pipeline, "SimpleImputer": learner_models.SimpleImputer, "StandardScaler": learner_models.StandardScaler}
    exec(compile(mutation, "preprocessing_leakage_mutant", "exec"), namespace)
    original = learner_models.preprocessing
    learner_models.preprocessing = namespace["preprocessing"]
    try:
        learner_models.self_check()
    except AssertionError:
        print("PASS deliberate evaluation-contaminated preprocessing mutant rejected", flush=True)
    else:
        raise AssertionError("Preprocessing leakage mutant survived")
    finally:
        learner_models.preprocessing = original
    learner_models.self_check()
    fit_records = []
    score_count = 0
    for fold in FOLDS:
        train, selection, labels, names = data(fold)
        assert not {"energy", "cf", "y", "smp", "k"} & set(names)
        assert abs(metrics(labels.assign(p=labels.p_reference))["W_pct"]-REFERENCE[fold]) < 1e-10
        for config_path in (DEST / fold).glob("*/seed*/config.json"):
            directory = config_path.parent
            config = json.loads(config_path.read_text())
            assert config["features"] == names
            normalized = config["normalization"]
            scale = normalizer(selection.cosz.to_numpy()) if normalized else np.ones(len(selection))
            if config["variant"] == "lgb_normalized":
                model = lgb.Booster(model_file=str(directory / "model.txt"))
                prediction = model.predict(selection[names], num_threads=2)
            else:
                transform = joblib.load(directory / "input_preprocessing.joblib")
                scaler = joblib.load(directory / "target_scaler.joblib")
                independently_fitted, x_train, x_selection = learner_models.preprocessing(train[names], selection[names])
                np.testing.assert_array_equal(transform[0].statistics_, independently_fitted[0].statistics_)
                np.testing.assert_array_equal(transform[1].mean_, independently_fitted[1].mean_)
                np.testing.assert_array_equal(transform[1].scale_, independently_fitted[1].scale_)
                train_scale = normalizer(train.cosz.to_numpy()) if normalized else np.ones(len(train))
                target = train.cf.to_numpy()/train_scale
                np.testing.assert_allclose(scaler.mean_, [target.mean()], rtol=1e-12)
                np.testing.assert_allclose(scaler.var_, [target.var()], rtol=1e-12)
                assert np.isfinite(transform.transform(pd.DataFrame(np.nan, index=range(2), columns=names))).all()
                if config["variant"] == "kernel_l1":
                    kernel = joblib.load(directory / "kernel.joblib")
                    x_selection = kernel.transform(x_selection)
                    assert kernel.n_components == 512 and kernel.n_jobs == 2
                model = joblib.load(directory / "model.joblib")
                prediction = scaler.inverse_transform(model.predict(x_selection).reshape(-1, 1)).ravel()
            predicted_raw = prediction*scale*selection.capacity_kw.to_numpy()
            saved_raw = pd.read_parquet(directory / "daylight_raw.parquet")
            pd.testing.assert_frame_equal(saved_raw[["ts", "grp"]], selection[["ts", "grp"]].reset_index(drop=True), check_exact=True)
            np.testing.assert_allclose(saved_raw.p_raw, predicted_raw, rtol=1e-12, atol=1e-8)
            runtime = json.loads((directory / "runtime.json").read_text())
            assert runtime["priority_class"] == 16384 and runtime["parallel_fits"] == 1 and runtime["model_n_jobs"] <= 2
            assert runtime["pyarrow_cpu"] == runtime["pyarrow_io"] == 2
            assert runtime["environment"] == {"OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"}
            convergence = json.loads((directory / "convergence.json").read_text())
            fit_records.append({"model": str(directory.relative_to(DEST)), "model_replay_matches": True, "train_only_preprocessing_verified": True, "peak_working_set_bytes": runtime["peak_working_set_bytes"], "iterations": convergence.get("iterations"), "warnings": convergence["warnings"], "artifact_sha256": {p.name: digest(p) for p in directory.iterdir() if p.is_file()}})
        for score_path in (DEST / fold).rglob("score.json"):
            frame = pd.read_parquet(score_path.parent / "predictions.parquet")
            assert len(frame) == len(labels) and not frame.duplicated(["ts", "grp"]).any()
            aligned = labels[["ts", "grp"]].merge(frame[["ts", "grp"]], on=["ts", "grp"], how="outer", indicator=True)
            assert aligned._merge.eq("both").all()
            assert np.isfinite(frame.p).all() and frame.p.ge(0).all()
            recorded = json.loads(score_path.read_text())
            assert abs(metrics(frame)["W_pct"]-recorded["W_pct"]) < 1e-12
            score_count += 1
    rows = json.loads((DEST / "scores.json").read_text())
    for row in rows:
        primary = pd.read_parquet(DEST / "primary" / row["variant"] / row["stage"] / row["blend"] / "predictions.parquet")
        alpha = optimal_weight(primary.assign(p_bu=primary[row["base_column"]], p_dir=primary.p_new), 0.)
        assert alpha == row["alpha_primary_only"]
        for fold in FOLDS:
            frame = pd.read_parquet(DEST / fold / row["variant"] / row["stage"] / row["blend"] / "predictions.parquet")
            assert frame.alpha.eq(alpha).all()
            np.testing.assert_array_equal(frame.p, (1-alpha)*frame[row["base_column"]]+alpha*frame.p_new)
    manifest = json.loads((DEST / "manifest.json").read_text())
    for name, expected in manifest["input_sha256"].items():
        assert digest(ROOT / name) == expected
    for name, expected in manifest["output_sha256"].items():
        assert digest(DEST / name) == expected
    for name, expected in json.loads((DEST / "sources/hashes.json").read_text()).items():
        assert digest(DEST / "sources" / name) == expected
    save_json(evidence / "verification.json", {"fit_records": fit_records, "score_count": score_count, "primary_only_calibration_pairs": len(rows), "preprocessing_leakage_mutant_rejected": True, "group_loss_equivalence_fixture_passed": True, "all_keys_finite_and_matching": True, "input_output_executed_source_hashes_verified": True, "reference_scores": REFERENCE, "confirmation_loaded": False, "test_loaded": False})
    print("PASS serialized model replay, train-only preprocessing, all group keys, primary-only alpha transfer and frozen hashes", flush=True)


if __name__ == "__main__":
    main()
