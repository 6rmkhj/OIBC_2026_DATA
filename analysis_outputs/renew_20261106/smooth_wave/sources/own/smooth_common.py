# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: imported by smooth_run.py; one fixed transform and alpha only.
"""Frozen smoothing protocol and established resource/import contracts."""
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Final
ROOT: Final = Path(__file__).resolve().parents[2]
RENEW: Final = ROOT/'analysis_outputs/renew_20261105'
OUT: Final = ROOT/'analysis_outputs/renew_20261106/smooth_wave'
DATA: Final = ROOT/'analysis_outputs/score_push_gpu_20261104/data'
REFERENCE_DIR: Final = RENEW/'calibration_wave/comparisons/temperature_then_snow'
COVERAGE: Final = RENEW/'extra_wave/data'
FOLDS: Final = {'primary':('2023-06-01','2024-06-01'),'recent':('2024-06-01','2025-03-01')}
REFERENCE: Final = {'primary':11.959229078372204,'recent':11.000952828788678}
SUPPORT: Final = {'primary':6252,'recent':4480}
APPLICATION: Final = ['ts','grp','p_reference','cosz','capacity_kw','static_capacity','night']
sys.path.insert(0,str(ROOT/'submission/score_push_gpu'))
import gpu_common
from gpu_common import digest,save,now,configure,resource
gpu_common.OUT = OUT

def environment() -> None:
    tmp = OUT/'tmp'
    tmp.mkdir(parents=True,exist_ok=True)
    for key in ('TMPDIR','TMP','TEMP'):
        os.environ[key] = str(tmp)
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[key] = '16'
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',NODE_COMPILE_CACHE=str(tmp/'node'),BUN_RUNTIME_TRANSPILER_CACHE_PATH=str(tmp/'bun'))

def freeze() -> None:
    assert not (OUT/'protocol.json').exists(),'Preserve frozen protocol'
    (OUT/'sources/own').mkdir(parents=True,exist_ok=True)
    (OUT/'evidence').mkdir(exist_ok=True)
    snapshots = {}
    for folder in ('autoresearch','score_push','score_push_gpu'):
        for path in (ROOT/'submission'/folder).glob('*.py'):
            shutil.copyfile(path,OUT/'sources'/path.name)
            snapshots[path.stem] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    own = {}
    for path in Path(__file__).parent.glob('smooth_*.py'):
        shutil.copyfile(path,OUT/'sources/own'/path.name)
        own[path.name] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    inputs = [p for fold in FOLDS for p in (DATA/fold/'evaluation.parquet',REFERENCE_DIR/fold/'predictions.parquet',COVERAGE/fold/'coverage.parquet')]
    protected = set(inputs)
    protected.update(p for p in (ROOT/'submission').rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.startswith(('smooth_','score_push_verify_smooth')))
    folders = [p for base in (RENEW,OUT.parent) for p in base.iterdir() if p.is_dir() and p!=OUT]
    for folder in folders:
        protected.update(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'tmp' not in p.parts and p.name!='controller.lock' and not p.name.startswith('independent_'))
    save(OUT/'protocol.json',{'created_utc':now(),'arm':'normalized_temporal_smoothing','candidate_count':1,'folds':FOLDS,'kernel':[.25,.5,.25],'cosz_minimum':.15,'application_columns':APPLICATION,'support_rule':'Exact t-1h,t,t+1h within group and same KST calendar date; all3daylight finitecosz>=.15 and positivecapacity. Unsupported originalp bits retained.','normalizer':'Established site_features.normalizer(cosz), preserving source dtype semantics; inverse=n*day_capacity,0night.','transform':'q=p_reference/inverse (0night); supported q_smoothed=.25*q_prev+.5*q+.25*q_next; p_new=clip(q_smoothed*inverse,0,static_capacity). Unsupported q_smoothed=q_before and p_new originalbits.','reference':'Exact already-weather-corrected official-best temperature_then_snow; NO further weather/hour/cloud correction.','expected_support':SUPPORT,'reference_scores':REFERENCE,'selection':'One PRIMARY weighted-L1 alpha; unchanged recent transfer; bothstrictW improvement ANDalpha>=.02. Primary blend selection partly in-sample; no grid/retuning.','execution_authorization':'Direct single-alpha execution after freeze/preparation/selfchecks; no separate prefit release required.','resources':{'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_jobs':1},'real_model_fit_budget':0,'real_calibration_fit_budget':0,'real_alpha_fit_budget':1,'no_confirmation_test_fullrefit_export':True,'historical_exposure':'All history exposed; no independentholdout claim','snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)}})

def install_frozen() -> None:
    protocol = json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
    sys.meta_path.insert(0,gpu_common.FrozenImports())
    for name,record in protocol['own_sources'].items():
        assert digest(ROOT/record['original'])==digest(OUT/'sources/own'/name)==record['sha256']
    for record in protocol['snapshots'].values():
        assert digest(ROOT/record['original'])==record['sha256']
    for path,sha in protocol['input_sha256'].items():
        assert digest(ROOT/path)==sha,path
