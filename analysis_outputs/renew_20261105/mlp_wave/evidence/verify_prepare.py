# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "scikit-learn", "joblib", "threadpoolctl"]
# ///
# How to run: python analysis_outputs/renew_20261105/mlp_wave/evidence/verify_prepare.py
"""No-model audit of every projected row, matrix, scaler, target and weight."""
import json
import os
import sys
from pathlib import Path
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key] = '16'
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'submission/score_push_renew'))
from mlp_common import OUT,DATA,RENEW,REFERENCE_DIR,FOLDS,REFERENCE,digest,save,now,configure,install_frozen
import joblib
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact source and persisted preprocessing contracts
from threadpoolctl import threadpool_limits

def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def h(cosz: np.ndarray) -> np.ndarray:
    positive = np.maximum(cosz,0.)
    exponent = np.divide(-.059,positive,out=np.zeros_like(positive,dtype=np.float64),where=positive>0)
    return np.maximum(1.098*positive*np.exp(exponent),.05)

def main() -> None:
    configure()
    install_frozen()
    protocol = read(OUT/'protocol.json')
    for path,sha in protocol['protected_sha256'].items():
        assert digest(ROOT/path)==sha,path
    for path,sha in read(OUT/'prepared_manifest.json').items():
        assert digest(OUT/path)==sha,path
    capacity = read(RENEW/'final/static_capacity.json')
    records = []
    for fold,(cutoff_text,end_text) in FOLDS.items():
        directory = OUT/'data'/fold
        mask = read(directory/'feature_mask.json')
        candidates = read(DATA/fold/'features.json')['station']
        assert len(candidates)==904 and mask['candidate_columns']==candidates
        raw_train = pd.read_parquet(DATA/fold/'train.parquet',columns=['ts','grp','cf',*candidates])
        raw_eval = pd.read_parquet(DATA/fold/'evaluation.parquet',columns=['ts','grp','capacity_kw',*candidates])
        train = pd.read_parquet(directory/'train.parquet')
        evaluation = pd.read_parquet(directory/'evaluation.parquet')
        pd.testing.assert_frame_equal(raw_train,train)
        pd.testing.assert_frame_equal(raw_eval,evaluation)
        selected = [name for name in candidates if len(np.unique(train[name].dropna().to_numpy()))>1]
        assert mask['selected_columns']==selected and mask['dropped_columns']==[name for name in candidates if name not in selected]
        x_source = train[selected].astype(np.float64)
        e_source = evaluation[selected].astype(np.float64)
        transform = joblib.load(directory/'input_preprocessing.joblib')
        x = np.load(directory/'x_train.npy',allow_pickle=False)
        e = np.load(directory/'x_evaluation.npy',allow_pickle=False)
        y = np.load(directory/'y_train.npy',allow_pickle=False)
        weights = np.load(directory/'sample_weight.npy',allow_pickle=False)
        for values in (x,e,y,weights):
            assert values.dtype==np.dtype('float64') and np.isfinite(values).all()
        assert x.shape==(len(train),len(selected)) and e.shape==(len(evaluation),len(selected))
        medians = np.nanmedian(x_source.to_numpy(),axis=0)
        np.testing.assert_array_equal(medians,transform[0].statistics_)
        filled = np.where(np.isnan(x_source.to_numpy()),medians,x_source.to_numpy())
        np.testing.assert_allclose(np.mean(filled,axis=0,dtype=np.float64),transform[1].mean_,rtol=1e-12,atol=1e-12)
        np.testing.assert_allclose(np.var(filled,axis=0,dtype=np.float64),transform[1].var_,rtol=1e-12,atol=1e-12)
        assert transform[1].n_samples_seen_==len(train)
        assert (transform[1].scale_>0).all()
        np.testing.assert_array_equal((filled-transform[1].mean_)/transform[1].scale_,x)
        del filled
        np.testing.assert_array_equal(transform.transform(x_source),x)
        np.testing.assert_array_equal(transform.transform(e_source),e)
        before = joblib.hash(transform)
        adversarial = e_source.iloc[:3].copy()
        adversarial.iloc[:,:] = np.nan
        transform.transform(adversarial)
        assert joblib.hash(transform)==before
        cutoff,end = (pd.Timestamp(t,tz='Asia/Seoul') for t in (cutoff_text,end_text))
        assert train.ts.max()<=cutoff<evaluation.ts.min() and evaluation.ts.max()<=end
        scale = h(train.cosz.to_numpy(dtype=np.float64))
        age = (cutoff-train.ts).dt.total_seconds().to_numpy(dtype=np.float64)/86400.
        base = scale**2
        decay = np.exp2(-age/180.)
        expected_weight = base*decay*base.sum(dtype=np.float64)/(base*decay).sum(dtype=np.float64)
        np.testing.assert_array_equal(weights,expected_weight)
        assert (weights>0).all()
        np.testing.assert_allclose(weights.sum(),base.sum(),rtol=2e-15,atol=1e-12)
        target = train.cf.to_numpy(dtype=np.float64)/scale
        scaler = joblib.load(directory/'target_scaler.joblib')
        np.testing.assert_allclose(scaler.mean_,[target.mean()],rtol=1e-14,atol=1e-14)
        np.testing.assert_allclose(scaler.var_,[target.var()],rtol=1e-14,atol=1e-14)
        assert scaler.n_samples_seen_==len(train)
        np.testing.assert_array_equal(scaler.transform(target.reshape(-1,1)).ravel(),y)
        np.testing.assert_allclose(scaler.inverse_transform(y.reshape(-1,1)).ravel(),target,rtol=1e-12,atol=1e-12)
        training = pd.read_parquet(directory/'training_transform.parquet')
        pd.testing.assert_frame_equal(training[['ts','grp']],train[['ts','grp']])
        values = {'normalizer':scale,'age_days':age,'base_weight':base,'decay':decay,'sample_weight':weights,'target_normalized':target,'target_scaled':y}
        for name,value in values.items():
            np.testing.assert_array_equal(training[name],value)
        assert training.weight_normalization.eq(float(base.sum()/(base*decay).sum())).all()
        eval_scale = h(evaluation.cosz.to_numpy(dtype=np.float64))
        inverse = eval_scale*evaluation.capacity_kw.to_numpy(dtype=np.float64)
        eval_transform = pd.read_parquet(directory/'evaluation_transform.parquet')
        pd.testing.assert_frame_equal(eval_transform[['ts','grp']],evaluation[['ts','grp']])
        np.testing.assert_array_equal(eval_transform.normalizer,eval_scale)
        np.testing.assert_array_equal(eval_transform.capacity_kw,evaluation.capacity_kw.to_numpy(dtype=np.float64))
        np.testing.assert_array_equal(eval_transform.inverse_kwh,inverse)
        reference = pd.read_parquet(REFERENCE_DIR/fold/'predictions.parquet',columns=['ts','grp','y','smp','k','p']).rename(columns={'p':'p_reference'})
        labels = pd.read_parquet(directory/'labels.parquet')
        pd.testing.assert_frame_equal(labels,reference)
        raw_coverage = pd.read_parquet(RENEW/'recency_wave/data'/fold/'night_coverage.parquet')
        coverage = pd.read_parquet(directory/'coverage.parquet')
        pd.testing.assert_frame_equal(coverage,raw_coverage)
        fields = ['ts','grp','wa_temp','extra_wa_snow','wb_cloud']
        full = labels[['ts','grp']].merge(coverage,on=['ts','grp'],how='left',sort=False,validate='one_to_one')
        joined = full.merge(raw_eval[fields],on=['ts','grp'],how='left',sort=False,validate='one_to_one',indicator=True)
        np.testing.assert_array_equal(joined._merge.eq('left_only'),joined.night)
        assert int(joined._merge.eq('both').sum())==len(raw_eval)
        assert labels.loc[joined.night,'p_reference'].eq(0).all()
        expected_inputs = joined[fields].copy()
        expected_inputs['static_capacity'] = expected_inputs.grp.map(capacity)
        app = pd.read_parquet(directory/'application_inputs.parquet')
        pd.testing.assert_frame_equal(app,expected_inputs)
        assert not {'y','smp','k','cf'}&set(app)
        monetary = labels.smp*labels.k
        score = 100*float((monetary*(labels.p_reference-labels.y).abs()).sum())/float((monetary*labels.y).sum())
        assert abs(score-REFERENCE[fold])<1e-10
        from mlp_math import component
        zero = component(app,np.zeros((3,len(app)),dtype=np.float64))
        assert zero.p_new.eq(0).all() and zero.p_component.eq(0).all()
        import gpu_common
        assert gpu_common.OUT==OUT
        records.append({'fold':fold,'train_rows':len(train),'evaluation_rows':len(evaluation),'full_rows':len(labels),'selected_features':len(selected),'all_arrays_float64':True,'raw_projections_exact':True,'train_only_mask_exact':True,'medians_exact':True,'scaler_means_variances_train_only_rtol':1e-12,'full_matrices_exact':True,'target_scaler_train_only_and_full_replay':True,'normalizer_age_decay_weight_exact':True,'base_weight_sum':float(base.sum()),'sample_weight_sum':float(weights.sum()),'weight_mass_error':float(weights.sum()-base.sum()),'reference_W_pct':score,'full_reference_weather_coverage_exact':True,'allzero_component_pipeline_stays_zero':True,'original_OUT_unchanged':True})
    external = read(OUT/'evidence/prepare_attempt01_exit.json')
    start = read(OUT/'evidence/prepare_attempt01_start.json')
    prefit = read(OUT/'evidence/prefit_checks.json')
    assert external['exit_code']==0 and external['has_exited'] and external['exact_worker_absent'] and external['native_handle_retained_before_wait']
    assert (external['pid'],external['creation_filetime'])==(start['pid'],start['creation_filetime'])
    resource = prefit['identity']
    assert (resource['pid'],resource['creation_filetime'])==(start['pid'],start['creation_filetime'])
    assert resource['priority_class']==32 and resource['model_threads']==16 and resource['parallel_fits']==1
    assert resource['pyarrow_cpu']==4 and resource['pyarrow_io']==4
    assert all(pool['num_threads']==16 for pool in resource['threadpools'])
    assert prefit['real_model_fits']==0 and prefit['real_calibration_fits']==0
    assert read(OUT/'evidence/selfchecks.json')['passed']
    assert read(OUT/'evidence/environment.json')['sample_weight_supported']
    for name in ('trials','models','results.json','controller_start.json','controller_receipt.json'):
        assert not (OUT/name).exists(),name
    save(OUT/'evidence/prepare_terminal.json',{'passed':True,'utc':now(),'invocation':'python analysis_outputs/renew_20261105/mlp_wave/evidence/verify_prepare.py','scenario':'everyrawprojectedrow,TRAINmask/median/scalerstats,fullfloat64matrices,targetscaler/normalizedtarget/age/weightmass,fullreference/weather/coverage,releasebarrier/resources/hashpreservation','binary_observable':'all assertions passed','protected_files':len(protocol['protected_sha256']),'folds':records,'real_model_fits':0,'real_calibration_fits':0,'external_exit_code':0,'resource':resource,'source_amendment_sha256':digest(OUT/'source_amendment.json')})
    print('MLP PREPARE AUDIT PASS',flush=True)
if __name__=='__main__':
    with threadpool_limits(limits=16):
        main()
