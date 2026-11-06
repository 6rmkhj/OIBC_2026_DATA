# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn"]
# ///
# Run: python submission/autoresearch/calibrate.py SOURCE_ID NEW_ID
# Check: python submission/autoresearch/calibrate.py --self-check
"""Fit only a single blend coefficient on frozen inner-selection labels."""
import json
import subprocess
import sys
from dataclasses import asdict
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- retain existing prediction contract
from common import OUT, CACHE, SOURCE, save_json
from evaluate import align, verify_frozen
from train import Config


def optimal_weight(frame: pd.DataFrame, fallback: float) -> float:
    """Weighted median of target crossings minimizes the one-dimensional L1 loss."""
    assert np.isfinite(frame[["p_bu", "p_dir", "y", "smp", "k"]].to_numpy()).all()
    delta = frame.p_dir.to_numpy() - frame.p_bu.to_numpy()
    weights = (frame.smp * frame.k).to_numpy()
    assert (weights >= 0).all()
    valid = (delta != 0) & (weights > 0)
    if not valid.any():
        return fallback
    ratios = (frame.y.to_numpy()[valid] - frame.p_bu.to_numpy()[valid]) / delta[valid]
    masses = weights[valid] * np.abs(delta[valid])
    order = np.argsort(ratios)
    index = np.searchsorted(np.cumsum(masses[order]), masses.sum()/2)
    return float(np.clip(ratios[order[index]], 0, 1))


def self_check() -> None:
    frame = pd.DataFrame({"p_bu": [0., 0.], "p_dir": [10., 10.], "y": [2., 8.], "smp": [1., 3.], "k": [1., 1.]})
    assert optimal_weight(frame, .5) == .8
    assert optimal_weight(frame.assign(y=15.), .5) == 1.
    assert optimal_weight(frame.assign(y=-5.), .5) == 0.
    assert optimal_weight(frame.assign(p_dir=0.), .6) == .6
    assert optimal_weight(frame.assign(smp=0.), .6) == .6
    reverse = frame.assign(p_bu=10., p_dir=0., y=[8., 2.])
    assert optimal_weight(reverse, .5) == .8
    print("PASS unequal weights, signed forecast differences, [0,1] bounds and zero-mass fallback")


def main() -> None:
    verify_frozen()
    source_id, new_id = sys.argv[1:]
    source = OUT / "trials" / source_id
    original = Config(**json.loads((source / "config.json").read_text()))
    frame = align(pd.read_parquet(source / "predictions.parquet"), pd.read_parquet(CACHE / "selection_labels.parquet"))
    alpha = optimal_weight(frame, original.direct_weight)
    config = Config(**{**asdict(original), "id": new_id, "parent_id": source_id, "hypothesis": "Analytical weighted-median single blend coefficient fitted only on inner selection; no model fit", "direct_weight": alpha})
    path = OUT / f"{new_id}_config.json"
    save_json(path, asdict(config))
    subprocess.run([sys.executable, str(SOURCE / "rescore.py"), source_id, str(path)], check=True)
    save_json(OUT / "trials" / new_id / "calibration.json", {"method": "weighted median of (y-b)/(d-b), mass SMP*k*abs(d-b)", "alpha": alpha, "fit_period": "inner selection only", "model_fits": 0, "source_trial": source_id})
    print(f"CALIBRATION {source_id} alpha={alpha:.16g}", flush=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-check"]:
        self_check()
    else:
        main()
