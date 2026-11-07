#!/usr/bin/env python3
"""Publish a validated README snapshot through the unchanged audited publisher.

Run update_readme.py first. This command is a local dry run unless --publish is
explicitly supplied. Publication shares the original publisher's lock, pending
state, dedicated ref, Codex identity, and protection of the work HEAD/index.
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
PUBLISHER_PATH = "submission/score_push_22h/checkpoint_git.py"
PUBLISHER_SHA256 = "89d2e4276195847792b7cf31d5d22339fee0a8bd0fb904110a38e996b51ea109"
MANIFEST_PATH = "analysis_outputs/experiment_overview/snapshot_manifest.json"
REQUIRED_SOURCES = frozenset({
    "submission/research_reporting/update_readme.py",
    "submission/research_reporting/publish_readme.py",
})
ALLOWED_SOURCES = REQUIRED_SOURCES | {
    "submission/research_reporting/test_publish_readme.py",
    "submission/research_reporting/history_catalog.json",
}
OUTPUT_PATHS = frozenset({
    "README.md",
    "analysis_outputs/experiment_overview/README.md",
    "analysis_outputs/experiment_overview/experiments.csv",
})
MAX_AGE_SECONDS = 15 * 60
MAX_FUTURE_SECONDS = 120


def load_publisher(root=ROOT):
    path = Path(root) / PUBLISHER_PATH
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != PUBLISHER_SHA256:
        raise ValueError("Audited publisher source hash does not match the frozen source")
    spec = importlib.util.spec_from_file_location("oibc_audited_checkpoint_publisher", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_hash_mapping(value, required, allowed, label):
    if not isinstance(value, dict) or not required.issubset(value) or not set(value).issubset(allowed):
        raise ValueError(f"Snapshot {label} paths do not match the exact allowlist")
    if any(not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha) for sha in value.values()):
        raise ValueError(f"Snapshot {label} contains an invalid SHA256")


def capture_report(evidence, audited, now=None):
    """Add only the explicitly pinned, internally consistent reporting snapshot."""
    manifest_path = evidence.root / MANIFEST_PATH
    manifest = evidence.add(manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError("Snapshot manifest must be a JSON object")
    if manifest.get("publisher_sha256") != PUBLISHER_SHA256:
        raise ValueError("Snapshot was not generated for the frozen audited publisher")
    actual_publisher = evidence.root / PUBLISHER_PATH
    evidence.add(actual_publisher, PUBLISHER_SHA256)
    sources, outputs = manifest.get("source_sha256"), manifest.get("outputs_sha256")
    validate_hash_mapping(sources, REQUIRED_SOURCES, ALLOWED_SOURCES, "source")
    validate_hash_mapping(outputs, OUTPUT_PATHS, OUTPUT_PATHS, "output")
    if not isinstance(manifest.get("snapshot_id"), str) or not 1 <= len(manifest["snapshot_id"]) <= 256:
        raise ValueError("Snapshot identifier is missing or invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", str(manifest.get("source_snapshot_sha256", ""))):
        raise ValueError("Source snapshot SHA256 is missing or invalid")
    created = datetime.fromisoformat(str(manifest.get("created_utc", "")))
    if created.tzinfo is None:
        raise ValueError("Snapshot creation time must include its timezone")
    now = now or datetime.now(timezone.utc)
    age = (now - created).total_seconds()
    if age > MAX_AGE_SECONDS or age < -MAX_FUTURE_SECONDS:
        raise ValueError("README snapshot is stale or future-dated; regenerate it before publication")
    for relative, expected in sorted({**sources, **outputs}.items()):
        evidence.add(evidence.root / relative, expected)
    # A concurrent generator can replace the manifest atomically. The audited
    # Evidence collector rejects a second capture if its bytes have changed.
    evidence.add(manifest_path)
    summary = {
        "snapshot_id": manifest["snapshot_id"], "created_utc": manifest["created_utc"],
        "source_snapshot_sha256": manifest["source_snapshot_sha256"],
        "manifest_sha256": audited.digest(evidence.files[MANIFEST_PATH]),
        "output_files": len(outputs), "pinned_source_files": len(sources),
        "snapshot_age_seconds_at_capture": age,
        "historical_results_are_descriptive_not_new_official_scores": True,
    }
    evidence.summaries["experiment_overview"] = summary
    return summary


def gather(root=ROOT, now=None):
    audited = load_publisher(root)
    evidence = audited.Evidence(root).gather()
    summary = capture_report(evidence, audited, now=now)
    return audited, evidence, summary


def publish_snapshot(audited, evidence, summary, client=None):
    client = client or audited.Publisher(evidence.root)
    result = client.publish(evidence)
    # A saved pending commit predating this capture must finish first. Confirm
    # the requested manifest in the actual commit instead of claiming success.
    commit = result.get("commit")
    manifest_blob = client.git("show", f"{commit}:{MANIFEST_PATH}", check=False) if commit else None
    result["requested_readme_snapshot_in_commit"] = bool(
        manifest_blob is not None and manifest_blob.returncode == 0
        and manifest_blob.stdout == evidence.files[MANIFEST_PATH])
    result["requested_readme_snapshot_id"] = summary["snapshot_id"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--publish", action="store_true", help="Publish through the original shared checkpoint state/ref")
    mode.add_argument("--dry-run", action="store_true", help="Validate local captured files only (default)")
    parser.add_argument("--inventory", type=Path, help="Save the complete local dry-run file inventory as JSON")
    arguments = parser.parse_args()
    audited, evidence, summary = gather()
    if arguments.publish:
        result = publish_snapshot(audited, evidence, summary)
    else:
        if arguments.inventory:
            audited.atomic_json(arguments.inventory, {
                "created_utc": audited.utc(), "files": evidence.inventory(),
                "completed": evidence.completed, "summary": evidence.summaries, "excluded": evidence.omitted,
            })
        result = {
            "status": "DRY_RUN", "files": len(evidence.files), "bytes": sum(map(len, evidence.files.values())),
            "readme_snapshot": summary, "readme_output_paths": sorted(OUTPUT_PATHS),
            "author": audited.IDENTITY, "local_ref": audited.LOCAL_REF,
            "shared_publisher_state": ".git/codex-checkpoints/state.json",
            "working_head_and_index_will_remain_unchanged": True,
            "inventory": str(arguments.inventory) if arguments.inventory else None,
        }
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
