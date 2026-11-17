"""知识库首页 (step 12): the four layer cards, the main line and 正在做."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd import asset_layers as al
from tools.rtd.portal import ASSETS
from tools.rtd.workspace_home import load_home_copy, now_view

SYSTEM = {
    "focus": {"doing": [{"lead": "网页化", "text": "印刷版说明书持续转成网页版", "lane": "web"}]},
}
COPY = {"assets_note": "每写一本都在积累，下一本直接复用"}
CORPUS = {"exported_at": "2026-09-24", "stale": ["语料快照已超过 7 天"], "rows": [], "tiles": [
    {"key": "pairs", "label": "句对", "value": "1,372"}, {"key": "approved", "label": "句对已批准", "value": "71%"}]}
CHIP = {"status": "planned", "status_label": "已规划", "revs": ["REV-50", "REV-52"], "tally": "待做 2"}


def views(*, data: bool = True):
    """Layer views as asset_pages builds them; without data every figure is unknown."""
    product = al.product_layer({"facts": {"products": 3, "models": 4}, "built_on": "2026-11-13"} if data else None,
                               {"total": 9} if data else None, topics=None, build_date="2026-11-16")
    content = {**al.layer("content"), "chapters": {"pages": 12, "languages": ["de", "en"]} if data else None,
               "components": {"total": 19} if data else None, "web_languages": 5 if data else None}
    media = {**al.layer("media"), "registry": {"total": 40} if data else None, "symbols": {"total": 7} if data else None}
    language = {**al.layer("language"), "corpus": CORPUS if data else None,
                "tiles": {tile["key"]: tile for tile in CORPUS["tiles"]} if data else {}}
    return product, content, media, language


def layers(**kwargs):
    chips = {"product": CHIP, "content": None, "media": None, "language": None}
    return {"cards": al.home_cards(*views(**kwargs), chips),
            "main_line": {"text": "主线的一句话", "umbrella": "统称", "source": "https://example.invalid/doc"},
            "coverage": {"online": 3, "total": 5, "percent": 60}, "matrix_stage": {"id": "matrix", "chip": CHIP}}


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
    def test_layer_cards_follow_the_priority_order_with_dated_figures(self):
        home = render(now=now_view(SYSTEM, COPY), layers=layers())
        cards = home.select("#layers .home-layer")
        self.assertEqual([card.strong.get_text() for card in cards], ["产品信息", "内容与表现", "视觉媒体", "语言"])
        self.assertEqual([card["href"] for card in cards],
                         ["products/matrix", "assets/content/index", "assets/media/index", "assets/language/index"])
        self.assertIn("is-first", cards[0]["class"])
        # Every figure carries the date it was read on.
        for card in cards:
            for label in card.select(".home-layer-label"):
                self.assertRegex(label.get_text(), r"(构建|导出|发布清单) \d{4}-\d{2}-\d{2}")
        self.assertEqual(cards[3].select_one(".home-layer-fig b").get_text(), "1,372")
        self.assertIn("29% 句对未批准", cards[3].select_one(".home-layer-weak").get_text())
        # Chips only where ledger rows give one.
        self.assertEqual([bool(card.select_one(".home-status")) for card in cards], [True, False, False, False])
        main = home.select_one("#main-line")
        self.assertEqual(main.select_one(".home-mainline-text").get_text(), "主线的一句话")
        self.assertIn("3", main.select_one("li").get_text())
        self.assertEqual([li.get_text() for li in home.select(".home-doing li")], ["网页化：印刷版说明书持续转成网页版"])

    def test_cards_without_a_source_say_pending_never_zero(self):
        home = render(now=now_view(None, COPY), layers={**layers(data=False), "coverage": None},
                      system_entry=False)
        pending = [b.get_text() for b in home.select("#layers .home-layer-fig b")]
        self.assertEqual(set(pending), {"待统计"})
        self.assertEqual(home.select_one("#main-line .is-pending").get_text(), "待统计")
        self.assertIsNone(home.select_one("#now .home-doing"))

    def test_entry_cards_carry_line_icons_not_glyphs(self):
        home = render()
        cards = home.select("#doors .home-card")
        self.assertTrue(cards)
        for card in cards:
            self.assertIsNotNone(card.select_one(".home-tile svg.ic"))
        sidebar = home.select("#app-sidebar a.app-nav-link")
        self.assertEqual(sidebar[0].span.get_text(), "首页")
        self.assertTrue(all(link.select_one("svg.ic") for link in sidebar))

    def test_share_link_shows_only_with_the_package(self):
        self.assertIsNone(render().select_one("#shares"))
        share = render(share_entry="../ai-share/00_打开分享.html").select_one("#shares a.share-card")
        self.assertEqual(share["href"], "../ai-share/00_打开分享.html")


if __name__ == "__main__":
    unittest.main()
