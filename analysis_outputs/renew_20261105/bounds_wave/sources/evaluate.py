# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
# Run: python submission/autoresearch/evaluate.py --self-check
"""Frozen official weighted score and prediction boundary."""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- preserve existing model interface
from common import CACHE, SOURCE, digest, save_json


def verify_frozen() -> None:
    manifest = json.loads((CACHE / "manifest.json").read_text())
    for name, expected in manifest["cache_sha256"].items():
        assert digest(CACHE / name) == expected, f"Changed frozen input: {name}"
    for name, expected in manifest["fixed_sources"].items():
        assert digest(SOURCE / name) == expected, f"Changed evaluator: {name}"


def metrics(frame: pd.DataFrame) -> dict[str, float]:
    assert np.isfinite(frame[["y", "p", "smp", "k"]].to_numpy()).all(), "Nonfinite score input"
    weights = frame.smp * frame.k
    denominator = float((weights * frame.y).sum())
    assert denominator > 0
    penalty = float((weights * (frame.p - frame.y).abs()).sum())
    return {"W": penalty, "W_pct": 100 * penalty / denominator}


def align(predictions: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    assert list(predictions.columns) == ["ts", "grp", "p_dir"], "Invalid prediction schema"
    assert not predictions.duplicated(["ts", "grp"]).any(), "Duplicate predictions"
    assert np.isfinite(predictions.p_dir).all() and predictions.p_dir.ge(0).all(), "Invalid prediction values"
    result = labels.merge(predictions, on=["ts", "grp"], how="outer", validate="one_to_one", indicator=True)
    assert len(result) == len(labels) and result._merge.eq("both").all(), "Prediction keys differ"
    return result.drop(columns="_merge")


def evaluate(trial: Path, weight: float) -> dict[str, float]:
    verify_frozen()
    assert 0 <= weight <= 1
    labels = pd.read_parquet(CACHE / "selection_labels.parquet")
    frame = align(pd.read_parquet(trial / "predictions.parquet"), labels)
    frame["p"] = (1-weight) * frame.p_bu + weight * frame.p_dir
    # The timestamp is the end of the hourly interval, including midnight.
    months = (frame.ts - pd.Timedelta(hours=1)).dt.strftime("%Y-%m")
    diagnostics = [{"slice": month, **metrics(rows)} for month, rows in frame.groupby(months)]
    mid = pd.Timestamp("2023-12-01", tz="Asia/Seoul")
    diagnostics += [{"slice": name, **metrics(rows)} for name, rows in [("first_half", frame[frame.ts <= mid]), ("second_half", frame[frame.ts > mid])]]
    pd.DataFrame(diagnostics).to_csv(trial / "diagnostics.csv", index=False)
    result = metrics(frame)
    save_json(trial / "score.json", result)
    return result


def self_check() -> None:
    frame = pd.DataFrame({"y": [10., 20.], "p": [12., 19.], "smp": [100., 200.], "k": [1., 3.]})
    score = metrics(frame)
    assert score["W"] == 800 and np.isclose(score["W_pct"], 100*800/13000)
    labels = pd.DataFrame({"ts": [1, 2], "grp": ["G1", "G1"], "y": [1., 2.]})
    valid = labels[["ts", "grp"]].assign(p_dir=[1., 2.])
    assert len(align(valid, labels)) == 2
    for bad in [valid.iloc[:1], valid.assign(p_dir=[np.nan, 2.]), valid.assign(p_dir=[-1., 2.]), pd.concat([valid, valid]), valid.rename(columns={"p_dir": "p"})]:
        try:
            align(bad, labels)
        except AssertionError:
            continue
        raise AssertionError("Malformed prediction accepted")
    print("PASS hand-computed W=800; malformed/missing/duplicate/nonfinite/negative predictions rejected")


if __name__ == "__main__":
    assert sys.argv[1:] == ["--self-check"]
    self_check()
