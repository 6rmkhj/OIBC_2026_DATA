# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: called by renew_final_run.py --prepare before any new diagnostic comparison read.
"""Freeze the selected recipe, six-fit budget and untouched prior artifacts."""
import json
from pathlib import Path
import shutil
from renew_final_common import ROOT,OUT,OLD,CPU,RENEW,ALPHA,COMPOSITION,CUTOFFS,PARAMS,save,digest,now


def freeze() -> None:
    if (OUT/'protocol.json').exists():
        return
    (OUT/'sources/own').mkdir(parents=True)
    (OUT/'evidence').mkdir(exist_ok=True)
    snapshots = {}
    sources = [p for folder in ('autoresearch','score_push','score_push_gpu') for p in (ROOT/'submission'/folder).glob('*.py')]
    sources += [Path(__file__).with_name('cal_math.py'),ROOT/'submission/validate_artifacts.py']
    for path in sources:
        shutil.copyfile(path,OUT/'sources'/path.name)
        snapshots[path.stem] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    own = {}
    for path in [*Path(__file__).parent.glob('renew_final_*.py'),Path(__file__).with_name('temporal_common.py')]:
        shutil.copyfile(path,OUT/'sources/own'/path.name)
        own[path.name] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    composition = ROOT/'submission/autoresearch_candidate/composition.csv'
    assert digest(composition)==COMPOSITION
    shutil.copyfile(RENEW/'calibration_wave/coefficients.json',OUT/'selected_coefficients.json')
    shutil.copyfile(RENEW/'calibration_wave/static_capacity.json',OUT/'static_capacity.json')
    provenance = ROOT/'analysis_outputs/award_run/provenance.json'
    cache = provenance.parent/'cache'/json.loads(provenance.read_text())['cache_key']
    inputs = [composition,provenance,cache/'feat_train.parquet',cache/'feat_test.parquet',ROOT/'handover 2/01_participant_dataset/sites.csv',ROOT/'analysis_outputs/autoresearch_20261103/cache/assignment.json',ROOT/'analysis_outputs/autoresearch_20261103/cache/features.json',CPU/'trials/combined_physics/features.json']
    inputs += [OLD/name for name in ('full_train.parquet','outer_features.parquet','test_features.parquet')]
    inputs += [CPU/'final/cache'/f'{split}_{kind}.parquet' for split in ('train','test') for kind in ('weather','stations')]
    inputs += [CPU/'final'/f'{split}_predictions.parquet' for split in ('outer','test')]
    inputs += [CPU/'deployment_check'/name for name in ('evaluation_features.parquet','paired_predictions.parquet','frozen_predictions.parquet')]
    inputs += [RENEW/'calibration_wave'/name for name in ('coefficients.json','static_capacity.json','independent_check.json')]
    inputs += [RENEW/'calibration_wave/comparisons/temperature_then_snow/recent/predictions.parquet',RENEW/'recency_wave/comparisons/decay180/ensemble/decision.json',RENEW/'recency_wave/comparisons/decay180/ensemble/recent/predictions.parquet',ROOT/'analysis_outputs/score_push_gpu_20261104/data/recent/evaluation.parquet']
    inputs += [RENEW/'recency_wave/trials/decay180/recent'/f'seed{s}'/n for s in range(3) for n in ('model.txt','config.json')]
    protected = set(inputs)|set(sources)
    for folder in (CPU/'final',CPU/'deployment_check',OLD,ROOT/'submission/autoresearch_candidate',ROOT/'submission/score_push_candidate',RENEW/'recency_wave',RENEW/'calibration_wave',RENEW/'group_wave',RENEW/'total_wave'):
        protected.update(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    save(OUT/'protocol.json',{
        'created_utc':now(),'selected_recipe':'decay180 temporal blend then temperature_then_snow fixed calibration',
        'alpha':ALPHA,'alpha_source':'recency_wave/comparisons/decay180/ensemble/decision.json',
        'calibration_source':'calibration_wave/coefficients.json','coefficient_sha256':digest(OUT/'selected_coefficients.json'),
        'static_capacity_sha256':digest(OUT/'static_capacity.json'),'composition_sha256':COMPOSITION,
        'new_model_budget':6,'cutoffs':CUTOFFS,'seeds':[0,1,2],'seed0_random_state':None,'parameters':PARAMS,
        'target':'existing normalized station cf/normalizer','weights':'normalizer * exp2(-age_days/180)/mean(TRAIN decay), fixed cutoff age',
        'mask':'fit train-only constant mask separately at each cutoff',
        'inference':'mean SIGNED kWh all3seeds then clip>=0, zero only proven allnight groups; temporal blend=(1-alpha)*CPUbase+alpha*temporal. Frozen cal_math.apply temperature_then_snow, no coefficient fitting.',
        'diagnostics':{'recent':'reconstruct and replay against selected calibration predictions before new fits','old_cutoff_MarMay':'existing recent temporal models cutoff2024Jun1 plus existing final outer p_candidate','latest_cutoff_MarMay':'3new temporal fits cutoff2025Mar1 plus existing deployment_check frozen p_candidate','test':'3new temporal fits cutoff2025Jun1 plus existing final test p_candidate'},
        'label_policy':'Freeze before any new comparison. Preparation may read bounded full_train cf for declared training cutoffs, but never opens MarchMay evaluation y/SMP/k. Diagnostic labels opened only after root release and predictions frozen. No test labels.',
        'decision':'No tuning/reselection/adaptation from confirmation; preserve adverse results. Export selected development recipe regardless diagnostic direction.',
        'reconstruction':'final_build.enrich READONLY using preexisting final/cache sidecars; NEVER call sidecars(), never write older namespace.',
        'export':{'new_directory':'submission/renew_candidate_20261105','forecast_rows':17520,'sites':253,'composition':'byte-identical fixed assignment','precision_decimals':3,'zip_members':['composition.csv','forecast.csv'],'readme':'Korean','upload':False},
        'resources':{'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_fits':1},
        'night_cache':str(cache.relative_to(ROOT)),'snapshots':snapshots,'own_sources':own,
        'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},
        'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)}})
