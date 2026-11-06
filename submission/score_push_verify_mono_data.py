# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow"]
# ///
# How to run: python submission/score_push_verify_mono_data.py BEFORE real fits.
"""Independently verify fixed monotonic signs and unchanged temporal inputs."""
from __future__ import annotations

import json
import re
from datetime import datetime
from math import fsum
from typing import Final
from zoneinfo import ZoneInfo

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from score_push_verify_mlp_data import ROOT, read, digest
from score_push_verify_renew_final_data import equal_source, scale

RENEW: Final = ROOT / "analysis_outputs/renew_20261105"
OUT: Final = RENEW / "mono_wave"
GPU: Final = ROOT / "analysis_outputs/score_push_gpu_20261104/data"


def direction(name: str) -> int:
    if name in {"wa_cloud", "wb_cloud"} or re.fullmatch(r"wa_station_WA\d{3}_wa_cloud|wb_station_WB\d{3}_wb_cloud", name):
        return -1
    if name in {"toaa", "toab"} or re.fullmatch(r"wa_station_WA\d{3}_toaa|wb_station_WB\d{3}_toab", name):
        return 1
    return 0


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
    assert not list(OUT.rglob("model.txt"))
    for stage, previous in (("weather", "calibration_wave"), ("hour", "hour_wave"), ("cloud", "sky_wave")):
        assert (OUT / f"original_{stage}_coefficients.json").read_bytes() == (RENEW / previous / "coefficients.json").read_bytes()
    records = []
    for fold, date in (("primary", "2023-06-01"), ("recent", "2024-06-01")):
        directory = OUT / "data" / fold
        cutoff = datetime.fromisoformat(date).replace(tzinfo=ZoneInfo("Asia/Seoul"))
        train, evaluation = [pq.read_table(directory / f"{name}.parquet") for name in ("train", "evaluation")]
        for name, table in (("train", train), ("evaluation", evaluation)):
            original = pq.read_table(GPU / fold / f"{name}.parquet")
            assert len(table) == len(original) and table.select(["ts", "grp"]).to_pylist() == original.select(["ts", "grp"]).to_pylist()
            equal_source(table, original)
        candidates = read(GPU / fold / "features.json")["station"]
        assert set(train.column_names) == {"ts", "grp", "cf", *candidates}
        assert set(evaluation.column_names) == {"ts", "grp", "capacity_kw", *candidates}
        selected = [name for name in candidates if len(np.unique(train[name].to_numpy()[~np.isnan(train[name].to_numpy())])) > 1]
        spec = read(directory / "feature_mask.json")
        assert spec["candidate_columns"] == candidates and spec["selected_columns"] == selected
        signs = [direction(name) for name in selected]
        assert signs.count(-1) == signs.count(1) == (62 if fold == "primary" else 117)
        assert all(direction(name) == 0 for name in selected if name.endswith(("_csa", "_csb")) or name in {"csa", "csb"})
        vectors = pq.read_table(directory / "constraints.parquet")
        assert vectors["feature"].to_pylist() == selected
        assert vectors["feature_index"].to_pylist() == list(range(len(selected)))
        assert vectors["fair_control"].to_pylist() == [0] * len(selected) and vectors["fair_monotone"].to_pylist() == signs
        times = train["ts"].to_pylist()
        assert all(ts <= cutoff for ts in times) and all(ts > cutoff for ts in evaluation["ts"].to_pylist())
        normalizer = scale(train["cosz"].to_numpy())
        age = np.array([(cutoff - ts).total_seconds() / 86400 for ts in times])
        raw_decay = np.exp2(-age / 180)
        decay = raw_decay / (fsum(raw_decay) / len(raw_decay))
        weights = normalizer * decay
        target = train["cf"].to_numpy() / normalizer
        saved = pq.read_table(directory / "training_transform.parquet")
        assert saved.select(["ts", "grp"]).to_pylist() == train.select(["ts", "grp"]).to_pylist()
        for name, expected in (("normalizer", normalizer), ("age_days", age), ("decay", raw_decay), ("recency_multiplier", decay), ("sample_weight", weights), ("target_normalized", target)):
            np.testing.assert_allclose(saved[name].to_numpy(), expected, rtol=1e-12, atol=1e-12, err_msg=name)
        temporal = pq.read_table(RENEW / "recency_wave/data/decay180" / fold / "training_weights.parquet")
        np.testing.assert_array_equal(saved["sample_weight"].to_numpy(), temporal["sample_weight"].to_numpy())
        inverse = pq.read_table(directory / "evaluation_transform.parquet")
        assert inverse.select(["ts", "grp"]).to_pylist() == evaluation.select(["ts", "grp"]).to_pylist()
        eval_scale = scale(evaluation["cosz"].to_numpy())
        for name, expected in (("normalizer", eval_scale), ("capacity_kw", evaluation["capacity_kw"].to_numpy()), ("inverse_kwh", eval_scale * evaluation["capacity_kw"].to_numpy())):
            np.testing.assert_allclose(inverse[name].to_numpy(), expected, rtol=1e-12, atol=1e-12, err_msg=name)
        for name in ("labels.parquet", "coverage.parquet", "application_inputs.parquet"):
            assert (directory / name).read_bytes() == (RENEW / "mlp_wave/data" / fold / name).read_bytes()
        records.append({"fold": fold, "train_rows": len(train), "evaluation_rows": len(evaluation),
                        "features": len(selected), "negative_constraints": signs.count(-1),
                        "positive_constraints": signs.count(1), "weight_sum": fsum(weights)})
    evidence = {"status": "PASS", "records": records, "protocol_sha256": digest(OUT / "protocol.json"),
                "prepared_manifest_sha256": digest(OUT / "prepared_manifest.json"),
                "scope": "All original inputs, train-only masks, exact sign order, temporal weights, normalized targets and inverses, frozen references and application inputs. Zero real fits."}
    (OUT / "independent_data_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
