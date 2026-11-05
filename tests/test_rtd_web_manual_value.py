from __future__ import annotations

import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd import web_manual_value as wmv
from tools.rtd.portal import ASSETS

SHIPPED = yaml.safe_load((ASSETS / wmv.SOURCE_NAME).read_text(encoding="utf-8"))
# Words the public manuals project must not show: internal names, governance, AI and status wording.
INTERNAL_WORDS = ("Hello-Docs", "HELLO-DOCS", "治理", "AI", "Agent", "知识库", "资产", "REV", "建设中", "可用")


def strings(value, skip=("revs",)):
    """Every copy string in a loaded block, leaving out REV ids."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            if key not in skip:
                yield from strings(item, skip)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item, skip)


def render(template: str, **context) -> BeautifulSoup:
    env = Environment(loader=FileSystemLoader(ASSETS))
    page = env.get_template(template).render(pathto=lambda name, *args: name, **context)
    return BeautifulSoup(page, "html.parser")


class CopyTests(unittest.TestCase):
    def test_shipped_copy_tags_each_theme_from_its_facets(self):
        themes = wmv.load_value(ASSETS)["internal"]["themes"]
        self.assertEqual([(t["id"], t["theme"], t["status"], t["status_label"]) for t in themes], [
            ("reading", "便捷阅读", "available", "可用"),
            ("machine", "AI 可读", "partial", "部分可用"),
            ("governance", "内容治理", "partial", "部分可用"),
            ("knowledge", "知识积累", "in_progress", "建设中"),
        ])
        self.assertEqual([[f["label"] for f in t["facets"]] for t in themes],
                         [["统一呈现", "扫码直达", "快速查阅"], ["机读导出", "AI 问答", "市场覆盖"],
                          ["版本追溯", "读者反馈", "质量改进"], ["规范沉淀", "可信复用", "辅助创作"]])

    def test_theme_tag_rule(self):
        cases = {("available", "available"): "available", ("available", "in_progress"): "partial",
                 ("validated",): "partial", ("in_progress", "planned"): "in_progress", ("planned",): "planned"}
        for statuses, expected in cases.items():
            with self.subTest(statuses):
                self.assertEqual(wmv.theme_status(list(statuses))[0], expected)
        self.assertEqual(wmv.theme_status(["available", "planned"]), ("partial", "部分可用"))

    def test_public_copy_is_the_approved_reader_text_only(self):
        band = wmv.band_context(wmv.load_value(ASSETS), internal=False)
        self.assertEqual(set(band), {"internal", "title", "lead", "points"})
        self.assertEqual(band["title"], "网页说明书的定位与价值")
        self.assertEqual(band["lead"], "网页说明书以已批准的产品说明书为依据，提供更方便查找和阅读的网页版本。")
        self.assertEqual([(p["title"], p["text"]) for p in band["points"]], [
            ("便捷阅读", "统一的版式和章节导航，手机和电脑都能读，可按型号、产品名称或正文搜索。"),
            ("版本清楚", "每份说明书都标明型号、适用市场和语言。"),
            ("持续更新", "新的产品和语言版本陆续上线，内容修订后发布新版本。"),
        ])
        for text in strings(band):
            for word in INTERNAL_WORDS:
                self.assertNotIn(word, text)

    def test_copy_writes_no_counts_and_says_web_manual(self):
        value = wmv.load_value(ASSETS)
        for text in strings(value):
            self.assertIsNone(re.search(r"[0-9]", text), text)
            self.assertNotIn("电子说明书", text)
        # Our own knowledge base says what the web manuals do: no 总纲, principles, direction block or
        # defensive caveats; what is unfinished shows as a status tag (operator, 2026-11-04).
        self.assertFalse({"key_idea", "direction", "intro", "triad"} & set(value["internal"]))
        self.assertFalse(any("principle" in theme for theme in value["internal"]["themes"]))
        for text in strings(value):
            for caveat in ("不天然", "而不是", "不改变技术事实", "尚非", "未完成"):
                self.assertNotIn(caveat, text)


class ValidationTests(unittest.TestCase):
    def load(self, data) -> None:
        with TemporaryDirectory() as temp:
            (Path(temp) / wmv.SOURCE_NAME).write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
            wmv.load_value(Path(temp))

    def changed(self, edit):
        data = yaml.safe_load(yaml.safe_dump(SHIPPED, allow_unicode=True))
        edit(data)
        return data

    def test_shipped_file_loads(self):
        self.load(SHIPPED)

    def test_malformed_copy_fails_the_build(self):
        facet = ["internal", "themes", 0, "facets", 0]

        def at(data, path):
            for key in path:
                data = data[key]
            return data

        edits = {
            "schema": lambda d: d.update(schema="other/v1"),
            "status": lambda d: at(d, facet).update(status="done"),
            "is planned, so it names its REV": lambda d: at(d, facet).update(status="planned", revs=[]),
            "must list REV-<n> ids": lambda d: at(d, facet).update(revs=["rev-1"]),
            "unique lower-case id": lambda d: d["internal"]["themes"][1].update(id="reading"),
            "public.lead": lambda d: d["public"].update(lead=" "),
            "public.points": lambda d: d["public"].update(points=[]),
            "facets": lambda d: d["internal"]["themes"][2].update(facets=[]),
            "internal.themes[0].summary": lambda d: d["internal"]["themes"][0].update(summary=" "),
        }
        for message, edit in edits.items():
            with self.subTest(message), self.assertRaisesRegex(ValueError, re.escape(message)):
                self.load(self.changed(edit))


class RenderTests(unittest.TestCase):
    def test_public_band_has_no_links_statuses_or_eyebrow(self):
        band = render("_value_band.html", value=wmv.band_context(wmv.load_value(ASSETS), internal=False))
        self.assertEqual(band.h2.get_text(), "网页说明书的定位与价值")
        self.assertEqual(len(band.select(".value-item")), 3)
        self.assertEqual(band.select("a, .value-status, .value-eyebrow"), [])

    def test_internal_band_links_each_theme_to_its_card_on_the_knowledge_home(self):
        band = render("_value_band.html", value=wmv.band_context(wmv.load_value(ASSETS), internal=True))
        self.assertEqual(band.h2.get_text(), "人能读，AI 能读，团队能持续复用")
        self.assertEqual([(a["href"], a.select_one(".value-text").get_text()) for a in band.select("a.value-item")], [
            (f"{wmv.HOME}#reading", "统一呈现、扫码直达、快速查阅"),
            (f"{wmv.HOME}#machine", "机读导出、AI 问答、市场覆盖"),
            (f"{wmv.HOME}#governance", "版本追溯、读者反馈、质量改进"),
            (f"{wmv.HOME}#knowledge", "规范沉淀、可信复用、辅助创作"),
        ])
        self.assertEqual(band.select_one(".value-more a")["href"], f"{wmv.HOME}#value")

    def test_without_a_band_the_home_renders_nothing_for_it(self):
        self.assertIsNone(render("_value_band.html").select_one("section"))

    def test_knowledge_home_shows_one_card_per_theme_with_its_facets(self):
        value = wmv.load_value(ASSETS)
        home = render("workspace_portal.html", value=wmv.page_context(value), share_entry="", system_entry=True,
                      deliverables_entry=True, design_entry=True, matrix_entry=True, updates=[])
        self.assertEqual(home.select_one(".home-line").get_text(), value["internal"]["tagline"])
        cards = home.select("#value article.home-theme")
        self.assertEqual([card["id"] for card in cards], ["reading", "machine", "governance", "knowledge"])
        for card, theme in zip(cards, value["internal"]["themes"], strict=True):
            # First level: name, status and one sentence.
            self.assertEqual(card.h3.get_text(), theme["theme"])
            self.assertEqual(card.select_one("header .home-status")["class"][-1], f"is-{theme['status']}")
            self.assertEqual(card.select_one(":scope > p").get_text(), theme["summary"])
            # Then each facet with its status mark; the note is the row's tooltip.
            facets = card.select("ul > li")
            self.assertEqual([(li.span.get_text(), li.svg["class"][-1]) for li in facets],
                             [(f["label"], f"is-{f['status']}") for f in theme["facets"]])
            self.assertEqual([li["title"] for li in facets],
                             [f"{f['status_label']}：{f['note']}" for f in theme["facets"]])
        # REV ids are evidence in the data file, never shown; no 总纲, principles or direction block.
        self.assertNotIn("REV-", home.get_text())
        self.assertIsNone(home.select_one("#direction, .vp-key, .vp-principle"))
        current = home.select('#app-sidebar a[aria-current="page"]')
        self.assertEqual([(a.span.get_text(), a["href"]) for a in current], [("首页", wmv.HOME)])
        self.assertNotIn("定位与价值", [a.span.get_text() for a in home.select("#app-sidebar a.app-nav-link")])


if __name__ == "__main__":
    unittest.main()
