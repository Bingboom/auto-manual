"""Research presentation keeps provenance, uncertainty and safe routes visible."""
from copy import deepcopy
from pathlib import Path
import unittest

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd.product_research import TEMPLATE, research_page_context

ASSETS = Path(__file__).resolve().parents[1] / "tools" / "rtd_portal_assets"
ROUTE = "JE-TEST/EU/en/md/manual_je_test.html"


def snapshots():
    evidence = {"source_type": "published_manual", "path": "frozen/manual.md", "url": ROUTE,
                "sha256": "manual-v1", "locator": "Specifications / Capacity", "quote": "Capacity 512 Wh"}
    product = {
        "id": "JE-TEST:EU:en:1", "model": "JE-TEST", "name": "Test power", "region": "EU",
        "language": "en", "version": "1",
        "source": {"route": "JE-TEST/EU/en/md", "manual": "manual_je_test.md", "url": ROUTE,
                   "sha256": "manual-v1", "built_at": "2026-10-20", "git_ref": "revision-1",
                   "language_scope": "single"},
        "category": {"state": "known", "value": "homebackup", "source_type": "curated_configuration"},
        "specifications": {
            "capacity_wh": {"state": "known", "value": 512, "unit": "Wh", "source_type": "published_manual"},
            "weight_kg": {"state": "unknown", "value": None, "source_type": "published_manual",
                          "reason": "重量未见于本变体手册。"},
        },
        "capabilities": {"UPS功能": {"state": "known", "value": False, "source_type": "capability_registry"}},
        "unknowns": ["当地接入许可未知。"],
    }
    event = {
        "id": "test-policy", "title": "政策变化研究", "kind": "policy", "market": "NL",
        "catalog_markets": ["EU"], "status": "verified", "occurred_on": "2027-01-01",
        "reviewed_on": "2026-10-20（核对）", "research_question": "哪些产品值得进一步研究？",
        "summary": "政策发生变化。", "boundary": "尚未核实当地产品适用性。",
        "sources": [{"kind": "official", "title": "官方资料", "url": "https://example.org/policy",
                     "checked_on": "2026-10-20", "note": "已核对政策原文。"}],
        "revision": 2, "content_sha256": "event-v2", "source_kind": "market_policy",
        "review": {"status": "pending", "decision": None}, "hypotheses": ["可能值得继续调查。"],
        "unknowns": ["连接条件未知。"],
        "history": [{"event_id": "test-policy", "revision": 1, "recorded_on": "2026-10-20",
                     "summary": "首次研究记录。", "reason": "新增研究问题。",
                     "evidence_refs": ["https://example.org/previous"], "review_status": "pending",
                     "content_sha256": "event-v1"}],
    }
    association = {
        "event_id": event["id"], "product_id": product["id"], "model": product["model"],
        "name": product["name"], "market": "EU", "language": "en", "version": "1",
        "status": "candidate",
        "reasons": [{"dimension": "market", "state": "match", "source_type": "rule_inference",
                     "message": "欧规发布资料属于本次研究目录范围。"}],
        "evidence": [evidence], "hypotheses": ["可进入场景研究。"], "unknowns": ["能力需复核。"],
    }
    return (
        {"schema_version": "product-knowledge/v1", "content_sha256": "knowledge-v1", "products": [product]},
        {"schema_version": "product-intelligence/v1", "snapshot_id": "research-v1",
         "knowledge_snapshot_id": "knowledge-v1", "events": [event], "associations": [association],
         "history": deepcopy(event["history"])},
    )


def render(knowledge, research):
    context = research_page_context(knowledge, research)
    # Match Sphinx's templates: explicit escaping must work even without autoescape.
    environment = Environment(loader=FileSystemLoader(str(ASSETS)), autoescape=False)
    html = environment.get_template(TEMPLATE).render(
        **context, site_nav={"research": True},
        pathto=lambda path, resource=False: "../../" + path + ("" if resource else ".html"),
    )
    return BeautifulSoup(html, "html.parser")


class ProductResearchTests(unittest.TestCase):
    def test_snapshot_binding_and_schema_are_required(self):
        knowledge, research = snapshots()
        for source, key, value in ((knowledge, "schema_version", "product-knowledge/v2"),
                                   (research, "schema_version", "product-intelligence/v2"),
                                   (research, "knowledge_snapshot_id", "stale-knowledge")):
            with self.subTest(key=key):
                previous = source[key]
                source[key] = value
                with self.assertRaises(ValueError):
                    research_page_context(knowledge, research)
                source[key] = previous

    def test_render_separates_sources_and_keeps_false_distinct_from_unknown(self):
        knowledge, research = snapshots()
        page = render(knowledge, research)
        text = page.get_text()
        for label in ("已发布说明书", "人工配置／分类", "能力登记表", "规则推导", "候选关联",
                      "事件要点已核实", "待人工复核", "研究假设 · 尚未证实"):
            self.assertIn(label, text)
        facts = {row.dt.get_text(): row.dd.get_text() for row in page.select(".fact-list>div")}
        self.assertIn("512 Wh", facts["电池容量"])
        self.assertIn("否", facts["UPS功能"])
        self.assertNotIn("未知", facts["UPS功能"])
        self.assertIn("未知", facts["重量"])
        self.assertIn("重量未见于本变体手册", facts["重量"])
        self.assertEqual(page.select_one(".human-review p").get_text(), "尚未记录人工判断。")
        self.assertEqual(page.select_one(".research-product a")["href"], "../../" + ROUTE)

    def test_variant_identity_does_not_collapse_same_model_across_markets(self):
        knowledge, research = snapshots()
        second = deepcopy(knowledge["products"][0])
        second.update(id="JE-TEST:US:en:2", region="US", version="2")
        second["source"]["url"] = "JE-TEST/US/en/md/manual_je_test.html"
        knowledge["products"].append(second)
        other = deepcopy(research["associations"][0])
        other.update(product_id=second["id"], status="excluded")
        research["associations"].append(other)
        event = research_page_context(knowledge, research)["research_events"][0]
        self.assertEqual(event["candidates"][0]["market"], "EU")
        self.assertEqual(event["excluded_products"][0]["market"], "US")
        self.assertEqual(event["excluded_products"][0]["version"], "2")
        self.assertIn("/US/", event["excluded_products"][0]["page"])

    def test_unknown_and_excluded_are_collapsed_and_no_match_is_explained(self):
        knowledge, research = snapshots()
        for status in ("unknown", "excluded"):
            row = deepcopy(research["associations"][0])
            row["status"] = status
            row["reasons"][0].update(state="no_match" if status == "excluded" else "unknown")
            research["associations"].append(row)
        page = render(knowledge, research)
        for css in (".unknown-products", ".excluded-products"):
            group = page.select_one(css)
            self.assertEqual(group.name, "details")
            self.assertNotIn("open", group.attrs)
            self.assertIsNotNone(group.select_one(".research-product"))
        self.assertIn("不符合", page.select_one(".excluded-products").get_text())
        self.assertEqual(len(page.select(".candidate-section .research-product")), 1)

    def test_only_catalog_routes_become_product_evidence_links(self):
        invalid = ("javascript:alert(1)", "//evil.example/a.html", "../escape.html",
                   "/absolute.html", "missing.html", "https://evil.example/manual.html",
                   "JE-TEST/%2e%2e/secret.html", "//[bad", "JE-TEST\\EU\\manual.html")
        for url in invalid:
            with self.subTest(url=url):
                knowledge, research = snapshots()
                research["associations"][0]["evidence"][0]["url"] = url
                page = render(knowledge, research)
                self.assertIsNone(page.select_one(".evidence-list a"))
                self.assertIn("未提供可打开的发布页链接", page.select_one(".evidence-list").get_text())
        knowledge, research = snapshots()
        knowledge["products"][0]["source"]["url"] = "../escape.html"
        research["associations"][0]["evidence"][0]["url"] = "../escape.html"
        page = render(knowledge, research)
        self.assertIsNone(page.select_one(".product-facts a"))
        self.assertIsNone(page.select_one(".evidence-list a"))

    def test_unsafe_external_sources_and_history_are_plain_text(self):
        urls = ("javascript:alert(1)", "http://example.org", "https://u:p@example.org",
                "https://example.org\\@evil.org", "https://example.org/\nunsafe", "https://[bad")
        for url in urls:
            with self.subTest(url=url):
                knowledge, research = snapshots()
                research["events"][0]["sources"][0]["url"] = url
                research["events"][0]["history"][0]["evidence_refs"] = [url]
                page = render(knowledge, research)
                self.assertIsNone(page.select_one(".event-sources a"))
                self.assertIsNone(page.select_one(".history-list a"))
                self.assertIn("暂无安全可用", page.select_one(".event-sources").get_text())

    def test_untrusted_text_is_escaped_in_all_major_surfaces(self):
        knowledge, research = snapshots()
        attack = '<img src=x onerror="alert(1)"><script>alert(1)</script>'
        knowledge["products"][0]["name"] = attack
        knowledge["products"][0]["specifications"]["capacity_wh"]["value"] = attack
        event = research["events"][0]
        for field in ("title", "summary", "research_question", "boundary"):
            event[field] = attack
        event["sources"][0]["title"] = attack
        event["history"][0]["summary"] = attack
        event["review"]["decision"] = attack
        research["associations"][0]["reasons"][0]["message"] = attack
        research["associations"][0]["evidence"][0]["quote"] = attack
        research["associations"][0]["hypotheses"] = [attack]
        page = render(knowledge, research)
        self.assertIsNone(page.select_one("img"))
        self.assertFalse(any(script.get_text() == "alert(1)" for script in page.select("script")))
        self.assertIn(attack, page.get_text())
        self.assertTrue(all(not any(key.startswith("on") for key in node.attrs) for node in page.select("*")))

    def test_history_remains_bound_to_its_recorded_revision(self):
        knowledge, research = snapshots()
        old = deepcopy((knowledge, research))
        context = research_page_context(knowledge, research)
        page = render(knowledge, research)
        self.assertEqual((knowledge, research), old)
        self.assertIn("event-v1", page.select_one(".history-list").get_text())
        self.assertIn("event-v2", page.select_one(".research-history .snapshot-fields").get_text())
        context["research_events"][0]["hypotheses"].append("presentation edit")
        self.assertEqual((knowledge, research), old)
        self.assertIn("历史判断不会随本次计算改写", page.get_text())

    def test_missing_products_sources_and_evidence_have_readable_fallbacks(self):
        knowledge, research = snapshots()
        knowledge["products"] = []
        knowledge["warnings"] = ["发布清单尚未提供。"]
        research["associations"][0]["evidence"] = []
        research["events"][0].update(status="missing", sources=[], history=[])
        page = render(knowledge, research)
        text = page.get_text()
        for message in ("当前没有可用的冻结产品发布输入", "发布清单尚未提供", "来源资料缺失",
                        "尚未提供来源", "尚无可定位的产品证据", "当前产品知识快照没有该产品变体",
                        "尚无已记录的研究修订"):
            self.assertIn(message, text)
        self.assertIsNone(page.select_one(".product-facts a"))

    def test_empty_state_no_script_and_downloads_are_available(self):
        knowledge, research = snapshots()
        populated = render(knowledge, research)
        self.assertIn("全部案例、证据和修订记录仍可直接阅读", populated.select_one("noscript").get_text())
        self.assertIsNotNone(populated.select_one('#research-filters[hidden]'))
        self.assertEqual(len(populated.select(".research-downloads a[download]")), 2)
        self.assertEqual(populated.select_one('meta[name="robots"]')["content"], "noindex,nofollow")
        research.update(events=[], associations=[], history=[])
        page = render(knowledge, research)
        self.assertIn("暂未录入研究案例", page.get_text())
        self.assertIsNone(page.select_one("#research-filters"))

    def test_invalid_event_ids_and_unbound_associations_fail_closed(self):
        for key in ("../escape", '"><script>', "space id"):
            knowledge, research = snapshots()
            research["events"][0]["id"] = key
            with self.assertRaisesRegex(ValueError, "safe identifiers"):
                research_page_context(knowledge, research)
        knowledge, research = snapshots()
        research["associations"][0]["event_id"] = "not-in-current-snapshot"
        with self.assertRaisesRegex(ValueError, "unknown event"):
            research_page_context(knowledge, research)


if __name__ == "__main__":
    unittest.main()
