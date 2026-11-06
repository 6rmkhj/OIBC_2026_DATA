# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: python analysis_outputs/renew_20261105/mono_wave/evidence/verify_terminal.py
"""Terminal immutable-model replays and independent matched-arm scoring audit."""
import json
import os
import sys
from pathlib import Path
sys.dont_write_bytecode = True
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key] = '16'
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'submission/score_push_renew'))
from mono_common import OUT,FOLDS,ARMS,PARAMS,digest,save,now,configure,install_frozen,check_prepared
import lightgbm as lgb
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen scientific scoring contracts
from threadpoolctl import threadpool_limits,threadpool_info
from verify_scoring import component,primary_alpha,metrics

def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def resources(record: dict, exact: bool = True) -> None:
    assert record['priority_class']==32 and record['model_threads']==16 and record['parallel_fits']==1
    assert record['pyarrow_cpu']==record['pyarrow_io']==4
    assert all(p['num_threads']==16 if exact else 1<=p['num_threads']<=16 for p in record['threadpools'])

def main() -> None:
    configure()
    install_frozen()
    check_prepared()
    protocol = read(OUT/'protocol.json')
    for path,sha in protocol['protected_sha256'].items():
        assert digest(ROOT/path)==sha,path
    native = read(OUT/'evidence/native_terminal_identities.json')
    assert native['passed'] and len(native['records'])==13
    terminal_ids = {(r['pid'],r['creation_filetime']) for r in native['records'] if r['exact_absent']}
    external = read(OUT/'evidence/run_attempt01_exit.json')
    assert external['exit_code']==0 and external['has_exited'] and external['native_handle_retained_before_wait']
    assert (external['pid'],external['creation_filetime']) in terminal_ids
    originals = {stage:read(OUT/f'original_{stage}_coefficients.json')['factors'] for stage in ('weather','hour','cloud')}
    results = read(OUT/'results.json')
    assert len(results['records'])==2 and [r['arm'] for r in results['records']]==list(ARMS)
    trials = []
    decisions = []
    for arm,record in zip(ARMS,results['records']):
        frames = {}
        for fold in FOLDS:
            data = OUT/'data'/fold
            names = read(data/'feature_mask.json')['selected_columns']
            vector = pd.read_parquet(data/'constraints.parquet')[arm].tolist()
            matrix = pd.read_parquet(data/'evaluation.parquet',columns=names)
            inverse = pd.read_parquet(data/'evaluation_transform.parquet')
            inputs = pd.read_parquet(data/'application_inputs.parquet')
            labels = pd.read_parquet(data/'labels.parquet')
            keys = inputs[['ts','grp']].merge(pd.read_parquet(data/'coverage.parquet'),on=['ts','grp'],sort=False,validate='one_to_one')
            seeds = []
            for seed in (0,1,2):
                directory = OUT/'trials'/arm/fold/f'seed{seed}'
                config = read(directory/'config.json')
                assert config['parameters']=={**PARAMS,'random_state':None if seed==0 else seed,'monotone_constraints':vector}
                assert config['features']==names and config['prepared_manifest_sha256']==digest(OUT/'prepared_manifest.json')
                for name,sha in config['input_sha256'].items():
                    assert digest(data/name)==sha,name
                model = lgb.Booster(model_file=str(directory/'model.txt'))
                assert model.feature_name()==names and model.current_iteration()==400
                with threadpool_limits(limits=16):
                    assert all(p['num_threads']==16 for p in threadpool_info())
                    replay = model.predict(matrix,num_threads=16,validate_features=True)*inverse.inverse_kwh.to_numpy()
                raw = pd.read_parquet(directory/'daylight_raw.parquet')
                pd.testing.assert_frame_equal(raw[['ts','grp']],inverse[['ts','grp']])
                np.testing.assert_array_equal(raw.p_raw,replay)
                full = keys.merge(raw,on=['ts','grp'],how='left',sort=False,validate='one_to_one')
                assert full.p_raw.isna().eq(full.night).all() and int(full.p_raw.notna().sum())==len(raw)
                seeds.append(full.p_raw.fillna(0.).to_numpy())
                status,runtime,proof,receipt = [read(directory/name) for name in ('worker_status.json','runtime.json','replay.json','controller_receipt.json')]
                assert status['state']=='complete' and status['new_model_fits']==runtime['new_model_fits']==receipt['new_model_fits']==1
                assert proof['passed'] and proof['max_absolute_error']==0 and proof['inverse_once']
                for item in (status,proof):
                    assert item['model_sha256']==digest(directory/'model.txt') and item['raw_sha256']==digest(directory/'daylight_raw.parquet')
                assert receipt['exit_code']==0 and receipt['exact_worker_absent']
                identity = receipt['identity']
                assert (identity['pid'],identity['creation_filetime']) in terminal_ids
                for item in (runtime,status['identity']):
                    resources(item)
                    assert (item['pid'],item['creation_filetime'])==(identity['pid'],identity['creation_filetime'])
                creation = pd.Timestamp((identity['creation_filetime']-116444736000000000)*100,tz='UTC')
                trials.append({'arm':arm,'fold':fold,'seed':seed,'identity':identity,'creation_utc':creation.isoformat(),'finished_utc':receipt['finished_utc'],'seconds':runtime['seconds'],'warnings':runtime['warnings'],'full_replay_error':0.,'rows':len(raw)})
            frame = pd.read_parquet(OUT/'comparisons'/arm/fold/'predictions.parquet')
            pd.testing.assert_frame_equal(frame[labels.columns],labels)
            pd.testing.assert_frame_equal(frame[inputs.columns],inputs)
            for name,expected in component(inputs,np.asarray(seeds),originals).items():
                np.testing.assert_array_equal(frame[name],expected)
            assert (frame.loc[keys.night,'p_new']==0).all() and (frame.loc[keys.night,'p']==0).all()
            frames[fold] = frame
        alpha = primary_alpha(frames['primary'])
        assert alpha==record['alpha_primary_only']
        for fold,frame in frames.items():
            assert (frame.alpha==alpha).all()
            np.testing.assert_array_equal(frame.p,(1-alpha)*frame.p_reference+alpha*frame.p_new)
            for name in ('p','p_reference','p_new'):
                assert metrics(frame,name)==record['scores'][fold][name]
        both = all(record['scores'][f]['p']['W']<record['scores'][f]['p_reference']['W'] for f in FOLDS)
        assert record['both_folds_improve']==both and record['eligible']==(both and alpha>=.02)
        assert record['mean_relative_W']==np.mean([record['scores'][f]['p']['W']/record['scores'][f]['p_reference']['W'] for f in FOLDS])
        decisions.append(record)
    for previous,current in zip(trials,trials[1:]):
        assert pd.Timestamp(previous['finished_utc'])<=pd.Timestamp(current['creation_utc'])
    eligible = [r for r in decisions if r['eligible']]
    selected = min(eligible,key=lambda r:r['mean_relative_W']) if eligible else None
    assert results['selected']==selected and results['reference_retained']==(selected is None) and results['eligible']==bool(eligible)
    for fold in FOLDS:
        for name in ('p_new','p'):
            control,monotone = [r['scores'][fold][name] for r in decisions]
            assert results['matched_fair_comparison'][fold][name]=={'control_W':control['W'],'monotone_W':monotone['W'],'monotone_minus_control_W':monotone['W']-control['W'],'control_W_pct':control['W_pct'],'monotone_W_pct':monotone['W_pct']}
    for name,value in {'real_model_fit_count':12,'real_calibration_fit_count':0,'candidate_count':2,'confirmation_loaded':False,'test_loaded':False,'exported':False}.items():
        assert results[name]==value
    controller = read(OUT/'controller_receipt.json')
    assert controller['exit_code']==0 and controller['real_model_fit_count']==12
    resources(controller['identity'],exact=False)
    save(OUT/'evidence/terminal_audit.json',{'passed':True,'utc':now(),'trials':trials,'full_replays':12,'all_stage_and_metric_equality':True,'serial_intervals_nonoverlap':True,'protected_files':len(protocol['protected_sha256']),'protected_hashes_unchanged':True,'native_identity_count':len(terminal_ids),'worker_pools_exact16':True,'controller_terminal_pool_threads':[p['num_threads'] for p in controller['identity']['threadpools']],'records':decisions,'selected':selected,'real_model_fit_count':12,'real_calibration_fit_count':0})
    print('MONO TERMINAL AUDIT PASS',flush=True)

if __name__=='__main__':
    with threadpool_limits(limits=16):
        main()
