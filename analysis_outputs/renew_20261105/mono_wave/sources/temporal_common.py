# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: imported by temporal_run.py and temporal_fit.py.
"""Temporal wave constants and reuse of existing resource/snapshot contracts."""
from pathlib import Path
import sys
from typing import Final
ROOT: Final = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'submission/score_push_gpu'))
import gpu_common
OUT: Final = ROOT/'analysis_outputs/renew_20261105/recency_wave'
DATA: Final = ROOT/'analysis_outputs/score_push_gpu_20261104/data'
gpu_common.OUT = OUT
from gpu_common import digest, save, now, configure, resource, child_identity
FOLDS: Final = ('primary', 'recent')
VARIANTS: Final = {'decay180':180, 'decay365':365, 'decay730':730, 'window365':None}
REFERENCE: Final = {'primary':12.041603595410752, 'recent':11.064366712650248}
PARAMS: Final = {'n_estimators':400, 'learning_rate':.03, 'num_leaves':63, 'min_child_samples':50, 'objective':'regression_l1', 'subsample':.8, 'subsample_freq':1, 'colsample_bytree':.8, 'n_jobs':16, 'verbose':-1}

def decay_multiplier(age, half_life: int | None):
    import numpy as np
    assert np.isfinite(age).all() and (age >= 0).all()
    multiplier = np.ones(len(age)) if half_life is None else np.exp2(-age/half_life)
    return multiplier/multiplier.mean()

def signed_mean(predictions):
    import numpy as np
    assert np.isfinite(predictions).all()
    return np.maximum(np.mean(predictions, axis=0), 0.)


def install_frozen() -> None:
    import json
    sys.meta_path.insert(0, gpu_common.FrozenImports())
    protocol = json.loads((OUT/'protocol.json').read_text())
    records = protocol['own_sources'].copy()
    amendment = OUT/'source_amendment.json'
    if amendment.exists():
        change = json.loads(amendment.read_text())
        assert digest(OUT/'protocol.json') == change['original_protocol_sha256']
        records.update(change['own_sources'])
    for name, record in records.items():
        assert digest(ROOT/record['original']) == record['sha256']
        snapshot = record.get('snapshot', 'sources/own/'+name)
        assert digest(OUT/snapshot) == record['sha256']


def ensure_terminal(identity) -> None:
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000,False,identity['pid'])
    if handle:
        code = wintypes.DWORD()
        assert kernel.GetExitCodeProcess(handle,ctypes.byref(code))
        kernel.CloseHandle(handle)
        assert code.value != 259 or child_identity(identity['pid'])['creation_filetime'] != identity['creation_filetime']
    else:
        assert ctypes.get_last_error() == 87
