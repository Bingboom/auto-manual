from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest

from tests.test_reference_layout_plan import _approved_payload, _manual_ir
from tools.idml.page_roles import PageRole
from tools.idml.pdf_parity_contract import _approved_contract_report
from tools.idml.reference_layout_plan import (
    ReferenceLayoutPlanError,
    V2_SCHEMA_VERSION,
    build_identity_scopes,
    validate_approved_reference_plan,
)
from tools.idml.reference_layout_rebind import build_rebound_reference_layout_plan


def _v2_payload() -> tuple[object, dict[str, object]]:
    ir = _manual_ir()
    payload = deepcopy(_approved_payload(ir))
    payload["schema_version"] = V2_SCHEMA_VERSION
    payload["idml_contract"]["allowed_unclassified_source_refs"] = [  # type: ignore[index]
        page.source_ref for page in ir.pages
    ]
    payload["identity"] = build_identity_scopes(payload, ir)
    del payload["source_identity"]
    return ir, payload


class ReferenceLayoutContractV2Tests(unittest.TestCase):
    def test_valid_v2_contract_uses_scoped_identity(self) -> None:
        ir, payload = _v2_payload()

        self.assertEqual([], validate_approved_reference_plan(payload, ir))
        identity = payload["identity"]  # type: ignore[assignment]
        self.assertEqual(ir.content_sha256, identity["content"]["manual_content_sha256"])
        self.assertEqual(ir.snapshot_sha256, identity["provenance"]["snapshot_sha256"])
        self.assertRegex(identity["assembly"]["sha256"], r"^[0-9a-f]{64}$")

    def test_v2_snapshot_drift_is_trace_only(self) -> None:
        ir, payload = _v2_payload()
        payload["identity"]["provenance"]["snapshot_sha256"] = "9" * 64  # type: ignore[index]

        issues = validate_approved_reference_plan(payload, ir)

        self.assertFalse(any("snapshot_sha256" in issue for issue in issues), issues)

    def test_v1_snapshot_drift_remains_fail_closed(self) -> None:
        ir = _manual_ir()
        payload = _approved_payload(ir)
        payload["source_identity"]["snapshot_sha256"] = "9" * 64  # type: ignore[index]

        issues = validate_approved_reference_plan(payload, ir)

        self.assertTrue(any("source_identity.snapshot_sha256" in issue for issue in issues))

    def test_v2_enforced_scopes_reject_drift(self) -> None:
        cases = (
            ("content", "manual_content_sha256"),
            ("style", "style_contract_sha256"),
            ("style", "layout_params_sha256"),
            ("assembly", "sha256"),
        )
        for scope, field in cases:
            with self.subTest(scope=scope, field=field):
                ir, payload = _v2_payload()
                payload["identity"][scope][field] = "9" * 64  # type: ignore[index]

                issues = validate_approved_reference_plan(payload, ir)

                self.assertTrue(
                    any(f"identity.{scope}.{field}" in issue for issue in issues),
                    issues,
                )

    def test_v2_assembly_identity_includes_semantic_page_roles(self) -> None:
        ir, payload = _v2_payload()

        with patch(
            "tools.idml.reference_layout_plan.classify_page_role",
            return_value=PageRole.PRODUCT_OVERVIEW,
        ):
            issues = validate_approved_reference_plan(payload, ir)

        self.assertTrue(any("identity.assembly.sha256" in issue for issue in issues), issues)

    def test_v2_rebind_requires_approval_for_page_role_drift(self) -> None:
        ir, payload = _v2_payload()

        with patch(
            "tools.idml.reference_layout_plan.classify_page_role",
            return_value=PageRole.PRODUCT_OVERVIEW,
        ), self.assertRaisesRegex(
            ReferenceLayoutPlanError,
            "cannot change content or assembly identity",
        ):
            build_rebound_reference_layout_plan(payload, ir)

    def test_v2_rejects_unclassified_approved_page_without_exact_exception(self) -> None:
        ir, payload = _v2_payload()
        payload["idml_contract"]["allowed_unclassified_source_refs"] = []  # type: ignore[index]
        payload["identity"] = build_identity_scopes(payload, ir)

        issues = validate_approved_reference_plan(payload, ir)

        self.assertTrue(any("unclassified prose is forbidden" in issue for issue in issues), issues)

    def test_v2_rejects_stale_unclassified_exception(self) -> None:
        ir, payload = _v2_payload()
        payload["idml_contract"]["allowed_unclassified_source_refs"].append(  # type: ignore[index]
            "page/not-in-this-manual.rst",
        )
        payload["identity"] = build_identity_scopes(payload, ir)

        issues = validate_approved_reference_plan(payload, ir)

        self.assertTrue(any("exception is not a current source_ref" in issue for issue in issues), issues)

    def test_v2_parity_report_marks_snapshot_as_non_enforced_provenance(self) -> None:
        ir, payload = _v2_payload()
        with tempfile.TemporaryDirectory() as tmp:
            reference_path = Path(tmp) / "reference.pdf"
            reference_path.write_bytes(b"pdf")
            payload["reference_pdf"]["byte_size"] = 3  # type: ignore[index]
            report = _approved_contract_report(
                plan_path=None,
                plan=payload,
                manual_ir={
                    "content_sha256": ir.content_sha256,
                    "snapshot_sha256": "9" * 64,
                    "style_contract_sha256": ir.style_contract_sha256,
                    "layout_params_sha256": ir.layout_params_sha256,
                },
                reference={
                    "path": str(reference_path),
                    "sha256": payload["reference_pdf"]["sha256"],  # type: ignore[index]
                    "page_count": payload["reference_pdf"]["page_count"],  # type: ignore[index]
                },
            )

        self.assertTrue(report["pass"])
        self.assertFalse(report["provenance"]["snapshot_sha256"]["enforced"])
        self.assertNotEqual(
            report["provenance"]["snapshot_sha256"]["approved"],
            report["provenance"]["snapshot_sha256"]["current"],
        )


if __name__ == "__main__":
    unittest.main()
