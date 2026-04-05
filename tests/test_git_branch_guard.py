from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "git_branch_guard.py"
MODULE_SPEC = importlib.util.spec_from_file_location("git_branch_guard", MODULE_PATH)
git_branch_guard = importlib.util.module_from_spec(MODULE_SPEC)
assert MODULE_SPEC.loader is not None
MODULE_SPEC.loader.exec_module(git_branch_guard)


def run_git(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if check and completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "").strip()
        raise AssertionError(f"git {' '.join(args)} failed.\n{message}")
    return completed


def configure_git_identity(repo_root: Path) -> None:
    run_git(repo_root, "config", "user.name", "Codex Test")
    run_git(repo_root, "config", "user.email", "codex@example.com")


def init_remote_clone(temp_root: Path) -> tuple[Path, Path]:
    remote_repo = temp_root / "remote.git"
    seed_repo = temp_root / "seed"
    clone_repo = temp_root / "clone"

    run_git(temp_root, "init", "--bare", str(remote_repo))
    run_git(temp_root, "init", str(seed_repo))
    configure_git_identity(seed_repo)
    run_git(seed_repo, "checkout", "-b", "main")
    (seed_repo / "README.md").write_text("initial\n", encoding="utf-8")
    run_git(seed_repo, "add", "README.md")
    run_git(seed_repo, "commit", "-m", "initial")
    run_git(seed_repo, "remote", "add", "origin", str(remote_repo))
    run_git(seed_repo, "push", "-u", "origin", "main")
    run_git(remote_repo, "symbolic-ref", "HEAD", "refs/heads/main")

    run_git(temp_root, "clone", str(remote_repo), str(clone_repo))
    configure_git_identity(clone_repo)
    return remote_repo, clone_repo


class TestGitBranchGuard(unittest.TestCase):
    def test_collect_disallowed_dirty_lines_should_ignore_generated_paths(self) -> None:
        lines = [
            " M docs/_build/JE-1000F/US/rst/index.rst",
            "?? reports/releases/demo/out.html",
            "?? .tmp/smoke/check.log",
            " M README.md",
        ]

        dirty = git_branch_guard.collect_disallowed_dirty_lines(lines)

        self.assertEqual([" M README.md"], dirty)

    def test_start_branch_should_allow_generated_only_dirty_paths(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, clone_repo = init_remote_clone(Path(td))
            generated_file = clone_repo / ".tmp" / "smoke.log"
            generated_file.parent.mkdir(parents=True)
            generated_file.write_text("ok\n", encoding="utf-8")

            result = git_branch_guard.start_branch_command(
                git_branch_guard.build_parser().parse_args(
                    [
                        "start-branch",
                        "--repo-root",
                        str(clone_repo),
                        "--branch",
                        "codex/generated-only",
                    ]
                )
            )

            self.assertEqual(0, result)
            self.assertEqual("codex/generated-only", git_branch_guard.current_branch(clone_repo))

    def test_start_branch_should_reject_non_generated_dirty_paths(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, clone_repo = init_remote_clone(Path(td))
            (clone_repo / "README.md").write_text("changed\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "dirty worktree"):
                git_branch_guard.start_branch_command(
                    git_branch_guard.build_parser().parse_args(
                        [
                            "start-branch",
                            "--repo-root",
                            str(clone_repo),
                            "--branch",
                            "codex/dirty-worktree",
                        ]
                    )
                )

    def test_pre_push_should_block_stale_branch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            remote_repo, clone_repo = init_remote_clone(Path(td))

            git_branch_guard.start_branch_command(
                git_branch_guard.build_parser().parse_args(
                    [
                        "start-branch",
                        "--repo-root",
                        str(clone_repo),
                        "--branch",
                        "codex/stale-branch",
                    ]
                )
            )

            run_git(clone_repo, "switch", "main")
            (clone_repo / "README.md").write_text("updated on main\n", encoding="utf-8")
            run_git(clone_repo, "add", "README.md")
            run_git(clone_repo, "commit", "-m", "update main")
            run_git(clone_repo, "push", "origin", "main")
            run_git(remote_repo, "symbolic-ref", "HEAD", "refs/heads/main")
            run_git(clone_repo, "switch", "codex/stale-branch")

            result = git_branch_guard.pre_push_command(
                git_branch_guard.build_parser().parse_args(
                    [
                        "pre-push",
                        "--repo-root",
                        str(clone_repo),
                        "--remote",
                        "origin",
                        "--base-branch",
                        "main",
                    ]
                )
            )

            self.assertEqual(1, result)


if __name__ == "__main__":
    unittest.main()
