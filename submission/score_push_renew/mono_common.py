# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: imported by mono_run.py; --prepare does not fit.
"""Frozen matched fair-loss station protocol and native resource contracts."""
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Final
ROOT: Final = Path(__file__).resolve().parents[2]
RENEW: Final = ROOT/'analysis_outputs/renew_20261105'
OUT: Final = RENEW/'mono_wave'
DATA: Final = ROOT/'analysis_outputs/score_push_gpu_20261104/data'
MLP: Final = RENEW/'mlp_wave'
FOLDS: Final = {'primary':('2023-06-01','2024-06-01'),'recent':('2024-06-01','2025-03-01')}
ARMS: Final = ('fair_control','fair_monotone')
REFERENCE: Final = {'primary':11.792837177705382,'recent':10.955416218320197}
PARAMS: Final = {'n_estimators':400,'learning_rate':.03,'num_leaves':63,'min_child_samples':50,'objective':'fair','fair_c':.1,'linear_tree':False,'monotone_constraints_method':'basic','subsample':.8,'subsample_freq':1,'colsample_bytree':.8,'n_jobs':16,'device_type':'cpu','verbose':-1}
sys.path.insert(0,str(ROOT/'submission/score_push_gpu'))
import gpu_common
from gpu_common import digest,save,now,configure,resource,child_identity
from temporal_common import ensure_terminal

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
    assert not (OUT/'protocol.json').exists(),'Preserve frozen protocol; preparation is one-shot'
    (OUT/'sources/own').mkdir(parents=True,exist_ok=True)
    (OUT/'evidence').mkdir(exist_ok=True)
    snapshots = {}
    helpers = [p for folder in ('autoresearch','score_push','score_push_gpu') for p in (ROOT/'submission'/folder).glob('*.py')]
    helpers += [Path(__file__).with_name(n) for n in ('cal_math.py','hour_math.py','sky_math.py','temporal_common.py')]
    for path in helpers:
        shutil.copyfile(path,OUT/'sources'/path.name)
        snapshots[path.stem] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    own = {}
    for path in Path(__file__).parent.glob('mono_*.py'):
        shutil.copyfile(path,OUT/'sources/own'/path.name)
        own[path.name] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    coefficients = [MLP/f'original_{name}_coefficients.json' for name in ('weather','hour','cloud')]
    for path in coefficients:
        shutil.copyfile(path,OUT/path.name)
    inputs = [DATA/fold/name for fold in FOLDS for name in ('train.parquet','evaluation.parquet','features.json')]
    inputs += [MLP/'data'/fold/name for fold in FOLDS for name in ('labels.parquet','coverage.parquet','application_inputs.parquet')]
    inputs += [*coefficients,RENEW/'final/static_capacity.json',RENEW/'best_development.json',RENEW/'monotone_compatibility.json']
    protected = set(inputs)
    protected.update(ROOT/r['original'] for r in snapshots.values())
    protected.update(p for p in (ROOT/'submission').rglob('*.py') if '__pycache__' not in p.parts and not p.name.startswith(('mono_','score_push_verify_mono')))
    folders = [ROOT/'submission'/name for name in ('autoresearch_candidate','score_push_candidate','renew_candidate_20261105','renew_hour_candidate_20261105','renew_sky_candidate_20261105')]
    folders += [p for p in RENEW.iterdir() if p.is_dir() and p!=OUT]
    for folder in folders:
        protected.update(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'tmp' not in p.parts and p.name!='controller.lock' and not p.name.startswith('independent_'))
    save(OUT/'protocol.json',{'created_utc':now(),'arms':ARMS,'candidate_count':2,'folds':FOLDS,'seeds':[0,1,2],'parameters':PARAMS,'seed_rule':'0 -> random_state=None, 1 -> 1, 2 -> 2','features':'904 immutable native station candidates; selected TRAIN-only nunique(dropna=True)>1; no imputation/scaling/bounds/feature changes; preserve NaNs and source dtypes.','constraints':'fair_control all0; fair_monotone -1 on wa_cloud/wb_cloud and exact wa_station_WA[0-9]{3}_wa_cloud / wb_station_WB[0-9]{3}_wb_cloud; +1 on toaa/toab and exact corresponding station_toaa/toab; everything else0, especially csa/csb and temporal derivatives.','expected_masks':{'primary':{'features':460,'negative':62,'positive':62},'recent':{'features':790,'negative':117,'positive':117}},'target':'cf / Haurwitz normalizer(cosz), exact temporal source dtype semantics, no target scaler','weight':'normalizer * mean-one decay180; age=(fixedcutoff-ts)/86400; raw_decay=exp2(-age/180); multiplier=raw_decay/raw_decay.mean(); no price weights.','inference':'SIGNED raw model prediction * normalizer * daylight capacity; mean3signed seeds BEFORE0/staticcapclip; night0; unchanged originalweather->hour->cloud stages; no calibration fits.','selection':'Separate PRIMARY-only alpha per arm vs current sky; transfer recent; both strictW improvement AND alpha>=.02; choose eligible minimum mean blendedW/referenceW over both folds; report matched pure and mixed fair comparisons.','reference_scores':REFERENCE,'interpretation':'Partial coordinate regularization only; unconstrained revisions/ramps/leads/std/csa/csb preclude global physical guarantee. Fair changes historical L1 loss; matched fair control required.','prefit_barrier':'--prepare only until root release pins protocol/prepared SHA256; zero real model fits now','resources':{'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_jobs':1,'model_fit_budget_after_release':12},'no_confirmation_test_fullrefit_export':True,'historical_exposure':'All history exposed; no independent holdout claim','original_coefficients_sha256':{p.name:digest(p) for p in coefficients},'snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)}})

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
    for name,sha in protocol['original_coefficients_sha256'].items():
        assert digest(OUT/name)==sha

def check_prepared() -> None:
    for path,sha in json.loads((OUT/'prepared_manifest.json').read_text(encoding='utf-8')).items():
        assert digest(OUT/path)==sha,path

def require_release() -> None:
    release = json.loads((OUT/'release.json').read_text(encoding='utf-8'))
    assert release['approved'] and release['protocol_sha256']==digest(OUT/'protocol.json') and release['prepared_manifest_sha256']==digest(OUT/'prepared_manifest.json')
    assert release['model_fit_budget']==12
    check_prepared()
