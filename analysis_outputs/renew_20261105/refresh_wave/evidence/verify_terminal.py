# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: python analysis_outputs/renew_20261105/refresh_wave/evidence/verify_terminal.py
"""No-fit full raw-data, original-pipeline,32factor and forward-gate audit."""
import json
import os
import sys
from pathlib import Path
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key] = '16'
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'submission/score_push_renew'))
from refresh_common import OUT,RENEW,FOLDS,COLUMNS,source_paths,digest,save,now,configure,install_frozen
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- raw parquet and exact stage arithmetic
from threadpoolctl import threadpool_limits
from verify_math import verify_factors,stages

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
    original = {stage:read(OUT/f'original_{stage}_coefficients.json')['factors'] for stage in ('weather','hour','cloud')}
    capacity = read(RENEW/'final/static_capacity.json')
    cohorts = {}
    originals = {}
    source_records = []
    for source in ('primary','recent','latest'):
        paths = source_paths(source)
        p_name = 'p_reference' if source=='latest' else 'p'
        raw = pd.read_parquet(paths['raw'],columns=['ts','grp',p_name]).rename(columns={p_name:'p_reference'})
        labels = pd.read_parquet(paths['labels'],columns=['ts','grp','y','smp','k'])
        features = pd.read_parquet(paths['weather'],columns=['ts','grp','wa_temp','extra_wa_snow','wb_cloud'])
        coverage = pd.read_parquet(paths['coverage'])
        rows = pd.read_parquet(OUT/'data/sources'/source/'rows.parquet')
        projection = pd.read_parquet(OUT/'data/sources'/source/'feature_projection.parquet')
        pd.testing.assert_frame_equal(projection,features)
        pd.testing.assert_frame_equal(rows[list(raw)],raw)
        pd.testing.assert_frame_equal(rows[list(labels)],labels)
        joined = raw[['ts','grp']].merge(features,on=['ts','grp'],how='left',sort=False,validate='one_to_one',indicator=True).merge(coverage,on=['ts','grp'],how='left',sort=False,validate='one_to_one')
        pd.testing.assert_frame_equal(rows[list(features)],joined[list(features)])
        np.testing.assert_array_equal(rows.night,joined.night)
        np.testing.assert_array_equal(joined._merge.eq('left_only'),rows.night)
        assert int(joined._merge.eq('both').sum())==len(features)
        assert rows.loc[rows.night,'p_reference'].eq(0).all()
        np.testing.assert_array_equal(rows.static_capacity,rows.grp.map(capacity))
        reference = pd.read_parquet(OUT/'data/sources'/source/'frozen_references.parquet')
        replay = pd.read_parquet(OUT/'old_replay'/source/'predictions.parquet')
        pd.testing.assert_frame_equal(replay[COLUMNS],rows[COLUMNS])
        calculated = stages(rows,original)
        for stage in ('p_weather','p_hour','p_cloud'):
            prior = pd.read_parquet(paths[stage],columns=['ts','grp','p'])
            pd.testing.assert_frame_equal(rows[['ts','grp']],prior[['ts','grp']])
            np.testing.assert_array_equal(prior.p,reference[stage])
            np.testing.assert_array_equal(prior.p,replay[stage])
            np.testing.assert_array_equal(prior.p,calculated[stage])
        cohorts[source],originals[source] = rows,reference
        source_records.append({'source':source,'rows':len(rows),'raw_inputs_exact':True,'old_three_stage_full_replay_max_error':0.})
    history = pd.concat([cohorts['primary'],cohorts['recent']],ignore_index=True)
    old_receipt = read(OUT/'old_replay/receipt.json')
    assert old_receipt['passed'] and old_receipt['real_scalar_fit_count']==0
    result = read(OUT/'results.json')
    assert result['real_scalar_fit_count']==32 and result['tree_fits']==0 and not result['loaded_existing_coefficients']
    assert not result['test_loaded'] and not result['exported'] and not result['full_refit']
    count = 0
    gates = []
    fold_records = []
    previous_completed = None
    for fold,(cutoff_text,end_text) in FOLDS.items():
        cutoff,end = (pd.Timestamp(t,tz='Asia/Seoul') for t in (cutoff_text,end_text))
        source = 'recent' if fold=='late_recent' else 'latest'
        expected_train = history.loc[history.ts<=cutoff].reset_index(drop=True)
        expected_eval = cohorts[source].loc[(cohorts[source].ts>cutoff)&(cohorts[source].ts<=end)].reset_index(drop=True)
        expected_refs = originals[source].loc[(originals[source].ts>cutoff)&(originals[source].ts<=end)].reset_index(drop=True)
        directory = OUT/'data'/fold
        train = pd.read_parquet(directory/'train.parquet')
        evaluation = pd.read_parquet(directory/'evaluation.parquet')
        labels = pd.read_parquet(directory/'labels.parquet')
        references = pd.read_parquet(directory/'references.parquet')
        pd.testing.assert_frame_equal(train,expected_train)
        pd.testing.assert_frame_equal(evaluation,expected_eval[COLUMNS])
        pd.testing.assert_frame_equal(labels,expected_eval[['ts','grp','y','smp','k']])
        pd.testing.assert_frame_equal(references,expected_refs)
        assert list(evaluation)==COLUMNS
        assert len(train)==(26352 if fold=='late_recent' else 30672)
        assert len(evaluation)==(4320 if fold=='late_recent' else 4416)
        assert train.ts.max()<=cutoff<evaluation.ts.min()
        assert not train[['ts','grp']].merge(evaluation[['ts','grp']],on=['ts','grp']).shape[0]
        coefficient_path = OUT/'coefficients'/f'{fold}.json'
        record = read(coefficient_path)
        assert record['train_source_sha256']==digest(directory/'train.parquet')
        assert record['fit_scalar_count']==16
        assert record['original_replay_receipt_sha256']==digest(OUT/'old_replay/receipt.json')
        assert pd.Timestamp(record['fit_started_utc'])>=pd.Timestamp(old_receipt['utc'])
        if previous_completed is not None:
            assert pd.Timestamp(record['fit_started_utc'])>=previous_completed
        previous_completed = pd.Timestamp(record['fit_completed_utc'])
        count += verify_factors(train,record['factors'])
        saved_training = pd.read_parquet(OUT/'training_stages'/f'{fold}.parquet')
        pd.testing.assert_frame_equal(saved_training[COLUMNS],train[COLUMNS])
        for name,values in stages(train,record['factors']).items():
            np.testing.assert_array_equal(saved_training[name],values)
        prediction_path = OUT/'comparisons'/fold/'predictions.parquet'
        prediction = pd.read_parquet(prediction_path)
        pd.testing.assert_frame_equal(prediction[COLUMNS],evaluation)
        pd.testing.assert_frame_equal(prediction[['ts','grp','y','smp','k']],labels)
        for name,values in stages(evaluation,record['factors']).items():
            np.testing.assert_array_equal(prediction[name],values)
        for stage in ('weather','hour','cloud'):
            np.testing.assert_array_equal(prediction['frozen_'+stage],references['p_'+stage])
        scores = {}
        for name in ('p','frozen_weather','frozen_hour','frozen_cloud'):
            weight = prediction.smp*prediction.k
            w = float((weight*(prediction[name]-prediction.y).abs()).sum())
            revenue = float((prediction.smp*prediction.y).sum())
            scores[name] = {'W':w,'W_pct':100*w/float((weight*prediction.y).sum()),'revenue':revenue,'S':revenue-.1*w,'rows':len(prediction)}
            assert scores[name]==result['records'][0]['scores'][fold][name]
        for reference in ('frozen_weather','frozen_hour','frozen_cloud'):
            gates.append({'fold':fold,'reference':reference,'new_W':scores['p']['W'],'reference_W':scores[reference]['W'],'strictly_improves':scores['p']['W']<scores[reference]['W']})
        application = read(OUT/'comparisons'/fold/'application.json')
        assert application['coefficient_sha256']==digest(coefficient_path)
        assert application['prediction_sha256']==digest(prediction_path)
        assert application['train_stages_sha256']==digest(OUT/'training_stages'/f'{fold}.parquet')
        fold_records.append({'fold':fold,'train_rows':len(train),'evaluation_rows':len(evaluation),'scalar_records_verified':16,'train_all_stage_error':0.,'evaluation_all_stage_error':0.,'cutoff_and_no_leakage_passed':True,'scores':scores})
    assert count==32 and len(gates)==6
    assert gates==result['gate_comparisons']==result['records'][0]['gate_comparisons']
    eligible = all(row['strictly_improves'] for row in gates)
    assert eligible==result['eligible']==result['records'][0]['eligible']
    assert result['reference_retained']==(not eligible) and (result['selected'] is not None)==eligible
    start = read(OUT/'evidence/run_attempt01_start.json')
    external = read(OUT/'evidence/run_attempt01_exit.json')
    assert external['exit_code']==0 and external['has_exited'] and external['exact_worker_absent']
    assert external['native_handle_retained_before_wait']
    assert (start['pid'],start['creation_filetime'])==(external['pid'],external['creation_filetime'])
    for name in ('controller_start.json','controller_receipt.json'):
        receipt = read(OUT/name)
        r = receipt['identity']
        assert (r['pid'],r['creation_filetime'])==(start['pid'],start['creation_filetime'])
        assert r['priority_class']==32 and r['model_threads']==16 and r['parallel_fits']==1
        assert r['pyarrow_cpu']==4 and r['pyarrow_io']==4
        assert all(pool['num_threads']==16 for pool in r['threadpools'])
    assert read(OUT/'controller_receipt.json')['real_scalar_fit_count']==32
    assert read(OUT/'evidence/selfchecks.json')['passed']
    save(OUT/'evidence/terminal_audit.json',{'passed':True,'utc':now(),'invocation':'python analysis_outputs/renew_20261105/refresh_wave/evidence/verify_terminal.py','scenario':'all3rawcohorts/originalstages,32scalarrecords includingunusedsnow,alltraining/evaluationstages,6strictcomparisons,chronologicalisolation,hashes/resources/lifecycle','binary_observable':'all assertions passed','protected_files':len(protocol['protected_sha256']),'sources':source_records,'folds':fold_records,'gate_comparisons':gates,'eligible':eligible,'real_scalar_fits':32,'tree_fits':0,'extra_fit_calls':0,'external_exit_code':0})
    print('REFRESH TERMINAL AUDIT PASS',flush=True)
if __name__=='__main__':
    with threadpool_limits(limits=16):
        main()
