"""A prose figure can carry its source labels over the artwork.

The shipped JP battery-pack book sets the charging labels as live 6 pt Regular
text inside each illustration's own white band -- the band the text-free asset
extraction left behind when it redacted them. The pipeline printed them instead
as a two-cell table under the figure, which the renderer was right to do: the
page source authors them as a `list-table`.

So the copy stays in the page source, where translation, review and cloud-doc
backport can reach it, and the target contract supplies only where each label
sits, bound by cell ordinal the way the LCD hero callouts bind to their parts
rows. A figure whose target declares nothing keeps its table under the art.

The IDML goldens do not exercise this path -- regenerating all four leaves them
byte-identical -- so these tests are the only coverage.
"""

from __future__ import annotations

import inspect
import json
import unittest
from pathlib import Path

from tools.idml.stories import add_prose_story
from tools.idml.components.prose_image import (
    plan_figure_callouts,
    render_image_block,
)
from tools.idml.target_assembly_plan import _figure_callout_issues
from tools.idml.writer import IdmlWriter

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "docs/renderers/contracts/target_assembly"

LABEL_TABLE = json.dumps([["拡張ケーブル", "ACケーブル"]], ensure_ascii=False)
BLOCKS = [
    ("h2", "AC充電"),
    ("image", "asset:charging/jbp2000b/jp/ac_wall"),
    ("table", LABEL_TABLE),
]
GEOMETRY = (
    {"cell_index": 0, "x": 0.07, "y": 0.87, "width": 0.14},
    {"cell_index": 1, "x": 0.5485, "y": 0.8756, "width": 0.14},
)


class PairingCopyWithGeometry(unittest.TestCase):
    def plan(self, blocks, *figures):
        return plan_figure_callouts(blocks, tuple(figures))

    def test_each_ordinal_takes_its_source_label(self) -> None:
        planned, consumed = self.plan(BLOCKS, GEOMETRY)
        self.assertEqual([1], sorted(planned))
        self.assertEqual(
            ["拡張ケーブル", "ACケーブル"],
            [text for _callout, text in planned[1]],
        )
        self.assertEqual([0.07, 0.5485], [c["x"] for c, _t in planned[1]])
        self.assertEqual({2}, consumed)

    def test_declaring_out_of_source_order_still_binds_by_ordinal(self) -> None:
        """The reference sets the solar labels right-then-left."""
        planned, _consumed = self.plan(BLOCKS, (GEOMETRY[1], GEOMETRY[0]))
        self.assertEqual(
            ["ACケーブル", "拡張ケーブル"],
            [text for _callout, text in planned[1]],
        )

    def test_no_declaration_leaves_the_table_alone(self) -> None:
        """The isolation guarantee: every other target renders as before."""
        self.assertEqual(({}, set()), self.plan(BLOCKS))

    def test_a_figure_beyond_the_declaration_is_left_alone(self) -> None:
        """A second figure with no entry keeps its own label table."""
        blocks = [*BLOCKS, ("image", "asset:charging/jbp2000b/jp/solar"),
                  ("table", LABEL_TABLE)]
        planned, consumed = self.plan(blocks, GEOMETRY)
        self.assertEqual([1], sorted(planned))
        self.assertEqual({2}, consumed)

    def test_a_figure_with_no_following_table_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            self.plan(BLOCKS[:2], GEOMETRY)

    def test_an_ordinal_past_the_last_cell_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            self.plan(
                BLOCKS, ({"cell_index": 4, "x": 0.1, "y": 0.5, "width": 0.1},)
            )


class DefaultsProtectEveryOtherFigure(unittest.TestCase):
    def test_render_image_block_defaults_to_no_callouts(self) -> None:
        self.assertEqual(
            (), inspect.signature(render_image_block).parameters["callouts"].default
        )

    def test_prose_story_defaults_to_no_callouts(self) -> None:
        for target in (add_prose_story, IdmlWriter.add_prose_story):
            self.assertEqual(
                (),
                inspect.signature(target).parameters["image_callouts"].default,
                msg=target.__qualname__,
            )


class DeclaredGeometryIsRefused(unittest.TestCase):
    def test_absent_is_fine(self) -> None:
        self.assertEqual([], _figure_callout_issues(None, label="x"))

    def test_an_empty_declaration_is_refused(self) -> None:
        self.assertTrue(_figure_callout_issues([], label="x"))

    def test_a_fraction_outside_the_figure_is_refused(self) -> None:
        self.assertTrue(
            _figure_callout_issues(
                [[{"cell_index": 0, "x": 1.4, "y": 0.5, "width": 0.1}]], label="x"
            )
        )

    def test_a_label_running_off_the_right_edge_is_refused(self) -> None:
        self.assertTrue(
            _figure_callout_issues(
                [[{"cell_index": 0, "x": 0.95, "y": 0.5, "width": 0.2}]], label="x"
            )
        )

    def test_a_repeated_ordinal_is_refused(self) -> None:
        self.assertTrue(
            _figure_callout_issues(
                [[
                    {"cell_index": 0, "x": 0.1, "y": 0.5, "width": 0.1},
                    {"cell_index": 0, "x": 0.5, "y": 0.5, "width": 0.1},
                ]],
                label="x",
            )
        )

    def test_an_unknown_key_is_refused(self) -> None:
        self.assertTrue(
            _figure_callout_issues(
                [[{"cell_index": 0, "x": 0.1, "y": 0.5, "width": 0.1, "z": 1}]],
                label="x",
            )
        )

    def test_well_formed_geometry_passes(self) -> None:
        self.assertEqual([], _figure_callout_issues([list(GEOMETRY)], label="x"))


class ShippedContractsAreUnaffected(unittest.TestCase):
    def test_only_bp_jp_declares_figure_callouts(self) -> None:
        """Pins the blast radius.

        BP@US and BP@EU declare the same charging composition without callouts
        and keep printing their label tables. If another target starts
        declaring them, this is where that shows up.
        """
        declaring = []
        for path in sorted(CONTRACTS.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for page in data.get("pages", []):
                charging = (page.get("composition_data") or {}).get("charging") or {}
                if charging.get("figure_callouts"):
                    declaring.append(path.stem)
        self.assertEqual(["jbp2000b_jp_v1_candidate"], sorted(set(declaring)))

    def test_bp_jp_geometry_reproduces_the_reference_positions(self) -> None:
        """The declared fractions are measurements, so pin what they measure.

        Reference page 9: the AC panel box is x 28.7..340.3 / y 114.4..265.5 and
        the solar panel box is x 28.7..340.3 / y 316.7..496.2. `y` is the
        label's vertical centre, so a 6 pt label's bbox top is `y` less 3 pt.
        """
        data = json.loads(
            (CONTRACTS / "jbp2000b_jp_v1_candidate.json").read_text(encoding="utf-8")
        )
        figures = [
            grp
            for page in data.get("pages", [])
            for grp in (
                ((page.get("composition_data") or {}).get("charging") or {})
                .get("figure_callouts") or []
            )
        ]
        self.assertEqual(2, len(figures))

        boxes = [(28.7, 114.4, 311.6, 151.1), (28.7, 316.7, 311.6, 179.5)]
        expected = [
            [(50.5, 242.9), (199.6, 243.7)],
            [(37.6, 463.4), (285.6, 427.2)],
        ]
        for figure, (ox, oy, w, h), wanted in zip(figures, boxes, expected):
            self.assertEqual(len(wanted), len(figure))
            for callout, (ref_x, ref_top) in zip(figure, wanted):
                self.assertAlmostEqual(ref_x, ox + callout["x"] * w, delta=0.1)
                self.assertAlmostEqual(
                    ref_top, oy + callout["y"] * h - 3.0, delta=0.1
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
