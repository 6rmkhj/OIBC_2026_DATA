"""Bounded, target-free weather extension for the immutable final recipe."""
from wave_common import ROOT, OUT
from features import CORE, cyclic_wind, weighted_weather, revisions
from profile_features import CHANNELS, profile
from train import forecast_context
import gc
import json
import pandas as pd

DEST = OUT / "final"
OLD = ROOT / "analysis_outputs/autoresearch_20261103/final"
DATA = ROOT / "handover 2/01_participant_dataset"
CACHE = ROOT / "analysis_outputs/award_run/cache" / json.loads((ROOT / "analysis_outputs/award_run/provenance.json").read_text())["cache_key"]
MARCH = pd.Timestamp("2025-03-01", tz="Asia/Seoul")
JUNE = pd.Timestamp("2025-06-01", tz="Asia/Seoul")


def sidecars(split: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    assert (DEST / "freeze.json").exists()
    filters = [("ts", ">", MARCH), ("ts", "<=", JUNE)] if split == "train" else []
    sites = pd.read_csv(DATA / "sites.csv")
    assignment = json.loads((OLD.parent / "cache/assignment.json").read_text())
    source = CACHE / f"feat_{split}.parquet"
    coverage = pd.read_parquet(source, columns=["site_id", "ts"], filters=[*filters, ("night", "==", False)])
    coverage = coverage.merge(sites[["site_id", "capacity_kw", "wa_station", "wb_station"]], on="site_id", validate="many_to_one")
    coverage["grp"] = coverage.site_id.map(assignment)
    weather = coverage[["ts", "grp"]].drop_duplicates().sort_values(["ts", "grp"])
    for provider in ("wa", "wb"):
        station = f"{provider}_station"
        raw = cyclic_wind(pd.read_parquet(DATA / split / f"forecast_{provider}.parquet", filters=filters or None), provider)
        names = [n for n in raw if n.startswith(provider + "_") and n != station]
        rounds = {}
        for issued in (17, 10):
            panel = coverage[["ts", "grp", "capacity_kw", station]].merge(raw.loc[raw["round"].eq(issued)].drop(columns="round"), on=[station, "ts"], how="left", validate="many_to_one")
            rounds[issued] = weighted_weather(panel, names)
            del panel
        core = [n for n in names if n in CORE]
        extra = [n for n in names if n not in CORE]
        frames = [rounds[17][["ts", "grp", *extra]].rename(columns={n: f"extra_{n}" for n in extra}), rounds[10][["ts", "grp", *core]].rename(columns={n: f"r10_{n}" for n in core}), revisions(rounds[17], rounds[10], core)]
        for frame in frames:
            weather = weather.merge(frame, on=["ts", "grp"], validate="one_to_one")
        del raw, rounds, frames
        gc.collect()
    del coverage
    channels = sorted(set(CHANNELS["wa_station"]) | set(CHANNELS["wb_station"]))
    rows = pd.read_parquet(source, columns=["site_id", "ts", "capacity_kw", *channels], filters=[*filters, ("night", "==", False)])
    rows = rows.merge(sites[["site_id", "wa_station", "wb_station"]], on="site_id", validate="many_to_one")
    rows["grp"] = rows.site_id.map(assignment)
    profiles = []
    for bucket in ("wa_station", "wb_station"):
        frame = profile(rows, bucket, list(CHANNELS[bucket]), sorted(sites[bucket].unique()), bucket)
        profiles.append(frame.astype({n: "float32" for n in frame.columns[2:]}))
    stations = profiles[0].merge(profiles[1], on=["ts", "grp"], validate="one_to_one")
    del rows, profiles
    gc.collect()
    if split == "train":
        weather = pd.concat([pd.read_parquet(OUT / "recent/cache/weather.parquet"), weather], ignore_index=True)
        stations = pd.concat([pd.read_parquet(OUT / "profile_wave/cache/stations.parquet"), stations], ignore_index=True)
    for name, frame in (("weather", weather), ("stations", stations)):
        assert not frame.duplicated(["ts", "grp"]).any()
        frame.to_parquet(DEST / "cache" / f"{split}_{name}.parquet", index=False)
    return weather, stations


def enrich(frame: pd.DataFrame, weather: pd.DataFrame, stations: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    frame = frame.merge(weather, on=["ts", "grp"], how="left", validate="one_to_one", indicator=True)
    assert frame._merge.eq("both").all()
    frame = frame.drop(columns="_merge")
    frame["phys_humidity_clear"] = frame.wa_humidity * frame.csa
    frame["phys_dew_spread"] = frame.wb_temp - frame.wb_dew_point
    frame["phys_uv_clear"] = frame.wb_uv_idx * frame.csb
    frame = forecast_context(frame, "ramps_daily_lead")
    names = json.loads((OUT / "trials/combined_physics/features.json").read_text())
    names += [n for n in frame if n.endswith(("_ramp", "_lead", "_daylight_mean", "_daylight_std"))]
    frame["grp_code"] = frame.grp.map({"G1": 0, "G2": 1})
    names.append("grp_code")
    frame = frame.merge(stations, on=["ts", "grp"], how="left", validate="one_to_one", indicator=True)
    assert frame._merge.eq("both").all() and len(names) == 100
    frame = frame.drop(columns="_merge")
    profile_names = names + list(stations.columns[2:])
    assert len(profile_names) == 904
    return frame, names, profile_names
