# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "scikit-learn", "joblib", "threadpoolctl"]
# ///
# How to run: python analysis_outputs/renew_20261105/mlp_wave/evidence/verify_terminal.py
"""Full saved-model replay, signed ensemble, primary alpha and process audit."""
import json
import os
import sys
from pathlib import Path
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key] = '16'
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'submission/score_push_renew'))
from mlp_common import OUT,FOLDS,PARAMS,digest,save,now,configure,install_frozen,require_release
import joblib
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- full frozen prediction and scoring contract
from threadpoolctl import threadpool_limits
from verify_scoring import component,primary_alpha,metrics

def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def check_resources(record: dict) -> None:
    assert record['priority_class']==32 and record['model_threads']==16 and record['parallel_fits']==1
    assert record['pyarrow_cpu']==4 and record['pyarrow_io']==4
    assert all(pool['num_threads']==16 for pool in record['threadpools'])

def main() -> None:
    configure()
    install_frozen()
    require_release()
    protocol = read(OUT/'protocol.json')
    for path,sha in protocol['protected_sha256'].items():
        assert digest(ROOT/path)==sha,path
    terminal = read(OUT/'evidence/native_terminal_identities.json')
    assert terminal['passed'] and len(terminal['records'])==7
    terminal_ids = {(r['pid'],r['creation_filetime']) for r in terminal['records'] if r['exact_absent']}
    start = read(OUT/'evidence/run_attempt01_start.json')
    external = read(OUT/'evidence/run_attempt01_exit.json')
    assert external['exit_code']==0 and external['has_exited'] and external['native_handle_retained_before_wait']
    assert (start['pid'],start['creation_filetime']) in terminal_ids
    assert (external['pid'],external['creation_filetime'])==(start['pid'],start['creation_filetime'])
    originals = {stage:read(OUT/f'original_{stage}_coefficients.json')['factors'] for stage in ('weather','hour','cloud')}
    models = list((OUT/'trials').rglob('model.joblib'))
    assert len(models)==6
    frames = {}
    trials = []
    for fold in FOLDS:
        data = OUT/'data'/fold
        matrix = np.load(data/'x_evaluation.npy',allow_pickle=False)
        assert matrix.dtype==np.dtype('float64')
        scaler = joblib.load(data/'target_scaler.joblib')
        inverse = pd.read_parquet(data/'evaluation_transform.parquet')
        inputs = pd.read_parquet(data/'application_inputs.parquet')
        coverage = pd.read_parquet(data/'coverage.parquet')
        labels = pd.read_parquet(data/'labels.parquet')
        keys = inputs[['ts','grp']].merge(coverage,on=['ts','grp'],sort=False,validate='one_to_one')
        seeds = []
        for seed in (0,1,2):
            directory = OUT/'trials'/fold/f'seed{seed}'
            config = read(directory/'config.json')
            expected = {**PARAMS,'random_state':seed}
            expected_json = json.loads(json.dumps(expected))
            assert config['parameters']==expected_json
            assert config['prepared_manifest_sha256']==digest(OUT/'prepared_manifest.json')
            assert config['sample_weight_used'] and config['dtype']=='float64'
            for name,sha in config['matrix_sha256'].items():
                assert digest(data/name)==sha,name
            model = joblib.load(directory/'model.joblib')
            actual = model.get_params()
            for name,value in expected.items():
                assert actual[name]==value,(name,actual[name],value)
            assert actual['loss']=='squared_error'
            assert model.n_features_in_==matrix.shape[1]==config['feature_count']
            assert all(value.dtype==np.dtype('float64') for value in [*model.coefs_,*model.intercepts_])
            scaled_prediction = model.predict(matrix)
            replay = scaler.inverse_transform(scaled_prediction.reshape(-1,1)).ravel()*inverse.inverse_kwh.to_numpy()
            raw = pd.read_parquet(directory/'daylight_raw.parquet')
            pd.testing.assert_frame_equal(raw[['ts','grp']],inverse[['ts','grp']])
            np.testing.assert_array_equal(raw.p_raw,replay)
            full = keys.merge(raw,on=['ts','grp'],how='left',sort=False,validate='one_to_one')
            assert full.p_raw.isna().eq(full.night).all()
            assert int(full.p_raw.notna().sum())==len(raw)
            seeds.append(full.p_raw.fillna(0.).to_numpy())
            status = read(directory/'worker_status.json')
            receipt = read(directory/'controller_receipt.json')
            runtime = read(directory/'runtime.json')
            convergence = read(directory/'convergence.json')
            assert status['state']=='complete' and receipt['exit_code']==0 and receipt['exact_worker_absent']
            assert status['model_sha256']==digest(directory/'model.joblib') and status['raw_sha256']==digest(directory/'daylight_raw.parquet')
            identity = receipt['identity']
            assert (identity['pid'],identity['creation_filetime']) in terminal_ids
            assert (runtime['pid'],runtime['creation_filetime'])==(identity['pid'],identity['creation_filetime'])
            assert not runtime['loaded_existing_model']
            check_resources(runtime)
            check_resources(status['identity'])
            assert 1<=model.n_iter_<=400 and convergence['iterations']==model.n_iter_
            np.testing.assert_array_equal(convergence['loss_curve'],model.loss_curve_)
            assert convergence['last_loss']==model.loss_ and convergence['all_seeds_retained']
            log = (directory/'fit.log').read_text(encoding='utf-8')
            for warning in convergence['warnings']:
                assert warning['message'] in log
            creation = pd.Timestamp((identity['creation_filetime']-116444736000000000)*100,tz='UTC')
            trials.append({'fold':fold,'seed':seed,'identity':identity,'creation_utc':str(creation),'finished_utc':receipt['finished_utc'],'iterations':model.n_iter_,'warnings':convergence['warnings'],'seconds':runtime['seconds'],'rows':len(raw),'negative_raw':int(raw.p_raw.lt(0).sum()),'full_saved_model_replay_max_error':0.})
        prediction = pd.read_parquet(OUT/'comparisons'/fold/'predictions.parquet')
        pd.testing.assert_frame_equal(prediction[list(labels)],labels)
        pd.testing.assert_frame_equal(prediction[list(inputs)],inputs)
        calculated = component(inputs,np.array(seeds,dtype=np.float64),originals)
        for name,values in calculated.items():
            np.testing.assert_array_equal(prediction[name],values)
        assert prediction.loc[keys.night,'p_new'].eq(0).all() and prediction.loc[keys.night,'p'].eq(0).all()
        frames[fold] = prediction
    for previous,current in zip(trials,trials[1:]):
        assert pd.Timestamp(previous['finished_utc'])<=pd.Timestamp(current['creation_utc'])
    alpha = primary_alpha(frames['primary'])
    result = read(OUT/'results.json')
    record = result['records'][0]
    assert alpha==record['alpha_primary_only']
    scores = {}
    for fold,frame in frames.items():
        assert frame.alpha.eq(alpha).all()
        np.testing.assert_array_equal(frame.p,(1-alpha)*frame.p_reference+alpha*frame.p_new)
        scores[fold] = {name:metrics(frame,name) for name in ('p','p_reference','p_new')}
        assert scores[fold]==record['scores'][fold]
        assert scores[fold]==read(OUT/'comparisons'/fold/'metrics.json')
    both = all(scores[f]['p']['W']<scores[f]['p_reference']['W'] for f in FOLDS)
    eligible = both and alpha>=.02
    assert both==record['both_folds_improve']
    assert eligible==record['eligible']==result['eligible']
    assert result['reference_retained']==(not eligible) and (result['selected'] is not None)==eligible
    assert result['real_model_fit_count']==6 and result['real_calibration_fit_count']==0
    assert not result['confirmation_loaded'] and not result['test_loaded'] and not result['exported']
    controller = read(OUT/'controller_receipt.json')
    assert controller['exit_code']==0 and controller['real_model_fit_count']==6 and controller['real_calibration_fit_count']==0
    check_resources(controller['identity'])
    check_resources(read(OUT/'controller_start.json')['identity'])
    assert controller['identity']['pid']==start['pid']
    assert controller['identity']['creation_filetime']==start['creation_filetime']
    assert pd.Timestamp(trials[-1]['finished_utc'])<=pd.Timestamp(controller['finished_utc'])
    save(OUT/'evidence/terminal_audit.json',{'passed':True,'utc':now(),'invocation':'python analysis_outputs/renew_20261105/mlp_wave/evidence/verify_terminal.py','scenario':'all6savedMLPparams/coefs/losses/warnings/fullreplays,complete signed ensemble and original3stage component,PRIMARYonly alpha,allmetrics/gate,7nativeidentities/serialintervals/resources,source/input/prepared/protected hashes','binary_observable':'all assertions passed','protected_files':len(protocol['protected_sha256']),'trials':trials,'scores':scores,'alpha_primary_only':alpha,'both_folds_improve':both,'eligible':eligible,'real_model_fits':6,'real_calibration_fits':0,'extra_fit_calls':0,'external_exit_code':0})
    print('MLP TERMINAL AUDIT PASS',flush=True)
if __name__=='__main__':
    with threadpool_limits(limits=16):
        main()
