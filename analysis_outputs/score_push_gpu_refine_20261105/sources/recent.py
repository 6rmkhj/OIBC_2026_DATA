# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn"]
# ///
# Run: python submission/score_push/recent.py
"""Reproduce recent incumbent and evaluate frozen primary richer-direct recipe."""
from wave_common import ALPHA, RICH_ALPHA, FINAL, OUT, ROOT, PRIMARY_END, RECENT_END, configure, receipt, snapshots, score, save_json, digest, align
import gc
import importlib.util
import json
import sys
from dataclasses import replace, asdict
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen numerical interface
from features import build


def main() -> None:
    configure()
    out = OUT / "recent"
    out.mkdir(exist_ok=True)
    snapshots(out / "sources")
    spec = importlib.util.spec_from_file_location("recent_frozen_predictor", FINAL / "train_snapshot.py")
    assert spec is not None and spec.loader is not None
    model = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = model
    spec.loader.exec_module(model)
    baseline_features = model.BASE_FEATURES
    config = model.Config(**json.loads((FINAL / "config.json").read_text()))
    train = pd.read_parquet(FINAL / "outer_train.parquet", filters=[("ts", "<=", PRIMARY_END)])
    selection = pd.read_parquet(FINAL / "outer_features.parquet", filters=[("ts", ">", PRIMARY_END), ("ts", "<=", RECENT_END)])
    labels = pd.read_parquet(FINAL / "outer_predictions.parquet", columns=["ts", "grp", "y", "p_bu", "smp", "k", "candidate_direct", "p_candidate"], filters=[("ts", ">", PRIMARY_END), ("ts", "<=", RECENT_END)])
    assert len(labels) == 13104 and labels.ts.max() <= RECENT_END
    assert train.ts.max() <= PRIMARY_END < selection.ts.min() and selection.ts.max() <= RECENT_END
    labels.to_parquet(out / "labels.parquet", index=False)
    direct, models, timings = model.predict_frames(train, selection, config)
    expected = pd.read_parquet(FINAL / "outer_selected/direct.parquet", filters=[("ts", "<=", RECENT_END)])
    pd.testing.assert_frame_equal(direct.reset_index(drop=True), expected.reset_index(drop=True), check_exact=True)
    aligned = align(labels[["ts", "grp"]].merge(direct, on=["ts", "grp"], how="left", validate="one_to_one").fillna({"p_dir": 0.}), labels)
    np.testing.assert_array_equal(aligned.p_dir, aligned.candidate_direct)
    aligned["p"] = (1-ALPHA)*aligned.p_bu + ALPHA*aligned.p_dir
    np.testing.assert_array_equal(aligned.p, aligned.p_candidate)
    baseline = score(aligned, out / "incumbent")
    assert abs(baseline-11.639886825195315) < 1e-10
    receipt(out / "incumbent/runtime.json", list(timings.values()))
    for name, fitted in models.items():
        fitted.booster_.save_model(str(out / "incumbent" / f"{name}.txt"))
    save_json(out / "incumbent/config.json", asdict(config))
    print("RECENT incumbent exact", baseline, flush=True)
    del models, aligned
    gc.collect()
    weather, _, inputs = build(end=RECENT_END, output=out)
    new_frames = []
    for frame in (train, selection):
        joined = frame.merge(weather, on=["ts", "grp"], how="left", validate="one_to_one", indicator=True)
        assert joined._merge.eq("both").all()
        joined = joined.drop(columns="_merge")
        joined["phys_humidity_clear"] = joined.wa_humidity*joined.csa
        joined["phys_dew_spread"] = joined.wb_temp-joined.wb_dew_point
        joined["phys_uv_clear"] = joined.wb_uv_idx*joined.csb
        new_frames.append(joined)
    train, selection = new_frames
    model.BASE_FEATURES = tuple(json.loads((OUT / "trials/combined_physics/features.json").read_text()))
    assert set(baseline_features) <= set(model.BASE_FEATURES)
    train.to_parquet(out / "cache/train.parquet", index=False)
    selection.to_parquet(out / "cache/selection.parquet", index=False)
    direct, models, timings = model.predict_frames(train, selection, config)
    predictions = labels[["ts", "grp"]].merge(direct, on=["ts", "grp"], how="left", validate="one_to_one").fillna({"p_dir": 0.})
    frame = align(predictions, labels)
    result = {"incumbent": baseline}
    for name, alpha in (("rich_fixed_alpha", ALPHA), ("rich_primary_alpha", RICH_ALPHA)):
        output = frame.assign(p=(1-alpha)*frame.p_bu+alpha*frame.p_dir, alpha=alpha)
        result[name] = score(output, out / name)
        save_json(out / name / "config.json", asdict(replace(config, direct_weight=alpha)))
    receipt(out / "rich_fixed_alpha/runtime.json", list(timings.values()))
    for name, fitted in models.items():
        fitted.booster_.save_model(str(out / "rich_fixed_alpha" / f"{name}.txt"))
    inputs += [FINAL / name for name in ("outer_train.parquet", "outer_features.parquet", "outer_predictions.parquet", "outer_selected/direct.parquet", "train_snapshot.py", "config.json")]
    save_json(out / "manifest.json", {"inputs_sha256": {str(p.relative_to(ROOT)): digest(p) for p in inputs}, "outputs_sha256": {str(p.relative_to(out)): digest(p) for p in out.rglob("*.parquet")}, "feature_names": list(model.BASE_FEATURES), "primary_end": str(PRIMARY_END), "recent_end": str(RECENT_END), "baseline_prediction_exact": True, "confirmation_loaded": False, "test_loaded": False})
    save_json(out / "results.json", result)
    print("RECENT COMPLETE", result, flush=True)


if __name__ == "__main__":
    main()
