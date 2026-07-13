from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from tools.attachment_identity import stage_bundle_attachment_aliases
from tools.export_idml import IdmlWriter, load_layout_params
from tools.idml import ir_projection, page_placed, page_toc
from tools.idml.components.base import RenderContext
from tools.idml.components.prose_table import render_table_block
from tools.idml.page_objects import (
    anchored_panel_group_paragraph,
    h1_bar_h_pt,
    heading_bar_opts,
    rounded_path_geometry,
)
from tools.idml.params import param_pt
from tools.idml.styles import para_styles


ROOT = Path(__file__).resolve().parents[1]


class IdmlVisualParityTests(unittest.TestCase):
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
        self.assertEqual((8.6, 9.4, "Heavy"), styles["HB Title L2"])
        self.assertEqual((8.0, 8.0, "Bold"), styles["HB Data Code"])
        self.assertEqual((8.0, 9.6, "Bold"), styles["HB Spec Section"])
        self.assertEqual((6.0, 6.6, "Medium"), styles["HB Spec Label"])

    def test_h1_bar_height_uses_the_explicit_shared_height_token(self) -> None:
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        self.assertAlmostEqual(
            param_pt(writer.params, "comp_h1_pill_height", 20.126),
            h1_bar_h_pt(writer),
            places=5,
        )

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
            'PointSize="7" FontStyle="Medium"',
            stories["st_toc_bar_label_0"],
        )
        self.assertIn("ParagraphStyle/HB TOC Entry", stories["st_toc_seg0_c0"])
        self.assertIn('FontStyle="Medium"', stories["st_toc_seg0_c0"])
        self.assertIn('PointSize="7" FontStyle="Regular"', stories["st_toc_seg0_c0"])
        self.assertNotIn("HB Big Numeral", stories["st_toc_title"])
        self.assertNotIn("HB Spec Label", stories["st_toc_seg0_c0"])

        toc_xml = dict(writer.spreads)["sp_toc"]
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

    def test_product_overview_reuses_the_shared_finished_art_for_every_language(self) -> None:
        docs = ROOT / "docs"
        self.assertEqual(
            docs / "renderers" / "latex" / "assets" / "product_overview-en.pdf",
            page_placed.placed_asset_for(
                "03_product_overview_placeholder", "en", docs),
        )
        self.assertEqual(
            docs / "renderers" / "latex" / "assets" / "product_overview-fr.pdf",
            page_placed.placed_asset_for(
                "03_product_overview_placeholder", "fr", docs),
        )

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
        self.assertIn('FillColor="Color/HB Header K08"', auto_story)
        self.assertIn('FillColor="Color/HB Bg K05"', auto_story)
        self.assertIn('MinimumHeight="11.9055"', auto_story)
        self.assertIn('<Group Self="grp_st_anchor_data_tbl_auto"', auto_xml)
        self.assertIn('SingleColumnWidth="158.057"', auto_story)
        self.assertIn('LeftInset="0"', auto_story)

        key_rows = [
            ["Buttons", "Operation", "Function"],
            ["Main POWER button", "Press and hold", "Turn on/off"],
        ]
        render_table_block(key_rows, ctx, tid="tbl_key", terminal=True)
        key_story = dict(writer.stories)["st_anchor_data_tbl_key"]
        self.assertIn('MinimumHeight="32.8819"', key_story)
        self.assertIn('SingleColumnWidth="130.104"', key_story)
        self.assertIn('SingleColumnWidth="95.2224"', key_story)
        self.assertIn('AppliedParagraphStyle="ParagraphStyle/HB Data Header"', key_story)
        self.assertIn('AppliedParagraphStyle="ParagraphStyle/HB Data Body"', key_story)

    def test_explicit_story_frames_merge_two_stories_on_one_spread(self) -> None:
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        writer.add_story_frames("story_top", [(7, 20.0, 190.0)])
        writer.add_story_frames("story_bottom", [(7, 200.0, 500.0)])
        self.assertEqual(1, len(writer.spreads))
        xml = writer.spreads[0][1]
        self.assertIn('ParentStory="story_top"', xml)
        self.assertIn('ParentStory="story_bottom"', xml)

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
        self.assertIn('MinimumHeight="57.61" AutoGrow="true"', table_story)
        self.assertIn('MinimumHeight="31.96" AutoGrow="true"', table_story)
        self.assertIn('TopEdgeStrokeWeight="0.25"', table_story)
        self.assertIn('TopEdgeStrokeColor="Color/HB Brand Dark"', table_story)


if __name__ == "__main__":
    unittest.main()
