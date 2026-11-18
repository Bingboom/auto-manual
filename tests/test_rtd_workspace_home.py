"""知识资产 overview page (workspace/index.html): summary capsule, unified six-card directory and count-only metadata."""
from __future__ import annotations

import unittest

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd.asset_pages import front_cards, front_summary
from tools.rtd.portal import ASSETS

CORPUS = {
    "exported_at": "2026-09-24",
    "stale": ["语料快照已超过 7 天"],
    "rows": [],
    "listed": [{"code": "en"}, {"code": "ja"}, {"code": "fr"}],
    "tiles": [{"key": "pairs", "label": "句对", "value": "1,372"},
              {"key": "approved", "label": "句对已批准", "value": "71%"}],
}


def render(**context) -> BeautifulSoup:
    base = {
        "share_entry": "", "system_entry": True, "deliverables_entry": True,
        "design_entry": True, "matrix_entry": True, "summary": [], "cards": [],
    }
    template = Environment(loader=FileSystemLoader(ASSETS)).get_template("workspace_portal.html")
    return BeautifulSoup(template.render(**{**base, **context}, pathto=lambda name, *args: name), "html.parser")


class HomeRenderTests(unittest.TestCase):
    MATRIX = {"facts": {"products": 109}, "categories": [{}, {}, {}, {}, {}], "built_on": "2026-11-17"}
    LEARNING = {"topics": [{}, {}], "themes": [{}, {}, {}], "latest_added": "2026-10-22"}
    PRODUCTS = [
        {"model": "JE-1000F", "region": "US", "publications": [{"language_scope": "single", "lang": "en"},
                                                               {"language_scope": "single", "lang": "fr"}]},
        {"model": "JE-1000F", "region": "JP", "publications": [{"language_scope": "single", "lang": "ja"}]},
        {"model": "JE-2000F", "region": "EU", "publications": [{"language_scope": "single", "lang": "de"}]},
    ]
    MEDIA = {"count": 142, "types": [{}, {}, {}], "updated": "2026-11-18"}
    MARKET = {"records": [{}, {}, {}, {}], "country_count": 5, "reviewed": "2026-11-01"}

    def test_unified_six_cards_with_count_only_metadata_never_enumerating_markets(self):
        cards = front_cards(self.MATRIX, self.LEARNING, CORPUS,
                            products=self.PRODUCTS, media_front=self.MEDIA, market=self.MARKET)
        summary = front_summary(self.MATRIX, self.PRODUCTS, CORPUS)
        home = render(cards=cards, summary=summary)

        rendered = home.select("#now .home-front-card")
        self.assertEqual([c.select_one(".home-front-title").get_text() for c in rendered],
                         ["产品信息", "说明书资料库", "语料库", "产品知识", "视觉媒体", "市场与政策"])
        self.assertEqual([c["href"] for c in rendered],
                         ["products/matrix", "index", "assets/language/index",
                          "products/knowledge", "assets/media/index", "market/policy"])
        self.assertEqual([c.select_one(".home-front-fig b").get_text() for c in rendered],
                         ["109", "3", "1,372", "2", "142", "4"])
        self.assertEqual([c.select_one(".home-front-meta").get_text() for c in rendered],
                         ["5 个产品类别", "3 个市场 · 4 语种", "3 语种对照", "3 个知识主题", "3 类共用图元", "5 个国家与地区"])

        # Manual card shows counts ("3 个市场 · 4 语种") and never enumerates market/language codes.
        manuals_meta = home.select_one("#asset-manuals .home-front-meta").get_text()
        for code in ("US", "JP", "EU", "KR", "en", "fr", "ja", "de"):
            self.assertNotIn(code, manuals_meta)

        # Header summary capsule renders the three top-level figures cleanly.
        self.assertEqual([s.strong.get_text() for s in home.select(".home-summary .home-sum-item")],
                         ["109款", "3份", "3种"])

        text = home.select_one("#home").get_text()
        for word in ("已规划", "建设中", "REV-", "主线", "正在做", "最近更新", "台账"):
            self.assertNotIn(word, text)

    def test_corpus_card_shows_the_corpus_pages_pair_figure(self):
        whole = render(cards=front_cards(None, None, CORPUS))
        self.assertEqual(whole.select_one("#asset-corpus .home-front-fig b").get_text(), "1,372")
        approved = {**CORPUS, "approved": True, "counts": {"pairs": 971, "terms": 40}}
        home = render(cards=front_cards(None, None, approved))
        self.assertEqual(home.select_one("#asset-corpus .home-front-fig b").get_text(), "971")

    def test_cards_without_a_source_say_none_yet_never_zero(self):
        cards = front_cards(None, None, None)
        self.assertEqual([card["id"] for card in cards], ["manuals", "corpus", "knowledge", "media", "policy"])
        summary = front_summary(None, None, None)
        home = render(cards=cards, summary=summary, system_entry=False)
        self.assertEqual({b.get_text() for b in home.select(".home-front-fig b")}, {"暂无"})
        self.assertEqual([e.get_text() for e in home.select(".home-sum-item .is-pending")], ["暂无", "暂无", "暂无"])
        self.assertIsNone(home.select_one(".home-front-meta"))
        # 产品库 always builds; without a readable snapshot its context has no product count: the card reads 暂无.
        unread = render(cards=front_cards({"facts": {}, "built_on": ""}, None, None), system_entry=False)
        self.assertEqual(unread.select_one("#asset-product .home-front-fig b").get_text(), "暂无")

    def test_cards_and_sidebar_carry_line_icons_and_overview_is_first_left_entry(self):
        home = render(cards=front_cards(self.MATRIX, self.LEARNING, CORPUS))
        cards = home.select("#now .home-front-card")
        self.assertEqual(len(cards), 6)
        for card in cards:
            self.assertIsNotNone(card.select_one(".home-front-tile svg.ic"))
            self.assertIsNotNone(card.select_one(".home-front-arrow svg.ic"))
        sidebar = home.select("#app-sidebar a.app-nav-link")
        self.assertEqual([a.span.get_text() for a in sidebar],
                         ["资产总览", "产品信息", "产品知识", "说明书资料库", "语料库", "视觉媒体", "市场与政策"])
        self.assertEqual(sidebar[0]["aria-current"], "page")
        self.assertIn("active", sidebar[0]["class"])
        self.assertTrue(all(link.select_one("svg.ic") for link in sidebar))

    def test_share_link_shows_only_with_the_package(self):
        self.assertIsNone(render().select_one("#shares"))
        share = render(share_entry="../ai-share/00_打开分享.html").select_one("a#shares")
        self.assertEqual(share["href"], "../ai-share/00_打开分享.html")


if __name__ == "__main__":
    unittest.main()
