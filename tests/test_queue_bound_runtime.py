from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import queue_bound_runtime


class QueueBoundRuntimeTests(unittest.TestCase):
    def test_prepare_git_ref_worktree_adapts_worktree_dir_provider_signature(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def fake_prepare_impl(
                *,
                repo_root: Path,
                git_ref: str,
                run_git,
                worktree_dir_for_git_ref,
                remove_worktree,
            ) -> Path:
                self.assertEqual(repo_root, root)
                self.assertEqual(git_ref, "feature/test")
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


if __name__ == "__main__":
    unittest.main()
