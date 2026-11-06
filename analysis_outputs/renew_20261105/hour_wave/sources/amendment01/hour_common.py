# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: imported by hour_run.py.
"""Frozen hour-stage paths and existing CPU resource contracts."""
import json
import os
import sys
from pathlib import Path
from typing import Final
ROOT: Final = Path(__file__).resolve().parents[2]
OUT: Final = ROOT/'analysis_outputs/renew_20261105/hour_wave'
REFERENCE_DIR: Final = ROOT/'analysis_outputs/renew_20261105/calibration_wave/comparisons/temperature_then_snow'
FOLDS: Final = {'primary':('2023-06-01','2024-06-01'),'recent':('2024-06-01','2025-03-01')}
REFERENCE: Final = {'primary':11.959229078372204,'recent':11.000952828788678}
BINS: Final = ('[0,10)','[10,12)','[12,14)','[14,16)','[16,24)')
sys.path.insert(0,str(ROOT/'submission/score_push_gpu'))
import gpu_common
from gpu_common import digest,save,now,configure,resource
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
    protocol = json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
    sys.meta_path.insert(0,gpu_common.FrozenImports())
    records = protocol['own_sources'].copy()
    amendment_path = OUT/'source_amendment.json'
    if amendment_path.exists():
        amendment = json.loads(amendment_path.read_text(encoding='utf-8'))
        assert amendment['original_protocol_sha256']==digest(OUT/'protocol.json')
        records.update(amendment['own_sources'])
        if (OUT/'release.json').exists():
            assert json.loads((OUT/'release.json').read_text(encoding='utf-8'))['source_amendment_sha256']==digest(amendment_path)
    for name,record in records.items():
        assert digest(ROOT/record['original'])==record['sha256']
        assert digest(OUT/record.get('snapshot','sources/own/'+name))==record['sha256']
    for record in protocol['snapshots'].values():
        assert digest(ROOT/record['original'])==record['sha256']
    for name,sha in protocol['input_sha256'].items():
        assert digest(ROOT/name)==sha,name
