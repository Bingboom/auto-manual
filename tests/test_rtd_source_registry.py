from __future__ import annotations

import copy
import datetime as dt
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from tools import rtd_portal
from tools import rtd_source_registry as reg
from tools.utils.path_utils import repo_root

REPO = repo_root()
SHIPPED = yaml.safe_load((rtd_portal.ASSETS / reg.REGISTRY_NAME).read_text(encoding="utf-8"))
TODAY = dt.date(2026, 9, 25)


def link(ref: str) -> dict:
    return {"label": ref.rsplit(":", 1)[-1], "href": f"https://example.test/{ref}", "title": ref}


class RegistryRulesTests(unittest.TestCase):
    def test_shipped_registry_is_sound_and_covers_every_page_domain(self):
        registry, problems = reg.load_registry(rtd_portal.ASSETS)
        self.assertEqual(problems, [])
        self.assertEqual(set(reg.PAGE_DOMAINS) - set(registry), set())

    def test_shipped_file_authorities_exist_in_this_repo(self):
        registry, _ = reg.load_registry(rtd_portal.ASSETS)
        missing = [(d, path) for d, repo, path in reg.file_refs(registry)
                   if repo == "auto-manual" and not (REPO / path).exists()]
        self.assertEqual(missing, [])

    def test_shipped_snapshots_sit_next_to_the_registry(self):
        registry, _ = reg.load_registry(rtd_portal.ASSETS)
        for domain in registry.values():
            if domain["read"] == "snapshot":
                self.assertIsNotNone(reg.snapshot_date(rtd_portal.ASSETS, domain), domain["id"])

    def test_each_rule_is_enforced(self):
        def domain_of(data, domain_id):
            return next(d for d in data["domains"] if d["id"] == domain_id)

        cases = {
            "schema is": lambda d: d.update(schema="other/v1"),
            "domains must be a non-empty list": lambda d: d.update(domains=[]),
            "duplicate id": lambda d: d["domains"].append(copy.deepcopy(d["domains"][0])),
            "id must be lower_snake_case": lambda d: domain_of(d, "focus").update(id="Focus"),
            "needs fallback": lambda d: domain_of(d, "ledger").update(fallback=""),
            "read must be one of": lambda d: domain_of(d, "ledger").update(read="live"),
            "snapshot must name a .json file": lambda d: domain_of(d, "corpus").update(snapshot="../corpus.json"),
            "a snapshot needs its refresh command": lambda d: domain_of(d, "corpus").pop("refresh"),
            "a snapshot needs stale_after_days": lambda d: domain_of(d, "corpus").pop("stale_after_days"),
            "stale_after_days must be a positive integer": lambda d: domain_of(d, "capabilities").update(stale_after_days=0),
            "only snapshot domains name": lambda d: domain_of(d, "ledger").update(snapshot="x.json"),
            "authority must be text": lambda d: domain_of(d, "tooling").update(authority=["", "file:auto-manual:x"]),
            "not registered": lambda d: d.update(domains=[x for x in d["domains"] if x["id"] != "skeletons"]),
        }
        for fragment, mutate in cases.items():
            with self.subTest(fragment):
                data = copy.deepcopy(SHIPPED)
                mutate(data)
                problems = reg.registry_problems(data)
                self.assertTrue(any(fragment in p for p in problems), problems)
        # A bool is not a day count, even though Python treats True as 1.
        data = copy.deepcopy(SHIPPED)
        next(d for d in data["domains"] if d["id"] == "capabilities").update(stale_after_days=True)
        self.assertTrue(reg.registry_problems(data))
        self.assertEqual(reg.registry_problems([]), [f"{reg.REGISTRY_NAME} is not a mapping"])

    def test_load_reports_an_unreadable_file(self):
        with TemporaryDirectory() as temp:
            registry, problems = reg.load_registry(Path(temp))
            self.assertIsNone(registry)
            self.assertIn("cannot read", problems[0])


class SourcesViewTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.assets = Path(temp.name)
        self.registry = {d["id"]: d for d in copy.deepcopy(SHIPPED)["domains"]}
        for domain in self.registry.values():
            if domain["read"] == "snapshot":
                (self.assets / domain["snapshot"]).write_text(json.dumps({"exported_at": "2026-09-25"}),
                                                              encoding="utf-8")

    def rows(self, today=TODAY):
        return {row["id"]: row for row in reg.sources_view(self.registry, assets=self.assets, today=today, link=link)}

    def test_rows_follow_the_registry(self):
        rows = self.rows()
        self.assertEqual(list(rows), [d["id"] for d in SHIPPED["domains"]])
        self.assertEqual((rows["publications"]["how"], rows["publications"]["freshness"]), ("构建时读", "随构建"))
        self.assertEqual(rows["capabilities"]["freshness"], "30 天复核")
        corpus = rows["corpus"]
        self.assertEqual((corpus["how"], corpus["freshness"], corpus["stale"]),
                         ("读快照 system_workspace_corpus.json", "45 天 · 快照 2026-09-25", []))
        self.assertIn("corpus-export", corpus["refresh"])
        # file: authorities become links; anything else stays plain text.
        self.assertTrue(rows["ledger"]["sources"][0]["href"].startswith("https://example.test/file:auto-manual:"))
        self.assertEqual(rows["focus"]["sources"][0], {"label": "操作者决定", "href": "", "title": "操作者决定"})
        self.assertEqual([s["label"] for s in rows["tooling"]["sources"]],
                         [".agents/skills", ".claude/skills", ".claude/settings.json", ".githooks/pre-push"])

    def test_old_or_unreadable_snapshots(self):
        old = self.rows(today=TODAY + dt.timedelta(days=46))
        self.assertEqual(old["corpus"]["stale"], ["语料规模快照已超过 45 天（导出于 2026-09-25）"])
        (self.assets / "deliverables_snapshot.json").write_text("{not json", encoding="utf-8")
        row = self.rows()["deliverables_feishu"]
        self.assertEqual((row["freshness"], row["stale"]), ("45 天 · 飞书快照当前不可读", []))


if __name__ == "__main__":
    unittest.main()
