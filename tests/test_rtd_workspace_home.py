from __future__ import annotations

import unittest

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd.portal import ASSETS
from tools.rtd.workspace_home import now_view

SYSTEM = {
    "focus": {"groups": [
        {"horizon": "now", "lanes": [
            {"id": "workbench", "title": "资料开发工作台", "goal": "在工作台写作，由人审核"},
            {"id": "web", "title": "网页发布与维护闭环", "goal": ""},
        ]},
        {"horizon": "next", "lanes": [{"id": "corpus", "title": "语料库建设与管理", "goal": "按需补齐"}]},
    ]},
    "now": [{"rev": "REV-09", "label": "代表目标修订、发布与恢复演练"}, {"rev": "REV-47", "label": "写作规则与并行试点"}],
}
DELIVERABLES = {
    "production": {"overview": [{"id": "manuals", "value": 101, "display": "101"},
                                {"id": "variants", "value": 209, "display": "209"},
                                {"id": "word", "value": 19, "display": "19"}]},
    "progress": {"kpis": {"reviews": 6}},
}


def render(**context) -> BeautifulSoup:
    base = {"share_entry": "", "system_entry": True, "deliverables_entry": True, "design_entry": True,
            "matrix_entry": True, "updates": []}
    template = Environment(loader=FileSystemLoader(ASSETS)).get_template("workspace_portal.html")
    return BeautifulSoup(template.render(**{**base, **context}, pathto=lambda name, *args: name), "html.parser")


class NowViewTests(unittest.TestCase):
    def test_current_lanes_doing_labels_and_three_figures(self):
        view = now_view(SYSTEM, DELIVERABLES)
        self.assertEqual([lane["title"] for lane in view["lanes"]], ["资料开发工作台", "网页发布与维护闭环"])
        self.assertEqual(view["doing"], ["代表目标修订、发布与恢复演练", "写作规则与并行试点"])
        self.assertEqual([(f["label"], f["value"], f["unit"]) for f in view["figures"]],
                         [("网页说明书", "101", "本"), ("语言版本", "209", "个"), ("审核中", 6, "本")])
        self.assertTrue(view["system"])

    def test_missing_inputs_leave_out_lanes_and_show_no_data(self):
        view = now_view(None, {})
        self.assertEqual((view["lanes"], view["doing"], view["system"]), ([], [], False))
        self.assertEqual([f["value"] for f in view["figures"]], [None, None, None])
        unknown = now_view(SYSTEM, {"production": {"overview": [{"id": "manuals", "value": None, "display": ""}]},
                                    "progress": {"kpis": {"reviews": None}}})
        self.assertEqual([f["value"] for f in unknown["figures"]], [None, None, None])


class HomeRenderTests(unittest.TestCase):
    def test_now_shows_lanes_doing_and_figures_linked_to_their_pages(self):
        home = render(now=now_view(SYSTEM, DELIVERABLES))
        now = home.select_one("#now")
        self.assertEqual([li.strong.get_text() for li in now.select(".home-lanes li")], ["资料开发工作台", "网页发布与维护闭环"])
        self.assertIn("代表目标修订、发布与恢复演练；写作规则与并行试点", now.select_one(".home-doing").get_text())
        self.assertNotIn("REV-", now.get_text())
        self.assertEqual([(a["href"], a.strong.get_text()) for a in now.select("a.home-figure")], [
            ("workspace/deliverables/index#deliverables", "101本"),
            ("workspace/deliverables/index#deliverables", "209个"),
            ("workspace/deliverables/index#web-progress-reviews", "6本"),
        ])
        self.assertEqual(now.select_one(".section-header a")["href"], "workspace/system/index")

    def test_missing_figures_read_no_data_and_doors_follow_the_sidebar(self):
        home = render(now=now_view(None, {}), system_entry=False, matrix_entry=False)
        self.assertEqual([a.strong.get_text() for a in home.select("#now a.home-figure")], ["无数据"] * 3)
        self.assertIsNone(home.select_one("#now .home-lanes"))
        groups = [(s.h2.get_text(), [c.strong.get_text() for c in s.select(".home-card")])
                  for s in home.select("#doors .home-group")]
        self.assertEqual(groups, [("说明书", ["说明书资料库", "搜索说明书正文"]),
                                  ("产品与市场", ["产品知识", "市场与政策"]),
                                  ("说明书生产", ["说明书工作台", "设计规范"])])

    def test_share_link_shows_only_with_the_package(self):
        self.assertIsNone(render().select_one("#shares"))
        share = render(share_entry="../ai-share/00_打开分享.html").select_one("#shares a.share-card")
        self.assertEqual(share["href"], "../ai-share/00_打开分享.html")


if __name__ == "__main__":
    unittest.main()
