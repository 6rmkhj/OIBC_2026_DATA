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
SPEC = importlib.util.spec_from_file_location("readme_v2_publication_under_test", SOURCE)
wrapper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wrapper)
AUDITED = wrapper.load_publisher()


class ReadmeV2PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="oibc-readme-publication-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "work"
        self.root.mkdir()
        self.now = datetime.now(timezone.utc)
        self.write(wrapper.PUBLISHER_PATH, (wrapper.ROOT / wrapper.PUBLISHER_PATH).read_bytes())
        self.write("submission/research_reporting_v2/update_readme.py", b"# Fixture generator\n")
        self.write("submission/research_reporting_v2/publish_readme.py", SOURCE.read_bytes())
        for relative in wrapper.FROZEN_DEPENDENCIES:
            self.write(relative, (wrapper.ROOT / relative).read_bytes())
        for path in wrapper.REQUIRED_OUTPUTS:
            self.write(path, b"# Reproducible fixture\n" if path.endswith(".md") else b"id,status\nx,PASS\n")
        self.manifest = {
            "schema_version": 2,
            "created_utc": self.now.isoformat(), "snapshot_id": "fixture-snapshot",
            "source_snapshot_sha256": "d" * 64, "publisher_sha256": wrapper.PUBLISHER_SHA256,
            "deadline_utc": wrapper.DEADLINE.isoformat(), "search_stop_utc": wrapper.SEARCH_STOP.isoformat(),
            "source_sha256": {path: self.sha(path) for path in wrapper.REQUIRED_SOURCES},
            "outputs_sha256": {path: self.sha(path) for path in wrapper.REQUIRED_OUTPUTS},
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
        expected = set(wrapper.REQUIRED_OUTPUTS) | set(self.manifest["source_sha256"]) | {
            wrapper.MANIFEST_PATH, wrapper.PUBLISHER_PATH}
        self.assertEqual(set(evidence.files), expected)
        self.assertEqual(summary["snapshot_id"], self.manifest["snapshot_id"])
        self.assertEqual(summary["output_files"], 3)

    def test_tampered_output_is_rejected(self):
        self.write("README.md", b"tampered\n")
        with self.assertRaises(AUDITED.Refused):
            self.capture()

    def test_tampered_pinned_source_is_rejected(self):
        self.write("submission/research_reporting_v2/update_readme.py", b"# Changed\n")
        with self.assertRaises(AUDITED.Refused):
            self.capture()

    def test_extra_output_scope_is_rejected(self):
        self.manifest["outputs_sha256"]["unrequested.txt"] = "a" * 64
        self.save_manifest()
        with self.assertRaises(ValueError):
            self.capture()

    def test_unpinned_or_unapproved_reporting_source_is_rejected(self):
        self.manifest["source_sha256"]["submission/research_reporting_v2/unrequested.py"] = "a" * 64
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

    def test_csv_parts_are_bounded_consecutive_and_hashed(self):
        part = wrapper.OVERVIEW + "/experiments_part_001.csv"
        self.write(part, b"id,status\ny,PASS\n")
        self.manifest["outputs_sha256"][part] = self.sha(part)
        self.save_manifest()
        evidence, summary = self.capture()
        self.assertIn(part, evidence.files)
        self.assertEqual(summary["output_files"], 4)
        del self.manifest["outputs_sha256"][part]
        self.manifest["outputs_sha256"][part.replace("001", "003")] = "a" * 64
        self.save_manifest()
        with self.assertRaises(ValueError):
            self.capture()

    def test_deadline_and_old_dependency_pins_cannot_drift(self):
        self.manifest["deadline_utc"] = "2026-11-08T13:00:00Z"
        self.save_manifest()
        with self.assertRaises(ValueError):
            self.capture()
        self.manifest["deadline_utc"] = wrapper.DEADLINE.isoformat()
        key = next(iter(wrapper.FROZEN_DEPENDENCIES))
        self.manifest["source_sha256"][key] = "a" * 64
        self.save_manifest()
        with self.assertRaises(ValueError):
            self.capture()

    def stage_fixture(self):
        protocol = {"folds": {"primary": {}, "recent": {}}, "search_seeds": [0, 1, 2], "source_sha256": {}}
        self.write(wrapper.STAGE_ROOT + "/protocol.json", json.dumps(protocol).encode())
        self.write(wrapper.STAGE_ROOT + "/configs.json", b"[]")
        self.write(wrapper.STAGE_ROOT + "/CAMPAIGN.md", b"# New stage\n")
        return protocol

    def receipt(self, relative, seed, fold, config):
        self.write(relative + "/receipt.json", json.dumps({"status": "PASS", "seed": seed,
            "fold": fold, "config": config, "real_model_fits": 1}).encode())

    def test_new_campaign_unified_source_pins_keep_exact_reporting_scope(self):
        self.stage_fixture()
        allowed = "submission/research_reporting_v2/update_readme.py"
        pins = {"source_sha256": {allowed: self.sha(allowed)}}
        path = wrapper.STAGE_ROOT + "/publication_pins.json"
        self.write(path, json.dumps(pins).encode())
        evidence = AUDITED.Evidence(self.root)
        wrapper.capture_stage(evidence)
        self.assertIn(allowed, evidence.files)
        pins["source_sha256"]["submission/unapproved.py"] = "a" * 64
        self.write(path, json.dumps(pins).encode())
        with self.assertRaises(ValueError):
            wrapper.capture_stage(AUDITED.Evidence(self.root))

    def test_finalized_new_trials_require_every_declared_seed_and_fold(self):
        protocol = self.stage_fixture()
        folder = wrapper.STAGE_ROOT + "/trials/r0000"
        config = {"id": "r0000", "base_id": "b00"}
        result = {"id": "r0000", "status": "PASS", "config": config,
                  "folds": {fold: {} for fold in protocol["folds"]}}
        self.write(folder + "/result.json", json.dumps(result).encode())
        for seed in protocol["search_seeds"]:
            for fold in protocol["folds"]:
                self.receipt(folder + f"/seed{seed}/{fold}", seed, fold, config)
        self.write(folder + "/model.txt", b"binary model excluded")
        evidence = AUDITED.Evidence(self.root)
        wrapper.capture_stage(evidence)
        self.assertIn("r0000", evidence.completed[wrapper.STAGE]["trials"])
        self.assertNotIn(folder + "/model.txt", evidence.files)
        (self.root / folder / "seed2/recent/receipt.json").unlink()
        with self.assertRaises(ValueError):
            wrapper.capture_stage(AUDITED.Evidence(self.root))

    def test_recovery_and_seed_validation_remain_separate_diagnostics(self):
        self.stage_fixture()
        recovered = wrapper.STAGE_ROOT + "/recovered/n0132/result.json"
        self.write(recovered, json.dumps({"status": "RECOVERED_DIAGNOSTIC", "eligible": False,
                                         "real_model_fits": 0}).encode())
        folder = wrapper.STAGE_ROOT + "/validation/n0132"
        self.write(folder + "/result.json", json.dumps({"status": "PASS", "diagnostics_only": True,
                                                       "eligible": False, "real_model_fits": 4}).encode())
        for seed in (1, 2):
            for fold in ("primary", "recent"):
                self.receipt(folder + f"/seed{seed}/{fold}", seed, fold, {})
        evidence = AUDITED.Evidence(self.root)
        wrapper.capture_stage(evidence)
        self.assertEqual(evidence.completed[wrapper.STAGE]["recovered_prior_failures"], ["n0132"])
        self.assertEqual(evidence.completed[wrapper.STAGE]["new_seed_validations"], ["n0132"])
        self.write(recovered, json.dumps({"status": "RECOVERED_DIAGNOSTIC", "eligible": True,
                                         "real_model_fits": 0}).encode())
        with self.assertRaises(ValueError):
            wrapper.capture_stage(AUDITED.Evidence(self.root))

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
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReadmeV2PublicationTests)
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
