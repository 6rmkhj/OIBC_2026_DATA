# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "joblib"]
# ///
"""Final-stage aggregation and frozen-candidate loading."""
import gc
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- preserve the original group numerics
from common import ROOT, OUT, CACHE, digest

FINAL = OUT / "final"
PRIOR = ROOT / "analysis_outputs/award_run"
CANDIDATE = ROOT / "submission/autoresearch_candidate"
sys.path.insert(0, str(ROOT / "submission"))
import make_submission as original


def load_frozen():
    freeze = json.loads((FINAL / "freeze.json").read_text())
    path = FINAL / "train_snapshot.py"
    assert digest(path) == freeze["current_snapshot_sha256"]
    assert digest(FINAL / "config.json") == freeze["config_sha256"]
    spec = importlib.util.spec_from_file_location("frozen_final_train", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def feature_cache() -> Path:
    provenance = json.loads((PRIOR / "provenance.json").read_text())
    return PRIOR / "cache" / provenance["cache_key"]


def read_rows(split: str) -> pd.DataFrame:
    cutoff = pd.Timestamp("2024-06-01", tz=original.TZ)
    end = pd.Timestamp("2025-06-01", tz=original.TZ)
    filters = {"train": [("ts", "<=", cutoff)], "outer": [("ts", ">", cutoff), ("ts", "<=", end)], "test": None}
    name = "feat_test.parquet" if split == "test" else "feat_train.parquet"
    columns = ["site_id", "ts", "capacity_kw", "night", *original.GFEATS]
    if split != "test":
        columns.append("energy")
    return pd.read_parquet(feature_cache() / name, columns=columns, filters=filters[split])


def prepare_outer_train(assignment: dict[str, str]) -> None:
    data = read_rows("train")
    grouped = original.group_frame(data[~data.night], assignment)
    grouped.to_parquet(FINAL / "outer_train.parquet", index=False)
    del data, grouped
    gc.collect()


def prepare_prediction(split: str, assignment: dict[str, str]) -> None:
    data = read_rows(split)
    site = pd.read_parquet(PRIOR / f"{split}_site_predictions.parquet")
    keys = ["site_id", "ts"]
    actual = data[keys + (["energy"] if split == "outer" else [])]
    aligned = actual.merge(site, on=keys, how="left", validate="one_to_one", indicator=True)
    assert len(aligned) == len(site) and aligned._merge.eq("both").all()
    assert np.isfinite(aligned.p).all() and aligned.p.ge(0).all()
    if split == "outer":
        np.testing.assert_array_equal(aligned.energy, aligned.y)
        grouped_targets = original.group_frame(data[~data.night], assignment)
        grouped_targets.to_parquet(FINAL / "outer_as_train.parquet", index=False)
    clean = data.drop(columns=[name for name in ["energy", "cf", "y"] if name in data])
    assert not {"energy", "cf", "y"} & set(clean.columns)
    features = original.group_frame(clean[~clean.night], assignment)
    assert not {"energy", "cf", "y"} & set(features.columns)
    features.to_parquet(FINAL / f"{split}_features.parquet", index=False)
    site["grp"] = site.site_id.map(assignment)
    groups = site.groupby(["ts", "grp"], as_index=False)
    values = groups[["p", "y"] if split == "outer" else ["p"]].sum().rename(columns={"p": "p_bu"})
    counts = groups.size().rename(columns={"size": "site_count"})
    values = values.merge(counts, on=["ts", "grp"], validate="one_to_one")
    if split == "outer":
        smp = pd.read_parquet(feature_cache() / "smp.parquet", columns=["ts", "smp", "k"])
        values = values.merge(smp, on="ts", how="left", validate="many_to_one")
        assert np.isfinite(values[["y", "smp", "k"]].to_numpy()).all()
    values.to_parquet(FINAL / f"{split}_labels_bu.parquet", index=False)
    print(f"PREPARED {split}: site_rows={len(data)} group_rows={len(values)} daylight_rows={len(features)}", flush=True)
    del data, site, clean, aligned, features
    gc.collect()
