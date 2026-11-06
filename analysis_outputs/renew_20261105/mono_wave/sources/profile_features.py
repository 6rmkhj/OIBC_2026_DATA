# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
"""Weather-only geographic and provider-station capacity contributions."""
from wave_common import ROOT, OUT, save_json, digest, receipt
import gc
import inspect
import json
import time
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen site/group interface

DEST = OUT / "profile_wave"
CHANNELS = {"cells": ("wa_cloud", "wb_cloud", "wb_uv_idx", "csa", "csb", "toaa", "toab", "wa_humidity", "wa_temp"), "wa_station": ("wa_cloud", "csa", "toaa", "wa_humidity", "wa_temp"), "wb_station": ("wb_cloud", "wb_uv_idx", "csb", "toab", "wb_rel_hum")}


def profile(rows: pd.DataFrame, bucket: str, channels: list[str], levels: list[str], prefix: str) -> pd.DataFrame:
    """Absent bucket=0; present all-missing weather=NaN; partial sums unrenormalized."""
    assert not rows.duplicated(["site_id", "ts"]).any(), "Duplicate site-hour keys"
    assert rows[bucket].notna().all() and rows.capacity_kw.gt(0).all()
    assert not {"energy", "cf", "y"} & set(channels)
    weighted = rows[["ts", "grp", bucket, "capacity_kw"]].copy()
    for name in channels:
        weighted[name] = rows[name].to_numpy()*rows.capacity_kw.to_numpy()
    total = rows.groupby(["ts", "grp"], observed=True).capacity_kw.sum()
    summed = weighted.groupby(["ts", "grp", bucket], observed=True).sum(min_count=1)
    denominator = total.reindex(summed.index.droplevel(bucket)).to_numpy()
    summed = summed.div(denominator, axis=0).rename(columns={"capacity_kw": "share"})
    wide = summed.unstack(bucket).reindex(columns=pd.MultiIndex.from_product([["share", *channels], levels]))
    share = wide["share"].fillna(0.)
    blocks = [share] + [wide[name].where(share.ne(0.), 0.) for name in channels]
    result = pd.concat(blocks, axis=1)
    result.columns = [f"{prefix}_{level}_{name}" for name in ["share", *channels] for level in levels]
    np.testing.assert_allclose(share.sum(axis=1), 1., atol=1e-12)
    return result.reset_index()


def column_mask(train: pd.DataFrame, names: list[str]) -> list[str]:
    """Never expose constant/unseen-future dimensions to an untrained coefficient."""
    return [name for name in names if train[name].nunique(dropna=True) > 1]


def fixture() -> None:
    rows = pd.DataFrame({"site_id": ["s1", "s2", "s3"], "ts": pd.Timestamp("2024-01-01", tz="Asia/Seoul"), "grp": "G1", "capacity_kw": [1., 3., 2.], "bucket": ["a", "a", "b"], "cloud": [10., 30., np.nan], "humidity": [20., np.nan, 0.]})
    actual = profile(rows, "bucket", ["cloud", "humidity"], ["a", "b", "c"], "p")
    assert np.isclose(actual.p_a_share.iloc[0], 2/3) and np.isclose(actual.p_b_share.iloc[0], 1/3)
    assert np.isclose(actual.p_a_cloud.iloc[0], 100/6) and np.isclose(actual.p_a_humidity.iloc[0], 20/6)
    assert np.isnan(actual.p_b_cloud.iloc[0]) and actual.p_b_humidity.iloc[0] == 0
    assert actual.p_c_share.iloc[0] == actual.p_c_cloud.iloc[0] == actual.p_c_humidity.iloc[0] == 0
    perturbed = rows.assign(energy=[1e9, -1e9, np.nan], cf=[99, 0, -99], y=[np.nan, 1e20, 0])
    pd.testing.assert_frame_equal(actual, profile(perturbed, "bucket", ["cloud", "humidity"], ["a", "b", "c"], "p"))
    try:
        profile(pd.concat([rows, rows.iloc[:1]]), "bucket", ["cloud"], ["a", "b", "c"], "p")
    except AssertionError as error:
        assert str(error) == "Duplicate site-hour keys"
    else:
        raise AssertionError("Duplicate site-hour accepted")
    training = pd.DataFrame({"constant": [1., 1.], "all_missing": [np.nan, np.nan], "absent": [0., 0.], "varying": [1., 2.]})
    selected = column_mask(training, list(training))
    assert selected == ["varying"]
    future = pd.DataFrame({"constant": [999.], "all_missing": [4.], "absent": [100.], "varying": [np.nan]})
    assert list(future[selected]) == ["varying"]


def self_check() -> None:
    fixture()
    source = inspect.getsource(profile)
    mutated = source.replace("rows[name].to_numpy()*rows.capacity_kw.to_numpy()", "rows[name].to_numpy()")
    assert mutated != source
    namespace = {"pd": pd, "np": np}
    exec(compile(mutated, "profile_weighting_mutant", "exec"), namespace)
    original = fixture.__globals__["profile"]
    fixture.__globals__["profile"] = namespace["profile"]
    try:
        fixture()
    except AssertionError:
        print("PASS deliberate capacity-weighting mutant rejected", flush=True)
    else:
        raise AssertionError("Weighting mutant survived")
    finally:
        fixture.__globals__["profile"] = original
    fixture()
    print("PASS shares/contributions, absent-vs-all-missing/partial-missing, duplicate rejection, label invariance and train-only constant mask", flush=True)


def build() -> None:
    started = time.monotonic()
    provenance = json.loads((ROOT / "analysis_outputs/award_run/provenance.json").read_text())
    source = ROOT / "analysis_outputs/award_run/cache" / provenance["cache_key"] / "feat_train.parquet"
    sites_path = ROOT / "handover 2/01_participant_dataset/sites.csv"
    assignment_path = ROOT / "analysis_outputs/autoresearch_20261103/cache/assignment.json"
    sites = pd.read_csv(sites_path)
    sites["cells"] = np.floor(sites.lat).astype(int).astype(str)+"_"+np.floor(sites.lon).astype(int).astype(str)
    levels = {bucket: sorted(sites[bucket].unique()) for bucket in CHANNELS}
    assert [len(levels[b]) for b in CHANNELS] == [11, 61, 73]
    channels = sorted(set().union(*CHANNELS.values()))
    columns = ["site_id", "ts", "night", "capacity_kw", *channels]
    assert not {"energy", "cf", "y"} & set(columns)
    rows = pd.read_parquet(source, columns=columns, filters=[("ts", "<=", pd.Timestamp("2025-03-01", tz="Asia/Seoul")), ("night", "==", False)])
    rows = rows.merge(sites[["site_id", *CHANNELS]], on="site_id", validate="many_to_one")
    rows["grp"] = rows.site_id.map(json.loads(assignment_path.read_text()))
    assert rows.grp.notna().all()
    cache = DEST / "cache"
    cache.mkdir()
    stations = []
    for bucket, names in CHANNELS.items():
        frame = profile(rows, bucket, list(names), levels[bucket], bucket)
        frame = frame.astype({name: "float32" for name in frame.columns[2:]})
        if bucket == "cells":
            frame.to_parquet(cache / "cells.parquet", index=False)
        else:
            stations.append(frame)
        del frame
        gc.collect()
    station_frame = stations[0].merge(stations[1], on=["ts", "grp"], validate="one_to_one")
    station_frame.to_parquet(cache / "stations.parquet", index=False)
    save_json(cache / "manifest.json", {"projected_columns": columns, "filter_end": "2025-03-01 00:00:00+09:00", "daylight_only": True, "site_rows": len(rows), "group_rows": len(station_frame), "levels": levels, "channels": CHANNELS, "missing_semantics": "Absent bucket:share0 and contribution0. Present all-missing channel:NaN. Partial-missing channel:known cap*x sum/group total capacity, not renormalized.", "coverage": "Exact existing daylight site-hour coverage; no generation values read or used", "input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in (source, sites_path, assignment_path)}, "cache_sha256": {p.name: digest(p) for p in cache.glob("*.parquet")}})
    del rows, station_frame, stations
    gc.collect()
    receipt(DEST / "build_runtime.json", [time.monotonic()-started])
    print("PROFILE CACHE COMPLETE", flush=True)
