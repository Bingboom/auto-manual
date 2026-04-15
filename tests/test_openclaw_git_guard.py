from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "openclaw_git_guard.py"
MODULE_SPEC = importlib.util.spec_from_file_location("openclaw_git_guard", MODULE_PATH)
openclaw_git_guard = importlib.util.module_from_spec(MODULE_SPEC)
assert MODULE_SPEC.loader is not None
MODULE_SPEC.loader.exec_module(openclaw_git_guard)


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


def run_guard(*args: str) -> tuple[int, dict[str, object]]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        exit_code = openclaw_git_guard.main(list(args))
    output = buffer.getvalue().strip()
    payload = json.loads(output) if output else {}
    return exit_code, payload


class TestOpenClawGitGuard(unittest.TestCase):
    def test_status_should_report_allowed_and_disallowed_dirty_lines(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, clone_repo = init_remote_clone(Path(td))
            generated_file = clone_repo / ".tmp" / "translation.log"
            generated_file.parent.mkdir(parents=True)
            generated_file.write_text("ok\n", encoding="utf-8")
            (clone_repo / "README.md").write_text("changed\n", encoding="utf-8")

            exit_code, payload = run_guard("status", "--repo-root", str(clone_repo))

            self.assertEqual(0, exit_code)
            self.assertTrue(payload["dirty"])
            self.assertTrue(payload["allowed_dirty_lines"])
            self.assertTrue(payload["disallowed_dirty_lines"])
            self.assertFalse(payload["safe_to_switch"])

    def test_switch_should_reject_non_generated_dirty_paths(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, clone_repo = init_remote_clone(Path(td))
            (clone_repo / "README.md").write_text("changed\n", encoding="utf-8")

            exit_code, payload = run_guard(
                "switch",
                "--repo-root",
                str(clone_repo),
                "--branch",
                "main",
                "--pull",
            )

            self.assertEqual(1, exit_code)
            self.assertFalse(payload["ok"])
            self.assertIn("dirty worktree", str(payload["error"]))

    def test_switch_should_checkout_remote_branch_and_create_local_tracking_branch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, clone_repo = init_remote_clone(Path(td))
            run_git(clone_repo, "checkout", "-b", "codex/review-demo")
            (clone_repo / "notes.txt").write_text("demo\n", encoding="utf-8")
            run_git(clone_repo, "add", "notes.txt")
            run_git(clone_repo, "commit", "-m", "review demo")
            run_git(clone_repo, "push", "-u", "origin", "codex/review-demo")
            run_git(clone_repo, "switch", "main")
            run_git(clone_repo, "branch", "-D", "codex/review-demo")

            exit_code, payload = run_guard(
                "switch",
                "--repo-root",
                str(clone_repo),
                "--branch",
                "codex/review-demo",
            )

            self.assertEqual(0, exit_code)
            self.assertTrue(payload["ok"])
            self.assertTrue(payload["created_local_branch"])
            self.assertEqual("codex/review-demo", payload["to_branch"])
            self.assertEqual("origin/codex/review-demo", payload["tracking_branch"])

    def test_switch_should_fetch_and_fast_forward_pull_existing_branch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            remote_repo, clone_repo = init_remote_clone(Path(td))
            updater_repo = Path(td) / "updater"
            run_git(Path(td), "clone", str(remote_repo), str(updater_repo))
            configure_git_identity(updater_repo)
            run_git(updater_repo, "switch", "main")
            (updater_repo / "README.md").write_text("updated remotely\n", encoding="utf-8")
            run_git(updater_repo, "add", "README.md")
            run_git(updater_repo, "commit", "-m", "remote update")
            run_git(updater_repo, "push", "origin", "main")
            remote_head = run_git(updater_repo, "rev-parse", "--short", "HEAD").stdout.strip()

            exit_code, payload = run_guard(
                "switch",
                "--repo-root",
                str(clone_repo),
                "--branch",
                "main",
                "--pull",
            )

            self.assertEqual(0, exit_code)
            self.assertTrue(payload["performed_pull"])
            self.assertEqual("main", payload["to_branch"])
            self.assertEqual(remote_head, payload["to_head_sha"])


if __name__ == "__main__":
    unittest.main()
