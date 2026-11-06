# R5 — 갭 보완 조사 (COMPLETENESS CRITIC)

작성일: 2026-10-26. 입력: `lens1_official_rules.md`(R1), `lens2_past_winners_competitor_intel.md`(R2), `LENS3_methods_state_of_the_art.md`(R3), `lens4_korean_market_context.md`(R4) — 모두 `C:\Users\User\Downloads\OIBC_2026_DATA\research\`.
이번 조사에서 새로 연 1차 자료: dataen.ai 공지·FAQ·2026 규정 탭(브라우저 라이브 열람), GitHub API 저장소 검색(OIBC 전 연도), **2025 대상팀 '재시도'의 노트북 + 발표자료 22장**, **2023 대상팀 '김최신이' 노트북**, 2024 상위 7팀 공지, KPX 규칙 개정이력 PDF(부록2), 전기신문 2025-02-25 기사, 확률예측 집계 논문 2편.

표기: **[A]** 공식/1차 자료 직접 확인, **[B]** 보도·공고 전재, **[C]** 참가자 자가보고(저장소·발표자료), **[미확인]** 확인 실패.

---

## 0. 갭 진단 → 보완 결과 한눈에

| # | R1~R4가 비워 둔 것 | 이번 결과 | 등급 |
|---|---|---|---|
| 1 | 동점 처리 규정 | **여전히 어디에도 없음.** dataen 공지 16건·FAQ 5건·2026 규정 탭·참가자 저장소 6곳·보도 전부 무언급. 10/26 현재 공개 경로로는 확인 불가 → §1.4 문의 문안 | 미확인(확정) |
| 2 | 리더보드 범위(public/private) | 공식 문구는 "리더보드에는 S(원)가 표시" 뿐. 분할 언급 없음. 2024 선례는 "대회 기간 누적 → 상위 7팀 순위별 공지" | 미확인 |
| 3 | 무효 제출 조건 정본 | 공식 목록 없음. 제3자 starter 미러에도 `문제정의서`·`scoring.py` 없음 → 원래 배포 목록에 없었음 재확인 | A(부재 확인) |
| 4 | 2026 발표 배점 | 미공개 그대로. 2024 선례: 상위 7팀 발표 3시간(09:30~12:30) | 미확인 / A(선례) |
| 5 | 10/06 이후 신규 공지 | **없음**(10/26 라이브). 설명회 자료·형식 검증 도구 공지 없음 | A |
| 6 | 외부 사전학습 모델 | 규정 탭 원문: "외부 데이터 사용은 금지하며, **이에 따라** 외부 데이터로 학습된 모델은 사용할 수 없습니다" — 인과 문장. 2024 FAQ 답변도 "별도 데이터 사용 불가능" | A |
| 7 | KPX 정산단가 개정(4%/6%) 근거 | 전기신문 2025-02-25 원문 확보 + KPX 공식 개정공고(2025.2.12 시행 패키지에 "예측제도 정산기준 변경" 포함) + 개정이력 PDF 연표 | A/B |
| 8 | 업계 오차율 벤치마크 | KPX 평균 8.3%→5.7%(2021 도입 후), 해줌 2.6%(2025 이행능력시험), 2024 5% 이내 | B |
| 9 | 2025 대상 '재시도' 방법 | **노트북·슬라이드 22장 전량 열람.** ML 아님: 이상치 정제 + K-NN 커널 회귀(IDW) + 시간 평활 + LOGO-CV | C(1차) |
| 10 | 2023 대상 '김최신이' 방법 | 저장소·노트북 확인: 5종 예측을 피처로 쓴 단일 XGBoost(무작위 80/20 분할, ×1.03 스케일) | C(1차) |
| 11 | 2024(6회) 결과 | 상위 7팀 순위·발표 일정 공지 확보, 시상 구조(17팀), 참가팀 방법 3건. **대상팀 기사는 미발견** | A/C |
| 12 | 2026 경쟁자 저장소 전수 | GitHub API 검색: 기존 4 + 2(ksmini0928-blip, lce2005) = 6곳. 블로그 후기 0건 | A |
| 13 | SOTA: 발전소 분위수→집합 중앙값 | Q-sum/독립/코퓰라 비교 수치(2502.07010) + 2026 후속 CoCopula(2602.02583) | A(초록·본문) |

---

## 1. 공식 규칙 — 2026-10-26 라이브 재확인 [A]

### 1.1 dataen.ai/notice (전 16건)
- 2026 OIBC 관련은 R1이 정리한 3건뿐: 10/02 휴학생, 10/02 참가자격 검증, 10/06 문의 창구. **10/06 이후 신규 공지 없음.**
- 나머지 13건은 2024 대회 운영 공지: `경진대회 발표평가 안내`(11/18), `API 잔여 횟수 조회·전력시장 현황 데이터 호출 불가`(11/13), `데이터 호출 시 누락 건`(11/12), `일일 API 호출 횟수제한`(11/11), `기상 관측소 2의 중복 제주 명칭`(11/08), `[필독] API 가격 데이터 조회 불가`(11/05), `[필독] 예측 입력 미수행 처리`(11/05) 등. → **2024에는 대회 기간 중 거의 매일 운영 공지로 규칙이 보완됐다.** 2026도 11/2 이후 공지 탭을 매일 확인해야 한다.

### 1.2 FAQ 탭 (답변 열람 성공)
- 항목: `연구 주제 1 제출 시 주의해야할 점`, `[2024 OIBC] 온라인 설명회에 실시간으로 참여하지 않아도…`, `[2024 OIBC] 졸업생은…`, `[2024 OIBC] 제공 데이터 외에 별도의 데이터를 사용해도 되나요?`, `[2024 OIBC] DataEn 연구자 등록을 해야하나요?`
- 외부 데이터 항목 답변 원문: **"제공 데이터 외에 별도의 데이터를 사용하는 것은 불가능합니다"** (2024 기준, 2026 항목 없음).

### 1.3 dataen.ai/challenge/2026 "대회 규정" 탭 원문 (10/26)
> 평가 기준 — 정산금 S (매전수익 − 예측 오차 페널티). 정산금 S를 최대화하는 것이 목표이며, 실질적으로는 오차에 비례한 페널티(W)를 최소화하는 경쟁입니다. **순위는 정산금 S 내림차순이며, 리더보드에는 S(원)가 표시됩니다.**
> 코드 및 발표자료 제출 안내 — 제출 대상: 대회기간 종료 후 리더보드 기준 상위 7개팀 (필수 제출) / 제출물: 코드(.py, .ipynb, .R, .rmd), 발표자료(.pdf, .pptx) / 제출 코드는 데이터 전처리부터 학습, 추론까지 전체 과정이 포함 / 제출 기한: 2026.11.23(월) / 제출처: competition@dershare.xyz
> 유의사항 — … 계정 중복 및 팀 간 담합은 금지되며, 제출 결과의 유사도가 기준을 초과할 경우 소명을 요구하고 실패 시 실격 처리됩니다. / 평가 구간의 기상 실측·발전 실적 등 예측시점(대상일 전일 17시 KST) 이후 생성된 정보는 사용할 수 없습니다. / **경진대회에서 제공한 데이터 이외의 외부 데이터 사용은 금지하며, 이에 따라 외부 데이터로 학습된 모델은 사용할 수 없습니다.** / 사용 가능 언어: Python, R / 1일 최대 제출 횟수: 일 3회, 대회 기간 총 20회

- R1의 인용과 일치. 동점·무효·분할·배점 문구는 없다.
- "제공 데이터" 탭도 R1 §1.7과 동일(264행 0.0247% 결손, 우측닫힘, 10/17시 라운드 자유, 익명화, 253개소 전부, 최초 1회 다운로드).

### 1.4 그래도 남는 공백 → 1:1 문의 권장 문안
1. "리더보드 점수는 평가구간 8,760시간 전체에 대한 S 단일 값인가, 일부 구간을 숨긴 public/private 분할인가?"
2. "S가 동일할 때의 순위 결정 기준(제출 시각 선착? W? 절대오차 합?)과, 제출이 '무효' 처리되는 조건의 정본 목록(행 수·tz·음수·NaN·용량 하한·중복 site)을 알려 달라. 무효 제출도 20회에서 차감되는가?"
3. "상위 7팀 최종 순위 산정에서 리더보드 S와 발표 평가의 배점 비율은? (역대 50/30/20이 유지되는가)"
- 실무적으로 동점은 S가 원 단위 소수까지 계산되므로 거의 발생하지 않는다. 우선순위는 1 > 3 > 2.

### 1.5 2024(6회) 선례로 추정 가능한 2026 운영 방식 [A/C]
- dataen 공지 2024.11.18 「경진대회 발표평가 안내」 원문: "상위 7팀의 발표평가… (순위별) 1위 스탑앤웨이트 / 2위 천마군림보 / 3위 분석푸앙 / 4위 브레멘 / 5위 정승환 / 6위 GEO / 7위 알파코 — 일시 2024.11.21(목) 09:30 ~ 12:30". 즉 **리더보드 순위를 공개한 채 7팀을 3시간(팀당 약 25분)에 발표**시켰다.
- 2024 참가 저장소 2곳(myoungse, kimjin1022) README: "200여 팀 중 14위, 참가상(상금 20만원)", "200여 팀 중 17위, 참가상 20만원", "상위 17팀 시상, 10~17위 참가상". → **8~17위 상은 발표 없이 리더보드 순위로 확정**된 것으로 보인다(2026 장려상 10팀 구조와 동일). 설명회 "장려상까지 코드 제출 요구 가능"은 검증용으로 해석.
- 2024 대회 기간은 공지상 11.11~11.18(기사 11.11~11.15). 참가상 2024는 20만원(2026 장려상 40만원).

### 1.6 문제정의서·scoring.py 부재 재확인
- 제3자 저장소 `ksmini0928-blip/OIBC2026`의 `oibc2026/OIBC2026_starter/`: `README.md`(9,791B, 공식 README와 동일 문구 — "식과 동점 처리, 제출 횟수는 문제정의서에 있습니다" 등 3문장 그대로), `baseline.py`(7,923B), `prepare_data.py`, `verify_env.py`, `requirements.txt`, `SETUP_WINDOWS_KO.md`, `benchmark_2025.csv`(참가자가 2025 1위 지표 MAE 44.51/NMAPE 3.42/MSE 9979.19/MSLE 0.156/RMSLE 0.395를 적어 둔 메모 파일; 공식 아님). 문제정의서·scoring.py 없음. 웹 검색("OIBC2026-문제정의서", "scoring.py --composition")도 0건.

---

## 2. 미검증 주장 검증

### 2.1 KPX 예측제도 정산기준 개정 (R2·R4가 해줌 블로그에 의존했던 부분)
- **전기신문 2025-02-25(수정 03-11) 김진후 기자 원문 [B]**: "오차율 4% 이하일 경우 kWh당 4원, 4% 초과 6% 이하 범위에선 3원의 정산단가를 적용한다. 현행 기준에선 오차율 6% 이하일 경우 4원, 6~8% 이하 범위에선 3원" / "오는 6월부터 적용할 계획" / "풍력이 포함된 개별·집합·혼합자원의 경우 1년간 시행을 유예" / "오는 5월부로 제주도에선 예측제도를 일몰" / "현재 오차율을 유지할 경우 약 10% 내외의 수익저감이 예상" / **"2021년 제도 도입 후 예측오차율이 평균 8.3%에서 5.7%로 감소"**. 기사엔 '6월 1일'이라는 날짜는 없고 '6월부터'만 있다 → 해줌의 2025-06-01은 블로그 해석.
- **KPX 공식 공고 [A]**: 「전력시장운영규칙(2025.2.12 시행)」 공고(공고 2025.2.11)의 4개 개정안 중 4번째가 "재생에너지 발전량 예측제도 정산기준 변경을 위한 규칙개정(안)" — 규칙개정위 2024.12.20(24-6차), 전기위 2025.1.24(308차), 산업부 승인 2025.2.10. 수치는 hwp 첨부(붙임1 개정내용)에 있어 본 세션에서는 미열람.
- **KPX 개정이력 PDF(부록2, 2025/5 업로드) [A]** 예측제도 연표:
  - 2018.12.12(시행 12.13) 소규모전력중개시장 개설 — 집합전력자원 등록·변경·말소 신설
  - 2020.9.24(시행 10.1) 재생에너지 발전량 예측제도 도입 — "발전사업자가 발전량을 예측하여 입찰하고 정확도에 따라 정산받는 제도 신설"
  - 2021.9.17(시행 9.18) 보완 — "발전기 기준, 예측오차율 산정방식, 등록시험 기준 및 정산금 산정방식 등 규정 전반 보완"
  - 2022.12.22(시행 12.28) 혼합자원 반영 — "집합전력자원의 등록, 참여기준, 등록시험 중단기준, 예측오차율 산정 등 개정"
  - 2023.6.30(시행 7.1) — "집합전력자원 정의 명확화, 용량감소 발생시 복구기한 변경 및 등록기간 선택권"
  - 2023.12.29(시행 12.30) — 등록시험 신청일정 일원화(시험월 1일 5영업일 전)
  - 2024.1.31(시행 2.14) — 제주 시범사업 규칙에 "예측제도 경과조치 마련"
- 결론: 4%/6% 개정은 실재(공식 개정 패키지 확인)하고 시행은 2025년 6월(태양광)·2026년 6월(풍력 포함)이 보도 기준. 대회 평가 첫날과 같은 달이라는 R4의 관찰은 유지하되 "6월 1일"은 [B].

### 2.2 집합자원 하루전 오차 벤치마크 (발표용 맥락, 대회 지표와 직접 비교 불가)
- KPX 전체: 도입 후 평균 8.3% → 5.7% [B, 전기신문].
- 해줌: 2025년 1차 이행능력시험(제주 입찰제도 급전가능재생에너지) 평균 오차율 **2.6%**, 허용 기준 12%→8% 강화, 2024년 평균 5% 이내 [B, 해줌 blog 2025-02-20]; 2024.10~2025.3 6개월 연속 혼합자원 부문 최소 오차율(자사 분석, KPX 공시 대조 주장) [B].
- 주의: 제도 오차율 = |예측−실적|/설비용량, 이용률 10% 미만 제외. 대회는 kWh 절대오차 × SMP × k. 그래도 "잘하는 집합자원은 설비용량 대비 3~6%"가 현업 감각이고, ruby9915의 "팀 합계 오차 11.9%"는 분모가 실적(발전량 합)이라 더 크게 보인다.

### 2.3 그 외
- 제공사 A=OpenWeatherMap, B=AccuWeather: 추가 근거 없음(여전히 스키마 추론).
- 설명회 "81~82%" 발언: 녹취 외 자료 없음, 검증 불가. 로컬 데이터로 기준선 페널티 분해를 직접 계산하는 것이 유일한 확인 방법(분석 에이전트 과제).
- 2024 대회 "음의 가격 구간 임의 상수 → 수상 제외" 공지는 competition.postech.ac.kr(DNS 소멸)·Wayback(차단) 모두 열람 불가. 검색 스니펫으로만 확인 [B].

---

## 3. 경쟁자·역대 수상팀 인텔 (신규)

### 3.1 2026 참가자 공개 저장소 전수 (GitHub API `q=OIBC`, `q=POSTECH OIBC`, 10/26)
| 저장소 | 최근 push | 내용 |
|---|---|---|
| ruby9915/OIBC | 10-19 | R1·R2 상세. 유일하게 수치가 있는 실험 로그 |
| Max-JI64/OIBC-2026-DATA_TADA | 10-25 | R2 §3.3 |
| KTHYEONG/oibc-2026 | 10-20 | 운영 매뉴얼만 |
| kwonjh0721-pixel/kwonjh0721 | — | 파이프라인 README |
| **ksmini0928-blip/OIBC2026** | 10-14 | starter 미러(§1.6). 모델 없음 |
| **lce2005/2026_OIBC** | 10-24 | LICENSE만 |
- velog/tistory/네이버 블로그 후기: **0건**(한국어 확장 검색 3회). 공개 인텔의 상한은 ruby9915이며, 260여 팀 대부분은 비공개.
- 2025 대회 저장소 중 2025-11 이후에도 갱신된 것(= 2026 참가 가능성 있는 숙련자): `JinseokChun/OIBC_Retry`(12-13), `DohyunBu/OIBC_ReTry`(11-29), `fosemfhtm/2025_oibc_team_chidies`(12-05), `junyoungking/OIBC_2025`(12-11), `qewr1234/POSTECH-OIBC-Solar`(2026-09-06), `NKyeong/2025_OIBC`(2026-06-14), `JunseoPark543/OIBC`(2026-05-08), `kimjin1022/2024_POSTECH_OIBC_CHALLENGE`(2025-11-01).

### 3.2 2025(7회) 대상 '재시도' — 실제 방법 (1차 자료) [C]
출처: `github.com/JinseokChun/OIBC_Retry`(README, `재시도팀_2025_OIBC_코드.ipynb` 20KB, 발표자료 22장 jpg) 및 미러 `github.com/DohyunBu/OIBC_ReTry`. 슬라이드 사본: `C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-OIBC-2026-DATA\dfcedbe5-607d-48a7-8c29-05284fe8d563\scratchpad\dl\retry_slides\p01.jpg ~ p22.jpg`.
- **팀 구성 단서**: DohyunBu(부도현)는 2023 성균관대 仁義禮智信(우수상 2위/120) 멤버로도 저장소를 갖고 있다 → 2023 "적응형 가중 앙상블"로 2위 → 2025 "단순 커널 회귀"로 대상. (GitHub 계정 기준 추정)
- **최종 리더보드(발표자료 18p 캡처)**: 1 재시도 MAE 44.51 / NMAPE 3.42 / MSE 9979 / MSLE 0.156 / RMSLE 0.395 · 2 CHIDIES 44.93 / 3.46 · 3 RTTechnica 45.18 / 3.48 · 4 쿼드알파 45.53 / 3.5 · 5 Snowflake 45.53 / 3.5 · 6 신nano흥nano 45.59 / 3.51 · 7 QKV 45.79 / 3.52. 문구: "대회 시작부터 끝까지 모든 평가 지표에서 1위 유지". **1~7위 MAE 격차 1.28 W/m²(2.9%)** — 상위권은 박빙.
- **방법(노트북 원문 기준, ML 모델 없음)**:
  1. 선형보간 이상치 검출: 발전소별 nins 1·2차 차분으로 "직선 구간"(`rtol=1e-7, atol=1e-9`, 최소 길이 `min_run=10`, 0 평탄 구간 제외) 탐지 → NaN 처리. 출력 "총 보간 의심 구간 수: 626 / 고유 발전소 수: 58". 발표에서는 OLS 잔차 MSE<ε 의사코드(Algorithm 1)로 제시.
  2. K-최근접 이웃 Nadaraya–Watson 커널 회귀: 같은 시각의 인접 발전소 nins를 유클리드 좌표 거리로 가중 `w=1/(d^p+ε)`, **k=55, p=2, ε=1e-8**, 블랙리스트 3개소(`PV_ID_49, 39, 28`) 제외. 탐욕적 순서: 학습 풀에 가장 가까운 테스트 발전소부터 채우고 **예측값을 풀에 추가**해 다음 발전소에 재사용.
  3. 양측 시간 평활: 가중 (1,3,6,7,6,3,1)/27 (코드는 3점 이동평균 3회 = 동일 커널).
  4. 물리 제약: 최소 0, 센서 상한 1,300 W/m².
  - 검증: **공간 좌표 단위 교차검증(LOGO-CV)** — 같은 시각 같은 좌표의 다른 발전소를 블라인드. 검증 MAE **39** → 대회 44.51.
- **발표 서사(22장 구조)**: 목차(문제 정의 → 데이터 분석 → 시스템 모델링 → 방법론 → 결과 및 분석 → 결론). 데이터 분석 4장이 핵심: (완결성) 5분 간격 선형보간 이상치 발견, (외생변수 정확성) 1시간 기상 데이터가 발전소 군집별로 **전부 일치** → 관측소 공유, (공간 정확성) 같은 좌표인데 다른 일사량 추이·인접 좌표의 일출시각 차이 → "낮은 해상도의 공간 좌표", (시공간 연관성) 거시(일출·일몰 지도)/미시(같은 시각 일사 지도), (물리 제약) 센서 상한 1,300. 시스템 모델링 1장: 그래프 모델 — 실제 좌표 X·실제 시각 T·실제 일사 Y는 관측 불가, 데이터 좌표 X̂·인근 발전소 일사 Ỹk·인근 기상 W̃는 관측 가능 → 근사모델 **Y ← Ỹk(X̂, T)**. 결론 한 줄: **"시스템의 구조를 읽어, 단순함으로 답하다"**.
- **2위 CHIDIES**(`fosemfhtm/2025_oibc_team_chidies`, 김수민): `0_baseline`(LightGBM) → `1` 보간 → `2` 물리 기반 감쇠(attenuation) → `3` 최근접 이웃 → `4` 로컬 IDW → `5` 추세 예측 + 회귀 IDW → `6` 최종 앙상블. 발표 PDF「태양광 발전량 추정 전략_TEAM CHIDIES.pdf」. 즉 2위도 IDW 계열 + 물리 모델.
- **7위권 추정 `qewr1234/POSTECH-OIBC-Solar`**(대회 MAE 45.77, 7위 QKV 45.79보다 근소 우위): LightGBM Tweedie(1.05) 20,000 trees·lr 0.03·511 leaves·3 seeds, KMeans 10 위치 군집, Haurwitz 청천 GHI·에어매스·태양기하 피처, `pv_id` GroupSplit(146/37). **홀드아웃 34.05 → 대회 45.77 (낙관 11.7)**. 트리 모델은 LOGO/그룹 분할을 해도 공간 일반화에서 커널 회귀에 졌다.
- **2026 번역** (평가기간 인접 실측이 없어 K-NN 자체는 불가):
  - (a) 2026 데이터도 `wa_point/wb_point`를 발전소들이 공유 → 같은 지점을 쓰는 발전소 간 **예보 오차가 공통**이고 잔차 상관이 높다. 이 구조를 쌍둥이 분할(지점 단위 층화)과 집합 수준 보정에 쓰고, 발표에서 "같은 지점 공유 = 동일 예보" 플롯으로 보여 주면 2025 심사평("인접 발전소 활용")과 연결된다.
  - (b) 학습 발전량의 보간·센티널·클리핑 이상치 검출을 **의사코드 + 사례 플롯**으로 제시(2025 대상의 9p 형식). 설명회도 "이상치·결측 처리 방식이 가장 중요한 평가 요소"라고 했다.
  - (c) LOGO-CV 아이디어 → 48개 단기 이력 발전소를 모사한 **plant-held-out 보조 검증**(시간 블록 CV가 주).
  - (d) 결론 한 줄 서사 + 시스템 모델링(그래프) 1장. 7팀×25분이므로 슬라이드 20장 내외.

### 3.3 2023(5회) 대상 '김최신이'(경북대) — 방법 확인 [C]
출처: `github.com/hjinshin/OIBC_2023` (README, `notebooks/PreProcessing.ipynb`, `notebooks/StackingRegression.ipynb`, `2023_OIBC_KCSL.pptx`). 팀: 김시형·최지원·이한빈(수학과)·신형진(컴퓨터학부). "1위/73팀".
- README 설명: "XGBoost 기반 Stacking Regression + 데이터 동화(data assimilation)".
- 노트북 실제: 5종 모델 예측(`model1~5`)과 기상예보, `cos/sin(hour)`, month/day/hour를 피처로 한 **단일 XGBRegressor** (`reg:squarederror, n_estimators=8000, lr=0.01, max_depth=6, colsample_bytree=0.8, alpha=24`) — 메타러너 OOF 스태킹이 아니라 "예측값을 피처로 넣은 회귀". 라운드별 별도 모델(round2: 7000 trees). `vis, humidity, azimuth, elevation, dew_point, model5, model4` 제거 → 16 피처. **검증은 무작위 80/20 `train_test_split`**(시간순 아님). 예측에 스케일 **w=1.03** 곱, 1 kWh 미만 0 클립. 검증 인센티브 round1 89,221 / round2 84,808 (완전예측 151,231 → 59%/56%). "데이터 동화" 코드는 노트북 가시 영역(처음 20만 자)에서 확인 못 함 — 손으로 넣은 `day27…day5` 시간별 리스트가 있어 대회 중 수동 보정으로 추정 [미확인].
- 시사점: 2023 대상도 모델은 평범했다. 공고가 "5종 단순 평균 앙상블은 감점"이라 했고, 이 팀은 "학습된 비선형 결합"으로 창의성 요건을 충족 + 리더보드 1위. **2026에서 '참조 배정 그대로 + 10/17시 단순 평균'은 같은 이유로 감점 리스크.**
- 2023 2위 성균관대 仁義禮智信(`lhk6565/2023_POSTECH_OIBC`, 우수상): 적응형 가중 ŵ=f(x_F, x), 손실 L_quan = I_max − I_present, L_qual = |ŵ·x − y|^α (0<α<1), 지표 S=(1−ΣI_present/ΣI_max)×100%, PyTorch. 회고: "가중치를 해석해 새 통찰을 못 냈다". 2023 규칙(README): 10시·17시 예측 평균 vs 실제, 오차율=|평균−실제|/C×100, ≤6% 4원 / 6~8% 3원, 이용률<10% 제외, 미제출 시 0 kWh 간주.

### 3.4 2024(6회) 제주 하루전 SMP 예측 — 결과 공지 확보
- 상위 7팀(dataen 2024.11.18, 순위별): 스탑앤웨이트, 천마군림보, 분석푸앙, 브레멘, 정승환, GEO, 알파코. 발표평가 2024.11.21(목) 09:30~12:30. **대상 확정 기사·수상팀 방법 자료는 미발견**(팀명 검색 0건).
- 규모·시상: 약 200팀, 상위 17팀 시상, 10~17위 참가상 20만원 [C, 참가자 README 2곳].
- 참가팀 방법(모두 비수상권): kimjin1022(XGBoost, lag 1~3일 SMP, 시간별 롤링 통계, 주말 더미, LSTM은 데이터 부족으로 열세, **17위**), myoungse(RandomForest + SVR 잔차 보정, Optuna, 시간 분할 검증, **14위**), bluelemon61/24-OIBC-WolgoksTears(**대회 산식 그대로의 손실 + α×Zero Penalty**, API 제출 훅). 2024는 "음수 가격 구간 상수 입력 시 수상 제외" 공지가 있었던 해 — 지표 꼼수에 대한 주최 측 민감도 근거.

### 3.5 2022·2021·2020 저장소(참고)
- `HiddenBeginner/2022_oibc_competition`(2022 대상 Sun capturer, R2 §1.1), `lhk6565/2022_POSTECH_OIBC`(Duck Curve 팀), `Min-su-Jeong/2021_POSTECH_OIBC_CHALLENGE`(2021 수상), `Min-su-Jeong/2020_POSTECH_OIBC_CHALLENGE`(2020 수상), `DveloperY0115/POSTECH-OIBC-SolarChallenge`(2020). 이번 세션에서는 열람하지 않음.

---

## 4. SOTA 보완 — 발전소 분위수 → 집합 중앙값

- **Moradi, Tanneau, Zandehshahvar, Van Hentenryck (2025), arXiv 2502.07010, IISE Annual Conf. 2025 pp.1920–1925 [A, 본문]**: NREL ARPA-E PERFORM, **MISO 751개 사이트**, 사이트별 99 분위 하루전(리드 11h, 시간별) 예측을 플릿으로 집계. 비교: Q-sum(분위수 단순 합), Indep(독립 샘플 합), Gaussian copula(학습 실적을 주변 CDF→정규점수→상관행렬, 샘플링 후 합).

  | 명목 커버리지 | 방법 | PICP(%) | AIW |
  |---|---|---|---|
  | 90% | Indep | 13.7 | 874 |
  | 90% | Q-sum | 97.2 | 14,727 |
  | 90% | Copula | 78.2 | 7,437 |
  | 60% | Indep | 7.3 | 440 |
  | 60% | Q-sum | 80.2 | 7,404 |
  | 60% | Copula | 50.4 | 3,849 |

  Q-sum은 구간이 코퓰라의 약 2배로 과대, Indep은 약 1/10로 과소. 집계 품질은 주변분포 보정도에 좌우(일출·일몰 전후 과소 커버).
- **CoCopula (2026-01-31, v2 2026-10-15), arXiv 2602.02583 [A, 초록]**: 코퓰라 집계 + Context-Aware Conformal Prediction으로 집계 후 미보정 교정, MISO/ERCOT/SPP, Winkler 점수 개선, 시스템 수준 직접 보정 모델과 동급.
- **2026 대회 적용**: 점예측(가중 중앙값)만 내면 되므로 (i) 발전소별 분위수 모델 → (ii) 학습구간 OOF 잔차로 가우시안 코퓰라(지점 공유 구조가 상관을 설명) → (iii) 집합 시나리오 → (iv) 시각별 가중 중앙값. **분위수 합(Q-sum, 코모노톤 가정)이나 독립 가정으로 집합 분포를 만들지 말 것.** R3 §3의 "집합 수준 2단계 L1 보정"과 OOF에서 비교 ablation.
- 국내 선행연구: 한혜승·김아현·강동주, 「발전량 예측오차 최소화를 위한 집합자원 포트폴리오 최적화: 태양광을 중심으로」, 대한전기학회 하계학술대회 2021, pp.495–496 (초록 일부만 열람, 수치 미확인) + 경희대 JIIS 2023(R2 §4.3). 발표 시 "국내 선행연구 2건은 제도 오차율(임계값) 기준, 본 대회는 선형 절대오차 → 쌍둥이 분할"로 차별화.

---

## 5. 남은 공백 (이번에도 못 메운 것)
1. 동점 처리·무효 조건·public/private·발표 배점 — **공개 경로에 없음**. §1.4 문의 외 방법 없음.
2. 2024(6회) 대상팀과 방법 — 공지는 상위 7팀 순위까지만.
3. 2023 대상의 "데이터 동화" 구체 구현 — pptx 미열람(`2023_OIBC_KCSL.pptx` 다운로드·텍스트 추출하면 확인 가능).
4. 제공사 A/B 신원 — 추가 근거 없음.
5. KPX 개정 조문 수치의 1차 원문(hwp) — 미열람. 보도 2건 + 공식 공고 제목으로 간접 확인.
6. 설명회 녹취 수치(81~82%) — 로컬 재계산으로만 검증 가능.

---

## Sources
**공식 (dataen / KPX)**
- https://dataen.ai/notice (공지 16건, 2026-10-26 열람)
- https://dataen.ai/notice?tab=faq (FAQ 5건, 외부 데이터 답변 열람)
- https://dataen.ai/notice/c3c1f3ca-0ae5-4d00-aa3c-ce1fdd699d45 (2024.11.18 경진대회 발표평가 안내: 상위 7팀 순위·일정)
- https://dataen.ai/challenge/2026 (대회 규정 탭·제공 데이터 탭 원문, 2026-10-26)
- https://dataen.ai/challenge/history (역대 1~7회 목록)
- https://www.kpx.or.kr/board.es?mid=a11002010000&bid=0030&act=view&list_no=74304&tag=&nPage=1 (전력시장운영규칙 2025.2.12 시행 개정 공고 — 예측제도 정산기준 변경 포함)
- https://marketrule.kpx.or.kr/lmxdata/attach/2025/5/upload_5127126665285383397_p749.pdf (전력시장운영규칙 개정이력 부록2; 예측제도 연표)
- https://marketrule.kpx.or.kr/lmxsrv/law/joHistoryContent.do?SEQ=2&SEQ_CONTENTS=21489&DATE_START=20210501&DATE_END=20231230 (제14.1.1조 용어 정의)

**보도 / 업계**
- https://www.electimes.com/news/articleView.html?idxno=350873 (전기신문 2025-02-25: 4%/6%, 8.3%→5.7%, 6월 적용, 풍력 유예, 제주 일몰)
- https://blog.haezoom.com/news_03/ (해줌 2025-02-20: 이행능력시험 평균 오차 2.6%, 허용 12%→8%, 2024 5% 이내)
- https://blog.haezoom.com/notice_05/ , https://blog.haezoom.com/insight_vpp_19/ (해줌 해설)
- https://www.energydaily.co.kr/news/articleView.html?idxno=158656 , https://www.ezyeconomy.com/news/articleView.html?idxno=218806 (해줌 6개월 연속 최소 오차율)
- https://www.industrynews.co.kr/news/articleView.html?idxno=56693 (2024-11-07, 제6회 제주 전기가격 예측 대회 개요)
- https://m.news.nate.com/view/20251223n24813 (2025 결과 보도, 프라임경제)
- https://www.devtimes.co.kr/news/435023 , https://www.kyongbuk.co.kr/news/articleView.html?idxno=4056124 (2025 대회)
- https://www.industrynews.co.kr/news/articleView.html?idxno=51733 , https://www.ikld.kr/news/articleView.html?idxno=285654 (2023 시상)

**참가자·수상팀 저장소 (GitHub)**
- 2026: https://github.com/ruby9915/OIBC , https://github.com/Max-JI64/OIBC-2026-DATA_TADA , https://github.com/KTHYEONG/oibc-2026 , https://github.com/kwonjh0721-pixel/kwonjh0721 , https://github.com/ksmini0928-blip/OIBC2026 (starter 미러; raw README·benchmark_2025.csv) , https://github.com/lce2005/2026_OIBC
- 2025 대상 재시도: https://github.com/JinseokChun/OIBC_Retry (README, 재시도팀_2025_OIBC_코드.ipynb, 발표자료 22장) , https://github.com/DohyunBu/OIBC_ReTry
- 2025 기타: https://github.com/fosemfhtm/2025_oibc_team_chidies (2위 CHIDIES) , https://github.com/qewr1234/POSTECH-OIBC-Solar (MAE 45.77) , https://github.com/junyoungking/OIBC_2025 , https://github.com/NKyeong/2025_OIBC , https://github.com/JunseoPark543/OIBC , https://github.com/junseo5777/nins_prediction_obic
- 2024: https://github.com/kimjin1022/2024_POSTECH_OIBC_CHALLENGE (17위) , https://github.com/myoungse/2024_POSTECH_OIBC_CHALLENGE (14위) , https://github.com/bluelemon61/24-OIBC-WolgoksTears , https://github.com/eonjong0218/2024_POSTECH_OIBC_CHALLENGE- , https://github.com/lky473736/OIBC , https://github.com/LeeDuho/2024_POSTECH_OIBC
- 2023: https://github.com/hjinshin/OIBC_2023 (대상 김최신이; notebooks/StackingRegression.ipynb) , https://github.com/lhk6565/2023_POSTECH_OIBC (2위 仁義禮智信) , https://github.com/DohyunBu/OIBC_INUIYEJISIN , https://github.com/swanseacity/OIBC_IEYJS , https://github.com/Glanceyes/2023-POSTECH-OIBC-Challenge , https://github.com/sakamii/2023_POSTECH_PV , https://github.com/ColdTbrew/Solar-Power-Prediction-Competition , https://github.com/kktbr/2023_POSTECH_OIBC
- 2022 이전: https://github.com/HiddenBeginner/2022_oibc_competition , https://github.com/lhk6565/2022_POSTECH_OIBC , https://github.com/Min-su-Jeong/2021_POSTECH_OIBC_CHALLENGE , https://github.com/Min-su-Jeong/2020_POSTECH_OIBC_CHALLENGE
- GitHub 검색 API: https://api.github.com/search/repositories?q=OIBC+in:name,description,readme&sort=updated&per_page=50 , https://api.github.com/search/repositories?q=POSTECH+OIBC+in:name,description,readme&sort=updated&per_page=50

**학술**
- https://arxiv.org/abs/2502.07010 , https://arxiv.org/html/2502.07010v1 (Probabilistic Forecast Aggregation: Q-sum / Indep / Copula 비교)
- https://arxiv.org/abs/2602.02583 (CoCopula, 2026)
- https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE10609786 (한혜승 외 2021, 집합자원 포트폴리오 최적화)

**접근 실패**
- https://competition.postech.ac.kr/ 및 /공지사항/?mod=document&uid=67 (2024 평가 산출 공지) — DNS 소멸; web.archive.org — 도구 차단
