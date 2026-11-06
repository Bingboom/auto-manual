"""Keep policy evidence and its verification status tied to the same snapshot."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd import portal
from tools.rtd.market_policy import (
    PAGE, THEMES, group_by_theme, load_themes, market_context, missing_knowledge_anchors,
)


class MarketPolicyTests(unittest.TestCase):
    def snapshot(self, folder, *, status="verified", sources=None, **fields):
        record = dict.fromkeys(("title", "country", "region", "timeline", "change",
                               "mechanism", "impact", "boundary", "reviewed"), "example")
        record.update(id="example-policy", status=status, tags=["example"], sources=sources or [])
        record.update(fields)
        content = Path(folder, "market-policy")
        content.mkdir(exist_ok=True)
        (content / "records.json").write_text(json.dumps({
            "schema_version": 1, "reviewed": "2026-10-06", "records": [record],
        }), encoding="utf-8")
        return content

    def test_missing_snapshot_is_empty(self):
        with TemporaryDirectory() as folder:
            self.assertEqual(market_context(Path(folder))["records"], [])

    def test_verified_record_needs_official_evidence(self):
        with TemporaryDirectory() as folder:
            self.snapshot(folder, sources=[{"kind": "brief", "url": "https://example.org/brief"}])
            with self.assertRaisesRegex(ValueError, "official source"):
                market_context(Path(folder))
            self.snapshot(folder, sources=[{"kind": "official", "url": "https://example.org/policy"}])
            self.assertEqual(market_context(Path(folder))["records"][0]["status"], "verified")

    def test_unsafe_source_links_block_the_build(self):
        for url in ("javascript:alert(1)", "http://example.org", "https://user:password@example.org"):
            with self.subTest(url=url), TemporaryDirectory() as folder:
                self.snapshot(folder, sources=[{"kind": "official", "url": url}])
                with self.assertRaisesRegex(ValueError, "HTTPS URL"):
                    market_context(Path(folder))

    def test_source_image_cannot_escape_its_business_directory(self):
        with TemporaryDirectory() as folder:
            content = self.snapshot(folder, status="unverified", image="../evidence.jpg")
            content.joinpath("evidence.jpg").write_bytes(b"original evidence")
            with self.assertRaisesRegex(ValueError, "unsafe policy source image"):
                market_context(Path(folder))
            self.snapshot(folder, status="unverified", image="evidence.jpg")
            content.joinpath("_assets").mkdir()
            content.joinpath("_assets", "evidence.jpg").symlink_to(content / "evidence.jpg")
            with self.assertRaisesRegex(ValueError, "unsafe policy source image"):
                market_context(Path(folder))

    def test_recorded_business_basis_does_not_claim_policy_verification(self):
        for status in ("demand", "unverified"):
            with self.subTest(status=status), TemporaryDirectory() as folder:
                self.snapshot(folder, status=status, evidence_note="Operator recorded this requirement.")
                record = market_context(Path(folder))["records"][0]
                self.assertEqual(record["status"], status)
                self.assertEqual(record["sources"], [])
        with TemporaryDirectory() as folder:
            self.snapshot(folder, evidence_note="Operator recorded this requirement.")
            with self.assertRaisesRegex(ValueError, "tags and evidence"):
                market_context(Path(folder))

    def test_knowledge_anchors_must_name_an_existing_topic(self):
        records = [{"id": "first", "knowledge": [{"id": "watts"}, {"id": "retired-topic"}]},
                   {"id": "second"}]
        self.assertEqual(missing_knowledge_anchors(records, {"watts"}), [("first", "retired-topic")])
        self.assertEqual(missing_knowledge_anchors(records, {"watts", "retired-topic"}), [])

    def test_unknown_knowledge_anchor_warns_and_the_page_still_renders(self):
        settings = json.loads((portal.ASSETS / "settings.json").read_text(encoding="utf-8"))
        topics = json.loads((portal.ASSETS / "product_knowledge.json").read_text(encoding="utf-8"))["topics"]
        with TemporaryDirectory() as folder:
            self.snapshot(folder, sources=[{"kind": "official", "url": "https://example.org/policy"}], tags=["说明书语言"],
                          knowledge=[{"id": topics[0]["id"], "title": "Known"},
                                     {"id": "retired-topic", "title": "Renamed"}])
            # Seed the per-build caches so only the knowledge pages read their inputs.
            app = SimpleNamespace(
                config=SimpleNamespace(rtd_site_role="combined", rtd_knowledge_dir=folder),
                _rtd_portal_data=(settings, []), _rtd_system_context=None, _rtd_design_context=None,
                _rtd_data_context=None, _rtd_matrix_context=None,
            )
            with patch.object(portal, "deliverables_page_context", return_value={}), \
                    patch("sphinx.util.logging.getLogger") as get_logger:
                pages = {name: context for name, context, _ in portal.collect_workspace_pages(app)}
        self.assertEqual([record["id"] for record in pages[PAGE]["records"]], ["example-policy"])
        warnings = [call.args[0] % call.args[1:] for call in get_logger.return_value.warning.call_args_list]
        self.assertEqual(len(warnings), 1, warnings)
        self.assertIn("example-policy", warnings[0])
        self.assertIn("retired-topic", warnings[0])

    def test_a_record_no_theme_claims_warns_and_shows_under_other(self):
        settings = json.loads((portal.ASSETS / "settings.json").read_text(encoding="utf-8"))
        with TemporaryDirectory() as folder:
            self.snapshot(folder, sources=[{"kind": "official", "url": "https://example.org/policy"}])
            app = SimpleNamespace(
                config=SimpleNamespace(rtd_site_role="combined", rtd_knowledge_dir=folder),
                _rtd_portal_data=(settings, []), _rtd_system_context=None, _rtd_design_context=None,
                _rtd_data_context=None, _rtd_matrix_context=None,
            )
            with patch.object(portal, "deliverables_page_context", return_value={}), \
                    patch("sphinx.util.logging.getLogger") as get_logger:
                pages = {name: context for name, context, _ in portal.collect_workspace_pages(app)}
        self.assertEqual([(theme["id"], theme["title"]) for theme in pages[PAGE]["themes"]], [("other", "其他")])
        warnings = [call.args[0] % call.args[1:] for call in get_logger.return_value.warning.call_args_list]
        self.assertEqual(len(warnings), 1, warnings)
        self.assertIn("example-policy matches no theme", warnings[0])


def record(key, country, status, tags, **fields):
    return {"id": key, "country": country, "status": status, "tags": tags, "title": f"{key} 标题",
            "region": "范围", "timeline": "2027-01-01 起生效", "change": "变化", "mechanism": "原理", "impact": "影响",
            "reviewed": "2026-10-06", "sources": [], **fields}


CONFIG = {"cross_region": "跨地区", "themes": [
    {"id": "language", "title": "说明书语言与准入", "blurb": "b", "icon": "language", "tags": ["说明书语言", "市场准入"]},
    {"id": "energy", "title": "电价与家庭储能", "blurb": "b", "icon": "energy", "tags": ["净计量", "备电"]},
    {"id": "spare", "title": "空主题", "blurb": "b", "icon": "energy", "tags": ["没有记录"]},
]}


class MarketThemeTests(unittest.TestCase):
    """The 2026-11 layout: theme cards with country chips, then the records grouped by theme."""

    def test_shipped_config_names_two_themes(self):
        config = load_themes()
        self.assertEqual([theme["id"] for theme in config["themes"]], ["language", "energy"])
        self.assertEqual(config["cross_region"], "跨地区")

    def test_malformed_config_fails(self):
        good = (portal.ASSETS / THEMES).read_text(encoding="utf-8")
        cases = {
            "schema must be": good.replace("hello-docs-market-themes/v1", "other/v0"),
            "needs a themes list": "schema: hello-docs-market-themes/v1\nthemes: []\n",
            "theme ids must be unique": good.replace("id: energy", "id: language"),
            "other than 'other'": good.replace("id: energy", "id: other"),
            "needs a title and a blurb": good.replace("blurb: 电价", "blurb: ''\n    x: 电价"),
            "needs an icon": good.replace("icon: energy", "icon: rocket"),
            "needs a list of tags": good.replace("tags: [净计量", "tags: []\n    y: [净计量"),
        }
        for message, text in cases.items():
            with self.subTest(message), TemporaryDirectory() as folder:
                Path(folder, THEMES).write_text(text, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    load_themes(Path(folder))

    def test_a_record_joins_the_first_theme_naming_one_of_its_tags(self):
        records = [record("a", "葡萄牙", "verified", ["说明书语言", "备电"]), record("b", "荷兰", "verified", ["净计量"]),
                   record("c", "比利时", "unverified", ["市场线索"])]
        themes, unthemed = group_by_theme(records, CONFIG)
        self.assertEqual([(theme["id"], [r["id"] for r in theme["records"]]) for theme in themes],
                         [("language", ["a"]), ("energy", ["b"]), ("other", ["c"])])  # 空主题 has no records
        self.assertEqual(unthemed, ["c"])

    def test_a_country_chip_counts_its_records_and_opens_the_first(self):
        records = [record("b1", "比利时", "verified", ["净计量"]), record("nl", "荷兰", "verified", ["净计量"]),
                   record("b2", "比利时", "unverified", ["备电"]), record("b3", "比利时", "verified", ["备电"])]
        (energy,), _ = group_by_theme(records, CONFIG)
        self.assertEqual(energy["countries"], [
            {"country": "比利时", "first": "b1", "count": 3, "statuses": ["verified", "unverified"]},
            {"country": "荷兰", "first": "nl", "count": 1, "statuses": ["verified"]},
        ])

    def snapshot_context(self, records):
        with TemporaryDirectory() as folder:
            content = Path(folder, "market-policy")
            content.mkdir()
            (content / "records.json").write_text(json.dumps(
                {"schema_version": 1, "reviewed": "2026-10-06", "records": records}), encoding="utf-8")
            return market_context(Path(folder))

    def test_context_counts_markets_without_the_cross_region_value(self):
        official = [{"kind": "official", "title": "官方", "url": "https://example.org/policy"}]
        context = self.snapshot_context([
            record("pt", "葡萄牙", "verified", ["说明书语言"], sources=official),
            record("eu", "跨地区", "demand", ["渠道需求"], evidence_note="业务需求"),
            record("nl", "荷兰", "verified", ["净计量"], sources=official),
        ])
        self.assertEqual(context["country_count"], 2)
        self.assertEqual(context["statuses"], ["verified", "demand"])
        self.assertEqual([theme["id"] for theme in context["themes"]], ["language", "energy"])
        self.assertEqual(self.snapshot_context([])["themes"], [])

    def render(self, context):
        template = Environment(loader=FileSystemLoader(portal.ASSETS)).get_template("market_policy.html")
        return BeautifulSoup(template.render(**context, pathto=lambda name, *args: name, site_nav={}), "html.parser")

    def test_the_page_shows_theme_cards_then_closed_rows_and_no_filters(self):
        official = [{"kind": "official", "title": "荷兰政府 · 净计量", "url": "https://example.org/policy"}]
        context = self.snapshot_context([
            record("pt", "葡萄牙", "verified", ["说明书语言"], sources=official, boundary="不能用于巴西",
                   knowledge=[{"id": "watts", "title": "额定功率"}]),
            record("eu", "跨地区", "demand", ["渠道需求"], evidence_note="业务需求"),
            record("nl", "荷兰", "verified", ["净计量"], sources=official),
        ])
        page = self.render(context)
        cards = page.select(".mp-theme")
        self.assertEqual([card.strong.get_text() for card in cards], ["说明书语言与准入", "电价与家庭储能"])
        self.assertEqual(cards[0].select_one(".mp-theme-head")["href"], "#theme-language")
        self.assertEqual([(chip["href"], chip["data-record-link"]) for chip in cards[0].select(".mp-chip")],
                         [("#pt", "pt"), ("#eu", "eu")])
        self.assertIsNone(page.select_one(".mp-theme a a"))  # no link inside a link
        rows = page.select("details.mp-record")
        self.assertEqual([row["id"] for row in rows], ["pt", "eu", "nl"])
        self.assertFalse(any(row.has_attr("open") for row in rows))
        self.assertEqual([row.select_one(".mp-status").get_text() for row in rows], ["已核实", "业务需求", "已核实"])
        self.assertEqual(rows[1].select_one(".mp-steps h4").get_text(), "1需求变化")
        self.assertEqual(rows[0].select_one(".mp-boundary").get_text(), "适用边界不能用于巴西")
        self.assertIsNone(rows[2].select_one(".mp-boundary"))
        self.assertEqual(rows[0].select_one(".mp-know")["href"], "products/knowledge#watts")
        self.assertEqual(rows[0].select_one(".mp-source")["href"], "https://example.org/policy")
        self.assertEqual([span.get_text() for span in page.select(".mp-legend > span")][:2], ["已核实", "业务需求"])
        self.assertTrue(page.select_one("#mp-expand").has_attr("hidden"))
        self.assertIsNone(page.select_one("#policy-filters"))
        self.assertEqual(page.select_one(".mp-head .mp-pill").get_text(), "3 条资料 · 2 个国家和地区")

    def test_without_a_snapshot_the_page_says_nothing_is_recorded_yet(self):
        with TemporaryDirectory() as folder:
            page = self.render(market_context(Path(folder)))
        self.assertEqual(page.select_one("#policy-list h2").get_text(), "暂未录入市场与政策资料")
        self.assertIsNone(page.select_one(".mp-theme"))


if __name__ == "__main__":
    unittest.main()
