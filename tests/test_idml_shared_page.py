from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tools.export_idml import IdmlWriter, check_idml, load_layout_params
from tools.idml.shared_page import (
    add_charging_page,
    add_charging_storage_page,
    add_connection_tail_troubleshooting_page,
    add_connections_page,
    add_fcc_inbox_overview_page,
    add_lcd_operations_page,
    add_safety_symbols_page,
    add_storage_specifications_page,
    shares_latex_page,
)


ROOT = Path(__file__).resolve().parents[1]


class SharedPageTests(unittest.TestCase):
    def test_connections_page_reuses_target_declared_order_and_image_role(
        self,
    ) -> None:
        params = load_layout_params(
            ROOT / "data" / "layout_params.csv",
            (ROOT / "data" / "layout_params.idml-compact.csv",),
        )
        writer = IdmlWriter(
            params,
            model="JBP-2000B",
            region="US",
            language="fr",
            native_structure_markers=True,
        )
        art = (
            ROOT / "docs" / "renderers" / "latex" / "assets"
            / "warning_lockup.png"
        ).as_posix()

        add_connections_page(
            writer,
            sid="st_connections",
            title="connections",
            blocks=[
                ("h1", "CONNEXIONS"),
                ("body", "Source-authored introduction."),
                ("image", art),
                (
                    "component",
                    json.dumps({
                        "kind": "notice",
                        "label": "Important",
                        "variant": "caution",
                        "texts": ["First source-authored notice."],
                        "list": True,
                    }),
                ),
                (
                    "component",
                    json.dumps({
                        "kind": "notice",
                        "label": "Remarques",
                        "variant": "note",
                        "texts": ["Second source-authored notice."],
                        "list": True,
                    }),
                ),
            ],
            bundle_root=ROOT,
            page_index=6,
            language="fr",
            composition_data={
                "connections": {
                    "layout_variant": "notice_before_primary_figure",
                    "image_role": "reference_measure",
                }
            },
        )

        story = dict(writer.stories)["st_connections"]
        first_notice = story.index("grp_notice_st_connections_cmp")
        primary_figure = story.index('Self="st_connections_im1"')
        second_notice = story.index(
            "grp_notice_st_connections_cmp",
            first_notice + 1,
        )
        self.assertLess(first_notice, primary_figure)
        self.assertLess(primary_figure, second_notice)
        image_xml = story[primary_figure:story.index("</Rectangle>", primary_figure)]
        self.assertIn('Anchor="312.094', image_xml)

    def test_charging_page_uses_target_declared_full_width_and_suffix_pill(
        self,
    ) -> None:
        params = load_layout_params(
            ROOT / "data" / "layout_params.csv",
            (ROOT / "data" / "layout_params.idml-compact.csv",),
        )
        self.assertEqual(
            ("36.0", "pt"),
            params["idml_compact_charging_frame_bottom_extra"],
        )
        writer = IdmlWriter(
            params,
            model="JBP-2000B",
            region="US",
            language="en",
            native_structure_markers=True,
        )
        art = (
            ROOT / "docs" / "renderers" / "latex" / "assets"
            / "warning_lockup.png"
        ).as_posix()

        add_charging_page(
            writer,
            sid="st_charging",
            title="charging",
            charging_blocks=[
                ("h1", "CHARGING"),
                ("h2", "CHARGING VIA AC WALL OUTLET"),
                ("image", art),
                (
                    "h2",
                    "CHARGING VIA SOLAR PANELS (SOLD SEPARATELY)",
                ),
                ("image", art),
            ],
            bundle_root=ROOT,
            page_index=8,
            language="en",
            composition_data={
                "charging": {
                    "image_role": "reference_measure",
                    "h2_suffix_pill_indices": [1],
                }
            },
        )

        stories = dict(writer.stories)
        main_story = stories["st_charging"]
        self.assertIn("CHARGING VIA SOLAR PANELS", main_story)
        self.assertNotIn("(SOLD SEPARATELY)", main_story)
        pill_stories = "".join(
            xml for sid, xml in stories.items() if "headingpill" in sid
        )
        self.assertIn("SOLD SEPARATELY", pill_stories)
        image = main_story.split('Self="st_charging_im1"', 1)[1].split(
            "</Rectangle>", 1
        )[0]
        self.assertIn('Anchor="312.09', image)
        expected_bottom = (
            writer.page_h / 2 - writer.m_b
            + float(params["idml_compact_charging_frame_bottom_extra"][0])
        )
        spread = dict(writer.spreads)["sp_8"]
        self.assertIn(f" {expected_bottom:g}\"", spread)

    def test_storage_and_compact_specifications_reuse_one_physical_page(
        self,
    ) -> None:
        params = load_layout_params(
            ROOT / "data" / "layout_params.csv",
            (ROOT / "data" / "layout_params.idml-compact.csv",),
        )
        writer = IdmlWriter(
            params,
            model="JBP-2000B",
            region="US",
            language="en",
            native_structure_markers=True,
        )
        spec_data = SimpleNamespace(
            title="SPECIFICATIONS",
            annotations=(),
            sections=(
                {"title": "GENERAL INFO", "rows": [("Model", "M1")] * 7},
                {"title": "INPUT PORTS", "rows": [("Input", "36 V")]},
                {"title": "OUTPUT PORTS", "rows": [("Output", "36 V")]},
                {"title": "TEMPERATURE", "rows": [("Charge", "45 C")] * 2},
            ),
        )
        composition_data = {
            "specifications": {
                "layout_variant": "compact",
                "section_groups": [
                    {"source_indices": [0]},
                    {
                        "source_indices": [1, 2],
                        "title": "INPUT / OUTPUT PORTS",
                    },
                    {"source_indices": [3]},
                ],
            }
        }

        _storage_sid, spec_sid, grouped = add_storage_specifications_page(
            writer,
            sid="st_storage_spec",
            storage_blocks=[
                ("h1", "STORAGE"),
                ("body", "Store the product in a dry place."),
                ("list", "• Recharge every three months."),
            ],
            spec_data=spec_data,
            bundle_root=ROOT,
            page_index=9,
            language="en",
            composition_data=composition_data,
        )

        self.assertEqual(3, len(grouped))
        self.assertEqual("INPUT / OUTPUT PORTS", grouped[1]["title"])
        self.assertEqual(2, len(grouped[1]["rows"]))
        spread = dict(writer.spreads)["sp_9"]
        self.assertEqual(1, spread.count("<Page "))
        self.assertIn('FillColor="Color/HB Bg K05"', spread)
        storage_background = spread.split(
            'Self="bg_st_storage_spec_storage_body"', 1,
        )[1].split("</Rectangle>", 1)[0]
        self.assertEqual(8, storage_background.count("<PathPointType "))
        self.assertIn(f'ParentStory="{spec_sid}"', spread)
        stories = "".join(dict(writer.stories).values())
        self.assertEqual(3, stories.count("specification table"))
        self.assertIn('SingleRowHeight="11"', stories)

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
            story_map = dict(writer.stories)
            stories = "".join(story_map.values())
            self.assertEqual(1, spread.count("<Page "))
            self.assertIn('StrokeColor="Color/HB Border K10"', spread)
            self.assertIn('Anchor="66 ', story_map["st_compact_card_1"])
            self.assertIn('Anchor="58 ', story_map["st_compact_card_2"])
            self.assertIn('Anchor="40 ', story_map["st_compact_card_3"])
            self.assertIn("art_st_compact_overview_front", spread)
            self.assertIn("art_st_compact_overview_right", spread)
            self.assertEqual(10, spread.count("<GraphicLine "))
            self.assertIn(
                'PointSize="5.2"',
                story_map["st_compact_fcc_left"],
            )
            self.assertIn(
                '<Leading type="unit">5.7</Leading>',
                story_map["st_compact_fcc_right"],
            )
            self.assertIn(
                'HorizontalScale="92"',
                story_map["st_compact_fcc_left"],
            )
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
                        {
                            "signal_key": "warning",
                            "label": "WARNING",
                            "text": "Hazardous practices.",
                        },
                        {
                            "signal_key": "caution",
                            "label": "CAUTION",
                            "text": "Personal injury risk.",
                        },
                        {
                            "signal_key": "note",
                            "label": "NOTE",
                            "text": "Equipment damage risk.",
                        },
                        {
                            "signal_key": "tips",
                            "label": "TIP",
                            "text": "Helpful information.",
                        },
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
                signal_xml = stories[f"st_symbols_shared_{language}_signals"]
                self.assertIn('PointSize="5.6"', signal_xml)
                self.assertIn("sig1icon", signal_xml)
                self.assertIn("sig2icon", signal_xml)
                self.assertNotIn("sig3icon", signal_xml)
                self.assertNotIn("sig4icon", signal_xml)
                self.assertIn('PointSize="0.1" Leading="0.1"', left_xml)
                self.assertIn('PointSize="0.1" Leading="0.1"', right_xml)
                self.assertIn('SingleRowHeight="28"', left_xml)
                self.assertIn('SingleRowHeight="60"', right_xml)
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
                (
                    "component",
                    json.dumps({
                        "kind": "notice",
                        "label": "NOTE",
                        "variant": "note",
                        "texts": ["Keep the editable note inside the card."],
                    }),
                ),
                ("h2", "LCD DISPLAY ON/OFF"),
                    (
                        "image",
                        (
                            ROOT / "docs" / "renderers" / "latex" / "assets"
                            / "jbp2000b_lcd_control.png"
                        ).as_posix(),
                    ),
                    (
                        "body",
                        "Press the POWER button to switch the LCD display.",
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
                        "operation_panel_variant": "paired_cards",
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
            self.assertTrue(any(
                "Press the POWER button to switch the LCD display." in xml
                for sid, xml in stories.items()
                if "image_caption" in sid
            ))
            operation_story = stories[operation_sid]
            self.assertIn("st_anchor_oppanel_", operation_story)
            operation_component_stories = "".join(
                xml for sid, xml in stories.items()
                if "oppanel" in sid
            )
            self.assertIn("grp_oppanel_", operation_component_stories)
            self.assertIn("image_notice", operation_component_stories)
            self.assertIn("image_caption", operation_component_stories)
            self.assertNotIn("grp_notice_st_operation_en_cmp", operation_story)
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
