# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
"""Weather-only capacity-weighted features on frozen daylight site coverage."""
from pathlib import Path
import gc
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- preserve the assigned frozen model contract
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis_outputs/score_push_20261104"
OLD = ROOT / "analysis_outputs/autoresearch_20261103/cache"
END = pd.Timestamp("2024-06-01", tz="Asia/Seoul")
CORE = ("wa_cloud", "wa_temp", "wa_humidity", "wa_ground_press", "wa_wind_speed", "wa_rain", "wb_cloud", "wb_uv_idx", "wb_temp", "wb_rel_hum", "wb_dew_point", "wb_vis", "wb_ceiling", "wb_precip_prob", "wb_total_liq")


def weighted_weather(rows: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    """Average available site forecasts; all-missing groups remain missing."""
    assert not {"energy", "cf", "y"} & set(names)
    keys = [rows.ts, rows.grp]
    values = rows[names]
    numerator = values.mul(rows.capacity_kw, axis=0).groupby(keys).sum(min_count=1)
    denominator = values.notna().mul(rows.capacity_kw, axis=0).groupby(keys).sum()
    return numerator.div(denominator.where(denominator.gt(0))).reset_index()


def cyclic_wind(frame: pd.DataFrame, provider: str) -> pd.DataFrame:
    """Project directions to the unit circle before averaging."""
    result = frame.copy()
    angle = np.deg2rad(result.pop(f"{provider}_wind_dir"))
    result[f"{provider}_wind_sin"] = np.sin(angle)
    result[f"{provider}_wind_cos"] = np.cos(angle)
    return result


def revisions(late: pd.DataFrame, early: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    """Retain missingness when either issued round is unavailable."""
    joined = late.merge(early, on=["ts", "grp"], how="outer", validate="one_to_one", suffixes=("_17", "_10"), indicator=True)
    assert joined._merge.eq("both").all(), "Round group keys differ"
    result = joined[["ts", "grp"]].copy()
    for name in names:
        result[f"rev_{name}"] = joined[f"{name}_17"] - joined[f"{name}_10"]
    return result


def trajectory(frame: pd.DataFrame) -> pd.DataFrame:
    """Two/three-hour issued cloud/UV context, isolated across gaps and target days."""
    result = frame.sort_values(["grp", "ts"]).copy()
    day = (result.ts - pd.Timedelta(hours=1)).dt.floor("D")
    groups = result.groupby([result.grp, day], sort=False)
    for offset in (-3, -2, 2, 3):
        adjacent = (groups.ts.shift(offset) - result.ts).eq(pd.Timedelta(hours=-offset))
        for name in ("wa_cloud", "wb_cloud", "wb_uv_idx"):
            result[f"traj_{name}_{offset:+d}"] = (groups[name].shift(offset) - result[name]).where(adjacent)
    return result


def build(end: pd.Timestamp = END, output: Path = OUT) -> tuple[pd.DataFrame, dict[str, list[str]], list[Path]]:  # noqa: DICT_OK -- JSON feature manifest
    """Build compact sidecar without loading generation or target columns."""
    provenance = json.loads((ROOT / "analysis_outputs/award_run/provenance.json").read_text())
    old_features = ROOT / "analysis_outputs/award_run/cache" / provenance["cache_key"] / "feat_train.parquet"
    data = ROOT / "handover 2/01_participant_dataset"
    inputs = [old_features, data / "sites.csv", OLD / "assignment.json"]
    coverage = pd.read_parquet(old_features, columns=["ts", "site_id", "night"], filters=[("ts", "<=", end)])
    coverage = coverage.loc[~coverage.night, ["ts", "site_id"]]
    sites = pd.read_csv(data / "sites.csv", usecols=["site_id", "capacity_kw", "wa_station", "wb_station"])
    coverage = coverage.merge(sites, on="site_id", validate="many_to_one")
    coverage["grp"] = coverage.site_id.map(json.loads((OLD / "assignment.json").read_text()))
    assert coverage.grp.notna().all() and not coverage.duplicated(["site_id", "ts"]).any()
    sidecar = coverage[["ts", "grp"]].drop_duplicates().sort_values(["ts", "grp"])
    families = {"expanded": [], "rounds": []}
    for provider in ("wa", "wb"):
        path = data / "train" / f"forecast_{provider}.parquet"
        inputs.append(path)
        station = f"{provider}_station"
        columns = pq.read_schema(path).names
        assert not {"energy", "cf", "y"} & set(columns)
        raw = pd.read_parquet(path, columns=columns, filters=[("ts", "<=", end)])
        raw = cyclic_wind(raw, provider)
        names = [name for name in raw if name.startswith(provider + "_") and name != station]
        rounds = {}
        for issued in (17, 10):
            weather = raw.loc[raw["round"].eq(issued)].drop(columns="round")
            assert not weather.duplicated([station, "ts"]).any()
            panel = coverage[["ts", "grp", "capacity_kw", station]].merge(weather, on=[station, "ts"], how="left", validate="many_to_one")
            rounds[issued] = weighted_weather(panel, names)
            del panel, weather
        core = [name for name in names if name in CORE]
        extra = [name for name in names if name not in CORE]
        expanded = rounds[17][["ts", "grp", *extra]].rename(columns={name: f"extra_{name}" for name in extra})
        early = rounds[10][["ts", "grp", *core]].rename(columns={name: f"r10_{name}" for name in core})
        revision = revisions(rounds[17], rounds[10], core)
        for frame, family in ((expanded, "expanded"), (early, "rounds"), (revision, "rounds")):
            families[family] += list(frame.columns[2:])
            sidecar = sidecar.merge(frame, on=["ts", "grp"], validate="one_to_one")
        del raw, rounds
        gc.collect()
    assert not {"energy", "cf", "y"} & set(sidecar)
    output.joinpath("cache").mkdir(parents=True, exist_ok=True)
    sidecar.to_parquet(output / "cache/weather.parquet", index=False)
    return sidecar, families, inputs
