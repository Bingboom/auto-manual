"""The story estimate counts the gap an unbreakable figure leaves at a frame foot."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tools.export_idml import IdmlWriter, load_layout_params

ROOT = Path(__file__).resolve().parents[1]
ART = "_assets/charging/car_charge.png"


class FigureBreakEstimateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.params = load_layout_params(ROOT / "data" / "layout_params.csv")
        self._tmp = tempfile.TemporaryDirectory()
        self.bundle = Path(self._tmp.name)
        target = self.bundle / ART
        target.parent.mkdir(parents=True)
        shutil.copyfile(
            ROOT / "docs/templates/word_template/common_assets/charging/car_charge.png",
            target,
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _estimate(self, blocks, **options) -> float:
        writer = IdmlWriter(self.params)
        _, estimate = writer.add_prose_story(
            "st_probe", "08_charging_methods", blocks, self.bundle, **options,
        )
        return estimate

    def _figure_height(self) -> float:
        return self._estimate([("image", ART)])

    def _copy_until(self, limit: float) -> tuple[list[tuple[str, str]], float]:
        blocks: list[tuple[str, str]] = []
        used = 0.0
        while True:
            candidate = blocks + [("body", f"Copy line {len(blocks)} of the probe.")]
            height = self._estimate(candidate)
            if height > limit:
                return blocks, used
            blocks, used = candidate, height

    def test_a_figure_that_misses_the_frame_foot_adds_the_gap(self) -> None:
        frame = IdmlWriter(self.params).frame_height()
        figure = self._figure_height()
        # Copy that leaves less room than the figure needs, but some room.
        copy, used = self._copy_until(frame - figure / 2)
        self.assertGreater(used + figure, frame)
        blocks = copy + [("image", ART)]

        linear = self._estimate(blocks)
        modelled = self._estimate(blocks, figure_frame_height=frame)

        # The figure starts the next frame: the estimate gains the frame foot
        # the figure could not use, and nothing else.
        self.assertAlmostEqual(frame - used, modelled - linear, places=6)

    def test_a_figure_that_fits_the_frame_adds_nothing(self) -> None:
        frame = IdmlWriter(self.params).frame_height()
        figure = self._figure_height()
        copy, _ = self._copy_until(frame - figure * 1.5)
        blocks = copy + [("image", ART)]
        self.assertEqual(
            self._estimate(blocks),
            self._estimate(blocks, figure_frame_height=frame),
        )

    def test_two_column_stories_keep_the_linear_estimate(self) -> None:
        frame = IdmlWriter(self.params).frame_height()
        figure = self._figure_height()
        copy, _ = self._copy_until(frame - figure / 2)
        blocks = [("layout", "twocol_start"), ("layout", "twocol_end")] + copy + [("image", ART)]
        self.assertEqual(
            self._estimate(blocks),
            self._estimate(blocks, figure_frame_height=frame),
        )


if __name__ == "__main__":
    unittest.main()
