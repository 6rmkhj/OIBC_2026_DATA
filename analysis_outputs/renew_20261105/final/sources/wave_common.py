# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm"]
# ///
"""Shared resource receipts and frozen metric use for the paired site experiment."""
import os
for key, value in {"OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"}.items():
    os.environ[key] = value
import ctypes
from ctypes import wintypes
from pathlib import Path
import shutil
import sys
import pandas as pd  # noqa: PANDAS_OK -- frozen interface
import pyarrow as pa
from features import ROOT, OUT
from verify import MemoryCounters

sys.path.insert(0, str(ROOT / "submission/autoresearch"))
from common import digest, save_json
from evaluate import metrics, align
from calibrate import optimal_weight

FINAL = ROOT / "analysis_outputs/autoresearch_20261103/final"
PRIMARY_END = pd.Timestamp("2024-06-01", tz="Asia/Seoul")
RECENT_END = pd.Timestamp("2025-03-01", tz="Asia/Seoul")
ALPHA = .7149301735712863
RICH_ALPHA = .7642694482340047


def configure() -> None:
    ctypes.windll.kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    ctypes.windll.kernel32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    ctypes.windll.kernel32.GetPriorityClass.argtypes = [wintypes.HANDLE]
    ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(MemoryCounters), wintypes.DWORD]
    assert ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    pa.set_cpu_count(2)
    pa.set_io_thread_count(2)


def receipt(path: Path, fit_seconds: list[float], model_threads: int = 2) -> None:
    counters = MemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    assert ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
    priority = ctypes.windll.kernel32.GetPriorityClass(handle)
    assert priority == 16384
    save_json(path, {"pid": os.getpid(), "priority_class": priority, "parallel_fits": 1, "model_n_jobs": model_threads, "fit_seconds": fit_seconds, "peak_working_set_bytes": counters.peak_working_set, "working_set_bytes": counters.working_set, "environment": {k: os.environ[k] for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}, "pyarrow_cpu": pa.cpu_count(), "pyarrow_io": pa.io_thread_count()})


def snapshots(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    for path in Path(__file__).parent.glob("*.py"):
        shutil.copyfile(path, destination / path.name)
    for name in ("common.py", "evaluate.py", "calibrate.py"):
        shutil.copyfile(ROOT / "submission/autoresearch" / name, destination / f"frozen_{name}")
    save_json(destination / "hashes.json", {p.name: digest(p) for p in destination.glob("*.py")})


def score(frame: pd.DataFrame, directory: Path) -> float:
    """Use unchanged official loss; save right-closed months and January-February."""
    result = metrics(frame)
    monthly = [{"slice": month, **metrics(rows)} for month, rows in frame.groupby((frame.ts-pd.Timedelta(hours=1)).dt.strftime("%Y-%m"))]
    recent = frame[frame.ts.gt(pd.Timestamp("2025-01-01", tz="Asia/Seoul"))]
    if len(recent):
        monthly.append({"slice": "2025_JanFeb", **metrics(recent)})
    directory.mkdir(parents=True, exist_ok=True)
    save_json(directory / "score.json", result)
    pd.DataFrame(monthly).to_csv(directory / "diagnostics.csv", index=False)
    frame.to_parquet(directory / "predictions.parquet", index=False)
    return result["W_pct"]
