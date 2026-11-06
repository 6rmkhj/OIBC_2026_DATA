# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
# How to run: called before inference or diagnostics by hour_final_run.py.
"""Freeze the accepted hour recipe and every prior artifact before any diagnostics."""
import shutil
from pathlib import Path
from hour_final_common import ROOT,OUT,PRIOR,HOUR,CANDIDATE,COEFFICIENT,COMPOSITION,SPLITS,digest,save,now

def freeze() -> None:
    assert not (OUT/'protocol.json').exists(),'Export is single-run; preserve existing evidence'
    assert not CANDIDATE.exists(),'New candidate namespace required'
    (OUT/'sources/own').mkdir(parents=True)
    (OUT/'evidence').mkdir(exist_ok=True)
    snapshots = {}
    sources = [p for folder in ('autoresearch','score_push','score_push_gpu') for p in (ROOT/'submission'/folder).glob('*.py')]
    sources += [Path(__file__).with_name(n) for n in ('hour_math.py','cal_math.py')]
    for source in sources:
        shutil.copyfile(source,OUT/'sources'/source.name)
        snapshots[source.stem] = {'original':str(source.relative_to(ROOT)),'sha256':digest(source)}
    own = {}
    for source in Path(__file__).parent.glob('hour_final*.py'):
        shutil.copyfile(source,OUT/'sources/own'/source.name)
        own[source.name] = {'original':str(source.relative_to(ROOT)),'sha256':digest(source)}
    inputs = [PRIOR/'predictions'/split/'predictions.parquet' for split in SPLITS]
    inputs += [PRIOR/'predictions'/split/'scored_predictions.parquet' for split in SPLITS if split!='test']
    inputs += [HOUR/name for name in ('coefficients.json','results.json','protocol.json','source_amendment.json','terminal_manifest.json')]
    inputs += [PRIOR/'static_capacity.json',PRIOR/'selected_coefficients.json',ROOT/'submission/autoresearch_candidate/composition.csv',ROOT/'submission/validate_artifacts.py',ROOT/'handover 2/01_participant_dataset/sites.csv']
    protected = set(inputs)|{ROOT/r['original'] for r in snapshots.values()}
    protected.update(p for p in (ROOT/'submission').rglob('*.py') if '__pycache__' not in p.parts and not p.name.startswith('hour_final'))
    for folder in ('submission/autoresearch_candidate','submission/score_push_candidate','submission/renew_candidate_20261105','analysis_outputs/renew_20261105'):
        protected.update(p for p in (ROOT/folder).rglob('*') if p.is_file() and OUT not in p.parents and '__pycache__' not in p.parts and 'tmp' not in p.parts and p.name!='controller.lock')
    assert digest(HOUR/'coefficients.json')==COEFFICIENT
    assert digest(ROOT/'submission/autoresearch_candidate/composition.csv')==COMPOSITION
    shutil.copyfile(HOUR/'coefficients.json',OUT/'selected_hour_coefficients.json')
    save(OUT/'protocol.json',{'created_utc':now(),'authorization':'Root explicitly authorized export of independently verified accepted hour candidate; no additional fitting or tuning','candidate':str(CANDIDATE.relative_to(ROOT)),'source_prediction_splits':SPLITS,'source_prediction':'Reuse final/predictions/{split}/predictions.parquet p as p_reference; already weather-calibrated','recipe':'Frozen hour_math.apply exactly once: KST bins [0,10),[10,12),[12,14),[14,16),[16,24); effective=1+.5*(bounded_hour_factor-1); clip(current calibrated p*effective,0,static_capacity). No temperature/snow refit or repeated shrink.','coefficient_sha256':COEFFICIENT,'composition_sha256':COMPOSITION,'scalar_fits':0,'tree_fits':0,'predictions_before_labels':True,'diagnostics':'Read only existing old/latest scored_predictions labels after all output predictions frozen. Descriptive fixed recipe only; no reselection.','export':'17520 test rows sorted grp/ts, np.round(p,3); byte-identical original composition; ZIP exactly composition.csv and forecast.csv','original_official_score':6454220836,'original_score_provenance':'User-reported score of preserved renew_candidate; new candidate official score unavailable','all_history_exposed':True,'resources':{'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_jobs':1},'snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)}})
