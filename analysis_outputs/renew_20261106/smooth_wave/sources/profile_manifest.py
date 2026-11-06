# /// script
# requires-python = ">=3.12"
# dependencies = ["pandas", "pyarrow", "lightgbm", "scikit-learn"]
# ///
# Run last: python submission/score_push/profile_manifest.py
"""Freeze completed profile outputs and their externally reused dependencies."""
from pathlib import Path
from wave_common import ROOT, OUT, digest, save_json
from profile_features import DEST


def main() -> None:
    destination = DEST / "final_manifest.json"
    assert not destination.exists()
    external = [ROOT / "analysis_outputs/autoresearch_20261103/cache/selection_labels.parquet", ROOT / "submission/autoresearch/train.py", ROOT / "submission/autoresearch/evaluate.py", ROOT / "submission/autoresearch/calibrate.py", OUT / "trials/combined_physics/features.json", OUT / "trials/winner_calibrated/predictions.parquet", OUT / "recent/rich_primary_alpha/predictions.parquet"]
    save_json(destination, {"artifact_sha256": {str(p.relative_to(DEST)): digest(p) for p in DEST.rglob("*") if p.is_file() and p != destination}, "current_source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in Path(__file__).parent.glob("profile*.py")}, "additional_input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in external}, "selected_recipe": "selected_recipe.json", "results": "results.json"})


if __name__ == "__main__":
    main()
