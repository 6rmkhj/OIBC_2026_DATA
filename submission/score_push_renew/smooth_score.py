# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
# How to run: called once by smooth_run.py after preparation.
"""One fixed transform and one primary-period weighted absolute-error blend."""
import numpy as np
import pyarrow.parquet as pq

from smooth_common import FOLDS, OUT, SUPPORT, save
from smooth_math import apply


def compare() -> None:
    from calibrate import optimal_weight
    from final_metrics import metrics

    frames = {}
    for fold in FOLDS:
        directory = OUT / "data" / fold
        inputs = pq.read_table(directory / "application_inputs.parquet").to_pandas()
        transformed = apply(inputs)
        assert int(transformed.supported.sum()) == SUPPORT[fold]
        labels = pq.read_table(directory / "labels.parquet").to_pandas()
        frame = transformed.merge(labels[["ts", "grp", "y", "smp", "k"]], on=["ts", "grp"], validate="one_to_one", sort=False)
        assert frame[["ts", "grp"]].equals(inputs[["ts", "grp"]])
        frames[fold] = frame
    primary = frames["primary"]
    alpha = optimal_weight(primary.assign(p_bu=primary.p_reference, p_dir=primary.p_new), 0.)
    assert np.isfinite(alpha) and 0 <= alpha <= 1
    scores = {}
    for fold, frame in frames.items():
        frame["alpha"] = alpha
        frame["p"] = (1 - alpha) * frame.p_reference + alpha * frame.p_new
        directory = OUT / "comparisons" / fold
        directory.mkdir(parents=True, exist_ok=False)
        frame.to_parquet(directory / "predictions.parquet", index=False)
        scores[fold] = {name: metrics(frame, name) for name in ("p", "p_reference", "p_new")}
        save(directory / "metrics.json", scores[fold])
    both = all(scores[f]["p"]["W"] < scores[f]["p_reference"]["W"] for f in FOLDS)
    record = {"arm": "normalized_temporal_smoothing", "alpha_primary_only": alpha,
              "scores": scores, "both_folds_improve": both, "eligible": both and alpha >= .02}
    save(OUT / "results.json", {"records": [record], "selected": record if record["eligible"] else None,
         "eligible": record["eligible"], "reference_retained": not record["eligible"],
         "real_model_fit_count": 0, "real_calibration_fit_count": 0, "real_alpha_fit_count": 1,
         "candidate_count": 1, "primary_blend_partly_in_sample": True, "all_history_exposed": True,
         "confirmation_loaded": False, "test_loaded": False, "exported": False})
