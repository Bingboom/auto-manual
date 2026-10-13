from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools.rtd import product_matrix
from tools.rtd.portal import ASSETS
from tools.rtd.product_matrix import (
    ProductMatrixError, display_name, evidence_excerpt, load_config, matrix_context, number,
    product_matrix_page_context, read_specs, spec_pairs,
)
from tools.utils.path_utils import Paths

CAPABILITIES = "Document_key,Project,UPS功能,静音充电\nJE-A_EU,P1,TRUE,FALSE\nJE-A_US,P1,TRUE,TRUE\nJE-Z_JP,P2,FALSE,FALSE\n"
LANGUAGES = "Document_key,Project,languages,notes\nJE-A_EU,P1,en;fr,note\n"
SETTINGS = {"navigation": {
    "needs": [{"id": "appliance", "title": "通用电器供电", "models": ["JE-A"]}],
    "ecosystem": [{"id": "solar", "title": "太阳能补能", "models": ["JS-S"]}],
}}
CONFIG = {
    "region_order": ["US", "EU", "JP"], "language_order": ["en", "ja"],
    "lines": [{"id": "appliance"}, {"id": "home", "title": "家庭备电", "evidence": True}],
    "accessories": [{"id": "solar"}],
    "assign": {"JE-H": {"line": "home", "evidence": "backup power to home circuits"}},
    "names": {"JS-S": "Panel S"}, "notes": {},
    "tiers": [{"label": "small", "below": 800}, {"label": "large"}],
    "capability_labels": {"静音充电": "静音"},
    "companions": [
        {"title": "无独立说明书", "name": "Switch", "model": "JA-SW1", "spec": "约 10 kg", "source": "JE-H"},
        {"title": "无独立说明书", "name": "Gone", "model": "JA-GONE", "spec": "约 1 kg", "source": "JE-H"},
    ],
    "pairings": [{"model": "JE-H", "parts": ["Battery Pack 3", {"label": "Switch（JA-SW1）", "match": "JA-SW1"}],
                  "solar": ["SolarSaga 9"]}],
    "footnotes": ["顺序说明"],
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

    def test_unknown_groups_untitled_lines_and_open_tiers_are_rejected(self):
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
            {**CONFIG, "tiers": [{"label": "only", "below": 100}]},
        ]
        for config in broken:
            with self.subTest(config=config), self.assertRaises(ProductMatrixError):
                load_config(self.write(config), SETTINGS)


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
        targets = [target("JE-A", "EU", "en"), target("JE-A", "US", "en"), target("JE-A", "JP", "ja"),
                   target("JE-H", "US", "en"), target("JS-S", "EU", "en"), target("JX-Q", "EU", "en")]
        manuals = {
            "JE-A": [("Capacity", "512 Wh"), ("AC Output", "500W Rated, 1000W Surge"), ("Weight", "5.7 kg")],
            "JE-H": [("Capacity", "3584 Wh"), ("Total AC Output", "4000W Rated, 8000W Surge"), ("Weight", "33.5 kg")],
            "JS-S": [("Maximum Power (Pmax)", "STC*: 100 W"), ("IP Rating", "IP67"), ("Weight", "3.6 kg")],
            "JX-Q": [("Weight", "1 kg")],
        }
        for item in targets:
            folder = self.web / item["route"]
            folder.mkdir(parents=True)
            body = spec_table(manuals[item["model"]])
            if item["model"] == "JE-H":
                body += ("Use Battery Pack 3 and the transfer switch JA-SW1. "
                         "## Home circuits\nThe unit can supply backup\npower to home circuits. Next sentence.")
            (folder / item["manual"]).write_text(body, encoding="utf-8")
        self.manifest = self.root / "docs" / "publish" / "publish_manifest.json"
        self.manifest.write_text(json.dumps({"built_at": "2026-10-12T08:00:00+00:00", "targets": targets}), encoding="utf-8")
        self.catalog = [
            {"model": "JE-A", "region": "JP", "name": "ポータブル電源 500（JE-A）取扱説明書"},
            {"model": "JE-A", "region": "US", "name": "Explorer A"},
            {"model": "JE-H", "region": "US", "name": "HomePower H · JE-H"},
        ]

    def context(self):
        return matrix_context(self.root, self.web, self.manifest, self.assets, SETTINGS, self.catalog)

    def test_products_are_placed_by_line_and_capacity_tier(self):
        context = self.context()
        self.assertEqual(context["facts"], {"models": 4, "routes": 6, "energy": 2, "accessories": 2, "pending": 1})
        self.assertEqual(context["built_on"], "2026-10-12")
        self.assertEqual(context["markets"], ["US", "EU", "JP"])
        self.assertEqual(context["tiers"], ["small", "large"])
        appliance, home = context["lines"]
        card = appliance["cells"][0][0]
        # The English US manual and its catalog name win over the Japanese one.
        self.assertEqual((card["name"], card["regions"], card["inferred"]), ("Explorer A", ["US", "EU", "JP"], False))
        self.assertEqual(card["facts"], ["512 Wh", "AC 500 W", "5.7 kg"])
        self.assertEqual(card["source"], "JE-A/US/en/md（en）")
        self.assertEqual(home["cells"][1][0]["model"], "JE-H")
        self.assertTrue(home["cells"][1][0]["inferred"])
        self.assertEqual(home["cells"][1][0]["name"], "HomePower H")

    def test_a_backup_line_shows_the_manual_sentence_that_places_a_model_there(self):
        card = self.context()["lines"][1]["cells"][1][0]
        # The quote widens to its sentence; a heading right before it stays as context.
        self.assertEqual((card["model"], card["basis"]),
                         ("JE-H", "Home circuits The unit can supply backup power to home circuits."))

    def test_without_its_quote_in_the_manual_a_model_leaves_the_backup_line(self):
        config = {**CONFIG, "assign": {"JE-H": {"line": "home", "evidence": "whole-home backup"}}}
        (self.assets / "product_matrix.json").write_text(json.dumps(config), encoding="utf-8")
        context = self.context()
        self.assertEqual(sum(len(cell) for cell in context["lines"][1]["cells"]), 0)
        others = {group["title"]: group for group in context["accessories"]}["其他"]
        self.assertIn("JE-H", [card["model"] for card in others["cards"]])
        self.assertTrue(any("whole-home backup" in message for message in context["warnings"]))

    def test_a_market_variant_takes_the_line_of_the_same_product(self):
        config = {**CONFIG, "assign": {**CONFIG["assign"], "JX-Q": {"same_as": "JE-A"}}}
        (self.assets / "product_matrix.json").write_text(json.dumps(config), encoding="utf-8")
        specs = {row["model"]: row for row in self.context()["specs"]}
        self.assertEqual(specs["JX-Q"]["line"], "通用电器供电")
        loaded = load_config(self.assets, SETTINGS)
        warnings: list[str] = []
        products, _ = product_matrix.read_products(self.web, json.loads(self.manifest.read_text())["targets"],
                                                   self.catalog, loaded, warnings)
        self.assertEqual((products["JX-Q"]["group"], products["JX-Q"]["variant_of"]), ("appliance", "JE-A"))
        self.assertEqual((products["JE-A"]["variant_of"], products["JE-H"]["variant_of"]), ("", ""))

    def test_evidence_excerpt_keeps_the_sentence_and_ignores_case_and_spacing(self):
        text = "Intro. The unit can supply Backup  Power to home circuits. Next."
        self.assertEqual(evidence_excerpt(text, "backup power"), "The unit can supply Backup  Power to home circuits.")
        self.assertEqual(evidence_excerpt("x" * 300 + " backup power " + "y" * 300, "backup power")[:1], "…")
        self.assertEqual(evidence_excerpt(text, "absent"), "")
        self.assertEqual(evidence_excerpt(text, "  "), "")

    def test_accessories_companions_and_unplaced_products(self):
        context = self.context()
        groups = {group["title"]: group for group in context["accessories"]}
        self.assertEqual(groups["太阳能补能"]["cards"][0]["facts"], ["STC 100 W", "IP67", "3.6 kg"])
        self.assertEqual(groups["太阳能补能"]["cards"][0]["name"], "Panel S")
        self.assertEqual([card["model"] for card in groups["其他"]["cards"]], ["JX-Q"])
        self.assertEqual([card["model"] for card in groups["无独立说明书"]["cards"]], ["JA-SW1"])
        self.assertEqual(groups["无独立说明书"]["cards"][0]["facts"], ["约 10 kg", "见 HomePower H 说明书"])
        self.assertTrue(any("JX-Q" in message for message in context["warnings"]))
        self.assertTrue(any("JA-GONE" in message for message in context["warnings"]))

    def test_pairings_keep_only_what_the_manual_still_names(self):
        context = self.context()
        self.assertEqual(context["pairings"], [{"model": "JE-H", "name": "HomePower H",
                                               "parts": ["Battery Pack 3", "Switch（JA-SW1）"], "solar": []}])
        self.assertTrue(any("SolarSaga 9" in message for message in context["warnings"]))

    def test_capabilities_and_specs(self):
        context = self.context()
        self.assertEqual(context["capability_names"], ["UPS功能", "静音"])
        first, pending = context["capabilities"]
        self.assertEqual((first["model"], first["regions"]), ("JE-A", ["EU", "US"]))
        self.assertEqual([cell["state"] for cell in first["cells"]], ["all", "some"])
        self.assertIn("US 支持；EU 不支持", first["cells"][1]["tip"])
        self.assertEqual((pending["model"], pending["name"], pending["published"]), ("JE-Z", "", []))
        self.assertEqual([row["model"] for row in context["specs"]], ["JE-A", "JE-H"])
        self.assertEqual(context["specs"][1]["figures"][1], (4000.0, "4,000"))

    def test_without_a_manifest_the_page_is_skipped_quietly(self):
        self.manifest.unlink()
        self.assertIsNone(self.context())
        app = SimpleNamespace(srcdir=str(self.web))
        with patch.object(product_matrix, "repo_root", return_value=self.root), \
                patch("sphinx.util.logging.getLogger") as get_logger:
            self.assertIsNone(product_matrix_page_context(app, self.assets, SETTINGS, self.catalog))
        get_logger.return_value.warning.assert_not_called()

    def test_drifted_config_skips_the_page_with_a_warning(self):
        (self.assets / "product_matrix.json").write_text(json.dumps({**CONFIG, "assign": {"JE-H": "x"}}), encoding="utf-8")
        app = SimpleNamespace(srcdir=str(self.web))
        with patch.object(product_matrix, "repo_root", return_value=self.root), \
                patch("sphinx.util.logging.getLogger") as get_logger:
            self.assertIsNone(product_matrix_page_context(app, self.assets, SETTINGS, self.catalog))
        get_logger.return_value.warning.assert_called_once()
        self.assertIn("Product matrix page skipped", get_logger.return_value.warning.call_args.args[0])

    def test_data_warnings_are_logged_and_the_page_still_renders(self):
        app = SimpleNamespace(srcdir=str(self.web))
        with patch.object(product_matrix, "repo_root", return_value=self.root), \
                patch("sphinx.util.logging.getLogger") as get_logger:
            context = product_matrix_page_context(app, self.assets, SETTINGS, self.catalog)
        self.assertIsNotNone(context)
        self.assertEqual(get_logger.return_value.warning.call_count, len(context["warnings"]))


if __name__ == "__main__":
    unittest.main()
