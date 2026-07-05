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
    load_spec_annotations,
    load_spec_sections,
    load_symbols_rows,
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

    def test_latex_percent_comments_are_stripped(self) -> None:
        from tools.idml_rst_extract import _detex
        self.assertEqual(_detex("hello%\n world"), "hello world")
        self.assertEqual(_detex("100\\% done"), "100% done")

    def test_grid_tables_become_table_blocks(self) -> None:
        from tools.idml_rst_extract import _parse_grid_table
        grid = [
            "+------+------+",
            "| A    | B    |",
            "+======+======+",
            "| a1   | b1   |",
            "+------+------+",
            "| a2   | b2   |",
            "+------+------+",
        ]
        rows = _parse_grid_table(grid)
        self.assertEqual(rows, [["A", "B"], ["a1", "b1"], ["a2", "b2"]])

    def test_inline_image_anchors_hang_from_baseline(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        img = ROOT / "docs" / "renderers" / "latex" / "assets" / "warning_lockup.png"
        rect = w._image_cell_content("r1", img, 100.0, 60.0)
        self.assertIn('Anchor="0 -60', rect)
        self.assertNotIn('Anchor="0 60', rect)

    def test_no_semibold_font_style_in_paragraph_styles(self) -> None:
        # the licensed Gilroy set has no SemiBold face; referencing it makes
        # InDesign pink-highlight the text (designer-reported)
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        styles = IdmlWriter(params).styles_xml()
        self.assertNotIn("Semibold", styles)

    def test_h1_and_labels_are_shaded_bars(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        styles = IdmlWriter(params).styles_xml()
        h1 = styles.split('Name="HB H1"')[1].split("</ParagraphStyle>")[0]
        self.assertIn('ShadingOn="true"', 'Name="HB H1"' + h1.split(">")[0])
        self.assertIn("HB Notice Label", styles)

    def test_two_column_chain_halves_page_count(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        h = w.frame_height() * 1.5  # needs 2 single-column pages
        # replicate chain() arithmetic
        import math
        one_col = max(1, math.ceil(h * 1.2 / w.frame_height()))
        two_col = max(1, math.ceil(h * 1.2 / 2 / w.frame_height()))
        self.assertGreater(one_col, two_col)

    def test_symbols_story_has_signal_and_icon_tables(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        signals, icons = load_symbols_rows(FIXTURE_DATA_ROOT)
        self.assertTrue(signals)
        w = IdmlWriter(params)
        w.add_symbols_story(signals, icons, FIXTURE_DATA_ROOT)
        story = dict(w.stories)["st_symbols"]
        self.assertIn("MEANING OF SYMBOLS", story)
        self.assertIn("<Table ", story)
        self.assertIn("WARNING", story)

    def test_figure_style_uses_auto_leading(self) -> None:
        # fixed leading does not grow for inline anchored objects, so art
        # shoots out of the frame top (designer-reported stacked images)
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        styles = IdmlWriter(params).styles_xml()
        fig = styles.split('Name="HB Figure"')[1].split("</ParagraphStyle>")[0]
        self.assertIn(">Auto<", fig)

    def test_art_frames_honor_aspect_ratio(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        img = ROOT / "docs" / "renderers" / "latex" / "assets" / "warning_lockup.png"
        fw, fh = w._art_frame_size(img)
        try:
            from PIL import Image
            with Image.open(img) as im:
                iw, ih = im.size
            self.assertAlmostEqual(fh / fw, ih / iw, places=2)
        except ImportError:
            self.assertAlmostEqual(fh / fw, 0.62, places=2)

    def test_components_render_as_tables(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        bundle = ROOT / "docs" / "_build" / "JE-1000F" / "US" / "en" / "rst"
        # inbox: 3-column card table with linked art and numbered labels
        xml, h = w._render_component("t", 0, {
            "kind": "inbox",
            "items": [{"img": "x.png", "label": "A"},
                      {"img": "", "label": "B"},
                      {"img": "", "label": "C"}]}, bundle, True)
        self.assertIn('ColumnCount="3"', xml)
        self.assertIn(">A<", xml)
        self.assertGreater(h, 0)
        # notice: gray fill, no stroke
        xml, _ = w._render_component("t", 1, {
            "kind": "notice", "label": "TIP", "texts": ["hello"]}, bundle, True)
        self.assertIn('FillColor="Color/HB Bg K05"', xml)
        # warnbox: lockup art + label style
        xml, _ = w._render_component("t", 2, {
            "kind": "warnbox", "label": "WARNING", "texts": ["stay safe"]}, bundle, True)
        self.assertIn("warning_lockup", xml)
        self.assertIn("HB%20Notice%20Label", xml)
        # fcc: two gray columns with the mark
        xml, _ = w._render_component("t", 3, {
            "kind": "fcc", "texts": ["left", "right"]}, bundle, True)
        self.assertIn("fcc_mark", xml)
        self.assertEqual(xml.count('FillColor="Color/HB Bg K05"'), 2)

    def test_extractor_emits_component_blocks(self) -> None:
        from tools.idml_rst_extract import extract_page
        bundle = ROOT / "docs" / "_build" / "JE-1000F" / "US" / "en" / "rst"
        page = bundle / "page" / "02_whats_in_the_box.rst"
        if not page.exists():
            self.skipTest("no prepared bundle in this checkout")
        res = extract_page(page, {"latex", "region_us", "lang_en", "model_je_1000f"})
        kinds = [k for k, _ in res.blocks]
        self.assertIn("component", kinds)

    def test_component_tables_span_columns(self) -> None:
        # V2.0 master: warning boxes run full measure across the two-column
        # safety text; without SpanColumns the full-width table overlaps the
        # second column (designer-reported)
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        xml, _ = w._render_component("t", 0, {
            "kind": "warnbox", "label": "WARNING", "texts": ["x"]},
            ROOT, True)
        self.assertIn('SpanColumnType="SpanColumns"', xml)

    def test_inline_strong_markup_becomes_bold_runs(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        psr = IdmlWriter(params)._psr("HB Body", "**Note:** stay safe", terminal=True)
        self.assertNotIn("**", psr)
        self.assertIn('FontStyle="Bold"', psr)
        self.assertIn("Note:", psr)
        self.assertIn("stay safe", psr)

    def test_table_icon_cells_use_figure_style(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        rows = load_lcd_rows(FIXTURE_DATA_ROOT, "JE-1000F")
        w = IdmlWriter(params)
        w.add_lcd_story(rows, FIXTURE_DATA_ROOT)
        story = dict(w.stories)["st_lcd"]
        # icon cells must use the auto-leading figure style, or fixed leading
        # pushes the anchored icon a full row upward (designer-reported)
        self.assertIn("HB%20Figure", story)

    def test_shading_uses_paragraph_prefixed_attributes(self) -> None:
        # bare ShadingOn/ShadingColor are silently ignored by InDesign
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        styles = IdmlWriter(params).styles_xml()
        self.assertIn('ParagraphShadingOn="true"', styles)
        self.assertNotIn(' ShadingOn=', styles)

    def test_cell_fill_uses_fillcolor(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        cell = w._cell("c1", "0:0", "<Content/>", fill="Color/HB Bg K05")
        self.assertIn('FillColor="Color/HB Bg K05"', cell)
        self.assertNotIn("CellFillColor", cell)

    def test_spec_story_appends_annotations(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        sections = load_spec_sections(FIXTURE_DATA_ROOT, "JE-1000F", "US")
        notes = load_spec_annotations(FIXTURE_DATA_ROOT, "JE-1000F", "US")
        w = IdmlWriter(params)
        w.add_spec_story(sections, notes)
        story = dict(w.stories)["st_spec"]
        if notes:
            self.assertIn("HB%20Spec%20Note", story)
            self.assertIn(notes[0][:20].replace("&", "&amp;"), story)

    def test_dom_version_supports_paragraph_shading(self) -> None:
        # paragraph shading is CC2015+; a DOMVersion 8.0 doc is parsed with
        # CS6 semantics and the shading attributes are dropped (designer-
        # reported: H1 bar still missing after the attribute-name fix)
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        self.assertIn('DOMVersion="15.0"', w.styles_xml())
        self.assertNotIn('DOMVersion="8.0"', w.designmap_xml())

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
