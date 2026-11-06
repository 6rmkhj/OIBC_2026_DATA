# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "scikit-learn", "joblib", "threadpoolctl"]
# ///
# How to run: imported by extra_run.py; --prepare performs zero ExtraTrees fits.
"""One randomized-tree complement against the official-best weather-only baseline."""
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Final
ROOT: Final = Path(__file__).resolve().parents[2]
RENEW: Final = ROOT/'analysis_outputs/renew_20261105'
OUT: Final = RENEW/'extra_wave'
DATA: Final = ROOT/'analysis_outputs/score_push_gpu_20261104/data'
MLP: Final = RENEW/'mlp_wave'
REFERENCE_DIR: Final = RENEW/'calibration_wave/comparisons/temperature_then_snow'
FOLDS: Final = {'primary':('2023-06-01','2024-06-01'),'recent':('2024-06-01','2025-03-01')}
REFERENCE: Final = {'primary':11.959229078372204,'recent':11.000952828788678}
PARAMS: Final = {'n_estimators':600,'criterion':'squared_error','max_depth':None,'min_samples_split':2,'min_samples_leaf':5,'min_weight_fraction_leaf':0.,'max_features':1.,'max_leaf_nodes':None,'min_impurity_decrease':0.,'bootstrap':False,'oob_score':False,'warm_start':False,'ccp_alpha':0.,'max_samples':None,'monotonic_cst':None,'n_jobs':16,'verbose':0}
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
    assert not (OUT/'protocol.json').exists(),'Preserve frozen protocol'
    (OUT/'sources/own').mkdir(parents=True,exist_ok=True)
    (OUT/'evidence').mkdir(exist_ok=True)
    snapshots = {}
    helpers = [p for folder in ('autoresearch','score_push','score_push_gpu') for p in (ROOT/'submission'/folder).glob('*.py')]
    helpers += [Path(__file__).with_name(n) for n in ('cal_math.py','temporal_common.py')]
    for path in helpers:
        shutil.copyfile(path,OUT/'sources'/path.name)
        snapshots[path.stem] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    own = {}
    for path in Path(__file__).parent.glob('extra_*.py'):
        shutil.copyfile(path,OUT/'sources/own'/path.name)
        own[path.name] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    coefficient = RENEW/'final/selected_coefficients.json'
    shutil.copyfile(coefficient,OUT/'original_weather_coefficients.json')
    inputs = [DATA/fold/name for fold in FOLDS for name in ('train.parquet','evaluation.parquet','features.json')]
    inputs += [MLP/'data'/fold/name for fold in FOLDS for name in ('training_transform.parquet','evaluation_transform.parquet','coverage.parquet','application_inputs.parquet')]
    inputs += [REFERENCE_DIR/fold/'predictions.parquet' for fold in FOLDS]
    inputs += [coefficient,RENEW/'final/static_capacity.json']
    protected = set(inputs)
    protected.update(ROOT/r['original'] for r in snapshots.values())
    protected.update(p for p in (ROOT/'submission').rglob('*.py') if '__pycache__' not in p.parts and not p.name.startswith(('extra_','score_push_verify_extra')))
    folders = [ROOT/'submission'/name for name in ('autoresearch_candidate','score_push_candidate','renew_candidate_20261105','renew_hour_candidate_20261105','renew_sky_candidate_20261105')]
    folders += [p for p in RENEW.iterdir() if p.is_dir() and p!=OUT]
    for folder in folders:
        protected.update(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'tmp' not in p.parts and p.name!='controller.lock' and not p.name.startswith('independent_'))
    save(OUT/'protocol.json',{'created_utc':now(),'arm':'extratrees_normalized_rich_decay180','candidate_count':1,'folds':FOLDS,'seeds':[0,1,2],'estimator':'sklearn1.9.1 ExtraTreesRegressor','fit_parameters':PARAMS,'inference_only_parameter_change':{'n_jobs':1},'features':'Exact raw rich100; no station804, imputation, scaling or feature pruning. Preserve native NaNs. Estimator internal float32 conversion is sklearn native behavior.','target':'Use exact MLP training_transform.target_normalized = float64cf/Haurwitz(float64cosz), not target_scaled or y_train.npy. Independently reconstruct before copying.','weight':'base=n^2; age=(cutoff-ts)/86400; decay=exp2(-age/180); weight=base*decay*sum(base)/sum(base*decay), preserve sum(base), exact MLP scalar source.','inverse':'Exact MLP evaluation_transform.inverse_kwh = normalizer * daylightcapacity; no target StandardScaler.','inference':'After fit change ONLY n_jobs16->1 before save/predict; deterministic serial tree accumulation; exact complete savedmodel replay. Mean3signed seedkWh before0/staticcapclip; night0; originalWEATHER temperature_then_snow only. NO hour/cloud stages.','selection':'One PRIMARY-only alpha against weather-only reference; transfer recent; bothstrictW improvement ANDalpha>=.02. No grid/earlystop/extraarms.','reference_scores':REFERENCE,'reference_scope':'Actual official-best WEATHER-only model; earlier sky/hour waves stay immutable.','prefit_barrier':'--prepare only; zero real ExtraTrees fits until root release pins protocol/prepared hashes.','resources':{'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_jobs':1,'fit_internal_tree_jobs':16,'inference_tree_jobs':1,'model_fit_budget_after_release':6},'no_confirmation_test_fullrefit_export':True,'historical_exposure':'All history exposed; no independentholdout claim','hypothesis':'Independent randomized trees may complement boosting/neural mixture; no performance claim before measurement.','original_weather_sha256':digest(coefficient),'snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)}})

def install_frozen() -> None:
    protocol = json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
    sys.meta_path.insert(0,gpu_common.FrozenImports())
    for name,r in protocol['own_sources'].items():
        assert digest(ROOT/r['original'])==digest(OUT/'sources/own'/name)==r['sha256']
    for r in protocol['snapshots'].values():
        assert digest(ROOT/r['original'])==r['sha256']
    for path,sha in protocol['input_sha256'].items():
        assert digest(ROOT/path)==sha,path
    assert digest(OUT/'original_weather_coefficients.json')==protocol['original_weather_sha256']

def check_prepared() -> None:
    for path,sha in json.loads((OUT/'prepared_manifest.json').read_text(encoding='utf-8')).items():
        assert digest(OUT/path)==sha,path

def require_release() -> None:
    release = json.loads((OUT/'release.json').read_text(encoding='utf-8'))
    assert release['approved'] and release['protocol_sha256']==digest(OUT/'protocol.json') and release['prepared_manifest_sha256']==digest(OUT/'prepared_manifest.json')
    assert release['model_fit_budget']==6
    check_prepared()
