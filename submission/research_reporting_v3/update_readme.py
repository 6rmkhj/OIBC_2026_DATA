#!/usr/bin/env python3
"""Metadata-only reporting for deterministic transport experiments and retained history."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime
import fcntl
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE = 'research_novel_20261108'
OVERVIEW = 'analysis_outputs/experiment_overview_v3'
PREVIOUS_OVERVIEW = 'analysis_outputs/experiment_overview_v2'
DEADLINE = '2026-11-08T14:00:00Z'
SEARCH_STOP = '2026-11-08T12:00:00Z'
LIMIT = 2 * 1024 * 1024
PUBLISHER_SHA = '89d2e4276195847792b7cf31d5d22339fee0a8bd0fb904110a38e996b51ea109'
V2_REPORTER = 'submission/research_reporting_v2/update_readme.py'
PINS = {
    V2_REPORTER: 'f392d7e8806ed8b200797c9e7036cc8cc7947f2ec9755ba97460a0a08cb07f2a',
    'submission/research_reporting_v2/publish_readme.py': '24c471810a1b9548b2f06a836838f25a8514ffd0617abec56a1d17d30698ada2',
    'submission/research_reporting/update_readme.py': '651be8197f8f7784cb7d90f27ab9536d50c835473d5cea324822c2f094863f10',
    'submission/research_reporting/history_catalog.json': '0e3fdbb59d52290af2e92e9491d13160fe2a809723529e6d6defb2fa0f2518d1',
}
EXTRA_FIELDS = ['family', 'coefficient_budget', 'coefficient_budget_meaning', 'primary_fit_status',
                'recent_evaluation_status', 'metrics_json', 'result_status',
                'primary_W_change_pct_vs_reference', 'recent_W_change_pct_vs_reference']

def sha(data):
    return hashlib.sha256(data).hexdigest()

def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)

def load_v2(root=ROOT):
    root = Path(root)
    for relative, expected in PINS.items():
        if sha((root / relative).read_bytes()) != expected:
            raise ValueError('Pinned historical reporting source changed: ' + relative)
    path = root / V2_REPORTER
    source = path.read_bytes()
    spec = importlib.util.spec_from_file_location('oibc_reporting_v2_frozen_for_v3', path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, str(path), 'exec'), module.__dict__)
    return module

def comparison(config, previous):
    ignored = {'id', 'comparison_id', 'description', 'label'}
    changes = [(key, previous.get(key), config.get(key)) for key in sorted(set(previous) | set(config))
               if key not in ignored and previous.get(key) != config.get(key)]
    text = '; '.join(f'{k}: {a}→{b}' for k, a, b in changes)
    return text or '동일 설정 또는 비교 없음', len(changes), '단일 설정 차이' if len(changes) == 1 else '여러 설정 동시 변경' if changes else '기준 설정'

def score_pair(result, fold):
    record = result.get('metrics', result.get('folds', result.get('scores', {}))).get(fold, {})
    candidate = record.get('candidate', record.get('score', record))
    reference = record.get('reference', record.get('baseline', {}))
    return candidate if isinstance(candidate, dict) else {}, reference if isinstance(reference, dict) else {}

def actual_fit_seconds(receipt):
    training = receipt.get('training', {})
    for value in (receipt.get('elapsed_seconds'), training.get('elapsed_seconds')):
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0:
            return value
    try:
        start = datetime.fromisoformat(training['fit_started_utc'].replace('Z', '+00:00'))
        end = datetime.fromisoformat(training['fit_finished_utc'].replace('Z', '+00:00'))
        if start.utcoffset() is not None and end.utcoffset() is not None and end >= start:
            return (end - start).total_seconds()
    except (KeyError, TypeError, ValueError, AttributeError):
        pass
    return None

def completion_lines(stage, old, v2):
    result = stage['completion']; audit = stage.get('completion_audit', {})
    status = result.get('status', '미기록'); recommendation = result.get('recommendation', '미기록')
    decision = recommendation + (' (추천하지 않음)' if recommendation == 'NOT_RECOMMENDED' else '')
    lines = [f"최종 처리: `{status}` · 독립 검증: `{stage['independent_completion'].get('verification_status', '미기록')}`. "
             'CHECKPOINT_ONLY는 미완료이며 후보 검증 성공이 아닙니다.', '',
             f"선정 ID: `{old.cell(result.get('selected_id', '미선정'))}` · 추천 판정: **{old.cell(decision)}**."]
    if result.get('candidate'):
        folder = Path(result['candidate'])
        try: folder = folder.relative_to(ROOT)
        except ValueError: pass
        candidate = str(folder if folder.suffix == '.zip' else folder / 'submission_files.zip')
        lines += ['', f"기록된 후보 ZIP 경로: `{old.cell(candidate)}`. 이 경로 기록과 파일 형식 검증은 점수 개선·추천 판정과 구별합니다."]
    ratio = result.get('late_W_ratio')
    if not v2.finite_number(ratio): ratio = audit.get('metrics', {}).get('ratio')
    if v2.finite_number(ratio):
        change = 100 * (ratio - 1)
        direction = '악화' if ratio > 1 else '개선' if ratio < 1 else '동일'
        lines += ['', f"후기 latest(2025년 3~5월) W 비율: **{old.number(ratio, 6)}** · 최고 제출 대비 상대 변화 "
                  f"**{old.number(change)}% ({direction})**. 이 평가는 후보·예측 고정 뒤 수행하며 결과로 재선정하지 않습니다."]
    bootstrap = audit.get('weekly_bootstrap', {}); interval = bootstrap.get('CI95')
    if isinstance(interval, list) and len(interval) == 2 and all(v2.finite_number(x) for x in interval) and interval[0] <= interval[1]:
        contains_zero = interval[0] <= 0 <= interval[1]
        lines += ['', f"후기 W 상대 변화의 주 단위 쌍체 블록 부트스트랩 95% CI: "
                  f"**[{old.number(interval[0])}%, {old.number(interval[1])}%]** · 0 {'포함' if contains_zero else '미포함'}. "
                  '고정 모델과 개발 자료에서의 선택에 조건부인 구간이며 과거 노출·다중 비교의 영향을 제거하지 않습니다.']
    elif result.get('late_targets_loaded'):
        lines += ['', '후기 쌍체 신뢰구간: 미기록. 후기 점추정만으로 개선의 안정성을 확정하지 않습니다.']
    if recommendation == 'NOT_RECOMMENDED':
        lines += ['', '**후기 개선을 확인하지 못해 이 후보를 추천하지 않습니다. ZIP 생성·검증 성공을 개선 성공으로 해석하지 마세요.**']
    if status == 'NO_QUALIFYING_RECIPE':
        lines += ['', '**적격 후보 없음은 사전에 고정한 모든 조건을 함께 통과한 설정이 없다는 뜻입니다. '
                  '일부 기간의 점추정 개선까지 없었다는 뜻은 아닙니다.**']
    return lines

def novel_stage(snapshot, old, v2):
    folder = f'analysis_outputs/{STAGE}'
    protocol = snapshot.read(folder + '/protocol.json') or {}
    configs = snapshot.read(folder + '/configs.json') or []
    import re
    if not isinstance(configs, list) or any(not isinstance(c, dict) or not isinstance(c.get('id'), str)
            or not re.fullmatch('[A-Za-z0-9_-]+', c['id']) for c in configs):
        raise ValueError('Novel configs must be a list with explicit string IDs')
    by_id = {c['id']: c for c in configs}
    if len(by_id) != len(configs):
        raise ValueError('Novel config IDs must be unique')
    state = snapshot.read(folder + '/controller_state/state.json') or {}
    manifest = snapshot.read(folder + '/controller_manifest.json') or {}
    comparisons = protocol.get('comparison_ids', {})
    rows = []
    for config in configs:
        identifier = config['id']; unit = folder + '/trials/' + identifier
        result = snapshot.read(unit + '/result.json') or {}
        receipt = snapshot.read(unit + '/receipt.json') or {}
        job = state.get('jobs', {}).get(identifier, {})
        valid_receipt = (receipt.get('status') == 'PASS' and receipt.get('id') == identifier
                         and receipt.get('config') == config and result.get('config') == config
                         and receipt.get('real_model_fits') == 1)
        status, alive = v2.job_status(job, result or None, [receipt] if receipt else [], old)
        if status == 'completed' and not valid_receipt:
            status = 'partial'
        ref_id = config.get('comparison_id', comparisons.get(identifier, ''))
        if not ref_id:
            same_family = [c for c in configs if c['id'] < identifier
                           and c.get('family', c.get('method')) == config.get('family', config.get('method'))]
            if same_family:
                ref_id = min(same_family, key=lambda c: (comparison(config, c)[1], c['id']))['id']
        if ref_id and (ref_id not in by_id or ref_id >= identifier):
            raise ValueError('Comparison must be a declared earlier config ID')
        ref = by_id.get(ref_id, {})
        changes, count, scope = comparison(config, ref) if ref else ('기준 설정', 0, '기준 설정')
        row = dict(campaign=STAGE, id=identifier, kind='deterministic_transport', status=status,
            controller_status=job.get('status', ''), family=config.get('family', config.get('method', '')),
            base_id='protected_reference', source_generation_id='renew_candidate_20261105',
            config_json=encoded(config), comparison_id=ref_id, changed_settings=changes,
            changed_setting_count=count, comparison_scope=scope, _config=config,
            coefficient_budget=config.get('budget', config.get('coefficient_budget', config.get('weight_budget'))),
            coefficient_budget_meaning='사전 고정한 계수·이동량 제한; 평가 정답으로 고른 혼합 alpha가 아님',
            primary_fit_status='학습 기간 내 진단', recent_evaluation_status='계수를 바꾸지 않은 이후 개발 기간',
            recorded_model_fits=1 if valid_receipt else 0, actual_fit_seconds=actual_fit_seconds(receipt) if valid_receipt else None,
            completed_folds=2 if status == 'completed' else 0, expected_folds=2, seed_count=0,
            expected_seed_fold_receipts=0, completed_seed_fold_receipts=0,
            started_kst=old.stamp(job.get('launched_utc')), finished_kst=old.stamp(job.get('finished_utc') or result.get('created_utc', result.get('utc'))),
            result_status=result.get('status', ''), process_identity_matches=alive,
            evidence_path=unit + '/result.json' if result else '',
            note='primary로 결정론적 계수를 한 번 학습하고 recent에 고정 적용; 새 트리·생성 모델 반복 학습이 아님.',
            model_selection_status='미평가', blend_alpha=None)
        if status == 'completed':
            row.update(eligible=result.get('eligible') if isinstance(result.get('eligible'), bool) else None,
                       metrics_json=encoded(result.get('metrics', {})),
                       gates_json=encoded(result.get('gate_checks', result.get('gates', {}))),
                       quarter_summary_json=encoded(result.get('recent_quarter_ratios', {})),
                       diagnostic_scores_json=encoded({'recent_group_ratios':result.get('recent_group_ratios', {}),
                                                       'physical_checks':result.get('physical_checks', {})}))
            row['model_selection_status'] = '개발 기준 통과' if row['eligible'] else '개발 기준 미통과'
            for fold in ('primary', 'recent'):
                candidate, reference = score_pair(result, fold)
                row[fold + '_W'] = candidate.get('W'); row[fold + '_W_pct'] = candidate.get('W_pct')
                row[fold + '_W_change_pct_vs_reference'] = old.percent_change(candidate.get('W'), reference.get('W'))
        rows.append(row)
    row_map = {r['id']: r for r in rows}
    for row in rows:
        previous = row_map.get(row['comparison_id'])
        if row['status'] == 'completed' and previous and previous['status'] == 'completed':
            for fold in ('primary', 'recent'):
                row[fold + '_W_change_pct_vs_comparison'] = old.percent_change(row.get(fold + '_W'), previous.get(fold + '_W'))
    snapshot.rows.extend(rows)
    alive = old.identity_alive(state.get('controller_identity')) if state.get('controller_identity') else None
    phase = state.get('phase', 'preparing')
    status = '종료' if phase == 'finished' else '진행 중' if alive is True else '중단·확인 필요' if state else '준비 중'
    item = dict(id=STAGE, label='새 접근: 시간·공간 운송 보정', kind='current_v3', folder=folder, rows=rows, bases=[],
        configs=configs, protocol=protocol, status=status, phase=phase, process_identity_matches=alive,
        current_job=state.get('current_job'), counts=dict(Counter(r['status'] for r in rows)), candidate_count=len(configs),
        recorded_model_fits=sum(r['recorded_model_fits'] for r in rows), eligible=sum(r.get('eligible') is True for r in rows),
        started=state.get('started_utc'), finished=state.get('finished_utc'),
        duration=v2.elapsed(state.get('started_utc'), state.get('finished_utc') or snapshot.created),
        deadline=manifest.get('deadline_utc', DEADLINE), completion=snapshot.read(folder + '/completion/result.json') or {},
        completion_audit=snapshot.read(folder + '/completion/audit.json') or {},
        independent_completion=snapshot.read(folder + '/independent_completion_check.json') or {})
    snapshot.campaigns.append(item)
    return item

def render(snapshot, old, v2, catalog, stage):
    c, n, stamp = old.cell, old.number, old.stamp
    lines = ['# OIBC 2026 · 모델 개선 실험 현황', '', f'**마지막 확인: {stamp(snapshot.created)}**. 저장 기록이며 실시간 화면은 아닙니다.', '',
        f'[전체 실험·설정 비교]({OVERVIEW}/README.md) · [전체 CSV]({OVERVIEW}/experiments.csv)', '',
        f"현재 새 접근: **{stage['status']}** · 작업 `{stage.get('current_job') or '없음'}` · 실제 프로세스 identity 일치 `{stage['process_identity_matches']}`.", '',
        f'계획 기한은 **{stamp(DEADLINE)}**, 새 탐색 중단은 **{stamp(SEARCH_STOP)}**입니다. 계획 기한과 실제 실행 시간을 구분합니다.', '',
        '## 이번에는 무엇이 다른가', '',
        '기존 288개 실험은 원래 발전량 예측에 트리 보정을 더했습니다. 새 실험은 보존된 최고 제출 예측을 출발점으로 '
        '시간·공간의 예측량 배분을 제한된 결정론적 계수로 조정합니다. 각 설정은 primary 기간에서 한 번 학습하고, '
        '그 계수를 바꾸지 않고 recent에 적용합니다. primary 결과는 학습 기간 내 진단이고 recent도 이미 노출된 개발 자료입니다.', '',
        '계수 예산(budget)은 미리 정한 이동·보정 한도이며, primary/recent 정답을 보고 최적화한 혼합 alpha와 다릅니다. '
        '트리 학습 시드 반복은 수행하지 않습니다. 비교 ID는 사전 지정값 또는 같은 실험군의 앞선 ID 중 설정 차이가 최소인 항목을 '
        '사용하고 동률은 ID로 해소합니다. 점수로 고르지 않습니다.', '',
        f'[새 실험의 설계·학습 경계·판정 기준](analysis_outputs/{STAGE}/CAMPAIGN.md)', '',
        '| 설정 키 | 뜻과 바뀌는 동작 |', '|---|---|',
        '| `family=temporal` | 하루·그룹 총발전량을 보존하며 예측 곡선의 시각별 배치를 조정합니다. |',
        '| `family=spatial` | 같은 시각의 G1·G2 합계를 보존하며 그룹 사이의 배분을 조정합니다. |',
        '| `shifts` | `[-1,1]`은 ±1시간, `[-2,-1,1,2]`는 ±1·±2시간 시나리오입니다. 양수는 같은 한국시간 날짜 안에서 뒤로 이동하며 날짜를 넘겨 순환하지 않습니다. |',
        '| `context=global` | 모든 대상 날짜·시각에 같은 계수 묶음을 적용합니다. |',
        '| `context=cloud_trend3` | 시간 재배치에서 예보 구름량의 오후 평균−오전 평균으로 계수 묶음을 나눕니다. |',
        '| `context=cloud_contrast3` | 그룹 재배치에서 같은 시각의 G1−G2 예보 구름량 차이로 계수 묶음을 나눕니다. |',
        '| 구름 구간 경계 | 사전 고정한 −10 미만 / −10~10 / 10 초과의 3구간이며 결측은 가운데 구간을 씁니다. 정답으로 경계를 고르지 않습니다. |',
        '| `budget` | 각 조건에서 이동 시나리오 혼합 비중 합계의 상한 0.10 또는 0.25입니다. 원본 예측을 최소 90% 또는 75% 남기며, 학습된 계수 자체나 별도 alpha가 아닙니다. |',
        '| `transfer_fraction=0.10` | 그룹 이동 시나리오는 두 그룹 원래 합계의 10% 이내이며 용량·비음수 조건으로 추가 제한됩니다. 최종 이동량에는 학습된 혼합 비중이 적용됩니다. |', '',
        '| ID / 비교 ID | 바뀐 설정 | 상태 | 계수 예산 | primary W 변화(학습 내) | recent W 변화(고정 이전) | 판정 |',
        '|---|---|---|---:|---:|---:|---|']
    for row in stage['rows']:
        lines.append(f"| {row['id']} / {row['comparison_id'] or '—'} | {c(row['changed_settings'])} ({row['comparison_scope']}) | "
            f"{c(old.LABELS.get(row['status'], row['status']))} | {n(row['coefficient_budget'])} | "
            f"{n(row.get('primary_W_change_pct_vs_reference'))}% | {n(row.get('recent_W_change_pct_vs_reference'))}% | {c(row['model_selection_status'])} |")
    lines += ['', '위 W 변화는 동일 기간의 보존된 최고 제출 예측 대비이며 음수일수록 좋습니다. '
              '앞선 설정과 직접 비교한 변화율은 CSV의 `*_W_change_pct_vs_comparison`에 두 결과가 정상 완료된 경우만 표시합니다.', '',
              *completion_lines(stage, old, v2), '',
              '## 실제 실행과 보존한 이전 단계', '',
              '| 단계 | 상태 | 실제 시작 → 종료 | 관측 구간 | 설정 수 | 설정 기록 | 새 학습 횟수 |',
              '|---|---|---|---:|---:|---|---:|']
    for item in snapshot.campaigns:
        if item['kind'] == 'historical': continue
        duration = item.get('duration')
        lines.append(f"| {c(item['label'])} | {c(item['status'])} | {stamp(item.get('started'))} → {stamp(item.get('finished'))} | "
            f"{n(duration / 3600 if duration is not None else None, 2)}시간 | {item['candidate_count']} | {c(item['counts'])} | {item['recorded_model_fits']} |")
    lines += ['', '관측 구간은 컨트롤러 시작·종료 간격이며 CPU가 실제로 학습한 시간과 같지 않습니다. '
        '복원·재사용은 새 학습으로 세지 않습니다. 동시에 학습 하나, CPU4/BLAS1 제한을 유지하며 보고서 생성은 학습하지 않습니다.', '',
        '## 결과를 해석할 때', '',
        'W는 `Σ SMP×k×|예측−실적|`이고 상대 변화는 `(후/전−1)×100`입니다. '
        '**모든 과거 기간은 이미 노출됐고 평가 기간도 겹칩니다.** 과거 OOF나 이번 recent 결과도 독립 홀드아웃·공식 개선 증거가 아닙니다. '
        '후기 정답은 후보와 예측 고정 후에만 감사하며 그 결과로 재선정하지 않습니다.', '',
        '이전 22시간 단계의 12개 JSON 저장 실패는 그대로 보존됩니다. 새 공간에서 복구한 요약은 새 학습 성공과 구별합니다. '
        '그 후보들의 과거 주 단위 구간 24개는 모두 0을 포함했고, 완료된 288개 실험의 최고 제출 혼합 primary 구간도 모두 0을 포함했습니다. '
        '작은 점수 차이를 확정된 개선으로 표시하지 않습니다.', '',
        f"최고 ZIP SHA256 확인: **{'일치' if snapshot.best_ok else '불일치 또는 파일 없음'}**. "
        '`submission/renew_candidate_20261105/submission_files.zip`을 보존합니다. 공식 업로드·유료 구매는 하지 않습니다.', '',
        '## 사용자 보고 공식 피드백', '', '| 후보 | 사용자 보고 점수 | 근거 범위 |', '|---|---:|---|']
    for feedback in catalog.get('official_feedback', []):
        lines.append(f"| {c(feedback['label'])} | {feedback['score']:,} | 사용자 보고, 직접 조회 아님; {c(feedback.get('note', ''))} |")
    lines += ['', '새 공식 점수는 추정하지 않습니다. 위 과거 피드백과 새 개발 검증 수치를 구별합니다.', '',
              '## 전체 연구 이력', '', '| 연구 묶음 | 기록 수 | 상태 |', '|---|---:|---|']
    for item in snapshot.campaigns:
        lines.append(f"| {c(item['label'])} | {len(item['rows']) + len(item.get('bases', []))} | {c(item.get('status', '과거 기록'))} |")
    lines += ['', '36개 과거 연구군과 완료된 10h·22h·23kst 기록을 함께 보존합니다. 행 수는 독립 모델 수나 성공 횟수가 아닙니다.', '',
        f'[이전 23kst 보고서]({PREVIOUS_OVERVIEW}/README.md) · [기존 제출 파이프라인](submission/README.md)', '']
    if snapshot.warnings: lines += ['확인 범위 제한: ' + '; '.join(snapshot.warnings), '']
    fields = list(dict.fromkeys([*old.FIELDS, *v2.EXTRA_FIELDS, *EXTRA_FIELDS]))
    csvs = {path.replace(v2.OVERVIEW, OVERVIEW, 1): data for path, data in v2.csv_outputs(snapshot.rows, fields).items()}
    detail = ['# 전체 연구·실험 현황', '', f'확인: **{stamp(snapshot.created)}**.', '', '[요약](../../README.md)', '',
              '정상 완료된 동일 기간 결과만 앞선 고정 설정과 비교합니다. 과거 시드·복원·진단·실패·미실행 항목을 유지합니다.', '']
    detail += [f'- [{Path(path).name}]({Path(path).name})' for path in csvs]
    for item in snapshot.campaigns:
        detail += ['', f"## {c(item['label'])}", '', '| ID / 종류 | 상태 | 기초 / 비교 | 설정 변화 | primary / recent W_pct | 새 학습 | 판정·근거 |', '|---|---|---|---|---:|---:|---|']
        for row in item['rows'] + item.get('bases', []):
            score = f"{n(row.get('primary_W_pct'))} / {n(row.get('recent_W_pct'))}"
            if row.get('kind') == 'historical_record': score = f"{c(row.get('metric_name', ''))}: {n(row.get('metric_value'))}"
            detail.append(f"| {c(row['id'])} / {c(row['kind'])} | {c(old.LABELS.get(row.get('status'), row.get('status', '')))} | "
                f"{c(row.get('base_id', ''))} / {c(row.get('comparison_id', ''))} | {c(row.get('changed_settings', ''))} ({c(row.get('comparison_scope', ''))}) | "
                f"{score} | {row.get('recorded_model_fits', '—')} | {c(row.get('model_selection_status', row.get('note', '')))} "
                f"{snapshot.link(row.get('evidence_path', ''), '근거', prefix='../../')} |")
    return {'README.md': '\n'.join(lines).encode(), f'{OVERVIEW}/README.md': '\n'.join(detail).encode(), **csvs}

def check_ownership(root, proposed):
    root = Path(root); previous = root / OVERVIEW / 'snapshot_manifest.json'
    if previous.exists():
        hashes = json.loads(previous.read_text()).get('outputs_sha256', {})
        if 'README.md' not in hashes: raise ValueError('Prior v3 root ownership missing')
        for path, expected in hashes.items():
            if path != 'README.md' and not path.startswith(OVERVIEW + '/'):
                raise ValueError('Prior output escaped v3 scope')
            if not (root / path).is_file() or sha((root / path).read_bytes()) != expected:
                raise ValueError('Manual generated-output edit preserved: ' + path)
    else:
        prior = json.loads((root / PREVIOUS_OVERVIEW / 'snapshot_manifest.json').read_text())
        expected = prior.get('outputs_sha256', {}).get('README.md')
        if not expected or sha((root / 'README.md').read_bytes()) != expected:
            raise ValueError('Initial v3 migration requires unchanged v2 root README')
        hashes = {'README.md': expected}
    for path in proposed:
        if (root / path).exists() and path not in hashes:
            raise ValueError('Unowned output would be overwritten: ' + path)
    if set(hashes) - set(proposed): raise ValueError('Output set shrank; preserve prior files')

def build(root=ROOT):
    root = Path(root).resolve(); v2 = load_v2(root); old = v2.load_old(root); snapshot = old.Snapshot(root)
    for path in PINS: snapshot.raw(path)
    catalog = snapshot.read(v2.CATALOG, required=True)
    if len(catalog['campaigns']) != 36: raise ValueError('Historical catalog must keep 36 groups')
    snapshot.history(catalog); snapshot.current(old.OLD, '기존 10시간 단계'); snapshot.current(old.NEW, '기존 22시간 단계')
    v2.new_stage(snapshot, old); stage = novel_stage(snapshot, old, v2)
    best = root / 'submission/renew_candidate_20261105/submission_files.zip'
    snapshot.best_ok = best.is_file() and sha(best.read_bytes()) == old.BEST_SHA
    outputs = render(snapshot, old, v2, catalog, stage)
    if any(len(data) > LIMIT for data in outputs.values()): raise ValueError('Public report exceeds 2MiB')
    check_ownership(root, outputs)
    sources = {**PINS}
    for name in ['update_readme.py', 'publish_readme.py', 'test_update_readme.py', 'test_publish_readme.py', 'README.md']:
        path = 'submission/research_reporting_v3/' + name
        if (root / path).is_file(): sources[path] = sha((root / path).read_bytes())
    digest = sha(encoded({'inputs': snapshot.inputs, 'source_sha256': sources, 'created': snapshot.created,
                          'process_identity_matches': stage['process_identity_matches']}).encode())
    manifest = dict(schema_version=3, created_utc=snapshot.created, snapshot_id=digest[:16], source_snapshot_sha256=digest,
        publisher_sha256=PUBLISHER_SHA, source_sha256=sources, outputs_sha256={p:sha(data) for p,data in outputs.items()},
        output_bytes={p:len(data) for p,data in outputs.items()}, experiment_rows=len(snapshot.rows), historical_campaigns=36,
        current_counts={x['id']:x['counts'] for x in snapshot.campaigns if x['kind'] != 'historical'}, new_stage=STAGE,
        deadline_utc=DEADLINE, search_stop_utc=SEARCH_STOP, model_fits=0, network_requests=0,
        all_history_previously_exposed=True, protected_best_sha256_matches=snapshot.best_ok)
    return outputs, manifest, old

def generate(root=ROOT):
    root = Path(root).resolve(); directory = root / OVERVIEW; directory.mkdir(parents=True, exist_ok=True)
    with (directory / '.generation.lock').open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        outputs, manifest, old = build(root); check_ownership(root, outputs)
        for path,data in outputs.items(): old.atomic(root / path, data)
        old.atomic(directory / 'snapshot_manifest.json', (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode())
    return manifest

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    print(json.dumps(build(args.root)[1] if args.check else generate(args.root), ensure_ascii=False, indent=2))
