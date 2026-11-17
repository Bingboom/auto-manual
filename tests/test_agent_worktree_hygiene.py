from __future__ import annotations

import json
import tomllib
import unittest

from tools.utils.path_utils import repo_root


class AgentWorktreeHygieneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = repo_root()

    def test_gitignore_covers_nested_claude_worktrees(self) -> None:
        gitignore = (self.root / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".claude/worktrees/", gitignore)

    def test_codexignore_covers_nested_worktrees_and_correct_tmp_dir(self) -> None:
        lines = [line.strip() for line in (self.root / ".codexignore").read_text(encoding="utf-8").splitlines()]
        self.assertIn(".claude/worktrees/**", lines)
        self.assertIn(".tmp/", lines)
        self.assertNotIn("tmp/", lines)

    def test_claude_settings_deny_rule_covers_nested_worktrees(self) -> None:
        settings_text = (self.root / ".claude" / "settings.json").read_text(encoding="utf-8")
        settings = json.loads(settings_text)
        deny = settings.get("permissions", {}).get("deny", [])
        self.assertIn("Read(./.claude/worktrees/**)", deny)
        # Check that deny patterns are all relative globs (no absolute paths or secrets)
        for pattern in deny:
            self.assertTrue(pattern.startswith("Read(./"), f"deny pattern must be a relative glob: {pattern}")
            self.assertFalse(pattern.startswith("Read(/"), f"deny pattern must not be absolute: {pattern}")

    def test_pyproject_toml_extend_exclude_covers_nested_worktrees(self) -> None:
        pyproject_text = (self.root / "pyproject.toml").read_text(encoding="utf-8")
        pyproject = tomllib.loads(pyproject_text)
        extend_exclude = pyproject.get("tool", {}).get("ruff", {}).get("extend-exclude", [])
        self.assertIn(".claude/worktrees", extend_exclude)


if __name__ == "__main__":
    unittest.main()
