from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from tools.idml.ir_projection import ProjectedPage
from tools.idml.target_assembly_render import TargetAssemblyRenderer


class TargetAssemblyRenderTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
