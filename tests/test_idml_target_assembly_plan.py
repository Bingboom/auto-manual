from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.idml.composition_plan import build_composition_plan
from tools.idml.target_assembly_plan import (
    TargetAssemblyPlanError,
    normalize_target_assembly_plan,
)
from tools.manual_ir import ManualBlock, ManualIR, ManualPage


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = (
    ROOT
    / "docs"
    / "renderers"
    / "contracts"
    / "target_assembly"
    / "jbp2000b_us_v1_candidate.json"
)


def _payload() -> dict:
    return json.loads(PLAN_PATH.read_text(encoding="utf-8"))


def _manual_ir(payload: dict) -> ManualIR:
    pages = []
    for index, entry in enumerate(payload["pages"], start=1):
        blocks = tuple(
            ManualBlock(
                block_id=f"block-{index}-{image_index}",
                source_ref=entry["source_ref"],
                kind="image",
                payload=f"asset-{image_index}.png",
                content_sha256=f"{image_index:064x}",
            )
            for image_index in range(1, 3)
        ) if entry["page_role"] == "connections" else ()
        pages.append(
            ManualPage(
                page_id=f"page-{index}",
                source_ref=entry["source_ref"],
                source_path=entry["source_ref"],
                language=entry["language"],
                source_sha256=f"{index:064x}",
                skipped_raw=0,
                blocks=blocks,
            )
        )
    return ManualIR(
        model="JBP-2000B",
        region="US",
        language="en",
        source="test",
        bundle_root=".",
        bundle_sha256="0" * 64,
        snapshot_sha256="1" * 64,
        layout_params_sha256="2" * 64,
        style_contract_sha256="3" * 64,
        content_sha256="4" * 64,
        pages=tuple(pages),
    )


class TargetAssemblyPlanTests(unittest.TestCase):
    def test_jbp_candidate_normalizes_to_28_shared_compositions(self) -> None:
        payload = _payload()
        plan = normalize_target_assembly_plan(
            payload,
            _manual_ir(payload),
            source_path=PLAN_PATH,
        )

        self.assertEqual(plan["plan_source"], "target-assembly")
        self.assertEqual(plan["physical_page_count"], 28)
        self.assertEqual(plan["source_page_count"], 43)
        self.assertEqual(plan["composition_count"], 28)
        compositions = build_composition_plan(plan)
        by_id = {item.composition_id: item for item in compositions.compositions}
        self.assertEqual(
            by_id["en_fcc_inbox_overview"].composition_type,
            "fcc_inbox_overview",
        )
        self.assertEqual(
            by_id["en_charging_storage"].source_refs,
            (
                "page/charging_en.rst",
                "page/storage_en.rst",
            ),
        )
        self.assertEqual(
            by_id["en_specifications"].source_refs,
            ("page/specifications_en.rst",),
        )

    def test_candidate_remains_non_approved(self) -> None:
        payload = _payload()
        self.assertEqual(payload["status"], "candidate")
        self.assertFalse(payload["production_eligible"])
        self.assertNotIn("approval", payload)

    def test_flow_split_requires_the_second_connection_image(self) -> None:
        payload = _payload()
        ir = _manual_ir(payload)
        pages = list(ir.pages)
        connection_index = next(
            index
            for index, page in enumerate(pages)
            if page.source_ref == "page/connections_en.rst"
        )
        page = pages[connection_index]
        pages[connection_index] = ManualPage(
            page_id=page.page_id,
            source_ref=page.source_ref,
            source_path=page.source_path,
            language=page.language,
            source_sha256=page.source_sha256,
            skipped_raw=page.skipped_raw,
            blocks=page.blocks[:1],
        )
        ir = ManualIR(**{**ir.to_dict(), "pages": tuple(pages)})

        with self.assertRaisesRegex(
            TargetAssemblyPlanError,
            "cannot find image occurrence 2",
        ):
            normalize_target_assembly_plan(payload, ir, source_path=PLAN_PATH)


if __name__ == "__main__":
    unittest.main()
