from __future__ import annotations

import hashlib
import json
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.asset_pipeline.models import RecipeValidationError
from tools.asset_pipeline.recipe import _transform, load_recipe

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
        self.assertEqual(25, len(recipe.assets))
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
            "controls/je1000f_us/network_pairing_panel": 39,
            "overview/je1000f_us/front_controls": 8,
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

    def test_every_committed_recipe_loads(self) -> None:
        """Guard the whole directory, not one hand-picked file.

        Nothing else globs data/asset_recipes/*.json: the tests name
        manual_je1000f_us_master.json and manual_je1000f_us_front_controls.json
        directly, so a malformed or half-edited recipe used to pass the suite
        and only fail when an operator ran asset_intake against it.
        """
        recipes = sorted(
            path
            for path in (ROOT / "data" / "asset_recipes").glob("*.json")
            if not path.name.endswith(".schema.json")
        )
        self.assertTrue(recipes, "no recipes found to validate")
        for path in recipes:
            with self.subTest(recipe=path.name):
                recipe = load_recipe(path)
                self.assertTrue(recipe.assets or recipe.page_catalog)
                for asset in recipe.assets:
                    if asset.gate.status == "approved":
                        self.assertTrue(
                            all(output.expected_sha256 for output in asset.outputs),
                            f"{path.name}:{asset.asset_key} approved without pinned hashes",
                        )

    def test_battery_pack_recipe_matches_runtime_contract(self) -> None:
        """The JBP-2000B master carries two text policies on purpose.

        The overview pair is textless because this master's product silkscreen
        is live text and gets redacted with the callouts. The connections and
        charging figures cannot be: every character left in those crops is
        vector outline that redaction physically cannot reach, so they declare
        fixed-product-markings and are scoped to US, where the host art's
        NEMA 5-20R receptacles and HomePower nameplate are correct.
        """
        recipe = load_recipe(
            ROOT / "data" / "asset_recipes" / "manual_jbp2000b_us_overview.json"
        )

        self.assertEqual(28, len(recipe.page_catalog))
        by_key = {asset.asset_key: asset for asset in recipe.assets}
        self.assertEqual(
            {
                "overview/jbp2000b/front_controls",
                "overview/jbp2000b/left_side_ports",
                "connections/jbp2000b/stack_clearance",
                "charging/jbp2000b/solar",
            },
            set(by_key),
        )
        for asset in recipe.assets:
            with self.subTest(asset_key=asset.asset_key):
                self.assertEqual("approved", asset.gate.status)
                self.assertTrue(asset.build_eligible)
                self.assertFalse(asset.visual_review_required)
                self.assertEqual(("JBP-2000B",), asset.scope.models)
                self.assertTrue(all(output.expected_sha256 for output in asset.outputs))

        overview = ("overview/jbp2000b/front_controls", "overview/jbp2000b/left_side_ports")
        for key in overview:
            self.assertEqual("textless", by_key[key].text_policy)
            self.assertEqual(("ALL",), by_key[key].scope.regions)

        region_locked = ("connections/jbp2000b/stack_clearance", "charging/jbp2000b/solar")
        for key in region_locked:
            asset = by_key[key]
            self.assertEqual("fixed-product-markings", asset.text_policy)
            self.assertEqual(("US",), asset.scope.regions)
            self.assertIn("region-locked-art", asset.risk_tags)

        stack = by_key["connections/jbp2000b/stack_clearance"]
        self.assertEqual(7, stack.page)
        self.assertEqual(
            ["crop", "whiteout"], [item.op for item in stack.transforms]
        )
        solar = by_key["charging/jbp2000b/solar"]
        self.assertEqual(9, solar.page)
        self.assertEqual(
            ["crop", "redact_text"], [item.op for item in solar.transforms]
        )

    def test_je3000c_eu_uk_overview_recipe_is_pinned(self) -> None:
        recipe = load_recipe(
            ROOT
            / "data"
            / "asset_recipes"
            / "manual_je3000c_eu_uk_overview.json"
        )

        self.assertEqual(19, len(recipe.page_catalog))
        self.assertEqual(
            "c7a43b6e77003c3e5e4bd772ea7a8df7c0938c9992b494b045e54970e0c00557",
            recipe.source.expected_sha256,
        )
        self.assertEqual(1, len(recipe.assets))
        asset = recipe.assets[0]
        self.assertEqual("overview/je3000c_kr/right_art", asset.asset_key)
        self.assertEqual(("JE-3000C",), asset.scope.models)
        self.assertEqual(("KR",), asset.scope.regions)
        self.assertEqual("approved", asset.gate.status)
        self.assertEqual(
            ["crop", "retain_vector_drawings"],
            [item.op for item in asset.transforms],
        )
        retained = asset.transforms[1]
        self.assertEqual(tuple(range(372, 392)), retained.drawing_indices)
        self.assertEqual((373,), retained.stroke_suppressed_indices)
        self.assertEqual(
            "ad9c45dd8b7fc3de49f849fbcbac89e9d3ba4be0e4a2ca896fb7cddd05645936",
            asset.outputs[0].expected_sha256,
        )

    def test_battery_pack_box_and_lcd_recipe_matches_operator_choice(self) -> None:
        recipe = load_recipe(
            ROOT
            / "data"
            / "asset_recipes"
            / "manual_jbp2000b_us_missing_assets.json"
        )

        self.assertEqual(28, len(recipe.page_catalog))
        by_key = {asset.asset_key: asset for asset in recipe.assets}
        self.assertEqual(
            {
                "in_the_box/jbp2000b/main_unit",
                "in_the_box/jbp2000b/expansion_cable",
                "lcd/jbp2000b/screen",
            },
            set(by_key),
        )
        for asset in by_key.values():
            self.assertEqual("approved", asset.gate.status)
            self.assertTrue(asset.build_eligible)
            self.assertFalse(asset.visual_review_required)
            self.assertEqual(("JBP-2000B",), asset.scope.models)
            self.assertEqual(("ALL",), asset.scope.regions)
            self.assertTrue(all(output.expected_sha256 for output in asset.outputs))

        main = by_key["in_the_box/jbp2000b/main_unit"]
        self.assertEqual("fixed-product-markings", main.text_policy)
        self.assertEqual(["crop"], [item.op for item in main.transforms])

        cable = by_key["in_the_box/jbp2000b/expansion_cable"]
        self.assertEqual("textless", cable.text_policy)
        self.assertEqual(
            ["crop", "whiteout", "whiteout"],
            [item.op for item in cable.transforms],
        )

        lcd = by_key["lcd/jbp2000b/screen"]
        self.assertEqual("numeric-only", lcd.text_policy)
        self.assertEqual(["crop"], [item.op for item in lcd.transforms])

    def test_battery_pack_layout_recipe_matches_visual_review(self) -> None:
        recipe = load_recipe(
            ROOT
            / "data"
            / "asset_recipes"
            / "manual_jbp2000b_us_layout_assets.json"
        )

        self.assertEqual(28, len(recipe.page_catalog))
        by_key = {asset.asset_key: asset for asset in recipe.assets}
        self.assertEqual(11, len(by_key))
        qr = by_key.pop("qr/jbp2000b/back_cover")
        for asset in by_key.values():
            with self.subTest(asset_key=asset.asset_key):
                self.assertEqual("approved", asset.gate.status)
                self.assertTrue(asset.build_eligible)
                self.assertFalse(asset.visual_review_required)
                self.assertEqual(("JBP-2000B",), asset.scope.models)
                self.assertEqual(("US",), asset.scope.regions)
                self.assertTrue(all(output.expected_sha256 for output in asset.outputs))

        self.assertEqual("quarantine", qr.gate.status)
        self.assertFalse(qr.build_eligible)
        self.assertTrue(qr.visual_review_required)
        self.assertTrue(all(output.expected_sha256 for output in qr.outputs))
        self.assertIn("160102000279", " ".join(qr.gate.reasons))
        self.assertEqual(
            ["crop", "redact_text_region"],
            [item.op for item in by_key["operation/jbp2000b/panels_es"].transforms],
        )

    def test_battery_pack_fixed_markings_corrective_recipe_is_pinned(self) -> None:
        recipe_root = ROOT / "data" / "asset_recipes"
        recipe = load_recipe(recipe_root / "manual_jbp2000b_us_fixed_markings.json")

        self.assertEqual(28, len(recipe.page_catalog))
        by_key = {asset.asset_key: asset for asset in recipe.assets}
        self.assertEqual(
            {
                "overview/jbp2000b/front_controls",
                "overview/jbp2000b/left_side_ports",
                "operation/jbp2000b/power_control",
                "operation/jbp2000b/lcd_control",
            },
            set(by_key),
        )
        for asset in by_key.values():
            with self.subTest(asset_key=asset.asset_key):
                self.assertEqual("approved", asset.gate.status)
                self.assertTrue(asset.build_eligible)
                self.assertFalse(asset.visual_review_required)
                self.assertEqual("fixed-product-markings", asset.text_policy)
                self.assertEqual(("JBP-2000B",), asset.scope.models)
                self.assertEqual(("ALL",), asset.scope.regions)
                self.assertEqual(("und",), asset.scope.locales)

        self.assertEqual(
            ["crop", "drop_leader_strokes"],
            [item.op for item in by_key["overview/jbp2000b/front_controls"].transforms],
        )
        self.assertEqual(
            ["crop", "drop_leader_strokes", "redact_text_region"],
            [item.op for item in by_key["overview/jbp2000b/left_side_ports"].transforms],
        )
        for key in ("operation/jbp2000b/power_control", "operation/jbp2000b/lcd_control"):
            self.assertEqual(["crop", "redact_text"], [item.op for item in by_key[key].transforms])

        expected_hashes = {
            "overview/jbp2000b/front_controls": (
                "26b6ac82fb421fc6ee906706c9a4ec41882a5b17a52c805ad29d95c94e81ec85",
                "c405e6a1fdd35bb593429ee85568e843e02ced8e8a43d672ef1cb8034774cce3",
            ),
            "overview/jbp2000b/left_side_ports": (
                "9c4bd27261e9a5688448867250a9afdc450d445e8eda46fdc3b939ff20de18e8",
                "6ac9bc60991ebd6da65bcea1f62a1f82a737d8f38031144396d857f35ccbd8fc",
            ),
            "operation/jbp2000b/power_control": (
                "66a0306a88f6a0e1163a996de234303544b46b9290012f6e7eed2744e1e32a54",
                "c8332fadce5987fef4ecd43938fb3a61bda2211b588bd20fd7c52a18768b1799",
            ),
            "operation/jbp2000b/lcd_control": (
                "e977dbc5bea5876e249cdf84db10545b488d692d62caac31ee55a057d719da7c",
                "4d5f74e927261d7c174b45b5c0eb039d0e7c11ff4ab4c932e5719d2138415975",
            ),
        }
        for key, hashes in expected_hashes.items():
            self.assertEqual(hashes, tuple(output.expected_sha256 for output in by_key[key].outputs))

        immutable_recipes = {
            "manual_jbp2000b_us_layout_assets.json": (
                "193dbefb773a04dfc1e6fface5f101c84b336aecc9906a5d94e0b073eefafc42"
            ),
            "manual_jbp2000b_us_overview.json": (
                "b1ad1130e03f48313d103f7b795e8c501c1795633c9af4730b64946a4a21365b"
            ),
        }
        for filename, expected in immutable_recipes.items():
            actual = hashlib.sha256((recipe_root / filename).read_bytes()).hexdigest()
            self.assertEqual(expected, actual, filename)

    def test_leader_widths_default_to_the_pipeline_constants(self) -> None:
        """Omitting the widths must keep pre-existing recipes byte-identical.

        The widths became per-recipe so a second master could use the operator
        at all; every recipe written before that carries no width fields and
        must still resolve to the JE-1000F US master's 1.821pt / 0.30pt.
        """
        from tools.asset_pipeline import leaders

        spec = _transform({"op": "drop_leader_strokes"}, "t")
        self.assertIsNone(spec.halo_width_pt)
        self.assertIsNone(spec.line_width_pt)
        self.assertIsNone(spec.width_tolerance_pt)
        self.assertNotIn("halo_width_pt", spec.as_manifest())
        self.assertAlmostEqual(1.821, leaders.HALO_WIDTH)
        self.assertAlmostEqual(0.30, leaders.LINE_WIDTH)
        self.assertAlmostEqual(0.03, leaders.WIDTH_TOLERANCE)

    def test_leader_widths_round_trip_when_declared(self) -> None:
        spec = _transform(
            {
                "op": "drop_leader_strokes",
                "halo_width_pt": 2.0,
                "line_width_pt": 0.202,
                "width_tolerance_pt": 0.05,
            },
            "t",
        )
        self.assertAlmostEqual(2.0, spec.halo_width_pt)
        self.assertAlmostEqual(0.202, spec.line_width_pt)
        self.assertAlmostEqual(0.05, spec.width_tolerance_pt)
        manifest = spec.as_manifest()
        self.assertAlmostEqual(2.0, manifest["halo_width_pt"])
        self.assertAlmostEqual(0.202, manifest["line_width_pt"])

    def test_rejects_out_of_range_leader_width(self) -> None:
        for bad in (0, -1, 9, "2.0", True):
            with self.subTest(bad=bad):
                with self.assertRaises(Exception):
                    _transform(
                        {"op": "drop_leader_strokes", "halo_width_pt": bad}, "t"
                    )

    def test_retain_vector_drawings_round_trips(self) -> None:
        spec = _transform(
            {
                "op": "retain_vector_drawings",
                "drawing_indices": [0, 2, 5],
                "fill_rgb_overrides": {"0": [244 / 255, 244 / 255, 244 / 255]},
                "stroke_suppressed_indices": [2],
            },
            "t",
        )

        self.assertEqual((0, 2, 5), spec.drawing_indices)
        self.assertEqual(0, spec.fill_rgb_overrides[0][0])
        self.assertEqual((2,), spec.stroke_suppressed_indices)
        self.assertEqual(
            [0, 2, 5],
            spec.as_manifest()["drawing_indices"],
        )

    def test_retain_vector_drawings_rejects_ambiguous_indices(self) -> None:
        for indices in ([], [1, 1], [2, 1], [-1], [True]):
            with self.subTest(indices=indices):
                with self.assertRaises(Exception):
                    _transform(
                        {
                            "op": "retain_vector_drawings",
                            "drawing_indices": indices,
                            "fill_rgb_overrides": {},
                            "stroke_suppressed_indices": [],
                        },
                        "t",
                    )

    def test_retain_vector_drawings_is_exclusive_after_crop(self) -> None:
        payload = sample_recipe_payload()
        payload["assets"][0]["transforms"] = [  # type: ignore[index]
            {"op": "crop", "bbox_pt": [10, 10, 110, 100]},
            {
                "op": "retain_vector_drawings",
                "drawing_indices": [0],
                "fill_rgb_overrides": {},
                "stroke_suppressed_indices": [],
            },
            {"op": "whiteout", "bbox_pt": [80, 70, 100, 90]},
        ]

        with self.assertRaisesRegex(
            RecipeValidationError,
            "retain_vector_drawings must be the only transform after crop",
        ):
            self._load(payload)

        for suppressed in ([1, 1], [2, 1], [5], [-1], [True]):
            with self.subTest(suppressed=suppressed):
                with self.assertRaises(Exception):
                    _transform(
                        {
                            "op": "retain_vector_drawings",
                            "drawing_indices": [0, 1, 2],
                            "fill_rgb_overrides": {},
                            "stroke_suppressed_indices": suppressed,
                        },
                        "t",
                    )


if __name__ == "__main__":
    unittest.main()
