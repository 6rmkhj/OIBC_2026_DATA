# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "scipy", "pyarrow", "lightgbm", "scikit-learn", "joblib"]
# ///
# Run: python submission/score_push/refine_wave.py
"""One predeclared refinement: convex members, five MLP seeds, bounded trees."""
from wave_common import OUT, ROOT, configure, snapshots, save_json, digest, score
from learner_wave import data, member
from learner_models import fit
from refine_models import convex_weights, normalized_fit
from pathlib import Path
import gc
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- immutable group inputs

DEST = OUT / "refinement_wave"
FOLDS = ("primary", "recent")
PRIOR = {"primary": 12.32194072929294, "recent": 11.317671544395346}
COMPLEXITY = (("leaves15_trees400", 15, 400), ("leaves63_trees400", 63, 400), ("leaves31_trees800", 31, 800))


def load_members(fold: str) -> pd.DataFrame:
    frame = pd.read_parquet(OUT / "learner_wave" / fold / "reference.parquet")
    for name, path in (("norm", "lgb_normalized/screen"), ("mlp", "mlp_cf/ensemble"), ("norm_mlp", "mlp_normalized/screen"), ("kernel", "kernel_l1/screen")):
        prediction = pd.read_parquet(OUT / "learner_wave" / fold / path / "pure/predictions.parquet", columns=["ts", "grp", "p_new"])
        frame = frame.merge(prediction.rename(columns={"p_new": name}), on=["ts", "grp"], how="outer", validate="one_to_one", indicator=True)
        assert frame._merge.eq("both").all()
        frame = frame.drop(columns="_merge")
    assert len(frame) == (17568 if fold == "primary" else 13104)
    return frame


def evaluate(identifier: str, frames: dict[str, pd.DataFrame], names: list[str]) -> dict:  # noqa: DICT_OK -- frozen experiment result
    weights = convex_weights(frames["primary"], names, DEST / "weights" / identifier)
    scores = {}
    for fold in FOLDS:
        frame = frames[fold]
        predicted = frame.assign(p=frame[names].to_numpy()@weights)
        assert np.isfinite(predicted.p).all() and predicted.p.ge(0).all()
        scores[fold] = score(predicted, DEST / fold / "recipes" / identifier)
    result = {"id": identifier, "members": names, "weights_primary_only": weights.tolist(), "scores": scores, "both_folds_beat_prior": all(scores[f] < PRIOR[f] for f in FOLDS), "mean_relative_loss": sum(scores[f]/PRIOR[f] for f in FOLDS)/2}
    save_json(DEST / "weights" / identifier / "paired_scores.json", result)
    print("PAIRED CONVEX", result, flush=True)
    return result


def replace_member(frames: dict[str, pd.DataFrame], predictions: dict[str, pd.DataFrame], name: str) -> dict[str, pd.DataFrame]:  # noqa: DICT_OK -- paired frames
    result = {}
    for fold in FOLDS:
        prediction = predictions[fold][["ts", "grp", "p_new"]].rename(columns={"p_new": name})
        result[fold] = frames[fold].drop(columns=name).merge(prediction, on=["ts", "grp"], validate="one_to_one")
        assert len(result[fold]) == len(frames[fold])
    return result


def main() -> None:
    configure()
    DEST.mkdir(exist_ok=True)
    assert not (DEST / "protocol.json").exists(), "Never overwrite a refinement run"
    save_json(DEST / "protocol.json", {"prior_scores": PRIOR, "initial_no_fit_members": ["p_reference", "norm", "mlp"], "five_member_alternative_adds": ["norm_mlp", "kernel"], "weights": "Nonnegative sum1; sparse HiGHS LP fitted on primary only; threads2", "extra_mlp_seeds": [3, 4], "adopt_mlp5_only_if": "Both folds strictly improve over same three-way blend with MLP3", "complexity_variants": COMPLEXITY, "complexity_screen_seeds": [0], "complexity_followup": "At most one screen beating default normalized3seed+selectedMLP on BOTH folds receives seeds1,2; retain only if ensemble also beats both", "final_ranking": "Eligible complete recipes beating best prior on both folds, equal mean relative loss; single-seed screens excluded", "confirmation_closed": True, "test_closed": True})
    snapshots(DEST / "sources")
    fixture = pd.DataFrame({"ts": pd.date_range("2024-01-01", periods=3, freq="h", tz="Asia/Seoul"), "grp": "G1", "y": [2., 8., 9.], "smp": [1., 3., 1.], "k": 1., "a": 0., "b": 10.})
    np.testing.assert_allclose(convex_weights(fixture, ["a", "b"], DEST / "solver_selfcheck"), [.2, .8], atol=1e-9)
    frames = {fold: load_members(fold) for fold in FOLDS}
    records = [evaluate("three_default_mlp3", frames, ["p_reference", "norm", "mlp"]), evaluate("five_default_mlp3", frames, ["p_reference", "norm", "mlp", "norm_mlp", "kernel"])]
    eligible = list(records)
    save_json(DEST / "progress.json", records)
    datasets = {fold: data(fold) for fold in FOLDS}
    predictions = {}
    for fold in FOLDS:
        train, selection, labels, names = datasets[fold]
        raws = [pd.read_parquet(OUT / "learner_wave" / fold / "mlp_cf" / f"seed{s}/daylight_raw.parquet") for s in (0, 1, 2)]
        for seed in (3, 4):
            raws.append(fit("mlp_cf", seed, train, selection, names, DEST / fold / "mlp_cf" / f"seed{seed}"))
        for raw in raws[1:]:
            pd.testing.assert_frame_equal(raw[["ts", "grp"]].reset_index(drop=True), raws[0][["ts", "grp"]].reset_index(drop=True))
        predictions[fold] = member(raws, labels, DEST / fold / "mlp5")
        del raws
        gc.collect()
    frames5 = replace_member(frames, predictions, "mlp")
    mlp5 = evaluate("three_default_mlp5", frames5, ["p_reference", "norm", "mlp"])
    records.append(mlp5)
    adopt5 = all(mlp5["scores"][f] < records[0]["scores"][f] for f in FOLDS)
    selected_frames = frames5 if adopt5 else frames
    baseline = mlp5 if adopt5 else records[0]
    if adopt5:
        eligible.append(mlp5)
    screens = []
    for identifier, leaves, trees in COMPLEXITY:
        predictions = {}
        for fold in FOLDS:
            train, selection, labels, names = datasets[fold]
            raw = normalized_fit(0, leaves, trees, train, selection, names, DEST / fold / identifier / "seed0")
            predictions[fold] = member([raw], labels, DEST / fold / identifier / "screen")
        replacement = replace_member(selected_frames, predictions, "norm")
        result = evaluate(identifier+"_screen", replacement, ["p_reference", "norm", "mlp"])
        result["beats_default_both"] = all(result["scores"][f] < baseline["scores"][f] for f in FOLDS)
        screens.append(result)
        records.append(result)
        save_json(DEST / "progress.json", records)
    qualified = [row for row in screens if row["beats_default_both"]]
    complexity_choice = None
    if qualified:
        chosen = min(qualified, key=lambda row: row["mean_relative_loss"])
        identifier = chosen["id"].removesuffix("_screen")
        _, leaves, trees = next(row for row in COMPLEXITY if row[0] == identifier)
        predictions = {}
        for fold in FOLDS:
            train, selection, labels, names = datasets[fold]
            raws = [pd.read_parquet(DEST / fold / identifier / "seed0/daylight_raw.parquet")]
            for seed in (1, 2):
                raws.append(normalized_fit(seed, leaves, trees, train, selection, names, DEST / fold / identifier / f"seed{seed}"))
            predictions[fold] = member(raws, labels, DEST / fold / identifier / "ensemble")
        replacement = replace_member(selected_frames, predictions, "norm")
        result = evaluate(identifier+"_ensemble", replacement, ["p_reference", "norm", "mlp"])
        records.append(result)
        if all(result["scores"][f] < baseline["scores"][f] for f in FOLDS):
            complexity_choice = identifier
            eligible.append(result)
    selectable = [row for row in eligible if row["both_folds_beat_prior"]]
    selected = min(selectable, key=lambda row: row["mean_relative_loss"]) if selectable else None
    save_json(DEST / "results.json", {"records": records, "selected_recipe": selected, "mlp_seed_count_for_three_way": 5 if adopt5 else 3, "complexity_adopted": complexity_choice, "prior_scores": PRIOR, "confirmation_loaded": False, "test_loaded": False})
    inputs = [p for p in (OUT / "learner_wave").rglob("*.parquet") if "seed" in str(p) or "pure" in str(p) or p.name == "reference.parquet"]
    inputs += [OUT / p for p in ("cache/train.parquet", "cache/selection.parquet", "recent/cache/train.parquet", "recent/cache/selection.parquet")]
    save_json(DEST / "manifest.json", {"input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in inputs}, "output_sha256": {str(p.relative_to(DEST)): digest(p) for p in DEST.rglob("*.parquet")}})
    print("REFINEMENT COMPLETE", selected, flush=True)


if __name__ == "__main__":
    main()
