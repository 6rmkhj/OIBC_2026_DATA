# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
"""Immutable prefit sources, input hashes, and complete wave protocol."""
from cloud_common import ROOT, OUT, RAW, DATA, TEMPORAL, CUTOFFS, PROVIDERS, FOLDS, ARMS, PARAMS, AUX_PARAMS, REFERENCE, save, digest, now
from pathlib import Path
import json
import shutil

def freeze() -> None:
    if (OUT/'protocol.json').exists():
        return
    for folder in ('sources/own','evidence','data'):
        (OUT/folder).mkdir(parents=True,exist_ok=True)
    previous = json.loads((TEMPORAL/'protocol.json').read_text())
    snapshots = {}
    for folder in ('autoresearch','score_push','score_push_gpu'):
        for path in (ROOT/'submission'/folder).glob('*.py'):
            shutil.copyfile(path,OUT/'sources'/path.name)
            snapshots[path.stem] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    own = {}
    for path in Path(__file__).parent.glob('*.py'):
        shutil.copyfile(path,OUT/'sources/own'/path.name)
        own[path.name] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    inputs = [p for f in FOLDS for p in (DATA/f).glob('*') if p.is_file()]
    inputs += [RAW/'sites.csv',ROOT/previous['night_source'],ROOT/previous['assignment_source']]
    inputs += [RAW/'train'/f'{kind}_{provider}.parquet' for provider in PROVIDERS for kind in ('forecast','observed')]
    inputs += [TEMPORAL/'comparisons/decay180/ensemble'/f/'predictions.parquet' for f in FOLDS]
    inputs += [TEMPORAL/'data'/f/'night_coverage.parquet' for f in FOLDS]
    protected = dict(previous['protected_sha256'])
    protected.update({str(p.relative_to(ROOT)):digest(p) for p in inputs})
    protected.update({str(p.relative_to(ROOT)):digest(p) for p in TEMPORAL.rglob('*') if p.is_file()})
    save(OUT/'protocol.json',{'created_utc':now(),'tier':'HEAVY: chronological auxiliary learning and model lineage','cutoffs':CUTOFFS,'providers':PROVIDERS,'arms':ARMS,'auxiliary_parameters':AUX_PARAMS,'generation_parameters':PARAMS,'generation_seeds':[0,1,2],'seed0_generation_random_state':None,'auxiliary_fit_count':14,'generation_fit_count':12,'reference_scores':REFERENCE,'observation_policy':'Each fit independently reads ONLY station,ts,cloud with Arrow ts<=own cutoff minus 1 day; finite 0<=cloud<=100 labels only. Saved exact valid label rows and read receipt. No observation input columns.','forecast_policy':'Complete metadata station x hourly grid, round17 whole-row fallback10 only if17 row absent, independent10,17-minus10; native NaNs; station category/hour and dayofyear cyclic. No year,epoch,generation,CF,price,k or actual observations as features.','chronology':'OOF block cutoff<ts<=next cutoff. Warmup ts<=2021Jun1 uses raw forecast cloud plus flag. Primary evaluation uses ONLY2023Jun1 model; recent ONLY2024Jun1. Cache same fit across OOF and outer.','aggregation':'Exact original daylight site coverage; capacity contributions divided by total group capacity, absent station0/allmissingNaN; groupmean uses sum(capacity*nonmissingcloud)/sum(availablecapacity), allmissingNaN. Means arm adds provider means/warmup; profiles adds station contributions.','generation':'station904 plus auxiliary features; train-only constant mask; decay180 normalized by TRAIN mean; sampleweight=normalizer*decay; targetCF/normalizer, inverse normalizer*capacity; 400 trees, all3seeds.','selection':'Mean signed finite raw predictions before clipping, verified night zero fill. One alpha PRIMARY only vs complete decay180 temporal reference, transfer unchanged recent; eligible both W strictly improve and alpha>=.02; select minimum mean relative W. Also compare matched pure noaux temporal predictions.','historical_exposure':'All development historically exposed. Seed0 auxiliary screening is not robust final adoption. No official score claim.','confirmation_loaded':False,'test_loaded':False,'no_full_refit_or_export':True,'night_source':previous['night_source'],'assignment_source':previous['assignment_source'],'snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':protected,'resources':{'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_fits':1,'gpu_device':0,'gpu_ram_part':.9}})

