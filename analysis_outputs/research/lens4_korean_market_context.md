# LENS 4 — 한국 전력시장·기상 맥락 (2026 POSTECH OIBC Challenge)

작성일: 2026-10-26. 대상: 253개 태양광(합계 42,655.4 kW) → G1/G2(각 ≥ 20,000 kW) 집합자원 구성 + 하루전(전일 17:00 KST) 시간별 kWh 예측, 평가기간 2025-06-01 01:00 ~ 2026-06-01 00:00 KST.

> **법적 사용범위 요약 (먼저 읽을 것)**
> - 모델 입력으로 쓸 수 있는 것: 주최측 제공 데이터(제공사 A/B 예보, 학습구간 실측기상·발전량, `smp.csv`의 SMP와 `k`)뿐입니다. 외부 데이터 사용은 금지입니다.
> - 아래 (b)(e)의 KPX·기상청 통계, 2025-06~2026-06 실제 날씨 사건은 **모델에 넣으면 안 되는 외부 정보**입니다. 검증 설계·리스크 이해·발표(상위 7팀 PT) 논리 구성에만 쓰세요.
> - 평가기간 SMP와 k는 `smp.csv`로 이미 제공되므로, 가격 가중치 자체는 "외부"가 아니라 "제공 데이터"입니다. 손실함수 가중치로 쓰는 것은 제공 데이터 활용입니다(문제정의서 원문 확인 권장 — 참가자 폴더에 없었음).

---

## 0. 핵심 요약 (TL;DR)

1. **왜 20,000 kW·두 집합자원인가** — 한국 「재생에너지 발전량 예측제도」(2021-10-01 시행)의 참여 단위가 "설비용량 20MW 초과/이상"의 개별자원 또는 집합전력자원(1MW 이하 소규모 자원을 중개사업자가 모은 가상 발전소)이기 때문입니다. 대회는 "집합자원 2개를 등록한 중개사업자"를 시뮬레이션합니다.
2. **왜 11~15시 k=3인가** — (근거 있는 추론) 육지 출력제어·SMP 0원이 집중되는 시간대(KPX 출력제어 전망 10~15시, 최소수요 13시경; 사업자들은 "11~15시 집중" 주장)이며, 태양광 절대오차(kWh)가 가장 큰 시간대입니다. 테스트 `smp.csv`의 0원 18시간은 **전부 13시 또는 14시**입니다.
3. **예측제도 정산 기준(2025-06-01 태양광 적용)**: 시간대별 예측오차율 ≤4% → 4원/kWh, 4~6% → 3원/kWh (구 기준 6%/8% → 4원/3원). 오차율 분모는 **설비용량**, 설비이용률 ≥10% 시간만 평가. 대회 점수식(SMP·k 가중 절대오차 × 0.10)은 이 제도를 **단순화·가격가중화한 대회 고유 지표**이므로, 오차율(%)이 아니라 **SMP·k 가중 MAE**를 직접 최적화해야 합니다.
4. **SMP 국면**: 학습구간 SMP는 2022년 193.7원(에너지위기) → 2025년 117.6원으로 추세 하락, 2024년부터 육지 0원 시간 출현. 평가기간(테스트) 단순평균 108.0원, 월평균 2025-07 118.6원(최고) ~ 2025-12 88.8원(최저). 시간대 평균은 **20시 120.8원 최고, 13시 103.7원(낮 골), 04시 89.4원 최저**. 육지 SMP는 0원 하한(음수 없음); 제주 시범시장만 음수(-79원까지, 0원 이하 214회 누적).
5. **정산 가중의 중심**: 11~15시가 Σ SMP·k의 **44.7%**를 차지. 월별로는 2025-06~09, 2026-05가 각 9%대로 가장 무겁고(평일 정오 SMP 124~135원, k=3 → 시간당 가중 370~390), 2025-11~2026-02는 7%대. 0원·저가(주말/연휴 정오) 시간은 오차가 공짜 또는 매우 싸다.
6. **제공사 추정**(스키마 기반 고신뢰 추론, 주최측 미확인): **B = AccuWeather**(RealFeel/RealFeelShade/WetBulb/Ceiling ft/Visibility mile/UVIndex/Ice·Rain·Snow·PrecipProbability/TotalLiquid 등이 AccuWeather API 필드명과 1:1), **A = OpenWeatherMap**(temp/temp_min/temp_max 동일값, grnd_level 기압, clouds %, wind m/s, rain/snow mm — OWM Hourly Forecast 응답 구조와 일치). 두 제공사 모두 일사량을 주지 않으며, 한국 대상 독립 정확도 평가는 공개 문헌에서 찾지 못함 → 학습구간 `observed_wa/wb`로 **자체 백테스트**가 유일하고 합법적인 검증 수단.
7. **평가기간 실제 날씨(리스크 이해용)**: 2025 여름 = 역대 가장 더운 여름(25.7℃), 역대 2번째로 짧은 장마(남부 6/19~7/1, 13일), 7월 일조 251.0h(역대 2위) 뒤 7/16~20 광주 426.4mm 기록 호우; 9~10월 "이틀에 한 번 비"(9월 강수일수 15.1일 역대 2위, 10월 평균기온·강수량·강수일수 모두 역대 1위, 강릉 22일 연속 강수); 11월·2026년 1~2월은 역대급 건조·맑음(1월 일조 219.2h 역대 1위, 강수 4.3mm 역대 2위 적음; 다만 목포 42.1cm 등 호남 서해안 폭설); 2026 봄 2위 고온(5월 18.6℃ 역대 1위); 2026 장마는 6/30~7/1 지각 시작(평가기간 밖).

---

## (a) 제도: 예측제도·입찰제도·집합자원

### a-1. 재생에너지 발전량 예측제도 (육지, 2021-10-01 시행)
- **구조**: 20MW 이상(규칙상 "20MW 초과" 표기 자료도 있음) 태양광·풍력 사업자, 또는 **1MW 이하 소규모 자원을 모아 20MW를 채운 집합전력자원(소규모전력중개사업자)**이 **거래일 전일**에 시간대별 예측발전량을 KPX에 제출하고, 당일 오차율이 기준 이내면 정산금을 받는 인센티브 제도(페널티 없음). [kidd](https://kidd.co.kr/news/218609), [에너지신문](https://www.energy-news.co.kr/news/articleView.html?idxno=72728), [KDI 정책자료](https://eiec.kdi.re.kr/policy/materialView.do?num=205187)
- **예측오차율 정의**(전력시장운영규칙 제14.1.1조): "보유자원 내 주요자원의 **설비용량**에 대한 보유자원 예측발전량과 계량전력량의 차이의 절댓값의 백분율(%)". 즉 오차율 = |예측 − 계량| / 설비용량 × 100. **설비이용률 10% 이상인 시간만** 평가(이용률 <10% 시간 제외). [KPX 운영규칙 제14.1.1조](https://marketrule.kpx.or.kr/lmxsrv/law/joHistoryContent.do?SEQ=2&SEQ_CONTENTS=21489&DATE_START=20210501&DATE_END=20231230), [ETRI 논문](https://ksp.etri.re.kr/ksp/article/file/66174.pdf)
- **등록시험**: 1개월 평균 예측오차율 10% 이하. [일렉트릭파워](http://www.epj.co.kr/news/articleView.html?idxno=28702)
- **정산단가 개정(핵심)**:
  - 구 기준(2021~2025-05): 오차율 ≤6% → 4원/kWh, 6~8% → 3원/kWh.
  - **신 기준(태양광 2025-06-01부터, 풍력·혼합자원은 1년 유예 2026-06-01)**: ≤4% → 4원/kWh, 4% 초과~6% → 3원/kWh(2%p 강화). [전기신문](https://www.electimes.com/news/articleView.html?idxno=350873), [해줌 공지](https://blog.haezoom.com/notice_05/) (해줌 글 하나는 "4% 이하 3원"으로 적혀 있어 자료 간 불일치 — 전기신문·해줌 총정리 글의 4원/3원이 일관됨), [해줌 총정리](https://blog.haezoom.com/insight_vpp_19/)
  - 전기신문은 이 개정과 함께 **예측제도 일몰 예고**(입찰제도로 흡수)를 보도. 대회 평가기간 첫날(2025-06-01)이 정확히 신 기준 시행일과 같다는 점이 흥미롭습니다.
- **수익 규모 참고**: 중개사업자 광고 기준 1MW당 연 약 330만 원(이용률 3.6시간 가정). [해줌 총정리](https://blog.haezoom.com/insight_vpp_19/)
- **대회와의 관계(해석)**: 대회 점수식 S = ΣSMP·실적 − 0.10·ΣSMP·k·|오차| 는 "예측 인센티브"가 아니라 "불균형 비용형 페널티"입니다. 분모가 설비용량이 아닌 **절대 kWh 오차**에 **가격(SMP)**과 **시간대 가중(k)**을 곱하므로, 제도상 오차율 6% 같은 기준은 대회 점수와 직접 대응하지 않습니다. 최적화 대상은 Σ SMP(t)·k(t)·|e(t)| 이며, 절대오차 가중합을 최소화하는 점예측은 **가중 조건부 중앙값**(평균이 아님)입니다.

### a-2. 재생에너지 입찰제도 (제주 시범 → 육지 확대)
- **제주 시범사업**: 2024-06-01 착수. 실시간시장(15분 단위) + 예비력시장 + 재생에너지 입찰제도. 3MW 초과 의무참여, 1MW 초과는 선택(1MW급은 공동사업체로 참여 가능). 참여자는 용량정산금 등 추가 수익, 대신 급전지시(출력제어) 이행 의무. [에너지신문](https://www.energy-news.co.kr/news/articleView.html?idxno=203140), [발전산업신문](http://www.pgnkorea.com/news/articleView.html?idxno=28044), [KEA 이슈브리핑](https://www.energy.or.kr/energy_issue/mail_vol233/pdf/issue_336_03_all.pdf), [제주일보](https://www.jejunews.com/news/articleView.html?idxno=2208819)
- **제주 결과**: 하루전시장 입찰 하한이 0원이라 시장가격이 0원 이하로 떨어지며 **0원 이하 214회, 최저 −79원/kWh**(육지는 음수 없음). 출력제어는 시범사업 후 약 72% 감소(또 다른 보도는 약 11개월간 0건). [전기신문](https://www.electimes.com/news/articleView.html?idxno=337975), [전기신문](https://www.electimes.com/news/articleView.html?idxno=347287), [제이누리](https://www.jnuri.net/news/article.html?no=63460)
- **육지 확대 일정(2차 자료, 변동 많음)**: 2023년 산업부 계획은 "2025년 말 전국 확대". 2025-09 KPX 발표(해줌 전언)에 따르면 **2026년 1월부터 육지 하루전시장에 발전량 한정 적용, 6~9월 실시간·예비력시장 포함 본격 시행, 호남 우선** 거론. 2026년에는 호남권 **"재생에너지 준중앙급전제도"** 시범(봄·가을 급전지시 이행 시 출력제어 정산금 지급)이 시행. 2026-09 기사에서는 전국 확대 확정 일정이 제시되지 않았음. [해줌 2025-09](https://blog.haezoom.com/insight_vpp_28/), [머니투데이 2026-05](https://www.mt.co.kr/policy/2026/05/26/2026052609322861248), [파이낸셜뉴스 2026-09](https://www.fnnews.com/news/202609141514102012), [해줌 준중앙 가이드](https://blog.haezoom.com/insight_vpp_32/)
- **RPS 폐지 → 장기고정가격 입찰(2027 예정)**: 2026-01 전기신문 칼럼. [전기신문 칼럼](https://www.electimes.com/news/articleView.html?idxno=363629)
- **의미**: 대회 설정(두 집합자원, 하루전 17시 예측, 가격·시간대 가중 페널티)은 "예측제도(인센티브) → 입찰제도(불균형 책임)"로 넘어가는 2025~2026 과도기를 반영한 설계로 해석됩니다.

### a-3. 집합자원(Aggregator) 정의
- 전력시장운영규칙: **예측형 집합전력자원** = 재생에너지·ESS 등 소규모전력자원을 통합해 **주요자원 설비용량이 20MW를 넘는 가상의 설비**. 소규모전력중개사업은 1MW 이하 자원 대상. 2024년 개정안에 집합전력자원 등록·참여기준·등록시험 중단기준·예측오차율 산정 개정 포함. [KPX 운영규칙 개정이력](https://marketrule.kpx.or.kr/lmxdata/attach/2025/5/upload_5127126665285383397_p749.pdf)
- 대회 데이터의 253개소 평균 용량 ≈ 168.6 kW(42,655.4/253) → 전형적인 "1MW 이하 소규모 자원" 집합입니다. 태양광-풍력 혼합자원 등록 사례도 있음(대건소프트, 제주). [헬로디디](https://www.hellodd.com/news/articleView.html?idxno=93398)
- **G1/G2 분리의 점수 영향(수학적 사실, 참고)**: Σ(|e_G1|+|e_G2|) ≥ Σ|e_G1+e_G2| 이므로 두 집합으로 나누는 순간 페널티는 단일집합 대비 같거나 커집니다. 등호는 매 시각 두 집합 오차 부호가 같을 때 성립 → **두 집합의 오차가 강하게 양의 상관을 갖도록(지역·설비 구성이 서로 '거울'처럼 비슷하도록)** 나누는 것이 페널티 최소화에 유리합니다. 지역별로 갈라놓으면 서로 다른 날씨 오차가 상쇄되지 못하고 각각 절대값으로 계산됩니다.

---

## (b) SMP 동향 2025-06 ~ 2026-06

### b-1. KPX 공식 월별 SMP (원/kWh, 가중평균) — 외부 참고용
| 월 | 육지 | 제주 | | 월 | 육지 | 제주 |
|---|---|---|---|---|---|---|
| 2025-06 | 118.02 | 120.62 | | 2025-12 | 90.43 | 91.03 |
| 2025-07 | 120.39 | 121.13 | | 2026-01 | 103.54 | 102.94 |
| 2025-08 | 117.39 | 118.46 | | 2026-02 | 108.52 | 108.47 |
| 2025-09 | 112.90 | 114.06 | | 2026-03 | 110.03 | 106.77 |
| 2025-10 | 101.53 | 101.17 | | 2026-04 | 118.94 | 117.24 |
| 2025-11 | 94.80 | 95.82 | | 2026-05 | 121.36 | 118.26 |
2025년 연평균 육지 112.73 / 제주 112.49. 평가기간 이후 2026-07 133.79, 2026-08 148.39(유가 급등)로 급등했으나 **평가기간 밖**. [KPX 월별 SMP](https://new.kpx.or.kr/smpMonthly.es?mid=a10606080300&device=pc), [KPX 연도별](https://new.kpx.or.kr/menu.es?mid=a10606080400)

### b-2. 제공된 `smp.csv`(평가기간) 자체 집계 — 제공 데이터이므로 사용 가능
- 8,760행, 단순평균 **108.02원**, 최소 0, 최대 193.75(2025-06-20 11시). 0원 **18시간**.
- 월별 단순평균: 06월 116.1 / 07월 118.6 / 08월 116.0 / 09월 109.8 / 10월 98.8 / 11월 93.5 / 12월 88.8 / 01월 101.7 / 02월 106.5 / 03월 108.8 / 04월 117.8 / 05월 120.1. KPX 육지 가중평균보다 1~2원 낮게 일관되게 따라감(가중평균은 고가 시간 수요가 커서 단순평균보다 높음) → **육지 SMP로 판단**. 결정적 증거: 2025-10-08(추석 연휴) 13시 0원이 에너지경제 보도("추석 연휴 비 그쳐 태양광 늘자 13~14시 육지 SMP 0원, 13시 태양광 13,125MW = 수요의 23.2%")와 일치. 제주였다면 음수와 훨씬 많은 0원이 있어야 함. [에너지경제](https://m.ekn.kr/view.php?key=20251008029334262)
- **시간대 평균**: 04시 89.4(최저) → 10시 116.3 → **13시 103.7(낮 골, 덕커브)** → 19시 120.3, **20시 120.8(최고)** → 23시 112.4. 저녁피크는 전력시장 전체 추세(최대전력 발생시각 평균 2024 17:49 → 2025 18:20 → 2026 18:53; 7~8시 피크 비중 60.5% → 69.8% → 86.0%)와 일치. [뉴시스](https://www.newsis.com/view/NISX20260814_0003749637), [더팩트](https://m.tf.co.kr/read/economy/2354650.htm)
- **0원 18시간 전부 13시 또는 14시**: 10/8(수, 추석연휴), 10/11(토), 11/15(토), 11/16(일), 11/22(토), 11/26(수), 11/29(토), 12/7(일), 1/17(토), 1/18(일), 1/25(일), 1/31(토), 2/1(일), **2/17(화)·2/18(수) = 설 연휴**, 3/26(목), 3/27(금), 3/29(일). 즉 "경부하(주말·명절) + 맑음 + 정오"가 조건이고, 2026년 3월 하순엔 평일에도 발생(기상청: 3/23~24, 26~29 고온·맑음).
- **낮(11~15시) SMP 평일 vs 주말**: 2025-06 135.0 vs 117.1, 2025-11 106.2 vs 72.0, 2025-12 99.8 vs 70.1, 2026-01 101.5 vs 69.5 → 겨울 주말 정오는 평일의 70% 수준.
- 30원 미만 시간: 10월 3, 11월 5, 12월 2, 1월 6, 2월 7, 3월 3 (4~9월 없음).
- **학습구간 `train/smp.csv` 연평균**: 2021 93.0 / 2022 193.7 / 2023 163.3 / 2024 125.4(0원 6시간, 첫 출현) / 2025(1~5월) 117.6(0원 11시간). 가격 수준이 구조적으로 바뀌었으므로 "과거 SMP 패턴"을 학습해 봐야 의미가 작고, 평가기간 SMP는 어차피 주어져 있습니다.

### b-3. 육지 0원·출력제어·마이너스 가격 논의 (외부 맥락)
- 육지 0원 사례: 2025-03-09(일) 11~15시 5시간 연속 0원(13시 태양광이 총수요의 35.4%), 2025-04-20, 2025-10-08(추석). [전기신문](https://www.electimes.com/news/articleView.html?idxno=351562), [전기신문](https://www.electimes.com/news/articleView.html?idxno=332825)
- **육지 출력제어 급증**: 호남 기준 2023년 2일 → 2024년 26일 → 2025년 82일 → **2026년 상반기 59회**; 3~5월 봄철 집중, 2026-06-13(토) 전남·전북 100여 곳 제어(계통 제약). 전남 2026-03 5회(9시간, 제어율 3.9%), 04월 3회(5시간, 3.5%). KPX 출력제어 전망 공지(2025-05-25 일) 예정시간 10~15시, 최소수요 13시경; 사업자들은 "11~15시 집중" 주장. [해줌 2026 상반기](https://blog.haezoom.com/insight_vpp_48/), [파이낸셜뉴스](https://fnnews.com/news/202610251844069781), [뉴스펭귄](https://www.newspenguin.com/news/articleView.html?idxno=21861), [머니투데이](https://www.mt.co.kr/policy/2026/05/26/2026052609322861248), [KPX 출력제어 전망](https://new.kpx.or.kr/board.es?mid=a10109050000&bid=0216&act=view&list_no=75189&tag=&nPage=1), [이투뉴스](http://www.e2news.com/news/articleView.html?idxno=320342), [전기신문](https://www.electimes.com/news/articleView.html?idxno=335254)
- **마이너스 SMP**: 육지 제도상 0원 하한, 음수 도입 공식 논의는 확인되지 않음. 제주 시범시장만 음수. 2026년 4~6월에는 반대로 유가 급등으로 **SMP 상한제 재도입** 논의(평가기간 밖). [해줌 해설](https://blog.haezoom.com/insight_vpp_22/), [에너지경제 2026-04](https://edata.ekn.kr/article/view/ekn202604130001), [다음/뉴스 2026-06](https://v.daum.net/v/20260620140002069)
- **대회 리스크로의 번역**: (1) 0원 시간엔 오차 비용 0 → 그 시간 예측에 자원 낭비 불필요. (2) 출력제어는 "실적"을 예보보다 낮추는 사건이지만, 이 데이터셋 발전소(평균 169 kW)는 1MW 이하 비제어 자원이 대부분일 가능성이 커(추론, 미확인) 제어 대상이 아닐 수 있음. 학습구간 호남권 발전소의 맑은 봄 주말 정오 실적이 비정상적으로 낮은지 확인하면 판단 가능.

---

## (c) 어느 시간·계절이 정산 가중을 지배하는가 (`smp.csv` 기반, 사용 가능)
- **페널티 가중 Σ SMP·k 의 시간대 비중**: 11시 9.3%, 12시 9.1%, 13시 8.4%, 14시 8.9%, 15시 9.0% → **11~15시 합 44.7%**. 나머지 19시간이 55.3%(각 2.4~3.3%). 태양광 발전은 어차피 10~15시에 몰리므로 **실질 페널티의 과반이 11~15시에서 발생**.
- **월별 비중**: 2025-06 9.1 / 07 9.5 / 08 9.2 / 09 8.7 / 10 7.8 / 11 7.1 / 12 7.0 / 2026-01 7.7 / 02 7.4 / 03 8.2 / 04 8.8 / 05 9.5 (%). 발전량까지 고려하면 **2025-06~09, 2026-04~05**가 승부처(가격·일사 모두 높음).
- **평일 정오(11~15시) 시간당 가중치 SMP·k 평균**: 2025-06 389, 07 383, 08 368, 09 377, 10 312, 11 284, 12 276, 2026-01 277, 02 302, 03 290, 04 336, 05 370. 즉 6월 평일 정오 1 kWh 오차 = 약 39원 손실(수익 1 kWh ≈ 130원의 30%).
- **수익 항 ΣSMP·실적은 예측과 무관**(집합 구성만 영향; 253개 전부를 둘 중 하나에 반드시 배정하므로 총수익도 고정). 따라서 **순위는 오로지 페널티 항**으로 갈립니다. 동점 처리 규칙은 문제정의서 확인 필요.
- **최고가 시간**: 2025-06-20 11시 193.75, 2025-09-18 12시 193.74, 2026-01-21~23 및 02-04 10시 185~190(한파 아침피크), 2026-03-16 19시 179.89. 여름·초가을 평일 정오와 겨울 한파 오전이 고가.
- **계절성 요약**: 여름(6~9월) 낮 SMP 119~125원·k=3 → 최대 가중. 겨울(11~2월) 낮 93~107원이나 주말 정오 70원대·0원 빈발 → 가중 낮음. 봄(4~5월) 다시 상승.

---

## (d) 기상 제공사 A·B 추정과 품질 특성

### d-1. 제공사 B ≈ AccuWeather (고신뢰 추론)
- 근거(README 스키마): `wb_feel_temp`(RealFeelTemperature), `wb_feel_temp_shade`(RealFeelTemperatureShade, 실측에만), `wb_wet_bulb_temp`(WetBulbTemperature), `wb_ceiling`(Ceiling, 원단위 ft), `wb_vis`(원단위 mile), `wb_uv_idx`(UVIndex), `wb_precip_prob/rain_prob/snow_prob/ice_prob`(PrecipitationProbability/RainProbability/SnowProbability/IceProbability), `wb_total_liq`(TotalLiquid), `wb_rain/snow/ice`(Rain/Snow/Ice), `wb_wind_gust_spd`(WindGust), `wb_cloud`(CloudCover); 실측의 `wb_appr_temp`(ApparentTemperature), `wb_wind_chill_temp`(WindChillTemperature), `wb_precip_1h`(Precip1hr), `wb_pressure`. 이 조합은 AccuWeather Hourly Forecast(details=true)·Current Conditions API 고유 필드명과 1:1이며, README의 "원본 단위 °F·mile·ft에서 환산되어 값 간격이 일정" 설명도 AccuWeather 기본(imperial) 응답과 부합. [AccuWeather Forecast API 개요](https://apidev.accuweather.com/developers/forecasts/general), [AccuWeather Hourly 레시피](https://apidev.accuweather.com/recipes/hourly-forecast.md), [필드명 참고(제3자 스키마)](https://docs.discover.swiss/dev/reference/dataschema/definition/infocenter-classes/HourlyForecast/)
- 알려진 특성(일반론, 한국 대상 독립 검증 문헌 없음): 미국 기반 글로벌 블렌드 모델 + 지점 보정. 강수확률은 캡(데이터 최대 90%)이 걸린 듯한 분포, UV 지수는 주간에만 의미, `wb_ceiling` 0/최대값(16,337 m ≈ 'unlimited')이 섞여 있어 구간화 필요, 실측 `wb_cloud`>100·`wb_uv_idx`>15 같은 수신 오류값(README 표) 존재. 운량·운고·UV·시정 조합은 일사 대리변수로 A보다 풍부.

### d-2. 제공사 A ≈ OpenWeatherMap (고신뢰 추론)
- 근거: `wa_temp/temp_max/temp_min`이 하루전 예보에서 동일값 — OWM 문서가 "대부분의 경우 temp_min·temp_max는 temp와 같은 값"이라고 명시; `wa_ground_press`(grnd_level, hPa), `wa_humidity`(%, 104 같은 >100 원본값), `wa_cloud`(clouds.all %), `wa_wind_speed` m/s, `wa_rain/snow` mm — OWM Hourly Forecast 응답 필드 구성과 일치하고 체감온도·이슬점·UV·시정이 빠진 점도 부합. [OpenWeatherMap Hourly Forecast 문서](https://openweathermap.org/api/hourly-forecast)
- 알려진 특성(일반론): 글로벌 NWP(GFS/ECMWF 계열) 기반 자체 블렌드를 격자 보간, 운량은 거칠고 저해상도, 강설은 mm 물환산, 일사량 없음. 실측 `wa_wind_speed` 9,999 같은 결측 코드 존재(README). "61개 지점"은 관측소가 아니라 제공사 격자/도시 포인트일 가능성.
- **주의**: A/B 모두 주최측이 공식적으로 밝힌 것은 아니며(대회 FAQ/문제정의서 확인 필요), 식별해도 외부 데이터 사용은 금지이므로 "어느 API인지"는 변수 해석·전처리 설계에만 활용하세요.

### d-3. 품질 비교에 대한 공개 근거
- OWM vs AccuWeather의 한국 태양광 대상 일대일 비교 연구는 찾지 못함. 벤더 자료(Solcast GHI 오차 3.8% vs 범용 API ~8%, 하루전 일발전량 MAPE 5.9% vs GFS 7.7%; Solargis 시간별 GHI RMSD 8.58%)는 자사 주장이며 대회와 무관. [Solcast](https://www.solcast.com.au/live-and-forecast/comparisons), [Solargis](https://www.solargis.com/technology/accuracy-and-validation-forecast), [Sangrody et al. arXiv](https://arxiv.org/pdf/1709.08135)
- 국내 VPP/발전사는 하루전 오차율 5% 내외(엔라이튼), 95~97% 정확도(한전·중부발전)를 주장하나 기준이 달라 비교 불가. [머니투데이](https://mt.co.kr/future/2026/10/26/2026102609111849407), [인더스트리뉴스](https://www.industrynews.co.kr/news/articleView.html?idxno=45106)
- **합법적 검증 방법**: 학습구간 `forecast_wa/wb`(round 10·17) ↔ `observed_wa/wb` ↔ `generation`으로 지점·계절·시간대별 예보 오차(운량 bias, 강수 hit/miss)를 산출하고, 두 제공사·두 라운드의 가중 앙상블을 발전량 기준으로 학습. round=17이 리드타임이 짧아 일반적으로 우세하나 두 라운드 모두 예측시점(전일 17:00) 이전 발행이라 사용 가능(README).

---

## (e) 한국 태양광 기후학 + 평가기간(2025-06~2026-06) 실제 사건 — **리스크 이해 전용, 모델 입력 금지**

### e-1. 일반 기후학
- **장마**(평년 시작: 제주 6/19, 남부 6/23, 중부 6/25; 7월 하순 종료): 6월 하순~7월 중순 발전량 급감·예보 불확실 최대. **폭염**(7~8월): 모듈 온도 상승으로 kWh/일사 효율 저하, 맑아 예측은 쉬움. **가을 이동성 고기압**(10~11월): 맑고 건조, 연중 예측이 가장 쉬운 시기. **겨울 서해안 눈**(12~2월, 호남·충남 서해안 해기차 강설): 적설이 패널을 덮으면 맑은 날에도 발전 0에 가까움(며칠 지속), 예보 운량·일사와 실적 괴리 최대. **황사·미세먼지**(3~5월, 최근 1~2월도): 맑음 예보에도 일사 감소. 2026년 봄 황사는 서울 기준 2월 1일·4월 2일만 관측(전국 통계 미확인). [기상청 황사통계](https://www.weather.go.kr/w/hazard/dust/dust-obs-days.do)

### e-2. 평가기간 월별 실제 (기상청 보도자료 기준)
| 기간 | 실제 | 태양광·예측 함의 |
|---|---|---|
| 2025-06 | 6월 폭염·열대야 기승, 평균기온 역대 최고 수준(보도자료 제목). 장마 **제주 6/12~6/26(15일), 남부 6/19~7/1(13일)** 역대 2번째로 짧음, 장마 강수 200.5mm(평년 356.7), 강수일수 8.8일(평년 17.3). | 6월 발전·SMP 모두 높음(평일 정오 135원) → 연중 최대 가중 구간이 '맑고 더운' 달. |
| 2025-07 | 평균기온 역대 2위, 상순 1위. 강수 249.0mm(85.8%), 강수일수 8.3일(1973년 이래 3번째 적음), **일조 251.0h(평년 150.1, 역대 2위)**, 강수 96.1% 중순 집중: 7/16~20 광주 일강수 426.4mm(관측 이래 최고), 서산 1시간 114.9mm, 산청 누적 775mm(2차 자료). | 전반적으로 맑으나 7/16~20 호남·충청·경남 극한 호우 → 며칠간 '예보 대비 과대예측' 리스크 집중. |
| 2025-08 | 폭염일수 11.5일(+5.6), 열대야 8.0일, 강수 189.8mm(평년 282.6), 강수일수 10.6일(−3.2). 여름 전체: 평균 25.7℃ 역대 1위, 폭염 28.1일, 강수일수 29.3일(−9.2, 하위 5위). | 맑고 더움 → 고온 효율 저하 보정이 관건. |
| 2025-09 | 평균 23.0℃(역대 2위, 3년 연속 기록 고온), 강수 228.8mm(155%), **강수일수 15.1일(평년 9.3, 역대 2위)**, 뇌전일수 4.5일 역대 최다, 군산 시간당 152.2mm(9/7). | 소나기·뇌우형 → 운량 예보 신뢰도 낮음, 오차 큰 달(가격은 아직 높음: 낮 평균 119원). |
| 2025-10 | **평균기온·강수량·강수일수 모두 역대 1위**, 강릉 10/3~24 22일 연속 강수(1911년 이래 최장), 중순까지 이틀에 한 번 비. 10/8 추석 연휴 맑음 → 육지 SMP 0원. | 10월 발전량 비정상적으로 낮고 변동 큼; 추석 연휴(10/3~9) 경부하 + 맑음 조합. |
| 2025-11 | 건조·맑음: 강수 20.2mm(하위 10위), 강수일수 4.9일(하위 6위), 평균 8.5℃(+0.9). | 예측 쉬운 달이나 SMP 낮고 주말 정오 0원 5회(11/15,16,22,26,29). |
| 2025-12 | 겨울철 자료상 12월 강수는 평년 수준. 호남 서해안 12/2~4·12/25 대설특보(나무위키, 미검증). 12월 SMP 월평균 88.8원(연중 최저). | 호남 적설 리스크, 가중은 최저. |
| 2026-01 | **강수 4.3mm(평년의 19.6%, 역대 2위 적음), 상대습도 53% 역대 최저, 일조 219.2h(+41.1h, 역대 1위)**, 눈일수 6.6, 적설 7.0cm이나 **목포 42.1cm(1월 4위)**, 1/11 무안 19.7cm. 1/20부터 10일 이상 한파(하순 −3.8℃), 1/15 남부 20℃ 이상고온. 원인: 음의 북극진동+베링해 블로킹. | 전국 맑음이지만 호남 서해안 폭설 → 지역 편차 극대. 한파 오전 10시 SMP 185~190원(1/21~23). 0원은 주말 13시 4회. |
| 2026-02 | 공식 월보 미확인. 3월 보도자료가 "1~2월 강수 평년보다 적음" 명시; 서울 2월 강수 3.2mm(나무위키, 미검증). 설 연휴 2/17~18 13시 0원. 겨울 전체(12~2월): 강수 45.6mm(53%), 적설 14.7cm(평년 26.4의 절반), 평균 1.1℃(+0.6). | 건조·맑음 지속, 명절 경부하. |
| 2026-03 | 평균 7.4℃(+1.3, 9위), 강수 66.0mm(120%), 강수일수 7.6, 3/23~24·3/26~29 고온(62개 지점 중 50% 이상 90퍼센타일 초과). 3/26(목)·27(금)·29(일) 13시 0원. | 봄철 출력제어 시즌 개막(전남 3월 5회). 평일 0원 출현. |
| 2026-04 | 평균 13.8℃(역대 3위), 강수 79.7mm 중 87.6%가 상순(4/4, 4/9) 집중, 중순 이상고온, 하순 건조. 육지 출력제어(전남 4월 3회). | 상순만 흐림, 이후 맑음·고온. |
| 2026-05 | **평균 18.6℃ 역대 1위**, 폭염일수 0.5일(2위), 5/14~18 고온(최고 35.1℃), 강수 123.5mm 중 62.3%가 5/20~21 집중, 5/30 첫 열대야. 봄 전체 13.3℃(2위), 268.1mm(108%). | 5월 평일 정오 SMP 129원·k=3 → 6월 다음으로 무거운 달이 '맑고 더움'. |
| 2026-06-01 | 평가 마지막 시각(00:00)만 해당. 2026 장마는 제주 6/30·남부 6/30~7/1·중부 7/1 지각 시작(기사 기준, 기상청 확정치 아님) → 평가기간 밖. | — |
- 2025년 연간: 평균 13.7℃(역대 2위), 연 일조 2266.4h(평년 2376.1h보다 적음), 강수일수 109.0일, 가을 강수일수 34.3일(평년 22.6, 역대 2위). 즉 평가기간은 "**여름·겨울은 이례적으로 맑고, 가을(9~10월)은 이례적으로 흐린**" 비대칭 해였습니다. 학습구간(2021~2025-05)의 가을 평균 패턴으로 2025년 가을을 예측하면 체계적 과대예측이 났을 것입니다 — **사후 통계이므로 모델에는 못 쓰고**, 제공 예보(A/B)의 운량·강수 신호를 얼마나 신뢰할지, 계절 사전분포에 얼마나 기대지 않을지 설계할 때의 '교훈'으로만 쓰세요.
- 출처: [기상청 2025 여름철](https://www.korea.kr/briefing/pressReleaseView.do?newsId=156713340), [기상청 2025 6월](https://www.kma.go.kr/kma/news/press.jsp?bid=press&mode=view&num=1194505&page=1&from=2025-05-19&to=2025-08-19), [기상청 2025 7월](https://www.kma.go.kr/kma/news/press.jsp?bid=press&mode=view&num=1194509&page=1&from=2025-05-07&to=2025-08-07), [기상청 8월 기후동향](https://www.kma.go.kr/download_02/ellinonewsletter_2025_08.pdf), [기상청 2025 9월](https://www.korea.kr/briefing/pressReleaseView.do?newsId=156713395), [기상청 2025 10월](https://www.korea.kr/briefing/pressReleaseView.do?newsId=156725042), [기상청 2025 가을철](https://www.korea.kr/briefing/pressReleaseView.do?newsId=156733139&pWise=sub&pWiseSub=C4), [기상청 11월 기후동향](https://www.kma.go.kr/download_02/ellinonewsletter_2025_11.pdf), [기상청 2025 연 기후특성](https://www.korea.kr/briefing/pressReleaseView.do?newsId=156738247), [워터저널 2025 연 분석](https://www.waterjournal.co.kr/news/articleView.html?idxno=85167), [기상청 2025 겨울철](https://www.kma.go.kr/kma/news/press_01.jsp?bid=press&mode=view&num=1194607), [워터저널 겨울철](https://www.waterjournal.co.kr/news/articleView.html?idxno=85553), [기상청 2026 1월](https://www.weather.go.kr/kma/flexer/html/press/2026/02/03/ATC202602031731562_92984048-2e9a-4cd9-94c3-9a042308c0a8.hwp.files/Sections1.html), [한국일보 1월 건조](https://www.hankookilbo.com/news/article/A2026020410310003095), [아시아경제 1/11 호남 폭설](https://view.asiae.co.kr/article/2026011110212490879), [기상청 2026 3월](https://www.kma.go.kr/kma/news/press_01.jsp?mode=view&num=1194628), [2026 4월 기후특성](https://m.news.nate.com/view/20260504n22394), [2026 봄철 기후특성](https://m.news.nate.com/view/20260602n24271), [기상청 5월 기후동향](https://www.kma.go.kr/download_02/ellinonewsletter_2026_05.pdf), [2026 장마 시작](https://v.daum.net/v/WqmSLdhDeI), [광주 426mm 호우](https://www.newsis.com/view/NISX20250717_0003256468), [나무위키 2025-26 한파·폭설(미검증)](https://namu.wiki/w/2025-2026%EB%85%84%20%ED%95%9C%EB%B0%98%EB%8F%84%20%ED%95%9C%ED%8C%8C%20%EB%B0%8F%20%ED%8F%AD%EC%84%A4%20%EC%82%AC%ED%83%9C)

---

## (f) 시장 관점의 전략 시사점 (요약)
1. **손실함수 = Σ SMP(t)·k(t)·|e(t)|** 를 그대로 학습 목적함수(가중 MAE / τ=0.5 pinball)로 쓰고, 점예측은 **가중 중앙값**을 노리세요. 평가기간 SMP·k는 제공 데이터입니다(규정 재확인).
2. **11~15시·4~9월 평일**에 모델 용량과 검증을 집중. 0원·30원 미만 시간(주말·명절 정오, 10~3월)은 우선순위 최하.
3. **집합 구성**: 두 집합의 시간별 오차 부호가 같아지도록 '거울 분할'(지역·용량·성능 층화 후 번갈아 배정)이 수학적으로 유리. 지역 분할은 불리.
4. **제도 숫자(오차율 4/6%, 4원/3원)는 대회 점수와 무관**하나 발표평가에서 "왜 20MW·왜 11~15시·왜 가격가중인가"를 설명하는 배경으로 유효.
5. **외부 날씨 사후정보 사용 금지**. 다만 학습구간 안에서 "흐린 가을(예: 2023-09~10), 서해안 폭설(2022-12, 2023-01), 짧은 장마" 유사 구간을 골라 **스트레스 검증 세트**를 만드는 것은 합법이며, 2025-26 실제 패턴에 대비하는 가장 현실적인 방법입니다.
6. **출력제어**는 호남 소형 발전소엔 아직 제한적(추론). 학습구간 호남 지점의 봄 맑은 주말 정오 실적 급락 여부를 확인해 포함 여부 결정.

---

## 검증 상태 / 미확인 사항
- 예측제도 신 정산단가(4%→4원, 4~6%→3원)는 전기신문·해줌 총정리 기준. 해줌 공지 글은 "4% 이하 3원"으로 표기(불일치). 운영규칙 원문 미열람.
- 육지 재생에너지 입찰제도 2026-01 적용 여부는 2차 자료(해줌 전언)만 확인, KPX/정부 공식 발표문 미확인. 2026-09 기사엔 확대 일정 없음.
- 제공사 A=OpenWeatherMap, B=AccuWeather 는 스키마 기반 추론이며 주최측 공식 확인 아님.
- 2025-12, 2026-02 전국 월간 기후특성 원문 미확인(겨울철 종합·3월 보도자료의 간접 언급만). 2026 봄 전국 황사일수·일조시간 미확인. 2025년 12월 호남 대설 날짜는 나무위키(미검증).
- `smp.csv`가 육지 SMP라는 판단은 KPX 월평균 비교 + 2025-10-08 보도 일치에 근거한 추론(README에 명시 없음).
- 문제정의서(OIBC2026-문제정의서.md)·scoring.py가 폴더에 없어 동점 처리·무효 조건·k 정의의 정본은 미확인.

## Sources
- https://kidd.co.kr/news/218609
- https://www.energy-news.co.kr/news/articleView.html?idxno=72728
- https://eiec.kdi.re.kr/policy/materialView.do?num=205187
- http://www.epj.co.kr/news/articleView.html?idxno=28702
- https://ksp.etri.re.kr/ksp/article/file/66174.pdf
- https://marketrule.kpx.or.kr/lmxsrv/law/joHistoryContent.do?SEQ=2&SEQ_CONTENTS=21489&DATE_START=20210501&DATE_END=20231230
- https://marketrule.kpx.or.kr/lmxdata/attach/2025/5/upload_5127126665285383397_p749.pdf
- https://www.electimes.com/news/articleView.html?idxno=350873
- https://blog.haezoom.com/notice_05/
- https://blog.haezoom.com/insight_vpp_19/
- https://blog.haezoom.com/insight_vpp_28/
- https://blog.haezoom.com/insight_vpp_32/
- https://blog.haezoom.com/insight_vpp_48/
- https://blog.haezoom.com/insight_vpp_22/
- https://www.hellodd.com/news/articleView.html?idxno=93398
- https://www.energy-news.co.kr/news/articleView.html?idxno=203140
- http://www.pgnkorea.com/news/articleView.html?idxno=28044
- https://www.energy.or.kr/energy_issue/mail_vol233/pdf/issue_336_03_all.pdf
- https://www.jejunews.com/news/articleView.html?idxno=2208819
- https://www.electimes.com/news/articleView.html?idxno=337975
- https://www.electimes.com/news/articleView.html?idxno=347287
- https://www.jnuri.net/news/article.html?no=63460
- https://www.mt.co.kr/policy/2026/05/26/2026052609322861248
- https://www.fnnews.com/news/202609141514102012
- https://fnnews.com/news/202610251844069781
- https://www.electimes.com/news/articleView.html?idxno=363629
- https://new.kpx.or.kr/smpMonthly.es?mid=a10606080300&device=pc
- https://new.kpx.or.kr/menu.es?mid=a10606080400
- https://m.ekn.kr/view.php?key=20251008029334262
- https://www.electimes.com/news/articleView.html?idxno=351562
- https://www.electimes.com/news/articleView.html?idxno=332825
- https://www.electimes.com/news/articleView.html?idxno=335254
- https://www.newsis.com/view/NISX20260814_0003749637
- https://m.tf.co.kr/read/economy/2354650.htm
- https://www.newspenguin.com/news/articleView.html?idxno=21861
- https://new.kpx.or.kr/board.es?mid=a10109050000&bid=0216&act=view&list_no=75189&tag=&nPage=1
- http://www.e2news.com/news/articleView.html?idxno=320342
- https://edata.ekn.kr/article/view/ekn202604130001
- https://v.daum.net/v/20260620140002069
- https://apidev.accuweather.com/developers/forecasts/general
- https://apidev.accuweather.com/recipes/hourly-forecast.md
- https://docs.discover.swiss/dev/reference/dataschema/definition/infocenter-classes/HourlyForecast/
- https://openweathermap.org/api/hourly-forecast
- https://www.solcast.com.au/live-and-forecast/comparisons
- https://www.solargis.com/technology/accuracy-and-validation-forecast
- https://arxiv.org/pdf/1709.08135
- https://mt.co.kr/future/2026/10/26/2026102609111849407
- https://www.industrynews.co.kr/news/articleView.html?idxno=45106
- https://www.weather.go.kr/w/hazard/dust/dust-obs-days.do
- https://www.korea.kr/briefing/pressReleaseView.do?newsId=156713340
- https://www.kma.go.kr/kma/news/press.jsp?bid=press&mode=view&num=1194505&page=1&from=2025-05-19&to=2025-08-19
- https://www.kma.go.kr/kma/news/press.jsp?bid=press&mode=view&num=1194509&page=1&from=2025-05-07&to=2025-08-07
- https://www.kma.go.kr/download_02/ellinonewsletter_2025_08.pdf
- https://www.korea.kr/briefing/pressReleaseView.do?newsId=156713395
- https://www.korea.kr/briefing/pressReleaseView.do?newsId=156725042
- https://www.korea.kr/briefing/pressReleaseView.do?newsId=156733139&pWise=sub&pWiseSub=C4
- https://www.kma.go.kr/download_02/ellinonewsletter_2025_11.pdf
- https://www.korea.kr/briefing/pressReleaseView.do?newsId=156738247
- https://www.waterjournal.co.kr/news/articleView.html?idxno=85167
- https://www.kma.go.kr/kma/news/press_01.jsp?bid=press&mode=view&num=1194607
- https://www.waterjournal.co.kr/news/articleView.html?idxno=85553
- https://www.weather.go.kr/kma/flexer/html/press/2026/02/03/ATC202602031731562_92984048-2e9a-4cd9-94c3-9a042308c0a8.hwp.files/Sections1.html
- https://www.hankookilbo.com/news/article/A2026020410310003095
- https://view.asiae.co.kr/article/2026011110212490879
- https://www.kma.go.kr/kma/news/press_01.jsp?mode=view&num=1194628
- https://m.news.nate.com/view/20260504n22394
- https://m.news.nate.com/view/20260602n24271
- https://www.kma.go.kr/download_02/ellinonewsletter_2026_05.pdf
- https://v.daum.net/v/WqmSLdhDeI
- https://www.newsis.com/view/NISX20250717_0003256468
- https://namu.wiki/w/2025-2026%EB%85%84%20%ED%95%9C%EB%B0%98%EB%8F%84%20%ED%95%9C%ED%8C%8C%20%EB%B0%8F%20%ED%8F%AD%EC%84%A4%20%EC%82%AC%ED%83%9C
- https://dataen.ai/challenge (공식 사이트; JS 앱이라 본 세션에서는 미열람)
- https://i-ai.postech.ac.kr/event/41?page=2
- https://www.solartodaymag.com/news/articleView.html?idxno=21096
