# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: imported by refresh_run.py.
"""Chronological refresh preregistration, frozen helpers and resources."""
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Final
ROOT: Final = Path(__file__).resolve().parents[2]
RENEW: Final = ROOT/'analysis_outputs/renew_20261105'
OUT: Final = RENEW/'refresh_wave'
GPU: Final = ROOT/'analysis_outputs/score_push_gpu_20261104/data'
FOLDS: Final = {'late_recent':('2024-12-01','2025-03-01'),'latest':('2025-03-01','2025-06-01')}
COLUMNS: Final = ['ts','grp','p_reference','wa_temp','extra_wa_snow','wb_cloud','static_capacity']
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

def source_paths(name: str) -> dict[str,Path]:
    if name=='latest':
        return {'raw':RENEW/'final/predictions/latest_cutoff_march_may/predictions.parquet','labels':RENEW/'final/predictions/latest_cutoff_march_may/scored_predictions.parquet','weather':RENEW/'final/data/march_may/evaluation.parquet','coverage':RENEW/'final/data/march_may/coverage.parquet','p_weather':RENEW/'final/predictions/latest_cutoff_march_may/predictions.parquet','p_hour':RENEW/'hour_final/predictions/latest_cutoff_march_may/predictions.parquet','p_cloud':RENEW/'sky_final/predictions/latest_cutoff_march_may/predictions.parquet'}
    return {'raw':RENEW/'recency_wave/comparisons/decay180/ensemble'/name/'predictions.parquet','labels':RENEW/'recency_wave/comparisons/decay180/ensemble'/name/'predictions.parquet','weather':GPU/name/'evaluation.parquet','coverage':RENEW/'recency_wave/data'/name/'night_coverage.parquet','p_weather':RENEW/'calibration_wave/comparisons/temperature_then_snow'/name/'predictions.parquet','p_hour':RENEW/'hour_wave/comparisons/hour_bias'/name/'predictions.parquet','p_cloud':RENEW/'sky_wave/comparisons/cloud_bias'/name/'predictions.parquet'}

def freeze() -> None:
    assert not (OUT/'protocol.json').exists(),'Single execution; preserve any prior attempt'
    (OUT/'sources/own').mkdir(parents=True)
    (OUT/'evidence').mkdir(exist_ok=True)
    snapshots = {}
    helpers = [p for folder in ('autoresearch','score_push','score_push_gpu') for p in (ROOT/'submission'/folder).glob('*.py')]
    helpers += [Path(__file__).with_name(name) for name in ('cal_math.py','hour_math.py','sky_math.py')]
    for path in helpers:
        shutil.copyfile(path,OUT/'sources'/path.name)
        snapshots[path.stem] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    own = {}
    for path in Path(__file__).parent.glob('refresh_*.py'):
        shutil.copyfile(path,OUT/'sources/own'/path.name)
        own[path.name] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    originals = {'weather':RENEW/'final/selected_coefficients.json','hour':RENEW/'hour_wave/coefficients.json','cloud':RENEW/'sky_wave/coefficients.json'}
    for name,path in originals.items():
        shutil.copyfile(path,OUT/f'original_{name}_coefficients.json')
    inputs = set(originals.values())|{path for name in ('primary','recent','latest') for path in source_paths(name).values()}
    inputs |= {RENEW/'final/static_capacity.json',RENEW/'best_development.json'}
    protected = set(inputs)
    protected.update(ROOT/r['original'] for r in snapshots.values())
    protected.update(p for p in (ROOT/'submission').rglob('*.py') if '__pycache__' not in p.parts and not p.name.startswith(('refresh_','score_push_verify_refresh')))
    folders = [ROOT/'submission'/name for name in ('autoresearch_candidate','score_push_candidate','renew_candidate_20261105','renew_hour_candidate_20261105','renew_sky_candidate_20261105')]
    folders += [p for p in RENEW.iterdir() if p.is_dir() and p!=OUT]
    for folder in folders:
        protected.update(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'tmp' not in p.parts and p.name!='controller.lock' and not p.name.startswith('independent_'))
    save(OUT/'protocol.json',{'created_utc':now(),'authorization':'One fixed chronological refresh directly authorized,32scalarfits0trees','folds':FOLDS,'training':'PRIMARY all +RECENT ts<=fold cutoff; unique disjoint source keys; no forward evaluation rows in training','evaluation':'late_recent 2024-12-01<ts<=2025-03-01(4320); latest2025-03-01<ts<=2025-06-01(4416), latestcutoff preweather p_reference base','algorithm':'cal_math.fit7 including unused snow-only; apply temperature_then_snow(.5 shrink,capacityclip) toTRAIN; hour_math.fit5 onweatherp; applyhour(.5,clip) toTRAIN; sky_math.fit4 onhourp. Freeze16coefficients/fold,applyfuturepipeline unchanged.','fit_contract':'Existing weighted median y/p with SMP*k*p;150positiveprediction/costrows AND20distinct KST(ts-1h)days;unsupportedidentity;bounds.85..1.15. No recency weights,new thresholds,grids or alpha.','original_replay_first':'Saved original weather/hour/cloud coefficients must exactly replay eachstage on primary/recent/latest before any newfit; never refit originals','gate':'Strict Wlower than EACH frozen weather/hour/cloud reference in BOTH forward periods; six comparisons; no weak-reference selection','historical_exposure':'All historical periods exposed, no independent holdout claim; chronological evaluation prevents this refresh from fitting evaluation labels','resources':{'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_jobs':1,'scalar_fit_budget':32,'tree_fits':0},'no_full_refit_test_export':True,'original_coefficients_sha256':{name:digest(path) for name,path in originals.items()},'snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(inputs)},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)}})

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
