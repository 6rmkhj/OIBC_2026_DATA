#!/usr/bin/env python3
"""Validate README snapshot publication using disposable local fixtures only."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).with_name("publish_readme.py")
SPEC = importlib.util.spec_from_file_location("readme_publication_under_test", SOURCE)
wrapper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wrapper)
AUDITED = wrapper.load_publisher()


class ReadmePublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="oibc-readme-publication-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "work"
        self.root.mkdir()
        self.now = datetime.now(timezone.utc)
        self.write(wrapper.PUBLISHER_PATH, (wrapper.ROOT / wrapper.PUBLISHER_PATH).read_bytes())
        self.write("submission/research_reporting/update_readme.py", b"# Fixture generator\n")
        self.write("submission/research_reporting/publish_readme.py", SOURCE.read_bytes())
        self.write("submission/research_reporting/history_catalog.json", b'{"fixture": true}\n')
        for path in wrapper.OUTPUT_PATHS:
            self.write(path, b"# Reproducible fixture\n" if path.endswith(".md") else b"id,status\nx,PASS\n")
        self.manifest = {
            "created_utc": self.now.isoformat(), "snapshot_id": "fixture-snapshot",
            "source_snapshot_sha256": "d" * 64, "publisher_sha256": wrapper.PUBLISHER_SHA256,
            "source_sha256": {path: self.sha(path) for path in wrapper.REQUIRED_SOURCES | {
                "submission/research_reporting/history_catalog.json"}},
            "outputs_sha256": {path: self.sha(path) for path in wrapper.OUTPUT_PATHS},
        }
        self.save_manifest()

    def write(self, path, contents):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(contents)

    def sha(self, path):
        return hashlib.sha256((self.root / path).read_bytes()).hexdigest()

    def save_manifest(self):
        AUDITED.atomic_json(self.root / wrapper.MANIFEST_PATH, self.manifest)

    def capture(self):
        evidence = AUDITED.Evidence(self.root)
        summary = wrapper.capture_report(evidence, AUDITED, now=self.now)
        return evidence, summary

    def test_valid_snapshot_adds_only_exact_pinned_reporting_scope(self):
        self.write("private/model.txt", b"unpublished model\n")
        evidence, summary = self.capture()
        expected = set(wrapper.OUTPUT_PATHS) | set(self.manifest["source_sha256"]) | {
            wrapper.MANIFEST_PATH, wrapper.PUBLISHER_PATH}
        self.assertEqual(set(evidence.files), expected)
        self.assertEqual(summary["snapshot_id"], self.manifest["snapshot_id"])
        self.assertEqual(summary["output_files"], 3)

    def test_tampered_output_is_rejected(self):
        self.write("README.md", b"tampered\n")
        with self.assertRaises(AUDITED.Refused):
            self.capture()

    def test_tampered_pinned_source_is_rejected(self):
        self.write("submission/research_reporting/update_readme.py", b"# Changed\n")
        with self.assertRaises(AUDITED.Refused):
            self.capture()

    def test_extra_output_scope_is_rejected(self):
        self.manifest["outputs_sha256"]["unrequested.txt"] = "a" * 64
        self.save_manifest()
        with self.assertRaises(ValueError):
            self.capture()

    def test_unpinned_or_unapproved_reporting_source_is_rejected(self):
        self.manifest["source_sha256"]["submission/research_reporting/unrequested.py"] = "a" * 64
        self.save_manifest()
        with self.assertRaises(ValueError):
            self.capture()

    def test_missing_required_output_is_rejected(self):
        del self.manifest["outputs_sha256"]["README.md"]
        self.save_manifest()
        with self.assertRaises(ValueError):
            self.capture()

    def test_stale_and_future_snapshots_are_rejected(self):
        for offset in (-wrapper.MAX_AGE_SECONDS - 1, wrapper.MAX_FUTURE_SECONDS + 1):
            with self.subTest(offset=offset):
                self.manifest["created_utc"] = (self.now + timedelta(seconds=offset)).isoformat()
                self.save_manifest()
                with self.assertRaises(ValueError):
                    self.capture()

    def test_naive_timestamp_is_rejected(self):
        self.manifest["created_utc"] = self.now.replace(tzinfo=None).isoformat()
        self.save_manifest()
        with self.assertRaises(ValueError):
            self.capture()

    def test_wrong_publisher_hash_is_rejected(self):
        self.manifest["publisher_sha256"] = "0" * 64
        self.save_manifest()
        with self.assertRaises(ValueError):
            self.capture()
        self.write(wrapper.PUBLISHER_PATH, b"# Different publisher\n")
        with self.assertRaises(ValueError):
            wrapper.load_publisher(self.root)

    def test_concurrent_manifest_replacement_is_rejected(self):
        evidence = AUDITED.Evidence(self.root)
        original = evidence.add
        seen = 0

        def changing_capture(path, expected=None):
            nonlocal seen
            if Path(path) == self.root / wrapper.MANIFEST_PATH:
                seen += 1
                if seen == 2:
                    self.manifest["snapshot_id"] = "concurrent-generation"
                    self.save_manifest()
            return original(path, expected)

        with patch.object(evidence, "add", side_effect=changing_capture):
            with self.assertRaises(AUDITED.Refused):
                wrapper.capture_report(evidence, AUDITED, now=self.now)

    def test_shared_pending_commit_then_readme_commit_preserve_work(self):
        environment = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_COUNT": "0"}
        with patch.dict(os.environ, environment):
            remote = Path(self.temporary.name) / "remote.git"
            subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)

            def git(*arguments):
                return subprocess.check_output(["git", "-C", str(self.root), *arguments], stderr=subprocess.DEVNULL).decode().strip()

            git("init", "-q", "-b", "work")
            git("config", "user.name", "Fixture")
            git("config", "user.email", "fixture@example.test")
            self.write("initial.txt", b"initial\n")
            git("add", "initial.txt")
            git("commit", "-qm", "initial")
            initial = git("rev-parse", "HEAD")
            git("remote", "add", "origin", str(remote))
            git("push", "origin", "HEAD:refs/heads/main")
            before = (self.root / ".git/index").read_bytes()
            client = AUDITED.Publisher(self.root, initial, str(remote))
            old = AUDITED.Evidence(self.root)
            old.files = {"old_checkpoint.json": b'{"status": "PASS"}\n'}
            with patch.object(client, "finish_push", side_effect=AUDITED.Refused("fixture interrupted")):
                with self.assertRaises(AUDITED.Refused):
                    client.publish(old)
            pending = json.loads(client.state_path.read_text())["pending"]["commit"]
            evidence, summary = self.capture()
            first = wrapper.publish_snapshot(AUDITED, evidence, summary, client=client)
            self.assertEqual(first["commit"], pending)
            self.assertFalse(first["requested_readme_snapshot_in_commit"])
            second = wrapper.publish_snapshot(AUDITED, evidence, summary, client=client)
            self.assertTrue(second["requested_readme_snapshot_in_commit"])
            self.assertEqual(git("rev-parse", second["commit"] + "^"), pending)
            self.assertEqual(git("rev-parse", "HEAD"), initial)
            self.assertEqual((self.root / ".git/index").read_bytes(), before)
            self.assertEqual(git("show", "-s", "--format=%an <%ae>|%cn <%ce>", second["commit"]),
                             "Codex <codex@openai.com>|Codex <codex@openai.com>")
            self.assertEqual(wrapper.publish_snapshot(AUDITED, evidence, summary, client=client)["status"], "NO_CHANGES")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-json", type=Path)
    arguments = parser.parse_args()
    started = time.monotonic()
    started_utc = datetime.now(timezone.utc).isoformat()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReadmePublicationTests)
    cases = [case.id().split(".")[-1] for case in suite]
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if arguments.audit_json:
        AUDITED.atomic_json(arguments.audit_json, {
            "status": "PASS" if result.wasSuccessful() else "FAIL", "cases": cases,
            "cases_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
            "started_utc": started_utc, "finished_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": time.monotonic() - started, "exit_code": 0 if result.wasSuccessful() else 1,
            "publisher_source_sha256": wrapper.PUBLISHER_SHA256,
            "wrapper_source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "test_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "temporary_local_git_repositories_only": True, "github_contacted": False,
            "research_git_refs_and_index_modified": False,
        })
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
