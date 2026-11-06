# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm"]
# ///
# How to run: called ONLY after released six-fit controller completes.
"""Frozen diagnostics and new-namespace export without reselection."""
import json
import shutil
import subprocess
import sys
import zipfile
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen inference and score contract
from renew_final_common import ROOT,OUT,CPU,RENEW,CANDIDATE,ALPHA,COMPOSITION,save,digest,now
from renew_final_predict import temporal,compose


def finish() -> None:
    from final_metrics import metrics
    old_paths = [RENEW/'recency_wave/trials/decay180/recent'/f'seed{s}' for s in range(3)]
    specifications = {'old_cutoff_march_may':('march_may','march_may',old_paths),'latest_cutoff_march_may':('march_may','latest',[OUT/'models/latest'/f'seed{s}' for s in range(3)]),'test':('test','test',[OUT/'models/test'/f'seed{s}' for s in range(3)])}
    results = {}
    for name,(feature_split,base_split,paths) in specifications.items():
        frame = pd.read_parquet(OUT/'data'/feature_split/'evaluation.parquet')
        base = pd.read_parquet(OUT/'data'/base_split/'cpu_base.parquet')
        raw = temporal(frame,paths)
        prediction = compose(frame,base,raw)
        coverage = pd.read_parquet(OUT/'data'/feature_split/'coverage.parquet')
        checked = prediction.merge(coverage,on=['ts','grp'],validate='one_to_one')
        assert checked.loc[checked.night,'p'].eq(0).all() and len(checked)==len(base)
        if name!='old_cutoff_march_may':
            for seed,path in enumerate(paths):
                saved = pd.read_parquet(path/'daylight_raw.parquet')
                pd.testing.assert_frame_equal(raw[['ts','grp']],saved[['ts','grp']])
                np.testing.assert_array_equal(raw[f'seed{seed}_raw'],saved.p_raw)
        directory = OUT/'predictions'/name
        directory.mkdir(parents=True,exist_ok=True)
        raw.to_parquet(directory/'signed_seeds.parquet',index=False)
        prediction.to_parquet(directory/'predictions.parquet',index=False)
        save(directory/'replay.json',{'passed':True,'rows':len(prediction),'night_zero':True,'prediction_sha256':digest(directory/'predictions.parquet'),'negative_raw_seed_values':int((raw[['seed0_raw','seed1_raw','seed2_raw']]<0).to_numpy().sum()),'capacity_clip_count':int(prediction.capacity_clipped.sum())})
        results[name] = prediction
    save(OUT/'prediction_freeze.json',{'utc':now(),'before_confirmation_labels':True,'sha256':{name:digest(OUT/'predictions'/name/'predictions.parquet') for name in results}})
    march = pd.Timestamp('2025-03-01',tz='Asia/Seoul')
    june = pd.Timestamp('2025-06-01',tz='Asia/Seoul')
    labels = pd.read_parquet(CPU/'final/outer_predictions.parquet',columns=['ts','grp','y','smp','k'],filters=[('ts','>',march),('ts','<=',june)])
    fresh_labels = pd.read_parquet(CPU/'deployment_check/paired_predictions.parquet',columns=['ts','grp','y','smp','k'])
    pd.testing.assert_frame_equal(labels.reset_index(drop=True),fresh_labels.reset_index(drop=True))
    scores = {}
    for name in ('old_cutoff_march_may','latest_cutoff_march_may'):
        scored = results[name].merge(labels,on=['ts','grp'],how='outer',validate='one_to_one',indicator=True)
        assert scored._merge.eq('both').all() and len(scored)==4416
        scored = scored.drop(columns='_merge')
        scored.to_parquet(OUT/'predictions'/name/'scored_predictions.parquet',index=False)
        scores[name] = {column:metrics(scored,column) for column in ('p_cpu','p_reference','p')}
    save(OUT/'diagnostic_metrics.json',{'scores':scores,'descriptive_only':True,'no_reselection':True,'all_history_exposed':True})
    prediction = results['test']
    assert len(prediction)==17520 and not prediction.duplicated(['ts','grp']).any()
    CANDIDATE.mkdir(exist_ok=False)
    shutil.copyfile(ROOT/'submission/autoresearch_candidate/composition.csv',CANDIDATE/'composition.csv')
    assert digest(CANDIDATE/'composition.csv')==COMPOSITION
    export = prediction.sort_values(['grp','ts'])
    pd.DataFrame({'group':export.grp,'ts':export.ts.astype(str),'forecast_kwh':np.round(export.p.to_numpy(),3)}).to_csv(CANDIDATE/'forecast.csv',index=False)
    with zipfile.ZipFile(CANDIDATE/'submission_files.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for name in ('composition.csv','forecast.csv'):
            archive.write(CANDIDATE/name,name)
    validation = subprocess.run([sys.executable,str(ROOT/'submission/validate_artifacts.py'),str(CANDIDATE),'--self-check'],capture_output=True,text=True,check=False)
    (OUT/'export_validation.log').write_text(validation.stdout+validation.stderr,encoding='utf-8')
    assert validation.returncode==0,validation.stdout+validation.stderr
    save(CANDIDATE/'manifest.json',{'protocol_sha256':digest(OUT/'protocol.json'),'prepared_manifest_sha256':digest(OUT/'prepared_manifest.json'),'coefficient_sha256':digest(OUT/'selected_coefficients.json'),'alpha':ALPHA,'calibration':'temperature_then_snow, fixed shrink0.5','new_model_count':6,'model_sha256':{str(p.relative_to(OUT)):digest(p) for p in (OUT/'models').rglob('model.txt')},'files_sha256':{n:digest(CANDIDATE/n) for n in ('composition.csv','forecast.csv','submission_files.zip')},'diagnostic_metrics':scores,'no_confirmation_reselection':True,'official_score_available':False})
    (CANDIDATE/'README.md').write_text('''# 재검증 후보 제출 파일\n\n기존 CPU 예측에 반감기 180일 시계열 모델을 고정 비율로 혼합한 뒤, 고정된 기온·적설 보정을 적용했습니다. 조합은 기존 253개 발전소 배정과 바이트 단위로 동일합니다.\n\nforecast.csv는 17,520개 그룹·시간 예측을 소수 셋째 자리까지 기록합니다. submission_files.zip에는 composition.csv와 forecast.csv만 포함됩니다.\n\n보정 계수는 개발 기본 구간에서만 추정했습니다. 해당 구간 개선은 일부 표본 내 보정 효과이며, 모든 과거 구간은 이미 노출된 개발 데이터입니다. 2025년 3~5월 결과는 설명용 진단으로만 기록했고 모델·계수 재선택에 사용하지 않았습니다. 실제 대회 점수나 업로드 성공을 주장하지 않습니다.\n\n전체 재현 정보와 진단 결과는 manifest.json 및 analysis_outputs/renew_20261105/final/에 있습니다. 기존 제출 후보는 변경하지 않았습니다.\n''',encoding='utf-8')
    save(OUT/'export_receipt.json',{'passed':True,'candidate':str(CANDIDATE.relative_to(ROOT)),'forecast_rows':17520,'sites':253,'composition_sha256':COMPOSITION,'validator_exit_code':validation.returncode,'uploaded':False})
