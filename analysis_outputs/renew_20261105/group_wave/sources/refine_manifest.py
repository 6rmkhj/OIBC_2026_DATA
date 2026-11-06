# /// script
# requires-python = ">=3.12"
# dependencies = ["pandas", "pyarrow", "lightgbm", "scikit-learn"]
# ///
# Run last: python submission/score_push/refine_manifest.py
"""Fingerprint the completed refinement outputs after all writers have exited."""
from pathlib import Path
from wave_common import ROOT, digest, save_json
from refine_wave import DEST


def main() -> None:
    destination = DEST / "final_manifest.json"
    assert not destination.exists(), "Final manifest is immutable"
    save_json(destination, {"artifact_sha256": {str(path.relative_to(DEST)): digest(path) for path in DEST.rglob("*") if path.is_file() and path != destination}, "current_source_sha256": {str(path.relative_to(ROOT)): digest(path) for path in Path(__file__).parent.glob("refine*.py")}, "selection_results": "clarified_results.json", "selected_recipe": "chosen_recipe.json", "original_results_preserved": "results.json", "original_protocol_preserved": "protocol.json"})


if __name__ == "__main__":
    main()
