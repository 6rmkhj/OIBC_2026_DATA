#!/usr/bin/env python3
"""Generate public research documentation from small metadata; never train or publish."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import quote
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
KST = ZoneInfo('Asia/Seoul')
BEST_SHA = 'ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434'
PUBLISHER_SHA = '89d2e4276195847792b7cf31d5d22339fee0a8bd0fb904110a38e996b51ea109'
OLD = 'research_10h_20261107'
NEW = 'research_22h_20261107'
FOLDS = ('early2022', 'primary', 'winter', 'spring', 'recent')
LABELS = {'completed': '완료', 'failed': '실패', 'running': '진행 중', 'pending': '대기',
          'finalizing': '결과 기록 후 종료 확인 중', 'partial': '부분 결과', 'stopped': '중단',
          'time_limit': '시간 제한', 'skipped_dependency': '선행 작업 실패로 건너뜀',
          'budget_reserved': '시간 예산으로 미실행', 'deferred_budget': '시간 예산으로 미실행',
          'interrupted': '실행 중 끊김', 'blocked_ambiguous_launch': '시작 여부 불명확해 보류',
          'recorded': '과거 기록', 'unknown': '확인 불가'}
LABELS.update({'keep':'당시 탐색에서 유지','discard':'당시 탐색에서 제외','crash':'실행 실패',
    'verified':'검증 기록 있음','analysis_document_available':'분석 문서 있음',
    'both_development_periods_improve':'두 개발 기간 개선','both_periods_not_improved':'두 기간 동시 개선 아님',
    'comparison_recorded':'비교 기록','development_gate_fail':'개발 기준 미통과','development_gate_pass':'개발 기준 통과',
    'exported_verified_mixed_generalization':'후보 생성·검증, 기간별 성능 혼재',
    'exported_verified_official_unknown':'후보 생성·검증, 당시 공식 점수 미확인',
    'fixed_alpha_screen':'고정 혼합 계수 비교','prepared_then_resumed_in_linux':'준비 후 Linux에서 이어 실행',
    'rejected_recent_regression':'최근 기간 악화로 제외','user_reported_official_best':'사용자 보고 최고점',
    'user_reported_official_regression':'사용자 보고 점수 하락','verified_no_advantage':'검증상 이점 없음',
    'calibration_fit_period_baseline':'보정 학습 기간 기준값',
    'forward_calibration_comparison':'이후 기간으로 보정 이전 평가',
    'historical_composition_comparison':'과거 발전소 구성 비교',
    'historical_development_comparison':'과거 개발 모델 비교',
    'historical_forecast_input_comparison':'과거 예보 입력 비교',
    'in_sample_calibration_diagnostic':'계수 학습 기간 내 진단',
    'nondeployable_rolling_observation_diagnostic':'실시간 관측 사용 진단·제출 불가',
    'observation_trained_forecast_fed_diagnostic':'관측 학습·예보 입력 차이 진단',
    'perfect_weather_diagnostic_only':'완벽한 날씨 가정 진단·제출 불가',
    'unseen_site_diagnostic':'미학습 발전소 진단'})
FIELDS = ['campaign', 'id', 'kind', 'status', 'controller_status', 'completed_folds', 'expected_folds',
          'recorded_model_fits', 'mean_W_ratio_vs_c000', 'primary_blend_W_change_pct',
          'recent_blend_W_change_pct', 'eligible', 'audit_gate_pass', 'started_kst', 'finished_kst',
          'metric_name', 'metric_value', 'evidence_path', 'note']
FIELDS += ['base_id', 'source_generation_id', 'config_json', 'comparison_id', 'changed_settings',
           'changed_setting_count', 'comparison_scope', 'primary_W', 'recent_W',
           'primary_W_pct', 'recent_W_pct', 'primary_W_change_pct_vs_comparison',
           'recent_W_change_pct_vs_comparison', 'primary_W_change_pct_vs_raw',
           'recent_W_change_pct_vs_raw', 'blend_alpha']
SETTING_NAMES = {'features':'입력', 'objective':'학습 손실', 'target':'학습 정답', 'weighting':'오차 가중치',
    'half_life':'최근 자료 가중치 반감기', 'n_estimators':'트리 수', 'learning_rate':'학습률',
    'num_leaves':'트리 최대 잎 수', 'min_child_samples':'잎 최소 표본 수', 'reg_lambda':'L2 규제',
    'colsample_bytree':'입력 샘플 비율', 'subsample':'행 샘플 비율', 'base_id':'기초 모델',
    'method':'보정 방법', 'mode':'보정 단위', 'shrink':'보정 적용 비율', 'bound':'보정 제한값'}


def setting_value(value):
    return '없음' if value is None else str(value)


def config_changes(before, after):
    return {k: (before.get(k), after.get(k)) for k in sorted(set(before) | set(after))
            if k != 'id' and before.get(k) != after.get(k)}


def describe_changes(changes, friendly=False):
    return '; '.join(f'{SETTING_NAMES.get(k,k) if friendly else k}: {setting_value(a)}→{setting_value(b)}'
                     for k, (a,b) in changes.items()) or '변경 없음(비교 기준 자체)'


def percent_change(after, before):
    return (after / before - 1) * 100 if after is not None and before is not None and before > 0 else None


def direction(value):
    if value is None:
        return '미평가'
    return '개선' if value < -1e-10 else '악화' if value > 1e-10 else '동일'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def stamp(value):
    if not value:
        return '—'
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00')).astimezone(KST).strftime('%Y-%m-%d %H:%M:%S KST')
    except (ValueError, TypeError):
        return str(value)


def cell(value):
    return str(value if value is not None else '—').replace('|', '\\|').replace('\n', ' ')


def number(value, digits=4):
    if value is None or value == '':
        return '—'
    try:
        value = float(value)
        return f'{value:.{digits}f}' if math.isfinite(value) else '—'
    except (ValueError, TypeError):
        return cell(value)


def identity_alive(value):
    if not value:
        return False
    try:
        fields = Path(f"/proc/{value['pid']}/stat").read_text().rsplit(')', 1)[1].split()
        boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        return (fields[0] not in {'Z', 'X'} and int(fields[2]) == value['pgid']
                and int(fields[19]) == value['start_ticks'] and boot == value['boot_id'])
    except (FileNotFoundError, ProcessLookupError):
        return False
    except (PermissionError, KeyError, ValueError):
        return None


class Snapshot:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.created = datetime.now(timezone.utc).isoformat()
        self.inputs = {}
        self.cache = {}
        self.warnings = []
        self.rows = []
        self.campaigns = []
        tree = subprocess.run(['git', 'ls-tree', '-r', '--name-only', '-z', 'refs/heads/codex/checkpoints'],
                              cwd=self.root, capture_output=True, check=False)
        self.public = {x.decode() for x in tree.stdout.split(b'\0') if x}

    def raw(self, relative):
        relative = str(relative)
        if relative in self.cache:
            return self.cache[relative]
        path = self.root / relative
        if not path.is_file():
            return None
        if path.stat().st_size > 16 * 1024 * 1024:
            raise ValueError(f'Metadata unexpectedly exceeds 16 MiB: {relative}')
        data = path.read_bytes()
        if data.startswith(b'version https://git-lfs.github.com/spec/'):
            self.warnings.append(f'{relative}: Git LFS 포인터만 있어 세부 값을 읽지 않음')
            return None
        self.inputs[relative] = digest(data)
        self.cache[relative] = data
        return data

    def read(self, relative, required=False):
        data = self.raw(relative)
        if data is None:
            if required:
                raise FileNotFoundError(relative)
            return None
        return json.loads(data.decode('utf-8-sig'))

    def link(self, relative, label='근거', prefix=''):
        if not relative:
            return '—'
        public = relative in self.public
        if relative.startswith(f'analysis_outputs/{OLD}/') or relative.startswith(f'analysis_outputs/{NEW}/'):
            public |= relative.endswith('/result.json') and (self.root / relative).is_file()
            public |= '/hourly_checks/' in relative and relative.endswith('_science.json')
            public |= Path(relative).name in {'protocol.json', 'configs.json', 'bases.json', 'jobs.json', 'CAMPAIGN.md'}
        return f'[{cell(label)}]({prefix}{quote(relative, safe="/")})' if public else f'`{cell(relative)}` (로컬 근거)'

    def receipts(self, folder):
        result = []
        for fold in FOLDS:
            p = f'{folder}/{fold}/receipt.json'
            value = self.read(p)
            if value and value.get('status') == 'PASS':
                result.append(value)
        return result

    def current(self, name, title):
        folder = f'analysis_outputs/{name}'
        state = self.read(f'{folder}/controller_state/state.json') or {}
        manifest = self.read(f'{folder}/controller_manifest.json', required=True)
        protocol = self.read(f'{folder}/protocol.json', required=True)
        configs = self.read(f'{folder}/configs.json', required=True)
        bases = {b['id']:b for b in self.read(f'{folder}/bases.json') or []}
        report = self.read(f'{folder}/report.json') or {}
        old_ranking = {r['id']: r for r in report.get('ranking', [])}
        audited_failed = {}
        failed_audit_path = ''
        for path in sorted((self.root / folder / 'hourly_checks').glob('*_failed_candidates_science.json')):
            audit = self.read(path.relative_to(self.root))
            if audit.get('verification_status') == 'PASS' and audit.get('frozen_files_modified') is False:
                for row in audit.get('rows', []):
                    if row.get('gate_recomputed') is True:
                        audited_failed[row['id']] = row
                failed_audit_path = str(path.relative_to(self.root))
        actual_fit_count = 0
        data_rows = []
        errors = []
        for config in configs:
            identifier = config['id']
            job = state.get('jobs', {}).get(identifier, {})
            unit = f'{folder}/trials/{identifier}'
            result = self.read(f'{unit}/result.json')
            receipts = self.receipts(unit)
            fits = sum(r.get('real_model_fits', 0) for r in receipts)
            actual_fit_count += fits
            controller_status = job.get('status', '')
            if controller_status in {'failed', 'time_limit', 'stopped', 'interrupted', 'skipped_dependency',
                                     'budget_reserved', 'deferred_budget', 'blocked_ambiguous_launch'}:
                status = controller_status
            elif result and result.get('status') == 'PASS':
                status = 'finalizing' if controller_status in {'running','launching'} else 'completed'
            elif controller_status in {'running','launching'}:
                status = 'running'
            elif receipts:
                status = 'partial'
            else:
                status = 'pending' if controller_status in {'', 'pending'} else 'unknown'
            note = ''
            if status == 'failed':
                log_path = self.root / folder / 'controller_state/jobs' / identifier / 'run.log'
                tail = ''
                if log_path.exists():
                    with log_path.open('rb') as stream:
                        stream.seek(max(0, log_path.stat().st_size - 4096))
                        tail = stream.read().decode('utf-8', errors='replace')
                if 'Object of type bool is not JSON serializable' in tail:
                    note = 'NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록'
                    errors.append(identifier)
                else:
                    note = f"컨트롤러 실패 기록(exit={job.get('exit_code', '?')}); 완료로 집계하지 않음"
                if identifier in audited_failed:
                    note += '; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료'
            ranking = result if name == NEW else old_ranking.get(identifier, {})
            ranking = ranking or {}
            blend = ranking.get('blend', {})
            deltas = {}
            for fold in ('primary', 'recent'):
                score = blend.get('scores', {}).get(fold, {})
                if score.get('reference', {}).get('W'):
                    deltas[fold] = (score['blend']['W'] / score['reference']['W'] - 1) * 100
            diagnostic = audited_failed.get(identifier) if status == 'failed' else None
            if diagnostic:
                ranking = dict(mean_W_ratio=1+diagnostic['mean_baseline_W_change_pct']/100)
                deltas = diagnostic['blend_W_change_pct']
            eligible = ranking.get('eligible') if status == 'completed' else None
            row = dict(campaign=name, id=identifier, kind='generation' if name == OLD else 'calibration',
                status=status, controller_status=controller_status, completed_folds=len(receipts), expected_folds=5,
                recorded_model_fits=fits, mean_W_ratio_vs_c000=ranking.get('mean_W_ratio'),
                primary_blend_W_change_pct=deltas.get('primary'), recent_blend_W_change_pct=deltas.get('recent'),
                eligible=eligible, audit_gate_pass=identifier in audited_failed if status=='failed' else None,
                started_kst=stamp(job.get('launched_utc')),
                finished_kst=stamp(job.get('finished_utc') or (result or {}).get('utc')),
                metric_name='mean W / c000 (실패 기록 독립 감사)' if diagnostic else 'mean W / c000',
                metric_value=ranking.get('mean_W_ratio'),
                evidence_path=f'{unit}/result.json' if result else failed_audit_path if diagnostic else '', note=note)
            row.update(_config=config, base_id=config.get('base_id',''),
                source_generation_id=bases.get(config.get('base_id'),{}).get('source_id',''),
                config_json=json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(',',':')))
            # Failed/partial jobs must not acquire successful comparison metrics from receipts.
            if status == 'completed' and result and result.get('status') == 'PASS':
                row['blend_alpha'] = result.get('blend',{}).get('alpha')
                for fold in ('primary','recent'):
                    record = result.get('folds',{}).get(fold,{})
                    row[f'{fold}_W'] = record.get('score',{}).get('W')
                    row[f'{fold}_W_pct'] = record.get('score',{}).get('W_pct')
                    row[f'{fold}_W_change_pct_vs_raw'] = percent_change(
                        row[f'{fold}_W'], record.get('raw_score',{}).get('W'))
            self.rows.append(row)
            data_rows.append(row)
        # Choose by frozen configuration and ID only, never by a good score.
        # A future row therefore keeps the same comparator as it completes.
        for index, row in enumerate(data_rows):
            earlier = [r for r in data_rows[:index] if r['base_id'] == row['base_id']]
            comparator = min(earlier, key=lambda r: (len(config_changes(r['_config'],row['_config'])), r['id'])) if earlier else row
            changes = config_changes(comparator['_config'],row['_config'])
            row.update(comparison_id=comparator['id'], changed_settings=describe_changes(changes),
                changed_setting_count=len(changes), _changes=changes,
                comparison_scope='기준 자체' if comparator is row else '단일 설정 차이' if len(changes)==1 else '여러 설정 동시 변경')
            if row['status']=='completed' and comparator['status']=='completed':
                for fold in ('primary','recent'):
                    row[f'{fold}_W_change_pct_vs_comparison'] = percent_change(row.get(f'{fold}_W'),comparator.get(f'{fold}_W'))
        base_rows = []
        for base in bases.values():
            job = state.get('jobs', {}).get(base['id'], {})
            result = self.read(f"{folder}/bases/{base['id']}/result.json")
            fit_count = 0
            for p in sorted((self.root / folder / 'bases' / base['id'] / 'origins').glob('*/receipt.json')):
                receipt = self.read(p.relative_to(self.root))
                fit_count += receipt.get('real_model_fits', 0)
            actual_fit_count += fit_count
            status = job.get('status', 'pending')
            if result and result.get('status') == 'PASS' and status in {'pending','completed'}:
                status = 'completed'
            elif status == 'launching':
                status = 'running'
            row = dict(campaign=name, id=base['id'], kind='oof_generation', status=status,
                controller_status=job.get('status', ''), recorded_model_fits=fit_count,
                started_kst=stamp(job.get('launched_utc')), finished_kst=stamp(job.get('finished_utc')),
                evidence_path=f"{folder}/bases/{base['id']}/result.json" if result else '',
                note=f"기존 {base['source_id']} 설정 재사용; 보정 학습용 시간 순서 OOF 생성")
            row.update(base_id=base['id'], source_generation_id=base['source_id'],
                       config_json=json.dumps(base['config'],ensure_ascii=False,sort_keys=True,separators=(',',':')))
            self.rows.append(row)
            base_rows.append(row)
        completion_fits = 0
        seen = set()
        for path in (self.root / folder / 'completion').glob('**/receipt.json'):
            resolved = path.resolve()
            if resolved in seen or any('.interrupted.' in part for part in path.parts):
                continue
            seen.add(resolved)
            completion_fits += (self.read(path.relative_to(self.root)) or {}).get('real_model_fits', 0)
        actual_fit_count += completion_fits
        alive = identity_alive(state.get('controller_identity'))
        stop = (self.root / folder / 'controller_state/STOP').exists()
        status = ('명시적 중단' if stop else '종료' if state.get('phase') == 'finished'
                  else '진행 중' if alive else '프로세스 확인 불가' if state else '시작 대기')
        heartbeat_age = None
        if state.get('heartbeat_utc'):
            heartbeat_age = max(0., (datetime.fromisoformat(self.created)-datetime.fromisoformat(state['heartbeat_utc'])).total_seconds())
        if not stop and alive and state.get('phase') != 'finished' and (heartbeat_age is None or heartbeat_age > 120):
            status = '상태 기록 갱신 지연 — 프로세스는 식별됨'
        counts = Counter(r['status'] for r in data_rows)
        stored = [r for r in data_rows if r['status'] == 'completed' and r.get('mean_W_ratio_vs_c000') is not None]
        best = min(stored, key=lambda r: r['mean_W_ratio_vs_c000']) if stored else None
        completion = self.read(f'{folder}/completion/result.json')
        check = self.read(f'{folder}/independent_completion_check.json')
        duration = None
        if state.get('started_utc'):
            end = state.get('finished_utc') or self.created
            duration = (datetime.fromisoformat(end) - datetime.fromisoformat(state['started_utc'])).total_seconds()
        item = dict(id=name, label=title, folder=folder, kind='current', status=status, counts=dict(counts),
            candidate_count=len(configs), rows=data_rows, bases=base_rows, recorded_model_fits=actual_fit_count,
            eligible=sum(r.get('eligible') is True for r in data_rows), serialization_failures=errors,
            current_job=state.get('current_job'), phase=state.get('phase'), started=state.get('started_utc'),
            finished=state.get('finished_utc'), duration=duration, deadline=manifest['deadline_utc'],
            heartbeat=state.get('heartbeat_utc'), heartbeat_age_seconds=heartbeat_age,
            process_identity_matches=alive, completion=completion,
            independent_completion=check, best=best, stop_reason=state.get('stop_reason'))
        item.update(audited_failed_gate_count=sum(x in errors for x in audited_failed), failed_audit_path=failed_audit_path)
        item.update(configs=configs, base_specs=bases, protocol=protocol)
        self.campaigns.append(item)
        return item

    def history(self, catalog):
        for campaign in catalog.get('campaigns', []):
            records = list(campaign.get('records', []))
            table = campaign.get('table')
            if table:
                raw = self.raw(table['path'])
                if raw:
                    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')), delimiter=table.get('delimiter', ',').replace('\\t','\t'))
                    for n, row in enumerate(reader, 1):
                        summary = row.get('hypothesis') or row.get('label') or ''
                        if row.get('direct_weight') not in {None,''}:
                            summary = f"그룹 직접 모델 혼합 비중 {row['direct_weight']}. " + summary
                        records.append(dict(id=row.get(table.get('id_column', 'id')) or f'row{n}',
                            status=row.get(table.get('status_column', 'status')) or 'recorded',
                            metric_name=table.get('metric_column', 'W_pct'),
                            metric_value=row.get(table.get('metric_column', 'W_pct'), ''),
                            evidence_path=table['path'], summary=summary,
                            attempt_row=n))
            rows = []
            for n, record in enumerate(records, 1):
                row = dict(campaign=campaign['id'], id=record.get('id', f'record{n}'), kind='historical_record',
                    status=record.get('status', 'recorded'), metric_name=record.get('metric_name', ''),
                    metric_value=record.get('metric_value', ''), evidence_path=record.get('evidence_path', ''),
                    note=record.get('summary', record.get('note', '')))
                if record.get('attempt_row'):
                    row['note'] = f"원본 표/로그 행 {record['attempt_row']} (재시도·다른 조건을 합치지 않음). " + row['note']
                rows.append(row)
                self.rows.append(row)
            for path in campaign.get('evidence', []):
                payload = self.raw(path)
                if payload is None:
                    self.warnings.append(f'{path}: 현재 파일을 읽지 못함; 아래 과거 기록은 카탈로그 작성 시점 기준')
                expected = campaign.get('evidence_sha256', {}).get(path)
                if payload is not None and expected and digest(payload) != expected:
                    raise ValueError(f'Historical evidence changed; review catalog before publication: {path}')
            self.campaigns.append(dict(campaign, kind='historical', rows=rows, counts=dict(Counter(r['status'] for r in rows)),
                                       candidate_count=len(rows), status=campaign.get('status', '과거 기록')))

    def explain_experiments(self, old, new):
        lines = ['## 무엇을 바꾸며 실험하는가', '',
            '**현재는 기존 발전량 모델의 예측에 보정을 더하는 단계입니다.** 앞선 `c000~c255`는 발전량 모델 자체의 입력·학습 방식을 비교했고, '
            '연장 `n0000~n2047`은 그중 고정한 32개 기초 모델(`b00~b31`)마다 64개 보정 설정(중앙값 4개·트리 60개)을 비교합니다. '
            'ID는 고정된 실행 큐의 번호이며, 번호가 커진다고 모델이 누적 개선되는 것은 아닙니다.', '',
            '1. **발전량 모델**: 날씨·태양고도 등의 입력에서 기초 예측을 만듭니다. 예: `b00`은 앞선 `c206` 설정입니다.',
            '2. **오차 보정**: 학습 마감일 이후에 만든 과거 예측(시간 순서 OOF)의 오차를 배워 기초 예측에 제한된 보정량을 더합니다.',
            '3. **최고 제출 모델과 혼합**: 보정 예측에 가중치 `alpha`, 기존 최고 예측에 `1-alpha`를 줍니다. '
            '`alpha`는 primary에서만 정하고 recent에는 그대로 적용합니다.', '',
            '**각 행의 결과는 동일한 설정을 5개 학습 마감일에서 평가한 값입니다.** 일부 설정은 함께 바뀌는 조합 탐색입니다. '
            '그 경우 점수 차이를 한 변수의 효과로 단정하지 않습니다. 가능한 모든 조합을 평가한 완전요인실험은 아닙니다. '
            '아래 설명은 기존 설정과 저장된 결과를 읽어 생성하며 새 학습·후보 선택을 하지 않습니다.', '',
            '### 바뀌는 설정과 의미', '',
            '| 단계 / 설정 키 | 무엇을 바꾸는가 |', '|---|---|',
            '| 발전 모델 `features` | `station`: 관측소별 확장 입력 목록 904개. `rich`: 그 부분집합인 요약·물리 입력 100개. rich가 더 많은 입력이라는 뜻은 아니며, 실제 학습에서는 학습 기간의 상수 열을 제거합니다. |',
            '| 발전 모델 `target` + `weighting` | `original_cf`+`legacy`: 기존 정규화 정답·태양고도 가중치. `exact_energy`+`monetary`: 그룹 실제 발전량으로 만든 정답·가격과 벌점 계수를 반영한 오차 가중치. 이 두 키는 함께 바뀌므로 각각의 효과를 분리하지 않습니다. |',
            '| 발전 모델 `objective` | `regression_l1`: 절대 오차, `regression_l2`: 제곱 오차를 줄이도록 학습. 공식 평가 지표를 바꾸는 설정이 아닙니다. |',
            '| 공통 `half_life` | 학습 자료가 반감기만큼 오래되면 시간 가중치를 절반으로 줄입니다. 학습 기간을 잘라내는 설정은 아닙니다. `없음`은 시간 감쇠 없음. 발전 모델: 90/180/365일, 보정: 180/365일을 비교합니다. 보정 단계에서는 OOF 오차의 가중치이며 발전 모델 가중치를 바꾸지 않습니다. |',
            '| 보정 `base_id` | 어떤 기초 발전량 모델을 보정하는지. 예: `b00→c206`, `b01→c003`. 기초 모델 교체는 내부 설정 여러 개의 변경일 수 있습니다. 전체 표와 CSV에 연결 ID를 적습니다. |',
            '| 보정 `method` | `median`: 정규화된 OOF 오차의 가중 중앙값 하나를 적용. 가중치에는 금액·보정 단위·시간 감쇠·중복 횟수를 반영합니다. `tree`: 날씨와 시점 조건에 따라 보정량을 다르게 예측하는 작은 LightGBM 모델. median에서는 입력·트리 설정을 사용하지 않습니다. |',
            '| 보정 `features` | `core`: 날씨·태양고도·그룹·기초 예측/설비용량(14개). `season`: core+연중 위치·시간(17개). `age`: season+발전 모델 학습 마감 이후 일수·학습 이력 길이(19개). 기상예보 발표 후 경과시간이 아닙니다. |',
            '| 보정 `mode` | `additive`: 설비용량×태양고도 정규화값을 보정 단위로 사용. `multiplicative`: 기초 예측량을 사용하되 너무 작으면 하한을 적용합니다. |',
            '| 보정 `shrink` / `bound` | 학습한 정규화 보정값을 ±bound로 제한한 뒤 shrink만큼 적용합니다. `shrink=0.5`는 보정량의 절반. `bound=0.2`는 발전량의 무조건 20%가 아닙니다. 보정량 = shrink × 제한된 보정값 × mode별 단위. 마지막에 물리적 출력 범위로 제한하고 밤은 0입니다. |',
            '| 트리 `num_leaves` / `min_child_samples` | 잎 수와 한 잎의 최소 표본 수. 잎이 많고 최소 표본이 작을수록 복잡한 조건을 표현할 수 있지만 항상 성능이 좋아지는 것은 아닙니다. |',
            '| 트리 `n_estimators` / `learning_rate` | 트리 개수와 단계별 학습률. 반복 횟수·갱신 크기를 함께 결정합니다. |',
            '| 트리 `reg_lambda` / `colsample_bytree` / `subsample` | 규제 강도·트리별 입력 사용 비율·행 사용 비율. 보정 트리의 입력 비율 0.9, 행 비율 0.8은 고정입니다. |', '',
            f"실제 모든 설정값: {self.link(old['folder']+'/configs.json','발전 모델 256개')} · "
            f"{self.link(new['folder']+'/configs.json','보정 2,048개')} · {self.link(new['folder']+'/bases.json','기초 모델 연결표')}", '']
        active = next((r for r in new['rows'] if r['id']==new['current_job']), None)
        if active:
            c = active['_config']
            lines += ['### 지금 실행하는 설정', '',
                f"`{active['id']}`: **{LABELS.get(active['status'],active['status'])}**. 기초 `{active['base_id']}` → `{active['source_generation_id']}`, "
                f"보정 `{c['method']}`, 입력 `{c['features']}`, 단위 `{c['mode']}`, 반감기 {setting_value(c['half_life'])}, "
                f"적용 비율 {c['shrink']}, 제한값 {c['bound']}.", '',
                f"설정이 가장 가까운 앞선 동일 기초 모델 실험 `{active['comparison_id']}`와의 차이: "
                f"{describe_changes(active['_changes'],friendly=True)}. {active['comparison_scope']}. 완료 전에는 결과 차이를 표시하지 않습니다.", '']
        elif new['current_job'] in new['base_specs']:
            base=new['base_specs'][new['current_job']]
            lines += ['### 지금 실행하는 설정', '',
                f"`{base['id']}` → 발전 모델 `{base['source_id']}`: **보정 학습용 과거 예측(OOF)을 준비하는 단계**입니다. "
                '고정한 기초 모델 설정을 여러 과거 학습 마감일에 적용해 그 이후의 예측 오차를 모읍니다. '
                '기존 일치 모델은 재사용하며, 이 단계 자체를 보정 후보 성능 개선으로 집계하지 않습니다.', '']
        lines += ['### 실제 결과: 설정 변경 전 → 후', '',
            '아래는 **두 실험이 모두 정상 완료된 경우**만 비교합니다. 설명 예시는 점수 순위와 무관하게 각 변경 유형에서 ID가 가장 앞선 쌍을 택합니다. '
            '기초 모델·나머지 설정이 같은 쌍만 “한 설정”으로 표시하며, 묶음 변경은 따로 표시합니다. 전체 실험에는 각각의 비교 ID와 차이를 적습니다.', '',
            '**표의 수치는 혼합 전 예측의 W_pct(낮을수록 좋음)**입니다. 괄호는 같은 기간의 W 상대 변화 `(후/전−1)×100`이며, W_pct의 퍼센트포인트 차이가 아닙니다. '
            '혼합 성능과 alpha는 아래 및 전체 CSV에서 별도로 확인합니다.', '',
            '| 실험 전 → 후 | 바뀐 설정 | primary W_pct 전 → 후 (W 상대 변화) | recent W_pct 전 → 후 (W 상대 변화) | 해석 |',
            '|---|---|---:|---:|---|']
        for item, keys in [(old,('features',)),(old,('target','weighting')),
                           (old,('half_life',)),(old,('num_leaves',)),
                           (new,('half_life',)),(new,('features',)),(new,('shrink',)),
                           (new,('reg_lambda',)),(new,('mode','bound'))]:
            pair = self.first_pair(item, keys)
            if not pair:
                continue
            a,b = pair
            values=[]
            changes=[]
            for fold in ('primary','recent'):
                delta=percent_change(b.get(f'{fold}_W'),a.get(f'{fold}_W'))
                changes.append(delta)
                values.append(f"{number(a.get(f'{fold}_W_pct'))} → {number(b.get(f'{fold}_W_pct'))} ({number(delta)}%)")
            refs=f"{self.link(a['evidence_path'],a['id'])} → {self.link(b['evidence_path'],b['id'])}"
            lines.append(f"| {refs} | {cell(describe_changes(config_changes(a['_config'],b['_config']),friendly=True))} "
                         f"({'한 설정' if len(keys)==1 else str(len(keys))+'개 함께 변경'}) | {values[0]} | {values[1]} | "
                         f"primary {direction(changes[0])}, recent {direction(changes[1])} |")
        lines += ['', '쌍이 없는 변경 유형은 억지로 단일 효과를 계산하지 않습니다. 예시의 개선·악화는 해당 기초 모델과 기간에서의 관찰입니다. '
            '전체 평균이나 미래 성능 보장으로 일반화할 수 없고, 별도 확인 실험이나 여러 시드 반복 결과도 아닙니다. '
            '저장 실패 후보는 이 정상 완료 비교에서 제외되어 있습니다.', '',
            '### 왜 단독 오차 개선이 최종 점수 개선과 다른가', '']
        best=new.get('best')
        if best:
            c=best['_config']
            lines += [f"현재 저장된 결과의 평균 W/c000 최저 설정 `{best['id']}`는 `{best['base_id']}→{best['source_generation_id']}`에 "
                f"`{c['method']}` / `{c['features']}` / `{c['mode']}` 보정, 반감기 {setting_value(c['half_life'])}, "
                f"shrink={c['shrink']}, bound={c['bound']}를 적용합니다. 나머지 트리 설정은 전체 CSV의 `config_json`에 있습니다.", '',
                '| 비교 단계 | primary W 상대 변화 | recent W 상대 변화 |', '|---|---:|---:|',
                f"| 같은 기초 모델의 보정 전 → 보정 후 | {number(best.get('primary_W_change_pct_vs_raw'))}% | {number(best.get('recent_W_change_pct_vs_raw'))}% |",
                f"| 기존 최고 제출 예측 → 혼합 후 (alpha={number(best.get('blend_alpha'),6)}) | {number(best.get('primary_blend_W_change_pct'))}% | {number(best.get('recent_blend_W_change_pct'))}% |", '']
        lines += ['보정 전 모델을 이겼더라도 기존 최고 제출 예측을 이긴 것은 아닙니다. 특히 alpha=0이면 후보가 혼합에 기여하지 않아 '
            '혼합 결과는 기존 최고와 같습니다. 이 문서의 수치는 모두 과거 개발 자료의 내부 오차이며 새 공식 점수가 아닙니다.', '',
            '### 평가 기간과 읽는 방법', '', '| 평가 ID | 학습·보정 정답 사용 마감 (KST) | 이후 평가 구간 (KST) |', '|---|---|---|']
        for fold,window in new['protocol']['folds'].items():
            lines.append(f"| {fold} | {window['origin']} 00:00까지 | ({window['origin']} 00:00, {window['end']} 00:00] |")
        lines += ['', '위 마감은 발전 모델과 OOF 보정기의 학습 정답에 적용합니다. **혼합 alpha는 별도로 primary 평가 정답을 사용해 정합니다.** '
            '따라서 primary 혼합 결과는 계수를 선택한 자료에서의 값이며, recent는 그 계수를 변경 없이 적용한 후속 기간 평가입니다.', '',
            '기간은 서로 겹치며 모두 이미 노출된 과거 자료입니다. 시간 순서를 지킨 OOF도 독립적인 미사용 평가셋을 뜻하지 않습니다. '
            '같은 기간 안의 전후 비교에만 위 상대 변화식을 적용합니다.', '']
        return lines

    @staticmethod
    def first_pair(item, keys):
        # Group on all unchanged settings. The earliest pair is stable as later jobs finish.
        groups={}
        pairs=[]
        for row in sorted(item['rows'], key=lambda r:r['id']):
            if row['status']!='completed' or any(row.get(f'{f}_W') is None for f in ('primary','recent')):
                continue
            config=row['_config']
            if keys==('features',) and config.get('method')=='median':
                continue
            signature=json.dumps({k:v for k,v in config.items() if k not in ('id',*keys)},sort_keys=True)
            for prior in groups.get(signature,[]):
                if set(config_changes(prior['_config'],config))==set(keys):
                    pairs.append((prior,row))
            groups.setdefault(signature,[]).append(row)
        return min(pairs,key=lambda pair:(pair[0]['id'],pair[1]['id'])) if pairs else None

    def render(self, catalog, old, new):
        now_kst = stamp(self.created)
        failed = new['serialization_failures']
        lines = ['# OIBC 2026 · 모델 개선 실험 현황', '', f'**마지막 확인: {now_kst}** · GitHub에 약 1시간마다 갱신하는 기록입니다. 실시간 화면은 아닙니다.', '',
            '태양광 발전량 예측 모델을 개선하는 연구 저장소입니다. 이 문서는 처음 보는 사람도 무엇을 시도했고, 무엇이 끝났고, 어떤 결과가 아직 불확실한지 확인할 수 있도록 작성합니다.', '',
            '[전체 실험별 상태표](analysis_outputs/experiment_overview/README.md) · [전체 실험 CSV](analysis_outputs/experiment_overview/experiments.csv) · [실행 계약](analysis_outputs/research_22h_20261107/CAMPAIGN.md)', '',
            '## 현재 상황', '',
            f"- 연장 연구: **{new['status']}**. 현재 작업 `{new['current_job'] or '없음'}`. 프로세스 식별 확인: {'일치' if new['process_identity_matches'] else '종료 또는 확인 불가'}(위 확인 시각 기준).",
            f"- 마지막 상태 기록: {stamp(new['heartbeat'])} · 확인 시각과의 차이 {number(new['heartbeat_age_seconds'],0)}초. 120초 이상 갱신되지 않으면 지연으로 표시합니다.",
            f"- 최종 기한: **{stamp(new['deadline'])}**. 원래 10시간 계획에 12시간을 더한 **22시간의 작업 창**이며, 22시간 학습 완료를 뜻하지 않습니다.",
            f"- 기존 단계 자동 실행: {stamp(old['started'])} → {stamp(old['finished'])} ({int(old['duration']//3600)}시간 {int(old['duration']%3600//60)}분). 연장 단계 시작: {stamp(new['started'])}.",
            '- 학습은 동시에 하나, CPU 4개 / BLAS 1스레드입니다. README 생성과 GitHub 게시 명령은 학습을 시작하지 않습니다.', '',
            '| 단계 | 정상 완료 | 실패·시간 제한 | 진행/종료 확인 | 대기·미실행 | 부분·확인 필요 | 저장된 적격 후보 |',
            '|---|---:|---:|---:|---:|---:|---:|']
        for item in (old, new):
            c = item['counts']; done = c.get('completed', 0); bad = c.get('failed', 0) + c.get('time_limit', 0)
            running = c.get('running', 0) + c.get('finalizing', 0)
            pending = sum(c.get(k,0) for k in ('pending','deferred_budget','budget_reserved','skipped_dependency'))
            other = item['candidate_count']-done-bad-running-pending
            lines.append(f"| {item['label']} | {done}/{item['candidate_count']} | {bad} | {running} | {pending} | {other} | {item['eligible']} |")
        lines += ['', f"연장 보정용 OOF 기초 설정은 {sum(r['status']=='completed' for r in new['bases'])}/{len(new['bases'])}개 완료됐습니다. 완료 영수증에서 확인되는 실제 모델 학습은 기존 {old['recorded_model_fits']:,}회, 연장 {new['recorded_model_fits']:,}회입니다. 재사용 예측과 중앙값 보정은 학습 횟수에서 제외하며, 영수증 없이 끝난 학습은 세지 않습니다.", '']
        lines += self.explain_experiments(old,new)
        lines += ['## 현재 확인된 문제', '']
        if failed:
            lines += [f"**{len(failed)}개 보정 실험이 결과 JSON 저장 중 실패했습니다.** NumPy 불리언을 JSON으로 저장하는 타입 오류이며, 해당 실험의 학습 영수증은 남아 있어도 최종 `result.json`이 없습니다.", '',
                      '실패 ID: ' + ', '.join(f'`{x}`' for x in failed) + '.', '',
                      '**저장된 적격 후보가 0개라는 사실만으로 개선 후보가 없다고 단정할 수 없습니다.** 실패를 정상 완료·새 후보 검증 성공으로 집계하지 않습니다.', '',
                      f"이 중 **{new['audited_failed_gate_count']}개는 저장된 예측의 독립 감사에서 고정된 탐색 조건 통과가 확인**됐습니다. 그러나 결과가 선택 큐에 반영되지 않았고, 추가 시드 안정성·최종 재학습·제출 ZIP 검증은 수행되지 않았습니다. {self.link(new['failed_audit_path'],'실패 후보 독립 감사')}", '',
                      '실행 중 소스와 manifest를 수정하지 말라는 지시에 따라 이 오류는 아직 미수정 상태입니다. 최소 타입 변환 수정안은 감사 기록에 있으며, 현재 학습 코드에 적용하지 않았습니다.']
            checked = [r for r in new['rows'] if r.get('audit_gate_pass')]
            if checked:
                lines += ['', '독립 감사가 끝난 실패 기록 중 ID 순서로 처음 5개를 예시로 표시합니다. 모든 실패 기록은 전체 표·CSV에 있습니다. **아래는 개발 기간의 재계산 값이며 최종 제출 검증이나 공식 점수가 아닙니다.**', '',
                          '| ID | primary 혼합 W 상대 변화 | recent 혼합 W 상대 변화 | 상태 |', '|---|---:|---:|---|']
                for row in checked[:5]:
                    lines.append(f"| `{row['id']}` | {number(row['primary_blend_W_change_pct'])}% | {number(row['recent_blend_W_change_pct'])}% | 탐색 조건 통과 확인 / 최종 결과 저장 실패 |")
        else:
            lines.append('현재 스냅샷에서 해당 타입 오류로 실패한 작업은 없습니다. 완료 결과가 없는 작업은 대기·부분 결과·실패로 구분합니다.')
        lines += ['', '## 성능 숫자 읽는 법', '',
            '- **W / W_pct는 낮을수록 좋은 내부 오차 지표**입니다. `W = Σ(SMP × 벌점계수 × |예측−실적|)`, '
            '`W_pct = 100 × W / Σ(SMP × 벌점계수 × 실적)`입니다. 같은 기간의 W 상대 변화와 W_pct의 퍼센트포인트 차이를 구분합니다.',
            '- 다섯 기간 평균 W/c000는 각 기간의 비율을 평균한 값입니다. 기간 전체를 합친 오차율이 아닙니다.',
            '- `c000`은 단일 모델 비교용 기준입니다. **c000 대비 개선률은 기존 최고 제출 모델 대비 개선률이 아닙니다.**',
            '- primary에서 정한 혼합 계수를 recent에 그대로 적용합니다. 후보별로 계수를 따로 정하므로 혼합 비교에는 계수 변화도 포함됩니다. '
            '다섯 시점의 안정성 기준·최소 혼합 계수·두 기간의 개선 조건을 함께 통과해야 적격 후보가 됩니다. primary/recent 두 열만으로 적격을 판단하지 않습니다.',
            '- 모든 과거 기간은 이미 노출된 자료이며 평가 기간도 겹칩니다. 독립적인 미사용 홀드아웃이나 새 공식 리더보드 점수로 해석할 수 없습니다.',
            '- 탐색 정답은 2025-03-01까지입니다. 후기 2025년 3–5월 평가는 후보·계수를 고정한 뒤에만 사용하며 재선택에 쓰지 않습니다.', '',
            '아래는 **정상적으로 최종 기록이 저장된 실험 중** 다섯 기간 평균 W/c000가 가장 낮은 실험입니다. 최종 제출 권장 순위가 아닙니다.', '',
            '| 단계 / ID | 평균 W/c000 | c000 대비 상대 변화 | 기존 최고 예측 대비 primary 혼합 W 변화 | recent 혼합 W 변화 | 적격 |',
            '|---|---:|---:|---:|---:|---|']
        for item in (old, new):
            r = item['best']
            if r:
                ratio = r['mean_W_ratio_vs_c000']
                lines.append(f"| {item['label']} / {self.link(r['evidence_path'], r['id'])} | {number(ratio,6)} | {(ratio-1)*100:+.4f}% | {number(r['primary_blend_W_change_pct'])}% | {number(r['recent_blend_W_change_pct'])}% | {'예' if r['eligible'] else '아니오'} |")
        lines += ['', '혼합 계수가 0이면 기존 최고 예측을 그대로 사용하므로 혼합 성능 변화도 0%입니다. 적격 후보 여부와 ZIP 생성·형식 검증·공식 제출은 서로 다른 단계입니다.', '',
            '## 기존 최고 제출 파일과 공식 피드백', '',
            '**기존 최고점은 사용자에게 전달받은 6,454,220,836입니다.** 이 자동화가 리더보드를 조회해 새로 검증한 점수가 아닙니다. 더 높은 새 공식 점수는 확인되지 않았습니다.', '',
            f"보존 대상: `submission/renew_candidate_20261105/submission_files.zip`  \\nSHA256: `{BEST_SHA}`", '',
            '원본 ZIP 해시 확인: **' + ('일치' if self.best_ok else '불일치 — 확인 필요') + '**. 공식 리더보드 업로드와 유료 구매는 수행하지 않습니다.', '',
            '| 대상 | 사용자 보고 점수 | 해석 / 출처 |', '|---|---:|---|']
        for feedback in catalog.get('official_feedback', []):
            lines.append(f"| {cell(feedback.get('label',feedback.get('id','')))} | {cell(feedback.get('score','—'))} | {cell(feedback.get('note','사용자 보고'))} {self.link(feedback.get('evidence_path',''))} |")
        completion = old.get('completion') or {}
        continuation_outcome = (new.get('completion') or {}).get('status')
        outcome_text = (f"연장 단계의 기록된 종료 결과는 `{continuation_outcome}`입니다. 후보 생성 여부와 독립 검증을 별도로 확인해야 합니다."
                        if continuation_outcome else '연장 단계에는 최종 완료 결과가 아직 없습니다. 최종 후보 생성 결과를 확정하지 않습니다.')
        lines += ['', f"기존 256개 실험 단계의 종료 결과는 `{completion.get('status','확인 불가')}`입니다. 독립 검증은 `{(old.get('independent_completion') or {}).get('status','아직 없음')}`이며, 새 후보 ZIP 검증 성공을 뜻하지 않습니다. {outcome_text}", '',
            '## 전체 연구 이력', '', '과거 캠페인마다 평가 기간·단위가 다릅니다. 아래 행 수를 서로 같은 종류의 모델 학습 횟수로 더하지 않습니다. 재시도·실패 행은 원래 기록대로 보존합니다.', '',
            '| 캠페인 | 읽은 실험/시도 기록 | 상태 요약 |', '|---|---:|---|']
        for item in self.campaigns:
            counts = ', '.join(f'{LABELS.get(k,k)} {v}' for k,v in sorted(item['counts'].items())) or '개별 실험 수 미확인'
            lines.append(f"| {cell(item['label'])} | {item['candidate_count']} | {cell(counts)} |")
        lines += ['', '모든 개별 ID와 남은 계획 항목은 [전체 상태표](analysis_outputs/experiment_overview/README.md)와 [CSV](analysis_outputs/experiment_overview/experiments.csv)에 있습니다. 파일이 없는 과거 항목은 완료로 추정하지 않고 근거 범위를 표시합니다.', '',
            '## 파일과 재현 범위', '',
            '- `analysis_outputs/research_10h_20261107/`: 기존 단계 설정·완료 실험 검증 기록.',
            '- `analysis_outputs/research_22h_20261107/`: 연장 단계 설정·실험·독립 감사 기록.',
            '- `submission/research_reporting/`: 학습 없이 README와 전체 현황표를 만드는 코드.',
            '- `analysis_outputs/github_checkpoints_20261107/`: 각 공개 커밋에 포함된 파일 목록과 SHA256.',
            '- 대형 모델·원본 데이터·개별 예측·새 제출 ZIP·실행 상태 원문·로그·자동화 식별자는 시간별 게시 대상에서 제외합니다. 코드와 기록만으로 모든 학습 산출물을 즉시 복원할 수 있는 것은 아닙니다.', '',
            '기존 제출 파이프라인 설명은 [submission/README.md](submission/README.md)에 보존돼 있습니다. 그 문서의 과거 후보 안내보다 이 문서의 확인 시각과 최신 공식 피드백을 우선 확인하세요.', '',
            '문서 생성 명령(학습·네트워크 게시 없음):', '', '```bash',
            '/workspace/.venvs/oibc-2026/bin/python submission/research_reporting/update_readme.py', '```', '',
            'README는 완료·진행·실패 기록을 설명하는 문서입니다. 읽는 시점에 프로세스가 계속 살아 있다는 보장이 아니므로 마지막 확인 시각을 확인하세요.', '']
        if self.warnings:
            lines += ['확인 범위 제한: ' + '; '.join(self.warnings), '']
        root_text = '\n'.join(lines).replace('  \\nSHA256:', '  \nSHA256:')
        detail = ['# 전체 실험·시도 상태표', '', f'확인 시각: **{now_kst}**.', '',
            '[프로젝트 요약](../../README.md) · [필터링 가능한 전체 CSV](experiments.csv)', '',
            '현재 단계의 ID는 고정된 전체 설정 큐를 포함합니다. `pending`은 아직 실행되지 않았다는 뜻이며 실패가 아닙니다. 과거 표의 `keep`/`discard`는 당시 탐색 결정이지 공식 점수 상승이나 실패를 뜻하지 않습니다. 같은 ID의 재시도는 별도 과거 로그 행으로 남깁니다.', '',
            '현재 5개 기간 검증에서 결과 저장이 실패한 실험은 완료 영수증 수와 별도로 `failed`로 표시합니다. 모델의 과학적 적격 여부를 최종 결과 없이 추정하지 않습니다.', '',
            '## 설정과 결과 비교 읽는 법', '',
            '설정 키의 한국어 설명·평가 날짜·대표 전후 비교는 [프로젝트 README](../../README.md#무엇을-바꾸며-실험하는가)에 있습니다. '
            '아래 현재 실험 표는 **앞선 ID 중 설정 차이가 가장 적은 실험**을 비교 대상으로 고릅니다(동률이면 ID순, 점수는 선택에 사용하지 않음). '
            '연장 단계는 동일한 기초 모델 안에서만 비교합니다. 비교 대상은 실험 설계의 공식 대조군을 뜻하지 않습니다.', '',
            '`primary/recent` 칸: **혼합 전 W_pct (비교 ID 대비 W 상대 변화)**. 낮을수록 좋으며 음수는 개선, 양수는 악화입니다. '
            '두 결과가 모두 정상 완료된 경우만 상대 변화를 계산합니다. 여러 설정이 바뀐 행은 각각의 효과를 분리할 수 없습니다. '
            '대기·실패 행도 설정 차이는 표시하지만 혼합 전 전후 점수를 성공으로 추정하지 않습니다.', '',
            'CSV에는 각 실험의 전체 `config_json`, `base_id→source_generation_id`, `comparison_id`, `changed_settings`, '
            'primary/recent 원래 W와 W_pct, 비교 대상·보정 전 기초 모델 대비 W 변화, `blend_alpha`, 최고 제출 대비 혼합 W 변화를 따로 제공합니다. '
            '실패 후보의 감사로 복원한 혼합 수치는 기존 `audit_gate_pass`와 근거를 함께 확인하세요. '
            '과거 캠페인은 평가 방식이 달라 자동으로 공통 기준을 붙이지 않고 기존 변경 설명·지표 단위·근거를 보존합니다.', '']
        for item in self.campaigns:
            if item['kind']=='current':
                detail += [f"## {item['label']}", '',
                    '| ID / 상태 | 기초 / 비교 ID | 바뀐 설정 | primary W_pct (W 변화) | recent W_pct (W 변화) | alpha / 최고 제출 대비 혼합 W 변화 primary, recent | 완료 기간 / 학습 횟수 | 비고·근거 |',
                    '|---|---|---|---:|---:|---|---|---|']
                for r in item['rows']:
                    scores=[]
                    for fold in ('primary','recent'):
                        delta=r.get(f'{fold}_W_change_pct_vs_comparison')
                        scores.append(number(r.get(f'{fold}_W_pct')) + (f' ({number(delta)}%)' if delta is not None else ''))
                    base=f"{r['base_id']}→{r['source_generation_id']} / " if r['base_id'] else ''
                    blend=f"{number(r.get('blend_alpha'),6)} / {number(r.get('primary_blend_W_change_pct'))}%, {number(r.get('recent_blend_W_change_pct'))}%"
                    detail.append(f"| {r['id']} / {LABELS.get(r['status'],r['status'])} | {base}{r['comparison_id']} | "
                        f"{cell(r['changed_settings'])} ({r['comparison_scope']}) | {scores[0]} | {scores[1]} | {blend} | "
                        f"{r['completed_folds']}/{r['expected_folds']} / {r['recorded_model_fits']} | {cell(r['note'])} "
                        f"{self.link(r['evidence_path'],'기록',prefix='../../')} |")
                if item['bases']:
                    detail += ['', '### 보정 학습용 OOF 기초 모델', '',
                        '| 기초 ID → 발전 모델 | 상태 | 확인된 새 학습 횟수 | 설명·근거 |','|---|---|---:|---|']
                    for r in item['bases']:
                        detail.append(f"| {r['id']} → {r['source_generation_id']} | {LABELS.get(r['status'],r['status'])} | "
                            f"{r['recorded_model_fits']} | {cell(r['note'])} {self.link(r['evidence_path'],'기록',prefix='../../')} |")
                detail.append('')
                continue
            detail += [f"## {item['label']}", '', item.get('note','현재 고정된 실행 큐'), '',
                       '| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |', '|---|---|---|---:|---:|---|---:|---|']
            for r in item['rows'] + item.get('bases', []):
                folds = f"{r.get('completed_folds',0)}/{r['expected_folds']}" if r.get('expected_folds') else '—'
                evidence = self.link(r.get('evidence_path',''), '기록', prefix='../../')
                detail.append(f"| {cell(r['id'])} | {cell(r['kind'])} | {cell(LABELS.get(r['status'],r['status']))} | {folds} | {r.get('recorded_model_fits','—')} | {cell(r.get('metric_name',''))} | {number(r.get('metric_value'))} | {cell(r.get('note',''))} {evidence} |")
            detail.append('')
        buffer = io.StringIO(newline='')
        writer = csv.DictWriter(buffer, fieldnames=FIELDS, extrasaction='ignore', lineterminator='\n')
        writer.writeheader()
        for row in self.rows:
            writer.writerow({key: '' if value is None else value for key,value in row.items()})
        return {'README.md': root_text.encode(), 'analysis_outputs/experiment_overview/README.md': '\n'.join(detail).encode(),
                'analysis_outputs/experiment_overview/experiments.csv': buffer.getvalue().encode('utf-8-sig')}


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = stream.name
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def generate(root=ROOT):
    snapshot = Snapshot(root)
    prior_manifest_path = snapshot.root/'analysis_outputs/experiment_overview/snapshot_manifest.json'
    prior_outputs = json.loads(prior_manifest_path.read_text()).get('outputs_sha256',{}) if prior_manifest_path.exists() else {}
    catalog = snapshot.read('submission/research_reporting/history_catalog.json', required=True)
    snapshot.history(catalog)
    old = snapshot.current(OLD, '기존 10시간 단계')
    new = snapshot.current(NEW, '12시간 연장 단계')
    protected = snapshot.root / 'submission/renew_candidate_20261105/submission_files.zip'
    snapshot.best_ok = protected.is_file() and digest(protected.read_bytes()) == BEST_SHA
    outputs = snapshot.render(catalog, old, new)
    # Preserve manual edits instead of silently overwriting documentation.
    for name in outputs:
        destination = snapshot.root/name
        if destination.exists() and (name not in prior_outputs or digest(destination.read_bytes()) != prior_outputs[name]):
            raise ValueError(f'Document changed outside the generator; preserve and reconcile before refresh: {name}')
    for name, data in outputs.items():
        if len(data) > 2 * 1024 * 1024:
            raise ValueError(f'Public document exceeds 2 MiB: {name}')
        atomic(snapshot.root / name, data)
    source_paths = ['submission/research_reporting/' + name for name in
                    ('update_readme.py','publish_readme.py','history_catalog.json','test_publish_readme.py')
                    if (snapshot.root / 'submission/research_reporting' / name).is_file()]
    source_digest = digest(json.dumps(snapshot.inputs, sort_keys=True).encode())
    manifest = {'created_utc': snapshot.created, 'snapshot_id': source_digest[:16],
        'source_snapshot_sha256': source_digest, 'publisher_sha256': PUBLISHER_SHA,
        'source_sha256': {name: digest((snapshot.root/name).read_bytes()) for name in source_paths},
        'outputs_sha256': {name: digest(data) for name,data in outputs.items()},
        'output_bytes': {name:len(data) for name,data in outputs.items()},
        'experiment_rows': len(snapshot.rows), 'current_counts': {x['id']:x['counts'] for x in (old,new)},
        'historical_catalog_created_utc': catalog.get('created_utc'),
        'source_files_observed': len(snapshot.inputs), 'model_fits':0,'network_requests':0,
        'all_history_previously_exposed':True,'protected_best_sha256_matches':snapshot.best_ok}
    atomic(snapshot.root/'analysis_outputs/experiment_overview/snapshot_manifest.json',
           (json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode())
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(generate(),ensure_ascii=False,indent=2))
