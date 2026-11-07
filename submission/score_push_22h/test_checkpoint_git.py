#!/usr/bin/env python3
"""Reproduce publisher safety checks using disposable local Git repositories.

No test contacts GitHub or mutates the research repository's Git refs/index.
Optionally pass --audit-json PATH to save a small public validation receipt.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
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


SOURCE = Path(__file__).with_name("checkpoint_git.py")
SPEC = importlib.util.spec_from_file_location("checkpoint_git_under_test", SOURCE)
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)


def git(root, *arguments, input=None):
    result = subprocess.run(["git", "-C", str(root), *arguments], input=input,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return result.stdout.decode().strip()


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_COUNT": "0",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.directory = tempfile.TemporaryDirectory(prefix="oibc-publisher-test-")
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.remote = self.base / "remote.git"
        self.root = self.base / "work"
        self.root.mkdir()
        subprocess.run(["git", "init", "--bare", "-q", str(self.remote)], check=True)
        git(self.root, "init", "-q", "-b", "work")
        git(self.root, "config", "user.name", "Fixture")
        git(self.root, "config", "user.email", "fixture@example.test")
        (self.root / "initial.txt").write_text("initial\n")
        git(self.root, "add", "initial.txt")
        git(self.root, "commit", "-qm", "initial")
        self.initial = git(self.root, "rev-parse", "HEAD")
        git(self.root, "remote", "add", "origin", str(self.remote))
        git(self.root, "push", "origin", "HEAD:refs/heads/main")
        self.client = publisher.Publisher(self.root, self.initial, str(self.remote))
        self.evidence = publisher.Evidence(self.root)
        self.evidence.files = {"submission/sample.py": b'print("checkpoint")\n'}
        self.evidence.completed = {"fixture": {"trials": ["done"], "crossfit_bases": []}}

    def test_codex_identity_and_exact_fast_forward_preserve_work(self):
        index = (self.root / ".git/index").read_bytes()
        result = self.client.publish(self.evidence)
        self.assertEqual(result["status"], "PUSHED")
        commit = result["commit"]
        self.assertEqual(git(self.remote, "rev-parse", "main"), commit)
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), self.initial)
        self.assertEqual((self.root / ".git/index").read_bytes(), index)
        self.assertEqual(git(self.root, "rev-parse", f"{commit}^"), self.initial)
        self.assertEqual(git(self.root, "show", "-s", "--format=%an <%ae>|%cn <%ce>", commit),
                         "Codex <codex@openai.com>|Codex <codex@openai.com>")
        self.assertEqual(git(self.root, "show", f"{commit}:submission/sample.py"), 'print("checkpoint")')

    def test_no_empty_commit_and_multiple_checkpoint_ancestry(self):
        first = self.client.publish(self.evidence)["commit"]
        self.assertEqual(self.client.publish(self.evidence)["status"], "NO_CHANGES")
        self.evidence.files["submission/sample.py"] = b'print("second")\n'
        second = self.client.publish(self.evidence)["commit"]
        self.assertEqual(git(self.root, "rev-parse", f"{second}^"), first)
        self.assertEqual(self.client.publish(self.evidence)["commit"], second)

    def test_staged_changes_are_refused_without_index_mutation(self):
        (self.root / "unrelated.txt").write_text("user work\n")
        git(self.root, "add", "unrelated.txt")
        staged = (self.root / ".git/index").read_bytes()
        with self.assertRaises(publisher.Refused):
            self.client.publish(self.evidence)
        self.assertEqual((self.root / ".git/index").read_bytes(), staged)
        self.assertEqual(git(self.remote, "rev-parse", "main"), self.initial)

    def test_pending_commit_recovers_before_ref_or_push_mutation(self):
        with patch.object(self.client, "finish_push", side_effect=publisher.Refused("fixture interrupted")):
            with self.assertRaises(publisher.Refused):
                self.client.publish(self.evidence)
        pending = json.loads(self.client.state_path.read_text())["pending"]["commit"]
        self.assertEqual(git(self.remote, "rev-parse", "main"), self.initial)
        self.assertEqual(self.client.git("rev-parse", "--verify", self.client.local_ref, check=False).returncode, 128)
        recovered = self.client.publish(self.evidence)
        self.assertEqual(recovered["commit"], pending)
        self.assertTrue((self.root / recovered["inventory"]).exists())
        self.assertEqual(self.client.publish(self.evidence)["status"], "NO_CHANGES")

    def test_unexpected_remote_advance_is_refused(self):
        first = self.client.publish(self.evidence)["commit"]
        tree = git(self.root, "rev-parse", f"{first}^{{tree}}")
        other = git(self.root, "commit-tree", tree, "-p", first, input=b"other writer\n")
        git(self.root, "push", "origin", f"{other}:refs/heads/main")
        with self.assertRaises(publisher.Refused):
            self.client.publish(self.evidence)
        self.assertEqual(git(self.remote, "rev-parse", "main"), other)

    def test_push_url_cannot_differ_from_authorized_remote(self):
        git(self.root, "remote", "set-url", "--push", "origin", str(self.base / "different.git"))
        with self.assertRaises(publisher.Refused):
            self.client.publish(self.evidence)
        self.assertEqual(git(self.remote, "rev-parse", "main"), self.initial)

    def test_working_head_cannot_use_publisher_ref(self):
        git(self.root, "update-ref", publisher.LOCAL_REF, self.initial)
        git(self.root, "symbolic-ref", "HEAD", publisher.LOCAL_REF)
        with self.assertRaises(publisher.Refused):
            self.client.publish(self.evidence)
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), self.initial)

    def test_secret_sentinel_rejects_payload_without_echoing_value(self):
        path = self.root / "secret.json"
        secret = "ghp_" + "a" * 36
        path.write_text(json.dumps({"key": secret}))
        with self.assertRaises(publisher.Refused) as error:
            publisher.Evidence(self.root).add(path)
        self.assertNotIn(secret, str(error.exception))

    def test_file_size_limit_is_enforced(self):
        path = self.root / "huge.json"
        path.write_bytes(b" " * (publisher.MAX_FILE_BYTES + 1))
        with self.assertRaises(publisher.Refused):
            publisher.Evidence(self.root).add(path)

    def test_changed_byte_budget_is_enforced_before_commit(self):
        with patch.object(publisher, "MAX_TOTAL_BYTES", 1):
            with self.assertRaises(publisher.Refused):
                self.client.publish(self.evidence)
        self.assertEqual(git(self.remote, "rev-parse", "main"), self.initial)

    def test_inflight_unit_is_excluded(self):
        folder = self.root / "trials/n0000"
        folder.mkdir(parents=True)
        (folder / "receipt.json").write_text("{}")
        evidence = publisher.Evidence(self.root)
        self.assertFalse(evidence.finalized_unit(folder))
        self.assertEqual(evidence.files, {})

    def test_duplicate_capture_cannot_replace_pinned_bytes(self):
        path = self.root / "script.py"
        path.write_text("one\n")
        evidence = publisher.Evidence(self.root)
        evidence.add(path, publisher.digest(path.read_bytes()))
        path.write_text("two\n")
        with self.assertRaises(publisher.Refused):
            evidence.add(path)
        self.assertEqual(evidence.files["script.py"], b"one\n")

    def test_large_inventory_shards_preserve_all_hashes(self):
        entries = {f"analysis_outputs/trials/n{number:05d}/receipt.json":
                   {"sha256": "a" * 64, "bytes": 1000} for number in range(16000)}
        path = "analysis_outputs/checkpoints/checkpoint.json"
        parts = publisher.inventory_files(path, {"files": entries, "summary": {}})
        self.assertGreater(len(parts), 1)
        self.assertTrue(all(len(payload) <= publisher.MAX_FILE_BYTES for payload in parts.values()))
        root = json.loads(parts[path])
        recovered = {}
        for manifest in root["file_manifests"]:
            self.assertEqual(publisher.digest(parts[manifest["path"]]), manifest["sha256"])
            recovered.update(json.loads(parts[manifest["path"]])["files"])
        self.assertEqual(recovered, entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-json", type=Path)
    arguments = parser.parse_args()
    started_utc = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PublisherTests)
    cases = [test.id().split(".")[-1] for test in suite]
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if arguments.audit_json:
        receipt = {
            "status": "PASS" if result.wasSuccessful() else "FAIL",
            "started_utc": started_utc,
            "finished_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": time.monotonic() - started,
            "exit_code": 0 if result.wasSuccessful() else 1,
            "cases": cases, "cases_run": result.testsRun,
            "failures": len(result.failures), "errors": len(result.errors),
            "publisher_source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "test_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "temporary_local_git_repositories_only": True,
            "github_contacted": False,
            "research_git_refs_and_index_modified": False,
        }
        publisher.atomic_json(arguments.audit_json, receipt)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
