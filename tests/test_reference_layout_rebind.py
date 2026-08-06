from __future__ import annotations

from contextlib import redirect_stdout
from copy import deepcopy
from dataclasses import replace
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.test_reference_layout_plan import _approved_payload, _manual_ir
from tools.idml.reference_layout_plan import (
    ReferenceLayoutPlanError,
    V2_SCHEMA_VERSION,
    build_identity_scopes,
    validate_approved_reference_plan,
)
from tools.idml.reference_layout_rebind import rebind_reference_layout_plan
from tools.manual_ir import write_manual_ir
from tools.reference_layout_rebind import main as rebind_main


def _composition_map(payload: dict[str, object]) -> list[tuple[object, ...]]:
    return [
        (
            page.get("source_ref"),
            page.get("composition_id"),
            page.get("start_page"),
            page.get("page_count"),
            page.get("flow_split"),
        )
        for page in payload["pages"]  # type: ignore[index,union-attr]
    ]


def _approval() -> dict[str, str]:
    return {
        "status": "approved",
        "approved_by": "operator",
        "approved_at": "2026-08-05T12:00:00Z",
        "method": "reviewed identity repin; composition map unchanged",
    }


def _legacy_payload() -> dict[str, object]:
    ir = _manual_ir()
    payload = deepcopy(_approved_payload(ir))
    payload["idml_contract"]["allowed_unclassified_source_refs"] = [  # type: ignore[index]
        page.source_ref for page in ir.pages
    ]
    payload["source_identity"] = {
        "manual_ir_schema_version": "old-schema",
        "manual_content_sha256": ir.content_sha256,
        "snapshot_sha256": "7" * 64,
        "style_contract_sha256": "7" * 64,
        "layout_params_sha256": "7" * 64,
    }
    for page in payload["pages"]:  # type: ignore[index,union-attr]
        page["source_sha256"] = "8" * 64
    return payload


def _stale_payload() -> dict[str, object]:
    ir = _manual_ir()
    payload = _legacy_payload()
    payload["schema_version"] = V2_SCHEMA_VERSION
    payload["identity"] = build_identity_scopes(payload, ir)
    del payload["source_identity"]
    payload["identity"]["content"]["manual_ir_schema_version"] = "old-schema"  # type: ignore[index]
    payload["identity"]["style"]["style_contract_sha256"] = "7" * 64  # type: ignore[index]
    payload["identity"]["style"]["layout_params_sha256"] = "7" * 64  # type: ignore[index]
    payload["identity"]["provenance"]["snapshot_sha256"] = "7" * 64  # type: ignore[index]
    return payload


class ReferenceLayoutRebindTests(unittest.TestCase):
    def test_dry_run_validates_complete_refresh_without_writing(self) -> None:
        ir = _manual_ir()
        payload = _stale_payload()
        payload["idml_contract"]["editable_components"] = {  # type: ignore[index]
            "future_component": {"contract_version": 1},
        }
        expected_idml_contract = deepcopy(payload["idml_contract"])
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "approved.json"
            original = json.dumps(payload, indent=2) + "\n"
            plan_path.write_text(original, encoding="utf-8")

            result = rebind_reference_layout_plan(plan_path, ir)

            self.assertFalse(result.wrote)
            self.assertEqual(original, plan_path.read_text(encoding="utf-8"))
            self.assertEqual(4, len(result.changed_identity_fields))
            self.assertNotIn(
                "manual_content_sha256", result.changed_identity_fields,
            )
            self.assertEqual(len(ir.pages), result.changed_page_bindings)
            self.assertEqual([], validate_approved_reference_plan(result.candidate, ir))
            self.assertEqual(
                _composition_map(payload),
                _composition_map(result.candidate),
            )
            self.assertEqual(
                expected_idml_contract,
                result.candidate["idml_contract"],
            )

    def test_write_atomically_replaces_only_binding_fields(self) -> None:
        ir = _manual_ir()
        payload = _stale_payload()
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "approved.json"
            plan_path.write_text(json.dumps(payload), encoding="utf-8")
            original_mode = plan_path.stat().st_mode

            result = rebind_reference_layout_plan(plan_path, ir, write=True)

            written = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertTrue(result.wrote)
            self.assertEqual(original_mode, plan_path.stat().st_mode)
            self.assertEqual([], validate_approved_reference_plan(written, ir))
            self.assertEqual(_composition_map(payload), _composition_map(written))
            self.assertEqual(
                [page.source_ref for page in ir.pages],
                [page["source_ref"] for page in written["pages"]],
            )
            self.assertEqual(
                [page.source_sha256 for page in ir.pages],
                [page["source_sha256"] for page in written["pages"]],
            )
            self.assertEqual(
                [page.language for page in ir.pages],
                [page["language"] for page in written["pages"]],
            )

    def test_rejects_changed_source_ref_order_without_writing(self) -> None:
        ir = _manual_ir()
        payload = _stale_payload()
        pages = payload["pages"]  # type: ignore[assignment]
        pages[1], pages[2] = pages[2], pages[1]  # type: ignore[index]
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "approved.json"
            original = json.dumps(payload)
            plan_path.write_text(original, encoding="utf-8")

            with self.assertRaisesRegex(
                ReferenceLayoutPlanError,
                "requires unchanged source_ref order",
            ):
                rebind_reference_layout_plan(plan_path, ir, write=True)

            self.assertEqual(original, plan_path.read_text(encoding="utf-8"))

    def test_rejects_manual_content_change_without_writing(self) -> None:
        payload = _stale_payload()
        changed_ir = replace(_manual_ir(), content_sha256="9" * 64)
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "approved.json"
            original = json.dumps(payload)
            plan_path.write_text(original, encoding="utf-8")
            with self.assertRaisesRegex(
                ReferenceLayoutPlanError, "cannot change content or assembly identity",
            ):
                rebind_reference_layout_plan(plan_path, changed_ir, write=True)
            self.assertEqual(original, plan_path.read_text(encoding="utf-8"))

    def test_operator_approved_content_change_preserves_composition(self) -> None:
        payload = _stale_payload()
        changed_ir = replace(_manual_ir(), content_sha256="9" * 64)
        approval = _approval()
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "approved.json"
            plan_path.write_text(json.dumps(payload), encoding="utf-8")

            result = rebind_reference_layout_plan(
                plan_path,
                changed_ir,
                content_approval=approval,
            )

        self.assertTrue(result.content_reapproved)
        self.assertIn(
            "content.manual_content_sha256",
            result.changed_identity_fields,
        )
        self.assertEqual(approval, result.candidate["approval"])
        self.assertEqual(_composition_map(payload), _composition_map(result.candidate))
        self.assertEqual(
            [],
            validate_approved_reference_plan(result.candidate, changed_ir),
        )

    def test_v1_migration_requires_explicit_identity_approval(self) -> None:
        ir = _manual_ir()
        payload = _legacy_payload()
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "approved.json"
            original = json.dumps(payload)
            plan_path.write_text(original, encoding="utf-8")

            with self.assertRaisesRegex(
                ReferenceLayoutPlanError,
                "cannot change content or assembly identity",
            ):
                rebind_reference_layout_plan(plan_path, ir, write=True)

            self.assertEqual(original, plan_path.read_text(encoding="utf-8"))

    def test_v1_migration_records_explicit_identity_approval(self) -> None:
        ir = _manual_ir()
        payload = _legacy_payload()
        approval = _approval()
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "approved.json"
            plan_path.write_text(json.dumps(payload), encoding="utf-8")

            result = rebind_reference_layout_plan(
                plan_path,
                ir,
                content_approval=approval,
            )

        self.assertEqual(V2_SCHEMA_VERSION, result.candidate["schema_version"])
        self.assertIn("assembly.sha256", result.changed_identity_fields)
        self.assertEqual(approval, result.candidate["approval"])
        self.assertEqual(
            payload["idml_contract"]["allowed_unclassified_source_refs"],  # type: ignore[index]
            result.candidate["idml_contract"]["allowed_unclassified_source_refs"],  # type: ignore[index]
        )

    def test_v1_migration_does_not_auto_approve_unclassified_pages(self) -> None:
        ir = _manual_ir()
        payload = deepcopy(_approved_payload(ir))
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "approved.json"
            original = json.dumps(payload)
            plan_path.write_text(original, encoding="utf-8")

            with self.assertRaisesRegex(
                ReferenceLayoutPlanError,
                "unclassified prose is forbidden",
            ):
                rebind_reference_layout_plan(
                    plan_path,
                    ir,
                    write=True,
                    content_approval=_approval(),
                )

            self.assertEqual(original, plan_path.read_text(encoding="utf-8"))

    def test_rejects_legacy_layout_hash_algorithm_without_writing(self) -> None:
        payload = _stale_payload()
        legacy_ir = replace(_manual_ir(), metadata={})
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "approved.json"
            original = json.dumps(payload)
            plan_path.write_text(original, encoding="utf-8")

            with self.assertRaisesRegex(
                ReferenceLayoutPlanError,
                "requires Manual IR layout hash algorithm",
            ):
                rebind_reference_layout_plan(plan_path, legacy_ir, write=True)

            self.assertEqual(original, plan_path.read_text(encoding="utf-8"))

    def test_rejects_page_language_change_without_writing(self) -> None:
        ir = _manual_ir()
        pages = list(ir.pages)
        pages[2] = replace(pages[2], language="fr")
        changed_ir = replace(ir, pages=tuple(pages))
        payload = _stale_payload()
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "approved.json"
            original = json.dumps(payload)
            plan_path.write_text(original, encoding="utf-8")
            with self.assertRaisesRegex(
                ReferenceLayoutPlanError, "cannot change page language for page/c",
            ):
                rebind_reference_layout_plan(
                    plan_path,
                    changed_ir,
                    write=True,
                    content_approval=_approval(),
                )
            self.assertEqual(original, plan_path.read_text(encoding="utf-8"))

    def test_rejects_invalid_physical_composition_map_without_writing(self) -> None:
        ir = _manual_ir()
        payload = _stale_payload()
        payload["pages"][3]["start_page"] = 5  # type: ignore[index]
        payload["pages"][3]["page_count"] = 1  # type: ignore[index]
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "approved.json"
            original = json.dumps(payload)
            plan_path.write_text(original, encoding="utf-8")

            with self.assertRaisesRegex(
                ReferenceLayoutPlanError,
                "rebound approved reference layout plan is invalid",
            ):
                rebind_reference_layout_plan(
                    plan_path,
                    ir,
                    write=True,
                    content_approval=_approval(),
                )

            self.assertEqual(original, plan_path.read_text(encoding="utf-8"))

    def test_failed_atomic_replace_leaves_original_plan_intact(self) -> None:
        ir = _manual_ir()
        payload = _stale_payload()
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "approved.json"
            original = json.dumps(payload)
            plan_path.write_text(original, encoding="utf-8")

            with patch(
                "tools.idml.reference_layout_rebind.os.replace",
                side_effect=OSError("replace failed"),
            ), self.assertRaisesRegex(OSError, "replace failed"):
                rebind_reference_layout_plan(plan_path, ir, write=True)

            self.assertEqual(original, plan_path.read_text(encoding="utf-8"))
            self.assertEqual([], list(plan_path.parent.glob(".approved.json.*.tmp")))

    def test_cli_is_dry_run_by_default(self) -> None:
        ir = _manual_ir()
        payload = _stale_payload()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / "approved.json"
            ir_path = root / "manual.ir.json"
            original = json.dumps(payload)
            plan_path.write_text(original, encoding="utf-8")
            write_manual_ir(ir, ir_path)
            output = io.StringIO()

            with redirect_stdout(output):
                exit_code = rebind_main([
                    "--plan", str(plan_path),
                    "--manual-ir", str(ir_path),
                ])

            self.assertEqual(0, exit_code)
            self.assertIn("DRY-RUN OK", output.getvalue())
            self.assertIn("composition_map=unchanged", output.getvalue())
            self.assertEqual(original, plan_path.read_text(encoding="utf-8"))

    def test_cli_all_registered_runs_every_plan_as_dry_run(self) -> None:
        ir = _manual_ir()
        payload = _stale_payload()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ir_path = root / "manual.ir.json"
            write_manual_ir(ir, ir_path)
            plan_paths = []
            for name in ("first.json", "second.json"):
                plan_path = root / name
                plan_path.write_text(json.dumps(payload), encoding="utf-8")
                plan_paths.append(plan_path)
            registry_path = root / "registry.json"
            registry_path.write_text(
                json.dumps({"plans": [{"path": str(path)} for path in plan_paths]}),
                encoding="utf-8",
            )
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = rebind_main([
                    "--all-registered",
                    "--registry", str(registry_path),
                    "--manual-ir", str(ir_path),
                ])

        self.assertEqual(0, exit_code)
        self.assertEqual(2, output.getvalue().count("DRY-RUN OK"))
        self.assertIn("ALL-REGISTERED: plans=2 passed=2 failed=0 write=disabled", output.getvalue())

    def test_cli_all_registered_rejects_write(self) -> None:
        with self.assertRaises(SystemExit):
            rebind_main([
                "--all-registered",
                "--manual-ir", "manual.ir.json",
                "--write",
            ])

    def test_cli_content_reapproval_requires_complete_metadata(self) -> None:
        with self.assertRaises(SystemExit):
            rebind_main([
                "--plan", "approved.json",
                "--manual-ir", "manual.ir.json",
                "--approve-content-change",
                "--approved-by", "operator",
            ])


if __name__ == "__main__":
    unittest.main()
