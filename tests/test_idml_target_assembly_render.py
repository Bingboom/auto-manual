from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from tools.idml.ir_projection import ProjectedPage
from tools.idml.target_assembly_render import TargetAssemblyRenderer


class TargetAssemblyRenderTests(unittest.TestCase):
    def test_symbols_route_places_the_shared_panel_and_marks_the_language_emitted(
        self,
    ) -> None:
        """Symbols compositions must claim ``symbols:<lang>`` for the book.

        ``export_idml`` emits a standalone Symbols page for any language the
        renderer did not already mark as emitted, so dropping the marker would
        print the Symbols panel twice.  The missing-data guard is pinned here
        too: a target that plans a Symbols composition without Symbols rows must
        fail the build instead of composing an empty panel.
        """
        bundle_root = Path("/tmp/bundle")
        symbols_ref = "page/symbols_ko.rst"
        page_plan = {
            "plan_source": "target-assembly",
            "physical_page_count": 1,
            "pages": [{
                "source_ref": symbols_ref,
                "source_path": symbols_ref,
                "language": "ko",
                "page_role": "symbols",
                "composition_id": "ko_symbols",
                "composition_type": "symbols",
                "latex_start_page": 1,
                "planned_page_count": 1,
            }],
        }
        projected_by_path = {
            bundle_root / symbols_ref: ProjectedPage(
                path=bundle_root / symbols_ref,
                language="ko",
                blocks=(("h1", "기호의 의미"),),
                skipped_raw=0,
                twocol=False,
            )
        }
        symbol_data = Mock(title="기호의 의미")
        emitted: set[str] = set()
        renderer = TargetAssemblyRenderer(
            page_plan=page_plan,
            projected_by_path=projected_by_path,
            bundle_root=bundle_root,
            writer=Mock(),
            toc=Mock(),
            manual_ir=Mock(),
            root=Path("/tmp/repo"),
            data_root=Path("/tmp/data"),
            output_lang="ko",
            emitted=emitted,
            spec_sections=[],
            lcd_rows=[],
            trouble_rows=[],
            symbol_data_for=Mock(return_value=symbol_data),
            slug_stem=lambda value: value,
        )

        with patch(
            "tools.idml.target_assembly_render.shared_page.add_symbols_page"
        ) as add_page:
            delta = renderer.render(
                bundle_root / symbols_ref,
                get_page_cursor=lambda: 5,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

        self.assertEqual(1, delta.page_count)
        self.assertEqual("st_ko_symbols", add_page.call_args.kwargs["sid"])
        self.assertIs(symbol_data, add_page.call_args.kwargs["symbol_data"])
        self.assertIn("symbols:ko", emitted)

    def test_safety_symbols_forwards_target_declared_column_split(self) -> None:
        bundle_root = Path("/tmp/bundle")
        safety_ref = "page/safety_info_de.rst"
        symbols_ref = "page/symbol_meaning_de.rst"
        composition_data = {"symbols": {"left_count": 6}}
        page_plan = {
            "plan_source": "target-assembly",
            "physical_page_count": 1,
            "pages": [
                {
                    "source_ref": safety_ref,
                    "source_path": safety_ref,
                    "language": "de",
                    "page_role": "safety",
                    "composition_id": "de_safety_symbols",
                    "composition_type": "safety_symbols",
                    "latex_start_page": 1,
                    "planned_page_count": 1,
                },
                {
                    "source_ref": symbols_ref,
                    "source_path": symbols_ref,
                    "language": "de",
                    "page_role": "symbols",
                    "composition_id": "de_safety_symbols",
                    "composition_type": "safety_symbols",
                    "latex_start_page": 1,
                    "planned_page_count": 1,
                    "composition_data": composition_data,
                },
            ],
        }
        projected_by_path = {
            bundle_root / ref: ProjectedPage(
                path=bundle_root / ref,
                language="de",
                blocks=(("h1", "SICHERHEIT"),),
                skipped_raw=0,
                twocol=False,
            )
            for ref in (safety_ref, symbols_ref)
        }
        renderer = TargetAssemblyRenderer(
            page_plan=page_plan,
            projected_by_path=projected_by_path,
            bundle_root=bundle_root,
            writer=Mock(),
            toc=Mock(),
            manual_ir=Mock(),
            root=Path("/tmp/repo"),
            data_root=Path("/tmp/data"),
            output_lang="de",
            emitted=set(),
            spec_sections=[],
            lcd_rows=[],
            trouble_rows=[],
            symbol_data_for=Mock(return_value=Mock(title="SYMBOLE")),
            slug_stem=lambda value: value,
        )

        with patch(
            "tools.idml.target_assembly_render.shared_page.add_safety_symbols_page"
        ) as add_page:
            renderer.render(
                bundle_root / safety_ref,
                get_page_cursor=lambda: 5,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

        self.assertEqual(
            composition_data,
            add_page.call_args.kwargs["composition_data"],
        )

        starved = TargetAssemblyRenderer(
            page_plan=page_plan,
            projected_by_path=projected_by_path,
            bundle_root=bundle_root,
            writer=Mock(),
            toc=Mock(),
            manual_ir=Mock(),
            root=Path("/tmp/repo"),
            data_root=Path("/tmp/data"),
            output_lang="ko",
            emitted=set(),
            spec_sections=[],
            lcd_rows=[],
            trouble_rows=[],
            symbol_data_for=Mock(return_value=None),
            slug_stem=lambda value: value,
        )

        with patch(
            "tools.idml.target_assembly_render.shared_page.add_symbols_page"
        ), self.assertRaisesRegex(ValueError, "missing Symbols data"):
            starved.render(
                bundle_root / symbols_ref,
                get_page_cursor=lambda: 5,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

    def test_inbox_overview_route_merges_both_source_entries_composition_data(
        self,
    ) -> None:
        """Both halves of an inbox_overview page must reach the compositor.

        This is the only route that reads ``composition_data`` from two
        different plan entries by position: ``source_refs[0]`` carries the inbox
        layout variant and ``source_refs[1]`` carries the overview instance id.
        Swapping or dropping one side silently strips the overview's callout
        bindings, and losing the second-source dedupe would double-count the
        page and shift every later ``page_index`` by one.
        """
        bundle_root = Path("/tmp/bundle")
        inbox_ref = "page/02_whats_in_the_box.rst"
        overview_ref = "page/03_product_overview_placeholder.rst"
        inbox_data = {"inbox": {"layout_variant": "compact_with_tip"}}
        overview_data = {"overview": {"instance_id": "je3000c-kr-v1"}}
        page_plan = {
            "plan_source": "target-assembly",
            "physical_page_count": 1,
            "pages": [
                {
                    "source_ref": inbox_ref,
                    "source_path": inbox_ref,
                    "language": "ko",
                    "page_role": "inbox",
                    "composition_id": "ko_inbox_overview",
                    "composition_type": "inbox_overview",
                    "latex_start_page": 1,
                    "planned_page_count": 1,
                    "composition_data": inbox_data,
                },
                {
                    "source_ref": overview_ref,
                    "source_path": overview_ref,
                    "language": "ko",
                    "page_role": "product_overview",
                    "composition_id": "ko_inbox_overview",
                    "composition_type": "inbox_overview",
                    "latex_start_page": 1,
                    "planned_page_count": 1,
                    "composition_data": overview_data,
                },
            ],
        }
        projected_by_path = {
            bundle_root / inbox_ref: ProjectedPage(
                path=bundle_root / inbox_ref,
                language="ko",
                blocks=(("h1", "구성품"),),
                skipped_raw=0,
                twocol=False,
            ),
            bundle_root / overview_ref: ProjectedPage(
                path=bundle_root / overview_ref,
                language="ko",
                blocks=(("h1", "제품 개요"),),
                skipped_raw=0,
                twocol=False,
            ),
        }
        renderer = TargetAssemblyRenderer(
            page_plan=page_plan,
            projected_by_path=projected_by_path,
            bundle_root=bundle_root,
            writer=Mock(),
            toc=Mock(),
            manual_ir=Mock(),
            root=Path("/tmp/repo"),
            data_root=Path("/tmp/data"),
            output_lang="ko",
            emitted=set(),
            spec_sections=[],
            lcd_rows=[],
            trouble_rows=[],
            symbol_data_for=Mock(),
            slug_stem=lambda value: value,
        )

        with patch(
            "tools.idml.target_assembly_render.shared_page.add_inbox_overview_page"
        ) as add_page:
            first = renderer.render(
                bundle_root / inbox_ref,
                get_page_cursor=lambda: 4,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )
            second = renderer.render(
                bundle_root / overview_ref,
                get_page_cursor=lambda: 5,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

        self.assertEqual(1, add_page.call_count)
        self.assertEqual(1, first.page_count)
        self.assertEqual(0, second.page_count)
        self.assertEqual(
            {
                "inbox": {"layout_variant": "compact_with_tip"},
                "overview": {"instance_id": "je3000c-kr-v1"},
            },
            add_page.call_args.kwargs["composition_data"],
        )

    def test_app_route_passes_the_whole_composition_span_and_the_source_stem(
        self,
    ) -> None:
        """The app route must forward the composition span and the RST stem.

        ``add_app_composition`` uses ``source_stem`` to align the second app
        page and to match approved/target app control labels, which key on the
        source stem rather than the composition id — passing the composition id
        makes figure promotion silently no-op and the app page renders raw
        images with no editable labels.  ``page_count`` must be the full
        composition span so the second physical page is reserved.
        """
        bundle_root = Path("/tmp/bundle")
        app_ref = "page/12_app_setup_placeholder.rst"
        page_plan = {
            "plan_source": "target-assembly",
            "physical_page_count": 2,
            "pages": [{
                "source_ref": app_ref,
                "source_path": app_ref,
                "language": "ko",
                "page_role": "app_setup",
                "composition_id": "ko_app",
                "composition_type": "app",
                "latex_start_page": 1,
                "planned_page_count": 2,
                "composition_data": {
                    "app": {
                        "instance_id": "je3000c-kr-v1",
                        "labels_by_role": {"primary": "기기 추가"},
                    }
                },
            }],
        }
        projected_by_path = {
            bundle_root / app_ref: ProjectedPage(
                path=bundle_root / app_ref,
                language="ko",
                blocks=(("h1", "앱 설정"), ("image", "app.png")),
                skipped_raw=0,
                twocol=False,
            )
        }
        renderer = TargetAssemblyRenderer(
            page_plan=page_plan,
            projected_by_path=projected_by_path,
            bundle_root=bundle_root,
            writer=Mock(),
            toc=Mock(),
            manual_ir=Mock(),
            root=Path("/tmp/repo"),
            data_root=Path("/tmp/data"),
            output_lang="ko",
            emitted=set(),
            spec_sections=[],
            lcd_rows=[],
            trouble_rows=[],
            symbol_data_for=Mock(),
            slug_stem=lambda value: value,
        )

        with patch(
            "tools.idml.target_assembly_render.shared_page.add_app_composition"
        ) as add_page:
            delta = renderer.render(
                bundle_root / app_ref,
                get_page_cursor=lambda: 12,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

        self.assertEqual(2, delta.page_count)
        self.assertEqual(2, add_page.call_args.kwargs["page_count"])
        self.assertEqual(
            "12_app_setup_placeholder",
            add_page.call_args.kwargs["source_stem"],
        )
        self.assertIs(page_plan, add_page.call_args.kwargs["page_plan"])

    def test_storage_troubleshooting_route_mirrors_rows_only_for_the_output_language(
        self,
    ) -> None:
        """Only the output language may seed the book's troubleshooting rows.

        In a multi-language bundle a foreign-language composition renders its
        own page but must not overwrite ``trouble_rows``, which feeds the output
        language's downstream table.  Without the ``lang == output_lang`` guard
        the last language rendered wins — the same class of bug the LCD route
        guards against.  ``trouble_sid`` comes from the troubleshooting page's
        own stem, not the composition id, so the story name stays stable.
        """
        bundle_root = Path("/tmp/bundle")

        def build(
            language: str,
            output_lang: str,
            trouble_rows: list[tuple[str, str]],
            emitted: set[str],
        ) -> tuple[TargetAssemblyRenderer, str]:
            storage_ref = f"page/09_storage_and_maintenance_{language}.rst"
            trouble_ref = f"page/troubleshooting_{language}.rst"
            page_plan = {
                "plan_source": "target-assembly",
                "physical_page_count": 1,
                "pages": [
                    {
                        "source_ref": storage_ref,
                        "source_path": storage_ref,
                        "language": language,
                        "page_role": "storage_maintenance",
                        "composition_id": f"{language}_storage_troubleshooting",
                        "composition_type": "storage_troubleshooting",
                        "latex_start_page": 1,
                        "planned_page_count": 1,
                    },
                    {
                        "source_ref": trouble_ref,
                        "source_path": trouble_ref,
                        "language": language,
                        "page_role": "troubleshooting_data",
                        "composition_id": f"{language}_storage_troubleshooting",
                        "composition_type": "storage_troubleshooting",
                        "latex_start_page": 1,
                        "planned_page_count": 1,
                    },
                ],
            }
            projected_by_path = {
                bundle_root / storage_ref: ProjectedPage(
                    path=bundle_root / storage_ref,
                    language=language,
                    blocks=(("h1", "STORAGE"),),
                    skipped_raw=0,
                    twocol=False,
                ),
                bundle_root / trouble_ref: ProjectedPage(
                    path=bundle_root / trouble_ref,
                    language=language,
                    blocks=(("h1", "TROUBLESHOOTING"),),
                    skipped_raw=0,
                    twocol=False,
                ),
            }
            renderer = TargetAssemblyRenderer(
                page_plan=page_plan,
                projected_by_path=projected_by_path,
                bundle_root=bundle_root,
                writer=Mock(),
                toc=Mock(),
                manual_ir=Mock(),
                root=Path("/tmp/repo"),
                data_root=Path("/tmp/data"),
                output_lang=output_lang,
                emitted=emitted,
                spec_sections=[],
                lcd_rows=[],
                trouble_rows=trouble_rows,
                symbol_data_for=Mock(),
                slug_stem=lambda value: value,
            )
            return renderer, storage_ref

        trouble_data = Mock(title="문제 해결", rows=(("F0", "재시작"),))
        rows: list[tuple[str, str]] = []
        emitted: set[str] = set()
        renderer, storage_ref = build("ko", "ko", rows, emitted)

        with patch(
            "tools.idml.target_assembly_render.ir_projection.trouble_page_data",
            return_value=trouble_data,
        ), patch(
            "tools.idml.target_assembly_render.shared_page."
            "add_storage_troubleshooting_page"
        ) as add_page:
            delta = renderer.render(
                bundle_root / storage_ref,
                get_page_cursor=lambda: 14,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

        self.assertEqual(1, delta.page_count)
        self.assertEqual(
            "st_troubleshooting_ko",
            add_page.call_args.kwargs["trouble_sid"],
        )
        self.assertEqual([("F0", "재시작")], rows)
        self.assertIn("trouble:ko", emitted)

        foreign_rows: list[tuple[str, str]] = []
        foreign_emitted: set[str] = set()
        foreign, foreign_storage_ref = build(
            "en", "ko", foreign_rows, foreign_emitted
        )

        with patch(
            "tools.idml.target_assembly_render.ir_projection.trouble_page_data",
            return_value=trouble_data,
        ), patch(
            "tools.idml.target_assembly_render.shared_page."
            "add_storage_troubleshooting_page"
        ):
            foreign.render(
                bundle_root / foreign_storage_ref,
                get_page_cursor=lambda: 14,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

        self.assertEqual([], foreign_rows)
        self.assertIn("trouble:en", foreign_emitted)

        starved, starved_storage_ref = build("ko", "ko", [], set())

        with patch(
            "tools.idml.target_assembly_render.ir_projection.trouble_page_data",
            return_value=None,
        ), patch(
            "tools.idml.target_assembly_render.shared_page."
            "add_storage_troubleshooting_page"
        ), self.assertRaisesRegex(ValueError, "missing Troubleshooting data"):
            starved.render(
                bundle_root / starved_storage_ref,
                get_page_cursor=lambda: 14,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

    def test_specifications_route_mirrors_only_the_output_language_sections(
        self,
    ) -> None:
        """The spec route forwards target layout data and guards the language.

        ``composition_data`` carries the target's ``layout_variant`` and
        ``annotation_order``; if it stops being forwarded the spec page silently
        falls back to the reference layout.  As with troubleshooting rows, only
        the output language may mirror the rendered sections into the book —
        otherwise a foreign-language spec composition overwrites them.
        """
        bundle_root = Path("/tmp/bundle")

        def build(
            language: str,
            output_lang: str,
            spec_sections: list[dict],
            emitted: set[str],
        ) -> tuple[TargetAssemblyRenderer, str]:
            spec_ref = f"page/spec_{language}.rst"
            page_plan = {
                "plan_source": "target-assembly",
                "physical_page_count": 1,
                "pages": [{
                    "source_ref": spec_ref,
                    "source_path": spec_ref,
                    "language": language,
                    "page_role": "spec",
                    "composition_id": f"{language}_specifications",
                    "composition_type": "specifications",
                    "latex_start_page": 1,
                    "planned_page_count": 1,
                    "composition_data": {
                        "specifications": {
                            "layout_variant": "compact",
                            "annotation_order": [1, 2, 0],
                        }
                    },
                }],
            }
            projected_by_path = {
                bundle_root / spec_ref: ProjectedPage(
                    path=bundle_root / spec_ref,
                    language=language,
                    blocks=(("h1", "SPECIFICATIONS"),),
                    skipped_raw=0,
                    twocol=False,
                )
            }
            renderer = TargetAssemblyRenderer(
                page_plan=page_plan,
                projected_by_path=projected_by_path,
                bundle_root=bundle_root,
                writer=Mock(),
                toc=Mock(),
                manual_ir=Mock(),
                root=Path("/tmp/repo"),
                data_root=Path("/tmp/data"),
                output_lang=output_lang,
                emitted=emitted,
                spec_sections=spec_sections,
                lcd_rows=[],
                trouble_rows=[],
                symbol_data_for=Mock(),
                slug_stem=lambda value: value,
            )
            return renderer, spec_ref

        spec_data = Mock(title="제품 사양")
        rendered_sections = [{"title": "충전"}]
        sections: list[dict] = []
        emitted: set[str] = set()
        renderer, spec_ref = build("ko", "ko", sections, emitted)

        # The route destructures the adder's ``(sid, sections)`` return value,
        # so the patch has to hand back a real 2-tuple.
        with patch(
            "tools.idml.target_assembly_render.ir_projection.spec_page_data",
            return_value=spec_data,
        ), patch(
            "tools.idml.target_assembly_render.shared_page.add_specifications_page",
            return_value=("st_spec", rendered_sections),
        ) as add_page:
            delta = renderer.render(
                bundle_root / spec_ref,
                get_page_cursor=lambda: 15,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

        self.assertEqual(1, delta.page_count)
        self.assertEqual(
            {
                "specifications": {
                    "layout_variant": "compact",
                    "annotation_order": [1, 2, 0],
                }
            },
            add_page.call_args.kwargs["composition_data"],
        )
        self.assertEqual(rendered_sections, sections)
        self.assertIn("spec:ko", emitted)

        foreign_sections: list[dict] = []
        foreign_emitted: set[str] = set()
        foreign, foreign_spec_ref = build(
            "en", "ko", foreign_sections, foreign_emitted
        )

        with patch(
            "tools.idml.target_assembly_render.ir_projection.spec_page_data",
            return_value=spec_data,
        ), patch(
            "tools.idml.target_assembly_render.shared_page.add_specifications_page",
            return_value=("st_spec", rendered_sections),
        ):
            foreign.render(
                bundle_root / foreign_spec_ref,
                get_page_cursor=lambda: 15,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

        self.assertEqual([], foreign_sections)
        self.assertIn("spec:en", foreign_emitted)

    def test_connections_passes_target_component_data_to_shared_compositor(
        self,
    ) -> None:
        bundle_root = Path("/tmp/bundle")
        connections_ref = "page/connections_en.rst"
        trouble_ref = "page/troubleshooting_en.rst"
        composition_data = {
            "connections": {
                "layout_variant": "notice_before_primary_figure",
                "image_role": "reference_measure",
            }
        }
        page_plan = {
            "plan_source": "target-assembly",
            "physical_page_count": 2,
            "pages": [
                {
                    "source_ref": connections_ref,
                    "source_path": connections_ref,
                    "language": "en",
                    "page_role": "connections",
                    "composition_id": "en_connections",
                    "composition_type": "connections",
                    "latex_start_page": 1,
                    "planned_page_count": 1,
                    "composition_data": composition_data,
                    "flow_split": {
                        "at_kind": "image",
                        "occurrence": 2,
                        "tail_composition_id": "en_troubleshooting",
                    },
                },
                {
                    "source_ref": trouble_ref,
                    "source_path": trouble_ref,
                    "language": "en",
                    "page_role": "troubleshooting_data",
                    "composition_id": "en_troubleshooting",
                    "composition_type": "troubleshooting",
                    "latex_start_page": 2,
                    "planned_page_count": 1,
                },
            ],
        }
        projected_by_path = {
            bundle_root / connections_ref: ProjectedPage(
                path=bundle_root / connections_ref,
                language="en",
                blocks=(
                    ("h1", "CONNECTIONS"),
                    ("body", "Introduction."),
                    ("image", "primary.png"),
                    ("component", json.dumps({"kind": "notice"})),
                    ("component", json.dumps({"kind": "notice"})),
                    ("image", "tail.png"),
                ),
                skipped_raw=0,
                twocol=False,
            ),
            bundle_root / trouble_ref: ProjectedPage(
                path=bundle_root / trouble_ref,
                language="en",
                blocks=(("h1", "TROUBLESHOOTING"),),
                skipped_raw=0,
                twocol=False,
            ),
        }
        renderer = TargetAssemblyRenderer(
            page_plan=page_plan,
            projected_by_path=projected_by_path,
            bundle_root=bundle_root,
            writer=Mock(),
            toc=Mock(),
            manual_ir=Mock(),
            root=Path("/tmp/repo"),
            data_root=Path("/tmp/data"),
            output_lang="en",
            emitted=set(),
            spec_sections=[],
            lcd_rows=[],
            trouble_rows=[],
            symbol_data_for=Mock(),
            slug_stem=lambda value: value,
        )

        with patch(
            "tools.idml.target_assembly_render.shared_page.add_connections_page"
        ) as add_page:
            delta = renderer.render(
                bundle_root / connections_ref,
                get_page_cursor=lambda: 6,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

        self.assertEqual(1, delta.page_count)
        self.assertEqual(
            composition_data,
            add_page.call_args.kwargs["composition_data"],
        )

    def test_charging_passes_target_component_data_to_shared_compositor(self) -> None:
        bundle_root = Path("/tmp/bundle")
        charging_ref = "page/charging_en.rst"
        composition_data = {
            "charging": {
                "image_role": "reference_measure",
                "h2_suffix_pill_indices": [1],
            }
        }
        page_plan = {
            "plan_source": "target-assembly",
            "physical_page_count": 1,
            "pages": [{
                "source_ref": charging_ref,
                "source_path": charging_ref,
                "language": "en",
                "page_role": "charging",
                "composition_id": "en_charging",
                "composition_type": "charging",
                "latex_start_page": 1,
                "planned_page_count": 1,
                "composition_data": composition_data,
            }],
        }
        projected_by_path = {
            bundle_root / charging_ref: ProjectedPage(
                path=bundle_root / charging_ref,
                language="en",
                blocks=(
                    ("h1", "CHARGING"),
                    ("h2", "AC WALL"),
                    ("image", "ac.png"),
                    ("h2", "SOLAR (SOLD SEPARATELY)"),
                    ("image", "solar.png"),
                ),
                skipped_raw=0,
                twocol=False,
            )
        }
        renderer = TargetAssemblyRenderer(
            page_plan=page_plan,
            projected_by_path=projected_by_path,
            bundle_root=bundle_root,
            writer=Mock(),
            toc=Mock(),
            manual_ir=Mock(),
            root=Path("/tmp/repo"),
            data_root=Path("/tmp/data"),
            output_lang="en",
            emitted=set(),
            spec_sections=[],
            lcd_rows=[],
            trouble_rows=[],
            symbol_data_for=Mock(),
            slug_stem=lambda value: value,
        )

        with patch(
            "tools.idml.target_assembly_render.shared_page.add_charging_page"
        ) as add_page:
            delta = renderer.render(
                bundle_root / charging_ref,
                get_page_cursor=lambda: 8,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

        self.assertEqual(1, delta.page_count)
        self.assertEqual(composition_data, add_page.call_args.kwargs[
            "composition_data"
        ])

    def test_composition_uses_page_cursor_after_pending_flow_flush(self) -> None:
        bundle_root = Path("/tmp/bundle")
        charging_ref = "page/charging_en.rst"
        storage_ref = "page/storage_en.rst"
        page_plan = {
            "plan_source": "target-assembly",
            "physical_page_count": 1,
            "pages": [
                {
                    "source_ref": charging_ref,
                    "source_path": charging_ref,
                    "language": "en",
                    "page_role": "charging",
                    "composition_id": "en_charging_storage",
                    "composition_type": "charging_storage",
                    "latex_start_page": 1,
                    "planned_page_count": 1,
                },
                {
                    "source_ref": storage_ref,
                    "source_path": storage_ref,
                    "language": "en",
                    "page_role": "storage_maintenance",
                    "composition_id": "en_charging_storage",
                    "composition_type": "charging_storage",
                    "latex_start_page": 1,
                    "planned_page_count": 1,
                },
            ],
        }
        projected_by_path = {
            bundle_root / charging_ref: ProjectedPage(
                path=bundle_root / charging_ref,
                language="en",
                blocks=(("h1", "Charging"),),
                skipped_raw=0,
                twocol=False,
            ),
            bundle_root / storage_ref: ProjectedPage(
                path=bundle_root / storage_ref,
                language="en",
                blocks=(("h1", "Storage"),),
                skipped_raw=0,
                twocol=False,
            ),
        }
        renderer = TargetAssemblyRenderer(
            page_plan=page_plan,
            projected_by_path=projected_by_path,
            bundle_root=bundle_root,
            writer=Mock(),
            toc=Mock(),
            manual_ir=Mock(),
            root=Path("/tmp/repo"),
            data_root=Path("/tmp/data"),
            output_lang="en",
            emitted=set(),
            spec_sections=[],
            lcd_rows=[],
            trouble_rows=[],
            symbol_data_for=Mock(),
            slug_stem=lambda value: value,
        )
        cursor = {"value": 3}

        def flush_prose_flow() -> None:
            cursor["value"] += 1

        with patch(
            "tools.idml.target_assembly_render.shared_page.add_charging_storage_page"
        ) as add_page:
            delta = renderer.render(
                bundle_root / charging_ref,
                get_page_cursor=lambda: cursor["value"],
                flush_prose_flow=flush_prose_flow,
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

        self.assertIsNotNone(delta)
        self.assertEqual(1, delta.page_count)
        self.assertEqual(0, delta.skipped_raw)
        self.assertEqual(4, add_page.call_args.kwargs["page_index"])

    def test_troubleshooting_reuses_complete_projected_blocks(self) -> None:
        bundle_root = Path("/tmp/bundle")
        trouble_ref = "page/troubleshooting_en.rst"
        blocks = (
            ("h1", "TROUBLESHOOTING"),
            ("body", "Follow the listed corrective actions."),
            (
                "table",
                json.dumps([
                    ["Error Code", "Corrective Measures"],
                    ["F0", "Restart the product."],
                ]),
            ),
        )
        page_plan = {
            "plan_source": "target-assembly",
            "physical_page_count": 1,
            "pages": [{
                "source_ref": trouble_ref,
                "source_path": trouble_ref,
                "language": "en",
                "page_role": "troubleshooting_data",
                "composition_id": "en_troubleshooting",
                "composition_type": "troubleshooting",
                "latex_start_page": 1,
                "planned_page_count": 1,
                "composition_data": {
                    "troubleshooting": {
                        "connection_image_role": "reference_measure",
                        "heading_space_after": 5.4,
                        "split": 303.6,
                    }
                },
            }],
        }
        projected_by_path = {
            bundle_root / trouble_ref: ProjectedPage(
                path=bundle_root / trouble_ref,
                language="en",
                blocks=blocks,
                skipped_raw=0,
                twocol=False,
            )
        }
        renderer = TargetAssemblyRenderer(
            page_plan=page_plan,
            projected_by_path=projected_by_path,
            bundle_root=bundle_root,
            writer=Mock(),
            toc=Mock(),
            manual_ir=Mock(),
            root=Path("/tmp/repo"),
            data_root=Path("/tmp/data"),
            output_lang="en",
            emitted=set(),
            spec_sections=[],
            lcd_rows=[],
            trouble_rows=[],
            symbol_data_for=Mock(),
            slug_stem=lambda value: value,
        )
        renderer.routed_tail_blocks["en_troubleshooting"] = [
            ("image", "connection-tail.png")
        ]
        trouble_data = Mock(title="TROUBLESHOOTING", rows=(("F0", "Restart"),))

        with patch(
            "tools.idml.target_assembly_render.ir_projection.trouble_page_data",
            return_value=trouble_data,
        ), patch(
            "tools.idml.target_assembly_render.shared_page."
            "add_connection_tail_troubleshooting_page"
        ) as add_page:
            delta = renderer.render(
                bundle_root / trouble_ref,
                get_page_cursor=lambda: 0,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

        self.assertEqual(1, delta.page_count)
        self.assertEqual(list(blocks), add_page.call_args.kwargs["trouble_blocks"])
        self.assertEqual(
            "st_troubleshooting_en",
            add_page.call_args.kwargs["trouble_sid"],
        )
        self.assertEqual(
            {
                "troubleshooting": {
                    "connection_image_role": "reference_measure",
                    "heading_space_after": 5.4,
                    "split": 303.6,
                }
            },
            add_page.call_args.kwargs["composition_data"],
        )


class TargetAssemblyRendererStateTests(unittest.TestCase):
    """Pins for the two renderer flags ``export_idml`` reads back."""

    @staticmethod
    def _renderer(
        page_plan: dict | None,
        projected_by_path: dict[Path, ProjectedPage] | None = None,
    ) -> TargetAssemblyRenderer:
        return TargetAssemblyRenderer(
            page_plan=page_plan,
            projected_by_path=projected_by_path or {},
            bundle_root=Path("/tmp/bundle"),
            writer=Mock(),
            toc=Mock(),
            manual_ir=Mock(pages=()),
            root=Path("/tmp/repo"),
            data_root=Path("/tmp/data"),
            output_lang="ko",
            emitted=set(),
            spec_sections=[],
            lcd_rows=[],
            trouble_rows=[],
            symbol_data_for=Mock(),
            slug_stem=lambda value: value,
        )

    @staticmethod
    def _single_page_plan(page_role: str, composition_type: str) -> dict:
        source_ref = f"page/{page_role}_ko.rst"
        return {
            "plan_source": "target-assembly",
            "physical_page_count": 1,
            "pages": [{
                "source_ref": source_ref,
                "source_path": source_ref,
                "language": "ko",
                "page_role": page_role,
                "composition_id": f"ko_{composition_type}",
                "composition_type": composition_type,
                "latex_start_page": 1,
                "planned_page_count": 1,
            }],
        }

    def test_toc_is_planned_only_when_the_target_declares_a_toc_composition(
        self,
    ) -> None:
        """``toc_planned`` gates whether ``export_idml`` finalizes a TOC story.

        A target assembly that plans no TOC composition has no page to hold one,
        so the flag must be False; if it regressed to unconditionally True the
        book would emit a TOC story with nowhere to place it.  Plans that are
        not target assemblies (and the no-plan case) keep the legacy behaviour
        of always finalizing.
        """
        self.assertFalse(
            self._renderer(self._single_page_plan("symbols", "symbols")).toc_planned
        )
        self.assertTrue(
            self._renderer(self._single_page_plan("toc", "toc")).toc_planned
        )
        self.assertTrue(self._renderer({"plan_source": "measured-latex"}).toc_planned)
        self.assertTrue(self._renderer(None).toc_planned)

    def test_back_cover_route_fails_closed_when_placement_is_refused(self) -> None:
        """A refused back-cover placement must stop the build, not be recorded.

        ``export_idml`` reads ``back_cover_added`` to decide whether to run its
        fallback placement and whether folio numbering has a back cover.  If the
        raise were removed, a back cover that was never rendered would still be
        reported as present and the folio sequence would be off by a page.
        """
        bundle_root = Path("/tmp/bundle")
        back_cover_ref = "page/back_cover_ko.rst"
        page_plan = self._single_page_plan("back_cover", "back_cover")
        page_plan["pages"][0]["source_ref"] = back_cover_ref
        page_plan["pages"][0]["source_path"] = back_cover_ref
        projected_by_path = {
            bundle_root / back_cover_ref: ProjectedPage(
                path=bundle_root / back_cover_ref,
                language="ko",
                blocks=(),
                skipped_raw=0,
                twocol=False,
            )
        }

        def render(renderer: TargetAssemblyRenderer):
            return renderer.render(
                bundle_root / back_cover_ref,
                get_page_cursor=lambda: 18,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

        placed = self._renderer(page_plan, projected_by_path)
        self.assertFalse(placed.back_cover_added)

        with patch(
            "tools.idml.target_assembly_render.page_placed."
            "add_preferred_back_cover_page",
            return_value=True,
        ):
            delta = render(placed)

        self.assertEqual(1, delta.page_count)
        self.assertTrue(placed.back_cover_added)

        refused = self._renderer(page_plan, projected_by_path)

        with patch(
            "tools.idml.target_assembly_render.page_placed."
            "add_preferred_back_cover_page",
            return_value=False,
        ), self.assertRaisesRegex(ValueError, "back cover was not rendered"):
            render(refused)

        self.assertFalse(refused.back_cover_added)


if __name__ == "__main__":
    unittest.main()
