# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "joblib"]
# ///
# Run: python submission/score_push/profile_wave.py
"""Final bounded weather-profile family on unchanged paired development folds."""
from wave_common import OUT, ROOT, configure, snapshots, save_json, digest, score, metrics, optimal_weight
from learner_wave import data, member
from profile_features import DEST, build, self_check
from profile_models import fit
import gc
import json
import pandas as pd  # noqa: PANDAS_OK -- original group interface

FOLDS = ("primary", "recent")
REFERENCE = {"primary": 12.161987873994034, "recent": 11.18733758871567}


def prepare(representation: str) -> dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]]:  # noqa: DICT_OK -- paired datasets
    profiles = pd.read_parquet(DEST / "cache" / f"{representation}.parquet")
    extra = list(profiles.columns[2:])
    chosen = json.loads((OUT / "refinement_wave/chosen_recipe.json").read_text())
    result = {}
    for fold in FOLDS:
        train, selection, labels, names = data(fold)
        frames = []
        for frame in (train, selection):
            joined = frame.merge(profiles, on=["ts", "grp"], how="left", validate="one_to_one", indicator=True)
            assert joined._merge.eq("both").all() and len(joined) == len(frame)
            frames.append(joined.drop(columns="_merge"))
        current = pd.read_parquet(OUT / "refinement_wave" / fold / "recipes" / chosen["id"] / "predictions.parquet", columns=["ts", "grp", "p"])
        labels = labels.drop(columns="p_reference").merge(current.rename(columns={"p": "p_reference"}), on=["ts", "grp"], validate="one_to_one")
        assert abs(metrics(labels.assign(p=labels.p_reference))["W_pct"]-REFERENCE[fold]) < 1e-10
        assert not {"energy", "cf", "y"} & set(frames[1])
        result[fold] = (frames[0], frames[1], labels, names+extra)
    return result


def compare(identifier: str, stage: str, frames: dict[str, pd.DataFrame]) -> dict:  # noqa: DICT_OK -- experiment result
    primary = frames["primary"].assign(p_bu=frames["primary"].p_reference, p_dir=frames["primary"].p_new)
    alpha = optimal_weight(primary, 0.)
    scores = {}
    for fold in FOLDS:
        frame = frames[fold]
        prediction = frame.assign(alpha=alpha, p=(1-alpha)*frame.p_reference+alpha*frame.p_new)
        scores[fold] = score(prediction, DEST / fold / identifier / stage / "complement")
    result = {"id": identifier, "stage": stage, "alpha_primary_only": alpha, "scores": scores, "both_folds_improve": all(scores[f] < REFERENCE[f] for f in FOLDS), "mean_relative_loss": sum(scores[f]/REFERENCE[f] for f in FOLDS)/2, "model_fits_for_calibration": 0}
    print("PROFILE PAIRED", result, flush=True)
    return result


def main() -> None:
    configure()
    DEST.mkdir(exist_ok=True)
    assert not (DEST / "protocol.json").exists(), "Never overwrite a profile attempt"
    save_json(DEST / "protocol.json", {"reference_scores": REFERENCE, "representations": ["cells", "stations"], "learners": ["lgb", "mlp"], "screen_seed": 0, "lgb_seed_zero": "None, matching existing direct sentinel", "mlp_seed_zero": "explicit0", "mask": "Drop all-missing or <=1 distinct nonmissing training value, applied before either learner", "followup": "At most one best paired-mean variant improving BOTH folds gets seeds1,2; final adoption requires its ensemble still improves BOTH", "blend": "New member complements complete current refinement; alpha fitted primary only", "confirmation_closed": True, "test_closed": True})
    snapshots(DEST / "sources")
    self_check()
    save_json(DEST / "prefit_checks.json", {"weighted_contributions_and_shares": True, "absent_vs_missing": True, "duplicates_rejected": True, "label_invariance": True, "train_only_constant_mask": True, "weighting_mutant_rejected": True, "completed_before_model_fits": True})
    build()
    records = []
    for representation in ("cells", "stations"):
        datasets = prepare(representation)
        for learner in ("lgb", "mlp"):
            identifier = f"{representation}_{learner}"
            frames = {}
            for fold in FOLDS:
                train, selection, labels, names = datasets[fold]
                raw = fit(learner, 0, train, selection, names, DEST / fold / identifier / "seed0")
                frames[fold] = member([raw], labels, DEST / fold / identifier / "screen")
            records.append(compare(identifier, "screen", frames))
            save_json(DEST / "progress.json", records)
        del datasets, train, selection, labels, frames, raw
        gc.collect()
    qualified = [row for row in records if row["both_folds_improve"]]
    selected = None
    if qualified:
        chosen = min(qualified, key=lambda row: row["mean_relative_loss"])
        representation, learner = chosen["id"].rsplit("_", 1)
        datasets = prepare(representation)
        frames = {}
        for fold in FOLDS:
            train, selection, labels, names = datasets[fold]
            raws = [pd.read_parquet(DEST / fold / chosen["id"] / "seed0/daylight_raw.parquet")]
            for seed in (1, 2):
                raws.append(fit(learner, seed, train, selection, names, DEST / fold / chosen["id"] / f"seed{seed}"))
            frames[fold] = member(raws, labels, DEST / fold / chosen["id"] / "ensemble")
        result = compare(chosen["id"], "ensemble", frames)
        records.append(result)
        if result["both_folds_improve"]:
            selected = result
    save_json(DEST / "results.json", {"records": records, "selected_profile": selected, "incumbent_retained": selected is None, "reference_scores": REFERENCE, "confirmation_loaded": False, "test_loaded": False})
    save_json(DEST / "selected_recipe.json", {"profile": selected, "base_recipe": "analysis_outputs/score_push_20261104/refinement_wave/chosen_recipe.json", "base_recipe_sha256": digest(OUT / "refinement_wave/chosen_recipe.json"), "prediction_paths": {fold: str((DEST / fold / selected["id"] / "ensemble/complement/predictions.parquet").relative_to(ROOT)) if selected else str((OUT / "refinement_wave" / fold / "recipes/leaves63_trees400_ensemble/predictions.parquet").relative_to(ROOT)) for fold in FOLDS}, "confirmation_closed": True})
    inputs = [OUT / p for p in ("cache/train.parquet", "cache/selection.parquet", "recent/cache/train.parquet", "recent/cache/selection.parquet", "refinement_wave/chosen_recipe.json")]
    inputs += [OUT / "refinement_wave" / fold / "recipes/leaves63_trees400_ensemble/predictions.parquet" for fold in FOLDS]
    save_json(DEST / "manifest.json", {"input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in inputs}, "output_sha256": {str(p.relative_to(DEST)): digest(p) for p in DEST.rglob("*.parquet")}})
    print("PROFILE FAMILY COMPLETE", selected, "incumbent_retained", selected is None, flush=True)


if __name__ == "__main__":
    main()
