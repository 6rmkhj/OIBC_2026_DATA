# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow"]
# ///
# How to run: python submission/score_push_verify_gpu.py
"""Independent bounded GPU development selection and artifact verification."""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from math import fsum, isclose, isfinite
from typing import Final

import pyarrow as pa
import pyarrow.parquet as pq

from autoresearch_verify_final import metrics
from score_push_verify import ROOT, digest

OUT: Final = ROOT / "analysis_outputs/score_push_gpu_20261104"
CPU: Final = ROOT / "analysis_outputs/score_push_20261104"
KST: Final = timezone(timedelta(hours=9))
HOUR: Final = timedelta(hours=1)
BASE: Final = {"primary": 12.041603595410752, "recent": 11.064366712650248}


def main(refinement: bool = False) -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    output = ROOT / "analysis_outputs/score_push_gpu_refine_20261105" if refinement else OUT
    protocol = json.loads((output / "protocol.json").read_text())
    result = json.loads((output / "results.json").read_text())
    controller = json.loads((output / "controller_receipt.json").read_text())
    terminal_key = "all_24_trial_controllers_terminal" if refinement else "all_trial_controllers_terminal"
    assert controller["exit_code"] == 0 and controller[terminal_key]
    assert not result["confirmation_loaded"] and not result["test_loaded"]
    for relative, expected in protocol["protected_sha256"].items():
        assert digest(ROOT / relative) == expected, relative
    for name, record in protocol["own_sources"].items():
        assert digest(output / "sources/own" / name) == record["sha256"]
    active_sources, active_folder = protocol["own_sources"], "sources/own"
    if refinement:
        amendment = json.loads((output / "prefit_amendment.json").read_text())
        assert amendment["model_fits_before_amendment"] == 0
        assert amendment["original_protocol_sha256"] == digest(output / "protocol.json")
        active_sources, active_folder = amendment["own_sources"], amendment["active_source_snapshots"]
    for name, record in active_sources.items():
        assert digest(ROOT / record["original"]) == record["sha256"]
        assert digest(output / active_folder / name) == record["sha256"]
    for relative, expected in json.loads((output / "artifact_hashes.json").read_text()).items():
        assert digest(output / relative) == expected, relative
    if refinement:
        for fold in BASE:
            folder = output / "data" / fold
            money_info = json.loads((folder / "money.json").read_text())
            cutoff = datetime(2023 if fold == "primary" else 2024, 6, 1, tzinfo=KST)
            prices = pq.read_table(ROOT / money_info["price_source"], columns=["ts", "smp", "k"], filters=[("ts", "<=", cutoff)]).to_pylist()
            caps = pq.read_table(ROOT / money_info["source"], columns=["ts", "grp", "capacity_kw"], filters=[("ts", "<=", cutoff)]).to_pylist()
            price_map = {r["ts"]: (r["smp"], r["k"]) for r in prices}
            capacity_map = {(r["ts"], r["grp"]): r["capacity_kw"] for r in caps}
            money = pq.read_table(folder / "training_money.parquet").to_pylist()
            train = pq.read_table(folder / "train.parquet", columns=["ts", "grp"]).to_pylist()
            assert len(money) == len(train) == len(capacity_map)
            assert [(r["ts"], r["grp"]) for r in money] == [(r["ts"], r["grp"]) for r in train]
            costs = []
            for row in money:
                assert row["ts"] <= cutoff and (row["smp"], row["k"]) == price_map[row["ts"]]
                assert row["capacity_kw"] == capacity_map[row["ts"], row["grp"]]
                assert row["k"] == (3 if 11 <= row["ts"].hour <= 15 else 1)
                costs.append(row["capacity_kw"] * row["smp"] * row["k"])
            mean_cost = fsum(costs) / len(costs)
            assert isfinite(mean_cost) and mean_cost > 0
            assert isclose(mean_cost, money_info["train_only_mean_capacity_smp_k"], rel_tol=1e-12)
            assert all(isfinite(r["normalized_cost"]) and r["normalized_cost"] >= 0 and
                       isclose(r["normalized_cost"], cost / mean_cost, rel_tol=1e-12) for r, cost in zip(money, costs, strict=True))
            assert sum(r["normalized_cost"] == 0 for r in money) == amendment["zero_weight_rows"][fold]
    checked = []
    for record in result["records"]:
        alpha = record["alpha_primary_only"]
        assert isfinite(alpha) and 0 <= alpha <= 1
        paired = {}
        for fold in ("primary", "recent"):
            start = datetime(2023, 6, 1, tzinfo=KST) if fold == "primary" else datetime(2024, 6, 1, tzinfo=KST)
            end = datetime(2024, 6, 1, tzinfo=KST) if fold == "primary" else datetime(2025, 3, 1, tzinfo=KST)
            count = int((end - start) / HOUR)
            expected_keys = {(start + i * HOUR, group) for i in range(1, count + 1) for group in ("G1", "G2")}
            reference = pq.read_table(CPU / f"closing_wave/{fold}/selected/predictions.parquet").to_pylist()
            oracle = {(r["ts"], r["grp"]): r for r in reference}
            rows = pq.read_table(output / f"comparisons/{record['variant']}/{record['stage']}/{fold}/predictions.parquet").to_pylist()
            assert len(rows) == len(oracle) == len(expected_keys)
            assert {(r["ts"], r["grp"]) for r in rows} == set(oracle) == expected_keys
            daylight = pq.read_table(output / f"data/{fold}/evaluation.parquet", columns=["ts", "grp"]).to_pylist()
            daylight_keys = {(r["ts"], r["grp"]) for r in daylight}
            assert len(daylight) == len(daylight_keys) and daylight_keys <= expected_keys
            members = []
            for seed in record["seeds"]:
                raw = pq.read_table(output / f"trials/{record['variant']}/{fold}/seed{seed}/daylight_raw.parquet").to_pylist()
                values = {(r["ts"], r["grp"]): r["p_raw"] for r in raw}
                assert len(raw) == len(values) and set(values) == daylight_keys
                assert all(isfinite(value) for value in values.values())
                members.append(values)
            for row in rows:
                key = row["ts"], row["grp"]
                assert all(row[name] == oracle[key][name] for name in ("y", "smp", "k"))
                assert row["p_reference"] == oracle[key]["p"] and row["alpha"] == alpha
                pure = max(0., fsum(member[key] for member in members) / len(members)) if key in daylight_keys else 0.
                assert isclose(row["p_new"], pure, rel_tol=1e-12, abs_tol=1e-7)
                assert isclose(row["p"], (1 - alpha) * row["p_reference"] + alpha * pure, rel_tol=1e-12, abs_tol=1e-7)
                assert all(isfinite(row[name]) and row[name] >= 0 for name in ("y", "smp", "p", "p_new", "p_reference"))
                assert row["k"] == (3 if 11 <= row["ts"].hour <= 15 else 1)
            computed = {arm: metrics(rows, arm) for arm in ("p", "p_new", "p_reference", "p_incumbent")}
            for arm, values in computed.items():
                for name, value in values.items():
                    assert isclose(value, record["scores"][fold][arm][name], rel_tol=1e-12, abs_tol=1e-5)
            assert isclose(computed["p_reference"]["W_pct"], BASE[fold], abs_tol=1e-10)
            paired[fold] = computed
            if fold == "primary":
                ratios = sorted(((r["y"] - r["p_reference"]) / (r["p_new"] - r["p_reference"]),
                                 r["smp"] * r["k"] * abs(r["p_new"] - r["p_reference"]))
                                for r in rows if r["p_new"] != r["p_reference"])
                half = fsum(weight for _, weight in ratios) / 2
                cumulative = 0.
                optimum = 0.
                for ratio, weight in ratios:
                    cumulative += weight
                    if cumulative >= half:
                        optimum = min(1., max(0., ratio))
                        break
                optimum_loss = fsum(r["smp"] * r["k"] * abs(r["y"] - ((1 - optimum) * r["p_reference"] + optimum * r["p_new"])) for r in rows)
                assert isclose(computed["p"]["W"], optimum_loss, rel_tol=1e-12, abs_tol=1e-4)
        both = all(paired[fold]["p"]["W_pct"] < BASE[fold] for fold in BASE)
        assert record["both_folds_improve"] == both and record["eligible"] == (both and alpha >= .02)
        checked.append({"variant": record["variant"], "stage": record["stage"], "alpha": alpha, "scores": paired, "eligible": record["eligible"]})
    if refinement:
        assert len(result["records"]) == 4 and all(r["seeds"] == [0, 1, 2] for r in result["records"])
        eligible = [r for r in result["records"] if r["eligible"]]
        adopted = min(eligible, key=lambda r: fsum(r["scores"][f]["p"]["W_pct"] / BASE[f] for f in BASE)) if eligible else None
        expected_fits = 24
    else:
        screens = [r for r in result["records"] if r["seeds"] == [0] and r["eligible"]]
        winner = min(screens, key=lambda r: fsum(r["scores"][fold]["p"]["W_pct"] / BASE[fold] for fold in BASE)) if screens else None
        assert result["followup_variant"] == (winner["variant"] if winner else None)
        ensembles = [r for r in result["records"] if r["seeds"] == [0, 1, 2]]
        adopted = next((r for r in ensembles if r["both_folds_improve"]), None)
        expected_fits = 8 if winner else 4
    assert result["selected"] == adopted and result["cpu_reference_retained"] == (adopted is None)
    trials = sorted((output / "trials").glob("*/*/seed*"))
    assert len(trials) == result["model_fit_count"] == expected_fits
    gpu = []
    for trial in trials:
        runtime = json.loads((trial / "runtime.json").read_text())
        replay = json.loads((trial / "replay.json").read_text())
        assert runtime["task_type"] == "GPU" and runtime["model_thread_count"] == 16 and runtime["priority_class"] == 32
        assert runtime["parallel_fits"] == 1 and runtime["pyarrow_cpu"] == 4
        assert replay["passed"] and replay["max_absolute_error"] == 0.
        assert digest(trial / "model.cbm") == replay["model_sha256"]
        assert json.loads((trial / "controller_receipt.json").read_text())["exit_code"] == 0
        with (trial / "gpu_samples.csv").open(encoding="utf-8", newline="") as stream:
            samples = list(csv.reader(stream))
        assert samples and all("RTX 5090 Laptop" in r[1] for r in samples)
        gpu.append({"trial": str(trial.relative_to(output)), "max_utilization_percent": max(float(r[2]) for r in samples), "max_memory_mib": max(float(r[3]) for r in samples)})
    evidence = {"status": "PASS", "records": checked, "selected": adopted,
                "protected_files": len(protocol["protected_sha256"]), "models": len(trials), "gpu": gpu,
                "limitations": "Adaptive historical development only; GPU training nondeterministic; no new leaderboard measurement."}
    (output / "independent_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    assert sys.argv[1:] in ([], ["--refinement"])
    main(refinement=bool(sys.argv[1:]))
