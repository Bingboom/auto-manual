#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Component registry contract (componentization P2).

The registry is the extension point for new manual components: every kind
the extractor can emit must have a renderer, every renderer must produce
render output for a minimal spec, and the writer façade must dispatch
through the registry (no forked logic).
"""
from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MINIMAL_SPECS: dict[str, dict] = {
    "inbox": {"kind": "inbox", "items": [{"img": "", "label": "Unit"}]},
    "safetywarning": {"kind": "safetywarning", "texts": ["Risk text."]},
    "safetyinstruction": {"kind": "safetyinstruction", "texts": ["Instruction text."]},
    "warninglead": {"kind": "warninglead", "label": "WARNING", "texts": ["Lead."]},
    "tailwarnbox": {"kind": "tailwarnbox", "label": "WARNING", "texts": ["Tail."]},
    "warnbox": {"kind": "warnbox", "label": "DANGER", "texts": ["Boxed."]},
    "notice": {"kind": "notice", "label": "NOTE", "texts": ["Note text."]},
    "fcc": {"kind": "fcc", "texts": ["Left copy.", "Right copy."]},
    "lcdmode": {"kind": "lcdmode", "img": "",
                "groups": [{"state": "On", "actions": [["Press", "Wakes"]]}]},
    "oppanel": {"kind": "oppanel", "image": "", "prereq": "Prerequisite: powered on.",
                "rows": [["On", "Press once"], ["Off", "Press once"]]},
    "langtag": {"kind": "langtag", "lang": "EN", "texts": ["IMPORTANT"]},
    "warrantyyears": {"kind": "warrantyyears", "items": [
        {"number": "3", "unit": "YEARS", "label": "Standard", "text": "Copy."}]},
    "warrantylead": {"kind": "warrantylead", "texts": ["Purchase-channel lead."]},
    "warrantysection": {"kind": "warrantysection", "title": "Limited Warranty",
                        "index": 1, "blocks": [{"kind": "body", "text": "Copy."}]},
    "emphasispill": {"kind": "emphasispill", "texts": ["Charge before first use."]},
    "headingpill": {
        "kind": "headingpill",
        "heading": "CHARGING VIA SOLAR PANELS",
        "pill": "SOLD SEPARATELY",
    },
    "referencefigure": {
        "kind": "referencefigure",
        "layout": "charging_ac",
        "image": "",
        "caption": "Editable caption.",
    },
}


def _ctx():
    from tools.idml.components import RenderContext

    return RenderContext(params={}, page_w=368.79, m_l=28.35, m_r=28.35,
                         root=ROOT, bundle_root=ROOT / "does-not-exist")


def _guidance_stack_spec(image: str, guidance: list | None = None) -> dict:
    """An `oppanel` spec already promoted to the guidance-stack layout.

    Shape mirrors what `tools.idml.oppanel.promote_operation_guidance_stack`
    emits: the panel keeps its own art/rows and gains a three-member
    `guidance` run of notice / body / notice.
    """
    return {
        "kind": "oppanel",
        "layout": "image_guidance_stack",
        "image": image,
        "rows": [],
        "guidance": guidance if guidance is not None else [
            {"kind": "notice", "spec": {
                "kind": "notice",
                "label": "NOTE",
                "texts": ["Charge before first use."],
            }},
            {"kind": "body", "text": "Interstitial guidance copy."},
            {"kind": "notice", "spec": {
                "kind": "notice",
                "label": "TIP",
                "texts": ["Keep the unit ventilated."],
            }},
        ],
    }


class ComponentRegistryTests(unittest.TestCase):
    def test_every_extractor_kind_has_a_renderer(self) -> None:
        from tools.idml.components import REGISTRY
        from tools.idml_rst_extract import EMITTED_COMPONENT_KINDS

        missing = sorted(set(EMITTED_COMPONENT_KINDS) - set(REGISTRY))
        self.assertEqual(missing, [], f"extractor kinds without a renderer: {missing}")

    def test_minimal_specs_cover_the_whole_registry(self) -> None:
        from tools.idml.components import REGISTRY

        self.assertEqual(sorted(MINIMAL_SPECS), sorted(REGISTRY))

    def test_every_registered_kind_renders(self) -> None:
        from tools.idml.components import RenderContext, render

        ctx = _ctx()
        for kind, spec in MINIMAL_SPECS.items():
            with self.subTest(kind=kind):
                xml, est = render(spec, ctx, tid=f"t_{kind}", terminal=True)
                self.assertTrue(xml, f"{kind} rendered empty")
                self.assertGreater(est, 0.0)
                self.assertIn("<Table ", xml)

    def test_preface_language_badge_uses_dedicated_geometry(self) -> None:
        from tools.idml.components import RenderContext, render

        params = {
            "idml_preface_tag_width": ("4.6", "mm"),
            "idml_preface_tag_height": ("2.9", "mm"),
        }
        xml, height = render(
            MINIMAL_SPECS["langtag"],
            RenderContext(
                params=params, page_w=368.79, m_l=28.35, m_r=28.35,
                root=ROOT, bundle_root=ROOT / "does-not-exist",
            ),
            tid="preface_badge", terminal=True,
        )
        self.assertIn('AppliedParagraphStyle="ParagraphStyle/HB Preface Tag"', xml)
        self.assertIn('AppliedParagraphStyle="ParagraphStyle/HB Preface Title"', xml)
        self.assertIn('AppliedParagraphStyle="ParagraphStyle/HB Preface Body"', xml)
        self.assertIn('SingleColumnWidth="13.0394"', xml)
        self.assertIn('FillColor="Color/HB Brand Dark"', xml)
        self.assertIn('LeftInset="2.244"', xml)
        self.assertIn('LeftInset="8.947"', xml)
        self.assertIn('BaselineShift="0.5672"', xml)
        self.assertIn('BaselineShift="-1.2665"', xml)
        self.assertIn('SpaceAfter="8.3191"', xml)
        self.assertAlmostEqual(16.53957, height, places=4)

    def test_preface_language_badge_geometry_remains_param_driven(self) -> None:
        from tools.idml.components import RenderContext, render

        params = {
            "idml_preface_tag_left_inset": ("2.5", "pt"),
            "idml_preface_title_left_inset": ("9.25", "pt"),
            "idml_preface_tag_baseline_shift": ("0.4", "pt"),
            "idml_preface_title_baseline_shift": ("-1.1", "pt"),
            "idml_preface_header_space_after": ("7.75", "pt"),
        }
        xml, height = render(
            MINIMAL_SPECS["langtag"],
            RenderContext(
                params=params, page_w=368.79, m_l=28.35, m_r=28.35,
                root=ROOT, bundle_root=ROOT / "does-not-exist",
            ),
            tid="preface_badge_override", terminal=True,
        )
        self.assertIn('LeftInset="2.5"', xml)
        self.assertIn('LeftInset="9.25"', xml)
        self.assertIn('BaselineShift="0.4"', xml)
        self.assertIn('BaselineShift="-1.1"', xml)
        self.assertIn('SpaceAfter="7.75"', xml)
        self.assertAlmostEqual(15.97047, height, places=4)

    def test_reference_preface_typography_is_loaded_from_layout_params(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render
        from tools.idml.styles import para_styles, styles_xml

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        styles = {name: (size, leading, weight) for name, size, leading, weight, _ in para_styles(params)}

        self.assertEqual((8.668, 8.668, "Bold"), styles["HB Preface Tag"])
        self.assertEqual((7.0, 10.003, "Regular"), styles["HB Preface Body"])
        tag_style = styles_xml(params).split(
            'Name="HB Preface Tag"', 1,
        )[1].split("</ParagraphStyle>", 1)[0]
        self.assertIn('Justification="CenterAlign"', tag_style)

        xml, _ = render(
            MINIMAL_SPECS["langtag"],
            RenderContext(
                params=params, page_w=368.79, m_l=28.35, m_r=28.35,
                root=ROOT, bundle_root=ROOT / "does-not-exist",
            ),
            tid="preface_badge_reference", terminal=True,
        )
        self.assertIn('BaselineShift="0.7"', xml)
        self.assertIn('TopInset="0.966" BottomInset="0.966"', xml)

    def test_preface_language_badge_uses_native_rounded_frame_in_production(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        stories: dict[str, str] = {}

        def add_story(sid: str, _title: str, parts: list[str]) -> str:
            stories[sid] = "".join(parts)
            return sid

        xml, _ = render(
            MINIMAL_SPECS["langtag"],
            RenderContext(
                params=params, page_w=368.79, m_l=28.35, m_r=28.35,
                root=ROOT, bundle_root=ROOT / "does-not-exist",
                add_story=add_story,
            ),
            tid="preface_badge_rounded", terminal=True,
        )
        self.assertIn(
            'Self="tfp_st_anchor_langbadge_preface_badge_rounded"', xml,
        )
        self.assertIn('FillColor="Color/HB Brand Dark"', xml)
        self.assertNotIn('FillColor="Color/HB Brand Dark" RowSpan=', xml)
        self.assertIn('BaselineShift="0.7"', next(iter(stories.values())))

    def test_heading_pill_reuses_h2_marker_and_rounded_emphasis_geometry(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        stories: dict[str, str] = {}

        def add_story(sid: str, _title: str, parts: list[str]) -> str:
            stories[sid] = "".join(parts)
            return sid

        xml, height = render(
            MINIMAL_SPECS["headingpill"],
            RenderContext(
                params=params,
                page_w=368.79,
                m_l=28.35,
                m_r=28.35,
                root=ROOT,
                bundle_root=ROOT / "does-not-exist",
                native_structure_markers=True,
                add_story=add_story,
            ),
            tid="charging_heading",
            terminal=False,
        )

        self.assertIn("<Table ", xml)
        self.assertIn("charging_heading_h2_marker_circle", xml)
        self.assertIn('AppliedParagraphStyle="ParagraphStyle/Heading2"', xml)
        self.assertIn("st_anchor_headingpill_charging_heading", xml)
        self.assertIn('FillColor="Color/HB Brand Dark"', xml)
        self.assertIn("SOLD SEPARATELY", "".join(stories.values()))
        self.assertGreater(height, 0.0)

    def test_heading_pill_owns_compact_trilingual_column_geometry(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        localized = (
            ("en", "CHARGING VIA SOLAR PANELS", "SOLD SEPARATELY"),
            ("fr", "CHARGEMENT PAR PANNEAUX SOLAIRES", "VENDU SÉPARÉMENT"),
            ("es", "CARGA MEDIANTE PANELES SOLARES", "SE VENDE POR SEPARADO"),
        )
        suffix_columns = []
        for language, heading, pill in localized:
            with self.subTest(language=language):
                stories = {}

                def add_story(sid, _title, parts):
                    stories[sid] = "".join(parts)
                    return sid

                xml, _height = render(
                    {
                        "kind": "headingpill",
                        "heading": heading,
                        "pill": pill,
                        "variant": "charging",
                    },
                    RenderContext(
                        params=params,
                        page_w=368.79,
                        m_l=28.35,
                        m_r=28.35,
                        root=ROOT,
                        bundle_root=ROOT,
                        language=language,
                        native_structure_markers=True,
                        add_story=add_story,
                    ),
                    tid=f"charging_heading_{language}",
                    terminal=True,
                )

                root = ET.fromstring(xml)
                columns = [
                    float(column.attrib["SingleColumnWidth"])
                    for column in root.iter("Column")
                ]
                cells = list(root.iter("Cell"))
                self.assertEqual(2, len(columns))
                self.assertLess(sum(columns), 250.0)
                self.assertAlmostEqual(
                    10.9,
                    float(cells[1].attrib["LeftInset"])
                    + float(params["idml_charging_emphasis_horizontal_padding"][0])
                    + 1.25,
                )
                self.assertIn(heading, xml)
                self.assertIn(pill, "".join(stories.values()))
                suffix_columns.append(columns[1])

        self.assertLess(suffix_columns[0], suffix_columns[1])
        self.assertLess(suffix_columns[1], suffix_columns[2])

    def test_reference_body_and_l2_typography_use_idml_calibration_tokens(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.styles import para_styles

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        styles = {
            name: (size, leading, weight)
            for name, size, leading, weight, _ in para_styles(params)
        }

        self.assertEqual((6.0, 7.2, "Regular"), styles["HB Body"])
        self.assertEqual((8.0, 9.4, "Bold"), styles["HB Title L2"])
        self.assertEqual(
            (10.0, 11.0, "Bold"),
            styles["HB Operation Row Label"],
        )
        self.assertEqual((6.5, 7.2, "Bold"), styles["HB Symbol Header"])
        self.assertEqual((5.6, 6.5, "Regular"), styles["HB Symbol Body"])
        self.assertEqual((6.6, 7.4, "Bold"), styles["HB Emphasis Pill"])

    def test_ups_notice_roles_use_editable_reference_typography(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        expected_rhythm = {
            "en": (6.0, 13.0, 11.9),
            "fr": (6.0, 18.5, 18.5),
            "es": (8.0, 2.5, 10.5),
        }
        for language, (leading, before, after) in expected_rhythm.items():
            with self.subTest(language=language):
                stories = []

                def add_story(sid, title, parts):
                    stories.append((sid, title, parts))
                    return sid

                xml, _height = render(
                    {
                        "kind": "notice",
                        "layout_role": "ups_caution",
                        "label": "CAUTION",
                        "texts": ["First item", "Second item"],
                        "list": True,
                    },
                    RenderContext(
                        params=params,
                        page_w=368.79,
                        m_l=28.35,
                        m_r=28.35,
                        root=ROOT,
                        bundle_root=ROOT,
                        language=language,
                        add_story=add_story,
                    ),
                    tid=f"ups_notice_{language}",
                    terminal=True,
                )
                body = next(
                    "".join(parts)
                    for sid, _title, parts in stories
                    if "body" in sid
                )
                self.assertIn('PointSize="5.5" FontStyle="Regular"', body)
                self.assertIn(f'<Leading type="unit">{leading:g}</Leading>', body)
                self.assertIn(
                    f'SpaceBefore="{before:g}" SpaceAfter="{after:g}"',
                    xml,
                )
                self.assertIn(
                    f'<Leading type="unit">{leading:g}</Leading>'
                    '</Properties><Br/>',
                    body,
                )

    def test_charging_emphasis_uses_shared_tokenized_leading_gap(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        for language in ("en", "fr", "es"):
            with self.subTest(language=language):
                stories = []

                def add_story(sid, title, parts):
                    stories.append((sid, title, parts))
                    return sid

                xml, height = render(
                    MINIMAL_SPECS["emphasispill"],
                    RenderContext(
                        params=params,
                        page_w=368.79,
                        m_l=28.35,
                        m_r=28.35,
                        root=ROOT,
                        bundle_root=ROOT,
                        language=language,
                        add_story=add_story,
                    ),
                    tid=f"charging_emphasis_{language}",
                    terminal=True,
                )

                self.assertIn('SpaceBefore="5" SpaceAfter="1.5"', xml)
                self.assertIn(
                    '<ListItem type="unit">0</ListItem>'
                    '<ListItem type="unit">0</ListItem>'
                    '<ListItem type="unit">0</ListItem>'
                    '<ListItem type="unit">0</ListItem>',
                    xml,
                )
                self.assertTrue(stories)
                story = "".join(stories[0][2])
                self.assertIn('LeftIndent="6.1"', story)
                self.assertNotIn('RightIndent=', story)
                self.assertIn('VerticalJustification="CenterAlign"', xml)
                self.assertAlmostEqual(20.7, height)

    def test_charging_emphasis_endcap_allowance_is_component_token(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        params["idml_charging_emphasis_horizontal_padding"] = ("8.5", "pt")
        stories = []

        def add_story(sid, title, parts):
            stories.append((sid, title, parts))
            return sid

        xml, _height = render(
            {
                "kind": "emphasispill",
                "texts": ["Fully charge the product before its first use."],
            },
            RenderContext(
                params=params,
                page_w=368.79,
                m_l=28.35,
                m_r=28.35,
                root=ROOT,
                bundle_root=ROOT,
                add_story=add_story,
            ),
            tid="charging_emphasis_padding",
            terminal=True,
        )

        story = "".join(stories[0][2])
        self.assertIn('LeftIndent="8.5"', story)
        self.assertNotIn('RightIndent=', story)
        self.assertIn(
            '<ListItem type="unit">0</ListItem>'
            '<ListItem type="unit">0</ListItem>'
            '<ListItem type="unit">0</ListItem>'
            '<ListItem type="unit">0</ListItem>',
            xml,
        )
        self.assertIn('PathPointType Anchor="152.584 0"', xml)

    def test_reference_warranty_typography_separates_body_and_list_rhythm(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.styles import para_styles, styles_xml

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        styles = {
            name: (size, leading, weight)
            for name, size, leading, weight, _ in para_styles(params)
        }

        self.assertEqual((6.0, 6.0, "Regular"), styles["HB Warranty Body"])
        self.assertEqual((6.0, 7.2, "Regular"), styles["HB Warranty List"])
        self.assertEqual((8.0, 8.8, "Bold"), styles["HB Warranty Title"])
        note_style = styles_xml(params).split(
            'Self="ParagraphStyle/HB Warranty Note"', 1,
        )[1].split("</ParagraphStyle>", 1)[0]
        self.assertIn('Hyphenation="false"', note_style)
        list_style = styles_xml(params).split(
            'Self="ParagraphStyle/HB Warranty List"', 1,
        )[1].split("</ParagraphStyle>", 1)[0]
        self.assertIn('LeftIndent="5.67"', list_style)
        self.assertIn('FirstLineIndent="-5.67"', list_style)

    def test_app_numbered_headings_and_lists_share_hanging_contract(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.styles import styles_xml

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        app_h2 = styles_xml(params).split(
            'Self="ParagraphStyle/HB App H2"', 1,
        )[1].split("</ParagraphStyle>", 1)[0]
        app_list = styles_xml(params).split(
            'Self="ParagraphStyle/HB App List"', 1,
        )[1].split("</ParagraphStyle>", 1)[0]
        app_h3 = styles_xml(params).split(
            'Self="ParagraphStyle/HB App H3"', 1,
        )[1].split("</ParagraphStyle>", 1)[0]
        self.assertIn('LeftIndent="5.7"', app_h2)
        self.assertIn('FirstLineIndent="-5.7"', app_h2)
        self.assertIn('LeftIndent="5.7"', app_h3)
        self.assertIn('LeftIndent="11.4"', app_list)
        self.assertIn('FirstLineIndent="-5.7"', app_list)

    def test_warranty_year_subtitle_starts_at_year_unit(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        stories = []

        def add_story(sid, title, parts):
            stories.append((sid, title, parts))
            return sid

        xml, _height = render(
            {
                "kind": "warrantyyears",
                "items": [
                    {
                        "number": "3",
                        "unit": "YEARS",
                        "label": "Standard Warranty",
                        "text": "Copy.",
                    },
                    {
                        "number": "2",
                        "unit": "YEARS",
                        "label": "Extended Warranty",
                        "text": "Copy.",
                    },
                ],
            },
            RenderContext(
                params=params,
                page_w=368.79,
                m_l=28.35,
                m_r=28.35,
                root=ROOT,
                bundle_root=ROOT / "does-not-exist",
                add_story=add_story,
            ),
            tid="warranty_year_subtitle_alignment",
            terminal=True,
        )
        self.assertEqual(2, xml.count('LeftIndent="26.21"'))
        self.assertEqual(2, xml.count('<Position type="unit">26.21</Position>'))
        self.assertIn("<Content>\tYEARS</Content>", xml)
        self.assertIn("<Content>Standard Warranty</Content>", xml)
        self.assertIn("<Content>Extended Warranty</Content>", xml)
        self.assertEqual(2, len(stories))
        self.assertEqual(2, xml.count('VerticalJustification="TopAlign" TopInset="0"'))

    def test_warranty_years_reuse_the_je_portable_glyph_on_target_plans(
        self,
    ) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        stories = []

        def add_story(sid, title, parts):
            stories.append((sid, title, parts))
            return sid

        xml, _height = render(
            {
                "kind": "warrantyyears",
                "items": [{
                    "number": "3",
                    "unit": "YEARS",
                    "label": "Standard Warranty",
                    "text": "Copy.",
                }],
            },
            RenderContext(
                params=params,
                page_w=368.79,
                m_l=28.35,
                m_r=28.35,
                root=ROOT,
                bundle_root=ROOT / "does-not-exist",
                native_structure_markers=True,
                add_story=add_story,
            ),
            tid="warranty_native_year",
            terminal=True,
        )

        self.assertIn('Self="bg_warranty_year_warranty_native_year_0"', xml)
        self.assertIn('Self="tf_warranty_year_warranty_native_year_0"', xml)
        self.assertIn('FillColor="Color/HB Brand Dark"', xml)
        self.assertNotIn("<Content>❸</Content>", xml)
        self.assertIn("<Content>\tYEARS</Content>", xml)
        self.assertIn('<Position type="unit">26.21</Position>', xml)
        self.assertEqual(1, len(stories))
        self.assertIn("<Content>3</Content>", "".join(stories[0][2]))
        self.assertIn('FillColor="Color/Paper"', "".join(stories[0][2]))

    def test_bp_warranty_years_use_reference_subtitle_and_rhythm(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(
            ROOT / "data" / "layout_params.csv",
            (ROOT / "data" / "layout_params.idml-compact.csv",),
        )
        stories = []

        def add_story(sid, title, parts):
            stories.append((sid, title, parts))
            return sid

        xml, _height = render(
            {
                "kind": "warrantyyears",
                "layout_variant": "bp_default",
                "items": [{
                    "number": "3",
                    "unit": "YEARS",
                    "label": "— Standard Warranty",
                    "text": "Reference-width explanatory copy.",
                }],
            },
            RenderContext(
                params=params,
                page_w=368.79,
                m_l=28.35,
                m_r=28.35,
                root=ROOT,
                bundle_root=ROOT / "does-not-exist",
                language="en",
                native_structure_markers=True,
                add_story=add_story,
            ),
            tid="warranty_bp_year",
            terminal=True,
        )

        self.assertIn('Self="bg_warranty_year_warranty_bp_year_0"', xml)
        self.assertNotIn("<Content>❸</Content>", xml)
        self.assertIn('Self="tf_warranty_year_warranty_bp_year_0"', xml)
        self.assertIn("<Content>3</Content>", "".join(stories[0][2]))
        self.assertIn("<Content>Standard Warranty</Content>", xml)
        self.assertNotIn("<Content>— Standard Warranty</Content>", xml)
        self.assertIn('HorizontalScale="100"', xml)
        self.assertIn('Leading="7"', xml)
        self.assertIn('Hyphenation="false"', xml)

    def test_warranty_years_honor_section_estimate_scale(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(
            ROOT / "data" / "layout_params.csv",
            (ROOT / "data" / "layout_params.idml-compact.csv",),
        )
        without_section_override = dict(params)
        without_section_override.pop(
            "lang_it_idml_warranty_variant_bp_default_"
            "body_estimate_horizontal_scale_2",
        )
        text = (
            "Il periodo di garanzia standard decorre dalla data di acquisto "
            "del consumatore originale ed è necessario conservare la prova "
            "documentale ragionevole. "
        ) * 3
        spec = {
            "kind": "warrantysection",
            "title": "Periodo di garanzia",
            "index": 2,
            "layout_variant": "bp_default",
            "blocks": [{
                "kind": "component",
                "spec": {
                    "kind": "warrantyyears",
                    "items": [{
                        "number": "3",
                        "unit": "ANNI",
                        "label": "Garanzia standard",
                        "text": text,
                    }],
                },
            }],
        }

        def height(layout_params) -> float:
            _, rendered_height = render(
                spec,
                RenderContext(
                    params=layout_params,
                    page_w=368.79,
                    m_l=28.35,
                    m_r=28.35,
                    root=ROOT,
                    bundle_root=ROOT / "does-not-exist",
                    language="it",
                    add_story=lambda sid, _title, _parts: sid,
                ),
                tid="warranty_it_period",
                terminal=True,
            )
            return rendered_height

        self.assertLess(height(params), height(without_section_override))

    def test_bp_warranty_body_uses_reference_rhythm_only_in_variant(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(
            ROOT / "data" / "layout_params.csv",
            (ROOT / "data" / "layout_params.idml-compact.csv",),
        )

        def rendered(layout_variant: str) -> tuple[str, str]:
            stories = []

            def add_story(sid, title, parts):
                stories.append((sid, title, parts))
                return sid

            spec = {
                "kind": "warrantysection",
                "title": "Limited Warranty",
                "index": 1,
                "blocks": [
                    {"kind": "body", "text": "First warranty paragraph."},
                    {"kind": "body", "text": "Second warranty paragraph."},
                ],
            }
            if layout_variant:
                spec["layout_variant"] = layout_variant
            xml, _height = render(
                spec,
                RenderContext(
                    params=params,
                    page_w=368.79,
                    m_l=28.35,
                    m_r=28.35,
                    root=ROOT,
                    bundle_root=ROOT / "does-not-exist",
                    language="en",
                    add_story=add_story,
                ),
                tid=f"warranty_body_{layout_variant or 'base'}",
                terminal=True,
            )
            body = next(
                "".join(parts)
                for sid, _title, parts in stories
                if sid.startswith("st_anchor_warranty_body_")
            )
            return xml, body

        bp_xml, bp_body = rendered("bp_default")
        _base_xml, base_body = rendered("")

        self.assertIn('Leading="7"', bp_body)
        self.assertIn('HorizontalScale="100"', bp_body)
        self.assertIn('Hyphenation="false"', bp_body)
        self.assertIn('Composer="HL Single"', bp_body)
        self.assertNotIn('Leading="7"', base_body)
        self.assertNotIn('Hyphenation="false"', base_body)
        body_frame = bp_xml.split(
            'Self="tf_warranty_body_warranty_body_bp_default"', 1,
        )[1].split("</TextFrame>", 1)[0]
        self.assertIn('Anchor="9.07087 -15.1524"', body_frame)

    def test_warranty_section_height_counts_east_asian_glyph_width(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        context = RenderContext(
            params=params,
            page_w=368.79,
            m_l=28.35,
            m_r=28.35,
            root=ROOT,
            bundle_root=ROOT / "does-not-exist",
        )

        def height(text: str) -> float:
            _xml, value = render(
                {
                    "kind": "warrantysection",
                    "title": "Warranty",
                    "index": 4,
                    "blocks": [{"kind": "body", "text": text}],
                },
                context,
                tid="warranty_unicode_width",
                terminal=True,
            )
            return value

        self.assertGreater(height("가" * 60), height("A" * 60))

    def test_bp_final_warranty_copy_is_vertically_centered(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(
            ROOT / "data" / "layout_params.csv",
            (ROOT / "data" / "layout_params.idml-compact.csv",),
        )
        stories = []

        def add_story(sid, title, parts):
            stories.append((sid, title, parts))
            return sid

        xml, _height = render(
            {
                "kind": "warrantysection",
                "title": "Interpretation Rights",
                "index": 6,
                "layout_variant": "bp_default",
                "blocks": [{"kind": "body", "text": "One-line final policy."}],
            },
            RenderContext(
                params=params,
                page_w=368.79,
                m_l=28.35,
                m_r=28.35,
                root=ROOT,
                bundle_root=ROOT / "does-not-exist",
                language="en",
                add_story=add_story,
            ),
            tid="warranty_final_center",
            terminal=True,
        )

        body_frame = xml.split(
            'Self="tf_warranty_body_warranty_final_center"', 1,
        )[1].split("</TextFrame>", 1)[0]
        self.assertIn('VerticalJustification="CenterAlign"', body_frame)

    def test_warranty_variant_correction_resolves_per_language(self) -> None:
        """A variant correction must follow the same language cascade as its base.

        The values it offsets are per-language (`lang_<code>_idml_warranty_*`), and
        those base tokens are also read by the approved JE-1000F/US reference
        layout. If the variant layer were language-blind, a per-language BP
        correction would have to be folded back into the shared base — which moves
        the host's approved geometry and breaks its `layout_params_sha256` pin.
        """
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext
        from tools.idml.components.warranty import _variant_adjust

        params = load_layout_params(
            ROOT / "data" / "layout_params.csv",
            (ROOT / "data" / "layout_params.idml-compact.csv",),
        )
        spec = {"layout_variant": "bp_default"}

        def adjust(language: str, key: str) -> float:
            return _variant_adjust(
                spec,
                RenderContext(
                    params=params,
                    page_w=368.79,
                    m_l=28.35,
                    m_r=28.35,
                    root=ROOT,
                    bundle_root=ROOT / "does-not-exist",
                    language=language,
                ),
                key,
            )

        # en and es need opposite corrections on the same key — the whole point of
        # the cascade. These two numbers are what used to live in the base tokens.
        self.assertAlmostEqual(-5.5, adjust("en", "panel_height_adjust_5"), places=3)
        self.assertAlmostEqual(8.0, adjust("es", "panel_height_adjust_5"), places=3)

        # fr declares no bp_default correction, so it must fall through to zero
        # rather than inherit either sibling's value.
        self.assertAlmostEqual(0.0, adjust("fr", "panel_height_adjust_5"), places=3)

        # An unregistered variant contributes nothing at all.
        self.assertAlmostEqual(
            0.0,
            _variant_adjust(
                {"layout_variant": "no_such_variant"},
                RenderContext(
                    params=params,
                    page_w=368.79,
                    m_l=28.35,
                    m_r=28.35,
                    root=ROOT,
                    bundle_root=ROOT / "does-not-exist",
                    language="en",
                ),
                "panel_height_adjust_5",
            ),
            places=3,
        )

    def test_localized_warranty_note_uses_reviewed_reference_width(self) -> None:
        from tools.export_idml import IdmlWriter, load_layout_params

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        cases = {"WARRANTY": "100", "GARANTIE": "94", "GARANTÍA": "94"}
        for heading, expected_scale in cases.items():
            with self.subTest(heading=heading):
                writer = IdmlWriter(params)
                writer.add_prose_story(
                    "st_warranty_note",
                    "warranty",
                    [("h1", heading), ("warrantynote", "Localized legal note.")],
                    ROOT,
                )
                story = dict(writer.stories)["st_warranty_note"]
                self.assertIn(
                    f'HorizontalScale="{expected_scale}"',
                    story,
                )

    def test_warranty_lead_uses_language_specific_reference_geometry(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        heights = {}
        xml_by_language = {}
        for language in ("en", "fr", "es"):
            xml, height = render(
                {
                    "kind": "warrantylead",
                    "texts": ["A short purchase-channel warranty lead."],
                },
                RenderContext(
                    params=params,
                    page_w=368.79,
                    m_l=28.35,
                    m_r=28.35,
                    root=ROOT,
                    bundle_root=ROOT / "does-not-exist",
                    language=language,
                ),
                tid=f"warranty_lead_{language}",
                terminal=True,
            )
            heights[language] = height
            xml_by_language[language] = xml

        self.assertGreater(heights["en"], heights["es"])
        self.assertGreater(heights["es"], heights["fr"])
        self.assertIn('HorizontalScale="96"', xml_by_language["fr"])
        self.assertIn('HorizontalScale="100"', xml_by_language["en"])

    def test_warranty_lead_preserves_authored_multiline_target_copy(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        stories = []

        def add_story(sid, title, parts):
            stories.append((sid, title, parts))
            return sid

        _single_xml, single_height = render(
            {
                "kind": "warrantylead",
                "texts": ["Line one Line two Line three"],
            },
            RenderContext(
                params=params,
                page_w=368.79,
                m_l=28.35,
                m_r=28.35,
                root=ROOT,
                bundle_root=ROOT / "does-not-exist",
                language="fr",
                add_story=add_story,
            ),
            tid="warranty_lead_single",
            terminal=True,
        )
        _multi_xml, multiline_height = render(
            {
                "kind": "warrantylead",
                "texts": ["Line one", "Line two", "Line three"],
            },
            RenderContext(
                params=params,
                page_w=368.79,
                m_l=28.35,
                m_r=28.35,
                root=ROOT,
                bundle_root=ROOT / "does-not-exist",
                language="fr",
                add_story=add_story,
            ),
            tid="warranty_lead_multiline",
            terminal=True,
        )

        self.assertGreater(multiline_height, single_height)
        multiline_story = stories[-1][2][0]
        self.assertEqual(2, multiline_story.count("<Br/>"))

    def test_warranty_layout_variant_resolves_shared_section_tokens(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(
            ROOT / "data" / "layout_params.csv",
            (ROOT / "data" / "layout_params.idml-compact.csv",),
        )
        stories = []

        def add_story(sid, title, parts):
            stories.append((sid, title, parts))
            return sid

        xml, _height = render(
            {
                "kind": "warrantysection",
                "title": "Garantie limitée",
                "index": 1,
                "layout_variant": "multiline_lead",
                "blocks": [{"kind": "body", "text": "Copy."}],
            },
            RenderContext(
                params=params,
                page_w=368.79,
                m_l=28.35,
                m_r=28.35,
                root=ROOT,
                bundle_root=ROOT / "does-not-exist",
                language="fr",
                add_story=add_story,
            ),
            tid="warranty_multiline_variant",
            terminal=True,
        )

        self.assertIn('SpaceBefore="2.36"', xml)
        body = next(
            "".join(parts) for sid, _title, parts in stories if "body" in sid
        )
        self.assertIn('HorizontalScale="97"', body)
        self.assertIn('Leading="7"', body)
        self.assertIn('Hyphenation="false"', body)

    def test_warranty_lead_uses_approved_shell_width_and_host_inset(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        stories = []

        def add_story(sid, title, parts):
            stories.append((sid, title, parts))
            return sid

        xml, _height = render(
            {
                "kind": "warrantylead",
                "texts": ["A short purchase-channel warranty lead."],
            },
            RenderContext(
                params=params,
                page_w=368.787,
                m_l=28.3465,
                m_r=28.3465,
                root=ROOT,
                bundle_root=ROOT / "does-not-exist",
                language="es",
                add_story=add_story,
            ),
            tid="warranty_lead_shell",
            terminal=True,
        )

        self.assertIn('LeftIndent="0.45"', xml)
        self.assertIn('Anchor="310.684', xml)

    def test_warranty_h1_uses_approved_width_and_host_inset(self) -> None:
        from tools.export_idml import IdmlWriter, load_layout_params

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        writer = IdmlWriter(params)
        writer.add_prose_story(
            "st_warranty_h1",
            "p49_11_warranty",
            [("h1", "GARANTÍA")],
            ROOT,
            language="es",
        )

        story = dict(writer.stories)["st_warranty_h1"]
        self.assertIn('LeftIndent="0.87"', story)
        self.assertIn('Anchor="311.914', story)

    def test_spanish_warranty_body_uses_reference_glyph_width(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        stories = []

        def add_story(sid, title, parts):
            stories.append((sid, title, parts))
            return sid

        render(
            {
                "kind": "warrantysection",
                "title": "Exclusiones",
                "index": 5,
                "blocks": [
                    {"kind": "body", "text": "La garantía no se aplica."},
                    {"kind": "list", "text": "• Elemento de exclusión."},
                ],
            },
            RenderContext(
                params=params,
                page_w=368.79,
                m_l=28.35,
                m_r=28.35,
                root=ROOT,
                bundle_root=ROOT / "does-not-exist",
                language="es",
                add_story=add_story,
            ),
            tid="warranty_es_width",
            terminal=True,
        )
        body = next(
            "".join(parts) for sid, _title, parts in stories if "body" in sid
        )
        self.assertIn('HorizontalScale="98.6"', body)
        self.assertIn('<TabList type="list">', body)
        self.assertIn('<Position type="unit">5.67</Position>', body)
        self.assertIn('<Content>•</Content>', body)
        self.assertIn('<Content>\t</Content>', body)
        self.assertNotIn('<Content>• Elemento de exclusión.</Content>', body)

    def test_warranty_body_spacing_drives_story_and_panel_height(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        spec = {
            "kind": "warrantysection",
            "title": "Droits d'interprétation",
            "index": 6,
            "blocks": [
                {"kind": "body", "text": "Premier paragraphe de garantie."},
                {"kind": "body", "text": "Deuxième paragraphe de garantie."},
                {"kind": "body", "text": "Dernier paragraphe de garantie."},
            ],
        }

        def rendered(param_values):
            stories = []

            def add_story(sid, title, parts):
                stories.append((sid, title, parts))
                return sid

            xml, height = render(
                spec,
                RenderContext(
                    params=param_values,
                    page_w=368.79,
                    m_l=28.35,
                    m_r=28.35,
                    root=ROOT,
                    bundle_root=ROOT / "does-not-exist",
                    language="fr",
                    add_story=add_story,
                ),
                tid="warranty_spacing",
                terminal=True,
            )
            return xml, height, {sid: "".join(parts) for sid, _title, parts in stories}

        _xml, compact_height, compact_stories = rendered(params)
        body = compact_stories["st_anchor_warranty_body_warranty_spacing"]
        self.assertEqual(2, body.count('SpaceAfter="2.83"'))
        self.assertNotIn('SpaceAfter="2.27"', body)

        loose_params = dict(params)
        loose_params["idml_warranty_paragraph_after"] = ("2.27", "pt")
        _xml, loose_height, _stories = rendered(loose_params)
        self.assertAlmostEqual(2 * (2.27 - 2.83), loose_height - compact_height)

    def test_tail_warning_cells_are_vertically_centered(self) -> None:
        from tools.idml.components import render

        xml, _ = render(
            MINIMAL_SPECS["tailwarnbox"],
            _ctx(),
            tid="t_tail_center",
            terminal=True,
        )
        self.assertEqual(3, xml.count('VerticalJustification="CenterAlign"'))

    def test_all_notice_signal_labels_are_vertically_centered(self) -> None:
        from tools.idml.components import render

        for label, variant in (
            ("WARNING", "warning"),
            ("CAUTION", "caution"),
            ("NOTE", "note"),
            ("TIP", "tip"),
        ):
            with self.subTest(label=label):
                xml, _ = render(
                    {
                        "kind": "notice",
                        "label": label,
                        "variant": variant,
                        "texts": ["Editable body copy."],
                    },
                    _ctx(),
                    tid=f"notice_{variant}_center",
                    terminal=True,
                )
                label_cell = xml.split(
                    f'Self="notice_{variant}_centerc0"', 1,
                )[1].split("</Cell>", 1)[0]
                self.assertIn(
                    'VerticalJustification="CenterAlign"', label_cell,
                )

    def test_safety_warning_visible_geometry_uses_layout_tokens(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        params["idml_safety_warning_icon_column_width"] = ("30", "pt")
        params["idml_safety_warning_icon_max_width"] = ("12", "pt")
        params["idml_safety_warning_panel_min_height"] = ("32", "pt")
        ctx = RenderContext(
            params=params,
            page_w=368.79,
            m_l=28.35,
            m_r=28.35,
            root=ROOT,
            bundle_root=ROOT,
        )

        xml, height = render(
            {"kind": "safetywarning", "texts": ["Risk of fire."]},
            ctx,
            tid="safety_warning_tokens",
            terminal=True,
        )

        self.assertIn('SingleColumnWidth="30"', xml)
        self.assertIn('Anchor="12 -10.5682"', xml)
        self.assertEqual(32.0, height)

    def test_rounded_notice_reserves_rendered_height_and_rounded_label(self) -> None:
        from tools.idml.components import RenderContext, render

        stories = []

        def add_story(sid, title, parts):
            stories.append((sid, title, parts))
            return sid

        base = _ctx()
        ctx = RenderContext(
            params=base.params,
            page_w=base.page_w,
            m_l=base.m_l,
            m_r=base.m_r,
            root=base.root,
            bundle_root=base.bundle_root,
            add_story=add_story,
        )
        spec = {
            "kind": "notice",
            "label": "CAUTION",
            "list": True,
            "texts": ["x" * 90, "x" * 125, "x" * 92],
        }
        _xml, estimate = render(spec, ctx, tid="notice_wrap", terminal=True)
        self.assertGreaterEqual(estimate, 56.8)
        story_map = {sid: "".join(parts) for sid, _title, parts in stories}
        label_story = story_map["st_anchor_notice_label_notice_wrap"]
        body_story = story_map["st_anchor_notice_body_notice_wrap"]
        self.assertIn('FontStyle="Bold"', label_story)
        self.assertIn('BaselineShift="2.63"', label_story)
        self.assertIn('<Leading type="unit">7.83</Leading>', body_story)
        self.assertIn('BaselineShift="0.9"', body_story)
        self.assertIn('PointSize="4.8"', body_story)
        self.assertIn(
            'LeftIndent="5.95" FirstLineIndent="-3.4"',
            body_story,
        )
        self.assertIn('<Group Self="grp_notice_notice_wrap"', _xml)
        self.assertIn('<Rectangle Self="plate_notice_notice_wrap"', _xml)
        self.assertEqual(2, _xml.count('VerticalJustification="CenterAlign"'))
        self.assertNotIn('<Table ', _xml)

    def test_notice_width_override_keeps_contracted_size_and_leading(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        ctx = RenderContext(
            params=params,
            page_w=368.79,
            m_l=28.35,
            m_r=28.35,
            root=ROOT,
            bundle_root=ROOT / "does-not-exist",
        )
        spec = {
            "kind": "notice",
            "label": "REMARQUE",
            "list": True,
            "texts": ["un", "deux", "trois"],
            "body_horizontal_scale": 1.0,
        }

        xml, _height = render(spec, ctx, tid="notice_natural_width", terminal=True)

        self.assertIn('PointSize="6.5"', xml)
        self.assertIn('<Leading type="unit">7.83</Leading>', xml)
        self.assertIn('HorizontalScale="100"', xml)
        self.assertNotIn('HorizontalScale="106.9"', xml)

    def test_notice_list_geometry_uses_shared_bullet_tokens(self) -> None:
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        params["comp_callout_bullet_indent"] = ("2", "pt")
        params["comp_callout_bullet_width"] = ("4", "pt")
        params["type_callout_bullet_font_size"] = ("5", "pt")
        stories: list[tuple[str, str, list[str]]] = []

        def add_story(story_id: str, title: str, parts: list[str]) -> str:
            stories.append((story_id, title, parts))
            return story_id

        ctx = RenderContext(
            params=params,
            page_w=368.79,
            m_l=28.35,
            m_r=28.35,
            root=ROOT,
            bundle_root=ROOT,
            add_story=add_story,
        )
        render(
            {
                "kind": "notice",
                "label": "NOTE",
                "list": True,
                "texts": ["First", "Second"],
            },
            ctx,
            tid="notice_bullet_tokens",
            terminal=True,
        )

        body = next(
            "".join(parts)
            for story_id, _title, parts in stories
            if story_id == "st_anchor_notice_body_notice_bullet_tokens"
        )
        self.assertIn('LeftIndent="6" FirstLineIndent="-4"', body)
        self.assertIn('PointSize="5"', body)

    def test_multilingual_plural_note_labels_render_through_shared_notice(self) -> None:
        from tools.idml.components import RenderContext, render

        base = _ctx()
        for language, label in (
            ("en", "NOTES"),
            ("fr", "REMARQUES"),
            ("es", "OBSERVACIONES"),
        ):
            with self.subTest(language=language):
                stories: dict[str, str] = {}

                def add_story(story_id: str, _title: str, parts: list[str]) -> str:
                    stories[story_id] = "".join(parts)
                    return story_id

                xml, height = render(
                    {
                        "kind": "notice",
                        "label": label,
                        "variant": "note",
                        "texts": ["First item.", "Second item."],
                        "list": True,
                    },
                    RenderContext(
                        params=base.params,
                        page_w=base.page_w,
                        m_l=base.m_l,
                        m_r=base.m_r,
                        root=base.root,
                        bundle_root=base.bundle_root,
                        language=language,
                        add_story=add_story,
                    ),
                    tid=f"plural_note_{language}",
                    terminal=True,
                )
                self.assertGreater(height, 0.0)
                self.assertIn(f'grp_notice_plural_note_{language}', xml)
                rendered = "".join(stories.values())
                self.assertIn(label, rendered)
                self.assertIn("First item.", rendered)
                self.assertIn("Second item.", rendered)

    def test_notice_symbol_fallback_keeps_valid_character_attributes(self) -> None:
        from tools.idml.components import RenderContext, render

        stories: list[tuple[str, str, list[str]]] = []

        def add_story(story_id: str, title: str, parts: list[str]) -> str:
            stories.append((story_id, title, parts))
            return story_id

        base = _ctx()
        ctx = RenderContext(
            params=base.params,
            page_w=base.page_w,
            m_l=base.m_l,
            m_r=base.m_r,
            root=base.root,
            bundle_root=base.bundle_root,
            add_story=add_story,
        )

        render(
            {
                "kind": "notice",
                "label": "DANGER",
                "texts": ["Indoor only.\n※ Keep away from rain."],
            },
            ctx,
            tid="notice_symbol",
            terminal=True,
        )

        body = next(
            "".join(parts)
            for story_id, _title, parts in stories
            if story_id == "st_anchor_notice_body_notice_symbol"
        )
        ET.fromstring(f"<root>{body}</root>")
        self.assertIn("<!--HB_NATIVE_REFERENCE_MARK-->", body)
        self.assertIn('<Polygon Self="__HB_NATIVE_REFERENCE_MARK_GLYPH__"', body)
        self.assertNotIn("<Content>※</Content>", body)

    def test_notice_reference_geometry_overrides_width_height_and_inline_offset(self) -> None:
        from tools.idml.components import RenderContext, render

        stories: list[tuple[str, str, list[str]]] = []

        def add_story(story_id: str, title: str, parts: list[str]) -> str:
            stories.append((story_id, title, parts))
            return story_id

        base = _ctx()
        ctx = RenderContext(
            params=base.params,
            page_w=base.page_w,
            m_l=base.m_l,
            m_r=base.m_r,
            root=base.root,
            bundle_root=base.bundle_root,
            add_story=add_story,
        )
        spec = {
            "kind": "notice",
            "label": "NOTE",
            "body_width": 300.516,
            "panel_height": 24.869,
            "inline_x_offset": 10.943,
            "list": True,
            "texts": ["One", "Two"],
            "paragraph_space_after": 2.0,
            "unbulleted_first": True,
        }

        xml, height = render(spec, ctx, tid="reference_notice", terminal=True)

        self.assertIn('ItemTransform="1 0 0 1 10.943 0"', xml)
        # The governed height is a minimum. Final type/width overrides are
        # remeasured so localized copy can grow instead of oversetting.
        self.assertIn('Anchor="294.416 -25.46"', xml)
        self.assertAlmostEqual(32.26, height, places=2)
        self.assertEqual(2, len(stories))
        self.assertIn('SpaceAfter="2"', "".join(stories[1][2]))
        self.assertEqual(1, "".join(stories[1][2]).count("<Content>•</Content>"))
        self.assertEqual(2, xml.count('LockPosition="false" PinPosition="false"'))

    def test_notice_remeasures_french_app_overrides_after_final_style(self) -> None:
        from tools.idml.components import RenderContext, render

        stories: list[tuple[str, str, list[str]]] = []

        def add_story(story_id: str, title: str, parts: list[str]) -> str:
            stories.append((story_id, title, parts))
            return story_id

        base = _ctx()
        ctx = RenderContext(
            params=base.params,
            page_w=base.page_w,
            m_l=base.m_l,
            m_r=base.m_r,
            root=base.root,
            bundle_root=base.bundle_root,
            language="fr",
            add_story=add_story,
        )
        spec = {
            "kind": "notice",
            "label": "REMARQUE",
            "app_text_frame_safety": True,
            "body_width": 300.516,
            "panel_height": 44.737,
            "inline_x_offset": 10.943,
            "plate_left": 1.418,
            "label_width": 48.939,
            "body_size": 5.8,
            "body_leading": 5.997,
            "pad_tb": 3.1,
            "label_size": 10.0,
            "label_leading": 10.8,
            "body_inset": 3.917,
            "paragraph_space_after": 2.0,
            "unbulleted_first": True,
            "list": True,
            "texts": [
                (
                    "Si le message «l'appareil a été associé» s'affiche pendant "
                    "l'appairage, vous pouvez suivre l'une de ces deux étapes "
                    "pour procéder à la connexion."
                ),
                (
                    "Le propriétaire de l'appareil peut partager ce dernier "
                    "avec d'autres utilisateurs dans l'application."
                ),
                (
                    "Maintenez le bouton d'alimentation et le bouton "
                    "d’alimentation CC / USB enfoncés pendant 3 secondes pour "
                    "réinitialiser le Wi-Fi et le Bluetooth de l'appareil et "
                    "l'associer de nouveau."
                ),
            ],
        }

        xml, height = render(spec, ctx, tid="notice_fr_app", terminal=True)

        self.assertIn('Anchor="294.416 -54.779"', xml)
        self.assertAlmostEqual(61.58, height, places=2)
        story_map = {
            story_id: "".join(parts)
            for story_id, _title, parts in stories
        }
        label_story = story_map["st_anchor_notice_label_notice_fr_app"]
        self.assertNotIn('PointSize="10"', label_story)
        self.assertIn("REMARQUE", label_story)
        self.assertEqual(2, xml.count('LockPosition="false" PinPosition="false"'))

    def test_approved_app_notice_requires_text_frame_safety_token(self) -> None:
        from tools.idml.components import RenderContext, render

        base = _ctx()
        ctx = RenderContext(
            params={},
            page_w=base.page_w,
            m_l=base.m_l,
            m_r=base.m_r,
            root=base.root,
            bundle_root=base.bundle_root,
            strict_component_assets=True,
            add_story=lambda story_id, _title, _parts: story_id,
        )
        with self.assertRaisesRegex(
            ValueError,
            "idml_app_notice_text_frame_safety",
        ):
            render(
                {
                    "kind": "notice",
                    "label": "NOTE",
                    "texts": ["Copy."],
                    "app_text_frame_safety": True,
                },
                ctx,
                tid="strict_app_notice",
                terminal=True,
            )

    def test_notice_remeasures_long_french_caution_above_requested_height(self) -> None:
        from tools.idml.components import RenderContext, render

        base = _ctx()
        ctx = RenderContext(
            params=base.params,
            page_w=base.page_w,
            m_l=base.m_l,
            m_r=base.m_r,
            root=base.root,
            bundle_root=base.bundle_root,
            add_story=lambda story_id, _title, _parts: story_id,
        )
        spec = {
            "kind": "notice",
            "label": "ATTENTION",
            "body_width": 300.516,
            "panel_height": 24.869,
            "plate_left": 1.418,
            "label_width": 48.939,
            "body_size": 5.8,
            "body_leading": 5.997,
            "pad_tb": 2.2,
            "label_size": 9.0,
            "label_leading": 9.8,
            "body_inset": 5.42,
            "texts": [
                (
                    "L'application Jackery ne peut se connecter qu'à une seule "
                    "station d'énergie à la fois via Bluetooth. Revenir à la "
                    "liste des appareils déconnecte automatiquement le Bluetooth. "
                    "Touchez à nouveau la station d'énergie dans la liste pour "
                    "vous reconnecter automatiquement."
                ),
            ],
        }

        xml, _height = render(spec, ctx, tid="notice_fr_caution", terminal=True)

        self.assertIn('Anchor="294.416 -29.388"', xml)

    def test_lcd_mode_states_are_true_vertical_rowspans(self) -> None:
        from tools.idml.components import render

        spec = {
            "kind": "lcdmode",
            "img": "",
            "groups": [{
                "state": "Shortly On",
                "actions": [["Turn on", "Press once"],
                            ["Turn off", "Press once"],
                            ["Auto-off", "After two minutes"]],
            }],
        }
        xml, _ = render(spec, _ctx(), tid="lcd_vertical", terminal=True)
        self.assertIn('Self="lcd_verticalc0_0"', xml)
        self.assertIn('RowSpan="3"', xml)
        self.assertNotIn('Self="lcd_verticalc1_0"', xml)
        self.assertIn('FillColor="Color/HB Bg K05"', xml)
        self.assertEqual(7, xml.count('VerticalJustification="CenterAlign"'))

    def test_lcd_mode_corner_masks_use_the_panel_fill(self) -> None:
        from tools.idml.components import RenderContext, render

        stories = []

        def add_story(sid, title, parts):
            stories.append((sid, title, parts))
            return sid

        base = _ctx()
        ctx = RenderContext(
            params=base.params,
            page_w=base.page_w,
            m_l=base.m_l,
            m_r=base.m_r,
            root=base.root,
            bundle_root=base.bundle_root,
            add_story=add_story,
        )
        host, _ = render(
            MINIMAL_SPECS["lcdmode"], ctx, tid="lcd_corners", terminal=True)
        self.assertIn(
            'Self="mask_top_left_group_st_anchor_lcdmode_lcd_corners" '
            'ContentType="Unassigned" AppliedObjectStyle="ObjectStyle/$ID/[None]" '
            'FillColor="Color/Paper"',
            host,
        )
        self.assertIn(
            'Self="mask_bottom_left_group_st_anchor_lcdmode_lcd_corners" '
            'ContentType="Unassigned" AppliedObjectStyle="ObjectStyle/$ID/[None]" '
            'FillColor="Color/Paper"',
            host,
        )

    def test_image_guidance_stack_stacks_art_notice_body_notice_in_one_card(
        self,
    ) -> None:
        """The four members must stay stacked, in order, inside one card.

        `_render_image_guidance_stack` composes art, the first notice, the
        editable interstitial body, and the second notice into a single outer
        group whose members are positioned by explicit bottom offsets. If the
        emission order flips, or the offsets lose their sign, the art
        overprints the notices instead of sitting above them — a silent
        visual regression no other gate catches, because the IDML still
        parses. The nested notices are re-anchored by `_nested_notice_group`,
        which slices `render_notice` output on the literal `<Group
        Self="grp_notice_` and rewrites `ItemTransform` by regex, so this
        also pins that coupling: a rename inside notice.py breaks the slice.

        Everything the card emits lands in the anchored sub-story, not in the
        returned inline XML, so both are searched together.
        """
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        stories: dict[str, str] = {}

        def add_story(sid: str, _title: str, parts: list[str]) -> str:
            stories[sid] = "".join(parts)
            return sid

        tid = "guidance_stack"
        xml, height = render(
            _guidance_stack_spec("docs/renderers/latex/assets/op_energy_saving.png"),
            RenderContext(
                params=params, page_w=368.79, m_l=28.35, m_r=28.35,
                root=ROOT, bundle_root=ROOT,
                add_story=add_story,
            ),
            tid=tid, terminal=True,
        )
        composed = xml + "".join(stories.values())

        members = [
            f"grp_oppanel_image_guidance_art_{tid}",
            f"grp_notice_{tid}_notice_1",
            f"tf_oppanel_guidance_body_{tid}",
            f"grp_notice_{tid}_notice_2",
        ]
        pattern = "|".join(re.escape(member) for member in members)
        self.assertEqual(
            members,
            re.findall(f'Self="({pattern})"', composed),
            "guidance-stack members are missing or out of document order",
        )

        transforms = dict(
            (name, (x, float(y)))
            for name, x, y in re.findall(
                r'<Group Self="(grp_notice_' + re.escape(tid) + r'_notice_[12])"'
                r'[^>]*?ItemTransform="1 0 0 1 ([-\d.]+) ([-\d.]+)"',
                composed,
            )
        )
        self.assertEqual(
            ["7", "7"],
            [transforms[f"grp_notice_{tid}_notice_1"][0],
             transforms[f"grp_notice_{tid}_notice_2"][0]],
            "both nested notices must stay pinned to the card's left inset",
        )
        self.assertEqual(-7.0, transforms[f"grp_notice_{tid}_notice_2"][1])
        self.assertLess(
            transforms[f"grp_notice_{tid}_notice_1"][1],
            transforms[f"grp_notice_{tid}_notice_2"][1],
            "the first notice must sit further down the card than the second",
        )
        self.assertIn("Interstitial guidance copy.", composed)
        self.assertGreater(height, 0.0)

    def test_image_guidance_stack_falls_back_flat_when_the_art_is_missing(
        self,
    ) -> None:
        """Without art, the run degrades to flat blocks — never a half card.

        A permissive (flow/preview) build may not have the governed operation
        artwork on disk. The renderer then emits the two notices and the body
        copy as ordinary stacked output instead of composing a card around a
        missing image. If that branch ever emitted the card frames anyway,
        the export would place an empty art group and an unfilled body frame
        over the notices.
        """
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        stories: dict[str, str] = {}

        def add_story(sid: str, _title: str, parts: list[str]) -> str:
            stories[sid] = "".join(parts)
            return sid

        tid = "guidance_stack_flat"
        xml, height = render(
            _guidance_stack_spec("_assets/operation/definitely_missing_art.png"),
            RenderContext(
                params=params, page_w=368.79, m_l=28.35, m_r=28.35,
                root=ROOT, bundle_root=ROOT / "does-not-exist",
                add_story=add_story,
            ),
            tid=tid, terminal=True,
        )
        composed = xml + "".join(stories.values())

        self.assertNotIn("grp_oppanel_image_guidance_art_", composed)
        self.assertNotIn("tf_oppanel_guidance_body_", composed)
        self.assertIn(f"st_anchor_notice_body_{tid}_notice_1", stories)
        self.assertIn(f"st_anchor_notice_body_{tid}_notice_2", stories)
        self.assertGreater(height, 0.0)

    def test_image_guidance_stack_fails_closed_on_a_missing_governed_asset(
        self,
    ) -> None:
        """An approved/target build must abort, not silently drop the art.

        `strict_component_assets` is what separates a governed reference
        build from a permissive preview. If the strict and permissive
        branches were ever swapped, a shipped book would quietly lose the
        operation illustration instead of failing the build.
        """
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        with self.assertRaisesRegex(
            FileNotFoundError,
            "operation image-guidance asset missing: "
            "_assets/operation/definitely_missing_art.png",
        ):
            render(
                _guidance_stack_spec(
                    "_assets/operation/definitely_missing_art.png",
                ),
                RenderContext(
                    params=params, page_w=368.79, m_l=28.35, m_r=28.35,
                    root=ROOT, bundle_root=ROOT / "does-not-exist",
                    strict_component_assets=True,
                    add_story=lambda sid, _title, _parts: sid,
                ),
                tid="guidance_stack_strict", terminal=True,
            )

    def test_image_guidance_stack_requires_notice_body_notice(self) -> None:
        """The guidance run's shape is a contract, checked before layout.

        The plan declares `layout_variant: guidance_stack` and the promoter
        builds exactly notice / body / notice. A malformed or reordered run
        would otherwise be indexed positionally and render a notice where the
        editable body belongs, so the renderer refuses it up front.
        """
        from tools.export_idml import load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        notice = {"kind": "notice", "spec": {
            "kind": "notice", "label": "NOTE", "texts": ["Copy."],
        }}
        body = {"kind": "body", "text": "Interstitial guidance copy."}
        for label, guidance in (
            ("empty", []),
            ("reordered", [notice, notice, body]),
        ):
            with self.subTest(guidance=label):
                with self.assertRaisesRegex(
                    ValueError,
                    "image_guidance_stack requires notice, body, notice guidance",
                ):
                    render(
                        _guidance_stack_spec(
                            "docs/renderers/latex/assets/op_energy_saving.png",
                            guidance,
                        ),
                        RenderContext(
                            params=params, page_w=368.79, m_l=28.35, m_r=28.35,
                            root=ROOT, bundle_root=ROOT,
                            add_story=lambda sid, _title, _parts: sid,
                        ),
                        tid=f"guidance_stack_shape_{label}", terminal=True,
                    )

    def test_unknown_kind_renders_nothing(self) -> None:
        from tools.idml.components import render

        self.assertEqual(render({"kind": "hologram"}, _ctx(), tid="t", terminal=True),
                         ("", 0.0))

    def test_writer_dispatches_through_the_registry(self) -> None:
        from tools.export_idml import IdmlWriter, load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        ctx = RenderContext(params=params, page_w=w.page_w, m_l=w.m_l, m_r=w.m_r,
                            root=ROOT, bundle_root=ROOT / "does-not-exist",
                            add_story=w._add_story_parts)
        for kind, spec in MINIMAL_SPECS.items():
            with self.subTest(kind=kind):
                via_writer = w._render_component(
                    "st_x", 3, spec, ROOT / "does-not-exist", True)
                via_registry = render(spec, ctx, tid="st_x_cmp3", terminal=True)
                self.assertEqual(via_writer, via_registry)


if __name__ == "__main__":
    unittest.main()


class FccEdgeCaseTests(unittest.TestCase):
    def test_empty_texts_render_instead_of_crashing(self) -> None:
        # `\HBFccBlock{}{}` arrives as texts=[]; this used to IndexError and
        # abort the whole export.
        from tools.idml.components import render

        xml, est = render({"kind": "fcc", "texts": []}, _ctx(), tid="t_fcc0", terminal=True)
        self.assertIn("<Table ", xml)
        self.assertGreater(est, 0.0)

    def test_single_text_fills_left_panel_only(self) -> None:
        from tools.idml.components import render

        xml, _ = render({"kind": "fcc", "texts": ["Only left."]}, _ctx(),
                        tid="t_fcc1", terminal=True)
        self.assertIn("Only left.", xml)
        left, right = xml.split('Name="1:0"', 1)
        self.assertIn("Only left.", left)
        self.assertNotIn("Only left.", right)
