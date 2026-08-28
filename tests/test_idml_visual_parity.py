from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from tools.attachment_identity import (
    resolve_semantic_attachment,
    semantic_attachment_key,
    stage_bundle_attachment_aliases,
)
from tools.export_idml import IdmlWriter, load_layout_params
from tools.idml import ir_projection, page_placed, page_toc
from tools.idml.components.base import RenderContext
from tools.idml.components.notice import notice_box_layout
from tools.idml.components.prose_table import render_table_block
from tools.idml.components.rounded_table import rounded_table_panel, table_text_indent
from tools.idml.page_objects import (
    anchored_panel_group_paragraph,
    h1_bar_h_pt,
    h1_frame_opts,
    h1_pill_paragraph,
    heading_bar_opts,
    heading_text,
    left_rounded_path_geometry,
    rounded_path_geometry,
)
from tools.idml.params import param_pt
from tools.idml.styles import para_styles
from tools.idml.prose_paragraph import build_text_paragraph


ROOT = Path(__file__).resolve().parents[1]


class IdmlVisualParityTests(unittest.TestCase):
    def test_tip_notice_uses_the_frozen_latex_geometry_and_type(self) -> None:
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        text = (
            "The car charging cable is not included but is available for purchase "
            "separately on our website. For assistance, please contact Jackery "
            "customer service."
        )
        tip = notice_box_layout(
            writer.params, 311.0, "TIP", [text], variant="tip")
        note = notice_box_layout(
            writer.params, 311.0, "NOTE", ["Short note."], variant="note")

        self.assertAlmostEqual(41.6693, tip.panel_height, places=3)
        self.assertAlmostEqual(6.10394, tip.arc, places=3)
        self.assertAlmostEqual(1.24724, tip.plate_left, places=3)
        self.assertAlmostEqual(5.45197, tip.body_inset, places=3)
        self.assertAlmostEqual(1.069, tip.body_horizontal_scale, places=3)
        self.assertAlmostEqual(2.63, tip.label_baseline_shift, places=3)
        self.assertAlmostEqual(0.9, tip.body_baseline_shift, places=3)
        self.assertLess(note.panel_height, tip.panel_height)

        plate = left_rounded_path_geometry(0.0, 0.0, 50.0, 40.0, 5.0)
        self.assertIn(
            'Anchor="50 0" LeftDirection="50 0" RightDirection="50 0"',
            plate,
        )
        self.assertIn(
            'Anchor="50 40" LeftDirection="50 40" RightDirection="50 40"',
            plate,
        )

    def test_subbar_text_frame_is_vertically_centered(self) -> None:
        self.assertEqual(
            "CenterAlign",
            heading_bar_opts(2, (0.5, 0, 0.5, 0))["valign"],
        )

    def test_english_data_table_type_matches_the_production_master(self) -> None:
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        styles = {
            name: (size, leading, weight)
            for name, size, leading, weight, _kind in para_styles(writer.params)
        }
        self.assertEqual((6.6, 7.0, "Heavy"), styles["HB Data Header"])
        self.assertEqual((8.0, 9.4, "Bold"), styles["HB Title L2"])
        self.assertEqual((8.0, 8.0, "Bold"), styles["HB Data Code"])
        self.assertEqual((8.0, 9.6, "Bold"), styles["HB Spec Section"])
        self.assertEqual((6.0, 6.6, "Medium"), styles["HB Spec Label"])
        self.assertEqual((8.0, 9.0, "Bold"), styles["HB Callout Label"])
        self.assertEqual((6.5, 7.83, "Medium"), styles["HB Callout Body"])

    def test_h1_bar_height_uses_the_explicit_shared_height_token(self) -> None:
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        self.assertAlmostEqual(
            param_pt(writer.params, "comp_h1_pill_height", 20.126),
            h1_bar_h_pt(writer),
            places=5,
        )

    def test_fixed_and_flowed_h1_share_the_je_visible_cap_centre(self) -> None:
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        rect = (28.35, 27.92, 312.09, h1_bar_h_pt(writer))
        opts = h1_frame_opts(rect)
        fixed = heading_text(writer, "IMPORTANT SAFETY INFORMATION", level=1)
        h1_pill_paragraph(writer, "STORAGE", rect[2])
        flowed = dict(writer.stories)["st_anchor_h1pill_0"]

        self.assertEqual("CenterAlign", opts["valign"])
        self.assertEqual((34.35, 27.92, 300.09, rect[3]), opts["text_rect"])
        for story in (fixed, flowed):
            self.assertIn('BaselineShift="0.5"', story)
            self.assertNotIn('BaselineShift="-1.5"', story)

    def test_heading_styles_derive_keep_with_next_from_shared_needspace(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        writer = IdmlWriter(params)
        styles = writer.styles_xml()
        l2 = styles.split('Name="Heading2"', 1)[1].split(">", 1)[0]
        l3 = styles.split('Name="Heading3"', 1)[1].split(">", 1)[0]

        self.assertIn('KeepWithNext="3"', l2)
        self.assertIn('KeepWithNext="3"', l3)

        params["comp_title_l2_needspace"] = ("5", "pt")
        smaller = IdmlWriter(params).styles_xml()
        smaller_l2 = smaller.split('Name="Heading2"', 1)[1].split(">", 1)[0]
        self.assertIn('KeepWithNext="1"', smaller_l2)

    def test_prose_lists_select_language_density_styles(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        params["lang_fr_type_list_font_leading"] = ("6.8", "pt")
        params["lang_es_type_list_font_leading"] = ("6.6", "pt")
        writer = IdmlWriter(params)
        styles = {
            name: leading
            for name, _size, leading, _weight, _kind in para_styles(params)
        }
        self.assertEqual(6.8, styles["HB List FR"])
        self.assertEqual(6.6, styles["HB Sublist ES"])

        for language, semantic, expected in (
            ("en", "list", "ParagraphStyle/Item List"),
            ("fr", "list", "ParagraphStyle/HB List FR"),
            ("es", "sublist", "ParagraphStyle/HB Sublist ES"),
        ):
            with self.subTest(language=language, semantic=semantic):
                paragraph, *_ = build_text_paragraph(
                    writer,
                    kind=semantic,
                    text="• Copy",
                    terminal=True,
                    is_preface=False,
                    has_twocol_layout=False,
                    in_twocol=False,
                    bundle_root=ROOT,
                    page_language=language,
                    story_id="st_list",
                    block_index=0,
                )
                self.assertIn(expected, paragraph)

    def test_app_headings_and_lists_emit_fixed_tab_alignment(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        writer = IdmlWriter(params)

        heading, *_ = build_text_paragraph(
            writer,
            kind="h2_app",
            text="4. Notes",
            terminal=True,
            is_preface=False,
            has_twocol_layout=False,
            in_twocol=False,
            bundle_root=ROOT,
            page_language="en",
            story_id="st_app_heading",
            block_index=0,
        )
        self.assertIn('<Position type="unit">5.7</Position>', heading)
        self.assertIn(
            'PointSize="5.4" BaselineShift="1.25">',
            heading,
        )
        self.assertIn("<Content>●</Content>", heading)
        self.assertIn("<Content>\t4. Notes</Content>", heading)
        self.assertNotIn("<Content> 4. Notes</Content>", heading)

        params["idml_app_h2_marker_font_size"] = ("5.1", "pt")
        params["idml_app_h2_marker_baseline_shift"] = ("0.8", "pt")
        adjusted, *_ = build_text_paragraph(
            IdmlWriter(params),
            kind="h2_app",
            text="4. Notes",
            terminal=True,
            is_preface=False,
            has_twocol_layout=False,
            in_twocol=False,
            bundle_root=ROOT,
            page_language="en",
            story_id="st_app_heading_adjusted",
            block_index=0,
        )
        self.assertIn('PointSize="5.1" BaselineShift="0.8"', adjusted)

        for language, copy in (
            ("en", "• Wi-Fi and Bluetooth are enabled."),
            ("fr", "• Le Wi-Fi et le Bluetooth sont activés."),
        ):
            with self.subTest(language=language):
                item, *_ = build_text_paragraph(
                    writer,
                    kind="list_app",
                    text=copy,
                    terminal=True,
                    is_preface=False,
                    has_twocol_layout=False,
                    in_twocol=False,
                    bundle_root=ROOT,
                    page_language=language,
                    story_id=f"st_app_list_{language}",
                    block_index=0,
                )
                self.assertIn('<Position type="unit">11.4</Position>', item)
                self.assertIn("<Content>•\t", item)
                self.assertNotIn("<Content>• ", item)

    def test_target_assembly_headings_use_font_independent_vector_markers(
        self,
    ) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        writer = IdmlWriter(params, native_structure_markers=True)

        heading, *_ = build_text_paragraph(
            writer,
            kind="h2",
            text="AC OUTPUT ON/OFF",
            terminal=True,
            is_preface=False,
            has_twocol_layout=False,
            in_twocol=False,
            bundle_root=ROOT,
            page_language="en",
            story_id="st_operation",
            block_index=2,
        )

        self.assertNotIn("<Content>●</Content>", heading)
        self.assertNotIn("Segoe UI Symbol", heading)
        self.assertIn("st_operation_h2_marker_2_circle", heading)
        self.assertIn('FillColor="Color/HB Brand Dark"', heading)
        self.assertIn("st_operation_h2_marker_2_gap", heading)

        writer.add_spec_story(
            [{
                "title": "GENERAL INFO",
                "rows": [
                    ("Chemistry", "LiFePO₄"),
                    ("Input", "36.8V⎓75A"),
                ],
            }],
            [],
            lang="en",
            title="SPECIFICATIONS",
        )
        spec_story = dict(writer.stories)["st_spec"]
        self.assertNotIn("<Content>●</Content>", spec_story)
        self.assertNotIn("Segoe UI Symbol", spec_story)
        self.assertIn("st_spec_section_marker_0_circle", spec_story)
        spec_xml = "".join(
            xml
            for story_id, xml in writer.stories
            if story_id == "st_spec" or story_id.startswith("st_anchor_spec_")
        )
        self.assertIn("st_spec_spec_symbol_3_direct_current", spec_xml)
        self.assertIn(
            "st_spec_spec_symbol_3_direct_current_left_bearing",
            spec_xml,
        )
        self.assertIn(
            "st_spec_spec_symbol_3_direct_current_right_bearing",
            spec_xml,
        )
        self.assertIn('StrokeWeight="0.408691"', spec_xml)
        self.assertIn('Anchor="0 -1.88965"', spec_xml)
        self.assertIn('Anchor="3.68555 -1.88965"', spec_xml)
        self.assertNotIn('Anchor="7 -3.8"', spec_xml)
        self.assertIn('Position="Subscript"', spec_xml)
        self.assertIn("<Content>4</Content>", spec_xml)
        self.assertNotIn("Segoe UI Symbol", spec_xml)

        warranty, _ = writer._render_component(
            "st_warranty",
            0,
            {
                "kind": "warrantyyears",
                "items": [{
                    "number": "3",
                    "unit": "YEARS",
                    "label": "For the original buyer",
                    "text": "Limited warranty coverage.",
                }],
            },
            ROOT,
            True,
        )
        self.assertIn("Yu Gothic", warranty)
        self.assertIn("❸", warranty)

        compact_params = load_layout_params(
            ROOT / "data" / "layout_params.csv",
            (ROOT / "data" / "layout_params.idml-compact.csv",),
        )
        compact_writer = IdmlWriter(
            compact_params,
            native_structure_markers=True,
        )
        compact_warranty, _ = compact_writer._render_component(
            "st_warranty_compact",
            0,
            {
                "kind": "warrantyyears",
                "items": [{
                    "number": "3",
                    "unit": "YEARS",
                    "label": "For the original buyer",
                    "text": "Limited warranty coverage.",
                }],
            },
            ROOT,
            True,
        )
        self.assertEqual(warranty, compact_warranty.replace(
            "st_warranty_compact_cmp0",
            "st_warranty_cmp0",
        ))
        self.assertIn("❸", compact_warranty)

        base_period_writer = IdmlWriter(
            writer.params,
            native_structure_markers=False,
        )
        period_writer = IdmlWriter(
            compact_params,
            native_structure_markers=True,
        )
        period_spec = {
            "kind": "warrantysection",
            "title": "WARRANTY PERIOD",
            "index": 2,
            "blocks": [{
                "kind": "warrantyyears",
                "items": [{
                    "number": "3",
                    "unit": "YEARS",
                    "label": "Standard Warranty",
                    "text": "Limited warranty coverage.",
                }],
            }],
        }
        base_period, base_period_height = base_period_writer._render_component(
            "st_warranty_period",
            0,
            period_spec,
            ROOT,
            True,
        )
        period, period_height = period_writer._render_component(
            "st_warranty_period",
            0,
            period_spec,
            ROOT,
            True,
        )
        self.assertEqual(base_period, period)
        self.assertEqual(base_period_height, period_height)

    def test_body_table_group_uses_panel_fill_for_corner_masks(self) -> None:
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        ctx = RenderContext(
            params=writer.params,
            page_w=writer.page_w,
            m_l=writer.m_l,
            m_r=writer.m_r,
            root=ROOT,
            bundle_root=ROOT,
            add_story=writer._add_story_parts,
        )
        rows = [
            ["Auto Resume Conditions", "Not Auto Resume Conditions"],
            ["Power-on", "Manual output off"],
            ["", "Energy Saving mode output off"],
        ]
        xml, _ = render_table_block(rows, ctx, tid="auto_indent", terminal=True)
        self.assertNotIn('LeftIndent=', xml)
        self.assertIn(
            f'Anchor="{ctx.text_measure - 0.37:g} 0"',
            xml,
        )
        self.assertIn(
            'Self="mask_top_left_group_st_anchor_data_auto_indent" '
            'ContentType="Unassigned" AppliedObjectStyle="ObjectStyle/$ID/[None]" '
            'FillColor="Color/Paper"',
            xml,
        )
        self.assertIn(
            'Self="mask_bottom_left_group_st_anchor_data_auto_indent" '
            'ContentType="Unassigned" AppliedObjectStyle="ObjectStyle/$ID/[None]" '
            'FillColor="Color/Paper"',
            xml,
        )

        writer.add_prose_story(
            "st_body_table_alignment",
            "aligned body table",
            [
                ("h2", "AC AND DC Output Resume Function"),
                ("body", "The AC/DC Output Resume Function is disabled by default."),
                ("table", json.dumps(rows)),
            ],
            ROOT,
        )
        prose_story = dict(writer.stories)["st_body_table_alignment"]
        self.assertNotIn('LeftIndent=', prose_story)

    def test_full_capsule_has_a_real_incoming_upper_left_handle(self) -> None:
        radius = 7.0
        kappa = radius * 0.5522847498
        xml = rounded_path_geometry(0.0, 0.0, 100.0, 14.0, radius)
        match = re.search(
            r'Anchor="([-.0-9]+) ([-.0-9]+)" '
            r'LeftDirection="([-.0-9]+) ([-.0-9]+)"',
            xml,
        )
        self.assertIsNotNone(match)
        anchor_x, anchor_y, left_x, left_y = map(float, match.groups())
        self.assertEqual((0.0, radius), (anchor_x, anchor_y))
        self.assertAlmostEqual(0.0, left_x, places=5)
        self.assertAlmostEqual(radius - kappa, left_y, places=5)
        self.assertNotEqual((anchor_x, anchor_y), (left_x, left_y))

    def test_toc_uses_dedicated_typography_instead_of_warranty_and_spec_styles(self) -> None:
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        writer.spreads = [(f"sp_{index}", f'<Spread Self="sp_{index}"/>') for index in range(4)]
        source = {
            "title": "TABLE OF CONTENTS",
            "languages": [{
                "code": "EN",
                "label": "English",
                "page_range": "01-18",
                "entries": [
                    {"title": "OPERATIONS", "folio": "07"},
                    {"title": "WARRANTY", "folio": "16"},
                ],
            }],
        }
        self.assertTrue(page_toc.finalize(
            writer,
            page_toc.TocCollector(),
            writer._add_story_parts,
            writer._psr,
            source=source,
        ))
        stories = dict(writer.stories)
        self.assertIn("ParagraphStyle/HB TOC Title", stories["st_toc_title"])
        self.assertIn("ParagraphStyle/HB TOC Bar", stories["st_toc_bar_0"])
        self.assertIn(
            'PointSize="7" FontStyle="Bold"',
            stories["st_toc_bar_label_0"],
        )
        self.assertIn("ParagraphStyle/HB TOC Entry", stories["st_toc_seg0_c0"])
        self.assertIn('FontStyle="Medium"', stories["st_toc_seg0_c0"])
        self.assertIn('HorizontalScale="105.244"', stories["st_toc_seg0_c0"])
        self.assertIn('PointSize="7" FontStyle="Regular"', stories["st_toc_seg0_c0"])
        self.assertIn(
            '<Leader type="string"></Leader>', stories["st_toc_seg0_c0"],
        )
        self.assertNotIn('<Leader type="string">. ', stories["st_toc_seg0_c0"])
        self.assertNotIn('<Content>. </Content>', stories["st_toc_seg0_c0"])
        self.assertNotIn("HB Big Numeral", stories["st_toc_title"])
        self.assertNotIn("HB Spec Label", stories["st_toc_seg0_c0"])

        toc_xml = dict(writer.spreads)["sp_toc"]
        self.assertIn('Self="gl_toc_leader_0_0_0"', toc_xml)
        self.assertIn('StrokeType="StrokeStyle/$ID/Dashed"', toc_xml)
        self.assertIn('StrokeDashAndGap="0.976 0.976"', toc_xml)
        self.assertIn('StrokeWeight="0.25"', toc_xml)
        bar = toc_xml.split('Self="bg_toc_bar_0"', 1)[1].split(
            "</Rectangle>", 1,
        )[0]
        anchors = [
            (float(x), float(y))
            for x, y in re.findall(r'Anchor="([-.0-9]+) ([-.0-9]+)"', bar)
        ]
        left_x = min(x for x, _ in anchors)
        left_ys = sorted(y for x, y in anchors if x == left_x)
        self.assertAlmostEqual(15.852, max(y for _, y in anchors) - min(y for _, y in anchors), places=3)
        self.assertAlmostEqual(4.753, left_ys[0] - min(y for _, y in anchors), places=3)
        self.assertAlmostEqual(6.346, left_ys[1] - left_ys[0], places=3)

    def test_toc_splice_does_not_modify_the_cover_spread(self) -> None:
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        cover = '<Spread Self="sp_0"><Page Self="sp_0_pg" Name="1"/></Spread>'
        writer.spreads = [
            ("sp_0", cover),
            ("sp_1", '<Spread Self="sp_1"/>'),
            ("sp_2", '<Spread Self="sp_2"><Page Self="sp_2_pg" Name="3"/></Spread>'),
            ("sp_3", '<Spread Self="sp_3"><Page Self="sp_3_pg" Name="4"/></Spread>'),
        ]
        source = {
            "languages": [{
                "code": "EN", "label": "English", "page_range": "01-01",
                "entries": [{"title": "SAFETY", "folio": "01"}],
            }],
        }
        self.assertTrue(page_toc.finalize(
            writer, page_toc.TocCollector(), writer._add_story_parts,
            writer._psr, source=source,
        ))
        self.assertEqual(("sp_0", cover), writer.spreads[0])

    def test_stale_attachment_hash_resolves_by_unique_semantic_identity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            data_root = Path(td)
            icons = data_root / "_attachments" / "lcd_icons"
            icons.mkdir(parents=True)
            current = icons / "1_Wi-Fi_CurrentHashToken123456789.png"
            current.write_bytes(b"png")
            resolved = ir_projection._asset_path(
                Path(td) / "repo",
                data_root,
                "lcd_icons",
                "1_Wi-Fi_OldHashToken123456789012.png",
            )
            self.assertEqual(current.as_posix(), resolved)

    def test_review_bundle_stages_current_art_under_the_frozen_basename(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "bundle"
            page = bundle / "page" / "lcd.rst"
            page.parent.mkdir(parents=True)
            frozen = "1_Wi-Fi_OldHashToken123456789012.png"
            page.write_text(
                ".. image:: .tmp/review-start/phase2/_attachments/lcd_icons/"
                + frozen + "\n",
                encoding="utf-8",
            )
            current_dir = root / "phase2" / "_attachments" / "lcd_icons"
            current_dir.mkdir(parents=True)
            current = current_dir / "1_Wi-Fi_CurrentHashToken123456789.png"
            current.write_bytes(b"current-art")

            report = stage_bundle_attachment_aliases(bundle, root / "phase2")

            self.assertEqual(1, report.aliases)
            self.assertEqual(1, report.rewritten_files)
            self.assertEqual((), report.missing)
            staged = (
                bundle / "_repo_assets" / "data" / "phase2" /
                "_attachments" / "lcd_icons" / frozen
            )
            self.assertEqual(b"current-art", staged.read_bytes())
            self.assertIn(
                "_repo_assets/data/phase2/_attachments/lcd_icons/" + frozen,
                page.read_text(encoding="utf-8"),
            )

    def test_attachment_identity_ignores_changed_display_ordinal(self) -> None:
        frozen = "1_warning_triangle_OldHashToken123456789012.png"
        current = "10_warning_triangle_CurrentHashToken123456789.png"
        self.assertEqual(
            semantic_attachment_key(frozen),
            semantic_attachment_key(current),
        )

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "bundle"
            page = bundle / "page" / "symbols.rst"
            page.parent.mkdir(parents=True)
            page.write_text(
                ".. image:: .tmp/review-start/phase2/_attachments/symbols/"
                + frozen
                + "\n",
                encoding="utf-8",
            )
            current_dir = root / "phase2" / "_attachments" / "symbols"
            current_dir.mkdir(parents=True)
            (current_dir / current).write_bytes(b"current-art")

            report = stage_bundle_attachment_aliases(bundle, root / "phase2")

            self.assertEqual(1, report.aliases)
            self.assertEqual((), report.missing)
            staged = (
                bundle
                / "_repo_assets"
                / "data"
                / "phase2"
                / "_attachments"
                / "symbols"
                / frozen
            )
            self.assertEqual(b"current-art", staged.read_bytes())

    def test_attachment_identity_rejects_ambiguous_reordered_matches(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            (directory / "1_warning_triangle_FirstHashToken123456789.png").write_bytes(
                b"first"
            )
            (directory / "10_warning_triangle_SecondHashToken12345678.png").write_bytes(
                b"second"
            )

            with self.assertRaisesRegex(ValueError, "ambiguous semantic attachment"):
                resolve_semantic_attachment(
                    directory,
                    "2_warning_triangle_FrozenHashToken123456789.png",
                )

    def test_product_overview_finished_art_is_not_a_production_idml_asset(self) -> None:
        docs = ROOT / "docs"
        self.assertIsNone(page_placed.placed_asset_for(
            "03_product_overview_placeholder", "en", docs))
        self.assertIsNone(page_placed.placed_asset_for(
            "03_product_overview_placeholder", "fr", docs))

    def test_rounded_table_group_keeps_a_square_editable_content_frame(self) -> None:
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        xml = anchored_panel_group_paragraph(
            writer._add_story_parts,
            "st_anchor_test_table",
            "test table",
            [writer._psr("HB Body", "editable", terminal=True)],
            100.0,
            50.0,
        )
        self.assertIn('<Group Self="grp_st_anchor_test_table"', xml)
        self.assertIn('<Rectangle Self="bg_group_st_anchor_test_table"', xml)
        self.assertIn('<TextFrame Self="tf_group_st_anchor_test_table"', xml)
        self.assertIn('ParentStory="st_anchor_test_table"', xml)
        self.assertEqual(4, xml.count('Self="mask_'))
        self.assertIn(
            '<Rectangle Self="outline_group_st_anchor_test_table"', xml)
        background = xml.split(
            '<Rectangle Self="bg_group_st_anchor_test_table"', 1
        )[1].split('</Rectangle>', 1)[0]
        self.assertIn('StrokeColor="Swatch/None" StrokeWeight="0"', background)
        outline = xml.split(
            '<Rectangle Self="outline_group_st_anchor_test_table"', 1
        )[1].split('</Rectangle>', 1)[0]
        self.assertIn('FillColor="Swatch/None"', outline)

    def test_shared_rounded_table_component_owns_frame_and_text_indent(self) -> None:
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        indent = table_text_indent(writer.params)
        self.assertAlmostEqual(5.2, indent, places=3)
        xml = rounded_table_panel(
            writer._add_story_parts,
            writer.params,
            sid="st_anchor_shared_table",
            title="shared table",
            table_xml=writer._component_table(
                "tbl_shared",
                [50.0, 50.0],
                [
                    writer._cell(
                        "tbl_shared_c0", "0:0", writer._psr("HB Body", "A"),
                        left=indent, right=indent,
                    ),
                    writer._cell(
                        "tbl_shared_c1", "1:0", writer._psr("HB Body", "B"),
                        left=indent, right=indent,
                    ),
                ],
                n_rows=1,
                role="data",
            ),
            width=100.0,
            height=20.0,
            n_cols=2,
            terminal=True,
        )
        self.assertIn('<Group Self="grp_st_anchor_shared_table"', xml)
        story = dict(writer.stories)["st_anchor_shared_table"]
        self.assertIn('LeftEdgeStrokeWeight="0"', story)
        self.assertIn('RightEdgeStrokeWeight="0"', story)
        for corner in ("top_left", "top_right", "bottom_left", "bottom_right"):
            mask = xml.split(
                f'Self="mask_{corner}_group_st_anchor_shared_table"',
                1,
            )[1].split(">", 1)[0]
            self.assertIn('FillColor="Color/Paper"', mask)

    def test_operation_data_tables_share_latex_table_tokens(self) -> None:
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        ctx = RenderContext(
            params=writer.params,
            page_w=writer.page_w,
            m_l=writer.m_l,
            m_r=writer.m_r,
            root=ROOT,
            bundle_root=ROOT / "docs",
            add_story=writer._add_story_parts,
        )
        auto_rows = [
            ["Auto Resume Conditions", "Not Auto Resume Conditions"],
            ["Power-on/Restart", "Manual output off"],
            ["Battery SOC", "Energy Saving mode output off"],
            ["", "Protection-triggered output off"],
            ["OTA upgrade completed", "Discharge timer-triggered output off"],
        ]
        auto_xml, _ = render_table_block(
            auto_rows, ctx, tid="tbl_auto", terminal=True)
        auto_story = dict(writer.stories)["st_anchor_data_tbl_auto"]
        self.assertIn('RowSpan="2"', auto_story)
        self.assertNotIn('Self="tbl_autoc3_0"', auto_story)
        self.assertNotIn('FillColor="Color/Paper"', auto_story)
        self.assertNotIn('FillColor="Color/HB Header K08"', auto_story)
        self.assertIn('FillColor="Color/HB Bg K05"', auto_story)
        left_header = auto_story.split(
            '<Cell Self="tbl_autoc0_0" ', 1,
        )[1].split("</Cell>", 1)[0]
        right_header = auto_story.split(
            '<Cell Self="tbl_autoc0_1" ', 1,
        )[1].split("</Cell>", 1)[0]
        self.assertIn('FillColor="Color/HB Bg K05"', left_header)
        self.assertNotIn("FillColor=", right_header)
        self.assertIn(
            'SingleRowHeight="11.49" MinimumHeight="11.49" AutoGrow="false"',
            auto_story,
        )
        self.assertIn('<Group Self="grp_st_anchor_data_tbl_auto"', auto_xml)
        self.assertIn('SingleColumnWidth="157.52"', auto_story)
        self.assertIn('ItemTransform="1 0 0 1 -0.37 0"', auto_xml)
        self.assertIn('LeftIndent="0"', auto_xml)
        self.assertIn('FirstLineIndent="-6.82"', auto_xml)
        self.assertIn('SpaceBefore="6.62"', auto_xml)
        indent = table_text_indent(writer.params)
        self.assertIn(f'LeftInset="{indent:g}"', auto_story)
        self.assertNotIn('LeftInset="0"', auto_story)

        key_rows = [
            ["Buttons", "Operation", "Function"],
            ["Main POWER button", "Press and hold", "Turn on/off"],
        ]
        render_table_block(key_rows, ctx, tid="tbl_key", terminal=True)
        key_story = dict(writer.stories)["st_anchor_data_tbl_key"]
        self.assertIn('FillColor="Color/HB Header K08"', key_story)
        self.assertIn('MinimumHeight="32.8819"', key_story)
        self.assertIn('SingleColumnWidth="131.074"', key_story)
        self.assertIn('SingleColumnWidth="95.7259"', key_story)
        self.assertIn('AppliedParagraphStyle="ParagraphStyle/HB Data Header"', key_story)
        self.assertIn('AppliedParagraphStyle="ParagraphStyle/HB Data Body"', key_story)
        self.assertIn(f'LeftInset="{indent:g}"', key_story)

    def test_explicit_story_frames_merge_two_stories_on_one_spread(self) -> None:
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        writer.add_story_frames("story_top", [(7, 20.0, 190.0)])
        writer.add_story_frames("story_bottom", [(7, 200.0, 500.0)])
        self.assertEqual(1, len(writer.spreads))
        xml = writer.spreads[0][1]
        self.assertIn('ParentStory="story_top"', xml)
        self.assertIn('ParentStory="story_bottom"', xml)

    def test_preface_story_frame_accepts_page_specific_margins(self) -> None:
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        writer.add_story_frames(
            "preface", [(1, 53.86, 487.84)],
            margin_left=35.4331, margin_right=35.4331,
        )
        xml = writer.spreads[0][1]
        self.assertIn('ParentStory="preface"', xml)
        self.assertIn('Anchor="-148.961 -208.486"', xml)

    def test_troubleshooting_rows_emit_operational_minimum_heights(self) -> None:
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        ctx = RenderContext(
            params=writer.params,
            page_w=writer.page_w,
            m_l=writer.m_l,
            m_r=writer.m_r,
            root=ROOT,
            bundle_root=ROOT / "docs",
            add_story=writer._add_story_parts,
        )
        rows = [["Error Code", "Corrective Measures"]]
        rows.extend([[f"F{index}", "Restart the product."] for index in range(6)])
        rows.extend([
            ["F6", "1. First|2. Second|3. Third|4. Fourth|5. Fifth"],
            ["F7", "1. First|2. Second|3. Third"],
            ["F8", "Contact support."],
            ["F9", "Remove the load."],
            ["FE", "Contact support."],
        ])

        render_table_block(rows, ctx, tid="tbl_test_trouble", terminal=True)

        table_story = dict(writer.stories)["st_anchor_trouble_tbl_test_trouble"]
        self.assertIn('MinimumHeight="62.03" AutoGrow="true"', table_story)
        self.assertIn('MinimumHeight="38.67" AutoGrow="true"', table_story)
        self.assertIn('PointSize="5.5"', table_story)
        self.assertIn('FontStyle="Bold"', table_story)
        self.assertIn('TopEdgeStrokeWeight="0.25"', table_story)
        self.assertIn('TopEdgeStrokeColor="Color/HB Brand Dark"', table_story)

    def test_localized_troubleshooting_headers_use_shared_rounded_component(self) -> None:
        for header, language in (
            ("Code d'erreur", "fr"),
            ("Código de fallo", "es"),
            ("Código de error", "es"),
            ("오류 코드", "ko"),
        ):
            writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
            ctx = RenderContext(
                params=writer.params,
                page_w=writer.page_w,
                m_l=writer.m_l,
                m_r=writer.m_r,
                root=ROOT,
                bundle_root=ROOT / "docs",
                language=language,
                add_story=writer._add_story_parts,
            )
            render_table_block(
                [[header, "Mesures correctives"], ["F0", "Redémarrer le produit."]],
                ctx,
                tid="tbl_localized_trouble",
                terminal=True,
            )
            self.assertIn(
                'st_anchor_trouble_tbl_localized_trouble',
                dict(writer.stories),
            )


if __name__ == "__main__":
    unittest.main()
