"""Editable, positioned KEY COMBINATION panel regressions."""
from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from tools.idml.components import RenderContext
from tools.idml.components.key_combinations import (
    KEY_STYLE_BASE_TOKENS,
    KEY_STYLE_LOCALE_TOKENS,
    is_key_combinations_rows,
    render_key_combinations,
)
from tools.idml.components.prose_table import (
    body_data_table_kind,
    render_table_block,
)
from tools.idml.params import load_layout_params, param_pt
from tools.idml.prose_flow import operation_final_frame_x_offset


ROOT = Path(__file__).resolve().parents[1]
KEY_ASSETS = {
    "button_power.png",
    "button_ac.png",
    "button_dc_usb.png",
    "button_led.png",
    "icon_clock_3s.png",
}


def _item_bounds(xml: str, item_id: str) -> tuple[float, float, float, float]:
    match = re.search(
        rf'<TextFrame Self="{re.escape(item_id)}".*?</TextFrame>',
        xml,
        re.S,
    )
    if match is None:
        raise AssertionError(f"rendered XML has no TextFrame {item_id}")
    points = [
        (float(x), float(y))
        for x, y in re.findall(
            r'Anchor="([-0-9.]+) ([-0-9.]+)"', match.group(0),
        )
    ]
    return (
        min(x for x, _y in points),
        min(y for _x, y in points),
        max(x for x, _y in points),
        max(y for _x, y in points),
    )


def _object_bounds(xml: str, item_id: str) -> tuple[float, float, float, float]:
    match = re.search(
        rf'<(?:TextFrame|Rectangle) Self="{re.escape(item_id)}".*?'
        r'</(?:TextFrame|Rectangle)>',
        xml,
        re.S,
    )
    if match is None:
        raise AssertionError(f"rendered XML has no page item {item_id}")
    points = [
        (float(x), float(y))
        for x, y in re.findall(
            r'Anchor="([-0-9.]+) ([-0-9.]+)"', match.group(0),
        )
    ]
    return (
        min(x for x, _y in points),
        min(y for _x, y in points),
        max(x for x, _y in points),
        max(y for _x, y in points),
    )


def _rows(language: str) -> list[list[str]]:
    if language == "fr":
        return [
            ["Boutons", "Utilisation", "Fonction"],
            [
                "Bouton d'alimentation principal + Bouton d'alimentation CA",
                "Appuyer 3 secondes sur les deux",
                "Activer/désactiver le mode économie d'énergie",
            ],
            [
                "Bouton d'alimentation principal + Bouton d'alimentation **CC/USB**",
                "Appuyer 3 secondes sur les deux",
                "Réinitialiser le Wi-Fi et le Bluetooth",
            ],
            [
                "Bouton d'alimentation **CC/USB** + Bouton d'alimentation CA",
                "Appuyer 1 seconde sur les deux",
                "Activer/désactiver le Wi-Fi et le Bluetooth",
            ],
            [
                "Bouton d'alimentation principal + Bouton d'éclairage LED",
                "Appuyer 1 seconde sur les deux",
                "Activer/désactiver le mode d'urgence",
            ],
        ]
    if language == "es":
        return [
            ["Botones", "Operación", "Función"],
            [
                "Botón de encendido principal + botón de energía de CA",
                "Mantenga pulsados ambos botones durante 3 segundos",
                "Encender/apagar el modo de ahorro de energía",
            ],
            [
                "Botón de encendido principal + botón de energía CC/USB",
                "Mantenga pulsados ambos botones durante 3 segundos",
                "Restablecer Wi-Fi y Bluetooth",
            ],
            [
                "Botón de energía CC/USB + botón de energía de CA",
                "Mantenga pulsados ambos botones durante 1 segundo",
                "Encender/apagar Wi-Fi y Bluetooth",
            ],
            [
                "Botón de encendido principal + botón de luz LED",
                "Mantenga pulsados ambos botones durante 1 segundo",
                "Activar/desactivar el modo de carga de emergencia",
            ],
        ]
    return [
        ["Buttons", "Operation", "Function"],
        [
            "Main POWER button + AC Power Button",
            "Press and hold both for 3s",
            "Turn on/off the Energy Saving Mode",
        ],
        [
            "Main POWER button + DC/USB Power Button",
            "Press and hold both for 3s",
            "Reset Wi-Fi and Bluetooth",
        ],
        [
            "DC/USB Power Button + AC Power Button",
            "Press and hold both for 1s",
            "Turn on/off Wi-Fi and Bluetooth",
        ],
        [
            "Main POWER button + LED Light button",
            "Press and hold both for 1s",
            "Turn on/off Emergency Charging Mode",
        ],
    ]


class EditableKeyCombinationTests(unittest.TestCase):
    def _render(
        self,
        language: str,
        *,
        params: dict[str, tuple[str, str]] | None = None,
        strict: bool = False,
    ) -> tuple[str, float, dict[str, str]]:
        stories: dict[str, str] = {}

        def add_story(story_id: str, _title: str, parts: list[str]) -> str:
            stories[story_id] = "".join(parts)
            return story_id

        ctx = RenderContext(
            params=(
                params
                if params is not None
                else load_layout_params(ROOT / "data" / "layout_params.csv")
            ),
            page_w=368.79,
            m_l=28.35,
            m_r=28.35,
            root=ROOT,
            bundle_root=ROOT / "docs",
            language=language,
            inline_origin_shift=operation_final_frame_x_offset(language),
            strict_component_assets=strict,
            add_story=add_story,
        )
        xml, height = render_table_block(
            _rows(language), ctx, tid=f"key_{language}", terminal=True,
        )
        return xml, height, stories

    def test_approved_style_requires_base_and_locale_override_tokens(self) -> None:
        cases = [("en", token) for token in KEY_STYLE_BASE_TOKENS]
        cases.extend(
            (language, f"lang_{language}_{token}")
            for language in ("fr", "es")
            for token in KEY_STYLE_LOCALE_TOKENS
        )
        for language, token in cases:
            for mutation in ("missing", "empty", "invalid"):
                with self.subTest(
                    language=language,
                    token=token,
                    mutation=mutation,
                ):
                    params = load_layout_params(
                        ROOT / "data" / "layout_params.csv"
                    )
                    if mutation == "missing":
                        del params[token]
                        message = "missing required layout token"
                    elif mutation == "empty":
                        params[token] = ("", "pt")
                        message = "missing required layout token"
                    else:
                        params[token] = ("not-a-number", "pt")
                        message = "non-numeric layout token"
                    with self.assertRaisesRegex(
                        ValueError,
                        rf"{message}: {token}",
                    ):
                        self._render(language, params=params, strict=True)

    def test_three_languages_use_structure_driven_specialization(self) -> None:
        for language in ("en", "fr", "es"):
            with self.subTest(language=language):
                rows = _rows(language)
                self.assertTrue(is_key_combinations_rows(rows))
                self.assertEqual("key_combinations", body_data_table_kind(rows))

    def test_arbitrary_three_column_table_does_not_match(self) -> None:
        rows = [
            ["One", "Two", "Three"],
            ["A", "B", "C"],
            ["D", "E", "F"],
            ["G", "H", "I"],
            ["J", "K", "L"],
        ]
        self.assertFalse(is_key_combinations_rows(rows))
        self.assertIsNone(body_data_table_kind(rows))

    def test_arbitrary_plus_shaped_table_does_not_match(self) -> None:
        rows = [
            ["Buttons", "Operation", "Function"],
            ["Alpha + Beta", "Wait 3s", "First"],
            ["Gamma + Delta", "Wait 3s", "Second"],
            ["Epsilon + Zeta", "Wait 1s", "Third"],
            ["Eta + Theta", "Wait 1s", "Fourth"],
        ]
        self.assertFalse(is_key_combinations_rows(rows))
        self.assertIsNone(body_data_table_kind(rows))

    def test_reordered_governed_pairs_do_not_match(self) -> None:
        rows = _rows("en")
        rows[1], rows[2] = rows[2], rows[1]

        self.assertFalse(is_key_combinations_rows(rows))
        self.assertIsNone(body_data_table_kind(rows))

    def test_missing_any_governed_asset_falls_back_atomically(self) -> None:
        for missing in sorted(KEY_ASSETS):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as tmp:
                asset_dir = Path(tmp) / "renderers" / "latex" / "assets"
                asset_dir.mkdir(parents=True)
                for name in KEY_ASSETS - {missing}:
                    (asset_dir / name).touch()

                stories: dict[str, str] = {}

                def add_story(story_id: str, _title: str, parts: list[str]) -> str:
                    stories[story_id] = "".join(parts)
                    return story_id

                root = Path(tmp)
                ctx = RenderContext(
                    params={},
                    page_w=368.79,
                    m_l=28.35,
                    m_r=28.35,
                    root=root,
                    bundle_root=root,
                    language="en",
                    add_story=add_story,
                )
                xml, height = render_table_block(
                    _rows("en"),
                    ctx,
                    tid="key_missing",
                    terminal=True,
                )

                self.assertGreater(height, 0.0)
                self.assertFalse(any(
                    story_id.startswith("st_anchor_key_")
                    for story_id in stories
                ))
                self.assertNotIn("tf_key_", xml)
                self.assertIn("<Table ", stories["st_anchor_data_key_missing"])
                self.assertNotIn(
                    "LinkResourceURI=",
                    xml + "".join(stories.values()),
                )

    def test_approved_component_fails_for_each_missing_asset(self) -> None:
        for missing in sorted(KEY_ASSETS):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as tmp:
                asset_dir = Path(tmp) / "renderers" / "latex" / "assets"
                asset_dir.mkdir(parents=True)
                for name in KEY_ASSETS - {missing}:
                    (asset_dir / name).touch()

                root = Path(tmp)
                ctx = RenderContext(
                    params={},
                    page_w=368.79,
                    m_l=28.35,
                    m_r=28.35,
                    root=root,
                    bundle_root=root,
                    language="en",
                    strict_component_assets=True,
                    add_story=lambda story_id, _title, _parts: story_id,
                )
                with self.assertRaisesRegex(ValueError, re.escape(missing)):
                    render_table_block(
                        _rows("en"),
                        ctx,
                        tid="key_missing_strict",
                        terminal=True,
                    )

    def test_unknown_language_fullwidth_copy_grows_dynamic_rows(self) -> None:
        rows = _rows("en")
        # A stale EN header must not force EN fixed geometry when the target
        # locale is explicitly unknown to the governed reference set.
        for row in rows[1:]:
            row[1] = "長" * 80
            row[2] = "機" * 80

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
            bundle_root=ROOT / "docs",
            language="ja",
            add_story=add_story,
        )
        xml, height = render_key_combinations(
            rows,
            ctx,
            tid="key_ja",
            terminal=True,
        )

        self.assertGreater(height, 240.0)
        operation = _item_bounds(xml, "tf_key_operation_0_key_ja")
        function = _item_bounds(xml, "tf_key_function_0_key_ja")
        self.assertGreaterEqual(operation[3] - operation[1], 38.4)
        self.assertGreaterEqual(function[3] - function[1], 51.0)
        self.assertEqual(12, xml.count("LinkResourceURI="))

    def test_assets_and_grid_are_below_all_editable_copy(self) -> None:
        xml, _height, stories = self._render("en")

        outline = xml.index('Self="outline_group_st_anchor_key_key_en"')
        first_copy = xml.index('Self="tf_key_header_0_key_en"')
        self.assertLess(xml.index('Self="key_button_0_0_key_en"'), first_copy)
        self.assertLess(xml.index('Self="key_clock_0_key_en"'), first_copy)
        self.assertLess(outline, first_copy)
        self.assertEqual(27, xml.count(
            'LockPosition="false" PinPosition="false"'))
        self.assertEqual(12, xml.count("LinkResourceURI="))
        self.assertNotIn("<Table", xml)
        self.assertIn("st_anchor_key_caption_0_0_key_en", stories)
        self.assertIn("st_anchor_key_plus_3_key_en", stories)
        self.assertIn("st_anchor_key_duration_3_key_en", stories)
        self.assertIn("st_anchor_key_function_3_key_en", stories)

    def test_reference_width_height_and_locale_offsets(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        trailing_gap = param_pt(params, "comp_data_table_after", 3.4)
        expected = {
            "en": (152.92, 2.48, 10.62),
            "fr": (167.06, 1.15, 3.53),
            "es": (166.70, 3.35, 4.14),
        }
        for language, (panel_h, left_indent, space_before) in expected.items():
            with self.subTest(language=language):
                xml, estimated_h, _ = self._render(language)
                outline = re.search(
                    rf'<Rectangle Self="outline_group_st_anchor_key_key_{language}"'
                    r'.*?</Rectangle>',
                    xml,
                    re.S,
                )
                self.assertIsNotNone(outline)
                points = [
                    (float(x), float(y))
                    for x, y in re.findall(
                        r'Anchor="([-0-9.]+) ([-0-9.]+)"',
                        outline.group(0) if outline else "",
                    )
                ]
                self.assertAlmostEqual(
                    311.02,
                    max(x for x, _y in points) - min(x for x, _y in points),
                    places=2,
                )
                self.assertAlmostEqual(
                    panel_h,
                    max(y for _x, y in points) - min(y for _x, y in points),
                    places=2,
                )
                host = re.search(r"<ParagraphStyleRange ([^>]+)>", xml)
                self.assertIsNotNone(host)
                host_attrs = host.group(1) if host else ""
                self.assertIn(f'SpaceBefore="{space_before:g}"', host_attrs)
                self.assertIn(f'SpaceAfter="{trailing_gap:g}"', host_attrs)
                self.assertIn('LeftIndent="0"', host_attrs)
                self.assertIn(
                    f'FirstLineIndent="{left_indent:g}"', host_attrs,
                )
                group = re.search(
                    rf'<Group Self="grp_st_anchor_key_key_{language}" '
                    r'[^>]+>',
                    xml,
                )
                self.assertIsNotNone(group)
                self.assertIn(
                    'ItemTransform="1 0 0 1 -0.37 0"',
                    group.group(0) if group else "",
                )
                self.assertAlmostEqual(
                    panel_h + space_before + trailing_gap,
                    estimated_h,
                    places=2,
                )

    def test_reference_column_widths_stay_fixed(self) -> None:
        xml, _height, _ = self._render("en")
        divider_centers = []
        for divider in range(2):
            rule = re.search(
                rf'<Rectangle Self="key_vrule_{divider}_key_en".*?'
                r'</Rectangle>',
                xml,
                re.S,
            )
            self.assertIsNotNone(rule)
            xs = [
                float(x)
                for x in re.findall(
                    r'Anchor="([-0-9.]+) [-0-9.]+"',
                    rule.group(0) if rule else "",
                )
            ]
            divider_centers.append((min(xs) + max(xs)) / 2.0)
        self.assertAlmostEqual(128.49, divider_centers[0], places=2)
        self.assertAlmostEqual(128.49 + 90.70, divider_centers[1], places=2)

    def test_shared_tokens_drive_geometry_type_and_locale_override(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        params["idml_key_panel_width"] = ("300", "pt")
        params["idml_key_function_font_size"] = ("9", "pt")
        params["lang_fr_idml_key_panel_height"] = ("180", "pt")

        en_xml, _en_height, en_stories = self._render("en", params=params)
        fr_xml, _fr_height, _fr_stories = self._render("fr", params=params)

        def outline_height(xml: str, language: str) -> float:
            outline = re.search(
                rf'<Rectangle Self="outline_group_st_anchor_key_key_{language}"'
                r'.*?</Rectangle>',
                xml,
                re.S,
            )
            self.assertIsNotNone(outline)
            points = [
                (float(x), float(y))
                for x, y in re.findall(
                    r'Anchor="([-0-9.]+) ([-0-9.]+)"',
                    outline.group(0) if outline else "",
                )
            ]
            self.assertAlmostEqual(
                300.0,
                max(x for x, _y in points) - min(x for x, _y in points),
                places=2,
            )
            return max(y for _x, y in points) - min(y for _x, y in points)

        self.assertAlmostEqual(152.92, outline_height(en_xml, "en"), places=2)
        self.assertAlmostEqual(180.0, outline_height(fr_xml, "fr"), places=2)
        self.assertIn(
            'PointSize="9"',
            en_stories["st_anchor_key_function_0_key_en"],
        )

    def test_narrow_measure_scales_the_complete_component_contract(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        stories: dict[str, str] = {}
        ctx = RenderContext(
            params=params,
            page_w=368.79,
            m_l=28.35,
            m_r=28.35,
            root=ROOT,
            bundle_root=ROOT / "docs",
            language="en",
            add_story=lambda story_id, _title, parts: (
                stories.setdefault(story_id, "".join(parts)) or story_id
            ),
        )
        width = param_pt(params, "idml_key_panel_width", 311.02)
        xml, estimated_height = render_key_combinations(
            _rows("en"),
            ctx,
            tid="key_half",
            terminal=True,
            measure_w=width / 2.0,
        )

        outline = _object_bounds(xml, "outline_group_st_anchor_key_key_half")
        panel_width = outline[2] - outline[0]
        panel_height = outline[3] - outline[1]
        self.assertAlmostEqual(width / 2.0, panel_width, places=3)
        self.assertAlmostEqual(152.92 / 2.0, panel_height, places=3)
        self.assertAlmostEqual((152.92 + 10.62) / 2.0, estimated_height, places=3)

        button = _object_bounds(xml, "key_button_0_0_key_half")
        clock = _object_bounds(xml, "key_clock_0_key_half")
        self.assertAlmostEqual(22.08 / 2.0, button[2] - button[0], places=3)
        self.assertAlmostEqual(10.45 / 2.0, clock[2] - clock[0], places=3)
        self.assertIn(
            'PointSize="3"',
            stories["st_anchor_key_function_0_key_half"],
        )
        self.assertIn(
            '<Leading type="unit">4.25</Leading>',
            stories["st_anchor_key_function_0_key_half"],
        )

        frame_ids = re.findall(r'<TextFrame Self="(tf_key_[^"]+)"', xml)
        self.assertEqual(27, len(frame_ids))
        for frame_id in frame_ids:
            with self.subTest(frame=frame_id):
                left, top, right, bottom = _item_bounds(xml, frame_id)
                self.assertGreaterEqual(left, -1e-6)
                self.assertLess(right, panel_width + 1e-6)
                self.assertGreaterEqual(top, -panel_height - 1e-6)
                self.assertLessEqual(bottom, 1e-6)
                self.assertLess(left, right)
                self.assertLess(top, bottom)

        dividers = []
        for index in range(2):
            bounds = _object_bounds(xml, f"key_vrule_{index}_key_half")
            dividers.append((bounds[0] + bounds[2]) / 2.0)
        self.assertAlmostEqual(128.49 / 2.0, dividers[0], places=3)
        self.assertAlmostEqual((128.49 + 90.70) / 2.0, dividers[1], places=3)

    def test_invalid_style_tokens_and_available_width_fail_closed(self) -> None:
        base = load_layout_params(ROOT / "data" / "layout_params.csv")
        cases = (
            ("idml_key_panel_width", "0", None, "idml_key_panel_width"),
            ("comp_key_table_left_ratio", "0", None, "left_ratio"),
            ("comp_key_table_middle_ratio", "0.7", None, "column ratios"),
            ("idml_key_function_font_size", "0", None, "function_font_size"),
            ("idml_key_outer_radius", "-1", None, "outer_radius"),
            (None, None, 0.0, "available width"),
        )
        for token, value, measure_w, message in cases:
            with self.subTest(token=token, measure_w=measure_w):
                params = dict(base)
                if token is not None and value is not None:
                    params[token] = (value, params[token][1])
                ctx = RenderContext(
                    params=params,
                    page_w=368.79,
                    m_l=28.35,
                    m_r=28.35,
                    root=ROOT,
                    bundle_root=ROOT / "docs",
                    language="en",
                    add_story=lambda story_id, _title, _parts: story_id,
                )
                with self.assertRaisesRegex(ValueError, message):
                    render_key_combinations(
                        _rows("en"),
                        ctx,
                        tid="key_invalid",
                        terminal=True,
                        measure_w=measure_w,
                    )

    def test_source_copy_stays_editable_without_markdown_leakage(self) -> None:
        _xml, _height, stories = self._render("fr")
        all_copy = "\n".join(stories.values())
        self.assertIn("Bouton d'alimentation principal", all_copy)
        self.assertIn("CC/USB", all_copy)
        self.assertNotIn("**", all_copy)
        self.assertIn("Appuyer 3 secondes sur les deux", all_copy)
        self.assertIn("Activer/désactiver le mode d'urgence", all_copy)


if __name__ == "__main__":
    unittest.main()
