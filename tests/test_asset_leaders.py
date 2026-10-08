#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Callout-leader suppression: the structural detector and its two traps."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asset_pipeline.leaders import (  # noqa: E402
    HALO_WIDTH,
    LINE_WIDTH,
    find_leader_geometries,
    suppress_leader_strokes,
)
from tools.asset_pipeline.extract import _leader_geometries_for_transform  # noqa: E402
from tools.asset_pipeline.recipe import _transform  # noqa: E402


class _Point:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y


class _Rect:
    def __init__(self, x0: float, y0: float, x1: float, y1: float) -> None:
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1

    @property
    def height(self) -> float:
        return self.y1 - self.y0


class _Page:
    def __init__(self, drawings: list[dict]) -> None:
        self._drawings = drawings

    def get_drawings(self) -> list[dict]:
        return self._drawings


def _stroke(width: float, points: list[tuple[float, float]]) -> dict:
    items = [
        ("l", _Point(*points[i]), _Point(*points[i + 1]))
        for i in range(len(points) - 1)
    ]
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return {
        "items": items,
        "width": width,
        "rect": _Rect(min(xs), min(ys), max(xs), max(ys)),
    }


CROP = (28.0, 98.0, 345.0, 283.0)


class FindLeadersTest(unittest.TestCase):
    def test_halo_and_line_pair_is_a_leader(self):
        elbow = [(341.0, 139.0), (215.0, 139.0), (215.0, 160.0)]
        page = _Page([_stroke(HALO_WIDTH, elbow), _stroke(LINE_WIDTH, elbow)])
        found = find_leader_geometries(None, page, CROP)
        self.assertEqual(len(found), 1)
        self.assertEqual(len(found[0]), 2)

    def test_single_segment_axis_aligned_leader_is_found(self):
        """A straight line has a zero-area rect; the overlap test must survive it."""
        straight = [(343.0, 168.0), (240.0, 168.0)]
        page = _Page([_stroke(HALO_WIDTH, straight), _stroke(LINE_WIDTH, straight)])
        self.assertEqual(len(find_leader_geometries(None, page, CROP)), 1)

    def test_unpaired_stroke_is_not_a_leader(self):
        """Device artwork shares the thin width; only the pair identifies a leader."""
        line = [(140.0, 184.0), (238.0, 184.0)]
        page = _Page([_stroke(LINE_WIDTH, line)])
        self.assertEqual(find_leader_geometries(None, page, CROP), ())

    def test_diagonal_pair_is_not_a_leader(self):
        diagonal = [(200.0, 150.0), (260.0, 190.0)]
        page = _Page([_stroke(HALO_WIDTH, diagonal), _stroke(LINE_WIDTH, diagonal)])
        self.assertEqual(find_leader_geometries(None, page, CROP), ())

    def test_leader_outside_the_crop_is_ignored(self):
        far = [(500.0, 600.0), (560.0, 600.0)]
        page = _Page([_stroke(HALO_WIDTH, far), _stroke(LINE_WIDTH, far)])
        self.assertEqual(find_leader_geometries(None, page, CROP), ())


class SuppressStrokesTest(unittest.TestCase):
    """The walker must resolve `cm` transforms before comparing geometry."""

    class _Doc:
        def __init__(self, stream: bytes) -> None:
            self.streams = {1: stream}

        def xref_stream(self, xref: int) -> bytes:
            return self.streams[xref]

        def update_stream(self, xref: int, data: bytes) -> None:
            self.streams[xref] = data

    class _RealPage:
        def __init__(self, height: float) -> None:
            self.rect = _Rect(0, 0, 400, height)

        def get_contents(self):
            return [1]

    def _run(self, stream: bytes, leaders) -> tuple[int, bytes]:
        import fitz

        doc = self._Doc(stream)
        page = self._RealPage(500.0)
        count = suppress_leader_strokes(fitz, doc, page, leaders)
        return count, doc.streams[1]

    def test_translated_leader_is_matched_and_neutralised(self):
        # `cm` shifts by (100, 300); page-space y is flipped against height 500.
        stream = b"q 1 0 0 1 100 300 cm 0 0 m 50 0 l S Q"
        leaders = (((100.0, 200.0, 150.0, 200.0),),)
        count, patched = self._run(stream, leaders)
        self.assertEqual(count, 1)
        self.assertIn(b" n ", patched)
        self.assertNotIn(b" S ", patched)
        self.assertEqual(len(patched), len(stream))  # geometry bytes untouched

    def test_unmatched_stroke_is_left_alone(self):
        stream = b"q 1 0 0 1 100 300 cm 0 0 m 50 0 l S Q"
        count, patched = self._run(stream, (((0.0, 0.0, 1.0, 1.0),),))
        self.assertEqual(count, 0)
        self.assertEqual(patched, stream)

    def test_no_leaders_is_a_no_op(self):
        stream = b"0 0 m 10 0 l S"
        self.assertEqual(self._run(stream, ())[0], 0)

    def test_bbox_suppresses_only_whole_right_leader_in_real_pdf(self):
        import fitz

        doc = fitz.open()
        page = doc.new_page(width=220, height=60)
        for x0, x1 in ((20, 80), (120, 180)):
            for width, color in ((2.0, (1, 1, 1)), (0.3, (0, 0, 0))):
                page.draw_line((x0, 30), (x1, 30), color=color, width=width)
        selected = _transform(
            {
                "op": "drop_leader_strokes",
                "bbox_pt": [118, 27, 182, 33],
                "halo_width_pt": 2.0,
                "line_width_pt": 0.3,
            },
            "test",
        )
        crop = fitz.Rect(0, 0, 220, 60)
        legacy = _transform({"op": "drop_leader_strokes", "halo_width_pt": 2.0, "line_width_pt": 0.3}, "test")
        self.assertEqual(
            find_leader_geometries(fitz, page, tuple(crop), halo_width=2.0, line_width=0.3),
            _leader_geometries_for_transform(fitz, page, crop, legacy),
        )
        leaders = _leader_geometries_for_transform(fitz, page, crop, selected)
        self.assertEqual(1, len(leaders))
        self.assertEqual(2, suppress_leader_strokes(fitz, doc, page, leaders))
        pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), alpha=False)
        self.assertLess(max(pixels.pixel(200, 120)), 240)
        self.assertEqual((255, 255, 255), pixels.pixel(600, 120))
        # A selector that only crosses a stroke cannot erase the whole path.
        partial = _transform(
            {
                "op": "drop_leader_strokes",
                "bbox_pt": [50, 27, 60, 33],
                "halo_width_pt": 2.0,
                "line_width_pt": 0.3,
            },
            "test",
        )
        self.assertEqual((), _leader_geometries_for_transform(fitz, page, crop, partial))
        doc.close()


class RealRecipeTest(unittest.TestCase):
    def test_front_controls_recipe_uses_the_structural_op(self):
        """The corrected base map must stay reproducible from a recipe."""
        import json

        recipe = json.loads(
            (ROOT / "data/asset_recipes/manual_je1000f_us_front_controls.json")
            .read_text(encoding="utf-8")
        )
        (asset,) = recipe["assets"]
        self.assertEqual(asset["asset_key"], "overview/je1000f_us/front_controls")
        ops = [t["op"] for t in asset["transforms"]]
        self.assertIn("drop_leader_strokes", ops)
        self.assertNotIn("whiteout", ops)

    def test_frozen_master_recipe_keeps_its_whiteouts(self):
        """The reviewed App-UI promotion pins the master recipe byte-for-byte."""
        import hashlib

        from tools.app_ui_promotion import EXPECTED_RECIPE_SHA256

        digest = hashlib.sha256(
            (ROOT / "data/asset_recipes/manual_je1000f_us_master.json").read_bytes()
        ).hexdigest()
        self.assertEqual(EXPECTED_RECIPE_SHA256, digest)


if __name__ == "__main__":
    unittest.main()
