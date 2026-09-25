from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import rtd_system_tooling as tooling
from tools.utils.path_utils import repo_root


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def skill(name: str | None, description: str) -> str:
    head = f"name: {name}\n" if name else ""
    return f"---\n{head}description: {description}\n---\n\n# Skill\n"


class SkillFactsTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        write(self.root, "AGENTS.md", "- Use [`.agents/skills/alpha/SKILL.md`](.agents/skills/alpha/SKILL.md).\n")
        write(self.root, ".claude/skills/README.md", "- `alpha`: the Claude copy.\n")
        write(self.root, ".agents/skills/alpha/SKILL.md", skill("alpha", "Alpha runs the thing, e.g. a build. Then more."))
        write(self.root, ".claude/skills/alpha/SKILL.md", skill(None, "Claude alpha."))
        write(self.root, ".agents/skills/beta/SKILL.md", skill("beta", "Beta."))
        write(self.root, ".agents/skills/gamma/SKILL.md", skill(None, "Gamma lacks a name."))
        write(self.root, ".claude/skills/delta/SKILL.md", skill("other", "Delta's name contradicts its directory."))
        write(self.root, ".agents/skills/Bad_Name/SKILL.md", skill("Bad_Name", "Bad."))

    def test_merges_copies_and_names_every_gap(self) -> None:
        facts = {entry["id"]: entry for entry in tooling.skill_facts(self.root)}
        self.assertEqual(sorted(facts), ["Bad_Name", "alpha", "beta", "delta", "gamma"])
        alpha = facts["alpha"]
        self.assertEqual((alpha["agents"], alpha["unregistered"], alpha["problems"]), (["Codex", "Claude"], [], []))
        # The Codex description wins; Claude copies may omit name.
        self.assertTrue(alpha["description"].startswith("Alpha runs"))
        self.assertEqual(facts["beta"]["unregistered"], ["Codex"])
        self.assertEqual(facts["gamma"]["problems"], ["Codex copy needs frontmatter name 'gamma'"])
        self.assertEqual((facts["delta"]["unregistered"], facts["delta"]["problems"]),
                         (["Claude"], ["Claude copy needs frontmatter name 'delta'"]))
        self.assertIn("skill name is not lowercase hyphen-case", facts["Bad_Name"]["problems"])

    def test_view_groups_by_lane_and_keeps_the_first_sentence(self) -> None:
        skills = tooling.skill_facts(self.root)
        config = {"note": "n", "skill_lanes": {"web": ["alpha"], "ir": []}}
        lanes = {"web": {"title": "网页化", "horizon": "now", "horizon_label": "现在"},
                 "ir": {"title": "IR", "horizon": "next", "horizon_label": "下一步"}}
        view = tooling.tooling_view(config, skills, [], lanes)
        self.assertEqual([(g["title"], [r["id"] for r in g["rows"]]) for g in view["groups"]],
                         [("网页化", ["alpha"]), ("IR", []), ("其他技能", ["Bad_Name", "beta", "delta", "gamma"])])
        self.assertEqual(view["groups"][0]["rows"][0]["summary"], "Alpha runs the thing, e.g. a build.")
        tiles = {tile["label"]: tile for tile in view["tiles"]}
        self.assertEqual((tiles["技能"]["value"], tiles["技能"]["sub"]), ("5", "Codex 4 · Claude 2"))
        # Only alpha is listed in AGENTS.md, and delta's Claude copy is not in the README.
        self.assertEqual(sorted(s["id"] for s in skills if s["unregistered"]), ["Bad_Name", "beta", "delta", "gamma"])
        self.assertEqual(tiles["未登记的技能"]["value"], "4")


class HookFactsTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        settings = {"hooks": {"PostToolUse": [{"matcher": "Bash", "hooks": [
            {"type": "command", "command": 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/guard_a.py"'}]}]}}
        write(self.root, ".claude/settings.json", json.dumps(settings))
        write(self.root, ".claude/hooks/guard_a.py", '"""Guard A: warns about things.\n\nMore."""\n')
        write(self.root, "tests/test_guard_a.py", "")
        write(self.root, ".githooks/pre-push",
              '"${python_cmd}" "${repo_root}/tools/advice.py" \\\n  --repo-root "${repo_root}" || true\n'
              'exec "${python_cmd}" "${repo_root}/scripts/blocker.py" \\\n  pre-push\n')
        write(self.root, "tools/advice.py", "print('no docstring')\n")

    def test_reads_both_layers_with_mode_tests_and_purpose(self) -> None:
        hooks = tooling.hook_facts(self.root)
        self.assertEqual([(h["layer"], h["event"], h["matcher"], h["script"], h["blocking"]) for h in hooks], [
            ("Claude Code", "PostToolUse", "Bash", ".claude/hooks/guard_a.py", False),
            ("git", "pre-push", "", "tools/advice.py", False),
            ("git", "pre-push", "", "scripts/blocker.py", True),
        ])
        self.assertEqual([(h["exists"], h["tested"], h["purpose"]) for h in hooks], [
            (True, True, "Guard A: warns about things."), (True, False, ""), (False, False, "")])
        view = tooling.tooling_view({}, [], hooks, {})
        self.assertEqual([(h["trigger"], h["mode_label"]) for h in view["hooks"]],
                         [("PostToolUse · Bash", "提醒"), ("pre-push", "提醒"), ("pre-push", "拦截")])
        self.assertEqual({t["label"]: t["value"] for t in view["tiles"]}["没有测试的钩子"], "2")

    def test_findings_grade_contract_errors_above_data_gaps(self) -> None:
        skills = [{"id": "alpha", "description": "d", "agents": ["Codex"], "unregistered": ["Codex"],
                   "problems": ["Codex copy has no frontmatter description"]}]
        found = tooling.tooling_findings({"skill_lanes": {"web": ["alpha", "missing"]}}, skills,
                                         tooling.hook_facts(self.root))
        self.assertEqual(found, [
            ("error", "tooling.skill_lanes.web", "no skill named 'missing' in the tree"),
            ("warning", "skill alpha", "Codex copy is not registered in AGENTS.md"),
            ("warning", "skill alpha", "Codex copy has no frontmatter description"),
            ("warning", "hook tools/advice.py", "has no tests/test_<script>.py"),
            ("warning", "hook scripts/blocker.py", "script is missing"),
        ])

    def test_contract_section_problems(self) -> None:
        self.assertEqual(tooling.tooling_problems({"skill_lanes": {"web": []}}, {"web"}), [])
        self.assertEqual(tooling.tooling_problems([], {"web"}), ["tooling must be a mapping"])
        self.assertEqual(tooling.tooling_problems({"skill_lanes": {"web": "alpha", "tm": []}}, {"web"}), [
            "tooling.skill_lanes: unknown focus lane 'tm'", "tooling.skill_lanes.web must be a list of skill names"])


class ShippedToolingTests(unittest.TestCase):
    def test_the_tree_has_readable_skills_and_hooks(self) -> None:
        root = repo_root()
        skills = tooling.skill_facts(root)
        self.assertGreaterEqual(len(skills), 18)
        self.assertEqual([s["id"] for s in skills if s["problems"]], [])
        hooks = {(h["layer"], Path(h["script"]).name): h for h in tooling.hook_facts(root)}
        self.assertIn(("Claude Code", "derived_surface_guard.py"), hooks)
        self.assertTrue(hooks[("git", "git_branch_guard.py")]["blocking"])


if __name__ == "__main__":
    unittest.main()
