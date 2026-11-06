# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn"]
# ///
# Run after site_wave.py exits: python submission/score_push/site_calibrate.py
"""Primary-only blend transfer for every screened site/direct pair."""
from wave_common import ALPHA, configure, snapshots, optimal_weight, save_json, score, receipt, digest
from site_wave import DEST, VARIANTS, fit_predict, evaluate_group, direct_labels
from site_features import FOLDS
import gc
import json
import pandas as pd  # noqa: PANDAS_OK -- frozen interface


def main() -> None:
    configure()
    assert (DEST / "results.json").exists(), "Original synchronous family must finish first"
    snapshots(DEST / "calibration_sources")
    baseline = {"primary": 12.695950143757269, "recent": 11.639886825195315}
    pairs = []
    for variant in VARIANTS:
        for direct in ("incumbent", "rich"):
            primary = pd.read_parquet(DEST / "primary" / variant / "screen" / direct / "predictions.parquet")
            alpha = optimal_weight(primary.rename(columns={"p_bu_new": "p_bu"}), ALPHA)
            scores = {}
            for fold, _, _ in FOLDS:
                frame = pd.read_parquet(DEST / fold / variant / "screen" / direct / "predictions.parquet")
                frame = frame.assign(alpha=alpha, p=(1-alpha)*frame.p_bu_new+alpha*frame.p_dir)
                scores[fold] = score(frame, DEST / fold / variant / "screen_primary_calibration" / direct)
            pairs.append({"variant": variant, "direct": direct, "alpha_primary_only": alpha, "scores": scores, "mean_relative_loss": sum(scores[f]/baseline[f] for f, _, _ in FOLDS)/2, "both_folds_improve": all(scores[f] < baseline[f] for f, _, _ in FOLDS)})
            print("PRIMARY ALPHA TRANSFER", variant, direct, alpha, scores, flush=True)
    ranking = sorted(pairs, key=lambda item: item["mean_relative_loss"])
    save_json(DEST / "all_primary_calibrations.json", ranking)
    original_extra_seeds = (DEST / "ensemble_scores.json").exists()
    best = ranking[0]
    followup = None
    if best["both_folds_improve"] and not original_extra_seeds:
        variant = best["variant"]
        direct = best["direct"]
        for fold, _, _ in FOLDS:
            train = pd.read_parquet(DEST / "cache" / fold / "train.parquet")
            selection = pd.read_parquet(DEST / "cache" / fold / "selection.parquet")
            pieces = [pd.read_parquet(DEST / fold / variant / "seed0/group_predictions.parquet")]
            for seed in (1, 2):
                pieces.append(fit_predict(variant, seed, train, selection, DEST / fold / variant / f"seed{seed}"))
            averaged = pd.concat(pieces).groupby(["ts", "grp"], as_index=False, observed=True).p_bu_new.mean()
            evaluate_group(averaged, direct_labels(fold), DEST / fold / variant / "calibration_qualified_ensemble")
            del train, selection, pieces, averaged
            gc.collect()
        primary = pd.read_parquet(DEST / "primary" / variant / "calibration_qualified_ensemble" / direct / "predictions.parquet")
        alpha = optimal_weight(primary.rename(columns={"p_bu_new": "p_bu"}), ALPHA)
        scores = {}
        for fold, _, _ in FOLDS:
            frame = pd.read_parquet(DEST / fold / variant / "calibration_qualified_ensemble" / direct / "predictions.parquet")
            scores[fold] = score(frame.assign(alpha=alpha, p=(1-alpha)*frame.p_bu_new+alpha*frame.p_dir), DEST / fold / variant / "ensemble_primary_calibration" / direct)
        followup = {"variant": variant, "direct": direct, "alpha_primary_only": alpha, "scores": scores, "mean_relative_loss": sum(scores[f]/baseline[f] for f, _, _ in FOLDS)/2}
    receipt(DEST / "calibration_receipt.json", [])
    save_json(DEST / "calibration_summary.json", {"all_screen_pairs_primary_calibrated": 6, "original_extra_seed_variant_preserved": original_extra_seeds, "best_screen_pair": best, "newly_qualified_followup": followup, "recent_alpha_fits": 0, "outputs_sha256": {str(p.relative_to(DEST)): digest(p) for p in DEST.rglob("*.parquet")}})
    print("CALIBRATION COMPLETE", best, followup, flush=True)


if __name__ == "__main__":
    main()
