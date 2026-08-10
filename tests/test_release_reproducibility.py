from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.release_reproducibility import (
    REVIEW_OVERLAY_PATH_ENV,
    REVIEW_OVERLAY_REF_ENV,
    REVIEW_OVERLAY_SHA_ENV,
    SOURCE_DATE_EPOCH_ENV,
    deterministic_release_environment,
    ensure_tracked_worktree_clean,
    git_commit_epoch,
    review_overlay_from_environment,
    source_date_epoch_from_environment,
)


class ReleaseReproducibilityTests(unittest.TestCase):
    @staticmethod
    def _git(root: Path, *args: str) -> str:
        proc = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return (proc.stdout or "").strip()

    def test_commit_epoch_should_read_full_git_commit_timestamp(self) -> None:
        completed = subprocess.CompletedProcess(
            ["git"],
            0,
            stdout="1785513828\n",
            stderr="",
        )
        with mock.patch("tools.release_reproducibility.subprocess.run", return_value=completed) as run:
            self.assertEqual(1_785_513_828, git_commit_epoch(Path("/repo"), "abc"))

        self.assertEqual(
            ["git", "show", "-s", "--format=%ct", "abc"],
            run.call_args.args[0],
        )

    def test_deterministic_environment_should_override_and_restore_epoch(self) -> None:
        env = {SOURCE_DATE_EPOCH_ENV: "123"}
        with mock.patch(
            "tools.release_reproducibility.git_commit_epoch",
            return_value=456,
        ):
            with deterministic_release_environment(repo_root=Path("/repo"), environ=env) as epoch:
                self.assertEqual(456, epoch)
                self.assertEqual("456", env[SOURCE_DATE_EPOCH_ENV])
        self.assertEqual("123", env[SOURCE_DATE_EPOCH_ENV])

    def test_source_date_epoch_should_fail_closed_when_required_or_invalid(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "required"):
            source_date_epoch_from_environment({}, required=True)
        with self.assertRaisesRegex(RuntimeError, "integer"):
            source_date_epoch_from_environment({SOURCE_DATE_EPOCH_ENV: "tomorrow"})
        with self.assertRaisesRegex(RuntimeError, "negative"):
            source_date_epoch_from_environment({SOURCE_DATE_EPOCH_ENV: "-1"})

    def test_clean_gate_should_ignore_untracked_but_reject_tracked_changes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            clean = subprocess.CompletedProcess(["git"], 0, stdout="", stderr="")
            with mock.patch("tools.release_reproducibility.subprocess.run", return_value=clean):
                ensure_tracked_worktree_clean(root)

            dirty = subprocess.CompletedProcess(
                ["git"],
                0,
                stdout=" M tools/example.py\n",
                stderr="",
            )
            with mock.patch("tools.release_reproducibility.subprocess.run", return_value=dirty):
                with self.assertRaisesRegex(RuntimeError, "tools/example.py"):
                    ensure_tracked_worktree_clean(root)

    def test_clean_gate_should_allow_only_hash_verified_review_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._git(root, "init", "-q")
            self._git(root, "config", "user.name", "Queue Test")
            self._git(root, "config", "user.email", "queue@example.test")
            target = root / "docs" / "_review" / "M" / "US"
            target.mkdir(parents=True)
            (target / "page.rst").write_text("main\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-qm", "main")
            main_sha = self._git(root, "rev-parse", "HEAD")
            self._git(root, "checkout", "-qb", "review")
            (target / "page.rst").write_text("reviewed\n", encoding="utf-8")
            (target / "extra.rst").write_text("extra\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-qm", "review")
            review_sha = self._git(root, "rev-parse", "HEAD")
            self._git(root, "checkout", "-q", main_sha)
            self._git(root, "restore", "--source", review_sha, "--staged", "--worktree", "--", "docs/_review/M/US")

            env = {
                REVIEW_OVERLAY_REF_ENV: "review/M-US",
                REVIEW_OVERLAY_SHA_ENV: review_sha,
                REVIEW_OVERLAY_PATH_ENV: "docs/_review/M/US",
            }
            overlay = review_overlay_from_environment(root, env)
            self.assertIsNotNone(overlay)
            ensure_tracked_worktree_clean(root, review_overlay=overlay)

            (root / "outside.txt").write_text("unexpected\n", encoding="utf-8")
            self._git(root, "add", "outside.txt")
            with self.assertRaisesRegex(RuntimeError, "outside.txt"):
                ensure_tracked_worktree_clean(root, review_overlay=overlay)

if __name__ == "__main__":
    unittest.main()
