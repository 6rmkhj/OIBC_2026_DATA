# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "joblib"]
# ///
# Run: python submission/score_push/learner_wave.py
"""Four group learner families with primary-only convex blend transfer."""
from wave_common import OUT, ROOT, RICH_ALPHA, configure, snapshots, save_json, digest, score, metrics, optimal_weight
from learner_models import fit, self_check
from train import forecast_context
from pathlib import Path
import gc
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen group interface

DEST = OUT / "learner_wave"
FOLDS = ("primary", "recent")
VARIANTS = ("lgb_normalized", "mlp_cf", "mlp_normalized", "kernel_l1")
REFERENCE = {"primary": 12.622155808512135, "recent": 11.536044344428209}


def data(fold: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    """Load only already bounded compact caches; build frozen context identically."""
    cache = OUT / "cache" if fold == "primary" else OUT / "recent/cache"
    train = pd.read_parquet(cache / "train.parquet")
    selection = pd.read_parquet(cache / ("selection.parquet"))
    assert not {"energy", "cf", "y"} & set(selection)
    cutoff = pd.Timestamp("2023-06-01" if fold == "primary" else "2024-06-01", tz="Asia/Seoul")
    end = pd.Timestamp("2024-06-01" if fold == "primary" else "2025-03-01", tz="Asia/Seoul")
    assert train.ts.max() <= cutoff < selection.ts.min() and selection.ts.max() <= end
    train = forecast_context(train, "ramps_daily_lead")
    selection = forecast_context(selection, "ramps_daily_lead")
    names = json.loads((OUT / "trials/combined_physics/features.json").read_text())
    names += [name for name in selection if name.endswith(("_ramp", "_lead", "_daylight_mean", "_daylight_std"))]
    train["grp_code"] = train.grp.map({"G1": 0, "G2": 1})
    selection["grp_code"] = selection.grp.map({"G1": 0, "G2": 1})
    names.append("grp_code")
    assert len(names) == len(set(names)) and train.grp_code.notna().all() and selection.grp_code.notna().all()
    if fold == "primary":
        labels = pd.read_parquet(ROOT / "analysis_outputs/autoresearch_20261103/cache/selection_labels.parquet")
        direct = pd.read_parquet(OUT / "trials/winner_calibrated/predictions.parquet")
        labels = labels.merge(direct, on=["ts", "grp"], validate="one_to_one")
        labels["p_reference"] = (1-RICH_ALPHA)*labels.p_bu+RICH_ALPHA*labels.p_dir
    else:
        labels = pd.read_parquet(OUT / "recent/rich_primary_alpha/predictions.parquet", columns=["ts", "grp", "y", "p_bu", "smp", "k", "p_dir", "p"])
        labels = labels.rename(columns={"p": "p_reference"})
    labels = labels.rename(columns={"p_bu": "p_bu_old", "p_dir": "p_dir_reference"})
    assert len(labels) == (17568 if fold == "primary" else 13104)
    assert abs(metrics(labels.assign(p=labels.p_reference))["W_pct"]-REFERENCE[fold]) < 1e-10
    return train, selection, labels, names


def member(raws: list[pd.DataFrame], labels: pd.DataFrame, directory: Path) -> pd.DataFrame:
    """Average signed seed output before clipping, preserving original direct recipe."""
    raw = pd.concat(raws).groupby(["ts", "grp"], as_index=False).p_raw.mean()
    frame = labels.merge(raw, on=["ts", "grp"], how="left", validate="one_to_one")
    frame["p_new"] = np.clip(frame.p_raw.fillna(0.), 0., None)
    frame = frame.drop(columns="p_raw")
    assert np.isfinite(frame.p_new).all()
    score(frame.assign(p=frame.p_new), directory / "pure")
    return frame


def calibrate(variant: str, stage: str, frames: dict[str, pd.DataFrame]) -> list[dict]:  # noqa: DICT_OK -- bounded experiment table
    rows = []
    for blend, base in (("old_bottom_up", "p_bu_old"), ("richer_reference", "p_reference")):
        primary = frames["primary"].assign(p_bu=frames["primary"][base], p_dir=frames["primary"].p_new)
        alpha = optimal_weight(primary, 0.)
        scores = {}
        for fold in FOLDS:
            frame = frames[fold]
            prediction = frame.assign(alpha=alpha, p=(1-alpha)*frame[base]+alpha*frame.p_new)
            scores[fold] = score(prediction, DEST / fold / variant / stage / blend)
        row = {"variant": variant, "stage": stage, "blend": blend, "base_column": base, "alpha_primary_only": alpha, "scores": scores, "mean_relative_loss": sum(scores[f]/REFERENCE[f] for f in FOLDS)/2, "both_folds_improve": all(scores[f] < REFERENCE[f] for f in FOLDS), "model_fits_for_calibration": 0}
        rows.append(row)
        print("BLEND", row, flush=True)
    return rows


def main() -> None:
    configure()
    DEST.mkdir(exist_ok=True)
    snapshots(DEST / "sources")
    self_check()
    save_json(DEST / "protocol.json", {"models": VARIANTS, "reference_scores": REFERENCE, "screen_seeds": {"lgb_normalized": [0, 1, 2], "others": [0]}, "nontrivial_learner_weight": .02, "followup_gate": "One neural/kernel member with both-fold improvement over richer reference and alpha>=.02; add seeds1,2 only; no iteration extension/grid", "blend_weights_fit_on": "primary only", "confirmation_closed": True, "test_closed": True})
    datasets = {fold: data(fold) for fold in FOLDS}
    for fold, (_, _, labels, names) in datasets.items():
        (DEST / fold).mkdir()
        labels.to_parquet(DEST / fold / "reference.parquet", index=False)
        save_json(DEST / fold / "features.json", names)
    records = []
    for variant in VARIANTS:
        frames = {}
        for fold in FOLDS:
            train, selection, labels, names = datasets[fold]
            seeds = (0, 1, 2) if variant == "lgb_normalized" else (0,)
            raws = [fit(variant, seed, train, selection, names, DEST / fold / variant / f"seed{seed}") for seed in seeds]
            frames[fold] = member(raws, labels, DEST / fold / variant / "screen")
            del raws
            gc.collect()
        records += calibrate(variant, "screen", frames)
        save_json(DEST / "scores.json", records)
    qualified = [row for row in records if row["variant"] != "lgb_normalized" and row["both_folds_improve"] and row["alpha_primary_only"] >= .02]
    followup = None
    if qualified:
        chosen = min(qualified, key=lambda row: row["mean_relative_loss"])
        variant = chosen["variant"]
        followup = variant
        frames = {}
        for fold in FOLDS:
            train, selection, labels, names = datasets[fold]
            raws = [pd.read_parquet(DEST / fold / variant / "seed0/daylight_raw.parquet")]
            for seed in (1, 2):
                raws.append(fit(variant, seed, train, selection, names, DEST / fold / variant / f"seed{seed}"))
            frames[fold] = member(raws, labels, DEST / fold / variant / "ensemble")
            del raws
            gc.collect()
        records += calibrate(variant, "ensemble", frames)
        save_json(DEST / "scores.json", records)
    inputs = [OUT / name for name in ("cache/train.parquet", "cache/selection.parquet", "recent/cache/train.parquet", "recent/cache/selection.parquet", "trials/combined_physics/features.json", "trials/winner_calibrated/predictions.parquet", "recent/rich_primary_alpha/predictions.parquet")]
    inputs += [ROOT / "analysis_outputs/autoresearch_20261103/cache/selection_labels.parquet", ROOT / "submission/autoresearch/train.py", ROOT / "submission/autoresearch/evaluate.py", ROOT / "submission/autoresearch/calibrate.py"]
    save_json(DEST / "manifest.json", {"input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in inputs}, "output_sha256": {str(p.relative_to(DEST)): digest(p) for p in DEST.rglob("*.parquet")}})
    save_json(DEST / "results.json", {"ranking": sorted(records, key=lambda row: row["mean_relative_loss"]), "followup_variant": followup, "reference_scores": REFERENCE, "confirmation_loaded": False, "test_loaded": False})
    print("LEARNER FAMILY COMPLETE", min(records, key=lambda row: row["mean_relative_loss"]), flush=True)


if __name__ == "__main__":
    main()
