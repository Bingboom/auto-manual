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
            "specifications_en.rst": PageRole.SPEC,
            "lcd_icons_fr.rst": PageRole.LCD,
            "lcd_display_en.rst": PageRole.LCD,
            "symbols_es.rst": PageRole.SYMBOLS,
            "symbol_meaning_fr.rst": PageRole.SYMBOLS,
            "troubleshooting_en.rst": PageRole.TROUBLESHOOTING_DATA,
        }

        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(expected, classify_page_role(Path("page") / name))

    def test_merged_physical_prefix_does_not_change_role(self) -> None:
        for name, expected in (
            ("p20_01_user_maintenance_instructions.rst", PageRole.MAINTENANCE),
            ("p24_03_product_overview_placeholder.rst", PageRole.PRODUCT_OVERVIEW),
            ("p34_12_app_setup_placeholder.rst", PageRole.APP_SETUP),
            ("p40_03_product_overview_placeholder.rst", PageRole.PRODUCT_OVERVIEW),
            ("p45_08_charging_methods.rst", PageRole.CHARGING_METHODS),
        ):
            with self.subTest(name=name):
                self.assertEqual(expected, classify_page_role(Path("page") / name))

    def test_bp_stable_slot_filenames_have_explicit_roles(self) -> None:
        cases = {
            "back_cover.rst": PageRole.BACK_COVER,
            "box_contents_en.rst": PageRole.INBOX,
            "box_contents_es.rst": PageRole.INBOX,
            "box_contents_fr.rst": PageRole.INBOX,
            "charging_en.rst": PageRole.CHARGING,
            "charging_es.rst": PageRole.CHARGING,
            "charging_fr.rst": PageRole.CHARGING,
            "connections_en.rst": PageRole.CONNECTIONS,
            "connections_es.rst": PageRole.CONNECTIONS,
            "connections_fr.rst": PageRole.CONNECTIONS,
            "fcc_en.rst": PageRole.FCC,
            "fcc_es.rst": PageRole.FCC,
            "fcc_fr.rst": PageRole.FCC,
            "preface_important.rst": PageRole.PREFACE,
            "product_overview_en.rst": PageRole.PRODUCT_OVERVIEW,
            "product_overview_es.rst": PageRole.PRODUCT_OVERVIEW,
            "product_overview_fr.rst": PageRole.PRODUCT_OVERVIEW,
            "storage_en.rst": PageRole.STORAGE_MAINTENANCE,
            "storage_es.rst": PageRole.STORAGE_MAINTENANCE,
            "storage_fr.rst": PageRole.STORAGE_MAINTENANCE,
            "toc.rst": PageRole.TOC,
            "warranty_en.rst": PageRole.WARRANTY,
            "warranty_es.rst": PageRole.WARRANTY,
            "warranty_fr.rst": PageRole.WARRANTY,
        }
        self.assertEqual(24, len(cases))

        for name, expected in cases.items():
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

    def test_stable_slot_prefixes_do_not_capture_unknown_pages(self) -> None:
        for name in (
            "box_contents_notes.rst",
            "charging_notes.rst",
            "connections_notes.rst",
            "fcc_notes.rst",
            "lcd_display_notes.rst",
            "operation_notes.rst",
            "preface_important_notes.rst",
            "product_overview_notes.rst",
            "safety_info_notes.rst",
            "specifications_notes.rst",
            "storage_notes.rst",
            "symbol_meaning_notes.rst",
            "toc_notes.rst",
            "warranty_notes.rst",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    PageRole.UNCLASSIFIED_PROSE,
                    classify_page_role(Path("page") / name),
                )

    def test_warning_is_absent_when_every_page_has_an_explicit_role(self) -> None:
        self.assertIsNone(assembly_coverage_warning([
            (Path("page/00_preface.rst"), PageRole.PREFACE),
            (Path("page/spec_en.rst"), PageRole.SPEC),
        ]))


if __name__ == "__main__":
    unittest.main()
