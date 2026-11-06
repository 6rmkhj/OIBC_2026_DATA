# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow"]
# ///
# How to run: python submission/score_push_verify_deployment.py
"""Independently check the fixed-recipe cutoff sensitivity evidence."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from math import fsum, isclose, isfinite
from typing import Final

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from autoresearch_verify_final import metrics
from score_push_verify import OUT, ROOT, digest

DEST: Final = OUT / "deployment_check"
KST: Final = timezone(timedelta(hours=9))
HOUR: Final = timedelta(hours=1)


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = json.loads((DEST / "protocol.json").read_text())
    controller = json.loads((DEST / "resume/controller_receipt.json").read_text())
    assert controller["exit_code"] == 0
    assert controller["original_controller_exit_code"] is None
    assert controller["original_status"] == "interrupted"
    amendment = json.loads((DEST / "resource_amendment.json").read_text())
    assert controller["amendment_sha256"] == digest(DEST / "resource_amendment.json")
    assert amendment["protocol_sha256"] == digest(DEST / "protocol.json")
    for relative, expected_hash in amendment["completed_before_sha256"].items():
        assert digest(DEST / relative) == expected_hash, relative
    for name, expected_hash in amendment["resumed_sources_sha256"].items():
        assert digest(DEST / "resume/sources" / name) == expected_hash, name
        assert digest(ROOT / "submission/score_push" / name) == expected_hash, name
    for relative, expected_hash in protocol["protected_sha256"].items():
        assert digest(ROOT / relative) == expected_hash, relative
    for name, record in protocol["snapshots"].items():
        assert digest(DEST / "sources" / (name + ".py")) == record["sha256"], name
    freeze = json.loads((DEST / "prediction_freeze.json").read_text())
    assert freeze["evaluation_labels_opened"] is False
    assert digest(DEST / "frozen_predictions.parquet") == freeze["sha256"]
    rows = pq.read_table(DEST / "paired_predictions.parquet").to_pylist()
    prediction = pq.read_table(DEST / "frozen_predictions.parquet").to_pylist()
    frozen = {(r["ts"], r["grp"]): r for r in prediction}
    original = pq.read_table(OUT / "final/outer_predictions.parquet").to_pylist()
    start = datetime(2025, 3, 1, tzinfo=KST)
    end = datetime(2025, 6, 1, tzinfo=KST)
    expected = {(start + i * HOUR, g) for i in range(1, 2209) for g in ("G1", "G2")}
    oracle = {(r["ts"], r["grp"]): r for r in original if start < r["ts"] <= end}
    assert len(rows) == len(prediction) == len(frozen) == len(oracle) == 4416
    assert {(r["ts"], r["grp"]) for r in rows} == set(frozen) == set(oracle) == expected
    for row in rows:
        key = row["ts"], row["grp"]
        assert all(row[k] == oracle[key][k] for k in ("y", "smp", "k", "site_count"))
        assert all(row[k] == value for k, value in frozen[key].items())
        assert row["k"] == (3 if 11 <= row["ts"].hour <= 15 else 1)
        assert all(isfinite(row[k]) and row[k] >= 0 for k in
                   ("y", "smp", "p_bu", "incumbent", "rich", "normalized", "mlp", "station", "p_previous", "p_candidate"))
        # The frozen bottom-up column retains float32 multiplication before mixing with float64 components.
        weighted_bu = float(np.float32(.23573055176599533) * np.float32(row["p_bu"]))
        reference = .7642694482340047 * row["rich"] + weighted_bu
        refined = .380705173762783 * reference + .41926809371483975 * row["normalized"] + .2000267325223772 * row["mlp"]
        candidate = .7191528379552014 * refined + .2808471620447986 * row["station"]
        old_weighted_bu = float(np.float32(1 - .7149301735712863) * np.float32(row["p_bu"]))
        incumbent = .7149301735712863 * row["incumbent"] + old_weighted_bu
        assert isclose(candidate, row["p_candidate"], rel_tol=1e-12, abs_tol=1e-8)
        assert isclose(incumbent, row["p_previous"], rel_tol=1e-12, abs_tol=1e-8)
    train_counts = json.loads((DEST / "site_train_counts.json").read_text())
    assert len(train_counts) == len({r["site_id"] for r in train_counts}) == 253
    assert all(datetime.fromisoformat(r["train_max"]) <= start and r["fitted"] == (r["rows"] >= 1000) for r in train_counts)
    features = json.loads((DEST / "features.json").read_text())
    assert datetime.fromisoformat(features["train_max"]) <= start
    for member in ("incumbent", "candidate", "station_candidates"):
        assert not {"energy", "cf", "y"} & set(features[member])
    worker_scores = json.loads((DEST / "metrics.json").read_text())
    worker_bootstrap = json.loads((DEST / "bootstrap.json").read_text())
    scores, intervals = {}, {}
    for cutoff, values in (("original_2024Jun1", list(oracle.values())), ("fresh_2025Mar1", rows)):
        scores[cutoff] = {p: metrics(values, p) for p in ("p_previous", "p_candidate")}
        for arm, values_score in scores[cutoff].items():
            assert all(isclose(v, worker_scores[cutoff][arm][name], rel_tol=1e-12, abs_tol=1e-6)
                       for name, v in values_score.items())
        daily = {}
        for row in values:
            key = (row["ts"] - HOUR).date()
            weight = row["smp"] * row["k"]
            delta = weight * (abs(row["p_candidate"] - row["y"]) - abs(row["p_previous"] - row["y"]))
            daily.setdefault(key, []).append((delta, weight * row["y"]))
        blocks = np.array([(fsum(x[0] for x in daily[d]), fsum(x[1] for x in daily[d])) for d in sorted(daily)])
        indices = np.random.default_rng(20261104).integers(0, len(blocks), size=(2000, len(blocks)))
        samples = blocks[indices].sum(axis=1)
        intervals[cutoff] = np.quantile(100 * samples[:, 0] / samples[:, 1], [.025, .975]).tolist()
        np.testing.assert_allclose(intervals[cutoff], worker_bootstrap[cutoff]["W_pct_delta_95CI"], atol=1e-10, rtol=1e-10)
    receipt = json.loads((DEST / "resume/runtime.json").read_text())
    assert receipt["parallel_fits"] == 1 and receipt["model_n_jobs"] == 16 and receipt["priority_class"] == 32
    assert receipt["station_fits"] == 3 and receipt["blas_threads"] == 16
    for seed in range(3):
        runtime = json.loads((DEST / f"resume/models/station/seed{seed}/runtime.json").read_text())
        assert runtime["model_n_jobs"] == 16 and runtime["priority_class"] == 32
        assert runtime["parallel_fits"] == 1 and runtime["pyarrow_cpu"] == 4
        assert all(runtime["environment"][k] == "16" for k in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"))
        assert runtime["replay_max_absolute_error"] <= 1e-6
    replay = json.loads((DEST / "replay.json").read_text())
    assert all(r["max_absolute_error"] <= 1e-6 for r in replay)
    result = {"status": "PASS", "method": "Independent raw-key, label, fixed-mixture, fsum and paired-day bootstrap check",
              "rows": len(rows), "protected_files": len(protocol["protected_sha256"]),
              "resource_amendment": "User authorized CPU16/BLAS16/Normal for the three remaining station fits; original interrupted execution preserved.",
              "replayed_models": len({r["model"] for r in replay}), "metrics": scores,
              "W_pct_delta_95CI": intervals,
              "limitation": "Post-hoc cutoff sensitivity, not a fresh holdout or official leaderboard score."}
    (DEST / "independent_check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
