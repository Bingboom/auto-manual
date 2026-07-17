from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.asset_pipeline.models import RecipeValidationError
from tools.asset_pipeline.recipe import load_recipe

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_RECIPE = ROOT / "data" / "asset_recipes" / "manual_je1000f_us_master.json"


def sample_recipe_payload(*, source_sha256: str = "a" * 64) -> dict[str, object]:
    page_catalog: list[dict[str, object]] = []
    for page in range(1, 60):
        role = "engineering_overview" if page == 1 else "manual_page"
        risk_tags: list[str] = []
        gate = {"status": "archive", "reasons": []}
        if page == 20:
            role = "app_setup"
            risk_tags = ["app-ui", "qr"]
            gate = {"status": "quarantine", "reasons": ["localized App and QR review"]}
        page_catalog.append(
            {
                "page": page,
                "page_key": f"page_{page:04d}",
                "role": role,
                "locale": "und",
                "build_eligible": False,
                "gate": gate,
                "risk_tags": risk_tags,
            }
        )

    assets: list[dict[str, object]] = []
    for index in range(10):
        asset_key = f"illustration/figure_{index + 1}"
        gate = {"status": "approved", "reasons": []}
        risk_tags = []
        if index == 9:
            asset_key = "app/qr_setup"
            gate = {"status": "quarantine", "reasons": ["QR target not approved"]}
            risk_tags = ["app-ui", "qr"]
        transforms: list[dict[str, object]] = [
            {"op": "crop", "bbox_pt": [10, 10, 110, 100]},
        ]
        if index < 3:
            transforms.append(
                {
                    "op": "redact_text",
                    "images": "preserve",
                    "graphics": "remove_if_touched" if index == 0 else "preserve",
                    "fill": None,
                }
            )
        if index == 0:
            transforms.append({"op": "whiteout", "bbox_pt": [80, 70, 100, 90]})
        outputs: list[dict[str, object]] = [
            {
                "format": "pdf",
                "path": f"docs/assets/figure_{index + 1}.pdf",
                "expected_sha256": "c" * 64,
            },
            {
                "format": "png",
                "path": f"docs/assets/figure_{index + 1}.png",
                "scale": (4, 8, 3)[index] if index < 3 else 1,
                "expected_sha256": "c" * 64,
            },
        ]
        if index == 0:
            outputs[1]["expected_sha256"] = "b" * 64
        assets.append(
            {
                "asset_key": asset_key,
                "page": index + 2,
                "build_eligible": gate["status"] == "approved",
                "scope": {"models": ["TEST"], "regions": ["US"], "locales": ["und"]},
                "text_policy": "numeric-only" if index == 0 else "textless",
                "visual_review_required": gate["status"] == "quarantine",
                "transforms": transforms,
                "outputs": outputs,
                "gate": gate,
                "risk_tags": risk_tags,
            }
        )
    return {
        "schema_version": 1,
        "coordinate_contract": {
            "page_numbering": "pdf-1-based",
            "bbox_units": "pt",
            "bbox_origin": "top-left",
            "bbox_space": "source-page",
        },
        "normalization": {
            "engine": "pymupdf",
            "validated_version": "1.28.0",
            "validated_mupdf_version": "1.29.0",
            "pdf_save": {
                "garbage": 4,
                "clean": True,
                "deflate": True,
                "no_new_id": True,
            },
            "forbidden_pdf_markers": ["AIPrivateData", "PieceInfo", "AIMetaData"],
            "max_render_pixels": 40_000_000,
        },
        "source": {
            "source_key": "source/manual_test_master",
            "expected_sha256": source_sha256,
            "expected_page_count": 59,
        },
        "archive": {
            "pages": {"first": 1, "last": 59},
            "pdf": {"path_pattern": "archive/pages/page-{page:04d}.pdf"},
            "previews": {
                "path_pattern": "archive/previews/page-{page:04d}.png",
                "default_scale": 1,
                "page_scale": {"1": 0.25},
            },
        },
        "page_catalog": page_catalog,
        "assets": assets,
    }


class TestAssetRecipe(unittest.TestCase):
    def _load(self, payload: dict[str, object]):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "recipe.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return load_recipe(path)

    def test_loads_59_page_archive_and_ten_bbox_assets(self) -> None:
        recipe = self._load(sample_recipe_payload())

        self.assertEqual(tuple(range(1, 60)), recipe.archive.pages.values)
        self.assertEqual(59, len(recipe.page_catalog))
        self.assertEqual(10, len(recipe.assets))
        self.assertEqual((10.0, 10.0, 110.0, 100.0), recipe.assets[0].crop_bbox)
        self.assertEqual("remove_if_touched", recipe.assets[0].transforms[1].graphics)
        self.assertEqual("preserve", recipe.assets[1].transforms[1].graphics)
        self.assertEqual(4.0, recipe.assets[0].outputs[1].scale)
        self.assertEqual("b" * 64, recipe.assets[0].outputs[1].expected_sha256)
        self.assertEqual("quarantine", recipe.assets[-1].gate.status)
        self.assertEqual("pdf-1-based", recipe.coordinate_contract.page_numbering)
        self.assertEqual(40_000_000, recipe.normalization.max_render_pixels)

    def test_rejects_zero_based_asset_page(self) -> None:
        payload = sample_recipe_payload()
        payload["assets"][0]["page"] = 0  # type: ignore[index]

        with self.assertRaisesRegex(RecipeValidationError, "integer >= 1"):
            self._load(payload)

    def test_rejects_crop_that_is_not_first(self) -> None:
        payload = sample_recipe_payload()
        transforms = payload["assets"][0]["transforms"]  # type: ignore[index]
        transforms[0], transforms[1] = transforms[1], transforms[0]

        with self.assertRaisesRegex(RecipeValidationError, "crop must be the first"):
            self._load(payload)

    def test_rejects_unapproved_sensitive_asset(self) -> None:
        payload = sample_recipe_payload()
        payload["assets"][-1]["gate"] = {"status": "approved", "reasons": []}  # type: ignore[index]

        with self.assertRaisesRegex(RecipeValidationError, "must be quarantined"):
            self._load(payload)

    def test_rejects_unsupported_redaction_graphics_mode(self) -> None:
        payload = sample_recipe_payload()
        payload["assets"][0]["transforms"][1]["graphics"] = "remove_all"  # type: ignore[index]

        with self.assertRaisesRegex(RecipeValidationError, "remove_if_touched"):
            self._load(payload)

    def test_loads_bbox_scoped_text_redaction(self) -> None:
        payload = sample_recipe_payload()
        payload["assets"][0]["transforms"].insert(  # type: ignore[index]
            1,
            {
                "op": "redact_text_region",
                "bbox_pt": [70, 60, 100, 90],
                "images": "preserve",
                "graphics": "preserve",
                "fill": None,
            },
        )

        recipe = self._load(payload)

        transform = recipe.assets[0].transforms[1]
        self.assertEqual("redact_text_region", transform.op)
        self.assertEqual((70.0, 60.0, 100.0, 90.0), transform.bbox_pt)
        self.assertEqual("preserve", transform.graphics)

    def test_rejects_bbox_scoped_text_redaction_without_bbox(self) -> None:
        payload = sample_recipe_payload()
        payload["assets"][0]["transforms"].insert(  # type: ignore[index]
            1,
            {
                "op": "redact_text_region",
                "images": "preserve",
                "graphics": "preserve",
                "fill": None,
            },
        )

        with self.assertRaisesRegex(RecipeValidationError, "missing field.*bbox_pt"):
            self._load(payload)

    def test_rejects_high_scale_engineering_overview_preview(self) -> None:
        payload = sample_recipe_payload()
        payload["archive"]["previews"]["page_scale"]["1"] = 1  # type: ignore[index]

        with self.assertRaisesRegex(RecipeValidationError, "explicit scale below 1"):
            self._load(payload)

    def test_rejects_missing_archive_previews(self) -> None:
        payload = sample_recipe_payload()
        del payload["archive"]["previews"]  # type: ignore[index]

        with self.assertRaisesRegex(RecipeValidationError, "missing field.*previews"):
            self._load(payload)

    def test_allows_multiple_png_repo_paths(self) -> None:
        payload = sample_recipe_payload()
        payload["assets"][0]["outputs"].append(  # type: ignore[index]
            {
                "format": "png",
                "path": "docs/assets/mirror/figure_1.png",
                "scale": 4,
                "expected_sha256": "b" * 64,
            }
        )

        recipe = self._load(payload)

        self.assertEqual(2, sum(output.format == "png" for output in recipe.assets[0].outputs))

    def test_rejects_unsafe_output_path(self) -> None:
        payload = sample_recipe_payload()
        payload["assets"][0]["outputs"][0]["path"] = "../escaped.pdf"  # type: ignore[index]

        with self.assertRaisesRegex(RecipeValidationError, "unsafe path segment"):
            self._load(payload)

    def test_rejects_partial_expected_hash(self) -> None:
        payload = deepcopy(sample_recipe_payload())
        payload["assets"][0]["outputs"][1]["expected_sha256"] = "deadbeef"  # type: ignore[index]

        with self.assertRaisesRegex(RecipeValidationError, "complete 64-character"):
            self._load(payload)

    def test_rejects_approved_output_without_expected_hash(self) -> None:
        payload = sample_recipe_payload()
        del payload["assets"][0]["outputs"][0]["expected_sha256"]  # type: ignore[index]

        with self.assertRaisesRegex(RecipeValidationError, "approved assets require expected"):
            self._load(payload)

    def test_rejects_normalization_version_drift(self) -> None:
        payload = sample_recipe_payload()
        payload["normalization"]["validated_version"] = "1.27.0"  # type: ignore[index]

        with self.assertRaisesRegex(RecipeValidationError, "must be '1.28.0'"):
            self._load(payload)

    @unittest.skipUnless(OFFICIAL_RECIPE.is_file(), "official recipe lands in companion PR")
    def test_official_recipe_matches_runtime_contract(self) -> None:
        recipe = load_recipe(OFFICIAL_RECIPE)

        self.assertEqual(59, len(recipe.page_catalog))
        self.assertEqual(24, len(recipe.assets))
        self.assertEqual(
            {21, 22, 39, 40, 57, 58, 59},
            {row.page for row in recipe.page_catalog if row.gate.status == "quarantine"},
        )
        self.assertEqual(
            {"textless", "numeric-only", "fixed-product-markings", "localized-full-page"},
            {asset.text_policy for asset in recipe.assets},
        )
        self.assertTrue(
            any(
                sum(output.format == "png" for output in asset.outputs) > 1
                for asset in recipe.assets
            )
        )
        by_key = {asset.asset_key: asset for asset in recipe.assets}
        expected_pages = {
            "operation/je1000f_us/energy_saving": 13,
            "operation/je1000f_us/lcd_mode": 14,
            "operation/je1000f_us/ups_mode": 15,
            "charging/je1000f_us/solar_adapter": 17,
            "charging/je1000f_us/car_charge": 17,
        }
        for asset_key, page in expected_pages.items():
            with self.subTest(asset_key=asset_key):
                asset = by_key[asset_key]
                self.assertEqual(page, asset.page)
                self.assertEqual("approved", asset.gate.status)
                self.assertEqual(("JE-1000F",), asset.scope.models)
                self.assertEqual(("US",), asset.scope.regions)
                self.assertTrue(all(
                    not output.path.startswith(
                        "docs/templates/word_template/common_assets/"
                    )
                    for output in asset.outputs
                ))
        qr_candidate = by_key["qr/back_cover_ai_candidate"]
        self.assertEqual(59, qr_candidate.page)
        self.assertEqual("quarantine", qr_candidate.gate.status)
        self.assertFalse(qr_candidate.build_eligible)
        self.assertTrue(qr_candidate.visual_review_required)
        self.assertEqual("numeric-only", qr_candidate.text_policy)
        self.assertEqual(
            (309.16900634765625, 464.8030090332031,
             338.9330139160156, 494.5670166015625),
            qr_candidate.crop_bbox,
        )
        self.assertTrue(all(output.expected_sha256 for output in qr_candidate.outputs))


if __name__ == "__main__":
    unittest.main()
