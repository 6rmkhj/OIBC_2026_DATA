# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: imported by sky_run.py.
"""Fixed cloud-stage paths, source freezing and CPU resource contracts."""
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Final
ROOT: Final = Path(__file__).resolve().parents[2]
RENEW: Final = ROOT/'analysis_outputs/renew_20261105'
OUT: Final = RENEW/'sky_wave'
DATA: Final = ROOT/'analysis_outputs/score_push_gpu_20261104/data'
REFERENCE_DIR: Final = RENEW/'hour_wave/comparisons/hour_bias'
FOLDS: Final = {'primary':('2023-06-01','2024-06-01'),'recent':('2024-06-01','2025-03-01')}
REFERENCE: Final = {'primary':11.912571076235176,'recent':10.998534992012488}
BINS: Final = ('[-inf,20)','[20,50)','[50,80)','[80,inf)')
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

def freeze() -> None:
    assert not (OUT/'protocol.json').exists(),'Single authorized wave; preserve existing evidence'
    (OUT/'sources/own').mkdir(parents=True)
    (OUT/'evidence').mkdir(exist_ok=True)
    snapshots = {}
    sources = [p for folder in ('autoresearch','score_push','score_push_gpu') for p in (ROOT/'submission'/folder).glob('*.py')]
    sources.append(Path(__file__).with_name('cal_math.py'))
    for source in sources:
        shutil.copyfile(source,OUT/'sources'/source.name)
        snapshots[source.stem] = {'original':str(source.relative_to(ROOT)),'sha256':digest(source)}
    own = {}
    for source in Path(__file__).parent.glob('sky_*.py'):
        shutil.copyfile(source,OUT/'sources/own'/source.name)
        own[source.name] = {'original':str(source.relative_to(ROOT)),'sha256':digest(source)}
    inputs = [REFERENCE_DIR/fold/'predictions.parquet' for fold in FOLDS]
    inputs += [DATA/fold/'evaluation.parquet' for fold in FOLDS]
    inputs += [RENEW/'recency_wave/data'/fold/'night_coverage.parquet' for fold in FOLDS]
    inputs += [RENEW/'hour_wave'/name for name in ('coefficients.json','results.json','terminal_manifest.json')]
    inputs += [RENEW/'final/static_capacity.json',RENEW/'best_development.json']
    protected = set(inputs)|{ROOT/r['original'] for r in snapshots.values()}
    protected.update(p for p in (ROOT/'submission').rglob('*.py') if '__pycache__' not in p.parts and not p.name.startswith('sky_'))
    folders = [ROOT/'submission'/name for name in ('autoresearch_candidate','score_push_candidate','renew_candidate_20261105','renew_hour_candidate_20261105')]
    folders += [p for p in RENEW.iterdir() if p.is_dir() and p!=OUT]
    for folder in folders:
        protected.update(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'tmp' not in p.parts and p.name!='controller.lock')
    save(OUT/'protocol.json',{'created_utc':now(),'authorization':'Root direct execution of one preregistered fixed provider-B cloud stage','candidate':'cloud_bias','candidate_count':1,'folds':FOLDS,'reference_scores':REFERENCE,'reference':'CURRENT hour/weather calibrated p; neither earlier stage refitted or collapsed','feature_projection':['ts','grp','wb_cloud'],'cloud_bins':BINS,'nonfinite':'Identity, cloud_bin=-1','finite_out_of_range':'Keep all finite values, including100.00000000000001; no0..100filter','fit':'Exactly4 cal_math.fit_factor calls PRIMARY only. y/p, weights=SMP*k*p; p>0,cost>0; >=150rows AND>=20distinct KST(ts-1h) dates; unsupported identity; bounded[.85,1.15].','apply':'Only ts,grp,p_reference,wb_cloud,static_capacity. NEW stage effective=1+.5*(bounded_cloud_factor-1); clip(alreadyhour/weathercalibratedp*effective,0,staticcap).','selection':'Single fixed candidate; strict W improvement both folds else retain current hour reference. No alpha/bin/factor/shrink grid.','historical_exposure':'All history exposed; primary improvement partly in-sample; no independent holdout claim','resources':{'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_jobs':1,'scalar_fit_budget':4,'tree_fits':0},'no_confirmation_test_export':True,'snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)}})

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
