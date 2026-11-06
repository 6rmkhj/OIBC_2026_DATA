# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
"""Right-closed target-day outer diagnostics; no model-selection decisions."""
from pathlib import Path
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- preserve established score arithmetic
from common import save_json


def metrics(frame: pd.DataFrame, prediction: str) -> dict[str, float | int]:
    assert np.isfinite(frame[[prediction, "y", "smp", "k"]].to_numpy()).all()
    weight = frame.smp * frame.k
    penalty = float((weight * (frame[prediction] - frame.y).abs()).sum())
    denominator = float((weight * frame.y).sum())
    revenue = float((frame.smp * frame.y).sum())
    assert denominator > 0
    return {"W": penalty, "W_pct": 100*penalty/denominator, "revenue": revenue, "S": revenue-.1*penalty, "rows": len(frame)}


def bootstrap(frame: pd.DataFrame) -> dict[str, int | list[float]]:
    weight = frame.smp * frame.k
    delta = weight * ((frame.p_candidate-frame.y).abs() - (frame.p_previous-frame.y).abs())
    day = (frame.ts-pd.Timedelta(hours=1)).dt.floor("D")
    daily = pd.DataFrame({"day": day, "delta": delta, "denominator": weight*frame.y}).groupby("day").sum()
    rng = np.random.default_rng(20261103)
    ix = rng.integers(0, len(daily), size=(2000, len(daily)))
    sampled = daily.delta.to_numpy()[ix].sum(axis=1)
    percentages = 100*sampled/daily.denominator.to_numpy()[ix].sum(axis=1)
    return {"replicates": 2000, "seed": 20261103, "blocks": len(daily), "W_delta_95CI": np.quantile(sampled, [.025,.975]).tolist(), "W_pct_delta_95CI": np.quantile(percentages, [.025,.975]).tolist()}


def report(frame: pd.DataFrame, destination: Path) -> None:
    january = pd.Timestamp("2025-01-01", tz="Asia/Seoul")
    june = pd.Timestamp("2025-06-01", tz="Asia/Seoul")
    fleet = frame[(frame.ts > january) & (frame.ts <= june)]
    assert len(fleet) == 7248
    months = (frame.ts-pd.Timedelta(hours=1)).dt.strftime("%Y-%m")
    slices = {"all": frame, "2025_Jan_May": fleet, "k11_15": frame[frame.k == 3], **dict(frame.groupby(months))}
    rows = [{"subset": subset, "recipe": recipe, **metrics(values, recipe)} for subset, values in slices.items() for recipe in ["p_previous", "p_candidate"]]
    pd.DataFrame(rows).to_csv(destination / "diagnostics.csv", index=False)
    save_json(destination / "outer_metrics.json", {recipe: metrics(frame, recipe) for recipe in ["p_previous", "p_candidate"]})
    save_json(destination / "bootstrap.json", {"all": bootstrap(frame), "2025_Jan_May": bootstrap(fleet)})


def self_check() -> None:
    frame = pd.DataFrame({"p": [12.,19.], "y": [10.,20.], "smp": [100.,200.], "k": [1.,3.]})
    result = metrics(frame, "p")
    assert result["W"] == 800 and result["revenue"] == 5000 and result["S"] == 4920
    assert np.isclose(result["W_pct"], 100*800/13000)
