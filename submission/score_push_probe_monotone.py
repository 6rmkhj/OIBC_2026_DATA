# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "lightgbm"]
# ///
# How to run: python submission/score_push_probe_monotone.py
"""Probe installed native objective support with synthetic inputs only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TypedDict

import lightgbm as lgb
import numpy as np


class Probe(TypedDict):
    objective: str
    supported: bool
    native_error: str | None
    max_increase: float | None
    trees: int


def main() -> None:
    rng = np.random.default_rng(20261105)
    x = rng.uniform(0, 1, (512, 3))
    y = 1.1 - 0.8 * x[:, 0] - 0.2 * x[:, 1] + 0.05 * x[:, 2]
    rows: list[Probe] = []
    for objective in ("regression_l1", "fair"):
        parameters = {
            "objective": objective, "fair_c": 0.1, "verbosity": -1,
            "num_threads": 16, "seed": 0, "num_leaves": 7,
            "min_data_in_leaf": 8, "feature_fraction": 0.8,
            "monotone_constraints": [-1, -1, 0],
            "monotone_constraints_method": "basic",
            "deterministic": True, "force_col_wise": True,
        }
        try:
            model = lgb.train(parameters, lgb.Dataset(x, label=y), num_boost_round=20)
        except lgb.basic.LightGBMError as error:
            rows.append({"objective": objective, "supported": False,
                         "native_error": str(error), "max_increase": None, "trees": 0})
            continue
        increases = []
        for column in (0, 1):
            grid = np.repeat(x[:16], 101, axis=0)
            grid[:, column] = np.tile(np.linspace(0, 1, 101), 16)
            differences = np.diff(model.predict(grid).reshape(16, 101), axis=1)
            increases.append(float(differences.max()))
        maximum = max(increases)
        assert maximum <= 1e-12, (objective, maximum)
        rows.append({"objective": objective, "supported": True,
                     "native_error": None, "max_increase": maximum,
                     "trees": model.num_trees()})
    native = Path(lgb.basic._LIB._name)
    result = {"synthetic_only": True, "real_data_loaded": False,
              "lightgbm": lgb.__version__, "native_library": str(native),
              "native_sha256": hashlib.sha256(native.read_bytes()).hexdigest(),
              "records": rows}
    output = Path(__file__).resolve().parents[1] / "analysis_outputs/renew_20261105/monotone_compatibility.json"
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
