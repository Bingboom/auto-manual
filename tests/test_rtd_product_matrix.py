from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools.rtd import product_matrix
from tools.rtd.portal import ASSETS
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd.product_matrix import (
    ProductMatrixError, capacity_mismatch, display_name, evidence_excerpt, load_config, matrix_context, number, positioning_groups,
    product_matrix_page_context, read_specs, spec_pairs,
)
from tools.utils.path_utils import Paths

CAPABILITIES = "Document_key,Project,UPS功能,静音充电\nJE-A_EU,P1,TRUE,FALSE\nJE-A_US,P1,TRUE,TRUE\nJE-Z_JP,P2,FALSE,FALSE\n"
LANGUAGES = "Document_key,Project,languages,notes\nJE-A_EU,P1,en;fr,note\n"
SETTINGS = {"navigation": {
    "needs": [{"id": "appliance", "title": "通用电器供电", "models": ["JE-A"]}],
    "ecosystem": [{"id": "solar", "title": "太阳能补能", "models": ["JS-S"]}],
}, "catalog_categories": {"便携电源": {"id": "portable", "icon": "portable"}},
    "language_labels": {"en": "English", "fr": "Français", "ja": "日本語"}}
# The 产品分类 snapshot: A500 has a second market model (JE-B) and a colour edition sold on JE-A's US pages.
CATALOG = {
    "schema": "hello-docs-product-catalog/v3", "exported_at": "2026-11-06", "source": "网页文档",
    "categories": [{"name": "便携电源", "series": ["标准", "Plus"]}, {"name": "家庭备电", "series": ["HomePower"]},
                   {"name": "太阳能板", "series": ["SolarSaga"]}],
    "capacity_tiers": ["1度以下", "1度电", "3.6度电"],
    "models": {
        "JE-A": {"category": "便携电源", "series": "标准", "capacity": "1度以下", "short": "A500"},
        "JE-B": {"category": "便携电源", "series": "标准", "capacity": "1度以下", "short": "A500"},
        "JE-A-SG": {"category": "便携电源", "series": "标准", "capacity": "1度以下", "short": "A500沙金色",
                    "pages_of": "JE-A", "routes": ["JE-A/US/en"]},
        "JE-H": {"category": "家庭备电", "series": "HomePower", "capacity": "3.6度电", "short": "HP3600"},
        "JS-S": {"category": "太阳能板", "series": "SolarSaga", "short": "100W"},
    },
}
CONFIG = {
    "region_order": ["US", "EU", "JP"], "language_order": ["en", "ja"],
    "lines": [{"id": "appliance"}, {"id": "home", "title": "家庭备电", "evidence": True}],
    "accessories": [{"id": "solar"}],
    "assign": {"JE-H": {"line": "home", "evidence": "backup power to home circuits"}},
    "names": {"JS-S": "Panel S"}, "notes": {},
    "capability_labels": {"静音充电": "静音"},
    "markets": {"US": {"letter": "美", "label": "美规"}, "EU": {"letter": "欧", "label": "欧规"},
                "JP": {"letter": "日", "label": "日规"}},
    "variant_marks": ["沙金色"],
    "pairings": [{"model": "JE-H", "parts": ["Battery Pack 3", {"label": "Switch（JA-SW1）", "match": "JA-SW1"}],
                  "solar": [{"label": "SolarSaga 100", "product": "100W"}, "SolarSaga 9"]}],
}


def spec_table(rows: list[tuple[str, str]], heading: str = "# SPECIFICATIONS") -> str:
    cells = "".join(f"<tr><th>{label}</th><td>{value}</td></tr>" for label, value in rows)
    return f"# INTRO\n<table><tr><th>Ignored</th><td>before the heading</td></tr></table>\n{heading}\n<table>{cells}</table>\n"


def target(model: str, region: str, lang: str) -> dict:
    return {"model": model, "region": region, "lang": lang, "route": f"{model}/{region}/{lang}/md",
            "manual": f"manual_{lang}.md", "built_at": "2026-10-01T00:00:00+00:00"}


class SpecParsingTests(unittest.TestCase):
    def test_the_table_after_the_spec_heading_is_read_as_label_value_pairs(self):
        markup = spec_table([("Capacity", "1024 Wh (20Ah/51.2V)"), ("Weight", "About<br/>10.6 kg")])
        self.assertEqual(spec_pairs(markup), [("Capacity", "1024 Wh (20Ah/51.2V)"), ("Weight", "About / 10.6 kg")])
        self.assertEqual(spec_pairs(spec_table([("容量", "96Wh")], heading="## 仕様")), [("容量", "96Wh")])

    def test_a_total_ac_row_wins_over_the_largest_port(self):
        specs = read_specs([
            ("Capacity", "3,072 Wh"), ("4 x AC Output", "120V, 20A, 2400W Rated"),
            ("Total AC Output", "3600W Rated, 7200W Surge peak"), ("AC Input", "1800W Max"),
            ("Expansion Port", "51.2V"), ("Cycle Life", "4000 cycles to 70%"), ("Weight", "About 59.5 lbs/27 kg"),
        ])
        self.assertEqual((specs["wh"], specs["ac"], specs["surge"]), (3072.0, 3600.0, 7200.0))
        self.assertEqual((specs["cycles"], specs["kg"], specs["expansion"]), (4000, 27.0, True))

    def test_japanese_surge_is_not_read_as_the_rated_output(self):
        specs = read_specs([("定格容量", "20Ah (1024Wh)"), ("AC出力", "100V，8A，800W，瞬間最大1600W"),
                            ("サイズ＆重量", "約600 mm (約10.5 kg）")])
        self.assertEqual((specs["wh"], specs["ac"], specs["surge"], specs["kg"]), (1024.0, 800.0, 1600.0, 10.5))

    def test_colon_labels_spec_rows_and_a_total_output_with_surge(self):
        rows = '<div data-source-layout="spec-row"><p>Capacity:</p><p>Lithium-ion 20.4Ah/43.2V DC(881Wh)</p></div>'
        self.assertEqual(spec_pairs("## TECHNICAL SPECIFICATIONS\n" + rows), [("Capacity", "Lithium-ion 20.4Ah/43.2V DC(881Wh)")])
        specs = read_specs(spec_pairs(spec_table([("容量：", "6.2Ah / 16V DC 99.2Wh"),
                                                  ("Total Output", "1500W Rated, 3000W Surge peak")])))
        self.assertEqual((specs["wh"], specs["ac"], specs["surge"]), (99.2, 1500.0, 3000.0))
        self.assertEqual(read_specs([("Internal Battery", "6.2Ah/16V 99.2Wh")])["wh"], 99.2)
        # A Total Output row without a surge figure (a power bank's DC total) is not read as AC.
        self.assertIsNone(read_specs([("Total Output", "100W Max")])["ac"])
        self.assertEqual(read_specs([("3 x AC Output", "1000W rated output, 2000W peak surge")])["surge"], 2000.0)

    def test_accessory_figures_and_missing_ones(self):
        specs = read_specs([("Weight", "195g±5g"), ("IP Rating", "IP68"),
                            ("Maximum Power (Pₘₐₓ)", "STC*: 42 W ± 5%"), ("Output Power", "600W Max")])
        self.assertEqual((specs["kg"], specs["ip"], specs["pv"], specs["out"]), (0.2, "IP68", 42, 600))
        self.assertEqual(read_specs([])["wh"], None)
        self.assertFalse(read_specs([])["expansion"])

    def test_numbers_and_names_read_like_the_catalog_without_its_suffixes(self):
        self.assertEqual([number(v) for v in (5040.0, 1510.4, 0.85, None)], ["5,040", "1,510.4", "0.85", "—"])
        self.assertEqual(display_name("HomePower 3000 · JHP-3000D", "JHP-3000D"), "HomePower 3000")
        self.assertEqual(display_name("SlimPower H1（JE-WH）取扱説明書", "JE-WH"), "SlimPower H1")
        self.assertEqual(display_name("Battery Pack — JBP-1", "JBP-1"), "Battery Pack")
        self.assertEqual(display_name("", "JE-X"), "JE-X")


class ConfigTests(unittest.TestCase):
    def write(self, config: dict) -> Path:
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        (Path(temp.name) / "product_matrix.json").write_text(json.dumps(config), encoding="utf-8")
        return Path(temp.name)

    def test_the_shipped_config_resolves_against_the_shipped_navigation(self):
        settings = json.loads((ASSETS / "settings.json").read_text(encoding="utf-8"))
        config = load_config(ASSETS, settings)
        self.assertTrue(all(line["title"] for line in config["lines"] + config["accessories"]))

    def test_unknown_groups_untitled_lines_and_bad_display_settings_are_rejected(self):
        broken = [
            {**CONFIG, "assign": {"JE-H": "nowhere"}},
            # A backup line takes an assigned model only with a quote from its manual, never by name alone.
            {**CONFIG, "assign": {"JE-H": "home"}},
            {**CONFIG, "assign": {"JE-H": {"line": "home", "evidence": " "}}},
            # A market variant follows a navigation-listed model and names no line of its own.
            {**CONFIG, "assign": {"JE-H": {"same_as": "JE-NOT-IN-NAVIGATION"}}},
            {**CONFIG, "assign": {"JE-H": {"same_as": "JE-A", "line": "home"}}},
            {**CONFIG, "lines": [{"id": "not-in-navigation"}]},
            {**CONFIG, "accessories": [{"id": "appliance"}]},
            {**CONFIG, "markets": {"US": {"letter": "美"}}},
            {**CONFIG, "variant_marks": ["沙金色", ""]},
        ]
        for config in broken:
            with self.subTest(config=config), self.assertRaises(ProductMatrixError):
                load_config(self.write(config), SETTINGS)

    def test_positioning_groups_add_the_config_lines_and_assignments_to_the_navigation(self):
        config = {**CONFIG, "assign": {**CONFIG["assign"], "JX-Q": {"same_as": "JE-A"}, "JE-A": "solar"}}
        # The evidence line keeps JE-H (no manual is read here); a navigation-listed model keeps its own group.
        self.assertEqual(positioning_groups(self.write(config), SETTINGS),
                         {"appliance": {"JE-A", "JX-Q"}, "solar": {"JS-S"}, "home": {"JE-H"}})

    def test_positioning_groups_report_any_unusable_config_as_a_matrix_error(self):
        for raw in ("{not json", "[]", json.dumps({**CONFIG, "assign": ["JE-H"]}), None):
            with self.subTest(raw=raw), self.assertRaises(ProductMatrixError):
                folder = self.write(CONFIG)
                if raw is None:
                    (folder / "product_matrix.json").unlink()
                else:
                    (folder / "product_matrix.json").write_text(raw, encoding="utf-8")
                positioning_groups(folder, SETTINGS)


class MatrixContextTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        paths = Paths(self.root)
        paths.data_dir.mkdir()
        (paths.data_dir / "model_capabilities.csv").write_text(CAPABILITIES, encoding="utf-8")
        (paths.data_dir / "model_languages.csv").write_text(LANGUAGES, encoding="utf-8")
        self.assets = self.root / "assets"
        self.assets.mkdir()
        (self.assets / "product_matrix.json").write_text(json.dumps(CONFIG), encoding="utf-8")
        self.web = self.root / "docs" / "publish" / "web"
        targets = [target("JE-A", "EU", "en"), target("JE-A", "EU", "fr"), target("JE-A", "US", "en"),
                   target("JE-A", "JP", "ja"), target("JE-B", "JP", "ja"), target("JE-H", "US", "en"),
                   target("JS-S", "EU", "en"), target("JX-Q", "EU", "en")]
        manuals = {
            "JE-A": [("Capacity", "512 Wh"), ("AC Output", "500W Rated, 1000W Surge"), ("Weight", "5.7 kg")],
            "JE-B": [("容量：", "512Wh"), ("重量：", "約 5.5 kg")],
            "JE-H": [("Capacity", "3584 Wh"), ("Total Output", "4000W Rated, 8000W Surge"), ("Weight", "33.5 kg")],
            "JS-S": [("Maximum Power (Pmax)", "STC*: 100 W"), ("IP Rating", "IP67"), ("Weight", "3.6 kg")],
            "JX-Q": [("Weight", "1 kg")],
        }
        for item in targets:
            folder = self.web / item["route"]
            folder.mkdir(parents=True)
            body = spec_table(manuals[item["model"]])
            if item["model"] == "JE-H":
                body += ("Use Battery Pack 3, SolarSaga 100 and the transfer switch JA-SW1. "
                         "## Home circuits\nThe unit can supply backup\npower to home circuits. Next sentence.")
            (folder / item["manual"]).write_text(body, encoding="utf-8")
        self.manifest = self.root / "docs" / "publish" / "publish_manifest.json"
        self.manifest.write_text(json.dumps({"built_at": "2026-10-12T08:00:00+00:00", "targets": targets}), encoding="utf-8")
        self.catalog = [
            {"model": "JE-A", "region": "JP", "name": "ポータブル電源 500（JE-A）取扱説明書"},
            {"model": "JE-A", "region": "US", "name": "Explorer A"},
            {"model": "JE-H", "region": "US", "name": "HomePower H · JE-H"},
        ]

    def context(self, product_catalog=CATALOG):
        return matrix_context(self.root, self.web, self.manifest, self.assets, SETTINGS, self.catalog, product_catalog)

    def products(self, context=None):
        context = context or self.context()
        return {p["short"]: p for c in context["categories"] for row in c["rows"] for p in row["products"]}

    def test_one_product_per_short_name_with_its_markets_editions_and_shared_pages(self):
        context = self.context()
        self.assertEqual(context["facts"], {"products": 4, "models": 6})
        self.assertEqual((context["built_on"], context["classified_on"]), ("2026-10-12", "2026-11-06"))
        a500 = self.products(context)["A500"]
        # The model with the most markets leads; the English US manual's catalog name wins over the Japanese one.
        self.assertEqual((a500["name"], a500["key"], a500["wh_text"]), ("Explorer A", "p-A500", "512 Wh"))
        self.assertEqual((a500["regions"], a500["editions"]), (["US", "EU", "JP"], ["沙金色"]))
        self.assertEqual([row["model"] for row in a500["rows"]], ["JE-A", "JE-B", "JE-A-SG"])
        shared = a500["detail"]["rows"][2]
        self.assertEqual((shared["short"], shared["note"]), ("A500沙金色", "与 JE-A 共用美规说明书"))
        self.assertEqual(shared["docs"], [{"label": "美规", "doc": "JE-A/US/en/md/manual_en", "title": "美规：English"}])

    def test_categories_follow_the_snapshot_with_series_rows_and_capacity_tiers(self):
        categories = self.context()["categories"]
        self.assertEqual([(c["id"], c["title"], c["count"]) for c in categories],
                         [("portable", "便携电源", 1), ("category-2", "家庭备电", 1), ("category-3", "太阳能板", 1),
                          ("other", "其他", 1)])
        portable, home, solar, other = categories
        # The columns are the 容量档 a category's products use, in the snapshot's order.
        self.assertEqual((portable["tiered"], portable["columns"]), (True, ["1度以下"]))
        # A series without a product (Plus) has no row; a card sits in its 容量档.
        self.assertEqual([row["title"] for row in portable["rows"]], ["标准"])
        self.assertEqual([[p["short"] for p in cell] for cell in portable["rows"][0]["cells"]], [["A500"]])
        self.assertEqual((home["columns"], [[p["short"] for p in cell] for cell in home["rows"][0]["cells"]]),
                         (["3.6度电"], [["HP3600"]]))
        self.assertEqual((solar["tiered"], solar["columns"]), (False, ["产品"]))
        self.assertEqual((other["rows"][0]["title"], other["rows"][0]["products"][0]["short"]), ("未分类", "JX-Q"))
        self.assertEqual(portable["markets"], ["US", "EU", "JP"])

    def test_a_product_without_a_tier_goes_to_the_unstated_column(self):
        models = {**CATALOG["models"], "JE-H": {"category": "便携电源", "series": "标准", "short": "HP3600"}}
        portable = self.context({**CATALOG, "models": models})["categories"][0]
        self.assertEqual(portable["columns"], ["1度以下", "容量未注明"])
        self.assertEqual([[p["short"] for p in cell] for cell in portable["rows"][0]["cells"]], [["A500"], ["HP3600"]])

    def test_a_tier_the_manual_capacity_does_not_fit_warns(self):
        models = {**CATALOG["models"], "JE-H": {**CATALOG["models"]["JE-H"], "capacity": "1度电"}}
        context = self.context({**CATALOG, "capacity_tiers": ["1度以下", "1度电"], "models": models})
        self.assertIn("HP3600: 容量档 1度电 does not fit the 3,584 Wh its manual states", context["warnings"])
        self.assertFalse(any(message.startswith("A500") for message in context["warnings"]))
        self.assertEqual([(1000, "1度电", False), (1300, "1度电", True), (512, "1度以下", False), (1024, "1度以下", True),
                          (3584, "3.6度电", False), (2042, "2度电", False), (None, "2度电", False), (900, "大号", False)],
                         [(wh, tier, capacity_mismatch(tier, wh)) for wh, tier in
                          ((1000, "1度电"), (1300, "1度电"), (512, "1度以下"), (1024, "1度以下"), (3584, "3.6度电"),
                           (2042, "2度电"), (None, "2度电"), (900, "大号"))])

    def test_detail_columns_show_only_what_some_model_states(self):
        products = self.products()
        a500 = products["A500"]["detail"]
        self.assertEqual(a500["columns"], ["容量", "AC 额定 / 峰值", "重量"])
        self.assertEqual([row.get("figures") for row in a500["rows"][:2]],
                         [["512 Wh", "500 / 1,000 W", "5.7 kg"], ["512 Wh", "—", "5.5 kg"]])
        self.assertEqual([doc["label"] for doc in a500["rows"][0]["docs"]], ["美规", "欧规", "日规"])
        self.assertEqual(a500["rows"][0]["docs"][1]["title"], "欧规：English、Français")
        self.assertEqual(products["HP3600"]["detail"]["rows"][0]["figures"][1], "4,000 / 8,000 W")
        self.assertEqual(products["100W"]["detail"]["columns"], ["太阳能功率", "防护", "重量"])
        self.assertEqual(products["100W"]["detail"]["rows"][0]["figures"], ["STC 100 W", "IP67", "3.6 kg"])

    def test_features_come_from_the_first_model_in_the_capability_table(self):
        products = self.products()
        features = products["A500"]["detail"]["features"]
        self.assertEqual((features["model"], features["all"], features["none"]), ("JE-A", ["UPS功能"], []))
        self.assertEqual(features["some"], [{"name": "静音", "tip": "US 支持；EU 不支持"}])
        self.assertIsNone(products["HP3600"]["detail"]["features"])

    def test_pairings_link_named_products_both_ways_and_drop_what_the_manual_lost(self):
        context = self.context()
        products = self.products(context)
        named = products["HP3600"]["detail"]["pairing"]["named"]
        self.assertEqual(named, [{"label": "Battery Pack 3", "key": ""}, {"label": "Switch（JA-SW1）", "key": ""},
                                 {"label": "SolarSaga 100", "key": "p-100W"}])
        self.assertEqual(products["100W"]["detail"]["pairing"]["named_by"],
                         [{"key": "p-HP3600", "name": "HomePower H", "model": "JE-H", "label": "SolarSaga 100"}])
        self.assertIsNone(products["A500"]["detail"]["pairing"])
        self.assertTrue(any("SolarSaga 9" in message for message in context["warnings"]))

    def test_unlisted_models_and_lost_evidence_warn(self):
        config = {**CONFIG, "assign": {"JE-H": {"line": "home", "evidence": "whole-home backup"}}}
        (self.assets / "product_matrix.json").write_text(json.dumps(config), encoding="utf-8")
        warnings = self.context()["warnings"]
        self.assertTrue(any(message.startswith("JX-Q: the 产品分类 snapshot does not list it") for message in warnings))
        self.assertTrue(any("whole-home backup" in message for message in warnings))
        (self.assets / "product_matrix.json").write_text(json.dumps(CONFIG), encoding="utf-8")
        self.assertFalse(any("evidence" in message or "home circuits" in message for message in self.context()["warnings"]))

    def test_a_general_guide_is_no_product_and_shows_under_the_products_it_covers(self):
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        manifest["targets"] += [target("JS-G", "JP", "ja"), target("JE-A-QG", "US", "en")]
        self.manifest.write_text(json.dumps(manifest), encoding="utf-8")
        for route in ("JS-G/JP/ja/md", "JE-A-QG/US/en/md"):
            folder = self.web / route
            folder.mkdir(parents=True)
            (folder / f"manual_{route.split('/')[2]}.md").write_text("# Guide\nJE-A\n", encoding="utf-8")
        snapshot = {**CATALOG, "guides": {
            "JS-G": {"kind": "通用指南", "short": "太阳能连接指南", "routes": ["JS-G/JP/ja"], "applies_to": ["JE-B", "PTB101"]},
            "JE-A-QG": {"kind": "快速指南", "short": "A500", "routes": ["JE-A-QG/US/en"], "applies_to": ["JE-A"]}}}
        context = self.context(snapshot)
        self.assertEqual(context["facts"], {"products": 4, "models": 6})
        self.assertFalse(any(message.startswith(("JS-G", "JE-A-QG")) for message in context["warnings"]))
        products = self.products(context)
        self.assertNotIn("JS-G", products)
        # A500's own quick guide comes first; its second market model JE-B is covered by the solar guide.
        self.assertEqual(products["A500"]["detail"]["guides"], [
            {"label": "快速指南", "quick": True, "docs": [
                {"label": "美规", "doc": "JE-A-QG/US/en/md/manual_en", "title": "美规：English"}]},
            {"label": "太阳能连接指南", "quick": False, "docs": [
                {"label": "日规", "doc": "JS-G/JP/ja/md/manual_ja", "title": "日规：日本語"}]}])
        self.assertEqual(products["HP3600"]["detail"]["guides"], [])
        template = Environment(loader=FileSystemLoader(ASSETS)).get_template("product_matrix.html")
        page = BeautifulSoup(template.render(**context, pathto=lambda name, *args: name, site_nav={}), "html.parser")
        link = page.select_one(".mx-detail#p-A500 a.mx-pair[href='JS-G/JP/ja/md/manual_ja']")
        self.assertEqual(link.get_text(), "太阳能连接指南日规")
        self.assertIsNone(page.select_one(".mx-detail#p-HP3600 a.mx-pair[href^='JS-G']"))

    def test_evidence_excerpt_keeps_the_sentence_and_ignores_case_and_spacing(self):
        text = "Intro. The unit can supply Backup  Power to home circuits. Next."
        self.assertEqual(evidence_excerpt(text, "backup power"), "The unit can supply Backup  Power to home circuits.")
        self.assertEqual(evidence_excerpt("x" * 300 + " backup power " + "y" * 300, "backup power")[:1], "…")
        self.assertEqual(evidence_excerpt(text, "absent"), "")
        self.assertEqual(evidence_excerpt(text, "  "), "")

    def test_without_a_manifest_or_a_snapshot_the_page_is_skipped_quietly(self):
        self.assertIsNone(self.context(None))
        self.manifest.unlink()
        self.assertIsNone(self.context())
        app = SimpleNamespace(srcdir=str(self.web))
        with patch.object(product_matrix, "repo_root", return_value=self.root), \
                patch("sphinx.util.logging.getLogger") as get_logger:
            self.assertIsNone(product_matrix_page_context(app, self.assets, SETTINGS, self.catalog, CATALOG))
        get_logger.return_value.warning.assert_not_called()

    def test_drifted_config_skips_the_page_with_a_warning(self):
        (self.assets / "product_matrix.json").write_text(json.dumps({**CONFIG, "assign": {"JE-H": "x"}}), encoding="utf-8")
        app = SimpleNamespace(srcdir=str(self.web))
        with patch.object(product_matrix, "repo_root", return_value=self.root), \
                patch("sphinx.util.logging.getLogger") as get_logger:
            self.assertIsNone(product_matrix_page_context(app, self.assets, SETTINGS, self.catalog, CATALOG))
        get_logger.return_value.warning.assert_called_once()
        self.assertIn("Product matrix page skipped", get_logger.return_value.warning.call_args.args[0])

    def test_data_warnings_are_logged_and_the_page_still_renders(self):
        app = SimpleNamespace(srcdir=str(self.web))
        with patch.object(product_matrix, "repo_root", return_value=self.root), \
                patch("sphinx.util.logging.getLogger") as get_logger:
            context = product_matrix_page_context(app, self.assets, SETTINGS, self.catalog, CATALOG)
        self.assertIsNotNone(context)
        self.assertEqual(get_logger.return_value.warning.call_count, len(context["warnings"]))

    def test_the_page_renders_tabs_cards_and_a_detail_under_each_row(self):
        template = Environment(loader=FileSystemLoader(ASSETS)).get_template("product_matrix.html")
        page = BeautifulSoup(template.render(**self.context(), pathto=lambda name, *args: name, site_nav={}),
                             "html.parser")
        self.assertEqual([(a["href"], a.get_text()) for a in page.select(".mx-tabs a")],
                         [("#cat-portable", "便携电源1"), ("#cat-category-2", "家庭备电1"),
                          ("#cat-category-3", "太阳能板1"), ("#cat-other", "其他1")])
        card = page.select_one('.mx-prod[data-product="p-A500"]')
        self.assertEqual((card["href"], card["aria-expanded"]), ("#p-A500", "false"))
        self.assertEqual(card.select_one(".mx-code").get_text(), "A500")
        self.assertEqual([i.get_text() for i in card.select(".mx-mks i")], ["美", "欧", "日"])
        self.assertEqual(card.select_one("em").get_text(), "+沙金色")
        # The detail follows its series row inside the grid, and links each market's manual.
        detail = page.select_one(".mx-detail#p-A500")
        self.assertIn("mx-row", detail.find_previous_sibling("div")["class"])
        self.assertEqual([th.get_text() for th in detail.select("thead th")],
                         ["型号", "简称", "容量", "AC 额定 / 峰值", "重量", "说明书"])
        self.assertEqual(detail.select_one("td.is-note")["colspan"], "3")
        self.assertEqual(detail.select_one(".mx-doc")["href"], "JE-A/US/en/md/manual_en")
        self.assertEqual(detail.select_one("[data-close]")["href"], "#cat-portable")
        paired = page.select_one(".mx-detail#p-100W .mx-dbox")
        self.assertEqual(paired.select_one("a.mx-pair")["data-product"], "p-HP3600")
        self.assertIn("HomePower H 的说明书写到「SolarSaga 100」", paired.get_text())
        self.assertIsNone(page.select_one("#capabilities, #specs, #pairings, .pm-filter"))


if __name__ == "__main__":
    unittest.main()
