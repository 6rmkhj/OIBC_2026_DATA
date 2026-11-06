# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/hour_final_run.py
"""Single authorized no-fit export of the accepted frozen hour calibration."""
import json
import msvcrt
import shutil
import subprocess
import sys
import zipfile
from hour_final_common import ROOT,OUT,PRIOR,HOUR,CANDIDATE,COMPOSITION,COEFFICIENT,SPLITS,environment,install_frozen,configure,resource,save,digest,now

def export() -> None:
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- preserve exact saved-prediction and metric contracts
    from hour_math import HourFactors,apply
    from cal_math import Factor
    from final_metrics import metrics
    coefficients = json.loads((OUT/'selected_hour_coefficients.json').read_text(encoding='utf-8'))
    fitted = HourFactors(tuple(Factor(**item) for item in coefficients['factors']['hours']))
    capacities = json.loads((PRIOR/'static_capacity.json').read_text(encoding='utf-8'))
    results = {}
    for split in SPLITS:
        source = PRIOR/'predictions'/split/'predictions.parquet'
        frame = pd.read_parquet(source,columns=['ts','grp','p','static_capacity']).rename(columns={'p':'p_reference'})
        assert len(frame)==(17520 if split=='test' else 4416)
        assert not frame.duplicated(['ts','grp']).any()
        np.testing.assert_array_equal(frame.static_capacity,frame.grp.map(capacities))
        prediction = apply(frame,fitted)
        pd.testing.assert_frame_equal(prediction[list(frame)],frame)
        np.testing.assert_array_equal(prediction.p,apply(frame,fitted).p)
        assert prediction.loc[prediction.p_reference.eq(0),'p'].eq(0).all()
        directory = OUT/'predictions'/split
        directory.mkdir(parents=True)
        prediction.to_parquet(directory/'predictions.parquet',index=False)
        save(directory/'replay.json',{'passed':True,'rows':len(prediction),'source_sha256':digest(source),'coefficient_sha256':COEFFICIENT,'prediction_sha256':digest(directory/'predictions.parquet'),'full_replay_max_error':0.,'zero_reference_stays_zero':True,'capacity_clip_count':int(prediction.capacity_clipped.sum())})
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
    development = json.loads((HOUR/'results.json').read_text(encoding='utf-8'))
    assert development['selected']['arm']=='hour_bias' and development['selected']['eligible']
    development_gain = {fold:{'reference':entry['p_reference'],'hour':entry['p'],'W_reduction':entry['p_reference']['W']-entry['p']['W'],'W_pct_reduction':entry['p_reference']['W_pct']-entry['p']['W_pct']} for fold,entry in development['selected']['scores'].items()}
    protocol = json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
    save(CANDIDATE/'manifest.json',{'protocol_sha256':digest(OUT/'protocol.json'),'coefficient_sha256':COEFFICIENT,'prediction_freeze_sha256':digest(OUT/'prediction_freeze.json'),'source_input_sha256':protocol['input_sha256'],'recipe':protocol['recipe'],'new_scalar_fits':0,'new_tree_fits':0,'development_gain':development_gain,'diagnostic_metrics':scores,'diagnostics_descriptive_only':True,'no_reselection':True,'all_history_exposed':True,'primary_calibration_partly_in_sample':True,'original_candidate':'submission/renew_candidate_20261105','original_user_reported_official_score':6454220836,'original_score_provenance':'User-reported; original submission unchanged','official_score_available':False,'uploaded':False,'files_sha256':{name:digest(CANDIDATE/name) for name in ('composition.csv','forecast.csv','submission_files.zip')}})
    (CANDIDATE/'README.md').write_text("""# 시간대 보정 후보 제출 파일

기존 기온·적설 보정이 끝난 예측에, 한국시간 기준 5개 시간대의 고정 보정 계수를 한 번 적용했습니다. 시간대는 [0,10), [10,12), [12,14), [14,16), [16,24)이며 추가 보정만 0.5 비율로 축소한 뒤 그룹 설비용량 범위로 제한했습니다. 이번 내보내기에서는 모델이나 보정 계수를 새로 학습하지 않았습니다.

제출용 submission_files.zip에는 composition.csv와 forecast.csv만 들어 있습니다. 조합은 기존 253개 발전소 배정과 바이트 단위로 같고, 예측은 17,520개 그룹·시간 행을 소수 셋째 자리로 반올림했습니다.

개발 기본 구간 W는 11.959229%에서 11.912571%로, 최근 구간은 11.000953%에서 10.998535%로 개선되었습니다. 계수는 기본 구간에서 추정했으므로 해당 개선은 일부 표본 내 효과입니다. 모든 과거 구간은 이미 노출된 데이터이며 독립 검증 구간이라고 주장하지 않습니다. 2025년 3~5월 진단은 예측을 먼저 고정한 뒤 기록한 설명용 결과이며 계수나 후보 재선택에 사용하지 않았습니다.

사용자가 알려 준 기존 renew_candidate의 공식 점수 6,454,220,836에 해당하는 제출 파일은 그대로 보존했습니다. 이 새 후보의 공식 점수는 아직 없으며 업로드하지 않았습니다.

계수·원본·출력 해시, 개발 개선 및 설명용 진단은 manifest.json에, 실행·검증 증거는 analysis_outputs/renew_20261105/hour_final/에 있습니다.
""",encoding='utf-8')
    save(OUT/'export_receipt.json',{'passed':True,'candidate':str(CANDIDATE.relative_to(ROOT)),'sites':253,'forecast_rows':17520,'composition_sha256':COMPOSITION,'validator_exit_code':validation.returncode,'scalar_fits':0,'tree_fits':0,'uploaded':False})
    after = {path:digest(ROOT/path) for path in protocol['protected_sha256']}
    assert after==protocol['protected_sha256']
    save(OUT/'preservation.json',{'unchanged':True,'files':len(after),'sha256':after})
    save(OUT/'candidate_artifact_hashes.json',{p.name:digest(p) for p in CANDIDATE.iterdir() if p.is_file()})

def main() -> None:
    environment()
    from hour_final_freeze import freeze
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
            print('HOUR FINAL EXPORT COMPLETE',flush=True)
if __name__=='__main__':
    main()
