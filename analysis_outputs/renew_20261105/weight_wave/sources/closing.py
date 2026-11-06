# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "scipy", "pyarrow", "lightgbm", "scikit-learn"]
# ///
# Run: python submission/score_push/closing.py
# Finalize after recording process exit: python submission/score_push/closing.py --manifest
"""One final no-fit convex check; close adaptive search before confirmation."""
from wave_common import OUT, ROOT, configure, snapshots, save_json, digest, score, metrics, receipt
from refine_models import convex_weights
from datetime import datetime, timezone
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen prediction/metric interface

DEST = OUT / "closing_wave"
FOLDS = ("primary", "recent")
REFERENCE = {"primary": 12.041603595410752, "recent": 11.064366712650248}
MEMBERS = {"station": ("stations_lgb/ensemble/complement/predictions.parquet", "p"), "cell_lgb": ("cells_lgb/screen/pure/predictions.parquet", "p_new"), "cell_mlp": ("cells_mlp/screen/pure/predictions.parquet", "p_new")}


def main() -> None:
    configure()
    DEST.mkdir(exist_ok=True)
    assert not (DEST / "protocol.json").exists(), "Closing check is one-shot"
    save_json(DEST / "protocol.json", {"members": MEMBERS, "primary_only_solver": "Sparse HiGHS nonnegative unit-sum LP,threads2", "reference_scores": REFERENCE, "adoption_gate": "Both folds strictly improve; otherwise retain station complete forecast", "model_fits": 0, "new_families": 0, "optimizer_calls": 1, "confirmation_closed": True, "test_closed": True, "search_ends_after_this_check": True})
    snapshots(DEST / "sources")
    parent_manifest_path = OUT / "profile_wave/final_manifest.json"
    parent_manifest = json.loads(parent_manifest_path.read_text())
    inputs = [parent_manifest_path, OUT / "profile_wave/selected_recipe.json", ROOT / "submission/autoresearch/evaluate.py", ROOT / "submission/autoresearch/calibrate.py"]
    frames = {}
    night_masks = {}
    for fold in FOLDS:
        frame = None
        for name, (relative, value_column) in MEMBERS.items():
            path = OUT / "profile_wave" / fold / relative
            assert digest(path) == parent_manifest["artifact_sha256"][str(path.relative_to(OUT / "profile_wave"))]
            inputs.append(path)
            member = pd.read_parquet(path, columns=["ts", "grp", "y", "smp", "k", value_column]).rename(columns={value_column: name})
            assert not member.duplicated(["ts", "grp"]).any()
            assert np.isfinite(member[name]).all() and member[name].ge(0).all()
            if frame is None:
                frame = member
            else:
                aligned = frame.merge(member, on=["ts", "grp"], how="outer", validate="one_to_one", suffixes=("", "_check"), indicator=True)
                assert aligned._merge.eq("both").all()
                for label in ("y", "smp", "k"):
                    np.testing.assert_array_equal(aligned[label], aligned[f"{label}_check"])
                frame = aligned.drop(columns=["_merge", "y_check", "smp_check", "k_check"])
        assert frame is not None and len(frame) == (17568 if fold == "primary" else 13104)
        cutoff = pd.Timestamp("2023-06-01" if fold == "primary" else "2024-06-01", tz="Asia/Seoul")
        end = pd.Timestamp("2024-06-01" if fold == "primary" else "2025-03-01", tz="Asia/Seoul")
        assert cutoff < frame.ts.min() and frame.ts.max() <= end
        daylight_path = OUT / ("cache/selection.parquet" if fold == "primary" else "recent/cache/selection.parquet")
        inputs.append(daylight_path)
        daylight = pd.read_parquet(daylight_path, columns=["ts", "grp"])
        night = ~pd.MultiIndex.from_frame(frame[["ts", "grp"]]).isin(pd.MultiIndex.from_frame(daylight))
        assert frame.loc[night, list(MEMBERS)].eq(0.).all().all()
        assert abs(metrics(frame.assign(p=frame.station))["W_pct"]-REFERENCE[fold]) < 1e-10
        frames[fold] = frame
        night_masks[fold] = night
        score(frame.assign(p=frame.station), DEST / fold / "baseline")
    save_json(DEST / "input_manifest.json", {str(path.relative_to(ROOT)): digest(path) for path in inputs})
    names = list(MEMBERS)
    weights = convex_weights(frames["primary"], names, DEST / "weights")
    candidate_scores = {}
    for fold in FOLDS:
        candidate = frames[fold].assign(p=frames[fold][names].to_numpy()@weights)
        assert candidate.loc[night_masks[fold], "p"].eq(0.).all()
        candidate_scores[fold] = score(candidate, DEST / fold / "candidate")
    adopt = all(candidate_scores[fold] < REFERENCE[fold] for fold in FOLDS)
    selected_weights = weights if adopt else np.array([1., 0., 0.])
    selected_scores = {}
    for fold in FOLDS:
        frame = frames[fold]
        selected = frame.assign(p=frame[names].to_numpy()@selected_weights)
        assert np.isfinite(selected.p).all() and selected.p.ge(0).all() and selected.loc[night_masks[fold], "p"].eq(0.).all()
        selected_scores[fold] = score(selected, DEST / fold / "selected")
        replay = pd.read_parquet(DEST / fold / "selected/predictions.parquet")
        pd.testing.assert_frame_equal(replay, selected, check_exact=True)
        np.testing.assert_array_equal(replay.p, replay[names].to_numpy()@selected_weights)
        candidate_replay = pd.read_parquet(DEST / fold / "candidate/predictions.parquet")
        np.testing.assert_array_equal(candidate_replay.p, candidate_replay[names].to_numpy()@weights)
    optimization = json.loads((DEST / "weights/optimization.json").read_text())
    assert optimization["solver_success"] and optimization["solver_status"] == 0 and optimization["model_fits"] == 0
    assert optimization["minimum_weight"] >= 0 and abs(optimization["weight_sum"]-1) < 1e-9
    assert optimization["solver_options"]["threads"] == 2 and abs(optimization["scaled_dual_gap"]) < 1e-7
    assert optimization["max_primal_residual"] <= 1e-7
    fit_matrix = pd.read_parquet(DEST / "weights/primary_fit_matrix.parquet")
    pd.testing.assert_frame_equal(fit_matrix, frames["primary"][["ts", "grp", "y", "smp", "k", *names]], check_exact=True)
    score_paths = list(DEST.glob("*/*/score.json"))
    assert len(score_paths) == 6
    for path in score_paths:
        recorded = json.loads(path.read_text())
        prediction = pd.read_parquet(path.parent / "predictions.parquet")
        assert abs(metrics(prediction)["W_pct"]-recorded["W_pct"]) < 1e-12
    for relative, expected in json.loads((DEST / "input_manifest.json").read_text()).items():
        assert digest(ROOT / relative) == expected
    result = {"adopted_closing_blend": adopt, "decision": "adopt_convex" if adopt else "retain_station_complete", "member_order": names, "candidate_weights_primary_only": weights.tolist(), "selected_weights": selected_weights.tolist(), "candidate_scores": candidate_scores, "selected_scores": selected_scores, "reference_scores": REFERENCE, "source_members_relative_to_profile_wave": MEMBERS, "selected_prediction_paths": {fold: str((DEST / fold / "selected/predictions.parquet").relative_to(ROOT)) for fold in FOLDS}, "search_closed": True, "closed_at_utc": datetime.now(timezone.utc).isoformat(), "no_later_tuning_from_confirmation": True, "confirmation_loaded": False, "test_loaded": False, "model_fits": 0}
    save_json(DEST / "results.json", result)
    save_json(DEST / "selected_recipe.json", result)
    save_json(DEST / "verification.json", {"parent_member_hashes_match": True, "labels_and_keys_exact": True, "primary_only_optimizer_verified": True, "identical_weights_transferred": True, "arithmetic_replay_exact": True, "night_and_allzero_rows_stable": True, "solver_feasibility_verified": True, "input_hashes_rechecked": True, "score_artifacts_recomputed": len(score_paths), "evaluation_rows": {fold: len(frame) for fold, frame in frames.items()}, "model_fits": 0})
    receipt(DEST / "runtime.json", [])
    print("CLOSING CHECK COMPLETE; ADAPTIVE SEARCH CLOSED", result, flush=True)


def finalize_manifest() -> None:
    destination = DEST / "final_manifest.json"
    assert not destination.exists() and (DEST / "selected_recipe.json").exists()
    save_json(destination, {"artifact_sha256": {str(path.relative_to(DEST)): digest(path) for path in DEST.rglob("*") if path.is_file() and path != destination}, "current_source_sha256": {str(Path(__file__).relative_to(ROOT)): digest(Path(__file__))}, "selected_recipe": "selected_recipe.json", "search_closed": True})


if __name__ == "__main__":
    if sys.argv[1:] == ["--manifest"]:
        finalize_manifest()
    else:
        assert not sys.argv[1:]
        main()
