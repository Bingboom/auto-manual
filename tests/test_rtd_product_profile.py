"""产品档案 (tools/rtd/product_profile.py, product_profile.html): one page per model from the product snapshot.

All products, projects and values are invented (P-FAKE-*, FAKE-*); real ones are private.
"""
from __future__ import annotations

import unittest

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd import product_profile as pp
from tools.rtd.portal import ASSETS

LABELS = {"en": "English", "ja": "日本語"}
PARAMETERS = [
    {"key": "capacity_wh", "name_zh": "标称容量", "group": "电池", "order": 1, "unit": "Wh"},
    {"key": "cycle_life", "name_zh": "循环寿命", "group": "电池", "order": 5, "unit": "次"},
    {"key": "ac_rated", "name_zh": "AC 额定输出", "group": "输出", "order": 2, "unit": "W"},
    {"key": "ac_input", "name_zh": "AC 输入", "group": "输入", "order": 1, "unit": "W"},
    {"key": "dimensions_mm", "name_zh": "尺寸", "group": "物理", "order": 3, "unit": "mm"},
    {"key": "weight", "name_zh": "重量", "group": "物理", "order": 1, "unit": "kg"},
    {"key": "product_name", "name_zh": "产品名称", "group": "其他", "order": 1, "unit": None},
    {"key": "warranty", "name_zh": "保修期", "group": "商业", "order": 1, "unit": None},
]
PRODUCTS = [
    {"key": "FAKE-1/US", "model": "FAKE-1", "market": "US", "project": "P-FAKE-1", "category": "便携储能",
     "series": "标准", "capacity_tier": "1度电", "names": {"en": "Fake Station 1"}, "short_name": "F1"},
    {"key": "FAKE-1/JP", "model": "FAKE-1", "market": "JP", "project": "P-FAKE-1", "category": "便携储能",
     "series": "标准", "capacity_tier": "1度电", "names": {"ja": "フェイク 1"}, "short_name": "F1"},
    {"key": "FAKE-2/US", "model": "FAKE-2", "market": "US", "project": None, "category": None, "series": None,
     "capacity_tier": None, "names": {}, "short_name": None},
]
SOURCES = [
    {"id": "s-us", "model": "FAKE-1", "market": "US", "language": "en", "edition_date": "2026-01-02",
     "page": "FAKE-1/US/en/md/manual_us.html"},
    {"id": "s-jp", "model": "FAKE-1", "market": "JP", "language": "ja", "edition_date": None,
     "page": "FAKE-1/JP/ja/md/manual_jp.html"},
]


def value(product, parameter, *, text=None, number=None, unit=None, source="s-us", qualifier="无", disagree=False,
          printed="Printed: x"):
    return {"product": product, "parameter": parameter, "text": text, "number": number, "printed_unit": unit,
            "source": source, "qualifier": qualifier, "sources_disagree": disagree, "printed": printed,
            "position": "SPECIFICATIONS > GENERAL"}


VALUES = [
    value("FAKE-1/US", "capacity_wh", number=1000, unit="Wh", printed="Capacity: 1000Wh"),
    value("FAKE-1/JP", "capacity_wh", number=1000, unit="Wh", source="s-jp"),
    value("FAKE-1/US", "cycle_life", number=4000, unit="cycles"),
    value("FAKE-1/JP", "cycle_life", number=6000, unit="cycles", source="s-jp"),
    value("FAKE-1/US", "ac_rated", number=1500, unit="W", qualifier="额定", disagree=True),
    value("FAKE-1/US", "ac_input", text="100V-120V~ 60Hz, 15A Max"),
    value("FAKE-1/JP", "ac_input", text="100V～ 50/60Hz", source="s-jp"),
    value("FAKE-1/US", "dimensions_mm", text="300×200×250", unit="cm"),
    value("FAKE-1/US", "weight", number=10.5, unit="kg", qualifier="约"),
    value("FAKE-1/US", "product_name", text="Fake Station 1"),
    value("FAKE-1/US", "warranty", text="5 years"),
]
SNAPSHOT = {"schema": "hello-docs-product-matrix-snapshot/v1", "read_at": "2026-01-02T00:00:00Z",
            "products": PRODUCTS, "parameters": PARAMETERS, "sources": SOURCES, "values": VALUES}


def render(context) -> BeautifulSoup:
    template = Environment(loader=FileSystemLoader(ASSETS)).get_template(pp.TEMPLATE)
    nav = {"system": True, "deliverables": True, "design": True, "matrix": True}
    return BeautifulSoup(template.render(**context, site_nav=nav, pathto=lambda name, *args: name), "html.parser")


class DisplayTests(unittest.TestCase):
    def test_units_and_qualifiers(self):
        self.assertEqual(pp.display({"number": 4000, "printed_unit": "cycles"}, "次"), "4,000 次")
        self.assertEqual(pp.display({"number": 10.5, "qualifier": "约"}, "kg"), "约 10.5 kg")
        self.assertEqual(pp.display({"number": 1500, "qualifier": "额定"}, "W"), "1,500 W（额定）")
        self.assertEqual(pp.display({"text": "300×200×250", "printed_unit": "cm"}, "mm"), "300×200×250 mm")
        self.assertEqual(pp.display({"text": "0~45"}, "°C"), "0~45 °C")
        # Words take no unit: the base's unit belongs to a figure, not a described input.
        self.assertEqual(pp.display({"text": "100V-120V~ 60Hz, 15A Max"}, "W"), "100V-120V~ 60Hz, 15A Max")
        self.assertEqual(pp.display({"number": 2, "printed_unit": "count"}), "2")
        self.assertEqual(pp.display({"printed": "Printed only"}), "Printed only")


class SkuDateTests(unittest.TestCase):
    def test_year_month_an_upper_bound_or_nothing(self):
        self.assertEqual(pp.sku_date([{"first_sku_created": "2021-03-14"}]), "2021-03")
        self.assertEqual(pp.sku_date([{"first_sku_created": "2019-07-01", "first_sku_created_upper_bound": True}]),
                         "不晚于 2019-07")
        self.assertEqual(pp.sku_date([{"first_sku_created": None}, {"first_sku_created": "2020-01-02"}]), "2020-01")
        self.assertEqual(pp.sku_date([{}]), "")
        self.assertEqual(pp.sku_date([{"first_sku_created": "unknown"}]), "")


class ProfileTests(unittest.TestCase):
    def pages(self, extras=None):
        return dict(pp.profile_pages(SNAPSHOT, labels=LABELS, extras=extras))

    def test_one_page_per_model_with_its_head(self):
        pages = self.pages()
        self.assertEqual(list(pages), ["products/item/FAKE-1", "products/item/FAKE-2"])
        one = pages["products/item/FAKE-1"]
        self.assertEqual((one["name"], one["project"], one["classes"]), ("Fake Station 1", "P-FAKE-1",
                                                                        ["便携储能", "标准", "1度电"]))
        self.assertEqual([m["label"] for m in one["markets"]], ["美规", "日规"])
        self.assertEqual(one["sku_date"], "")
        two = pages["products/item/FAKE-2"]
        self.assertEqual((two["name"], two["project"], two["classes"], two["groups"]), ("FAKE-2", "", [], []))

    def test_groups_follow_the_page_order_and_hide_the_head_fields(self):
        one = self.pages()["products/item/FAKE-1"]
        self.assertEqual([(g["title"], [p["name_zh"] for p in g["parameters"]]) for g in one["groups"]], [
            ("电池", ["标称容量", "循环寿命"]), ("输出", ["AC 额定输出"]), ("充电与输入", ["AC 输入"]),
            ("尺寸与重量", ["重量", "尺寸"]), ("保修", ["保修期"])])

    def test_differences_compare_numbers_and_mark_the_odd_cell(self):
        one = self.pages()["products/item/FAKE-1"]
        rows = {row["label"]: row["cells"] for row in one["differences"]}
        self.assertNotIn("标称容量", rows)  # the same number in both markets
        self.assertEqual(rows["循环寿命"], [{"text": "4,000 次", "odd": True}, {"text": "6,000 次", "odd": True}])
        self.assertEqual(list(rows), ["循环寿命", "AC 输入"])
        # Texts in two languages differ in wording: listed, never marked.
        self.assertEqual([cell["odd"] for cell in rows["AC 输入"]], [False, False])
        source = one["cells"]["US|capacity_wh"]["source"]
        self.assertEqual(source, {"market": "美规", "language": "English", "date": "2026-01-02",
                                  "position": "SPECIFICATIONS > GENERAL", "printed": "Capacity: 1000Wh",
                                  "doc": "FAKE-1/US/en/md/manual_us"})
        self.assertEqual(one["manuals"], [{"market": "美规", "docs": [{"label": "English",
                                                                       "doc": "FAKE-1/US/en/md/manual_us"}]},
                                          {"market": "日规", "docs": [{"label": "日本語",
                                                                       "doc": "FAKE-1/JP/ja/md/manual_jp"}]}])

    def test_carried_over_pairings_link_only_to_models_with_a_page(self):
        matrix = {"categories": [{"rows": [{"products": [
            {"key": "p-one", "rows": [{"model": "FAKE-1"}], "detail": {
                "features": {"all": ["UPS"], "some": [], "none": []},
                "pairing": {"named": [{"label": "Fake Panel", "key": "p-panel"}, {"label": "Loose", "key": ""}],
                            "named_by": [{"key": "p-x", "name": "Fake Charger", "model": "FAKE-X", "label": "F1"}]},
                "guides": [{"label": "快速指南", "quick": True, "docs": [{"label": "美规", "doc": "g", "title": "t"}]}]}},
            {"key": "p-panel", "rows": [{"model": "FAKE-2"}], "detail": {}},
        ]}]}]}
        one = self.pages(pp.matrix_extras(matrix))["products/item/FAKE-1"]
        self.assertEqual(one["features"]["all"], ["UPS"])
        self.assertEqual(one["pairing"]["named"], [{"label": "Fake Panel", "model": "FAKE-2"},
                                                   {"label": "Loose", "model": ""}])
        self.assertEqual(one["pairing"]["named_by"][0]["model"], "")  # FAKE-X has no page
        self.assertEqual(one["guides"][0]["label"], "快速指南")
        self.assertEqual(pp.matrix_extras(None), {})


class TemplateTests(unittest.TestCase):
    def test_the_page_shows_values_as_buttons_and_the_source_only_on_click(self):
        one = dict(pp.profile_pages(SNAPSHOT, labels=LABELS))["products/item/FAKE-1"]
        page = render(one)
        self.assertEqual(page.select_one(".fr-head h1").get_text(), "Fake Station 1")
        head = page.select_one(".fr-head p").get_text()
        self.assertEqual(head, "FAKE-1 · 便携储能 · 标准 · 1度电 · P-FAKE-1")
        self.assertEqual(page.select_one(".fr-head p a")["href"], "products/matrix?project=P-FAKE-1")
        self.assertEqual(page.select_one(".pf-date").get_text(), "SKU 创建时间：暂无")
        dated = render({**one, "sku_date": "不晚于 2019-07"})
        self.assertEqual(dated.select_one(".pf-date").get_text(), "SKU 创建时间：不晚于 2019-07")
        self.assertNotIn("上市时间", page.get_text())
        us = page.select_one('[data-market-panel="US"]')
        button = us.select_one(".pf-val")
        self.assertEqual((button.get_text(), button["data-language"], button["data-doc"]),
                         ("1,000 Wh", "English", "FAKE-1/US/en/md/manual_us"))
        self.assertEqual(page.select_one('[data-market-panel="JP"] .pf-group dd .pf-none').get_text(), "暂无")
        badges = page.select(".pf-badge")
        self.assertEqual([b.get_text() for b in badges], ["各说明书写法不一致"])
        self.assertTrue(page.select_one("[data-pf-source]").has_attr("hidden"))
        self.assertTrue(page.select_one("[data-pf-switch]").has_attr("hidden"))
        self.assertEqual([th.get_text() for th in page.select("#differences thead th")], ["参数", "美规", "日规"])
        self.assertEqual(len(page.select("#differences td.is-odd")), 2)
        # A front page: no keys, paths or plumbing words; no verification marks besides the conflict badge.
        text = page.select_one("main").get_text()
        for word in ("snapshot", ".json", "capacity_wh", "未核实", "候选", "REV-"):
            self.assertNotIn(word, text)

    def test_a_single_market_product_has_no_switch_and_no_difference_table(self):
        two = dict(pp.profile_pages(SNAPSHOT, labels=LABELS))["products/item/FAKE-2"]
        page = render(two)
        self.assertIsNone(page.select_one("[data-pf-switch], #differences, #features, #pairing"))
        self.assertEqual(page.select_one(".fr-empty").get_text(), "暂无参数。")


if __name__ == "__main__":
    unittest.main()
