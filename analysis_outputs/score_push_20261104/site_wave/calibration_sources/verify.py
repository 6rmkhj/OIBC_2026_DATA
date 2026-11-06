# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
# Run: python submission/score_push/verify.py
"""No-fit replay of weather cache, feature mutation checks and artifact receipts."""
import os
for name, value in {"OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"}.items():
    os.environ[name] = value
import ctypes
from ctypes import wintypes
import inspect
import json
from pathlib import Path
import sys
import time
import pandas as pd  # noqa: PANDAS_OK -- frozen interface
import pyarrow as pa
import features
import check_features

sys.path.insert(0, str(features.ROOT / "submission/autoresearch"))
from common import digest, save_json


class MemoryCounters(ctypes.Structure):
    """Windows PROCESS_MEMORY_COUNTERS layout for measured peak resident memory."""
    _fields_ = [("cb", wintypes.DWORD), ("page_fault_count", wintypes.DWORD), ("peak_working_set", ctypes.c_size_t), ("working_set", ctypes.c_size_t), ("quota_peak_paged", ctypes.c_size_t), ("quota_paged", ctypes.c_size_t), ("quota_peak_nonpaged", ctypes.c_size_t), ("quota_nonpaged", ctypes.c_size_t), ("pagefile", ctypes.c_size_t), ("peak_pagefile", ctypes.c_size_t)]


def main() -> None:
    ctypes.windll.kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    ctypes.windll.kernel32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(MemoryCounters), wintypes.DWORD]
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    assert ctypes.windll.kernel32.SetPriorityClass(handle, 0x4000)
    pa.set_cpu_count(2)
    pa.set_io_thread_count(2)
    check_features.main()
    original = features.weighted_weather
    mutated = inspect.getsource(original).replace("values.mul(rows.capacity_kw, axis=0)", "values")
    assert mutated != inspect.getsource(original)
    namespace = {"pd": pd}
    exec(compile(mutated, "weighted_weather_mutant", "exec"), namespace)
    check_features.weighted_weather = namespace["weighted_weather"]
    try:
        check_features.main()
    except AssertionError:
        print("PASS deliberate capacity-weighting mutant rejected by numerical fixture", flush=True)
    else:
        raise AssertionError("Capacity-weighting mutant survived")
    finally:
        check_features.weighted_weather = original
    check_features.main()
    evidence = features.OUT / "evidence"
    started = time.monotonic()
    replay, _, _ = features.build(output=evidence / "cache_replay")
    expected = pd.read_parquet(features.OUT / "cache/weather.parquet")
    pd.testing.assert_frame_equal(expected, replay, check_exact=True)
    memory = MemoryCounters()
    memory.cb = ctypes.sizeof(memory)
    assert ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(memory), memory.cb)
    manifest = json.loads((features.OUT / "cache/manifest.json").read_text())
    for relative, sha in manifest["inputs_sha256"].items():
        assert digest(features.ROOT / relative) == sha
    for name, sha in manifest["cache_sha256"].items():
        assert digest(features.OUT / "cache" / name) == sha
    for name, sha in manifest["source_sha256"].items():
        assert digest(features.OUT / "sources" / name) == sha
    runtime = [json.loads(p.read_text()) for p in (features.OUT / "trials").glob("*/runtime.json")]
    assert len(runtime) == 7 and all(r["priority_class"] == 16384 and r["model_n_jobs"] == 2 and r["parallel_fits"] == 1 and r["pyarrow_cpu"] == r["pyarrow_io"] == 2 for r in runtime)
    base = pd.read_csv(features.OUT / "trials/baseline_exact/diagnostics.csv")
    winner = pd.read_csv(features.OUT / "trials/winner_calibrated/diagnostics.csv")
    diagnostics = base.merge(winner, on="slice", validate="one_to_one", suffixes=("_baseline", "_winner"))
    diagnostics["delta_W_pct"] = diagnostics.W_pct_winner-diagnostics.W_pct_baseline
    diagnostics.to_csv(evidence / "winner_slice_comparison.csv", index=False)
    save_json(evidence / "verification.json", {"weather_cache_exact_replay": True, "key_mismatch_rejected": True, "label_perturbation_invariant": True, "weighting_mutant_rejected": True, "input_cache_executed_snapshot_hashes_verified": True, "model_configs": len(runtime), "model_fits": sum(len(r["fit_seconds"]) for r in runtime), "maximum_simultaneous_fits": 1, "rebuild_seconds": time.monotonic()-started, "rebuild_peak_working_set_bytes": memory.peak_working_set, "rebuild_working_set_bytes": memory.working_set, "runtime_receipts": [str(p.relative_to(features.ROOT)) for p in (features.OUT / "trials").glob("*/runtime.json")], "current_source_sha256": {p.name: digest(p) for p in Path(__file__).parent.glob("*.py")}, "source_delta_after_fit": "Added round-key rejection guard and numerical fixture; exact no-fit weather cache replay proves unchanged primary features. Original executed snapshots remain immutable.", "skipped": "No outer evaluation, test data, full-data refit, submission export, or installed LSP/typechecker."})
    print(diagnostics.to_string(index=False), flush=True)
    print("PASS exact weather cache replay, frozen hashes, 21 sequential fit receipts; measured rebuild peak bytes", memory.peak_working_set, flush=True)


if __name__ == "__main__":
    main()
