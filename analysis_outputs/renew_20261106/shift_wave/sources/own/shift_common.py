# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: imported by shift_run.py; --prepare performs zero covariate-shift fits.
"""One fixed covariate-shift complement against the official-best weather-only baseline."""
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Final
ROOT: Final = Path(__file__).resolve().parents[2]
RENEW: Final = ROOT/'analysis_outputs/renew_20261105'
OUT: Final = ROOT/'analysis_outputs/renew_20261106/shift_wave'
DATA: Final = ROOT/'analysis_outputs/score_push_gpu_20261104/data'
SOURCE: Final = ROOT/'analysis_outputs/renew_20261106/poisson_wave'

REFERENCE_DIR: Final = RENEW/'calibration_wave/comparisons/temperature_then_snow'
FOLDS: Final = {'primary':('2023-06-01','2024-06-01'),'recent':('2024-06-01','2025-03-01')}
REFERENCE: Final = {'primary':11.959229078372204,'recent':11.000952828788678}
PARAMS: Final = {'n_estimators':400,'learning_rate':.03,'num_leaves':63,'min_child_samples':50,'objective':'regression_l1','subsample':.8,'subsample_freq':1,'colsample_bytree':.8,'n_jobs':16,'verbose':-1}
DOMAIN_PARAMS: Final = {'C':.01,'solver':'lbfgs','max_iter':1000,'tol':1e-6,'class_weight':'balanced','random_state':0}
DOMAIN_COLUMNS: Final = ['wa_cloud','wa_temp','wa_humidity','wa_ground_press','wa_wind_speed','wa_rain','wb_cloud','wb_uv_idx','wb_temp','wb_rel_hum','wb_dew_point','wb_vis','wb_ceiling','wb_precip_prob','wb_total_liq','cosz','doy_sin','doy_cos','hour','grp_code']
GENERATION_FILES: Final = ('train.parquet','evaluation.parquet','feature_mask.json','training_transform.parquet','evaluation_transform.parquet','application_inputs.parquet','coverage.parquet','labels.parquet')
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
    for path in Path(__file__).parent.glob('shift_*.py'):
        shutil.copyfile(path,OUT/'sources/own'/path.name)
        own[path.name] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    coefficient = RENEW/'final/selected_coefficients.json'
    shutil.copyfile(coefficient,OUT/'original_weather_coefficients.json')
    inputs = [SOURCE/'data'/fold/name for fold in FOLDS for name in GENERATION_FILES]
    inputs += [SOURCE/'prepared_manifest.json',SOURCE/'protocol.json',SOURCE/'evidence/environment.json',SOURCE/'terminal_manifest.json',SOURCE/'independent_check.json']




    inputs += [REFERENCE_DIR/fold/'predictions.parquet' for fold in FOLDS]
    inputs += [coefficient,RENEW/'final/static_capacity.json']
    protected = set(inputs)
    protected.update(ROOT/r['original'] for r in snapshots.values())
    protected.update(p for p in (ROOT/'submission').rglob('*.py') if '__pycache__' not in p.parts and not p.name.startswith(('shift_','score_push_verify_shift')))
    folders = [ROOT/'submission'/name for name in ('autoresearch_candidate','score_push_candidate','renew_candidate_20261105','renew_hour_candidate_20261105','renew_sky_candidate_20261105')]
    folders += [p for base in (RENEW,OUT.parent) for p in base.iterdir() if p.is_dir() and p!=OUT]
    for folder in folders:
        protected.update(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'tmp' not in p.parts and p.name!='controller.lock' and not p.name.startswith('independent_'))
    save(OUT/'protocol.json',{'created_utc':now(),'arm':'covariate_shift_station_decay180','candidate_count':1,'folds':FOLDS,'seeds':[0,1,2],'seed_rule':'0->None,1->1,2->2','parameters':PARAMS,'domain_parameters':DOMAIN_PARAMS,'domain_columns':DOMAIN_COLUMNS,'generation_lineage':'Eight generation input files byte-identical verified Poisson preparation;904candidates/TRAIN-only460/790mask,cf/Haurwitz target,inverse once. Only weights change.','domain_preprocessing':'TRAIN-only nanmedian,then TRAIN-only imputed mean/populationstd(ddof0);std0->1;float64source/future standardized and clipped[-8,8].','domain_crossfit':'KST date.toordinal()%3,all groups/hours same day held together; splitk classifier sees source!=k domain0 plus ALL provided unlabeled future domain1; held-source decision_function only.','domain_interpretation':'Transductive provided future forecast covariates; no future energy/labels/smp/k in domain inputs. Balanced priors yield exp(logit) density ratio.','weight':'base EXACT normalizer*mean1decay180;modifier=sqrt(clip(exp(OOFlogit),.25,4));combined=base*modifier*sum(base)/sum(base*modifier).','inference':'Mean3signed generationkWh then0/staticcapclip,originaltemperature_then_snow ONCE; nohour/cloud.','selection':'OnePRIMARY-onlyweightedL1alpha,unchangedrecent;bothstrictWimproveANDalpha>=.02;no grid/retries/convergence retuning.','reference_scores':REFERENCE,'reference_scope':'Officialbest6454220836weatheronly;allhistoryexposed.','prefit_barrier':'Zero actualdomain/generation fits until root hash-pinned release.','resources':{'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_jobs':1},'model_fit_budget_after_release':12,'domain_fit_budget_after_release':6,'generation_fit_budget_after_release':6,'alpha_fit_budget_after_release':1,'no_confirmation_test_fullrefit_export':True,'historical_exposure':'Allhistoryexposed;PRIMARYselectionpartlyin-sample;transductiveprovidedweather.','original_weather_sha256':digest(coefficient),'domain_reference_sha256':digest(OUT/'evidence/domain_reference.txt'),'snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)}})

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
    assert release['model_fit_budget']==12 and release['domain_fit_budget']==6 and release['generation_fit_budget']==6 and release['alpha_fit_budget']==1
    check_prepared()
