# SPDX-FileCopyrightText: 2026 Tanya Babitskaya
# SPDX-License-Identifier: Apache-2.0
"""Regression cases use disposable Git repositories and mocked CI, never live evidence."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from collections.abc import Iterator
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "assurance", Path(__file__).resolve().parents[1] / "src/ai_assurance/cli.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Test module unavailable")
assurance = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = assurance
SPEC.loader.exec_module(assurance)
SOURCE = Path(__file__).resolve().parents[1]


def command(root: Path, *args: str) -> str:
    return (
        subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL)
        .decode("utf-8")
        .strip()
    )


def init(root: Path) -> None:
    command(root, "init", "-b", "fixture")
    command(root, "config", "user.email", "fixture@example.org")
    command(root, "config", "user.name", "Synthetic Fixture")
    command(root, "config", "commit.gpgsign", "false")


def save_commit(root: Path) -> str:
    command(root, "add", ".")
    command(root, "commit", "-m", "test: Disposable fixture")
    return command(root, "rev-parse", "HEAD")


class AssuranceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.source_tmp.cleanup)
        cls.source = Path(cls.source_tmp.name).resolve()
        shutil.copytree(SOURCE / "bundle", cls.source / "bundle")
        shutil.copyfile(SOURCE / "source.json", cls.source / "source.json")
        init(cls.source)
        cls.source_commit = save_commit(cls.source)
        cls.pin = assurance.Pin(cls.source, cls.source_commit)

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.root = self.base / "arbitrary checkout name"
        self.root.mkdir()
        init(self.root)
        self.original = "# Project rules\n\nKeep the project-specific invariant.\n"
        (self.root / "AGENTS.md").write_text(self.original, encoding="utf-8")
        self.revision = save_commit(self.root)
        (self.root / "AGENTS.local.md").write_text("Private local instruction\n", encoding="utf-8")
        self.profile = {
            "schema": 2,
            "project_id": "fixture:stable-id",
            "scope": "unit-test-only",
            "ci": {"repository": "example/demo", "workflow": ".github/workflows/ci.yml"},
            "controls": {
                key: {
                    "applicable": True,
                    "claim": "Synthetic fixture claim: " + key,
                    "ci_checks": ["unit-test"],
                }
                for key in assurance.CONTROLS
            },
        }
        self.profile_path = self.base / "profile.json"
        self.evidence_path = self.base / "evidence.json"
        self.inputs(self.record())
        self.install()

    def record(self, **changes: str) -> dict[str, str]:
        return {
            "id": "sample",
            "control": "data-exposure",
            "origin": "executed",
            "result": "pass",
            "scope": "unit-test-only",
            "source_revision": self.revision,
            "method": "Mocked CI response for unit tests only",
            "captured_at": (datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
            "run_url": "https://github.com/example/demo/actions/runs/1",
            "ci_check": "unit-test",
            **changes,
        }

    def inputs(self, *records: dict[str, str]) -> None:
        self.profile_path.write_text(json.dumps(self.profile), encoding="utf-8")
        self.evidence_path.write_text(json.dumps(records), encoding="utf-8")

    def ci(self, url: str) -> dict[str, object]:
        if "/jobs?" in url:
            return {
                "total_count": 1,
                "jobs": [{"name": "unit-test", "status": "completed", "conclusion": "success"}],
            }
        return {
            "head_sha": self.revision,
            "status": "completed",
            "path": ".github/workflows/ci.yml",
        }

    def install(self) -> None:
        with patch.object(assurance, "github_json", side_effect=self.ci):
            assurance.install(self.root, self.pin, self.profile_path, self.evidence_path)

    def uninstall_fixture(self) -> None:
        shutil.rmtree(self.root / ".ai-assurance")
        (self.root / "AGENTS.md").write_text(self.original, encoding="utf-8")

    def records(self, *records: dict[str, str]) -> None:
        (self.root / ".ai-assurance/evidence.json").write_text(
            json.dumps(records), encoding="utf-8"
        )

    def status(self) -> str:
        return next(
            x["status"]
            for x in assurance.assess(self.root, self.pin)["findings"]
            if x["control"] == "data-exposure"
        )

    @contextmanager
    def stalled_git(self) -> Iterator[Path]:
        directory = self.base / "fake-bin"
        directory.mkdir()
        pidfile = directory / "pid"
        executable = directory / "git"
        executable.write_text(
            f"#!{sys.executable}\n"
            "import os, sys, time\n"
            "from pathlib import Path\n"
            f"Path({str(pidfile)!r}).write_text(str(os.getpid()), encoding='utf-8')\n"
            "print('FIXTURE-SENSITIVE-OUTPUT', flush=True)\n"
            "print('FIXTURE-SENSITIVE-ERROR', file=sys.stderr, flush=True)\n"
            "time.sleep(5)\n",
            encoding="utf-8",
        )
        executable.chmod(0o755)
        try:
            with (
                patch.dict(os.environ, {"PATH": str(directory) + os.pathsep + os.environ["PATH"]}),
                patch.object(assurance, "GIT_TIMEOUT_SECONDS", 1),
            ):
                yield pidfile
        finally:
            if pidfile.exists():
                pid = int(pidfile.read_text(encoding="utf-8"))
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                try:
                    os.waitpid(pid, 0)
                except ChildProcessError:
                    pass

    def assert_git_reaped(self, pidfile: Path) -> None:
        self.assertTrue(pidfile.is_file(), "The fixture Git process must actually start")
        pid = int(pidfile.read_text(encoding="utf-8"))
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)
        with self.assertRaises(ChildProcessError):
            os.waitpid(pid, os.WNOHANG)

    @unittest.skipUnless(os.name == "posix", "Executable fixture requires POSIX")
    def test_git_deadline_reaps_process_and_keeps_cli_output_fixed(self) -> None:
        args = [
            "assurance",
            "report",
            str(self.root),
            "--source-repo",
            str(self.source),
            "--source-commit",
            self.source_commit,
        ]
        output, error = io.StringIO(), io.StringIO()
        started = time.monotonic()
        with (
            self.stalled_git() as pidfile,
            patch.object(sys, "argv", args),
            redirect_stdout(output),
            redirect_stderr(error),
        ):
            self.assertEqual(assurance.main(), 2)
            self.assert_git_reaped(pidfile)
        self.assertLess(time.monotonic() - started, 4)
        self.assertEqual(output.getvalue(), "")
        self.assertEqual(
            error.getvalue(), "Git operation timed out; check the local repository and retry\n"
        )

    @unittest.skipUnless(os.name == "posix", "Executable fixture requires POSIX")
    def test_install_rolls_back_after_git_deadline(self) -> None:
        self.uninstall_fixture()

        def final_check(root: Path, pin: object) -> None:
            self.assertTrue((root / ".ai-assurance").is_dir())
            self.assertIn(assurance.START, (root / "AGENTS.md").read_text(encoding="utf-8"))
            with self.stalled_git() as pidfile:
                try:
                    assurance.git(root, "status")
                finally:
                    self.assert_git_reaped(pidfile)

        with (
            patch.object(assurance, "assess", side_effect=final_check),
            self.assertRaisesRegex(assurance.AssuranceError, "^Git operation timed out;"),
        ):
            self.install()
        self.assertFalse((self.root / ".ai-assurance").exists())
        self.assertEqual((self.root / "AGENTS.md").read_text(encoding="utf-8"), self.original)
        self.assertFalse(list(self.root.glob(".ai-assurance-stage-*")))
        self.assertFalse(list(self.root.glob(".assurance-reference-*")))

    def test_commit_lineage_requires_existing_full_commit_not_label_or_blob(self) -> None:
        blob = command(self.root, "rev-parse", "HEAD:AGENTS.md")
        for revision in ("synthetic-fixture", "HEAD", "a" * 40, blob):
            self.records(self.record(source_revision=revision))
            with self.subTest(revision=revision), self.assertRaises(assurance.AssuranceError):
                self.status()
        self.records(self.record())
        self.assertEqual(self.status(), "supported")

    def test_future_and_naive_timestamps_are_refused(self) -> None:
        for captured in (
            (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            "2026-01-01T12:00:00",
        ):
            self.records(self.record(captured_at=captured))
            with self.assertRaises(assurance.AssuranceError):
                self.status()

    def test_every_origin_requires_run_or_artifact_reference(self) -> None:
        for origin in ("executed", "simulated", "declared"):
            record = self.record(origin=origin)
            record.pop("run_url")
            self.records(record)
            with self.assertRaises(assurance.AssuranceError):
                self.status()
            record["artifact_sha256"] = "a" * 64
            self.records(record)
            self.assertIn(self.status(), {"supported", "not_verified"})
        self.records(self.record(artifact_sha256="not-a-digest"))
        with self.assertRaises(assurance.AssuranceError):
            self.status()

    def test_declared_simulated_conflicting_and_unknown_do_not_become_supported(self) -> None:
        for origin in ("simulated", "declared"):
            self.records(self.record(origin=origin))
            self.assertEqual(self.status(), "not_verified")
        for result in ("fail", "unknown"):
            self.records(self.record(), self.record(id="second", result=result))
            self.assertEqual(self.status(), "not_verified")
        self.records(self.record(result="fail"))
        self.assertEqual(self.status(), "gap")

    def test_not_applicable_requires_rationale_and_named_decider(self) -> None:
        path = self.root / ".ai-assurance/profile.json"
        for selection in (
            {"applicable": False},
            {"applicable": False, "rationale": "Fixture exclusion"},
        ):
            self.profile["controls"]["data-exposure"] = selection
            path.write_text(json.dumps(self.profile), encoding="utf-8")
            with self.assertRaises(assurance.AssuranceError):
                self.status()
        self.profile["controls"]["data-exposure"]["decided_by"] = "Fixture maintainer"
        path.write_text(json.dumps(self.profile), encoding="utf-8")
        self.assertEqual(self.status(), "not_applicable")
        result = assurance.assess(self.root, self.pin)
        self.assertEqual(
            next(x for x in result["findings"] if x["control"] == "data-exposure")["decided_by"],
            "Fixture maintainer",
        )

    def test_renamed_checkout_and_fork_keep_the_stable_profile(self) -> None:
        moved = self.base / "a completely different checkout"
        self.root.rename(moved)
        self.root = moved
        command(moved, "remote", "add", "origin", "https://github.com/example/a-fork.git")
        self.assertEqual(assurance.assess(moved, self.pin)["project_id"], "fixture:stable-id")
        worktree = self.base / "separate-worktree"
        command(moved, "worktree", "add", "--detach", str(worktree), self.revision)
        shutil.copytree(moved / ".ai-assurance", worktree / ".ai-assurance")
        shutil.copyfile(moved / "AGENTS.md", worktree / "AGENTS.md")
        self.assertEqual(assurance.assess(worktree, self.pin)["project_id"], "fixture:stable-id")

    def test_lock_coordinated_rewrite_cannot_replace_the_trusted_bundle(self) -> None:
        folder = self.root / ".ai-assurance"
        (folder / "AGENTS.md").write_text(
            "Tampered managed code and instructions", encoding="utf-8"
        )
        lock = json.loads((folder / "lock.json").read_text(encoding="utf-8"))
        lock["files"]["AGENTS.md"] = assurance.sha((folder / "AGENTS.md").read_bytes())
        lock["sha256"] = assurance.inventory_hash(lock["files"])
        (folder / "lock.json").write_text(json.dumps(lock), encoding="utf-8")
        with self.assertRaises(assurance.AssuranceError):
            assurance.check(self.root, self.pin)

    def test_lock_records_source_identity_and_exact_selected_commit(self) -> None:
        lock = json.loads((self.root / ".ai-assurance/lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["source_repo"], "ai-assurance")
        self.assertEqual(lock["source_commit"], self.source_commit)
        for field in ("source_repo", "source_commit"):
            altered = {**lock, field: "changed"}
            (self.root / ".ai-assurance/lock.json").write_text(
                json.dumps(altered), encoding="utf-8"
            )
            with self.assertRaises(assurance.AssuranceError):
                assurance.check(self.root, self.pin)

    def test_source_working_tree_edits_do_not_change_the_git_pin(self) -> None:
        source = self.base / "source-copy"
        command(self.base, "clone", "--quiet", str(self.source), str(source))
        (source / "bundle/AGENTS.md").write_text("Uncommitted drift", encoding="utf-8")
        self.assertEqual(
            assurance.assess(self.root, assurance.Pin(source, self.source_commit))["project_id"],
            "fixture:stable-id",
        )

    def test_idempotence_preserves_private_instructions_and_edited_profile(self) -> None:
        before = (self.root / "AGENTS.md").read_bytes()
        self.install()
        self.assertEqual(before, (self.root / "AGENTS.md").read_bytes())
        self.assertEqual(
            (self.root / "AGENTS.local.md").read_text(encoding="utf-8"),
            "Private local instruction\n",
        )
        for path in (self.root / ".ai-assurance").rglob("*"):
            if path.is_file():
                self.assertNotIn(b"Private local instruction", path.read_bytes())
        self.profile["scope"] = "new human decision"
        self.inputs(self.record())
        with self.assertRaises(assurance.AssuranceError):
            self.install()
        self.assertEqual(before, (self.root / "AGENTS.md").read_bytes())

    def test_agent_instructions_and_skill_forbid_evidence_and_applicability_edits(self) -> None:
        agents = (SOURCE / "bundle/AGENTS.md").read_text(encoding="utf-8")
        skill = (SOURCE / "bundle/skills/assurance-review/SKILL.md").read_text(encoding="utf-8")
        self.assertIn(".ai-assurance/skills/assurance-review/SKILL.md", agents)
        for text in (agents, skill):
            self.assertIn("must not", text)
            self.assertIn("executed", text)
            self.assertIn("applicability", text)
            self.assertIn("decided_by", text)

    def test_one_blank_line_and_marker_bounded_matching(self) -> None:
        text = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(self.original.rstrip("\n") + "\n\n" + assurance.START, text)
        altered = "# Additional rules\n\n" + text + "\nKeep this unrelated trailing rule.\n"
        (self.root / "AGENTS.md").write_text(altered, encoding="utf-8")
        assurance.check(self.root, self.pin)
        for corrupt in (
            altered.replace(assurance.END, ""),
            altered + "\n" + assurance.START,
            altered.replace(assurance.REFERENCE, assurance.END + "\n" + assurance.START),
        ):
            (self.root / "AGENTS.md").write_text(corrupt, encoding="utf-8")
            with self.assertRaises(assurance.AssuranceError):
                assurance.check(self.root, self.pin)

    def test_install_folder_mode_is_0755_even_with_private_umask(self) -> None:
        self.uninstall_fixture()
        previous = os.umask(0o077)
        try:
            self.install()
        finally:
            os.umask(previous)
        self.assertEqual((self.root / ".ai-assurance").stat().st_mode & 0o777, 0o755)

    def test_install_rolls_back_when_reference_write_fails(self) -> None:
        self.uninstall_fixture()
        with patch.object(assurance, "atomic_text", side_effect=OSError("Synthetic private error")):
            with self.assertRaises(OSError):
                self.install()
        self.assertFalse((self.root / ".ai-assurance").exists())
        self.assertEqual((self.root / "AGENTS.md").read_text(encoding="utf-8"), self.original)
        self.assertFalse(list(self.root.glob(".ai-assurance-stage-*")))

    def test_install_rolls_back_both_outputs_when_final_verification_fails(self) -> None:
        self.uninstall_fixture()
        with patch.object(
            assurance, "assess", side_effect=assurance.AssuranceError("Final check failed")
        ):
            with self.assertRaises(assurance.AssuranceError):
                self.install()
        self.assertFalse((self.root / ".ai-assurance").exists())
        self.assertEqual((self.root / "AGENTS.md").read_text(encoding="utf-8"), self.original)

    def test_empty_scaffold_and_declared_ci_are_never_installed(self) -> None:
        self.uninstall_fixture()
        for records in ([], [self.record(origin="declared")]):
            self.inputs(*records)
            with self.assertRaises(assurance.AssuranceError):
                self.install()
            self.assertFalse((self.root / ".ai-assurance").exists())
            self.assertEqual((self.root / "AGENTS.md").read_text(encoding="utf-8"), self.original)

    def test_ci_metadata_revision_workflow_and_job_must_substantiate_record(self) -> None:
        self.uninstall_fixture()
        for changes in (
            {"head_sha": "b" * 40},
            {"status": "queued"},
            {"path": ".github/workflows/unrelated.yml"},
        ):

            def response(url: str, changes: dict[str, str] = changes) -> dict[str, object]:
                return self.ci(url) if "/jobs?" in url else {**self.ci(url), **changes}

            with (
                patch.object(assurance, "github_json", side_effect=response),
                self.assertRaises(assurance.AssuranceError),
            ):
                assurance.install(self.root, self.pin, self.profile_path, self.evidence_path)
        with (
            patch.object(assurance, "github_json", return_value={"total_count": 0, "jobs": []}),
            self.assertRaises(assurance.AssuranceError),
        ):
            assurance.install(self.root, self.pin, self.profile_path, self.evidence_path)

    def test_profile_requires_explicit_project_ci_and_claims(self) -> None:
        for key in ("ci", "scope", "project_id"):
            bad = {k: v for k, v in self.profile.items() if k != key}
            with self.assertRaises(assurance.AssuranceError):
                assurance.validate_profile(bad)
        for field in ("claim", "ci_checks"):
            bad = json.loads(json.dumps(self.profile))
            bad["controls"]["data-exposure"].pop(field)
            with self.assertRaises(assurance.AssuranceError):
                assurance.validate_profile(bad)

    def test_duplicate_keys_wrong_encoding_and_excessive_nesting_are_refused(self) -> None:
        path = self.root / ".ai-assurance/evidence.json"
        for raw in (b'[{"id":"one","id":"two"}]', b"\xff", b"[" * 2000 + b"0" + b"]" * 2000):
            path.write_bytes(raw)
            with self.assertRaises(assurance.AssuranceError):
                self.status()

    def test_symlink_input_does_not_touch_target(self) -> None:
        target = self.base / "outside.txt"
        target.write_text("Outside sentinel", encoding="utf-8")
        path = self.root / ".ai-assurance/evidence.json"
        path.unlink()
        path.symlink_to(target)
        with self.assertRaises(assurance.AssuranceError):
            self.status()
        self.assertEqual(target.read_text(encoding="utf-8"), "Outside sentinel")

    def test_cli_prints_actionable_error_without_raw_exception_or_evidence(self) -> None:
        args = [
            "assurance",
            "report",
            str(self.root),
            "--source-repo",
            str(self.source),
            "--source-commit",
            self.source_commit,
        ]
        self.records(self.record(result="PRIVATE_SENTINEL"))
        error = io.StringIO()
        with patch.object(sys, "argv", args), redirect_stderr(error):
            self.assertEqual(assurance.main(), 2)
        self.assertIn("Evidence result must", error.getvalue())
        self.assertNotIn("PRIVATE_SENTINEL", error.getvalue())
        for exception in (UnicodeError("PRIVATE_SENTINEL"), RecursionError("PRIVATE_SENTINEL")):
            error = io.StringIO()
            with (
                patch.object(sys, "argv", args),
                patch.object(assurance, "assess", side_effect=exception),
                redirect_stderr(error),
            ):
                self.assertEqual(assurance.main(), 2)
            self.assertNotIn("PRIVATE_SENTINEL", error.getvalue())

    def test_evidence_method_is_never_executed(self) -> None:
        marker = self.base / "never-create"
        self.records(self.record(method=f"touch {marker}"))
        self.assertEqual(self.status(), "supported")
        self.assertFalse(marker.exists())

    def test_bundle_change_without_version_bump_is_refused(self) -> None:
        source = self.base / "changed-source"
        command(self.base, "clone", "--quiet", str(self.source), str(source))
        command(source, "config", "user.email", "fixture@example.org")
        command(source, "config", "user.name", "Synthetic Fixture")
        command(source, "config", "commit.gpgsign", "false")
        path = source / "bundle/AGENTS.md"
        path.write_text(
            path.read_text(encoding="utf-8") + "\nA changed instruction.\n", encoding="utf-8"
        )
        changed = save_commit(source)
        with self.assertRaisesRegex(assurance.AssuranceError, "VERSION bump"):
            assurance.Pin(source, changed).payload()

    def test_profile_and_records_require_utf8(self) -> None:
        path = self.root / ".ai-assurance/profile.json"
        path.write_bytes(b"\xff")
        with self.assertRaises(assurance.AssuranceError):
            assurance.check(self.root, self.pin)

    def test_ci_job_failure_cannot_be_presented_as_pass(self) -> None:
        self.uninstall_fixture()

        def response(url: str) -> dict[str, object]:
            if "/jobs?" in url:
                return {
                    "total_count": 1,
                    "jobs": [{"name": "unit-test", "status": "completed", "conclusion": "failure"}],
                }
            return self.ci(url)

        with (
            patch.object(assurance, "github_json", side_effect=response),
            self.assertRaises(assurance.AssuranceError),
        ):
            assurance.install(self.root, self.pin, self.profile_path, self.evidence_path)
        self.assertFalse((self.root / ".ai-assurance").exists())


if __name__ == "__main__":
    unittest.main()
