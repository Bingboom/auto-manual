from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd.portal import ASSETS
from tools.rtd.workspace_home import (
    knowledge_growth, load_home_copy, now_view, read_image_assets, read_shared_chapters, reusable_assets,
)

SYSTEM = {
    "focus": {"groups": [
        {"horizon": "now", "lanes": [
            {"id": "workbench", "title": "资料开发工作台", "goal": "在工作台写作，由人审核"},
            {"id": "web", "title": "网页发布与维护闭环", "goal": ""},
        ]},
        {"horizon": "next", "lanes": [{"id": "corpus", "title": "语料库建设与管理", "goal": "按需补齐"}]},
    ], "doing": [{"lead": "网页化", "text": "印刷版说明书持续转成网页版", "lane": "web", "lane_name": "网页发布与维护闭环"}]},
    "corpus": {"exported_at": "2026-09-24", "tiles": [
        {"key": "pairs", "label": "句对", "value": "1,372"}, {"key": "terms", "label": "术语", "value": "232"},
        {"key": "languages", "label": "语料覆盖语言", "value": "11"},
        {"key": "approved", "label": "句对已批准", "value": "71%"},
    ]},
}
COPY = {"assets_note": "每写一本都在积累，下一本直接复用"}
REGISTRY = ("asset_key,override_for,类别,语言维度,状态,适用机型\n"
            "a,,插图,中立,✅成品,ALL\nb,,图标,中立,✅成品,JE-1000F\nc,,插图,按语言,✅成品,JE-1000F\n"
            "d,,插图,按语言,❌缺失,JE-1000F\n")


def make_repo(root: Path, *, registry: str | None = REGISTRY, chapters: bool = True) -> None:
    if registry is not None:
        (root / "data").mkdir(parents=True)
        (root / "data" / "asset_registry.csv").write_text(registry, encoding="utf-8")
    if chapters:
        for lang, stems in {"en": ("11_warranty", "10_troubleshooting", "00_toc"), "de": ("11_warranty",)}.items():
            folder = root / "docs" / "templates" / "page_shared" / lang
            folder.mkdir(parents=True)
            for stem in stems:
                (folder / f"{stem}.rst").write_text("x", encoding="utf-8")


KNOWLEDGE = Path(__file__).parent / "fixtures" / "rtd_product_knowledge"


def make_knowledge(root: Path, added: list[str]) -> None:
    folder = root / "product-knowledge"
    folder.mkdir(parents=True, exist_ok=True)
    topics = [{"id": f"t{index}", **({"added": day} if day else {})} for index, day in enumerate(added)]
    (folder / "topics.json").write_text(json.dumps({"schema_version": 1, "tags": [], "topics": topics}),
                                        encoding="utf-8")


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
        self.assertEqual([lane["title"] for lane in view["lanes"]], ["资料开发工作台", "网页发布与维护闭环"])
        self.assertEqual(view["doing"], [{"lead": "网页化", "text": "印刷版说明书持续转成网页版"}])
        self.assertEqual(view["assets_note"], COPY["assets_note"])
        self.assertTrue(view["system"])
        alone = now_view(None, COPY)
        self.assertEqual((alone["lanes"], alone["doing"], alone["system"]), ([], [], False))


class AssetSourceTests(unittest.TestCase):
    def test_image_assets_count_finished_neutral_and_every_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(Path(tmp), chapters=False)
            self.assertEqual(read_image_assets(Path(tmp) / "data" / "asset_registry.csv"),
                             {"finished": 3, "neutral": 2, "every_model": 1})
            self.assertIsNone(read_image_assets(Path(tmp) / "missing.csv"))

    def test_shared_chapters_count_pages_languages_and_name_known_chapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(Path(tmp), registry=None)
            templates = Path(tmp) / "docs" / "templates"
            self.assertEqual(read_shared_chapters(templates), {"pages": 4, "languages": 2, "names": ["保修", "故障排除"]})
            self.assertIsNone(read_shared_chapters(Path(tmp) / "nowhere"))

    def test_knowledge_growth_draws_the_cumulative_topic_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets = Path(tmp)
            make_knowledge(assets, ["2026-10-08"] * 15 + ["2026-10-21"] * 4 + ["2026-10-22"] * 5)
            growth = knowledge_growth(assets)
            self.assertEqual((growth["total"], growth["since"], growth["delta"]), (24, "10 月 8 日", 9))
            self.assertEqual(growth["spark"]["line"], "4.0,26.0 108.0,17.1 116.0,6.0")
            # A topic without its date leaves the count but drops the line.
            make_knowledge(assets, ["2026-10-08", ""])
            self.assertEqual((knowledge_growth(assets)["total"], knowledge_growth(assets)["spark"]), (2, None))
            self.assertIsNone(knowledge_growth(Path(tmp) / "nowhere"))

    def test_fixture_topics_all_carry_their_added_date(self):
        growth = knowledge_growth(KNOWLEDGE)
        self.assertIsNotNone(growth["spark"])
        self.assertGreater(growth["total"], growth["delta"])


class ReusableAssetTests(unittest.TestCase):
    def test_cards_read_each_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root)
            make_knowledge(root / "assets", ["2026-10-08", "2026-10-08", "2026-10-22"])
            cards = {card["id"]: card for card in reusable_assets(SYSTEM, root / "assets", root)}
        self.assertEqual(list(cards), ["corpus", "images", "chapters", "knowledge"])
        self.assertEqual([part["value"] for part in cards["corpus"]["stock"]], ["1,372", "232"])
        self.assertEqual(cards["corpus"]["bar"]["percent"], 71)
        self.assertEqual(cards["corpus"]["caption"], "11 种语言 · 快照 2026-09-24")
        self.assertEqual((cards["images"]["stock"][0]["value"], cards["images"]["bar"]["percent"]), ("3", 67))
        self.assertEqual(cards["images"]["caption"], "1 张全型号共用")
        self.assertEqual(cards["chapters"]["chips"], ["保修", "故障排除"])
        self.assertEqual(cards["knowledge"]["spark"]["value"], "+1")

    def test_unreadable_sources_leave_their_cards_without_figures(self):
        with tempfile.TemporaryDirectory() as tmp:
            cards = reusable_assets(None, Path(tmp), Path(tmp))
        self.assertEqual([card["stock"] for card in cards], [[], [], [], []])
        self.assertIsNone(cards[0]["docname"])  # no 系统建设 page to link to


class HomeRenderTests(unittest.TestCase):
    def test_now_shows_asset_cards_main_lines_and_doing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root)
            make_knowledge(root / "assets", ["2026-10-08", "2026-10-22"])
            home = render(now=now_view(SYSTEM, COPY), assets=reusable_assets(SYSTEM, root / "assets", root))
        now = home.select_one("#now")
        self.assertEqual(now.select_one(".home-assets-head span").get_text(), COPY["assets_note"])
        cards = now.select(".home-asset")
        self.assertEqual([card.strong.get_text() for card in cards], ["翻译语料", "图片素材", "通用章节", "产品知识"])
        self.assertEqual(cards[0]["href"], "workspace/system/index#language-assets")
        self.assertEqual(cards[0].select_one(".home-asset-track i")["style"], "width:71%")
        self.assertEqual(cards[1]["href"], "workspace/deliverables/index#statistics")
        self.assertEqual(cards[2].name, "div")  # 通用章节 has no page of its own
        self.assertEqual([chip.get_text() for chip in cards[2].select(".home-asset-chips span")], ["保修", "故障排除"])
        self.assertIsNotNone(cards[3].select_one("svg.home-asset-spark polyline"))
        self.assertEqual([li.get_text() for li in now.select(".home-lanes li")], ["资料开发工作台", "网页发布与维护闭环"])
        self.assertEqual([(li.strong.get_text(), li.span.get_text()) for li in now.select(".home-doing li")],
                         [("网页化", "网页化：印刷版说明书持续转成网页版")])
        self.assertNotIn("REV-", now.get_text())
        self.assertEqual(now.select_one(".home-head a")["href"], "workspace/system/index")

    def test_cards_without_a_source_read_no_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = render(now=now_view(None, COPY), assets=reusable_assets(None, Path(tmp), Path(tmp)),
                          system_entry=False)
        self.assertEqual([em.get_text() for em in home.select("#now .home-asset em")], ["无数据"] * 4)
        self.assertIsNone(home.select_one("#now .home-lanes"))
        self.assertIsNone(home.select_one("#now .home-doing"))
        self.assertIsNone(home.select_one("#now .home-head a"))

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
