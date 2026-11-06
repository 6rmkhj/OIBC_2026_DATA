"""Observed-row metrics and paired daily-block uncertainty for the locked recipe."""
from pathlib import Path
from typing import TypedDict

import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- existing model's explicitly retained interface


class Metrics(TypedDict):
    W: float
    W_pct: float | None
    revenue: float
    S: float
    rows: int


def metrics(frame: pd.DataFrame, prediction: str, target: str = "y") -> Metrics:
    """Return penalty and official score, with no missing-target imputation."""
    values = frame[[prediction, target, "smp", "k"]].to_numpy()
    assert np.isfinite(values).all(), "Nonfinite score inputs"
    weight = frame.smp * frame.k
    penalty = float((weight * (frame[prediction] - frame[target]).abs()).sum())
    denominator = float((weight * frame[target]).sum())
    revenue = float((frame.smp * frame[target]).sum())
    return {"W": penalty, "W_pct": 100 * penalty / denominator if denominator > 0 else None,
            "revenue": revenue, "S": revenue - .1 * penalty, "rows": len(frame)}


def report(frame: pd.DataFrame, destination: Path) -> dict[str, Metrics]:
    """Persist month, complete-fleet and peak-hour diagnostics for every recipe."""
    recipes = [("p_candidate", "y"), ("p_selected50", "y"),
               ("p_reference50", "y_reference"), ("p_original50", "y_original")]
    slices = {"all": frame, "2025_Jan_May": frame[frame.ts >= pd.Timestamp("2025-01-01", tz="Asia/Seoul")],
              "k11_15": frame[frame.k == 3]}
    slices.update({str(month): rows for month, rows in frame.groupby(frame.ts.dt.strftime("%Y-%m"))})
    rows = []
    for label, subset in slices.items():
        for prediction, target in recipes:
            rows.append({"subset": label, "recipe": prediction, **metrics(subset, prediction, target)})
    pd.DataFrame(rows).to_csv(destination / "metrics.csv", index=False)
    return {prediction: metrics(frame, prediction, target) for prediction, target in recipes}


def bootstrap(frame: pd.DataFrame) -> dict[str, list[float] | int | str]:
    """Paired calendar-day resampling: candidate minus reference W, lower is better."""
    weight = frame.smp * frame.k
    delta = weight * ((frame.p_candidate - frame.y).abs() -
                      (frame.p_reference50 - frame.y_reference).abs())
    daily = pd.DataFrame({"day": frame.ts.dt.floor("D"), "delta": delta,
                          "denom": weight * frame.y}).groupby("day").sum()
    rng = np.random.default_rng(20261102)
    ix = rng.integers(0, len(daily), size=(2000, len(daily)))
    sampled_delta = daily.delta.to_numpy()[ix].sum(axis=1)
    sampled_pct = 100 * sampled_delta / daily.denom.to_numpy()[ix].sum(axis=1)
    return {"replicates": 2000, "seed": 20261102, "blocks": len(daily),
            "unit": "KST calendar day; candidate minus reference50; negative favors candidate",
            "W_delta_95CI": np.quantile(sampled_delta, [.025, .975]).tolist(),
            "W_pct_delta_95CI": np.quantile(sampled_pct, [.025, .975]).tolist()}


def self_check() -> None:
    """Hand-computed asymmetric errors catch weights, signs, and score scaling."""
    frame = pd.DataFrame({"y": [10., 20.], "p": [12., 19.], "smp": [100., 200.], "k": [1., 3.]})
    result = metrics(frame, "p")
    assert result["W"] == 800 and result["revenue"] == 5000 and result["S"] == 4920
    assert np.isclose(result["W_pct"], 100 * 800 / 13000)
