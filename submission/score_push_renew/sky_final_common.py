# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: imported by sky_final_run.py.
"""No-fit cloud export paths, resources and immutable helper imports."""
import json
import os
import sys
from pathlib import Path
from typing import Final
ROOT: Final = Path(__file__).resolve().parents[2]
OUT: Final = ROOT/'analysis_outputs/renew_20261105/sky_final'
PRIOR: Final = ROOT/'analysis_outputs/renew_20261105/hour_final'
WEATHER: Final = ROOT/'analysis_outputs/renew_20261105/final'
WAVE: Final = ROOT/'analysis_outputs/renew_20261105/sky_wave'
CANDIDATE: Final = ROOT/'submission/renew_sky_candidate_20261105'
COMPOSITION: Final = '68216d1f6b8b6f9c026703e3bfaf7b0470cc8e018580826c866ee0f7357cc141'
COEFFICIENT: Final = 'b4ddc35d6c4c1f712c5dfd6f52e64e3fce2c07437247756d2dc8a56645751cee'
SPLITS: Final = ('old_cutoff_march_may','latest_cutoff_march_may','test')
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
    for name,record in protocol['own_sources'].items():
        assert digest(ROOT/record['original'])==record['sha256']
        assert digest(OUT/'sources/own'/name)==record['sha256']
    for record in protocol['snapshots'].values():
        assert digest(ROOT/record['original'])==record['sha256']
    for path,sha in protocol['input_sha256'].items():
        assert digest(ROOT/path)==sha,path
    assert digest(OUT/'selected_cloud_coefficients.json')==COEFFICIENT
