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
from common import CACHE, OUT, ROOT, digest, save_json

BASE_FEATURES = tuple(json.loads((CACHE / "features.json").read_text()))
SPATIAL_FEATURES = ("sp_wa_cloud_sd", "sp_wb_cloud_sd", "sp_wb_uv_idx_sd", "sp_csa_sd", "sp_csb_sd", "sp_wa_cloud_clear", "sp_wa_cloud_overcast", "sp_wb_cloud_clear", "sp_wb_cloud_overcast")


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
    feature_mode: str = "base"
    seeds: tuple[int, ...] = (0,)
    pooled_groups: bool = False
    spatial: bool = False
    spatial_manifest_sha256: str = ""

    def __post_init__(self) -> None:
        assert self.id and all(c.isalnum() or c in "_-" for c in self.id)
        assert self.parent_id and self.hypothesis
        assert self.n_estimators > 0 and self.num_leaves > 1 and self.min_child_samples > 0
        assert 0 < self.learning_rate <= 1 and self.recency_days >= 0 and 0 <= self.direct_weight <= 1
        assert self.objective in {"regression_l1", "regression_l2"}
        assert self.weighting in {"none", "capacity", "scored"}
        assert self.feature_mode in {"base", "ramps", "ramps_daily", "ramps_lead", "ramps_daily_lead"}
        assert self.seeds and all(isinstance(seed, int) and seed >= 0 for seed in self.seeds)
        assert isinstance(self.pooled_groups, bool) and isinstance(self.spatial, bool)
        assert not self.spatial or len(self.spatial_manifest_sha256) == 64


def ramp_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Backward issued-forecast differences within one target day, never across gaps."""
    result = frame.sort_values(["grp", "ts"]).copy()
    day = (result.ts - pd.Timedelta(hours=1)).dt.floor("D")
    grouped = result.groupby([result.grp, day], sort=False)
    adjacent = grouped.ts.diff().eq(pd.Timedelta(hours=1))
    for name in ["wa_cloud", "wb_cloud", "wb_uv_idx", "toaa", "toab", "wa_temp"]:
        result[f"{name}_ramp"] = grouped[name].diff().where(adjacent)
    return result


def forecast_context(frame: pd.DataFrame, mode: str) -> pd.DataFrame:
    """Same-issued-day daylight forecast summaries and next-hour forecast differences."""
    result = ramp_features(frame)
    day = (result.ts - pd.Timedelta(hours=1)).dt.floor("D")
    grouped = result.groupby([result.grp, day], sort=False)
    if "daily" in mode:
        for name in ["wa_cloud", "wb_cloud", "wb_uv_idx", "wa_temp"]:
            result[f"{name}_daylight_mean"] = grouped[name].transform("mean")
            result[f"{name}_daylight_std"] = grouped[name].transform("std")
    if "lead" in mode:
        adjacent = (grouped.ts.shift(-1) - result.ts).eq(pd.Timedelta(hours=1))
        for name in ["wa_cloud", "wb_cloud", "wb_uv_idx", "toaa", "toab", "wa_temp"]:
            result[f"{name}_lead"] = (grouped[name].shift(-1) - result[name]).where(adjacent)
    return result


def predict_frames(train: pd.DataFrame, selection: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, dict[str, lgb.LGBMRegressor], dict[str, float]]:
    """Fit direct models and predict label-free frames for any caller-supplied split."""
    features = list(BASE_FEATURES)
    assert not {"energy", "cf", "y"} & set(selection.columns)
    if config.feature_mode != "base":
        train = forecast_context(train, config.feature_mode)
        selection = forecast_context(selection, config.feature_mode)
        features += [name for name in selection.columns if name.endswith(("_ramp", "_lead", "_daylight_mean", "_daylight_std"))]
    if config.spatial:
        spatial_features = [name for name in selection.columns if name.startswith("sp_")]
        assert set(spatial_features) == set(SPATIAL_FEATURES) and set(spatial_features) <= set(train.columns)
        features += list(SPATIAL_FEATURES)
    if config.pooled_groups:
        train = train.assign(grp_code=train.grp.map({"G1": 0, "G2": 1}))
        selection = selection.assign(grp_code=selection.grp.map({"G1": 0, "G2": 1}))
        assert train.grp_code.notna().all() and selection.grp_code.notna().all()
        features.append("grp_code")
    selection = selection.copy()
    selection["p_dir"] = 0.
    fit_seconds = {}
    models = {}
    groups = [("pooled", train)] if config.pooled_groups else train.groupby("grp")
    for group, rows in groups:
        weights = np.ones(len(rows))
        if config.weighting in {"capacity", "scored"}:
            weights *= rows.capacity_kw.to_numpy()
        if config.weighting == "scored":
            weights *= (rows.smp * rows.k).to_numpy()
        if config.recency_days:
            age = (train.ts.max() - rows.ts).dt.total_seconds().to_numpy() / 86400
            weights *= np.exp2(-age/config.recency_days)
        weights /= weights.mean()
        sample_weight = None if config.weighting == "none" and not config.recency_days else weights
        mask = pd.Series(True, index=selection.index) if config.pooled_groups else selection.grp == group
        predictions = np.zeros(int(mask.sum()))
        for seed in config.seeds:
            # Seed zero denotes the original omitted-seed recipe; explicit 0 changes LightGBM's internal seeds.
            model = lgb.LGBMRegressor(n_estimators=config.n_estimators, learning_rate=config.learning_rate, num_leaves=config.num_leaves, min_child_samples=config.min_child_samples, subsample=.8, subsample_freq=1, colsample_bytree=.8, objective=config.objective, verbose=-1, n_jobs=2, random_state=None if seed == 0 else seed)
            t0 = time.monotonic()
            model.fit(rows[features], rows.cf, sample_weight=sample_weight)
            key = f"{group}_seed{seed}"
            fit_seconds[key] = time.monotonic()-t0
            models[key] = model
            predictions += model.predict(selection.loc[mask, features]) / len(config.seeds)
        selection.loc[mask, "p_dir"] = np.clip(predictions, 0, None) * selection.loc[mask, "capacity_kw"].to_numpy()
    return selection[["ts", "grp", "p_dir"]], models, fit_seconds


def main(trial: Path) -> None:
    config = Config(**json.loads((trial / "config.json").read_text()))
    train = pd.read_parquet(CACHE / "train.parquet")
    selection = pd.read_parquet(CACHE / "selection_features.parquet")
    if config.spatial:
        manifest_path = OUT / "spatial/manifest.json"
        assert digest(manifest_path) == config.spatial_manifest_sha256, "Spatial manifest pin differs"
        manifest = json.loads(manifest_path.read_text())
        assert manifest["feature_names"] == list(SPATIAL_FEATURES), "Spatial whitelist differs"
        assert manifest["assignment_sha256"] == digest(CACHE / "assignment.json"), "Spatial assignment differs"
        joined = []
        for name, frame in [("train", train), ("selection", selection)]:
            output = manifest["outputs"][name]
            path = (ROOT / output["path"]).resolve()
            assert path.is_relative_to(ROOT) and digest(path) == output["sha256"], "Spatial output hash differs"
            sidecar = pd.read_parquet(path)
            assert list(sidecar.columns) == ["ts", "grp", *SPATIAL_FEATURES], "Spatial output schema differs"
            assert len(sidecar) == len(frame) == output["rows"], "Spatial row counts differ"
            merged = frame.merge(sidecar, on=["ts", "grp"], how="left", validate="one_to_one", indicator=True)
            assert merged._merge.eq("both").all(), "Spatial keys differ"
            joined.append(merged.drop(columns="_merge"))
        train, selection = joined
    keys = pd.read_parquet(CACHE / "selection_labels.parquet", columns=["ts", "grp"])
    start = time.monotonic()
    selection, models, fit_seconds = predict_frames(train, selection, config)
    for name, model in models.items():
        model.booster_.save_model(str(trial / f"{name}.txt"))
    predictions = keys.merge(selection[["ts", "grp", "p_dir"]], on=["ts", "grp"], how="left", validate="one_to_one").fillna({"p_dir": 0.})
    predictions.to_parquet(trial / "predictions.parquet", index=False)
    save_json(trial / "runtime.json", {"fit_seconds": fit_seconds, "total_seconds": time.monotonic()-start})
    print(config.id, fit_seconds, flush=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
