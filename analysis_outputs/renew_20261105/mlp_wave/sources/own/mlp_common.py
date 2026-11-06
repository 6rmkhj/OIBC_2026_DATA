# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "scikit-learn", "joblib", "threadpoolctl"]
# ///
# How to run: imported by mlp_run.py.
"""One normalized/time-weighted station MLP preregistration and resources."""
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Final
ROOT: Final = Path(__file__).resolve().parents[2]
RENEW: Final = ROOT/'analysis_outputs/renew_20261105'
OUT: Final = RENEW/'mlp_wave'
DATA: Final = ROOT/'analysis_outputs/score_push_gpu_20261104/data'
REFERENCE_DIR: Final = RENEW/'sky_wave/comparisons/cloud_bias'
FOLDS: Final = {'primary':('2023-06-01','2024-06-01'),'recent':('2024-06-01','2025-03-01')}
REFERENCE: Final = {'primary':11.792837177705382,'recent':10.955416218320197}
PARAMS: Final = {'hidden_layer_sizes':(64,32),'activation':'relu','solver':'adam','alpha':.1,'batch_size':128,'learning_rate_init':.001,'max_iter':400,'tol':1e-5,'n_iter_no_change':20,'early_stopping':False}
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
    if (OUT/'protocol.json').exists():
        return
    (OUT/'sources/own').mkdir(parents=True)
    (OUT/'evidence').mkdir(exist_ok=True)
    snapshots = {}
    helpers = [p for folder in ('autoresearch','score_push','score_push_gpu') for p in (ROOT/'submission'/folder).glob('*.py')]
    helpers += [Path(__file__).with_name(n) for n in ('cal_math.py','hour_math.py','sky_math.py','temporal_common.py')]
    for p in helpers:
        shutil.copyfile(p,OUT/'sources'/p.name)
        snapshots[p.stem] = {'original':str(p.relative_to(ROOT)),'sha256':digest(p)}
    own = {}
    for p in Path(__file__).parent.glob('mlp_*.py'):
        shutil.copyfile(p,OUT/'sources/own'/p.name)
        own[p.name] = {'original':str(p.relative_to(ROOT)),'sha256':digest(p)}
    coefficients = {'weather':RENEW/'final/selected_coefficients.json','hour':RENEW/'hour_wave/coefficients.json','cloud':RENEW/'sky_wave/coefficients.json'}
    for name,p in coefficients.items():
        shutil.copyfile(p,OUT/f'original_{name}_coefficients.json')
    inputs = [DATA/fold/name for fold in FOLDS for name in ('train.parquet','evaluation.parquet','features.json')]
    inputs += [REFERENCE_DIR/fold/'predictions.parquet' for fold in FOLDS]
    inputs += [RENEW/'recency_wave/data'/fold/'night_coverage.parquet' for fold in FOLDS]
    inputs += [RENEW/'final/static_capacity.json',RENEW/'best_development.json',*coefficients.values()]
    protected = set(inputs)
    protected.update(ROOT/r['original'] for r in snapshots.values())
    protected.update(p for p in (ROOT/'submission').rglob('*.py') if '__pycache__' not in p.parts and not p.name.startswith(('mlp_','score_push_verify_mlp')))
    folders = [ROOT/'submission'/n for n in ('autoresearch_candidate','score_push_candidate','renew_candidate_20261105','renew_hour_candidate_20261105','renew_sky_candidate_20261105')]
    folders += [p for p in RENEW.iterdir() if p.is_dir() and p!=OUT]
    for folder in folders:
        protected.update(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'tmp' not in p.parts and p.name!='controller.lock' and not p.name.startswith('independent_'))
    save(OUT/'protocol.json',{'created_utc':now(),'arm':'station_mlp_normalized_decay180','candidate_count':1,'folds':FOLDS,'seeds':[0,1,2],'parameters':PARAMS,'hypothesis':'Previous stationMLP rawCF/unweighted; previous normalized MLP used richsummary not904station candidates. One fixed normalized/time-weighted station variant.','features':'904cached station candidates; profile_features.column_mask TRAINonly; cast selectedfeatureDataFrames float64 BEFORE learner_models.preprocessing medianimputer+StandardScaler fittedTRAINonly. Shared per-fold matrices/scalers across3seeds.','target':'float64 train.cf / site_features.normalizer(float64cosz), then TRAINonly StandardScaler.','weight':'base=normalizer^2; age_days=(fixedcutoff-ts)/86400; decay=exp2(-age_days/180); sample_weight=base*decay*sum(base)/sum(base*decay),float64finitepositive,preservebaseweighttotal. No pricefeature/weight.','inference':'targetscaler.inverse_transform ONCE *evalnormalizer*daycapacity; saveSIGNEDrawkWh; mean3signed seeds BEFORE0..staticcapclip; allnight0; then originalweather->hour->cloud sequential halfshrink/cap eachstage, NOrefit.','selection':'ONEPRIMARYonly optimal alpha vs currentskyreference; transferrecent; BOTHstrictWimprovement ANDalpha>=.02. No grid.','reference_scores':REFERENCE,'prefit_barrier':'Prepare matrices/scalers/targets/weights and syntheticproofsonly; zero real MLP fits until rootrelease protocol/prepared hashes.','resources':{'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_jobs':1,'model_fit_budget_after_release':6},'no_confirmation_test_fullrefit_export':True,'historical_exposure':'Allperiodshistoricallyexposed;noindependentholdoutclaim','original_coefficients_sha256':{k:digest(p) for k,p in coefficients.items()},'snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)}})

def install_frozen() -> None:
    protocol = json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
    sys.meta_path.insert(0,gpu_common.FrozenImports())
    for name,r in protocol['own_sources'].items():
        assert digest(ROOT/r['original'])==r['sha256']
        assert digest(OUT/'sources/own'/name)==r['sha256']
    for r in protocol['snapshots'].values():
        assert digest(ROOT/r['original'])==r['sha256']
    for path,sha in protocol['input_sha256'].items():
        assert digest(ROOT/path)==sha,path
    for name,sha in protocol['original_coefficients_sha256'].items():
        assert digest(OUT/f'original_{name}_coefficients.json')==sha

def require_release() -> None:
    release = json.loads((OUT/'release.json').read_text(encoding='utf-8'))
    assert release['approved'] and release['protocol_sha256']==digest(OUT/'protocol.json') and release['prepared_manifest_sha256']==digest(OUT/'prepared_manifest.json')
    for path,sha in json.loads((OUT/'prepared_manifest.json').read_text(encoding='utf-8')).items():
        assert digest(OUT/path)==sha,path
