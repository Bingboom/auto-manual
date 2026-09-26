from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "derived_surface_guard.py"
SPEC = importlib.util.spec_from_file_location("derived_surface_guard", HOOK)
guard = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(guard)


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def run_hook(payload: object, *, project_dir: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project_dir))
    data = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run([sys.executable, str(HOOK)], input=data, capture_output=True, text=True, env=env)


def bash(command: str, cwd: Path) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd)}


class BuildDirectoryTests(unittest.TestCase):
    def test_follows_cd_steps_and_the_script_path(self) -> None:
        start = Path("/start")
        cases = {
            "python build.py check": Path("/start"),
            "cd /wt && python build.py check": Path("/wt"),
            "cd sub && .venv/bin/python build.py sync-review": Path("/start/sub"),
            "(cd '/wt dir' && python build.py publish)": Path("/wt dir"),
            'cd "/wt dir"; python build.py check --config x': Path("/wt dir"),
            "python /abs/wt/build.py check": Path("/abs/wt"),
            "cd /wt && python ../other/build.py check": Path("/wt/../other"),
            "echo hi && python build.py check | tail -1": Path("/start"),
        }
        for command, expected in cases.items():
            with self.subTest(command):
                self.assertEqual(guard.build_directory(command, start), expected)


class DerivedSurfaceGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(os.path.realpath(temp.name))
        self.primary, self.worktree = root / "primary", root / "wt"
        self.primary.mkdir()
        git(self.primary, "init", "-q", "-b", "main")
        git(self.primary, "config", "user.name", "Test")
        git(self.primary, "config", "user.email", "test@example.com")
        for rel in ("docs/_build/a.txt", "docs/_review/r.txt", "README.md"):
            path = self.primary / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("seed\n", encoding="utf-8")
        git(self.primary, "add", ".")
        git(self.primary, "commit", "-q", "-m", "seed")
        git(self.primary, "worktree", "add", "-q", "-b", "feat", str(self.worktree))
        # Another window's leftovers in the shared primary checkout.
        (self.primary / "docs" / "_build" / "a.txt").write_text("other window\n", encoding="utf-8")

    def test_reports_the_checkout_the_build_ran_in(self) -> None:
        result = run_hook(bash("python build.py check", self.primary), project_dir=self.primary)
        self.assertEqual(result.returncode, 2)
        self.assertIn(f"dirty in {self.primary}: docs/_build (1)", result.stderr)
        self.assertIn("may belong to another window", result.stderr)

    def test_a_worktree_build_ignores_the_primary_checkout(self) -> None:
        # The old hook always checked CLAUDE_PROJECT_DIR and reported these as ours.
        for command in (f"cd {self.worktree} && python build.py check",
                        f"python {self.worktree}/build.py check"):
            with self.subTest(command):
                result = run_hook(bash(command, self.primary), project_dir=self.primary)
                self.assertEqual((result.returncode, result.stderr), (0, ""))

    def test_a_dirty_worktree_is_named_in_the_warning(self) -> None:
        (self.worktree / "docs" / "_review" / "r.txt").write_text("token rotation\n", encoding="utf-8")
        result = run_hook(bash(f"cd {self.worktree} && python build.py sync-review", self.primary),
                          project_dir=self.primary)
        self.assertEqual(result.returncode, 2)
        self.assertIn(f"dirty in {self.worktree}: docs/_review (1)", result.stderr)
        self.assertNotIn("docs/_build", result.stderr.split(":")[1])

    def test_everything_else_stays_silent(self) -> None:
        outside = self.primary.parent / "not-a-repo"
        outside.mkdir()
        for payload in (
            bash("git status", self.primary),
            {"tool_name": "Read", "tool_input": {"file_path": "x"}, "cwd": str(self.primary)},
            "{not json",
            bash(f"cd {outside} && python build.py check", self.primary),
        ):
            with self.subTest(payload):
                result = run_hook(payload, project_dir=self.primary)
                self.assertEqual((result.returncode, result.stderr), (0, ""))


if __name__ == "__main__":
    unittest.main()
