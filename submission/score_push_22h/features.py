"""Fixed, target-free features and weighted residual transformations.

The caller supplies daylight, chronological OOF rows to ``training``.  No
parameters are estimated here.  Repeated target timestamps from different
OOF origins receive inverse-duplicate weights rather than extra influence.
"""
from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd


WEATHER = (
    "wa_cloud", "wa_temp", "wa_humidity", "wa_rain", "wa_wind_speed",
    "wb_cloud", "wb_uv_idx", "wb_precip_prob", "wb_total_liq",
    "wb_rel_hum", "extra_wa_snow", "cosz", "grp_code",
)
CALENDAR = ("doy_sin", "doy_cos", "hour")
CORE = (*WEATHER, "raw_fraction")
FEATURE_FAMILIES = {
    "core": CORE,
    "season": (*CORE, *CALENDAR),
    "age": (*CORE, *CALENDAR, "forecast_age_days", "model_history_days"),
}


def _numbers(frame: pd.DataFrame, column: str, *, finite: bool = True) -> np.ndarray:
    values = frame[column].to_numpy(dtype=np.float64)
    if finite and not np.isfinite(values).all():
        raise ValueError(f"{column} must contain finite values")
    return values


def _time(values, name: str) -> pd.DatetimeIndex:
    result = pd.DatetimeIndex(pd.to_datetime(values))
    if result.hasnans:
        raise ValueError(f"{name} must not contain missing timestamps")
    return result.tz_localize("Asia/Seoul") if result.tz is None else result.tz_convert("Asia/Seoul")


def _cutoff(value) -> pd.Timestamp:
    return _time([value], "cutoff")[0]


def normalizer(frame: pd.DataFrame) -> np.ndarray:
    """Clear-sky elevation scale, floored at 0.05; identical to base engine."""
    cosine = np.maximum(_numbers(frame, "cosz"), 0.0)
    exponent = np.divide(-0.059, cosine, out=np.zeros_like(cosine), where=cosine > 0)
    return np.maximum(1.098 * cosine * np.exp(exponent), 0.05)


def scale(frame: pd.DataFrame, config: Mapping) -> np.ndarray:
    """Residual scale in kWh; multiplicative targets also have a solar floor."""
    capacity = _numbers(frame, "capacity_kw")
    if (capacity <= 0).any():
        raise ValueError("capacity_kw must be positive")
    solar_capacity = capacity * normalizer(frame)
    mode = config.get("mode", "additive")
    if mode == "additive":
        return solar_capacity
    if mode == "multiplicative":
        return np.maximum(_numbers(frame, "p"), 0.05 * solar_capacity)
    raise ValueError(f"Unknown residual mode: {mode}")


def engineer(frame: pd.DataFrame) -> pd.DataFrame:
    """Return all fixed feature columns, never inspecting observed targets.

    Weather missing values remain missing for the learner.  Forecast age is
    deterministically capped at 366 days, the calibrated forecast horizon.
    """
    result = pd.DataFrame(index=frame.index)
    for column in (*WEATHER, *CALENDAR):
        if column == "grp_code" and column not in frame:
            result[column] = frame["grp"].map({"G1": 0.0, "G2": 1.0})
            if result[column].isna().any():
                raise ValueError("Unknown group; provide a finite grp_code")
        else:
            result[column] = _numbers(frame, column, finite=False)
    result = result.replace([np.inf, -np.inf], np.nan)
    capacity = _numbers(frame, "capacity_kw")
    if (capacity <= 0).any():
        raise ValueError("capacity_kw must be positive")
    result["raw_fraction"] = _numbers(frame, "p") / capacity
    dates, origins = _time(frame["ts"], "ts"), _time(frame["model_origin"], "model_origin")
    ages = np.asarray((dates - origins).total_seconds(), dtype=float) / 86400.0
    if (ages <= 0).any():
        raise ValueError("OOF model_origin must be strictly earlier than ts")
    history = _numbers(frame, "train_history_days")
    if (history < 0).any():
        raise ValueError("train_history_days must be nonnegative")
    result["forecast_age_days"] = np.minimum(ages, 366.0)
    result["model_history_days"] = history
    return result


def training(frame: pd.DataFrame, config: Mapping, cutoff):
    """Return ``(X, target, sample_weight)`` without fitting or target clipping.

    The caller filters OOF rows to the outer training cutoff before calling.
    ``money * scale`` makes weighted target L1 equal monetary energy L1;
    optional target-time decay and inverse duplicate counts apply afterward.
    """
    if frame.empty:
        raise ValueError("No calibration rows")
    dates = _time(frame["ts"], "ts")
    end = _cutoff(cutoff)
    if (dates > end).any():
        raise ValueError("Calibration target exceeds the outer training cutoff")
    if frame["night"].isna().any() or frame["night"].astype(bool).any():
        raise ValueError("Calibration training requires daylight OOF rows")
    family = config.get("features", "core")
    if family not in FEATURE_FAMILIES:
        raise ValueError(f"Unknown feature family: {family}")
    X = engineer(frame).loc[:, list(FEATURE_FAMILIES[family])]
    units = scale(frame, config)
    target = (_numbers(frame, "y") - _numbers(frame, "p")) / units
    money = _numbers(frame, "smp") * _numbers(frame, "k")
    if (money < 0).any():
        raise ValueError("Monetary weights must be nonnegative")
    duplicate_count = frame.groupby(["ts", "grp"], dropna=False)["ts"].transform("size").to_numpy(dtype=float)
    weights = money * units / duplicate_count
    half_life = config.get("half_life")
    if half_life is not None:
        half_life = float(half_life)
        if not np.isfinite(half_life) or half_life <= 0:
            raise ValueError("half_life must be positive days or None")
        elapsed = np.asarray((end - dates).total_seconds(), dtype=float) / 86400.0
        weights *= np.exp2(-elapsed / half_life)
    if not np.isfinite(weights).all() or weights.sum() <= 0:
        raise ValueError("Calibration weights must be finite with positive total")
    return X, target, weights / weights.mean()


def apply(frame: pd.DataFrame, rawdelta, config: Mapping) -> np.ndarray:
    """Apply a bounded, shrunken residual and enforce physical output limits."""
    delta = np.asarray(rawdelta, dtype=np.float64)
    if delta.ndim != 1 or len(delta) != len(frame) or not np.isfinite(delta).all():
        raise ValueError("rawdelta must be a finite vector aligned to frame")
    bound, shrink = float(config["bound"]), float(config.get("shrink", 1.0))
    if not np.isfinite(bound) or bound <= 0:
        raise ValueError("bound must be finite and positive")
    if not np.isfinite(shrink) or not 0 <= shrink <= 1:
        raise ValueError("shrink must be between zero and one")
    if frame["night"].isna().any():
        raise ValueError("night must not contain missing values")
    daytime = ~frame["night"].to_numpy(dtype=bool)
    prediction = np.zeros(len(frame), dtype=float)
    if daytime.any():
        active = frame.loc[daytime]
        upper = _numbers(active, "static_capacity")
        if (upper <= 0).any():
            raise ValueError("static_capacity must be positive")
        prediction[daytime] = np.clip(_numbers(active, "p") + shrink * np.clip(delta[daytime], -bound, bound) * scale(active, config), 0, upper)
    return prediction
