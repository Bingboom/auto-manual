from __future__ import annotations

import hashlib
import json
import shutil
import unittest
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.app_ui_promotion import (
    CANDIDATE_ASSET_KEYS,
    EU_PROMOTION,
    EU_PROMOTION_ID,
    PROMOTED_ASSET_KEYS,
    PROMOTION_CONTRACT_SHA256,
    PROMOTION_ID,
    PROMOTION_RELATIVE_PATH,
    ReviewedPromotionError,
    promotion_for_asset,
    validate_reviewed_promotion,
)
from tools.asset_rewrites import restore_registry_asset_uris
from tools.asset_registry import (
    QUARANTINED_STATUS,
    AssetRegistryError,
    check_registry,
    load_registry,
    resolve_asset,
)
from tools.asset_usage import AssetTarget, BundleAssetUsage
from tools.build_docs_export import _copy_attachment_images_for_latex
from tools.gen_index_bundle_assets import rewrite_rst_asset_paths
from tools.idml.primitives import resolve_bundle_image


ROOT = Path(__file__).resolve().parents[1]
RECIPE_RELATIVE_PATH = Path("data/asset_recipes/manual_je1000f_us_master.json")
EVIDENCE_RELATIVE_PATH = Path("data/asset_evidence/app_ui_candidates.json")
CANDIDATE_DIR = Path("data/asset_evidence/app_ui/je1000f_us")
PROMOTED_DIR = Path("docs/templates/word_template/common_assets/app/je1000f_us")
LEGACY_APP_DIR = Path("docs/templates/word_template/common_assets/app")
EU_CANDIDATE_DIR = Path("data/asset_evidence/app_ui/je1000f_eu")
EU_PROMOTED_DIR = Path("docs/templates/word_template/common_assets/app/je1000f_eu")
EU_LANGUAGES = ("en", "fr", "es", "de", "it", "uk")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_file(root: Path, relative: Path) -> None:
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / relative, destination)


def _copy_promotion_inputs(root: Path) -> None:
    for relative in (
        PROMOTION_RELATIVE_PATH,
        RECIPE_RELATIVE_PATH,
        EVIDENCE_RELATIVE_PATH,
    ):
        _copy_file(root, relative)
    shutil.copytree(ROOT / CANDIDATE_DIR, root / CANDIDATE_DIR)
    shutil.copytree(ROOT / PROMOTED_DIR, root / PROMOTED_DIR)


def _copy_eu_promotion_inputs(root: Path) -> None:
    for relative in (
        EU_PROMOTION.contract_path,
        EU_PROMOTION.recipe_path,
        EU_PROMOTION.evidence_path,
    ):
        _copy_file(root, relative)
    shutil.copytree(ROOT / EU_CANDIDATE_DIR, root / EU_CANDIDATE_DIR)
    shutil.copytree(ROOT / EU_PROMOTED_DIR, root / EU_PROMOTED_DIR)


def _rewrite_app_page(bundle: Path, source: str, target: AssetTarget) -> tuple[str, BundleAssetUsage]:
    page = bundle / "page" / "app.rst"
    page.parent.mkdir(parents=True)
    page.write_text(source, encoding="utf-8")
    usage = BundleAssetUsage(target=target, repo_root=ROOT)
    rewritten = rewrite_rst_asset_paths(
        source,
        source_path=page,
        target_path=page,
        bundle_dir=bundle,
        docs_dir=ROOT / "docs",
        repo_root=ROOT,
        asset_usage=usage,
        model=target.model,
        region=target.region,
        language=target.language,
    )
    return rewritten, usage


class TestAppUiReviewedPromotion(unittest.TestCase):
    def setUp(self) -> None:
        self.records = load_registry(ROOT / "data" / "asset_registry.csv")
        self.by_key = {record.asset_key: record for record in self.records}

    def test_real_contract_resolves_only_the_scoped_production_mapping(self) -> None:
        for asset_key in PROMOTED_ASSET_KEYS:
            for language in ("en", "fr", "es"):
                with self.subTest(asset_key=asset_key, language=language):
                    resolution = resolve_asset(
                        self.records,
                        repo_root=ROOT,
                        asset_key=asset_key,
                        format_name="png",
                        language=language,
                        model="JE-1000F",
                        region="US",
                    )
                    self.assertEqual(language, resolution.language)
                    self.assertEqual(
                        f"reviewed-promotion:{PROMOTION_ID}",
                        resolution.source,
                    )
                    self.assertTrue(
                        resolution.path.startswith(PROMOTED_DIR.as_posix() + "/")
                    )
                    self.assertEqual(64, len(resolution.declared_hash))

        report = check_registry(
            self.records,
            repo_root=ROOT,
            asset_keys=PROMOTED_ASSET_KEYS,
            publish=True,
        )
        self.assertEqual((), report.errors)

    def test_scoped_mapping_rejects_cross_target_and_missing_target_requests(self) -> None:
        requests = (
            ({"model": "JE-2000F", "region": "US", "language": "en"}, "model"),
            ({"model": "JE-1000F", "region": "EU", "language": "en"}, "region"),
            ({"model": "JE-1000F", "region": "US", "language": "de"}, "language"),
            ({"model": None, "region": "US", "language": "en"}, "model"),
            ({"model": "JE-1000F", "region": None, "language": "en"}, "region"),
            ({"model": "JE-1000F", "region": "US", "language": None}, "language"),
        )
        for kwargs, message in requests:
            with self.subTest(**kwargs):
                with self.assertRaisesRegex(AssetRegistryError, message):
                    resolve_asset(
                        self.records,
                        repo_root=ROOT,
                        asset_key=PROMOTED_ASSET_KEYS[0],
                        format_name="png",
                        **kwargs,
                    )

    def test_quarantined_candidates_and_qr_assets_do_not_gain_a_bypass(self) -> None:
        for asset_key in CANDIDATE_ASSET_KEYS:
            with self.subTest(asset_key=asset_key):
                with self.assertRaisesRegex(AssetRegistryError, "not registered"):
                    resolve_asset(
                        self.records,
                        repo_root=ROOT,
                        asset_key=asset_key,
                        format_name="png",
                        language="en",
                        model="JE-1000F",
                        region="US",
                    )

        for asset_key in ("qr/back_cover_reference_candidate",):
            with self.subTest(asset_key=asset_key):
                self.assertEqual(QUARANTINED_STATUS, self.by_key[asset_key].status)
                with self.assertRaisesRegex(AssetRegistryError, QUARANTINED_STATUS):
                    resolve_asset(
                        self.records,
                        repo_root=ROOT,
                        asset_key=asset_key,
                        format_name="png",
                        model="JE-1000F",
                        region="US",
                        allow_temporary=True,
                    )

        ai_qr = resolve_asset(
            self.records,
            repo_root=ROOT,
            asset_key="qr/back_cover_ai_candidate",
            format_name="png",
            model="JE-1000F",
            region="US",
        )
        self.assertEqual(
            "back_cover_qr_ai_candidate.png", Path(ai_qr.path).name,
        )

    def test_legacy_shared_app_composites_remain_byte_identical(self) -> None:
        self.assertEqual(
            "474b6e86398672ad0e36c08df860c09fe1645f96c95e80c9d68cc5549f012f4c",
            _sha256(ROOT / LEGACY_APP_DIR / "add_device.png"),
        )
        self.assertEqual(
            "01d3694dd833380066161364a6c67f5d26a088bfd4428b72d836c26e4f123a90",
            _sha256(ROOT / LEGACY_APP_DIR / "connect_result.png"),
        )

    def test_idml_and_raw_latex_use_the_same_unique_promoted_asset(self) -> None:
        with TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "bundle"
            page = bundle / "page" / "app_es.rst"
            page.parent.mkdir(parents=True)
            source = (
                ".. raw:: latex\n\n"
                "   \\HBAppAsset{add_device.png}{66mm}{57mm}\n\n"
                ".. image:: asset:app/add_device\n"
            )
            page.write_text(source, encoding="utf-8")
            usage = BundleAssetUsage(
                target=AssetTarget(model="JE-1000F", region="US", language="es"),
                repo_root=ROOT,
            )

            rewritten = rewrite_rst_asset_paths(
                source,
                source_path=page,
                target_path=page,
                bundle_dir=bundle,
                docs_dir=ROOT / "docs",
                repo_root=ROOT,
                asset_usage=usage,
                model="JE-1000F",
                region="US",
                language="es",
            )
            page.write_text(rewritten, encoding="utf-8")

            unique_name = "add_device_je1000f_us.png"
            staged_relative = PROMOTED_DIR / unique_name
            staged = bundle / "_assets" / staged_relative.relative_to("docs")
            self.assertIn(f"\\HBAppAsset{{{unique_name}}}", rewritten)
            self.assertIn(staged.relative_to(bundle).as_posix(), rewritten)
            self.assertTrue(staged.is_file())
            self.assertEqual(
                staged.resolve(),
                resolve_bundle_image(bundle, unique_name).resolve(),  # type: ignore[union-attr]
            )
            self.assertEqual(
                staged.resolve(),
                resolve_bundle_image(
                    bundle,
                    staged.relative_to(bundle).as_posix(),
                ).resolve(),  # type: ignore[union-attr]
            )

            latex_dir = Path(tmp) / "latex"
            latex_dir.mkdir()
            _copy_attachment_images_for_latex(bundle, latex_dir, lambda _message: None)
            self.assertEqual(staged.read_bytes(), (latex_dir / unique_name).read_bytes())

            usage.write(
                usage_manifest_path=bundle / "asset_usage_manifest.json",
                registry_snapshot_path=bundle / "asset_registry_snapshot.csv",
                bundle_dir=bundle,
            )
            manifest = json.loads(
                (bundle / "asset_usage_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                f"reviewed-promotion:{PROMOTION_ID}",
                manifest["assets"][0]["source"],
            )
            self.assertEqual(2, len(manifest["rewrites"]))
            restore_registry_asset_uris(
                source_bundle_dir=bundle,
                target_bundle_dir=bundle,
                strict=True,
            )
            restored = page.read_text(encoding="utf-8")
            self.assertIn("\\HBAppAsset{asset:app/add_device}", restored)
            self.assertIn(".. image:: asset:app/add_device", restored)

    def test_raw_latex_alias_does_not_leak_outside_reviewed_targets(self) -> None:
        source = "\\HBAppAsset{add_device.png}{66mm}{57mm}\n"
        targets = (
            AssetTarget(model="JE-1000F", region="JP", language="ja"),
            AssetTarget(model="JE-1000F", region="KR", language="ko"),
            # A reviewed region is still limited to its reviewed languages.
            AssetTarget(model="JE-1000F", region="US", language="de"),
            AssetTarget(model="JE-2000F", region="EU", language="de"),
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for index, target in enumerate(targets):
                with self.subTest(target=target):
                    bundle = root / str(index)
                    page = bundle / "page" / "app.rst"
                    page.parent.mkdir(parents=True)
                    page.write_text(source, encoding="utf-8")
                    usage = BundleAssetUsage(target=target, repo_root=ROOT)
                    rewritten = rewrite_rst_asset_paths(
                        source,
                        source_path=page,
                        target_path=page,
                        bundle_dir=bundle,
                        docs_dir=ROOT / "docs",
                        repo_root=ROOT,
                        asset_usage=usage,
                        model=target.model,
                        region=target.region,
                        language=target.language,
                    )
                    self.assertEqual(source, rewritten)
                    self.assertFalse((bundle / "_assets").exists())

    def test_contract_rejects_decision_scope_hash_and_whitelist_tampering(self) -> None:
        cases = (
            ("reviewer", lambda row: row["decision"].update(reviewer="Someone Else"), "reviewer"),
            ("timezone", lambda row: row["decision"].update(decided_at="2026-07-16T22:35:10"), "timezone"),
            ("decision time", lambda row: row["decision"].update(decided_at="2026-07-16T22:35:11-07:00"), "decision time"),
            ("scope", lambda row: row["scope"]["languages"].append("de"), "scope"),
            ("source", lambda row: row["bindings"]["source"].update(sha256="0" * 64), "source"),
            ("recipe", lambda row: row["bindings"]["recipe"].update(sha256="0" * 64), "recipe"),
            ("evidence", lambda row: row["bindings"]["evidence"].update(sha256="0" * 64), "evidence"),
            ("candidate hash", lambda row: row["candidate_assets"][0].update(sha256="0" * 64), "candidate"),
            ("output hash", lambda row: row["promoted_outputs"][0].update(sha256="0" * 64), "output"),
            (
                "extra QR candidate",
                lambda row: row["candidate_assets"].append(
                    {
                        "asset_key": "qr/back_cover_ai_candidate",
                        "path": "docs/renderers/latex/assets/back_cover_qr_ai_candidate.png",
                        "sha256": "0" * 64,
                    }
                ),
                "whitelist",
            ),
            (
                "extra output",
                lambda row: row["promoted_outputs"].append(
                    {
                        "asset_key": "qr/back_cover_reference_candidate",
                        "path": "docs/renderers/latex/assets/back_cover_qr_reference_candidate.png",
                        "sha256": "0" * 64,
                        "composition": {
                            "canvas_px": [1, 1],
                            "background": "#FFFFFF",
                            "placements": [],
                        },
                    }
                ),
                "output whitelist",
            ),
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _copy_promotion_inputs(root)
            contract_path = root / PROMOTION_RELATIVE_PATH
            baseline = json.loads(contract_path.read_text(encoding="utf-8"))
            for label, mutate, message in cases:
                with self.subTest(case=label):
                    payload = deepcopy(baseline)
                    mutate(payload)
                    contract_path.write_text(
                        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    with self.assertRaisesRegex(ReviewedPromotionError, message):
                        validate_reviewed_promotion(root, PROMOTION_ID)

    def test_contract_rejects_bound_file_drift(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _copy_promotion_inputs(root)
            drift_cases = (
                (RECIPE_RELATIVE_PATH, "recipe"),
                (EVIDENCE_RELATIVE_PATH, "evidence"),
                (CANDIDATE_DIR / "ai-p39-add-device-home.png", "candidate"),
                (PROMOTED_DIR / "add_device_je1000f_us.png", "output"),
            )
            for relative, message in drift_cases:
                with self.subTest(relative=relative.as_posix()):
                    path = root / relative
                    original = path.read_bytes()
                    path.write_bytes(original + b"drift")
                    try:
                        with self.assertRaisesRegex(ReviewedPromotionError, message):
                            validate_reviewed_promotion(root, PROMOTION_ID)
                    finally:
                        path.write_bytes(original)

    def test_contract_carrier_hash_is_immutable_even_for_json_equivalent_edits(self) -> None:
        self.assertEqual(
            PROMOTION_CONTRACT_SHA256,
            _sha256(ROOT / PROMOTION_RELATIVE_PATH),
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _copy_promotion_inputs(root)
            contract_path = root / PROMOTION_RELATIVE_PATH
            contract_path.write_text(
                contract_path.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ReviewedPromotionError, "SHA-256"):
                validate_reviewed_promotion(root, PROMOTION_ID)

    def test_registry_binding_must_match_the_reviewed_contract_exactly(self) -> None:
        record = self.by_key[PROMOTED_ASSET_KEYS[0]]
        cases = (
            (replace(record, model_scope=("ALL",)), "model scope"),
            (replace(record, region_scope=("ALL",)), "region scope"),
            (replace(record, override_for=None), "override target"),
            (replace(record, language_dimension="中立"), "language dimension"),
            (replace(record, language_variants=("en", "fr", "es", "de")), "language variants"),
            (replace(record, export_root=LEGACY_APP_DIR), "export root"),
            (replace(record, hashes=(("png", "0" * 64),)), "registry hash"),
            (replace(record, notes="reviewed-promotion=another-id"), "promotion marker"),
        )
        for mutated, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ReviewedPromotionError, message):
                    validate_reviewed_promotion(
                        ROOT,
                        PROMOTION_ID,
                        registry_record=mutated,
                    )


class TestJe1000fEuAppUiReviewedPromotion(unittest.TestCase):
    """The EU contract: the EU print's own English App screens for JE-1000F/EU."""

    def setUp(self) -> None:
        self.records = load_registry(ROOT / "data" / "asset_registry.csv")
        self.by_key = {record.asset_key: record for record in self.records}

    def test_shared_keys_resolve_to_each_target_region_own_screens(self) -> None:
        expectations = (
            ("EU", EU_LANGUAGES, f"reviewed-promotion:{EU_PROMOTION_ID}", EU_PROMOTED_DIR),
            ("US", ("en", "fr", "es"), f"reviewed-promotion:{PROMOTION_ID}", PROMOTED_DIR),
        )
        for shared_key in ("app/add_device", "app/connect_result"):
            for region, languages, source, directory in expectations:
                for language in languages:
                    with self.subTest(asset_key=shared_key, region=region, language=language):
                        resolution = resolve_asset(
                            self.records,
                            repo_root=ROOT,
                            asset_key=shared_key,
                            format_name="png",
                            language=language,
                            model="JE-1000F",
                            region=region,
                        )
                        self.assertEqual(source, resolution.source)
                        self.assertEqual(directory.as_posix(), Path(resolution.path).parent.as_posix())
            with self.subTest(asset_key=shared_key, region="JP"):
                jp = resolve_asset(
                    self.records,
                    repo_root=ROOT,
                    asset_key=shared_key,
                    format_name="png",
                    language="ja",
                    model="JE-1000F",
                    region="JP",
                )
                self.assertEqual(LEGACY_APP_DIR.as_posix(), Path(jp.path).parent.as_posix())

        report = check_registry(
            self.records,
            repo_root=ROOT,
            asset_keys=EU_PROMOTION.promoted_asset_keys,
            publish=True,
        )
        self.assertEqual((), report.errors)

    def test_exports_are_the_confirmed_print_crops_byte_for_byte(self) -> None:
        for candidate, output in zip(EU_PROMOTION.candidates, EU_PROMOTION.outputs, strict=True):
            with self.subTest(asset_key=output.asset_key):
                self.assertEqual(candidate.sha256, output.sha256)
                self.assertEqual(
                    (ROOT / candidate.path).read_bytes(), (ROOT / output.path).read_bytes()
                )
                self.assertEqual(
                    ((candidate.asset_key, (0, 0), (0, 0) + candidate.dimensions_px),),
                    tuple(
                        (item.candidate_asset_key, item.xy_px, item.source_rect_px)
                        for item in output.placements
                    ),
                )

    def test_raw_latex_alias_and_image_uri_use_the_eu_screens(self) -> None:
        source = (
            ".. raw:: latex\n\n"
            "   \\HBAppAsset{connect_result.png}{78mm}{50mm}\n\n"
            ".. image:: asset:app/connect_result\n"
        )
        for language in ("de", "uk"):
            with self.subTest(language=language), TemporaryDirectory() as tmp:
                bundle = Path(tmp) / "bundle"
                rewritten, usage = _rewrite_app_page(
                    bundle, source, AssetTarget(model="JE-1000F", region="EU", language=language)
                )
                unique_name = "connect_result_je1000f_eu.png"
                staged = bundle / "_assets" / (EU_PROMOTED_DIR / unique_name).relative_to("docs")
                self.assertIn(f"\\HBAppAsset{{{unique_name}}}", rewritten)
                self.assertIn(staged.relative_to(bundle).as_posix(), rewritten)
                self.assertEqual((ROOT / EU_PROMOTED_DIR / unique_name).read_bytes(), staged.read_bytes())
                self.assertNotIn("je1000f_us", rewritten)

    def test_candidates_stay_quarantined_evidence(self) -> None:
        for asset_key in EU_PROMOTION.candidate_asset_keys:
            with self.subTest(asset_key=asset_key):
                with self.assertRaisesRegex(AssetRegistryError, "not registered"):
                    resolve_asset(
                        self.records,
                        repo_root=ROOT,
                        asset_key=asset_key,
                        format_name="png",
                        language="en",
                        model="JE-1000F",
                        region="EU",
                    )

    def test_contracts_do_not_cross(self) -> None:
        self.assertIs(EU_PROMOTION, promotion_for_asset("app/je1000f_eu/add_device"))
        self.assertIsNone(promotion_for_asset("app/add_device"))
        us_record = self.by_key[PROMOTED_ASSET_KEYS[0]]
        eu_record = self.by_key["app/je1000f_eu/add_device"]
        for record, promotion_id in ((us_record, EU_PROMOTION_ID), (eu_record, PROMOTION_ID)):
            with self.subTest(asset_key=record.asset_key, promotion_id=promotion_id):
                with self.assertRaisesRegex(ReviewedPromotionError, "outside the promoted output whitelist"):
                    validate_reviewed_promotion(ROOT, promotion_id, registry_record=record)

    def test_contract_rejects_decision_scope_hash_and_whitelist_tampering(self) -> None:
        cases = (
            ("reviewer", lambda row: row["decision"].update(reviewer="Someone Else"), "reviewer"),
            ("decision time", lambda row: row["decision"].update(decided_at="2026-09-24T06:18:01-07:00"), "decision time"),
            ("scope", lambda row: row["scope"]["languages"].append("pl"), "scope"),
            ("region", lambda row: row["scope"].update(regions=["US"]), "scope"),
            ("source", lambda row: row["bindings"]["source"].update(sha256="0" * 64), "source"),
            ("recipe", lambda row: row["bindings"]["recipe"].update(sha256="0" * 64), "recipe"),
            ("evidence", lambda row: row["bindings"]["evidence"].update(sha256="0" * 64), "evidence"),
            ("candidate hash", lambda row: row["candidate_assets"][0].update(sha256="0" * 64), "candidate"),
            ("output hash", lambda row: row["promoted_outputs"][0].update(sha256="0" * 64), "output"),
            ("extra output", lambda row: row["promoted_outputs"].append(deepcopy(row["promoted_outputs"][0])), "output whitelist"),
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _copy_eu_promotion_inputs(root)
            contract_path = root / EU_PROMOTION.contract_path
            baseline = json.loads(contract_path.read_text(encoding="utf-8"))
            self.assertEqual(EU_PROMOTION_ID, validate_reviewed_promotion(root, EU_PROMOTION_ID))
            for label, mutate, message in cases:
                with self.subTest(case=label):
                    payload = deepcopy(baseline)
                    mutate(payload)
                    contract_path.write_text(
                        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    with self.assertRaisesRegex(ReviewedPromotionError, message):
                        validate_reviewed_promotion(root, EU_PROMOTION_ID)
            contract_path.write_text(
                json.dumps(baseline, ensure_ascii=False, indent=2) + "\n\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ReviewedPromotionError, "SHA-256"):
                validate_reviewed_promotion(root, EU_PROMOTION_ID)

    def test_registry_binding_must_match_the_reviewed_contract_exactly(self) -> None:
        record = self.by_key["app/je1000f_eu/connect_result"]
        cases = (
            (replace(record, region_scope=("US",)), "region scope"),
            (replace(record, override_for="app/add_device"), "override target"),
            (replace(record, language_variants=("en", "fr", "es", "de", "it")), "language variants"),
            (replace(record, export_root=PROMOTED_DIR), "export root"),
            (replace(record, hashes=(("png", "0" * 64),)), "registry hash"),
            (replace(record, notes=f"reviewed-promotion={PROMOTION_ID}"), "promotion marker"),
        )
        self.assertEqual(
            EU_PROMOTION_ID, validate_reviewed_promotion(ROOT, EU_PROMOTION_ID, registry_record=record)
        )
        for mutated, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ReviewedPromotionError, message):
                    validate_reviewed_promotion(ROOT, EU_PROMOTION_ID, registry_record=mutated)


if __name__ == "__main__":
    unittest.main()
