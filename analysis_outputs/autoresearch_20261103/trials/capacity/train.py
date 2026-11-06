# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm"]
# ///
# Run through run.py to enforce the fit deadline.
"""Mutable candidate: direct group models with fixed bottom-up predictions."""
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
import lightgbm as lgb
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- preserve existing model interface
from common import CACHE, save_json


@dataclass(frozen=True, slots=True)
class Config:
    id: str
    parent_id: str
    hypothesis: str
    n_estimators: int = 400
    learning_rate: float = .03
    num_leaves: int = 31
    min_child_samples: int = 50
    objective: str = "regression_l1"
    weighting: str = "none"
    recency_days: float = 0
    direct_weight: float = .5

    def __post_init__(self) -> None:
        assert self.id and all(c.isalnum() or c in "_-" for c in self.id)
        assert self.parent_id and self.hypothesis
        assert self.n_estimators > 0 and self.num_leaves > 1 and self.min_child_samples > 0
        assert 0 < self.learning_rate <= 1 and self.recency_days >= 0 and 0 <= self.direct_weight <= 1
        assert self.objective in {"regression_l1", "regression_l2"}
        assert self.weighting in {"none", "capacity", "scored"}


def main(trial: Path) -> None:
    config = Config(**json.loads((trial / "config.json").read_text()))
    features = json.loads((CACHE / "features.json").read_text())
    train = pd.read_parquet(CACHE / "train.parquet")
    selection = pd.read_parquet(CACHE / "selection_features.parquet")
    assert not {"energy", "cf", "y"} & set(selection.columns)
    keys = pd.read_parquet(CACHE / "selection_labels.parquet", columns=["ts", "grp"])
    selection["p_dir"] = 0.
    start = time.monotonic()
    fit_seconds = {}
    for group, rows in train.groupby("grp"):
        weights = np.ones(len(rows))
        if config.weighting in {"capacity", "scored"}:
            weights *= rows.capacity_kw.to_numpy()
        if config.weighting == "scored":
            weights *= (rows.smp * rows.k).to_numpy()
        if config.recency_days:
            age = (pd.Timestamp("2023-06-01", tz="Asia/Seoul") - rows.ts).dt.total_seconds().to_numpy() / 86400
            weights *= np.exp2(-age/config.recency_days)
        weights /= weights.mean()
        model = lgb.LGBMRegressor(n_estimators=config.n_estimators, learning_rate=config.learning_rate, num_leaves=config.num_leaves, min_child_samples=config.min_child_samples, subsample=.8, subsample_freq=1, colsample_bytree=.8, objective=config.objective, verbose=-1, n_jobs=2)
        t0 = time.monotonic()
        sample_weight = None if config.weighting == "none" and not config.recency_days else weights
        model.fit(rows[features], rows.cf, sample_weight=sample_weight)
        fit_seconds[group] = time.monotonic()-t0
        mask = selection.grp == group
        selection.loc[mask, "p_dir"] = np.clip(model.predict(selection.loc[mask, features]), 0, None) * selection.loc[mask, "capacity_kw"].to_numpy()
        model.booster_.save_model(str(trial / f"{group}.txt"))
    predictions = keys.merge(selection[["ts", "grp", "p_dir"]], on=["ts", "grp"], how="left", validate="one_to_one").fillna({"p_dir": 0.})
    predictions.to_parquet(trial / "predictions.parquet", index=False)
    save_json(trial / "runtime.json", {"fit_seconds": fit_seconds, "total_seconds": time.monotonic()-start})
    print(config.id, fit_seconds, flush=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
