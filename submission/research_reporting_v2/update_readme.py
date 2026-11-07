#!/usr/bin/env python3
"""Render the new campaign and retained history from metadata; never fit or publish."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OVERVIEW = 'analysis_outputs/experiment_overview_v2'
STAGE = 'research_23kst_20261108'
DEADLINE = '2026-11-08T14:00:00Z'
SEARCH_STOP = '2026-11-08T12:00:00Z'
LIMIT = 2 * 1024 * 1024
OLD_REPORTER = 'submission/research_reporting/update_readme.py'
CATALOG = 'submission/research_reporting/history_catalog.json'
PINS = {
    OLD_REPORTER: '651be8197f8f7784cb7d90f27ab9536d50c835473d5cea324822c2f094863f10',
    CATALOG: '0e3fdbb59d52290af2e92e9491d13160fe2a809723529e6d6defb2fa0f2518d1',
}
PUBLISHER_SHA = '89d2e4276195847792b7cf31d5d22339fee0a8bd0fb904110a38e996b51ea109'
EXTRA_FIELDS = ['source_campaign', 'source_trial_id', 'seed_count', 'completed_seed_fold_receipts',
                'expected_seed_fold_receipts', 'actual_fit_seconds', 'job_elapsed_seconds',
                'quarter_summary_json', 'annual_summary_json', 'gates_json', 'recovered',
                'model_selection_status', 'process_identity_matches', 'diagnostic_scores_json', 'result_status']
TERMINAL_FAILURES = {'failed', 'time_limit', 'stopped', 'interrupted', 'skipped_dependency',
                     'budget_reserved', 'deferred_budget', 'blocked_ambiguous_launch'}
FINALIZATION_OUTCOMES = {'EXPORTED_UNSCORED_CANDIDATE', 'NO_QUALIFYING_RECIPE',
                         'INSUFFICIENT_COMPLETED_COVERAGE', 'ENSEMBLE_GATE_FAILED'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_old(root):
    for relative, expected in PINS.items():
        if sha((root / relative).read_bytes()) != expected:
            raise ValueError(f'Pinned historical reporting source changed: {relative}')
    spec = importlib.util.spec_from_file_location('oibc_reporting_v1_pinned', root / OLD_REPORTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def encoded_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def elapsed(start, end):
    if not start or not end:
        return None
    try:
        return max(0.0, (datetime.fromisoformat(end.replace('Z', '+00:00')) -
                         datetime.fromisoformat(start.replace('Z', '+00:00'))).total_seconds())
    except (ValueError, TypeError):
        return None


def job_status(job, result, receipts, old, finalization=False):
    """A stale running string is not evidence that the matching process lives."""
    state = job.get('status', '')
    identity = job.get('wrapper_identity') or job.get('identity') or job.get('process_identity')
    alive = old.identity_alive(identity) if identity else None
    if state in TERMINAL_FAILURES:
        return state, alive
    accepted = {'PASS', 'RECOVERED_DIAGNOSTIC'} | (FINALIZATION_OUTCOMES if finalization else set())
    if result and result.get('status') in accepted:
        return ('finalizing' if state in {'running', 'launching'} and alive is True else 'completed'), alive
    if state in {'running', 'launching'}:
        return ('running' if alive is True else 'unknown'), alive
    if receipts:
        return 'partial', alive
    return ('pending' if state in {'', 'pending'} else 'unknown'), alive


def csv_outputs(rows, fields, limit=LIMIT):
    """Split only between complete UTF-8 CSV records, with a header in every part."""
    def record(values):
        out = io.StringIO(newline='')
        csv.writer(out, lineterminator='\n').writerow(values)
        return out.getvalue().encode('utf-8')
    header = b'\xef\xbb\xbf' + record(fields)
    chunks, current = [], bytearray(header)
    for row in rows:
        line = record(['' if row.get(key) is None else row.get(key, '') for key in fields])
        if len(header) + len(line) > limit:
            raise ValueError('A single metadata CSV row exceeds the publication limit')
        if len(current) + len(line) > limit:
            chunks.append(bytes(current))
            current = bytearray(header)
        current.extend(line)
    chunks.append(bytes(current))
    if len(chunks) > 65:
        raise ValueError('CSV exceeds the 64 additional-part publication limit')
    return {f'{OVERVIEW}/' + ('experiments.csv' if n == 0 else f'experiments_part_{n:03d}.csv'): data
            for n, data in enumerate(chunks)}


def locate_job(state, identifier, kind):
    jobs = state.get('jobs', {})
    if kind == 'new_calibration' and identifier in jobs:
        return jobs[identifier]
    if kind == 'recovered_result':
        return jobs.get('recover', {})
    prefixes = ('recover_', 'recovered_') if kind == 'recovered_result' else ('validate_', 'validation_')
    for name in [*(prefix + identifier for prefix in prefixes), identifier]:
        if name in jobs:
            return jobs[name]
    return {}


def record_receipts(snapshot, unit, seeds, folds):
    records = []
    allowed_seeds = {f'seed{seed}' for seed in seeds} & {'seed0', 'seed1', 'seed2'}
    allowed_folds = set(folds)
    for path in sorted((snapshot.root / unit).glob('seed*/*/receipt.json')):
        relative_parts = path.relative_to(snapshot.root / unit).parts
        if any('.interrupted.' in part or part.startswith('.') for part in relative_parts):
            continue
        if path.parent.parent.name not in allowed_seeds or path.parent.name not in allowed_folds:
            continue
        value = snapshot.read(path.relative_to(snapshot.root))
        if value and value.get('status') == 'PASS':
            records.append((path.parent.parent.name, path.parent.name, value))
    return records


def new_stage(snapshot, old):
    folder = f'analysis_outputs/{STAGE}'
    state = snapshot.read(f'{folder}/controller_state/state.json') or {}
    manifest = snapshot.read(f'{folder}/controller_manifest.json') or {}
    protocol = snapshot.read(f'{folder}/protocol.json') or {}
    configs = snapshot.read(f'{folder}/configs.json') or []
    if not isinstance(configs, list):
        raise ValueError('New campaign configs.json must be a list')
    bases_value = snapshot.read(f'{folder}/bases.json') or []
    bases = {x['id']: x for x in bases_value} if isinstance(bases_value, list) else bases_value
    jobs_value = snapshot.read(f'{folder}/jobs.json') or manifest.get('jobs', [])
    if isinstance(jobs_value, dict):
        jobs_value = jobs_value.get('jobs', [])
    validation_ids = {j['id'][len('validate_'):] for j in jobs_value
                      if isinstance(j, dict) and j.get('id', '').startswith('validate_')}
    validation_ids.update(protocol.get('recovered_ids', []))
    old_configs = {r['id']: r.get('_config', {}) for campaign in snapshot.campaigns if campaign['id'] == old.NEW
                   for r in campaign['rows']}
    # The engine's separate recovery and seed validation results never overwrite old failures.
    units = [(c['id'], 'new_calibration', c, f"{folder}/trials/{c['id']}") for c in configs]
    for directory, kind in [('recovered', 'recovered_result'), ('validation', 'seed_validation')]:
        identifiers = {p.parent.name for p in (snapshot.root / folder / directory).glob('*/result.json')}
        identifiers.update(p.name for p in (snapshot.root / folder / directory).glob('n*') if p.is_dir())
        identifiers.update(validation_ids)
        if isinstance(jobs_value, list):
            for job in jobs_value:
                argv = job.get('argv', [])
                if any(word in argv for word in (('recover',) if directory == 'recovered' else ('validate', 'validation'))):
                    if '--id' in argv:
                        identifiers.add(argv[argv.index('--id') + 1])
        for identifier in sorted(identifiers):
            unit = f'{folder}/{directory}/{identifier}'
            result = snapshot.read(f'{unit}/result.json') or {}
            config = result.get('config') or old_configs.get(identifier) or {'id': identifier, 'source_trial_id': identifier}
            units.append((identifier, kind, config, unit))
    data_rows = []
    folds = protocol.get('folds', {})
    fold_names = list(folds) if isinstance(folds, dict) else [x['id'] for x in folds] if isinstance(folds, list) else []
    for identifier, kind, config, unit in units:
        result = snapshot.read(f'{unit}/result.json')
        seeds = [1, 2] if kind == 'seed_validation' else protocol.get('search_seeds', [0, 1, 2])
        expected_folds = ['primary', 'recent'] if kind == 'seed_validation' else fold_names
        if kind == 'recovered_result':
            seeds, expected_folds = [], []
        receipts = record_receipts(snapshot, unit, seeds, expected_folds)
        job = locate_job(state, identifier, kind)
        status, alive = job_status(job, result, receipts, old)
        completed = sum(all((f'seed{s}', fold) in {(a, b) for a, b, _ in receipts} for s in seeds)
                        for fold in expected_folds) if seeds else 0
        actual_fits = sum(r.get('real_model_fits', r.get('actual_model_fits', 0)) for _, _, r in receipts)
        actual_seconds = sum(r.get('elapsed_seconds', 0) for _, _, r in receipts)
        note = ('과거 결과의 타입 변환·감사 복원. 새 학습 없이 옛 실패 행을 보존하며 진단으로만 표시.' if kind == 'recovered_result' else
                '이전 실패 후보의 추가 시드 진단; 공통 분기 평가가 없어 새 후보로 자동 채택하지 않음.' if kind == 'seed_validation' else
                '고정한 새 설정의 시간 순서 평가; 기존 실패 후보 복원과 별도 실험.')
        if status == 'unknown' and job.get('status') in {'running', 'launching'}:
            note += ' 실행 문자열은 있으나 PID·시작 시각·부팅 식별자로 현재 실행을 확인하지 못함.'
        row = dict(campaign=STAGE, id=identifier, kind=kind, status=status,
                   controller_status=job.get('status', ''), completed_folds=completed,
                   expected_folds=len(expected_folds) if expected_folds else None,
                   seed_count=len(seeds), completed_seed_fold_receipts=len(receipts),
                   expected_seed_fold_receipts=len(seeds) * len(expected_folds) if seeds else 0,
                   recorded_model_fits=actual_fits, actual_fit_seconds=actual_seconds,
                   job_elapsed_seconds=elapsed(job.get('launched_utc'), job.get('finished_utc') or snapshot.created),
                   started_kst=old.stamp(job.get('launched_utc')),
                   finished_kst=old.stamp(job.get('finished_utc') or (result or {}).get('utc')),
                   evidence_path=f'{unit}/result.json' if result else '', note=note,
                   base_id=config.get('base_id', ''), source_generation_id=bases.get(config.get('base_id'), {}).get('source_id', ''),
                   source_campaign=old.NEW if kind != 'new_calibration' else '',
                   source_trial_id=identifier if kind != 'new_calibration' else '',
                   config_json=encoded_json(config), _config=config,
                   process_identity_matches=alive, recovered=kind == 'recovered_result',
                   model_selection_status='복원은 새 후보 채택이 아님' if kind == 'recovered_result' else '미평가')
        # Report terminal results only; partial/failed receipts are counts, never a successful score.
        if status == 'completed' and result:
            if not receipts and kind != 'recovered_result':
                value = result.get('real_model_fits', result.get('actual_model_fits'))
                if isinstance(value, int) and not isinstance(value, bool):
                    row['recorded_model_fits'] = value
                    row['note'] += ' 학습 횟수는 최종 결과 영수증에서 읽음.'
            if kind == 'new_calibration':
                row['eligible'] = result.get('eligible') if isinstance(result.get('eligible'), bool) else None
                row['model_selection_status'] = '개발 기준 통과' if row['eligible'] is True else '개발 기준 미통과' if row['eligible'] is False else '판정 미기록'
            else:
                row['eligible'] = None
                row['model_selection_status'] = '추가 시드 진단 전용·후보 자동 채택 없음' if kind == 'seed_validation' else '옛 실패 결과 복원·새 후보 채택 아님'
                row['audit_gate_pass'] = result.get('previous_scientific_gate')
                row['diagnostic_scores_json'] = encoded_json(result.get('scores', {}))
            row['quarter_summary_json'] = encoded_json(result.get('quarter_summary', {}))
            row['annual_summary_json'] = encoded_json(result.get('annual_summary', {}))
            row['_quarter_summary'] = result.get('quarter_summary', {})
            row['_annual_summary'] = result.get('annual_summary', {})
            row['gates_json'] = encoded_json(result.get('gates', result.get('gate', {})))
            blend = result.get('blend', {})
            row['blend_alpha'] = blend.get('alpha', result.get('frozen_alpha', result.get('alpha')))
            for fold in ('primary', 'recent'):
                record = result.get('folds', result.get('scores', {})).get(fold, {})
                score = record.get('score', record)
                row[f'{fold}_W'], row[f'{fold}_W_pct'] = score.get('W'), score.get('W_pct')
                row[f'{fold}_W_change_pct_vs_raw'] = old.percent_change(score.get('W'), record.get('raw_score', {}).get('W'))
                pair = blend.get('scores', {}).get(fold, {})
                row[f'{fold}_blend_W_change_pct'] = old.percent_change(pair.get('blend', {}).get('W'), pair.get('reference', {}).get('W'))
        data_rows.append(row)
        snapshot.rows.append(row)
    for index, row in enumerate(data_rows):
        earlier = [r for r in data_rows[:index] if r['kind'] == row['kind'] and r['base_id'] == row['base_id']]
        compare = min(earlier, key=lambda r: (len(old.config_changes(r['_config'], row['_config'])), r['id'])) if earlier else row
        diff = old.config_changes(compare['_config'], row['_config'])
        row.update(comparison_id=compare['id'], changed_settings=old.describe_changes(diff), changed_setting_count=len(diff),
                   comparison_scope='기준 자체' if compare is row else '단일 설정 차이' if len(diff) == 1 else '여러 설정 동시 변경')
        if row['status'] == compare['status'] == 'completed':
            for fold in ('primary', 'recent'):
                row[f'{fold}_W_change_pct_vs_comparison'] = old.percent_change(row.get(f'{fold}_W'), compare.get(f'{fold}_W'))
    prep_rows = []
    prep_specs = [(base_id, 'reused_oof_inputs', f'{folder}/bases/{base_id}/result.json') for base_id in bases]
    prep_specs.append(('assemble', 'assembled_search_inputs', f'{folder}/assemble/result.json'))
    for identifier, kind, path in prep_specs:
        result = snapshot.read(path)
        job = state.get('jobs', {}).get(identifier, {})
        origin_receipts = []
        if identifier in bases:
            for origin_path in sorted((snapshot.root / folder / 'bases' / identifier / 'origins').glob('*/receipt.json')):
                if any('.interrupted.' in part for part in origin_path.parts):
                    continue
                value = snapshot.read(origin_path.relative_to(snapshot.root))
                if value and value.get('status') == 'PASS':
                    origin_receipts.append(value)
        status, alive = job_status(job, result, origin_receipts, old)
        count = sum(r.get('real_model_fits', 0) for r in origin_receipts) if origin_receipts else (result or {}).get('real_model_fits', 0)
        row = dict(campaign=STAGE, id=identifier, kind=kind, status=status,
                   controller_status=job.get('status', ''), recorded_model_fits=count,
                   evidence_path=path if result else '', base_id=identifier if identifier in bases else '',
                   source_generation_id=bases.get(identifier, {}).get('source_id', ''),
                   process_identity_matches=alive, started_kst=old.stamp(job.get('launched_utc')),
                   finished_kst=old.stamp(job.get('finished_utc') or (result or {}).get('utc')),
                   note='기존 모델은 재사용하고 필요한 이후 학습 마감일 모델만 새 학습. 원점별 영수증의 새 학습만 합산; 후보 채택 결과가 아님.')
        prep_rows.append(row)
        snapshot.rows.append(row)
    snapshot.read(f'{folder}/shared/search_data_manifest.json')
    completion = snapshot.read(f'{folder}/completion/result.json')
    budget_stop = snapshot.read(f'{folder}/completion/budget_stop.json') if not completion else None
    completion_job = state.get('jobs', {}).get('completion', {})
    completion_receipts = []
    for path in sorted((snapshot.root / folder / 'completion').glob('**/receipt.json')):
        if any('.interrupted.' in part for part in path.parts):
            continue
        record = snapshot.read(path.relative_to(snapshot.root))
        if record and record.get('status') == 'PASS':
            completion_receipts.append(record)
    if completion or budget_stop or completion_receipts or completion_job:
        completion_status, completion_alive = job_status(completion_job, completion, completion_receipts, old, finalization=True)
        if budget_stop and completion_job.get('status') not in TERMINAL_FAILURES:
            completion_status = 'time_limit' if budget_stop.get('status') == 'TIME_BUDGET_EXHAUSTED' else 'partial'
        result_status = (completion or budget_stop or {}).get('status', '')
        completion_row = dict(campaign=STAGE, id='completion', kind='finalization', status=completion_status,
                              controller_status=completion_job.get('status', ''),
                              process_identity_matches=completion_alive, result_status=result_status,
                              started_kst=old.stamp(completion_job.get('launched_utc')),
                              finished_kst=old.stamp(completion_job.get('finished_utc') or (completion or budget_stop or {}).get('utc')),
                              job_elapsed_seconds=elapsed(completion_job.get('launched_utc'), completion_job.get('finished_utc') or snapshot.created),
                              recorded_model_fits=sum(r.get('real_model_fits', 0) for r in completion_receipts),
                              evidence_path=f'{folder}/completion/result.json' if completion else f'{folder}/completion/budget_stop.json' if budget_stop else '',
                              note=f'최종 처리 결과: {result_status or "미기록"}. '
                                   + ('체크포인트만 보존; 후보 검증 성공이 아님. ' if budget_stop else '')
                                   + '작업 종료·후보 생성·독립 검증·공식 제출은 서로 다른 상태이며 자동으로 추정하지 않음.')
        prep_rows.append(completion_row)
        snapshot.rows.append(completion_row)
    alive = old.identity_alive(state.get('controller_identity')) if state.get('controller_identity') else None
    heartbeat_age = elapsed(state.get('heartbeat_utc'), snapshot.created)
    stopped = (snapshot.root / folder / 'controller_state/STOP').exists()
    phase = state.get('phase')
    status = ('명시적 중단' if stopped else '종료' if phase == 'finished' else
              '진행 중' if alive is True and heartbeat_age is not None and heartbeat_age <= 120 else
              '프로세스 확인·상태 갱신 지연' if alive is True else '프로세스 확인 불가' if state else '준비·시작 대기')
    item = dict(id=STAGE, label='11월 8일 23시 KST까지 연장 단계', folder=folder, kind='current_v2',
                rows=data_rows, bases=prep_rows, configs=configs, protocol=protocol, status=status,
                counts=dict(Counter(r['status'] for r in data_rows)), candidate_count=len(configs),
                recorded_model_fits=sum(r['recorded_model_fits'] for r in [*data_rows, *prep_rows]),
                eligible=sum(r.get('eligible') is True for r in data_rows if r['kind'] == 'new_calibration'),
                started=state.get('started_utc'), finished=state.get('finished_utc'),
                duration=elapsed(state.get('started_utc'), state.get('finished_utc') or snapshot.created),
                current_job=state.get('current_job'), heartbeat=state.get('heartbeat_utc'),
                heartbeat_age_seconds=heartbeat_age, process_identity_matches=alive, phase=phase,
                deadline=manifest.get('deadline_utc', DEADLINE), search_stop=SEARCH_STOP,
                completion=completion or budget_stop,
                independent_completion=snapshot.read(f'{folder}/independent_completion_check.json'))
    snapshot.campaigns.append(item)
    return item


def render(snapshot, old, catalog, stage):
    c, n, stamp = old.cell, old.number, old.stamp
    current = [x for x in snapshot.campaigns if x['kind'] in {'current', 'current_v2'}]
    lines = ['# OIBC 2026 · 모델 개선 실험 현황', '', f'**마지막 확인: {stamp(snapshot.created)}**. 주기적으로 저장하는 상태 기록이며 실시간 화면은 아닙니다.', '',
             f'[전체 실험과 설정 비교]({OVERVIEW}/README.md) · [전체 CSV 첫 파일]({OVERVIEW}/experiments.csv)', '',
             f"현재 연장 단계: **{stage['status']}**. 실행 중 작업: `{stage.get('current_job') or '없음'}`. "
             f"식별자가 일치하는 컨트롤러: `{stage['process_identity_matches']}`.", '',
             f'계획 마감은 **{stamp(DEADLINE)}**, 새 탐색 중단은 **{stamp(SEARCH_STOP)}**입니다. 마지막 2시간은 검증·최종 학습·산출물 정리에 예약합니다. '
             '이는 실행 계획이며 실제 학습 시간이나 완료 횟수를 뜻하지 않습니다.', '',
             '## 현재 실행과 완료 근거', '',
             '| 단계 | 실제 상태 | 기록 시작 → 종료 | 관측 실행 경과 | 후보 계획 | 기록 상태 | 영수증의 새 모델 학습 |',
             '|---|---|---|---:|---:|---|---:|']
    for item in current:
        duration = item.get('duration')
        lines.append(f"| {c(item['label'])} | {c(item['status'])} | {stamp(item.get('started'))} → {stamp(item.get('finished'))} | "
                     f"{n(duration / 3600 if duration is not None else None, 2)}시간 | {item['candidate_count']} | {c(item['counts'])} | {item['recorded_model_fits']} |")
    lines += ['', '경과 시간은 컨트롤러 기록의 시작·종료 간격입니다. 새 학습 횟수는 완료 영수증의 합이며, 재사용 모델·결과 복원을 새 학습으로 세지 않습니다. '
              '실패·부분 결과는 정상 완료와 별도로 보존합니다. CPU 4개에서 동시에 한 학습 작업을 실행하며, 이 문서 생성은 학습·추론·업로드를 시작하지 않습니다.', '',
              '## 새 단계에서 무엇을 비교하는가', '',
              '기존 22시간 단계의 저장 실패 결과 복원, 그 후보의 추가 시드 확인, 새 보정 설정 탐색을 각각 별도 행으로 기록합니다. '
              '복원된 결과가 과거 개발 기준을 통과해도 새 후보 채택이나 공식 점수 개선으로 표시하지 않습니다.', '',
              f"현재 고정 설정 파일에서 확인한 새 설정은 **{len(stage['configs'])}개**입니다. 전체 설정값과 비교 ID는 CSV의 `config_json`, `changed_settings`, "
              '`comparison_id`에 있습니다. 비교 대상은 동일 기초 모델의 앞선 설정 중 차이가 가장 작은 ID로 고정하며 점수로 고르지 않습니다. '
              '여러 키가 함께 바뀐 비교를 한 변수의 효과로 해석하지 않습니다.', '',
              '| 새 설정 | 비교하는 내용 |', '|---|---|',
              '| `features` | `weather_spread`와 `rich_spread`: 날씨·계절 또는 rich100 입력에 같은 학습 마감일에서 만든 네 기초 모델 예측의 차이·분산을 추가합니다. 실제 사용 열은 영수증을 확인합니다. |',
              '| `weighting` | `money`는 기존 366일 OOF 범위, `horizon`은 평가 길이에 맞춘 범위(분기 92일/연간 366일), `horizon_groupseason`은 여기에 그룹×계절 가중치 총량 균등화를 추가합니다. 마지막 방식은 학습 목적을 바꾸며 공식 평가 산식은 유지합니다. |',
              '| `group_mix` | 0은 통합 보정 모델, 0.5는 통합·그룹별 모델 반반, 1은 그룹별 모델만 사용합니다. 계수는 정해진 값이며 점수로 연속 조정하지 않습니다. |',
              '| `regularization` / `anchor_penalty` | small / medium / large / anchored의 고정 규제 조합. anchored는 같은 입력에 보정량 0인 학습 행을 원래 가중치의 0.25배로 추가해 보정을 억제합니다. |',
              '| `base_id` | b00 / b02 / b09 / b22. 기존 모델을 재사용하고 2024년 9·12월 원점은 필요한 경우 새로 학습합니다. 재사용 추론은 학습에서 제외하고 각 영수증의 real_model_fits만 합산합니다. |', '',
              '새 설정은 3개 시드와 연간 5개·분기 11개 기간으로 계획됩니다. 11개 분기 평가 구간은 서로 겹치지 않지만, 연간 5개 구간은 서로 및 분기 구간과 겹칩니다. '
              '모든 구간은 이미 노출된 과거 자료입니다. 기존 실패 후보의 추가 시드 진단은 primary/recent만 확인하므로 '
              '이 공통 분기 기준을 통과한 후보와 동등하게 취급하지 않습니다. 실제 고정 목록은 protocol/configs 파일을 기준으로 표시합니다.', '',
              '새 탐색의 개발 기준 통과 기록: **' + str(stage['eligible']) + '개**. 추가 시드·최종 후보 검증·실제 제출은 별도 단계입니다.', '',
              '## 점수와 평가 자료의 한계', '',
              'W는 `Σ SMP×k×|그룹 예측−실적|`, W_pct는 `100×W/Σ SMP×k×실적`이며 낮을수록 좋습니다. '
              'CSV의 W 상대 변화는 `(후/전−1)×100`입니다. 서로 다른 기간·지표를 단순 순위로 합치지 않습니다. '
              '과거 `W_over_revenue` 원본은 비율이고 구성 `gap_pct`는 W_pool 대비 초과 오차율입니다.', '',
              '**모든 과거 기간은 이미 노출된 개발 자료입니다.** 시간 순서를 지킨 OOF도 새로운 독립 검증셋이라는 뜻은 아닙니다. '
              '이번 탐색의 선택에는 2025년 3~5월 정답을 사용하지 않으며, 최종 고정 후 감사가 있더라도 이전 노출 이력을 밝힙니다. '
              '혼합 alpha를 primary에서 정한 경우 primary 개선은 계수 선택 자료에서의 수치이고 recent에 그대로 전달한 결과를 별도로 확인합니다.', '',
              '12개는 기존 단계에서 JSON 결과 저장에 실패한 실험이며, 옛 기록은 계속 실패 상태로 보존합니다. 새 단계의 복원·추가 시드 진단이 이미 완료됐다는 뜻은 아닙니다. '
              '이 12개 옛 실패 기록의 primary/recent 주 단위 조건부 구간 총 24개는 모두 0을 포함했습니다. '
              '이 결과를 통계적으로 확정된 개선이나 독립 테스트 증거로 바꾸어 해석하지 않습니다.', '',
              '## 사용자 보고 공식 피드백', '', '| 후보 | 사용자 보고 점수 | 근거 범위 |', '|---|---:|---|']
    for feedback in catalog.get('official_feedback', []):
        lines.append(f"| {c(feedback['label'])} | {feedback['score']:,} | 사용자 보고, 직접 조회 아님; {c(feedback.get('note', ''))} |")
    lines += ['', f"보존 대상 최고 ZIP의 SHA256 확인: **{'일치' if snapshot.best_ok else '불일치 또는 파일 없음'}**. "
              '`submission/renew_candidate_20261105/submission_files.zip`은 새 탐색 결과와 별도로 보존합니다. 새 공식 점수·업로드는 이 보고서에서 추정하지 않습니다.', '',
              '## 보존한 전체 연구 이력', '', '| 캠페인 | 근거 기록 수 | 종류·상태 |', '|---|---:|---|']
    for item in snapshot.campaigns:
        lines.append(f"| {c(item['label'])} | {len(item['rows']) + len(item.get('bases', []))} | {c(item.get('status', '과거 기록'))} |")
    lines += ['', '과거 36개 연구 묶음과 기존 10시간·22시간 단계는 모두 남겨 두었습니다. 행 수에는 기준값·재채점·진단·미실행 계획이 포함되므로 '
              '독립 모델 수나 성공 횟수가 아닙니다. 옛 문서의 당시 최상 표현은 현재 최고 후보를 뜻하지 않습니다.', '',
              '[기존 제출 파이프라인](submission/README.md) · [이전 보고서 스냅샷](analysis_outputs/experiment_overview/README.md)', '']
    if snapshot.warnings:
        lines += ['확인 범위 제한: ' + '; '.join(snapshot.warnings), '']
    # Keep current settings and recent completed measurements near the top of the overview.
    live = next((r for r in stage['rows'] if r['id'] == stage.get('current_job') and r['kind'] == 'new_calibration'), None)
    observation = ['## 지금 확인하는 설정과 최근 완료 결과', '']
    if live:
        observation += [f"`{live['id']}` / 기초 `{live['base_id']}→{live['source_generation_id']}`: {c(live['config_json'])}", '',
                        f"고정 비교 ID `{live['comparison_id']}`: **{c(live['changed_settings'])}** ({c(live['comparison_scope'])}).", '']
    else:
        observation += ['현재 실행 중인 새 설정을 식별하지 못했거나 준비·진단·종료 단계입니다. 계획 항목을 학습 중이라고 표시하지 않습니다.', '']
    latest = sorted([r for r in stage['rows'] if r['kind'] == 'new_calibration' and r['status'] == 'completed'],
                    key=lambda r: (r.get('finished_kst', ''), r['id']), reverse=True)[:3]
    observation += ['아래는 완료 시각이 가장 최근인 최대 3개 결과입니다. 성능으로 골라낸 후보가 아니며, 채택 여부는 고정 기준과 별도 최종 검증에 따릅니다.', '',
                    '| ID / 비교 ID | 바뀐 설정 | primary / recent W_pct | 기초 대비 W 변화 primary / recent | 분기 평균 W 비율 | alpha / 최고 제출 대비 혼합 W 변화 | 개발 기준 |',
                    '|---|---|---:|---:|---:|---|---|']
    for row in latest:
        observation.append(f"| {row['id']} / {row['comparison_id']} | {c(row['changed_settings'])} ({c(row['comparison_scope'])}) | "
                           f"{n(row.get('primary_W_pct'))} / {n(row.get('recent_W_pct'))} | "
                           f"{n(row.get('primary_W_change_pct_vs_raw'))}% / {n(row.get('recent_W_change_pct_vs_raw'))}% | "
                           f"{n(row.get('_quarter_summary', {}).get('mean_ratio'), 6)} | {n(row.get('blend_alpha'), 6)} / "
                           f"{n(row.get('primary_blend_W_change_pct'))}% / {n(row.get('recent_blend_W_change_pct'))}% | {c(row['model_selection_status'])} |")
    if not latest:
        observation += ['| 아직 정상 완료된 새 설정 없음 | — | — | — | — | — | 미평가 |']
    observation += ['', f"최종 처리 기록: `{(stage.get('completion') or {}).get('status', '미기록')}` · "
                    f"독립 최종 검증: `{(stage.get('independent_completion') or {}).get('status', '미기록')}`. "
                    '과거 실패 결과 복원과 추가 시드 진단은 이 새 설정 표에 섞지 않습니다.', '']
    insert_at = lines.index('## 점수와 평가 자료의 한계')
    lines[insert_at:insert_at] = observation
    detail = ['# 전체 연구·실험 상태표', '', f'확인 시각: **{stamp(snapshot.created)}**.', '',
              '[프로젝트 요약](../../README.md)', '',
              '설정 비교는 점수와 무관한 고정 ID 비교입니다. 개발 기준 통과는 최종 후보 승인·독립 성능 증거·대회 제출을 뜻하지 않습니다. '
              '완료 seed×기간 영수증과 새 모델 학습 횟수를 구분합니다. 부분·실패 행의 영수증을 성공 결과로 승격하지 않습니다.', '',
              '전체 설정·비교 차이·원래 점수·혼합 점수·기간 요약은 아래 CSV들에 같은 열로 보존합니다.', '']
    fields = list(dict.fromkeys([*old.FIELDS, *EXTRA_FIELDS]))
    csvs = csv_outputs(snapshot.rows, fields)
    for path in csvs:
        detail.append(f'- [{Path(path).name}]({Path(path).name})')
    for item in snapshot.campaigns:
        detail += ['', f"## {c(item['label'])}", '', c(item.get('note', '')), '',
                   '| ID / 종류 | 상태 | 기초 / 비교 ID | 실제 설정 변경 / 비교 범위 | primary / recent W_pct | 영수증 / 새 학습 | 판정·근거 |',
                   '|---|---|---|---:|---|---|---|']
        for row in item['rows'] + item.get('bases', []):
            label = old.LABELS.get(row.get('status'), row.get('status', ''))
            score = f"{n(row.get('primary_W_pct'))} / {n(row.get('recent_W_pct'))}"
            if row.get('kind') == 'historical_record':
                score = f"{c(row.get('metric_name', ''))}: {n(row.get('metric_value'))}"
            evidence = snapshot.link(row.get('evidence_path', ''), '근거', prefix='../../')
            receipt_count = row.get('completed_seed_fold_receipts', row.get('completed_folds', '—'))
            detail.append(f"| {c(row['id'])} / {c(row['kind'])} | {c(label)} | {c(row.get('base_id', ''))} / {c(row.get('comparison_id', ''))} | "
                          f"{c(row.get('changed_settings', ''))} ({c(row.get('comparison_scope', ''))}) | {score} | {receipt_count} / {row.get('recorded_model_fits', '—')} | "
                          f"{c(row.get('model_selection_status', row.get('note', '')))} {evidence} |")
    detail += ['', '설정 변경의 정확한 값은 CSV의 changed_settings와 config_json을 함께 확인하세요. '
               '과거 기록의 지표·참조 기간·진단 여부를 유지하며 캠페인 간 자동 우승자를 만들지 않습니다.', '']
    return {'README.md': '\n'.join(lines).encode(), f'{OVERVIEW}/README.md': '\n'.join(detail).encode(), **csvs}


def check_ownership(root, proposed):
    previous = root / OVERVIEW / 'snapshot_manifest.json'
    if previous.exists():
        prior = json.loads(previous.read_text())
        hashes = prior.get('outputs_sha256', {})
        for path, expected in hashes.items():
            if path != 'README.md' and not path.startswith(OVERVIEW + '/'):
                raise ValueError('Prior v2 manifest contains an output outside its scope')
            actual = root / path
            if not actual.is_file() or sha(actual.read_bytes()) != expected:
                raise ValueError(f'Prior generated output changed; preserve manual edits: {path}')
    else:
        prior = json.loads((root / 'analysis_outputs/experiment_overview/snapshot_manifest.json').read_text())
        expected = prior.get('outputs_sha256', {}).get('README.md')
        if not expected or sha((root / 'README.md').read_bytes()) != expected:
            raise ValueError('First migration requires root README to match the old snapshot manifest')
        hashes = {'README.md': expected}
    for path in proposed:
        if (root / path).exists() and path not in hashes:
            raise ValueError(f'Unowned existing output will not be overwritten: {path}')
    stale = set(hashes) - set(proposed)
    if stale:
        raise ValueError(f'Output set unexpectedly shrank; preserve and review prior files: {sorted(stale)}')


def build(root=ROOT):
    root = Path(root).resolve()
    old = load_old(root)
    snapshot = old.Snapshot(root)
    for path in PINS:
        snapshot.raw(path)
    catalog = snapshot.read(CATALOG, required=True)
    if len(catalog['campaigns']) != 36:
        raise ValueError('The pinned 36-family historical catalog must remain intact')
    snapshot.history(catalog)
    snapshot.current(old.OLD, '기존 10시간 단계')
    snapshot.current(old.NEW, '기존 22시간 단계')
    stage = new_stage(snapshot, old)
    protected = root / 'submission/renew_candidate_20261105/submission_files.zip'
    snapshot.best_ok = protected.is_file() and sha(protected.read_bytes()) == old.BEST_SHA
    outputs = render(snapshot, old, catalog, stage)
    for path, data in outputs.items():
        if len(data) > LIMIT:
            raise ValueError(f'Public output exceeds 2 MiB: {path}')
    check_ownership(root, outputs)
    source_paths = [OLD_REPORTER, CATALOG, 'submission/research_reporting_v2/update_readme.py',
                    'submission/research_reporting_v2/publish_readme.py']
    for name in ['test_update_readme.py', 'test_publish_readme.py', 'README.md']:
        relative = 'submission/research_reporting_v2/' + name
        if (root / relative).is_file():
            source_paths.append(relative)
    source_hashes = {path: sha((root / path).read_bytes()) for path in source_paths}
    source_digest = sha(encoded_json({'inputs': snapshot.inputs, 'source_sha256': source_hashes,
                                     'process_identity_matches': stage['process_identity_matches'],
                                     'observed_utc': snapshot.created}).encode())
    manifest = dict(schema_version=2, created_utc=snapshot.created, snapshot_id=source_digest[:16],
                    source_snapshot_sha256=source_digest, publisher_sha256=PUBLISHER_SHA,
                    source_sha256=source_hashes, outputs_sha256={p: sha(v) for p, v in outputs.items()},
                    output_bytes={p: len(v) for p, v in outputs.items()}, experiment_rows=len(snapshot.rows),
                    historical_campaigns=36, historical_catalog_created_utc=catalog.get('created_utc'),
                    current_counts={x['id']: x['counts'] for x in snapshot.campaigns if x['kind'] != 'historical'},
                    new_stage=STAGE, deadline_utc=DEADLINE, search_stop_utc=SEARCH_STOP,
                    source_files_observed=len(snapshot.inputs), model_fits=0, network_requests=0,
                    all_history_previously_exposed=True, protected_best_sha256_matches=snapshot.best_ok)
    return outputs, manifest, old


def generate(root=ROOT):
    root = Path(root).resolve()
    folder = root / OVERVIEW
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / '.generation.lock').open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        outputs, manifest, old = build(root)
        # Recheck all ownership immediately before the first replacement.
        check_ownership(root, outputs)
        for path, data in outputs.items():
            old.atomic(root / path, data)
        old.atomic(folder / 'snapshot_manifest.json', (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode())
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--check', action='store_true', help='Build and validate in memory without writing reports')
    args = parser.parse_args()
    result = build(args.root)[1] if args.check else generate(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
