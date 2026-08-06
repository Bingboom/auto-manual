from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from tests.test_reference_layout_plan import _approved_payload, _manual_ir
from tools.idml.reference_layout_plan import ReferenceLayoutPlanError
from tools.idml.reference_layout_plan import load_approved_reference_plan
from tools.idml.reference_layout_scaffold import (
    SCAFFOLD_SCHEMA_VERSION,
    build_reference_layout_scaffold,
)
from tools.manual_ir import write_manual_ir
from tools.reference_layout_scaffold import main as scaffold_main


class ReferenceLayoutScaffoldTests(unittest.TestCase):
    def test_draft_refreshes_identity_but_preserves_composition_and_is_inert(self) -> None:
        ir = _manual_ir()
        seed = _approved_payload(ir)
        seed["source_identity"]["snapshot_sha256"] = "7" * 64  # type: ignore[index]
        seed["pages"][0]["source_sha256"] = "8" * 64  # type: ignore[index]
        original_map = [
            (
                page["source_ref"], page["composition_id"],
                page["start_page"], page["page_count"], page.get("flow_split"),
            )
            for page in seed["pages"]  # type: ignore[index]
        ]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_path = root / "seed.json"
            seed_path.write_text(json.dumps(seed), encoding="utf-8")
            draft = build_reference_layout_scaffold(seed_path, ir)

        self.assertEqual(SCAFFOLD_SCHEMA_VERSION, draft["scaffold"]["schema_version"])
        self.assertEqual("draft", draft["approval"]["status"])
        self.assertFalse(draft["scaffold"]["production_eligible"])
        self.assertEqual(
            ir.snapshot_sha256,
            draft["identity"]["provenance"]["snapshot_sha256"],
        )
        self.assertEqual(
            ir.content_sha256,
            draft["identity"]["content"]["manual_content_sha256"],
        )
        self.assertEqual(
            original_map,
            [
                (
                    page["source_ref"], page["composition_id"],
                    page["start_page"], page["page_count"], page.get("flow_split"),
                )
                for page in draft["pages"]  # type: ignore[index]
            ],
        )

    def test_changed_source_order_is_fail_closed(self) -> None:
        ir = _manual_ir()
        seed = _approved_payload(ir)
        seed["pages"][1], seed["pages"][2] = seed["pages"][2], seed["pages"][1]  # type: ignore[index]
        with tempfile.TemporaryDirectory() as tmp:
            seed_path = Path(tmp) / "seed.json"
            seed_path.write_text(json.dumps(seed), encoding="utf-8")
            with self.assertRaisesRegex(ReferenceLayoutPlanError, "source_ref order"):
                build_reference_layout_scaffold(seed_path, ir)

    def test_draft_freezes_current_skipped_raw_as_review_baseline(self) -> None:
        ir = _manual_ir()
        changed_page = replace(ir.pages[0], skipped_raw=2)
        ir = replace(ir, pages=(changed_page, *ir.pages[1:]))
        seed = _approved_payload(ir)
        seed["idml_contract"]["max_skipped_raw"] = 0  # type: ignore[index]

        with tempfile.TemporaryDirectory() as tmp:
            seed_path = Path(tmp) / "seed.json"
            seed_path.write_text(json.dumps(seed), encoding="utf-8")
            draft = build_reference_layout_scaffold(seed_path, ir)

        self.assertEqual(2, draft["idml_contract"]["max_skipped_raw"])

    def test_missing_snapshot_is_fail_closed(self) -> None:
        ir = _manual_ir()
        ir = replace(ir, snapshot_sha256=None)
        seed = _approved_payload(ir)
        with tempfile.TemporaryDirectory() as tmp:
            seed_path = Path(tmp) / "seed.json"
            seed_path.write_text(json.dumps(seed), encoding="utf-8")
            with self.assertRaisesRegex(ReferenceLayoutPlanError, "frozen snapshot"):
                build_reference_layout_scaffold(seed_path, ir)

    def test_cli_writes_only_named_draft(self) -> None:
        ir = _manual_ir()
        seed = _approved_payload(ir)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_path = root / "seed.json"
            ir_path = root / "manual.ir.json"
            output = root / "draft.json"
            seed_path.write_text(json.dumps(seed), encoding="utf-8")
            write_manual_ir(ir, ir_path)
            self.assertEqual(
                0,
                scaffold_main([
                    "--seed-plan", str(seed_path),
                    "--manual-ir", str(ir_path),
                    "--output", str(output),
                ]),
            )
            draft = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("draft", draft["approval"]["status"])
            self.assertEqual("required-after-approval", draft["scaffold"]["registry_update"])

    def test_even_explicit_registry_entry_cannot_activate_draft(self) -> None:
        ir = _manual_ir()
        seed = _approved_payload(ir)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_path = root / "seed.json"
            seed_path.write_text(json.dumps(seed), encoding="utf-8")
            draft = build_reference_layout_scaffold(seed_path, ir)
            contract_dir = root / "docs/renderers/contracts/reference_layout"
            contract_dir.mkdir(parents=True)
            (contract_dir / "draft.json").write_text(
                json.dumps(draft), encoding="utf-8",
            )
            registry = contract_dir.parent / "reference_layout_registry.json"
            registry.write_text(json.dumps({
                "schema_version": "approved-reference-layout-registry/v1",
                "plans": [{
                    "target": seed["target"],
                    "path": "docs/renderers/contracts/reference_layout/draft.json",
                }],
            }), encoding="utf-8")

            with self.assertRaisesRegex(ReferenceLayoutPlanError, "approval.status"):
                load_approved_reference_plan(root=root, ir=ir)


if __name__ == "__main__":
    unittest.main()
