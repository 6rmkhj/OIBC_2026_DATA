# 12시간 연장 및 GitHub 기록 계약

사용자는 기존 종료 시각을 12시간 뒤로 미루고 GitHub에 주기적으로 Codex 작성자로 커밋하도록 승인했다. 새 절대 종료 시각은 **2026-11-07 20:56:33 UTC / 2026-11-08 05:56:33 한국시간**이다. 원래 요청 시작부터 계산한 계획 구간은 22시간이며, 준비·점검 시간도 포함한다. 실제 학습 시작·완료 시각과 계산 시간은 각 실행 영수증으로 별도 집계한다. 22시간 학습을 완료했다는 뜻이 아니다.

## 실행 연결

기존 `research_10h_20261107`의 소스·manifest·산출물은 보존한다. 기존 컨트롤러가 종료 단계에 도달하고 기록된 PID/start identity 및 관련 프로세스 그룹이 모두 종료된 것을 확인한 뒤에만 새 컨트롤러를 시작한다. 기존 작업이 살아 있으면 중복 학습 없이 기다린다. 명시적인 STOP은 자동으로 해제하지 않는다.

- `controller_manifest.json`: 고정된 새 학습 큐와 해시, 종료 시각.
- `continuation_spec.json`: 기존 작업에서 새 작업으로 연결하는 로컬 학습 감독기. GitHub 게시 명령은 포함하지 않는다.
- `supervisor_state/state.json`: 감독기의 실제 PID/start identity와 인계·GitHub 실행 이력.
- `controller_state/state.json`: 새 학습의 실제 단계, 현재 작업, 완료·실패·시간 제한 이력.
- `bases/bNN/`: 기존 모델의 시간 순서 OOF 예측과 생성 영수증.
- `trials/nNNNN/`: 다섯 평가 기간의 보정 결과, 저장 모델 재현 검증과 점수.
- `completion/`: 고정 후보, 추가 시드 점검, 후기 기간 평가와 별도 제출 산출물.

학습은 동시에 하나만 실행하고 CPU 4개, BLAS 1스레드를 사용한다. 새 탐색은 2026-11-07 19:56:33 UTC까지이며, 마지막 한 시간은 후보 검증·최종 재학습·제출 파일 생성에 예약한다. 절대 종료 이후 새 학습은 시작하지 않는다. 보고 전용 마무리와 검증은 별도로 수행한다. 2,048개 보정 설정은 큐 크기이며 시간 안에 모두 완료된다는 보장이 아니다. 완료된 기존 실험을 다시 학습하지 않는다.

감독기만 중단된 경우 같은 spec과 state-dir로 재개한다. 실행 전 STOP 유무와 소스·manifest 해시 및 실제 프로세스 identity를 확인한다. 살아 있는 새 컨트롤러와 worker는 인계받는다.

```bash
/workspace/.venvs/oibc-2026/bin/python /workspace/OIBC_2026_DATA/submission/score_push_22h/continuation.py \
  --spec /workspace/OIBC_2026_DATA/analysis_outputs/research_22h_20261107/continuation_spec.json \
  --state-dir /workspace/OIBC_2026_DATA/analysis_outputs/research_22h_20261107/supervisor_state \
  --detach
```

## 평가와 보존

이전 실험에서 완료된 32개 설정을 고정하고, 해당 모델의 기존 다섯 평가 기간 학습·예측을 재사용한다. 보정 학습에는 생성 모델의 학습 종료 뒤에 발생하면서 각 외부 학습 시점 이전인 실제 OOF 예측만 사용한다. 중복된 대상 날짜의 가중치를 보정한다. 새 기초 모델의 OOF 생성과 해당 64개 보정 설정을 묶어 순차 실행한다.

모든 과거 기간은 이전 작업에서 이미 노출된 자료이며 평가 기간도 겹친다. 시간 순서 OOF를 사용해도 독립적인 미사용 검증 집합이 되지는 않는다. 탐색 정답은 2025-03-01까지로 제한한다. primary에서 선택한 혼합 계수를 recent로 그대로 이전한다. 후보·계수를 고정한 다음에만 2025년 3–5월 정답으로 후기 성능을 평가하며 그 결과로 다시 고르지 않는다.

기존 최고 제출 파일 `submission/renew_candidate_20261105/submission_files.zip`의 SHA256 `ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434`를 보존한다. 새 후보가 검증되면 `submission/research_22h_candidate_20261107/`에 별도 생성한다. 적격 후보가 없거나 시간이 부족하면 미생성·미완료로 보고한다. CHECKPOINT_ONLY는 후보 검증 성공이 아니다. 공식 리더보드 업로드와 유료 구매는 하지 않는다.

## GitHub 기록

계획된 대상은 `https://github.com/6rmkhj/OIBC_2026_DATA`의 `main`이다. 자동 승인 검토가 공개 저장소와 파일 범위에 대한 구체적 승인 부족을 이유로 자동 push 실행을 거절했다. 따라서 실제 게시와 주기 push는 사용자 범위 확인을 기다리며 비활성 상태이다. 현재 감독기는 로컬 학습만 수행한다. 게시 명령을 포함한 원래 제안은 `continuation_spec_publish_proposal.json`에 보존하며 실행하지 않는다.

승인 후 적용할 계획은 약 1시간마다 변경된 코드·고정 설정·완료 실험의 검증 기록을 커밋하고 일반 fast-forward push하는 것이다. 작성자와 커미터는 모두 `Codex <codex@openai.com>`이며 GitHub의 `codex` 계정에 연결되는 이메일임을 확인했다. 변경 내용이 없으면 빈 커밋을 만들지 않는다.

독립 Git index와 로컬 `codex/checkpoints` 브랜치를 사용해 사용자의 작업 브랜치와 staging 영역을 보존한다. 예상치 못한 원격 변경이 있으면 강제 push하지 않고 충돌을 기록한다. 대형 모델·데이터·예측 파일·제출 ZIP·실행 중 상태·로그·자동화 식별자는 게시 대상에서 제외한다. 각 커밋의 파일 목록과 해시를 `analysis_outputs/github_checkpoints_20261107/`의 새 감사 기록으로 남긴다. 대형 모델이 제외되므로 GitHub 기록만으로 학습 산출물 전체를 복원할 수 있는 것은 아니다.

주기 실행은 현재 작업 환경이 유지되는 동안 수행된다. 감독기와 별도로 이 대화의 매시간 점검도 새 종료 시각까지 연장한다. 최종 점검은 실제 결과와 독립 검증, 후보 경로, 개선·악화 기간, 실패·시간 제한을 한국어로 보고하고 자동화를 비활성화한다.
