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
        self.assertEqual(len(view["stages"]), 9)
        self.assertEqual([s["status"] for s in view["stages"]],
                         ["recorded"] * 3 + ["in_progress", "ongoing", "recorded", "in_progress", "ongoing", "planned"])
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

    def test_context_escaping_disclosure_and_missing_source_panel(self):
        payload = '<img src=x onerror="alert(1)">'
        self.data["stages"][0]["summary"] = payload
        self.data["crosscutting"][0]["detail"] = payload
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
        self.assertEqual(page.count('class="sw-evolution-details"'), 10)
        self.assertIn('class="sw-crosscutting" id="evolution-engineering"', page)
        timeline = page.split('<ol class="sw-timeline"', 1)[1].split('</aside>', 1)[0]
        self.assertNotIn('id="evolution-engineering"', timeline)
        self.assertEqual(page.count('class="sw-timeline-row '), 9)
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


if __name__ == "__main__":
    unittest.main()
