# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: imported by total_run.py.
"""Total-portfolio frozen paths and established resource contracts."""
from pathlib import Path
from typing import Final
import json
import os
import sys
ROOT: Final = Path(__file__).resolve().parents[2]
OUT: Final = ROOT/'analysis_outputs/renew_20261105/total_wave'
DATA: Final = ROOT/'analysis_outputs/score_push_gpu_20261104/data'
GROUP: Final = ROOT/'analysis_outputs/renew_20261105/group_wave'
REFERENCE_DIR: Final = ROOT/'analysis_outputs/renew_20261105/recency_wave/comparisons/decay180/ensemble'
FOLDS: Final = {'primary':('2023-06-01','2024-06-01'),'recent':('2024-06-01','2025-03-01')}
ARMS: Final = {'total_rich':'rich','total_station':'station'}
REFERENCE: Final = {'primary':12.033226215978063,'recent':11.059225184100658}
sys.path.insert(0,str(ROOT/'submission/score_push_gpu'))
import gpu_common
from gpu_common import digest,save,now,configure,resource,child_identity
from temporal_common import PARAMS,ensure_terminal,decay_multiplier
gpu_common.OUT = OUT


def environment() -> None:
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
        assert digest(ROOT/record['original'])==record['sha256']
        assert digest(OUT/'sources/own'/name)==record['sha256']


def check_inputs() -> None:
    protocol = json.loads((OUT/'protocol.json').read_text())
    for name,sha in protocol['input_sha256'].items():
        assert digest(ROOT/name)==sha,name
