# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/temporal_run.py --prepare
"""Immutable prefit protocol and target-free night coverage checks."""
from temporal_common import ROOT, OUT, DATA, FOLDS, VARIANTS, PARAMS, REFERENCE, digest, save, now, decay_multiplier, signed_mean
from pathlib import Path
import json
import shutil

def freeze() -> None:
    if (OUT/'protocol.json').exists():
        return
    (OUT/'sources/own').mkdir(parents=True)
    (OUT/'evidence').mkdir()
    snapshots = {}
    for folder in ('autoresearch','score_push','score_push_gpu'):
        for path in (ROOT/'submission'/folder).glob('*.py'):
            shutil.copyfile(path, OUT/'sources'/path.name)
            snapshots[path.stem] = {'original':str(path.relative_to(ROOT)), 'sha256':digest(path)}
    own = {}
    for path in Path(__file__).parent.glob('temporal_*.py'):
        shutil.copyfile(path, OUT/'sources/own'/path.name)
        own[path.name] = {'original':str(path.relative_to(ROOT)), 'sha256':digest(path)}
    prior = ROOT/'analysis_outputs/score_push_20261104'
    provenance = ROOT/'analysis_outputs/award_run/provenance.json'
    night_source = provenance.parent/'cache'/json.loads(provenance.read_text())['cache_key']/'feat_train.parquet'
    assignment = ROOT/'analysis_outputs/autoresearch_20261103/cache/assignment.json'
    inputs = [p for f in FOLDS for p in (DATA/f).glob('*') if p.is_file()]
    inputs += [prior/f'closing_wave/{f}/selected/predictions.parquet' for f in FOLDS]
    inputs += [provenance, night_source, assignment]
    protected = set(inputs) | {ROOT/r['original'] for r in snapshots.values()}
    for folder in (prior/'final',ROOT/'submission/score_push_candidate',ROOT/'submission/autoresearch_candidate'):
        protected.update(p for p in folder.rglob('*') if p.is_file() and p.suffix!='.md' and '__pycache__' not in p.parts)
    save(OUT/'protocol.json', {'created_utc':now(),'variants':VARIANTS,'folds':{'primary':{'cutoff':'2023-06-01','end':'2024-06-01','full_keys':17568,'daylight_keys':9642},'recent':{'cutoff':'2024-06-01','end':'2025-03-01','full_keys':13104,'daylight_keys':7015}},'seeds':[0,1,2],'seed0_random_state':None,'model_fit_budget':24,'parameters':PARAMS,'reference_scores':REFERENCE,'decay':'age_days=(fixed_fold_cutoff-ts)/86400seconds; 2**(-age_days/half_life), divided by retained TRAIN mean; sample_weight=normalizer*decay','window':'cutoff-365days < ts <= cutoff; normalizer sample weights; refit train-only constant mask after row filtering','target':'cf/normalizer; inverse normalizer*capacity_kw','ensemble':'mean finite signed seed raw values, then clip >=0; zero fill only independently verified full-night keys','selection':'Fit one scalar alpha on PRIMARY only versus complete CPU reference; transfer unchanged recent. Eligible iff both W strictly improve and alpha>=.02; select minimum equal-fold mean relative W else retain CPU reference. No simplex, screening, early stopping, full refit or export.','historical_exposure':'All development historically exposed; no pristine holdout claim. Prior raw-CF recent365/recent730 failed (autoresearch results rows10/11); this is normalized station904 feature temporal adaptation.','confirmation_loaded':False,'test_loaded':False,'night_source':str(night_source.relative_to(ROOT)),'assignment_source':str(assignment.relative_to(ROOT)),'snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)},'resources':{'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_fits':1}})

def prepare() -> None:
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- exact historical keys
    from final_metrics import metrics
    from calibrate import self_check
    protocol = json.loads((OUT/'protocol.json').read_text())
    assert all(digest(ROOT/p)==sha for p,sha in protocol['input_sha256'].items())
    self_check()
    np.testing.assert_array_equal(decay_multiplier(np.array([0.,180.]),180), [4/3,2/3])
    age = np.array([0., 365.-1/24,365.,366.])
    np.testing.assert_array_equal(age<365, [True,True,False,False])
    np.testing.assert_array_equal(signed_mean(np.array([[-2.,0.],[1.,0.],[4.,0.]])),[1.,0.])
    try:
        signed_mean(np.array([[np.nan]]))
    except AssertionError:
        rejected_nan = True
    else:
        raise AssertionError('NaN accepted')
    assert rejected_nan
    duplicate = pd.DataFrame({'ts':[1,1],'grp':['G1','G1']})
    assert duplicate.duplicated(['ts','grp']).any()
    assignment = json.loads((ROOT/protocol['assignment_source']).read_text())
    for fold in FOLDS:
        spec = protocol['folds'][fold]
        cutoff = pd.Timestamp(spec['cutoff'],tz='Asia/Seoul')
        end = pd.Timestamp(spec['end'],tz='Asia/Seoul')
        labels = pd.read_parquet(DATA/fold/'labels.parquet')
        closing = pd.read_parquet(ROOT/f'analysis_outputs/score_push_20261104/closing_wave/{fold}/selected/predictions.parquet',columns=['ts','grp','y','smp','k','p'],filters=[('ts','>',cutoff),('ts','<=',end)]).rename(columns={'p':'p_reference'})
        pd.testing.assert_frame_equal(labels[list(closing)].reset_index(drop=True),closing.reset_index(drop=True))
        assert len(labels)==spec['full_keys'] and abs(metrics(labels,'p_reference')['W_pct']-REFERENCE[fold])<1e-10
        rows = pd.read_parquet(ROOT/protocol['night_source'],columns=['site_id','ts','night'],filters=[('ts','>',cutoff),('ts','<=',end)])
        rows['grp'] = rows.site_id.map(assignment)
        assert rows.grp.notna().all() and not rows.duplicated(['ts','site_id']).any()
        coverage = rows.groupby(['ts','grp'],as_index=False).night.all()
        aligned = labels[['ts','grp']].merge(coverage,on=['ts','grp'],how='outer',validate='one_to_one',indicator=True)
        assert aligned._merge.eq('both').all()
        keys = pd.read_parquet(DATA/fold/'evaluation.parquet',columns=['ts','grp'])
        expected = coverage.loc[~coverage.night,['ts','grp']].sort_values(['ts','grp']).reset_index(drop=True)
        pd.testing.assert_frame_equal(keys.sort_values(['ts','grp']).reset_index(drop=True),expected)
        assert len(keys)==spec['daylight_keys']
        directory = OUT/'data'/fold
        directory.mkdir(parents=True,exist_ok=True)
        coverage.to_parquet(directory/'night_coverage.parquet',index=False)
    save(OUT/'evidence/prefit_checks.json',{'passed':True,'utc':now(),'fixtures':['age half-life','strict window boundary','signed mean before clipping','zero','NaN rejection','duplicate detection'],'reference_labels_exact':True,'night_coverage_exact':True,'confirmation_loaded':False,'test_loaded':False})
