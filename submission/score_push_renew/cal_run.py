# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/cal_run.py --prepare; then --run after root release.
"""Three fixed scalar-calibration recipes with a prefit release barrier."""
from dataclasses import asdict
import json
import msvcrt
import os
import sys
from cal_common import ROOT,OUT,FOLDS,ARMS,REFERENCE,environment,install_frozen,configure,resource,save,digest,now


def main() -> None:
    environment()
    from cal_prepare import freeze,prepare
    with (OUT/'controller.lock').open('a+b') as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        freeze()
        install_frozen()
        configure()
        from threadpoolctl import threadpool_limits
        from cal_checks import self_check
        from cal_math import Calibration,Factor,fit,apply
        import numpy as np
        import pandas as pd  # noqa: PANDAS_OK -- frozen calibration metric contract
        from final_metrics import metrics
        with threadpool_limits(limits=16):
            if sys.argv[1:]==['--prepare']:
                self_check()
                prepare()
                save(OUT/'evidence/prefit_checks.json',{'passed':True,'utc':now(),'protocol_sha256':digest(OUT/'protocol.json'),'prepared_manifest_sha256':digest(OUT/'prepared_manifest.json'),'identity':resource(),'actual_calibration_fits':0})
                print('CALIBRATION PREFIT READY',flush=True)
                return
            assert sys.argv[1:]==['--run']
            release = json.loads((OUT/'release.json').read_text())
            assert release['approved'] and release['protocol_sha256']==digest(OUT/'protocol.json') and release['prepared_manifest_sha256']==digest(OUT/'prepared_manifest.json')
            for name,sha in json.loads((OUT/'prepared_manifest.json').read_text()).items():
                assert digest(OUT/name)==sha,name
            save(OUT/'controller_start.json',{'identity':resource(),'utc':now(),'environment':{k:os.environ.get(k) for k in ('TMPDIR','TMP','TEMP','NODE_COMPILE_CACHE','BUN_RUNTIME_TRANSPILER_CACHE_PATH','PYTHONDONTWRITEBYTECODE','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}})
            coefficient_path = OUT/'coefficients.json'
            loaded = coefficient_path.exists()
            if not loaded:
                primary = pd.read_parquet(OUT/'data/primary/rows.parquet')
                fitted = fit(primary)
                save(coefficient_path,{'fit_period':FOLDS['primary'],'target_source':'data/primary/rows.parquet','target_source_sha256':digest(OUT/'data/primary/rows.parquet'),'fit_columns':['ts','y','p_reference','smp','k','wa_temp','extra_wa_snow'],'temperature_then_snow_second_fit':'FULL temperature-adjusted PRIMARY prediction in ratio denominator and monetary weight; NO shrink before second fit','factors':asdict(fitted)})
            stored = json.loads(coefficient_path.read_text())
            assert stored['target_source_sha256']==digest(OUT/'data/primary/rows.parquet')
            factors = stored['factors']
            fitted = Calibration(tuple(Factor(**item) for item in factors['temperature']),Factor(**factors['snow']),Factor(**factors['conditional_snow']))
            records = []
            for arm in ARMS:
                scores = {}
                for fold in FOLDS:
                    inputs = pd.read_parquet(OUT/'data'/fold/'apply_inputs.parquet')
                    prediction = apply(inputs,fitted,arm)
                    labels = pd.read_parquet(OUT/'data'/fold/'rows.parquet',columns=['ts','grp','y','smp','k'])
                    frame = prediction.merge(labels,on=['ts','grp'],validate='one_to_one')
                    assert len(frame)==len(inputs)==len(labels)
                    directory = OUT/'comparisons'/arm/fold
                    directory.mkdir(parents=True,exist_ok=True)
                    frame.to_parquet(directory/'predictions.parquet',index=False)
                    replay = apply(inputs,fitted,arm)
                    np.testing.assert_array_equal(replay.p,frame.p)
                    scores[fold] = {name:metrics(frame,name) for name in ('p','p_reference')}
                    assert abs(scores[fold]['p_reference']['W_pct']-REFERENCE[fold])<1e-10
                    save(directory/'metrics.json',scores[fold])
                    save(directory/'application.json',{'passed':True,'rows':len(frame),'capacity_clip_count':int(frame.capacity_clipped.sum()),'allnight_zero':bool(frame.loc[frame.p_reference.eq(0),'p'].eq(0).all()),'effective_factor_min':float(frame.effective_factor.min()),'effective_factor_max':float(frame.effective_factor.max()),'coefficient_sha256':digest(coefficient_path),'exact_replay':True,'prediction_sha256':digest(directory/'predictions.parquet')})
                eligible = all(scores[f]['p']['W_pct']<REFERENCE[f] for f in FOLDS)
                record = {'arm':arm,'scores':scores,'eligible':eligible,'mean_relative_W':sum(scores[f]['p']['W_pct']/REFERENCE[f] for f in FOLDS)/2,'fixed_shrink':.5,'alpha_optimization':False}
                save(OUT/'comparisons'/arm/'decision.json',record)
                records.append(record)
            eligible = [r for r in records if r['eligible']]
            selected = min(eligible,key=lambda r:r['mean_relative_W']) if eligible else None
            save(OUT/'results.json',{'records':records,'selected':selected,'reference_retained':selected is None,'candidate_count':3,'tree_model_fits':0,'loaded_existing_coefficients':loaded,'confirmation_loaded':False,'test_loaded':False,'primary_fit_partly_in_sample':True})
            protocol = json.loads((OUT/'protocol.json').read_text())
            after = {p:digest(ROOT/p) for p in protocol['protected_sha256']}
            assert after==protocol['protected_sha256']
            save(OUT/'preservation.json',{'unchanged':True,'files':len(after),'sha256':after})
            save(OUT/'controller_receipt.json',{'exit_code':0,'finished_utc':now(),'identity':resource(),'candidate_count':3,'tree_model_fits':0})
            save(OUT/'artifact_hashes.json',{str(p.relative_to(OUT)):digest(p) for p in OUT.rglob('*') if p.is_file() and p.name not in ('artifact_hashes.json','controller.lock','controller.log') and 'tmp' not in p.relative_to(OUT).parts})
            print('CALIBRATION WAVE TERMINAL',selected['arm'] if selected else 'REFERENCE RETAINED',flush=True)

if __name__=='__main__':
    main()
