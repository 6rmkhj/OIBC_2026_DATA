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
            self.rows.append(row)
            data_rows.append(row)
        base_rows = []
        for base in self.read(f'{folder}/bases.json') or []:
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
        lines += ['', f"연장 보정용 OOF 기초 설정은 {sum(r['status']=='completed' for r in new['bases'])}/{len(new['bases'])}개 완료됐습니다. 완료 영수증에서 확인되는 실제 모델 학습은 기존 {old['recorded_model_fits']:,}회, 연장 {new['recorded_model_fits']:,}회입니다. 재사용 예측과 중앙값 보정은 학습 횟수에서 제외하며, 영수증 없이 끝난 학습은 세지 않습니다.", '', '## 현재 확인된 문제', '']
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
            '- **W / W_pct는 낮을수록 좋은 내부 오차 지표**입니다. W는 SMP와 벌점 계수를 적용한 절대 오차 합입니다. W_pct는 평가 자료의 발전량·가격 규모로 정규화한 값입니다.',
            '- `c000`은 단일 모델 비교용 기준입니다. **c000 대비 개선률은 기존 최고 제출 모델 대비 개선률이 아닙니다.**',
            '- primary에서 정한 혼합 계수를 recent에 그대로 적용합니다. 다섯 시점의 안정성 기준과 두 기간의 개선 조건을 함께 통과해야 적격 후보가 됩니다.',
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
            '현재 5개 기간 검증에서 결과 저장이 실패한 실험은 완료 영수증 수와 별도로 `failed`로 표시합니다. 모델의 과학적 적격 여부를 최종 결과 없이 추정하지 않습니다.', '']
        for item in self.campaigns:
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
