"""产品库 (tools/rtd/product_library.py, product_matrix.html): the matrix read from the product-information snapshot.

Every product, model and project here is invented (P-FAKE-*, FAKE-*): project numbers and product values are private
and never belong in this repository.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd import product_library as pl
from tools.rtd.portal import ASSETS

CATALOG = {"capacity_tiers": ["1度以下", "1度电", "2度电"],
           "categories": [{"name": "便携储能", "series": ["标准", "Plus"]}, {"name": "配件", "series": ["线材"]}]}


def row(model, market="US", *, project="P-FAKE-1", category="便携储能", series="标准", tier="1度电"):
    return {"key": f"{model}/{market}", "model": model, "market": market, "project": project, "category": category,
            "series": series, "capacity_tier": tier}


def snapshot(*rows, read_at="2026-01-02T03:04:05Z"):
    return {"schema": pl.SCHEMA, "read_at": read_at, "products": list(rows), "parameters": [], "sources": [],
            "values": []}


def render(context) -> BeautifulSoup:
    template = Environment(loader=FileSystemLoader(ASSETS)).get_template("product_matrix.html")
    nav = {"system": True, "deliverables": True, "design": True, "matrix": True}
    return BeautifulSoup(template.render(**context, site_nav=nav, pathto=lambda name, *args: name), "html.parser")


class LoadTests(unittest.TestCase):
    def write(self, folder: Path, text: str) -> None:
        path = pl.snapshot_path(folder)
        path.parent.mkdir(parents=True)
        path.write_text(text, encoding="utf-8")

    def test_a_missing_file_is_none_and_an_unusable_one_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(pl.load_snapshot(Path(tmp)))
        for text, reason in (("{not json", "cannot read"), (json.dumps({"schema": "other/v1"}), "schema is 'other/v1'"),
                             (json.dumps({"schema": pl.SCHEMA + ".9"}), "not one of"),
                             (json.dumps({"schema": pl.SCHEMA, "products": [{"market": "US"}]}), "with a model")):
            with self.subTest(reason), tempfile.TemporaryDirectory() as tmp:
                self.write(Path(tmp), text)
                with self.assertRaisesRegex(pl.SnapshotError, reason):
                    pl.load_snapshot(Path(tmp))

    def test_the_context_says_plainly_when_there_is_no_usable_snapshot(self):
        warnings = []
        with tempfile.TemporaryDirectory() as tmp:
            missing = pl.library_context(Path(tmp), CATALOG, warn=lambda *args: warnings.append(args))
            self.write(Path(tmp), "{not json")
            broken = pl.library_context(Path(tmp), CATALOG, warn=lambda *args: warnings.append(args))
        self.assertEqual((missing["built"], missing["problem"], missing["count"]), (False, "还没有产品数据。", None))
        self.assertEqual(broken["problem"], "产品数据暂时读不到，请稍后再看。")
        self.assertEqual(len(warnings), 1)
        for context in (missing, broken):
            page = render(context)
            self.assertEqual(page.select_one("#matrix").get_text(), context["problem"])
            self.assertIsNone(page.select_one(".fr-head p"))  # no count or date without data
            self.assertFalse(page.select(".pl-chip, table"))


class ViewTests(unittest.TestCase):
    def test_models_of_one_project_in_one_cell_merge_and_others_stay_alone(self):
        view = pl.library_view(snapshot(
            row("FAKE-200B"), row("FAKE-200B", "JP"), row("FAKE-100A", "EU"),  # one project, two models
            row("FAKE-300A", project="P-FAKE-2"), row("FAKE-400A", project=None),
            row("FAKE-500A", tier="2度电"),  # same project, another cell: a chip of its own
        ), CATALOG)
        self.assertEqual(view["categories"][0]["columns"], ["1度电", "2度电"])  # only the tiers present
        cell = view["categories"][0]["rows"][0]["cells"][0]
        self.assertEqual([[m["model"] for m in chip["models"]] for chip in cell],
                         [["FAKE-100A", "FAKE-200B"], ["FAKE-300A"], ["FAKE-400A"]])
        self.assertEqual(cell[0]["markets"], ["US", "EU", "JP"])
        self.assertEqual(cell[0]["models"][1]["label"], "美规、日规")
        self.assertEqual((cell[0]["project"], cell[2]["project"]), ("P-FAKE-1", ""))
        self.assertEqual(view["categories"][0]["rows"][0]["cells"][1][0]["models"][0]["model"], "FAKE-500A")
        self.assertEqual((view["count"], view["updated"], view["projects"], view["unassigned"]),
                         (5, "2026-01-02", ["P-FAKE-1", "P-FAKE-2"], True))
        self.assertEqual(view["markets"], [{"code": "US", "label": "美规"}, {"code": "EU", "label": "欧规"},
                                           {"code": "JP", "label": "日规"}])
        self.assertEqual((view["facts"], view["built_on"]), ({"products": 5}, "2026-01-02"))

    def test_order_follows_the_catalog_and_gaps_still_have_a_place(self):
        view = pl.library_view(snapshot(
            row("FAKE-1", series="Plus"), row("FAKE-2", series="标准", tier="1度以下"),
            row("FAKE-3", series=None, tier=None),
            row("FAKE-4", category="配件", series="线材", tier=None),
            row("FAKE-5", category=None, series=None, tier=None),
            row("FAKE-6", category="新类别", series="X", tier=None),
        ), CATALOG)
        self.assertEqual([c["title"] for c in view["categories"]], ["便携储能", "配件", "新类别", "其他"])
        portable = view["categories"][0]
        self.assertEqual(portable["columns"], ["1度以下", "1度电", "容量未注明"])
        self.assertEqual([r["title"] for r in portable["rows"]], ["标准", "Plus", "未分类"])
        self.assertEqual(portable["rows"][2]["cells"][2][0]["models"][0]["model"], "FAKE-3")
        accessories = view["categories"][1]
        self.assertEqual((accessories["tiered"], accessories["columns"]), (False, ["产品"]))
        other = view["categories"][3]
        self.assertEqual([r["title"] for r in other["rows"]], ["未分类"])
        self.assertEqual([c["id"] for c in view["categories"]], ["c1", "c2", "c3", "c4"])

    def test_without_any_project_every_model_is_its_own_chip(self):
        view = pl.library_view(snapshot(row("FAKE-B", project=None), row("FAKE-A", project=None)), CATALOG)
        cell = view["categories"][0]["rows"][0]["cells"][0]
        self.assertEqual([chip["models"][0]["model"] for chip in cell], ["FAKE-A", "FAKE-B"])
        self.assertEqual((view["projects"], view["unassigned"]), ([], True))


    def test_a_project_split_across_cells_stays_split(self):
        # A cell's position is its series and capacity tier: merging across cells would misplace a model, so each
        # cell has its own chip, and the 项目 filter highlights both.
        view = pl.library_view(snapshot(row("FAKE-1"), row("FAKE-2", tier="2度电"), row("FAKE-3", series="Plus")),
                               CATALOG)
        portable = view["categories"][0]
        chips = [chip for r in portable["rows"] for cell in r["cells"] for chip in cell]
        self.assertEqual([[m["model"] for m in chip["models"]] for chip in chips], [["FAKE-1"], ["FAKE-2"], ["FAKE-3"]])
        self.assertEqual({chip["project"] for chip in chips}, {"P-FAKE-1"})
        self.assertTrue(all(chip["rows"] == "P-FAKE-1|US" for chip in chips))

    def test_three_members_read_a_b_c_d_in_code_order(self):
        view = pl.library_view(snapshot(row("FAKE-D"), row("FAKE-B"), row("FAKE-A"), row("FAKE-C")), CATALOG)
        chip = view["categories"][0]["rows"][0]["cells"][0][0]
        self.assertEqual([m["model"] for m in chip["models"]], ["FAKE-A", "FAKE-B", "FAKE-C", "FAKE-D"])
        self.assertEqual(render(view).select_one(".pl-chip").get_text(), "FAKE-A(FAKE-B、FAKE-C、FAKE-D)")

    def test_a_repeated_row_counts_once(self):
        view = pl.library_view(snapshot(row("FAKE-1"), row("FAKE-1"), row("FAKE-1", "JP")), CATALOG)
        chip = view["categories"][0]["rows"][0]["cells"][0][0]
        self.assertEqual((view["count"], chip["markets"], chip["rows"]), (1, ["US", "JP"], "P-FAKE-1|JP P-FAKE-1|US"))

    def test_an_empty_product_list_reads_like_a_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pl.snapshot_path(Path(tmp))
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(snapshot()), encoding="utf-8")
            context = pl.library_context(Path(tmp), CATALOG)
        self.assertEqual((context["built"], context["problem"]), (False, "还没有产品数据。"))
        page = render(context)
        self.assertIsNone(page.select_one(".fr-head p"))
        self.assertNotIn("0 个产品", page.get_text())


class TemplateTests(unittest.TestCase):
    def test_text_from_the_snapshot_is_escaped(self):
        nasty = 'FAKE-<b>&"</script>'
        view = pl.library_view(snapshot(row(nasty, project='P-FAKE-<i>&"', series='S</script>&')), CATALOG)
        html = Environment(loader=FileSystemLoader(ASSETS)).get_template("product_matrix.html").render(
            **view, site_nav={}, pathto=lambda name, *args: name)
        for raw in ("<b>", "</script>&", "<i>"):
            self.assertNotIn(raw, html.split("<main", 1)[1].split("</main>", 1)[0])
        page = BeautifulSoup(html, "html.parser")
        self.assertEqual(page.select_one(".pl-chip a").get_text(), nasty)
        self.assertEqual(page.select_one("tbody th").get_text(), "S</script>&")
        self.assertIn('P-FAKE-<i>&"', [o.get_text() for o in page.select('[data-pl-filter="project"] option')])

    def test_a_merged_chip_reads_a_b_and_links_each_code(self):
        view = pl.library_view(snapshot(row("FAKE-200B"), row("FAKE-100A", "EU"), row("FAKE-300A", project=None)),
                               CATALOG)
        page = render(view)
        self.assertEqual(page.select_one(".fr-head h1").get_text(), "产品库")
        self.assertEqual(page.select_one(".fr-head p").get_text(), "3 个产品 · 更新于 2026-01-02")
        chips = page.select(".pl-chip")
        self.assertEqual([chip.get_text() for chip in chips], ["FAKE-100A(FAKE-200B)", "FAKE-300A"])
        # Without the decided cells no 产品档案 is built: codes open the manual library filtered to them.
        self.assertEqual([a["href"] for a in chips[0].select("a")], ["index?q=FAKE-100A", "index?q=FAKE-200B"])
        with_cells = render(pl.library_view({**snapshot(row("FAKE-200B"), row("FAKE-1/x")), "cells": []}, CATALOG))
        self.assertEqual([a["href"] for a in with_cells.select(".pl-chip a")],
                         ["index?q=FAKE-1/x", "products/item/FAKE-200B"])
        self.assertEqual(chips[0]["data-rows"], "P-FAKE-1|EU P-FAKE-1|US")
        self.assertEqual(chips[1]["data-rows"], "|US")
        self.assertEqual([o.get_text() for o in page.select('[data-pl-filter="project"] option')],
                         ["全部项目", "P-FAKE-1", "未归入项目"])
        self.assertEqual([o["value"] for o in page.select('[data-pl-filter="market"] option')], ["", "US", "EU"])
        # Filters and tabs need the script; without it every category shows.
        self.assertTrue(page.select_one("[data-pl-filters]").has_attr("hidden"))
        self.assertTrue(page.select_one(".pl-tabs").has_attr("hidden"))
        self.assertEqual([th.get_text() for th in page.select("thead th")], ["系列", "1度电"])
        # A front page: no keys, paths, chips about plans or provenance small print.
        text = page.select_one("main").get_text()
        for word in ("snapshot", ".json", "REV-", "建设中", "已规划", "构建"):
            self.assertNotIn(word, text)


if __name__ == "__main__":
    unittest.main()
