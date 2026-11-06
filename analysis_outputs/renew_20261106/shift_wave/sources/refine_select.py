# /// script
# requires-python = ">=3.12"
# dependencies = ["pandas", "pyarrow", "lightgbm", "scikit-learn"]
# ///
# Run after refinement: python submission/score_push/refine_select.py
"""Apply caller's clarified final ranking without changing fitted artifacts."""
import json
from wave_common import save_json, digest
from refine_wave import DEST, FOLDS


def main() -> None:
    original = json.loads((DEST / "results.json").read_text())
    assert not (DEST / "clarified_results.json").exists()
    eligible = [row for row in original["records"] if not row["id"].endswith("_screen") and row["both_folds_beat_prior"] and (row["id"] != "three_default_mlp5" or original["mlp_seed_count_for_three_way"] == 5)]
    selected = min(eligible, key=lambda row: row["mean_relative_loss"])
    baseline = next(row for row in original["records"] if row["id"] == "three_default_mlp3")
    clarification = {"caller_instruction": "Final eligibility: BOTH folds better than prior best MLP complement; then lowest equal-weight mean relative loss. Tree screen must beat default on both to authorize extra seeds, but this is not a final adoption veto.", "clarification_timing": "After all fitted predictions and scores were saved; explicit caller clarification, not a new model or weight fit", "original_results_sha256": digest(DEST / "results.json"), "original_protocol_sha256": digest(DEST / "protocol.json"), "eligible_ids": [row["id"] for row in eligible], "selected_id": selected["id"], "delta_W_pct_vs_default_three_way": {fold: selected["scores"][fold]-baseline["scores"][fold] for fold in FOLDS}, "new_model_fits": 0, "new_weight_fits": 0, "original_predictions_models_results_preserved": True}
    save_json(DEST / "selection_rule_clarification.json", clarification)
    save_json(DEST / "clarified_results.json", {**original, "selected_recipe": selected, "complexity_adopted": selected["id"].removesuffix("_ensemble") if selected["id"].endswith("_ensemble") else None, "selection_rule_clarification": "selection_rule_clarification.json"})
    print("CLARIFIED SELECTION", selected, flush=True)


if __name__ == "__main__":
    main()
