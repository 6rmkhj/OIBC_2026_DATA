# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: python analysis_outputs/renew_20261105/incbound_wave/evidence/verify_terminal.py
"""Saved-output audit of one fixed replacement; no additional model inference."""
import json
import os
import sys
from pathlib import Path
sys.dont_write_bytecode = True
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key] = '16'
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'submission/score_push_renew'))
from incbound_common import OUT,MODELS,FOLDS,digest,save,now,configure,install_frozen,check_prepared
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact historical stored groupmean and scoring contract
from threadpoolctl import threadpool_limits

def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

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
    external = read(OUT/'evidence/run_attempt01_exit.json')
    assert external['exit_code']==0 and external['has_exited'] and external['native_handle_retained_before_wait']
    assert (external['pid'],external['creation_filetime']) in terminal_ids
    originals = {stage:read(OUT/f'original_{stage}_coefficients.json')['factors'] for stage in ('weather','hour','cloud')}
    weight = read(OUT/'lineage.json')['effective_mlp_weight']
    assert weight==(1-.07794876465304705)*(1-.2808471620447986)*.2000267325223772
    results = read(OUT/'results.json')
    assert len(results['records'])==1
    record = results['records'][0]
    assert record['effective_mlp_weight']==weight
    trials = []
    fold_receipts = []
    for fold in FOLDS:
        data = OUT/'data'/fold
        lineage = pd.read_parquet(data/'lineage.parquet')
        inputs = pd.read_parquet(data/'application_inputs.parquet')
        labels = pd.read_parquet(data/'labels.parquet')
        keys = lineage[['ts','grp']].merge(pd.read_parquet(data/'coverage.parquet'),on=['ts','grp'],sort=False,validate='one_to_one')
        inverse = pd.read_parquet(data/'evaluation_transform.parquet')
        old_matrix = np.load(data/'x_evaluation_original.npy',allow_pickle=False)
        bounded_matrix = np.load(data/'x_evaluation_bounded.npy',allow_pickle=False)
        unchanged = np.all(old_matrix==bounded_matrix,axis=1)
        old_raws,bounded_raws = [],[]
        for seed in (0,1,2):
            directory = OUT/'trials'/fold/f'seed{seed}'
            source = MODELS/fold/'mlp_cf'/f'seed{seed}'
            config = read(directory/'config.json')
            assert ROOT/config['source_model']==source/'model.joblib'
            for key,name in (('source_model_sha256','model.joblib'),('source_preprocessor_sha256','input_preprocessing.joblib'),('source_target_scaler_sha256','target_scaler.joblib'),('source_config_sha256','config.json')):
                assert config[key]==digest(source/name)
            assert config['original_matrix_sha256']==digest(data/'x_evaluation_original.npy')
            assert config['bounded_matrix_sha256']==digest(data/'x_evaluation_bounded.npy')
            assert config['capacity_inverse_sha256']==digest(data/'evaluation_transform.parquet')
            assert config['prepared_manifest_sha256']==digest(OUT/'prepared_manifest.json')
            assert config['native_model_inferences']==2 and config['new_model_fits']==0 and config['historical_inference_blas_threads']==1
            stored = pd.read_parquet(source/'daylight_raw.parquet')
            old = pd.read_parquet(directory/'original_raw.parquet')
            bounded = pd.read_parquet(directory/'bounded_raw.parquet')
            for raw in (stored,old,bounded):
                pd.testing.assert_frame_equal(raw[['ts','grp']],inverse[['ts','grp']])
                assert np.isfinite(raw.p_raw).all()
                full = keys.merge(raw,on=['ts','grp'],how='left',sort=False,validate='one_to_one')
                assert full.p_raw.isna().eq(full.night).all() and int(full.p_raw.notna().sum())==len(raw)
            assert np.array_equal(stored.p_raw.to_numpy().view(np.uint64),old.p_raw.to_numpy().view(np.uint64))
            assert np.array_equal(old.p_raw.to_numpy()[unchanged].view(np.uint64),bounded.p_raw.to_numpy()[unchanged].view(np.uint64))
            old_raws.append(old)
            bounded_raws.append(bounded)
            status,runtime,proof,receipt = [read(directory/name) for name in ('worker_status.json','runtime.json','replay.json','controller_receipt.json')]
            assert status['state']=='complete' and proof['original_full_exact'] and proof['original_max_absolute_error']==0 and proof['inverse_scaler_once_then_capacity']
            for item in (config,status,runtime,proof,receipt):
                assert item['new_model_fits']==0 and item['native_model_inferences']==2
            for item in (status,proof):
                assert item['source_model_sha256']==digest(source/'model.joblib')
                assert item['original_raw_sha256']==digest(directory/'original_raw.parquet') and item['bounded_raw_sha256']==digest(directory/'bounded_raw.parquet')
            assert proof['source_original_raw_sha256']==digest(source/'daylight_raw.parquet')
            assert receipt['exit_code']==0 and receipt['exact_worker_absent']
            identity = receipt['identity']
            assert (identity['pid'],identity['creation_filetime']) in terminal_ids
            for item in (runtime,status['identity']):
                assert (item['pid'],item['creation_filetime'])==(identity['pid'],identity['creation_filetime'])
                assert item['priority_class']==32 and item['parallel_fits']==1 and item['model_threads']==16
                assert item['pyarrow_cpu']==item['pyarrow_io']==4
                assert all(p['num_threads']==1 if p['user_api']=='blas' else 1<=p['num_threads']<=16 for p in item['threadpools'])
            assert runtime['historical_inference_blas_threads']==1
            creation = pd.Timestamp((identity['creation_filetime']-116444736000000000)*100,tz='UTC')
            trials.append({'fold':fold,'seed':seed,'identity':identity,'creation_utc':creation.isoformat(),'finished_utc':receipt['finished_utc'],'seconds':runtime['seconds'],'original_full_bitwise_exact':True,'rows':len(old),'native_model_inferences':2,'model_fits':0})
        frame = pd.read_parquet(OUT/'comparisons'/fold/'predictions.parquet')
        pd.testing.assert_frame_equal(frame[labels.columns],labels)
        pd.testing.assert_frame_equal(frame[inputs.columns],inputs)
        means = []
        for raws in (old_raws,bounded_raws):
            mean = pd.concat(raws).groupby(['ts','grp'],as_index=False).p_raw.mean()
            full = keys[['ts','grp']].merge(mean,on=['ts','grp'],how='left',sort=False,validate='one_to_one')
            means.append(np.maximum(full.p_raw.fillna(0.).to_numpy(),0.))
        old_mean,bounded_mean = means
        np.testing.assert_array_equal(old_mean,lineage.p_old_mlp)
        np.testing.assert_array_equal(frame.p_old_mlp,old_mean)
        np.testing.assert_array_equal(frame.p_bounded_mlp,bounded_mean)
        delta = bounded_mean-lineage.p_old_mlp.to_numpy()
        np.testing.assert_array_equal(frame.mlp_delta,delta)
        np.testing.assert_array_equal(frame.p_raw_temporal,lineage.p_raw_temporal)
        candidate = lineage.p_raw_temporal.to_numpy().copy()
        active = delta!=0.
        candidate[active] += weight*delta[active]
        assert np.array_equal(frame.p_raw_candidate.to_numpy().view(np.uint64),candidate.view(np.uint64))
        assert np.array_equal(candidate[~active].view(np.uint64),lineage.p_raw_temporal.to_numpy()[~active].view(np.uint64))
        temperature = inputs.wa_temp.to_numpy()
        finite = np.isfinite(temperature)
        bins = np.full(len(temperature),-1,dtype=np.int64)
        bins[finite] = np.select([temperature[finite]<0,temperature[finite]<10,temperature[finite]<20,temperature[finite]<30],[0,1,2,3],default=4)
        tf = np.array([1.,*[f['factor'] for f in originals['weather']['temperature']]])[bins+1]
        snow = np.isfinite(inputs.extra_wa_snow)&inputs.extra_wa_snow.ge(.001)
        wf = 1+.5*(np.clip(tf*np.where(snow,originals['weather']['conditional_snow']['factor'],1.),.85,1.15)-1)
        hours = inputs.ts.dt.tz_convert('Asia/Seoul').dt.hour.to_numpy()
        hb = np.select([hours<10,hours<12,hours<14,hours<16],[0,1,2,3],default=4)
        hf = 1+.5*(np.array([f['factor'] for f in originals['hour']['hours']])[hb]-1)
        clouds = inputs.wb_cloud.to_numpy()
        finite = np.isfinite(clouds)
        cb = np.full(len(clouds),-1,dtype=np.int64)
        cb[finite] = np.select([clouds[finite]<20,clouds[finite]<50,clouds[finite]<80],[0,1,2],default=3)
        cf = 1+.5*(np.array([1.,*[f['factor'] for f in originals['cloud']['clouds']]])[cb+1]-1)
        capacity = inputs.static_capacity.to_numpy()
        for raw,expected in ((lineage.p_raw_temporal.to_numpy(),lineage[['p_weather_reference','p_hour_reference','p_sky_reference']]),(candidate,frame[['p_weather','p_hour','p']])):
            weather = np.maximum(0,np.minimum(capacity,raw*wf))
            hour = np.maximum(0,np.minimum(capacity,weather*hf))
            final = np.maximum(0,np.minimum(capacity,hour*cf))
            for actual,column in zip((weather,hour,final),expected.columns):
                np.testing.assert_array_equal(actual,expected[column])
        assert frame.loc[keys.night,'p'].eq(0).all()
        cost = frame.smp*frame.k
        revenue = float((frame.smp*frame.y).sum())
        denominator = float((cost*frame.y).sum())
        for name in ('p','p_reference'):
            w = float((cost*(frame[name]-frame.y).abs()).sum())
            assert record['scores'][fold][name]=={'W':w,'W_pct':100*w/denominator,'revenue':revenue,'S':revenue-.1*w,'rows':len(frame)}
        fold_receipts.append({'fold':fold,'changed_mlp_rows':int(active.sum()),'changed_final_rows':int(frame.p.ne(frame.p_reference).sum()),'zero_delta_raw_bits_preserved':True,'original_and_candidate_all_stages_exact':True,'all_metrics_exact':True})
    for previous,current in zip(trials,trials[1:]):
        assert pd.Timestamp(previous['finished_utc'])<=pd.Timestamp(current['creation_utc'])
    both = all(record['scores'][f]['p']['W']<record['scores'][f]['p_reference']['W'] for f in FOLDS)
    assert record['both_folds_improve']==record['eligible']==results['eligible']==both
    assert results['selected']==(record if both else None) and results['reference_retained']==(not both)
    for name,value in {'real_model_fit_count':0,'native_worker_count':6,'native_model_inferences':12,'real_calibration_fit_count':0,'new_weight_fits':0,'new_alpha_fits':0,'candidate_count':1,'confirmation_loaded':False,'test_loaded':False,'exported':False}.items():
        assert results[name]==value
    controller = read(OUT/'controller_receipt.json')
    assert controller['exit_code']==0 and controller['native_model_inferences']==12 and controller['real_model_fit_count']==0
    identity = controller['identity']
    assert identity['priority_class']==32 and identity['pyarrow_cpu']==identity['pyarrow_io']==4
    assert all(1<=p['num_threads']<=16 for p in identity['threadpools'])
    save(OUT/'evidence/terminal_audit.json',{'passed':True,'utc':now(),'trials':trials,'folds':fold_receipts,'saved_original_raw_full_bitwise_matches':6,'serial_intervals_nonoverlap':True,'protected_files':len(protocol['protected_sha256']),'protected_hashes_unchanged':True,'native_identity_count':len(terminal_ids),'worker_blas_threads':1,'worker_other_pool_max_threads':16,'controller_terminal_pool_threads':[p['num_threads'] for p in identity['threadpools']],'record':record,'additional_model_inferences_in_audit':0,'production_native_model_inferences':12,'real_model_fit_count':0})
    print('INCBOUND TERMINAL AUDIT PASS',flush=True)

if __name__=='__main__':
    with threadpool_limits(limits=16):
        main()
