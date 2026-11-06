# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "joblib"]
# ///
# Run: python submission/autoresearch/prepare.py
"""Immutable selection-only preparation, preserving original aggregate numerics."""
import json
import sys
import time
from pathlib import Path
import pyarrow as pa
import pandas as pd  # noqa: PANDAS_OK -- preserve existing numerical interface
from common import ROOT, OUT, CACHE, SOURCE, digest, save_json

sys.path.insert(0, str(ROOT / "submission"))
import make_submission as model


def main() -> None:
    pa.set_cpu_count(2)
    pa.set_io_thread_count(2)
    start = time.monotonic()
    CACHE.mkdir(parents=True, exist_ok=True)
    assert not (CACHE / "manifest.json").exists(), "Preparation already frozen"
    previous = ROOT / "analysis_outputs/award_run"
    provenance = json.loads((previous / "provenance.json").read_text())
    old_cache = previous / "cache" / provenance["cache_key"]
    hashes = json.loads((old_cache / "feature_hashes.json").read_text())
    for name in ["feat_train.parquet", "smp.parquet"]:
        assert digest(old_cache / name) == hashes[name], name
    locked = json.loads((previous / "locked_configuration.json").read_text())
    assignment = locked["assignment"]
    cutoff = pd.Timestamp("2023-06-01", tz=model.TZ)
    end = pd.Timestamp("2024-06-01", tz=model.TZ)
    # Parquet predicate pushdown excludes outer-period labels entirely.
    data = pd.read_parquet(old_cache / "feat_train.parquet", filters=[("ts", "<=", end)])
    train = data[data.ts <= cutoff]
    selection = data[data.ts > cutoff]
    assert train.ts.max() < selection.ts.min()
    assert not data.duplicated(["site_id", "ts"]).any()
    grouped_train = model.group_frame(train[~train.night], assignment)
    clean = selection.drop(columns=[c for c in ["energy", "cf"] if c in selection])
    features = model.group_frame(clean[~clean.night], assignment)
    assert not {"energy", "cf", "y"} & set(features.columns)
    smp = pd.read_parquet(old_cache / "smp.parquet")[["ts", "smp", "k"]]
    grouped_train = grouped_train.merge(smp, on="ts", validate="many_to_one")
    site_path = previous / "inner_site_predictions.parquet"
    site_hash = digest(site_path)
    site = pd.read_parquet(site_path)
    aligned = selection[["site_id", "ts", "energy"]].merge(site, on=["site_id", "ts"], validate="one_to_one")
    assert len(aligned) == len(selection) == len(site)
    assert (aligned.energy.to_numpy() == aligned.y.to_numpy()).all()
    labels = site.assign(grp=site.site_id.map(assignment)).groupby(["ts", "grp"], as_index=False)[["y", "p"]].sum().rename(columns={"p": "p_bu"})
    labels = labels.merge(smp, on="ts", validate="many_to_one")
    grouped_train.to_parquet(CACHE / "train.parquet", index=False)
    features.to_parquet(CACHE / "selection_features.parquet", index=False)
    labels.to_parquet(CACHE / "selection_labels.parquet", index=False)
    save_json(CACHE / "assignment.json", assignment)
    save_json(CACHE / "features.json", model.GFEATS)
    manifest = {"inputs": {"feat_train": hashes["feat_train.parquet"], "smp": hashes["smp.parquet"], "inner_site_predictions": site_hash, "locked_configuration": digest(previous / "locked_configuration.json"), "model_source": digest(Path(model.__file__))}, "cache_sha256": {p.name: digest(p) for p in CACHE.iterdir() if p.is_file()}, "fixed_sources": {n: digest(SOURCE / n) for n in ["prepare.py", "evaluate.py", "common.py"]}, "train_end": str(cutoff), "selection_end": str(end), "training_rows": len(grouped_train), "selection_rows": len(labels), "training_sites_rows": len(train), "selection_sites_rows": len(selection), "expected_baseline_pct": 13.210225898116454, "threads_per_trial": 2, "parallel_trials": 2, "fit_ceiling_seconds": 600, "seconds": time.monotonic()-start}
    save_json(CACHE / "manifest.json", manifest)
    print(json.dumps(manifest), flush=True)


if __name__ == "__main__":
    main()
