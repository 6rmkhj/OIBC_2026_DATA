# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/refresh_run.py
"""Two fixed chronological calibration refreshes; no production refit or export."""
from dataclasses import asdict
import json
import msvcrt
from refresh_common import ROOT,OUT,FOLDS,COLUMNS,environment,freeze,install_frozen,configure,resource,save,digest,now

def execute() -> None:
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- exact fit/apply/scoring contract
    from refresh_math import fit_pipeline,apply_pipeline
    from final_metrics import metrics
    for path,sha in json.loads((OUT/'prepared_manifest.json').read_text(encoding='utf-8')).items():
        assert digest(OUT/path)==sha,path
    old_receipt = json.loads((OUT/'old_replay/receipt.json').read_text(encoding='utf-8'))
    assert old_receipt['passed'] and old_receipt['real_scalar_fit_count']==0
    (OUT/'coefficients').mkdir()
    (OUT/'training_stages').mkdir()
    scores = {}
    gates = []
    count = 0
    for fold,(cutoff_text,end_text) in FOLDS.items():
        directory = OUT/'data'/fold
        train_path = directory/'train.parquet'
        train = pd.read_parquet(train_path)
        cutoff = pd.Timestamp(cutoff_text,tz='Asia/Seoul')
        assert train.ts.max()<=cutoff
        assert not (OUT/'coefficients'/f'{fold}.json').exists()
        started = now()
        fitted = fit_pipeline(train)
        completed = now()
        assert len(fitted.weather.temperature)+2+len(fitted.hour.hours)+len(fitted.cloud.clouds)==16
        count += 16
        save(OUT/'coefficients'/f'{fold}.json',{'fold':fold,'cutoff_inclusive':str(cutoff),'train_source':str(train_path.relative_to(OUT)),'train_source_sha256':digest(train_path),'train_rows':len(train),'train_max_ts':str(train.ts.max()),'fit_started_utc':started,'fit_completed_utc':completed,'original_replay_receipt_sha256':digest(OUT/'old_replay/receipt.json'),'fit_scalar_count':16,'factors':asdict(fitted)})
        training = apply_pipeline(train[COLUMNS],fitted)
        training.to_parquet(OUT/'training_stages'/f'{fold}.parquet',index=False)
        inputs = pd.read_parquet(directory/'evaluation.parquet')
        assert list(inputs)==COLUMNS and inputs.ts.min()>cutoff and inputs.ts.max()<=pd.Timestamp(end_text,tz='Asia/Seoul')
        prediction = apply_pipeline(inputs,fitted)
        np.testing.assert_array_equal(prediction.p,apply_pipeline(inputs,fitted).p)
        labels = pd.read_parquet(directory/'labels.parquet')
        frozen = pd.read_parquet(directory/'references.parquet').rename(columns={'p_weather':'frozen_weather','p_hour':'frozen_hour','p_cloud':'frozen_cloud'})
        scored = prediction.merge(labels,on=['ts','grp'],sort=False,validate='one_to_one').merge(frozen,on=['ts','grp'],sort=False,validate='one_to_one')
        assert len(scored)==len(inputs)==len(labels)==len(frozen)
        pd.testing.assert_frame_equal(scored[['ts','grp']],inputs[['ts','grp']])
        destination = OUT/'comparisons'/fold
        destination.mkdir(parents=True)
        scored.to_parquet(destination/'predictions.parquet',index=False)
        scores[fold] = {name:metrics(scored,name) for name in ('p','frozen_weather','frozen_hour','frozen_cloud')}
        save(destination/'metrics.json',scores[fold])
        save(destination/'application.json',{'passed':True,'rows':len(scored),'full_replay_max_error':0.,'coefficient_sha256':digest(OUT/'coefficients'/f'{fold}.json'),'prediction_sha256':digest(destination/'predictions.parquet'),'train_stages_sha256':digest(OUT/'training_stages'/f'{fold}.parquet'),'no_evaluation_labels_in_application':True,'night_zero':bool(scored.loc[scored.p_reference.eq(0),'p'].eq(0).all())})
        for reference in ('frozen_weather','frozen_hour','frozen_cloud'):
            gates.append({'fold':fold,'reference':reference,'new_W':scores[fold]['p']['W'],'reference_W':scores[fold][reference]['W'],'strictly_improves':scores[fold]['p']['W']<scores[fold][reference]['W']})
    assert count==32 and len(gates)==6
    eligible = all(row['strictly_improves'] for row in gates)
    record = {'arm':'chronological_refresh','scores':scores,'gate_comparisons':gates,'eligible':eligible}
    save(OUT/'results.json',{'records':[record],'selected':record if eligible else None,'eligible':eligible,'reference_retained':not eligible,'gate_comparisons':gates,'real_scalar_fit_count':count,'tree_fits':0,'loaded_existing_coefficients':False,'candidate_count':1,'test_loaded':False,'exported':False,'full_refit':False,'historical_exposure':'All history exposed; no independent holdout claim. Two forward periods excluded from their corresponding new scalar fits.'})
    protocol = json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
    after = {path:digest(ROOT/path) for path in protocol['protected_sha256']}
    assert after==protocol['protected_sha256']
    save(OUT/'preservation.json',{'unchanged':True,'files':len(after),'sha256':after})

def main() -> None:
    environment()
    with (OUT/'controller.lock').open('a+b') as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        freeze()
        install_frozen()
        configure()
        from threadpoolctl import threadpool_limits
        from refresh_math import self_check
        from refresh_prepare import prepare,original_replay
        with threadpool_limits(limits=16):
            save(OUT/'controller_start.json',{'identity':resource(),'utc':now(),'scalar_fit_budget':32,'tree_fit_budget':0})
            fixtures = self_check()
            save(OUT/'evidence/selfchecks.json',{'passed':True,'utc':now(),'fixtures':fixtures,'real_scalar_fit_count':0})
            prepare()
            original_replay()
            execute()
            save(OUT/'controller_receipt.json',{'exit_code':0,'finished_utc':now(),'identity':resource(),'real_scalar_fit_count':32,'tree_fits':0})
            print('REFRESH WAVE TERMINAL',flush=True)
if __name__=='__main__':
    main()
