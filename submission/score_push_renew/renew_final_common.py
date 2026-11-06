# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: imported by renew_final_run.py.
"""Immutable final recipe and bounded resource contracts."""
import json
import os
from pathlib import Path
import sys
from typing import Final
ROOT: Final = Path(__file__).resolve().parents[2]
OUT: Final = ROOT/'analysis_outputs/renew_20261105/final'
OLD: Final = ROOT/'analysis_outputs/autoresearch_20261103/final'
CPU: Final = ROOT/'analysis_outputs/score_push_20261104'
RENEW: Final = OUT.parent
CANDIDATE: Final = ROOT/'submission/renew_candidate_20261105'
ALPHA: Final = .07794876465304705
COMPOSITION: Final = '68216d1f6b8b6f9c026703e3bfaf7b0470cc8e018580826c866ee0f7357cc141'
CUTOFFS: Final = {'latest':'2025-03-01','test':'2025-06-01'}
sys.path.insert(0,str(ROOT/'submission/score_push_gpu'))
import gpu_common
from gpu_common import digest,save,now,configure,resource,child_identity
from temporal_common import PARAMS,ensure_terminal,decay_multiplier
gpu_common.OUT = OUT


def environment() -> None:
    tmp = OUT/'tmp'
    tmp.mkdir(parents=True,exist_ok=True)
    for key in ('TMPDIR','TMP','TEMP'):
        os.environ[key] = str(tmp)
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[key] = '16'
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',NODE_COMPILE_CACHE=str(tmp/'node'),BUN_RUNTIME_TRANSPILER_CACHE_PATH=str(tmp/'bun'))


def install_frozen() -> None:
    sys.meta_path.insert(0,gpu_common.FrozenImports())
    protocol = json.loads((OUT/'protocol.json').read_text())
    records = protocol['own_sources'].copy()
    amendment_path = OUT/'source_amendment.json'
    if amendment_path.exists():
        amendment = json.loads(amendment_path.read_text())
        assert amendment['original_protocol_sha256']==digest(OUT/'protocol.json')
        records.update(amendment['own_sources'])
        if (OUT/'release.json').exists():
            assert json.loads((OUT/'release.json').read_text())['source_amendment_sha256']==digest(amendment_path)
    for name,record in records.items():
        assert digest(ROOT/record['original'])==record['sha256']
        assert digest(OUT/record.get('snapshot','sources/own/'+name))==record['sha256']
    for name,sha in protocol['input_sha256'].items():
        assert digest(ROOT/name)==sha,name


def coefficients():
    from cal_math import Calibration,Factor
    stored = json.loads((OUT/'selected_coefficients.json').read_text())['factors']
    return Calibration(tuple(Factor(**r) for r in stored['temperature']),Factor(**stored['snow']),Factor(**stored['conditional_snow']))
