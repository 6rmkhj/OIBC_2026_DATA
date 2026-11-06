# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "joblib"]
# ///
# Run after profile_wave.py exits: python submission/score_push/profile_verify.py
"""No-fit profile/model replay, mask isolation, score and monthly evidence."""
from wave_common import configure, OUT, ROOT, save_json, digest, metrics, optimal_weight
from profile_wave import DEST, FOLDS, REFERENCE, prepare
from profile_features import column_mask, self_check
from learner_models import preprocessing
from site_features import normalizer
import json
import joblib
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen numerical interface
import lightgbm as lgb


def main() -> None:
    configure()
    evidence = DEST / "evidence"
    evidence.mkdir(exist_ok=True)
    self_check()
    prefit = json.loads((DEST / "prefit_checks.json").read_text())
    assert all(prefit.values())
    cache_manifest = json.loads((DEST / "cache/manifest.json").read_text())
    assert not {"energy", "cf", "y"} & set(cache_manifest["projected_columns"])
    models = []
    for representation in ("cells", "stations"):
        profile = pd.read_parquet(DEST / "cache" / f"{representation}.parquet")
        assert not profile.duplicated(["ts", "grp"]).any()
        assert profile.ts.max() <= pd.Timestamp("2025-03-01", tz="Asia/Seoul")
        prefixes = ["cells_"] if representation == "cells" else ["wa_station_", "wb_station_"]
        for prefix in prefixes:
            shares = [name for name in profile if name.startswith(prefix) and name.endswith("_share")]
            np.testing.assert_allclose(profile[shares].sum(axis=1), 1., atol=1e-6)
        del profile
        datasets = prepare(representation)
        for fold in FOLDS:
            train, selection, labels, names = datasets[fold]
            for config_path in (DEST / fold).glob(f"{representation}_*/seed*/config.json"):
                directory = config_path.parent
                config = json.loads(config_path.read_text())
                mask = json.loads((directory / "feature_mask.json").read_text())
                selected = mask["selected_columns"]
                assert selected == column_mask(train, names) and mask["candidate_columns"] == names
                assert not {"energy", "cf", "y", "smp", "k"} & set(selected)
                if config["learner"] == "lgb":
                    model = lgb.Booster(model_file=str(directory / "model.txt"))
                    prediction = model.predict(selection[selected], num_threads=2)*normalizer(selection.cosz.to_numpy())
                else:
                    transform = joblib.load(directory / "input_preprocessing.joblib")
                    scaler = joblib.load(directory / "target_scaler.joblib")
                    model = joblib.load(directory / "model.joblib")
                    independent, _, x_selection = preprocessing(train[selected], selection[selected])
                    np.testing.assert_array_equal(transform[0].statistics_, independent[0].statistics_)
                    np.testing.assert_array_equal(transform[1].mean_, independent[1].mean_)
                    np.testing.assert_array_equal(transform[1].scale_, independent[1].scale_)
                    np.testing.assert_allclose(scaler.mean_, [train.cf.mean()], rtol=1e-12)
                    prediction = scaler.inverse_transform(model.predict(x_selection).reshape(-1, 1)).ravel()
                raw = pd.read_parquet(directory / "daylight_raw.parquet")
                pd.testing.assert_frame_equal(raw[["ts", "grp"]], selection[["ts", "grp"]].reset_index(drop=True), check_exact=True)
                np.testing.assert_allclose(raw.p_raw, prediction*selection.capacity_kw.to_numpy(), rtol=1e-12, atol=1e-8)
                runtime = json.loads((directory / "runtime.json").read_text())
                assert runtime["priority_class"] == 16384 and runtime["parallel_fits"] == 1 and runtime["model_n_jobs"] <= 2
                assert runtime["pyarrow_cpu"] == runtime["pyarrow_io"] == 2
                assert runtime["environment"] == {"OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"}
                models.append({"path": str(directory.relative_to(DEST)), "mask_train_only_and_replay_passed": True, "candidate_features": len(names), "selected_features": len(selected), "peak_working_set_bytes": runtime["peak_working_set_bytes"], "warnings": json.loads((directory / "convergence.json").read_text())["warnings"], "artifact_sha256": {p.name: digest(p) for p in directory.iterdir() if p.is_file()}})
    results = json.loads((DEST / "results.json").read_text())
    monthly = []
    for row in results["records"]:
        primary_path = DEST / "primary" / row["id"] / row["stage"] / "complement/predictions.parquet"
        primary = pd.read_parquet(primary_path)
        alpha = optimal_weight(primary.assign(p_bu=primary.p_reference, p_dir=primary.p_new), 0.)
        assert alpha == row["alpha_primary_only"]
        for fold in FOLDS:
            directory = DEST / fold / row["id"] / row["stage"]
            frame = pd.read_parquet(directory / "complement/predictions.parquet")
            assert len(frame) == (17568 if fold == "primary" else 13104)
            assert not frame.duplicated(["ts", "grp"]).any()
            assert frame.ts.max() <= pd.Timestamp("2024-06-01" if fold == "primary" else "2025-03-01", tz="Asia/Seoul")
            assert np.isfinite(frame[["p", "p_new", "p_reference", "y", "smp", "k"]]).all().all()
            assert frame.p.ge(0).all() and frame.alpha.eq(alpha).all()
            np.testing.assert_array_equal(frame.p, (1-alpha)*frame.p_reference+alpha*frame.p_new)
            assert abs(metrics(frame)["W_pct"]-row["scores"][fold]) < 1e-12
            assert abs(metrics(frame.assign(p=frame.p_reference))["W_pct"]-REFERENCE[fold]) < 1e-10
            pure = pd.read_parquet(directory / "pure/predictions.parquet")
            assert abs(metrics(pure)["W_pct"]-json.loads((directory / "pure/score.json").read_text())["W_pct"]) < 1e-12
            base_path = OUT / "refinement_wave" / fold / "recipes/leaves63_trees400_ensemble"
            baseline = pd.read_parquet(base_path / "predictions.parquet", columns=["ts", "grp", "y", "smp", "k"])
            aligned = frame.merge(baseline, on=["ts", "grp"], how="outer", validate="one_to_one", suffixes=("", "_baseline"), indicator=True)
            assert aligned._merge.eq("both").all()
            for name in ("y", "smp", "k"):
                np.testing.assert_array_equal(aligned[name], aligned[f"{name}_baseline"])
            base_diag = pd.read_csv(base_path / "diagnostics.csv")
            diag = pd.read_csv(directory / "complement/diagnostics.csv")
            joined = diag.merge(base_diag, on="slice", validate="one_to_one", suffixes=("_candidate", "_baseline"))
            joined["delta_W_pct"] = joined.W_pct_candidate-joined.W_pct_baseline
            monthly.append(joined.assign(fold=fold, variant=row["id"], stage=row["stage"]))
    pd.concat(monthly, ignore_index=True).to_csv(evidence / "monthly_comparison.csv", index=False)
    for name, expected in cache_manifest["input_sha256"].items():
        assert digest(ROOT / name) == expected
    for name, expected in cache_manifest["cache_sha256"].items():
        assert digest(DEST / "cache" / name) == expected
    manifest = json.loads((DEST / "manifest.json").read_text())
    for name, expected in manifest["input_sha256"].items():
        assert digest(ROOT / name) == expected
    for name, expected in manifest["output_sha256"].items():
        assert digest(DEST / name) == expected
    for name, expected in json.loads((DEST / "sources/hashes.json").read_text()).items():
        assert digest(DEST / "sources" / name) == expected
    save_json(evidence / "verification.json", {"models": models, "model_count": len(models), "profile_share_identity_verified": True, "prefit_checks_passed": True, "mask_and_preprocessing_train_only_verified": True, "serialized_replays_passed": True, "all_keys_labels_finite_predictions_and_dates_verified": True, "primary_only_alpha_transfer_verified": True, "input_output_executed_source_hashes_verified": True, "incumbent_retained": results["incumbent_retained"], "confirmation_loaded": False, "test_loaded": False})
    print("PASS profile semantics, saved masks/model replay, exact keys/labels/cutoffs, primary-only alpha transfer, monthly diagnostics and hashes", flush=True)


if __name__ == "__main__":
    main()
