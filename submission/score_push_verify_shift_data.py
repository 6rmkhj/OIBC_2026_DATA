# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow"]
# ///
# How to run: python submission/score_push_verify_shift_data.py BEFORE shift fits.
"""Independently verify projected domain inputs and their train-only transforms."""
from __future__ import annotations

import json
from typing import Final
from zoneinfo import ZoneInfo

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from score_push_verify_mlp_data import ROOT, digest, read

OUT: Final = ROOT / "analysis_outputs/renew_20261106/shift_wave"
SOURCE: Final = ROOT / "analysis_outputs/renew_20261106/poisson_wave"
COLUMNS: Final = [
    "wa_cloud", "wa_temp", "wa_humidity", "wa_ground_press", "wa_wind_speed", "wa_rain",
    "wb_cloud", "wb_uv_idx", "wb_temp", "wb_rel_hum", "wb_dew_point", "wb_vis",
    "wb_ceiling", "wb_precip_prob", "wb_total_liq", "cosz", "doy_sin", "doy_cos", "hour", "grp_code",
]
COPIES: Final = [
    "train.parquet", "evaluation.parquet", "feature_mask.json", "training_transform.parquet",
    "evaluation_transform.parquet", "application_inputs.parquet", "coverage.parquet", "labels.parquet",
]


def hashes() -> None:
    protocol = read(OUT / "protocol.json")
    for mapping in (protocol["input_sha256"], protocol["protected_sha256"]):
        for path, expected in mapping.items():
            assert digest(ROOT / path) == expected, path
    for name, record in protocol["own_sources"].items():
        assert digest(ROOT / record["original"]) == digest(OUT / "sources/own" / name) == record["sha256"]
    for name, record in protocol["snapshots"].items():
        assert digest(ROOT / record["original"]) == digest(OUT / "sources" / f"{name}.py") == record["sha256"]
    for path, expected in read(OUT / "prepared_manifest.json").items():
        assert digest(OUT / path) == expected, path


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    hashes()
    assert not list((OUT / "trials").glob("**/model.txt"))
    assert not list((OUT / "domain_trials").glob("**/classifier.joblib"))
    prior = read(SOURCE / "independent_check.json")
    assert prior["status"] == "PASS"
    assert prior["terminal_manifest_sha256"] == digest(SOURCE / "terminal_manifest.json")
    for path, expected in read(SOURCE / "terminal_manifest.json").items():
        assert digest(SOURCE / path) == expected, path
    assert (OUT / "original_weather_coefficients.json").read_bytes() == (SOURCE / "original_weather_coefficients.json").read_bytes()
    checked = []
    for fold in ("primary", "recent"):
        directory = OUT / "data" / fold
        for name in COPIES:
            assert digest(directory / name) == digest(SOURCE / "data" / fold / name), (fold, name)
        matrices = {}
        for kind in ("train", "evaluation"):
            original = pq.read_table(SOURCE / "data" / fold / f"{kind}.parquet", columns=COLUMNS)
            projection = pq.read_table(directory / f"domain_{kind}_inputs.parquet")
            assert projection.column_names == COLUMNS and len(projection) == len(original)
            for name in COLUMNS:
                np.testing.assert_array_equal(projection[name].to_numpy(), original[name].to_numpy(), err_msg=name)
            # Match the frozen column-major reduction order without changing values or tolerance.
            matrices[kind] = np.asfortranarray(np.column_stack([original[name].to_numpy() for name in COLUMNS]), dtype=np.float64)
            assert not np.isinf(matrices[kind]).any()
        source = matrices["train"]
        medians = np.nanmedian(source, axis=0)
        assert np.isfinite(medians).all()
        imputed = np.where(np.isnan(source), medians, source)
        means = imputed.mean(axis=0)
        stds = imputed.std(axis=0, ddof=0)
        scales = np.where(stds == 0, 1., stds)
        preprocessing = read(directory / "preprocessing.json")
        assert preprocessing["columns"] == COLUMNS and preprocessing["clip"] == [-8, 8]
        assert preprocessing["training_rows"] == len(source)
        for field, expected in (("median", medians), ("mean", means), ("scale", scales)):
            np.testing.assert_allclose(preprocessing[field], expected, rtol=1e-14, atol=1e-12)
        clips = {}
        for kind, matrix in matrices.items():
            standardized = (np.where(np.isnan(matrix), medians, matrix) - means) / scales
            expected = np.clip(standardized, -8., 8.)
            saved = np.load(directory / f"domain_{kind}_matrix.npy", allow_pickle=False)
            assert saved.dtype == np.float64 and saved.shape == (len(matrix), 20)
            assert np.isfinite(saved).all() and np.abs(saved).max() <= 8.
            np.testing.assert_allclose(saved, expected, rtol=1e-14, atol=1e-12)
            clips[kind] = int(np.count_nonzero(np.abs(standardized) > 8))
        keys = pq.read_table(directory / "train.parquet", columns=["ts", "grp"]).to_pylist()
        partition = pq.read_table(directory / "domain_fold.parquet")
        assert partition.column_names == ["ts", "grp", "date_ordinal", "domain_fold"]
        assert partition.select(["ts", "grp"]).to_pylist() == keys
        ordinals = np.array([r["ts"].astimezone(ZoneInfo("Asia/Seoul")).date().toordinal() for r in keys])
        np.testing.assert_array_equal(partition["date_ordinal"].to_numpy(), ordinals)
        folds = ordinals % 3
        np.testing.assert_array_equal(partition["domain_fold"].to_numpy(), folds)
        counts = []
        for split in range(3):
            held = folds == split
            assert held.any() and (~held).any()
            assert not set(ordinals[held]) & set(ordinals[~held])
            counts.append(int(held.sum()))
        assert sum(counts) == len(source)
        checked.append({"fold": fold, "train_rows": len(source), "evaluation_rows": len(matrices["evaluation"]),
                        "domain_columns": 20, "source_partition_rows": counts, "clipped_entries": clips,
                        "generation_files_byte_identical": True, "domain_inputs_exclude_energy_labels": True})
    evidence = {"status": "PASS", "records": checked, "protocol_sha256": digest(OUT / "protocol.json"),
                "prepared_manifest_sha256": digest(OUT / "prepared_manifest.json"), "real_fits": 0,
                "scope": "Verified original generation lineage; independent20column projections, train-only medians/means/population scales, bounded matrices and KST daily source partitions. Future weather is transductive; future generation labels excluded."}
    (OUT / "independent_data_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
