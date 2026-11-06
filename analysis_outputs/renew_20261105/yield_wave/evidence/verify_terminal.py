# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: python analysis_outputs/renew_20261105/yield_wave/evidence/verify_terminal.py
"""Read-only mathematical and full saved-model audit after the released wave."""
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name] = '16'
import json
import sys
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact saved parquet replay
import lightgbm as lgb
from threadpoolctl import threadpool_limits
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'submission/score_push_renew'))
from yield_common import OUT, digest, save, now, install_frozen, ensure_terminal, configure, resource, PARAMS
def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
def physical(c):
    z = np.maximum(c, 0.)
    return 1.098*z*np.exp(np.divide(-.059,z,out=np.zeros_like(z,dtype=float),where=z>0))
def main() -> None:
    configure()
    install_frozen()
    start = read(OUT/'evidence/run_attempt01_start.json')
    outer = read(OUT/'evidence/run_attempt01_exit.json')
    native_terminal = read(OUT/'evidence/native_terminal_identities.json')
    assert native_terminal['passed']
    terminal_ids = {(r['pid'],r['creation_filetime']) for r in native_terminal['records'] if r['exact_absent']}
    assert (start['pid'],start['creation_filetime']) in terminal_ids
    assert outer['has_exited'] and outer['pid']==start['pid']
    assert read(OUT/'controller_receipt.json')['exit_code']==0
    for manifest_name in ('prepared_manifest.json','transform_manifest.json'):
        for p, sha in read(OUT/manifest_name).items():
            assert digest(OUT/p)==sha,p
    protocol = read(OUT/'protocol.json')
    for p, sha in protocol['protected_sha256'].items():
        assert digest(ROOT/p)==sha,p
    sites = pd.read_parquet(OUT/'data/sites.parquet')
    assert len(sites)==253
    folds = []
    trials = []
    for fold in ('primary','recent'):
        directory = OUT/'data'/fold
        coef = read(OUT/'coefficients'/f'{fold}.json')
        panel = pd.read_parquet(directory/'site_train.parquet')
        spec = read(directory/'features.json')
        cutoff = pd.Timestamp(spec['cutoff'])
        assert panel.ts.max()<=cutoff
        assert coef['source_sha256']==digest(directory/'site_train.parquet')
        assert len(coef['sites'])==253
        assert {r['site_id'] for r in coef['sites']}==set(sites.site_id)
        mask = np.isfinite(panel[['cf','cosz','wa_cloud','wb_cloud']]).all(axis=1)
        mask &= (panel.cf>=0)&(panel.cosz>.5)&(panel.wa_cloud>=0)&(panel.wa_cloud<20)&(panel.wb_cloud>=0)&(panel.wb_cloud<20)
        clear = panel.loc[mask].copy()
        clear['ratio'] = clear.cf.to_numpy()/physical(clear.cosz.to_numpy())
        global_q90 = np.quantile(clear.ratio,.9,method='linear')
        assert coef['clear_rows']==len(clear)
        np.testing.assert_equal(coef['global_q90'],global_q90)
        for item in coef['sites']:
            subset = clear.loc[clear.site_id.eq(item['site_id'])]
            n = len(subset)
            days = (subset.ts-pd.Timedelta(hours=1)).dt.normalize().nunique()
            q = float(np.quantile(subset.ratio,.9,method='linear')) if n else None
            observed = int(panel.site_id.eq(item['site_id']).sum())
            assert (observed,n,int(days))==(item['observed_rows'],item['clear_rows'],item['clear_days'])
            assert q==item['raw_q90']
            relative = q/global_q90 if q is not None else None
            assert relative==item['raw_relative']
            shrink = n/(n+200)
            supported = n>=100 and days>=20 and q is not None and np.isfinite(q) and q>0
            gain = float(np.clip(1+shrink*(relative-1),.5,1.5)) if supported else 1.
            reason = 'supported' if supported else ('no_clear_rows' if n==0 else 'insufficient_rows' if n<100 else 'insufficient_days' if days<20 else 'nonpositive_or_nonfinite_q90')
            assert (shrink,gain,reason)==(item['shrink'],item['gain'],item['fallback_reason'])
        gains = {r['site_id']:r['gain'] for r in coef['sites']}
        split_records = []
        for split in ('train','evaluation'):
            site_frame = pd.read_parquet(directory/f'site_{split}.parquet')
            assert (site_frame.ts.max()<=cutoff) if split=='train' else (site_frame.ts.min()>cutoff)
            active = site_frame[['ts','site_id','capacity_kw']].copy()
            active['grp'] = active.site_id.map(sites.set_index('site_id').grp)
            active['yield_capacity'] = active.capacity_kw*active.site_id.map(gains).fillna(1.)
            grouped = active.groupby(['ts','grp'],as_index=False,observed=True)[['capacity_kw','yield_capacity']].sum()
            grouped['group_gain'] = grouped.yield_capacity/grouped.capacity_kw
            saved_group = pd.read_parquet(directory/f'{split}_group_gain.parquet')
            pd.testing.assert_frame_equal(grouped,saved_group)
            original_capacity = pd.read_parquet(directory/f'{split}_capacity.parquet')
            aligned = grouped.merge(original_capacity,on=['ts','grp'],validate='one_to_one',suffixes=('','_original'))
            np.testing.assert_allclose(aligned.capacity_kw,aligned.capacity_kw_original,rtol=1e-12,atol=1e-8)
            frame = pd.read_parquet(directory/f'{split}.parquet')
            transform = pd.read_parquet(directory/('training_transform.parquet' if split=='train' else 'evaluation_transform.parquet'))
            pd.testing.assert_frame_equal(frame[['ts','grp']],transform[['ts','grp']])
            expected_gain = frame[['ts','grp']].merge(grouped[['ts','grp','group_gain']],on=['ts','grp'],validate='one_to_one',sort=False).group_gain
            h = physical(frame.cosz.to_numpy())
            normal = np.maximum(.05,h*expected_gain.to_numpy())
            np.testing.assert_array_equal(transform.group_gain,expected_gain)
            np.testing.assert_array_equal(transform.physical_haurwitz,h)
            np.testing.assert_array_equal(transform.new_normalizer,normal)
            if split=='train':
                age = (cutoff-frame.ts).dt.total_seconds().to_numpy()/86400
                decay = np.exp2(-age/180)
                decay /= decay.mean()
                np.testing.assert_array_equal(transform.age_days,age)
                np.testing.assert_array_equal(transform.decay,decay)
                np.testing.assert_array_equal(transform.target,frame.cf.to_numpy()/normal)
                np.testing.assert_array_equal(transform.sample_weight,normal*decay)
            split_records.append({'split':split,'rows':len(frame),'capacity_max_error':float(np.max(np.abs(aligned.capacity_kw-aligned.capacity_kw_original))),'gain_range':[float(expected_gain.min()),float(expected_gain.max())],'full_transform_exact':True})
        folds.append({'fold':fold,'global_q90':float(global_q90),'clear_rows':len(clear),'site_records':253,'all_coefficient_fields_exact':True,'fallback_counts':dict(Counter(r['fallback_reason'] for r in coef['sites'])),'transforms':split_records})
        evaluation = pd.read_parquet(directory/'evaluation.parquet')
        inverse = pd.read_parquet(directory/'evaluation_transform.parquet').new_normalizer.to_numpy()*evaluation.capacity_kw.to_numpy()
        for seed in (0,1,2):
            trial = OUT/'trials/site_yield'/fold/f'seed{seed}'
            receipt = read(trial/'controller_receipt.json')
            status = read(trial/'worker_status.json')
            runtime = read(trial/'runtime.json')
            config = read(trial/'config.json')
            assert (receipt['identity']['pid'],receipt['identity']['creation_filetime']) in terminal_ids
            assert receipt['exit_code']==0 and status['state']=='complete'
            assert not runtime['loaded_existing_model']
            assert config['parameters']=={**PARAMS,'random_state':None if seed==0 else seed}
            assert config['transform_manifest_sha256']==digest(OUT/'transform_manifest.json')
            assert config['weights_sha256']==digest(directory/'training_transform.parquet')
            assert config['coefficient_sha256']==digest(OUT/'coefficients'/f'{fold}.json')
            assert config['features']==spec['features'] and config['candidates']==spec['candidates']
            for record in (runtime,status['identity']):
                assert record['priority_class']==32 and record['model_threads']==16
                assert record['pyarrow_cpu']==4 and record['pyarrow_io']==4
                assert all(p['num_threads']==16 for p in record['threadpools'])
            model = lgb.Booster(model_file=str(trial/'model.txt'))
            native = model.params
            for key,value in {'num_threads':16,'num_iterations':400,'num_leaves':63,'learning_rate':.03,'min_data_in_leaf':50,'bagging_fraction':.8,'bagging_freq':1,'feature_fraction':.8,'device_type':'cpu'}.items():
                assert native[key]==value,(key,native.get(key))
            assert model.current_iteration()==400
            replay = model.predict(evaluation[spec['features']],raw_score=True,num_threads=16)*inverse
            raw = pd.read_parquet(trial/'daylight_raw.parquet')
            pd.testing.assert_frame_equal(raw[['ts','grp']],evaluation[['ts','grp']])
            np.testing.assert_array_equal(replay,raw.p_raw)
            assert digest(trial/'model.txt')==status['model_sha256']
            assert digest(trial/'daylight_raw.parquet')==status['raw_sha256']
            trials.append({'fold':fold,'seed':seed,'rows':len(raw),'replay_max_error':0.,'native_parameters_passed':True,'identity':receipt['identity'],'started_utc':receipt['started_utc'],'finished_utc':receipt['finished_utc'],'creation_utc':str(pd.Timestamp((receipt['identity']['creation_filetime']-116444736000000000)*100,tz='UTC'))})
    assert len(trials)==6
    for previous,current in zip(trials,trials[1:]):
        assert pd.Timestamp(previous['finished_utc'])<=pd.Timestamp(current['creation_utc'])
    result = read(OUT/'results.json')
    assert result['real_model_fit_count']==6 and result['real_site_gain_fit_count']==2
    assert not result['confirmation_loaded'] and not result['test_loaded']
    record = {'passed':True,'utc':now(),'invocation':'python analysis_outputs/renew_20261105/yield_wave/evidence/verify_terminal.py','scenario':'all253sites per cutoff, every transform row, six full saved-model replays, native resources and actual PID serial intervals, protected/prepared/frozen hashes','binary_observable':'all assertions passed','resource':resource(),'folds':folds,'trials':trials,'protected_files_unchanged':len(protocol['protected_sha256']),'controller_exact_absent':True,'outer_exit_code':outer['exit_code'],'outer_exit_code_limitation':'PowerShell failed to preserve the native exit code; internal controller receipt is0, six child subprocess return codes are0, exact process is absent. No outer exit code inferred.'}
    save(OUT/'evidence/terminal_audit.json',record)
    print('TERMINAL AUDIT PASS',flush=True)
if __name__=='__main__':
    with threadpool_limits(limits=16):
        main()
