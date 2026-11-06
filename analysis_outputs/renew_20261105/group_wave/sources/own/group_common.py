# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: imported by group_run.py.
"""Frozen complete-group experiment constants and resource contracts."""
from pathlib import Path
import json
import os
import sys
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[2]
OUT: Final = ROOT/'analysis_outputs/renew_20261105/group_wave'
SITE: Final = ROOT/'analysis_outputs/score_push_20261104/site_wave/cache'
REFERENCE_DIR: Final = ROOT/'analysis_outputs/renew_20261105/recency_wave/comparisons/decay180/ensemble'
FOLDS: Final = {'primary':('2023-06-01','2024-06-01',521423), 'recent':('2024-06-01','2025-03-01',1203117)}
ARMS: Final = {'group_l01':(.05,.1,True), 'group_l1':(.05,1.,True), 'site_control':(.05,.1,False)}
REFERENCE: Final = {'primary':12.033226215978063,'recent':11.059225184100658}
PARAMS: Final = {'learning_rate':.08,'num_leaves':127,'min_data_in_leaf':200,'feature_fraction':.8,'bagging_fraction':1.,'bagging_freq':0,'boosting_type':'gbdt','data_sample_strategy':'bagging','device_type':'cpu','num_threads':16,'max_bin':255,'lambda_l1':0.,'lambda_l2':0.,'min_sum_hessian_in_leaf':1e-3,'verbosity':-1,'metric':'None','deterministic':True,'force_col_wise':True}
sys.path.insert(0,str(ROOT/'submission/score_push_gpu'))
import gpu_common
from gpu_common import digest, save, now, configure, resource, child_identity
from temporal_common import ensure_terminal
gpu_common.OUT = OUT

def environment() -> None:
    """Give all descendants the same owned temp and bounded threading."""
    tmp = OUT/'tmp'
    tmp.mkdir(parents=True,exist_ok=True)
    for name in ('TMPDIR','TMP','TEMP'):
        os.environ[name] = str(tmp)
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[name] = '16'
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',NODE_COMPILE_CACHE=str(tmp/'node'),BUN_RUNTIME_TRANSPILER_CACHE_PATH=str(tmp/'bun'))

def install_frozen() -> None:
    sys.meta_path.insert(0,gpu_common.FrozenImports())
    protocol = json.loads((OUT/'protocol.json').read_text())
    for name,record in protocol['own_sources'].items():
        assert digest(ROOT/record['original']) == record['sha256']
        assert digest(OUT/'sources/own'/name) == record['sha256']

def check_inputs() -> None:
    protocol = json.loads((OUT/'protocol.json').read_text())
    for name,sha in protocol['input_sha256'].items():
        assert digest(ROOT/name) == sha, name
