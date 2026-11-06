# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "joblib", "scikit-learn"]
# ///
# How to run: python submission/score_push_diagnose_existing_mlp.py
"""Inspect incumbent neural inputs without loading labels or executing models."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- stored sklearn preprocessing accepts named frames
import pyarrow as pa

from score_push_verify import ROOT, digest


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    original = ROOT / "analysis_outputs/score_push_20261104/learner_wave"
    data = ROOT / "analysis_outputs/score_push_gpu_20261104/data"
    records = []
    inputs: list[Path] = []
    for fold in ("primary", "recent"):
        names = json.loads((data / fold / "features.json").read_text())["rich"]
        assert len(names) == 100 and not {"cf", "y", "energy", "smp", "k"} & set(names)
        paths = [data / fold / f"{name}.parquet" for name in ("train", "evaluation")]
        frames = [pd.read_parquet(path, columns=names) for path in paths]
        transform_path = original / fold / "mlp_cf/seed0/input_preprocessing.joblib"
        transform = joblib.load(transform_path)
        assert list(transform.feature_names_in_) == names
        assert transform[1].n_samples_seen_ == len(frames[0])
        train, future = [transform.transform(frame) for frame in frames]
        assert np.isfinite(train).all() and np.isfinite(future).all()
        for seed in (1, 2):
            other_path = original / fold / f"mlp_cf/seed{seed}/input_preprocessing.joblib"
            other = joblib.load(other_path)
            np.testing.assert_array_equal(other[0].statistics_, transform[0].statistics_)
            np.testing.assert_array_equal(other[1].mean_, transform[1].mean_)
            np.testing.assert_array_equal(other[1].scale_, transform[1].scale_)
            inputs.append(other_path)
        lower, upper = train.min(axis=0), train.max(axis=0)
        outside = (future < lower) | (future > upper)
        constant = lower == upper
        constant_changes = (future[:, constant] != lower[constant])
        features = []
        for index in np.flatnonzero(outside.any(axis=0)):
            features.append({"name": names[index], "train_min": float(lower[index]),
                             "train_max": float(upper[index]), "future_min": float(future[:, index].min()),
                             "future_max": float(future[:, index].max()), "outside_rows": int(outside[:, index].sum()),
                             "constant_in_training": bool(constant[index])})
        records.append({"fold": fold, "train_rows": len(train), "evaluation_rows": len(future),
                        "features": len(names), "dtype": str(train.dtype),
                        "outside_rows": int(outside.any(axis=1).sum()), "outside_entries": int(outside.sum()),
                        "constant_features": [names[i] for i in np.flatnonzero(constant)],
                        "constant_future_changed_rows": int(constant_changes.any(axis=1).sum()),
                        "constant_future_changed_entries": int(constant_changes.sum()),
                        "input_ranges": features})
        inputs.extend([*paths, transform_path, data / fold / "features.json"])
    result = {"input_only": True, "model_inferences": 0, "fits": 0, "labels_loaded": False,
              "records": records, "input_sha256": {str(path.relative_to(ROOT)): digest(path) for path in inputs}}
    output = ROOT / "analysis_outputs/renew_20261105/existing_mlp_input_diagnostics.json"
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    for record in records:
        print(json.dumps({key: value for key, value in record.items() if key != "input_ranges"}))
        print(json.dumps(sorted(record["input_ranges"], key=lambda item: max(abs(item["future_min"]), abs(item["future_max"])), reverse=True)[:5]))


if __name__ == "__main__":
    main()
