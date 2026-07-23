from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from tools.idml import ir_projection
from tools.manual_ir import build_manual_ir


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
        self.assertEqual(11, len(ir_projection.trouble_rows(self.ir, "en")))

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
                        "row_presentation": [
                            {"source_no": "22", "display_no": "21"},
                            {
                                "source_no": "27",
                                "display_no": "22",
                                "number_row_span": 2,
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
