# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/sky_run.py
"""One authorized cloud stage: exact projections, four scalar fits, fixed gate."""
from dataclasses import asdict
import json
import msvcrt
from sky_common import ROOT,RENEW,OUT,DATA,REFERENCE_DIR,FOLDS,REFERENCE,BINS,environment,freeze,install_frozen,configure,resource,save,digest,now

def prepare() -> None:
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- exact current calibrated keys and labels
    from final_metrics import metrics
    capacity = json.loads((RENEW/'final/static_capacity.json').read_text(encoding='utf-8'))
    receipts = []
    for fold,(start_text,end_text) in FOLDS.items():
        start,end = (pd.Timestamp(t,tz='Asia/Seoul') for t in (start_text,end_text))
        reference = pd.read_parquet(REFERENCE_DIR/fold/'predictions.parquet',columns=['ts','grp','y','smp','k','p','static_capacity']).rename(columns={'p':'p_reference'})
        features = pd.read_parquet(DATA/fold/'evaluation.parquet',columns=['ts','grp','wb_cloud'])
        assert not reference.duplicated(['ts','grp']).any() and not features.duplicated(['ts','grp']).any()
        assert start<reference.ts.min() and reference.ts.max()<=end
        assert start<features.ts.min() and features.ts.max()<=end
        coverage = pd.read_parquet(RENEW/'recency_wave/data'/fold/'night_coverage.parquet')
        frame = reference.merge(features,on=['ts','grp'],how='left',sort=False,validate='one_to_one',indicator=True)
        frame = frame.merge(coverage,on=['ts','grp'],how='left',sort=False,validate='one_to_one')
        assert frame.night.notna().all()
        assert frame._merge.eq('left_only').eq(frame.night).all()
        assert int(frame._merge.eq('both').sum())==len(features)
        frame = frame.drop(columns='_merge')
        pd.testing.assert_frame_equal(frame[list(reference)],reference)
        assert frame.loc[frame.night,'p_reference'].eq(0).all()
        np.testing.assert_array_equal(frame.static_capacity,frame.grp.map(capacity))
        assert np.isfinite(frame[['y','smp','k','p_reference','static_capacity']]).all().all()
        assert frame.smp.ge(0).all() and frame.k.ge(0).all() and frame.p_reference.ge(0).all()
        assert (frame.p_reference<=frame.static_capacity+1e-8).all()
        assert abs(metrics(frame,'p_reference')['W_pct']-REFERENCE[fold])<1e-10
        directory = OUT/'data'/fold
        directory.mkdir(parents=True)
        frame.to_parquet(directory/'rows.parquet',index=False)
        features.to_parquet(directory/'feature_projection.parquet',index=False)
        columns = ['ts','grp','p_reference','wb_cloud','static_capacity']
        frame[columns].to_parquet(directory/'apply_inputs.parquet',index=False)
        finite = np.isfinite(frame.wb_cloud)
        receipts.append({'fold':fold,'full_rows':len(frame),'projected_rows':len(features),'night_rows':int(frame.night.sum()),'unmatched_exact_allnight':True,'reference_zero_allnight':True,'rows_columns':list(frame),'apply_columns':columns,'feature_columns':list(features),'finite_cloud_rows':int(finite.sum()),'nonfinite_identity_rows':int((~finite).sum()),'finite_gt100_rows':int((finite&frame.wb_cloud.gt(100)).sum()),'finite_min':float(frame.loc[finite,'wb_cloud'].min()),'finite_max':float(frame.loc[finite,'wb_cloud'].max()),'reference_W_pct':metrics(frame,'p_reference')['W_pct']})
    save(OUT/'evidence/read_receipts.json',receipts)
    save(OUT/'prepared_manifest.json',{str(p.relative_to(OUT)):digest(p) for p in (OUT/'data').rglob('*') if p.is_file()})

def execute() -> None:
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- existing fit and metric contracts
    from final_metrics import metrics
    from sky_math import fit,apply
    assert not (OUT/'coefficients.json').exists(),'No repeat fitting'
    for path,sha in json.loads((OUT/'prepared_manifest.json').read_text(encoding='utf-8')).items():
        assert digest(OUT/path)==sha
    primary = pd.read_parquet(OUT/'data/primary/rows.parquet')
    fitted = fit(primary)
    save(OUT/'coefficients.json',{'fit_period':FOLDS['primary'],'target_source':'data/primary/rows.parquet','target_source_sha256':digest(OUT/'data/primary/rows.parquet'),'fit_columns':['ts','p_reference','y','smp','k','wb_cloud'],'timezone':'Asia/Seoul','cloud_bins':BINS,'nonfinite_identity':True,'real_scalar_fit_count':4,'factors':asdict(fitted)})
    scores = {}
    for fold in FOLDS:
        inputs = pd.read_parquet(OUT/'data'/fold/'apply_inputs.parquet')
        assert list(inputs)==['ts','grp','p_reference','wb_cloud','static_capacity']
        prediction = apply(inputs,fitted)
        labels = pd.read_parquet(OUT/'data'/fold/'rows.parquet',columns=['ts','grp','y','smp','k'])
        scored = prediction.merge(labels,on=['ts','grp'],sort=False,validate='one_to_one')
        pd.testing.assert_frame_equal(scored[['ts','grp']],inputs[['ts','grp']])
        assert len(scored)==len(inputs)==len(labels)
        np.testing.assert_array_equal(scored.p,apply(inputs,fitted).p)
        directory = OUT/'comparisons/cloud_bias'/fold
        directory.mkdir(parents=True)
        scored.to_parquet(directory/'predictions.parquet',index=False)
        scores[fold] = {name:metrics(scored,name) for name in ('p','p_reference')}
        assert abs(scores[fold]['p_reference']['W_pct']-REFERENCE[fold])<1e-10
        save(directory/'metrics.json',scores[fold])
        save(directory/'application.json',{'passed':True,'rows':len(scored),'full_replay_max_error':0.,'coefficient_sha256':digest(OUT/'coefficients.json'),'prediction_sha256':digest(directory/'predictions.parquet'),'nonfinite_identity_rows':int(scored.cloud_bin.eq(-1).sum()),'capacity_clip_count':int(scored.capacity_clipped.sum()),'night_zero':bool(scored.loc[scored.p_reference.eq(0),'p'].eq(0).all()),'labels_not_used_in_apply':True})
    eligible = all(scores[fold]['p']['W']<scores[fold]['p_reference']['W'] for fold in FOLDS)
    record = {'arm':'cloud_bias','scores':scores,'eligible':eligible,'fixed_cloud_shrink':.5,'alpha_optimization':False}
    save(OUT/'comparisons/cloud_bias/decision.json',record)
    save(OUT/'results.json',{'records':[record],'selected':record if eligible else None,'reference_retained':not eligible,'candidate_count':1,'real_scalar_fit_count':4,'tree_fits':0,'loaded_existing_coefficients':False,'confirmation_loaded':False,'test_loaded':False,'exported':False,'primary_fit_partly_in_sample':True,'all_history_exposed':True})
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
        from sky_math import self_check
        with threadpool_limits(limits=16):
            save(OUT/'controller_start.json',{'identity':resource(),'utc':now(),'scalar_fit_budget':4,'tree_fit_budget':0})
            fixtures = self_check()
            save(OUT/'evidence/selfchecks.json',{'passed':True,'utc':now(),'fixtures':fixtures,'real_scalar_fits':0})
            prepare()
            execute()
            save(OUT/'controller_receipt.json',{'exit_code':0,'finished_utc':now(),'identity':resource(),'real_scalar_fit_count':4,'tree_fits':0})
            print('SKY WAVE TERMINAL',flush=True)
if __name__=='__main__':
    main()
