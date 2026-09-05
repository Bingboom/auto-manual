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
    source_ref = f"page/{stem}.rst"
    return {
        "plan_source": "approved-reference",
        "approved_contract": {
            "schema_version": "approved-reference-layout-plan/v1",
            "target": {
                "model": model,
                "region": region,
                "languages": [language],
            },
            "approval": {"status": "approved"},
            "idml_contract": {
                "editable_components": {
                    "app_add_device": {"page_owners": [source_ref]},
                },
            },
            "pages": [{"source_ref": source_ref, "language": language}],
        },
        "pages": [{
            "source_ref": source_ref,
            "source_path": source_ref,
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
        self.prose_story_blocks: list[list[tuple[str, str]]] = []

    def add_prose_story(
        self,
        sid: str,
        _title: str,
        _blocks: list[tuple[str, str]],
        _bundle_root: Path,
        **kwargs: float,
    ) -> tuple[str, float]:
        self.prose_story_options.append(kwargs)
        self.prose_story_blocks.append(list(_blocks))
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
    def test_fallback_span_never_exceeds_the_story_height_estimate(self) -> None:
        """A measured physical gap is not a request to thread blank frames.

        LaTeX and the IDML writer are different composition engines, so the
        anchor distance can cover more pages than the writer actually composes
        the section into, and every surplus frame in the chain is then a blank
        body page.  This is the exception the preface already carried,
        generalized to every fallback story (JE-1000F/JP folio 04).
        """
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

        self.assertEqual(8, next_page)
        self.assertEqual([("st_operation", 1, 7, 1)], writer.spread_chains)
        self.assertEqual([("st_operation", 7)], writer.chain_frames)
        self.assertEqual([1], toc.noted_pages)
        self.assertEqual([], writer.story_frames)

    def test_explicit_assembly_span_still_overrides_the_estimate(self) -> None:
        """An approved contract mapped page-by-page by a human still wins."""
        writer = _RecordingWriter()
        toc = _RecordingToc()
        plan = {
            "plan_source": "target-assembly",
            "physical_page_count": 20,
            "pages": [
                {
                    "source_path": "page/operation.rst",
                    "latex_start_page": 10,
                    "composition_id": "operation-en",
                    "planned_page_count": 4,
                },
                {
                    "source_path": "page/charging.rst",
                    "latex_start_page": 14,
                    "composition_id": "charging-en",
                    "planned_page_count": 1,
                },
            ],
        }
        emitter = ReferenceStoryEmitter(writer, toc, ROOT, plan)

        next_page = emitter.emit(
            "st_operation",
            "operation",
            [("h1", "OPERATION")],
            page_cursor=7,
        )

        self.assertEqual(11, next_page)
        self.assertEqual([("st_operation", 4, 7, 1)], writer.spread_chains)

    def test_authored_page_breaks_keep_a_frame_each(self) -> None:
        """The height estimate ignores forced breaks; the cap must not."""
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
            [
                ("h1", "OPERATION"),
                ("layout", "page_break"),
                ("body", "second page"),
                ("layout", "page_break"),
                ("body", "third page"),
            ],
            page_cursor=7,
        )

        self.assertEqual(10, next_page)
        self.assertEqual([("st_operation", 3, 7, 1)], writer.spread_chains)

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
            {"inline_origin_shift": -6.82, "language": "en"},
            writer.prose_story_options[0],
        )

    def test_operation_chain_uses_only_its_language_specific_bottom_override(
        self,
    ) -> None:
        for language, expected in (("en", 18.0), ("fr", 46.0), ("es", 46.0)):
            with self.subTest(language=language):
                writer = _RecordingWriter()
                writer.params["comp_operation_page_extra_height"] = (
                    "18", "pt",
                )
                writer.params["lang_es_comp_operation_page_extra_height"] = (
                    "46", "pt",
                )
                writer.params["lang_fr_comp_operation_page_extra_height"] = (
                    "46", "pt",
                )
                title = f"05_operation_guide_{language}"
                emitter = ReferenceStoryEmitter(
                    writer,
                    _RecordingToc(),
                    ROOT,
                    {
                        "plan_source": "approved-reference",
                        "pages": [{
                            "source_path": f"page/{title}.rst",
                            "language": language,
                        }],
                    },
                )

                emitter.emit(
                    f"st_{title}",
                    title,
                    [("h1", "Localized operation heading")],
                    page_cursor=7,
                )

                self.assertEqual(
                    expected,
                    writer.spread_chain_options[0]["bottom_extra"],
                )

    def test_all_approved_warranty_locales_use_governed_frame_geometry(
        self,
    ) -> None:
        cases = {
            "en": ("11_warranty", "WARRANTY", -0.32),
            "fr": ("p33_11_warranty", "GARANTIE", -2.02),
            "es": ("p49_11_warranty", "GARANTÍA", -2.02),
        }
        for language, (title, heading, expected_x) in cases.items():
            with self.subTest(language=language):
                writer = _RecordingWriter()
                writer.params["comp_warranty_page_extra_height"] = (
                    "17.01", "pt",
                )
                writer.params[
                    f"lang_{language}_idml_warranty_frame_x_offset"
                ] = (str(expected_x), "pt")
                emitter = ReferenceStoryEmitter(
                    writer,
                    _RecordingToc(),
                    ROOT,
                    {
                        "plan_source": "approved-reference",
                        "pages": [{
                            "source_path": f"page/{title}.rst",
                            "composition_id": f"{language}_warranty",
                            "language": language,
                        }],
                    },
                )

                emitter.emit(
                    f"st_{title}",
                    title,
                    [("h1", heading)],
                    page_cursor=18,
                )

                self.assertEqual(
                    17.01,
                    writer.spread_chain_options[0]["bottom_extra"],
                )
                self.assertEqual(
                    expected_x,
                    writer.spread_chain_options[0]["last_frame_x_offset"],
                )

    def test_target_warranty_reuses_shared_composition_geometry(self) -> None:
        writer = _RecordingWriter()
        writer.params["comp_warranty_page_extra_height"] = ("17.01", "pt")
        writer.params["lang_en_idml_warranty_frame_x_offset"] = (
            "-0.32", "pt",
        )
        writer.params["lang_en_idml_warranty_page_top_offset"] = (
            "14.22", "pt",
        )
        emitter = ReferenceStoryEmitter(
            writer,
            _RecordingToc(),
            ROOT,
            {
                "plan_source": "target-assembly",
                "pages": [{
                    "source_path": "page/warranty_en.rst",
                    "composition_id": "en_warranty",
                    "composition_type": "warranty",
                    "language": "en",
                    "composition_data": {
                        "warranty": {"layout_variant": "multiline_lead"},
                    },
                }],
            },
        )

        emitter.emit(
            "st_warranty_en",
            "warranty_en",
            [
                ("h1", "WARRANTY"),
                ("component", json.dumps({
                    "kind": "warrantylead",
                    "texts": ["Lead."],
                })),
            ],
            page_cursor=10,
        )

        self.assertEqual(
            17.01,
            writer.spread_chain_options[0]["bottom_extra"],
        )
        self.assertEqual(
            -0.32,
            writer.spread_chain_options[0]["last_frame_x_offset"],
        )
        self.assertEqual(
            {
                "inline_origin_shift": -0.32,
                "semantic_page_role": "warranty",
                "language": "en",
            },
            writer.prose_story_options[0],
        )
        self.assertEqual(
            14.22,
            writer.spread_chain_options[0]["first_top_offset"],
        )
        projected_lead = json.loads(writer.prose_story_blocks[0][1][1])
        self.assertEqual("multiline_lead", projected_lead["layout_variant"])

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
        self.assertEqual(18.0, writer.spread_chain_options[0]["bottom_extra"])

        writer = _RecordingWriter()
        emitter = ReferenceStoryEmitter(
            writer,
            _RecordingToc(),
            ROOT,
            {"plan_source": "approved-reference"},
        )
        emitter.emit(
            "st_p29_08_charging_methods",
            "p29_08_charging_methods",
            [("h2", "Localized charging heading")],
            page_cursor=28,
        )
        self.assertEqual(54.0, writer.spread_chain_options[0]["bottom_extra"])

    def test_localized_charging_methods_use_measured_top_offsets(self) -> None:
        for stem, language, expected in (
            ("08_charging_methods", "en", 23.8),
            ("p29_08_charging_methods", "fr", 15.3),
            ("p45_08_charging_methods", "es", 11.8),
        ):
            with self.subTest(language=language):
                writer = _RecordingWriter()
                writer.params.update({
                    "idml_charging_methods_page_top_offset": ("23.8", "pt"),
                    f"lang_{language}_idml_charging_methods_page_top_offset": (
                        str(expected), "pt",
                    ),
                })
                emitter = ReferenceStoryEmitter(
                    writer,
                    _RecordingToc(),
                    ROOT,
                    {
                        "plan_source": "approved-reference",
                        "pages": [{
                            "source_path": f"page/{stem}.rst",
                            "composition_id": f"{language}_charging_methods",
                            "language": language,
                        }],
                    },
                )

                emitter.emit(
                    f"st_{stem}", stem,
                    [("h2", "Localized charging heading")],
                    page_cursor=14,
                )

                self.assertEqual(
                    expected,
                    writer.spread_chain_options[0]["first_top_offset"],
                )

    def test_approved_charging_intro_chain_gets_dense_final_frame_allowance(self) -> None:
        writer = _RecordingWriter()
        toc = _RecordingToc()
        emitter = ReferenceStoryEmitter(
            writer,
            toc,
            ROOT,
            {"plan_source": "approved-reference"},
        )

        emitter.emit(
            "st_flow_06_ups_mode_charging",
            "06_ups_mode + charging",
            [("h1", "UPS MODE"), ("body", "Charging via AC wall outlet")],
            page_cursor=13,
        )

        self.assertEqual(18.0, writer.spread_chain_options[0]["bottom_extra"])

    def test_approved_ups_composition_uses_localized_top_offset_and_language(self) -> None:
        expected_offsets = {"en": 20.86, "fr": 12.65, "es": 15.22}
        for language, expected in expected_offsets.items():
            with self.subTest(language=language):
                writer = _RecordingWriter()
                writer.params[f"lang_{language}_idml_ups_page_top_offset"] = (
                    str(expected), "pt",
                )
                plan = {
                    "plan_source": "approved-reference",
                    "pages": [
                        {
                            "source_path": "page/06_ups_mode.rst",
                            "composition_id": "ups_charging",
                            "language": language,
                            "planned_page_count": 1,
                        },
                        {
                            "source_path": "page/charging.rst",
                            "composition_id": "ups_charging",
                            "language": language,
                            "planned_page_count": 1,
                        },
                    ],
                }
                emitter = ReferenceStoryEmitter(
                    writer, _RecordingToc(), ROOT, plan,
                )
                emitter.emit(
                    "st_ups_charging",
                    "06_ups_mode + charging",
                    [("h1", "Localized UPS"), ("body", "Charging")],
                    page_cursor=13,
                )

                self.assertEqual(
                    expected,
                    writer.spread_chain_options[0]["first_top_offset"],
                )
                self.assertEqual(
                    {"inline_origin_shift": 0.0, "language": language},
                    writer.prose_story_options[0],
                )

    def test_troubleshooting_chain_uses_component_frame_depth_allowance(self) -> None:
        writer = _RecordingWriter()
        writer.params["comp_trouble_page_extra_height"] = ("32", "pt")
        emitter = ReferenceStoryEmitter(
            writer,
            _RecordingToc(),
            ROOT,
            {"plan_source": "approved-reference"},
        )

        emitter.emit(
            "st_flow_storage_troubleshooting",
            "09_storage_and_maintenance + troubleshooting_en",
            [("h1", "TROUBLESHOOTING")],
            page_cursor=16,
        )

        self.assertEqual(32.0, writer.spread_chain_options[0]["bottom_extra"])

    def test_measured_troubleshooting_chain_reuses_component_allowance(self) -> None:
        writer = _RecordingWriter()
        writer.params["comp_trouble_page_extra_height"] = ("32", "pt")
        emitter = ReferenceStoryEmitter(
            writer,
            _RecordingToc(),
            ROOT,
            {"schema_version": "latex-page-plan/v1", "pages": []},
        )

        emitter.emit(
            "st_flow_troubleshooting_es_charging_es",
            "troubleshooting_es + charging_es + storage_es",
            [("h1", "SOLUCIÓN DE PROBLEMAS")],
            page_cursor=23,
        )

        self.assertEqual(32.0, writer.spread_chain_options[0]["bottom_extra"])

    def test_measured_overview_chain_gets_tokenized_import_allowance(self) -> None:
        writer = _RecordingWriter()
        writer.params["idml_measured_overview_page_extra_height"] = ("48", "pt")
        emitter = ReferenceStoryEmitter(
            writer,
            _RecordingToc(),
            ROOT,
            {"schema_version": "latex-page-plan/v1", "pages": []},
        )

        emitter.emit(
            "st_flow_fcc_en_box_contents_en",
            "fcc_en + box_contents_en + product_overview_en",
            [("h1", "PRODUCT OVERVIEW")],
            page_cursor=4,
        )

        self.assertEqual(48.0, writer.spread_chain_options[0]["bottom_extra"])

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

    def test_app_chain_reference_offset_fails_closed_without_contract_ownership(self) -> None:
        unowned = _approved_app_plan()
        unowned["approved_contract"]["idml_contract"]["editable_components"][
            "app_add_device"
        ]["page_owners"] = ["page/other.rst"]
        draft = _approved_app_plan()
        draft["approved_contract"]["approval"] = {"status": "draft"}
        cases = (
            ("future target", _approved_app_plan(model="OTHER", region="EU"), 15.06),
            ("French", _approved_app_plan(language="fr"), 15.06),
            ("Spanish", _approved_app_plan(language="es"), 15.06),
            ("unowned page", unowned, 13.81),
            ("draft contract", draft, 13.81),
            ("missing metadata", {"plan_source": "approved-reference"}, 13.81),
            (
                "missing language",
                {
                    **_approved_app_plan(),
                    "pages": [{
                        "source_path": "page/12_app_setup_placeholder.rst",
                    }],
                },
                13.81,
            ),
        )
        for label, plan, expected in cases:
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

                self.assertEqual(expected, writer.spread_chain_options[0]["first_top_offset"])

    def test_localized_app_chains_use_the_approved_top_offset(self) -> None:
        for title, h1, expected in (
            ("p34_12_app_setup_placeholder", "APP SETUP", 15.06),
            ("p50_12_app_setup_placeholder", "Localized app heading", 15.06),
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
