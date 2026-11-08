#!/usr/bin/env python3
"""Publish only reviewed text evidence through the unchanged shared publisher."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
STAGE = 'research_novel_20261108'
STAGE_ROOT = 'analysis_outputs/' + STAGE
OVERVIEW = 'analysis_outputs/experiment_overview_v3'
MANIFEST_PATH = OVERVIEW + '/snapshot_manifest.json'
PUBLISHER_PATH = 'submission/score_push_22h/checkpoint_git.py'
PUBLISHER_SHA256 = '89d2e4276195847792b7cf31d5d22339fee0a8bd0fb904110a38e996b51ea109'
V2_PATH = 'submission/research_reporting_v2/publish_readme.py'
FROZEN_DEPENDENCIES = {
    'submission/research_reporting/update_readme.py': '651be8197f8f7784cb7d90f27ab9536d50c835473d5cea324822c2f094863f10',
    'submission/research_reporting/history_catalog.json': '0e3fdbb59d52290af2e92e9491d13160fe2a809723529e6d6defb2fa0f2518d1',
    'submission/research_reporting_v2/update_readme.py': 'f392d7e8806ed8b200797c9e7036cc8cc7947f2ec9755ba97460a0a08cb07f2a',
    V2_PATH: '24c471810a1b9548b2f06a836838f25a8514ffd0617abec56a1d17d30698ada2',
}
SHARED_SOURCE_PINS = {
    'submission/validate_artifacts.py': '89e4a757bdada17cc523c948a59408caadc641566d454533021e9c5a3475031f',
}
REQUIRED_SOURCES = frozenset(FROZEN_DEPENDENCIES) | {'submission/research_reporting_v3/update_readme.py', 'submission/research_reporting_v3/publish_readme.py'}
ALLOWED_SOURCES = REQUIRED_SOURCES | {'submission/research_reporting_v3/test_update_readme.py', 'submission/research_reporting_v3/test_publish_readme.py', 'submission/research_reporting_v3/README.md'}
REQUIRED_OUTPUTS = frozenset({'README.md', OVERVIEW + '/README.md', OVERVIEW + '/experiments.csv'})
DEADLINE = datetime(2026, 11, 8, 14, tzinfo=timezone.utc)
SEARCH_STOP = datetime(2026, 11, 8, 12, tzinfo=timezone.utc)
MAX_AGE_SECONDS = 900
MAX_FUTURE_SECONDS = 120
MAX_CSV_PARTS = 64

def load_frozen(root, relative, expected, name):
    path = Path(root) / relative; source = path.read_bytes()
    if path.is_symlink() or hashlib.sha256(source).hexdigest() != expected:
        raise ValueError('Frozen source hash changed: ' + relative)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, str(path), 'exec'), module.__dict__)
    return module

def load_publisher(root=ROOT):
    return load_frozen(root, PUBLISHER_PATH, PUBLISHER_SHA256, 'oibc_original_publisher_for_v3')

def hash_mapping(mapping, required, allowed, label):
    if not isinstance(mapping, dict) or not required.issubset(mapping) or not set(mapping).issubset(allowed):
        raise ValueError(label + ' paths do not match the exact scope')
    if any(not isinstance(v, str) or not re.fullmatch('[0-9a-f]{64}', v) for v in mapping.values()):
        raise ValueError('Invalid SHA256 in ' + label)

def output_paths(mapping):
    if not isinstance(mapping, dict) or not REQUIRED_OUTPUTS.issubset(mapping):
        raise ValueError('Required report outputs missing')
    parts = []
    for path in set(mapping) - REQUIRED_OUTPUTS:
        match = re.fullmatch(re.escape(OVERVIEW) + r'/experiments_part_(\d{3})\.csv', path)
        if not match or not 1 <= int(match[1]) <= MAX_CSV_PARTS:
            raise ValueError('Unexpected reporting output')
        parts.append(int(match[1]))
    if sorted(parts) != list(range(1, len(parts) + 1)):
        raise ValueError('CSV parts must be consecutive')
    hash_mapping(mapping, REQUIRED_OUTPUTS, set(mapping), 'output')

def reject_model_payload(value, path):
    """Model coefficients are intentionally private even when stored as JSON."""
    if isinstance(value, dict):
        forbidden = {'transport_model', 'coefficients', 'learned_weights', 'model_parameters'}
        if forbidden.intersection(value):
            raise ValueError('Learned model payload is outside public scope: ' + str(path))
        for child in value.values(): reject_model_payload(child, path)
    elif isinstance(value, list):
        for child in value: reject_model_payload(child, path)

def capture_stage(evidence):
    folder = evidence.root / STAGE_ROOT
    if not (folder / 'protocol.json').is_file(): raise ValueError('Novel protocol is not frozen')
    for name in ('protocol.json', 'publication_pins.json'):
        path = folder / name
        if not path.exists(): continue
        value = evidence.add(path)
        for relative, expected in value.get('source_sha256', {}).items():
            if relative in SHARED_SOURCE_PINS and expected != SHARED_SOURCE_PINS[relative]:
                raise ValueError('Shared validator source pin changed: ' + relative)
            novel_code = re.fullmatch(r'submission/score_push_novel/[A-Za-z0-9_]+\.py', relative)
            if relative not in evidence.files and relative not in ALLOWED_SOURCES and relative not in SHARED_SOURCE_PINS and not novel_code and relative != 'submission/score_push_novel/README.md':
                raise ValueError('Unapproved novel source pin: ' + relative)
    # Collect only explicitly named public metadata rather than recursively
    # following completion/model JSON files.
    protocol = evidence.pins(folder / 'protocol.json')
    evidence.pins(folder / 'publication_pins.json')
    for filename, field in [('configs.json', 'configs_sha256'), ('jobs.json', 'jobs_sha256'), ('bases.json', 'bases_sha256')]:
        if (folder / filename).exists(): evidence.add(folder / filename, protocol.get(field))
    evidence.optional(folder, ['authorization.json', 'CAMPAIGN.md', 'controller_manifest.json', 'launch_contract.json',
        'final_verification_contract.json', 'reporting_contract.json', 'selection_contract.json', 'prepare/result.json'])
    for path in sorted(folder.glob('independent*.json')):
        value = evidence.add(path); reject_model_payload(value, path)
    configs = json.loads(evidence.files[STAGE_ROOT + '/configs.json'])
    config_map = {config['id']: config for config in configs}
    if len(config_map) != len(configs) or any(not re.fullmatch('[A-Za-z0-9_-]+', str(x)) for x in config_map):
        raise ValueError('Novel config IDs are not unique safe names')
    expected_folds = protocol.get('evaluation_folds', ['primary', 'recent'])
    predictions = protocol.get('required_prediction_files', ['primary.parquet', 'recent.parquet'])
    if expected_folds != ['primary', 'recent'] or predictions != ['primary.parquet', 'recent.parquet']:
        raise ValueError('Novel evaluation publication contract changed')
    completed = []
    for path in sorted((folder / 'trials').glob('*/result.json')):
        identifier = path.parent.name
        if identifier not in config_map: raise ValueError('Unknown finalized novel trial')
        result = evidence.add(path); reject_model_payload(result, path)
        if result.get('status') != 'PASS':
            if result.get('status') not in {'FAIL', 'FAILED', 'ERROR', 'TIMEOUT', 'CHECKPOINT_ONLY'}:
                raise ValueError('Unknown result status')
            completed.append(identifier); continue
        config = config_map[identifier]
        if result.get('id') != identifier or result.get('config') != config or result.get('real_model_fits') != 1:
            raise ValueError('Novel finalized result identity mismatch')
        if set(result.get('metrics', {})) != set(expected_folds):
            raise ValueError('Novel completed result lacks declared evaluation metrics')
        receipt_path = path.parent / 'receipt.json'
        receipt = evidence.add(receipt_path, result.get('receipt_sha256'))
        reject_model_payload(receipt, receipt_path)
        if receipt.get('status') != 'PASS' or receipt.get('id') != identifier or receipt.get('config') != config or receipt.get('real_model_fits') != 1:
            raise ValueError('Novel trial receipt/config/fit count mismatch')
        artifact_hashes = receipt.get('files_sha256', {})
        hash_mapping(artifact_hashes, {'model.json', *predictions}, {'model.json', *predictions}, 'private trial artifact')
        for name, expected in artifact_hashes.items():
            artifact = path.parent / name
            if artifact.is_symlink() or not artifact.is_file() or hashlib.sha256(artifact.read_bytes()).hexdigest() != expected:
                raise ValueError('Completed private artifact missing or changed: ' + str(artifact))
        if result.get('model_sha256') != artifact_hashes['model.json']:
            raise ValueError('Result model hash differs from receipt')
        completed.append(identifier)
    for name in ['completion/result.json', 'completion/audit.json', 'completion/budget_stop.json']:
        path = folder / name
        if path.exists():
            value = evidence.add(path); reject_model_payload(value, path)
    # selection_frozen may contain learned weights, so never capture it by
    # filename alone. Hash references in audited completion metadata suffice.
    evidence.completed[STAGE] = {'trials': completed}
    evidence.summaries[STAGE] = {'finished_trials':len(completed), 'deterministic_primary_fits':True,
        'recent_is_development_transfer':True, 'learned_models_and_predictions_excluded':True,
        'deadline_utc':DEADLINE.isoformat(), 'search_stop_utc':SEARCH_STOP.isoformat()}

def capture_report(evidence, audited, now=None):
    path = evidence.root / MANIFEST_PATH; manifest = evidence.add(path)
    if manifest.get('schema_version') != 3 or manifest.get('publisher_sha256') != PUBLISHER_SHA256:
        raise ValueError('Incorrect snapshot version or publisher hash')
    sources, outputs = manifest.get('source_sha256'), manifest.get('outputs_sha256')
    hash_mapping(sources, REQUIRED_SOURCES, ALLOWED_SOURCES, 'source'); output_paths(outputs)
    for relative, expected in FROZEN_DEPENDENCIES.items():
        if sources.get(relative) != expected: raise ValueError('Historical reporting dependency changed')
    for field, expected in [('deadline_utc', DEADLINE), ('search_stop_utc', SEARCH_STOP)]:
        if datetime.fromisoformat(str(manifest.get(field, ''))) != expected: raise ValueError('Wrong report deadline')
    if not isinstance(manifest.get('snapshot_id'), str) or not 1 <= len(manifest['snapshot_id']) <= 256:
        raise ValueError('Invalid snapshot ID')
    if not re.fullmatch('[0-9a-f]{64}', str(manifest.get('source_snapshot_sha256', ''))): raise ValueError('Invalid source digest')
    created = datetime.fromisoformat(str(manifest.get('created_utc', '')))
    if created.tzinfo is None: raise ValueError('Snapshot timestamp lacks timezone')
    age = ((now or datetime.now(timezone.utc)) - created).total_seconds()
    if not -MAX_FUTURE_SECONDS <= age <= MAX_AGE_SECONDS: raise ValueError('Snapshot stale or future-dated; regenerate')
    evidence.add(evidence.root / PUBLISHER_PATH, PUBLISHER_SHA256)
    for relative, expected in sorted({**sources, **outputs}.items()): evidence.add(evidence.root / relative, expected)
    evidence.add(path)
    summary = {'snapshot_id':manifest['snapshot_id'], 'created_utc':manifest['created_utc'],
        'manifest_sha256':audited.digest(evidence.files[MANIFEST_PATH]), 'source_snapshot_sha256':manifest['source_snapshot_sha256'],
        'output_files':len(outputs), 'pinned_source_files':len(sources), 'snapshot_age_seconds_at_capture':age,
        'all_historical_periods_previously_exposed':True}
    evidence.summaries['experiment_overview_v3'] = summary
    return summary

def gather(root=ROOT, now=None):
    audited = load_publisher(root)
    v2 = load_frozen(root, V2_PATH, FROZEN_DEPENDENCIES[V2_PATH], 'oibc_v2_capture_for_v3')
    evidence = audited.Evidence(root).gather()
    v2.capture_stage(evidence)
    capture_stage(evidence)
    summary = capture_report(evidence, audited, now)
    return audited, evidence, summary

def publish_snapshot(audited, evidence, summary, client=None):
    client = client or audited.Publisher(evidence.root)
    result = client.publish(evidence); commit = result.get('commit')
    actual = client.git('show', f'{commit}:{MANIFEST_PATH}', check=False) if commit else None
    result['requested_readme_snapshot_in_commit'] = bool(actual is not None and actual.returncode == 0 and actual.stdout == evidence.files[MANIFEST_PATH])
    result['requested_readme_snapshot_id'] = summary['snapshot_id']
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(); mode.add_argument('--publish', action='store_true'); mode.add_argument('--dry-run', action='store_true')
    parser.add_argument('--inventory', type=Path); args = parser.parse_args()
    audited, evidence, summary = gather()
    if args.publish: result = publish_snapshot(audited, evidence, summary)
    else:
        if args.inventory: audited.atomic_json(args.inventory, {'files':evidence.inventory(), 'summary':evidence.summaries, 'completed':evidence.completed, 'excluded':evidence.omitted})
        result = {'status':'DRY_RUN', 'files':len(evidence.files), 'bytes':sum(map(len, evidence.files.values())), 'readme_snapshot':summary,
            'author':audited.IDENTITY, 'local_ref':audited.LOCAL_REF, 'shared_state':'.git/codex-checkpoints/state.json'}
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
