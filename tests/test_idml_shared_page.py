from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tools.export_idml import IdmlWriter, check_idml, load_layout_params
from tools.idml.shared_page import (
    add_charging_storage_page,
    add_connection_tail_troubleshooting_page,
    add_connections_page,
    add_fcc_inbox_overview_page,
    add_lcd_operations_page,
    add_safety_symbols_page,
    shares_latex_page,
)


ROOT = Path(__file__).resolve().parents[1]


class SharedPageTests(unittest.TestCase):
    def test_compact_fcc_inbox_page_embeds_shared_semantic_overview(self) -> None:
        params = load_layout_params(
            ROOT / "data" / "layout_params.csv",
            (ROOT / "data" / "layout_params.idml-compact.csv",),
        )
        art = (
            ROOT
            / "docs"
            / "renderers"
            / "latex"
            / "assets"
            / "warning_lockup.png"
        ).as_posix()
        with tempfile.TemporaryDirectory() as td:
            writer = IdmlWriter(
                params,
                model="JBP-2000B",
                region="US",
                language="en",
            )
            add_fcc_inbox_overview_page(
                writer,
                sid="st_compact",
                fcc_blocks=[
                    (
                        "component",
                        json.dumps(
                            {"kind": "fcc", "texts": ["Left.", "Right."]}
                        ),
                    )
                ],
                inbox_blocks=[
                    ("h1", "WHAT'S IN THE BOX"),
                    (
                        "component",
                        json.dumps(
                            {
                                "kind": "inbox",
                                "items": [
                                    {"img": art, "label": f"Item {index}"}
                                    for index in range(1, 4)
                                ],
                            }
                        ),
                    ),
                ],
                overview_blocks=[
                    ("h1", "PRODUCT OVERVIEW"),
                    ("h2", "FRONT VIEW"),
                    ("image", art),
                    ("table", [["**POWER button**", "**LCD Display**"]]),
                    ("h2", "LEFT SIDE VIEW"),
                    ("image", art),
                    (
                        "table",
                        [
                            [
                                "**Handle**",
                                "**DC Expansion Port A** (Connect to Terminal A)",
                            ],
                            [
                                "",
                                "**DC Expansion Port B** (Connect to Terminal B)",
                            ],
                        ],
                    ),
                ],
                bundle_root=Path(td),
                page_index=4,
                language="en",
            )

            spread = dict(writer.spreads)["sp_4"]
            stories = "".join(xml for _, xml in writer.stories)
            self.assertEqual(1, spread.count("<Page "))
            self.assertIn("art_st_compact_overview_front", spread)
            self.assertIn("art_st_compact_overview_right", spread)
            self.assertEqual(10, spread.count("<GraphicLine "))
            for text in (
                "POWER button",
                "LCD Display",
                "Handle",
                "DC Expansion Port A",
                "DC Expansion Port B",
            ):
                self.assertIn(text, stories)

    def test_measured_sources_share_only_the_same_latex_page(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            first = bundle / "page" / "safety_info_en.rst"
            second = bundle / "page" / "symbol_meaning_en.rst"
            plan = {
                "pages": [
                    {"source_path": "page/safety_info_en.rst", "latex_start_page": 4},
                    {"source_path": "page/symbol_meaning_en.rst", "latex_start_page": 4},
                ]
            }
            self.assertTrue(shares_latex_page(plan, first, second, bundle))
            plan["pages"][1]["latex_start_page"] = 5
            self.assertFalse(shares_latex_page(plan, first, second, bundle))

    def test_compact_page_reuses_safety_lists_and_two_column_symbols(self) -> None:
        params = load_layout_params(
            ROOT / "data" / "layout_params.csv",
            (ROOT / "data" / "layout_params.idml-compact.csv",),
        )
        for language, safety_style in {
            "en": "HB Safety List",
            "fr": "HB Safety List FR",
            "es": "HB Safety List ES",
        }.items():
            with self.subTest(language=language), tempfile.TemporaryDirectory() as td:
                writer = IdmlWriter(params)
                symbol_data = SimpleNamespace(
                    title="MEANING OF SYMBOLS",
                    signal_headers=("Symbol", "Meaning"),
                    icon_headers=("Symbol", "Meaning"),
                    signals=(
                        ("WARNING", "Hazardous practices."),
                        ("CAUTION", "Personal injury risk."),
                        ("NOTE", "Equipment damage risk."),
                        ("TIP", "Helpful information."),
                    ),
                    icons=tuple(
                        {"figure": "", "text": f"Icon meaning {index}"}
                        for index in range(1, 12)
                    ),
                )
                safety = [
                    ("h1", "IMPORTANT SAFETY INFORMATION"),
                    ("body", "Follow the basic safety precautions."),
                    *[("list", f"• Safety item {index}") for index in range(1, 11)],
                ]

                add_safety_symbols_page(
                    writer,
                    safety_sid=f"st_safety_{language}",
                    safety_title=f"safety_{language}",
                    safety_blocks=safety,
                    symbol_data=symbol_data,
                    bundle_root=Path(td),
                    data_root=Path(td),
                    page_index=3,
                    language=language,
                )

                stories = dict(writer.stories)
                safety_xml = stories[f"st_safety_{language}"]
                self.assertEqual(10, safety_xml.count("<Content>•</Content>"))
                self.assertIn(
                    f'AppliedParagraphStyle="ParagraphStyle/{safety_style}"',
                    safety_xml,
                )
                self.assertIn(f"st_symbols_shared_{language}_signals", stories)
                self.assertIn(f"st_symbols_shared_{language}_icons_left", stories)
                self.assertIn(f"st_symbols_shared_{language}_icons_right", stories)
                left_xml = stories[f"st_symbols_shared_{language}_icons_left"]
                right_xml = stories[f"st_symbols_shared_{language}_icons_right"]
                self.assertIn('PointSize="0.1" Leading="0.1"', left_xml)
                self.assertIn('PointSize="0.1" Leading="0.1"', right_xml)
                for index in range(1, 12):
                    text = f"<Content>Icon meaning {index}</Content>"
                    self.assertNotEqual(text in left_xml, text in right_xml)
                spread = dict(writer.spreads)["sp_3"]
                self.assertIn("_icons_left", spread)
                self.assertIn("_icons_right", spread)
                self.assertEqual(1, spread.count("<Page "))

                output = Path(td) / f"shared-{language}.idml"
                writer.write(output)
                self.assertEqual([], check_idml(output))

    def test_compact_page_reuses_lcd_and_operations_stories(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        with tempfile.TemporaryDirectory() as td:
            writer = IdmlWriter(params)
            lcd_data = SimpleNamespace(
                title="LCD DISPLAY",
                rows=(
                    {
                        "no": "①",
                        "figure": "",
                        "name": "Battery level",
                        "desc": "Shows the remaining charge.",
                    },
                    {
                        "no": "②",
                        "figure": "",
                        "name": "Charging indicator",
                        "desc": "Shown while charging.",
                    },
                ),
            )

            lcd_sid, operation_sid = add_lcd_operations_page(
                writer,
                lcd_data=lcd_data,
                operation_sid="st_operation_en",
                operation_title="operation_en",
                operation_blocks=[
                    ("h1", "OPERATIONS"),
                    ("h2", "POWER ON/OFF"),
                    (
                        "image",
                        (
                            ROOT / "docs" / "renderers" / "latex" / "assets"
                            / "jbp2000b_power_control.png"
                        ).as_posix(),
                    ),
                    (
                        "body",
                        "**On**\nPress once\n**Off**\nPress and hold for 3 seconds",
                    ),
                    ("h2", "LCD DISPLAY ON/OFF"),
                    (
                        "image",
                        (
                            ROOT / "docs" / "renderers" / "latex" / "assets"
                            / "jbp2000b_lcd_control.png"
                        ).as_posix(),
                    ),
                ],
                bundle_root=Path(td),
                data_root=Path(td),
                page_index=5,
                language="en",
                hero_path=None,
                composition_data={
                    "lcd": {
                        "table_variant": "label_description",
                        "hero_horizontal_scale": 1.14,
                        "hero_callouts": [
                            {
                                "row_index": 1,
                                "text_rect": [28.35, 65.0, 101.0, 16.0],
                                "align": "RightAlign",
                                "leader_points": [[130.0, 72.5], [159.0, 72.5]],
                            },
                            {
                                "row_index": 2,
                                "text_rect": [276.0, 65.0, 64.5, 16.0],
                                "align": "LeftAlign",
                                "leader_points": [[228.0, 72.5], [274.0, 72.5]],
                            },
                        ],
                    }
                },
            )

            self.assertEqual("st_lcd", lcd_sid)
            self.assertEqual("st_operation_en", operation_sid)
            self.assertEqual(1, writer.lcd_segment_counts["en"])
            lcd_table = dict(writer.stories)["st_anchor_lcd_table_en_0"]
            self.assertIn('ColumnCount="2"', lcd_table)
            self.assertNotIn("①", lcd_table)
            self.assertNotIn("②", lcd_table)
            self.assertNotIn("Yu Gothic", lcd_table)
            self.assertIn('TopInset="2.8" BottomInset="2.8"', lcd_table)
            self.assertIn('SingleColumnWidth="74.9987"', lcd_table)
            self.assertIn('SingleColumnWidth="237.496"', lcd_table)
            self.assertNotIn('TopInset="13.322"', lcd_table)
            spread = dict(writer.spreads)["sp_5"]
            self.assertIn('ParentStory="st_lcd"', spread)
            self.assertIn('ParentStory="st_operation_en"', spread)
            self.assertIn('ParentStory="st_lcd_callout_en_1"', spread)
            self.assertIn('ParentStory="st_lcd_callout_en_2"', spread)
            self.assertEqual(2, spread.count("<GraphicLine "))
            stories = dict(writer.stories)
            self.assertIn("Battery level", stories["st_lcd_callout_en_1"])
            self.assertIn("Charging indicator", stories["st_lcd_callout_en_2"])
            self.assertEqual(1, spread.count("<Page "))

            output = Path(td) / "shared-lcd-operations.idml"
            writer.write(output)
            self.assertEqual([], check_idml(output))

    def test_shared_diagram_compositions_use_one_explicit_physical_page(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        art = (
            ROOT / "docs" / "renderers" / "latex" / "assets"
            / "warning_lockup.png"
        ).as_posix()
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            writer = IdmlWriter(params)
            add_connections_page(
                writer,
                sid="st_connections",
                title="connections",
                blocks=[("h1", "CONNECTIONS"), ("image", art)],
                bundle_root=bundle,
                page_index=6,
                language="en",
            )
            add_connection_tail_troubleshooting_page(
                writer,
                connection_sid="st_connection_tail",
                connection_title="connection_tail",
                connection_blocks=[("image", art)],
                trouble_sid="st_trouble_complete",
                trouble_title="troubleshooting_en",
                trouble_blocks=[
                    ("h1", "TROUBLESHOOTING"),
                    ("body", "Follow the listed corrective actions."),
                    (
                        "table",
                        json.dumps([
                            ["Error Code", "Corrective Measures"],
                            ["F0", "Restart the product."],
                        ]),
                    ),
                ],
                bundle_root=bundle,
                page_index=7,
                language="en",
                composition_data={
                    "troubleshooting": {
                        "connection_image_role": "reference_measure",
                        "heading_space_after": 5.4,
                        "split": 303.6,
                    }
                },
            )
            add_charging_storage_page(
                writer,
                sid="st_charging_storage",
                title="charging_storage",
                charging_blocks=[
                    ("h1", "CHARGING"),
                    ("image", art),
                    ("image", art),
                ],
                storage_blocks=[("h1", "STORAGE"), ("body", "Store dry.")],
                bundle_root=bundle,
                page_index=8,
                language="en",
            )

            for page_index in (6, 7, 8):
                spread = dict(writer.spreads)[f"sp_{page_index}"]
                self.assertEqual(1, spread.count("<Page "))
            self.assertIn(
                'ParentStory="st_connection_tail"',
                dict(writer.spreads)["sp_7"],
            )
            self.assertIn(
                'ParentStory="st_trouble_complete"',
                dict(writer.spreads)["sp_7"],
            )
            stories = dict(writer.stories)
            self.assertIn(
                "Follow the listed corrective actions.",
                stories["st_trouble_complete"],
            )
            self.assertIn(
                'Hyphenation="false"',
                stories["st_trouble_complete"],
            )
            self.assertIn(
                'SpaceAfter="5.4"',
                stories["st_trouble_complete"],
            )
            self.assertIn("Error Code", "".join(stories.values()))
            self.assertTrue(any(
                'StoryTitle="troubleshooting table"' in xml
                for xml in stories.values()
            ))

            output = bundle / "shared-diagram-compositions.idml"
            writer.write(output)
            self.assertEqual([], check_idml(output))


if __name__ == "__main__":
    unittest.main()
