# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: imported by yield_run.py.
"""Site-yield frozen paths and established resource contracts."""
from pathlib import Path
from typing import Final
import json
import os
import sys
ROOT: Final = Path(__file__).resolve().parents[2]
OUT: Final = ROOT/'analysis_outputs/renew_20261105/yield_wave'
DATA: Final = ROOT/'analysis_outputs/score_push_gpu_20261104/data'
GROUP: Final = ROOT/'analysis_outputs/renew_20261105/group_wave'
SITE: Final = ROOT/'analysis_outputs/score_push_20261104/site_wave/cache'
REFERENCE_DIR: Final = ROOT/'analysis_outputs/renew_20261105/calibration_wave/comparisons/temperature_then_snow'
FOLDS: Final = {'primary':('2023-06-01','2024-06-01'),'recent':('2024-06-01','2025-03-01')}
ARMS: Final = ('site_yield',)
REFERENCE: Final = {'primary':11.959229078372204,'recent':11.000952828788678}
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
    assert digest(OUT/'selected_coefficients.json')==protocol['coefficient_sha256']
    assert digest(OUT/'static_capacity.json')==protocol['static_capacity_sha256']
    for name,record in protocol['own_sources'].items():
        assert digest(ROOT/record['original'])==record['sha256']
        assert digest(OUT/'sources/own'/name)==record['sha256']


def check_inputs() -> None:
    protocol = json.loads((OUT/'protocol.json').read_text())
    assert digest(OUT/'selected_coefficients.json')==protocol['coefficient_sha256']
    assert digest(OUT/'static_capacity.json')==protocol['static_capacity_sha256']
    for name,sha in protocol['input_sha256'].items():
        assert digest(ROOT/name)==sha,name


def coefficients():
    from cal_math import Calibration,Factor
    factors = json.loads((OUT/'selected_coefficients.json').read_text())['factors']
    return Calibration(tuple(Factor(**r) for r in factors['temperature']),Factor(**factors['snow']),Factor(**factors['conditional_snow']))
