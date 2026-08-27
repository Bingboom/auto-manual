from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from tools.idml.ir_projection import ProjectedPage
from tools.idml.target_assembly_render import TargetAssemblyRenderer


class TargetAssemblyRenderTests(unittest.TestCase):
    def test_app_routes_through_shared_app_composition(self) -> None:
        bundle_root = Path("/tmp/bundle")
        source_ref = "page/app_setup_ko.rst"
        page_plan = {
            "plan_source": "target-assembly",
            "physical_page_count": 2,
            "pages": [{
                "source_ref": source_ref,
                "source_path": source_ref,
                "language": "ko",
                "page_role": "app_setup",
                "composition_id": "ko_app",
                "composition_type": "app",
                "latex_start_page": 1,
                "planned_page_count": 2,
                "composition_data": {
                    "app": {
                        "instance_id": "je3000c-kr-v1",
                        "control_image": "controls/panel.pdf",
                        "control_layout_variant": "embedded_leaders",
                        "labels_by_role": {
                            "main_power": "POWER 버튼",
                            "dc_usb": "DC/USB 전원 버튼",
                            "ac": "AC 전원 버튼",
                        },
                    }
                },
            }],
        }
        blocks = (("h1", "APP 설정"), ("image", "download.png"))
        projected_by_path = {
            bundle_root / source_ref: ProjectedPage(
                path=bundle_root / source_ref,
                language="ko",
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
                bundle_root / source_ref,
                get_page_cursor=lambda: 15,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

        self.assertEqual(2, delta.page_count)
        self.assertEqual(list(blocks), add_page.call_args.kwargs["blocks"])
        self.assertEqual(page_plan, add_page.call_args.kwargs["page_plan"])
        self.assertEqual("app_setup_ko", add_page.call_args.kwargs["source_stem"])

    def test_inbox_overview_merges_target_component_data(self) -> None:
        bundle_root = Path("/tmp/bundle")
        inbox_ref = "page/inbox_ko.rst"
        overview_ref = "page/overview_ko.rst"
        inbox_data = {
            "inbox": {
                "image_width_pt_by_language": {
                    "ko": [66.0, 30.0, 40.0],
                }
            }
        }
        overview_data = {
            "overview": {"instance_id": "je3000c-kr-v1"}
        }
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
                blocks=(("h1", "박스 구성품"),),
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
            delta = renderer.render(
                bundle_root / inbox_ref,
                get_page_cursor=lambda: 3,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

        self.assertEqual(1, delta.page_count)
        self.assertEqual(
            {**inbox_data, **overview_data},
            add_page.call_args.kwargs["composition_data"],
        )

    def test_specifications_routes_layout_variant_to_complete_component(self) -> None:
        bundle_root = Path("/tmp/bundle")
        source_ref = "page/spec_ko.rst"
        composition_data = {
            "specifications": {"layout_variant": "compact"}
        }
        page_plan = {
            "plan_source": "target-assembly",
            "physical_page_count": 1,
            "pages": [{
                "source_ref": source_ref,
                "source_path": source_ref,
                "language": "ko",
                "page_role": "spec",
                "composition_id": "ko_spec",
                "composition_type": "specifications",
                "latex_start_page": 1,
                "planned_page_count": 1,
                "composition_data": composition_data,
            }],
        }
        projected_by_path = {
            bundle_root / source_ref: ProjectedPage(
                path=bundle_root / source_ref,
                language="ko",
                blocks=(("h1", "사양"),),
                skipped_raw=0,
                twocol=False,
            )
        }
        sections: list[dict] = []
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
            spec_sections=sections,
            lcd_rows=[],
            trouble_rows=[],
            symbol_data_for=Mock(),
            slug_stem=lambda value: value,
        )
        spec_data = Mock(
            title="사양",
            sections=({"title": "일반 정보", "rows": []},),
            annotations=(),
        )

        with patch(
            "tools.idml.target_assembly_render.ir_projection.spec_page_data",
            return_value=spec_data,
        ), patch(
            "tools.idml.target_assembly_render.shared_page.add_specifications_page",
            return_value=("st_spec", list(spec_data.sections)),
        ) as add_page:
            delta = renderer.render(
                bundle_root / source_ref,
                get_page_cursor=lambda: 13,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

        self.assertEqual(1, delta.page_count)
        self.assertEqual(
            composition_data,
            add_page.call_args.kwargs["composition_data"],
        )
        self.assertEqual(list(spec_data.sections), sections)

    def test_symbols_routes_through_complete_symbols_panel(self) -> None:
        bundle_root = Path("/tmp/bundle")
        source_ref = "page/symbols_ko.rst"
        page_plan = {
            "plan_source": "target-assembly",
            "physical_page_count": 1,
            "pages": [{
                "source_ref": source_ref,
                "source_path": source_ref,
                "language": "ko",
                "page_role": "symbols",
                "composition_id": "ko_symbols",
                "composition_type": "symbols",
                "latex_start_page": 1,
                "planned_page_count": 1,
            }],
        }
        projected_by_path = {
            bundle_root / source_ref: ProjectedPage(
                path=bundle_root / source_ref,
                language="ko",
                blocks=(("h1", "기호 설명"),),
                skipped_raw=0,
                twocol=False,
            )
        }
        symbol_data = Mock(title="기호 설명")
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
            symbol_data_for=Mock(return_value=symbol_data),
            slug_stem=lambda value: value,
        )

        with patch(
            "tools.idml.target_assembly_render.shared_page.add_symbols_page"
        ) as add_page:
            delta = renderer.render(
                bundle_root / source_ref,
                get_page_cursor=lambda: 2,
                flush_prose_flow=Mock(),
                flush_pending_fcc=Mock(),
                flush_pending_prefix=Mock(),
            )

        self.assertEqual(1, delta.page_count)
        self.assertEqual(symbol_data, add_page.call_args.kwargs["symbol_data"])

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


if __name__ == "__main__":
    unittest.main()
