"""Reference-manual semantic image geometry regressions."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from tools.idml.components import RenderContext
from tools.idml.components.oppanel import _prereq_overlay, render_oppanel
from tools.idml.components.prose_image import render_image_block


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


class ReferenceArtGeometryTests(unittest.TestCase):
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
