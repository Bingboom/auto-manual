from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from tools.idml import ir_projection
from tools.manual_ir import build_manual_ir
from tools.render_contract import (
    layout_tokens_sha256,
    load_layout_token_layers,
)


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "tests" / "fixtures" / "idml_bundle"
DATA = ROOT / "tests" / "fixtures" / "phase2"


class IdmlIRProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ir = build_manual_ir(
            root=ROOT, bundle_root=BUNDLE, model="JE-1000F", region="US",
            lang="en", source="test", data_root=DATA)

    def test_fixture_satisfies_same_source_contract(self) -> None:
        self.assertEqual([], ir_projection.same_source_issues(self.ir))
        spec = ir_projection.spec_page_data(self.ir, "en")
        lcd = ir_projection.lcd_page_data(
            self.ir, "en", root=ROOT, data_root=DATA)
        symbols = ir_projection.symbol_page_data(
            self.ir, "en", root=ROOT, data_root=DATA)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(lcd)
        self.assertIsNotNone(symbols)
        assert spec is not None and lcd is not None and symbols is not None
        self.assertEqual(16, sum(len(section["rows"]) for section in spec.sections))
        self.assertEqual(26, len(lcd.rows))
        self.assertEqual("①", lcd.rows[0]["no"])
        self.assertEqual(4, len(symbols.signals))
        self.assertEqual(
            ["warning", "caution", "note", "tips"],
            [row["signal_key"] for row in symbols.signals],
        )
        self.assertEqual(11, len(ir_projection.trouble_rows(self.ir, "en")))

    def test_specifications_filename_alias_keeps_semantic_spec_page(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / "rst"
            page_dir = bundle / "page"
            page_dir.mkdir(parents=True)
            source = BUNDLE / "page" / "spec_en.rst"
            target = page_dir / "specifications_en.rst"
            target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            (bundle / "index.rst").write_text(
                ".. include:: page/specifications_en.rst\n",
                encoding="utf-8",
            )
            ir = build_manual_ir(
                root=ROOT,
                bundle_root=bundle,
                model="JE-1000F",
                region="US",
                lang="en",
                source="test",
                data_root=DATA,
            )

        spec = ir_projection.spec_page_data(ir, "en")
        self.assertIsNotNone(spec)
        assert spec is not None
        self.assertEqual("SPECIFICATIONS", spec.title)

    def test_bp_slot_filename_aliases_keep_lcd_and_symbols_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / "rst"
            page_dir = bundle / "page"
            page_dir.mkdir(parents=True)
            aliases = {
                "lcd_icons_en.rst": "lcd_display_en.rst",
                "symbols_en.rst": "symbol_meaning_en.rst",
            }
            includes = []
            for source_name, target_name in aliases.items():
                source = BUNDLE / "page" / source_name
                target = page_dir / target_name
                target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
                includes.append(f".. include:: page/{target_name}")
            (bundle / "index.rst").write_text(
                "\n".join(includes) + "\n",
                encoding="utf-8",
            )
            ir = build_manual_ir(
                root=ROOT,
                bundle_root=bundle,
                model="JBP-2000B",
                region="US",
                lang="en",
                source="test",
                data_root=DATA,
            )

        lcd = ir_projection.lcd_page_data(
            ir, "en", root=ROOT, data_root=DATA,
        )
        symbols = ir_projection.symbol_page_data(
            ir, "en", root=ROOT, data_root=DATA,
        )
        self.assertIsNotNone(lcd)
        self.assertIsNotNone(symbols)
        assert lcd is not None and symbols is not None
        self.assertEqual(26, len(lcd.rows))
        self.assertEqual(4, len(symbols.signals))

    def test_empty_optional_asset_reference_stays_empty(self) -> None:
        self.assertEqual(
            "",
            ir_projection._asset_path(ROOT, DATA, "lcd_icons", ""),
        )

    def test_idml_tag_selects_editable_semantics_over_raw_latex(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / "rst"
            page_dir = bundle / "page"
            page_dir.mkdir(parents=True)
            (bundle / "index.rst").write_text(
                ".. include:: page/overview_en.rst\n",
                encoding="utf-8",
            )
            (page_dir / "overview_en.rst").write_text(
                ".. only:: latex and not idml\n\n"
                "   .. raw:: latex\n\n"
                "      \\section{OPAQUE LATEX}\n\n"
                ".. only:: not latex or idml\n\n"
                "   EDITABLE OVERVIEW\n"
                "   =================\n\n"
                "   Editable body copy.\n",
                encoding="utf-8",
            )
            ir = build_manual_ir(
                root=ROOT,
                bundle_root=bundle,
                model="JBP-2000B",
                region="US",
                lang="en",
                source="test",
                data_root=DATA,
            )

        payloads = [
            block.payload
            for page in ir.pages
            for block in page.blocks
        ]
        self.assertIn("EDITABLE OVERVIEW", payloads)
        self.assertIn("Editable body copy.", payloads)
        self.assertNotIn("OPAQUE LATEX", payloads)

    def test_idml_only_expression_selects_one_parenthesized_branch(self) -> None:
        from tools.idml_rst_extract import _only_matches

        tags = {"latex", "idml"}
        self.assertTrue(_only_matches("latex or idml", tags))
        self.assertFalse(_only_matches("not (latex or idml)", tags))

    def test_multilingual_plural_notes_project_as_shared_callout_components(self) -> None:
        labels = {
            "en": "NOTES",
            "fr": "REMARQUES",
            "es": "OBSERVACIONES",
        }
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / "rst"
            page_dir = bundle / "page"
            page_dir.mkdir(parents=True)
            includes = []
            for language, label in labels.items():
                name = f"connections_{language}.rst"
                includes.append(f".. include:: page/{name}")
                (page_dir / name).write_text(
                    "CONNECTIONS\n===========\n\n"
                    ".. list-table::\n"
                    "   :header-rows: 0\n"
                    "   :widths: 12 88\n\n"
                    f"   * - **{label}**\n"
                    "     -\n"
                    "       - First source-authored item.\n"
                    "       - Second source-authored item.\n",
                    encoding="utf-8",
                )
            (bundle / "index.rst").write_text(
                "\n".join(includes) + "\n",
                encoding="utf-8",
            )
            ir = build_manual_ir(
                root=ROOT,
                bundle_root=bundle,
                model="JBP-2000B",
                region="US",
                lang="en",
                source="test",
                data_root=DATA,
            )

        components = {
            page.language: [
                block.payload for block in page.blocks
                if block.kind == "component"
            ]
            for page in ir.pages
        }
        self.assertEqual(set(labels), set(components))
        for language, label in labels.items():
            with self.subTest(language=language):
                self.assertEqual(1, len(components[language]))
                payload = components[language][0]
                self.assertEqual("notice", payload["kind"])
                self.assertEqual(label, payload["label"])
                self.assertEqual("note", payload["variant"])
                self.assertTrue(payload["list"])
                self.assertEqual(
                    ["First source-authored item.", "Second source-authored item."],
                    payload["texts"],
                )

    def test_bp_connections_keep_source_pdf_notice_labels(self) -> None:
        from tools.idml.oppanel import transform
        from tools.idml_rst_extract import extract_page

        expected = {
            "en": ["CAUTION", "NOTES"],
            "fr": ["Important", "Remarques"],
            "es": ["PRECAUCIÓN", "Observaciones"],
        }
        for language, labels in expected.items():
            with self.subTest(language=language):
                page = (
                    ROOT / "docs" / "templates" / "page_bp" / language
                    / "04_connections.rst"
                )
                blocks = transform(extract_page(page, {"latex"}).blocks)
                specs = [
                    json.loads(payload)
                    for kind, payload in blocks
                    if kind == "component"
                ]
                self.assertEqual(labels, [spec["label"] for spec in specs])

    def test_same_source_ir_keeps_skipped_raw_report_only_before_plan_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / "rst"
            page_dir = bundle / "page"
            page_dir.mkdir(parents=True)
            (bundle / "index.rst").write_text(
                ".. include:: page/prose.rst\n", encoding="utf-8"
            )
            (page_dir / "prose.rst").write_text(
                "PROSE\n=====\n\n"
                ".. raw:: latex\n\n"
                "   \\UnsupportedRawBlock{value}\n",
                encoding="utf-8",
            )

            ir = ir_projection.build_same_source_ir(
                root=ROOT,
                bundle_root=bundle,
                model="UNAPPROVED-MODEL",
                region="US",
                lang="en",
                data_root=DATA,
            )

        self.assertEqual(1, sum(page.skipped_raw for page in ir.pages))

    def test_same_source_ir_hashes_the_layout_layers_consumed_by_idml(self) -> None:
        base = ROOT / "data" / "layout_params.csv"
        overlay = ROOT / "data" / "layout_params.idml-compact.csv"

        ir = ir_projection.build_same_source_ir(
            root=ROOT,
            bundle_root=BUNDLE,
            model="JE-1000F",
            region="US",
            lang="en",
            data_root=DATA,
            layout_params_csv=base,
            layout_param_overlays=(overlay,),
        )

        self.assertEqual(
            layout_tokens_sha256(load_layout_token_layers(base, (overlay,))),
            ir.layout_params_sha256,
        )

    def test_lcd_projection_preserves_source_numbering_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / "rst"
            page_dir = bundle / "page"
            page_dir.mkdir(parents=True)
            (bundle / "index.rst").write_text(
                ".. include:: page/lcd_icons_en.rst\n", encoding="utf-8")
            (page_dir / "lcd_icons_en.rst").write_text(
                "LCD DISPLAY\n===========\n\n"
                ".. raw:: latex\n\n"
                "   \\begin{HBLcdIconTable}\n"
                "   \\HBLcdIconRow{22}{}{Energy Saving Mode}{Description.}\n"
                "   \\HBLcdIconRow{27}{}{Remaining Discharge Time}{Description.}\n"
                "   \\end{HBLcdIconTable}\n",
                encoding="utf-8",
            )
            ir = build_manual_ir(
                root=ROOT, bundle_root=bundle, model="JE-1000F", region="US",
                lang="en", source="test", data_root=DATA)
            lcd = ir_projection.lcd_page_data(
                ir, "en", root=ROOT, data_root=DATA)

        self.assertIsNotNone(lcd)
        assert lcd is not None
        self.assertEqual(["㉒", "㉗"], [row["no"] for row in lcd.rows])

    def test_lcd_projection_applies_approved_presentation_without_mutating_source(self) -> None:
        plan = {
            "idml_contract": {
                "editable_components": {
                    "lcd_icon_table": {
                        "icon_size_pt_by_language": {
                            "en": 14.2,
                            "fr": 13.8,
                            "es": 13.8,
                        },
                        "row_presentation": [
                            {
                                "source_no": "22",
                                "display_no": "21",
                                "row_height_pt_by_language": {
                                    "en": 33.078,
                                    "fr": 37.75,
                                    "es": 40.384,
                                },
                            },
                            {
                                "source_no": "27",
                                "display_no": "22",
                                "number_row_span": 2,
                                "typography_role": "dense",
                                "row_height_pt_by_language": {
                                    "en": 23.094,
                                    "fr": 16.306,
                                    "es": 16.306,
                                },
                            },
                        ],
                    },
                },
            },
        }
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / "rst"
            page_dir = bundle / "page"
            page_dir.mkdir(parents=True)
            (bundle / "index.rst").write_text(
                ".. include:: page/lcd_icons_en.rst\n", encoding="utf-8")
            (page_dir / "lcd_icons_en.rst").write_text(
                "LCD DISPLAY\n===========\n\n"
                ".. raw:: latex\n\n"
                "   \\begin{HBLcdIconTable}\n"
                "   \\HBLcdIconRow{27}{}{Remaining Discharge Time}{Last.}\n"
                "   \\HBLcdIconRow{22}{}{Energy Saving Mode}{First.}\n"
                "   \\end{HBLcdIconTable}\n",
                encoding="utf-8",
            )
            ir = build_manual_ir(
                root=ROOT, bundle_root=bundle, model="JE-1000F", region="US",
                lang="en", source="test", data_root=DATA)
            lcd = ir_projection.lcd_page_data(
                ir, "en", root=ROOT, data_root=DATA, reference_plan=plan)

        self.assertIsNotNone(lcd)
        assert lcd is not None
        self.assertEqual(["㉑", "㉒"], [row["no"] for row in lcd.rows])
        self.assertEqual(["22", "27"], [row["source_no"] for row in lcd.rows])
        self.assertEqual("2", lcd.rows[1]["number_row_span"])
        self.assertEqual("dense", lcd.rows[1]["typography_role"])
        self.assertEqual("33.078", lcd.rows[0]["row_height_pt"])
        self.assertEqual("23.094", lcd.rows[1]["row_height_pt"])
        self.assertEqual(["14.2", "14.2"], [row["icon_size_pt"] for row in lcd.rows])

    def test_projected_pages_preserve_source_order_and_layout_markers(self) -> None:
        pages = ir_projection.project_pages(self.ir, BUNDLE)
        self.assertEqual(10, len(pages))
        self.assertEqual("00_preface.rst", pages[0].path.name)
        safety = next(page for page in pages if page.path.name == "safety_en.rst")
        self.assertTrue(safety.twocol)
        self.assertFalse(any(kind == "data" for page in pages for kind, _ in page.blocks))

    def test_production_export_does_not_call_phase2_content_loaders(self) -> None:
        import tools.export_idml as exporter

        def forbidden(*_args, **_kwargs):
            raise AssertionError("production IDML re-read phase2 content")

        with tempfile.TemporaryDirectory() as td, patch.object(
            exporter, "load_spec_sections", forbidden
        ), patch.object(exporter, "load_spec_annotations", forbidden), patch.object(
            exporter, "load_lcd_rows", forbidden
        ), patch.object(exporter, "load_symbols_rows", forbidden), patch.object(
            exporter, "load_trouble_rows", forbidden
        ), patch.object(
            exporter.sys, "argv", [
                "export_idml.py", "--model", "JE-1000F", "--region", "US",
                "--lang", "en", "--data-root", str(DATA),
                "--bundle-root", str(BUNDLE), "--out", str(Path(td) / "manual.idml"),
            ]
        ):
            self.assertEqual(0, exporter.main())

    def test_production_export_keeps_overview_and_back_cover_native(self) -> None:
        import tools.export_idml as exporter

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "rst"
            page_dir = bundle / "page"
            page_dir.mkdir(parents=True)
            (bundle / "index.rst").write_text(
                ".. include:: page/03_product_overview_placeholder.rst\n"
                ".. include:: page/99_back_cover.rst\n",
                encoding="utf-8",
            )
            (page_dir / "03_product_overview_placeholder.rst").write_text(
                "PRODUCT OVERVIEW\n"
                "================\n\n"
                "FRONT VIEW\n"
                "----------\n\n"
                ".. list-table::\n"
                "   :header-rows: 0\n\n"
                "   * - **POWER Button**\n"
                "     - **Handle**\n",
                encoding="utf-8",
            )
            (page_dir / "99_back_cover.rst").write_text(
                ".. raw:: latex\n\n"
                "   \\HBBackCoverPage{SOURCE COMPANY}{Source address}{Source phone}"
                "{source@example.com}{www.example.com}\n",
                encoding="utf-8",
            )
            out = root / "manual.idml"
            with patch.object(
                exporter.sys,
                "argv",
                [
                    "export_idml.py",
                    "--model",
                    "TEST-MODEL",
                    "--region",
                    "US",
                    "--lang",
                    "en",
                    "--data-root",
                    str(DATA),
                    "--bundle-root",
                    str(bundle),
                    "--out",
                    str(out),
                ],
            ):
                self.assertEqual(0, exporter.main())

            with zipfile.ZipFile(out) as zf:
                package_xml = "\n".join(
                    zf.read(name).decode("utf-8")
                    for name in zf.namelist()
                    if name.endswith(".xml")
                )

        self.assertNotIn("product_overview-", package_xml)
        self.assertNotIn("back_cover-", package_xml)
        self.assertIn("PRODUCT OVERVIEW", package_xml)
        self.assertIn("POWER Button", package_xml)
        self.assertIn("<Table ", package_xml)
        self.assertIn("SOURCE COMPANY", package_xml)
        self.assertIn("Source address", package_xml)
        self.assertIn("Source phone", package_xml)
        self.assertIn("source@example.com", package_xml)
        self.assertIn("www.example.com", package_xml)

    def test_reference_page_count_gate_rejects_silent_export_drift(self) -> None:
        # parity is a hard gate only under an APPROVED plan (2026-07-21 scope
        # change; the measured fallback case lives in
        # ReferencePageCountGateScopeTests)
        plan = {"physical_page_count": 60, "plan_source": "approved-reference"}

        self.assertEqual(
            [],
            ir_projection.reference_page_count_issues(plan, 60),
        )
        self.assertEqual(
            ["emitted 52 pages but the reference plan requires 60"],
            ir_projection.reference_page_count_issues(plan, 52),
        )
        self.assertEqual(
            [],
            ir_projection.reference_page_count_issues(None, 52),
        )


class ReferencePageCountGateScopeTests(unittest.TestCase):
    """2026-07-21: exact physical parity binds only APPROVED plans; the
    measured LaTeX fallback compares two composition engines and must not
    hard-fail (writer 63 vs latex 61 at 100% source match, live case)."""

    def test_fallback_plan_mismatch_is_not_an_issue(self) -> None:
        plan = {"physical_page_count": 61}
        self.assertEqual(
            [], ir_projection.reference_page_count_issues(plan, 63))

    def test_approved_plan_mismatch_still_fails(self) -> None:
        plan = {"physical_page_count": 61, "plan_source": "approved-reference"}
        issues = ir_projection.reference_page_count_issues(plan, 63)
        self.assertEqual(1, len(issues))
        self.assertIn("61", issues[0])

    def test_approved_plan_match_passes(self) -> None:
        plan = {"physical_page_count": 63, "plan_source": "approved-reference"}
        self.assertEqual(
            [], ir_projection.reference_page_count_issues(plan, 63))

    def test_none_plan_passes(self) -> None:
        self.assertEqual(
            [], ir_projection.reference_page_count_issues(None, 63))


if __name__ == "__main__":
    unittest.main()
