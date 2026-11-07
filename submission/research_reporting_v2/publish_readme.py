#!/usr/bin/env python3
"""Publish the additional research stage and its validated README snapshot.

The original publisher remains unchanged. Its lock, pending commit, dedicated
ref, author identity and protection of the working HEAD/index are shared.
Default execution is a local dry run; only --publish permits an ordinary push.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
STAGE = "research_23kst_20261108"
STAGE_ROOT = f"analysis_outputs/{STAGE}"
OVERVIEW = "analysis_outputs/experiment_overview_v2"
MANIFEST_PATH = f"{OVERVIEW}/snapshot_manifest.json"
PUBLISHER_PATH = "submission/score_push_22h/checkpoint_git.py"
PUBLISHER_SHA256 = "89d2e4276195847792b7cf31d5d22339fee0a8bd0fb904110a38e996b51ea109"
FROZEN_DEPENDENCIES = {
    "submission/research_reporting/update_readme.py": "651be8197f8f7784cb7d90f27ab9536d50c835473d5cea324822c2f094863f10",
    "submission/research_reporting/history_catalog.json": "0e3fdbb59d52290af2e92e9491d13160fe2a809723529e6d6defb2fa0f2518d1",
}
REQUIRED_SOURCES = frozenset(FROZEN_DEPENDENCIES) | {
    "submission/research_reporting_v2/update_readme.py",
    "submission/research_reporting_v2/publish_readme.py",
}
ALLOWED_SOURCES = REQUIRED_SOURCES | {
    "submission/research_reporting_v2/test_update_readme.py",
    "submission/research_reporting_v2/test_publish_readme.py",
    "submission/research_reporting_v2/README.md",
}
REQUIRED_OUTPUTS = frozenset({"README.md", f"{OVERVIEW}/README.md", f"{OVERVIEW}/experiments.csv"})
DEADLINE = datetime(2026, 11, 8, 14, tzinfo=timezone.utc)
SEARCH_STOP = datetime(2026, 11, 8, 12, tzinfo=timezone.utc)
MAX_AGE_SECONDS = 900
MAX_FUTURE_SECONDS = 120
MAX_CSV_PARTS = 64


def load_publisher(root=ROOT):
    path = Path(root) / PUBLISHER_PATH
    source = path.read_bytes()
    if path.is_symlink() or hashlib.sha256(source).hexdigest() != PUBLISHER_SHA256:
        raise ValueError("Audited publisher source hash changed")
    spec = importlib.util.spec_from_file_location("oibc_unchanged_checkpoint_publisher", path)
    module = importlib.util.module_from_spec(spec)
    # Execute the exact bytes whose hash was checked, avoiding a second read.
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def hash_mapping(value, required, allowed, label):
    if not isinstance(value, dict) or not required.issubset(value) or not set(value).issubset(allowed):
        raise ValueError(f"{label} paths do not match the exact publication scope")
    if any(not isinstance(x, str) or not re.fullmatch(r"[0-9a-f]{64}", x) for x in value.values()):
        raise ValueError(f"Invalid SHA256 in {label}")


def output_paths(mapping):
    if not isinstance(mapping, dict) or not REQUIRED_OUTPUTS.issubset(mapping):
        raise ValueError("Required README/CSV outputs are missing")
    parts = []
    for relative in set(mapping) - REQUIRED_OUTPUTS:
        match = re.fullmatch(re.escape(OVERVIEW) + r"/experiments_part_(\d{3})\.csv", relative)
        if not match or not 1 <= int(match[1]) <= MAX_CSV_PARTS:
            raise ValueError("Unexpected reporting output path")
        parts.append(int(match[1]))
    if sorted(parts) != list(range(1, len(parts) + 1)):
        raise ValueError("CSV parts must be consecutive from001")
    hash_mapping(mapping, REQUIRED_OUTPUTS, set(mapping), "output")
    return set(mapping)


def capture_stage(evidence):
    """Extend only the new namespace; the old campaign capture stays unchanged."""
    folder = evidence.root / STAGE_ROOT
    if not folder.is_dir():
        raise ValueError("The additional campaign is unavailable in this environment")
    # Check source extension scope before the generic frozen collector follows
    # a source pin. Existing captured sources remain valid dependencies.
    for name in ("protocol.json", "publication_pins.json"):
        path = folder / name
        if not path.exists():
            continue
        pins = evidence.add(path).get("source_sha256", {})
        for relative in pins:
            new_code = re.fullmatch(r"submission/score_push_23kst/[A-Za-z0-9_]+\.py", relative)
            if relative not in evidence.files and relative not in ALLOWED_SOURCES and not new_code and relative not in {
                "submission/score_push_23kst/README.md", "submission/validate_artifacts.py"}:
                raise ValueError(f"New campaign source lies outside the approved extension: {relative}")
    evidence.campaign(STAGE)
    if not (folder / "protocol.json").exists():
        raise ValueError("The additional campaign has no frozen protocol yet")
    evidence.optional(folder, ["authorization.json", "CAMPAIGN.md", "launch_contract.json",
        "final_verification_contract.json", "continuation_spec.json", "recovery_registry.json",
        "selection_contract.json", "reporting_contract.json", "recovered/result.json",
        "assemble/result.json", "shared/search_data_manifest.json"])
    protocol = json.loads(evidence.files[f"{STAGE_ROOT}/protocol.json"])
    required_folds = set(protocol.get("folds", {}))
    required_seeds = protocol.get("search_seeds", [])
    if not required_folds or required_seeds != [0, 1, 2]:
        raise ValueError("New campaign fold/seed contract is incomplete")
    # Averaged fold scores alone are insufficient publication evidence for a
    # completed trial: every declared seed/fold needs its matching receipt.
    for identifier in evidence.completed.get(STAGE, {}).get("trials", []):
        relative = f"{STAGE_ROOT}/trials/{identifier}"
        result = json.loads(evidence.files[f"{relative}/result.json"])
        if result.get("status") != "PASS":
            continue
        if set(result.get("folds", {})) != required_folds:
            raise ValueError("Finalized new trial is missing declared fold scores")
        for seed in required_seeds:
            for fold in required_folds:
                key = f"{relative}/seed{seed}/{fold}/receipt.json"
                if key not in evidence.files:
                    raise ValueError("Finalized new trial is missing a seed/fold receipt")
                receipt = json.loads(evidence.files[key])
                if receipt.get("seed") != seed or receipt.get("fold") != fold or receipt.get("config") != result.get("config"):
                    raise ValueError("New trial receipt does not match its seed/fold/config")
    counts = {}
    for directory, label in (("recovered", "recovered_prior_failures"), ("validation", "new_seed_validations")):
        ids = []
        for path in sorted((folder / directory).glob("*/result.json")):
            if directory == "recovered":
                value = evidence.add(path)
                if (value.get("status") != "RECOVERED_DIAGNOSTIC" or value.get("eligible") is not False
                        or value.get("real_model_fits") != 0):
                    raise ValueError("Recovered prior failure must remain a diagnostic with zero new fits")
            else:
                evidence.finalized_unit(path.parent)
                value = json.loads(evidence.files[path.relative_to(evidence.root).as_posix()])
                if value.get("status") == "PASS":
                    if value.get("diagnostics_only") is not True or value.get("eligible") is not False:
                        raise ValueError("Seed validation must remain diagnostic, not a promoted candidate")
                    for seed in (1, 2):
                        for fold in ("primary", "recent"):
                            key = f"{STAGE_ROOT}/validation/{path.parent.name}/seed{seed}/{fold}/receipt.json"
                            if key not in evidence.files:
                                raise ValueError("Finished validation is missing a new seed/fold receipt")
                            receipt = json.loads(evidence.files[key])
                            if receipt.get("seed") != seed or receipt.get("fold") != fold:
                                raise ValueError("Validation receipt does not match its new seed/fold")
            ids.append(path.parent.name)
        counts[label] = ids
    evidence.completed.setdefault(STAGE, {}).update(counts)
    evidence.summaries.setdefault(STAGE, {}).update({
        "recovered_prior_failure_results": len(counts["recovered_prior_failures"]),
        "new_seed_validation_results": len(counts["new_seed_validations"]),
        "recovery_is_not_new_training": True,
        "deadline_utc": DEADLINE.isoformat(), "search_stop_utc": SEARCH_STOP.isoformat(),
    })


def capture_report(evidence, audited, now=None):
    manifest_path = evidence.root / MANIFEST_PATH
    manifest = evidence.add(manifest_path)
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 2:
        raise ValueError("Reporting snapshot must use schema_version2")
    if manifest.get("publisher_sha256") != PUBLISHER_SHA256:
        raise ValueError("Reporting snapshot does not identify the frozen publisher")
    evidence.add(evidence.root / PUBLISHER_PATH, PUBLISHER_SHA256)
    sources, outputs = manifest.get("source_sha256"), manifest.get("outputs_sha256")
    hash_mapping(sources, REQUIRED_SOURCES, ALLOWED_SOURCES, "source")
    output_paths(outputs)
    for relative, expected in FROZEN_DEPENDENCIES.items():
        if sources.get(relative) != expected:
            raise ValueError("A frozen reporting dependency pin changed")
    for field, expected in (("deadline_utc", DEADLINE), ("search_stop_utc", SEARCH_STOP)):
        if datetime.fromisoformat(str(manifest.get(field, ""))) != expected:
            raise ValueError(f"Reporting snapshot has an incorrect {field}")
    if not isinstance(manifest.get("snapshot_id"), str) or not 1 <= len(manifest["snapshot_id"]) <= 256:
        raise ValueError("Snapshot ID is missing or invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", str(manifest.get("source_snapshot_sha256", ""))):
        raise ValueError("Source snapshot SHA256 is invalid")
    created = datetime.fromisoformat(str(manifest.get("created_utc", "")))
    if created.tzinfo is None:
        raise ValueError("Snapshot creation time must include a timezone")
    age = ((now or datetime.now(timezone.utc)) - created).total_seconds()
    if not -MAX_FUTURE_SECONDS <= age <= MAX_AGE_SECONDS:
        raise ValueError("Reporting snapshot is stale or future-dated; regenerate it")
    for relative, expected in sorted({**sources, **outputs}.items()):
        evidence.add(evidence.root / relative, expected)
    evidence.add(manifest_path)
    summary = {
        "snapshot_id": manifest["snapshot_id"], "created_utc": manifest["created_utc"],
        "manifest_sha256": audited.digest(evidence.files[MANIFEST_PATH]),
        "source_snapshot_sha256": manifest["source_snapshot_sha256"],
        "output_files": len(outputs), "pinned_source_files": len(sources),
        "snapshot_age_seconds_at_capture": age, "deadline_utc": DEADLINE.isoformat(),
        "search_stop_utc": SEARCH_STOP.isoformat(), "recovery_is_not_new_training": True,
        "all_historical_periods_previously_exposed": True,
    }
    evidence.summaries["experiment_overview_v2"] = summary
    return summary


def gather(root=ROOT, now=None):
    audited = load_publisher(root)
    evidence = audited.Evidence(root).gather()
    capture_stage(evidence)
    summary = capture_report(evidence, audited, now)
    return audited, evidence, summary


def publish_snapshot(audited, evidence, summary, client=None):
    client = client or audited.Publisher(evidence.root)
    result = client.publish(evidence)
    commit = result.get("commit")
    actual = client.git("show", f"{commit}:{MANIFEST_PATH}", check=False) if commit else None
    result["requested_readme_snapshot_in_commit"] = bool(actual is not None and actual.returncode == 0
        and actual.stdout == evidence.files[MANIFEST_PATH])
    result["requested_readme_snapshot_id"] = summary["snapshot_id"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--publish", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    parser.add_argument("--inventory", type=Path)
    args = parser.parse_args()
    audited, evidence, summary = gather()
    if args.publish:
        result = publish_snapshot(audited, evidence, summary)
    else:
        if args.inventory:
            audited.atomic_json(args.inventory, {"created_utc": audited.utc(), "files": evidence.inventory(),
                "summary": evidence.summaries, "completed": evidence.completed, "excluded": evidence.omitted})
        result = {"status": "DRY_RUN", "files": len(evidence.files), "bytes": sum(map(len, evidence.files.values())),
            "readme_snapshot": summary, "author": audited.IDENTITY, "local_ref": audited.LOCAL_REF,
            "shared_state": ".git/codex-checkpoints/state.json", "inventory": str(args.inventory) if args.inventory else None,
            "working_head_and_index_will_remain_unchanged": True}
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
