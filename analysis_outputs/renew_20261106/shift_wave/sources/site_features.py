# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
"""Projected site data, fixed metadata categories and analytic clear-sky scaling."""
from pathlib import Path
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- original site feature contract
from features import ROOT, OUT, OLD

BASE = tuple(json.loads((OLD / "features.json").read_text()))
CATEGORIES = ("site_id", "wa_station", "wb_station")
DERIVED = ("site_humidity_clear", "site_dew_spread", "site_uv_clear")
FEATURES = (*BASE, "capacity_kw", "lat", "lon", *CATEGORIES, *DERIVED)
FOLDS = (("primary", "2023-06-01", "2024-06-01"), ("recent", "2024-06-01", "2025-03-01"))


def normalizer(cosz: np.ndarray) -> np.ndarray:
    """Haurwitz GHI / 1000, floored at .05 to bound twilight targets."""
    positive = np.maximum(cosz, 0.)
    exponent = np.divide(-.059, positive, out=np.zeros_like(positive, dtype=float), where=positive>0)
    return np.maximum(1.098*positive*np.exp(exponent), .05)


def encode(frame: pd.DataFrame, sites: pd.DataFrame) -> pd.DataFrame:
    """Use metadata-only vocabularies identically in training and prediction."""
    result = frame.copy()
    for column in CATEGORIES:
        dtype = pd.CategoricalDtype(categories=sorted(sites[column].dropna().unique()))
        result[column] = result[column].astype(dtype)
        assert result[column].notna().all(), f"Unknown metadata category: {column}"
    result["site_humidity_clear"] = result.wa_humidity*result.csa
    result["site_dew_spread"] = result.wb_temp-result.wb_dew_point
    result["site_uv_clear"] = result.wb_uv_idx*result.csb
    return result


def prepare(fold: tuple[str, str, str], directory: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Only training projection includes cf; eval feature projection has no labels."""
    _, cutoff_text, end_text = fold
    cutoff = pd.Timestamp(cutoff_text, tz="Asia/Seoul")
    end = pd.Timestamp(end_text, tz="Asia/Seoul")
    provenance = json.loads((ROOT / "analysis_outputs/award_run/provenance.json").read_text())
    path = ROOT / "analysis_outputs/award_run/cache" / provenance["cache_key"] / "feat_train.parquet"
    columns = ["ts", "night", *BASE, "capacity_kw", "lat", "lon", *CATEGORIES]
    sites = pd.read_csv(ROOT / "handover 2/01_participant_dataset/sites.csv", usecols=list(CATEGORIES))
    train = pd.read_parquet(path, columns=[*columns, "cf"], filters=[("ts", "<=", cutoff), ("night", "==", False)])
    selection = pd.read_parquet(path, columns=columns, filters=[("ts", ">", cutoff), ("ts", "<=", end)])
    assert train.ts.max() <= cutoff < selection.ts.min() and selection.ts.max() <= end
    assert not {"energy", "cf", "y"} & set(selection)
    assert not {"energy", "cf", "y", "ts", "night"} & set(FEATURES)
    assert not train.duplicated(["site_id", "ts"]).any() and not selection.duplicated(["site_id", "ts"]).any()
    train, selection = encode(train, sites), encode(selection, sites)
    directory.mkdir(parents=True, exist_ok=False)
    train.to_parquet(directory / "train.parquet", index=False)
    selection.to_parquet(directory / "selection.parquet", index=False)
    return train, selection


def self_check() -> None:
    sites = pd.DataFrame({"site_id": ["history", "no_history"], "wa_station": ["a", "b"], "wb_station": ["c", "d"]})
    raw = sites.assign(wa_humidity=50., csa=.5, wb_temp=20., wb_dew_point=15., wb_uv_idx=3., csb=.4)
    history = encode(raw.iloc[:1], sites)
    unseen = encode(raw.iloc[1:], sites)
    for column in CATEGORIES:
        assert history[column].dtype == unseen[column].dtype and unseen[column].cat.codes.iloc[0] == 1
    assert unseen.site_dew_spread.iloc[0] == 5.
    cosz = np.array([-.1, 0., .5, 1.])
    scale = normalizer(cosz)
    np.testing.assert_allclose(scale, [.05, .05, .549*np.exp(-.118), 1.098*np.exp(-.059)], rtol=1e-12)
    truth = np.array([.01, .04, .4, .8])
    predicted_normalized = np.array([.3, .5, .9, .7])
    np.testing.assert_allclose(scale*np.abs(truth/scale-predicted_normalized), np.abs(truth-scale*predicted_normalized), rtol=1e-12)
    print("PASS metadata-only unseen-history categories, Haurwitz values and normalized weighted L1 loss equivalence", flush=True)
