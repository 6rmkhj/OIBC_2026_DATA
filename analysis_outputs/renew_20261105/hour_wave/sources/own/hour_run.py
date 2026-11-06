# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/hour_run.py --prepare; --run ONLY after release.json.
"""One fixed hour-stage candidate with an explicit barrier before real factor fits."""
from dataclasses import asdict
import json
import msvcrt
import sys
from hour_common import ROOT,OUT,FOLDS,REFERENCE,BINS,environment,install_frozen,configure,resource,save,digest,now

def main() -> None:
    environment()
    from hour_prepare import freeze,prepare
    with (OUT/'controller.lock').open('a+b') as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        freeze()
        install_frozen()
        configure()
        import numpy as np
        import pandas as pd  # noqa: PANDAS_OK -- exact original scoring and calibration contracts
        from threadpoolctl import threadpool_limits
        from final_metrics import metrics
        from cal_math import Factor
        from hour_math import HourFactors,fit,apply
        from hour_checks import self_check
        with threadpool_limits(limits=16):
            if sys.argv[1:]==['--prepare']:
                self_check()
                prepare()
                save(OUT/'evidence/prefit_checks.json',{'passed':True,'utc':now(),'identity':resource(),'protocol_sha256':digest(OUT/'protocol.json'),'prepared_manifest_sha256':digest(OUT/'prepared_manifest.json'),'real_scalar_fits':0,'tree_fits':0})
                print('HOUR PREFIT READY',flush=True)
                return
            assert sys.argv[1:]==['--run']
            release = json.loads((OUT/'release.json').read_text(encoding='utf-8'))
            assert release['approved'] and release['protocol_sha256']==digest(OUT/'protocol.json') and release['prepared_manifest_sha256']==digest(OUT/'prepared_manifest.json')
            for path,sha in json.loads((OUT/'prepared_manifest.json').read_text(encoding='utf-8')).items():
                assert digest(OUT/path)==sha,path
            save(OUT/'controller_start.json',{'identity':resource(),'utc':now(),'real_scalar_fit_budget':5,'tree_fit_budget':0})
            coefficient_path = OUT/'coefficients.json'
            loaded = coefficient_path.exists()
            if not loaded:
                primary = pd.read_parquet(OUT/'data/primary/rows.parquet')
                fitted = fit(primary)
                save(coefficient_path,{'fit_period':FOLDS['primary'],'target_source':'data/primary/rows.parquet','target_source_sha256':digest(OUT/'data/primary/rows.parquet'),'fit_columns':['ts','p_reference','y','smp','k'],'timezone':'Asia/Seoul','hour_bins':BINS,'factors':asdict(fitted)})
            stored = json.loads(coefficient_path.read_text(encoding='utf-8'))
            assert stored['target_source_sha256']==digest(OUT/'data/primary/rows.parquet')
            fitted = HourFactors(tuple(Factor(**item) for item in stored['factors']['hours']))
            scores = {}
            for fold in FOLDS:
                inputs = pd.read_parquet(OUT/'data'/fold/'apply_inputs.parquet')
                assert list(inputs)==['ts','grp','p_reference','static_capacity']
                prediction = apply(inputs,fitted)
                labels = pd.read_parquet(OUT/'data'/fold/'rows.parquet',columns=['ts','grp','y','smp','k'])
                frame = prediction.merge(labels,on=['ts','grp'],validate='one_to_one',sort=False)
                assert len(frame)==len(inputs)==len(labels)
                pd.testing.assert_frame_equal(frame[['ts','grp']],inputs[['ts','grp']])
                directory = OUT/'comparisons/hour_bias'/fold
                directory.mkdir(parents=True,exist_ok=True)
                frame.to_parquet(directory/'predictions.parquet',index=False)
                np.testing.assert_array_equal(apply(inputs,fitted).p,frame.p)
                scores[fold] = {name:metrics(frame,name) for name in ('p','p_reference')}
                assert abs(scores[fold]['p_reference']['W_pct']-REFERENCE[fold])<1e-10
                save(directory/'metrics.json',scores[fold])
                save(directory/'application.json',{'passed':True,'rows':len(frame),'exact_replay':True,'zero_reference_stays_zero':bool(frame.loc[frame.p_reference.eq(0),'p'].eq(0).all()),'capacity_clip_count':int(frame.capacity_clipped.sum()),'coefficient_sha256':digest(coefficient_path),'prediction_sha256':digest(directory/'predictions.parquet'),'labels_not_used_in_apply':True})
            eligible = all(scores[f]['p']['W']<scores[f]['p_reference']['W'] for f in FOLDS)
            record = {'arm':'hour_bias','scores':scores,'eligible':eligible,'fixed_hour_shrink':.5,'alpha_optimization':False}
            save(OUT/'comparisons/hour_bias/decision.json',record)
            save(OUT/'results.json',{'records':[record],'selected':record if eligible else None,'reference_retained':not eligible,'candidate_count':1,'real_scalar_fit_count':0 if loaded else 5,'loaded_existing_coefficients':loaded,'tree_fits':0,'confirmation_loaded':False,'test_loaded':False,'primary_fit_partly_in_sample':True,'historical_exposure':'All periods historically exposed; not independent holdout.'})
            protocol = json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
            after = {p:digest(ROOT/p) for p in protocol['protected_sha256']}
            assert after==protocol['protected_sha256']
            save(OUT/'preservation.json',{'unchanged':True,'files':len(after),'sha256':after})
            save(OUT/'controller_receipt.json',{'exit_code':0,'identity':resource(),'finished_utc':now(),'real_scalar_fit_count':0 if loaded else 5,'tree_fits':0})
            print('HOUR WAVE TERMINAL','SELECTED' if eligible else 'REFERENCE RETAINED',flush=True)
if __name__=='__main__':
    main()
