from __future__ import annotations

import json
import sys
import tempfile
import threading
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
    split_safety_first_page,
)
from tools.idml import export_paths as idml_export_paths  # noqa: E402
from tools.idml.style_names import paragraph_style_name, paragraph_style_ref  # noqa: E402

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
            table_stories = "".join(
                zf.read(name).decode("utf-8")
                for name in zf.namelist()
                if name.startswith("Stories/Story_st_anchor_spec_")
            )
        self.assertIn("<Table ", table_stories)
        self.assertIn("GENERAL INFO", story)
        self.assertIn("Product Name", table_stories)

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

    def test_symbol_glyphs_use_fallback_font_without_text_rewrite(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        psr = w._psr(
            "HB Body",
            "16 V-60 V\u23935 A and LiFePO\u2084 \u203b \u2460",
            terminal=True,
        )
        self.assertIn("\u2393", psr)
        self.assertIn("\u2084", psr)
        self.assertIn("\u203b", psr)
        self.assertIn("\u2460", psr)
        self.assertNotIn(" DC ", psr)
        self.assertNotIn('AppliedFont="Arial Unicode MS"', psr)
        self.assertIn("<Properties><AppliedFont type=\"string\">Apple Symbols</AppliedFont></Properties>", psr)
        self.assertIn("<Content>\u2393</Content>", psr)
        self.assertIn("<Properties><AppliedFont type=\"string\">Arial Unicode MS</AppliedFont></Properties>", psr)
        self.assertIn('FontStyle="Regular"', psr)

    def test_fonts_xml_declares_symbol_fallback_font(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        fonts = IdmlWriter(params).fonts_xml()
        self.assertIn('Name="Arial Unicode MS"', fonts)
        self.assertIn('PostScriptName="ArialUnicodeMS"', fonts)
        self.assertIn('Name="Apple Symbols"', fonts)
        self.assertIn('PostScriptName="AppleSymbols"', fonts)

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
        self.assertEqual(
            [t for k, t in res.blocks if k == "layout"],
            ["twocol_start", "twocol_end", "twocol_start", "twocol_end"],
        )

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

    def test_grid_table_partial_rules_split_spanned_rows(self) -> None:
        from tools.idml_rst_extract import _parse_grid_table
        grid = [
            "+----------------+----------------+",
            "| Left           | Right          |",
            "+================+================+",
            "| left first     | right one      |",
            "| continued      +----------------+",
            "|                | right two      |",
            "+----------------+----------------+",
        ]
        rows = _parse_grid_table(grid)
        self.assertEqual(rows, [
            ["Left", "Right"],
            ["left first continued", "right one"],
            ["", "right two"],
        ])
        self.assertFalse(any("----" in cell or "|" in cell for row in rows for cell in row))

    def test_unclosed_optional_arg_does_not_hang(self) -> None:
        # A truncated `\HBNoticeBlock[warn` (no closing `]`) must not spin the
        # macro scanner forever. Run under a watchdog thread so a regression
        # fails cleanly instead of hanging the whole suite.
        from tools.idml_rst_extract import ExtractResult, _extract_raw_latex

        result = ExtractResult()
        done = threading.Event()

        def _run() -> None:
            _extract_raw_latex("\\HBNoticeBlock[warn oops no closing bracket", result)
            done.set()

        worker = threading.Thread(target=_run, daemon=True)
        worker.start()
        worker.join(timeout=5)
        self.assertTrue(done.is_set(), "extraction hung on an unclosed optional arg")

    def test_escaped_asterisk_in_json_block_stays_valid_json(self) -> None:
        # A JSON payload (table/component) carries `\*` already JSON-escaped; the
        # unescape must reach into the string values, not corrupt the envelope.
        from tools.idml_rst_extract import _unescape_rst_stars

        payload = json.dumps([["Rated power\\*", "1000 W"]], ensure_ascii=False)
        out = _unescape_rst_stars("table", payload)
        self.assertEqual(json.loads(out), [["Rated power*", "1000 W"]])

    def test_escaped_asterisk_in_prose_block_is_unescaped(self) -> None:
        from tools.idml_rst_extract import _unescape_rst_stars

        self.assertEqual(_unescape_rst_stars("body", "Rated power\\*"), "Rated power*")

    def test_grid_table_cell_with_escaped_asterisk_round_trips(self) -> None:
        # End-to-end: a grid-table cell with an escaped asterisk survives
        # extract_page as a valid table block (the #562 list-table JSON path).
        from tools.idml_rst_extract import extract_page

        grid = (
            "+----------------+--------+\n"
            "| Param          | Value  |\n"
            "+================+========+\n"
            "| Rated power\\*   | 1000 W |\n"
            "+----------------+--------+\n"
        )
        with tempfile.TemporaryDirectory() as td:
            page = Path(td) / "spec.rst"
            page.write_text(grid, encoding="utf-8")
            res = extract_page(page, {"latex"})
        tables = [json.loads(t) for k, t in res.blocks if k == "table"]
        self.assertTrue(tables)
        self.assertIn("Rated power*", [cell for row in tables[0] for cell in row])

    def test_inline_image_anchors_hang_from_baseline(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        img = ROOT / "docs" / "renderers" / "latex" / "assets" / "warning_lockup.png"
        rect = w._image_cell_content("r1", img, 100.0, 60.0)
        self.assertIn('Anchor="0 -60', rect)
        self.assertNotIn('Anchor="0 60', rect)
        self.assertIn('<AnchoredObjectSetting AnchoredPosition="InlinePosition"', rect)
        self.assertNotIn('StrokeWeight="0" AnchoredPosition=', rect)

    def test_prose_images_take_an_above_line_layout_slot(self) -> None:
        from tools.idml.components.prose_image import render_image_block

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        bundle = ROOT / "tests" / "fixtures" / "idml_bundle"
        image = ROOT / "docs" / "renderers" / "latex" / "assets" / "warning_lockup.png"
        xml, _ = render_image_block(
            image.as_posix(), w._render_context(bundle), rect_id="r2", terminal=False)
        self.assertIn('AnchoredPosition="AboveLine"', xml)
        self.assertIn('Anchor="0 0"', xml)
        self.assertNotIn('Anchor="0 -', xml)

        result = ROOT / "docs" / "templates" / "word_template" / "common_assets" / "app" / "connect_result.png"
        result_xml, height = render_image_block(
            result.as_posix(),
            w._render_context(bundle), rect_id="r3", terminal=False)
        self.assertIn(f'AnchorSpaceAbove="{height - 4:g}"', result_xml)

    def test_no_semibold_font_style_in_paragraph_styles(self) -> None:
        # the licensed Gilroy set has no SemiBold face; referencing it makes
        # InDesign pink-highlight the text (designer-reported)
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        styles = IdmlWriter(params).styles_xml()
        self.assertNotIn("Semibold", styles)

    def test_h1_and_labels_are_shaded_bars(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        styles = IdmlWriter(params).styles_xml()
        h1_name = paragraph_style_name("HB H1")
        h1 = styles.split(f'Name="{h1_name}"')[1].split("</ParagraphStyle>")[0]
        self.assertIn('ShadingOn="true"', f'Name="{h1_name}"' + h1.split(">")[0])
        self.assertIn(f'Name="{paragraph_style_name("HB Notice Label")}"', styles)
        self.assertNotIn('Name="HB H1"', styles)

    def test_two_column_chain_halves_page_count(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        h = w.frame_height() * 1.5  # needs 2 single-column pages
        # replicate chain() arithmetic
        one_col = w.pages_for_height(h)
        two_col = w.pages_for_height(h / 2)
        self.assertGreater(one_col, two_col)

    def test_chain_estimate_under_one_page_does_not_allocate_blank_page(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        self.assertEqual(w.pages_for_height(w.frame_height() * 0.95), 1)

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

    def test_symbols_icon_rows_keep_key_and_order(self) -> None:
        import csv
        tmp = Path(tempfile.mkdtemp())
        with (tmp / "symbols_blocks.csv").open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=[
                "Is_Latest", "block_type", "order", "symbol_key",
                "label_en", "text_en", "image_path",
            ])
            w.writeheader()
            w.writerow({
                "Is_Latest": "TRUE", "block_type": "table_row", "order": "1",
                "symbol_key": "warning_triangle", "label_en": "",
                "text_en": "Warning symbol", "image_path": "symbol.png",
            })
        _, icons = load_symbols_rows(tmp)
        self.assertEqual(icons[0]["symbol_key"], "warning_triangle")
        self.assertEqual(icons[0]["order"], "1")

    def test_symbols_rows_use_requested_language(self) -> None:
        signals, icons = load_symbols_rows(FIXTURE_DATA_ROOT, "fr")
        self.assertIn(
            ("AVERTISSEMENT",
             "Pratiques dangereuses pouvant entraîner des blessures graves, "
             "la mort et/ou des dommages matériels."),
            signals,
        )
        self.assertEqual(icons, [])
        self.assertFalse(any(row[0] == "WARNING" for row in signals))

    def test_symbol_signal_rows_drop_empty_meanings(self) -> None:
        import csv
        tmp = Path(tempfile.mkdtemp())
        with (tmp / "symbols_blocks.csv").open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=[
                "Is_Latest", "block_type", "order", "label_en", "text_en", "image_path",
            ])
            w.writeheader()
            w.writerow({
                "Is_Latest": "TRUE", "block_type": "signal_row", "order": "1",
                "label_en": "WARNING", "text_en": "Has text", "image_path": "",
            })
            w.writerow({
                "Is_Latest": "TRUE", "block_type": "signal_row", "order": "2",
                "label_en": "DANGER", "text_en": "", "image_path": "",
            })
        signals, icons = load_symbols_rows(tmp)
        self.assertEqual(signals, [("WARNING", "Has text")])
        self.assertEqual(icons, [])

    def test_figure_style_uses_auto_leading(self) -> None:
        # fixed leading does not grow for inline anchored objects, so art
        # shoots out of the frame top (designer-reported stacked images)
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        styles = IdmlWriter(params).styles_xml()
        figure_name = paragraph_style_name("HB Figure")
        fig = styles.split(f'Name="{figure_name}"')[1].split("</ParagraphStyle>")[0]
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
        self.assertIn(paragraph_style_ref("HB Card Number"), xml)
        self.assertIn(paragraph_style_ref("HB InBox Label"), xml)
        self.assertNotIn(paragraph_style_ref("HB Notice Label"), xml)
        self.assertGreater(h, 0)
        # notice/tip: plain left label + gray text panel; no warning icon
        xml, _ = w._render_component("t", 1, {
            "kind": "notice", "label": "TIP", "texts": ["hello"]}, bundle, True)
        # rounded parity: grey shell, equal-height white label plate, and
        # separate editable label/body stories in one anchored group.
        self.assertIn('FillColor="Color/HB Bg K05"', xml)
        self.assertIn('FillColor="Color/Paper"', xml)
        self.assertIn('ParentStory="st_anchor_notice_label_t_cmp1"', xml)
        self.assertIn('ParentStory="st_anchor_notice_body_t_cmp1"', xml)
        self.assertIn("st_anchor_notice_label_t_cmp1", dict(w.stories))
        self.assertIn("st_anchor_notice_body_t_cmp1", dict(w.stories))
        self.assertNotIn("warning_triangle", xml)
        # warnbox: triangle icon + one editable label; do not place the
        # WARNING lockup art and then print WARNING again below it.
        xml, _ = w._render_component("t", 2, {
            "kind": "warnbox", "label": "WARNING", "texts": ["stay safe"]}, bundle, True)
        self.assertIn("warning_triangle", xml)
        self.assertNotIn("warning_lockup", xml)
        self.assertIn(paragraph_style_ref("HB Title L2"), xml)
        self.assertEqual(xml.count(">WARNING<"), 1)
        xml, _ = w._render_component("t", 4, {
            "kind": "safetywarning", "texts": ["RISK OF FIRE"]}, bundle, True)
        self.assertIn("warning_triangle", xml)
        self.assertIn(paragraph_style_ref("HB Title L3"), xml)
        self.assertNotIn(">WARNING<", xml)
        xml, _ = w._render_component("t", 5, {
            "kind": "warninglead", "label": "WARNING", "texts": ["lead"]},
            bundle, True, span_columns=False, measure_w=150.0)
        self.assertIn("warning_triangle", xml)
        self.assertIn(">WARNING<", xml)
        self.assertNotIn('SpanColumnType="SpanColumns"', xml)
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
        xml, _ = w._render_component("t", 1, {
            "kind": "warninglead", "label": "WARNING", "texts": ["x"]},
            ROOT, True, span_columns=False, measure_w=150.0)
        self.assertNotIn('SpanColumnType="SpanColumns"', xml)

    def test_component_table_can_leave_outer_border_to_page_object(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        cells = [
            w._cell("c00", "0:0", w._psr("HB Spec Label", "Symbol", terminal=True)),
            w._cell("c01", "1:0", w._psr("HB Spec Label", "Meaning", terminal=True)),
            w._cell("c10", "0:1", w._psr("HB Spec Value", "WARNING", terminal=True)),
            w._cell("c11", "1:1", w._psr("HB Spec Value", "Hazard", terminal=True)),
        ]
        table = w._component_table(
            "tbl_inner_grid", [72.0, 180.0], cells, n_rows=2,
            role="data", outer_stroke=False,
        )
        c00 = table.split('Self="c00"', 1)[1].split(">", 1)[0]
        c01 = table.split('Self="c01"', 1)[1].split(">", 1)[0]
        c10 = table.split('Self="c10"', 1)[1].split(">", 1)[0]
        c11 = table.split('Self="c11"', 1)[1].split(">", 1)[0]
        self.assertIn('LeftEdgeStrokeWeight="0"', c00)
        self.assertIn('TopEdgeStrokeWeight="0"', c00)
        self.assertNotIn('RightEdgeStrokeWeight="0"', c00)
        self.assertIn('RightEdgeStrokeWeight="0"', c01)
        self.assertIn('BottomEdgeStrokeWeight="0"', c10)
        self.assertIn('RightEdgeStrokeWeight="0"', c11)
        self.assertIn('BottomEdgeStrokeWeight="0"', c11)

    def test_safetywarning_macro_keeps_distinct_component(self) -> None:
        import json
        from tools.idml_rst_extract import ExtractResult, _extract_raw_latex
        res = ExtractResult()
        _extract_raw_latex(
            r"\safetywarning{RISK OF FIRE}\HBTipBlock{TIP}{hello}",
            res,
        )
        self.assertEqual(len(res.blocks), 2)
        kind, payload = res.blocks[0]
        self.assertEqual(kind, "component")
        self.assertEqual(json.loads(payload)["kind"], "safetywarning")
        self.assertEqual(json.loads(res.blocks[1][1])["kind"], "notice")
        self.assertEqual(json.loads(res.blocks[1][1])["variant"], "tip")

    def test_upstream_page_macros_keep_same_source_semantics(self) -> None:
        import json
        from tools.idml_rst_extract import ExtractResult, _extract_raw_latex

        res = ExtractResult()
        _extract_raw_latex(r"\HBSafetyInstruction{Keep this instruction.}", res)
        _extract_raw_latex(r"\HBAppStep{2}{Connect the device}", res)
        _extract_raw_latex(r"\HBAppAsset{app.png}{ignored}{ignored}", res)

        self.assertEqual(json.loads(res.blocks[0][1])["kind"], "safetyinstruction")
        self.assertEqual(res.blocks[1], ("h2", "2 Connect the device"))
        self.assertEqual(res.blocks[2], ("image", "app.png"))

        paged = ExtractResult()
        _extract_raw_latex(
            r"\HBPageBreak{}\HBAppBody{First.}\HBPageBreak{}\HBAppBody{Second.}",
            paged,
        )
        self.assertEqual(paged.blocks, [
            ("body", "First."), ("layout", "page_break"), ("body", "Second."),
        ])

    def test_latex_false_fallback_is_not_duplicated_in_ir(self) -> None:
        from tools.idml_rst_extract import _parse_text

        text = (
            ".. only:: latex\n\n"
            "   .. raw:: latex\n\n"
            "      \\HBAppBody{Canonical copy.}\n"
            "      \\iffalse\n\n"
            "Fallback copy.\n\n"
            ".. only:: latex\n\n"
            "   .. raw:: latex\n\n"
            "      \\fi\n"
        )
        latex = _parse_text(text, {"latex"})
        fallback = _parse_text(text, {"html"})

        self.assertEqual(latex.blocks, [("body", "Canonical copy.")])
        self.assertEqual(fallback.blocks, [("body", "Fallback copy.")])

        fcc = _parse_text(
            ".. raw:: latex\n\n   \\HBFccBlock{Left copy.}{Right copy.}\n",
            {"latex"},
        )
        self.assertEqual([kind for kind, _ in fcc.blocks], ["h1", "component"])
        self.assertEqual(fcc.blocks[0], ("h1", "FCC"))

    def test_prose_flow_splits_at_reference_page_starts(self) -> None:
        from tools.idml.prose_flow import ProseFlowBuffer

        flow = ProseFlowBuffer()
        flow.add("operation", [("h1", "Operation")])
        flow.add("ups", [("h1", "UPS")])
        flow.add("charging", [("h1", "Charging")])
        emitted = []
        starts = {"operation": 10, "ups": 14, "charging": 14}

        flow.flush(
            lambda _sid, title, _blocks, _columns: emitted.append(title),
            lambda stem: stem,
            {"pages": [
                {"source_path": f"page/{stem}.rst", "latex_start_page": start}
                for stem, start in starts.items()
            ]},
        )

        self.assertEqual(emitted, ["operation", "ups + charging"])

    def test_prose_flow_merges_a_group_that_exceeds_its_page_span(self) -> None:
        from tools.idml.prose_flow import ProseFlowBuffer

        flow = ProseFlowBuffer()
        flow.add("ups", [("body", "ups"), ("body", "overflow")])
        for stem in ("methods", "storage"):
            flow.add(stem, [("body", stem)])
        emitted = []
        plan = {"pages": [
            {"source_path": "page/ups.rst", "latex_start_page": 10},
            {"source_path": "page/methods.rst", "latex_start_page": 11},
            {"source_path": "page/storage.rst", "latex_start_page": 14},
        ]}

        flow.flush(
            lambda _sid, title, _blocks, _columns: emitted.append(title),
            lambda stem: stem,
            plan,
            estimate_pages=lambda blocks, _columns: len(blocks),
        )

        self.assertEqual(emitted, ["ups + methods", "storage"])

    def test_long_troubleshooting_table_starts_on_its_second_page(self) -> None:
        from tools.idml.prose_flow import align_trouble_table

        blocks = [("h1", "Trouble"), ("body", "Intro"), ("table", "[]")]
        plan = {"pages": [
            {"source_path": "page/troubleshooting_es.rst", "latex_start_page": 54},
            {"source_path": "page/spec_es.rst", "latex_start_page": 56},
        ]}

        aligned = align_trouble_table(blocks, plan, "troubleshooting_es")

        self.assertEqual(aligned[-2], ("layout", "table_next_page"))

    def test_four_page_operation_flow_keeps_final_h2_on_last_page(self) -> None:
        from tools.idml.prose_flow import align_operation_tail

        blocks = [("h1", "Operations"), ("h2", "LCD"), ("table", "[]"),
                  ("h2", "Keys"), ("table", "[]")]
        plan = {"pages": [
            {"source_path": "page/05_operation_guide.rst", "latex_start_page": 10},
            {"source_path": "page/06_ups.rst", "latex_start_page": 14},
        ]}

        aligned = align_operation_tail(blocks, plan, "05_operation_guide")

        self.assertEqual(aligned[-3], ("layout", "page_break"))

    def test_page_break_layout_does_not_enable_two_columns(self) -> None:
        from tools.idml.ir_projection import project_pages
        from tools.manual_ir.model import ManualBlock, ManualIR, ManualPage

        block = ManualBlock("b", "page/x#b", "layout", "page_break", "h", ())
        page = ManualPage("p", "page/x", "page/x.rst", "en", "h", 0, (block,))
        ir = ManualIR("M", "US", "en", "test", ".", "h", None, "h", "h", "h", (page,), ())

        self.assertFalse(project_pages(ir, ROOT)[0].twocol)

    def test_safety_layout_markers_and_warninglead_are_preserved(self) -> None:
        import json
        from tools.idml_rst_extract import ExtractResult, _extract_raw_latex
        res = ExtractResult()
        _extract_raw_latex(r"\begin{safetytwocol}", res)
        _extract_raw_latex(r"\HBWarningLeadBlock{WARNING}{lead copy}", res)
        _extract_raw_latex(r"\end{safetytwocol}", res)
        self.assertEqual(res.blocks[0], ("layout", "twocol_start"))
        self.assertEqual(res.blocks[2], ("layout", "twocol_end"))
        self.assertEqual(json.loads(res.blocks[1][1])["kind"], "warninglead")

    def test_safety_first_page_split_stops_after_second_twocol(self) -> None:
        blocks = [
            ("h1", "IMPORTANT SAFETY INFORMATION"),
            ("layout", "twocol_start"),
            ("list", "• first"),
            ("layout", "twocol_end"),
            ("h2", "OPERATING INSTRUCTIONS"),
            ("layout", "twocol_start"),
            ("list", "• second"),
            ("layout", "twocol_end"),
            ("component", '{"kind":"warnbox","label":"WARNING","texts":["tail"]}'),
        ]
        head, tail = split_safety_first_page(blocks)
        self.assertEqual(head[-1], ("layout", "twocol_end"))
        self.assertEqual(tail[0][0], "component")

    def test_safety_page_uses_segmented_capsule_frames(self) -> None:
        import json
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        blocks = [
            ("h1", "IMPORTANT SAFETY INFORMATION"),
            ("component", json.dumps({
                "kind": "safetyinstruction",
                "texts": ["INSTRUCTIONS PERTAINING TO RISK OF FIRE"],
            })),
            ("layout", "twocol_start"),
            ("component", json.dumps({
                "kind": "warninglead",
                "label": "WARNING",
                "texts": ["Always follow these basic precautions."],
            })),
            ("list", "• Read all the instructions before using the product."),
            ("layout", "twocol_end"),
            ("h2", "OPERATING INSTRUCTIONS"),
            ("layout", "twocol_start"),
            ("body", "SAVE THESE INSTRUCTIONS"),
            ("list", "• Stop using the product immediately."),
            ("layout", "twocol_end"),
        ]
        w.add_safety_page("st_safety_en", "safety_en", blocks, ROOT, 1)
        self.assertIn("st_safety_en_top_warning", dict(w.stories))
        spread = dict(w.spreads)["sp_1"]
        self.assertEqual(spread.count("<TextFrame "), 5)
        self.assertEqual(spread.count("<Rectangle "), 3)
        self.assertEqual(spread.count('FillColor="Color/HB Brand Dark"'), 2)
        self.assertEqual(
            spread.count('AppliedObjectStyle="ObjectStyle/HB Capsule Heading"'),
            2,
        )
        import re
        title_bg = spread.split('Self="bg_st_safety_en_title"', 1)[1].split(
            "</Rectangle>", 1)[0]
        subbar_bg = spread.split('Self="bg_st_safety_en_subbar"', 1)[1].split(
            "</Rectangle>", 1)[0]
        self.assertEqual(len(re.findall(r'Anchor="[-0-9.]+ [-0-9.]+"', title_bg)), 6)
        self.assertEqual(len(re.findall(r'Anchor="[-0-9.]+ [-0-9.]+"', subbar_bg)), 8)
        self.assertIn('Self="bg_st_safety_en_warning"', spread)
        self.assertIn(
            'AppliedObjectStyle="ObjectStyle/HB Rounded Table Outer"',
            spread.split('Self="bg_st_safety_en_warning"', 1)[1].split(
                "</Rectangle>", 1)[0],
        )
        self.assertEqual(spread.count('VerticalBalanceColumns="true"'), 2)
        self.assertIn("tf_st_safety_en_section1", spread)
        self.assertIn("tf_st_safety_en_section2", spread)
        stories = dict(w.stories)
        self.assertIn("st_safety_en_subbar", stories)
        self.assertIn("OPERATING INSTRUCTIONS", stories["st_safety_en_subbar"])
        self.assertIn("SAVE THESE INSTRUCTIONS", stories["st_safety_en_section2"])

    def test_safety_symbols_page_combines_tail_maintenance_and_symbols(self) -> None:
        import json
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        tail = [
            ("component", json.dumps({
                "kind": "warnbox", "label": "WARNING", "texts": ["Grounding warning."],
            })),
            ("component", json.dumps({
                "kind": "warnbox", "label": "DANGER", "texts": ["Indoor use only."],
            })),
        ]
        maintenance = [
            ("h1", "USER MAINTENANCE INSTRUCTIONS"),
            ("body", "During the lifecycle of energy storage products."),
        ]
        signals = [("WARNING", "Hazardous practices."), ("TIP", "Helpful tips.")]
        icons = [{"figure": "", "text": f"Icon {i}"} for i in range(8)]
        w.add_safety_symbols_page(
            "st_safety_symbols", tail, maintenance, signals, icons, ROOT, 2)
        spread = dict(w.spreads)["sp_2"]
        self.assertEqual(spread.count("<TextFrame "), 8)
        self.assertEqual(spread.count("<Rectangle "), 7)
        self.assertEqual(
            spread.count('AppliedObjectStyle="ObjectStyle/HB Capsule Heading"'),
            2,
        )
        self.assertEqual(
            spread.count('AppliedObjectStyle="ObjectStyle/HB Rounded Table Outer"'),
            5,
        )
        self.assertIn('Self="bg_st_safety_symbols_tail_0"', spread)
        self.assertIn('Self="bg_st_safety_symbols_tail_1"', spread)
        self.assertIn('Self="bg_st_safety_symbols_signals"', spread)
        self.assertIn('Self="bg_st_safety_symbols_icons_left"', spread)
        self.assertIn('Self="bg_st_safety_symbols_icons_right"', spread)
        # Frames are cursor-flowed and index-named; stories keep label names.
        self.assertIn("tf_st_safety_symbols_tail_0", spread)
        self.assertIn("tf_st_safety_symbols_tail_1", spread)
        tail_frame = spread.split('Self="tf_st_safety_symbols_tail_0"', 1)[1].split(
            "</TextFrame>", 1,
        )[0]
        self.assertIn('VerticalJustification="CenterAlign"', tail_frame)
        self.assertIn("tf_st_safety_symbols_icons_left", spread)
        self.assertIn("tf_st_safety_symbols_icons_right", spread)
        import re
        maint_bg = spread.split('Self="bg_st_safety_symbols_maint_title"', 1)[1].split(
            "</Rectangle>", 1)[0]
        symbols_bg = spread.split('Self="bg_st_safety_symbols_symbols_title"', 1)[1].split(
            "</Rectangle>", 1)[0]
        self.assertEqual(len(re.findall(r'Anchor="[-0-9.]+ [-0-9.]+"', maint_bg)), 8)
        self.assertEqual(len(re.findall(r'Anchor="[-0-9.]+ [-0-9.]+"', symbols_bg)), 6)
        stories = dict(w.stories)
        self.assertIn("st_safety_symbols_tail_warning", stories)
        self.assertIn("st_safety_symbols_tail_danger", stories)
        self.assertIn(">WARNING<", stories["st_safety_symbols_tail_warning"])
        self.assertIn(
            'BaselineShift="0.68"',
            stories["st_safety_symbols_tail_warning"],
        )
        self.assertIn(">DANGER<", stories["st_safety_symbols_tail_danger"])
        self.assertIn("st_safety_symbols_signals", stories)
        self.assertIn("st_safety_symbols_icons_left", stories)
        self.assertIn("st_safety_symbols_icons_right", stories)
        self.assertIn("MEANING OF SYMBOLS", stories["st_safety_symbols_symbols_title"])
        self.assertIn("USER MAINTENANCE", stories["st_safety_symbols_maintenance_title"])
        self.assertIn("Icon 0", stories["st_safety_symbols_icons_left"])
        self.assertIn("Icon 7", stories["st_safety_symbols_icons_right"])
        self.assertIn(
            'TopEdgeStrokeWeight="0"',
            stories["st_safety_symbols_signals"],
        )
        self.assertIn(
            'BottomEdgeStrokeWeight="0"',
            stories["st_safety_symbols_icons_left"],
        )

    def test_safety_symbols_page_uses_localized_symbol_copy(self) -> None:
        import json
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        tail = [("component", json.dumps({
            "kind": "safetywarning",
            "texts": ["Avertissement de mise à la terre."],
        }))]
        maintenance = [
            ("h1", "INSTRUCTIONS D'ENTRETIEN PAR L'UTILISATEUR"),
            ("body", "Pendant le cycle de vie des produits de stockage d'énergie."),
        ]
        signals, _ = load_symbols_rows(FIXTURE_DATA_ROOT, "fr")
        icons = [{"figure": "", "text": "Icône localisée"}]
        w.add_safety_symbols_page(
            "st_safety_symbols_fr", tail, maintenance, signals, icons, ROOT, 4, "fr")
        stories = dict(w.stories)
        self.assertIn(
            "SIGNIFICATION DES SYMBOLES",
            stories["st_safety_symbols_fr_symbols_title"],
        )
        self.assertIn("Symbole", stories["st_safety_symbols_fr_signals"])
        self.assertIn("Signification", stories["st_safety_symbols_fr_icons_left"])
        self.assertIn("AVERTISSEMENT", stories["st_safety_symbols_fr_signals"])
        self.assertIn(
            'ParagraphShadingColor="Color/HB Brand Dark"',
            stories["st_safety_symbols_fr_signals"],
        )
        self.assertIn("AVERTISSEMENT", stories["st_safety_symbols_fr_tail_avertissement"])
        self.assertNotIn(">WARNING<", stories["st_safety_symbols_fr_tail_avertissement"])
        self.assertIn(
            "Pratiques dangereuses pouvant entraîner des blessures graves",
            stories["st_safety_symbols_fr_signals"],
        )
        self.assertIn("Icône localisée", stories["st_safety_symbols_fr_icons_left"])

    def test_safety_symbols_page_uses_template_icon_split(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        signals = [("WARNING", "Hazardous practice.")]
        icon_rows = [
            ("warning_triangle", 1, "Warning row"),
            ("read_manual", 2, "Read manual"),
            ("electric_shock", 3, "Risk of electric shock."),
            ("battery_charging", 4, "Battery charging"),
            ("explosive_material", 5, "Explosive material"),
            ("heavy_object", 6, "Heavy object"),
            ("do_not_dismantle", 7, "Do not dismantle the product."),
            ("no_open_flame", 8, "Keep the product away from fire."),
            ("keep_away_from_children", 9, "Keep away from children."),
            ("li_ion", 10, "Lithium-ion battery."),
            ("weee", 11, "Household waste recycling."),
            ("weee2", 12, "Batteries and accumulators."),
        ]
        icons = [
            {"symbol_key": key, "order": str(order), "figure": "", "text": text}
            for key, order, text in icon_rows
        ]
        w = IdmlWriter(params)
        w.add_safety_symbols_page(
            "st_safety_symbols_tpl",
            [],
            [("h1", "USER MAINTENANCE INSTRUCTIONS"), ("body", "Body.")],
            signals,
            icons,
            ROOT,
            4,
            "en",
        )
        stories = dict(w.stories)
        left = stories["st_safety_symbols_tpl_icons_left"]
        right = stories["st_safety_symbols_tpl_icons_right"]
        self.assertIn("Heavy object", left)
        self.assertNotIn("Do not dismantle", left)
        self.assertIn("Do not dismantle the product.", right)
        self.assertIn("Keep away from children.", right)
        self.assertNotIn("Batteries and accumulators", left + right)

    def test_fcc_inbox_page_combines_two_template_pages(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        fcc = [("component", json.dumps({
            "kind": "fcc",
            "texts": ["FCC left copy.", "FCC right copy."],
        }))]
        inbox = [
            ("h1", "WHAT'S IN THE BOX"),
            ("component", json.dumps({
                "kind": "inbox",
                "items": [
                    {"img": "", "label": "Jackery Explorer 1000"},
                    {"img": "", "label": "AC Charging Cable"},
                    {"img": "", "label": "Documents"},
                ],
            })),
            ("component", json.dumps({
                "kind": "notice",
                "label": "TIP",
                "texts": ["The car charging cable is sold separately."],
            })),
        ]
        w.add_fcc_inbox_page("st_fcc_inbox", fcc, inbox, ROOT, 3)
        spread = dict(w.spreads)["sp_3"]
        self.assertEqual(spread.count("<TextFrame "), 11)
        self.assertEqual(spread.count("<Rectangle "), 10)
        self.assertEqual(
            spread.count('AppliedObjectStyle="ObjectStyle/HB Rounded Panel"'),
            3,
        )
        self.assertEqual(
            spread.count('AppliedObjectStyle="ObjectStyle/HB Inbox Card"'),
            3,
        )
        self.assertEqual(
            spread.count('AppliedObjectStyle="ObjectStyle/HB Badge"'),
            3,
        )
        self.assertIn("tf_st_fcc_inbox_fcc_left", spread)
        self.assertIn("tf_st_fcc_inbox_fcc_right", spread)
        self.assertIn("tf_st_fcc_inbox_title", spread)
        self.assertIn("tf_st_fcc_inbox_card_1", spread)
        self.assertIn("tf_st_fcc_inbox_card_2", spread)
        self.assertIn("tf_st_fcc_inbox_card_3", spread)
        badge_frame = spread.split('Self="tf_st_fcc_inbox_badge_1"', 1)[1].split(
            "</TextFrame>", 1,
        )[0]
        self.assertIn('VerticalJustification="CenterAlign"', badge_frame)
        self.assertIn("tf_st_fcc_inbox_tip_label", spread)
        self.assertIn("tf_st_fcc_inbox_tip_body", spread)
        self.assertIn('Self="bg_st_fcc_inbox_title"', spread)
        fcc_frame = spread.split('Self="tf_st_fcc_inbox_fcc_left"', 1)[1].split(
            "</TextFrame>", 1)[0]
        self.assertIn('InsetSpacing="0 0 0 0"', fcc_frame)
        stories = dict(w.stories)
        self.assertIn("FCC left copy.", stories["st_fcc_inbox_fcc_left"])
        self.assertIn("FCC right copy.", stories["st_fcc_inbox_fcc_right"])
        self.assertIn("WHAT'S IN THE BOX", stories["st_fcc_inbox_title"])
        self.assertIn("AC Charging Cable", stories["st_fcc_inbox_card_2"])
        self.assertIn(
            'PointSize="10.912" FontStyle="Medium" BaselineShift="0.45"',
            stories["st_fcc_inbox_badge_1"],
        )
        self.assertIn(">TIPS<", stories["st_fcc_inbox_tip_label"])
        self.assertIn(
            "The car charging cable is sold separately.",
            stories["st_fcc_inbox_tip_body"],
        )
        for key in ("st_fcc_inbox_card_1", "st_fcc_inbox_tip_body"):
            self.assertNotIn("<Table", stories[key])

    def test_fcc_inbox_page_falls_back_to_plain_localized_fcc_prose(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        fcc = [
            ("h1", "FCC"),
            ("body", "Este dispositivo cumple con la parte 15 de las Reglas de la FCC."),
            ("body", "**NOTA:** Este aparato ha sido probado y cumple con los limites."),
            ("body", "Estos limites estan disenados para proporcionar una proteccion razonable."),
            ("body", "Si este aparato causa interferencias daninas en la recepcion de radio."),
            ("list", "• Reorientar o reubicar la antena receptora."),
            ("body", "**MODIFICACION:** Cualquier cambio podria anular la autoridad."),
        ]
        inbox = [
            ("h1", "WHAT'S IN THE BOX"),
            ("component", json.dumps({
                "kind": "inbox",
                "items": [{"img": "", "label": "Documents"}],
            })),
        ]
        w.add_fcc_inbox_page("st_fcc_plain", fcc, inbox, ROOT, 3)
        spread = dict(w.spreads)["sp_3"]
        fcc_frame = spread.split('Self="tf_st_fcc_plain_fcc_left"', 1)[1].split(
            "</TextFrame>", 1)[0]
        self.assertIn('TextColumnCount="1"', fcc_frame)
        stories = dict(w.stories)
        story = stories["st_fcc_plain_fcc_left"] + stories["st_fcc_plain_fcc_right"]
        self.assertNotIn("<Table", story)
        self.assertIn("Este dispositivo cumple", story)
        self.assertIn("Si este aparato causa", story)
        self.assertIn("Reorientar o reubicar", story)
        self.assertIn("MODIFICACION:", story)

    def test_default_idml_paths_follow_prepared_bundle_layout(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        region_bundle = tmp / "docs" / "_build" / "JE-1000F" / "US" / "rst"
        region_bundle.mkdir(parents=True)
        bundle = idml_export_paths.default_bundle_root(tmp, "JE-1000F", "US", "en")
        self.assertEqual(
            bundle,
            region_bundle,
        )
        self.assertEqual(
            idml_export_paths.default_output_path(tmp, "JE-1000F", "US", "en", bundle),
            tmp / "docs" / "_build" / "JE-1000F" / "US" / "idml"
            / "manual_je1000f_us.idml",
        )
        lang_bundle = tmp / "docs" / "_build" / "JE-1000F" / "US" / "en" / "rst"
        lang_bundle.mkdir(parents=True)
        bundle = idml_export_paths.default_bundle_root(tmp, "JE-1000F", "US", "en")
        self.assertEqual(bundle, lang_bundle)
        self.assertEqual(
            idml_export_paths.default_output_path(tmp, "JE-1000F", "US", "en", bundle),
            tmp / "docs" / "_build" / "JE-1000F" / "US" / "en" / "idml"
            / "manual_je1000f_us_en.idml",
        )

    def test_notice_list_tables_are_components_not_data_tables(self) -> None:
        import json
        from tools.idml_rst_extract import _parse_text
        text = """
.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **NOTE**
     - - First item.
       - Second item.
       - Third item.
"""
        res = _parse_text(text, {"latex"})
        self.assertEqual(len(res.blocks), 1)
        kind, payload = res.blocks[0]
        self.assertEqual(kind, "component")
        data = json.loads(payload)
        self.assertEqual(data["kind"], "notice")
        self.assertTrue(data["list"])
        self.assertEqual(data["texts"], ["First item.", "Second item.", "Third item."])

    def test_localized_notice_list_tables_are_components_not_data_tables(self) -> None:
        import json
        from tools.idml_rst_extract import _parse_text

        cases = [
            ("REMARQUE", "note"),
            ("NOTA", "note"),
            ("CONSEILS", "tip"),
            ("CONSEJOS", "tip"),
            ("ATTENTION", "caution"),
            ("PRECAUCIÓN", "caution"),
        ]
        for label, variant in cases:
            with self.subTest(label=label):
                text = f"""
.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **{label}** -
     - First localized item.
     - Second localized item.
"""
                res = _parse_text(text, {"latex"})
                self.assertEqual(len(res.blocks), 1)
                kind, payload = res.blocks[0]
                self.assertEqual(kind, "component")
                data = json.loads(payload)
                self.assertEqual(data["kind"], "notice")
                self.assertEqual(data["label"], label)
                self.assertEqual(data["variant"], variant)
                self.assertTrue(data["list"])
                self.assertEqual(
                    data["texts"],
                    ["First localized item.", "Second localized item."],
                )

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
        self.assertIn(paragraph_style_ref("HB Figure"), story)
        icon_cell = story.split('Self="tbl_lcdc0_1"', 1)[1].split("</Cell>", 1)[0]
        self.assertIn('VerticalJustification="CenterAlign"', icon_cell)
        self.assertIn('BaselineShift="0.6"', icon_cell)
        self.assertNotIn('BaselineShift="8.9"', story)

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
            self.assertIn(paragraph_style_ref("HB Spec Note"), story)
            marker, body = notes[0].split(" ", 1)
            self.assertIn(f"<Content>{marker}</Content>", story)
            self.assertIn(body[:20].replace("&", "&amp;"), story)

    def test_dom_version_supports_paragraph_shading(self) -> None:
        # paragraph shading is CC2015+; a DOMVersion 8.0 doc is parsed with
        # CS6 semantics and the shading attributes are dropped (designer-
        # reported: H1 bar still missing after the attribute-name fix)
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        self.assertIn('DOMVersion="15.0"', w.styles_xml())
        self.assertNotIn('DOMVersion="8.0"', w.designmap_xml())

    def test_lcdmode_component_parses_and_renders(self) -> None:
        from tools.idml_rst_extract import extract_page
        bundle = ROOT / "docs" / "_build" / "JE-1000F" / "US" / "en" / "rst"
        page = bundle / "page" / "05_operation_guide_placeholder.rst"
        if not page.exists():
            self.skipTest("no prepared bundle in this checkout")
        res = extract_page(page, {"latex", "region_us", "lang_en", "model_je_1000f"})
        import json
        comps = [json.loads(t) for k, t in res.blocks if k == "component"]
        lcd = [c for c in comps if c.get("kind") == "lcdmode"]
        self.assertTrue(lcd)
        self.assertEqual(len(lcd[0]["groups"]), 2)
        self.assertEqual(len(lcd[0]["groups"][0]["actions"]), 3)

    def test_list_tables_are_extracted_not_skipped(self) -> None:
        from tools.idml_rst_extract import _parse_list_table
        body = [
            "   :header-rows: 1",
            "",
            "   * - Buttons",
            "     - Operation",
            "     - Function",
            "   * - A + B",
            "     - Hold 3s",
            "     - Toggle mode",
        ]
        rows = _parse_list_table(body)
        self.assertEqual(rows[0], ["Buttons", "Operation", "Function"])
        self.assertEqual(rows[1], ["A + B", "Hold 3s", "Toggle mode"])

    def test_full_bundle_extraction_has_zero_skips(self) -> None:
        from tools.idml_rst_extract import bundle_page_order, extract_page
        bundle = ROOT / "docs" / "_build" / "JE-1000F" / "US" / "en" / "rst"
        if not bundle.is_dir():
            self.skipTest("no prepared bundle in this checkout")
        tags = {"latex", "region_us", "lang_en", "model_je_1000f"}
        data_prefixes = ("spec_", "lcd_icons_", "troubleshooting_", "symbols_")
        total = sum(
            extract_page(p, tags).skipped_raw
            for p in bundle_page_order(bundle)
            if not p.name.startswith(data_prefixes))
        self.assertEqual(total, 0)

    def test_styles_map_layout_params(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        styles = w.styles_xml()
        semantic_names = (
            "HB H1", "HB Body", "HB Spec Label", "HB Spec Value",
            "HB Capsule Text", "HB Notice Side Label", "HB Card Number",
        )
        for name in semantic_names:
            self.assertIn(f'Name="{paragraph_style_name(name)}"', styles)
            self.assertNotIn(f'Name="{name}"', styles)
        self.assertIn('Name="Heading1"', styles)
        self.assertIn('Name="Figure"', styles)
        card_name = paragraph_style_name("HB Card Number")
        card = styles.split(f'Name="{card_name}"')[1].split("</ParagraphStyle>")[0]
        self.assertIn('ParagraphShadingWidth="TextWidth"', card)
        self.assertIn('Justification="CenterAlign"', card)
        self.assertIn("Gilroy", styles)

    def test_page_geometry_is_130x185(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        self.assertAlmostEqual(w.page_w, 130.10 * 72 / 25.4, places=1)
        self.assertAlmostEqual(w.page_h, 185.10 * 72 / 25.4, places=1)


if __name__ == "__main__":
    unittest.main()


class AttributeEscapingTests(unittest.TestCase):
    def test_story_title_with_quotes_stays_well_formed(self) -> None:
        # saxutils.escape leaves `"` alone; inside StoryTitle="..." a raw quote
        # truncates the attribute and malforms the story part.
        from xml.etree import ElementTree as ET

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        w.add_text_story("st_q", 'The "Explorer" manual', [("HB Body", "x")])
        xml = dict(w.stories)["st_q"]
        self.assertIn('StoryTitle="The &quot;Explorer&quot; manual"', xml)
        ET.fromstring(xml)  # must parse

    def test_prose_story_title_with_quotes_stays_well_formed(self) -> None:
        from xml.etree import ElementTree as ET

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        w.add_prose_story("st_q2", 'page "one"', [("body", "x")], ROOT)
        ET.fromstring(dict(w.stories)["st_q2"])
