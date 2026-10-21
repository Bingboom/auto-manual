"""The research page leads with events; the product lens stays an escaped, optional appendix."""
from copy import deepcopy
from pathlib import Path
import unittest

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd.product_research import TEMPLATE, research_page_context

ASSETS = Path(__file__).resolve().parents[1] / "tools" / "rtd_portal_assets"
ROUTE = "JE-TEST/EU/en/md/manual_je_test.html"
LENS = {"catalog_markets": ["EU"], "market_mapping_note": "NL → EU 只是研究范围映射。",
        "rule": {"categories": ["homebackup"], "required_capabilities": ["UPS功能"],
                 "required_facts": ["capacity_wh"]}}


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
            "capacity_wh": {"state": "known", "value": 1024, "unit": "Wh", "source_type": "published_manual"},
            "weight_kg": {"state": "unknown", "value": None, "source_type": "published_manual",
                          "reason": "重量未见于本变体手册。"},
        },
        "capabilities": {"UPS功能": {"state": "known", "value": False, "source_type": "capability_registry"}},
        "unknowns": [{"field": "specifications.weight_kg", "reason": "重量未见于本变体手册。"},
                     {"field": "language", "reason": "Legacy publication does not verify a single-language edition"}],
    }
    event = {
        "id": "test-policy", "title": "政策变化", "kind": "policy", "market": "NL", "status": "verified",
        "occurred_on": "2027-01-01", "checked_on": "2026-10-20（核对）", "recorded_on": "2026-10-21",
        "decision": {"question": "是否启动当地接入条件核查？", "owner": None, "due_on": None},
        "summary": "政策发生变化。", "boundary": "尚未核实当地产品适用性。",
        "sources": [{"kind": "official", "title": "官方资料", "url": "https://example.org/policy",
                     "checked_on": "2026-10-20", "note": "已核对政策原文。"}],
        "revision": 2, "content_sha256": "event-v2", "source_kind": "market_policy",
        "review": {"status": "pending", "decision": None}, "hypotheses": ["可能值得继续调查。"],
        "unknowns": ["连接条件未知。"], "product_lens": deepcopy(LENS),
        "history": [{"event_id": "test-policy", "revision": 1, "recorded_on": "2026-10-20",
                     "summary": "首次决策问题。", "reason": "新增事件。",
                     "evidence_refs": ["https://example.org/previous"], "review_status": "pending",
                     "content_sha256": "event-v1"}],
    }
    association = {
        "event_id": event["id"], "product_id": product["id"], "model": product["model"],
        "name": product["name"], "market": "EU", "language": "en", "version": "1",
        "status": "candidate",
        "reasons": [{"dimension": "market", "state": "match", "source_type": "rule_inference",
                     "message": "欧规发布资料属于本次研究目录范围。"}],
        "evidence": [evidence], "unknowns": ["能力需复核。"],
    }
    intel = {"schema_version": "external-intel/v1", "snapshot_id": "events-v1", "events": [event],
             "history": deepcopy(event["history"])}
    knowledge = {"schema_version": "product-knowledge/v1", "content_sha256": "knowledge-v1", "products": [product]}
    lens = {"schema_version": "product-intelligence/v1", "snapshot_id": "lens-v1",
            "knowledge_snapshot_id": "knowledge-v1", "events_snapshot_id": "events-v1",
            "lenses": [{"event_id": event["id"], "status": "evaluated", "problems": []}],
            "associations": [association]}
    return intel, knowledge, lens


def context(intel, knowledge=None, lens=None, **options):
    return research_page_context(intel, lens=lens, knowledge=knowledge, **options)


def render(intel, knowledge=None, lens=None, **options):
    page_context = context(intel, knowledge, lens, **options)
    # Match Sphinx's templates: explicit escaping must work even without autoescape.
    environment = Environment(loader=FileSystemLoader(str(ASSETS)), autoescape=False)
    html = environment.get_template(TEMPLATE).render(
        **page_context, site_nav={"research": True},
        pathto=lambda path, resource=False: "../../" + path + ("" if resource else ".html"),
    )
    return BeautifulSoup(html, "html.parser")


class ProductResearchTests(unittest.TestCase):
    def test_lens_must_be_bound_to_both_snapshots(self):
        intel, knowledge, lens = snapshots()
        with self.assertRaises(ValueError):
            context({**intel, "schema_version": "product-intelligence/v1"})
        for source, key, value in ((lens, "schema_version", "product-intelligence/v2"),
                                   (lens, "knowledge_snapshot_id", "stale-knowledge"),
                                   (lens, "events_snapshot_id", "stale-events"),
                                   (knowledge, "schema_version", "product-knowledge/v2")):
            with self.subTest(key=key, value=value):
                previous = source[key]
                source[key] = value
                with self.assertRaises(ValueError):
                    context(intel, knowledge, lens)
                source[key] = previous
        with self.assertRaises(ValueError):
            context(intel, None, lens)

    def test_event_renders_decision_sources_and_review_without_products(self):
        intel, _knowledge, _lens = snapshots()
        del intel["events"][0]["product_lens"]
        page = render(intel)
        row = page.select_one(".research-event > details.event-entry > summary.event-row")
        self.assertNotIn("open", row.parent.attrs)
        self.assertEqual(row.select_one("h2").get_text(), "政策变化")
        for text in ("需要决策", "是否启动当地接入条件核查？", "决策人 待指派", "截止 未设定", "NL", "政策变化"):
            self.assertIn(text, " ".join(row.get_text(" ").split()))
        self.assertIn("政策发生变化。", page.select_one(".event-context").get_text())
        self.assertIsNotNone(page.select_one('.event-sources a[href="https://example.org/policy"]'))
        self.assertEqual(page.select_one(".human-review p").get_text(), "尚未记录人工判断。")
        appendix = page.select_one(".product-lens")
        self.assertEqual(appendix.name, "details")
        self.assertNotIn("open", appendix.attrs)
        self.assertIn("未配置产品视角", appendix.get_text())
        self.assertIsNone(page.select_one(".research-product"))

    def test_unavailable_lens_keeps_the_event_whole_and_says_why(self):
        intel, _knowledge, _lens = snapshots()
        page = render(intel, lens_problem="产品知识快照不可用：发布清单缺失。")
        self.assertIn("产品视角暂不可用", page.select_one(".product-lens summary").get_text())
        self.assertIn("发布清单缺失", page.select_one(".product-lens").get_text())
        self.assertIn("是否启动当地接入条件核查？", page.select_one(".event-row").get_text())
        self.assertEqual([a.get_text() for a in page.select(".research-downloads a")], [])

    def test_invalid_lens_lists_its_problems_and_no_products(self):
        intel, knowledge, lens = snapshots()
        lens["lenses"][0] = {"event_id": "test-policy", "status": "invalid",
                             "problems": ["规则引用的产品分类「home-backup」不在当前产品知识快照中。"]}
        lens["associations"] = []
        page = render(intel, knowledge, lens)
        self.assertIn("产品视角规则需修正", page.select_one(".product-lens summary").get_text())
        self.assertIn("「home-backup」", page.select_one(".lens-problems").get_text())
        self.assertIsNone(page.select_one(".research-product"))
        lens["associations"] = deepcopy(snapshots()[2]["associations"])
        with self.assertRaisesRegex(ValueError, "unknown event, lens or status"):
            context(intel, knowledge, lens)

    def test_candidate_card_separates_sources_and_keeps_false_distinct_from_unknown(self):
        page = render(*snapshots())
        text = page.select_one(".product-lens").get_text()
        for label in ("已发布说明书", "人工配置／分类", "能力登记表", "规则推导", "候选关联"):
            self.assertIn(label, text)
        facts = {row.dt.get_text(): row.dd.get_text() for row in page.select(".fact-list>div")}
        self.assertIn("1,024 Wh", facts["电池容量"])
        self.assertIn("否", facts["UPS功能"])
        self.assertNotIn("未知", facts["UPS功能"])
        self.assertIn("未知", facts["重量"])
        self.assertIn("重量未见于本变体手册", facts["重量"])
        self.assertEqual(page.select_one(".research-product a")["href"], "../../" + ROUTE)
        self.assertIn("NL → EU 只是研究范围映射。", text)

    def test_variant_identity_does_not_collapse_same_model_across_markets(self):
        intel, knowledge, lens = snapshots()
        second = deepcopy(knowledge["products"][0])
        second.update(id="JE-TEST:US:en:2", region="US", version="2")
        second["source"]["url"] = "JE-TEST/US/en/md/manual_je_test.html"
        knowledge["products"].append(second)
        other = deepcopy(lens["associations"][0])
        other.update(product_id=second["id"], status="excluded")
        other["reasons"][0].update(state="no_match", message="发布变体市场 US；研究目录范围 EU。")
        lens["associations"].append(other)
        view = context(intel, knowledge, lens)["research_events"][0]["lens"]
        self.assertEqual(view["candidates"][0]["market"], "EU")
        self.assertEqual((view["excluded_products"][0]["market"], view["excluded_products"][0]["version"]),
                         ("US", "2"))
        self.assertIn("/US/", view["excluded_products"][0]["page"])

    def test_unknown_and_excluded_are_compact_collapsed_rows_with_failing_conditions(self):
        intel, knowledge, lens = snapshots()
        for status in ("unknown", "excluded"):
            row = deepcopy(lens["associations"][0])
            row["status"] = status
            row["reasons"].append({"dimension": "capability", "state": "no_match" if status == "excluded" else "unknown",
                                   "source_type": "capability_registry", "message": f"{status} condition"})
            lens["associations"].append(row)
        page = render(intel, knowledge, lens)
        for css, state in ((".unknown-products", "待核实"), (".excluded-products", "不符合")):
            group = page.select_one(css)
            self.assertEqual(group.name, "details")
            self.assertNotIn("open", group.attrs)
            self.assertIsNone(group.select_one(".research-product"))
            cells = group.select(".lens-rows tbody td")
            self.assertIn(state, cells[1].get_text())
            # Only the failing or missing conditions are listed, not every matching reason.
            self.assertNotIn("欧规发布资料属于本次研究目录范围", cells[1].get_text())
        self.assertEqual(len(page.select(".candidate-section .research-product")), 1)

    def test_only_catalog_routes_become_product_evidence_links(self):
        invalid = ("javascript:alert(1)", "//evil.example/a.html", "../escape.html",
                   "/absolute.html", "missing.html", "https://evil.example/manual.html",
                   "JE-TEST/%2e%2e/secret.html", "//[bad", "JE-TEST\\EU\\manual.html")
        for url in invalid:
            with self.subTest(url=url):
                intel, knowledge, lens = snapshots()
                lens["associations"][0]["evidence"][0]["url"] = url
                page = render(intel, knowledge, lens)
                self.assertIsNone(page.select_one(".evidence-list a"))
                self.assertIn("未提供可打开的发布页链接", page.select_one(".evidence-list").get_text())
        intel, knowledge, lens = snapshots()
        knowledge["products"][0]["source"]["url"] = "../escape.html"
        lens["associations"][0]["evidence"][0]["url"] = "../escape.html"
        page = render(intel, knowledge, lens)
        self.assertIsNone(page.select_one(".product-facts a"))
        self.assertIsNone(page.select_one(".evidence-list a"))

    def test_unsafe_external_sources_and_history_are_plain_text(self):
        urls = ("javascript:alert(1)", "http://example.org", "https://u:p@example.org", "https://@example.org",
                "https://example.org\\@evil.org", "https://example.org/\nunsafe", "https://[bad")
        for url in urls:
            with self.subTest(url=url):
                intel, knowledge, lens = snapshots()
                intel["events"][0]["sources"][0]["url"] = url
                intel["events"][0]["history"][0]["evidence_refs"] = [url]
                page = render(intel, knowledge, lens)
                self.assertIsNone(page.select_one(".event-sources a"))
                self.assertIsNone(page.select_one(".history-list a"))
                self.assertIn("暂无安全可用", page.select_one(".event-sources").get_text())

    def test_untrusted_text_is_escaped_in_all_major_surfaces(self):
        intel, knowledge, lens = snapshots()
        attack = '<img src=x onerror="alert(1)"><script>alert(1)</script>'
        knowledge["products"][0]["name"] = attack
        knowledge["products"][0]["specifications"]["capacity_wh"]["value"] = attack
        event = intel["events"][0]
        for field in ("title", "summary", "boundary"):
            event[field] = attack
        event["decision"].update(question=attack, owner=attack)
        event["sources"][0]["title"] = attack
        event["history"][0]["summary"] = attack
        event["review"]["decision"] = attack
        event["product_lens"]["market_mapping_note"] = attack
        lens["associations"][0]["reasons"][0]["message"] = attack
        lens["associations"][0]["evidence"][0]["quote"] = attack
        page = render(intel, knowledge, lens)
        self.assertIsNone(page.select_one("img"))
        self.assertFalse(any(script.get_text() == "alert(1)" for script in page.select("script")))
        self.assertIn(attack, page.get_text())
        self.assertTrue(all(not any(key.startswith("on") for key in node.attrs) for node in page.select("*")))

    def test_event_anchors_cannot_collide_with_page_controls(self):
        intel, knowledge, lens = snapshots()
        for key in ("research-empty", "research-count"):
            with self.subTest(key=key):
                current = deepcopy((intel, knowledge, lens))
                current[0]["events"][0]["id"] = key
                current[2]["lenses"][0]["event_id"] = key
                current[2]["associations"][0]["event_id"] = key
                page = render(*current)
                self.assertEqual(page.select_one(".research-event")["id"], f"event-{key}")
                self.assertEqual(len(page.select(f"#{key}")), 1)
                self.assertNotEqual(page.select_one(f"#{key}").name, "article")

    def test_history_remains_bound_to_its_recorded_revision(self):
        intel, knowledge, lens = snapshots()
        old = deepcopy((intel, knowledge, lens))
        page_context = context(intel, knowledge, lens)
        page = render(intel, knowledge, lens)
        self.assertEqual((intel, knowledge, lens), old)
        self.assertIn("event-v1", page.select_one(".history-list").get_text())
        self.assertIn("event-v2", page.select_one(".research-history .snapshot-fields").get_text())
        page_context["research_events"][0]["hypotheses"].append("presentation edit")
        self.assertEqual((intel, knowledge, lens), old)
        self.assertIn("历史判断不会随本次构建改写", page.get_text())

    def test_structured_knowledge_gaps_and_association_prose_are_both_preserved(self):
        intel, knowledge, lens = snapshots()
        knowledge["products"][0]["unknowns"].extend([
            {"field": "capabilities.自发自用模式", "reason": "Missing registry value"},
            {"field": "specifications.weight_kg", "reason": "重量未见于本变体手册。"},
        ])
        view = context(intel, knowledge, lens)["research_events"][0]["lens"]["candidates"][0]
        self.assertEqual(view["unknowns"].count("重量：重量未见于本变体手册。"), 1)
        self.assertIn("能力需复核。", view["unknowns"])
        self.assertIn("自发自用模式：Missing registry value", view["unknowns"])
        page = render(intel, knowledge, lens)
        self.assertIn("语言范围：Legacy publication", page.select_one(".research-unknowns").get_text())
        self.assertNotIn("{'field':", page.get_text())

    def test_association_inference_and_rule_provenance_are_explicit(self):
        intel, knowledge, lens = snapshots()
        association = lens["associations"][0]
        association["source_type"] = "rule_inference"
        association["provenance"] = {
            "engine_version": "3", "rule_sha256": "rule-v2", "event_sha256": "event-v2",
            "product_sha256": "product-v1", "evidence_sha256": "evidence-v1",
            "rule_source": {"path": "external-intel/events.json", "locator": "events/test-policy/product_lens"},
        }
        page = render(intel, knowledge, lens)
        self.assertIn("规则推导", page.select_one(".product-status").get_text())
        basis = page.select_one(".association-basis").get_text()
        for value in ("rule-v2", "event-v2", "product-v1", "evidence-v1", "external-intel/events.json",
                      "events/test-policy/product_lens"):
            self.assertIn(value, basis)

    def test_current_and_historical_human_review_keep_their_own_attribution(self):
        intel, knowledge, lens = snapshots()
        event = intel["events"][0]
        event["review"] = {"status": "reviewed", "decision": "继续验证当地接入条件。",
                           "reviewed_by": "当前复核人", "reviewed_on": "2026-10-22"}
        event["history"][0].update(review_status="reviewed", decision="先补充资料。",
                                   reviewed_by="历史复核人", reviewed_on="2026-10-21")
        page = render(intel, knowledge, lens)
        current, previous = page.select_one(".human-review"), page.select_one(".history-list")
        for value in ("继续验证当地接入条件。", "当前复核人", "2026-10-22"):
            self.assertIn(value, current.get_text())
            self.assertNotIn(value, previous.get_text())
        for value in ("先补充资料。", "历史复核人", "2026-10-21"):
            self.assertIn(value, previous.get_text())
            self.assertNotIn(value, current.get_text())
        self.assertIn("2026-10-20（核对）", page.select_one(".event-dates").get_text())
        self.assertEqual(page.select_one(".research-event")["data-review"], "reviewed")

    def test_pending_review_does_not_render_reviewer_attribution(self):
        intel, knowledge, lens = snapshots()
        # Even a malformed stale reviewer field must not imply completed human review.
        intel["events"][0]["review"].update(reviewed_by="不可显示", reviewed_on="2026-10-22")
        intel["events"][0]["history"][0].update(reviewed_by="不可显示", reviewed_on="2026-10-21")
        page = render(intel, knowledge, lens)
        self.assertIsNone(page.select_one(".review-attribution"))
        self.assertNotIn("不可显示", page.get_text())
        self.assertIn("待人工判断", page.select_one(".human-review").get_text())

    def test_missing_sources_and_evidence_have_readable_fallbacks(self):
        intel, knowledge, lens = snapshots()
        knowledge["products"] = []
        knowledge["warnings"] = ["发布清单尚未提供。"]
        lens["associations"][0]["evidence"] = []
        intel["events"][0].update(status="missing", sources=[], history=[])
        page = render(intel, knowledge, lens)
        text = page.get_text()
        for message in ("发布清单尚未提供", "来源资料缺失", "尚未提供来源", "尚无可定位的产品证据",
                        "当前产品知识快照没有该产品变体", "尚无已记录的录入修订"):
            self.assertIn(message, text)
        self.assertIsNone(page.select_one(".product-facts a"))
        self.assertIn("产品关联附录", page.select_one(".research-footer .knowledge-gap").get_text())

    def test_metrics_count_events_and_decisions_not_products(self):
        intel, knowledge, lens = snapshots()
        unverified = deepcopy(intel["events"][0])
        unverified.update(id="second-event", status="unverified", review={
            "status": "reviewed", "decision": "暂缓。", "reviewed_by": "复核人", "reviewed_on": "2026-10-22"})
        del unverified["product_lens"]
        intel["events"].append(unverified)
        summary = context(intel, knowledge, lens)["research_summary"]
        self.assertEqual(summary, {"events": 2, "pending": 1, "reviewed": 1, "verified": 1})
        tiles = render(intel, knowledge, lens).select(".research-quick button")
        self.assertEqual([(tile.get("data-quick-field"), tile.get("data-quick-value"), tile.strong.get_text())
                          for tile in tiles],
                         [("all", None, "2"), ("review", "pending", "1"), ("review", "reviewed", "1"),
                          ("status", "verified", "1")])
        self.assertNotIn("候选", " ".join(tile.get_text() for tile in tiles))

    def test_empty_state_no_script_and_downloads_are_available(self):
        intel, knowledge, lens = snapshots()
        downloads = (("外部事件 JSON", "_static/external-intel.v1.json"),
                     ("决策摘要文本（Markdown）", "_static/external-intel-digest.v1.md"))
        populated = render(intel, knowledge, lens, downloads=downloads)
        self.assertIn("点开事件即可阅读全部来源、附录和修订记录", populated.select_one("noscript").get_text())
        self.assertIsNotNone(populated.select_one('#research-filters[hidden]'))
        self.assertIsNotNone(populated.select_one("#research-review"))
        links = populated.select(".research-downloads a[download]")
        self.assertEqual([link["href"] for link in links],
                         ["../../_static/external-intel.v1.json", "../../_static/external-intel-digest.v1.md"])
        self.assertEqual(populated.select_one('meta[name="robots"]')["content"], "noindex,nofollow")
        intel.update(events=[], history=[])
        page = render(intel)
        self.assertIn("暂未录入外部事件", page.get_text())
        self.assertIn("external-intel/events.json", page.get_text())
        self.assertIsNone(page.select_one("#research-filters"))

    def test_events_form_an_index_of_collapsed_rows_in_decision_order(self):
        intel, knowledge, lens = snapshots()
        first = intel["events"][0]
        decided, due, later = (deepcopy(first) for _ in range(3))
        decided.update(id="decided", title="已判断事件", recorded_on="2026-10-25", review={
            "status": "reviewed", "decision": "暂缓。", "reviewed_by": "复核人", "reviewed_on": "2026-10-25"})
        due.update(id="due-soon", title="有截止事件", decision={**first["decision"], "due_on": "2026-11-01"})
        later.update(id="recorded-later", title="新录入事件", recorded_on="2026-10-24")
        for event in (decided, due, later):
            del event["product_lens"]
        intel["events"] = [decided, first, later, due]
        page = render(intel, knowledge, lens)
        rows = page.select("#research-list > .research-event")
        self.assertEqual([row["id"] for row in rows],
                         ["event-due-soon", "event-recorded-later", "event-test-policy", "event-decided"])
        self.assertTrue(all(row.select_one(":scope > details.event-entry > summary.event-row h2") for row in rows))
        self.assertFalse(any("open" in row.details.attrs for row in rows))
        self.assertIn("截止 2026-11-01", " ".join(rows[0].summary.get_text(" ").split()))
        self.assertEqual([row["data-review"] for row in rows], ["pending", "pending", "pending", "reviewed"])
        # Details live under the row, not beside it.
        self.assertIsNotNone(rows[2].select_one("details.event-entry > .event-body .event-context"))

    def test_invalid_event_ids_and_unbound_associations_fail_closed(self):
        for key in ("../escape", '"><script>', "space id"):
            intel, knowledge, lens = snapshots()
            intel["events"][0]["id"] = key
            with self.assertRaisesRegex(ValueError, "safe identifiers"):
                context(intel)
        intel, knowledge, lens = snapshots()
        lens["associations"][0]["event_id"] = "not-in-current-snapshot"
        with self.assertRaisesRegex(ValueError, "unknown event"):
            context(intel, knowledge, lens)


if __name__ == "__main__":
    unittest.main()
