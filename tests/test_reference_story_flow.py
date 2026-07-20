from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.idml.reference_story_flow import ReferenceStoryEmitter


ROOT = Path(__file__).resolve().parents[1]


def _approved_app_plan(
    *,
    model: str = "JE-1000F",
    region: str = "US",
    language: str = "en",
    stem: str = "12_app_setup_placeholder",
) -> dict:
    return {
        "plan_source": "approved-reference",
        "approved_contract": {
            "target": {
                "model": model,
                "region": region,
                "languages": [language],
            },
        },
        "pages": [{
            "source_path": f"page/{stem}.rst",
            "language": language,
        }],
    }


class _RecordingWriter:
    def __init__(self) -> None:
        self.params: dict[str, tuple[str, str]] = {}
        self.m_l = 20.0
        self.m_r = 21.0
        self.m_t = 22.0
        self.m_b = 23.0
        self.page_h = 500.0
        self.spread_chains: list[tuple[str, int, int, int]] = []
        self.spread_chain_options: list[dict[str, float]] = []
        self.chain_frames: list[tuple[str, int]] = []
        self.story_frames: list[tuple[str, list[tuple[int, float, float]]]] = []
        self.prose_story_options: list[dict[str, float]] = []

    def add_prose_story(
        self,
        sid: str,
        _title: str,
        _blocks: list[tuple[str, str]],
        _bundle_root: Path,
        **kwargs: float,
    ) -> tuple[str, float]:
        self.prose_story_options.append(kwargs)
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
        **kwargs: float,
    ) -> None:
        self.spread_chains.append((sid, pages, page_cursor, columns))
        self.spread_chain_options.append(kwargs)
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

    def test_operation_chain_extends_below_the_ordinary_body_margin(self) -> None:
        writer = _RecordingWriter()
        toc = _RecordingToc()
        emitter = ReferenceStoryEmitter(
            writer,
            toc,
            ROOT,
            {"plan_source": "approved-reference"},
        )
        key_rows = [
            ["Buttons", "Operation", "Function"],
            ["Power + AC", "Press 3s", "Enable"],
        ]

        emitter.emit(
            "st_operation",
            "05_operation_guide_placeholder",
            [
                ("h1", "OPERATIONS"),
                ("table", json.dumps(key_rows)),
            ],
            page_cursor=7,
        )

        self.assertEqual(18.0, writer.spread_chain_options[0]["bottom_extra"])
        self.assertEqual(
            -6.82,
            writer.spread_chain_options[0]["last_frame_x_offset"],
        )
        self.assertEqual(
            {"inline_origin_shift": -6.82},
            writer.prose_story_options[0],
        )

    def test_unapproved_operation_chain_keeps_the_standard_bottom(self) -> None:
        writer = _RecordingWriter()
        toc = _RecordingToc()
        emitter = ReferenceStoryEmitter(writer, toc, ROOT)
        key_rows = [
            ["Buttons", "Operation", "Function"],
            ["Power + AC", "Press 3s", "Enable"],
        ]

        emitter.emit(
            "st_operation",
            "05_operation_guide_placeholder",
            [("table", json.dumps(key_rows))],
            page_cursor=7,
        )

        self.assertEqual(0.0, writer.spread_chain_options[0]["bottom_extra"])

    def test_approved_charging_methods_chain_uses_reference_top_offset(self) -> None:
        writer = _RecordingWriter()
        toc = _RecordingToc()
        emitter = ReferenceStoryEmitter(
            writer,
            toc,
            ROOT,
            {"plan_source": "approved-reference"},
        )

        emitter.emit(
            "st_08_charging_methods",
            "08_charging_methods",
            [("h2", "Localized charging heading")],
            page_cursor=14,
        )

        self.assertEqual(23.8, writer.spread_chain_options[0]["first_top_offset"])

    def test_app_chain_uses_reference_top_offset(self) -> None:
        for language in ("en", "en-US", "en_US"):
            with self.subTest(language=language):
                writer = _RecordingWriter()
                toc = _RecordingToc()
                emitter = ReferenceStoryEmitter(
                    writer,
                    toc,
                    ROOT,
                    _approved_app_plan(language=language),
                )

                emitter.emit(
                    "st_12_app_setup",
                    "12_app_setup_placeholder",
                    [("h1", "Localized app heading"), ("h2", "Download")],
                    page_cursor=19,
                )

                self.assertEqual(
                    15.06,
                    writer.spread_chain_options[0]["first_top_offset"],
                )

    def test_app_chain_reference_offset_fails_closed_for_other_targets(self) -> None:
        cases = (
            ("wrong model", _approved_app_plan(model="OTHER")),
            ("wrong region", _approved_app_plan(region="EU")),
            ("French", _approved_app_plan(language="fr")),
            ("Spanish", _approved_app_plan(language="es")),
            ("missing metadata", {"plan_source": "approved-reference"}),
            (
                "missing language",
                {
                    **_approved_app_plan(),
                    "pages": [{
                        "source_path": "page/12_app_setup_placeholder.rst",
                    }],
                },
            ),
        )
        for label, plan in cases:
            with self.subTest(label=label):
                writer = _RecordingWriter()
                emitter = ReferenceStoryEmitter(
                    writer,
                    _RecordingToc(),
                    ROOT,
                    plan,
                )

                emitter.emit(
                    "st_12_app_setup",
                    "12_app_setup_placeholder",
                    [("h1", "Localized app heading"), ("h2", "Download")],
                    page_cursor=19,
                )

                self.assertEqual(
                    13.81,
                    writer.spread_chain_options[0]["first_top_offset"],
                )

    def test_noncanonical_app_chains_keep_their_existing_top_offsets(self) -> None:
        for title, h1, expected in (
            ("p34_12_app_setup_placeholder", "APP SETUP", 13.13),
            ("p50_12_app_setup_placeholder", "Localized app heading", 13.81),
        ):
            with self.subTest(title=title):
                writer = _RecordingWriter()
                toc = _RecordingToc()
                emitter = ReferenceStoryEmitter(
                    writer,
                    toc,
                    ROOT,
                    _approved_app_plan(
                        language=(
                            "fr" if title.startswith("p34_") else "es"
                        ),
                        stem=title,
                    ),
                )

                emitter.emit(
                    f"st_{title}",
                    title,
                    [("h1", h1), ("h2", "Download")],
                    page_cursor=19,
                )

                self.assertEqual(
                    expected,
                    writer.spread_chain_options[0]["first_top_offset"],
                )


if __name__ == "__main__":
    unittest.main()
