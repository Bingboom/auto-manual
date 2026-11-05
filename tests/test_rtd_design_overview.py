"""设计规范 概览 and cover (the 2026-11 layout): what the foundation cards, figures, component gallery and icon
wall show is read from the repository, and a showcase entry that no longer matches fails closed. The page
itself is rendered in test_rtd_portal."""
from __future__ import annotations

import unittest
from tempfile import TemporaryDirectory

from tests import test_rtd_design_system as design_tests
from tools.render_contract import load_render_contract, style_ids
from tools.rtd import portal as rtd_portal
from tools.rtd.design_overview import FOUNDATION_ART, NEUTRALS, PALETTE
from tools.rtd.design_system import DesignSystemError, design_system_context
from tools.utils.path_utils import Paths, repo_root


class OverviewContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = design_system_context(rtd_portal.ASSETS)
        cls.overview = cls.context["overview"]

    def test_the_drawings_paint_with_the_live_stylesheet(self):
        keyed = {color["key"]: color for color in self.context["colors"] if color.get("key")}
        self.assertEqual(self.overview["palette"], {key: keyed[key]["value"] for key in PALETTE})
        self.assertEqual(self.overview["brand"], {"value": keyed["dark"]["value"], "contrast": keyed["dark"]["contrast"],
                                                  "is_text": keyed["text"]["value"] == keyed["dark"]["value"]})
        self.assertEqual([(item["name"], item["value"]) for item in self.overview["neutrals"]],
                         [(keyed[key]["name"], keyed[key]["value"]) for key in NEUTRALS])
        stack = [name.strip().strip('"') for name in self.context["font_family"].split(",")]
        self.assertEqual(self.overview["fonts"], stack)

    def test_the_semantic_style_figure_counts_the_contract(self):
        styles = style_ids(load_render_contract(Paths(root=repo_root()).manual_style_contract))
        self.assertEqual(self.overview["semantic_styles"], len(styles))
        self.assertTrue(styles and all(style.startswith("HB-") for style in styles))

    def test_each_foundation_is_a_card_and_a_rule(self):
        cards = self.overview["foundations"]
        self.assertEqual({card["id"] for card in cards}, FOUNDATION_ART)
        for card in cards:
            self.assertTrue(card["title"] and card["card"] and card["caption"] and card["text"], card["id"])
        self.assertEqual(len(self.overview["principles"]), 9)
        self.assertEqual(len(self.overview["usage"]), 4)
        self.assertEqual(len(self.overview["style"]), 2)

    def test_the_showcase_shows_listed_components_and_copied_files(self):
        components = {item["id"]: item for group in self.context["component_groups"] for item in group["items"]}
        self.assertEqual(len(self.overview["gallery"]), 6)
        for shot in self.overview["gallery"]:
            self.assertEqual(shot["preview"], components[shot["id"]]["preview"])
        wall = self.overview["icons"]
        refs = [self.overview["cover_icon"], *(art["ref"] for art in self.overview["image_art"]),
                *(icon["ref"] for group in wall["groups"] for icon in group["icons"])]
        # Every file the cover, the cards and the wall show is published beside the page.
        self.assertTrue(set(refs) <= set(self.context["assets"]), set(refs) - set(self.context["assets"]))
        counted = sum(group["count"] for group in wall["groups"]) + sum(other["count"] for other in wall["others"])
        self.assertEqual(counted, self.context["asset_library"]["count"])
        for icon in (icon for group in wall["groups"] for icon in group["icons"]):
            self.assertTrue(icon["alt"])
            self.assertNotIn("<", icon["alt"])


class OverviewDriftTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.assets = design_tests.DesignSystemDriftTests.copy_assets(temp.name)
        self.content = self.assets / "design_system" / "content.yaml"
        self.text = self.content.read_text(encoding="utf-8")

    def assert_fails(self, old: str, new: str, message: str):
        self.assertIn(old, self.text)
        self.content.write_text(self.text.replace(old, new, 1), encoding="utf-8")
        with self.assertRaisesRegex(DesignSystemError, message):
            design_system_context(self.assets)

    def test_a_foundation_the_page_cannot_draw_fails(self):
        self.assert_fails("  - id: state\n", "  - id: motion\n", "foundation motion")

    def test_a_retired_showcase_component_or_file_fails(self):
        self.assert_fails("components: [callout,", "components: [callout-retired,", "callout-retired")
        self.assert_fails("fcc_mark.svg,", "fcc_mark_retired.svg,", r"symbols no longer lists \['fcc_mark_retired.svg'\]")
        self.assert_fails("cover_icon: symbols/symbol_warning_triangle.svg", "cover_icon: symbols/retired.svg",
                          "symbols/retired.svg")
        self.assert_fails("    - group: lcd\n", "    - group: lcd-retired\n", "lcd-retired")

    def test_a_missing_colour_key_or_old_schema_fails(self):
        self.assert_fails("    key: lamp_off\n", "", "lamp_off")
        self.assert_fails("schema_version: 2", "schema_version: 1", "schema_version 2")


if __name__ == "__main__":
    unittest.main()
