# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "scikit-learn", "joblib", "threadpoolctl"]
# ///
# How to run: imported by bound_run.py.
"""One train-min/max bounded inference variant; existing models stay immutable."""
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Final
ROOT: Final = Path(__file__).resolve().parents[2]
RENEW: Final = ROOT/'analysis_outputs/renew_20261105'
OUT: Final = RENEW/'bounds_wave'
MLP: Final = RENEW/'mlp_wave'
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
    assert not (OUT/'protocol.json').exists(),'Single authorized execution; preserve evidence'
    (OUT/'sources/own').mkdir(parents=True)
    (OUT/'evidence').mkdir(exist_ok=True)
    snapshots = {}
    helpers = [p for folder in ('autoresearch','score_push','score_push_gpu') for p in (ROOT/'submission'/folder).glob('*.py')]
    helpers += [Path(__file__).with_name(n) for n in ('cal_math.py','hour_math.py','sky_math.py','temporal_common.py')]
    for path in helpers:
        shutil.copyfile(path,OUT/'sources'/path.name)
        snapshots[path.stem] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    own = {}
    for path in Path(__file__).parent.glob('bound_*.py'):
        shutil.copyfile(path,OUT/'sources/own'/path.name)
        own[path.name] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    coefficients = [MLP/f'original_{name}_coefficients.json' for name in ('weather','hour','cloud')]
    for path in coefficients:
        shutil.copyfile(path,OUT/path.name)
    inputs = [MLP/'data'/fold/name for fold in FOLDS for name in ('x_train.npy','x_evaluation.npy','target_scaler.joblib','evaluation_transform.parquet','labels.parquet','coverage.parquet','application_inputs.parquet','feature_mask.json')]
    inputs += [MLP/'trials'/fold/f'seed{seed}'/name for fold in FOLDS for seed in (0,1,2) for name in ('model.joblib','config.json')]
    inputs += [*coefficients,MLP/'evidence/environment.json',MLP/'prepared_manifest.json',MLP/'terminal_manifest.json',RENEW/'best_development.json']
    protected = set(inputs)
    protected.update(ROOT/r['original'] for r in snapshots.values())
    protected.update(p for p in (ROOT/'submission').rglob('*.py') if '__pycache__' not in p.parts and not p.name.startswith(('bound_','score_push_verify_bounds')))
    folders = [ROOT/'submission'/name for name in ('autoresearch_candidate','score_push_candidate','renew_candidate_20261105','renew_hour_candidate_20261105','renew_sky_candidate_20261105')]
    folders += [p for p in RENEW.iterdir() if p.is_dir() and p!=OUT]
    for folder in folders:
        protected.update(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'tmp' not in p.parts and p.name!='controller.lock' and not p.name.startswith('independent_'))
    save(OUT/'protocol.json',{'created_utc':now(),'arm':'station_mlp_train_range','candidate_count':1,'authorization':'Direct one fixed inference-only variant on existing6MLPs','folds':FOLDS,'seeds':[0,1,2],'bounds':'Per selected standardized feature, exact MIN/MAX over immutable mlp_wave/data/fold/x_train.npy. Clip x_evaluation.npy to these bounds. No quantiles/zthresholds/newselection/grid.','proof':'Clipping all TRAIN entries must be exact identity; all6original model weights reused,0refits. Bounds transform computed once/fold.','inference':'Original targetscaler inverse ONCE*original evaluation inverse_kwh; save signed raw;3seed signedmean before0/staticcapclip;originalweather->hour->cloud eachstage unchanged halfshrink/cap','selection':'One PRIMARY-onlyalpha vs currentcloud baseline; transferrecent; BOTHstrictWimprovement ANDalpha>=.02','reference_scores':REFERENCE,'new_model_fits':0,'native_inference_budget':6,'bounds_transform_count':2,'no_confirmation_test_export':True,'historical_exposure':'All history exposed; no independentholdout claim','resources':{'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_jobs':1,'inference_pools_exact16':True,'nonfitting_controller_pools_max16':True},'original_coefficients_sha256':{p.name:digest(p) for p in coefficients},'snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)}})

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
        assert digest(OUT/name)==sha

def check_prepared() -> None:
    for path,sha in json.loads((OUT/'prepared_manifest.json').read_text(encoding='utf-8')).items():
        assert digest(OUT/path)==sha,path
