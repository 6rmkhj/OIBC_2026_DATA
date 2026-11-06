# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/sky_final_run.py
"""Single authorized no-fit export of the accepted frozen cloud calibration."""
import json
import msvcrt
import shutil
import subprocess
import sys
import zipfile
from sky_final_common import ROOT,OUT,PRIOR,WEATHER,WAVE,CANDIDATE,COMPOSITION,COEFFICIENT,SPLITS,environment,install_frozen,configure,resource,save,digest,now

def export() -> None:
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- preserve exact saved-prediction and metric contracts
    from sky_math import CloudFactors,apply
    from cal_math import Factor
    from final_metrics import metrics
    coefficients = json.loads((OUT/'selected_cloud_coefficients.json').read_text(encoding='utf-8'))
    fitted = CloudFactors(tuple(Factor(**item) for item in coefficients['factors']['clouds']))
    capacities = json.loads((WEATHER/'static_capacity.json').read_text(encoding='utf-8'))
    results = {}
    for split in SPLITS:
        source = PRIOR/'predictions'/split/'predictions.parquet'
        frame = pd.read_parquet(source,columns=['ts','grp','p','static_capacity']).rename(columns={'p':'p_reference'})
        assert len(frame)==(17520 if split=='test' else 4416)
        assert not frame.duplicated(['ts','grp']).any()
        np.testing.assert_array_equal(frame.static_capacity,frame.grp.map(capacities))
        feature_split = 'test' if split=='test' else 'march_may'
        feature_path = WEATHER/'data'/feature_split/'evaluation.parquet'
        features = pd.read_parquet(feature_path,columns=['ts','grp','wb_cloud'])
        coverage = pd.read_parquet(WEATHER/'data'/feature_split/'coverage.parquet')
        assert not features.duplicated(['ts','grp']).any()
        reference_keys = frame[['ts','grp']].copy()
        frame = frame.merge(features,on=['ts','grp'],how='left',sort=False,validate='one_to_one',indicator=True)
        checked = frame.merge(coverage,on=['ts','grp'],how='left',sort=False,validate='one_to_one')
        assert checked.night.notna().all()
        assert checked._merge.eq('left_only').eq(checked.night).all()
        assert int(checked._merge.eq('both').sum())==len(features)
        assert checked.loc[checked.night,'p_reference'].eq(0).all()
        frame = frame[['ts','grp','p_reference','wb_cloud','static_capacity']]
        pd.testing.assert_frame_equal(frame[['ts','grp']],reference_keys)
        prediction = apply(frame,fitted)
        pd.testing.assert_frame_equal(prediction[list(frame)],frame)
        np.testing.assert_array_equal(prediction.p,apply(frame,fitted).p)
        assert prediction.loc[prediction.p_reference.eq(0),'p'].eq(0).all()
        directory = OUT/'predictions'/split
        directory.mkdir(parents=True)
        frame.to_parquet(directory/'apply_inputs.parquet',index=False)
        prediction.to_parquet(directory/'predictions.parquet',index=False)
        save(directory/'replay.json',{'passed':True,'rows':len(prediction),'source_sha256':digest(source),'weather_sha256':digest(feature_path),'projected_columns':['ts','grp','wb_cloud'],'daylight_rows':len(features),'allnight_rows':int(checked.night.sum()),'unmatched_exact_allnight':True,'finite_gt100_rows':int((np.isfinite(frame.wb_cloud)&frame.wb_cloud.gt(100)).sum()),'coefficient_sha256':COEFFICIENT,'prediction_sha256':digest(directory/'predictions.parquet'),'full_replay_max_error':0.,'zero_reference_stays_zero':True,'capacity_clip_count':int(prediction.capacity_clipped.sum())})
        results[split] = prediction
    save(OUT/'prediction_freeze.json',{'utc':now(),'before_diagnostic_labels':True,'coefficient_sha256':COEFFICIENT,'sha256':{split:digest(OUT/'predictions'/split/'predictions.parquet') for split in SPLITS}})
    scores = {}
    label_receipts = []
    for split in SPLITS:
        if split=='test':
            continue
        label_receipts.append({'split':split,'label_read_started_utc':now(),'prediction_freeze_sha256':digest(OUT/'prediction_freeze.json')})
        labels = pd.read_parquet(PRIOR/'predictions'/split/'scored_predictions.parquet',columns=['ts','grp','y','smp','k'])
        scored = results[split].merge(labels,on=['ts','grp'],how='outer',sort=False,validate='one_to_one',indicator=True)
        assert scored._merge.eq('both').all() and len(scored)==4416
        scored = scored.drop(columns='_merge')
        pd.testing.assert_frame_equal(scored[['ts','grp']],results[split][['ts','grp']])
        scored.to_parquet(OUT/'predictions'/split/'scored_predictions.parquet',index=False)
        scores[split] = {name:metrics(scored,name) for name in ('p_reference','p')}
    save(OUT/'evidence/diagnostic_label_reads.json',label_receipts)
    save(OUT/'diagnostic_metrics.json',{'scores':scores,'descriptive_only':True,'no_reselection':True,'all_history_exposed':True,'new_fits':0})
    prediction = results['test'].sort_values(['grp','ts'])
    CANDIDATE.mkdir(exist_ok=False)
    shutil.copyfile(ROOT/'submission/autoresearch_candidate/composition.csv',CANDIDATE/'composition.csv')
    assert digest(CANDIDATE/'composition.csv')==COMPOSITION
    pd.DataFrame({'group':prediction.grp,'ts':prediction.ts.astype(str),'forecast_kwh':np.round(prediction.p.to_numpy(),3)}).to_csv(CANDIDATE/'forecast.csv',index=False)
    with zipfile.ZipFile(CANDIDATE/'submission_files.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for name in ('composition.csv','forecast.csv'):
            archive.write(CANDIDATE/name,name)
    validation = subprocess.run([sys.executable,str(ROOT/'submission/validate_artifacts.py'),str(CANDIDATE),'--self-check'],capture_output=True,text=True,check=False)
    (OUT/'export_validation.log').write_text(validation.stdout+validation.stderr,encoding='utf-8')
    assert validation.returncode==0,validation.stdout+validation.stderr
    development = json.loads((WAVE/'results.json').read_text(encoding='utf-8'))
    assert development['selected']['arm']=='cloud_bias' and development['selected']['eligible']
    development_gain = {fold:{'reference':entry['p_reference'],'cloud':entry['p'],'W_reduction':entry['p_reference']['W']-entry['p']['W'],'W_pct_reduction':entry['p_reference']['W_pct']-entry['p']['W_pct']} for fold,entry in development['selected']['scores'].items()}
    protocol = json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
    save(CANDIDATE/'manifest.json',{'protocol_sha256':digest(OUT/'protocol.json'),'coefficient_sha256':COEFFICIENT,'prediction_freeze_sha256':digest(OUT/'prediction_freeze.json'),'source_input_sha256':protocol['input_sha256'],'recipe':protocol['recipe'],'new_scalar_fits':0,'new_tree_fits':0,'development_gain':development_gain,'diagnostic_metrics':scores,'diagnostics_descriptive_only':True,'no_reselection':True,'all_history_exposed':True,'primary_calibration_partly_in_sample':True,'reference_candidate':'submission/renew_hour_candidate_20261105','original_candidate':'submission/renew_candidate_20261105','preserved_candidate_sha256':{name:{p.name:digest(p) for p in (ROOT/'submission'/name).iterdir() if p.is_file()} for name in ('renew_candidate_20261105','renew_hour_candidate_20261105')},'original_user_reported_official_score':6454220836,'original_score_provenance':'User-reported; original submission unchanged','official_score_available':False,'uploaded':False,'files_sha256':{name:digest(CANDIDATE/name) for name in ('composition.csv','forecast.csv','submission_files.zip')}})
    (CANDIDATE/'README.md').write_text("""# 구름량 보정 후보 제출 파일

기온·적설 보정과 시간대 보정이 끝난 기존 예측에 공급자 B 구름량 보정을 한 번 추가했습니다. 고정 구간은 20 미만, 20 이상 50 미만, 50 이상 80 미만, 80 이상이며 비유한 값은 보정하지 않습니다. 유한한 값은 100을 조금 넘더라도 그대로 유지합니다. 새 보정만 0.5 비율로 축소하고 그룹 설비용량 범위로 제한했습니다. 이번 내보내기에서는 모델이나 계수를 새로 학습하지 않았습니다.

submission_files.zip에는 composition.csv와 forecast.csv만 있습니다. 조합은 기존 253개 발전소 배정과 바이트 단위로 같고, 예측은 17,520개 그룹·시간 행을 소수 셋째 자리로 반올림했습니다.

시간대 후보 대비 개발 기본 구간 W는 11.912571%에서 11.792837%로, 최근 구간은 10.998535%에서 10.955416%로 개선되었습니다. 기본 구간에서 계수를 추정했으므로 일부 표본 내 효과입니다. 모든 과거 구간은 이미 노출되었고 독립 검증 구간이 아닙니다. 2025년 3~5월 진단은 예측을 먼저 고정한 뒤 설명용으로만 기록했으며 후보나 계수 재선택에 쓰지 않았습니다.

사용자가 알려 준 공식 점수 6,454,220,836의 원래 renew_candidate와 이전 renew_hour_candidate 제출 파일을 모두 그대로 보존했습니다. 이번 renew_sky_candidate의 공식 점수는 아직 없고 업로드하지 않았습니다. 시간대 후보와의 설명용 진단 비교 및 세 후보의 계보·해시는 manifest.json에 있습니다.

전체 검증 증거는 analysis_outputs/renew_20261105/sky_final/에 있습니다.
""",encoding='utf-8')
    save(OUT/'export_receipt.json',{'passed':True,'candidate':str(CANDIDATE.relative_to(ROOT)),'sites':253,'forecast_rows':17520,'composition_sha256':COMPOSITION,'validator_exit_code':validation.returncode,'scalar_fits':0,'tree_fits':0,'uploaded':False})
    after = {path:digest(ROOT/path) for path in protocol['protected_sha256']}
    assert after==protocol['protected_sha256']
    save(OUT/'preservation.json',{'unchanged':True,'files':len(after),'sha256':after})
    save(OUT/'candidate_artifact_hashes.json',{p.name:digest(p) for p in CANDIDATE.iterdir() if p.is_file()})

def main() -> None:
    environment()
    from sky_final_freeze import freeze
    with (OUT/'controller.lock').open('a+b') as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        freeze()
        install_frozen()
        configure()
        from threadpoolctl import threadpool_limits
        with threadpool_limits(limits=16):
            save(OUT/'controller_start.json',{'identity':resource(),'utc':now(),'scalar_fits':0,'tree_fits':0})
            export()
            save(OUT/'controller_receipt.json',{'exit_code':0,'finished_utc':now(),'identity':resource(),'scalar_fits':0,'tree_fits':0,'candidate':str(CANDIDATE.relative_to(ROOT))})
            print('SKY FINAL EXPORT COMPLETE',flush=True)
if __name__=='__main__':
    main()
