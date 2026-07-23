from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from tools.idml.reference_layout_plan import (
    ReferenceLayoutPlanError,
    SCHEMA_VERSION,
    load_approved_reference_plan,
    normalize_approved_reference_plan,
    validate_approved_reference_plan,
)
from tools.manual_ir import ManualIR, ManualPage
from tools.utils.path_utils import PathSegments, Paths


def _manual_ir() -> ManualIR:
    source_pages = (
        ("a", "page/a", "page/a.rst", "a" * 64),
        ("b", "page/b", "page/b.rst", "b" * 64),
        ("c", "page/c", "page/c.rst", "c" * 64),
        ("d", "page/d", "page/d.rst", "d" * 64),
    )
    pages = tuple(
        ManualPage(
            page_id=f"page-{page_id}",
            source_ref=source_ref,
            source_path=source_path,
            language="en",
            source_sha256=source_sha256,
            skipped_raw=0,
            blocks=(),
        )
        for page_id, source_ref, source_path, source_sha256 in source_pages
    )
    return ManualIR(
        model="MODEL-1",
        region="US",
        language="en",
        source="test",
        bundle_root=".",
        bundle_sha256="0" * 64,
        snapshot_sha256="2" * 64,
        layout_params_sha256="3" * 64,
        style_contract_sha256="4" * 64,
        content_sha256="1" * 64,
        pages=pages,
        metadata={"layout_params_hash_algorithm": "ordered-layout-tokens/v1"},
    )


def _approved_payload(ir: ManualIR) -> dict[str, object]:
    compositions = (
        ("front", 1, 1),
        ("prose", 2, 2),
        ("prose", 2, 2),
        ("tail", 4, 2),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "target": {
            "model": ir.model,
            "region": ir.region,
            "languages": ["en"],
        },
        "reference_pdf": {
            "logical_id": "manual-model-1-us-v2",
            "file_name": "approved.pdf",
            "sha256": "5" * 64,
            "byte_size": 1234,
            "page_count": 5,
            "page_size_pt": {"width": 368.787, "height": 524.692},
            "page_size_tolerance_pt": 0.01,
            "pdfx": "PDF/X-4",
            "output_intent": "Display P3",
            "output_condition": "Display P3",
        },
        "source_identity": {
            "manual_ir_schema_version": ir.schema_version,
            "manual_content_sha256": ir.content_sha256,
            "snapshot_sha256": ir.snapshot_sha256,
            "style_contract_sha256": ir.style_contract_sha256,
            "layout_params_sha256": ir.layout_params_sha256,
        },
        "approval": {
            "status": "approved",
            "approved_by": "operator",
            "approved_at": "2026-07-16T12:00:00Z",
            "method": "page-by-page comparison",
        },
        "render_contract": {
            "dpi": 144,
            "raster_width_px": 738,
            "raster_height_px": 1050,
            "display_icc_sha256": "6" * 64,
            "gaussian_blur_px": 1.0,
            "changed_channel_threshold": 8,
            "max_rgb_mad": 0.015,
            "max_changed_pixel_ratio": 0.01,
        },
        "idml_contract": {
            "forbidden_visible_whole_page_links": ["flattened.pdf"],
        },
        "pages": [
            {
                "source_ref": page.source_ref,
                "source_sha256": page.source_sha256,
                "language": page.language,
                "composition_id": composition_id,
                "start_page": start_page,
                "page_count": page_count,
            }
            for page, (composition_id, start_page, page_count) in zip(
                ir.pages, compositions, strict=True
            )
        ],
    }


class ReferenceLayoutPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ir = _manual_ir()
        self.payload = _approved_payload(self.ir)

    def test_valid_approved_contract_normalizes_to_legacy_page_plan(self) -> None:
        self.assertEqual([], validate_approved_reference_plan(self.payload, self.ir))

        plan = normalize_approved_reference_plan(
            self.payload,
            self.ir,
            source_path=Path("docs/renderers/contracts/plans/model-1-us.json"),
        )

        self.assertEqual("latex-page-plan/v1", plan["schema_version"])
        self.assertEqual("approved-reference", plan["plan_source"])
        self.assertEqual(SCHEMA_VERSION, plan["approved_plan_schema_version"])
        self.assertEqual(5, plan["physical_page_count"])
        self.assertEqual(4, plan["source_page_count"])
        self.assertEqual(4, plan["matched_source_pages"])
        self.assertEqual(1.0, plan["match_rate"])
        self.assertEqual(self.ir.content_sha256, plan["manual_content_sha256"])
        self.assertEqual(self.ir.snapshot_sha256, plan["snapshot_sha256"])
        self.assertEqual(
            [page.source_path for page in self.ir.pages],
            [page["source_path"] for page in plan["pages"]],
        )
        self.assertEqual(
            [1, 2, 2, 4],
            [page["latex_start_page"] for page in plan["pages"]],
        )
        self.assertEqual(
            ["front", "prose", "prose", "tail"],
            [page["composition_id"] for page in plan["pages"]],
        )
        self.assertEqual(
            [1, 2, 2, 2],
            [page["planned_page_count"] for page in plan["pages"]],
        )
        self.assertRegex(plan["approved_plan_sha256"], r"^[0-9a-f]{64}$")

    def test_committed_je1000f_contract_keeps_58_page_component_binding(self) -> None:
        root = Path(__file__).resolve().parents[1]
        path = (
            root / "docs" / "renderers" / "contracts" / "reference_layout"
            / "je1000f_us_v2_20260605.json"
        )
        contract = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            "e38dad9c6e8d47ea2e1a3c5fe724786d22489861832beebd42cb5a4d953318b3",
            contract["source_identity"]["manual_content_sha256"],
        )
        pages = contract["pages"]
        self.assertEqual(52, len(pages))
        self.assertEqual(52, len({page["source_ref"] for page in pages}))
        self.assertEqual(1, min(page["start_page"] for page in pages))
        self.assertEqual(
            58,
            max(page["start_page"] + page["page_count"] - 1 for page in pages),
        )
        covered = {
            physical
            for page in pages
            for physical in range(
                page["start_page"],
                page["start_page"] + page["page_count"],
            )
        }
        self.assertEqual(set(range(1, 59)), covered)
        control_labels = contract["idml_contract"]["editable_components"][
            "app_add_device"
        ]["control_labels"]
        expected = {
            "en": {
                "base_labels_by_role": {
                    "main_power": "POWER Button",
                    "dc_usb": "DC / USB Power Button",
                    "ac": "AC Power Button",
                },
                "render_labels_by_role": {
                    "main_power": "Main Power Button",
                    "dc_usb": "DC/USB Power Button",
                    "ac": "AC Power Button",
                },
            },
            "fr": {
                "base_labels_by_role": {
                    "main_power": "Bouton d'alimentation",
                    "dc_usb": "Bouton d’alimentation CC / USB",
                    "ac": "Bouton Power CA",
                },
                "render_labels_by_role": {
                    "main_power": "Bouton POWER",
                    "dc_usb": "Bouton d’alimentation CC/USB",
                    "ac": "Bouton d’alimentation CA",
                },
            },
            "es": {
                "base_labels_by_role": {
                    "main_power": "Botón de encendido",
                    "dc_usb": "Botón de energía CC / USB",
                    "ac": "Botón Power CA",
                },
                "render_labels_by_role": {
                    "main_power": "Botón de encendido principal",
                    "dc_usb": "Botón de energía CC/USB",
                    "ac": "Botón de energía CA",
                },
            },
        }
        self.assertEqual(expected, control_labels)

    def test_legacy_layout_hash_algorithm_is_rejected(self) -> None:
        legacy_ir = replace(self.ir, metadata={})

        issues = validate_approved_reference_plan(self.payload, legacy_ir)

        self.assertIn(
            "manual IR metadata.layout_params_hash_algorithm must be "
            "'ordered-layout-tokens/v1'",
            issues,
        )

    def test_rejects_target_and_ir_identity_mismatches(self) -> None:
        cases = (
            (("target", "model"), "OTHER-MODEL", "target.model"),
            (
                ("source_identity", "manual_content_sha256"),
                "7" * 64,
                "source_identity.manual_content_sha256",
            ),
            (
                ("source_identity", "snapshot_sha256"),
                "7" * 64,
                "source_identity.snapshot_sha256",
            ),
            (
                ("source_identity", "style_contract_sha256"),
                "7" * 64,
                "source_identity.style_contract_sha256",
            ),
            (
                ("source_identity", "layout_params_sha256"),
                "7" * 64,
                "source_identity.layout_params_sha256",
            ),
        )
        for path, value, expected_issue in cases:
            with self.subTest(field=".".join(path)):
                payload = deepcopy(self.payload)
                payload[path[0]][path[1]] = value  # type: ignore[index]

                issues = validate_approved_reference_plan(payload, self.ir)

                self.assertTrue(
                    any(expected_issue in issue for issue in issues),
                    issues,
                )

    def test_rejects_impossible_or_loosened_render_contract(self) -> None:
        cases = (
            ("max_rgb_mad", 1.5, "must be in 0..1"),
            ("max_changed_pixel_ratio", 1.5, "must be in 0..1"),
            ("raster_width_px", 737, "raster dimensions must equal"),
        )
        for field, value, expected_issue in cases:
            with self.subTest(field=field):
                payload = deepcopy(self.payload)
                payload["render_contract"][field] = value  # type: ignore[index]

                issues = validate_approved_reference_plan(payload, self.ir)

                self.assertTrue(
                    any(expected_issue in issue for issue in issues), issues,
                )

    def test_rejects_whole_page_link_contract_paths(self) -> None:
        payload = deepcopy(self.payload)
        payload["idml_contract"] = {
            "forbidden_visible_whole_page_links": ["assets/flattened.pdf"],
        }

        issues = validate_approved_reference_plan(payload, self.ir)

        self.assertTrue(any("must contain file names only" in issue for issue in issues))

    def test_rejects_a_stale_source_page_hash(self) -> None:
        payload = deepcopy(self.payload)
        payload["pages"][1]["source_sha256"] = "7" * 64  # type: ignore[index]

        issues = validate_approved_reference_plan(payload, self.ir)

        self.assertTrue(any("page/b: source_sha256 does not match" in issue for issue in issues))

    def test_rejects_missing_source_coverage(self) -> None:
        payload = deepcopy(self.payload)
        payload["pages"].pop(2)  # type: ignore[union-attr]

        issues = validate_approved_reference_plan(payload, self.ir)

        self.assertTrue(any("exactly 4 entries" in issue for issue in issues), issues)
        self.assertTrue(any("missing source_ref entries: page/c" in issue for issue in issues), issues)

    def test_rejects_duplicate_source_coverage(self) -> None:
        payload = deepcopy(self.payload)
        payload["pages"][2] = deepcopy(payload["pages"][1])  # type: ignore[index]

        issues = validate_approved_reference_plan(payload, self.ir)

        self.assertTrue(any("duplicate source_ref: page/b" in issue for issue in issues), issues)
        self.assertTrue(any("missing source_ref entries: page/c" in issue for issue in issues), issues)

    def test_rejects_source_pages_out_of_ir_order(self) -> None:
        payload = deepcopy(self.payload)
        pages = payload["pages"]  # type: ignore[assignment]
        pages[1], pages[2] = pages[2], pages[1]  # type: ignore[index]

        issues = validate_approved_reference_plan(payload, self.ir)

        self.assertTrue(any("pages[1].source_ref is out of order" in issue for issue in issues), issues)
        self.assertTrue(any("pages[2].source_ref is out of order" in issue for issue in issues), issues)

    def test_rejects_composition_overlap_and_gap(self) -> None:
        cases = (
            (3, 3, "composition tail overlaps page 3"),
            (5, 1, "composition tail leaves a gap before page 5"),
        )
        for start_page, page_count, expected_issue in cases:
            with self.subTest(start_page=start_page, page_count=page_count):
                payload = deepcopy(self.payload)
                tail = payload["pages"][3]  # type: ignore[index]
                tail["start_page"] = start_page
                tail["page_count"] = page_count

                issues = validate_approved_reference_plan(payload, self.ir)

                self.assertIn(expected_issue, issues)

    def test_rejects_non_positive_composition_start_and_page_count(self) -> None:
        for field in ("start_page", "page_count"):
            with self.subTest(field=field):
                payload = deepcopy(self.payload)
                payload["pages"][0][field] = 0  # type: ignore[index]

                issues = validate_approved_reference_plan(payload, self.ir)

                self.assertTrue(
                    any("start_page and page_count must be positive integers" in issue for issue in issues),
                    issues,
                )

    def test_rejects_inconsistent_shared_composition_ranges(self) -> None:
        for field, value in (("start_page", 3), ("page_count", 1)):
            with self.subTest(field=field):
                payload = deepcopy(self.payload)
                payload["pages"][2][field] = value  # type: ignore[index]

                issues = validate_approved_reference_plan(payload, self.ir)

                self.assertTrue(
                    any("composition prose has inconsistent page ranges" in issue for issue in issues),
                    issues,
                )

    def test_rejects_composition_coverage_shorter_than_reference_page_count(self) -> None:
        payload = deepcopy(self.payload)
        payload["reference_pdf"]["page_count"] = 6  # type: ignore[index]

        issues = validate_approved_reference_plan(payload, self.ir)

        self.assertIn("composition coverage ends at page 5, expected 6", issues)

    def test_registry_non_matching_target_returns_none_without_reading_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_registry(
                root,
                target={"model": "OTHER", "region": "US", "languages": ["en"]},
                plan_path="missing.json",
            )

            self.assertIsNone(load_approved_reference_plan(root=root, ir=self.ir))

    def test_empty_registry_rejects_corrupt_plan_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_empty_registry(root)
            corrupt = (
                Paths(root=root).renderer_contracts_dir
                / PathSegments.REFERENCE_LAYOUT_DIR
                / "corrupt.json"
            )
            corrupt.parent.mkdir(parents=True, exist_ok=True)
            corrupt.write_text("{not-json", encoding="utf-8")
            with self.assertRaisesRegex(
                ReferenceLayoutPlanError,
                "cannot read approved reference layout candidate",
            ):
                load_approved_reference_plan(root=root, ir=self.ir)

    def test_missing_registry_and_no_approved_contract_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(
                load_approved_reference_plan(root=Path(tmp), ir=self.ir)
            )

    def test_missing_registry_with_matching_approved_plan_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = self._write_plan(root, self.payload)

            with self.assertRaisesRegex(
                ReferenceLayoutPlanError,
                "approved reference layout plan exists.*but is not registered",
            ) as caught:
                load_approved_reference_plan(root=root, ir=self.ir)

            self.assertIn(plan_path.as_posix(), str(caught.exception))

    def test_empty_registry_with_matching_approved_plan_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_empty_registry(root)
            self._write_plan(root, self.payload)

            with self.assertRaisesRegex(
                ReferenceLayoutPlanError,
                "approved reference layout plan exists.*but is not registered",
            ):
                load_approved_reference_plan(root=root, ir=self.ir)

    def test_registry_same_family_language_drift_fails_closed(self) -> None:
        pages = list(self.ir.pages)
        pages[1] = replace(pages[1], language="fr")
        multilingual_ir = replace(
            self.ir,
            pages=tuple(pages),
            metadata={**self.ir.metadata, "declared_languages": ["fr", "en"]},
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = self._target()
            target["languages"] = ["fr", "en"]
            self._write_registry(root, target=target, plan_path="missing.json")
            with self.assertRaisesRegex(ReferenceLayoutPlanError, "target mismatch"):
                load_approved_reference_plan(root=root, ir=multilingual_ir)

    def test_unregistered_same_family_language_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_empty_registry(root)
            payload = deepcopy(self.payload)
            payload["target"]["languages"] = ["fr"]  # type: ignore[index]
            self._write_plan(root, payload)
            with self.assertRaisesRegex(ReferenceLayoutPlanError, "not registered"):
                load_approved_reference_plan(
                    root=root,
                    ir=replace(
                        self.ir,
                        metadata={**self.ir.metadata, "declared_languages": ["fr"]},
                    ),
                )

    def test_same_family_registry_does_not_activate_ordinary_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_registry(
                root,
                target={"model": self.ir.model, "region": self.ir.region,
                        "languages": ["en", "fr", "es"]},
                plan_path="missing.json",
            )

            self.assertIsNone(load_approved_reference_plan(root=root, ir=self.ir))

    def test_empty_registry_ignores_draft_and_other_target_plans(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_empty_registry(root)
            draft = deepcopy(self.payload)
            draft["approval"]["status"] = "draft"  # type: ignore[index]
            self._write_plan(root, draft, name="draft.json")
            other = deepcopy(self.payload)
            other["target"]["model"] = "OTHER"  # type: ignore[index]
            self._write_plan(root, other, name="other.json")

            self.assertIsNone(load_approved_reference_plan(root=root, ir=self.ir))

    def test_registry_exact_target_loads_approved_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = self._write_plan(root, self.payload)
            self._write_registry(
                root, target=self._target(), plan_path=plan_path.as_posix(),
            )
            plan = load_approved_reference_plan(root=root, ir=self.ir)
            self.assertIsNotNone(plan)
            self.assertEqual("approved-reference", plan["plan_source"])

    def test_registry_matching_target_with_missing_plan_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_registry(root, target=self._target(), plan_path="missing.json")

            with self.assertRaisesRegex(ReferenceLayoutPlanError, "does not exist"):
                load_approved_reference_plan(root=root, ir=self.ir)

    def test_registry_matching_target_with_invalid_plan_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = "docs/renderers/contracts/plans/model-1-us.json"
            self._write_registry(root, target=self._target(), plan_path=plan_path)
            absolute_plan = root / plan_path
            absolute_plan.parent.mkdir(parents=True, exist_ok=True)
            invalid = deepcopy(self.payload)
            invalid["approval"]["status"] = "draft"  # type: ignore[index]
            absolute_plan.write_text(json.dumps(invalid), encoding="utf-8")

            with self.assertRaisesRegex(ReferenceLayoutPlanError, "approval.status"):
                load_approved_reference_plan(root=root, ir=self.ir)

    def _target(self) -> dict[str, object]:
        return {
            "model": self.ir.model,
            "region": self.ir.region,
            "languages": ["en"],
        }

    @staticmethod
    def _write_registry(
        root: Path,
        *,
        target: dict[str, object],
        plan_path: str,
    ) -> None:
        registry_path = (
            Paths(root=root).renderer_contracts_dir
            / PathSegments.REFERENCE_LAYOUT_REGISTRY_JSON
        )
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            json.dumps({
                "schema_version": "approved-reference-layout-registry/v1",
                "plans": [{"target": target, "path": plan_path}],
            }),
            encoding="utf-8",
        )

    @staticmethod
    def _write_empty_registry(root: Path) -> None:
        registry_path = (
            Paths(root=root).renderer_contracts_dir
            / PathSegments.REFERENCE_LAYOUT_REGISTRY_JSON
        )
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            json.dumps({
                "schema_version": "approved-reference-layout-registry/v1",
                "plans": [],
            }),
            encoding="utf-8",
        )

    @staticmethod
    def _write_plan(
        root: Path,
        payload: dict[str, object],
        *,
        name: str = "model-1-us.json",
    ) -> Path:
        relative = Path("docs/renderers/contracts/reference_layout") / name
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return relative


if __name__ == "__main__":
    unittest.main()
