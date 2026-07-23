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
APPROVED_LAYOUT_CONTRACT = (
    ROOT / "docs" / "renderers" / "contracts" / "reference_layout"
    / "je1000f_us_v2_20260605.json"
)


def _approved_app_plan(source_path: str, language: str) -> dict[str, object]:
    return {
        "plan_source": "approved-reference",
        "approved_contract": json.loads(
            APPROVED_LAYOUT_CONTRACT.read_text(encoding="utf-8")
        ),
        "pages": [{
            "source_path": source_path,
            "language": language,
            "composition_id": f"{Path(source_path).stem}-composition",
            "planned_page_count": 2,
        }],
    }


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

    def test_last_spread_frame_can_shift_without_changing_earlier_frames(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        writer = IdmlWriter(params)
        writer.add_spread_chain(
            "st_shifted",
            2,
            0,
            last_frame_x_offset=-6.82,
        )
        first = writer.spreads[0][1]
        last = writer.spreads[1][1]
        base_x = -writer.page_w / 2 + writer.m_l
        self.assertIn(f'Anchor="{base_x:g} ', first)
        self.assertIn(f'Anchor="{base_x - 6.82:g} ', last)
        self.assertNotIn(f'Anchor="{base_x - 6.82:g} ', first)

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
        self.assertIn('Name="Apple SD Gothic Neo"', fonts)
        self.assertIn('PostScriptName="AppleSDGothicNeo-Regular"', fonts)

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
        story = "".join(
            xml for sid, xml in dict(w.stories).items()
            if sid.startswith("st_anchor_lcd_table_")
        )
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

    def test_notice_macro_requires_source_label(self) -> None:
        from tools.idml_rst_extract import ExtractResult, _extract_raw_latex

        with self.assertRaisesRegex(ValueError, "required from source RST"):
            _extract_raw_latex(
                r"\HBNoticeBlock[tip]{}{renderer must not invent a label}{}",
                ExtractResult(),
            )

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
        result_xml, _ = render_image_block(
            result.as_posix(),
            w._render_context(bundle), rect_id="r3", terminal=False)
        self.assertIn('AnchorSpaceAbove="0"', result_xml)

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
        with self.assertRaisesRegex(ValueError, "required from source IR"):
            w._render_component(
                "t", 2,
                {"kind": "notice", "texts": ["renderer must not label this"]},
                bundle, True,
            )
        # warnbox: triangle icon + one editable label; do not place the
        # WARNING lockup art and then print WARNING again below it.
        xml, _ = w._render_component("t", 3, {
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
        instruction_xml, _ = w._render_component("t", 5, {
            "kind": "safetyinstruction", "texts": ["KEEP THIS INSTRUCTION"]},
            bundle, True)
        self.assertIn("warning_triangle_dark.svg", instruction_xml)
        self.assertIn(paragraph_style_ref("HB Safety Instruction"), instruction_xml)
        self.assertNotIn(paragraph_style_ref("HB Title L3"), instruction_xml)
        xml, _ = w._render_component("t", 5, {
            "kind": "warninglead", "label": "WARNING", "texts": ["lead"]},
            bundle, True, span_columns=False, measure_w=150.0)
        self.assertIn("warning_triangle", xml)
        self.assertIn('FillColor="Color/HB Brand Dark"', xml)
        warninglead_story = dict(w.stories)["st_anchor_warninglead_text_t_cmp5"]
        self.assertIn(">WARNING<", warninglead_story)
        self.assertIn(
            paragraph_style_ref("HB Warning Lead Label"), warninglead_story,
        )
        self.assertIn(
            paragraph_style_ref("HB Warning Lead Body"), warninglead_story,
        )
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

    def test_page_break_can_carry_reference_top_spacing(self) -> None:
        from tools.idml.writer import IdmlWriter

        writer = IdmlWriter({})
        writer.add_prose_story(
            "st_spaced_break",
            "spaced break",
            [
                ("body", "First."),
                ("layout", "page_break:10.5"),
                ("h2", "Second section"),
            ],
            ROOT,
        )
        story = dict(writer.stories)["st_spaced_break"]

        self.assertIn(
            'StartParagraph="NextPage" SpaceAfter="10.5"',
            story,
        )

    def test_operation_page_semantics_carry_reference_vertical_rhythm(self) -> None:
        from tools.idml.writer import IdmlWriter

        writer = IdmlWriter({})
        writer.add_prose_story(
            "st_operation_rhythm",
            "operation rhythm",
            [
                ("layout", "twocol_start"),
                ("body", "Earlier two-column copy."),
                ("layout", "twocol_end"),
                ("h2_operation_energy", "Energy"),
                ("body_operation_energy_intro", "Introductory copy."),
                ("h2_operation_led", "LED"),
            ],
            ROOT,
        )
        story = dict(writer.stories)["st_operation_rhythm"]

        self.assertIn('SpaceAfter="7.5"', story)
        self.assertIn('Leading="8.1" SpaceAfter="7"', story)
        self.assertIn(
            'SpaceBefore="22" SpaceAfter="6.5" '
            'AppliedParagraphStyle="ParagraphStyle/Heading2" '
            'SpanColumnType="SpanColumns"',
            story,
        )

    def test_operation_first_page_rhythm_uses_locale_tokens(self) -> None:
        from tools.idml.writer import IdmlWriter

        writer = IdmlWriter({
            "lang_fr_idml_operation_first_h2_space_before": ("9.8", "pt"),
            "lang_fr_idml_operation_inter_section_space_after": ("37.6", "pt"),
        })
        writer.add_prose_story(
            "st_operation_first_page",
            "05_operation_guide_placeholder",
            [
                ("h1", "FONCTIONNEMENT"),
                ("h2", "MARCHE/ARRÊT"),
                ("body", "First operation explanation."),
                ("h2", "SORTIE CA MARCHE/ARRÊT"),
            ],
            ROOT,
            language="fr",
        )
        story = dict(writer.stories)["st_operation_first_page"]
        self.assertIn('SpaceBefore="9.8"', story)
        self.assertIn('SpaceAfter="37.6"', story)

    def test_operation_key_heading_compensates_first_page_depth(self) -> None:
        from tools.idml.writer import IdmlWriter

        writer = IdmlWriter({
            "lang_fr_idml_operation_first_h2_space_before": ("9.8", "pt"),
            "lang_fr_idml_operation_inter_section_space_after": ("37.6", "pt"),
        })
        writer.add_prose_story(
            "st_operation_key_compensation",
            "05_operation_guide_placeholder",
            [
                ("h1", "FONCTIONNEMENT"),
                ("h2", "MARCHE/ARRÊT"),
                ("body", "First operation explanation."),
                ("h2", "SORTIE CA MARCHE/ARRÊT"),
                ("h2", "FONCTIONNEMENT DES BOUTONS"),
                ("table", '[["Boutons", "Utilisation", "Fonction"]]'),
            ],
            ROOT,
            language="fr",
        )
        story = dict(writer.stories)["st_operation_key_compensation"]
        self.assertIn('SpaceBefore="-19"', story)
        self.assertIn('BaselineShift="36.68"', story)

    def test_operation_led_gap_returns_space_consumed_by_localized_copy(self) -> None:
        from tools.idml.oppanel import operation_story_rhythm

        short_attrs, short_spacing = operation_story_rhythm(
            "h2_operation_led",
            intro_lines=7,
            energy_panel_height=172.0,
            baseline_panel_height=172.0,
        )
        long_attrs, long_spacing = operation_story_rhythm(
            "h2_operation_led",
            intro_lines=8,
            energy_panel_height=175.0,
            baseline_panel_height=172.0,
        )
        self.assertEqual('SpaceBefore="22" SpaceAfter="6.5"', short_attrs)
        self.assertEqual(28.5, short_spacing)
        self.assertEqual('SpaceBefore="10.9" SpaceAfter="6.5"', long_attrs)
        self.assertAlmostEqual(17.4, long_spacing or 0.0)

    def test_lcd_mode_component_resolves_finalized_renderer_asset(self) -> None:
        from tools.idml.components import RenderContext, render
        from tools.idml_rst_extract import ExtractResult, _extract_raw_latex

        raw = (
            r"\begin{HBLcdModeTable}{op_lcd_mode.png}"
            r"\HBLcdModeFirstGroup{Saving On}{On}{Press}{Off}{Press}{Auto}{Two minutes}"
            r"\HBLcdModeSecondGroup{Saving Off}{On}{Press}{Off}{Press}{Auto}{Never}"
            r"\end{HBLcdModeTable}"
        )
        result = ExtractResult()
        _extract_raw_latex(raw, result)
        spec = json.loads(result.blocks[0][1])
        self.assertEqual("lcdmode", spec["kind"])
        self.assertEqual("op_lcd_mode.png", spec["img"])

        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / "bundle"
            targeted = bundle / "renderers" / "latex" / "assets" / "op_lcd_mode.png"
            generic = bundle / "_assets" / "common" / "lcd_mode.png"
            targeted.parent.mkdir(parents=True)
            generic.parent.mkdir(parents=True)
            targeted.write_bytes(b"target-specific LCD image")
            generic.write_bytes(b"generic LCD image")
            ctx = RenderContext(
                params={},
                page_w=368.79,
                m_l=28.35,
                m_r=28.35,
                root=Path(td) / "outside",
                bundle_root=bundle,
            )

            resolved = ctx.resolve_bundle_image(spec["img"])
            self.assertIsNotNone(resolved)
            self.assertEqual(targeted.resolve(), resolved.resolve())  # type: ignore[union-attr]
            xml, _height = render(spec, ctx, tid="lcd_targeted", terminal=True)
            self.assertIn(targeted.resolve().as_uri(), xml)
            self.assertNotIn(generic.resolve().as_uri(), xml)

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

    def test_approved_prose_flow_groups_by_composition_without_estimator_merge(self) -> None:
        from tools.idml.prose_flow import ProseFlowBuffer

        flow = ProseFlowBuffer()
        flow.add("operation", [("h1", "Operation")])
        flow.add("ups", [("h1", "UPS")])
        flow.add("charging", [("h1", "Charging")])
        emitted = []
        plan = {
            "plan_source": "approved-reference",
            "pages": [
                {
                    "source_path": "page/operation.rst",
                    "latex_start_page": 10,
                    "composition_id": "operation-en",
                    "planned_page_count": 4,
                },
                {
                    "source_path": "page/ups.rst",
                    "latex_start_page": 10,
                    "composition_id": "charging-en",
                    "planned_page_count": 1,
                },
                {
                    "source_path": "page/charging.rst",
                    "latex_start_page": 10,
                    "composition_id": "charging-en",
                    "planned_page_count": 1,
                },
            ],
        }

        flow.flush(
            lambda _sid, title, _blocks, _columns: emitted.append(title),
            lambda stem: stem,
            plan,
            estimate_pages=lambda _blocks, _columns: self.fail(
                "approved compositions must not be merged by estimation"
            ),
        )

        self.assertEqual(emitted, ["operation", "ups + charging"])

    def test_approved_prose_flow_moves_declared_tail_to_next_composition(self) -> None:
        from tools.idml.prose_flow import ProseFlowBuffer

        flow = ProseFlowBuffer()
        flow.add("ups", [("h1", "UPS"), ("body", "UPS body")])
        flow.add("charging", [
            ("h1", "CHARGING"),
            ("body", "Charging intro"),
            ("h2", "AC WALL"),
            ("body", "AC method"),
        ])
        flow.add("methods", [("h2", "SOLAR"), ("body", "Solar method")])
        emitted = []
        plan = {
            "plan_source": "approved-reference",
            "pages": [
                {
                    "source_path": "page/ups.rst",
                    "latex_start_page": 14,
                    "composition_id": "ups-charging",
                },
                {
                    "source_path": "page/charging.rst",
                    "latex_start_page": 14,
                    "composition_id": "ups-charging",
                    "flow_split": {
                        "at_kind": "h2",
                        "occurrence": 1,
                        "tail_composition_id": "methods",
                    },
                },
                {
                    "source_path": "page/methods.rst",
                    "latex_start_page": 15,
                    "composition_id": "methods",
                },
            ],
        }

        flow.flush(
            lambda _sid, title, blocks, _columns: emitted.append((title, blocks)),
            lambda stem: stem,
            plan,
        )

        self.assertEqual(["ups + charging", "methods"], [item[0] for item in emitted])
        self.assertNotIn(("h2", "AC WALL"), emitted[0][1])
        self.assertEqual(("h2", "AC WALL"), emitted[1][1][0])
        self.assertIn(("h2", "SOLAR"), emitted[1][1])

    def test_prose_flow_can_ignore_reference_starts_for_natural_layout(self) -> None:
        from tools.idml.prose_flow import ProseFlowBuffer

        flow = ProseFlowBuffer()
        for stem in ("operation", "ups", "charging"):
            flow.add(stem, [("h1", stem.title())])
        emitted = []
        starts = {"operation": 10, "ups": 14, "charging": 14}

        flow.flush(
            lambda _sid, title, _blocks, _columns: emitted.append(title),
            lambda stem: stem,
            {"pages": [
                {"source_path": f"page/{stem}.rst", "latex_start_page": start}
                for stem, start in starts.items()
            ]},
            respect_page_plan=False,
        )

        self.assertEqual(emitted, ["operation + ups + charging"])

    def test_prose_flow_keeps_shared_region_stories_separate(self) -> None:
        from tools.idml.prose_flow import ProseFlowBuffer

        flow = ProseFlowBuffer()
        flow.add("09_storage_and_maintenance", [("h1", "Storage")])
        flow.add("troubleshooting_en", [("h1", "Troubleshooting")])
        emitted = []

        flow.flush(
            lambda _sid, title, _blocks, _columns: emitted.append(title),
            lambda stem: stem,
            {"pages": [
                {
                    "source_path": f"page/{stem}.rst",
                    "latex_start_page": 16,
                }
                for stem in (
                    "09_storage_and_maintenance",
                    "troubleshooting_en",
                )
            ]},
            dedicated_stems={
                "09_storage_and_maintenance",
                "troubleshooting_en",
            },
        )

        self.assertEqual(
            emitted,
            ["09_storage_and_maintenance", "troubleshooting_en"],
        )

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

    def test_approved_troubleshooting_heading_uses_semantic_locale_marker(self) -> None:
        from tools.idml.prose_flow import align_troubleshooting_heading

        rows = [
            ["Code d'erreur", "Mesures correctives"],
            ["FE", "Contacter le service à la clientèle de Jackery."],
        ]
        blocks = [
            ("h1", "DÉPANNAGE"),
            ("body", "Localized introduction"),
            ("table", json.dumps(rows, ensure_ascii=False)),
        ]

        aligned = align_troubleshooting_heading(blocks, "fr")

        self.assertEqual(
            ("layout", "trouble_h1_before:fr"),
            aligned[0],
        )
        self.assertEqual(blocks, aligned[1:])

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

    def test_approved_operation_flow_uses_all_three_page_boundaries(self) -> None:
        from tools.idml.prose_flow import align_operation_tail

        blocks = [("h1", "Operations")]
        blocks.extend(("h2", f"Section {index}") for index in range(1, 9))
        plan = {
            "plan_source": "approved-reference",
            "pages": [{
                "source_path": "page/05_operation_guide.rst",
                "composition_id": "operation",
                "planned_page_count": 4,
            }],
        }

        aligned = align_operation_tail(blocks, plan, "05_operation_guide")

        break_followers = [
            aligned[index + 1][1]
            for index, block in enumerate(aligned[:-1])
            if block[0] == "layout" and block[1].startswith("page_break")
        ]
        self.assertEqual(["Section 3", "Section 4", "Section 6"], break_followers)
        self.assertIn(("layout", "page_break:15.7"), aligned)

    def test_operation_language_and_last_page_gap_follow_localized_key_headers(
        self,
    ) -> None:
        from tools.idml.prose_flow import align_operation_tail, operation_language

        headers = {
            "en": ["Buttons", "Operation", "Function"],
            "fr": ["Boutons", "Utilisation", "Fonction"],
            "es": ["Botones", "Operación", "Función"],
        }
        expected_gaps = {"en": "15.7", "fr": "8.1", "es": "9.3"}
        plan = {
            "plan_source": "approved-reference",
            "pages": [{
                "source_path": "page/05_operation_guide.rst",
                "composition_id": "operation",
                "planned_page_count": 4,
            }],
        }

        for language, header in headers.items():
            with self.subTest(language=language):
                blocks = [("h1", "Operations")]
                blocks.extend(("h2", f"Section {index}") for index in range(1, 9))
                blocks.append(("table", json.dumps([header, ["A", "B", "C"]])))

                self.assertEqual(language, operation_language(blocks))
                aligned = align_operation_tail(
                    blocks,
                    plan,
                    "05_operation_guide",
                )
                self.assertIn(
                    ("layout", f"page_break:{expected_gaps[language]}"),
                    aligned,
                )

    def test_operation_page_break_gap_is_emitted_on_the_new_page_carrier(
        self,
    ) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        writer = IdmlWriter(params)

        writer.add_prose_story(
            "st_operation_gap",
            "operation gap",
            [
                ("layout", "page_break:8.1"),
                ("h2", "AFFICHAGE LCD"),
            ],
            ROOT,
        )

        story = dict(writer.stories)["st_operation_gap"]
        self.assertIn(
            '<ParagraphStyleRange StartParagraph="NextPage" SpaceAfter="8.1" ',
            story,
        )

    def test_single_page_ups_callouts_bind_shared_roles_and_fr_width(self) -> None:
        from tools.idml.prose_flow import ProseFlowBuffer

        def rendered_specs(language: str) -> list[dict]:
            flow = ProseFlowBuffer()
            notice = (
                "component",
                json.dumps({
                    "kind": "notice",
                    "label": "Localized label",
                    "texts": ["one", "two", "three"],
                    "list": True,
                }),
            )
            flow.add("06_ups_mode", [notice])
            flow.add("charging", [notice])
            emitted: list[tuple[str, str]] = []
            plan = {
                "plan_source": "approved-reference",
                "pages": [
                    {
                        "source_path": "page/06_ups_mode.rst",
                        "composition_id": f"{language}_ups_charging",
                        "language": language,
                        "planned_page_count": 1,
                    },
                    {
                        "source_path": "page/charging.rst",
                        "composition_id": f"{language}_ups_charging",
                        "language": language,
                        "planned_page_count": 1,
                    },
                ],
            }
            flow.flush(
                lambda _sid, _title, blocks, _columns: emitted.extend(blocks),
                lambda value: value,
                plan,
            )
            return [
                json.loads(payload)
                for kind, payload in emitted
                if kind == "component"
            ]

        for language in ("en", "fr", "es"):
            with self.subTest(language=language):
                specs = rendered_specs(language)
                self.assertEqual(
                    ["ups_caution", "charging_note"],
                    [spec.get("layout_role") for spec in specs],
                )
                expected_scale = [1.0, 1.0] if language == "fr" else [None, None]
                self.assertEqual(
                    expected_scale,
                    [spec.get("body_horizontal_scale") for spec in specs],
                )

    def test_approved_charging_methods_start_second_solar_figure_on_second_page(self) -> None:
        from tools.idml.prose_flow import align_charging_car_page

        blocks = [
            ("h2", "Solar"),
            ("image", "solar-direct.png"),
            ("body", "Connector guidance"),
            ("image", "solar-adapter.png"),
            ("component", json.dumps({"kind": "notice", "label": "CAUTION"})),
            ("h2", "Car"), ("image", "car.png"),
        ]
        plan = {
            "plan_source": "approved-reference",
            "pages": [{
                "source_path": "page/08_charging_methods.rst",
                "composition_id": "charging",
                "planned_page_count": 2,
            }],
        }

        aligned = align_charging_car_page(blocks, plan, "08_charging_methods")

        self.assertEqual(("layout", "page_break:14.4"), aligned[3])
        self.assertEqual(("image", "solar-adapter.png"), aligned[4])
        car_index = aligned.index(("h2", "Car"))
        self.assertNotEqual(("layout", "page_break:14.4"), aligned[car_index - 1])

    def test_approved_charging_tail_moves_car_notice_to_storage_composition(self) -> None:
        from tools.idml.prose_flow import ProseFlowBuffer

        car_notice = (
            "component",
            json.dumps({"kind": "notice", "label": "PRECAUCIÓN", "texts": ["x"]}),
        )
        flow = ProseFlowBuffer()
        flow.add("08_charging_methods", [
            ("h2", "Solar"),
            ("image", "solar-direct.png"),
            ("image", "solar-adapter.png"),
            ("h2", "Car"),
            ("image", "car.png"),
            ("body", "Localized vehicle caption"),
            car_notice,
        ])
        flow.add("09_storage_and_maintenance", [("h1", "Localized storage")])
        emitted = []
        plan = {
            "plan_source": "approved-reference",
            "pages": [
                {
                    "source_path": "page/08_charging_methods.rst",
                    "composition_id": "methods",
                    "planned_page_count": 2,
                },
                {
                    "source_path": "page/09_storage_and_maintenance.rst",
                    "composition_id": "storage",
                    "planned_page_count": 1,
                },
            ],
        }

        flow.flush(
            lambda _sid, title, blocks, _columns: emitted.append((title, blocks)),
            lambda stem: stem,
            plan,
        )

        self.assertEqual(["08_charging_methods", "09_storage_and_maintenance"],
                         [title for title, _blocks in emitted])
        self.assertNotIn(car_notice, emitted[0][1])
        self.assertEqual(car_notice, emitted[1][1][0])
        self.assertEqual(("h1", "Localized storage"), emitted[1][1][1])

    def test_unapproved_charging_tail_stays_in_its_source_composition(self) -> None:
        from tools.idml.prose_flow import _move_car_notice_to_storage

        car_notice = (
            "component",
            json.dumps({"kind": "notice", "label": "CAUTION", "texts": ["x"]}),
        )
        items = [
            ("08_charging_methods", [
                ("h2", "Solar"),
                ("image", "solar.png"),
                ("h2", "Car"),
                ("image", "car.png"),
                car_notice,
            ], 1),
            ("09_storage_and_maintenance", [("h1", "Storage")], 1),
        ]

        emitted = _move_car_notice_to_storage(
            items,
            {"plan_source": "measured-latex", "pages": []},
        )

        self.assertIn(car_notice, emitted[0][1])
        self.assertNotIn(car_notice, emitted[1][1])

    def test_approved_charging_tail_moves_after_car_reference_figure_promotion(self) -> None:
        from tools.idml.prose_flow import _move_car_notice_to_storage

        car_notice = (
            "component",
            json.dumps({"kind": "notice", "label": "ATTENTION", "texts": ["x"]}),
        )
        car_figure = (
            "component",
            json.dumps({"kind": "referencefigure", "layout": "charging_car"}),
        )
        items = [
            ("p29_08_charging_methods", [
                ("h2", "Solar"),
                ("component", json.dumps({"kind": "referencefigure", "layout": "charging_car"})),
                ("h2", "Car"),
                car_figure,
                car_notice,
            ], 1),
            ("p30_09_storage_and_maintenance", [("h1", "Storage")], 1),
        ]

        emitted = _move_car_notice_to_storage(
            items,
            {
                "plan_source": "approved-reference",
                "pages": [
                    {
                        "source_path": "page/p29_08_charging_methods.rst",
                        "composition_id": "methods",
                        "planned_page_count": 2,
                    },
                    {
                        "source_path": "page/p30_09_storage_and_maintenance.rst",
                        "composition_id": "storage",
                        "planned_page_count": 1,
                    },
                ],
            },
        )

        self.assertNotIn(car_notice, emitted[0][1])
        self.assertEqual(car_notice, emitted[1][1][0])

    def test_approved_app_flow_starts_second_page_at_first_post_device_notice(self) -> None:
        from tools.idml.prose_flow import ProseFlowBuffer

        notice = (
            "component",
            json.dumps({"kind": "notice", "label": "Localized note"}),
        )
        for stem, image_ref in (
            ("12_app_setup_placeholder", "_assets/app/add_device.png"),
            (
                "12_app_setup_placeholder",
                "_assets/app/je1000f_us/add_device_je1000f_us.png",
            ),
        ):
            with self.subTest(stem=stem):
                blocks = [
                    ("h1", "Localized app title"),
                    ("h2", "Localized download heading"),
                    ("image", "download.png"),
                    ("h2", "Localized add-device heading"),
                    ("image", image_ref),
                    ("body", "Localized 2.3 Bluetooth copy"),
                ]
                blocks.extend([notice, ("body", "Localized 2.4 copy")])
                flow = ProseFlowBuffer()
                flow.add(stem, blocks)
                emitted = []
                plan = _approved_app_plan(f"page/{stem}.rst", "en")

                flow.flush(
                    lambda _sid, _title, out, _columns: emitted.extend(out),
                    lambda value: value,
                    plan,
                )

                breaks = [
                    block for block in emitted
                    if block[0] == "layout" and block[1].startswith("page_break")
                ]
                self.assertEqual([("layout", "page_break:15.1")], breaks)
                notice_index = next(
                    index for index, (kind, payload) in enumerate(emitted)
                    if kind == "component"
                    and json.loads(payload).get("kind") == "notice"
                )
                self.assertEqual(
                    ("layout", "page_break:15.1"), emitted[notice_index - 1],
                )
                notice_spec = json.loads(emitted[notice_index][1])
                self.assertEqual(300.516, notice_spec["body_width"])
                self.assertEqual(10.943, notice_spec["inline_x_offset"])
                self.assertEqual(44.737, notice_spec["panel_height"])

    def test_localized_app_flows_use_the_approved_english_page_split(self) -> None:
        from tools.idml.prose_flow import (
            align_app_second_page,
            promote_reference_figures,
        )

        notice = (
            "component",
            json.dumps({"kind": "notice", "label": "Localized note"}),
        )
        for stem, language, existing_break in (
            ("p34_12_app_setup_placeholder", "fr", False),
            ("p50_12_app_setup_placeholder", "es", True),
            ("12_app_setup_placeholder", "fr", False),
            ("12_app_setup_placeholder", "es", True),
        ):
            with self.subTest(stem=stem, language=language):
                blocks = [
                    ("h1", "Localized app title"),
                    ("h2", "Localized download heading"),
                    ("image", "download.png"),
                    ("body", "Localized download copy part one."),
                    ("body", "Localized download copy part two."),
                    ("h2", "Localized add-device heading"),
                    ("image", "add_device.png"),
                    ("body", "Localized 2.3 Bluetooth copy"),
                ]
                if existing_break:
                    blocks.append(("layout", "page_break"))
                blocks.extend([notice, ("body", "Localized 2.4 copy")])
                plan = _approved_app_plan(
                    f"page/{stem}.rst",
                    language,
                )

                aligned = align_app_second_page(blocks, plan, stem)
                self.assertIn(("layout", "page_break:15.1"), aligned)
                promoted = promote_reference_figures(aligned, plan, stem)
                layouts = [
                    json.loads(payload)["layout"]
                    for kind, payload in promoted
                    if kind == "component"
                    and json.loads(payload).get("kind") == "referencefigure"
                ]
                self.assertEqual(
                    ["app_download", "app_add_device"], layouts,
                )
                self.assertIn(
                    ("body", "Localized 2.3 Bluetooth copy"),
                    promoted,
                )

    def test_approved_reference_figures_absorb_only_adjacent_figure_copy(self) -> None:
        from tools.idml.prose_flow import promote_reference_figures

        plan = {"plan_source": "approved-reference", "pages": []}
        charging = [
            ("h2", "Localized AC heading"),
            ("body", "Localized AC caption"),
            ("image", "_assets/charging/ac_wall.png"),
            ("h2", "Localized car heading"),
            ("image", "renderers/latex/assets/car_charge.png"),
            ("body", "Localized vehicle\nLocalized cable note"),
        ]

        promoted = promote_reference_figures(
            charging, plan, "08_charging_methods",
        )

        specs = [
            json.loads(payload)
            for kind, payload in promoted
            if kind == "component"
        ]
        self.assertEqual(["charging_ac", "charging_car"], [
            spec["layout"] for spec in specs
        ])
        self.assertEqual("Localized AC caption", specs[0]["caption"])
        self.assertEqual("Localized vehicle", specs[1]["vehicle"])
        self.assertEqual("Localized cable note", specs[1]["note"])
        self.assertNotIn(("body", "Localized AC caption"), promoted)
        self.assertNotIn(
            ("body", "Localized vehicle\nLocalized cable note"), promoted,
        )

        self.assertEqual(
            charging,
            promote_reference_figures(
                charging,
                {"plan_source": "measured-latex", "pages": []},
                "08_charging_methods",
            ),
        )

    def test_charging_reference_promotion_requires_canonical_page_stem(self) -> None:
        from tools.idml.prose_flow import promote_reference_figures

        blocks = [
            ("body", "AC caption"),
            ("image", "_assets/charging/ac_wall.png"),
        ]
        plan = {"plan_source": "approved-reference", "pages": []}

        for stem in ("08_charging_methods", "p29_08_charging_methods", "p45_08_charging_methods"):
            with self.subTest(stem=stem):
                promoted = promote_reference_figures(blocks, plan, stem)
                self.assertEqual("component", promoted[0][0])
                self.assertEqual("charging_ac", json.loads(promoted[0][1])["layout"])

        for stem in ("charging", "battery_charging", "08_charging_methods_notes"):
            with self.subTest(stem=stem):
                self.assertEqual(blocks, promote_reference_figures(blocks, plan, stem))

    def test_approved_app_figures_keep_step_numbers_and_movable_labels(self) -> None:
        from tools.idml.prose_flow import promote_reference_figures

        blocks = [
            ("h2", "Localized download"),
            ("image", "_assets/app/download.png"),
            ("body", "First sentence. Second sentence. Final sentence."),
            ("h2", "Localized add device"),
            ("body", "2.1 Localized first step"),
            ("body", "2.2 Localized second step"),
            ("image", "_assets/app/add_device_je1000f_us.png"),
            (
                "body",
                "POWER Button\nAC Power Button\nDC / USB Power Button",
            ),
            ("body", "2.3 Localized third step"),
            (
                "component",
                json.dumps({"kind": "notice", "label": "NOTE", "texts": ["One"]}),
            ),
            ("body", "2.4 Localized fourth step"),
            (
                "component",
                json.dumps({"kind": "notice", "label": "NOTE", "texts": ["Two"]}),
            ),
            ("body", "2.5 Localized fifth step"),
            ("image", "_assets/app/connect_result_je1000f_us.png"),
            ("body", "Localized reference-only note."),
            (
                "component",
                json.dumps({"kind": "notice", "label": "CAUTION", "texts": ["Three"]}),
            ),
        ]

        promoted = promote_reference_figures(
            blocks,
            _approved_app_plan(
                "page/12_app_setup_placeholder.rst",
                "en",
            ),
            "12_app_setup_placeholder",
        )

        specs = [
            json.loads(payload)
            for kind, payload in promoted
            if kind == "component"
            and json.loads(payload).get("kind") == "referencefigure"
        ]
        self.assertEqual(
            ["app_download", "app_add_device", "app_connect_result"], [
            spec["layout"] for spec in specs
            ],
        )
        self.assertEqual(["2.1", "2.2"], specs[1]["step_labels"])
        self.assertEqual(
            {
                "main_power": "Main Power Button",
                "dc_usb": "DC/USB Power Button",
                "ac": "AC Power Button",
            },
            specs[1]["labels_by_role"],
        )
        self.assertIn(("body_app_tail", "2.3 Localized third step"), promoted)
        self.assertEqual(
            "asset:controls/je1000f_us/network_pairing_panel",
            specs[1]["control_image"],
        )
        self.assertEqual(["2.3", "2.4", "2.5"], specs[2]["step_labels"])
        self.assertEqual(
            "Localized reference-only note.", specs[2]["reference_note"],
        )
        notice_specs = [
            json.loads(payload)
            for kind, payload in promoted
            if kind == "component"
            and json.loads(payload).get("kind") == "notice"
        ]
        self.assertEqual([44.737, 16.221, 24.869], [
            spec["panel_height"] for spec in notice_specs
        ])
        self.assertEqual([5.8, 6.0, 5.8], [
            spec["body_size"] for spec in notice_specs
        ])
        self.assertEqual(2.0, notice_specs[0]["paragraph_space_after"])
        self.assertTrue(all(spec["app_text_frame_safety"] for spec in notice_specs))
        self.assertTrue(notice_specs[0]["unbulleted_first"])
        self.assertTrue(notice_specs[1]["unbulleted_first"])

    def test_approved_localized_app_figures_keep_localized_top_layer_labels(self) -> None:
        from tools.idml.prose_flow import promote_reference_figures

        blocks = [
            ("image", "_assets/app/download.png"),
            ("body", "Recherchez Jackery. Scannez le code QR."),
            ("body", "2.1 Ajouter un appareil"),
            ("body", "2.2 Allumer l'appareil"),
            ("image", "_assets/app/add_device_je1000f_us.png"),
            ("body", "Bouton d'alimentation\n"
                      "Bouton Power CA\n"
                      "Bouton d’alimentation CC / USB"),
            ("body", "2.3 Connexion Bluetooth"),
        ]
        plan = _approved_app_plan(
            "page/p34_12_app_setup_placeholder.rst",
            "fr",
        )
        promoted = promote_reference_figures(
            blocks, plan, "p34_12_app_setup_placeholder",
        )
        specs = [
            json.loads(payload)
            for kind, payload in promoted
            if kind == "component"
            and json.loads(payload).get("kind") == "referencefigure"
        ]
        self.assertEqual(
            ["app_download", "app_add_device"],
            [spec["layout"] for spec in specs],
        )
        self.assertEqual(
            {
                "main_power": "Bouton POWER",
                "dc_usb": "Bouton d’alimentation CC/USB",
                "ac": "Bouton d’alimentation CA",
            },
            specs[1]["labels_by_role"],
        )
        self.assertEqual(
            "asset:controls/je1000f_us/network_pairing_panel",
            specs[1]["control_image"],
        )
        self.assertIn(("body_app_tail", "2.3 Connexion Bluetooth"), promoted)

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

    def test_safety_lead_and_nested_lists_keep_their_source_semantics(self) -> None:
        from tools.idml_rst_extract import _parse_text

        res = _parse_text(
            """.. raw:: latex

   \\safetylead{SAVE THESE INSTRUCTIONS}

- Parent item:

  - Charging temperature: 14°F to 113°F
  - Discharging temperature: 14°F to 113°F
""",
            {"latex"},
        )

        self.assertEqual(res.blocks, [
            ("safetylead", "SAVE THESE INSTRUCTIONS"),
            ("list", "• Parent item:"),
            ("sublist", "– Charging temperature: 14°F to 113°F"),
            ("sublist", "– Discharging temperature: 14°F to 113°F"),
        ])

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
            ("safetylead", "SAVE THESE INSTRUCTIONS"),
            ("list", "• Stop using the product immediately."),
            ("sublist", "– Charging temperature: 14°F to 113°F"),
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
        self.assertIn(
            paragraph_style_ref("HB Safety Lead"),
            stories["st_safety_en_section2"],
        )
        self.assertIn(
            paragraph_style_ref("HB Safety Sublist"),
            stories["st_safety_en_section2"],
        )
        self.assertIn(
            'LeftIndent="3.7" FirstLineIndent="-6.25" RightIndent="0"',
            stories["st_safety_en_section2"],
        )
        self.assertIn(
            'HorizontalScale="98"', stories["st_safety_en_section2"],
        )

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
        self.assertIn('SingleRowHeight="17.3"', stories["st_safety_symbols_signals"])
        self.assertIn('SingleRowHeight="25.42"', stories["st_safety_symbols_signals"])
        self.assertIn('SingleRowHeight="15"', stories["st_safety_symbols_icons_left"])
        self.assertIn('SingleRowHeight="30.7"', stories["st_safety_symbols_icons_left"])
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
        self.assertIn(
            'Name="0:0" RowSpan="1" ColumnSpan="1" '
            'AppliedCellStyle="CellStyle/$ID/[None]" '
            'FillColor="Color/HB Bg K05"',
            stories["st_safety_symbols_signals"],
        )
        self.assertIn(
            'Name="0:1" RowSpan="1" ColumnSpan="1" '
            'AppliedCellStyle="CellStyle/$ID/[None]" '
            'FillColor="Color/HB Bg K05"',
            stories["st_safety_symbols_icons_left"],
        )
        self.assertIn(
            'Name="0:1" RowSpan="1" ColumnSpan="1" '
            'AppliedCellStyle="CellStyle/$ID/[None]" '
            'FillColor="Color/HB Bg K05"',
            stories["st_safety_symbols_icons_right"],
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
        spread_id, symbol_overflow = w.add_safety_symbols_page(
            "st_safety_symbols_tpl",
            [],
            [("h1", "USER MAINTENANCE INSTRUCTIONS"), ("body", "Body.")],
            signals,
            icons,
            ROOT,
            4,
            "en",
        )
        self.assertEqual(spread_id, "sp_4")
        self.assertEqual(symbol_overflow, ([], []))
        stories = dict(w.stories)
        left = stories["st_safety_symbols_tpl_icons_left"]
        right = stories["st_safety_symbols_tpl_icons_right"]
        self.assertIn("Heavy object", left)
        self.assertNotIn("Do not dismantle", left)
        self.assertIn("Do not dismantle the product.", right)
        self.assertIn("Keep away from children.", right)
        self.assertNotIn("Batteries and accumulators", left + right)

    def test_dense_safety_symbols_page_returns_reference_continuation_rows(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        icons = [
            {"figure": "1_warning_triangle.png", "text": "Avertissement"},
            {"figure": "2_read_manual.png", "text": "Lire le manuel"},
            {"figure": "3_electric_shock.png", "text": "Choc électrique"},
            {"figure": "4_battery_charging.png", "text": "Charge de batterie"},
            {"figure": "7_do_not_dismantle.png", "text": "Ne démontez pas"},
            {"figure": "8_no_open_flame.png", "text": "Pas de flamme"},
            {"figure": "9_keep_away_from_children.png", "text": "Pas d’enfants"},
            {"figure": "10_li_ion.png", "text": "Batterie lithium-ion"},
            {"figure": "5_explosive_material.png", "text": "Matière explosive"},
            {"figure": "6_heavy_object.png", "text": "Objet lourd"},
            {"figure": "11_weee.png", "text": "Collecte séparée"},
            {"figure": "12_weee2.png", "text": "Piles et accumulateurs"},
        ]
        w = IdmlWriter(params)
        spread_id, (overflow_left, overflow_right) = w.add_safety_symbols_page(
            "st_safety_symbols_dense",
            [],
            [("h1", "ENTRETIEN"), ("body", "Corps.")],
            [("AVERTISSEMENT", "Pratique dangereuse.")],
            icons,
            ROOT,
            22,
            "fr",
            dense=True,
        )

        self.assertEqual(spread_id, "sp_22")
        self.assertEqual(
            [row["text"] for row in overflow_left],
            ["Matière explosive", "Objet lourd"],
        )
        self.assertEqual(
            [row["text"] for row in overflow_right],
            ["Collecte séparée"],
        )
        stories = dict(w.stories)
        first_page = (
            stories["st_safety_symbols_dense_icons_left"]
            + stories["st_safety_symbols_dense_icons_right"]
        )
        self.assertNotIn("Matière explosive", first_page)
        self.assertNotIn("Objet lourd", first_page)
        self.assertNotIn("Collecte séparée", first_page)
        self.assertNotIn("Piles et accumulateurs", first_page)
        self.assertIn("Ne démontez pas", first_page)
        self.assertIn("Batterie lithium-ion", first_page)

    def test_localized_symbols_default_keeps_all_rows_on_current_page(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        icons = [
            {"figure": f"{number}_{number}.png", "text": f"row {number}"}
            for number in range(1, 12)
        ]
        w = IdmlWriter(params)

        _spread_id, overflow = w.add_safety_symbols_page(
            "st_safety_symbols_eu",
            [],
            [("h1", "ENTRETIEN"), ("body", "Corps.")],
            [("AVERTISSEMENT", "Pratique dangereuse.")],
            icons,
            ROOT,
            22,
            "fr",
        )

        self.assertEqual(([], []), overflow)
        stories = dict(w.stories)
        page_xml = (
            stories["st_safety_symbols_eu_icons_left"]
            + stories["st_safety_symbols_eu_icons_right"]
        )
        for number in range(1, 12):
            self.assertIn(f"row {number}", page_xml)

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
                "variant": "tip",
                "texts": ["The car charging cable is sold separately."],
            })),
        ]
        w.add_fcc_inbox_page("st_fcc_inbox", fcc, inbox, ROOT, 3)
        spread = dict(w.spreads)["sp_3"]
        self.assertEqual(spread.count("<TextFrame "), 12)
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
        self.assertIn("fcc_mark.png", stories["st_fcc_inbox_fcc_mark"])
        self.assertNotIn("fcc_mark.pdf", stories["st_fcc_inbox_fcc_mark"])
        self.assertIn("FCC right copy.", stories["st_fcc_inbox_fcc_right"])
        self.assertIn("WHAT'S IN THE BOX", stories["st_fcc_inbox_title"])
        self.assertIn("AC Charging Cable", stories["st_fcc_inbox_card_2"])
        self.assertIn(
            'PointSize="10.912" FontStyle="Medium" BaselineShift="0.45"',
            stories["st_fcc_inbox_badge_1"],
        )
        self.assertIn(">TIP<", stories["st_fcc_inbox_tip_label"])
        self.assertNotIn("TIPS", stories["st_fcc_inbox_tip_label"])
        self.assertIn(
            'PointSize="8" Leading="9" FontStyle="Bold" BaselineShift="2.63"',
            stories["st_fcc_inbox_tip_label"],
        )
        self.assertIn(
            'PointSize="6.5" Leading="7.83" FontStyle="Medium" '
            'HorizontalScale="106.9" BaselineShift="0.9"',
            stories["st_fcc_inbox_tip_body"],
        )
        self.assertIn(
            "The car charging cable is sold separately.",
            stories["st_fcc_inbox_tip_body"],
        )
        for key in ("st_fcc_inbox_card_1", "st_fcc_inbox_tip_body"):
            self.assertNotIn("<Table", stories[key])

    def test_fcc_inbox_page_prepends_native_symbol_continuation(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        fcc = [("component", json.dumps({
            "kind": "fcc",
            "texts": ["FCC gauche.", "FCC droite."],
        }))]
        inbox = [
            ("h1", "CONTENU DE LA BOÎTE"),
            ("component", json.dumps({
                "kind": "inbox",
                "items": [{"img": "", "label": "Documents"}],
            })),
        ]
        overflow = (
            [
                {"figure": "", "text": "Matière explosive"},
                {"figure": "", "text": "Objet lourd"},
            ],
            [{"figure": "", "text": "Collecte séparée"}],
        )

        w.add_fcc_inbox_page(
            "st_fcc_dense",
            fcc,
            inbox,
            ROOT,
            23,
            symbol_overflow=overflow,
            lang="fr",
        )

        spread = dict(w.spreads)["sp_23"]
        stories = dict(w.stories)
        self.assertIn("tf_st_fcc_dense_symbols_left", spread)
        self.assertIn("tf_st_fcc_dense_symbols_right", spread)
        self.assertIn("bg_st_fcc_dense_symbols_left", spread)
        self.assertIn("bg_st_fcc_dense_symbols_right", spread)
        self.assertIn("<Table ", stories["st_fcc_dense_symbols_left"])
        self.assertIn("<Table ", stories["st_fcc_dense_symbols_right"])
        self.assertIn("Matière explosive", stories["st_fcc_dense_symbols_left"])
        self.assertIn("Objet lourd", stories["st_fcc_dense_symbols_left"])
        self.assertIn("Collecte séparée", stories["st_fcc_dense_symbols_right"])
        self.assertIn(
            'SingleRowHeight="34" MinimumHeight="34" AutoGrow="false"',
            stories["st_fcc_dense_symbols_left"],
        )
        self.assertIn(
            'SingleRowHeight="68" MinimumHeight="68" AutoGrow="false"',
            stories["st_fcc_dense_symbols_right"],
        )
        self.assertNotIn("Signification", stories["st_fcc_dense_symbols_left"])
        self.assertNotIn("Signification", stories["st_fcc_dense_symbols_right"])

    def test_spanish_symbol_overflow_uses_shared_inbox_layout_profile(self) -> None:
        import xml.etree.ElementTree as ET

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        w.add_fcc_inbox_page(
            "st_fcc_es_layout",
            [("component", json.dumps({
                "kind": "fcc",
                "texts": ["Aviso izquierdo.", "Aviso derecho."],
            }))],
            [
                ("h1", "CONTENIDO DE LA CAJA"),
                ("component", json.dumps({
                    "kind": "inbox",
                    "items": [{"img": "", "label": "Documentos"}],
                })),
                ("component", json.dumps({
                    "kind": "notice",
                    "label": "CONSEJOS",
                    "texts": ["Texto de ayuda."],
                })),
            ],
            ROOT,
            42,
            symbol_overflow=([{"figure": "", "text": "Explosivo"}], []),
            lang="es",
        )
        root = ET.fromstring(dict(w.spreads)["sp_42"])

        def bounds(self_id: str) -> tuple[float, float, float, float]:
            node = next(
                item for item in root.iter()
                if item.attrib.get("Self") == self_id
            )
            points = []
            for item in node.iter("PathPointType"):
                for key in ("Anchor", "LeftDirection", "RightDirection"):
                    points.append(tuple(
                        float(value) for value in item.attrib[key].split()
                    ))
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            return (
                min(xs) + w.page_w / 2.0,
                min(ys) + w.page_h / 2.0,
                max(xs) + w.page_w / 2.0,
                max(ys) + w.page_h / 2.0,
            )

        title = bounds("tf_st_fcc_es_layout_title")
        card = bounds("bg_st_fcc_es_layout_card_1")
        tip = bounds("bg_st_fcc_es_layout_tip_strip")
        self.assertAlmostEqual(263.5 - 1.96, title[1], places=3)
        self.assertAlmostEqual(288.0, card[1], places=3)
        self.assertAlmostEqual(160.8, card[3] - card[1], places=3)
        self.assertAlmostEqual(454.0, tip[1], places=3)

    def test_fcc_long_left_copy_wraps_beside_mark_as_native_stories(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        fcc = [("component", json.dumps({
            "kind": "fcc",
            "texts": [
                "This device complies with part 15 of the FCC Rules. "
                "Operation is subject to the following two conditions: "
                "(1) This device may not cause harmful interference, and "
                "(2) this device must accept any interference received.\n\n"
                "NOTE: Tested to the applicable limits.",
                "MODIFICATION: Changes could void the user's authority.",
            ],
        }))]
        inbox = [
            ("h1", "WHAT'S IN THE BOX"),
            ("component", json.dumps({
                "kind": "inbox",
                "items": [{"img": "", "label": "Documents"}],
            })),
        ]

        w.add_fcc_inbox_page("st_fcc_wrapped", fcc, inbox, ROOT, 5)

        spread = dict(w.spreads)["sp_5"]
        stories = dict(w.stories)
        self.assertIn("tf_st_fcc_wrapped_fcc_mark", spread)
        self.assertIn("tf_st_fcc_wrapped_fcc_lead", spread)
        self.assertIn("tf_st_fcc_wrapped_fcc_left", spread)
        self.assertIn("This device complies", stories["st_fcc_wrapped_fcc_lead"])
        self.assertIn("(1) This device", stories["st_fcc_wrapped_fcc_lead"])
        self.assertNotIn("NOTE: Tested", stories["st_fcc_wrapped_fcc_lead"])
        self.assertIn("NOTE: Tested", stories["st_fcc_wrapped_fcc_left"])
        self.assertNotIn("(1) This device", stories["st_fcc_wrapped_fcc_left"])
        self.assertNotIn("This device complies", stories["st_fcc_wrapped_fcc_left"])
        self.assertIn("fcc_mark.png", stories["st_fcc_wrapped_fcc_mark"])

    def test_fcc_localized_lead_frames_follow_reference_geometry(self) -> None:
        import xml.etree.ElementTree as ET

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        copy = {
            "en": (
                "This device complies with part 15 of the FCC Rules. "
                "Operation is subject to conditions (1) and (2). "
                "NOTE: Tested to the applicable limits."
            ),
            "fr": (
                "Cet appareil est conforme à la partie 15 des règles de la FCC. "
                "Son fonctionnement est soumis aux conditions (1) et (2). "
                "REMARQUE : Cet équipement a été testé."
            ),
            "es": (
                "Este dispositivo cumple con la parte 15 de la normativa FCC. "
                "Su operación está sujeta a las condiciones (1) y (2). "
                "NOTA: Este aparato ha sido probado."
            ),
        }
        expected = {
            "en": (97.0, 50.0),
            "fr": (103.0, 62.0),
            "es": (103.0, 56.0),
        }

        def bounds(spread: str, self_id: str) -> tuple[float, float, float, float]:
            root = ET.fromstring(spread)
            frame = next(
                node for node in root.iter("TextFrame")
                if node.attrib.get("Self") == self_id
            )
            points = [
                tuple(float(value) for value in node.attrib["Anchor"].split())
                for node in frame.iter("PathPointType")
            ]
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            return min(xs), min(ys), max(xs), max(ys)

        for page_index, lang in enumerate(("en", "fr", "es"), 3):
            with self.subTest(lang=lang):
                writer = IdmlWriter(params)
                sid = f"st_fcc_geometry_{lang}"
                writer.add_fcc_inbox_page(
                    sid,
                    [("component", json.dumps({
                        "kind": "fcc",
                        "texts": [copy[lang], "MODIFICATION: Right copy."],
                    }))],
                    [
                        ("h1", "WHAT'S IN THE BOX"),
                        ("component", json.dumps({
                            "kind": "inbox",
                            "items": [{"img": "", "label": "Documents"}],
                        })),
                    ],
                    ROOT,
                    page_index,
                    lang=lang,
                )
                spread = dict(writer.spreads)[f"sp_{page_index}"]
                lead = bounds(spread, f"tf_{sid}_fcc_lead")
                lower = bounds(spread, f"tf_{sid}_fcc_left")
                lead_w, lead_h = expected[lang]
                self.assertAlmostEqual(lead_w, lead[2] - lead[0], places=3)
                self.assertAlmostEqual(lead_h, lead[3] - lead[1], places=3)
                self.assertAlmostEqual(lead[3] - 2.0, lower[1], places=3)

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
        story = (
            stories["st_fcc_plain_fcc_lead"]
            + stories["st_fcc_plain_fcc_left"]
            + stories["st_fcc_plain_fcc_right"]
        )
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
        story = "".join(
            xml for sid, xml in dict(w.stories).items()
            if sid.startswith("st_anchor_lcd_table_")
        )
        # icon cells must use the auto-leading figure style, or fixed leading
        # pushes the anchored icon a full row upward (designer-reported)
        self.assertIn(paragraph_style_ref("HB Figure"), story)
        icon_cell = story.split('Self="tbl_lcdc0_1"', 1)[1].split("</Cell>", 1)[0]
        self.assertIn('VerticalJustification="CenterAlign"', icon_cell)
        self.assertIn('BaselineShift="0.6"', icon_cell)
        self.assertNotIn('BaselineShift="8.9"', story)

    def test_lcd_table_matches_reference_cell_styling(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        rows = load_lcd_rows(FIXTURE_DATA_ROOT, "JE-1000F")
        w = IdmlWriter(params)
        w.add_lcd_story(rows, FIXTURE_DATA_ROOT)
        stories = dict(w.stories)
        story = "".join(
            xml for sid, xml in stories.items()
            if sid.startswith("st_anchor_lcd_table_")
        )

        self.assertEqual(2, story.count("<Table "))
        self.assertEqual(2, stories["st_lcd"].count("<Group "))
        self.assertIn('StartParagraph="NextPage"', stories["st_lcd"])

        for column in range(4):
            cell = story.split(f'Self="tbl_lcdc0_{column}"', 1)[1].split(
                "</Cell>", 1
            )[0]
            self.assertIn('VerticalJustification="CenterAlign"', cell)
            if column < 3:
                self.assertIn('FillColor="Color/HB Bg K05"', cell)
            else:
                self.assertNotIn('FillColor="Color/HB Bg K05"', cell)

        label_cell = story.split('Self="tbl_lcdc0_2"', 1)[1].split("</Cell>", 1)[0]
        self.assertIn('FontStyle="Bold"', label_cell)
        self.assertIn('PointSize="7" Leading="8.4"', label_cell)
        self.assertIn('LeftInset="5.2"', label_cell)
        description_cell = story.split('Self="tbl_lcdc0_3"', 1)[1].split(
            "</Cell>", 1
        )[0]
        self.assertIn('PointSize="5.5" Leading="5.8"', description_cell)
        self.assertIn('LeftInset="5.2"', description_cell)
        number_cell = story.split('Self="tbl_lcdc0_0"', 1)[1].split("</Cell>", 1)[0]
        self.assertIn('PointSize="9" Leading="9.4"', number_cell)
        self.assertIn('TopInset="1.62" BottomInset="1.62"', number_cell)
        continuation_cell = story.split(
            'Self="tbl_lcd_cont_enc7_0"', 1
        )[1].split("</Cell>", 1)[0]
        self.assertIn(
            'TopInset="2.14" BottomInset="2.14"', continuation_cell)
        self.assertIn(
            '<AppliedFont type="string">Apple SD Gothic Neo</AppliedFont>',
            number_cell,
        )

    def test_lcd_story_bounds_long_continuations_as_separate_rounded_tables(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        rows = [
            {
                "no": str(index),
                "figure": "",
                "name": f"Indicator {index}",
                "desc": f"Description {index}",
            }
            for index in range(1, 27)
        ]
        w = IdmlWriter(params)
        w.add_lcd_story(rows, FIXTURE_DATA_ROOT)
        stories = dict(w.stories)

        self.assertEqual(2, stories["st_lcd"].count("<Group "))
        self.assertEqual(2, w.lcd_segment_counts["en"])
        self.assertIn("st_anchor_lcd_table_en_1", stories)
        self.assertNotIn("st_anchor_lcd_table_en_2", stories)
        self.assertNotIn('<ParagraphStyleRange LeftIndent="5.2"', stories["st_lcd"])

    def test_lcd_locale_default_precedes_foreign_generic_density_role(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        rows = [
            {
                "no": str(index),
                "figure": "",
                "name": f"Indicador {index}",
                "desc": f"Descripción {index}",
                "typography_role": "battery_saving" if index == 8 else "default",
            }
            for index in range(1, 9)
        ]
        w = IdmlWriter(params)
        w.add_lcd_story(rows, FIXTURE_DATA_ROOT, lang="es")
        continuation = dict(w.stories)["st_anchor_lcd_table_es_1"]
        description_cell = continuation.split(
            'Self="tbl_lcd_cont_esc7_3"', 1
        )[1].split("</Cell>", 1)[0]
        self.assertIn('PointSize="5.5" Leading="6"', description_cell)
        self.assertNotIn('PointSize="5.8"', description_cell)

    def test_lcd_high_circled_numbers_use_a_font_that_covers_them(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        for number in ("㉑", "㉗"):
            with self.subTest(number=number):
                psr = IdmlWriter(params)._psr(
                    "HB Spec Label", number, terminal=True)
                self.assertIn(
                    '<Properties><AppliedFont type="string">'
                    'Apple SD Gothic Neo</AppliedFont>',
                    psr,
                )

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
