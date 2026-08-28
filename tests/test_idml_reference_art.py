"""Reference-manual semantic image geometry regressions."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from tools.idml.components import RenderContext
from tools.idml.components.oppanel import (
    _operation_duration,
    _prereq_overlay,
    _row_layout,
    _row_text_layers,
    render_oppanel,
)
from tools.idml.components.prose_image import (
    IMAGE_ROLE_CHARGING_DIAGRAM,
    IMAGE_ROLE_COMPACT_DIAGRAM,
    IMAGE_ROLE_FULL_MEASURE,
    IMAGE_ROLE_REFERENCE_MEASURE,
    IMAGE_ROLE_WIDE_DIAGRAM,
    render_image_block,
)


ROOT = Path(__file__).resolve().parents[1]


def _ctx() -> RenderContext:
    return RenderContext(
        params={},
        page_w=368.79,
        m_l=28.35,
        m_r=28.35,
        root=ROOT,
        bundle_root=ROOT,
    )


def _image_width(xml: str) -> float:
    points = [
        (float(x), float(y))
        for x, y in re.findall(r'Anchor="([-0-9.]+) ([-0-9.]+)"', xml)
    ]
    if not points:
        raise AssertionError("rendered XML has no image path anchors")
    return max(x for x, _y in points) - min(x for x, _y in points)


def _item_xml(xml: str, item_id: str, tag: str = "TextFrame") -> str:
    match = re.search(
        rf'<{tag} Self="{re.escape(item_id)}".*?</{tag}>',
        xml,
        re.S,
    )
    if match is None:
        raise AssertionError(f"rendered XML has no {tag} {item_id}")
    return match.group(0)


def _item_bounds(xml: str, item_id: str, tag: str = "TextFrame") -> tuple[float, ...]:
    item = _item_xml(xml, item_id, tag)
    points = [
        (float(x), float(y))
        for x, y in re.findall(r'Anchor="([-0-9.]+) ([-0-9.]+)"', item)
    ]
    if not points:
        raise AssertionError(f"rendered {tag} {item_id} has no path anchors")
    return (
        min(x for x, _y in points),
        min(y for _x, y in points),
        max(x for x, _y in points),
        max(y for _x, y in points),
    )


def _item_translation(
    xml: str,
    item_id: str,
    tag: str = "Rectangle",
) -> tuple[float, float]:
    item = _item_xml(xml, item_id, tag)
    match = re.search(
        r'ItemTransform="1 0 0 1 ([-0-9.]+) ([-0-9.]+)"',
        item,
    )
    if match is None:
        raise AssertionError(f"rendered {tag} {item_id} has no translation")
    return float(match.group(1)), float(match.group(2))


class ReferenceArtGeometryTests(unittest.TestCase):
    def test_operation_row_overlays_use_role_specific_alignment(self) -> None:
        image_w = 294.9
        image_h = 160.0
        power = _row_layout("op_main_power.png", image_w, image_h)
        dc_usb = _row_layout("op_dc_usb_output.png", image_w, image_h)
        ac = _row_layout("op_ac_output.png", image_w, image_h)

        self.assertAlmostEqual(image_w * 0.765, power[0])
        self.assertAlmostEqual(-image_h + image_h * 0.035, power[1])
        self.assertAlmostEqual(image_w * 0.235, power[2])
        self.assertAlmostEqual(ac[0], dc_usb[0])
        self.assertAlmostEqual(ac[2], dc_usb[2])

    def test_operation_rows_apply_operator_adjusted_role_offsets(self) -> None:
        params = {
            "idml_operation_main_power_on_y_offset": ("7.086614", "pt"),
            "idml_operation_main_power_off_y_offset": ("2.125984", "pt"),
            "idml_operation_ac_output_off_y_offset": ("-1.417323", "pt"),
            "idml_operation_dc_usb_x_offset": ("3.543307", "pt"),
        }
        base = _ctx()
        ctx = RenderContext(
            params=params,
            page_w=base.page_w,
            m_l=base.m_l,
            m_r=base.m_r,
            root=base.root,
            bundle_root=base.bundle_root,
            add_story=lambda story_id, _label, _parts: story_id,
        )
        image_w = 294.9
        cases = (
            ("main_power", "op_main_power.png", 115.282),
            ("ac_output", "op_ac_output.png", 206.547),
            ("dc_usb", "op_dc_usb_output.png", 170.521),
        )
        rendered = {}
        for role, ref, image_h in cases:
            rendered[role] = _row_text_layers(
                ctx,
                tid=role,
                ref=ref,
                rows=[("On", "Press once"), ("Off", "Press once")],
                image_w=image_w,
                image_h=image_h,
                panel_w=312.09,
            )

        power_layout = _row_layout("op_main_power.png", image_w, 115.282)
        power_on = _item_bounds(rendered["main_power"], "tf_oppanel_row_0_main_power")
        power_off = _item_bounds(rendered["main_power"], "tf_oppanel_row_1_main_power")
        self.assertAlmostEqual(power_layout[1] + 7.086614, power_on[1], places=3)
        self.assertAlmostEqual(
            power_layout[1] + power_layout[3] + 2.125984,
            power_off[1],
            places=3,
        )

        ac_layout = _row_layout("op_ac_output.png", image_w, 206.547)
        ac_off = _item_bounds(rendered["ac_output"], "tf_oppanel_row_1_ac_output")
        self.assertAlmostEqual(
            ac_layout[1] + ac_layout[3] - 1.417323,
            ac_off[1],
            places=3,
        )

        dc_layout = _row_layout("op_dc_usb_output.png", image_w, 170.521)
        for index in (0, 1):
            dc_row = _item_bounds(
                rendered["dc_usb"], f"tf_oppanel_row_{index}_dc_usb")
            self.assertAlmostEqual(dc_layout[0] + 3.543307, dc_row[0], places=3)
            self.assertAlmostEqual(318.59, dc_row[2], places=3)

    def test_main_power_baked_clock_is_replaced_by_a_movable_asset(self) -> None:
        stories = {}

        def add_story(story_id, _label, parts):
            stories[story_id] = "".join(parts)
            return story_id

        base = _ctx()
        ctx = RenderContext(
            params={
                "idml_operation_main_power_clock_size": ("10.5", "pt"),
                "idml_operation_main_power_clock_x_offset": ("0", "pt"),
                "idml_operation_main_power_clock_y_offset": ("0", "pt"),
                "idml_operation_row_right_edge_offset": ("6.5", "pt"),
            },
            page_w=base.page_w,
            m_l=base.m_l,
            m_r=base.m_r,
            root=base.root,
            bundle_root=ROOT / "docs",
            add_story=add_story,
        )
        render_oppanel(
            {
                "kind": "oppanel",
                "image": "renderers/latex/assets/op_main_power.png",
                "rows": [["On", "Press once"], ["Off", "Hold for 3 seconds"]],
            },
            ctx,
            tid="movable_clock",
            terminal=False,
        )

        panel = stories["st_anchor_oppanel_movable_clock"]
        self.assertIn("oppanel_main_power_clock_mask_movable_clock", panel)
        clock = _item_xml(
            panel,
            "oppanel_main_power_clock_movable_clock",
            "Rectangle",
        )
        self.assertIn("icon_clock_3s.png", clock)
        self.assertIn('PinPosition="false"', clock)
        self.assertIn(
            "tf_oppanel_main_power_duration_movable_clock",
            panel,
        )
        self.assertIn(
            ">3s<",
            stories[
                "st_anchor_oppanel_main_power_duration_movable_clock"
            ],
        )

    def test_main_power_duration_is_language_neutral(self) -> None:
        for instruction in (
            "Press and hold for 3 seconds.",
            "Maintenez le bouton enfoncé pendant 3 secondes.",
            "Mantenga pulsado durante 3 segundos.",
            "Press and hold for 3s.",
        ):
            with self.subTest(instruction=instruction):
                self.assertEqual(
                    "3s",
                    _operation_duration([("Off", instruction)]),
                )

    def test_operation_and_charging_art_use_the_full_text_measure(self) -> None:
        ctx = _ctx()
        refs = (
            "docs/templates/word_template/common_assets/operation/energy_saving.png",
            "docs/templates/word_template/common_assets/operation/led_light.png",
            "docs/templates/word_template/common_assets/operation/ups_mode.png",
            "docs/templates/word_template/common_assets/charging/ac_wall.png",
            "docs/templates/word_template/common_assets/charging/solar_direct.png",
            "docs/templates/word_template/common_assets/charging/solar_adapter.png",
            "docs/templates/word_template/common_assets/charging/car_charge.png",
            "docs/renderers/latex/assets/op_energy_saving.png",
            "docs/renderers/latex/assets/op_ups_mode.png",
            "docs/renderers/latex/assets/solar_adapter.png",
            "docs/renderers/latex/assets/car_charge.png",
        )
        for index, ref in enumerate(refs):
            with self.subTest(ref=ref):
                xml, height = render_image_block(
                    (ROOT / ref).as_posix(),
                    ctx,
                    rect_id=f"full_{index}",
                    terminal=False,
                )
                self.assertIsNotNone(xml)
                self.assertAlmostEqual(ctx.text_measure, _image_width(xml or ""), places=3)
                self.assertGreater(height, 70.0)

    def test_ups_art_uses_localized_reference_gap(self) -> None:
        params = {
            "idml_ups_image_space_before": ("5.2", "pt"),
            "lang_fr_idml_ups_image_space_before": ("3.2", "pt"),
        }
        base = _ctx()
        ctx = RenderContext(
            params=params,
            page_w=base.page_w,
            m_l=base.m_l,
            m_r=base.m_r,
            root=base.root,
            bundle_root=base.bundle_root,
            language="fr",
        )
        xml, _height = render_image_block(
            (ROOT / "docs/renderers/latex/assets/op_ups_mode.png").as_posix(),
            ctx,
            rect_id="ups_fr",
            terminal=False,
        )
        self.assertIn('SpaceBefore="3.2"', xml or "")

    def test_app_art_uses_role_specific_measure_widths(self) -> None:
        base = _ctx()
        app_root = ROOT / "docs/templates/word_template/common_assets/app"
        ctx = RenderContext(
            params=base.params,
            page_w=base.page_w,
            m_l=base.m_l,
            m_r=base.m_r,
            root=base.root,
            bundle_root=app_root,
        )
        refs_and_ratios = (
            ("download.png", 0.60),
            ("add_device.png", 0.55),
            ("connect_result.png", 0.58),
            ("je1000f_us/add_device_je1000f_us.png", 0.55),
            ("je1000f_us/connect_result_je1000f_us.png", 0.58),
        )
        for index, (name, ratio) in enumerate(refs_and_ratios):
            with self.subTest(name=name):
                xml, height = render_image_block(
                    name,
                    ctx,
                    rect_id=f"app_{index}",
                    terminal=False,
                )
                self.assertIsNotNone(xml)
                self.assertAlmostEqual(
                    ctx.text_measure * ratio,
                    _image_width(xml or ""),
                    places=3,
                )
                self.assertIn('AnchorSpaceAbove="0"', xml or "")
                self.assertGreater(height, 0.0)

    def test_semantic_image_roles_use_layout_ratios_without_filename_routing(
        self,
    ) -> None:
        ctx = _ctx()
        neutral_asset = (
            ROOT / "docs" / "renderers" / "latex" / "assets"
            / "warning_lockup.png"
        )
        roles_and_ratios = (
            (IMAGE_ROLE_FULL_MEASURE, 1.0),
            (IMAGE_ROLE_REFERENCE_MEASURE, 1.0),
            (IMAGE_ROLE_WIDE_DIAGRAM, 0.78),
            (IMAGE_ROLE_COMPACT_DIAGRAM, 0.62),
            (IMAGE_ROLE_CHARGING_DIAGRAM, 0.58),
        )
        for index, (role, ratio) in enumerate(roles_and_ratios):
            with self.subTest(role=role):
                xml, height = render_image_block(
                    neutral_asset.as_posix(),
                    ctx,
                    rect_id=f"semantic_{index}",
                    terminal=False,
                    role=role,
                )
                self.assertIsNotNone(xml)
                self.assertAlmostEqual(
                    ctx.text_measure * ratio,
                    _image_width(xml or ""),
                    places=3,
                )
                self.assertGreater(height, 0.0)

        default_xml, _ = render_image_block(
            neutral_asset.as_posix(),
            ctx,
            rect_id="semantic_default",
            terminal=False,
        )
        self.assertAlmostEqual(120.0, _image_width(default_xml or ""), places=3)

        localized = RenderContext(
            params={
                "idml_semantic_image_full_measure_ratio": ("1.0", "ratio"),
                "lang_fr_idml_semantic_image_full_measure_ratio": (
                    "0.80",
                    "ratio",
                ),
            },
            page_w=ctx.page_w,
            m_l=ctx.m_l,
            m_r=ctx.m_r,
            root=ctx.root,
            bundle_root=ctx.bundle_root,
            language="fr",
        )
        localized_xml, _ = render_image_block(
            neutral_asset.as_posix(),
            localized,
            rect_id="semantic_fr",
            terminal=False,
            role=IMAGE_ROLE_FULL_MEASURE,
        )
        self.assertAlmostEqual(
            localized.text_measure * 0.80,
            _image_width(localized_xml or ""),
            places=3,
        )
        reference_xml, _ = render_image_block(
            neutral_asset.as_posix(),
            localized,
            rect_id="semantic_fr_reference",
            terminal=False,
            role=IMAGE_ROLE_REFERENCE_MEASURE,
        )
        self.assertAlmostEqual(
            localized.text_measure,
            _image_width(reference_xml or ""),
            places=3,
        )

    def test_operation_panel_preserves_reference_art_scale(self) -> None:
        ctx = _ctx()
        spec = {
            "kind": "oppanel",
            "image": (
                ROOT / "docs/renderers/latex/assets/op_ac_output.png"
            ).as_posix(),
            "prereq": "Localized prerequisite",
            "rows": [["Localized on", "Press once"], ["Localized off", "Press once"]],
        }

        xml, height = render_oppanel(
            spec,
            ctx,
            tid="reference_operation_panel",
            terminal=False,
        )

        self.assertGreaterEqual(_image_width(xml), ctx.text_measure * 0.94)
        self.assertGreater(height, 170.0)

    def test_operation_prerequisite_replaces_baked_pill_with_editable_stack(self) -> None:
        stories = []

        def add_story(story_id, _label, _parts):
            stories.append(story_id)
            return story_id

        base = _ctx()
        ctx = RenderContext(
            params=base.params, page_w=base.page_w, m_l=base.m_l, m_r=base.m_r,
            root=base.root, bundle_root=base.bundle_root, add_story=add_story,
        )
        xml = _prereq_overlay(
            ctx, tid="editable_prereq", text="Localized prerequisite",
            image_w=200.0, image_h=100.0,
        )
        mask = 'Self="oppanel_prereq_mask_editable_prereq"'
        background = 'Self="oppanel_prereq_bg_editable_prereq"'
        text_frame = 'Self="tf_oppanel_prereq_editable_prereq"'
        self.assertLess(xml.index(mask), xml.index(background))
        self.assertLess(xml.index(background), xml.index(text_frame))
        self.assertIn('LockPosition="false" PinPosition="false"', xml)
        self.assertEqual(["st_anchor_oppanel_prereq_editable_prereq"], stories)

    def test_long_spanish_prerequisite_uses_the_reserved_top_strip(self) -> None:
        stories = []

        def add_story(story_id, _label, _parts):
            stories.append(story_id)
            return story_id

        base = _ctx()
        ctx = RenderContext(
            params=base.params, page_w=base.page_w, m_l=base.m_l, m_r=base.m_r,
            root=base.root, bundle_root=base.bundle_root, add_story=add_story,
        )
        xml = _prereq_overlay(
            ctx,
            tid="spanish_prereq",
            text="Requisito previo: el producto está encendido.",
            image_w=294.9,
            image_h=120.0,
        )

        left, _top, right, _bottom = _item_bounds(
            xml, "oppanel_prereq_bg_spanish_prereq", "Rectangle",
        )
        self.assertGreater(right - left, 294.9 * 0.455)
        self.assertLessEqual(right - left, 294.9 * 0.62)
        self.assertEqual(["st_anchor_oppanel_prereq_spanish_prereq"], stories)

    def test_operation_copy_is_independently_editable_and_topmost(self) -> None:
        stories = {}

        def add_story(story_id, _label, parts):
            stories[story_id] = "".join(parts)
            return story_id

        base = _ctx()
        ctx = RenderContext(
            params=base.params, page_w=base.page_w, m_l=base.m_l, m_r=base.m_r,
            root=base.root, bundle_root=base.bundle_root, add_story=add_story,
        )
        render_oppanel(
            {
                "kind": "oppanel",
                "image": "docs/renderers/latex/assets/op_main_power.png",
                "prereq": "Prerequisite: Editable copy.",
                "rows": [["On", "Press once"], ["Off", "Press and hold"]],
                "tail": "**Default standby time:** 2 hours.",
            },
            ctx,
            tid="editable_operation",
            terminal=False,
        )

        panel = stories["st_anchor_oppanel_editable_operation"]
        rectangles = [match.start() for match in re.finditer("<Rectangle", panel)]
        text_frames = [match.start() for match in re.finditer("<TextFrame ", panel)]
        self.assertTrue(rectangles)
        self.assertEqual(4, len(text_frames))
        self.assertLess(max(rectangles), min(text_frames))
        self.assertEqual(4, panel.count('LockPosition="false" PinPosition="false"'))
        self.assertNotIn("<Table", panel)
        self.assertIn("st_anchor_oppanel_row_0_editable_operation", stories)
        self.assertIn("st_anchor_oppanel_row_1_editable_operation", stories)
        self.assertIn(
            'AppliedParagraphStyle="ParagraphStyle/HB Operation Row Label"',
            stories["st_anchor_oppanel_row_0_editable_operation"],
        )

    def test_energy_saving_panel_copy_is_editable_and_topmost(self) -> None:
        stories = {}

        def add_story(story_id, _label, parts):
            stories[story_id] = "".join(parts)
            return story_id

        base = _ctx()
        ctx = RenderContext(
            params=base.params, page_w=base.page_w, m_l=base.m_l, m_r=base.m_r,
            root=base.root, bundle_root=base.bundle_root, add_story=add_story,
        )
        xml, height = render_oppanel(
            {
                "kind": "oppanel",
                "layout": "energy_saving",
                "image": "docs/renderers/latex/assets/op_energy_saving.png",
                "guidance": [
                    "Localized disable guidance.",
                    "Localized low-power guidance.",
                ],
                "mode_label": "On/Off",
                "duration": "3s",
                "action": "Localized press-and-hold action.",
            },
            ctx,
            tid="editable_energy",
            terminal=False,
        )

        self.assertGreater(height, 165.0)
        self.assertIn("tfp_st_anchor_oppanel_editable_energy", xml)
        panel = stories["st_anchor_oppanel_editable_energy"]
        rectangles = [match.start() for match in re.finditer("<Rectangle", panel)]
        text_frames = [match.start() for match in re.finditer("<TextFrame ", panel)]
        self.assertTrue(rectangles)
        self.assertEqual(5, len(text_frames))
        self.assertLess(max(rectangles), min(text_frames))
        self.assertEqual(5, panel.count(
            'LockPosition="false" PinPosition="false"'))
        mode_bounds = _item_bounds(
            panel,
            "tf_oppanel_energy_mode_editable_energy",
        )
        self.assertAlmostEqual(-28.5, mode_bounds[1])
        self.assertAlmostEqual(-15.0, mode_bounds[3])
        self.assertIn("op_energy_saving.png", panel)
        self.assertNotIn("common_assets/operation/energy_saving.png", panel)
        self.assertNotIn("<Table", panel)
        expected = {
            "st_anchor_oppanel_energy_guidance_0_editable_energy",
            "st_anchor_oppanel_energy_guidance_1_editable_energy",
            "st_anchor_oppanel_energy_mode_editable_energy",
            "st_anchor_oppanel_energy_duration_editable_energy",
            "st_anchor_oppanel_energy_action_editable_energy",
        }
        self.assertTrue(expected.issubset(stories))

    def test_energy_controls_match_operator_adjusted_positions(self) -> None:
        stories = {}

        def add_story(story_id, _label, parts):
            stories[story_id] = "".join(parts)
            return story_id

        base = _ctx()
        ctx = RenderContext(
            params={
                "idml_operation_energy_mode_x_offset": ("-2.539370", "pt"),
                "idml_operation_energy_mode_y_offset": ("3.543307", "pt"),
                "idml_operation_energy_duration_x_offset": ("-9.625984", "pt"),
                "idml_operation_energy_duration_y_offset": ("1.417323", "pt"),
                "idml_operation_energy_clock_x_offset": ("-8.917323", "pt"),
                "idml_operation_energy_clock_y_offset": ("4.251969", "pt"),
                "idml_operation_energy_guidance_x_offset": ("-7.5", "pt"),
                "idml_operation_energy_guidance_y_offset": ("8.0", "pt"),
                "idml_operation_energy_guidance_gap": ("-2.0", "pt"),
                "idml_operation_energy_action_x_offset": ("-10.2", "pt"),
                "idml_operation_energy_action_y_offset": ("8.0", "pt"),
                "idml_operation_energy_panel_y_offset": ("-5.669291", "pt"),
            },
            page_w=base.page_w,
            m_l=base.m_l,
            m_r=base.m_r,
            root=base.root,
            bundle_root=ROOT / "docs",
            add_story=add_story,
        )
        render_oppanel(
            {
                "kind": "oppanel",
                "layout": "energy_saving",
                "image": "docs/renderers/latex/assets/op_energy_saving.png",
                "guidance": ["Guidance one.", "Guidance two."],
                "mode_label": "On/Off",
                "duration": "3s",
                "action": "Press and hold.",
            },
            ctx,
            tid="adjusted_energy",
            terminal=False,
        )
        host = render_oppanel(
            {
                "kind": "oppanel",
                "layout": "energy_saving",
                "image": "docs/renderers/latex/assets/op_energy_saving.png",
                "guidance": ["Guidance one.", "Guidance two."],
                "mode_label": "On/Off",
                "duration": "3s",
                "action": "Press and hold.",
            },
            ctx,
            tid="adjusted_energy_host",
            terminal=False,
        )[0]
        self.assertIn('AnchorYoffset="-5.66929"', host)
        panel = stories["st_anchor_oppanel_adjusted_energy"]
        mode = _item_bounds(panel, "tf_oppanel_energy_mode_adjusted_energy")
        duration = _item_bounds(panel, "tf_oppanel_energy_duration_adjusted_energy")
        guidance_bg = _item_bounds(
            panel,
            "oppanel_energy_guidance_bg_adjusted_energy",
            tag="Rectangle",
        )
        guidance = _item_bounds(
            panel,
            "tf_oppanel_energy_guidance_0_adjusted_energy",
        )
        second_guidance = _item_bounds(
            panel,
            "tf_oppanel_energy_guidance_1_adjusted_energy",
        )
        action = _item_bounds(
            panel,
            "tf_oppanel_energy_action_adjusted_energy",
        )
        clock = _item_translation(
            panel,
            "oppanel_energy_clock_adjusted_energy",
            tag="Rectangle",
        )
        width = ctx.text_measure
        self.assertAlmostEqual(width * 0.68 - 2.539370, mode[0], places=3)
        self.assertAlmostEqual(-28.5 + 3.543307, mode[1], places=3)
        self.assertAlmostEqual(width * 0.642 - 9.625984, duration[0], places=3)
        self.assertAlmostEqual(-21.5 + 1.417323, duration[1], places=3)
        self.assertAlmostEqual(width * 0.601 - 8.917323, clock[0], places=3)
        self.assertAlmostEqual(-12.0 + 4.251969, clock[1], places=3)
        grey_top = -max(width * 0.545, 159.0) + 8.0
        self.assertAlmostEqual(7.5 - 7.5, guidance_bg[0], places=3)
        self.assertAlmostEqual(grey_top + 8.0, guidance_bg[1], places=3)
        self.assertAlmostEqual(14.0 - 7.5, guidance[0], places=3)
        self.assertAlmostEqual(grey_top + 4.8 + 8.0, guidance[1], places=3)
        self.assertAlmostEqual(
            guidance[1] + 8.3 - 2.0,
            second_guidance[1],
            places=3,
        )
        self.assertAlmostEqual(width * 0.682 - 10.2, action[0], places=3)
        self.assertAlmostEqual(-20.0 + 8.0, action[1], places=3)

    def test_french_energy_action_has_fixed_in_panel_geometry(self) -> None:
        stories = {}

        def add_story(story_id, _label, parts):
            stories[story_id] = "".join(parts)
            return story_id

        base = _ctx()
        ctx = RenderContext(
            params=base.params, page_w=base.page_w, m_l=base.m_l, m_r=base.m_r,
            root=base.root, bundle_root=base.bundle_root, add_story=add_story,
        )
        render_oppanel(
            {
                "kind": "oppanel",
                "layout": "energy_saving",
                "image": "docs/renderers/latex/assets/op_energy_saving.png",
                "guidance": ["Texte un.", "Texte deux."],
                "mode_label": "On/Off",
                "duration": "3s",
                "action": (
                    "Maintenez les deux boutons enfoncés pendant plus de "
                    "3 secondes."
                ),
            },
            ctx,
            tid="french_energy",
            terminal=False,
        )

        panel = stories["st_anchor_oppanel_french_energy"]
        action_id = "tf_oppanel_energy_action_french_energy"
        _left, top, _right, bottom = _item_bounds(panel, action_id)
        self.assertGreaterEqual(bottom - top, 18.8)
        self.assertLessEqual(bottom, -6.0)
        self.assertIn('AutoSizingType="Off"', _item_xml(panel, action_id))
        _ml, mode_top, _mr, _mode_bottom = _item_bounds(
            panel, "tf_oppanel_energy_mode_french_energy",
        )
        self.assertLess(mode_top, top)

    def test_led_panel_copy_is_editable_and_topmost(self) -> None:
        stories = {}

        def add_story(story_id, _label, parts):
            stories[story_id] = "".join(parts)
            return story_id

        base = _ctx()
        ctx = RenderContext(
            params=base.params, page_w=base.page_w, m_l=base.m_l, m_r=base.m_r,
            root=base.root, bundle_root=base.bundle_root, add_story=add_story,
        )
        _xml, height = render_oppanel(
            {
                "kind": "oppanel",
                "layout": "led_light",
                "image": (
                    "docs/templates/word_template/common_assets/operation/"
                    "led_light.png"
                ),
                "lead": "The LED light has two modes: Light and SOS.",
                "steps": ["First localized step.", "Second localized step.",
                          "Third localized step."],
                "sos_label": "SOS",
            },
            ctx,
            tid="editable_led",
            terminal=False,
        )

        self.assertGreater(height, 140.0)
        panel = stories["st_anchor_oppanel_editable_led"]
        rectangles = [match.start() for match in re.finditer("<Rectangle", panel)]
        text_frames = [match.start() for match in re.finditer("<TextFrame ", panel)]
        self.assertTrue(rectangles)
        self.assertEqual(8, len(text_frames))
        self.assertLess(max(rectangles), min(text_frames))
        self.assertEqual(8, panel.count(
            'LockPosition="false" PinPosition="false"'))
        lead_story = stories["st_anchor_oppanel_led_lead_editable_led"]
        self.assertIn('FontStyle="Bold"', lead_story)
        self.assertIn("<Content>The LED light has two modes:</Content>", lead_story)
        for index in range(3):
            self.assertIn(
                f"st_anchor_oppanel_led_number_{index}_editable_led", stories)
            self.assertIn(
                f"st_anchor_oppanel_led_step_{index}_editable_led", stories)
        self.assertIn("st_anchor_oppanel_led_sos_editable_led", stories)
        self.assertNotIn("<Table", panel)

    def test_long_localized_led_steps_keep_non_overlapping_slots(self) -> None:
        stories = {}

        def add_story(story_id, _label, parts):
            stories[story_id] = "".join(parts)
            return story_id

        base = _ctx()
        ctx = RenderContext(
            params=base.params, page_w=base.page_w, m_l=base.m_l, m_r=base.m_r,
            root=base.root, bundle_root=base.bundle_root, add_story=add_story,
        )
        steps = [
            "Appuyez une fois sur le bouton de la lampe LED pour l'allumer.",
            "Appuyez de nouveau pour passer en mode SOS.",
            "Appuyez une troisième fois pour éteindre la lampe.",
        ]
        render_oppanel(
            {
                "kind": "oppanel",
                "layout": "led_light",
                "image": "docs/renderers/latex/assets/op_led_light.png",
                "lead": (
                    "La lampe LED dispose de deux modes : mode éclairage et "
                    "mode SOS."
                ),
                "steps": steps,
                "sos_label": "SOS",
            },
            ctx,
            tid="french_led",
            terminal=False,
        )

        panel = stories["st_anchor_oppanel_french_led"]
        bounds = [
            _item_bounds(panel, f"tf_oppanel_led_step_{index}_french_led")
            for index in range(3)
        ]
        effective_bottoms = [
            top + max(18.0, ((len(step) + 23) // 24) * 7.5)
            for (_left, top, _right, _bottom), step in zip(bounds, steps)
        ]
        self.assertLessEqual(effective_bottoms[0] + 1.0, bounds[1][1])
        self.assertLessEqual(effective_bottoms[1] + 1.0, bounds[2][1])
        self.assertLessEqual(effective_bottoms[2], 0.0)


if __name__ == "__main__":
    unittest.main()
