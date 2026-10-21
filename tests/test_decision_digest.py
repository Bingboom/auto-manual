"""The decision digest pushes events, never product conclusions, and stays literal text."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.rtd.decision_digest import SCHEMA_VERSION, decision_digest, safe_external_url
from tools.rtd.intelligence_events import CONTENT_DIR, EVENTS_FILE, load_events

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "external_intel" / "events.json"
PAGE = "research/product-intelligence"


class DecisionDigestTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / CONTENT_DIR).mkdir()
        self.data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.nl, self.us = self.data["events"]

    def digest(self, **options):
        (self.root / CONTENT_DIR / EVENTS_FILE).write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        return decision_digest(load_events(self.root), page=PAGE, **options)

    def item(self, digest, key="us-outage-resilience-research"):
        return next(item for item in digest["items"] if item["event_id"] == key)

    def test_items_carry_the_decision_and_no_product_data(self):
        digest = self.digest()
        self.assertEqual(digest["schema_version"], SCHEMA_VERSION)
        self.assertEqual(digest["counts"], {"events": 2, "pending": 2, "reviewed": 0})
        item = self.item(digest)
        self.assertEqual(item["decision"]["question"], "是否按州、负载和停电时长分组，启动美国家庭备电需求验证？")
        self.assertEqual(item["verification"], "verified")
        self.assertEqual(item["page"], f"{PAGE}.html#event-us-outage-resilience-research")
        self.assertIsNone(item["url"])
        for text in (json.dumps(digest, ensure_ascii=False), digest["text"]):
            for product_term in ("product_lens", "required_capabilities", "UPS功能", "catalog_markets"):
                self.assertNotIn(product_term, text)

    def test_pending_decisions_lead_by_due_date_and_decided_items_follow(self):
        self.nl["revisions"][-1]["decide_by"] = "2026-12-01"
        self.us["revisions"][-1]["review"] = {"status": "reviewed", "decision": "先按州收集停电数据。",
                                              "reviewed_by": "Fixture reviewer", "reviewed_on": "2026-10-22"}
        digest = self.digest()
        self.assertEqual([item["event_id"] for item in digest["items"]],
                         ["nl-self-consumption-research", "us-outage-resilience-research"])
        self.assertEqual(digest["counts"], {"events": 2, "pending": 1, "reviewed": 1})
        text = digest["text"]
        self.assertLess(text.index("## 待决策（1）"), text.index("荷兰净计量"))
        self.assertLess(text.index("## 已有人工判断（1）"), text.index("美国 2024 飓风季"))
        self.assertIn("截止：2026-12-01", text)
        self.assertIn("人工判断：先按州收集停电数据。（Fixture reviewer，2026-10-22）", text)

    def test_unassigned_owner_and_missing_due_date_are_explicit(self):
        message = self.item(self.digest())["message"]
        self.assertIn("决策人：待指派 · 截止：未设定", message)
        self.us["revisions"][-1].update(decision_owner="市场研究负责人", decide_by="2026-11-15")
        self.assertIn("决策人：市场研究负责人 · 截止：2026-11-15", self.item(self.digest())["message"])

    def test_absolute_links_use_the_site_base_url(self):
        item = self.item(self.digest(base_url="https://docs.example.org/en/latest"))
        self.assertEqual(item["url"], f"https://docs.example.org/en/latest/{PAGE}.html#event-us-outage-resilience-research")
        self.assertIn(f"详情：{item['url']}", item["message"])

    def test_intake_text_cannot_inject_lines_links_or_markup(self):
        self.us["title"] = "Title\n# Heading [link](javascript:alert(1)) <at id=all></at> *bold* `code`"
        self.us["revisions"][-1]["summary"] = "line one\n\n## injected"
        message = self.item(self.digest())["message"]
        first = message.splitlines()[0]
        self.assertTrue(first.startswith("### Title # Heading"))
        self.assertIn(r"\[link\](javascript:alert(1))", first)
        self.assertIn(r"\<at id=all\>\</at\>", first)
        self.assertIn(r"\*bold\* \`code\`", first)
        self.assertNotIn("\n## injected", message)
        self.assertIn("外部发生了什么：line one ## injected", message)

    def test_unsafe_source_links_are_omitted_not_forwarded(self):
        self.us["revisions"][-1]["sources"][0]["url"] = "https://example.org/<script>"
        item = self.item(self.digest())
        self.assertIsNone(item["sources"][0]["url"])
        self.assertIn("（无安全可用的链接）", item["message"])
        for url in ("https://example.org/a b", "http://example.org", "https://u:p@example.org", 'https://e.org/"x'):
            with self.subTest(url=url):
                self.assertEqual(safe_external_url(url), "")
        self.assertEqual(safe_external_url("https://www.eia.gov/todayinenergy/detail.php?id=66744"),
                         "https://www.eia.gov/todayinenergy/detail.php?id=66744")

    def test_empty_intake_still_produces_a_digest(self):
        digest = decision_digest(load_events(None), page=PAGE)
        self.assertEqual((digest["items"], digest["counts"]["events"]), ([], 0))
        self.assertIn("暂未录入外部事件。", digest["text"])

    def test_digest_is_deterministic_and_needs_the_events_schema(self):
        self.assertEqual(self.digest(), self.digest())
        with self.assertRaisesRegex(ValueError, "external-intel/v1"):
            decision_digest({"schema_version": "product-intelligence/v1", "events": []}, page=PAGE)


if __name__ == "__main__":
    unittest.main()
