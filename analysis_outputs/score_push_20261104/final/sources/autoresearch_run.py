# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm"]
# ///
# Run: python submission/autoresearch/run.py wave
# Or: python submission/autoresearch/run.py config.json [config2.json]
"""Central serialized ledger, isolated low-resource candidate subprocesses."""
import csv
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path
from common import OUT, SOURCE, CACHE, digest, save_json
from evaluate import evaluate, verify_frozen
from train import Config


def execute(config: Config) -> tuple[Path, int, float]:
    trial = OUT / "trials" / config.id
    trial.mkdir(parents=True, exist_ok=False)
    save_json(trial / "config.json", asdict(config))
    shutil.copy2(SOURCE / "train.py", trial / "train.py")
    save_json(trial / "snapshot.json", {"source_sha256": digest(trial / "train.py"), "config_sha256": digest(trial / "config.json"), "frozen_manifest_sha256": digest(CACHE / "manifest.json"), "parent_id": config.parent_id})
    env = os.environ.copy()
    temp = Path("C:/Users/slowg/AppData/Local/Temp/oibc-autoresearch-rkFdavwf/engine") / config.id
    temp.mkdir(parents=True, exist_ok=True)
    env.update({"TMPDIR": str(temp), "TEMP": str(temp), "TMP": str(temp), "NODE_COMPILE_CACHE": str(temp / "node"), "BUN_INSTALL_CACHE_DIR": str(temp / "bun"), "OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1", "PYTHONPATH": str(SOURCE)})
    command = [sys.executable, str(trial / "train.py"), str(trial)]
    save_json(trial / "invocation.json", {"argv": command, "threads": 2, "timeout_seconds": 600, "priority": "below_normal", "environment": {k: env[k] for k in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "TMPDIR"]}})
    start = time.monotonic()
    with (trial / "stdout.log").open("w", encoding="utf-8") as log:
        try:
            result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=600, creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW, check=False)
            code = result.returncode
        except subprocess.TimeoutExpired:
            log.write("Trial hard deadline exceeded; subprocess killed and reaped.\n")
            code = 124
    return trial, code, time.monotonic()-start


def record(completed: tuple[Path, int, float]) -> None:
    trial, code, seconds = completed
    config = Config(**json.loads((trial / "config.json").read_text()))
    ledger = OUT / "results.tsv"
    best_path = OUT / "best.json"
    best = json.loads(best_path.read_text()) if best_path.exists() else {"W": float("inf")}
    result = {"id": config.id, "parent_id": config.parent_id, "status": "crash", "W": "", "W_pct": "", "seconds": seconds, "exit_code": code, "source_sha256": digest(trial / "train.py"), "config_sha256": digest(trial / "config.json"), "hypothesis": config.hypothesis}
    if code == 0:
        try:
            score = evaluate(trial, config.direct_weight)
            if config.id == "baseline":
                expected = json.loads((CACHE / "manifest.json").read_text())["expected_baseline_pct"]
                assert abs(score["W_pct"]-expected) < 1e-5, (score, expected)
            result.update(score)
            result["status"] = "keep" if score["W"] < best["W"] else "discard"
            if result["status"] == "keep":
                save_json(best_path, result)
        except (AssertionError, ValueError, KeyError, OSError) as error:
            result["exit_code"] = 1
            result["hypothesis"] += f" | scoring failure: {type(error).__name__}: {error}"
            save_json(trial / "error.json", {"type": type(error).__name__, "message": str(error)})
            print(f"SCORING CRASH {config.id}: {type(error).__name__}: {error}", flush=True)
    with ledger.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(result), delimiter="\t")
        if stream.tell() == 0:
            writer.writeheader()
        writer.writerow(result)
    save_json(trial / "result.json", result)
    print(json.dumps(result), flush=True)


def wave() -> list[Config]:
    return [Config("baseline", "original", "Reproduce unchanged direct 50 percent baseline"),
            Config("scored", "baseline", "Capacity times SMP times k aligns CF loss with scored kWh", weighting="scored"),
            Config("capacity", "baseline", "Capacity weighting aligns CF loss with group kWh", weighting="capacity"),
            Config("trees800", "baseline", "More boosting reduces underfit", n_estimators=800),
            Config("leaves63", "baseline", "More trees and leaves capture weather interactions", n_estimators=800, num_leaves=63),
            Config("lr02", "baseline", "Slower 800-tree boosting improves generalization", n_estimators=800, learning_rate=.02),
            Config("l2", "baseline", "L2 alternative may offer ensemble diversity", objective="regression_l2"),
            Config("recent365", "baseline", "One-year half-life adapts to recent fleet and weather", recency_days=365),
            Config("recent730", "baseline", "Two-year half-life balances adaptation and history", recency_days=730)]


def main() -> None:
    verify_frozen()
    args = sys.argv[1:]
    configs = wave() if args == ["wave"] else [Config(**json.loads(Path(p).read_text())) for p in args]
    assert configs
    if configs[0].id == "baseline":
        record(execute(configs.pop(0)))
        assert (OUT / "best.json").exists(), "Baseline failed"
    for config in configs:
        record(execute(config))


if __name__ == "__main__":
    main()
