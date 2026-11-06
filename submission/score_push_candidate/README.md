# OIBC 2026 새 제출 후보

전체 연간 검증에서는 개선됐지만 마지막 2025년 3–5월 검증에서는 악화된 **실험 후보**입니다. 실제 리더보드 개선은 아직 확인하지 않았습니다. 기존 최고 제출 파일은 `../autoresearch_candidate/`에 보존했습니다.

제출 파일은 이 폴더의 `composition.csv`와 `forecast.csv`입니다. `submission_files.zip`에는 두 CSV만 들어 있습니다. 상위 `submission/composition.csv`는 다른 구성이므로 섞지 마세요.

| 검증 구간 | 기존 autoresearch 가중 오차율 | 새 후보 가중 오차율 |
|---|---:|---:|
| 2023-06~2024-05 개발 | 12.695950% | 12.041604% |
| 2024-06~2025-02 개발 | 11.639887% | 11.064367% |
| 2024-06~2025-05 전체 | 11.048843% | 10.716156% |
| 2025-03~2025-05 최종 확인 | **9.576119%** | 9.848507% |
| 2025-01~2025-05 | **9.663307%** | 9.746130% |

낮을수록 좋은 내부 지표이며 공식 점수의 백분율이 아닙니다. 개발 구간은 모델 선택에 사용했고, 전체 기간은 개발 구간과 최종 확인 구간을 함께 포함합니다. 과거 연구에서 모든 과거 기간이 노출된 이력이 있습니다.

형식 검사 및 원시 예측 독립 재계산 통과: 발전소 253개, 예측 17,520행, 그룹별 8,760시간, 시간대 Asia/Seoul, 잘못된 입력 9종 거부. 발전소 구성은 사용자가 실제 제출했다고 확인한 `award_candidate`/`autoresearch_candidate`와 바이트 단위로 같습니다.

SHA256:

- `composition.csv`: `68216d1f6b8b6f9c026703e3bfaf7b0470cc8e018580826c866ee0f7357cc141`
- `forecast.csv`: `886461035abd19c80daa021f46e17577642807c7396b528c4c95f27bedfde9a0`
- `submission_files.zip`: `31bf82fa2ec7df7329475ec695153acdc6662b99ba756d4a540cd09d8f1a8a6b`

워크스페이스 루트에서 확인:

```text
python submission/validate_artifacts.py submission/score_push_candidate --self-check
python submission/score_push_verify_final.py
```

모델·동결 설정·실험 근거는 `../../analysis_outputs/score_push_20261104/final/`, 상세 보고서는 `../../analysis_outputs/reports/score_push_성능검증보고서_20261104.md`입니다. 학습 종료일만 바꾼 추가 진단은 별도 `deployment_check/`에 저장하며 이 제출 파일은 수정하지 않습니다.

자동 제출하지 않았습니다. 새 공식 점수와 순위는 대회 채점 이후에만 알 수 있습니다.

2026-11-05 자원 확대 후 GPU 모델 32개를 추가 검증했습니다. 복잡도·학습량·금액 가중치까지 비교했지만 두 개발 구간에서 일관된 개선을 얻지 못해 최종 GPU 혼합은 채택하지 않았습니다. 이 폴더의 CSV·ZIP은 앞서 검증한 CPU 후보 그대로이며, 최신 결과는 위 상세 보고서와 `../../analysis_outputs/score_push_gpu_refine_20261105/independent_check.json`에 있습니다.
