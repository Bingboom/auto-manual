from __future__ import annotations

import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
