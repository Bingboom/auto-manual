#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Component registry contract (componentization P2).

The registry is the extension point for new manual components: every kind
the extractor can emit must have a renderer, every renderer must produce
render output for a minimal spec, and the writer façade must dispatch
through the registry (no forked logic).
"""
from __future__ import annotations

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
        from tools.idml.styles import para_styles

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        styles = {name: (size, leading, weight) for name, size, leading, weight, _ in para_styles(params)}

        self.assertEqual((8.668, 8.668, "Bold"), styles["HB Preface Tag"])
        self.assertEqual((7.0, 10.003, "Regular"), styles["HB Preface Body"])

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
        self.assertEqual((8.0, 8.8, "Bold"), styles["HB Symbol Header"])
        self.assertEqual((5.6, 6.5, "Regular"), styles["HB Symbol Body"])

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
        self.assertIn('LeftIndent="3.4" FirstLineIndent="-3.4"', body_story)
        self.assertIn('<Group Self="grp_notice_notice_wrap"', _xml)
        self.assertIn('<Rectangle Self="plate_notice_notice_wrap"', _xml)
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
        self.assertIn("※", body)

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

    def test_lcd_mode_gray_state_fill_reaches_both_left_corners(self) -> None:
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
            'FillColor="Color/HB Bg K05"',
            host,
        )
        self.assertIn(
            'Self="mask_bottom_left_group_st_anchor_lcdmode_lcd_corners" '
            'ContentType="Unassigned" AppliedObjectStyle="ObjectStyle/$ID/[None]" '
            'FillColor="Color/HB Bg K05"',
            host,
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
