from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.product_facts import __main__ as cli
from tools.product_facts.export import (
    ATTRIBUTES, ProductFactsError, SCHEMA, build_export, encode, load_attributes, read_facts,
)

CAPABILITIES = "Document_key,Project,UPS功能,静音充电\nJE-A_US,P-SECRET-1,TRUE,TRUE\nJE-A_EU,P-SECRET-1,TRUE,FALSE\n"
LANGUAGES = "Document_key,Project,languages,notes\nJE-A_US,P-SECRET-1,en;fr,note\n"
SETTINGS = {"site_base_url": "https://docs.example.test/en/latest/", "navigation": {}}
CONFIG = {"region_order": ["US", "EU", "JP"], "language_order": ["en", "ja"], "variant_marks": ["沙金色"],
          "capability_labels": {"静音充电": "静音"}}
# A500 is sold as JE-A (US, EU) and JE-B (JP); 100W is a solar panel; HP3600's manual is missing; JX-Q is unclassified.
CATALOG = {
    "schema": "hello-docs-product-catalog/v3", "exported_at": "2026-11-12", "source": "网页文档",
    "categories": [{"name": "便携储能", "series": ["标准"]}, {"name": "家庭备电", "series": ["HomePower"]},
                   {"name": "太阳能板", "series": ["SolarSaga"]}],
    "capacity_tiers": ["1度以下", "3.6度电"],
    "models": {
        "JE-A": {"category": "便携储能", "series": "标准", "capacity": "1度以下", "short": "A500"},
        "JE-B": {"category": "便携储能", "series": "标准", "capacity": "1度以下", "short": "A500"},
        "JE-H": {"category": "家庭备电", "series": "HomePower", "capacity": "3.6度电", "short": "HP3600"},
        "JS-S": {"category": "太阳能板", "series": "SolarSaga", "short": "100W"},
    },
    "guides": {"JS-G": {"kind": "通用指南", "short": "太阳能连接指南", "routes": ["JS-G/JP/ja"], "applies_to": ["JE-B"]}},
}
US_SPECS = [("Product Name", "Explorer 500"), ("Capacity", "25.6Ah/20V DC (512Wh)"),
            ("Total Output", "800W Rated, 1600W Surge peak"), ("Cycle Life", "3,000 cycles to 70%+ capacity"),
            ("Weight", "About 15.7 lbs / 7.1 kg")]
MANUALS = {
    ("JE-A", "US", "en"): US_SPECS,
    ("JE-A", "US", "fr"): [("Capacité", "512 Wh"), ("Poids", "7,1 kg")],
    ("JE-A", "EU", "en"): [("Capacity", "512Wh"), ("Weight", "Approx. 7.3 kg")],
    ("JE-B", "JP", "ja"): [("定格容量", "25.6Ah (512Wh)"), ("サイクル寿命", "3,000回の充放電後も容量の70%以上を維持"),
                           ("サイズ＆重量", "約300 x 200 x 200 mm (約7.1 kg)")],
    ("JS-S", "US", "en"): [("Peak Power (Pmax)", "STC: 100W"), ("IP Rating", "IP68")],
    ("JX-Q", "US", "en"): [("Capacity", "256Wh"), ("Weight", "3.5 kg")],
    ("JS-G", "JP", "ja"): [],
}


def spec_table(rows: list[tuple[str, str]]) -> str:
    cells = "".join(f"<tr><th>{label}</th><td>{value}</td></tr>" for label, value in rows)
    return f"# INTRO\n\n# SPECIFICATIONS\n<table>{cells}</table>\n"


def target(model: str, region: str, lang: str) -> dict:
    return {"schema_version": "auto-manual-web-publish-target/v2", "model": model, "region": region, "lang": lang,
            "route": f"{model}/{region}/{lang}/md", "manual": f"manual_{lang}.md",
            "version": f"git-20261101-{lang}", "built_at": "2026-11-01T00:00:00+00:00"}


class ProductFactsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.assets = self.root / "tools" / "rtd_portal_assets"
        self.assets.mkdir(parents=True)
        for name, value in (("settings.json", SETTINGS), ("product_matrix.json", CONFIG),
                            ("product_catalog.json", CATALOG)):
            (self.assets / name).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        (self.root / "data").mkdir()
        (self.root / "data" / "model_capabilities.csv").write_text(CAPABILITIES, encoding="utf-8")
        (self.root / "data" / "model_languages.csv").write_text(LANGUAGES, encoding="utf-8")
        publish = self.root / "docs" / "publish"
        targets = [target(*key) for key in MANUALS] + [target("JE-H", "US", "en")]
        for key, rows in MANUALS.items():
            row = target(*key)
            path = publish / "web" / row["route"] / row["manual"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(spec_table(rows), encoding="utf-8")
        (publish / "publish_manifest.json").write_text(
            json.dumps({"built_at": "2026-11-12T00:00:00+00:00", "targets": targets}), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def export(self) -> dict:
        return build_export(self.root, self.assets)

    def records(self) -> dict:
        return {record["id"]: record for record in self.export()["records"]}

    def test_one_record_per_model_and_market_read_from_its_first_edition(self):
        document = self.export()
        self.assertEqual(document["schema"], SCHEMA)
        self.assertEqual([r["id"] for r in document["records"]],
                         ["JE-A/EU", "JE-A/US", "JE-B/JP", "JE-H/US", "JS-S/US", "JX-Q/US"])
        record = self.records()["JE-A/US"]
        self.assertEqual(record["product"], {"short": "A500", "product": "A500", "edition": "", "category": "便携储能",
                                             "series": "标准", "capacity_tier": "1度以下"})
        self.assertEqual((record["manual"]["language"], record["manual"]["version"]), ("en", "git-20261101-en"))
        self.assertEqual(record["manual"]["url"], "https://docs.example.test/en/latest/JE-A/US/en/md/manual_en.html")
        self.assertEqual([e["language"] for e in record["editions"]], ["en", "fr"])
        self.assertEqual(len(record["manual"]["sha256"]), 64)

    def test_each_figure_keeps_the_row_it_was_read_from(self):
        facts = self.records()["JE-A/US"]["facts"]
        self.assertEqual(facts["capacity_wh"], {"value": 512, "unit": "Wh", "quote": "Capacity: 25.6Ah/20V DC (512Wh)"})
        self.assertEqual((facts["ac_rated_w"]["value"], facts["ac_surge_w"]["value"]), (800, 1600))
        self.assertEqual(facts["ac_rated_w"]["quote"], "Total Output: 800W Rated, 1600W Surge peak")
        self.assertEqual((facts["cycle_life"]["value"], facts["weight_kg"]["value"]), (3000, 7.1))
        self.assertEqual(self.records()["JE-B/JP"]["facts"]["cycle_life"]["value"], 3000)

    def test_unknown_lists_only_what_the_category_states(self):
        records = self.records()
        self.assertEqual(records["JE-A/US"]["unknown"], ["expansion_port"])
        self.assertEqual(records["JS-S/US"]["facts"]["panel_power_w"]["value"], 100)
        self.assertEqual(records["JS-S/US"]["facts"]["ip_rating"]["value"], "IP68")
        self.assertEqual(records["JS-S/US"]["unknown"], ["weight_kg"])

    def test_markets_are_never_merged_and_differences_are_listed(self):
        found = self.export()["differences"]
        self.assertEqual(found, [{"product": "A500", "attribute": "weight_kg", "values": [
            {"value": 7.3, "records": ["JE-A/EU"]}, {"value": 7.1, "records": ["JE-A/US", "JE-B/JP"]}]}])

    def test_problems_name_missing_manuals_and_unclassified_models(self):
        document = self.export()
        records = {record["id"]: record for record in document["records"]}
        self.assertIsNone(records["JE-H/US"]["manual"]["sha256"])
        self.assertEqual(records["JE-H/US"]["facts"], {})
        self.assertIn("ac_rated_w", records["JE-H/US"]["unknown"])
        self.assertIsNone(records["JX-Q/US"]["product"])
        self.assertEqual(records["JX-Q/US"]["facts"]["capacity_wh"]["value"], 256)
        self.assertEqual(len(document["problems"]), 2)
        self.assertTrue(any(p.startswith("JE-H/US/en: published manual") for p in document["problems"]))
        self.assertTrue(any(p.startswith("JX-Q: the 产品分类 snapshot") for p in document["problems"]))

    def test_capabilities_are_per_market_and_project_codes_stay_out(self):
        document = self.export()
        records = {record["id"]: record for record in document["records"]}
        self.assertEqual(records["JE-A/US"]["capabilities"], {"UPS功能": True, "静音充电": True})
        self.assertEqual(records["JE-A/EU"]["capabilities"], {"UPS功能": True, "静音充电": False})
        self.assertIsNone(records["JE-B/JP"]["capabilities"])
        self.assertNotIn("P-SECRET-1", encode(document).decode("utf-8"))

    def test_guides_are_listed_apart_from_products(self):
        document = self.export()
        self.assertEqual(document["guides"], [{"code": "JS-G", "kind": "通用指南", "short": "太阳能连接指南",
                                               "applies_to": ["JE-B"], "manuals": [
                                                   {"market": "JP", "language": "ja",
                                                    "page": "JS-G/JP/ja/md/manual_ja.html"}]}])
        self.assertNotIn("JS-G", {record["model"] for record in document["records"]})

    def test_the_same_inputs_give_the_same_bytes_and_the_check_sees_drift(self):
        self.assertEqual(encode(self.export()), encode(self.export()))
        out = self.root / "product_facts.json"
        args = ["--root", str(self.root), "--assets", str(self.assets)]
        with redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main([*args, "--out", str(out)]), 0)
            self.assertEqual(cli.main([*args, "--check", str(out)]), 0)
            (self.root / "docs/publish/web/JE-A/EU/en/md/manual_en.md").write_text(
                spec_table([("Capacity", "512Wh"), ("Weight", "7.1 kg")]), encoding="utf-8")
            self.assertEqual(cli.main([*args, "--check", str(out)]), 1)
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["summary"]["records"], 6)

    def test_an_unusable_publication_or_snapshot_stops_the_export(self):
        (self.assets / "product_catalog.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(ProductFactsError):
            self.export()
        (self.root / "docs/publish/publish_manifest.json").write_text("{}", encoding="utf-8")
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cli.main(["--root", str(self.root), "--assets", str(self.assets)]), 2)
        self.assertIn("ERROR", out.getvalue())


class AttributeDictionaryTest(unittest.TestCase):
    def test_the_shipped_dictionary_is_valid_and_covers_the_matrix_figures(self):
        keys = [attribute["key"] for attribute in load_attributes(ATTRIBUTES)]
        self.assertEqual(keys, ["capacity_wh", "ac_rated_w", "ac_surge_w", "weight_kg", "cycle_life", "panel_power_w",
                                "ip_rating", "output_w", "expansion_port"])

    def test_malformed_dictionaries_are_refused(self):
        good = json.loads(ATTRIBUTES.read_text(encoding="utf-8"))
        broken = [
            {**good, "schema": "other"},
            {**good, "attributes": good["attributes"] + [good["attributes"][0]]},
            {**good, "attributes": [{**good["attributes"][0], "field": "price"}]},
            {**good, "attributes": [{**good["attributes"][0], "type": "money"}]},
            {**good, "attributes": [{**good["attributes"][0], "key": "Capacity"}]},
            {**good, "attributes": [{**good["attributes"][0], "applies_to": "便携储能"}]},
        ]
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "attributes.json"
            for data in broken:
                path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                with self.subTest(data=str(data)[:60]), self.assertRaises(ProductFactsError):
                    load_attributes(path)

    def test_a_table_without_a_figure_states_nothing(self):
        attributes = load_attributes(ATTRIBUTES)
        self.assertEqual(read_facts("", attributes, "太阳能板"), ({}, ["weight_kg", "panel_power_w", "ip_rating"]))
        facts, unknown = read_facts(spec_table([("Expansion Port", "51.2V")]), attributes, "便携储能")
        self.assertEqual(facts["expansion_port"], {"value": True, "unit": None, "quote": "Expansion Port: 51.2V"})
        self.assertNotIn("expansion_port", unknown)


if __name__ == "__main__":
    unittest.main()
