"""Target-free transfer features and chronological OOF residual transforms."""
from __future__ import annotations

import numpy as np
import pandas as pd

BASE_IDS = ("b00", "b02", "b09", "b22")
WEATHER = ("wa_cloud", "wa_temp", "wa_humidity", "wa_rain", "wa_wind_speed",
           "wb_cloud", "wb_uv_idx", "wb_precip_prob", "wb_total_liq", "wb_rel_hum",
           "extra_wa_snow", "cosz", "grp_code", "doy_sin", "doy_cos", "hour")


def dates(values):
    out = pd.DatetimeIndex(pd.to_datetime(values))
    assert not out.hasnans
    return out.tz_localize("Asia/Seoul") if out.tz is None else out.tz_convert("Asia/Seoul")


def solar(frame):
    cosine = np.maximum(frame.cosz.to_numpy(dtype=float), 0.)
    power = np.divide(-.059, cosine, out=np.zeros_like(cosine), where=cosine > 0)
    return np.maximum(1.098 * cosine * np.exp(power), .05)


def scale(frame):
    capacity = frame.capacity_kw.to_numpy(dtype=float)
    assert np.isfinite(capacity).all() and (capacity > 0).all()
    return capacity * solar(frame)


def engineer(frame, config, rich):
    """All cross-base values must originate from the same model cutoff."""
    names = list(WEATHER if config["features"] == "weather_spread" else rich)
    assert not set(names) & {"y", "cf", "smp", "k", "energy", "p_reference"}
    X = frame[names].copy().replace([np.inf, -np.inf], np.nan)
    units = scale(frame)
    cross = frame[[f"cross_{b}" for b in BASE_IDS]].to_numpy(dtype=float)
    assert np.isfinite(cross).all()
    X["raw_solar_fraction"] = frame.p.to_numpy(dtype=float) / units
    X["cross_mean"] = cross.mean(axis=1) / units
    X["cross_spread"] = cross.std(axis=1) / units
    X["cross_range"] = (cross.max(axis=1) - cross.min(axis=1)) / units
    for index, base in enumerate(BASE_IDS):
        X[f"cross_delta_{base}"] = (cross[:, index] - frame.p.to_numpy(dtype=float)) / units
    age = np.asarray((dates(frame.ts) - dates(frame.model_origin)).total_seconds()) / 86400
    assert np.isfinite(age).all() and (age > 0).all() and (age <= 366).all()
    X["forecast_age_days"] = age
    X["model_history_days"] = frame.train_history_days.to_numpy(dtype=float)
    return X


def training(frame, config, cutoff, horizon_days, rich):
    end = dates([cutoff])[0]
    target_dates, origins = dates(frame.ts), dates(frame.model_origin)
    assert (origins < target_dates).all() and (target_dates <= end).all()
    assert not frame.night.astype(bool).any()
    age = np.asarray((target_dates - origins).total_seconds()) / 86400
    assert (age > 0).all() and (age <= 366).all()
    mask = np.ones(len(frame), dtype=bool)
    if config["weighting"] != "money":
        mask &= age <= horizon_days
    train = frame.loc[mask].reset_index(drop=True)
    assert len(train)
    units = scale(train)
    target = (train.y.to_numpy(dtype=float) - train.p.to_numpy(dtype=float)) / units
    duplicate = train.groupby(["ts", "grp"], dropna=False).ts.transform("size").to_numpy(dtype=float)
    weight = train.smp.to_numpy(dtype=float) * train.k.to_numpy(dtype=float) * units / duplicate
    assert np.isfinite(target).all() and np.isfinite(weight).all() and (weight >= 0).all()
    if config["weighting"] == "horizon_groupseason":
        # Deliberately reweighted robustness objective, not exact monetary L1.
        season = (dates(train.ts).month % 12) // 3
        cells = pd.Series(train.grp.astype(str).to_numpy() + "_" + season.astype(str))
        totals = pd.Series(weight).groupby(cells).transform("sum").to_numpy()
        assert (totals > 0).all()
        weight /= totals
    assert weight.sum() > 0
    weight /= weight.mean()
    X = engineer(train, config, rich)
    active = [name for name in X if X[name].nunique(dropna=False) > 1]
    assert active
    return train, X[active], target, weight


def apply(frame, delta, config):
    delta = np.asarray(delta, dtype=float)
    assert delta.shape == (len(frame),) and np.isfinite(delta).all()
    result = np.clip(frame.p.to_numpy(dtype=float) + config["shrink"] *
                     np.clip(delta, -config["bound"], config["bound"]) * scale(frame),
                     0., frame.static_capacity.to_numpy(dtype=float))
    return np.where(frame.night.to_numpy(dtype=bool), 0., result)


def anchored_training(X, target, weight, penalty):
    if not penalty:
        return X, target, weight
    assert 0 < penalty < 1
    return pd.concat([X, X], ignore_index=True), np.r_[target, np.zeros_like(target)], np.r_[weight, penalty*weight]


def combine_corrections(outputs, groups, mix):
    groups = np.asarray(groups)
    group = np.where(groups=="G1", outputs.get("G1", 0.), outputs.get("G2", 0.))
    return (1-mix)*outputs.get("pooled", np.zeros(len(groups))) + mix*group
