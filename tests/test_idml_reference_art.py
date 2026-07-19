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


if __name__ == "__main__":
    unittest.main()
