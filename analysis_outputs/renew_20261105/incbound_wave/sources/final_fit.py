# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "joblib"]
# ///
# Run only through final_run.py; each subprocess has a 600-second deadline.
"""One sequential direct-model stage executed from the frozen candidate source."""
import ctypes
import json
import os
import sys
import time
from pathlib import Path
import pandas as pd  # noqa: PANDAS_OK -- existing frozen interface
import pyarrow as pa
from common import save_json
from final_data import FINAL, load_frozen


def main(job: Path) -> None:
    pa.set_cpu_count(2)
    pa.set_io_thread_count(2)
    start = time.monotonic()
    spec = json.loads((job / "job.json").read_text())
    source = load_frozen()
    config = source.Config(**json.loads(Path(spec["config"]).read_text()))
    train = pd.read_parquet(spec["train"])
    features = pd.read_parquet(spec["features"])
    assert not {"energy", "cf", "y"} & set(features.columns)
    predictions, models, timings = source.predict_frames(train, features, config)
    predictions.to_parquet(job / "direct.parquet", index=False)
    for name, model in models.items():
        model.booster_.save_model(str(job / f"{name}.txt"))
    kernel = ctypes.windll.kernel32
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    kernel.GetPriorityClass.argtypes = [ctypes.c_void_p]
    priority = kernel.GetPriorityClass(kernel.GetCurrentProcess())
    assert priority == 0x4000, f"Unexpected Windows priority {priority}"
    assert max(timings.values()) < 600
    save_json(job / "receipt.json", {"pid": os.getpid(), "priority_class": priority, "priority": "BELOW_NORMAL_PRIORITY_CLASS", "fit_seconds": timings, "elapsed_seconds": time.monotonic()-start, "threads": {key: os.environ.get(key) for key in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"]}, "models": {name: model.get_params() for name, model in models.items()}, "rows": {"train": len(train), "prediction": len(features)}})
    print(json.dumps({"job": job.name, "fit_seconds": timings}), flush=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
