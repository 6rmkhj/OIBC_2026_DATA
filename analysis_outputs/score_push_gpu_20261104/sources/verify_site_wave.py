# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn"]
# ///
# Run after both site runners exit: python submission/score_push/verify_site_wave.py
"""No-fit integrity checks for bounded recent/site development artifacts."""
from wave_common import OUT, ROOT, configure, save_json, digest, metrics, optimal_weight
from site_features import FOLDS, FEATURES
import site_features
import inspect
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- compare exact saved numerical artifacts
import pyarrow.parquet as pq


def main() -> None:
    configure()
    out = OUT / "site_wave"
    evidence = out / "evidence"
    evidence.mkdir(exist_ok=True)
    site_features.self_check()
    original = site_features.normalizer
    source = inspect.getsource(original)
    mutated = source.replace("1.098*positive", "1.0*positive")
    assert mutated != source
    namespace = {"np": np}
    exec(compile(mutated, "haurwitz_mutant", "exec"), namespace)
    site_features.normalizer = namespace["normalizer"]
    try:
        site_features.self_check()
    except AssertionError:
        print("PASS incorrect Haurwitz coefficient mutant rejected", flush=True)
    else:
        raise AssertionError("Haurwitz mutant survived")
    finally:
        site_features.normalizer = original
    site_features.self_check()
    records = []
    for fold, cutoff_text, end_text in FOLDS:
        cutoff = pd.Timestamp(cutoff_text, tz="Asia/Seoul")
        end = pd.Timestamp(end_text, tz="Asia/Seoul")
        cache = out / "cache" / fold
        assert not {"energy", "cf", "y"} & set(pq.read_schema(cache / "selection.parquet").names)
        assert not {"energy", "cf", "y", "ts", "night"} & set(FEATURES)
        train_keys = pd.read_parquet(cache / "train.parquet", columns=["site_id", "ts"])
        eval_keys = pd.read_parquet(cache / "selection.parquet", columns=["site_id", "ts", "night"])
        assert train_keys.ts.max() <= cutoff < eval_keys.ts.min() and eval_keys.ts.max() <= end
        labels = pd.read_parquet(cache / "labels.parquet")
        expected_count = 17568 if fold == "primary" else 13104
        assert len(labels) == expected_count
        unseen = ~eval_keys.site_id.isin(train_keys.site_id.unique())
        for path in (out / fold).glob("*/seed*/site_predictions.parquet"):
            predictions = pd.read_parquet(path)
            pd.testing.assert_frame_equal(predictions[["site_id", "ts"]], eval_keys[["site_id", "ts"]], check_exact=True)
            assert np.isfinite(predictions.p).all() and predictions.p.ge(0).all()
            assert predictions.loc[eval_keys.night, "p"].eq(0).all()
            aggregated = predictions.groupby(["ts", "grp"], as_index=False, observed=True).p.sum().rename(columns={"p": "p_bu_new"})
            saved = pd.read_parquet(path.parent / "group_predictions.parquet")
            pd.testing.assert_frame_equal(aggregated, saved, check_exact=True)
            assert len(saved) == expected_count
            runtime = json.loads((path.parent / "runtime.json").read_text())
            assert runtime["parallel_fits"] == 1 and runtime["model_n_jobs"] == 2 and runtime["priority_class"] == 16384
            assert runtime["pyarrow_cpu"] == runtime["pyarrow_io"] == 2
            assert runtime["environment"] == {"OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"}
            records.append({"path": str(path.relative_to(OUT)), "sites_rows": len(predictions), "unseen_history_rows": int(unseen.sum()), "unseen_history_predictions_finite": bool(np.isfinite(predictions.loc[unseen, "p"]).all()), "group_rows": len(saved), "peak_working_set_bytes": runtime["peak_working_set_bytes"]})
        for path in (out / fold).rglob("score.json"):
            frame = pd.read_parquet(path.parent / "predictions.parquet")
            assert len(frame) == expected_count and frame.ts.max() <= end
            recomputed = metrics(frame)
            recorded = json.loads(path.read_text())
            assert abs(recorded["W_pct"]-recomputed["W_pct"]) < 1e-12
            assert frame[["ts", "grp"]].merge(labels[["ts", "grp"]], on=["ts", "grp"], how="outer", indicator=True)._merge.eq("both").all()
    calibrations = json.loads((out / "all_primary_calibrations.json").read_text())
    for row in calibrations:
        primary = pd.read_parquet(out / "primary" / row["variant"] / "screen" / row["direct"] / "predictions.parquet")
        alpha = optimal_weight(primary.rename(columns={"p_bu_new": "p_bu"}), .7149301735712863)
        assert alpha == row["alpha_primary_only"]
        for fold, _, _ in FOLDS:
            applied = pd.read_parquet(out / fold / row["variant"] / "screen_primary_calibration" / row["direct"] / "predictions.parquet")
            assert applied.alpha.eq(alpha).all()
            np.testing.assert_array_equal(applied.p, (1-alpha)*applied.p_bu_new+alpha*applied.p_dir)
    for directory in (OUT / "recent/sources", out / "sources", out / "calibration_sources"):
        hashes = json.loads((directory / "hashes.json").read_text())
        for name, expected in hashes.items():
            assert digest(directory / name) == expected
    for destination in (OUT / "recent", out):
        manifest = json.loads((destination / "manifest.json").read_text())
        inputs = manifest.get("inputs_sha256", manifest.get("input_sha256"))
        outputs = manifest.get("outputs_sha256", manifest.get("output_sha256"))
        for name, expected in inputs.items():
            assert digest(ROOT / name) == expected
        for name, expected in outputs.items():
            assert digest(destination / name) == expected
    summary = {"site_fit_count": len(records), "site_fits": records, "feature_selection_target_free": True, "all_train_eval_cutoffs_verified": True, "site_and_group_keys_exact": True, "all_predictions_finite": True, "normalization_mutant_rejected": True, "primary_only_alpha_transfer_verified": True, "primary_calibrated_pairs": len(calibrations), "all_input_output_source_hashes_verified": True, "confirmation_loaded": False, "test_loaded": False}
    save_json(evidence / "verification.json", summary)
    print("PASS paired site keys/night zeros/unseen history, bounded dates, six primary-alpha transfers, unchanged input/output/source hashes", flush=True)


if __name__ == "__main__":
    main()
