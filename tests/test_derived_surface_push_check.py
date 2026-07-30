from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "derived_surface_push_check.py"
MODULE_SPEC = importlib.util.spec_from_file_location("derived_surface_push_check", MODULE_PATH)
derived_surface_push_check = importlib.util.module_from_spec(MODULE_SPEC)
assert MODULE_SPEC.loader is not None
MODULE_SPEC.loader.exec_module(derived_surface_push_check)

ZERO = derived_surface_push_check.ZERO_SHA


def run_git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "").strip()
        raise AssertionError(f"git {' '.join(args)} failed.\n{message}")
    return completed.stdout


class DerivedSurfacePushCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        run_git(self.repo, "init", "-b", "main")
        run_git(self.repo, "config", "user.name", "Test")
        run_git(self.repo, "config", "user.email", "test@example.com")
        self._commit_file("README.md", "initial\n", "initial")
        self.base_sha = self._head()
        # a local origin/main ref so merge-base for new branches resolves
        run_git(self.repo, "update-ref", "refs/remotes/origin/main", self.base_sha)

    def _commit_file(self, rel_path: str, content: str, message: str) -> None:
        target = self.repo / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        run_git(self.repo, "add", rel_path)
        run_git(self.repo, "commit", "-m", message)

    def _head(self) -> str:
        return run_git(self.repo, "rev-parse", "HEAD").strip()

    def _check(self, branch: str, local_sha: str, remote_sha: str) -> str | None:
        line = f"refs/heads/{branch} {local_sha} refs/heads/{branch} {remote_sha}"
        return derived_surface_push_check.check_push([line], self.repo)

    def test_warns_on_derived_surface_change(self) -> None:
        run_git(self.repo, "checkout", "-b", "fix/some-topic")
        self._commit_file("docs/_build/M/out.txt", "built\n", "touch derived")
        message = self._check("fix/some-topic", self._head(), ZERO)
        self.assertIsNotNone(message)
        assert message is not None
        self.assertIn("docs/_build (1)", message)
        self.assertIn("fix/some-topic", message)

    def test_counts_multiple_surfaces(self) -> None:
        run_git(self.repo, "checkout", "-b", "fix/mixed")
        self._commit_file("docs/index.rst", "index\n", "touch index")
        self._commit_file("docs/_review/M/R/page/p.rst", "page\n", "touch review")
        message = self._check("fix/mixed", self._head(), ZERO)
        assert message is not None
        self.assertIn("docs/index.rst (1)", message)
        self.assertIn("docs/_review (1)", message)

    def test_silent_when_no_surface_touched(self) -> None:
        run_git(self.repo, "checkout", "-b", "fix/clean")
        self._commit_file("tools/util.py", "x = 1\n", "code only")
        self.assertIsNone(self._check("fix/clean", self._head(), ZERO))

    def test_exempts_review_and_backport_branches(self) -> None:
        run_git(self.repo, "checkout", "-b", "review/JE-1000F-US")
        self._commit_file("docs/_review/M/R/page/p.rst", "page\n", "review edit")
        head = self._head()
        self.assertIsNone(self._check("review/JE-1000F-US", head, ZERO))
        self.assertIsNone(self._check("backport/JE-1000F-US-r1", head, ZERO))

    def test_skips_ref_deletions_and_tags(self) -> None:
        self.assertIsNone(self._check("fix/deleted", ZERO, self.base_sha))
        line = f"refs/tags/v1 {self.base_sha} refs/tags/v1 {ZERO}"
        self.assertIsNone(derived_surface_push_check.check_push([line], self.repo))

    def test_diffs_against_remote_sha_for_existing_branch(self) -> None:
        run_git(self.repo, "checkout", "-b", "fix/incremental")
        self._commit_file("docs/_build/M/out.txt", "built\n", "old, already pushed")
        already_pushed = self._head()
        self._commit_file("tools/other.py", "y = 2\n", "new, clean")
        # only the new commit is outgoing -> no surface touched -> silent
        self.assertIsNone(self._check("fix/incremental", self._head(), already_pushed))


if __name__ == "__main__":
    unittest.main()
