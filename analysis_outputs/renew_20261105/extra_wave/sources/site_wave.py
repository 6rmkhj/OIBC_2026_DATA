# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn"]
# ///
# Run: python submission/score_push/site_wave.py
"""Three bounded global-site learners on paired chronological development folds."""
from wave_common import ALPHA, OUT, ROOT, configure, receipt, snapshots, score, save_json, digest, optimal_weight
import gc
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen site interface
import lightgbm as lgb
from site_features import FEATURES, FOLDS, normalizer, prepare, self_check

DEST = OUT / "site_wave"
VARIANTS = ("identity_l1", "identity_l2", "normalized_l1")


def direct_labels(fold: str) -> pd.DataFrame:
    """Read only prebounded development outputs, never unfiltered outer labels."""
    if fold == "primary":
        frame = pd.read_parquet(ROOT / "analysis_outputs/autoresearch_20261103/cache/selection_labels.parquet")
        incumbent = pd.read_parquet(OUT / "trials/baseline_exact/predictions.parquet")
        rich = pd.read_parquet(OUT / "trials/combined_physics/predictions.parquet")
    else:
        frame = pd.read_parquet(OUT / "recent/labels.parquet", columns=["ts", "grp", "y", "p_bu", "smp", "k"])
        incumbent = pd.read_parquet(OUT / "recent/incumbent/predictions.parquet", columns=["ts", "grp", "p_dir"])
        rich = pd.read_parquet(OUT / "recent/rich_fixed_alpha/predictions.parquet", columns=["ts", "grp", "p_dir"])
    frame = frame.rename(columns={"p_bu": "p_bu_old"})
    frame = frame.merge(incumbent.rename(columns={"p_dir": "direct_incumbent"}), on=["ts", "grp"], validate="one_to_one")
    return frame.merge(rich.rename(columns={"p_dir": "direct_rich"}), on=["ts", "grp"], validate="one_to_one")


def fit_predict(variant: str, seed: int, train: pd.DataFrame, selection: pd.DataFrame, directory: Path) -> pd.DataFrame:
    """One pooled fit, followed by zero-at-night full observed-site predictions."""
    directory.mkdir(parents=True, exist_ok=False)
    normalized = variant == "normalized_l1"
    parameters = {"n_estimators": 600, "learning_rate": .04, "num_leaves": 127, "min_child_samples": 200, "subsample": .8, "subsample_freq": 1, "colsample_bytree": .8, "objective": "regression_l2" if variant == "identity_l2" else "regression_l1", "random_state": seed, "n_jobs": 2, "verbose": -1}
    model = lgb.LGBMRegressor(**parameters)
    scale = normalizer(train.cosz.to_numpy()) if normalized else np.ones(len(train))
    started = time.monotonic()
    model.fit(train[list(FEATURES)], train.cf.to_numpy()/scale, sample_weight=scale if normalized else None)
    elapsed = time.monotonic()-started
    daylight = ~selection.night
    result = selection[["ts", "site_id"]].copy()
    result["p"] = 0.
    predicted = model.predict(selection.loc[daylight, list(FEATURES)])
    if normalized:
        predicted *= normalizer(selection.loc[daylight, "cosz"].to_numpy())
    result.loc[daylight, "p"] = np.clip(predicted, 0., None)*selection.loc[daylight, "capacity_kw"].to_numpy()
    assert np.isfinite(result.p).all() and result.p.ge(0).all() and result.loc[~daylight, "p"].eq(0).all()
    assignment = json.loads((ROOT / "analysis_outputs/autoresearch_20261103/cache/assignment.json").read_text())
    result["grp"] = result.site_id.map(assignment)
    assert result.grp.notna().all() and len(result) == len(selection)
    result.to_parquet(directory / "site_predictions.parquet", index=False)
    groups = result.groupby(["ts", "grp"], as_index=False, observed=True).p.sum().rename(columns={"p": "p_bu_new"})
    groups.to_parquet(directory / "group_predictions.parquet", index=False)
    model.booster_.save_model(str(directory / "model.txt"))
    save_json(directory / "config.json", {"variant": variant, "parameters": parameters, "features": FEATURES, "normalization": "Haurwitz / 1000 floored .05" if normalized else "none", "training_rows": len(train), "prediction_rows": len(selection), "daylight_prediction_rows": int(daylight.sum()), "train_end": str(train.ts.max()), "eval_start": str(selection.ts.min()), "eval_end": str(selection.ts.max())})
    receipt(directory / "runtime.json", [elapsed])
    print("FIT", directory.name, variant, "seed", seed, "seconds", elapsed, flush=True)
    return groups


def evaluate_group(groups: pd.DataFrame, labels: pd.DataFrame, directory: Path) -> dict[str, float]:  # noqa: DICT_OK -- score table
    frame = labels.merge(groups, on=["ts", "grp"], how="outer", validate="one_to_one", indicator=True)
    assert frame._merge.eq("both").all() and len(frame) == len(labels)
    frame = frame.drop(columns="_merge")
    pure = score(frame.assign(p=frame.p_bu_new, alpha=0.), directory / "pure")
    result = {"pure": pure}
    for direct in ("incumbent", "rich"):
        prediction = frame.assign(p_dir=frame[f"direct_{direct}"], alpha=ALPHA)
        prediction["p"] = (1-ALPHA)*prediction.p_bu_new+ALPHA*prediction.p_dir
        result[direct] = score(prediction, directory / direct)
    return result


def main() -> None:
    configure()
    DEST.mkdir(exist_ok=True)
    snapshots(DEST / "sources")
    self_check()
    save_json(DEST / "protocol.json", {"folds": FOLDS, "variants": VARIANTS, "screen_seeds": [0], "conditional_followup": "If best fixed-alpha pair improves BOTH folds, add seeds1,2 only for that variant; compare ensemble with seed0 before primary-only alpha optimization", "pair_ranking": "equal-weight mean fold W_pct/incumbent W_pct", "final_confirmation_closed": True, "test_closed": True})
    baseline = {"primary": 12.695950143757269, "recent": 11.639886825195315}
    scores = {}
    for fold in FOLDS:
        name = fold[0]
        train, selection = prepare(fold, DEST / "cache" / name)
        labels = direct_labels(name)
        labels.to_parquet(DEST / "cache" / name / "labels.parquet", index=False)
        for variant in VARIANTS:
            groups = fit_predict(variant, 0, train, selection, DEST / name / variant / "seed0")
            scores[f"{name}/{variant}"] = evaluate_group(groups, labels, DEST / name / variant / "screen")
            save_json(DEST / "screen_scores.json", scores)
            print("SCORE", name, variant, scores[f"{name}/{variant}"], flush=True)
        del train, selection, labels, groups
        gc.collect()
    candidates = [(sum(scores[f"{fold}/{variant}"][direct]/baseline[fold] for fold, _, _ in FOLDS)/2, variant, direct) for variant in VARIANTS for direct in ("incumbent", "rich")]
    ranking = sorted(candidates)
    _, chosen, direct = ranking[0]
    chosen_stage = "screen"
    if all(scores[f"{fold}/{chosen}"][direct] < baseline[fold] for fold, _, _ in FOLDS):
        ensemble_scores = {}
        for fold, _, _ in FOLDS:
            train = pd.read_parquet(DEST / "cache" / fold / "train.parquet")
            selection = pd.read_parquet(DEST / "cache" / fold / "selection.parquet")
            pieces = [pd.read_parquet(DEST / fold / chosen / "seed0/group_predictions.parquet")]
            for seed in (1, 2):
                pieces.append(fit_predict(chosen, seed, train, selection, DEST / fold / chosen / f"seed{seed}"))
            averaged = pd.concat(pieces).groupby(["ts", "grp"], as_index=False, observed=True).p_bu_new.mean()
            ensemble_scores[fold] = evaluate_group(averaged, direct_labels(fold), DEST / fold / chosen / "ensemble")
            del train, selection, pieces, averaged
            gc.collect()
        save_json(DEST / "ensemble_scores.json", ensemble_scores)
        ensemble_rank = sum(ensemble_scores[fold][direct]/baseline[fold] for fold, _, _ in FOLDS)/2
        if ensemble_rank < ranking[0][0]:
            chosen_stage = "ensemble"
    primary = pd.read_parquet(DEST / "primary" / chosen / chosen_stage / direct / "predictions.parquet")
    alpha = optimal_weight(primary.rename(columns={"p_bu_new": "p_bu"}), ALPHA)
    calibrated = {}
    for fold, _, _ in FOLDS:
        frame = pd.read_parquet(DEST / fold / chosen / chosen_stage / direct / "predictions.parquet")
        frame = frame.assign(p=(1-alpha)*frame.p_bu_new+alpha*frame.p_dir, alpha=alpha)
        calibrated[fold] = score(frame, DEST / fold / "chosen_primary_alpha")
    save_json(DEST / "results.json", {"ranking_fixed_alpha": ranking, "chosen_site": chosen, "chosen_stage": chosen_stage, "chosen_direct": direct, "alpha_primary_only": alpha, "calibrated_scores": calibrated, "incumbent_scores": baseline, "confirmation_loaded": False, "test_loaded": False})
    provenance = json.loads((ROOT / "analysis_outputs/award_run/provenance.json").read_text())
    inputs = [ROOT / "analysis_outputs/award_run/cache" / provenance["cache_key"] / "feat_train.parquet", ROOT / "handover 2/01_participant_dataset/sites.csv", ROOT / "analysis_outputs/autoresearch_20261103/cache/assignment.json"]
    save_json(DEST / "manifest.json", {"input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in inputs}, "output_sha256": {str(p.relative_to(DEST)): digest(p) for p in DEST.rglob("*.parquet")}, "source_sha256": {p.name: digest(p) for p in (DEST / "sources").glob("*.py")}})
    print("SITE FAMILY COMPLETE", chosen, chosen_stage, direct, alpha, calibrated, flush=True)


if __name__ == "__main__":
    main()
