# 전체 실험·시도 상태표

확인 시각: **2026-11-07 17:49:32 KST**.

[프로젝트 요약](../../README.md) · [필터링 가능한 전체 CSV](experiments.csv)

현재 단계의 ID는 고정된 전체 설정 큐를 포함합니다. `pending`은 아직 실행되지 않았다는 뜻이며 실패가 아닙니다. 과거 표의 `keep`/`discard`는 당시 탐색 결정이지 공식 점수 상승이나 실패를 뜻하지 않습니다. 같은 ID의 재시도는 별도 과거 로그 행으로 남깁니다.

현재 5개 기간 검증에서 결과 저장이 실패한 실험은 완료 영수증 수와 별도로 `failed`로 표시합니다. 모델의 과학적 적격 여부를 최종 결과 없이 추정하지 않습니다.

## 기초 데이터·예보·구성·점수 검증

기존 make_submission 실행 경로와 입력 품질·예보·발전소 구성·후처리 분석을 정리했습니다. 아래 행은 학습 횟수가 아닌 검토 문서이며, 기존 val_summary는 평가 기간의 자료로 발전소 구성을 선택한 개발 점수입니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| ANALYSIS_MEMO | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/ANALYSIS_MEMO.md) |
| bid_postproc_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/bid_postproc_report.md) |
| comp_verify_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/comp_verify_report.md) |
| composition_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/composition_report.md) |
| forecast_skill_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/forecast_skill_report.md) |
| gen_quality_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/gen_quality_report.md) |
| model_validation_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/model_validation_report.md) |
| smp_weights_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/smp_weights_report.md) |
| spatial_corr_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/spatial_corr_report.md) |
| ver_l1cal_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/ver_l1cal_report.md) |
| verify_composition_math_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_composition_math_report.md) |
| verify_composition_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_composition_report.md) |
| verify_fc_round_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_fc_round_report.md) |
| verify_forecast_input_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_forecast_input_report.md) |
| verify_genq_math_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_genq_math_report.md) |
| verify_gq_cleaning_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_gq_cleaning_report.md) |
| verify_gq_numbers_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_gq_numbers_report.md) |
| verify_l1_calib_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_l1_calib_report.md) |
| verify_l1_calib_repro_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_l1_calib_repro_report.md) |
| verify_round_provider_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_round_provider_report.md) |

## 초기 수상 도전 파이프라인

이전 연도에서 2개 구성과 5개 혼합비, 총 10개 조합을 비교해 inner_twins/direct0.5를 선택했으며, 후기 연간 W_pct는 11.552586으로 기준 11.881605보다 낮았습니다. 표의 10행은 모델 10개가 아닌 조합 평가 수이고, 후보 경로는 submission/award_candidate입니다; 생성 당시 공식 점수는 없었으며 이후 보고된 최초 점수를 어느 파일에 연결할지는 여기서 단정하지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| reference | historical_record | 과거 기록 | — | — | W_pct | 13.7844 | 원본 표/로그 행 1 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 0.0.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |
| reference | historical_record | 과거 기록 | — | — | W_pct | 13.4807 | 원본 표/로그 행 2 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 0.25.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |
| reference | historical_record | 과거 기록 | — | — | W_pct | 13.4126 | 원본 표/로그 행 3 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 0.5.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |
| reference | historical_record | 과거 기록 | — | — | W_pct | 13.5511 | 원본 표/로그 행 4 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 0.75.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |
| reference | historical_record | 과거 기록 | — | — | W_pct | 13.8526 | 원본 표/로그 행 5 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 1.0.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |
| inner_twins | historical_record | 과거 기록 | — | — | W_pct | 13.6476 | 원본 표/로그 행 6 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 0.0.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |
| inner_twins | historical_record | 과거 기록 | — | — | W_pct | 13.3181 | 원본 표/로그 행 7 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 0.25.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |
| inner_twins | historical_record | 과거 기록 | — | — | W_pct | 13.2102 | 원본 표/로그 행 8 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 0.5.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |
| inner_twins | historical_record | 과거 기록 | — | — | W_pct | 13.3134 | 원본 표/로그 행 9 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 0.75.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |
| inner_twins | historical_record | 과거 기록 | — | — | W_pct | 13.5837 | 원본 표/로그 행 10 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 1.0.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |

## Autoresearch 다섯 차례 탐색

results.tsv의 51개 시도 행은 성공 기록 50개와 baseline 사전 검사 실패 1회이며, 같은 baseline ID의 실패와 성공을 합치지 않습니다. 성공 기록은 실제 모델 적합 40회와 무학습 재평가 10회이므로 별도 모델 50개를 뜻하지 않습니다. 최종 선택은 w5_lgb_calibrated이고, 기본 개발 W_pct는 12.695950, 후기 연간은 11.048843(award 기준 11.552586)입니다. 후보 생성 당시에는 미제출 상태였지만 이후 사용자가 6,447,820,797점을 보고했습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| baseline | historical_record | 실행 실패 | — | — | W_pct | — | 원본 표/로그 행 1 (재시도·다른 조건을 합치지 않음). Reproduce unchanged direct 50 percent baseline [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| baseline | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 13.2102 | 원본 표/로그 행 2 (재시도·다른 조건을 합치지 않음). Reproduce unchanged direct 50 percent baseline [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| scored | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.4109 | 원본 표/로그 행 3 (재시도·다른 조건을 합치지 않음). Capacity times SMP times k aligns CF loss with scored kWh [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| capacity | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.3233 | 원본 표/로그 행 4 (재시도·다른 조건을 합치지 않음). Capacity weighting aligns CF loss with group kWh [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| trees800 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.2636 | 원본 표/로그 행 5 (재시도·다른 조건을 합치지 않음). More boosting reduces underfit [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| leaves63 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.4495 | 원본 표/로그 행 6 (재시도·다른 조건을 합치지 않음). More trees and leaves capture weather interactions [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| lr02 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.2295 | 원본 표/로그 행 7 (재시도·다른 조건을 합치지 않음). Slower 800-tree boosting improves generalization [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| l2 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.5860 | 원본 표/로그 행 8 (재시도·다른 조건을 합치지 않음). L2 alternative may offer ensemble diversity [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| recent365 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.3025 | 원본 표/로그 행 9 (재시도·다른 조건을 합치지 않음). One-year half-life adapts to recent fleet and weather [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| recent730 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.2315 | 원본 표/로그 행 10 (재시도·다른 조건을 합치지 않음). Two-year half-life balances adaptation and history [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_baseline | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.2544 | 원본 표/로그 행 11 (재시도·다른 조건을 합치지 않음). Second-wave one-factor w2_baseline [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_baseline_default | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.2102 | 원본 표/로그 행 12 (재시도·다른 조건을 합치지 않음). Reproduce original default seed after seed-zero explicit-vs-default check [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_child100 | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 13.2021 | 원본 표/로그 행 13 (재시도·다른 조건을 합치지 않음). Second-wave one-factor w2_child100 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_child200 | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 13.1849 | 원본 표/로그 행 14 (재시도·다른 조건을 합치지 않음). Second-wave one-factor w2_child200 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_leaves15 | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 13.1052 | 원본 표/로그 행 15 (재시도·다른 조건을 합치지 않음). Second-wave one-factor w2_leaves15 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_lr02 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.2039 | 원본 표/로그 행 16 (재시도·다른 조건을 합치지 않음). Second-wave one-factor w2_lr02 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_n200 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.2133 | 원본 표/로그 행 17 (재시도·다른 조건을 합치지 않음). Second-wave one-factor w2_n200 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_n300 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.1957 | 원본 표/로그 행 18 (재시도·다른 조건을 합치지 않음). Second-wave one-factor w2_n300 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_ramps | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 13.0593 | 원본 표/로그 행 19 (재시도·다른 조건을 합치지 않음). Second-wave one-factor w2_ramps [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_seeds012 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.1993 | 원본 표/로그 행 20 (재시도·다른 조건을 합치지 않음). Second-wave one-factor w2_seeds012 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_leaf15_child100 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.1210 | 원본 표/로그 행 21 (재시도·다른 조건을 합치지 않음). Combine measured promising smaller leaves with w2_leaf15_child100 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_leaf15_seeds | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.1047 | 원본 표/로그 행 22 (재시도·다른 조건을 합치지 않음). Combine measured promising smaller leaves with w2_leaf15_seeds [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_leaf15_ramps | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 13.0075 | 원본 표/로그 행 23 (재시도·다른 조건을 합치지 않음). Combine measured promising smaller leaves with w2_leaf15_ramps [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_blend4 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.0579 | 원본 표/로그 행 24 (재시도·다른 조건을 합치지 않음). Blend-only rescore best measured direct model at 0.4 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_blend6 | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 12.9937 | 원본 표/로그 행 25 (재시도·다른 조건을 합치지 않음). Blend-only rescore best measured direct model at 0.6 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_baseline | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.9937 | 원본 표/로그 행 26 (재시도·다른 조건을 합치지 않음). Third-wave one-factor w3_baseline [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_daily | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 12.8804 | 원본 표/로그 행 27 (재시도·다른 조건을 합치지 않음). Third-wave one-factor w3_daily [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_lead | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.9474 | 원본 표/로그 행 28 (재시도·다른 조건을 합치지 않음). Third-wave one-factor w3_lead [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_leaves7 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.1593 | 원본 표/로그 행 29 (재시도·다른 조건을 합치지 않음). Third-wave one-factor w3_leaves7 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_n600 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.9903 | 원본 표/로그 행 30 (재시도·다른 조건을 합치지 않음). Third-wave one-factor w3_n600 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_seeds | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.9884 | 원본 표/로그 행 31 (재시도·다른 조건을 합치지 않음). Third-wave one-factor w3_seeds [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_daily_lead | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 12.8490 | 원본 표/로그 행 32 (재시도·다른 조건을 합치지 않음). Both daylight summaries and next-hour issued forecasts improved parent; test complementary context [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_context_seeds | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 12.7950 | 원본 표/로그 행 33 (재시도·다른 조건을 합치지 않음). Seed ensemble marginally improved parent; test variance reduction with best measured context [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_blend5 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.8312 | 원본 표/로그 행 34 (재시도·다른 조건을 합치지 않음). Blend-only rescore of best measured context model [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_blend7 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.7996 | 원본 표/로그 행 35 (재시도·다른 조건을 합치지 않음). Blend-only rescore of best measured context model [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w4_baseline | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.7950 | 원본 표/로그 행 36 (재시도·다른 조건을 합치지 않음). Fourth-wave one-factor w4_baseline [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w4_spatial | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.8051 | 원본 표/로그 행 37 (재시도·다른 조건을 합치지 않음). Fourth-wave one-factor w4_spatial [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w4_pooled15 | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 12.7468 | 원본 표/로그 행 38 (재시도·다른 조건을 합치지 않음). Fourth-wave one-factor w4_pooled15 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w4_pooled31 | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 12.7219 | 원본 표/로그 행 39 (재시도·다른 조건을 합치지 않음). Fourth-wave one-factor w4_pooled31 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w4_pooled_spatial | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.7637 | 원본 표/로그 행 40 (재시도·다른 조건을 합치지 않음). Pooled groups improved; test whether spatial heterogeneity adds complementary group information [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w4_pooled_n600 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.7383 | 원본 표/로그 행 41 (재시도·다른 조건을 합치지 않음). One capacity check: pooled data may support more trees; n600 was marginally useful earlier [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w4_blend5 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.7841 | 원본 표/로그 행 42 (재시도·다른 조건을 합치지 않음). Blend-only refinement after measured pooled-group gain [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w4_blend7 | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 12.6964 | 원본 표/로그 행 43 (재시도·다른 조건을 합치지 않음). Blend-only refinement after measured pooled-group gain [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w5_baseline | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.6964 | 원본 표/로그 행 44 (재시도·다른 조건을 합치지 않음). Final distinct-learner family w5_baseline [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w5_hist31 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.8837 | 원본 표/로그 행 45 (재시도·다른 조건을 합치지 않음). Final distinct-learner family w5_hist31 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w5_hist15 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.7963 | 원본 표/로그 행 46 (재시도·다른 조건을 합치지 않음). Final distinct-learner family w5_hist15 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w5_original_calibrated | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.2100 | 원본 표/로그 행 47 (재시도·다른 조건을 합치지 않음). Analytical weighted-median single blend coefficient fitted only on inner selection; no model fit [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w5_lgb_calibrated | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 12.6960 | 원본 표/로그 행 48 (재시도·다른 조건을 합치지 않음). Analytical weighted-median single blend coefficient fitted only on inner selection; no model fit [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w5_hist15_calibrated | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.7870 | 원본 표/로그 행 49 (재시도·다른 조건을 합치지 않음). Analytical weighted-median single blend coefficient fitted only on inner selection; no model fit [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w5_hist15_n600 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.8214 | 원본 표/로그 행 50 (재시도·다른 조건을 합치지 않음). Single bounded neighbor: 15 leaves improved HGB markedly versus31; test whether more rounds recover remaining underfit [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w5_hist15_n600_calibrated | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.8124 | 원본 표/로그 행 51 (재시도·다른 조건을 합치지 않음). Analytical weighted-median single blend coefficient fitted only on inner selection; no model fit [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |

## 예보 변수 확장·물리 특성 탐색

17시 예보 확장, 10시 예보와의 변화량, 물리 특성 및 시간에 따른 변화 양상을 비교해 combined_physics를 선택했습니다. 표에는 요약 파일에 기록된 비교 행만 담았으며, 각 단계의 기준 예측이 다르므로 다른 실험군과 수치만으로 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| combined_physics | historical_record | 고정 혼합 계수 비교 | — | — | primary W_pct | 12.6250 | 혼합 계수를 고정한 입력 특성 비교 결과이며, 최종 모델 선택과는 구분합니다. [기록](../../analysis_outputs/score_push_20261104/ranking.json) |
| combined | historical_record | 고정 혼합 계수 비교 | — | — | primary W_pct | 12.6374 | 혼합 계수를 고정한 입력 특성 비교 결과이며, 최종 모델 선택과는 구분합니다. [기록](../../analysis_outputs/score_push_20261104/ranking.json) |
| expanded17 | historical_record | 고정 혼합 계수 비교 | — | — | primary W_pct | 12.6482 | 혼합 계수를 고정한 입력 특성 비교 결과이며, 최종 모델 선택과는 구분합니다. [기록](../../analysis_outputs/score_push_20261104/ranking.json) |
| combined_trajectory | historical_record | 고정 혼합 계수 비교 | — | — | primary W_pct | 12.6664 | 혼합 계수를 고정한 입력 특성 비교 결과이며, 최종 모델 선택과는 구분합니다. [기록](../../analysis_outputs/score_push_20261104/ranking.json) |
| bothround_core | historical_record | 고정 혼합 계수 비교 | — | — | primary W_pct | 12.6939 | 혼합 계수를 고정한 입력 특성 비교 결과이며, 최종 모델 선택과는 구분합니다. [기록](../../analysis_outputs/score_push_20261104/ranking.json) |
| baseline_exact | historical_record | 고정 혼합 계수 비교 | — | — | primary W_pct | 12.6960 | 혼합 계수를 고정한 입력 특성 비교 결과이며, 최종 모델 선택과는 구분합니다. [기록](../../analysis_outputs/score_push_20261104/ranking.json) |
| capacity63_600 | historical_record | 고정 혼합 계수 비교 | — | — | primary W_pct | 12.7053 | 혼합 계수를 고정한 입력 특성 비교 결과이며, 최종 모델 선택과는 구분합니다. [기록](../../analysis_outputs/score_push_20261104/ranking.json) |

## 정규화 LightGBM·신경망·커널 모델 비교

물리 정규화를 적용한 LightGBM, 설비용량 대비 발전 비율(CF) 또는 정규화된 값을 예측하는 신경망, L1 커널 모델이 기존 예측을 보완하는지 비교했습니다. 표는 이 단계에 기록된 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| mlp_cf | historical_record | 두 개발 기간 개선 | — | — | primary W_pct (lower better; internal) | 12.3219 | 단계=ensemble(시드 평균); 혼합 기준=richer_reference; 기준 예측열=p_reference; 기본 개발 W_pct=12.321941; 최근 개발 W_pct=11.317672; 기본 개발 기간에서 정한 혼합비(alpha)=0.243688 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |
| lgb_normalized | historical_record | 두 개발 기간 개선 | — | — | primary W_pct (lower better; internal) | 12.3573 | 단계=screen(1차 비교); 혼합 기준=richer_reference; 기준 예측열=p_reference; 기본 개발 W_pct=12.357347; 최근 개발 W_pct=11.378860; 기본 개발 기간에서 정한 혼합비(alpha)=0.524180 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |
| mlp_cf | historical_record | 두 개발 기간 개선 | — | — | primary W_pct (lower better; internal) | 12.3810 | 단계=screen(1차 비교); 혼합 기준=richer_reference; 기준 예측열=p_reference; 기본 개발 W_pct=12.380962; 최근 개발 W_pct=11.478764; 기본 개발 기간에서 정한 혼합비(alpha)=0.205419 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |
| mlp_normalized | historical_record | 두 개발 기간 개선 | — | — | primary W_pct (lower better; internal) | 12.4832 | 단계=screen(1차 비교); 혼합 기준=richer_reference; 기준 예측열=p_reference; 기본 개발 W_pct=12.483239; 최근 개발 W_pct=11.428834; 기본 개발 기간에서 정한 혼합비(alpha)=0.176650 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |
| kernel_l1 | historical_record | 두 개발 기간 개선 | — | — | primary W_pct (lower better; internal) | 12.5428 | 단계=screen(1차 비교); 혼합 기준=richer_reference; 기준 예측열=p_reference; 기본 개발 W_pct=12.542757; 최근 개발 W_pct=11.484403; 기본 개발 기간에서 정한 혼합비(alpha)=0.122572 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |
| lgb_normalized | historical_record | 두 기간 동시 개선 아님 | — | — | primary W_pct (lower better; internal) | 12.5254 | 단계=screen(1차 비교); 혼합 기준=old_bottom_up; 기준 예측열=p_bu_old; 기본 개발 W_pct=12.525412; 최근 개발 W_pct=11.562568; 기본 개발 기간에서 정한 혼합비(alpha)=0.811187 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |
| mlp_cf | historical_record | 두 기간 동시 개선 아님 | — | — | primary W_pct (lower better; internal) | 12.9245 | 단계=ensemble(시드 평균); 혼합 기준=old_bottom_up; 기준 예측열=p_bu_old; 기본 개발 W_pct=12.924519; 최근 개발 W_pct=11.935300; 기본 개발 기간에서 정한 혼합비(alpha)=0.395510 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |
| mlp_cf | historical_record | 두 기간 동시 개선 아님 | — | — | primary W_pct (lower better; internal) | 13.0256 | 단계=screen(1차 비교); 혼합 기준=old_bottom_up; 기준 예측열=p_bu_old; 기본 개발 W_pct=13.025560; 최근 개발 W_pct=12.274438; 기본 개발 기간에서 정한 혼합비(alpha)=0.321470 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |
| mlp_normalized | historical_record | 두 기간 동시 개선 아님 | — | — | primary W_pct (lower better; internal) | 13.1983 | 단계=screen(1차 비교); 혼합 기준=old_bottom_up; 기준 예측열=p_bu_old; 기본 개발 W_pct=13.198281; 최근 개발 W_pct=12.215356; 기본 개발 기간에서 정한 혼합비(alpha)=0.300956 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |
| kernel_l1 | historical_record | 두 기간 동시 개선 아님 | — | — | primary W_pct (lower better; internal) | 13.2403 | 단계=screen(1차 비교); 혼합 기준=old_bottom_up; 기준 예측열=p_bu_old; 기본 개발 W_pct=13.240267; 최근 개발 W_pct=12.361865; 기본 개발 기간에서 정한 혼합비(alpha)=0.282885 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |

## 기상 관측소·공간 격자별 입력 비교

공간 격자와 기상 관측소별 예보를 LightGBM·MLP에 입력해 비교하고, 관측소 LightGBM인 stations_lgb를 선택했습니다. 표에는 해당 단계의 비교 행만 담았으며, 기준 예측이 다른 실험군과 수치만으로 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| cells_lgb | historical_record | 두 개발 기간 개선 | — | — | primary W_pct (lower better; internal) | 12.1143 | 단계=screen(1차 비교); 기본 개발 W_pct=12.114264; 최근 개발 W_pct=11.178757; 기본 개발 기간에서 정한 혼합비(alpha)=0.274999 [기록](../../analysis_outputs/score_push_20261104/profile_wave/results.json) |
| cells_mlp | historical_record | 두 개발 기간 개선 | — | — | primary W_pct (lower better; internal) | 12.1221 | 단계=screen(1차 비교); 기본 개발 W_pct=12.122070; 최근 개발 W_pct=11.183734; 기본 개발 기간에서 정한 혼합비(alpha)=0.071150 [기록](../../analysis_outputs/score_push_20261104/profile_wave/results.json) |
| stations_lgb | historical_record | 두 개발 기간 개선 | — | — | primary W_pct (lower better; internal) | 12.0581 | 단계=screen(1차 비교); 기본 개발 W_pct=12.058063; 최근 개발 W_pct=11.090472; 기본 개발 기간에서 정한 혼합비(alpha)=0.256838 [기록](../../analysis_outputs/score_push_20261104/profile_wave/results.json) |
| stations_mlp | historical_record | 두 기간 동시 개선 아님 | — | — | primary W_pct (lower better; internal) | 12.1081 | 단계=screen(1차 비교); 기본 개발 W_pct=12.108093; 최근 개발 W_pct=11.210210; 기본 개발 기간에서 정한 혼합비(alpha)=0.047556 [기록](../../analysis_outputs/score_push_20261104/profile_wave/results.json) |
| stations_lgb | historical_record | 두 개발 기간 개선 | — | — | primary W_pct (lower better; internal) | 12.0416 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.041604; 최근 개발 W_pct=11.064367; 기본 개발 기간에서 정한 혼합비(alpha)=0.280847 [기록](../../analysis_outputs/score_push_20261104/profile_wave/results.json) |

## 모델 복잡도·시드·혼합 정제

모델 복잡도, 추가 시드, 여러 예측의 혼합을 비교한 최종 선택은 leaves63_trees400_ensemble입니다. 최초 results.json의 5개 모델 혼합 선택보다 clarified_results.json·chosen_recipe.json과 final/freeze.json을 우선하며, 탐색 중 선택 규칙을 명확히 한 이력을 보존합니다. 표는 이 단계의 비교 기록으로, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| three_default_mlp3 | historical_record | 비교 기록 | — | — | primary W_pct (lower better; internal) | 12.1593 | 기본 개발 W_pct=12.159323; 최근 개발 W_pct=11.222655 [기록](../../analysis_outputs/score_push_20261104/refinement_wave/clarified_results.json) |
| five_default_mlp3 | historical_record | 비교 기록 | — | — | primary W_pct (lower better; internal) | 12.1574 | 기본 개발 W_pct=12.157431; 최근 개발 W_pct=11.215643 [기록](../../analysis_outputs/score_push_20261104/refinement_wave/clarified_results.json) |
| three_default_mlp5 | historical_record | 비교 기록 | — | — | primary W_pct (lower better; internal) | 12.1961 | 기본 개발 W_pct=12.196127; 최근 개발 W_pct=11.255751 [기록](../../analysis_outputs/score_push_20261104/refinement_wave/clarified_results.json) |
| leaves15_trees400_screen | historical_record | 비교 기록 | — | — | primary W_pct (lower better; internal) | 12.1354 | 기본 개발 W_pct=12.135388; 최근 개발 W_pct=11.216609 [기록](../../analysis_outputs/score_push_20261104/refinement_wave/clarified_results.json) |
| leaves63_trees400_screen | historical_record | 비교 기록 | — | — | primary W_pct (lower better; internal) | 12.1354 | 기본 개발 W_pct=12.135414; 최근 개발 W_pct=11.211930 [기록](../../analysis_outputs/score_push_20261104/refinement_wave/clarified_results.json) |
| leaves31_trees800_screen | historical_record | 비교 기록 | — | — | primary W_pct (lower better; internal) | 12.1830 | 기본 개발 W_pct=12.183023; 최근 개발 W_pct=11.264612 [기록](../../analysis_outputs/score_push_20261104/refinement_wave/clarified_results.json) |
| leaves63_trees400_ensemble | historical_record | 비교 기록 | — | — | primary W_pct (lower better; internal) | 12.1620 | 기본 개발 W_pct=12.161988; 최근 개발 W_pct=11.187338 [기록](../../analysis_outputs/score_push_20261104/refinement_wave/clarified_results.json) |

## 발전소별 모델과 물리 정규화 비교

발전소별 입력과 물리 정규화 목표값을 비교했지만, 선택된 재혼합의 기본 개발 W_pct가 12.698487로 기존 기준 12.695950보다 나빠 최종 CPU 후보에 채택하지 않았습니다. 표의 행은 이 단계에서 기록한 모델·기준 예측 조합이며, 다른 실험군의 수치와 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| normalized_l1+rich | historical_record | 고정 혼합 계수 비교 | — | — | paired mean relative loss | 1.0012 | 두 개발 기간의 평균 상대 오차는 1.001241684입니다. 이 행은 발전소별 모델과 그룹 직접 예측의 조합 비교입니다. [기록](../../analysis_outputs/score_push_20261104/site_wave/results.json) |
| identity_l1+rich | historical_record | 고정 혼합 계수 비교 | — | — | paired mean relative loss | 1.0021 | 두 개발 기간의 평균 상대 오차는 1.002109152입니다. 이 행은 발전소별 모델과 그룹 직접 예측의 조합 비교입니다. [기록](../../analysis_outputs/score_push_20261104/site_wave/results.json) |
| identity_l2+rich | historical_record | 고정 혼합 계수 비교 | — | — | paired mean relative loss | 1.0052 | 두 개발 기간의 평균 상대 오차는 1.005249807입니다. 이 행은 발전소별 모델과 그룹 직접 예측의 조합 비교입니다. [기록](../../analysis_outputs/score_push_20261104/site_wave/results.json) |
| normalized_l1+incumbent | historical_record | 고정 혼합 계수 비교 | — | — | paired mean relative loss | 1.0092 | 두 개발 기간의 평균 상대 오차는 1.009242127입니다. 이 행은 발전소별 모델과 그룹 직접 예측의 조합 비교입니다. [기록](../../analysis_outputs/score_push_20261104/site_wave/results.json) |
| identity_l1+incumbent | historical_record | 고정 혼합 계수 비교 | — | — | paired mean relative loss | 1.0094 | 두 개발 기간의 평균 상대 오차는 1.009359116입니다. 이 행은 발전소별 모델과 그룹 직접 예측의 조합 비교입니다. [기록](../../analysis_outputs/score_push_20261104/site_wave/results.json) |
| identity_l2+incumbent | historical_record | 고정 혼합 계수 비교 | — | — | paired mean relative loss | 1.0134 | 두 개발 기간의 평균 상대 오차는 1.013417659입니다. 이 행은 발전소별 모델과 그룹 직접 예측의 조합 비교입니다. [기록](../../analysis_outputs/score_push_20261104/site_wave/results.json) |

## 기존 공간 격자 모델 추가 혼합

추가 모델 학습 0회로 기존 공간 격자 모델을 관측소 앙상블에 혼합했지만, 최근 개발 기간이 악화돼 거부했습니다. 표는 해당 단계에 기록된 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| cell_addition_no_fit | historical_record | 최근 기간 악화로 제외 | — | — |  | — | 기존 공간 격자 모델을 새 학습 없이 추가 혼합했지만 채택하지 않고 station_complete를 유지했습니다. [기록](../../analysis_outputs/score_push_20261104/closing_wave/results.json) |

## 최근 데이터 가중치와 학습 창 비교

180·365·730일 반감기 가중치와 최근 365일 학습 창을 비교하며 모델 24개를 적합했고, decay180을 선택했습니다. 표는 해당 단계의 기준 예측과 비교한 기록이므로, 다른 실험군의 수치와 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| decay180 | historical_record | 개발 기준 통과 | — | — | primary W_pct (lower better; internal) | 12.0332 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.033226; 최근 개발 W_pct=11.059225; 기본 개발 기간에서 정한 혼합비(alpha)=0.077949 [기록](../../analysis_outputs/renew_20261105/recency_wave/results.json) |
| decay365 | historical_record | 개발 기준 통과 | — | — | primary W_pct (lower better; internal) | 12.0409 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.040889; 최근 개발 W_pct=11.056701; 기본 개발 기간에서 정한 혼합비(alpha)=0.026961 [기록](../../analysis_outputs/renew_20261105/recency_wave/results.json) |
| decay730 | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0416 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.041586; 최근 개발 W_pct=11.063084; 기본 개발 기간에서 정한 혼합비(alpha)=0.005786 [기록](../../analysis_outputs/renew_20261105/recency_wave/results.json) |
| window365 | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.9924 | 단계=ensemble(시드 평균); 기본 개발 W_pct=11.992404; 최근 개발 W_pct=11.134984; 기본 개발 기간에서 정한 혼합비(alpha)=0.106463 [기록](../../analysis_outputs/renew_20261105/recency_wave/results.json) |

## 구름 예측을 보조 특성으로 추가

구름 예측과 예보 분포의 평균·공간 정보를 보조 입력으로 추가하며, 보조 모델 14개와 발전량 모델 12개를 적합했습니다. 표에는 기록된 비교 결과만 담았으며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| means | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0304 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.030441; 최근 개발 W_pct=11.066725; 기본 개발 기간에서 정한 혼합비(alpha)=0.043785 [기록](../../analysis_outputs/renew_20261105/cloud_wave/results.json) |
| profiles | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0309 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.030940; 최근 개발 W_pct=11.069780; 기본 개발 기간에서 정한 혼합비(alpha)=0.039184 [기록](../../analysis_outputs/renew_20261105/cloud_wave/results.json) |

## 그룹 오차를 반영한 모델 비교

그룹 단위 오차를 반영한 신경망과 발전소 단위 대조 모델을 비교하며 모델 18개를 적합했습니다. 표는 해당 단계에 기록된 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| group_l01 | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0332 | 기본 개발 W_pct=12.033226; 최근 개발 W_pct=11.059225; 기본 개발 기간에서 정한 혼합비(alpha)=0.000000 [기록](../../analysis_outputs/renew_20261105/group_wave/results.json) |
| group_l1 | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0332 | 기본 개발 W_pct=12.033226; 최근 개발 W_pct=11.059225; 기본 개발 기간에서 정한 혼합비(alpha)=0.000000 [기록](../../analysis_outputs/renew_20261105/group_wave/results.json) |
| site_control | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0332 | 기본 개발 W_pct=12.033226; 최근 개발 W_pct=11.059225; 기본 개발 기간에서 정한 혼합비(alpha)=0.000000 [기록](../../analysis_outputs/renew_20261105/group_wave/results.json) |

## 전체 발전량 예측 후 그룹 배분

전체 발전량을 먼저 예측한 뒤 고정된 그룹에 배분하는 방법으로 모델 12개를 적합했습니다. 표에는 해당 단계의 비교 결과만 담았으며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| total_rich | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0242 | 기본 개발 W_pct=12.024160; 최근 개발 W_pct=11.075880; 기본 개발 기간에서 정한 혼합비(alpha)=0.106190 [기록](../../analysis_outputs/renew_20261105/total_wave/results.json) |
| total_station | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0181 | 기본 개발 W_pct=12.018104; 최근 개발 W_pct=11.110085; 기본 개발 기간에서 정한 혼합비(alpha)=0.073052 [기록](../../analysis_outputs/renew_20261105/total_wave/results.json) |

## 온도·눈 조건별 편향 보정

기본 개발 기간에서 온도·눈 조건별 보정 계수를 구하고 보정 범위를 제한하는 후보 3개를 비교했으며, 새 트리 학습은 0회이고 선택은 temperature_then_snow입니다. 표는 해당 단계의 기준 예측과 비교한 결과이므로, 다른 실험군의 수치와 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| snow_only | historical_record | 개발 기준 통과 | — | — | primary W_pct (lower better; internal) | 12.0102 | 기본 개발 W_pct=12.010182; 최근 개발 W_pct=11.038762 [기록](../../analysis_outputs/renew_20261105/calibration_wave/results.json) |
| temperature_only | historical_record | 개발 기준 통과 | — | — | primary W_pct (lower better; internal) | 11.9689 | 기본 개발 W_pct=11.968930; 최근 개발 W_pct=11.010944 [기록](../../analysis_outputs/renew_20261105/calibration_wave/results.json) |
| temperature_then_snow | historical_record | 개발 기준 통과 | — | — | primary W_pct (lower better; internal) | 11.9592 | 기본 개발 W_pct=11.959229; 최근 개발 W_pct=11.000953 [기록](../../analysis_outputs/renew_20261105/calibration_wave/results.json) |

## 피크·금액 기준 손실 가중치 비교

피크 시간 가중치 k와 금액 기준 손실 가중치를 비교하며 모델 12개를 적합했습니다. 표는 이 단계에 기록된 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| peak_k | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.9560 | 기본 개발 W_pct=11.956016; 최근 개발 W_pct=11.022002; 기본 개발 기간에서 정한 혼합비(alpha)=0.041249 [기록](../../analysis_outputs/renew_20261105/weight_wave/results.json) |
| scored | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.9459 | 기본 개발 W_pct=11.945918; 최근 개발 W_pct=11.059273; 기본 개발 기간에서 정한 혼합비(alpha)=0.060576 [기록](../../analysis_outputs/renew_20261105/weight_wave/results.json) |

## 발전소별 수율 차이 정규화

학습 자료만으로 발전소별 수율 차이를 정규화하며 발전량 모델 6개와 발전소 수율 계수 2세트를 적합했습니다. 표에는 해당 단계의 비교 결과만 담았으며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| site_yield | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.9466 | 기본 개발 W_pct=11.946590; 최근 개발 W_pct=11.038143; 기본 개발 기간에서 정한 혼합비(alpha)=0.100551 [기록](../../analysis_outputs/renew_20261105/yield_wave/results.json) |

## 시간대별 편향 보정

시간대별 보정 범위를 제한한 후보 1개에 대해 스칼라 계수 5개를 적합하고 hour_bias를 선택했으며, 새 트리 학습은 0회입니다. 표는 해당 단계의 기준 예측과 비교한 결과이므로, 다른 실험군의 수치와 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| hour_bias | historical_record | 개발 기준 통과 | — | — | primary W_pct (lower better; internal) | 11.9126 | 기본 개발 W_pct=11.912571; 최근 개발 W_pct=10.998535 [기록](../../analysis_outputs/renew_20261105/hour_wave/results.json) |

## 구름량 구간별 편향 보정

시간대 보정을 마친 예측에 구름량 구간별 보정을 추가한 후보 1개를 비교해 cloud_bias를 선택했으며, 스칼라 계수 적합은 4회이고 새 트리 학습은 0회입니다. 표는 해당 단계의 기준 예측과 비교한 결과이므로, 다른 실험군의 수치와 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| cloud_bias | historical_record | 개발 기준 통과 | — | — | primary W_pct (lower better; internal) | 11.7928 | 기본 개발 W_pct=11.792837; 최근 개발 W_pct=10.955416 [기록](../../analysis_outputs/renew_20261105/sky_wave/results.json) |

## 시간 순서를 지킨 보정 계수 갱신

시간 순서를 지키며 기상·시간대·구름 보정 계수를 갱신한 후보 1개를 비교했고, 스칼라 계수 적합은 32회이며 새 트리 학습은 0회입니다. 표는 해당 단계의 기준 예측과 비교한 결과이므로, 다른 실험군의 수치와 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| chronological_refresh | historical_record | 개발 기준 미통과 | — | — |  | — | 후기 최근 기간(late_recent)의 W_pct는 9.485826으로 고정 기상 보정 기준 9.408122보다 높고, 최신 기간(latest)도 9.420960으로 기준 9.390467보다 높았습니다. 스칼라 계수 32개를 적합하고 트리 학습은 0회 수행했으며, 갱신된 보정은 채택하지 않았습니다. [기록](../../analysis_outputs/renew_20261105/refresh_wave/results.json) |

## 관측소 신경망에 물리·시간 정규화 적용

물리 정규화와 시간 가중치를 적용한 관측소 MLP 후보 1개를 모델 6개로 검증했으며, 추가 보정 계수 적합은 0회입니다. 표는 해당 단계의 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| station_mlp_normalized_decay180 | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.7772 | 기본 개발 W_pct=11.777166; 최근 개발 W_pct=10.982662; 기본 개발 기간에서 정한 혼합비(alpha)=0.021664 [기록](../../analysis_outputs/renew_20261105/mlp_wave/results.json) |

## 관측소 신경망 입력을 학습 범위로 제한

기존 관측소 MLP의 입력을 학습 범위로 제한한 후보 1개를 검증했으며, 모델 추론 6회와 범위 제한 변환 2회를 수행하고 새 모델 학습 및 보정 계수 적합은 각각 0회였습니다. 표는 해당 단계의 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| station_mlp_train_range | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.7687 | 기본 개발 W_pct=11.768679; 최근 개발 W_pct=11.062367; 기본 개발 기간에서 정한 혼합비(alpha)=0.052955 [기록](../../analysis_outputs/renew_20261105/bounds_wave/results.json) |

## 단조 제약 부스팅과 동일 손실 대조 모델

동일한 fair 손실을 사용하는 대조 모델과 단조 제약 관측소 부스팅 후보 2개를 모델 12개로 비교했으며, 추가 보정 계수 적합은 0회입니다. 표는 해당 단계의 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| fair_control | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.7885 | 기본 개발 W_pct=11.788477; 최근 개발 W_pct=10.979584; 기본 개발 기간에서 정한 혼합비(alpha)=0.067177 [기록](../../analysis_outputs/renew_20261105/mono_wave/results.json) |
| fair_monotone | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.7848 | 기본 개발 W_pct=11.784847; 최근 개발 W_pct=10.988034; 기본 개발 기간에서 정한 혼합비(alpha)=0.093063 [기록](../../analysis_outputs/renew_20261105/mono_wave/results.json) |

## 기존 신경망 입력 범위 제한

기존 rich MLP의 혼합 가중치를 고정하고 입력을 학습 범위로 제한한 후보 1개를 비교했으며, 새 모델 학습·보정 계수 적합·혼합비(alpha) 적합은 모두 0회였습니다. 표는 해당 단계의 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| incumbent_rich_mlp_train_range | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.7917 | 기본 개발 W_pct=11.791707; 최근 개발 W_pct=10.955423 [기록](../../analysis_outputs/renew_20261105/incbound_wave/results.json) |

## ExtraTrees 모델의 보완 효과 검증

확장 기상 입력과 물리 정규화를 사용하는 ExtraTrees 앙상블 후보 1개를 모델 6개로 검증했으며, 추가 보정 계수 적합은 0회입니다. 표는 해당 단계의 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| extratrees_normalized_rich_decay180 | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.9581 | 기본 개발 W_pct=11.958096; 최근 개발 W_pct=11.006260; 기본 개발 기간에서 정한 혼합비(alpha)=0.025608 [기록](../../analysis_outputs/renew_20261105/extra_wave/results.json) |

## Poisson 로그 연결 부스팅

Poisson 손실과 로그 연결을 사용하는 관측소 부스팅 후보 1개를 모델 6개로 검증했으며, 추가 보정 계수 적합은 0회입니다. 표는 해당 단계의 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| poisson_normalized_station_decay180 | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.9592 | 기본 개발 W_pct=11.959229; 최근 개발 W_pct=11.000953; 기본 개발 기간에서 정한 혼합비(alpha)=0.000000 [기록](../../analysis_outputs/renew_20261106/poisson_wave/results.json) |

## 태양 고도를 보정한 3시간 예측 평활화

맑은 하늘의 태양 고도로 정규화한 예측을 3시간 단위로 평활화하는 후보 1개를 비교했으며, 새 모델 학습과 보정 계수 적합은 각각 0회이고 혼합비(alpha)만 1회 적합했습니다. 표는 해당 단계의 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| normalized_temporal_smoothing | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.9509 | 기본 개발 W_pct=11.950907; 최근 개발 W_pct=11.010421; 기본 개발 기간에서 정한 혼합비(alpha)=0.380199 [기록](../../analysis_outputs/renew_20261106/smooth_wave/results.json) |

## CatBoost GPU 초기 비교

CatBoost GPU 후보를 1차 비교하고 여러 시드에서의 안정성을 확인하며 모델 8개를 적합했습니다. 표에는 실제 기록된 단계별 비교만 담았으며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| rich_cf | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0375 | 단계=screen(1차 비교); 기본 개발 W_pct=12.037505; 최근 개발 W_pct=11.069621; 기본 개발 기간에서 정한 혼합비(alpha)=0.062314 [기록](../../analysis_outputs/score_push_gpu_20261104/results.json) |
| station_normalized | historical_record | 개발 기준 통과 | — | — | primary W_pct (lower better; internal) | 12.0119 | 단계=screen(1차 비교); 기본 개발 W_pct=12.011915; 최근 개발 W_pct=11.055529; 기본 개발 기간에서 정한 혼합비(alpha)=0.160744 [기록](../../analysis_outputs/score_push_gpu_20261104/results.json) |
| station_normalized | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0104 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.010373; 최근 개발 W_pct=11.067682; 기본 개발 기간에서 정한 혼합비(alpha)=0.187019 [기록](../../analysis_outputs/score_push_gpu_20261104/results.json) |

## CatBoost GPU 네 가지 정제

얕은 모델·깊은 모델·긴 학습·금액 가중치라는 네 가지 고정 CatBoost GPU 가설을 모델 24개로 비교했습니다. 표에는 실제 기록된 비교 행만 담았으며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| shallow | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.9909 | 단계=ensemble(시드 평균); 기본 개발 W_pct=11.990907; 최근 개발 W_pct=11.117183; 기본 개발 기간에서 정한 혼합비(alpha)=0.226076 [기록](../../analysis_outputs/score_push_gpu_refine_20261105/results.json) |
| deep | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0024 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.002405; 최근 개발 W_pct=11.090419; 기본 개발 기간에서 정한 혼합비(alpha)=0.234670 [기록](../../analysis_outputs/score_push_gpu_refine_20261105/results.json) |
| longer | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0181 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.018120; 최근 개발 W_pct=11.069844; 기본 개발 기간에서 정한 혼합비(alpha)=0.153113 [기록](../../analysis_outputs/score_push_gpu_refine_20261105/results.json) |
| monetary | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0152 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.015155; 최근 개발 W_pct=11.163519; 기본 개발 기간에서 정한 혼합비(alpha)=0.116792 [기록](../../analysis_outputs/score_push_gpu_refine_20261105/results.json) |

## CPU 최종 후보·학습 종료일 진단

최종 재학습은 그룹 모델 12개이며, 학습 종료일 진단은 모델 272개로 기존 269개를 보존하고 미완료 3개만 재개했습니다. 이 수를 새로운 가설 수와 구분하고, autoresearch와 동일한 발전소 구성을 사용한 새 제출 파일 쌍은 별도 폴더에 보존했으며 공식 점수 기록은 없습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| cpu_final | historical_record | 후보 생성·검증, 기간별 성능 혼재 | — | — |  | — | 기본 개발 W_pct 12.041604, 최근 개발 11.064367로 개선됐고 후기 연간은 10.716156입니다. 다만 이전 학습 종료일 기준 3~5월은 9.848507로, 기준 9.576119보다 악화됐습니다. [기록](../../analysis_outputs/score_push_20261104/final/outer_metrics.json) |
| latest_cutoff_diagnostic | historical_record | 검증상 이점 없음 | — | — |  | — | 양쪽 모델을 2025-03-01까지 재학습해 같은 3~5월을 평가했을 때 새 모델은 9.446583, 기존 모델은 9.437775였습니다. 사후 진단이며 결과에 따라 다시 선택하지 않았습니다. [기록](../../analysis_outputs/score_push_20261104/deployment_check/independent_check.json) |

## 시간가중·기상·시간대·구름 보정 제출 후보

최고 공식 점수는 사용자 보고이며, 기상 보정만 적용한 renew가 현재 보존 기준입니다. hour·sky 후보의 더 좋은 개발 점수만으로 공식 성능 우위를 뜻하지는 않으며, 기상·시간대·구름 보정의 기본 개발 기간 자료는 계수 학습에도 일부 사용됐습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| renew_weather | historical_record | 사용자 보고 최고점 | — | — | user-reported official score | 6454220836.0000 | 180일 시간 가중치와 온도·눈 보정을 적용한 후보입니다. 기본 개발 W_pct는 11.959229, 최근 개발은 11.000953이며, 사용자가 6,454,220,836점을 보고했습니다. 후보: submission/renew_candidate_20261105. [기록](../../analysis_outputs/renew_20261105/official_feedback.json) |
| renew_hour | historical_record | 사용자 보고 점수 하락 | — | — | user-reported official score | 6453783187.0000 | 내부 기본 개발 W_pct는 11.912571, 최근 개발은 10.998535입니다. 사용자 보고 점수는 6,453,783,187로 기상 보정 기준보다 437,649 낮았습니다. 후보: submission/renew_hour_candidate_20261105. [기록](../../analysis_outputs/renew_20261105/official_feedback_hour_20261105.json) |
| renew_sky | historical_record | 후보 생성·검증, 당시 공식 점수 미확인 | — | — |  | — | 내부 기본 개발 W_pct는 11.792837, 최근 개발은 10.955416이며 공식 점수는 확인되지 않았습니다. 후보: submission/renew_sky_candidate_20261105. [기록](../../submission/renew_sky_candidate_20261105/manifest.json) |

## 분포 변화 가중치 사전 준비

이 폴더는 사전 준비 단계이며, 실행 결과는 11월 7일 Linux 후속 실험에 있습니다. 준비와 실행을 별도 모델 학습으로 중복 집계하지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| shift_preparation | historical_record | 준비 후 Linux에서 이어 실행 | — | — |  | — | 이 준비 폴더에서 학습 완료 횟수를 0회라고 단정하지 않고, 후속 shift_linux 결과로 실제 완료된 학습을 확인합니다. [기록](../../analysis_outputs/renew_20261106/shift_wave/protocol.json) |

## Linux 후속 여섯 가설

6개 가설 중 shift·PCA·DART는 최근 개발 기간이 악화돼 거부됐고, cloud_curve·cloud_solar_surface·weather_residual는 개발 기준을 통과해 후보 3개를 내보냈습니다. 다만 이미 공개된 최신 학습 종료일 기준 3~5월 오차는 각각 9.418260·9.417728·9.441703으로 기준 9.390467보다 높았습니다. 적합 수는 발전량 모델 18개, 분포 구분 모델 6개, PCA 2개, 보정 모델 6개, 혼합비(alpha) 3개로 구분하며, 새 후보는 모두 공식 미채점 상태이고 기존 공식 기준을 보존합니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| shift_linux | historical_record | 검증 기록 있음 | — | — | primary_W_pct | 11.9461 | 원본 표/로그 행 1 (재시도·다른 조건을 합치지 않음). 분포 변화 가중치 [기록](../../analysis_outputs/renew_20261107/results.csv) |
| pca_station | historical_record | 검증 기록 있음 | — | — | primary_W_pct | 11.9582 | 원본 표/로그 행 2 (재시도·다른 조건을 합치지 않음). 관측소 PCA 16성분 [기록](../../analysis_outputs/renew_20261107/results.csv) |
| dart_station | historical_record | 검증 기록 있음 | — | — | primary_W_pct | 11.9561 | 원본 표/로그 행 3 (재시도·다른 조건을 합치지 않음). DART 800트리 [기록](../../analysis_outputs/renew_20261107/results.csv) |
| cloud_curve | historical_record | 검증 기록 있음 | — | — | primary_W_pct | 11.8386 | 원본 표/로그 행 4 (재시도·다른 조건을 합치지 않음). 연속 구름량 보정 [기록](../../analysis_outputs/renew_20261107/results.csv) |
| cloud_solar_surface | historical_record | 검증 기록 있음 | — | — | primary_W_pct | 11.8478 | 원본 표/로그 행 5 (재시도·다른 조건을 합치지 않음). 구름량·태양 고도 보정 [기록](../../analysis_outputs/renew_20261107/results.csv) |
| weather_residual | historical_record | 검증 기록 있음 | — | — | primary_W_pct | 11.6949 | 원본 표/로그 행 6 (재시도·다른 조건을 합치지 않음). 기상 잔여 오차 보정 [기록](../../analysis_outputs/renew_20261107/results.csv) |

## 초기 모델·입력·앙상블 비교 E0~E7

원본 results_table.csv의 34개 비교 행을 순서대로 보존했습니다. 학습은 2022-06-01 01:00~2024-06-01 00:00 KST, 평가는 2024-06-01 01:00~2025-06-01 00:00 KST이며 당시의 고정 참조 발전소 구성을 사용하므로 이후 후보와 직접 순위를 매기지 않습니다. E5 보정은 별도 표에 있고, E3_r30은 실측 갱신을 요구하는 배포 불가 진단입니다. 후속 검증에서 확인된 기본 난수 설정과 선택 편향의 한계도 함께 보존합니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| E0_site_raw | historical_record | 미학습 발전소 진단 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 29.3478 | 원본 표/로그 행 1 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: per-site L2 600 trees. 고정 참조 구성의 연간 W_ref_pct=29.347803; E0_site 대비 오차 감소율=-80.194311%. 학습 이력이 없는 48개 발전소를 0으로 예측한 초기 진단이며, 신규 발전소 대체 예측을 적용한 E0_site와 구분합니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E0_site | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 16.2868 | 원본 표/로그 행 2 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: per-site L2 600 trees + pooled fallback for 48 unseen sites. 고정 참조 구성의 연간 W_ref_pct=16.286753; E0_site 대비 오차 감소율=0.000000%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E0_pool | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6610 | 원본 표/로그 행 3 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l2 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.660987; E0_site 대비 오차 감소율=22.262059%. 원래 실행은 명시적 seed=0이 아닌 LightGBM 기본 난수 설정입니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E1_l1 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.5214 | 원본 표/로그 행 4 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.521386; E0_site 대비 오차 감소율=23.119201%. 원래 실행은 명시적 seed=0이 아닌 LightGBM 기본 난수 설정입니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E1_l1w | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.4599 | 원본 표/로그 행 5 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.459947; E0_site 대비 오차 감소율=23.496434%. 원래 실행은 명시적 seed=0이 아닌 LightGBM 기본 난수 설정입니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E1_l2w | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.8324 | 원본 표/로그 행 6 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l2 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.832373; E0_site 대비 오차 감소율=21.209757%. 원래 실행은 명시적 seed=0이 아닌 LightGBM 기본 난수 설정입니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E2_r10 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 13.1061 | 원본 표/로그 행 7 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=13.106078; E0_site 대비 오차 감소율=19.529217%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E2_avg | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.5551 | 원본 표/로그 행 8 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: avg(E1_l1w, E2_r10). 고정 참조 구성의 연간 W_ref_pct=12.555137; E0_site 대비 오차 감소율=22.911971%. 저장된 모델 예측의 평균·혼합을 포함하며 별도 모델 한 개를 새로 학습했다는 뜻은 아닙니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E2_both | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.5123 | 원본 표/로그 행 9 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.512309; E0_site 대비 오차 감소율=23.174934%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_phys | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.7238 | 원본 표/로그 행 10 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.723761; E0_site 대비 오차 감소율=21.876629%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_phys_both | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6830 | 원본 표/로그 행 11 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.683040; E0_site 대비 오차 감소율=22.126656%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_site | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6804 | 원본 표/로그 행 12 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.680361; E0_site 대비 오차 감소율=22.143104%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_site_nolatlon | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6637 | 원본 표/로그 행 13 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.663746; E0_site 대비 오차 감소율=22.245119%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_r30 | historical_record | 실시간 관측 사용 진단·제출 불가 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.3635 | 원본 표/로그 행 14 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.363522; E0_site 대비 오차 감소율=24.088477%. 검증 기간의 실측을 갱신하는 이동 비율이 필요해, 연간 일괄 제출에 배포할 수 없는 진단입니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_r30f | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6311 | 원본 표/로그 행 15 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.631136; E0_site 대비 오차 감소율=22.445342%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_r365f | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6096 | 원본 표/로그 행 16 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.609570; E0_site 대비 오차 감소율=22.577754%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_site_r365f | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6247 | 원본 표/로그 행 17 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.624719; E0_site 대비 오차 감소율=22.484742%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_site_both | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.7059 | 원본 표/로그 행 18 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.705903; E0_site 대비 오차 감소율=21.986275%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_site_nophys | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6534 | 원본 표/로그 행 19 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.653412; E0_site 대비 오차 감소율=22.308570%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_r365f_nophys | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6011 | 원본 표/로그 행 20 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.601062; E0_site 대비 오차 감소율=22.629995%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E1_l1w_s2 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.4369 | 원본 표/로그 행 21 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.436864; E0_site 대비 오차 감소율=23.638160%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E1_l1w_s3 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.5533 | 원본 표/로그 행 22 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.553283; E0_site 대비 오차 감소율=22.923358%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E6_trees800 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6675 | 원본 표/로그 행 23 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.667464; E0_site 대비 오차 감소율=22.222287%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E6_lr03_t800 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.4497 | 원본 표/로그 행 24 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.449727; E0_site 대비 오차 감소율=23.559182%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E6_leaves255 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.4576 | 원본 표/로그 행 25 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.457566; E0_site 대비 오차 감소율=23.511052%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E6_leaves63 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.5927 | 원본 표/로그 행 26 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.592658; E0_site 대비 오차 감소율=22.681598%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E7_seed3 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.4286 | 원본 표/로그 행 27 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: ens:0.33*E1_l1w+0.33*E1_l1w_s2+0.33*E1_l1w_s3. 고정 참조 구성의 연간 W_ref_pct=12.428556; E0_site 대비 오차 감소율=23.689177%. 저장된 모델 예측의 평균·혼합을 포함하며 별도 모델 한 개를 새로 학습했다는 뜻은 아닙니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E7_mix | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.4069 | 원본 표/로그 행 28 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: ens:0.14*E1_l1w+0.14*E1_l1w_s2+0.14*E1_l1w_s3+0.14*E2_both+0.14*E3_site_nophys+0.14*E3_r365f_nophys+0.14*E3_phys. 고정 참조 구성의 연간 W_ref_pct=12.406942; E0_site 대비 오차 감소율=23.821884%. 저장된 모델 예측의 평균·혼합을 포함하며 별도 모델 한 개를 새로 학습했다는 뜻은 아닙니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E7_mix_site10 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.2956 | 원본 표/로그 행 29 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: ens:0.90*E7_mix+0.10*E0_site. 고정 참조 구성의 연간 W_ref_pct=12.295638; E0_site 대비 오차 감소율=24.505285%. 저장된 모델 예측의 평균·혼합을 포함하며 별도 모델 한 개를 새로 학습했다는 뜻은 아닙니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E7_mix_site25 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.4349 | 원본 표/로그 행 30 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: ens:0.75*E7_mix+0.25*E0_site. 고정 참조 구성의 연간 W_ref_pct=12.434867; E0_site 대비 오차 감소율=23.650426%. 저장된 모델 예측의 평균·혼합을 포함하며 별도 모델 한 개를 새로 학습했다는 뜻은 아닙니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E4_direct | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.5027 | 원본 표/로그 행 31 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: direct group-level regression_l1 w. 고정 참조 구성의 연간 W_ref_pct=12.502673; E0_site 대비 오차 감소율=23.234101%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E4_blend30 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.0524 | 원본 표/로그 행 32 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: 0.7*E7_mix_site10 + 0.3*E4_direct. 고정 참조 구성의 연간 W_ref_pct=12.052447; E0_site 대비 오차 감소율=25.998465%. 저장된 모델 예측의 평균·혼합을 포함하며 별도 모델 한 개를 새로 학습했다는 뜻은 아닙니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E4_blend50 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.0307 | 원본 표/로그 행 33 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: 0.5*E7_mix_site10 + 0.5*E4_direct. 고정 참조 구성의 연간 W_ref_pct=12.030696; E0_site 대비 오차 감소율=26.132015%. 저장된 모델 예측의 평균·혼합을 포함하며 별도 모델 한 개를 새로 학습했다는 뜻은 아닙니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E4_blend70 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.1375 | 원본 표/로그 행 34 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: 0.3*E7_mix_site10 + 0.7*E4_direct. 고정 참조 구성의 연간 W_ref_pct=12.137475; E0_site 대비 오차 감소율=25.476401%. 저장된 모델 예측의 평균·혼합을 포함하며 별도 모델 한 개를 새로 학습했다는 뜻은 아닙니다. [기록](../../analysis_outputs/tables/results_table.csv) |

## 초기 E5 사후 보정 비교

E4_blend50과 E0_site에 대한 10개 비교 행을 원본 순서대로 보존했습니다. 검증 전반인 2024-06~11월에서 계수를 적합하고 후반인 2024-12~2025-05월에서 평가했으며, 전반의 표본 내 진단도 별도 행으로 표시합니다. 전역·시간대 보정은 E4_blend50의 후반 오차를 악화시켰지만 E0_site에서는 개선됐고, 이 10행을 독립 모델 10개로 세지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| E4_blend50 / none (2nd half) | historical_record | 이후 기간으로 보정 이전 평가 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 10.2886 | 원본 표/로그 행 1 (재시도·다른 조건을 합치지 않음). 후반 평가의 보정 없는 기준입니다. W_ref_pct=10.288569, 평가 시각 수=4,368이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |
| E4_blend50 / global factor (2nd half) | historical_record | 이후 기간으로 보정 이전 평가 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 10.5289 | 원본 표/로그 행 2 (재시도·다른 조건을 합치지 않음). 전반에 적합한 전역 계수를 후반에 적용입니다. W_ref_pct=10.528879, 평가 시각 수=4,368이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |
| E4_blend50 / hourly factor (2nd half) | historical_record | 이후 기간으로 보정 이전 평가 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 10.5402 | 원본 표/로그 행 3 (재시도·다른 조건을 합치지 않음). 전반에 적합한 시간대별 계수를 후반에 적용입니다. W_ref_pct=10.540152, 평가 시각 수=4,368이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |
| E4_blend50 / none (1st half) | historical_record | 보정 학습 기간 기준값 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 13.8378 | 원본 표/로그 행 4 (재시도·다른 조건을 합치지 않음). 계수 적합에 사용한 전반의 보정 없는 기준입니다. W_ref_pct=13.837824, 평가 시각 수=4,392이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |
| E4_blend50 / hourly factor (1st half, in-sample) | historical_record | 계수 학습 기간 내 진단 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 13.6506 | 원본 표/로그 행 5 (재시도·다른 조건을 합치지 않음). 계수 적합과 같은 전반 자료에서 계산한 표본 내 결과입니다. W_ref_pct=13.650630, 평가 시각 수=4,392이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |
| E0_site / none (2nd half) | historical_record | 이후 기간으로 보정 이전 평가 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 14.2920 | 원본 표/로그 행 6 (재시도·다른 조건을 합치지 않음). 후반 평가의 보정 없는 기준입니다. W_ref_pct=14.292008, 평가 시각 수=4,368이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |
| E0_site / global factor (2nd half) | historical_record | 이후 기간으로 보정 이전 평가 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 13.3170 | 원본 표/로그 행 7 (재시도·다른 조건을 합치지 않음). 전반에 적합한 전역 계수를 후반에 적용입니다. W_ref_pct=13.317005, 평가 시각 수=4,368이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |
| E0_site / hourly factor (2nd half) | historical_record | 이후 기간으로 보정 이전 평가 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 12.4012 | 원본 표/로그 행 8 (재시도·다른 조건을 합치지 않음). 전반에 적합한 시간대별 계수를 후반에 적용입니다. W_ref_pct=12.401249, 평가 시각 수=4,368이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |
| E0_site / none (1st half) | historical_record | 보정 학습 기간 기준값 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 18.3559 | 원본 표/로그 행 9 (재시도·다른 조건을 합치지 않음). 계수 적합에 사용한 전반의 보정 없는 기준입니다. W_ref_pct=18.355924, 평가 시각 수=4,392이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |
| E0_site / hourly factor (1st half, in-sample) | historical_record | 계수 학습 기간 내 진단 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 14.6289 | 원본 표/로그 행 10 (재시도·다른 조건을 합치지 않음). 계수 적합과 같은 전반 자료에서 계산한 표본 내 결과입니다. W_ref_pct=14.628876, 평가 시각 수=4,392이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |

## 초기 발전소 구성 후보 10개

원본 구성 요약표의 10개 후보를 모두 기록하며, 이후 award_run의 2개 구성×5개 혼합비 비교와는 다른 실험군입니다. 값은 2024-06~2025-05월의 E1·E7 발전소별 예측을 합산했을 때 pooled 하한을 얼마나 초과하는지 나타내며, 전체 W_pct나 공식 점수가 아닙니다. 같은 검증 연도의 오차로 최적화한 구성도 포함돼 독립 검증으로 볼 수 없고, 그룹 직접 모델을 섞은 E4의 구성 개선 효과는 여기서 측정하지 않았습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| reference | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 2.3544 | 원본 표/로그 행 1 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=2.354429%, E7 기준=2.323334%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_reference.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |
| optimized_E1 | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 0.4662 | 원본 표/로그 행 2 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=0.466174%, E7 기준=0.650415%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_optimized_E1.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |
| twin_errcorr | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 1.0503 | 원본 표/로그 행 3 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=1.050339%, E7 기준=1.047958%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_twin_errcorr.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |
| twin_gencorr | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 1.1467 | 원본 표/로그 행 4 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=1.146748%, E7 기준=1.121325%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_twin_gencorr.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |
| embed_leaforder | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 1.5878 | 원본 표/로그 행 5 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=1.587842%, E7 기준=1.584817%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_embed_leaforder.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |
| strat_cluster8_cap | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 1.5046 | 원본 표/로그 행 6 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=1.504611%, E7 기준=1.354257%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_strat_cluster8_cap.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |
| cap_pairs_balanced | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 1.8094 | 원본 표/로그 행 7 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=1.809392%, E7 기준=1.782725%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_cap_pairs_balanced.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |
| optimized_joint_E1E7 | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 0.5047 | 원본 표/로그 행 8 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=0.504688%, E7 기준=0.546782%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_optimized_joint_E1E7.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |
| optimized_E7_full | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 0.6569 | 원본 표/로그 행 9 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=0.656942%, E7 기준=0.486551%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_optimized_E7_full.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |
| optimized_E1_tightcap | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 0.4951 | 원본 표/로그 행 10 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=0.495074%, E7 기준=0.666134%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_optimized_E1_tightcap.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |

## 초기 예보 제공사·입력 제거·완벽 예보 진단

model_results.csv의 25개 명명된 비교를 모두 보존했습니다. 150개 트리의 소형 LightGBM은 2023-06~2024-05월 주간 자료 중 50만 행을 학습에 사용하고 2024-06~2025-05월 주간 자료를 평가했으므로, 학습 창이 다른 E0~E7 표와 직접 순위를 매기지 않습니다. W_over_revenue는 Σ(SMP×k×절대오차)/Σ(SMP×k×실적)의 비율이며 백분율이나 공식 점수가 아니고, 실측 기상 입력 및 같은 모델의 반복 추론 진단을 포함하므로 25행을 새 모델 학습 25회로 세지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| S0 base(geometry+site) | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.3077 | 원본 표/로그 행 1 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.307723232, 발전 비율(CF) R²=0.512499. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sa r17 A | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1293 | 원본 표/로그 행 2 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.129265514, 발전 비율(CF) R²=0.796065. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sb r17 B | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1413 | 원본 표/로그 행 3 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.141276383, 발전 비율(CF) R²=0.787936. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sc r17 A+B | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1224 | 원본 표/로그 행 4 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.122408867, 발전 비율(CF) R²=0.809621. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sa r10 A | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1347 | 원본 표/로그 행 5 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.134718150, 발전 비율(CF) R²=0.791326. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sb r10 B | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1474 | 원본 표/로그 행 6 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.147440442, 발전 비율(CF) R²=0.779895. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sc r10 A+B | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1299 | 원본 표/로그 행 7 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.129878374, 발전 비율(CF) R²=0.802725. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sd r10+r17 A+B | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1250 | 원본 표/로그 행 8 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.124985574, 발전 비율(CF) R²=0.808098. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sa-cloud r17 A cloud | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1881 | 원본 표/로그 행 9 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.188126099, 발전 비율(CF) R²=0.703710. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sb-cloud r17 B cloud | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.2216 | 원본 표/로그 행 10 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.221558720, 발전 비율(CF) R²=0.670851. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sab-cloud r17 A+B cloud | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1774 | 원본 표/로그 행 11 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.177420713, 발전 비율(CF) R²=0.728151. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sb-noCloud r17 B minus cloud | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1434 | 원본 표/로그 행 12 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.143355518, 발전 비율(CF) R²=0.784910. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sa-noCloud r17 A minus cloud | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1523 | 원본 표/로그 행 13 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.152321903, 발전 비율(CF) R²=0.766906. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OA obs A -> obs (perfect weather) | historical_record | 완벽한 날씨 가정 진단·제출 불가 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1032 | 원본 표/로그 행 14 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.103165935, 발전 비율(CF) R²=0.827505. 실측 기상을 평가 입력으로 사용하는 완벽 예보 진단이며 실제 제출 가능한 후보가 아닙니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OA obs A -> r17 fc (obs-trained model fed forecast) | historical_record | 관측 학습·예보 입력 차이 진단 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1307 | 원본 표/로그 행 15 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.130727791, 발전 비율(CF) R²=0.789331. 실측 기상으로 학습한 모델에 예보를 넣은 분포 차이 진단입니다. 같은 학습 모델의 여러 입력 비교가 포함됩니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OA obs A -> r10 fc | historical_record | 관측 학습·예보 입력 차이 진단 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1362 | 원본 표/로그 행 16 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.136209411, 발전 비율(CF) R²=0.783927. 실측 기상으로 학습한 모델에 예보를 넣은 분포 차이 진단입니다. 같은 학습 모델의 여러 입력 비교가 포함됩니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OA fc17 A (fc-trained, fc-fed, same vars) | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1293 | 원본 표/로그 행 17 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.129265514, 발전 비율(CF) R²=0.796065. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OB obs B -> obs (perfect weather) | historical_record | 완벽한 날씨 가정 진단·제출 불가 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.0943 | 원본 표/로그 행 18 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.094269333, 발전 비율(CF) R²=0.844936. 실측 기상을 평가 입력으로 사용하는 완벽 예보 진단이며 실제 제출 가능한 후보가 아닙니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OB obs B -> r17 fc (obs-trained model fed forecast) | historical_record | 관측 학습·예보 입력 차이 진단 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1771 | 원본 표/로그 행 19 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.177117221, 발전 비율(CF) R²=0.727710. 실측 기상으로 학습한 모델에 예보를 넣은 분포 차이 진단입니다. 같은 학습 모델의 여러 입력 비교가 포함됩니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OB obs B -> r10 fc | historical_record | 관측 학습·예보 입력 차이 진단 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1832 | 원본 표/로그 행 20 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.183246558, 발전 비율(CF) R²=0.716787. 실측 기상으로 학습한 모델에 예보를 넣은 분포 차이 진단입니다. 같은 학습 모델의 여러 입력 비교가 포함됩니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OB fc17 B (fc-trained, fc-fed, same vars) | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1430 | 원본 표/로그 행 21 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.143037449, 발전 비율(CF) R²=0.785447. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OC obs A+B -> obs (perfect weather) | historical_record | 완벽한 날씨 가정 진단·제출 불가 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.0847 | 원본 표/로그 행 22 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.084678284, 발전 비율(CF) R²=0.861470. 실측 기상을 평가 입력으로 사용하는 완벽 예보 진단이며 실제 제출 가능한 후보가 아닙니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OC obs A+B -> r17 fc (obs-trained model fed forecast) | historical_record | 관측 학습·예보 입력 차이 진단 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1515 | 원본 표/로그 행 23 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.151455415, 발전 비율(CF) R²=0.777385. 실측 기상으로 학습한 모델에 예보를 넣은 분포 차이 진단입니다. 같은 학습 모델의 여러 입력 비교가 포함됩니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OC obs A+B -> r10 fc | historical_record | 관측 학습·예보 입력 차이 진단 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1572 | 원본 표/로그 행 24 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.157163020, 발전 비율(CF) R²=0.769749. 실측 기상으로 학습한 모델에 예보를 넣은 분포 차이 진단입니다. 같은 학습 모델의 여러 입력 비교가 포함됩니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OC fc17 A+B (fc-trained, fc-fed, same vars) | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1261 | 원본 표/로그 행 25 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.126055866, 발전 비율(CF) R²=0.807531. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |

## 기존 10시간 단계

현재 고정된 실행 큐

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| c000 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0000 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c000/result.json) |
| c001 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0894 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c001/result.json) |
| c002 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9492 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c002/result.json) |
| c003 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9211 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c003/result.json) |
| c004 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9310 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c004/result.json) |
| c005 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0558 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c005/result.json) |
| c006 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9875 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c006/result.json) |
| c007 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0799 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c007/result.json) |
| c008 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9553 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c008/result.json) |
| c009 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0270 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c009/result.json) |
| c010 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9409 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c010/result.json) |
| c011 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0843 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c011/result.json) |
| c012 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9560 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c012/result.json) |
| c013 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0849 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c013/result.json) |
| c014 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9493 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c014/result.json) |
| c015 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0478 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c015/result.json) |
| c016 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1077 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c016/result.json) |
| c017 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9811 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c017/result.json) |
| c018 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1509 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c018/result.json) |
| c019 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9706 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c019/result.json) |
| c020 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1634 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c020/result.json) |
| c021 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9503 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c021/result.json) |
| c022 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0697 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c022/result.json) |
| c023 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9831 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c023/result.json) |
| c024 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0111 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c024/result.json) |
| c025 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9676 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c025/result.json) |
| c026 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0510 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c026/result.json) |
| c027 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9430 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c027/result.json) |
| c028 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0279 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c028/result.json) |
| c029 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9469 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c029/result.json) |
| c030 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0001 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c030/result.json) |
| c031 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9841 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c031/result.json) |
| c032 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9491 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c032/result.json) |
| c033 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0688 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c033/result.json) |
| c034 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9420 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c034/result.json) |
| c035 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1657 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c035/result.json) |
| c036 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9384 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c036/result.json) |
| c037 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1621 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c037/result.json) |
| c038 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9469 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c038/result.json) |
| c039 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0317 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c039/result.json) |
| c040 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9679 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c040/result.json) |
| c041 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1689 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c041/result.json) |
| c042 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9782 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c042/result.json) |
| c043 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0525 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c043/result.json) |
| c044 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9355 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c044/result.json) |
| c045 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0562 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c045/result.json) |
| c046 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9303 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c046/result.json) |
| c047 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1474 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c047/result.json) |
| c048 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1828 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c048/result.json) |
| c049 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9504 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c049/result.json) |
| c050 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0991 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c050/result.json) |
| c051 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9604 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c051/result.json) |
| c052 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1537 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c052/result.json) |
| c053 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9441 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c053/result.json) |
| c054 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1662 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c054/result.json) |
| c055 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9930 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c055/result.json) |
| c056 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1583 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c056/result.json) |
| c057 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9657 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c057/result.json) |
| c058 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1017 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c058/result.json) |
| c059 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9614 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c059/result.json) |
| c060 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0932 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c060/result.json) |
| c061 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9610 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c061/result.json) |
| c062 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1016 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c062/result.json) |
| c063 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9812 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c063/result.json) |
| c064 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9626 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c064/result.json) |
| c065 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1621 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c065/result.json) |
| c066 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9401 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c066/result.json) |
| c067 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1703 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c067/result.json) |
| c068 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9526 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c068/result.json) |
| c069 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0816 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c069/result.json) |
| c070 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9548 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c070/result.json) |
| c071 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1872 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c071/result.json) |
| c072 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9742 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c072/result.json) |
| c073 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0091 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c073/result.json) |
| c074 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9388 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c074/result.json) |
| c075 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0707 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c075/result.json) |
| c076 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9472 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c076/result.json) |
| c077 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1425 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c077/result.json) |
| c078 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9367 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c078/result.json) |
| c079 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0727 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c079/result.json) |
| c080 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0812 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c080/result.json) |
| c081 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9308 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c081/result.json) |
| c082 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0667 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c082/result.json) |
| c083 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9512 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c083/result.json) |
| c084 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0727 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c084/result.json) |
| c085 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9384 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c085/result.json) |
| c086 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0064 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c086/result.json) |
| c087 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9931 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c087/result.json) |
| c088 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0570 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c088/result.json) |
| c089 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9484 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c089/result.json) |
| c090 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0491 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c090/result.json) |
| c091 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9477 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c091/result.json) |
| c092 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0406 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c092/result.json) |
| c093 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9288 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c093/result.json) |
| c094 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0989 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c094/result.json) |
| c095 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9653 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c095/result.json) |
| c096 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9512 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c096/result.json) |
| c097 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0723 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c097/result.json) |
| c098 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9563 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c098/result.json) |
| c099 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1677 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c099/result.json) |
| c100 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9432 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c100/result.json) |
| c101 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0522 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c101/result.json) |
| c102 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9788 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c102/result.json) |
| c103 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0997 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c103/result.json) |
| c104 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9576 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c104/result.json) |
| c105 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1597 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c105/result.json) |
| c106 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9824 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c106/result.json) |
| c107 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1360 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c107/result.json) |
| c108 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9876 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c108/result.json) |
| c109 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1456 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c109/result.json) |
| c110 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9616 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c110/result.json) |
| c111 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1127 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c111/result.json) |
| c112 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0162 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c112/result.json) |
| c113 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9750 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c113/result.json) |
| c114 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0432 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c114/result.json) |
| c115 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9458 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c115/result.json) |
| c116 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0832 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c116/result.json) |
| c117 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9339 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c117/result.json) |
| c118 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0492 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c118/result.json) |
| c119 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9941 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c119/result.json) |
| c120 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0578 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c120/result.json) |
| c121 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9725 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c121/result.json) |
| c122 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0986 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c122/result.json) |
| c123 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9781 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c123/result.json) |
| c124 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0232 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c124/result.json) |
| c125 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9522 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c125/result.json) |
| c126 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0331 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c126/result.json) |
| c127 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9624 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c127/result.json) |
| c128 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9445 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c128/result.json) |
| c129 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0443 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c129/result.json) |
| c130 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9491 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c130/result.json) |
| c131 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1704 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c131/result.json) |
| c132 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9760 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c132/result.json) |
| c133 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0315 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c133/result.json) |
| c134 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9537 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c134/result.json) |
| c135 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0442 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c135/result.json) |
| c136 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9555 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c136/result.json) |
| c137 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1434 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c137/result.json) |
| c138 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9401 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c138/result.json) |
| c139 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0427 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c139/result.json) |
| c140 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9514 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c140/result.json) |
| c141 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0893 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c141/result.json) |
| c142 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9259 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c142/result.json) |
| c143 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1007 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c143/result.json) |
| c144 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1663 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c144/result.json) |
| c145 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9494 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c145/result.json) |
| c146 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0911 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c146/result.json) |
| c147 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9574 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c147/result.json) |
| c148 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0057 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c148/result.json) |
| c149 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9718 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c149/result.json) |
| c150 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0851 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c150/result.json) |
| c151 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9692 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c151/result.json) |
| c152 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0723 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c152/result.json) |
| c153 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9836 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c153/result.json) |
| c154 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0605 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c154/result.json) |
| c155 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9587 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c155/result.json) |
| c156 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1587 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c156/result.json) |
| c157 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9410 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c157/result.json) |
| c158 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9999 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c158/result.json) |
| c159 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9712 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c159/result.json) |
| c160 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9437 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c160/result.json) |
| c161 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0155 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c161/result.json) |
| c162 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9574 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c162/result.json) |
| c163 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0510 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c163/result.json) |
| c164 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9338 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c164/result.json) |
| c165 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1462 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c165/result.json) |
| c166 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9342 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c166/result.json) |
| c167 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1632 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c167/result.json) |
| c168 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9637 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c168/result.json) |
| c169 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1336 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c169/result.json) |
| c170 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9441 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c170/result.json) |
| c171 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0554 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c171/result.json) |
| c172 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9411 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c172/result.json) |
| c173 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0085 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c173/result.json) |
| c174 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9228 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c174/result.json) |
| c175 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1407 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c175/result.json) |
| c176 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0692 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c176/result.json) |
| c177 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9602 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c177/result.json) |
| c178 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1597 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c178/result.json) |
| c179 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9802 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c179/result.json) |
| c180 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0296 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c180/result.json) |
| c181 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9668 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c181/result.json) |
| c182 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1782 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c182/result.json) |
| c183 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9642 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c183/result.json) |
| c184 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0858 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c184/result.json) |
| c185 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9326 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c185/result.json) |
| c186 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0000 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c186/result.json) |
| c187 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9632 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c187/result.json) |
| c188 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1696 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c188/result.json) |
| c189 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9570 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c189/result.json) |
| c190 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0096 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c190/result.json) |
| c191 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9413 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c191/result.json) |
| c192 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9582 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c192/result.json) |
| c193 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0628 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c193/result.json) |
| c194 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9822 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c194/result.json) |
| c195 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0441 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c195/result.json) |
| c196 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9865 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c196/result.json) |
| c197 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0516 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c197/result.json) |
| c198 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9496 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c198/result.json) |
| c199 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0528 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c199/result.json) |
| c200 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9379 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c200/result.json) |
| c201 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0579 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c201/result.json) |
| c202 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9597 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c202/result.json) |
| c203 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0268 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c203/result.json) |
| c204 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9624 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c204/result.json) |
| c205 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1515 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c205/result.json) |
| c206 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9207 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c206/result.json) |
| c207 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0974 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c207/result.json) |
| c208 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1519 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c208/result.json) |
| c209 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9785 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c209/result.json) |
| c210 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0786 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c210/result.json) |
| c211 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9600 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c211/result.json) |
| c212 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1006 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c212/result.json) |
| c213 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9330 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c213/result.json) |
| c214 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0618 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c214/result.json) |
| c215 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9691 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c215/result.json) |
| c216 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1964 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c216/result.json) |
| c217 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9814 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c217/result.json) |
| c218 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0621 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c218/result.json) |
| c219 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9526 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c219/result.json) |
| c220 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1076 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c220/result.json) |
| c221 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9418 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c221/result.json) |
| c222 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0308 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c222/result.json) |
| c223 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9586 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c223/result.json) |
| c224 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9413 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c224/result.json) |
| c225 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0860 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c225/result.json) |
| c226 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9491 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c226/result.json) |
| c227 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1827 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c227/result.json) |
| c228 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9682 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c228/result.json) |
| c229 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0604 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c229/result.json) |
| c230 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9543 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c230/result.json) |
| c231 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1694 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c231/result.json) |
| c232 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9510 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c232/result.json) |
| c233 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0302 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c233/result.json) |
| c234 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9537 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c234/result.json) |
| c235 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0156 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c235/result.json) |
| c236 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9706 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c236/result.json) |
| c237 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1641 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c237/result.json) |
| c238 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9605 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c238/result.json) |
| c239 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1053 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c239/result.json) |
| c240 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0172 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c240/result.json) |
| c241 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9323 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c241/result.json) |
| c242 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1609 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c242/result.json) |
| c243 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9487 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c243/result.json) |
| c244 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0162 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c244/result.json) |
| c245 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9743 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c245/result.json) |
| c246 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0100 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c246/result.json) |
| c247 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0081 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c247/result.json) |
| c248 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0226 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c248/result.json) |
| c249 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9788 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c249/result.json) |
| c250 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0846 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c250/result.json) |
| c251 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9572 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c251/result.json) |
| c252 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.1445 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c252/result.json) |
| c253 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9579 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c253/result.json) |
| c254 | generation | 완료 | 5/5 | 5 | mean W / c000 | 1.0970 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c254/result.json) |
| c255 | generation | 완료 | 5/5 | 5 | mean W / c000 | 0.9561 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c255/result.json) |

## 12시간 연장 단계

현재 고정된 실행 큐

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| n0000 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9296 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0000/result.json) |
| n0001 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9261 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0001/result.json) |
| n0002 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9295 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0002/result.json) |
| n0003 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9258 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0003/result.json) |
| n0004 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9199 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0004/result.json) |
| n0005 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0009 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0005/result.json) |
| n0006 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9208 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0006/result.json) |
| n0007 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9539 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0007/result.json) |
| n0008 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0046 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0008/result.json) |
| n0009 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9302 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0009/result.json) |
| n0010 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9182 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0010/result.json) |
| n0011 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9286 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0011/result.json) |
| n0012 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9834 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0012/result.json) |
| n0013 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9256 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0013/result.json) |
| n0014 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9224 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0014/result.json) |
| n0015 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9212 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0015/result.json) |
| n0016 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9238 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0016/result.json) |
| n0017 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9235 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0017/result.json) |
| n0018 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9275 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0018/result.json) |
| n0019 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9210 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0019/result.json) |
| n0020 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9330 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0020/result.json) |
| n0021 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0126 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0021/result.json) |
| n0022 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9173 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0022/result.json) |
| n0023 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9308 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0023/result.json) |
| n0024 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9220 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0024/result.json) |
| n0025 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9247 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0025/result.json) |
| n0026 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9342 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0026/result.json) |
| n0027 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9588 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0027/result.json) |
| n0028 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9651 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0028/result.json) |
| n0029 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9213 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0029/result.json) |
| n0030 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9314 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0030/result.json) |
| n0031 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9904 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0031/result.json) |
| n0032 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9245 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0032/result.json) |
| n0033 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9607 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0033/result.json) |
| n0034 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9551 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0034/result.json) |
| n0035 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9229 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0035/result.json) |
| n0036 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9469 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0036/result.json) |
| n0037 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9364 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0037/result.json) |
| n0038 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9686 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0038/result.json) |
| n0039 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9383 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0039/result.json) |
| n0040 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9270 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0040/result.json) |
| n0041 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9748 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0041/result.json) |
| n0042 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9365 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0042/result.json) |
| n0043 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9219 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0043/result.json) |
| n0044 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9205 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0044/result.json) |
| n0045 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9598 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0045/result.json) |
| n0046 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9672 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0046/result.json) |
| n0047 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9402 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0047/result.json) |
| n0048 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9400 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0048/result.json) |
| n0049 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9352 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0049/result.json) |
| n0050 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9218 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0050/result.json) |
| n0051 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9941 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0051/result.json) |
| n0052 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9183 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0052/result.json) |
| n0053 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9233 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0053/result.json) |
| n0054 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9221 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0054/result.json) |
| n0055 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9561 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0055/result.json) |
| n0056 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9343 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0056/result.json) |
| n0057 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9652 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0057/result.json) |
| n0058 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9332 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0058/result.json) |
| n0059 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9535 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0059/result.json) |
| n0060 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9530 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0060/result.json) |
| n0061 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9623 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0061/result.json) |
| n0062 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9309 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0062/result.json) |
| n0063 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9754 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0063/result.json) |
| n0064 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9345 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0064/result.json) |
| n0065 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9303 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0065/result.json) |
| n0066 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9339 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0066/result.json) |
| n0067 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9297 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0067/result.json) |
| n0068 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9288 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0068/result.json) |
| n0069 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9785 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0069/result.json) |
| n0070 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9999 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0070/result.json) |
| n0071 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9831 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0071/result.json) |
| n0072 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9265 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0072/result.json) |
| n0073 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0145 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0073/result.json) |
| n0074 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0114 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0074/result.json) |
| n0075 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0078 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0075/result.json) |
| n0076 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9971 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0076/result.json) |
| n0077 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9803 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0077/result.json) |
| n0078 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9709 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0078/result.json) |
| n0079 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9325 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0079/result.json) |
| n0080 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0272 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0080/result.json) |
| n0081 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9854 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0081/result.json) |
| n0082 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0022 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0082/result.json) |
| n0083 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9617 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0083/result.json) |
| n0084 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9324 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0084/result.json) |
| n0085 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9329 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0085/result.json) |
| n0086 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9277 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0086/result.json) |
| n0087 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9358 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0087/result.json) |
| n0088 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9279 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0088/result.json) |
| n0089 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9816 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0089/result.json) |
| n0090 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0035 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0090/result.json) |
| n0091 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9447 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0091/result.json) |
| n0092 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9730 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0092/result.json) |
| n0093 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9286 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0093/result.json) |
| n0094 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9491 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0094/result.json) |
| n0095 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9582 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0095/result.json) |
| n0096 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9796 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0096/result.json) |
| n0097 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9284 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0097/result.json) |
| n0098 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9722 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0098/result.json) |
| n0099 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9924 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0099/result.json) |
| n0100 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9621 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0100/result.json) |
| n0101 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9293 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0101/result.json) |
| n0102 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0168 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0102/result.json) |
| n0103 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9326 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0103/result.json) |
| n0104 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9289 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0104/result.json) |
| n0105 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0034 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0105/result.json) |
| n0106 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9616 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0106/result.json) |
| n0107 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0284 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0107/result.json) |
| n0108 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9454 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0108/result.json) |
| n0109 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9403 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0109/result.json) |
| n0110 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9501 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0110/result.json) |
| n0111 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0106 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0111/result.json) |
| n0112 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9252 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0112/result.json) |
| n0113 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9258 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0113/result.json) |
| n0114 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0105 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0114/result.json) |
| n0115 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0325 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0115/result.json) |
| n0116 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0180 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0116/result.json) |
| n0117 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0588 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0117/result.json) |
| n0118 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9460 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0118/result.json) |
| n0119 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9286 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0119/result.json) |
| n0120 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9575 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0120/result.json) |
| n0121 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9692 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0121/result.json) |
| n0122 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9485 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0122/result.json) |
| n0123 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9327 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0123/result.json) |
| n0124 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9269 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0124/result.json) |
| n0125 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9423 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0125/result.json) |
| n0126 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9299 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0126/result.json) |
| n0127 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9909 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0127/result.json) |
| n0128 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9668 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0128/result.json) |
| n0129 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9711 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0129/result.json) |
| n0130 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9694 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0130/result.json) |
| n0131 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9739 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0131/result.json) |
| n0132 | calibration | 실패 | 5/5 | 5 | mean W / c000 (실패 기록 독립 감사) | 0.9529 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T083900Z_failed_candidates_science.json) |
| n0133 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9819 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0133/result.json) |
| n0134 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9784 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0134/result.json) |
| n0135 | calibration | 실패 | 5/5 | 5 | mean W / c000 (실패 기록 독립 감사) | 0.9704 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T083900Z_failed_candidates_science.json) |
| n0136 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9775 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0136/result.json) |
| n0137 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9705 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0137/result.json) |
| n0138 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9746 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0138/result.json) |
| n0139 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9671 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0139/result.json) |
| n0140 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9844 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0140/result.json) |
| n0141 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9835 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0141/result.json) |
| n0142 | calibration | 실패 | 5/5 | 5 | mean W / c000 (실패 기록 독립 감사) | 0.9590 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T083900Z_failed_candidates_science.json) |
| n0143 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9923 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0143/result.json) |
| n0144 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9807 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0144/result.json) |
| n0145 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9729 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0145/result.json) |
| n0146 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9859 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0146/result.json) |
| n0147 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9986 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0147/result.json) |
| n0148 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9777 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0148/result.json) |
| n0149 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9876 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0149/result.json) |
| n0150 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9726 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0150/result.json) |
| n0151 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9781 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0151/result.json) |
| n0152 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9729 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0152/result.json) |
| n0153 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9651 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0153/result.json) |
| n0154 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9683 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0154/result.json) |
| n0155 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9892 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0155/result.json) |
| n0156 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9777 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0156/result.json) |
| n0157 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9769 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0157/result.json) |
| n0158 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9786 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0158/result.json) |
| n0159 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9960 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0159/result.json) |
| n0160 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9766 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0160/result.json) |
| n0161 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9791 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0161/result.json) |
| n0162 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9786 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0162/result.json) |
| n0163 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9758 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0163/result.json) |
| n0164 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9716 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0164/result.json) |
| n0165 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9817 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0165/result.json) |
| n0166 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9701 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0166/result.json) |
| n0167 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9771 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0167/result.json) |
| n0168 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9633 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0168/result.json) |
| n0169 | calibration | 실패 | 5/5 | 5 | mean W / c000 (실패 기록 독립 감사) | 0.9669 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T083900Z_failed_candidates_science.json) |
| n0170 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9874 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0170/result.json) |
| n0171 | calibration | 실패 | 5/5 | 5 | mean W / c000 (실패 기록 독립 감사) | 0.9847 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T083900Z_failed_candidates_science.json) |
| n0172 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9831 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0172/result.json) |
| n0173 | calibration | 실패 | 5/5 | 5 | mean W / c000 (실패 기록 독립 감사) | 0.9826 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T083900Z_failed_candidates_science.json) |
| n0174 | calibration | 실패 | 5/5 | 5 | mean W / c000 (실패 기록 독립 감사) | 0.9764 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T083900Z_failed_candidates_science.json) |
| n0175 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9921 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0175/result.json) |
| n0176 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9874 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0176/result.json) |
| n0177 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9691 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0177/result.json) |
| n0178 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9898 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0178/result.json) |
| n0179 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9787 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0179/result.json) |
| n0180 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0028 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0180/result.json) |
| n0181 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9802 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0181/result.json) |
| n0182 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9804 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0182/result.json) |
| n0183 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9812 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0183/result.json) |
| n0184 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9841 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0184/result.json) |
| n0185 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9710 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0185/result.json) |
| n0186 | calibration | 실패 | 5/5 | 5 | mean W / c000 (실패 기록 독립 감사) | 0.9675 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T083900Z_failed_candidates_science.json) |
| n0187 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9743 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0187/result.json) |
| n0188 | calibration | 실패 | 5/5 | 5 | mean W / c000 (실패 기록 독립 감사) | 0.9647 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T083900Z_failed_candidates_science.json) |
| n0189 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9766 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0189/result.json) |
| n0190 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9679 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0190/result.json) |
| n0191 | calibration | 실패 | 5/5 | 5 | mean W / c000 (실패 기록 독립 감사) | 0.9745 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T083900Z_failed_candidates_science.json) |
| n0192 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9346 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0192/result.json) |
| n0193 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9288 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0193/result.json) |
| n0194 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9339 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0194/result.json) |
| n0195 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9283 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0195/result.json) |
| n0196 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9260 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0196/result.json) |
| n0197 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9319 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0197/result.json) |
| n0198 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9391 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0198/result.json) |
| n0199 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9269 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0199/result.json) |
| n0200 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9278 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0200/result.json) |
| n0201 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9803 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0201/result.json) |
| n0202 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9488 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0202/result.json) |
| n0203 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0095 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0203/result.json) |
| n0204 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9278 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0204/result.json) |
| n0205 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9987 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0205/result.json) |
| n0206 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9461 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0206/result.json) |
| n0207 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9261 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0207/result.json) |
| n0208 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9774 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0208/result.json) |
| n0209 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9678 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0209/result.json) |
| n0210 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9587 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0210/result.json) |
| n0211 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9287 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0211/result.json) |
| n0212 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9388 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0212/result.json) |
| n0213 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9511 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0213/result.json) |
| n0214 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9672 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0214/result.json) |
| n0215 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9688 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0215/result.json) |
| n0216 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9700 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0216/result.json) |
| n0217 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9733 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0217/result.json) |
| n0218 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9760 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0218/result.json) |
| n0219 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9512 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0219/result.json) |
| n0220 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9900 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0220/result.json) |
| n0221 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9570 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0221/result.json) |
| n0222 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9252 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0222/result.json) |
| n0223 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0017 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0223/result.json) |
| n0224 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9605 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0224/result.json) |
| n0225 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9552 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0225/result.json) |
| n0226 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9752 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0226/result.json) |
| n0227 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0152 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0227/result.json) |
| n0228 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9970 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0228/result.json) |
| n0229 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9281 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0229/result.json) |
| n0230 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9276 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0230/result.json) |
| n0231 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9878 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0231/result.json) |
| n0232 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9627 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0232/result.json) |
| n0233 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9396 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0233/result.json) |
| n0234 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9276 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0234/result.json) |
| n0235 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9497 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0235/result.json) |
| n0236 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9624 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0236/result.json) |
| n0237 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0267 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0237/result.json) |
| n0238 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9382 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0238/result.json) |
| n0239 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9563 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0239/result.json) |
| n0240 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9280 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0240/result.json) |
| n0241 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0127 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0241/result.json) |
| n0242 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9283 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0242/result.json) |
| n0243 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9641 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0243/result.json) |
| n0244 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9563 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0244/result.json) |
| n0245 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9970 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0245/result.json) |
| n0246 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9405 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0246/result.json) |
| n0247 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9299 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0247/result.json) |
| n0248 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9465 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0248/result.json) |
| n0249 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9443 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0249/result.json) |
| n0250 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9251 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0250/result.json) |
| n0251 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9550 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0251/result.json) |
| n0252 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9730 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0252/result.json) |
| n0253 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0036 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0253/result.json) |
| n0254 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9256 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0254/result.json) |
| n0255 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9385 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0255/result.json) |
| n0256 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9494 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0256/result.json) |
| n0257 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9451 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0257/result.json) |
| n0258 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9481 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0258/result.json) |
| n0259 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9435 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0259/result.json) |
| n0260 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9437 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0260/result.json) |
| n0261 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9545 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0261/result.json) |
| n0262 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9377 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0262/result.json) |
| n0263 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9389 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0263/result.json) |
| n0264 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9393 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0264/result.json) |
| n0265 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0106 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0265/result.json) |
| n0266 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9687 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0266/result.json) |
| n0267 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9346 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0267/result.json) |
| n0268 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9427 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0268/result.json) |
| n0269 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9364 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0269/result.json) |
| n0270 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9547 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0270/result.json) |
| n0271 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9588 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0271/result.json) |
| n0272 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9517 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0272/result.json) |
| n0273 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0373 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0273/result.json) |
| n0274 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9333 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0274/result.json) |
| n0275 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9647 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0275/result.json) |
| n0276 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9997 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0276/result.json) |
| n0277 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9904 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0277/result.json) |
| n0278 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9803 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0278/result.json) |
| n0279 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0022 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0279/result.json) |
| n0280 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0034 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0280/result.json) |
| n0281 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9527 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0281/result.json) |
| n0282 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0348 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0282/result.json) |
| n0283 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9875 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0283/result.json) |
| n0284 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9537 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0284/result.json) |
| n0285 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0070 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0285/result.json) |
| n0286 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9590 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0286/result.json) |
| n0287 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9447 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0287/result.json) |
| n0288 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9924 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0288/result.json) |
| n0289 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9902 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0289/result.json) |
| n0290 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9710 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0290/result.json) |
| n0291 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0281 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0291/result.json) |
| n0292 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9883 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0292/result.json) |
| n0293 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9878 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0293/result.json) |
| n0294 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9362 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0294/result.json) |
| n0295 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9870 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0295/result.json) |
| n0296 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9521 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0296/result.json) |
| n0297 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0127 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0297/result.json) |
| n0298 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0015 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0298/result.json) |
| n0299 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9352 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0299/result.json) |
| n0300 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9357 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0300/result.json) |
| n0301 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9351 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0301/result.json) |
| n0302 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9380 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0302/result.json) |
| n0303 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9676 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0303/result.json) |
| n0304 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9521 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0304/result.json) |
| n0305 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9577 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0305/result.json) |
| n0306 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9584 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0306/result.json) |
| n0307 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9900 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0307/result.json) |
| n0308 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9329 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0308/result.json) |
| n0309 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0134 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0309/result.json) |
| n0310 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9512 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0310/result.json) |
| n0311 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0114 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0311/result.json) |
| n0312 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9590 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0312/result.json) |
| n0313 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0147 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0313/result.json) |
| n0314 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9501 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0314/result.json) |
| n0315 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9704 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0315/result.json) |
| n0316 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9680 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0316/result.json) |
| n0317 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9360 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0317/result.json) |
| n0318 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0081 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0318/result.json) |
| n0319 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0078 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0319/result.json) |
| n0320 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9592 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0320/result.json) |
| n0321 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9567 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0321/result.json) |
| n0322 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9563 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0322/result.json) |
| n0323 | calibration | 완료 | 5/5 | 0 | mean W / c000 | 0.9537 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0323/result.json) |
| n0324 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9570 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0324/result.json) |
| n0325 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9439 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0325/result.json) |
| n0326 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9359 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0326/result.json) |
| n0327 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0092 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0327/result.json) |
| n0328 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0279 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0328/result.json) |
| n0329 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9359 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0329/result.json) |
| n0330 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9522 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0330/result.json) |
| n0331 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9432 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0331/result.json) |
| n0332 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9478 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0332/result.json) |
| n0333 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9577 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0333/result.json) |
| n0334 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9995 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0334/result.json) |
| n0335 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9394 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0335/result.json) |
| n0336 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9659 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0336/result.json) |
| n0337 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9394 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0337/result.json) |
| n0338 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9353 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0338/result.json) |
| n0339 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9480 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0339/result.json) |
| n0340 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 1.0269 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0340/result.json) |
| n0341 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9518 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0341/result.json) |
| n0342 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9763 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0342/result.json) |
| n0343 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9662 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0343/result.json) |
| n0344 | calibration | 완료 | 5/5 | 5 | mean W / c000 | 0.9903 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0344/result.json) |
| n0345 | calibration | 결과 기록 후 종료 확인 중 | 5/5 | 5 | mean W / c000 | 0.9410 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0345/result.json) |
| n0346 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0347 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0348 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0349 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0350 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0351 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0352 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0353 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0354 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0355 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0356 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0357 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0358 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0359 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0360 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0361 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0362 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0363 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0364 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0365 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0366 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0367 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0368 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0369 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0370 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0371 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0372 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0373 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0374 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0375 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0376 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0377 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0378 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0379 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0380 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0381 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0382 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0383 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0384 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0385 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0386 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0387 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0388 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0389 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0390 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0391 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0392 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0393 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0394 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0395 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0396 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0397 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0398 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0399 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0400 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0401 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0402 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0403 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0404 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0405 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0406 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0407 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0408 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0409 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0410 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0411 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0412 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0413 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0414 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0415 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0416 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0417 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0418 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0419 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0420 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0421 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0422 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0423 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0424 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0425 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0426 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0427 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0428 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0429 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0430 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0431 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0432 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0433 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0434 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0435 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0436 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0437 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0438 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0439 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0440 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0441 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0442 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0443 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0444 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0445 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0446 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0447 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0448 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0449 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0450 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0451 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0452 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0453 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0454 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0455 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0456 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0457 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0458 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0459 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0460 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0461 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0462 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0463 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0464 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0465 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0466 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0467 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0468 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0469 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0470 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0471 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0472 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0473 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0474 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0475 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0476 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0477 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0478 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0479 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0480 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0481 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0482 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0483 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0484 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0485 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0486 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0487 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0488 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0489 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0490 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0491 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0492 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0493 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0494 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0495 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0496 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0497 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0498 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0499 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0500 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0501 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0502 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0503 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0504 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0505 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0506 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0507 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0508 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0509 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0510 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0511 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0512 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0513 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0514 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0515 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0516 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0517 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0518 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0519 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0520 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0521 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0522 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0523 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0524 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0525 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0526 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0527 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0528 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0529 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0530 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0531 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0532 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0533 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0534 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0535 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0536 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0537 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0538 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0539 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0540 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0541 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0542 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0543 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0544 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0545 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0546 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0547 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0548 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0549 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0550 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0551 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0552 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0553 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0554 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0555 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0556 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0557 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0558 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0559 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0560 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0561 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0562 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0563 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0564 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0565 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0566 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0567 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0568 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0569 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0570 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0571 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0572 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0573 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0574 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0575 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0576 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0577 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0578 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0579 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0580 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0581 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0582 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0583 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0584 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0585 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0586 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0587 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0588 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0589 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0590 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0591 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0592 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0593 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0594 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0595 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0596 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0597 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0598 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0599 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0600 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0601 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0602 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0603 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0604 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0605 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0606 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0607 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0608 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0609 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0610 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0611 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0612 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0613 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0614 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0615 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0616 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0617 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0618 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0619 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0620 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0621 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0622 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0623 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0624 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0625 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0626 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0627 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0628 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0629 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0630 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0631 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0632 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0633 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0634 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0635 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0636 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0637 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0638 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0639 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0640 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0641 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0642 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0643 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0644 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0645 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0646 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0647 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0648 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0649 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0650 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0651 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0652 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0653 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0654 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0655 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0656 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0657 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0658 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0659 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0660 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0661 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0662 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0663 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0664 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0665 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0666 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0667 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0668 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0669 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0670 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0671 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0672 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0673 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0674 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0675 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0676 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0677 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0678 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0679 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0680 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0681 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0682 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0683 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0684 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0685 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0686 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0687 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0688 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0689 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0690 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0691 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0692 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0693 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0694 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0695 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0696 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0697 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0698 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0699 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0700 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0701 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0702 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0703 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0704 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0705 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0706 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0707 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0708 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0709 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0710 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0711 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0712 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0713 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0714 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0715 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0716 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0717 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0718 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0719 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0720 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0721 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0722 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0723 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0724 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0725 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0726 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0727 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0728 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0729 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0730 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0731 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0732 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0733 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0734 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0735 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0736 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0737 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0738 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0739 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0740 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0741 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0742 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0743 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0744 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0745 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0746 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0747 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0748 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0749 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0750 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0751 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0752 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0753 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0754 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0755 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0756 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0757 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0758 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0759 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0760 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0761 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0762 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0763 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0764 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0765 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0766 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0767 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0768 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0769 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0770 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0771 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0772 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0773 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0774 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0775 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0776 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0777 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0778 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0779 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0780 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0781 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0782 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0783 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0784 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0785 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0786 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0787 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0788 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0789 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0790 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0791 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0792 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0793 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0794 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0795 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0796 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0797 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0798 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0799 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0800 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0801 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0802 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0803 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0804 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0805 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0806 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0807 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0808 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0809 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0810 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0811 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0812 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0813 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0814 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0815 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0816 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0817 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0818 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0819 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0820 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0821 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0822 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0823 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0824 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0825 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0826 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0827 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0828 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0829 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0830 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0831 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0832 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0833 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0834 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0835 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0836 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0837 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0838 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0839 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0840 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0841 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0842 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0843 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0844 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0845 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0846 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0847 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0848 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0849 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0850 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0851 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0852 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0853 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0854 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0855 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0856 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0857 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0858 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0859 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0860 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0861 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0862 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0863 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0864 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0865 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0866 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0867 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0868 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0869 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0870 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0871 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0872 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0873 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0874 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0875 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0876 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0877 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0878 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0879 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0880 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0881 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0882 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0883 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0884 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0885 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0886 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0887 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0888 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0889 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0890 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0891 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0892 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0893 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0894 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0895 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0896 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0897 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0898 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0899 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0900 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0901 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0902 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0903 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0904 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0905 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0906 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0907 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0908 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0909 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0910 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0911 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0912 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0913 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0914 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0915 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0916 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0917 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0918 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0919 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0920 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0921 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0922 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0923 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0924 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0925 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0926 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0927 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0928 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0929 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0930 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0931 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0932 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0933 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0934 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0935 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0936 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0937 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0938 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0939 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0940 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0941 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0942 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0943 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0944 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0945 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0946 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0947 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0948 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0949 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0950 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0951 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0952 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0953 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0954 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0955 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0956 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0957 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0958 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0959 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0960 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0961 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0962 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0963 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0964 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0965 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0966 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0967 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0968 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0969 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0970 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0971 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0972 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0973 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0974 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0975 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0976 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0977 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0978 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0979 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0980 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0981 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0982 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0983 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0984 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0985 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0986 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0987 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0988 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0989 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0990 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0991 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0992 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0993 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0994 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0995 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0996 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0997 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0998 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n0999 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1000 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1001 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1002 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1003 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1004 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1005 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1006 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1007 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1008 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1009 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1010 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1011 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1012 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1013 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1014 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1015 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1016 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1017 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1018 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1019 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1020 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1021 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1022 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1023 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1024 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1025 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1026 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1027 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1028 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1029 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1030 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1031 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1032 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1033 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1034 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1035 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1036 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1037 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1038 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1039 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1040 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1041 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1042 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1043 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1044 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1045 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1046 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1047 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1048 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1049 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1050 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1051 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1052 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1053 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1054 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1055 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1056 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1057 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1058 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1059 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1060 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1061 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1062 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1063 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1064 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1065 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1066 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1067 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1068 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1069 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1070 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1071 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1072 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1073 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1074 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1075 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1076 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1077 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1078 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1079 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1080 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1081 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1082 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1083 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1084 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1085 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1086 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1087 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1088 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1089 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1090 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1091 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1092 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1093 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1094 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1095 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1096 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1097 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1098 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1099 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1100 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1101 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1102 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1103 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1104 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1105 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1106 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1107 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1108 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1109 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1110 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1111 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1112 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1113 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1114 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1115 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1116 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1117 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1118 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1119 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1120 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1121 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1122 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1123 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1124 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1125 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1126 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1127 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1128 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1129 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1130 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1131 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1132 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1133 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1134 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1135 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1136 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1137 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1138 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1139 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1140 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1141 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1142 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1143 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1144 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1145 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1146 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1147 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1148 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1149 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1150 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1151 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1152 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1153 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1154 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1155 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1156 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1157 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1158 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1159 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1160 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1161 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1162 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1163 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1164 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1165 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1166 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1167 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1168 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1169 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1170 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1171 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1172 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1173 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1174 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1175 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1176 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1177 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1178 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1179 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1180 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1181 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1182 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1183 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1184 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1185 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1186 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1187 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1188 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1189 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1190 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1191 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1192 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1193 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1194 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1195 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1196 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1197 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1198 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1199 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1200 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1201 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1202 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1203 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1204 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1205 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1206 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1207 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1208 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1209 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1210 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1211 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1212 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1213 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1214 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1215 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1216 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1217 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1218 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1219 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1220 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1221 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1222 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1223 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1224 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1225 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1226 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1227 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1228 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1229 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1230 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1231 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1232 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1233 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1234 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1235 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1236 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1237 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1238 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1239 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1240 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1241 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1242 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1243 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1244 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1245 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1246 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1247 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1248 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1249 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1250 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1251 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1252 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1253 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1254 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1255 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1256 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1257 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1258 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1259 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1260 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1261 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1262 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1263 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1264 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1265 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1266 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1267 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1268 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1269 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1270 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1271 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1272 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1273 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1274 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1275 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1276 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1277 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1278 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1279 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1280 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1281 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1282 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1283 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1284 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1285 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1286 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1287 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1288 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1289 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1290 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1291 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1292 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1293 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1294 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1295 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1296 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1297 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1298 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1299 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1300 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1301 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1302 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1303 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1304 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1305 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1306 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1307 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1308 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1309 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1310 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1311 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1312 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1313 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1314 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1315 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1316 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1317 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1318 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1319 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1320 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1321 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1322 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1323 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1324 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1325 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1326 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1327 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1328 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1329 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1330 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1331 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1332 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1333 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1334 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1335 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1336 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1337 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1338 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1339 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1340 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1341 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1342 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1343 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1344 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1345 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1346 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1347 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1348 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1349 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1350 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1351 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1352 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1353 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1354 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1355 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1356 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1357 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1358 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1359 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1360 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1361 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1362 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1363 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1364 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1365 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1366 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1367 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1368 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1369 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1370 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1371 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1372 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1373 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1374 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1375 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1376 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1377 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1378 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1379 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1380 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1381 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1382 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1383 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1384 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1385 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1386 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1387 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1388 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1389 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1390 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1391 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1392 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1393 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1394 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1395 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1396 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1397 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1398 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1399 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1400 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1401 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1402 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1403 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1404 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1405 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1406 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1407 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1408 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1409 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1410 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1411 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1412 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1413 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1414 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1415 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1416 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1417 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1418 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1419 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1420 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1421 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1422 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1423 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1424 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1425 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1426 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1427 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1428 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1429 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1430 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1431 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1432 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1433 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1434 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1435 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1436 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1437 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1438 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1439 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1440 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1441 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1442 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1443 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1444 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1445 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1446 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1447 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1448 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1449 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1450 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1451 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1452 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1453 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1454 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1455 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1456 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1457 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1458 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1459 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1460 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1461 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1462 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1463 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1464 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1465 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1466 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1467 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1468 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1469 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1470 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1471 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1472 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1473 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1474 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1475 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1476 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1477 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1478 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1479 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1480 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1481 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1482 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1483 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1484 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1485 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1486 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1487 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1488 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1489 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1490 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1491 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1492 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1493 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1494 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1495 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1496 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1497 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1498 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1499 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1500 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1501 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1502 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1503 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1504 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1505 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1506 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1507 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1508 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1509 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1510 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1511 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1512 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1513 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1514 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1515 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1516 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1517 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1518 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1519 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1520 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1521 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1522 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1523 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1524 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1525 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1526 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1527 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1528 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1529 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1530 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1531 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1532 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1533 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1534 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1535 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1536 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1537 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1538 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1539 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1540 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1541 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1542 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1543 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1544 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1545 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1546 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1547 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1548 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1549 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1550 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1551 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1552 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1553 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1554 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1555 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1556 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1557 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1558 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1559 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1560 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1561 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1562 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1563 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1564 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1565 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1566 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1567 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1568 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1569 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1570 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1571 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1572 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1573 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1574 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1575 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1576 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1577 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1578 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1579 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1580 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1581 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1582 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1583 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1584 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1585 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1586 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1587 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1588 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1589 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1590 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1591 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1592 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1593 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1594 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1595 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1596 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1597 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1598 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1599 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1600 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1601 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1602 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1603 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1604 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1605 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1606 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1607 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1608 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1609 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1610 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1611 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1612 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1613 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1614 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1615 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1616 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1617 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1618 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1619 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1620 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1621 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1622 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1623 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1624 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1625 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1626 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1627 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1628 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1629 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1630 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1631 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1632 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1633 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1634 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1635 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1636 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1637 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1638 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1639 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1640 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1641 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1642 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1643 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1644 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1645 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1646 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1647 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1648 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1649 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1650 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1651 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1652 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1653 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1654 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1655 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1656 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1657 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1658 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1659 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1660 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1661 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1662 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1663 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1664 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1665 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1666 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1667 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1668 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1669 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1670 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1671 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1672 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1673 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1674 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1675 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1676 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1677 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1678 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1679 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1680 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1681 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1682 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1683 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1684 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1685 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1686 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1687 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1688 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1689 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1690 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1691 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1692 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1693 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1694 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1695 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1696 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1697 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1698 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1699 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1700 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1701 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1702 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1703 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1704 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1705 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1706 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1707 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1708 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1709 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1710 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1711 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1712 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1713 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1714 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1715 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1716 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1717 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1718 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1719 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1720 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1721 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1722 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1723 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1724 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1725 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1726 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1727 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1728 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1729 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1730 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1731 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1732 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1733 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1734 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1735 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1736 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1737 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1738 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1739 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1740 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1741 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1742 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1743 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1744 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1745 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1746 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1747 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1748 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1749 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1750 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1751 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1752 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1753 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1754 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1755 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1756 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1757 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1758 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1759 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1760 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1761 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1762 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1763 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1764 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1765 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1766 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1767 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1768 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1769 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1770 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1771 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1772 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1773 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1774 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1775 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1776 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1777 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1778 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1779 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1780 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1781 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1782 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1783 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1784 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1785 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1786 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1787 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1788 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1789 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1790 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1791 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1792 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1793 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1794 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1795 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1796 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1797 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1798 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1799 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1800 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1801 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1802 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1803 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1804 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1805 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1806 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1807 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1808 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1809 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1810 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1811 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1812 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1813 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1814 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1815 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1816 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1817 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1818 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1819 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1820 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1821 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1822 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1823 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1824 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1825 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1826 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1827 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1828 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1829 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1830 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1831 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1832 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1833 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1834 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1835 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1836 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1837 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1838 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1839 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1840 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1841 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1842 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1843 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1844 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1845 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1846 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1847 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1848 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1849 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1850 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1851 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1852 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1853 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1854 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1855 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1856 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1857 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1858 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1859 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1860 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1861 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1862 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1863 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1864 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1865 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1866 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1867 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1868 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1869 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1870 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1871 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1872 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1873 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1874 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1875 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1876 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1877 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1878 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1879 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1880 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1881 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1882 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1883 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1884 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1885 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1886 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1887 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1888 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1889 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1890 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1891 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1892 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1893 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1894 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1895 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1896 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1897 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1898 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1899 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1900 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1901 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1902 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1903 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1904 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1905 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1906 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1907 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1908 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1909 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1910 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1911 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1912 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1913 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1914 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1915 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1916 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1917 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1918 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1919 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1920 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1921 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1922 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1923 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1924 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1925 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1926 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1927 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1928 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1929 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1930 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1931 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1932 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1933 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1934 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1935 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1936 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1937 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1938 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1939 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1940 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1941 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1942 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1943 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1944 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1945 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1946 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1947 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1948 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1949 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1950 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1951 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1952 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1953 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1954 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1955 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1956 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1957 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1958 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1959 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1960 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1961 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1962 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1963 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1964 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1965 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1966 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1967 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1968 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1969 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1970 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1971 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1972 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1973 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1974 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1975 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1976 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1977 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1978 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1979 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1980 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1981 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1982 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1983 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1984 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1985 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1986 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1987 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1988 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1989 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1990 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1991 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1992 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1993 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1994 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1995 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1996 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1997 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1998 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n1999 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2000 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2001 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2002 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2003 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2004 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2005 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2006 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2007 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2008 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2009 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2010 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2011 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2012 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2013 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2014 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2015 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2016 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2017 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2018 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2019 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2020 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2021 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2022 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2023 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2024 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2025 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2026 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2027 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2028 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2029 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2030 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2031 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2032 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2033 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2034 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2035 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2036 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2037 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2038 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2039 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2040 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2041 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2042 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2043 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2044 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2045 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2046 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| n2047 | calibration | 대기 | 0/5 | 0 | mean W / c000 | — |  — |
| b00 | oof_generation | 완료 | — | 8 |  | — | 기존 c206 설정 재사용; 보정 학습용 시간 순서 OOF 생성 [기록](../../analysis_outputs/research_22h_20261107/bases/b00/result.json) |
| b01 | oof_generation | 완료 | — | 8 |  | — | 기존 c003 설정 재사용; 보정 학습용 시간 순서 OOF 생성 [기록](../../analysis_outputs/research_22h_20261107/bases/b01/result.json) |
| b02 | oof_generation | 완료 | — | 8 |  | — | 기존 c158 설정 재사용; 보정 학습용 시간 순서 OOF 생성 [기록](../../analysis_outputs/research_22h_20261107/bases/b02/result.json) |
| b03 | oof_generation | 완료 | — | 8 |  | — | 기존 c174 설정 재사용; 보정 학습용 시간 순서 OOF 생성 [기록](../../analysis_outputs/research_22h_20261107/bases/b03/result.json) |
| b04 | oof_generation | 완료 | — | 8 |  | — | 기존 c093 설정 재사용; 보정 학습용 시간 순서 OOF 생성 [기록](../../analysis_outputs/research_22h_20261107/bases/b04/result.json) |
| b05 | oof_generation | 완료 | — | 8 |  | — | 기존 c185 설정 재사용; 보정 학습용 시간 순서 OOF 생성 [기록](../../analysis_outputs/research_22h_20261107/bases/b05/result.json) |
| b06 | oof_generation | 대기 | — | 0 |  | — | 기존 c117 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b07 | oof_generation | 대기 | — | 0 |  | — | 기존 c000 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b08 | oof_generation | 대기 | — | 0 |  | — | 기존 c186 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b09 | oof_generation | 대기 | — | 0 |  | — | 기존 c030 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b10 | oof_generation | 대기 | — | 0 |  | — | 기존 c142 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b11 | oof_generation | 대기 | — | 0 |  | — | 기존 c046 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b12 | oof_generation | 대기 | — | 0 |  | — | 기존 c081 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b13 | oof_generation | 대기 | — | 0 |  | — | 기존 c010 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b14 | oof_generation | 대기 | — | 0 |  | — | 기존 c191 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b15 | oof_generation | 대기 | — | 0 |  | — | 기존 c170 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b16 | oof_generation | 대기 | — | 0 |  | — | 기존 c128 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b17 | oof_generation | 대기 | — | 0 |  | — | 기존 c115 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b18 | oof_generation | 대기 | — | 0 |  | — | 기존 c038 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b19 | oof_generation | 대기 | — | 0 |  | — | 기존 c226 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b20 | oof_generation | 대기 | — | 0 |  | — | 기존 c014 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b21 | oof_generation | 대기 | — | 0 |  | — | 기존 c232 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b22 | oof_generation | 대기 | — | 0 |  | — | 기존 c136 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b23 | oof_generation | 대기 | — | 0 |  | — | 기존 c098 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b24 | oof_generation | 대기 | — | 0 |  | — | 기존 c223 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b25 | oof_generation | 대기 | — | 0 |  | — | 기존 c238 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b26 | oof_generation | 대기 | — | 0 |  | — | 기존 c127 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b27 | oof_generation | 대기 | — | 0 |  | — | 기존 c064 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b28 | oof_generation | 대기 | — | 0 |  | — | 기존 c183 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b29 | oof_generation | 대기 | — | 0 |  | — | 기존 c095 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b30 | oof_generation | 대기 | — | 0 |  | — | 기존 c215 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b31 | oof_generation | 대기 | — | 0 |  | — | 기존 c151 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
