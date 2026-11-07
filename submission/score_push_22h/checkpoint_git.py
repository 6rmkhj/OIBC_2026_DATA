#!/usr/bin/env python3
"""Publish small, finalized research evidence without touching the working index.

Default is a local dry run. --publish explicitly permits a Codex-authored commit
and an ordinary fast-forward push to origin/main. No model/data files are read
or uploaded. A private index and dedicated local ref leave work/HEAD unchanged.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
INITIAL_BASE = "302da278fc3777076f9fcb48da914fd46575c0d7"
REMOTE = "https://github.com/6rmkhj/OIBC_2026_DATA.git"
LOCAL_REF = "refs/heads/codex/checkpoints"
CHECKPOINT_ROOT = "analysis_outputs/github_checkpoints_20261107"
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 50 * 1024 * 1024
MAX_CAPTURE_BYTES = 512 * 1024 * 1024
IDENTITY = {"name": "Codex", "email": "codex@openai.com"}
FOLDS = ("early2022", "primary", "winter", "spring", "recent")
SECRET_PATTERNS = {
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b"),
    "aws_access_key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "openai_key": re.compile(rb"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}\b"),
    "credentialed_url": re.compile(rb"https?://[^\s/:@]+:[^\s/@]+@"),
    "literal_secret": re.compile(rb'''(?i)(?:api_key|access_token|auth_token|secret_key|password)\s*[=:]\s*["'][A-Za-z0-9_+/=.-]{24,}["']'''),
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def inventory_files(relative, inventory):
    """Split unusually large hash inventories without exceeding file budgets."""
    payload = json_bytes(inventory)
    if len(payload) <= MAX_FILE_BYTES:
        return {relative: payload}
    entries = inventory.pop("files")
    result, chunk, chunk_size, manifests = {}, {}, 0, []
    for name, value in entries.items():
        entry_size = len(json_bytes({name: value}))
        if chunk and chunk_size + entry_size > MAX_FILE_BYTES // 2:
            manifests.append(chunk)
            chunk, chunk_size = {}, 0
        chunk[name] = value
        chunk_size += entry_size
    if chunk:
        manifests.append(chunk)
    inventory["file_manifests"] = []
    for number, entries in enumerate(manifests, 1):
        path = relative.removesuffix(".json") + f"_files_{number:03d}.json"
        part = json_bytes({"files": entries})
        result[path] = part
        inventory["file_manifests"].append({"path": path, "sha256": digest(part), "files": len(entries)})
    result[relative] = json_bytes(inventory)
    if any(len(payload) > MAX_FILE_BYTES for payload in result.values()):
        raise Refused("Checkpoint inventory exceeds its per-file budget")
    return result


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".checkpoint-", delete=False) as stream:
        name = stream.name
        stream.write(json_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(name, path)


class Refused(RuntimeError):
    pass


class Evidence:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.files = {}
        self.captured_bytes = 0
        self.completed = {}
        self.summaries = {}
        self.omitted = ["large models and predictions", "raw/prepared data", "logs and in-flight state",
                        "automation identifiers", "live viewer snapshots"]

    def add(self, path, expected=None):
        path = Path(path)
        relative = path.relative_to(self.root).as_posix()
        if not path.exists():
            raise Refused(f"Required finalized artifact is missing: {relative}")
        if path.is_symlink() or path.resolve() != path:
            raise Refused(f"Symlink or noncanonical artifact refused: {relative}")
        if path.suffix not in {".py", ".json", ".md", ".csv", ".html"}:
            raise Refused(f"Non-text artifact refused: {relative}")
        before = path.stat()
        if before.st_size > MAX_FILE_BYTES:
            raise Refused(f"Artifact exceeds {MAX_FILE_BYTES} bytes: {relative}")
        payload = path.read_bytes()
        after = path.stat()
        if (before.st_ino, before.st_mtime_ns, before.st_size) != (after.st_ino, after.st_mtime_ns, after.st_size):
            raise Refused(f"Artifact changed while being captured: {relative}")
        payload.decode("utf-8")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(payload):
                raise Refused(f"Secret sentinel {label} matched in {relative}; value suppressed")
        if path.suffix == ".json":
            json.loads(payload)
        if expected and digest(payload) != expected:
            raise Refused(f"Pinned text artifact hash changed: {relative}")
        if relative in self.files and self.files[relative] != payload:
            raise Refused(f"Artifact changed between repeated captures: {relative}")
        if relative not in self.files:
            self.captured_bytes += len(payload)
        self.files[relative] = payload
        if self.captured_bytes > MAX_CAPTURE_BYTES:
            raise Refused("Text evidence exceeds the 512 MiB local capture budget")
        return json.loads(payload) if path.suffix == ".json" else None

    def optional(self, folder, names):
        for name in names:
            path = folder / name
            if path.is_file():
                self.add(path)

    def pins(self, path):
        if not path.exists():
            return
        value = self.add(path)
        for relative, expected in value.get("source_sha256", {}).items():
            candidate = (self.root / relative).resolve()
            if not candidate.is_relative_to(self.root) or not str(relative).startswith("submission/"):
                raise Refused(f"Source pin lies outside submission code: {relative}")
            self.add(candidate, expected)
        return value

    def finalized_unit(self, folder):
        result_path = folder / "result.json"
        if not result_path.exists():
            return False
        result = self.add(result_path)
        if result.get("status") != "PASS":
            if result.get("status") not in {"FAIL", "FAILED", "ERROR", "TIMEOUT", "NO_CANDIDATE", "NO_ELIGIBLE_CANDIDATE", "CHECKPOINT_ONLY"}:
                raise Refused(f"Unrecognized terminal result status: {result_path.relative_to(self.root)}")
            # A failure/checkpoint is recorded as such, never candidate success.
            return True
        fold_results = result.get("folds", {})
        if folder.parent.name == "trials" and folder.parent.parent.name in {"research_10h_20261107", "research_22h_20261107"}:
            if set(fold_results) != set(FOLDS):
                raise Refused(f"Finalized generation trial lacks all five folds: {folder.name}")
            for fold in FOLDS:
                if self.add(folder / fold / "receipt.json") != fold_results[fold]:
                    raise Refused(f"Terminal result and fold receipt disagree: {folder.name}/{fold}")
        for path in sorted(folder.rglob("receipt.json")):
            if any(part.startswith(".") or ".interrupted." in part for part in path.relative_to(folder).parts):
                continue
            receipt = self.add(path)
            if receipt.get("status") not in {"PASS", "REUSED"}:
                raise Refused(f"Nonfinal receipt under finalized unit: {path.relative_to(self.root)}")
            for name in ("transform.json", "config.json", "features.json"):
                extra = path.parent / name
                if extra.exists():
                    self.add(extra, receipt.get("files_sha256", {}).get(name))
        return True

    def campaign(self, name):
        folder = self.root / "analysis_outputs" / name
        if not folder.exists():
            return
        self.optional(folder, ["authorization.json"])
        if not (folder / "protocol.json").exists():
            return
        protocol = self.pins(folder / "protocol.json")
        self.pins(folder / "publication_pins.json")
        for artifact_name, field in (("configs.json", "configs_sha256"), ("bases.json", "bases_sha256"), ("jobs.json", "jobs_sha256"), ("data/manifest.json", "data_manifest_sha256")):
            if (folder / artifact_name).exists():
                self.add(folder / artifact_name, protocol.get(field))
        self.optional(folder, ["controller_manifest.json", "launch_contract.json", "continuation_spec.json",
                               "final_verification_contract.json", "CAMPAIGN.md"])
        for path in sorted(folder.glob("independent*.json")):
            self.add(path)
        for path in sorted((folder / "hourly_checks").glob("*_science.json")):
            self.add(path)
        for path in (folder / "data").glob("**/*.json"):
            if path.name in {"manifest.json", "read_receipts.json", "features.json"}:
                self.add(path)
        units = []
        for path in sorted((folder / "trials").glob("*/result.json")):
            if self.finalized_unit(path.parent):
                units.append(path.parent.name)
        bases = []
        for path in sorted((folder / "bases").glob("*/result.json")):
            if self.finalized_unit(path.parent):
                bases.append(path.parent.name)
        self.completed[name] = {"trials": units, "crossfit_bases": bases}
        captured_results = [json.loads(self.files[(folder / "trials" / identifier / "result.json").relative_to(self.root).as_posix()]) for identifier in units]
        timestamps = sorted(result["utc"] for result in captured_results if result.get("utc"))
        self.summaries[name] = {
            "finished_trials": len(units),
            "passing_trials": sum(result.get("status") == "PASS" for result in captured_results),
            "finished_crossfit_bases": len(bases),
            "eligible_flags_in_trial_results": sum(bool(result.get("eligible", result.get("blend", {}).get("eligible", False))) for result in captured_results),
            "first_trial_completed_utc": timestamps[0] if timestamps else None,
            "latest_trial_completed_utc": timestamps[-1] if timestamps else None,
            "eligibility_requires_frozen_protocol_and_final_verification": True,
            "elapsed_wall_time_is_not_active_training_time": True,
        }
        completion = folder / "completion"
        if (completion / "result.json").exists():
            self.add(completion / "result.json")
            self.optional(completion, ["shortlist.json", "selection_frozen.json", "audit.json", "budget_stop.json"])
            for receipt in sorted(completion.glob("**/receipt.json")):
                value = self.add(receipt)
                for key in ("transform.json", "config.json", "features.json"):
                    if (receipt.parent / key).exists():
                        self.add(receipt.parent / key, value.get("files_sha256", {}).get(key))

    def gather(self):
        for name in ("research_10h_20261107", "research_22h_20261107"):
            self.campaign(name)
        # Earlier implementation is finished; these directories never contain keys.
        for directory in ("score_push_10h", "score_push_continue", "score_push_10h_viewer"):
            for path in sorted((self.root / "submission" / directory).glob("*.py")):
                self.add(path)
        # This publisher is complete when invoked, independent of engine freeze.
        self.add(self.root / "submission/score_push_22h/checkpoint_git.py")
        self.optional(self.root / "submission/score_push_10h_viewer", ["template.html"])
        prior = self.root / "analysis_outputs/renew_20261107"
        self.optional(prior, ["summary.json", "REPORT.md", "results.csv", "final_integrity_check.json",
                              "runtime_inputs/recovery.json"])
        return self

    def inventory(self):
        return {name: {"sha256": digest(payload), "bytes": len(payload)}
                for name, payload in sorted(self.files.items())}


class Publisher:
    def __init__(self, root=ROOT, initial_base=INITIAL_BASE, expected_remote=REMOTE):
        self.root = Path(root).resolve()
        self.initial_base = initial_base
        self.expected_remote = expected_remote
        self.gitdir = Path(self.git("rev-parse", "--absolute-git-dir").decode().strip())
        self.private = self.gitdir / "codex-checkpoints"
        self.state_path = self.private / "state.json"
        self.local_ref = LOCAL_REF

    def git(self, *args, input=None, env=None, timeout=30, check=True):
        result = subprocess.run(["git", *args], cwd=self.root, input=input,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0", **(env or {})}, timeout=timeout)
        if check and result.returncode:
            # Git diagnostics can contain remote auth material; never echo raw stderr.
            raise Refused(f"git {args[0]} failed with exit {result.returncode}; raw diagnostics suppressed")
        return result.stdout if check else result

    @contextmanager
    def locked(self):
        self.private.mkdir(exist_ok=True)
        with (self.private / "publisher.lock").open("a+b") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield

    def identity_env(self):
        return {"GIT_AUTHOR_NAME": IDENTITY["name"], "GIT_AUTHOR_EMAIL": IDENTITY["email"],
                "GIT_COMMITTER_NAME": IDENTITY["name"], "GIT_COMMITTER_EMAIL": IDENTITY["email"]}

    def remote_head(self):
        rows = self.git("ls-remote", "origin", "refs/heads/main", timeout=30).decode().splitlines()
        if len(rows) != 1 or not re.fullmatch(r"[0-9a-f]{40}\trefs/heads/main", rows[0]):
            raise Refused("Remote main is missing or ambiguous")
        return rows[0].split()[0]

    def guard(self, state):
        if self.git("remote", "get-url", "origin").decode().strip() != self.expected_remote:
            raise Refused("origin no longer matches the authorized repository")
        if self.git("remote", "get-url", "--push", "--all", "origin").decode().splitlines() != [self.expected_remote]:
            raise Refused("origin push URL no longer uniquely matches the authorized repository")
        symbolic = self.git("symbolic-ref", "-q", "HEAD", check=False)
        if symbolic.returncode == 0 and symbolic.stdout.decode().strip() == self.local_ref:
            raise Refused("Working HEAD uses the dedicated checkpoint ref")
        if self.git("rev-parse", "HEAD").decode().strip() != self.initial_base:
            raise Refused("Working HEAD changed; checkpoint publication requires review")
        if self.git("diff", "--cached", "--name-only", "-z"):
            raise Refused("The working index contains staged changes; it was left untouched")
        if state and state.get("initial_base") != self.initial_base:
            raise Refused("Publisher base changed")

    def install(self, files, parent, index_path):
        env = {"GIT_INDEX_FILE": str(index_path)}
        self.git("read-tree", parent, env=env)
        records = []
        for name, contents in sorted(files.items()):
            sha = self.git("hash-object", "-w", "--stdin", input=contents).decode().strip()
            records.append(f"100644 {sha}\t{name}".encode() + b"\0")
        if records:
            self.git("update-index", "-z", "--index-info", input=b"".join(records), env=env)
        return self.git("write-tree", env=env).decode().strip()

    def changed_files(self, files, parent):
        tree = {}
        for record in self.git("ls-tree", "-r", "-z", "--full-tree", parent).split(b"\0"):
            if record:
                info, name = record.split(b"\t", 1)
                tree[name.decode()] = info.split()[2].decode()
        changed = {}
        for name, payload in files.items():
            blob = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
            if tree.get(name) != blob:
                changed[name] = payload
        return changed

    def save_state(self, state):
        atomic_json(self.state_path, state)

    def finish_push(self, state):
        pending = state["pending"]
        head = self.remote_head()
        if head not in {pending["parent"], pending["commit"]}:
            raise Refused("Remote main changed unexpectedly; no force push or merge was attempted")
        current_ref = self.git("rev-parse", "--verify", self.local_ref, check=False)
        previous = current_ref.stdout.decode().strip() if current_ref.returncode == 0 else "0" * 40
        if previous not in {"0" * 40, pending["parent"], pending["commit"]}:
            raise Refused("Dedicated checkpoint ref changed unexpectedly")
        if previous != pending["commit"]:
            self.git("update-ref", self.local_ref, pending["commit"], previous)
        # Pending is durable before ref/push mutations, so a crash resumes exactly
        # this commit, including its local inventory copy, without a duplicate.
        for relative in pending.get("inventories", [pending["inventory"]]):
            inventory_bytes = self.git("show", f"{pending['commit']}:{relative}")
            inventory_path = self.root / relative
            if inventory_path.exists() and inventory_path.read_bytes() != inventory_bytes:
                raise Refused("Saved checkpoint inventory was modified")
            if not inventory_path.exists():
                atomic_json(inventory_path, json.loads(inventory_bytes))
        if head == pending["parent"]:
            self.git("push", "--porcelain", "--no-follow-tags", "--recurse-submodules=no", "origin", f"{pending['commit']}:refs/heads/main", timeout=90)
            head = self.remote_head()
        if head != pending["commit"]:
            raise Refused("Remote main changed unexpectedly; no force push or merge was attempted")
        state.update(last_published=head, pending=None, last_success_utc=utc())
        self.save_state(state)
        # Tracking ref is bookkeeping, not a change to work/HEAD or its index.
        current = self.git("rev-parse", "--verify", "refs/remotes/origin/main", check=False)
        if current.returncode == 0 and current.stdout.decode().strip() in {pending["parent"], head}:
            self.git("update-ref", "refs/remotes/origin/main", head, current.stdout.decode().strip())
        receipt = {"status": "PUSHED", "commit": head, "url": f"{self.expected_remote.removesuffix('.git')}/commit/{head}",
                   "author": IDENTITY, "committer": IDENTITY, "local_ref": self.local_ref,
                   "working_head_unchanged": True, "working_index_unchanged": True,
                   "inventory": pending["inventory"], "files": pending["files"], "bytes": pending["bytes"],
                   "verified_remote_main": head, "utc": utc()}
        atomic_json(self.private / "last_receipt.json", receipt)
        return receipt

    def publish(self, evidence):
        with self.locked():
            state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {"initial_base": self.initial_base, "last_published": None, "pending": None}
            self.guard(state)
            if state.get("pending"):
                return self.finish_push(state)
            parent = state.get("last_published") or self.initial_base
            if self.remote_head() != parent:
                raise Refused("Remote main differs from the initial base/last published checkpoint; refusing divergence")
            changed = self.changed_files(evidence.files, parent)
            if sum(map(len, changed.values())) > MAX_TOTAL_BYTES:
                raise Refused("Changed evidence exceeds the 50 MiB per-commit publication budget")
            with tempfile.TemporaryDirectory(dir=self.private, prefix="index-") as directory:
                index_path = Path(directory) / "index"
                if not changed:
                    return {"status": "NO_CHANGES", "commit": parent, "local_ref": self.local_ref,
                            "working_head_unchanged": True, "working_index_unchanged": True}
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
                relative = f"{CHECKPOINT_ROOT}/checkpoint_{stamp}.json"
                inventory = {"created_utc": utc(), "parent_commit": parent, "author": IDENTITY,
                    "completed": evidence.completed, "summary": evidence.summaries,
                    "files": {name: {"sha256": digest(payload), "bytes": len(payload)} for name, payload in sorted(changed.items())},
                    "captured_text_files": len(evidence.files), "unchanged_files_in_parent": len(evidence.files) - len(changed),
                    "excluded": evidence.omitted,
                    "source_files_are_captured_bytes": True, "large_artifact_hashes_are_receipt_references": True,
                    "official_score_queried": False, "all_history_previously_exposed": True}
                manifests = inventory_files(relative, inventory)
                all_files = {**changed, **manifests}
                if sum(map(len, all_files.values())) > MAX_TOTAL_BYTES:
                    raise Refused("Checkpoint including inventory exceeds 50 MiB")
                tree = self.install(all_files, parent, index_path)
                old_n = len(evidence.completed.get("research_10h_20261107", {}).get("trials", []))
                new_n = len(evidence.completed.get("research_22h_20261107", {}).get("trials", []))
                message = (f"Checkpoint OIBC research: {old_n} generation and {new_n} calibration trials\n\n"
                           "Record finalized code, protocols, metrics and audit receipts.\n"
                           "Large models/data and live runtime state remain in the execution workspace.\n"
                           "Historical development scores are not new official leaderboard scores.\n")
                commit = self.git("commit-tree", tree, "-p", parent, input=message.encode(), env=self.identity_env()).decode().strip()
            self.guard(state)
            current_ref = self.git("rev-parse", "--verify", self.local_ref, check=False)
            previous = current_ref.stdout.decode().strip() if current_ref.returncode == 0 else "0" * 40
            if previous not in {"0" * 40, parent}:
                raise Refused("Dedicated checkpoint ref changed unexpectedly")
            state["pending"] = {"commit": commit, "parent": parent, "inventory": relative,
                                "inventories": list(manifests),
                                "files": len(all_files), "bytes": sum(map(len, all_files.values()))}
            self.save_state(state)
            return self.finish_push(state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--publish", action="store_true", help="Create a Codex-authored checkpoint and fast-forward origin/main")
    mode.add_argument("--dry-run", action="store_true", help="Inspect only local finalized evidence (default)")
    parser.add_argument("--inventory", type=Path, help="Save the complete local dry-run inventory to this JSON path")
    args = parser.parse_args()
    evidence = Evidence(ROOT).gather()
    if args.publish:
        result = Publisher().publish(evidence)
    else:
        if args.inventory:
            atomic_json(args.inventory, {"created_utc": utc(), "files": evidence.inventory(), "completed": evidence.completed,
                                         "summary": evidence.summaries, "excluded": evidence.omitted})
        result = {"status": "DRY_RUN", "files": len(evidence.files), "bytes": sum(map(len, evidence.files.values())),
                  "completed": {key: {kind: len(ids) for kind, ids in value.items()} for key, value in evidence.completed.items()},
                  "author": IDENTITY, "remote": REMOTE, "target_branch": "main", "local_ref": LOCAL_REF,
                  "working_head_and_index_will_remain_unchanged": True, "excluded": evidence.omitted,
                  "per_commit_changed_bytes_limit": MAX_TOTAL_BYTES,
                  "inventory": str(args.inventory) if args.inventory else None,
                  "largest_files": sorted(({"path": path, "bytes": len(payload)} for path, payload in evidence.files.items()), key=lambda x: x["bytes"], reverse=True)[:8]}
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except (Refused, OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
