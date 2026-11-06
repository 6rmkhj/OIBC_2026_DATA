# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: python analysis_outputs/renew_20261105/sky_wave/evidence/verify_terminal.py
"""Full read-only raw-input, scalar arithmetic, prediction and lifecycle audit."""
import json
import os
import sys
from pathlib import Path
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name] = '16'
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'submission/score_push_renew'))
from sky_common import OUT,DATA,RENEW,REFERENCE_DIR,digest,save,now,configure,install_frozen
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact raw parquet/weighted-median contracts
from threadpoolctl import threadpool_limits

def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def bins_for(values: np.ndarray) -> np.ndarray:
    bins = np.full(len(values),-1,dtype=np.int64)
    finite = np.isfinite(values)
    bins[finite&(values<20)] = 0
    bins[finite&(values>=20)&(values<50)] = 1
    bins[finite&(values>=50)&(values<80)] = 2
    bins[finite&(values>=80)] = 3
    return bins

def main() -> None:
    configure()
    install_frozen()
    protocol = read(OUT/'protocol.json')
    for path,sha in protocol['protected_sha256'].items():
        assert digest(ROOT/path)==sha,path
    for path,sha in read(OUT/'prepared_manifest.json').items():
        assert digest(OUT/path)==sha,path
    coefficient = read(OUT/'coefficients.json')
    assert coefficient['target_source']=='data/primary/rows.parquet'
    assert coefficient['target_source_sha256']==digest(OUT/coefficient['target_source'])
    primary = pd.read_parquet(OUT/coefficient['target_source'])
    factors = coefficient['factors']['clouds']
    assert len(factors)==4
    bins = bins_for(primary.wb_cloud.to_numpy())
    for index,item in enumerate(factors):
        active = (bins==index)&primary.p_reference.gt(0)&(primary.smp*primary.k).gt(0)
        rows = primary.loc[active]
        count = len(rows)
        days = (rows.ts.dt.tz_convert('Asia/Seoul')-pd.Timedelta(hours=1)).dt.normalize().nunique()
        weights = (rows.smp*rows.k*rows.p_reference).to_numpy()
        mass = float(weights.sum(dtype=np.float64))
        assert count==item['support_rows'] and days==item['support_days'] and mass==item['weight_mass']
        supported = count>=150 and days>=20 and mass>0
        assert item['supported']==supported
        if supported:
            ratios = (rows.y/rows.p_reference).to_numpy()
            order = np.argsort(ratios,kind='stable')
            pivot = int(np.searchsorted(np.cumsum(weights[order],dtype=np.float64),mass/2,side='left'))
            median = float(ratios[order[pivot]])
            assert median==item['raw_median'] and float(np.clip(median,.85,1.15))==item['factor']
        else:
            assert item['raw_median'] is None and item['factor']==1.
    result = read(OUT/'results.json')
    assert result['real_scalar_fit_count']==4 and not result['loaded_existing_coefficients']
    assert result['tree_fits']==0 and result['candidate_count']==1
    assert not result['confirmation_loaded'] and not result['test_loaded'] and not result['exported']
    capacity = read(RENEW/'final/static_capacity.json')
    records = []
    for fold in ('primary','recent'):
        rows = pd.read_parquet(OUT/'data'/fold/'rows.parquet')
        inputs = pd.read_parquet(OUT/'data'/fold/'apply_inputs.parquet')
        raw = pd.read_parquet(DATA/fold/'evaluation.parquet',columns=['ts','grp','wb_cloud'])
        projection = pd.read_parquet(OUT/'data'/fold/'feature_projection.parquet')
        pd.testing.assert_frame_equal(raw,projection)
        reference = pd.read_parquet(REFERENCE_DIR/fold/'predictions.parquet',columns=['ts','grp','y','smp','k','p','static_capacity']).rename(columns={'p':'p_reference'})
        pd.testing.assert_frame_equal(rows[list(reference)],reference)
        joined = reference[['ts','grp']].merge(raw,on=['ts','grp'],how='left',sort=False,validate='one_to_one',indicator=True)
        np.testing.assert_array_equal(rows.wb_cloud,joined.wb_cloud)
        night = pd.read_parquet(RENEW/'recency_wave/data'/fold/'night_coverage.parquet')
        night = reference[['ts','grp']].merge(night,on=['ts','grp'],how='left',sort=False,validate='one_to_one')
        np.testing.assert_array_equal(rows.night,night.night)
        np.testing.assert_array_equal(joined._merge.eq('left_only'),night.night)
        assert int(joined._merge.eq('both').sum())==len(raw)
        assert list(inputs)==['ts','grp','p_reference','wb_cloud','static_capacity']
        pd.testing.assert_frame_equal(inputs,rows[list(inputs)])
        np.testing.assert_array_equal(rows.static_capacity,rows.grp.map(capacity))
        saved_path = OUT/'comparisons/cloud_bias'/fold/'predictions.parquet'
        saved = pd.read_parquet(saved_path)
        pd.testing.assert_frame_equal(saved[list(inputs)],inputs)
        pd.testing.assert_frame_equal(saved[['ts','grp','y','smp','k']],rows[['ts','grp','y','smp','k']])
        bins = bins_for(inputs.wb_cloud.to_numpy())
        bounded = np.ones(len(inputs))
        for i,factor in enumerate(factors):
            bounded[bins==i] = factor['factor']
        effective = 1+.5*(bounded-1)
        before = inputs.p_reference.to_numpy()*effective
        prediction = np.clip(before,0,inputs.static_capacity.to_numpy())
        np.testing.assert_array_equal(saved.cloud_bin,bins)
        np.testing.assert_array_equal(saved.bounded_cloud_factor,bounded)
        np.testing.assert_array_equal(saved.effective_cloud_factor,effective)
        np.testing.assert_array_equal(saved.before_capacity_clip,before)
        np.testing.assert_array_equal(saved.capacity_clipped,before>inputs.static_capacity.to_numpy())
        np.testing.assert_array_equal(saved.p,prediction)
        assert saved.loc[rows.night,'p'].eq(0).all()
        over = np.isfinite(inputs.wb_cloud)&inputs.wb_cloud.gt(100)
        assert int(over.sum())==(55 if fold=='primary' else 2)
        assert saved.loc[over,'cloud_bin'].eq(3).all()
        scores = {}
        for name in ('p','p_reference'):
            weight = saved.smp*saved.k
            w = float((weight*(saved[name]-saved.y).abs()).sum())
            revenue = float((saved.smp*saved.y).sum())
            scores[name] = {'W':w,'W_pct':100*w/float((weight*saved.y).sum()),'revenue':revenue,'S':revenue-.1*w,'rows':len(saved)}
            assert scores[name]==result['records'][0]['scores'][fold][name]
        application = read(OUT/'comparisons/cloud_bias'/fold/'application.json')
        assert application['prediction_sha256']==digest(saved_path)
        assert application['coefficient_sha256']==digest(OUT/'coefficients.json')
        records.append({'fold':fold,'rows':len(saved),'raw_projection_exact':True,'full_formula_max_error':0.,'finite_gt100_retained':int(over.sum()),'nonfinite_identity':int((bins<0).sum()),'scores':scores,'strictly_improves':scores['p']['W']<scores['p_reference']['W']})
    eligible = all(r['strictly_improves'] for r in records)
    assert eligible==result['records'][0]['eligible']
    assert result['reference_retained']==(not eligible)
    assert (result['selected'] is not None)==eligible
    external = read(OUT/'evidence/run_attempt01_exit.json')
    start = read(OUT/'evidence/run_attempt01_start.json')
    assert external['exit_code']==0 and external['has_exited'] and external['exact_worker_absent']
    assert external['native_handle_retained_before_wait']
    assert (start['pid'],start['creation_filetime'])==(external['pid'],external['creation_filetime'])
    for name in ('controller_start.json','controller_receipt.json'):
        receipt = read(OUT/name)
        r = receipt['identity']
        assert (r['pid'],r['creation_filetime'])==(start['pid'],start['creation_filetime'])
        assert r['priority_class']==32 and r['model_threads']==16
        assert r['pyarrow_cpu']==4 and r['pyarrow_io']==4
        assert all(pool['num_threads']==16 for pool in r['threadpools'])
    assert read(OUT/'controller_receipt.json')['real_scalar_fit_count']==4
    assert read(OUT/'evidence/selfchecks.json')['passed']
    save(OUT/'evidence/terminal_audit.json',{'passed':True,'utc':now(),'invocation':'python analysis_outputs/renew_20261105/sky_wave/evidence/verify_terminal.py','scenario':'all raw projections/reference/night/capacity,4factor arithmetic,30672predictions/metrics/gate,source/input/protected hashes and lifecycle/resources','binary_observable':'all assertions passed','protected_files':len(protocol['protected_sha256']),'folds':records,'eligible':eligible,'real_scalar_fits':4,'tree_fits':0,'extra_fit_calls':0,'external_exit_code':0})
    print('SKY TERMINAL AUDIT PASS',flush=True)
if __name__=='__main__':
    with threadpool_limits(limits=16):
        main()
