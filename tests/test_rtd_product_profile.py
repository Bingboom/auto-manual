"""产品档案 (tools/rtd/product_profile.py, product_profile.html): one page per model, read from the snapshot's cells.

The cells follow the snapshot schema v1.1 shape the matrix window agreed (the decided value per product, parameter and
condition). All products, projects, ids and values are invented (P-FAKE-*, FAKE-*); real ones are private.
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
    {"key": "pv_power", "name_zh": "额定功率", "group": "输出", "order": 2, "unit": "W"},
    {"key": "ac_input", "name_zh": "AC 输入", "group": "输入", "order": 1, "unit": "W"},
    {"key": "weight", "name_zh": "重量", "group": "物理", "order": 1, "unit": "kg"},
    {"key": "product_name", "name_zh": "产品名称", "group": "其他", "order": 1, "unit": None},
    {"key": "warranty", "name_zh": "保修期", "group": "商业", "order": 1, "unit": None},
]
PRODUCTS = [
    {"key": "FAKE-1/US", "model": "FAKE-1", "market": "US", "project": "P-FAKE-1", "category": "便携储能",
     "series": "标准", "capacity_tier": "1度电", "names": {"en": "Fake Station 1"}, "short_name": "F1",
     "first_sku_created": "2021-03-14", "first_sku_created_upper_bound": False},
    {"key": "FAKE-1/JP", "model": "FAKE-1", "market": "JP", "project": "P-FAKE-1", "category": "便携储能",
     "series": "标准", "capacity_tier": "1度电", "names": {"ja": "フェイク 1"}, "short_name": "F1"},
    {"key": "FAKE-2/US", "model": "FAKE-2", "market": "US", "project": None, "category": None, "series": None,
     "capacity_tier": None, "names": {}, "short_name": None},
]
SOURCES = [
    {"id": "s-us", "model": "FAKE-1", "market": "US", "language": "en", "edition_date": None,
     "page": "FAKE-1/US/en/md/manual_us.html"},
    {"id": "s-us2", "model": "FAKE-1", "market": "US", "language": "en", "edition_date": "2026-01-02",
     "page": "FAKE-1/US/en/md/manual_us_v2.html"},
    {"id": "s-jp", "model": "FAKE-1", "market": "JP", "language": "ja", "edition_date": None,
     "page": "FAKE-1/JP/ja/md/manual_jp.html"},
]
VALUES = [
    {"id": "v01", "product": "FAKE-1/US", "parameter": "capacity_wh", "printed": "Capacity: 1000Wh", "source": "s-us",
     "position": "SPECIFICATIONS > GENERAL"},
    {"id": "v02", "product": "FAKE-1/US", "parameter": "capacity_wh", "printed": "Capacity: 1002Wh", "source": "s-us2",
     "position": "SPECIFICATIONS"},
    {"id": "v03", "product": "FAKE-1/JP", "parameter": "capacity_wh", "printed": "容量: 1000Wh", "source": "s-jp",
     "position": "仕様"},
]


def cell(product, parameter, display, *, number=None, text=None, condition=None, value="v01", candidates=None,
         disagree=False, source="s-us"):
    return {"product": product, "parameter": parameter, "condition": condition, "display": display, "number": number,
            "text": text, "unit": "", "printed": f"printed {display}", "printed_unit": None, "source": source,
            "value": value, "verified": False, "sources_disagree": disagree, "conflict": False,
            "candidates": candidates if candidates is not None else [value], "empty_reason": None}


CELLS = [
    cell("FAKE-1/US", "capacity_wh", "1000 Wh", number=1000, candidates=["v01", "v02"], disagree=True),
    cell("FAKE-1/JP", "capacity_wh", "1000 Wh", number=1000.0, value="v03", source="s-jp"),
    cell("FAKE-1/US", "cycle_life", "4000 次", number=4000, value="missing-id"),
    cell("FAKE-1/JP", "cycle_life", "6000 次", number=6000, value="v03"),
    cell("FAKE-1/US", "pv_power", "100 W", number=100, condition="STC"),
    cell("FAKE-1/US", "pv_power", "75 W", number=75, condition="NOCT"),
    cell("FAKE-1/US", "ac_input", "100V~ 60Hz", text="100V~ 60Hz"),
    cell("FAKE-1/JP", "ac_input", "100V～ 50/60Hz", text="100V～ 50/60Hz", value="v03"),
    {**cell("FAKE-1/US", "weight", None), "empty_reason": "无数值"},
    cell("FAKE-1/US", "product_name", "Fake Station 1", text="Fake Station 1"),
    cell("FAKE-1/US", "warranty", "5 years", text="5 years"),
]
SNAPSHOT = {"schema": "hello-docs-product-matrix-snapshot/v1.1", "read_at": "2026-01-02T00:00:00Z",
            "products": PRODUCTS, "parameters": PARAMETERS, "sources": SOURCES, "values": VALUES, "cells": CELLS}


def pages(snapshot=SNAPSHOT, extras=None, warn=None):
    return dict(pp.profile_pages(snapshot, labels=LABELS, extras=extras, warn=warn))


def render(context) -> BeautifulSoup:
    template = Environment(loader=FileSystemLoader(ASSETS)).get_template(pp.TEMPLATE)
    nav = {"system": True, "deliverables": True, "design": True, "matrix": True}
    return BeautifulSoup(template.render(**context, site_nav=nav, pathto=lambda name, *args: name), "html.parser")


class SkuDateTests(unittest.TestCase):
    def test_year_month_an_upper_bound_or_nothing(self):
        self.assertEqual(pp.sku_date([{"first_sku_created": "2021-03-14"}]), "2021-03")
        self.assertEqual(pp.sku_date([{"first_sku_created": "2019-07-01", "first_sku_created_upper_bound": True}]),
                         "不晚于 2019-07")
        self.assertEqual(pp.sku_date([{"first_sku_created": None}, {"first_sku_created": "2020-01-02"}]), "2020-01")
        self.assertEqual(pp.sku_date([{}]), "")
        self.assertEqual(pp.sku_date([{"first_sku_created": "unknown"}]), "")


class ProfileTests(unittest.TestCase):
    def test_no_cells_no_pages(self):
        without = {key: value for key, value in SNAPSHOT.items() if key != "cells"}
        self.assertEqual(pp.profile_pages(without, labels=LABELS), [])
        self.assertEqual(pages({**SNAPSHOT, "products": []}), {})

    def test_one_page_per_safe_model_with_its_head(self):
        warnings = []
        unsafe = [{**PRODUCTS[0], "key": f"{model}/US", "model": model} for model in ("../x", "FAKE 3", 'FAKE"4', "A/B")]
        built = pages({**SNAPSHOT, "products": [*PRODUCTS, *unsafe]}, warn=lambda *args: warnings.append(args))
        self.assertEqual(list(built), ["products/item/FAKE-1", "products/item/FAKE-2"])
        self.assertEqual(len(warnings), 4)
        one = built["products/item/FAKE-1"]
        self.assertEqual((one["name"], one["project"], one["classes"]), ("Fake Station 1", "P-FAKE-1", ["便携储能", "标准", "1度电"]))
        # SKU 创建时间 is each market's own; the JP row has none.
        self.assertEqual(one["sku_dates"], [{"code": "US", "label": "美规", "text": "2021-03"},
                                            {"code": "JP", "label": "日规", "text": ""}])
        self.assertEqual([m["label"] for m in one["markets"]], ["美规", "日规"])
        two = built["products/item/FAKE-2"]
        self.assertEqual((two["name"], two["project"], two["classes"], two["groups"]), ("FAKE-2", "", [], []))

    def test_rows_follow_the_page_order_and_a_condition_has_its_own_row(self):
        one = pages()["products/item/FAKE-1"]
        self.assertEqual([(g["title"], [r["label"] for r in g["rows"]]) for g in one["groups"]], [
            ("电池", ["标称容量", "循环寿命"]), ("输出", ["额定功率（NOCT）", "额定功率（STC）"]),
            ("充电与输入", ["AC 输入"]), ("尺寸与重量", ["重量"]), ("保修", ["保修期"])])
        self.assertEqual(one["cells"]["US|pv_power|STC"]["text"], "100 W")
        self.assertEqual(one["cells"]["US|weight|"]["text"], "")  # display null: the page writes 暂无

    def test_sources_list_every_candidate_chosen_first(self):
        one = pages()["products/item/FAKE-1"]
        sources = one["cells"]["US|capacity_wh|"]["sources"]
        self.assertEqual([s["printed"] for s in sources], ["Capacity: 1000Wh", "Capacity: 1002Wh"])
        self.assertEqual(sources[0], {"manual": "《Fake Station 1 说明书》", "market": "美规", "language": "English",
                                      "date": "", "position": "SPECIFICATIONS > GENERAL", "anchor": "",
                                      "printed": "Capacity: 1000Wh", "derived": False,
                                      "doc": "FAKE-1/US/en/md/manual_us"})
        self.assertEqual(sources[1]["date"], "2026-01-02")
        self.assertTrue(one["cells"]["US|capacity_wh|"]["conflict"])
        # A chosen value missing from values still shows the cell's own printed text and source.
        fallback = one["cells"]["US|cycle_life|"]["sources"]
        self.assertEqual((len(fallback), fallback[0]["printed"], fallback[0]["market"]), (1, "printed 4000 次", "美规"))

    def test_differences_compare_rounded_numbers_and_mark_only_figures(self):
        one = pages()["products/item/FAKE-1"]
        rows = {row["label"]: row["cells"] for row in one["differences"]}
        self.assertNotIn("标称容量", rows)  # 1000 and 1000.0 agree
        # Two markets: the row being listed already says they differ, so neither figure is marked.
        self.assertEqual(rows["循环寿命"], [{"text": "4000 次", "odd": False}, {"text": "6000 次", "odd": False}])
        self.assertEqual([c["odd"] for c in rows["AC 输入"]], [False, False])  # texts are listed, never marked
        self.assertEqual(pp.compare_key({"number": 1}), pp.compare_key({"number": 1.0000000001}))

    def test_carried_over_pairings_link_only_to_models_with_a_page(self):
        matrix = {"categories": [{"rows": [{"products": [
            {"key": "p-one", "rows": [{"model": "FAKE-1"}], "detail": {
                "features": {"all": ["UPS"], "some": [], "none": []},
                "pairing": {"named": [{"label": "Fake Panel", "key": "p-panel"}, {"label": "Loose", "key": ""}],
                            "named_by": [{"key": "p-x", "name": "Fake Charger", "model": "FAKE-X", "label": "F1"}]},
                "guides": [{"label": "快速指南", "quick": True, "docs": [{"label": "美规", "doc": "g", "title": "t"}]}]}},
            {"key": "p-panel", "rows": [{"model": "FAKE-2"}], "detail": {}},
        ]}]}]}
        one = pages(extras=pp.matrix_extras(matrix))["products/item/FAKE-1"]
        self.assertEqual(one["pairing"]["named"], [{"label": "Fake Panel", "model": "FAKE-2"},
                                                   {"label": "Loose", "model": ""}])
        self.assertEqual(one["pairing"]["named_by"][0]["model"], "")
        self.assertEqual(pp.matrix_extras(None), {})


class TemplateTests(unittest.TestCase):
    def test_one_head_line_values_as_buttons_and_sources_hidden_until_clicked(self):
        page = render(pages()["products/item/FAKE-1"])
        self.assertEqual(page.select_one(".fr-head h1").get_text(), "Fake Station 1")
        lines = page.select(".fr-head p")
        self.assertEqual(len(lines), 1)
        # Without JavaScript every market panel shows, so the head lists every market's date with its market; the
        # script hides the labels and the other markets' dates (tests/product_profile_ui.test.mjs).
        self.assertEqual(lines[0].get_text(), "FAKE-1 · 便携储能 · 标准 · 1度电 · P-FAKE-1 · SKU 创建时间 美规 2021-03；日规 暂无")
        self.assertEqual([(d["data-market-date"], d.has_attr("hidden")) for d in lines[0].select("[data-market-date]")],
                         [("US", False), ("JP", False)])
        for label in lines[0].select("[data-market-date-label]"):
            label.decompose()
        after_script = [d.get_text() for d in lines[0].select("[data-market-date]")]
        self.assertEqual(after_script, ["2021-03", "暂无"])
        # 产品档案 sits below the 产品库 tab: that tab is current, but not as this page.
        self.assertEqual([(a.get_text(), a.get("aria-current")) for a in page.select(".pt-tabs a")],
                         [("产品库", "true"), ("产品对比", None), ("参数表", None)])
        self.assertNotIn("上市时间", page.get_text())
        us = page.select_one('[data-market-panel="US"]')
        button = us.select_one(".pf-val")
        self.assertEqual((button.get_text(), button["data-label"]), ("1000 Wh", "标称容量"))
        sources = page.find(id=button["data-sources"])
        self.assertTrue(sources.has_attr("hidden"))
        self.assertEqual([p.get_text() for p in sources.select(".pf-src")[0].select("p")],
                         ["来自《Fake Station 1 说明书》 · 美规 · English", "SPECIFICATIONS > GENERAL"])
        self.assertEqual(sources.select(".pf-src")[1].select("p")[1].get_text(), "版本日期 2026-01-02 · SPECIFICATIONS")
        self.assertEqual(sources.select_one("a")["href"], "FAKE-1/US/en/md/manual_us")
        weight = [div for div in us.select(".pf-group dl > div") if div.dt.get_text() == "重量"][0]
        self.assertEqual(weight.dd.get_text(), "暂无")
        self.assertEqual([b.get_text() for b in page.select(".pf-badge")], ["各说明书写法不一致"])
        self.assertTrue(page.select_one("[data-pf-source]").has_attr("hidden"))
        self.assertEqual(len(page.select("#differences td.is-odd")), 0)  # two markets: nothing marked
        text = page.select_one("main").get_text(" ")
        for word in ("snapshot", ".json", "capacity_wh", "未核实", "候选", "REV-", "无数值", "单位与列不符", "未知"):
            self.assertNotIn(word, text)

    def test_a_derived_value_is_described_not_quoted(self):
        # derived: put together from several lines of one manual, so the card says so instead of quoting it.
        derived = {**SNAPSHOT, "values": [{**VALUES[0], "printed": "3 × AC", "derived": True}, *VALUES[1:]]}
        page = render(pages(derived)["products/item/FAKE-1"])
        card = page.find(id=page.select_one('[data-market-panel="US"] .pf-val')["data-sources"]).select(".pf-src")
        self.assertEqual(card[0].p.get_text(), "由《Fake Station 1 说明书》的多处内容整理 · 美规 · English")
        self.assertIsNone(card[0].blockquote)
        self.assertEqual(card[1].blockquote.get_text(), "Capacity: 1002Wh")  # an older value without the field
        self.assertNotIn("派生", page.get_text())

    def test_each_market_shows_its_own_sku_date(self):
        # The markets' months differ, and one is only an upper bound: the page never picks one for the model.
        products = [{**PRODUCTS[0], "first_sku_created": "2021-03-14"},
                    {**PRODUCTS[1], "first_sku_created": "2020-11-02", "first_sku_created_upper_bound": True}, PRODUCTS[2]]
        one = pages({**SNAPSHOT, "products": products})["products/item/FAKE-1"]
        self.assertEqual([d["text"] for d in one["sku_dates"]], ["2021-03", "不晚于 2020-11"])

    def test_an_anchor_leaves_the_position_and_joins_the_manual_link(self):
        anchored = {**SNAPSHOT, "values": [{**VALUES[0], "position": "SPECIFICATIONS > GENERAL #native-specifications"},
                                           *VALUES[1:]]}
        page = render(pages(anchored)["products/item/FAKE-1"])
        card = page.find(id=page.select_one('[data-market-panel="US"] .pf-val')["data-sources"]).select(".pf-src")[0]
        self.assertEqual(card.select("p")[1].get_text(), "SPECIFICATIONS > GENERAL")
        self.assertEqual(card.a["href"], "FAKE-1/US/en/md/manual_us#native-specifications")
        self.assertNotIn("#native", page.select_one("main").get_text())

    def test_a_parameter_without_a_chinese_name_is_skipped_with_a_warning(self):
        warnings = []
        unnamed = {**SNAPSHOT, "parameters": [{**PARAMETERS[0], "name_zh": ""}, *PARAMETERS[1:]]}
        built = pages(unnamed, warn=lambda *args: warnings.append(args))
        one = built["products/item/FAKE-1"]
        labels = [row["label"] for group in one["groups"] for row in group["rows"]]
        self.assertNotIn(PARAMETERS[0]["key"], labels)
        self.assertTrue(any("没有中文名" in str(w[0]) for w in warnings))
        render(one)  # the page still renders
        self.assertEqual(pp.matrix_extras({"categories": [{"rows": [{"products": [
            {"key": "p", "rows": [{"model": "FAKE-1"}], "detail": {"pairing": {"named": [{"key": "x"}],
                                                                                "named_by": [{"name": "n"}]}}}]}]}]}),
            {"FAKE-1": {"features": None, "pairing": None, "guides": []}})

    def test_snapshot_text_is_escaped(self):
        nasty = {**SNAPSHOT, "values": [{**VALUES[0], "printed": 'x</div><script>&"'}],
                 "cells": [cell("FAKE-1/US", "capacity_wh", '<b>1</b>&"', number=1)]}
        page = render(pages(nasty)["products/item/FAKE-1"])
        html = str(page)
        self.assertNotIn("<b>1</b>", html)
        self.assertNotIn("<script>&", html)
        self.assertEqual(page.select_one(".pf-val").get_text(), '<b>1</b>&"')

    def test_a_single_market_product_has_no_switch_and_no_difference_table(self):
        page = render(pages()["products/item/FAKE-2"])
        self.assertIsNone(page.select_one("[data-pf-switch], #differences, #features, #pairing"))
        self.assertEqual(page.select_one(".fr-empty").get_text(), "暂无参数。")
        self.assertIsNone(page.select_one("[data-market-date-label]"))  # one market: no label to show
        self.assertTrue(page.select_one(".fr-head p").get_text().endswith("SKU 创建时间 暂无"))


class PositionTests(unittest.TestCase):
    def test_an_anchor_starts_with_a_letter_and_may_stand_alone(self):
        cases = {
            "SPECIFICATIONS > GENERAL #native-specifications": ("SPECIFICATIONS > GENERAL", "native-specifications"),
            "#native-specifications": ("", "native-specifications"),
            "Table #2": ("Table #2", ""),
            "#2": ("#2", ""),
            "仕様 #仕様": ("仕様 #仕様", ""),
            "Section#inline": ("Section#inline", ""),
        }
        for position, (text, anchor) in cases.items():
            with self.subTest(position=position):
                self.assertEqual(pp._position(position), {"position": text, "anchor": anchor})


class DifferenceTests(unittest.TestCase):
    def test_with_three_markets_the_figure_unlike_the_others_is_marked(self):
        three = [*PRODUCTS[:2], {**PRODUCTS[0], "key": "FAKE-1/EU", "market": "EU", "names": {}}]
        cells = [cell("FAKE-1/US", "cycle_life", "4000 次", number=4000), cell("FAKE-1/JP", "cycle_life", "4000 次", number=4000),
                 cell("FAKE-1/EU", "cycle_life", "6000 次", number=6000)]
        one = pages({**SNAPSHOT, "products": three, "cells": cells})["products/item/FAKE-1"]
        line = {m["code"]: c for m, c in zip(one["markets"], one["differences"][0]["cells"], strict=True)}
        self.assertEqual({code: c["odd"] for code, c in line.items()}, {"US": False, "JP": False, "EU": True})


if __name__ == "__main__":
    unittest.main()
