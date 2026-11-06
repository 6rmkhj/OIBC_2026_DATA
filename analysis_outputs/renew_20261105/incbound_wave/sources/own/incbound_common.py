# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "scikit-learn", "joblib", "threadpoolctl"]
# ///
# How to run: imported by incbound_run.py; --prepare performs no model inference.
"""One incumbent rich-MLP TRAIN-range substitution and immutable inputs."""
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Final
ROOT: Final = Path(__file__).resolve().parents[2]
RENEW: Final = ROOT/'analysis_outputs/renew_20261105'
OLD: Final = ROOT/'analysis_outputs/score_push_20261104'
OUT: Final = RENEW/'incbound_wave'
DATA: Final = ROOT/'analysis_outputs/score_push_gpu_20261104/data'
MODELS: Final = OLD/'learner_wave'
FOLDS: Final = {'primary':('2023-06-01','2024-06-01'),'recent':('2024-06-01','2025-03-01')}
REFERENCE: Final = {'primary':11.792837177705382,'recent':10.955416218320197}
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
    assert not (OUT/'protocol.json').exists(),'Preserve frozen preparation'
    (OUT/'sources/own').mkdir(parents=True,exist_ok=True)
    (OUT/'evidence').mkdir(exist_ok=True)
    snapshots = {}
    helpers = [p for folder in ('autoresearch','score_push','score_push_gpu') for p in (ROOT/'submission'/folder).glob('*.py')]
    helpers += [Path(__file__).with_name(n) for n in ('cal_math.py','hour_math.py','sky_math.py','temporal_common.py')]
    for path in helpers:
        shutil.copyfile(path,OUT/'sources'/path.name)
        snapshots[path.stem] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    own = {}
    for path in Path(__file__).parent.glob('incbound_*.py'):
        shutil.copyfile(path,OUT/'sources/own'/path.name)
        own[path.name] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    coefficients = [RENEW/'mlp_wave'/f'original_{name}_coefficients.json' for name in ('weather','hour','cloud')]
    for path in coefficients:
        shutil.copyfile(path,OUT/path.name)
    inputs = [DATA/fold/name for fold in FOLDS for name in ('train.parquet','evaluation.parquet','features.json')]
    inputs += [MODELS/fold/'mlp_cf'/f'seed{seed}'/name for fold in FOLDS for seed in (0,1,2) for name in ('model.joblib','input_preprocessing.joblib','target_scaler.joblib','daylight_raw.parquet','config.json','runtime.json')]
    inputs += [RENEW/'mlp_wave/data'/fold/name for fold in FOLDS for name in ('labels.parquet','coverage.parquet','application_inputs.parquet')]
    inputs += [OLD/'refinement_wave/chosen_recipe.json',OLD/'profile_wave/selected_recipe.json',RENEW/'recency_wave/results.json',*coefficients]
    for fold in FOLDS:
        inputs += [MODELS/fold/'mlp_cf/ensemble/pure/predictions.parquet',OLD/'refinement_wave'/fold/'recipes/leaves63_trees400_ensemble/predictions.parquet',OLD/'profile_wave'/fold/'stations_lgb/ensemble/complement/predictions.parquet',RENEW/'recency_wave/comparisons/decay180/ensemble'/fold/'predictions.parquet']
        inputs += [RENEW/wave/'comparisons'/arm/fold/'predictions.parquet' for wave,arm in (('calibration_wave','temperature_then_snow'),('hour_wave','hour_bias'),('sky_wave','cloud_bias'))]
    protected = set(inputs)
    protected.update(ROOT/r['original'] for r in snapshots.values())
    protected.update(p for p in (ROOT/'submission').rglob('*.py') if '__pycache__' not in p.parts and not p.name.startswith(('incbound_','score_push_verify_incbound')))
    folders = [ROOT/'submission'/name for name in ('autoresearch_candidate','score_push_candidate','renew_candidate_20261105','renew_hour_candidate_20261105','renew_sky_candidate_20261105')]
    folders += [p for p in RENEW.iterdir() if p.is_dir() and p!=OUT]
    for folder in folders:
        protected.update(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'tmp' not in p.parts and p.name!='controller.lock' and not p.name.startswith('independent_'))
    save(OUT/'protocol.json',{'created_utc':now(),'arm':'incumbent_rich_mlp_train_range','candidate_count':1,'folds':FOLDS,'seeds':[0,1,2],'bounds':'Exact column MIN/MAX over original identical preprocessor applied to TRAIN rich100 only; clip all future transformed columns. No column choice/quantile/grid. TRAIN clip bitwise identity.','target_inverse':'Original rawCF target scaler inverse ONCE then daylight capacity; no Haurwitz normalizer.','ensemble':'Original pandas concat/groupby signed3seed p_raw.mean, THEN max0; no capacity clip at component.','replacement':'canonical rawtemporal + effectiveMLPweight*(boundedMLPensemble-canonicaloldMLPensemble); preserve canonical rawtemporal bits when delta0; effective weight from stored refinement/profile/temporal recipes; no alpha or weight refit.','stages':'Original weather->hour->cloud arithmetic and caps, without early capacity clip before weather. Exact stored full lineage replay required.','selection':'ONE candidate strictly lower W than current sky on BOTH folds; otherwise retain reference; no alpha optimization.','reference_scores':REFERENCE,'prefit_barrier':'Zero model loads/predicts/fits during preparation. Stored prediction arithmetic permitted for lineage only; no candidate scoring until release.','resources':{'cpu_max_threads':16,'priority_class':32,'pyarrow_threads':4,'parallel_jobs':1,'historical_MLP_inference_blas_threads':1,'scope':'BLAS1 only original-model parity/bounded inference; no heavy fits'},'native_worker_budget':6,'native_inference_budget':12,'real_model_fit_budget':0,'no_confirmation_test_fullrefit_export':True,'historical_exposure':'All history exposed; no independent holdout claim','original_coefficients_sha256':{p.name:digest(p) for p in coefficients},'snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)}})

def install_frozen() -> None:
    protocol = json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
    sys.meta_path.insert(0,gpu_common.FrozenImports())
    for name,r in protocol['own_sources'].items():
        assert digest(ROOT/r['original'])==digest(OUT/'sources/own'/name)==r['sha256']
    for r in protocol['snapshots'].values():
        assert digest(ROOT/r['original'])==r['sha256']
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
    assert release['native_inference_budget']==12 and release['real_model_fit_budget']==0
    check_prepared()
