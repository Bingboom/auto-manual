from __future__ import annotations

import unittest
from pathlib import Path

from tools.idml.reference_story_flow import ReferenceStoryEmitter


ROOT = Path(__file__).resolve().parents[1]


class _RecordingWriter:
    def __init__(self) -> None:
        self.params: dict[str, tuple[str, str]] = {}
        self.m_l = 20.0
        self.m_r = 21.0
        self.m_t = 22.0
        self.m_b = 23.0
        self.page_h = 500.0
        self.spread_chains: list[tuple[str, int, int, int]] = []
        self.chain_frames: list[tuple[str, int]] = []
        self.story_frames: list[tuple[str, list[tuple[int, float, float]]]] = []

    def add_prose_story(
        self,
        sid: str,
        _title: str,
        _blocks: list[tuple[str, str]],
        _bundle_root: Path,
    ) -> tuple[str, float]:
        return sid, 1.0

    def pages_for_height(self, _height: float) -> int:
        return 1

    def add_spread_chain(
        self,
        sid: str,
        pages: int,
        page_cursor: int,
        *,
        columns: int,
        **_kwargs: float,
    ) -> None:
        self.spread_chains.append((sid, pages, page_cursor, columns))
        self.chain_frames.extend(
            (sid, page_cursor + offset) for offset in range(pages)
        )

    def add_story_frames(
        self,
        sid: str,
        frames: list[tuple[int, float, float]],
        **_kwargs: float,
    ) -> None:
        self.story_frames.append((sid, frames))


class _RecordingToc:
    def __init__(self) -> None:
        self.latched: list[str] = []
        self.noted_pages: list[int] = []

    def latch(self, title: str) -> None:
        self.latched.append(title)

    def note_h1s(
        self,
        _blocks: list[tuple[str, str]],
        _page_cursor: int,
        pages: int,
    ) -> None:
        self.noted_pages.append(pages)


class ReferenceStoryEmitterTests(unittest.TestCase):
    def test_reference_span_overrides_smaller_height_estimate(self) -> None:
        writer = _RecordingWriter()
        toc = _RecordingToc()
        plan = {"physical_page_count": 20, "pages": [
            {"source_path": "page/operation.rst", "latex_start_page": 10},
            {"source_path": "page/charging.rst", "latex_start_page": 14},
        ]}
        emitter = ReferenceStoryEmitter(writer, toc, ROOT, plan)

        next_page = emitter.emit(
            "st_operation",
            "operation",
            [("h1", "OPERATION")],
            page_cursor=7,
        )

        self.assertEqual(11, next_page)
        self.assertEqual([("st_operation", 4, 7, 1)], writer.spread_chains)
        self.assertEqual(
            [("st_operation", page) for page in (7, 8, 9, 10)],
            writer.chain_frames,
        )
        self.assertEqual([4], toc.noted_pages)
        self.assertEqual([], writer.story_frames)

    def test_preface_remains_one_page_when_plan_span_is_larger(self) -> None:
        writer = _RecordingWriter()
        toc = _RecordingToc()
        plan = {"physical_page_count": 20, "pages": [
            {"source_path": "page/00_preface.rst", "latex_start_page": 2},
            {"source_path": "page/01_fcc.rst", "latex_start_page": 6},
        ]}
        emitter = ReferenceStoryEmitter(writer, toc, ROOT, plan)

        next_page = emitter.emit(
            "st_preface",
            "00_preface",
            [("body", "Preface")],
            page_cursor=1,
        )

        self.assertEqual(2, next_page)
        self.assertEqual([], writer.spread_chains)
        self.assertEqual([], writer.chain_frames)
        self.assertEqual(1, len(writer.story_frames))
        self.assertEqual(1, len(writer.story_frames[0][1]))
        self.assertEqual(1, writer.story_frames[0][1][0][0])
        self.assertEqual([], toc.noted_pages)


if __name__ == "__main__":
    unittest.main()
