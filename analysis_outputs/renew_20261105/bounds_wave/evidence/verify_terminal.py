# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "scikit-learn", "joblib", "threadpoolctl"]
# ///
# How to run: python analysis_outputs/renew_20261105/bounds_wave/evidence/verify_terminal.py
"""Exact TRAIN-bound identity, immutable-model replay and primary gate audit."""
import json
import os
import sys
from pathlib import Path
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key] = '16'
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'submission/score_push_renew'))
from bound_common import OUT,MLP,FOLDS,digest,save,now,configure,install_frozen,check_prepared
import joblib
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- immutable inverse/key/scoring contracts
from threadpoolctl import threadpool_limits,threadpool_info
from verify_scoring import component,primary_alpha,metrics

def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def resources(record: dict, exact: bool = True) -> None:
    assert record['priority_class']==32 and record['model_threads']==16 and record['parallel_fits']==1
    assert record['pyarrow_cpu']==4 and record['pyarrow_io']==4
    if exact:
        assert all(p['num_threads']==16 for p in record['threadpools'])
    else:
        assert all(1<=p['num_threads']<=16 for p in record['threadpools'])

def main() -> None:
    configure()
    install_frozen()
    check_prepared()
    protocol = read(OUT/'protocol.json')
    for path,sha in protocol['protected_sha256'].items():
        assert digest(ROOT/path)==sha,path
    native = read(OUT/'evidence/native_terminal_identities.json')
    assert native['passed'] and len(native['records'])==7
    terminal_ids = {(r['pid'],r['creation_filetime']) for r in native['records'] if r['exact_absent']}
    start = read(OUT/'evidence/run_attempt01_start.json')
    external = read(OUT/'evidence/run_attempt01_exit.json')
    assert external['exit_code']==0 and external['has_exited'] and external['native_handle_retained_before_wait']
    assert (external['pid'],external['creation_filetime'])==(start['pid'],start['creation_filetime'])
    assert (start['pid'],start['creation_filetime']) in terminal_ids
    assert not list(OUT.rglob('model.joblib'))
    originals = {stage:read(OUT/f'original_{stage}_coefficients.json')['factors'] for stage in ('weather','hour','cloud')}
    frames = {}
    bounds_records = []
    trials = []
    for fold in FOLDS:
        source = MLP/'data'/fold
        data = OUT/'data'/fold
        train = np.load(source/'x_train.npy',mmap_mode='r',allow_pickle=False)
        future = np.load(source/'x_evaluation.npy',mmap_mode='r',allow_pickle=False)
        names = read(source/'feature_mask.json')['selected_columns']
        lower,upper = np.min(train,axis=0),np.max(train,axis=0)
        assert np.array_equal(np.clip(train,lower,upper).view(np.uint64),train.view(np.uint64))
        table = pd.read_parquet(data/'bounds.parquet')
        assert table.feature.tolist()==names and table.feature_index.tolist()==list(range(len(names)))
        np.testing.assert_array_equal(table.lower,lower)
        np.testing.assert_array_equal(table.upper,upper)
        below,above = future<lower,future>upper
        np.testing.assert_array_equal(table.below_count,below.sum(axis=0))
        np.testing.assert_array_equal(table.above_count,above.sum(axis=0))
        np.testing.assert_array_equal(table.clipped_count,(below|above).sum(axis=0))
        matrix = np.load(data/'x_evaluation_bounded.npy',allow_pickle=False)
        assert matrix.dtype==np.dtype('float64') and matrix.shape==future.shape
        np.testing.assert_array_equal(matrix,np.clip(future,lower,upper))
        assert np.array_equal(matrix[~(below|above)],future[~(below|above)])
        receipt = read(data/'bounds_receipt.json')
        assert receipt['train_identity_exact'] and receipt['train_identity_bitwise'] and not receipt['bounds_read_labels']
        assert receipt['changed_rows']==int((below|above).any(axis=1).sum())
        assert receipt['changed_entries']==int((below|above).sum())
        assert receipt['source_train_sha256']==digest(source/'x_train.npy')
        assert receipt['source_evaluation_sha256']==digest(source/'x_evaluation.npy')
        assert receipt['bounded_matrix_sha256']==digest(data/'x_evaluation_bounded.npy')
        assert receipt['bounds_sha256']==digest(data/'bounds.parquet')
        for name in ('labels.parquet','coverage.parquet','application_inputs.parquet'):
            assert digest(data/name)==digest(source/name)
        bounds_records.append({'fold':fold,'train_rows':len(train),'evaluation_rows':len(future),'features':len(names),'train_clip_bit_identity':True,'full_bounded_matrix_exact':True,'changed_rows':receipt['changed_rows'],'changed_entries':receipt['changed_entries']})
        del train,future,below,above
        scaler = joblib.load(source/'target_scaler.joblib')
        inverse = pd.read_parquet(source/'evaluation_transform.parquet')
        inputs = pd.read_parquet(data/'application_inputs.parquet')
        labels = pd.read_parquet(data/'labels.parquet')
        coverage = pd.read_parquet(data/'coverage.parquet')
        keys = inputs[['ts','grp']].merge(coverage,on=['ts','grp'],sort=False,validate='one_to_one')
        seeds = []
        for seed in (0,1,2):
            directory = OUT/'trials'/fold/f'seed{seed}'
            source_model = MLP/'trials'/fold/f'seed{seed}'/'model.joblib'
            config = read(directory/'config.json')
            assert ROOT/config['source_model']==source_model
            assert config['source_model_sha256']==digest(source_model)
            assert config['bounded_matrix_sha256']==digest(data/'x_evaluation_bounded.npy')
            assert config['target_scaler_sha256']==digest(source/'target_scaler.joblib')
            assert config['inverse_sha256']==digest(source/'evaluation_transform.parquet')
            assert config['new_model_fits']==0 and config['native_inferences']==1
            model = joblib.load(source_model)
            with threadpool_limits(limits=16):
                assert all(p['num_threads']==16 for p in threadpool_info())
                predicted_scaled = model.predict(matrix)
                replay = scaler.inverse_transform(predicted_scaled.reshape(-1,1)).ravel()*inverse.inverse_kwh.to_numpy()
            raw = pd.read_parquet(directory/'daylight_raw.parquet')
            pd.testing.assert_frame_equal(raw[['ts','grp']],inverse[['ts','grp']])
            np.testing.assert_array_equal(raw.p_raw,replay)
            full = keys.merge(raw,on=['ts','grp'],how='left',sort=False,validate='one_to_one')
            assert full.p_raw.isna().eq(full.night).all()
            assert int(full.p_raw.notna().sum())==len(raw)
            seeds.append(full.p_raw.fillna(0.).to_numpy())
            status = read(directory/'worker_status.json')
            runtime = read(directory/'runtime.json')
            proof = read(directory/'replay.json')
            controller = read(directory/'controller_receipt.json')
            assert status['state']=='complete' and status['new_model_fits']==0
            for record in (status,proof):
                assert record['source_model_sha256']==digest(source_model)
                assert record['raw_sha256']==digest(directory/'daylight_raw.parquet')
            assert proof['passed'] and proof['max_absolute_error']==0 and proof['inverse_target_scaler_once']
            assert controller['exit_code']==0 and controller['exact_worker_absent'] and controller['new_model_fits']==0
            assert runtime['new_model_fits']==0
            resources(runtime)
            resources(status['identity'])
            identity = controller['identity']
            for record in (runtime,status['identity']):
                assert (record['pid'],record['creation_filetime'])==(identity['pid'],identity['creation_filetime'])
            assert (identity['pid'],identity['creation_filetime']) in terminal_ids
            creation = pd.Timestamp((identity['creation_filetime']-116444736000000000)*100,tz='UTC')
            trials.append({'fold':fold,'seed':seed,'identity':identity,'creation_utc':creation.isoformat(),'finished_utc':controller['finished_utc'],'seconds':runtime['seconds'],'warnings':runtime['warnings'],'rows':len(raw),'full_replay_max_absolute_error':0.0})
        frame = pd.read_parquet(OUT/'comparisons'/fold/'predictions.parquet')
        pd.testing.assert_frame_equal(frame[labels.columns],labels)
        pd.testing.assert_frame_equal(frame[inputs.columns],inputs)
        for name,expected in component(inputs,np.asarray(seeds),originals).items():
            np.testing.assert_array_equal(frame[name],expected)
        assert (frame.loc[keys.night,'p_new']==0).all()
        assert (frame.loc[keys.night,'p']==0).all()
        frames[fold] = frame
    for previous,current in zip(trials,trials[1:]):
        assert pd.Timestamp(previous['finished_utc'])<=pd.Timestamp(current['creation_utc'])
    results = read(OUT/'results.json')
    record = results['records'][0]
    alpha = primary_alpha(frames['primary'])
    assert alpha==record['alpha_primary_only']
    for fold,frame in frames.items():
        assert (frame.alpha==alpha).all()
        np.testing.assert_array_equal(frame.p,(1-alpha)*frame.p_reference+alpha*frame.p_new)
        for name in ('p','p_reference','p_new'):
            assert metrics(frame,name)==record['scores'][fold][name]
    both = all(record['scores'][fold]['p']['W']<record['scores'][fold]['p_reference']['W'] for fold in FOLDS)
    eligible = both and alpha>=.02
    assert record['both_folds_improve']==both and record['eligible']==eligible
    assert results['eligible']==eligible and results['reference_retained']==(not eligible)
    assert not eligible and results['selected'] is None
    for name,value in {'real_model_fit_count':0,'real_inference_count':6,'bounds_transform_count':2,'real_calibration_fit_count':0,'candidate_count':1,'confirmation_loaded':False,'test_loaded':False,'exported':False}.items():
        assert results[name]==value
    controller = read(OUT/'controller_receipt.json')
    assert controller['exit_code']==0 and controller['real_model_fit_count']==0 and controller['real_inference_count']==6 and controller['bounds_transform_count']==2
    resources(controller['identity'],exact=False)
    save(OUT/'evidence/terminal_audit.json',{'passed':True,'utc':now(),'bounds':bounds_records,'trials':trials,'serial_intervals_nonoverlap':True,'full_stage_and_metric_equality':True,'protected_file_count':len(protocol['protected_sha256']),'protected_hashes_unchanged':True,'native_identity_count':len(terminal_ids),'worker_pools_exactly_16':True,'controller_terminal_pool_threads':[p['num_threads'] for p in controller['identity']['threadpools']],'alpha':alpha,'eligible':eligible,'scores':record['scores'],'new_model_fits':0,'real_inferences':6,'bounds_transforms':2})
    print('BOUNDS TERMINAL AUDIT PASS',flush=True)

if __name__=='__main__':
    with threadpool_limits(limits=16):
        main()
