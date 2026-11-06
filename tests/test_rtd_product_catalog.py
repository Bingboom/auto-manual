"""产品分类: the 网页文档 table's 产品类别, 产品系列 and 商品简称 per model, read into a public snapshot."""
import datetime as dt
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.rtd import product_catalog
from tools.rtd.portal import ASSETS
from tools.rtd.product_catalog import (
    CatalogError, catalog_from_rows, catalog_problems, cell_list, classify, export_catalog, field_options,
    load_catalog, short_names,
)

TODAY = dt.date(2026, 11, 6)
FIELDS = [
    {"field_name": "型号", "type": 1},
    {"field_name": "产品类别", "property": {"options": [{"name": "便携电源"}, {"name": "家庭备电"}, {"name": "空类别"}]}},
    # lark-cli lists options at the top level; the Open API nests them under property.
    {"name": "产品系列", "options": [{"name": "Plus"}, {"name": "标准"}, {"name": "HomePower"}, {"name": "无人用"}]},
]
SITE = "https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest"


def row(models, shorts, category="便携电源", series="标准", route=""):
    link = {"link": f"{SITE}/{route}/md/manual.html", "text": "manual"} if route else None
    return {"型号": models, "商品简称": shorts, "产品类别": category, "产品系列": series, "超链接": link}


ROWS = [
    ("rec1", row("JE-1000F, JE-1000F-SG", "E1000V2，E1000V2沙金色", route="JE-1000F/US/en")),
    ("rec2", row("JE-1000F", "E1000V2", route="JE-1000F/EU/en")),
    ("rec3", row("JE-1000H", "E1000Plusv2", series="Plus", route="JE-1000H/EU/en")),
    ("rec4", row([{"text": "JHP-3000D"}], [{"text": "HP3000"}], "家庭备电", "HomePower", route="JHP-3000D/US/en")),
    ("rec5", row("JE-NEW", "ENEW", category="", series="")),
]


class CellTests(unittest.TestCase):
    def test_cells_split_on_ascii_and_full_width_separators_and_join_segments(self):
        self.assertEqual(cell_list("JE-1, JE-2，JE-3、JE-4"), ["JE-1", "JE-2", "JE-3", "JE-4"])
        self.assertEqual(cell_list([{"text": "JE-1, "}, {"text": "JE-2"}]), ["JE-1", "JE-2"])
        self.assertEqual(cell_list(None), [])

    def test_options_keep_the_table_order_in_either_field_shape(self):
        self.assertEqual(field_options(FIELDS, "产品类别"), ["便携电源", "家庭备电", "空类别"])
        self.assertEqual(field_options(FIELDS, "产品系列"), ["Plus", "标准", "HomePower", "无人用"])
        with self.assertRaisesRegex(CatalogError, "no 产品类别 field"):
            field_options([], "产品类别")
        with self.assertRaisesRegex(CatalogError, "no options"):
            field_options([{"name": "产品类别", "options": []}], "产品类别")


class CatalogFromRowsTests(unittest.TestCase):
    def test_models_categories_and_shared_pages(self):
        snapshot, skipped = catalog_from_rows(FIELDS, ROWS, today=TODAY)
        self.assertEqual(snapshot["exported_at"], "2026-11-06")
        # Only used categories and series, in the options' order.
        self.assertEqual(snapshot["categories"], [{"name": "便携电源", "series": ["Plus", "标准"]},
                                                  {"name": "家庭备电", "series": ["HomePower"]}])
        models = snapshot["models"]
        self.assertEqual(list(models), ["JE-1000F", "JE-1000F-SG", "JE-1000H", "JHP-3000D"])
        self.assertEqual(models["JE-1000F"], {"category": "便携电源", "series": "标准", "short": "E1000V2"})
        self.assertEqual(models["JE-1000F-SG"], {"category": "便携电源", "series": "标准", "short": "E1000V2沙金色",
                                                 "pages_of": "JE-1000F", "routes": ["JE-1000F/US/en"]})
        self.assertEqual(models["JHP-3000D"]["short"], "HP3000")
        self.assertEqual(skipped, ["rec5 (JE-NEW): no 产品类别 or 产品系列"])
        self.assertEqual(catalog_problems(snapshot), [])

    def test_a_listed_model_with_rows_of_its_own_does_not_share_pages(self):
        rows = [*ROWS, ("rec6", row("JE-1000F-SG", "E1000V2沙金色", route="JE-1000F-SG/US/en"))]
        self.assertNotIn("pages_of", catalog_from_rows(FIELDS, rows, today=TODAY)[0]["models"]["JE-1000F-SG"])

    def test_inconsistent_rows_fail_the_refresh(self):
        broken = {
            "型号 lists 2 models but 商品简称 1": [("r", row("JE-1, JE-2", "E1"))],
            "rows disagree": [("r", row("JE-1", "E1")), ("s", row("JE-1", "E1", series="Plus"))],
            "listed after both": [("r", row("JE-1, JE-9", "E1, E9")), ("s", row("JE-2, JE-9", "E2, E9"))],
            "the link opens JE-2/US/en": [("r", row("JE-1", "E1", route="JE-2/US/en"))],
            "not an option": [("r", row("JE-1", "E1", series="Ultra"))],
            "not a model code": [("r", row("JE 1", "E1"))],
        }
        for message, rows in broken.items():
            with self.subTest(message=message), self.assertRaisesRegex(CatalogError, message):
                catalog_from_rows(FIELDS, rows, today=TODAY)


class SnapshotTests(unittest.TestCase):
    def test_the_shipped_snapshot_is_sound_and_covers_the_shared_colour_edition(self):
        snapshot, problems = load_catalog(ASSETS)
        self.assertEqual(problems, [])
        self.assertEqual(snapshot["models"]["JE-1000F-SG"]["pages_of"], "JE-1000F")
        self.assertEqual(short_names(snapshot)["JE-1000F"], "E1000V2")
        self.assertEqual(product_catalog.main(["check"]), 0)

    def test_unsound_snapshots_are_reported(self):
        good, _ = catalog_from_rows(FIELDS, ROWS, today=TODAY)
        cases = {
            "schema": {**good, "schema": "x"},
            "exported_at": {**good, "exported_at": "soon"},
            "unique name": {**good, "categories": [*good["categories"], good["categories"][0]]},
            "listed category": {**good, "models": {**good["models"], "JE-X": {"category": "家庭备电", "series": "Plus",
                                                                              "short": "X"}}},
            "商品简称": {**good, "models": {"JE-X": {"category": "家庭备电", "series": "HomePower", "short": " "}}},
            "unknown keys": {**good, "models": {"JE-X": {"category": "家庭备电", "series": "HomePower", "short": "X",
                                                         "sku": "HTE"}}},
            "come together": {**good, "models": {"JE-X": {"category": "家庭备电", "series": "HomePower", "short": "X",
                                                          "pages_of": "JE-X"}}},
            "another listed model": {**good, "models": {"JE-X": {"category": "家庭备电", "series": "HomePower",
                                                                 "short": "X", "pages_of": "JE-Y", "routes": []}}},
            "models must": {**good, "models": {}},
        }
        for message, data in cases.items():
            with self.subTest(message=message):
                self.assertTrue(any(message in problem for problem in catalog_problems(data)), catalog_problems(data))
        self.assertEqual(catalog_problems([]), ["the snapshot is not a JSON object"])

    def test_a_missing_or_unreadable_snapshot_is_reported_not_raised(self):
        with TemporaryDirectory() as temp:
            assets = Path(temp) / "tools" / "rtd_portal_assets"
            assets.mkdir(parents=True)
            self.assertIsNone(load_catalog(assets)[0])
            (assets / "product_catalog.json").write_text("{", encoding="utf-8")
            data, problems = load_catalog(assets)
            self.assertIsNone(data)
            self.assertIn("cannot read", problems[0])

    def test_classify_marks_each_product_and_names_the_models_left_out(self):
        snapshot, _ = catalog_from_rows(FIELDS, ROWS, today=TODAY)
        products = [{"model": "JE-1000F"}, {"model": "JE-OLD"}, {"model": "JE-OLD"}]
        self.assertEqual(classify(products, snapshot), ["JE-OLD"])
        self.assertEqual((products[0]["product_category"], products[0]["product_series"]), ("便携电源", "标准"))
        self.assertEqual(products[1]["product_category"], "")
        self.assertEqual(classify([{"model": "JE-1000F"}], None), ["JE-1000F"])


class ExportTests(unittest.TestCase):
    def test_export_reads_the_field_list_and_every_row_read_only(self):
        names = ["型号", "商品简称", "产品类别", "产品系列", "超链接", "规格型号"]
        calls = []

        def run(args):
            calls.append(args[:2])
            if args[1] == "+field-list":
                return {"code": 0, "data": {"fields": FIELDS}}
            rows = [[r[name] if name in r else "HTE-SKU" for name in names] for _, r in ROWS]
            return {"code": 0, "data": {"fields": names, "data": rows, "record_id_list": [rid for rid, _ in ROWS],
                                        "total": len(ROWS), "has_more": False}}

        snapshot, skipped = export_catalog(run=run, base_token="base", table_id="tbl", today=TODAY)
        self.assertEqual(calls, [["base", "+field-list"], ["base", "+record-list"]])
        self.assertEqual(len(snapshot["models"]), 4)
        self.assertEqual(len(skipped), 1)
        # Only the five columns are read: no SKU text reaches the public snapshot.
        self.assertNotIn("HTE", json.dumps(snapshot, ensure_ascii=False))

    def test_a_field_list_without_fields_fails(self):
        with self.assertRaisesRegex(CatalogError, "no fields"):
            export_catalog(run=lambda args: {"code": 0, "data": {}}, base_token="b", table_id="t", today=TODAY)


if __name__ == "__main__":
    unittest.main()
