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
    {"key": "pairs", "label": "句对", "value": "1,372"}, {"key": "approved", "label": "句对已批准", "value": "71%"}]}


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
        home = render(cards=front_cards(self.MATRIX, self.LEARNING, CORPUS))
        cards = home.select("#now .home-front-card")
        self.assertEqual([card.strong.get_text() for card in cards], ["产品信息矩阵", "产品知识", "语料库"])
        self.assertEqual([card.select_one(".home-front-line").get_text() for card in cards],
                         ["项目 · 属性 · 时间", "功能 · 限制 · 关系", "句对 · 术语 · 复用"])
        self.assertEqual([card["href"] for card in cards],
                         ["products/matrix", "products/knowledge", "assets/language/index"])
        self.assertEqual([card.select_one(".home-front-fig b").get_text() for card in cards], ["3", "2", "1,372"])
        self.assertEqual([card.time["datetime"] for card in cards], ["2026-11-13", "2026-10-22", "2026-09-24"])
        text = home.select_one("#home").get_text()
        for word in ("已规划", "建设中", "REV-", "主线", "正在做", "最近更新", "台账"):
            self.assertNotIn(word, text)
        self.assertEqual([a.strong.get_text() for a in home.select("#doors .home-card")], ["说明书资料库", "市场与政策"])

    def test_cards_without_a_source_say_none_yet_never_zero(self):
        cards = front_cards(None, None, None)
        self.assertEqual([card["id"] for card in cards], ["knowledge", "corpus"])  # no matrix, no 产品信息 card
        home = render(cards=cards, system_entry=False)
        self.assertEqual({b.get_text() for b in home.select(".home-front-fig b")}, {"暂无"})
        self.assertIsNone(home.select_one(".home-front-fig time"))
        # 产品库 always builds; without a readable snapshot its context has no product count: the card reads 暂无.
        unread = render(cards=front_cards({"facts": {}, "built_on": ""}, None, None), system_entry=False)
        self.assertEqual(unread.select_one("#asset-product .home-front-fig b").get_text(), "暂无")

    def test_entry_cards_carry_line_icons_not_glyphs(self):
        home = render()
        cards = home.select("#doors .home-card")
        self.assertTrue(cards)
        for card in cards:
            self.assertIsNotNone(card.select_one(".home-tile svg.ic"))
        sidebar = home.select("#app-sidebar a.app-nav-link")
        self.assertEqual(sidebar[0].span.get_text(), "产品信息")
        self.assertTrue(all(link.select_one("svg.ic") for link in sidebar))

    def test_share_link_shows_only_with_the_package(self):
        self.assertIsNone(render().select_one("#shares"))
        share = render(share_entry="../ai-share/00_打开分享.html").select_one("a#shares")
        self.assertEqual(share["href"], "../ai-share/00_打开分享.html")


if __name__ == "__main__":
    unittest.main()
