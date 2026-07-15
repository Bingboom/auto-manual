from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import queue_bound_runtime
from tools import queue_runtime


class QueueBoundRuntimeTests(unittest.TestCase):
    def test_prepare_git_ref_worktree_adapts_worktree_dir_provider_signature(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def fake_prepare_impl(
                *,
                repo_root: Path,
                git_ref: str,
                prefer_local: bool,
                run_git,
                worktree_dir_for_git_ref,
                remove_worktree,
            ) -> Path:
                self.assertEqual(repo_root, root)
                self.assertEqual(git_ref, "feature/test")
                self.assertTrue(prefer_local)
                worktree_path = worktree_dir_for_git_ref(repo_root=repo_root, git_ref=git_ref)
                self.assertEqual(
                    worktree_path,
                    root / ".tmp" / "process-build-queue-worktrees" / "feature-test",
                )
                remove_worktree(repo_root=repo_root, path=worktree_path)
                return root / "prepared-worktree"

            with mock.patch.object(queue_bound_runtime, "_repo_root_provider", lambda: root), mock.patch.object(
                queue_bound_runtime,
                "_prepare_git_ref_worktree_impl",
                side_effect=fake_prepare_impl,
            ), mock.patch.object(queue_bound_runtime, "remove_worktree") as remove_mock:
                result = queue_bound_runtime.prepare_git_ref_worktree("feature/test")

        self.assertEqual(result, root / "prepared-worktree")
        remove_mock.assert_called_once_with(root / ".tmp" / "process-build-queue-worktrees" / "feature-test")

    def test_prepare_git_ref_worktree_should_retry_retryable_fetch_errors(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            calls: list[list[str]] = []
            sleeps: list[float] = []

            def fake_run_git(args: list[str]) -> None:
                calls.append(args)
                if len(calls) == 1:
                    raise RuntimeError(
                        "fatal: unable to access 'https://github.com/example/repo.git/': Recv failure: Connection was reset"
                    )

            result = queue_runtime.prepare_git_ref_worktree(
                repo_root=root,
                git_ref="feature/test",
                run_git=fake_run_git,
                worktree_dir_for_git_ref=lambda *, repo_root, git_ref: repo_root / ".tmp" / git_ref.replace("/", "-"),
                remove_worktree=lambda *, repo_root, path: None,
                sleep=lambda seconds: sleeps.append(seconds),
            )

        self.assertEqual(root / ".tmp" / "feature-test", result)
        self.assertEqual(4, len(calls))
        self.assertEqual(
            ["-c", "http.version=HTTP/1.1", "-c", "http.schannelCheckRevoke=false", "fetch", "origin", "--prune"],
            calls[0],
        )
        self.assertEqual(calls[0], calls[1])
        self.assertEqual([1.0], sleeps)

    def test_prepare_git_ref_worktree_should_not_retry_nonretryable_fetch_errors(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            calls: list[list[str]] = []

            def fake_run_git(args: list[str]) -> None:
                calls.append(args)
                raise RuntimeError("fatal: repository not found")

            with self.assertRaisesRegex(RuntimeError, "repository not found"):
                queue_runtime.prepare_git_ref_worktree(
                    repo_root=root,
                    git_ref="feature/test",
                    run_git=fake_run_git,
                    worktree_dir_for_git_ref=lambda *, repo_root, git_ref: repo_root / ".tmp" / git_ref.replace("/", "-"),
                    remove_worktree=lambda *, repo_root, path: None,
                    sleep=lambda seconds: None,
                )

        self.assertEqual(1, len(calls))

    def test_prepare_git_ref_worktree_should_fallback_to_cached_remote_ref_after_fetch_failures(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            calls: list[list[str]] = []
            sleeps: list[float] = []

            def fake_run_git(args: list[str]) -> None:
                calls.append(args)
                if args[:6] == ["-c", "http.version=HTTP/1.1", "-c", "http.schannelCheckRevoke=false", "fetch", "origin"]:
                    raise RuntimeError(
                        "fatal: unable to access 'https://github.com/example/repo.git/': Failed to connect to github.com port 443"
                    )

            result = queue_runtime.prepare_git_ref_worktree(
                repo_root=root,
                git_ref="feature/test",
                run_git=fake_run_git,
                worktree_dir_for_git_ref=lambda *, repo_root, git_ref: repo_root / ".tmp" / git_ref.replace("/", "-"),
                remove_worktree=lambda *, repo_root, path: None,
                git_ref_exists=lambda *, repo_root, ref: ref == "refs/remotes/origin/feature/test",
                sleep=lambda seconds: sleeps.append(seconds),
            )

        self.assertEqual(root / ".tmp" / "feature-test", result)
        self.assertEqual(
            ["git", "worktree", "add", "--force", "--detach", str(root / ".tmp" / "feature-test"), "origin/feature/test"],
            ["git", *calls[-1]],
        )
        self.assertEqual([1.0, 2.0, 4.0], sleeps)

    def test_prepare_git_ref_worktree_should_prefer_local_branch_without_fetch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            calls: list[list[str]] = []

            def fake_run_git(args: list[str]) -> None:
                calls.append(args)

            result = queue_runtime.prepare_git_ref_worktree(
                repo_root=root,
                git_ref="feature/test",
                run_git=fake_run_git,
                worktree_dir_for_git_ref=lambda *, repo_root, git_ref: repo_root / ".tmp" / git_ref.replace("/", "-"),
                remove_worktree=lambda *, repo_root, path: None,
                git_ref_exists=lambda *, repo_root, ref: ref == "refs/heads/feature/test",
                sleep=lambda seconds: None,
            )

        self.assertEqual(root / ".tmp" / "feature-test", result)
        self.assertEqual(
            ["worktree", "add", "--force", "--detach", str(root / ".tmp" / "feature-test"), "feature/test"],
            calls[-1],
        )
        self.assertEqual(1, len(calls))

    def test_prepare_git_ref_worktree_should_use_remote_when_local_preference_is_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            calls: list[list[str]] = []

            def fake_run_git(args: list[str]) -> None:
                calls.append(args)

            result = queue_runtime.prepare_git_ref_worktree(
                repo_root=root,
                git_ref="main",
                prefer_local=False,
                run_git=fake_run_git,
                worktree_dir_for_git_ref=lambda *, repo_root, git_ref: root / ".tmp" / git_ref,
                remove_worktree=lambda *, repo_root, path: None,
                git_ref_exists=lambda *, repo_root, ref: ref == "refs/heads/main",
                sleep=lambda seconds: None,
            )

        self.assertEqual(root / ".tmp" / "main", result)
        self.assertEqual(
            ["worktree", "add", "--force", "--detach", str(root / ".tmp" / "main"), "origin/main"],
            calls[-1],
        )
        self.assertEqual(3, len(calls))


if __name__ == "__main__":
    unittest.main()
