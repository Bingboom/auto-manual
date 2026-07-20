from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

from tools.export_idml import IdmlWriter, check_idml, load_layout_params
from tools.idml.page_overview import add_product_overview_page


ROOT = Path(__file__).resolve().parents[1]


class ProductOverviewPageTests(unittest.TestCase):
    def test_overview_is_native_labels_plus_two_linked_art_frames(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            (bundle / "front.png").write_bytes(b"front-art")
            (bundle / "right.png").write_bytes(b"right-art")
            blocks = [
                ("h1", "PRODUCT OVERVIEW"),
                ("h2", "FRONT VIEW"),
                ("image", "front.png"),
                ("table", [
                    ["**Power Button**", "**LCD**"],
                    ["**DC 12 V Port** 12 V / 10 A max.", "**LED Light Button**"],
                    ["**DC / USB Power Button**", "**LED Light**"],
                    ["**USB-C 30 W Output** 30 W max., 5 V⎓3 A", "**AC Power Button**"],
                    ["**USB-C 100 W Output** 100 W max.", "**AC Output** 120 V~"],
                    ["**USB-A 18 W Output** 18 W max."],
                ]),
                ("table", [["**Total Output** 1500 W Rated"]]),
                ("h2", "RIGHT SIDE VIEW"),
                ("image", "right.png"),
                ("table", [
                    ["**Handle**", "**AC Input** 100-120 V~"],
                    ["", "**DC Input (2 x DC8020 Ports)** PV and Car"],
                ]),
            ]
            writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))

            add_product_overview_page(writer, "st_overview_en", blocks, bundle, 6)

            self.assertEqual(1, len(writer.spreads))
            spread = writer.spreads[0][1]
            self.assertEqual(2, spread.count("ContentType=\"GraphicType\""))
            self.assertIn("front.png", spread)
            self.assertIn("right.png", spread)
            self.assertNotIn("product_overview-en.pdf", spread)
            stories = "".join(xml for _, xml in writer.stories)
            self.assertIn("Power Button", stories)
            self.assertIn("DC Input (2 x DC8020 Ports)", stories)
            self.assertIn("PointSize=\"7\"", stories)
            self.assertIn("PointSize=\"5\"", stories)
            self.assertIn('FontStyle="Regular" PointSize="5"', stories)
            label_stories = [
                xml
                for story_id, xml in writer.stories
                if story_id.startswith("st_overview_en_front_label_")
                or story_id.startswith("st_overview_en_right_label_")
            ]
            label_runs = [
                run
                for story_xml in label_stories
                for run in ElementTree.fromstring(story_xml).iter(
                    "CharacterStyleRange"
                )
                if run.find("Content") is not None
            ]
            self.assertGreater(len(label_runs), 0)
            for run in label_runs:
                point_size = run.attrib["PointSize"]
                expected_leading = {"7": "7.9", "5": "6.2"}[point_size]
                self.assertNotIn("Leading", run.attrib)
                leading = run.find("./Properties/Leading")
                self.assertIsNotNone(leading)
                self.assertEqual("unit", leading.attrib.get("type"))
                self.assertEqual(expected_leading, leading.text)
            self.assertEqual(32, spread.count("<GraphicLine "))
            self.assertEqual(16, spread.count('StrokeWeight="1.82"'))
            self.assertEqual(16, spread.count('StrokeWeight="0.3"'))
            self.assertIn("leader_st_overview_en_total_connector", spread)
            self.assertIn("leader_st_overview_en_dc_input", spread)
            self.assertIn("leader_st_overview_en_ac_input", spread)
            self.assertLess(
                spread.index("leader_st_overview_en_total_connector"),
                spread.index("tf_st_overview_en_front_label_1"),
            )
            self.assertNotIn('Locked="true"', spread)

            output = bundle / "overview.idml"
            writer.write(output)
            self.assertEqual([], check_idml(output))

    def test_localized_table_shapes_preserve_all_overview_labels(self) -> None:
        from tools.idml.page_overview import _front_cells, _right_cells

        french_front = [
            ("table", [
                ["**Power**", "**LCD**"],
                ["**DC 12 V**", "**LED button**"],
                ["**DC / USB**", "**LED**"],
                ["**USB-C 30 W**", "**AC button**"],
                ["**USB-C 100 W**"],
                ["**USB-A 18 W**", "**AC Output**"],
            ]),
            ("table", [["**Total Output**"]]),
        ]
        self.assertEqual(
            [
                "Power", "LCD", "DC 12 V", "LED button", "USB-C 30 W",
                "LED", "USB-C 100 W", "AC button", "USB-A 18 W",
                "AC Output", "DC / USB", "Total Output",
            ],
            [label for label, _value in _front_cells(french_front)],
        )

        cases = (
            (
                [["**Handle**", "**AC Input**"], ["", "**DC Input**"]],
                ["Handle", "DC Input", "AC Input"],
            ),
            (
                [["**Poignee**"], ["**Entree CA**", "**Entree CC**"]],
                ["Poignee", "Entree CC", "Entree CA"],
            ),
            (
                [["**Asa**"], ["**Entrada CA**"], ["**Entrada CC**"]],
                ["Asa", "Entrada CC", "Entrada CA"],
            ),
        )
        for table, expected in cases:
            with self.subTest(table=table):
                self.assertEqual(
                    expected,
                    [
                        label
                        for label, _value in _right_cells([("table", table)])
                    ],
                )

    def test_overview_rejects_missing_governed_art(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
            blocks = [
                ("h1", "PRODUCT OVERVIEW"),
                ("h2", "FRONT VIEW"),
                ("image", "missing-front.png"),
                ("h2", "RIGHT SIDE VIEW"),
                ("image", "missing-right.png"),
            ]
            with self.assertRaisesRegex(ValueError, "unresolved governed image"):
                add_product_overview_page(
                    writer, "st_overview_en", blocks, Path(td), 6)

    def test_reference_geometry_covers_every_semantic_leader(self) -> None:
        from tools.idml.page_overview import (
            _FRONT_RECTS,
            _LEADER_PATHS,
            _RIGHT_RECTS,
        )

        self.assertEqual(12, len(_FRONT_RECTS))
        self.assertEqual(3, len(_RIGHT_RECTS))
        self.assertEqual(16, len(_LEADER_PATHS))
        self.assertEqual(
            ("power", ((31.489, 114.185), (158.505, 114.185),
                       (158.505, 161.418))),
            _LEADER_PATHS[0],
        )
        self.assertEqual(
            ("total_connector", ((213.902, 213.103), (213.902, 260.327))),
            _LEADER_PATHS[-1],
        )


if __name__ == "__main__":
    unittest.main()
