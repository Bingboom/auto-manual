from __future__ import annotations

import copy
import datetime as dt
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml
from jinja2 import Environment, FileSystemLoader

from tools.rtd import system_evolution as evolution
from tools.rtd import system_workspace as workspace
from tools.rtd.source_registry import load_registry
from tools.rtd.system_tooling import hook_facts, skill_facts
from tools.utils.path_utils import repo_root

ROOT = repo_root()
ASSETS = workspace.DEFAULT_CONTRACT.parent
REGISTRY, _ = load_registry(ASSETS)
DOMAIN = REGISTRY["evolution"]
REPOS = {"auto-manual": "https://github.com/Bingboom/auto-manual"}
HISTORY = ROOT / DOMAIN["authority"].split(":", 2)[2]
TEXT = HISTORY.read_text(encoding="utf-8")
DATA = yaml.safe_load(TEXT.split(evolution.START, 1)[1].split("```yaml\n", 1)[1].split("\n```", 1)[0])


class SystemEvolutionTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.domain = {**DOMAIN, "authority": "file:auto-manual:history.md"}
        self.data = copy.deepcopy(DATA)

    def write_story(self):
        self.text = (f"Updated: {self.data['updated_on']}\n\n{evolution.START}\n```yaml\n"
                     f"{yaml.safe_dump(self.data, allow_unicode=True)}\n```\n{evolution.END}\n")
        (self.root / "history.md").write_text(self.text, encoding="utf-8")

    def view(self):
        return evolution.evolution_view(root=self.root, domain=self.domain, repositories=REPOS)

    def test_history_is_the_only_timeline_source_and_future_is_distinct(self):
        view = evolution.evolution_view(root=ROOT, domain=DOMAIN, repositories=REPOS)
        self.assertEqual(view["problems"], [])
        self.assertEqual(len(view["stages"]), 12)
        self.assertEqual([s["status"] for s in view["stages"]],
                         ["recorded"] * 3 + ["in_progress", "ongoing", "ongoing", "recorded", "ongoing"] + ["planned"] * 4)
        self.write_story()
        self.assertEqual(self.view()["stages"][0]["summary"], DATA["stages"][0]["summary"])
        self.data["stages"][0]["summary"] = "源文件中的修订立即出现在展示中"
        self.write_story()
        self.assertEqual(self.view()["stages"][0]["summary"], self.data["stages"][0]["summary"])

    def test_crosscutting_work_is_separate_and_older_summaries_remain_readable(self):
        self.write_story()
        self.assertEqual(self.view()["crosscutting"][0]["id"], "engineering")
        self.assertNotIn("engineering", [s["id"] for s in self.view()["stages"]])
        self.data["crosscutting"][0]["summary"] = "贯穿整个建设过程的维护记录"
        self.write_story()
        self.assertEqual(self.view()["crosscutting"][0]["summary"], "贯穿整个建设过程的维护记录")
        del self.data["crosscutting"]
        self.write_story()
        self.assertEqual(self.view()["problems"], [])
        self.assertEqual(self.view()["crosscutting"], [])

    def test_authoring_errors_do_not_fabricate_a_timeline(self):
        for mutation in ("duplicate_id", "bad_status", "missing_evidence", "bad_date", "wrong_schema",
                         "duplicate_crosscutting_id", "bad_crosscutting", "crosscutting_evidence"):
            with self.subTest(mutation=mutation):
                self.data = copy.deepcopy(DATA)
                match mutation:
                    case "duplicate_id": self.data["stages"][1]["id"] = self.data["stages"][0]["id"]
                    case "bad_status": self.data["stages"][-1]["status"] = "available"
                    case "missing_evidence": self.data["stages"][0]["evidence"] = []
                    case "bad_date": self.data["updated_on"] = "unknown"
                    case "wrong_schema": self.data["schema"] = "other"
                    case "duplicate_crosscutting_id": self.data["crosscutting"][0]["id"] = self.data["stages"][0]["id"]
                    case "bad_crosscutting": self.data["crosscutting"] = {}
                    case "crosscutting_evidence": self.data["crosscutting"][0]["evidence"] = []
                self.write_story()
                self.assertTrue(self.view()["problems"])
                self.assertEqual(self.view()["stages"], [])

    def test_missing_bad_fences_and_multiple_summaries_fall_back(self):
        self.assertTrue(self.view()["problems"])
        self.write_story()
        for text in (self.text.replace("```yaml", "```json"), self.text * 2,
                     self.text.replace("stages:", "stages: ["),
                     self.text.replace(evolution.START, "REVERSE_START", 1).replace(evolution.END, evolution.START, 1).replace("REVERSE_START", evolution.END, 1)):
            (self.root / "history.md").write_text(text, encoding="utf-8")
            self.assertTrue(self.view()["problems"])
        self.assertIsNone(evolution.evolution_view(root=self.root, domain=None, repositories=REPOS))

    def test_authority_and_evidence_cannot_escape_the_source_contract(self):
        self.write_story()
        for authority in ("file:auto-manual:../history.md", "file:hello-docs:history.md",
                          "file:auto-manual:/history.md", [self.domain["authority"]]):
            view = evolution.evolution_view(root=self.root, domain={**self.domain, "authority": authority},
                                            repositories=REPOS)
            self.assertTrue(view["problems"])
        for ref in ("url:javascript:alert(1)", "pr:unknown#4", "file:auto-manual:../secret",
                    "file:auto-manual:https://example.test/file", "file:auto-manual:x#fragment"):
            self.data = copy.deepcopy(DATA)
            self.data["stages"][0]["evidence"] = [ref]
            self.write_story()
            self.assertTrue(self.view()["problems"])

    def test_chapters_place_every_stage_once_and_bars_share_one_month_scale(self):
        view = evolution.evolution_view(root=ROOT, domain=DOMAIN, repositories=REPOS)
        placed = [stage["id"] for chapter in view["chapters"] for stage in chapter["stages"]]
        self.assertEqual(sorted(placed), sorted(stage["id"] for stage in view["stages"]))
        kernel = next(stage for stage in view["stages"] if stage["id"] == "kernel")
        targets = next(stage for stage in view["stages"] if stage["id"] == "targets")
        month = view["timeline"]["ticks"][1]["left"] - view["timeline"]["ticks"][0]["left"]
        self.assertEqual(kernel["bar"]["left"], 0)
        self.assertAlmostEqual(kernel["bar"]["width"], 2 * month, places=2)
        self.assertAlmostEqual(targets["bar"]["left"], month, places=2)
        self.assertFalse(kernel["bar"]["open"])
        self.assertTrue(next(s for s in view["stages"] if s["id"] == "production")["bar"]["open"])
        self.assertNotIn("bar", next(s for s in view["stages"] if s["id"] == "review_experience"))
        self.assertLess(kernel["bar"]["left"], view["timeline"]["today"])

    def test_bad_chapters_spans_and_now_rows_fall_back(self):
        for mutate in (lambda d: d["chapters"][0]["stages"].append("missing"),
                       lambda d: d["chapters"][0]["stages"].pop(),
                       lambda d: d["chapters"].append({"title": "重复", "question": "?", "stages": ["kernel"]}),
                       lambda d: d["stages"][0].update(start="2026-13"),
                       lambda d: d["stages"][0].update(start="2026-05", end="2026-02"),
                       lambda d: d["now"][0].update(status="done")):
            with self.subTest(mutate=mutate):
                self.data = copy.deepcopy(DATA)
                mutate(self.data)
                self.write_story()
                self.assertTrue(self.view()["problems"])
                self.assertEqual(self.view()["stages"], [])

    def test_story_without_chapters_or_spans_keeps_a_flat_timeline(self):
        for key in ("chapters", "now"):
            del self.data[key]
        for row in self.data["stages"] + self.data["crosscutting"]:
            row.pop("start", None)
            row.pop("end", None)
        self.write_story()
        view = self.view()
        self.assertEqual((view["problems"], view["chapters"], view["now"], view["timeline"]), ([], [], [], None))

    def test_context_escaping_disclosure_and_missing_source_panel(self):
        payload = '<img src=x onerror="alert(1)">'
        self.data["stages"][0]["summary"] = payload
        self.data["crosscutting"][0]["detail"] = payload
        self.data["architecture"]["agent"][1]["summary"] = payload
        self.write_story()
        contract = workspace.load_contract(workspace.DEFAULT_CONTRACT)
        registry = {**REGISTRY, "evolution": self.domain}
        context = workspace.build_context(contract, root=self.root, ledger=None, facts=None,
                                          today=dt.date(2026, 10, 4), registry=registry, assets=ASSETS)
        context.update(pathto=lambda path, *args: path, has_share=False, deliverables_entry=False,
                       workspace_revision={"revision": "", "short_revision": "preview", "built_at": ""})
        template = Environment(loader=FileSystemLoader(ASSETS)).get_template("system_workspace.html")
        page = template.render(**context)
        self.assertIn('id="tab-evolution"', page)
        self.assertIn('id="tab-architecture"', page)
        self.assertIn('class="access-node is-planned" id="architecture-agent_mcp"', page)
        self.assertIn("Human Approval · 人工批准", page)
        self.assertIn("当前路径：正式发布 Web", page)
        self.assertIn("现在在仓库里已经能做什么", page)
        self.assertIn("AI 文件页码自动修正", page)
        self.assertIn("现有 hooks：什么时候自动检查", page)
        architecture_panel = page.split('id="tab-architecture"', 1)[1].split('id="tab-evolution"', 1)[0]
        self.assertIn("多维表 · 业务数据层", architecture_panel)
        self.assertIn("数据校验与快照", architecture_panel)
        self.assertIn("同步与映射", architecture_panel)
        self.assertIn("Content Authority → Assembly → Renderers → Publish", architecture_panel)
        self.assertNotIn("内容与能力平台", architecture_panel)
        self.assertNotIn("读到内容以后", architecture_panel)
        self.assertNotIn("产品知识 · 阅读与理解", architecture_panel)
        self.assertEqual(page.count('class="sw-evolution-details"'), 13)
        self.assertIn('class="sw-crosscutting" id="evolution-engineering"', page)
        chapters = page.split('<section class="evo-chapter"', 1)[1].split('<aside class="sw-crosscutting"', 1)[0]
        self.assertNotIn('id="evolution-engineering"', chapters)
        self.assertEqual(page.count('class="evo-chapter"'), len(DATA["chapters"]))
        self.assertEqual(page.count('class="evo-row is-'), 13)
        self.assertEqual(page.count('class="evo-bar'), 8)
        self.assertEqual(page.count('class="evo-plan"'), 4)
        progress_panel = page.split('id="tab-progress"', 1)[1].split('id="tab-corpus"', 1)[0]
        self.assertIn('aria-label="当前工作"', progress_panel)
        self.assertNotIn('class="evo-now"', page)
        self.assertEqual(page.count('class="sw-timeline-row '), 12)
        self.assertNotIn(payload, page)
        self.assertIn("&lt;img", page)
        self.assertIn("后半圈 · 未来建设方向", page)
        self.assertIn("System%20Evolution%20Strategy.md", page)
        (self.root / "history.md").unlink()
        context["evolution"] = self.view()
        page = template.render(**context)
        self.assertIn(self.domain["fallback"], page)
        self.assertNotIn('class="sw-timeline"', page)
        findings = workspace._evolution_findings(contract, self.root, registry)
        self.assertTrue(findings)
        self.assertTrue(all(f.severity == "error" for f in findings))

    def test_access_states_evidence_and_optional_compatibility(self):
        self.write_story()
        architecture = self.view()["architecture"]
        self.assertEqual(architecture["agent"][-1]["status"], "planned")
        self.assertEqual(architecture["enterprise"][-1]["status"], "planned")
        self.data["architecture"]["agent"].reverse()
        self.data["architecture"]["enterprise"].reverse()
        self.write_story()
        diagram = self.view()["architecture"]["diagram"]
        self.assertEqual(diagram["agent_mcp"]["status"], "planned")
        self.assertEqual(diagram["agent_existing"]["status"], "recorded")
        self.assertEqual(diagram["enterprise_systems"]["status"], "planned")
        self.assertEqual(diagram["enterprise_tables"]["status"], "recorded")
        self.assertEqual(diagram["data_snapshot"]["status"], "recorded")
        self.assertEqual(diagram["document_production"]["status"], "ongoing")
        for group in ("human", "agent", "enterprise", "core", "surfaces", "capabilities", "hooks"):
            for row in DATA["architecture"][group]:
                for ref in row["evidence"]:
                    self.assertTrue((ROOT / ref.split(":", 2)[2]).exists(), ref)
        for stage in self.view()["stages"]:
            if stage["status"] == "planned":
                self.assertNotIn("start", stage)
                self.assertNotIn("end", stage)
        del self.data["architecture"]
        self.write_story()
        self.assertIsNone(self.view()["architecture"])
        self.assertEqual(self.view()["problems"], [])

    def test_capability_evidence_names_real_skills_and_configured_hooks(self):
        skills = {s["id"] for s in skill_facts(ROOT)}
        hooks = {h["script"] for h in hook_facts(ROOT) if h["exists"]}
        for row in DATA["architecture"]["capabilities"]:
            skill_refs = [ref.split(":", 2)[2] for ref in row["evidence"] if ref.endswith("/SKILL.md")]
            self.assertTrue(skill_refs, row["id"])
            for ref in skill_refs:
                self.assertIn(Path(ref).parent.name, skills)
        for row in DATA["architecture"]["hooks"]:
            self.assertTrue(any(ref.split(":", 2)[2] in hooks for ref in row["evidence"]))

    def test_malformed_access_view_falls_back_instead_of_claiming_capabilities(self):
        for mutate in (lambda a: a.update(agent=[]), lambda a: a["agent"].pop(),
                       lambda a: a.update(enterprise=[r for r in a["enterprise"] if r["id"] != "data_snapshot"]),
                       lambda a: a.update(core="wrong"),
                       lambda a: a["agent"][0].update(status="launched"),
                       lambda a: a["agent"][1].update(id=a["human"][0]["id"]),
                       lambda a: a["agent"][1].update(id="bad-id"),
                       lambda a: a["agent"][1].update(evidence=[]),
                       lambda a: a["agent"][1].update(evidence=["file:auto-manual:../secret"]),
                       lambda a: a.update(artwork_flow=["Apply"]),
                       lambda a: a.update(adapter_note="")):
            with self.subTest(mutate=mutate):
                self.data = copy.deepcopy(DATA)
                mutate(self.data["architecture"])
                self.write_story()
                view = self.view()
                self.assertTrue(view["problems"])
                self.assertNotIn("architecture", view)


if __name__ == "__main__":
    unittest.main()
