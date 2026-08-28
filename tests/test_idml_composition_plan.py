from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.idml.composition_plan import (
    CompositionPlanError,
    REGISTRY,
    build_composition_plan,
)
from tools.idml.page_roles import classify_page_role


ROOT = Path(__file__).resolve().parents[1]
JE_PLAN = (
    ROOT
    / "docs"
    / "renderers"
    / "contracts"
    / "reference_layout"
    / "je1000f_us_v2_20260605.json"
)


def _normalized_je_plan() -> dict:
    payload = json.loads(JE_PLAN.read_text(encoding="utf-8"))
    return {
        "plan_source": "approved-reference",
        "physical_page_count": payload["reference_pdf"]["page_count"],
        "pages": [
            {
                "source_ref": entry["source_ref"],
                "language": entry["language"],
                "page_role": classify_page_role(
                    Path(entry["source_ref"])
                ).value,
                "composition_id": entry["composition_id"],
                "latex_start_page": entry["start_page"],
                "planned_page_count": entry["page_count"],
            }
            for entry in payload["pages"]
        ],
    }


class CompositionPlanTests(unittest.TestCase):
    def test_je_approved_contract_projects_to_shared_types(self) -> None:
        plan = build_composition_plan(_normalized_je_plan())

        self.assertEqual(plan.physical_page_count, 58)
        self.assertEqual(len(plan.compositions), 40)
        by_id = {item.composition_id: item for item in plan.compositions}
        self.assertEqual(
            by_id["en_maintenance_symbols"].composition_type,
            "maintenance_symbols",
        )
        self.assertEqual(
            by_id["en_fcc_inbox"].composition_type,
            "fcc_inbox",
        )
        self.assertEqual(
            by_id["en_storage_troubleshooting"].composition_type,
            "storage_troubleshooting",
        )

    def test_explicit_type_must_match_semantic_roles(self) -> None:
        plan = _normalized_je_plan()
        plan["pages"][0]["composition_type"] = "warranty"

        with self.assertRaisesRegex(
            CompositionPlanError,
            "requires roles.*got",
        ):
            build_composition_plan(plan)

    def test_registry_contains_no_target_names(self) -> None:
        registry_text = " ".join(REGISTRY).casefold()
        self.assertNotIn("je-1000f", registry_text)
        self.assertNotIn("jbp-2000b", registry_text)


if __name__ == "__main__":
    unittest.main()
