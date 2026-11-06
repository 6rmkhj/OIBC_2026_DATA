# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm"]
# ///
# Run: python submission/autoresearch/rescore.py SOURCE_TRIAL_ID CONFIG.json
"""Journal an explicit blend-only rescore without pretending to fit a model."""
import json
import shutil
import sys
import time
from dataclasses import asdict
from pathlib import Path
from common import OUT, CACHE, digest, save_json
from evaluate import verify_frozen
from run import record
from train import Config


def main() -> None:
    verify_frozen()
    source = OUT / "trials" / sys.argv[1]
    original = Config(**json.loads((source / "config.json").read_text()))
    config = Config(**json.loads(Path(sys.argv[2]).read_text()))
    assert config.parent_id == original.id
    metadata = {"id", "parent_id", "hypothesis", "direct_weight"}
    assert json.dumps({k: v for k, v in asdict(config).items() if k not in metadata}, sort_keys=True) == json.dumps({k: v for k, v in asdict(original).items() if k not in metadata}, sort_keys=True)
    trial = OUT / "trials" / config.id
    trial.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    save_json(trial / "config.json", asdict(config))
    for name in ["train.py", "predictions.parquet"]:
        shutil.copy2(source / name, trial / name)
    save_json(trial / "snapshot.json", {"source_sha256": digest(trial / "train.py"), "config_sha256": digest(trial / "config.json"), "frozen_manifest_sha256": digest(CACHE / "manifest.json"), "parent_id": config.parent_id, "prediction_sha256": digest(trial / "predictions.parquet")})
    save_json(trial / "invocation.json", {"argv": sys.argv, "operation": "blend-only rescore; no model fit", "source_trial": str(source)})
    save_json(trial / "runtime.json", {"fit_seconds": {}, "operation": "rescore", "total_seconds": time.monotonic()-start})
    record((trial, 0, time.monotonic()-start))


if __name__ == "__main__":
    main()
