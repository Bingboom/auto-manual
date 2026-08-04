from __future__ import annotations

import unittest
from pathlib import Path

from tools.idml.page_roles import (
    PageRole,
    assembly_coverage_warning,
    classify_page_role,
)


ROOT = Path(__file__).resolve().parents[1]


class IdmlPageRoleTests(unittest.TestCase):
    def test_known_semantic_pages_have_explicit_roles(self) -> None:
        cases = {
            "00_preface.rst": PageRole.PREFACE,
            "00_preface_single_language.rst": PageRole.PREFACE,
            "00_toc.rst": PageRole.TOC,
            "01_fcc.rst": PageRole.FCC,
            "01_user_maintenance_instructions.rst": PageRole.MAINTENANCE,
            "01_meaning_of_symbols.rst": PageRole.MEANING_OF_SYMBOLS,
            "02_whats_in_the_box.rst": PageRole.INBOX,
            "03_product_overview_placeholder.rst": PageRole.PRODUCT_OVERVIEW,
            "03_product_overview_je300e.rst": PageRole.PRODUCT_OVERVIEW,
            "05_operation_guide_placeholder.rst": PageRole.OPERATION_GUIDE,
            "06_ups_mode.rst": PageRole.UPS_MODE,
            "07_extra_battery.rst": PageRole.EXTRA_BATTERY,
            "charging.rst": PageRole.CHARGING,
            "08_charging_methods.rst": PageRole.CHARGING_METHODS,
            "09_storage_and_maintenance.rst": PageRole.STORAGE_MAINTENANCE,
            "10_troubleshooting.rst": PageRole.TROUBLESHOOTING_PROSE,
            "11_warranty.rst": PageRole.WARRANTY,
            "12_app_setup_placeholder.rst": PageRole.APP_SETUP,
            "99_back_cover.rst": PageRole.BACK_COVER,
            "cover_jp.rst": PageRole.COVER,
            "safety_pt-BR.rst": PageRole.SAFETY,
            "spec_zh.rst": PageRole.SPEC,
            "lcd_icons_fr.rst": PageRole.LCD,
            "symbols_es.rst": PageRole.SYMBOLS,
            "troubleshooting_en.rst": PageRole.TROUBLESHOOTING_DATA,
        }

        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(expected, classify_page_role(Path("page") / name))

    def test_merged_physical_prefix_does_not_change_role(self) -> None:
        for name, expected in (
            ("p20_01_user_maintenance_instructions.rst", PageRole.MAINTENANCE),
            ("p34_12_app_setup_placeholder.rst", PageRole.APP_SETUP),
            ("p45_08_charging_methods.rst", PageRole.CHARGING_METHODS),
        ):
            with self.subTest(name=name):
                self.assertEqual(expected, classify_page_role(Path("page") / name))

    def test_template_page_inventory_has_no_unclassified_fallback(self) -> None:
        pages = sorted(
            path
            for root in (ROOT / "docs" / "templates").glob("page*")
            for path in root.glob("*.rst")
        )
        self.assertTrue(pages)
        self.assertEqual(
            [],
            [path for path in pages if classify_page_role(path) is PageRole.UNCLASSIFIED_PROSE],
        )

    def test_unknown_page_uses_prose_fallback_with_stable_warning(self) -> None:
        source = Path("page/custom_connect_workflow.rst")
        role = classify_page_role(source)

        self.assertIs(PageRole.UNCLASSIFIED_PROSE, role)
        self.assertEqual(
            "[export-idml] WARNING: assembly coverage used unclassified prose "
            "fallback for 1 source page(s): page/custom_connect_workflow.rst",
            assembly_coverage_warning([(source, role)]),
        )

    def test_warning_is_absent_when_every_page_has_an_explicit_role(self) -> None:
        self.assertIsNone(assembly_coverage_warning([
            (Path("page/00_preface.rst"), PageRole.PREFACE),
            (Path("page/spec_en.rst"), PageRole.SPEC),
        ]))


if __name__ == "__main__":
    unittest.main()
