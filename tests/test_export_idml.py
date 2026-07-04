from __future__ import annotations

import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.export_idml import (  # noqa: E402
    IdmlWriter,
    check_idml,
    load_layout_params,
    load_lcd_rows,
    load_spec_sections,
    load_trouble_rows,
)

FIXTURE_DATA_ROOT = ROOT / "tests" / "fixtures" / "phase2"


class ExportIdmlTests(unittest.TestCase):
    def _write_package(self) -> Path:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        sections = load_spec_sections(FIXTURE_DATA_ROOT, "JE-1000F", "US")
        self.assertTrue(sections, "fixture snapshot must yield spec sections")
        w = IdmlWriter(params)
        intro = w.add_text_story("st_intro", "Intro", [("HB Body", "hello")])
        spec = w.add_spec_story(sections)
        w.add_spread_chain(intro, 1, 0)
        w.add_spread_chain(spec, 2, 1)
        out = Path(tempfile.mkdtemp()) / "t.idml"
        w.write(out)
        return out

    def test_package_passes_structural_check(self) -> None:
        out = self._write_package()
        self.assertEqual(check_idml(out), [])

    def test_mimetype_is_first_and_stored(self) -> None:
        out = self._write_package()
        with zipfile.ZipFile(out) as zf:
            names = zf.namelist()
            self.assertEqual(names[0], "mimetype")
            self.assertEqual(zf.getinfo("mimetype").compress_type, zipfile.ZIP_STORED)

    def test_spec_story_contains_tables_and_data(self) -> None:
        out = self._write_package()
        with zipfile.ZipFile(out) as zf:
            story = zf.read("Stories/Story_st_spec.xml").decode("utf-8")
        self.assertIn("<Table ", story)
        self.assertIn("GENERAL INFO", story)
        self.assertIn("Product Name", story)

    def test_text_frames_use_path_geometry(self) -> None:
        out = self._write_package()
        with zipfile.ZipFile(out) as zf:
            for name in zf.namelist():
                if not name.startswith("Spreads/"):
                    continue
                xml = zf.read(name).decode("utf-8")
                self.assertIn("<PathGeometry>", xml)
                self.assertNotIn("GeometricBounds", xml.split("<TextFrame", 1)[-1])

    def test_paragraphs_are_delimited_by_br(self) -> None:
        out = self._write_package()
        with zipfile.ZipFile(out) as zf:
            story = zf.read("Stories/Story_st_spec.xml").decode("utf-8")
        # H1 must not fuse with the first section title
        h1_range = story.split("</ParagraphStyleRange>")[0]
        self.assertIn("<Br/>", h1_range)

    def test_missing_glyph_characters_are_replaced(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        psr = w._psr("HB Body", "16 V-60 V\u23935 A and LiFePO\u2084", terminal=True)
        self.assertNotIn("\u2393", psr)
        self.assertNotIn("\u2084", psr)
        self.assertIn(" DC ", psr)
        self.assertIn("LiFePO4", psr)

    def test_page_count_follows_content(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        sections = load_spec_sections(FIXTURE_DATA_ROOT, "JE-1000F", "US")
        w = IdmlWriter(params)
        # current fixture spec content fits one page — no trailing blanks
        pages = w.pages_for_height(w.estimate_spec_height(sections))
        self.assertEqual(pages, 1)
        # a synthetic 10x volume must request more pages
        big = [{"title": s2["title"], "rows": s2["rows"] * 10} for s2 in sections]
        self.assertGreater(w.pages_for_height(w.estimate_spec_height(big)), 1)

    def test_lcd_story_embeds_linked_images(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        rows = load_lcd_rows(FIXTURE_DATA_ROOT, "JE-1000F")
        self.assertTrue(rows)
        w = IdmlWriter(params)
        w.add_lcd_story(rows, FIXTURE_DATA_ROOT)
        story = dict(w.stories)["st_lcd"]
        self.assertIn("<Table ", story)
        self.assertIn("LinkResourceURI=", story)
        self.assertIn("Wi-Fi", story)

    def test_trouble_rows_match_model_all_and_region_lists(self) -> None:
        rows = load_trouble_rows(FIXTURE_DATA_ROOT, "JE-1000F", "US")
        self.assertTrue(rows)
        for code, measure in rows:
            self.assertTrue(code)
            self.assertTrue(measure)

    def test_prose_extraction_covers_bundle_pages(self) -> None:
        from tools.idml_rst_extract import bundle_page_order, extract_page
        bundle = ROOT / "docs" / "_build" / "JE-1000F" / "US" / "en" / "rst"
        if not bundle.is_dir():
            self.skipTest("no prepared bundle in this checkout")
        tags = {"latex", "region_us", "lang_en", "model_je_1000f"}
        pages = bundle_page_order(bundle)
        self.assertGreater(len(pages), 10)
        total = sum(len(extract_page(p, tags).blocks) for p in pages)
        self.assertGreater(total, 100)

    def test_prose_story_marks_safety_twocol(self) -> None:
        from tools.idml_rst_extract import extract_page
        bundle = ROOT / "docs" / "_build" / "JE-1000F" / "US" / "en" / "rst"
        page = bundle / "page" / "safety_en.rst"
        if not page.exists():
            self.skipTest("no prepared bundle in this checkout")
        res = extract_page(page, {"latex", "region_us", "lang_en", "model_je_1000f"})
        self.assertTrue(res.twocol)
        kinds = {k for k, _ in res.blocks}
        self.assertIn("list", kinds)

    def test_styles_map_layout_params(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        styles = w.styles_xml()
        for name in ("HB H1", "HB Body", "HB Spec Label", "HB Spec Value"):
            self.assertIn(f'Name="{name}"', styles)
        self.assertIn("Gilroy", styles)

    def test_page_geometry_is_130x185(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        self.assertAlmostEqual(w.page_w, 130.10 * 72 / 25.4, places=1)
        self.assertAlmostEqual(w.page_h, 185.10 * 72 / 25.4, places=1)


if __name__ == "__main__":
    unittest.main()
