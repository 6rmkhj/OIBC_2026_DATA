# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
# How to run: imported by smooth_run.py after the protocol is frozen.
"""Project reference forecasts and label-free geometry onto exact full-hour keys."""
import shutil

import numpy as np
import pyarrow.parquet as pq

from smooth_common import APPLICATION, COVERAGE, DATA, FOLDS, OUT, REFERENCE, REFERENCE_DIR, digest, save


def prepare() -> None:
    from final_metrics import metrics

    receipts = []
    for fold in FOLDS:
        reference = pq.read_table(REFERENCE_DIR / fold / "predictions.parquet").to_pandas()
        labels = reference[["ts", "grp", "y", "smp", "k", "p"]].rename(columns={"p": "p_reference"})
        geometry = pq.read_table(DATA / fold / "evaluation.parquet", columns=["ts", "grp", "cosz", "capacity_kw"]).to_pandas()
        coverage = pq.read_table(COVERAGE / fold / "coverage.parquet").to_pandas()
        inputs = reference[["ts", "grp", "p", "static_capacity"]].rename(columns={"p": "p_reference"})
        inputs = inputs.merge(coverage, on=["ts", "grp"], validate="one_to_one", sort=False)
        inputs = inputs.merge(geometry, on=["ts", "grp"], how="left", validate="one_to_one", sort=False, indicator=True)
        assert inputs["_merge"].eq("left_only").eq(inputs.night).all()
        assert int(inputs["_merge"].eq("both").sum()) == len(geometry)
        inputs = inputs[APPLICATION]
        assert inputs[["ts", "grp"]].equals(labels[["ts", "grp"]])
        assert np.isfinite(inputs.p_reference).all() and inputs.p_reference.ge(0).all()
        assert inputs.p_reference.le(inputs.static_capacity).all()
        assert inputs.loc[inputs.night, "p_reference"].eq(0).all()
        assert abs(metrics(labels, "p_reference")["W_pct"] - REFERENCE[fold]) < 1e-10
        directory = OUT / "data" / fold
        directory.mkdir(parents=True, exist_ok=False)
        inputs.to_parquet(directory / "application_inputs.parquet", index=False)
        labels.to_parquet(directory / "labels.parquet", index=False)
        shutil.copyfile(COVERAGE / fold / "coverage.parquet", directory / "coverage.parquet")
        receipts.append({"fold": fold, "full_rows": len(inputs), "daylight_rows": len(geometry),
                         "night_rows": int(inputs.night.sum()), "application_columns": list(inputs),
                         "reference_W_pct": metrics(labels, "p_reference")["W_pct"]})
    save(OUT / "evidence/read_receipts.json", receipts)
    manifest = {str(p.relative_to(OUT)): digest(p) for p in (OUT / "data").rglob("*.parquet")}
    for name in ("read_receipts.json", "selfchecks.json"):
        manifest["evidence/" + name] = digest(OUT / "evidence" / name)
    save(OUT / "prepared_manifest.json", manifest)
