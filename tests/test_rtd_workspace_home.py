"""知识库首页 (front cleanup, 2026-11-17): three asset cards and the two entrances, with no management text."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd.asset_pages import front_cards
from tools.rtd.portal import ASSETS
from tools.rtd.workspace_home import load_home_copy, now_view

SYSTEM = {
    "focus": {"doing": [{"lead": "网页化", "text": "印刷版说明书持续转成网页版", "lane": "web"}]},
}
COPY = {"assets_note": "每写一本都在积累，下一本直接复用"}
CORPUS = {"exported_at": "2026-09-24", "stale": ["语料快照已超过 7 天"], "rows": [], "tiles": [
    {"key": "pairs", "label": "句对", "value": "1,372"}, {"key": "approved", "label": "句对已批准", "value": "71%"}],
    "counts": {"pairs": 1372, "pairs_approved": 974, "terms": 9, "terms_approved": 9, "languages": 3}}


def render(**context) -> BeautifulSoup:
    base = {"share_entry": "", "system_entry": True, "deliverables_entry": True, "design_entry": True,
            "matrix_entry": True, "updates": []}
    template = Environment(loader=FileSystemLoader(ASSETS)).get_template("workspace_portal.html")
    return BeautifulSoup(template.render(**{**base, **context}, pathto=lambda name, *args: name), "html.parser")


class HomeCopyTests(unittest.TestCase):
    def test_shipped_copy_has_only_the_note(self):
        self.assertEqual(list(load_home_copy(ASSETS)), ["assets_note"])
        self.assertTrue(load_home_copy(ASSETS)["assets_note"])

    def test_malformed_copy_fails_and_a_second_doing_list_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets = Path(tmp)
            for text in ("schema: other\n", "schema: hello-docs-workspace-home/v2\n",
                         "schema: hello-docs-workspace-home/v1\nassets_note: n\n",
                         "schema: hello-docs-workspace-home/v2\nassets_note: n\ndoing:\n  - {lead: x, text: y}\n"):
                (assets / "workspace_home.yaml").write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_home_copy(assets)


class NowViewTests(unittest.TestCase):
    def test_main_lines_and_doing_come_from_the_system_page(self):
        view = now_view(SYSTEM, COPY)
        self.assertNotIn("lanes", view)  # the main line replaced the lane list (step 12)
        self.assertEqual(view["doing"], [{"lead": "网页化", "text": "印刷版说明书持续转成网页版"}])
        self.assertEqual(view["assets_note"], COPY["assets_note"])
        self.assertTrue(view["system"])
        alone = now_view(None, COPY)
        self.assertEqual((alone["doing"], alone["system"]), ([], False))


class HomeRenderTests(unittest.TestCase):
    MATRIX = {"facts": {"products": 3, "models": 4}, "built_on": "2026-11-13"}
    LEARNING = {"topics": [{}, {}], "latest_added": "2026-10-22"}

    def test_three_asset_cards_each_with_one_dated_figure(self):
        matrix = {**self.MATRIX, "built": True}
        home = render(cards=front_cards(matrix, self.LEARNING, CORPUS), search_entry=True, manual_count=12)
        self.assertEqual(home.select_one("h1").get_text(), "产品信息中台")
        form = home.select_one("form.home-search")
        self.assertEqual((form["action"], form.input["name"]), ("products/matrix", "q"))
        cards = home.select("#now .home-front-card")
        self.assertEqual([card.strong.get_text() for card in cards], ["产品信息", "产品知识", "语料库"])
        self.assertIn("is-main", cards[0]["class"])
        self.assertEqual([card.select_one(".home-front-link")["href"] for card in cards],
                         ["products/matrix", "products/knowledge", "assets/language/index"])
        self.assertEqual([card.select_one(".home-front-fig").get_text(" ", strip=True) for card in cards],
                         ["3 个产品 · 更新于 2026-11-13", "2 个知识点 · 更新于 2026-10-22",
                          "1,372 组句子 · 更新于 2026-09-24"])
        self.assertEqual([(a.get_text(), a["href"]) for a in cards[0].select(".home-door")],
                         [("产品库", "products/matrix"), ("产品对比", "products/compare"), ("参数表", "products/table")])
        self.assertFalse(cards[1].select(".home-door"))
        text = home.select_one("#home").get_text()
        for word in ("已规划", "建设中", "REV-", "主线", "正在做", "台账", "AI 使用知识分享"):
            self.assertNotIn(word, text)
        self.assertEqual(home.select_one("#doors-title").get_text(), "也常用")
        self.assertEqual([(a.strong.get_text(), a.small.get_text()) for a in home.select("#doors .home-card")],
                         [("说明书资料库", "12 本说明书"), ("市场与政策", "各地区电压、插座与认证")])

    def test_without_products_there_is_no_search_and_one_entrance(self):
        home = render(cards=front_cards({"facts": {}, "built": False}, None, None))
        self.assertIsNone(home.select_one("form.home-search"))
        self.assertEqual([a.get_text() for a in home.select("#asset-product .home-door")], [])

    def test_cards_without_a_source_say_pending_never_zero(self):
        cards = front_cards(None, None, None)
        self.assertEqual([card["id"] for card in cards], ["knowledge", "corpus"])  # no matrix, no 产品信息 card
        home = render(cards=cards, system_entry=False)
        self.assertEqual({b.get_text() for b in home.select(".home-front-fig b")}, {"待统计"})
        self.assertIsNone(home.select_one(".home-front-fig time"))

    def test_entry_cards_carry_line_icons_not_glyphs(self):
        home = render()
        cards = home.select("#doors .home-card")
        self.assertTrue(cards)
        for card in cards:
            self.assertIsNotNone(card.select_one(".home-tile svg.ic"))
        sidebar = home.select("#app-sidebar a.app-nav-link")
        self.assertEqual(sidebar[0].span.get_text(), "首页")
        self.assertTrue(all(link.select_one("svg.ic") for link in sidebar))

    def test_the_share_package_is_not_on_the_home_page(self):
        # 分享资料 sits under 维护 › 其他 in the sidebar since step 13.
        home = render(share_entry="../ai-share/00_打开分享.html")
        self.assertIsNone(home.select_one("#shares"))


if __name__ == "__main__":
    unittest.main()
