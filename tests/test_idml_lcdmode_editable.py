"""Editable reference-art regressions for the LCD screen-mode panel."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from tools.idml.components import RenderContext
from tools.idml.components.lcdmode import render_lcdmode
from tools.idml.prose_flow import operation_final_frame_x_offset


ROOT = Path(__file__).resolve().parents[1]
ART_REF = "docs/renderers/latex/assets/op_lcd_mode.png"
ART_SOURCE_SIZE = (536.0, 404.0)
ART_VISIBLE_BOUNDS = (8.0, 37.0, 480.0, 383.0)


def _item_xml(xml: str, item_id: str, tag: str = "TextFrame") -> str:
    match = re.search(
        rf'<{tag} Self="{re.escape(item_id)}".*?</{tag}>',
        xml,
        re.S,
    )
    if match is None:
        raise AssertionError(f"rendered XML has no {tag} {item_id}")
    return match.group(0)


def _item_bounds(
    xml: str,
    item_id: str,
    tag: str = "TextFrame",
) -> tuple[float, float, float, float]:
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


def _item_transform(
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


def _spec(
    first_state: str,
    second_state: str,
    actions: tuple[tuple[str, str], ...],
) -> dict:
    return {
        "kind": "lcdmode",
        "img": ART_REF,
        "groups": [
            {"state": first_state, "actions": [list(row) for row in actions[:3]]},
            {"state": second_state, "actions": [list(row) for row in actions[3:]]},
        ],
    }


EN_SPEC = _spec(
    "Shortly On",
    "Steady On (in charging or discharging state)",
    (
        (
            "Turn on",
            "Press the main POWER button or when the product is charging.",
        ),
        ("Turn off", "Press the main POWER button."),
        (
            "Auto-off",
            "The LCD turns off automatically and enters sleep mode after "
            "2 minutes of inactivity.",
        ),
        (
            "Turn on",
            "Press the main POWER button twice when the product is powered on.",
        ),
        ("Turn off", "Press the main POWER button."),
        (
            "Auto-off",
            "The LCD turns off automatically after 2 hours of inactivity.",
        ),
    ),
)

FR_SPEC = _spec(
    "Allumer en discontinu",
    "Allumer en continu (en cours de charge ou de décharge)",
    (
        (
            "Allumer",
            "Appuyez sur le bouton d'alimentation principal ou lorsque le "
            "produit est en charge.",
        ),
        ("Éteindre", "Appuyez sur le bouton d'alimentation principal."),
        (
            "Arrêt automatique",
            "L'écran LCD s'éteint automatiquement et entre en mode veille "
            "après 2 minutes d'inactivité.",
        ),
        (
            "Allumer",
            "Appuyez deux fois sur le bouton d'alimentation principal lorsque "
            "le produit est allumé.",
        ),
        ("Éteindre", "Appuyez sur le bouton d'alimentation principal."),
        (
            "Arrêt automatique",
            "L'écran LCD s'éteint automatiquement après 2 heures d'inactivité.",
        ),
    ),
)

ES_SPEC = _spec(
    "En breve",
    "Estable en (durante el estado de carga o descarga)",
    (
        (
            "Encender",
            "Presione el botón de encendido principal o cuando el producto se "
            "esté cargando.",
        ),
        ("Apagar", "Presione el botón de encendido principal."),
        (
            "Apagado automático",
            "La pantalla LCD se apaga automáticamente y entra en modo de "
            "suspensión después de 2 minutos de inactividad.",
        ),
        (
            "Encender",
            "Presione dos veces el botón de encendido principal cuando el "
            "producto esté encendido.",
        ),
        ("Apagar", "Presione el botón de encendido principal."),
        (
            "Apagado automático",
            "La pantalla LCD se apaga automáticamente después de 2 horas de "
            "inactividad.",
        ),
    ),
)


def _render(
    spec: dict,
    tid: str,
    *,
    language: str = "en",
) -> tuple[str, float, dict[str, str]]:
    stories: dict[str, str] = {}

    def add_story(story_id: str, _title: str, parts: list[str]) -> str:
        stories[story_id] = "".join(parts)
        return story_id

    ctx = RenderContext(
        params={},
        page_w=368.79,
        m_l=28.35,
        m_r=28.35,
        root=ROOT,
        bundle_root=ROOT,
        language=language,
        inline_origin_shift=operation_final_frame_x_offset(language),
        add_story=add_story,
    )
    host, height = render_lcdmode(
        spec,
        ctx,
        tid=tid,
        terminal=False,
    )
    return host, height, stories


class EditableLcdModeTests(unittest.TestCase):
    def test_reference_panel_uses_left_art_and_topmost_editable_copy(self) -> None:
        host, height, stories = _render(EN_SPEC, "lcd_reference")

        self.assertGreater(height, 110.0)
        self.assertIn("tfp_st_anchor_oppanel_lcd_reference", host)
        panel = stories["st_anchor_oppanel_lcd_reference"]
        self.assertNotIn("<Table ", panel)
        self.assertIn("op_lcd_mode.png", panel)

        art_bounds = _item_bounds(
            panel,
            "lcdmode_art_lcd_reference",
            "Rectangle",
        )
        source_width, source_height = ART_SOURCE_SIZE
        self.assertAlmostEqual(
            source_width / source_height,
            (art_bounds[2] - art_bounds[0])
            / (art_bounds[3] - art_bounds[1]),
            places=4,
        )
        self.assertGreater(art_bounds[2] - art_bounds[0], 130.0)
        self.assertGreater(art_bounds[3] - art_bounds[1], 98.0)

        rectangles = [match.start() for match in re.finditer("<Rectangle", panel)]
        text_frames = [match.start() for match in re.finditer("<TextFrame ", panel)]
        self.assertTrue(rectangles)
        self.assertEqual(14, len(text_frames))
        self.assertLess(max(rectangles), min(text_frames))
        self.assertEqual(
            14,
            panel.count('LockPosition="false" PinPosition="false"'),
        )
        self.assertIn("lcdmode_table_bg_lcd_reference", panel)
        self.assertIn("lcdmode_state_bg_0_lcd_reference", panel)
        self.assertIn("lcdmode_state_rule_lcd_reference", panel)
        self.assertIn("lcdmode_action_rule_lcd_reference", panel)

        expected_story_ids = {
            "st_anchor_lcdmode_state_0_lcd_reference",
            "st_anchor_lcdmode_state_1_lcd_reference",
            *{
                f"st_anchor_lcdmode_{role}_{group}_{row}_lcd_reference"
                for role in ("action", "description")
                for group in range(2)
                for row in range(3)
            },
        }
        self.assertTrue(expected_story_ids.issubset(stories))

    def test_localized_copy_grows_rows_without_frame_overlap(self) -> None:
        rendered = [
            ("en", EN_SPEC),
            ("fr", FR_SPEC),
            ("es", ES_SPEC),
        ]
        heights: dict[str, float] = {}
        for language, spec in rendered:
            with self.subTest(language=language):
                _host, height, stories = _render(
                    spec,
                    f"lcd_{language}",
                    language=language,
                )
                heights[language] = height
                panel = stories[f"st_anchor_oppanel_lcd_{language}"]
                previous_bottom: float | None = None
                for group in range(2):
                    for row in range(3):
                        action_id = (
                            f"tf_lcdmode_action_{group}_{row}_lcd_{language}"
                        )
                        description_id = (
                            f"tf_lcdmode_description_{group}_{row}_lcd_{language}"
                        )
                        action_bounds = _item_bounds(panel, action_id)
                        description_bounds = _item_bounds(panel, description_id)
                        self.assertEqual(action_bounds[1], description_bounds[1])
                        self.assertEqual(action_bounds[3], description_bounds[3])
                        if previous_bottom is not None:
                            self.assertGreaterEqual(
                                action_bounds[1],
                                previous_bottom - 0.001,
                            )
                        previous_bottom = action_bounds[3]
                        self.assertIn(
                            'AutoSizingType="Off"',
                            _item_xml(panel, action_id),
                        )
                        self.assertIn(
                            'AutoSizingType="Off"',
                            _item_xml(panel, description_id),
                        )

                long_copy_story = (
                    f"st_anchor_lcdmode_description_0_2_lcd_{language}"
                )
                self.assertIn("<Content>", stories[long_copy_story])
                self.assertIn(
                    'PointSize="4.5"><Properties>'
                    '<Leading type="unit">4.5</Leading></Properties>',
                    stories[long_copy_story],
                )
                self.assertNotIn(
                    '<ParagraphStyleRange Leading="4.5"',
                    stories[long_copy_story],
                )

                action_story = f"st_anchor_lcdmode_action_0_2_lcd_{language}"
                self.assertIn(
                    'PointSize="5"><Properties>'
                    '<Leading type="unit">6</Leading></Properties>',
                    stories[action_story],
                )

        self.assertGreater(heights["fr"], heights["en"])
        self.assertGreater(heights["es"], heights["en"])

    def test_three_language_geometry_matches_reference_measurements(self) -> None:
        expected = {
            "en": {
                "spec": EN_SPEC,
                "panel_height": 111.48,
                "left_indent": 0.58,
                "row_heights": (15.00, 8.75, 24.50, 20.00, 8.30, 19.44),
                "columns": (43.05, 29.33, 79.35),
                "table_top_margin": 13.69,
                "art_top_margin": 20.445,
                "space_before": 4.13,
                "space_after": 0.42,
            },
            "fr": {
                "spec": FR_SPEC,
                "panel_height": 123.01,
                "left_indent": 0.52,
                "row_heights": (18.12, 12.01, 18.09, 17.22, 12.33, 16.74),
                "columns": (39.05, 33.33, 85.17),
                "table_top_margin": 20.85,
                "art_top_margin": 26.275,
                "space_before": 6.35,
                "space_after": 2.79,
            },
            "es": {
                "spec": ES_SPEC,
                "panel_height": 124.53,
                "left_indent": 0.0,
                "row_heights": (17.78, 11.76, 18.96, 17.00, 12.94, 20.63),
                "columns": (39.05, 33.33, 79.35),
                "table_top_margin": 20.23,
                "art_top_margin": 20.285,
                "space_before": 6.49,
                "space_after": 5.43,
            },
        }
        for language, values in expected.items():
            with self.subTest(language=language):
                tid = f"lcd_geometry_{language}"
                host, height, stories = _render(
                    values["spec"],
                    tid,
                    language=language,
                )
                panel = stories[f"st_anchor_oppanel_{tid}"]
                panel_height = values["panel_height"]
                assert isinstance(panel_height, float)

                outer = _item_bounds(
                    host,
                    f"tfp_st_anchor_oppanel_{tid}",
                )
                self.assertAlmostEqual(312.74, outer[2] - outer[0], places=2)
                self.assertAlmostEqual(
                    panel_height,
                    outer[3] - outer[1],
                    places=2,
                )
                outer_xml = _item_xml(
                    host,
                    f"tfp_st_anchor_oppanel_{tid}",
                )
                self.assertIn(
                    'AnchorXoffset="0"',
                    outer_xml,
                )
                host_range = re.search(
                    r"<ParagraphStyleRange ([^>]+)>",
                    host,
                )
                self.assertIsNotNone(host_range)
                host_attrs = host_range.group(1) if host_range else ""
                self.assertIn('LeftIndent="0"', host_attrs)
                self.assertIn(
                    f'FirstLineIndent="{values["left_indent"]:g}"',
                    host_attrs,
                )
                self.assertIn(
                    f'SpaceBefore="{values["space_before"]:g}"',
                    host,
                )
                self.assertIn(
                    f'SpaceAfter="{values["space_after"]:g}"',
                    host,
                )
                self.assertAlmostEqual(
                    panel_height
                    + values["space_before"]
                    + values["space_after"],
                    height,
                    places=2,
                )

                table = _item_bounds(
                    panel,
                    f"lcdmode_table_bg_{tid}",
                    "Rectangle",
                )
                self.assertAlmostEqual(140.04, table[0], places=2)
                self.assertAlmostEqual(
                    values["table_top_margin"],
                    table[1] + panel_height,
                    places=2,
                )
                self.assertAlmostEqual(
                    sum(values["columns"]),
                    table[2] - table[0],
                    places=2,
                )

                state = _item_bounds(
                    panel,
                    f"tf_lcdmode_state_0_{tid}",
                )
                action = _item_bounds(
                    panel,
                    f"tf_lcdmode_action_0_0_{tid}",
                )
                description = _item_bounds(
                    panel,
                    f"tf_lcdmode_description_0_0_{tid}",
                )
                for actual, measured in zip(
                    (
                        state[2] - state[0],
                        action[2] - action[0],
                        description[2] - description[0],
                    ),
                    values["columns"],
                ):
                    self.assertAlmostEqual(measured, actual, places=2)

                actual_rows = [
                    _item_bounds(
                        panel,
                        f"tf_lcdmode_action_{group}_{row}_{tid}",
                    )
                    for group in range(2)
                    for row in range(3)
                ]
                for bounds, measured in zip(
                    actual_rows,
                    values["row_heights"],
                ):
                    self.assertAlmostEqual(
                        measured,
                        bounds[3] - bounds[1],
                        places=2,
                    )

                art = _item_bounds(
                    panel,
                    f"lcdmode_art_{tid}",
                    "Rectangle",
                )
                art_x, art_y = _item_transform(
                    panel,
                    f"lcdmode_art_{tid}",
                )
                source_width, source_height = ART_SOURCE_SIZE
                visible_left, visible_top, visible_right, visible_bottom = (
                    ART_VISIBLE_BOUNDS
                )
                x_scale = (art[2] - art[0]) / source_width
                y_scale = (art[3] - art[1]) / source_height
                self.assertAlmostEqual(x_scale, y_scale, places=4)
                visible_width = (visible_right - visible_left) * x_scale
                visible_height = (visible_bottom - visible_top) * y_scale
                self.assertAlmostEqual(117.6, visible_width, delta=0.5)
                self.assertAlmostEqual(85.9, visible_height, delta=0.3)
                self.assertAlmostEqual(
                    6.91,
                    art_x + visible_left * x_scale,
                    places=2,
                )
                self.assertAlmostEqual(
                    values["art_top_margin"],
                    art[1] + art_y + visible_top * y_scale + panel_height,
                    places=2,
                )

    def test_unsupported_language_uses_dynamic_geometry_with_story_writer(self) -> None:
        long_description = (
            "メイン電源ボタンを押すと画面が点灯し、製品の状態を表示します。"
            "操作を続ける前に表示内容を確認してください。"
        ) * 3
        ja_spec = _spec(
            "短時間点灯",
            "充電中または放電中の連続点灯状態",
            tuple(
                ("電源を入れる", long_description)
                for _index in range(6)
            ),
        )

        tid = "lcd_dynamic_ja"
        host, _height, stories = _render(ja_spec, tid, language="ja")
        panel = stories[f"st_anchor_oppanel_{tid}"]
        outer = _item_bounds(host, f"tfp_st_anchor_oppanel_{tid}")
        panel_height = outer[3] - outer[1]
        self.assertGreater(panel_height, 111.48)

        state = _item_bounds(panel, f"tf_lcdmode_state_0_{tid}")
        action = _item_bounds(panel, f"tf_lcdmode_action_0_0_{tid}")
        self.assertNotAlmostEqual(43.05, state[2] - state[0], places=2)
        self.assertNotAlmostEqual(29.33, action[2] - action[0], places=2)

        english_row_heights = (15.00, 8.75, 24.50, 20.00, 8.30, 19.44)
        actual_rows = [
            _item_bounds(
                panel,
                f"tf_lcdmode_description_{group}_{row}_{tid}",
            )
            for group in range(2)
            for row in range(3)
        ]
        actual_heights = tuple(
            round(bounds[3] - bounds[1], 2) for bounds in actual_rows
        )
        self.assertNotEqual(english_row_heights, actual_heights)
        self.assertTrue(all(height >= 40.0 for height in actual_heights))
        for previous, current in zip(actual_rows, actual_rows[1:]):
            self.assertGreaterEqual(current[1], previous[3] - 0.001)

    def test_context_without_story_writer_keeps_table_fallback(self) -> None:
        ctx = RenderContext(
            params={},
            page_w=368.79,
            m_l=28.35,
            m_r=28.35,
            root=ROOT,
            bundle_root=ROOT,
        )

        xml, height = render_lcdmode(
            EN_SPEC,
            ctx,
            tid="lcd_fallback",
            terminal=True,
        )

        self.assertGreater(height, 0.0)
        self.assertIn("<Table ", xml)
        self.assertIn('RowSpan="3"', xml)
        self.assertIn("op_lcd_mode.png", xml)


if __name__ == "__main__":
    unittest.main()
