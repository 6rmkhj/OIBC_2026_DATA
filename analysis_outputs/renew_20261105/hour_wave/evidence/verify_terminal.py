# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: python analysis_outputs/renew_20261105/hour_wave/evidence/verify_terminal.py
"""Read-only arithmetic replay of saved hour factors, predictions and decision."""
import json
import os
import sys
from pathlib import Path
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name] = '16'
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'submission/score_push_renew'))
from hour_common import OUT,digest,save,now,configure,install_frozen
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact original parquet and scoring contracts
from threadpoolctl import threadpool_limits

def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def main() -> None:
    configure()
    install_frozen()
    protocol = read(OUT/'protocol.json')
    for path,sha in protocol['protected_sha256'].items():
        assert digest(ROOT/path)==sha,path
    for path,sha in read(OUT/'prepared_manifest.json').items():
        assert digest(OUT/path)==sha,path
    coefficients = read(OUT/'coefficients.json')
    assert coefficients['target_source']=='data/primary/rows.parquet'
    assert coefficients['target_source_sha256']==digest(OUT/coefficients['target_source'])
    primary = pd.read_parquet(OUT/coefficients['target_source'])
    factors = coefficients['factors']['hours']
    assert len(factors)==5
    hours = primary.ts.dt.tz_convert('Asia/Seoul').dt.hour
    bounds = [(0,10),(10,12),(12,14),(14,16),(16,24)]
    for (lower,upper),item in zip(bounds,factors):
        active = (hours>=lower)&(hours<upper)&primary.p_reference.gt(0)&(primary.smp*primary.k).gt(0)
        rows = primary.loc[active]
        count = len(rows)
        days = (rows.ts.dt.tz_convert('Asia/Seoul')-pd.Timedelta(hours=1)).dt.normalize().nunique()
        weight = (rows.smp*rows.k*rows.p_reference).to_numpy()
        mass = float(weight.sum(dtype=np.float64))
        assert count==item['support_rows'] and days==item['support_days'] and mass==item['weight_mass']
        supported = count>=150 and days>=20 and mass>0
        assert item['supported']==supported
        if supported:
            ratios = (rows.y/rows.p_reference).to_numpy()
            order = np.argsort(ratios,kind='stable')
            pivot = int(np.searchsorted(np.cumsum(weight[order],dtype=np.float64),mass/2,side='left'))
            median = float(ratios[order[pivot]])
            assert median==item['raw_median'] and float(np.clip(median,.85,1.15))==item['factor']
        else:
            assert item['raw_median'] is None and item['factor']==1.
    result = read(OUT/'results.json')
    assert result['real_scalar_fit_count']==5 and not result['loaded_existing_coefficients']
    assert result['tree_fits']==0 and result['candidate_count']==1
    assert not result['confirmation_loaded'] and not result['test_loaded']
    records = []
    for fold in ('primary','recent'):
        inputs = pd.read_parquet(OUT/'data'/fold/'apply_inputs.parquet')
        assert list(inputs)==['ts','grp','p_reference','static_capacity']
        labels = pd.read_parquet(OUT/'data'/fold/'rows.parquet')
        saved = pd.read_parquet(OUT/'comparisons/hour_bias'/fold/'predictions.parquet')
        pd.testing.assert_frame_equal(saved[list(inputs)],inputs)
        pd.testing.assert_frame_equal(saved[['ts','grp','y','smp','k']],labels[['ts','grp','y','smp','k']])
        h = inputs.ts.dt.tz_convert('Asia/Seoul').dt.hour.to_numpy()
        bins = np.zeros(len(h),dtype=np.int64)
        for i,(lo,hi) in enumerate(bounds):
            bins[(h>=lo)&(h<hi)] = i
        bounded = np.array([f['factor'] for f in factors])[bins]
        effective = 1+.5*(bounded-1)
        before = inputs.p_reference.to_numpy()*effective
        prediction = np.clip(before,0,inputs.static_capacity.to_numpy())
        np.testing.assert_array_equal(saved.hour_bin,bins)
        np.testing.assert_array_equal(saved.bounded_hour_factor,bounded)
        np.testing.assert_array_equal(saved.effective_hour_factor,effective)
        np.testing.assert_array_equal(saved.before_capacity_clip,before)
        np.testing.assert_array_equal(saved.capacity_clipped,before>inputs.static_capacity.to_numpy())
        np.testing.assert_array_equal(saved.p,prediction)
        assert saved.loc[labels.night,'p'].eq(0).all()
        scores = {}
        for name in ('p','p_reference'):
            penalty = float(((saved.smp*saved.k)*(saved[name]-saved.y).abs()).sum())
            denominator = float((saved.smp*saved.k*saved.y).sum())
            revenue = float((saved.smp*saved.y).sum())
            scores[name] = {'W':penalty,'W_pct':100*penalty/denominator,'revenue':revenue,'S':revenue-.1*penalty,'rows':len(saved)}
            assert scores[name]==result['records'][0]['scores'][fold][name]
        application = read(OUT/'comparisons/hour_bias'/fold/'application.json')
        assert application['prediction_sha256']==digest(OUT/'comparisons/hour_bias'/fold/'predictions.parquet')
        assert application['coefficient_sha256']==digest(OUT/'coefficients.json')
        records.append({'fold':fold,'rows':len(saved),'full_replay_max_error':0.,'scores':scores,'strictly_improves':scores['p']['W']<scores['p_reference']['W']})
    eligible = all(r['strictly_improves'] for r in records)
    assert eligible==result['records'][0]['eligible']
    assert result['reference_retained']==(not eligible)
    assert (result['selected'] is not None)==eligible
    start = read(OUT/'evidence/run_attempt01_start.json')
    external = read(OUT/'evidence/run_attempt01_exit.json')
    internal = read(OUT/'controller_receipt.json')
    assert external['exit_code']==0 and external['has_exited'] and external['exact_worker_absent']
    assert external['native_handle_retained_before_wait']
    assert (start['pid'],start['creation_filetime'])==(external['pid'],external['creation_filetime'])
    assert internal['exit_code']==0 and internal['real_scalar_fit_count']==5 and internal['tree_fits']==0
    for resource in (internal['identity'],read(OUT/'controller_start.json')['identity']):
        assert (resource['pid'],resource['creation_filetime'])==(start['pid'],start['creation_filetime'])
        assert resource['priority_class']==32 and resource['model_threads']==16
        assert resource['pyarrow_cpu']==4 and resource['pyarrow_io']==4
        assert all(p['num_threads']==16 for p in resource['threadpools'])
    for name in ('trials','models'):
        assert not (OUT/name).exists()
    save(OUT/'evidence/terminal_audit.json',{'passed':True,'utc':now(),'invocation':'python analysis_outputs/renew_20261105/hour_wave/evidence/verify_terminal.py','scenario':'all5 saved scalar support/weighted-median arithmetic, full predictions and score/selection replay, source/input/prepared/protected hashes and resources/lifecycle','binary_observable':'all assertions passed','protected_files':len(protocol['protected_sha256']),'coefficient_count':5,'extra_fit_calls':0,'real_scalar_fits':5,'tree_fits':0,'folds':records,'eligible':eligible,'external_exit_code':0,'identity':internal['identity']})
    print('HOUR TERMINAL AUDIT PASS',flush=True)
if __name__=='__main__':
    with threadpool_limits(limits=16):
        main()
