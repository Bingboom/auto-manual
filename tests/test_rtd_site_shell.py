"""The portal's site shell (layout of 2026-11-17): page -> section placement, crumbs and the optional sections."""
from __future__ import annotations

import re
import unittest

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd.portal import ASSETS

ALL = {"system": True, "deliverables": True, "design": True, "matrix": True}


def shell(active: str, crumb: str, nav: dict | None = None, internal: bool = True) -> BeautifulSoup:
    template = Environment(loader=FileSystemLoader(ASSETS)).from_string(
        '{% from "_site_shell.html" import site_sidebar, site_topbar with context %}'
        "{{ site_sidebar(active, nav, internal=internal) }}{{ site_topbar('知识库', crumb, internal=internal) }}")
    html = template.render(active=active, crumb=crumb, nav=ALL if nav is None else nav, internal=internal,
                           pathto=lambda name, *args: name)
    return BeautifulSoup(html, "html.parser")


def crumb_text(page: BeautifulSoup) -> str:
    return " ".join(page.select_one(".app-crumb").get_text(" ").split())


class SiteShellTests(unittest.TestCase):
    def test_every_page_key_the_templates_use_is_placed(self):
        keys = {key for path in ASSETS.glob("*.html")
                for key in re.findall(r"site_sidebar\('([^']+)'", path.read_text(encoding="utf-8"))}
        self.assertTrue(keys)
        for key in sorted(keys):
            page = shell(key, "x")
            self.assertNotIn("app-nav-unassigned", page.select_one("#app-sidebar")["class"], key)
            self.assertEqual(len(page.select(".app-tabs a.selected")), 1, key)

    def test_an_unplaced_page_gets_no_section_and_the_marker(self):
        page = shell("brand-new-page", "新页面")
        self.assertIn("app-nav-unassigned", page.select_one("#app-sidebar")["class"])
        self.assertEqual(page.select(".app-tabs a.selected"), [])
        self.assertEqual(page.select("#app-sidebar a.app-nav-link"), [])
        self.assertEqual(crumb_text(page), "工作资料 / 新页面")  # not filed under 知识资产

    def test_crumbs_name_the_section_of_each_page(self):
        cases = {
            ("overview", "资产总览"): "工作资料 / 知识资产",
            ("product-matrix", "产品信息"): "工作资料 / 知识资产 / 产品信息",
            ("search", "搜索说明书正文"): "工作资料 / 知识资产 / 说明书资料库 / 搜索说明书正文",
            ("deliverables", "说明书工作台"): "工作资料 / 工作台 / 说明书工作台",
            ("system", "系统建设"): "工作资料 / Agent 能力 / 系统建设",
            ("design-system", "设计规范"): "工作资料 / 设计规范",
            # 产品信息's pages name their tab in the crumb, beneath 产品信息 (the product branches pass these labels).
            ("product-matrix", "产品矩阵"): "工作资料 / 知识资产 / 产品信息 / 产品矩阵",
            ("product-matrix", "产品档案"): "工作资料 / 知识资产 / 产品信息 / 产品档案",
            ("product-matrix", "产品对比"): "工作资料 / 知识资产 / 产品信息 / 产品对比",
            ("product-matrix", "参数表"): "工作资料 / 知识资产 / 产品信息 / 参数表",
        }
        for (key, crumb), expected in cases.items():
            self.assertEqual(crumb_text(shell(key, crumb)), expected, key)

    def test_optional_sections_follow_their_pages(self):
        page = shell("overview", "资产总览", {"system": False, "deliverables": False, "design": False, "matrix": False})
        tabs = {a.get_text(): a["href"] for a in page.select(".app-tabs a")}
        # A section whose pages are not built is absent (内容与表现 is not shown, so 设计规范 has its page only).
        self.assertEqual(tabs, {"知识资产": "workspace/index"})
        self.assertIsNone(shell("asset-content", "x").select_one(".app-tabs a.selected"))  # no longer placed
        self.assertIsNone(page.select_one('.app-tool[aria-label="Agent 能力"]'))
        knowledge = shell("overview", "资产总览", {**ALL, "matrix": False})
        self.assertNotIn("产品信息", [a.span.get_text() for a in knowledge.select("#app-sidebar a.app-nav-link")])

    def test_the_knowledge_list_opens_with_its_own_page(self):
        # Reference layout (2026-11-18): 资产总览 is the first entry of 知识资产 and is current on that page only.
        home = shell("overview", "资产总览")
        links = home.select("#app-sidebar a.app-nav-link")
        self.assertEqual([(a.span.get_text(), a["href"]) for a in links][:2],
                         [("资产总览", "workspace/index"), ("产品信息", "products/matrix")])
        self.assertEqual([a.span.get_text() for a in links if "active" in a["class"]], ["资产总览"])
        self.assertEqual(links[0]["aria-current"], "page")
        matrix = shell("product-matrix", "产品矩阵")
        self.assertEqual([a.span.get_text() for a in matrix.select("#app-sidebar a.app-nav-link.active")], ["产品信息"])

    def test_the_top_bar_search_is_a_form_that_works_without_script(self):
        for internal in (True, False):
            page = shell("manuals", "说明书资料库", internal=internal)
            form = page.select_one('.app-header form[role="search"]')
            self.assertEqual((form["action"], form["method"]), ("search", "get"))
            field = form.select_one("input[type=search]")
            self.assertEqual((field["name"], field["aria-keyshortcuts"]), ("q", "/"))
            self.assertEqual(form.select_one(".sr-only").get_text(), "搜索说明书正文")
            self.assertIsNone(page.select_one('.app-tool[aria-label="Agent 能力"]'))
        self.assertEqual(shell("search", "搜索说明书正文").select_one(".app-search-go")["aria-current"], "page")

    def test_the_public_shell_keeps_the_manuals_only(self):
        page = shell("manuals", "说明书资料库", internal=False)
        self.assertIsNone(page.select_one(".app-tabs"))
        self.assertEqual([a.span.get_text() for a in page.select("#app-sidebar a.app-nav-link")],
                         ["说明书资料库", "搜索说明书正文"])
        self.assertEqual(crumb_text(page), "工作资料 / 说明书资料库")


if __name__ == "__main__":
    unittest.main()
