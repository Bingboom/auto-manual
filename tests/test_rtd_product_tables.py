"""参数表 and 产品对比 (tools/rtd/product_tables.py): read from the snapshot's decided cells, with invented data only."""
from __future__ import annotations

import json
import unittest

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd import product_tables as pt
from tools.rtd.portal import ASSETS

PARAMETERS = [
    {"key": "capacity_wh", "name_zh": "标称容量", "group": "电池", "order": 1, "unit": "Wh"},
    {"key": "cell", "name_zh": "电芯类型", "group": "电池", "order": 2, "unit": None},
    {"key": "pv_power", "name_zh": "额定功率", "group": "输出", "order": 1, "unit": "W"},
    {"key": "product_name", "name_zh": "产品名称", "group": "其他", "order": 1, "unit": None},
]


def product(model, market, *, project="P-FAKE-1", category="便携储能", series="标准", **extra):
    return {"key": f"{model}/{market}", "model": model, "market": market, "project": project, "category": category,
            "series": series, "capacity_tier": "1度电", "names": {"en": f"Name {model}"}, **extra}


def cell(product_key, parameter, display, *, number=None, condition=None, disagree=False):
    return {"product": product_key, "parameter": parameter, "condition": condition, "display": display,
            "number": number, "text": None if number is not None else display, "unit": "", "printed": "x",
            "printed_unit": None, "source": "s", "value": "v", "verified": False, "sources_disagree": disagree,
            "conflict": False, "candidates": ["v"], "empty_reason": None}


SNAPSHOT = {
    "schema": "hello-docs-product-matrix-snapshot/v1.1", "read_at": "2026-01-02T00:00:00Z", "parameters": PARAMETERS,
    "sources": [], "values": [],
    "products": [product("FAKE-B", "US", first_sku_created="2021-05-01"), product("FAKE-B", "JP"),
                 product("FAKE-A", "US", project=None, series="Plus"),
                 product("FAKE-P", "US", project="P-FAKE-2", category="太阳能板", series="Solar")],
    "cells": [cell("FAKE-B/US", "capacity_wh", "1,000 Wh", number=1000),
              cell("FAKE-B/JP", "capacity_wh", "1,000 Wh", number=1000.0),
              cell("FAKE-B/US", "cell", "LFP", disagree=True), cell("FAKE-A/US", "capacity_wh", "500 Wh", number=500),
              cell("FAKE-P/US", "pv_power", "100 W", number=100, condition="STC"),
              cell("FAKE-P/US", "pv_power", "75 W", number=75, condition="NOCT"),
              cell("FAKE-B/US", "product_name", "Name FAKE-B"),
              {**cell("FAKE-A/US", "cell", None), "empty_reason": "无数值"}],
}
CATALOG = {"categories": [{"name": "太阳能板", "series": []}, {"name": "便携储能", "series": []}]}


def render(template, context) -> BeautifulSoup:
    env = Environment(loader=FileSystemLoader(ASSETS))
    nav = {"system": True, "deliverables": True, "design": True, "matrix": True}
    return BeautifulSoup(env.get_template(template).render(**context, site_nav=nav,
                                                            pathto=lambda name, *args: name), "html.parser")


class TableTests(unittest.TestCase):
    def test_a_table_per_category_with_its_own_columns_and_a_row_per_model_and_market(self):
        view = pt.table_view(SNAPSHOT, CATALOG)
        self.assertEqual([c["title"] for c in view["categories"]], ["太阳能板", "便携储能"])
        portable = view["categories"][1]
        self.assertEqual([(c["name"], c["numeric"]) for c in portable["columns"]], [("标称容量", True), ("电芯类型", False)])
        # Projects first, a model's markets in the usual order, rows without a project last.
        self.assertEqual([(r["model"], r["market"], r["project"]) for r in portable["rows"]],
                         [("FAKE-B", "US", "P-FAKE-1"), ("FAKE-B", "JP", "P-FAKE-1"), ("FAKE-A", "US", "")])
        first = portable["rows"][0]
        self.assertEqual((first["name"], first["sku_date"], first["market_label"]), ("Name FAKE-B", "2021-05", "美规"))
        # A number column's head carries the unit, so its cells show the bare number; text columns show display.
        self.assertEqual(first["cells"][0], {"text": "1000", "conflict": False, "sort": 1000})
        self.assertEqual(portable["rows"][1]["cells"][0]["text"], "1000")  # 1000.0: no trailing .0
        self.assertEqual(first["cells"][1]["text"], "LFP")
        self.assertEqual(view["categories"][0]["rows"][0]["cells"][1]["text"], "100")
        self.assertEqual(first["cells"][1]["conflict"], True)
        self.assertEqual(portable["rows"][2]["cells"][1]["text"], "")  # display null: 暂无
        self.assertEqual((portable["projects"], portable["unassigned"], portable["series"]),
                         (["P-FAKE-1"], True, ["Plus", "标准"]))
        # A test condition is its own column.
        self.assertEqual([c["name"] for c in view["categories"][0]["columns"]], ["额定功率（NOCT）", "额定功率（STC）"])

    def test_the_page_renders_sortable_columns_and_plain_cells(self):
        page = render(pt.TABLE_TEMPLATE, pt.table_view(SNAPSHOT, CATALOG))
        self.assertEqual(page.select_one(".pt-tabs .is-on").get_text(), "参数表")
        portable = page.select_one('[data-pt-panel="t2"]')
        heads = [th.get("data-pt-head") or th.get_text() for th in portable.select("thead th")]
        self.assertEqual(heads, ["产品", "型号", "市场", "项目", "SKU 创建时间", "标称容量 (Wh)", "电芯类型"])
        rows = portable.select("tbody tr")
        self.assertEqual(rows[0]["data-project"], "P-FAKE-1")
        self.assertEqual(rows[0].th.a["href"], "products/item/FAKE-B")
        self.assertEqual(rows[2].select("td")[2].get_text(), "未归入")
        # SKU 创建时间 is each market's own: FAKE-B's JP row has none, so it reads 暂无 (never the US date).
        self.assertEqual([row.select("td")[3].get_text() for row in rows], ["2021-05", "暂无", "暂无"])
        self.assertEqual(rows[0].select("td")[3]["data-sort"], "2021-05")
        self.assertEqual(portable.select_one(".pt-badge").get_text(), "各说明书写法不一致")
        self.assertTrue(page.select_one("[data-pt-download]").has_attr("hidden"))
        text = page.select_one("main").get_text()
        for word in ("capacity_wh", "snapshot", "未核实", "候选", "无数值"):
            self.assertNotIn(word, text)

    def test_each_market_row_shows_its_own_sku_date(self):
        products = [product("FAKE-B", "US", first_sku_created="2021-05-01"),
                    product("FAKE-B", "JP", first_sku_created="2020-02-03", first_sku_created_upper_bound=True)]
        rows = pt.table_view({**SNAPSHOT, "products": products}, CATALOG)["categories"][-1]["rows"]
        self.assertEqual([(r["market"], r["sku_date"]) for r in rows], [("US", "2021-05"), ("JP", "不晚于 2020-02")])

    def test_plain_numbers_and_a_number_cell_without_a_number(self):
        self.assertEqual([pt.plain_number(n) for n in (333, 333.0, 2.5, 0.25)], ["333", "333", "2.5", "0.25"])
        # A number column's cell whose number is missing (a range printed as text) shows the display text in full.
        snapshot = {**SNAPSHOT, "cells": [cell("FAKE-B/US", "capacity_wh", "1,000 Wh", number=1000),
                                          cell("FAKE-A/US", "capacity_wh", "500–600 Wh")]}
        rows = pt.table_view(snapshot, CATALOG)["categories"][-1]["rows"]
        self.assertEqual({r["model"]: r["cells"][0]["text"] for r in rows if r["market"] == "US"},
                         {"FAKE-B": "1000", "FAKE-A": "500–600 Wh"})

    def test_no_products_or_no_cells_say_so(self):
        empty = pt.table_view({**SNAPSHOT, "products": []}, CATALOG)
        self.assertEqual((empty["built"], empty["problem"]), (False, "还没有产品数据。"))
        without = pt.table_view({k: v for k, v in SNAPSHOT.items() if k != "cells"}, CATALOG)
        self.assertEqual((without["built"], without["problem"]), (False, "产品数据暂时读不到，请稍后再看。"))
        page = render(pt.TABLE_TEMPLATE, without)
        self.assertEqual(page.select_one(".fr-empty").get_text(), "产品数据暂时读不到，请稍后再看。")
        self.assertIsNone(page.select_one("table"))


class CompareTests(unittest.TestCase):
    def test_every_model_carries_its_cells_per_market(self):
        view = pt.compare_view(SNAPSHOT)
        products = {p["model"]: p for p in view["data"]["products"]}
        self.assertEqual(sorted(products), ["FAKE-A", "FAKE-B", "FAKE-P"])
        self.assertEqual(products["FAKE-B"]["markets"], ["US", "JP"])
        self.assertEqual(products["FAKE-B"]["values"]["US"]["capacity_wh|"], ["1,000 Wh", "#1000", False])
        self.assertEqual(products["FAKE-B"]["values"]["JP"]["capacity_wh|"][1], "#1000")  # 1000.0 compares equal
        self.assertEqual(products["FAKE-B"]["values"]["US"]["cell|"][2], True)
        self.assertNotIn("product_name|", products["FAKE-B"]["values"]["US"])
        self.assertNotIn("cell|", products["FAKE-A"]["values"]["US"])  # an empty display is no value
        self.assertEqual(products["FAKE-P"]["values"]["US"]["pv_power|STC"][0], "100 W")
        self.assertEqual(view["data"]["groups"][0], {"title": "电池", "parameters": [["capacity_wh|", "标称容量"],
                                                                                      ["cell|", "电芯类型"]]})
        self.assertEqual(view["data"]["groups"][1]["parameters"][1], ["pv_power|STC", "额定功率（STC）"])
        self.assertEqual(view["data"]["labels"], {"US": "美规", "JP": "日规"})

    def test_only_safe_model_codes_reach_the_pages(self):
        # The comparison links item/<code>; codes are the allow-listed page names, so a link always has its page.
        unsafe = {**SNAPSHOT, "products": [*SNAPSHOT["products"], product("../x", "US"), product('FAKE"9', "US")]}
        models = [p["model"] for p in pt.compare_view(unsafe)["data"]["products"]]
        self.assertEqual(models, ["FAKE-A", "FAKE-B", "FAKE-P"])
        rows = [r["model"] for c in pt.table_view(unsafe, CATALOG)["categories"] for r in c["rows"]]
        self.assertNotIn("../x", rows)

    def test_without_cells_the_page_says_so(self):
        view = pt.compare_view({k: v for k, v in SNAPSHOT.items() if k != "cells"})
        page = render(pt.COMPARE_TEMPLATE, view)
        self.assertEqual(page.select_one(".fr-empty").get_text(), "产品数据暂时读不到，请稍后再看。")
        self.assertIsNone(page.select_one("#pc-data"))

    def test_the_json_block_cannot_close_its_script(self):
        nasty = {**SNAPSHOT, "products": [product("FAKE-1", "US", names={"en": "</script><b>&"})]}
        html = Environment(loader=FileSystemLoader(ASSETS)).get_template(pt.COMPARE_TEMPLATE).render(
            **pt.compare_view(nasty), site_nav={}, pathto=lambda name, *args: name)
        block = html.split('<script type="application/json" id="pc-data">', 1)[1].split("</script>", 1)[0]
        self.assertNotIn("<", block)
        self.assertEqual(json.loads(block)["products"][0]["name"], "</script><b>&")
        page = BeautifulSoup(html, "html.parser")
        self.assertTrue(page.select_one("[data-pc]").has_attr("hidden"))
        self.assertEqual(page.select_one(".pt-tabs .is-on").get_text(), "产品对比")


if __name__ == "__main__":
    unittest.main()
