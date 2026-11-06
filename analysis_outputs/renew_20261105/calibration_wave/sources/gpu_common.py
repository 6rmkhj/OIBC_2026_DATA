# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "catboost", "threadpoolctl"]
# ///
# How to run: imported by gpu_run.py and gpu_fit.py.
"""GPU experiment paths, immutable imports and native resource receipts."""
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT/'analysis_outputs/score_push_20261104'
OUT = ROOT/'analysis_outputs/score_push_gpu_20261104'
FOLDS = ('primary','recent')
REFERENCE = {'primary':12.041603595410752,'recent':11.064366712650248}
PARAMS = {'loss_function':'MAE','depth':6,'iterations':2000,'learning_rate':.03,'l2_leaf_reg':3,'task_type':'GPU','devices':'0','thread_count':16,'gpu_ram_part':.9,'allow_writing_files':True,'save_snapshot':True,'snapshot_interval':30,'border_count':128,'boosting_type':'Plain','nan_mode':'Min','verbose':200}


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def save(path: Path, value) -> None:
    path.write_text(json.dumps(value,indent=2,allow_nan=False),encoding='utf-8')


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FrozenImports(importlib.abc.MetaPathFinder,importlib.abc.Loader):
    """Execute hashed helper snapshots with their original path semantics."""
    def find_spec(self, fullname, path=None, target=None):
        if (OUT/'sources'/f'{fullname}.py').exists():
            return importlib.util.spec_from_loader(fullname,self)
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module) -> None:
        record = json.loads((OUT/'protocol.json').read_text())['snapshots'][module.__name__]
        source = OUT/'sources'/f'{module.__name__}.py'
        assert digest(source)==record['sha256']
        module.__file__ = str(ROOT/record['original'])
        exec(compile(source.read_bytes(),module.__file__,'exec'),module.__dict__)


def configure() -> None:
    kernel = ctypes.windll.kernel32
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.SetPriorityClass.argtypes = [wintypes.HANDLE,wintypes.DWORD]
    kernel.GetPriorityClass.argtypes = [wintypes.HANDLE]
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)]
    assert kernel.SetPriorityClass(kernel.GetCurrentProcess(),32)
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[name]='16'
    import pyarrow as pa
    pa.set_cpu_count(4)
    pa.set_io_thread_count(4)


def resource():
    from verify import MemoryCounters
    from threadpoolctl import threadpool_info
    import pyarrow as pa
    kernel = ctypes.windll.kernel32
    handle = kernel.GetCurrentProcess()
    counters = MemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE,ctypes.POINTER(MemoryCounters),wintypes.DWORD]
    assert ctypes.windll.psapi.GetProcessMemoryInfo(handle,ctypes.byref(counters),counters.cb)
    times = [wintypes.FILETIME() for _ in range(4)]
    assert kernel.GetProcessTimes(handle,*[ctypes.byref(t) for t in times])
    assert kernel.GetPriorityClass(handle)==32
    return {'pid':os.getpid(),'creation_filetime':(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime,'priority_class':32,'parallel_fits':1,'model_threads':16,'peak_working_set_bytes':counters.peak_working_set,'working_set_bytes':counters.working_set,'threadpools':threadpool_info(),'pyarrow_cpu':pa.cpu_count(),'pyarrow_io':pa.io_thread_count(),'utc':now()}


def install_frozen() -> None:
    sys.meta_path.insert(0,FrozenImports())
    protocol = json.loads((OUT/'protocol.json').read_text())
    for name,record in protocol['own_sources'].items():
        assert digest(ROOT/record['original'])==record['sha256']
        assert digest(OUT/'sources/own'/name)==record['sha256']


def child_identity(pid: int):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    kernel.GetProcessTimes.argtypes=[wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)]
    handle=kernel.OpenProcess(0x1000,False,pid)
    assert handle
    times=[wintypes.FILETIME() for _ in range(4)]
    assert kernel.GetProcessTimes(handle,*[ctypes.byref(t) for t in times])
    kernel.CloseHandle(handle)
    return {'pid':pid,'creation_filetime':(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime}
