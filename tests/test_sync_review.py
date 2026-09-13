from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools import sync_review
from tools.review_support import SyncPlanEntry
from tools.sync_review import (
    remap_sync_plan_for_review_dir,
    resolve_runtime_bundle_for_sync,
    resolve_review_dir_for_sync,
    resolve_sync_plan,
    resolve_sync_relative_paths,
)


class TestSyncReview(unittest.TestCase):
    def _projection_fixture(self, root: Path) -> tuple[Path, Path]:
        canonical = root / "rst"
        source = root / "web" / "source" / "rst"
        (canonical / "page").mkdir(parents=True)
        (source / "page").mkdir(parents=True)
        source_index = source / "index.rst"
        source_page = source / "page" / "00_preface.rst"
        source_index.write_text(".. include:: page/00_preface.rst\n", encoding="utf-8")
        source_page.write_text("Full runtime preface.\n", encoding="utf-8")
        (canonical / "bundle_manifest.json").write_text(
            json.dumps(
                {
                    "schema_version": "web-language-bundle/v1",
                    "source_index_sha256": hashlib.sha256(
                        source_index.read_bytes()
                    ).hexdigest(),
                    "source_pages": [
                        {
                            "path": "page/00_preface.rst",
                            "sha256": hashlib.sha256(
                                source_page.read_bytes()
                            ).hexdigest(),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return canonical, source

    def test_runtime_bundle_resolver_should_keep_regular_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / "rst"
            runtime.mkdir()
            (runtime / "bundle_manifest.json").write_text(
                '{"schema_version": 2}\n', encoding="utf-8"
            )

            self.assertEqual(runtime, resolve_runtime_bundle_for_sync(runtime))

    def test_runtime_bundle_resolver_should_verify_and_select_full_web_source(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            canonical, source = self._projection_fixture(Path(td))

            self.assertEqual(source, resolve_runtime_bundle_for_sync(canonical))

    def test_runtime_bundle_resolver_should_reject_missing_or_drifted_source(self) -> None:
        for case in ("source", "index", "index_hash", "page_hash"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as td:
                canonical, source = self._projection_fixture(Path(td))
                if case == "source":
                    source.rename(source.with_name("missing"))
                elif case == "index":
                    (source / "index.rst").unlink()
                elif case == "index_hash":
                    (source / "index.rst").write_text("stale index\n", encoding="utf-8")
                else:
                    (source / "page" / "00_preface.rst").write_text(
                        "stale page\n", encoding="utf-8"
                    )

                with self.assertRaisesRegex(RuntimeError, "missing|hash mismatch"):
                    resolve_runtime_bundle_for_sync(canonical)

    def test_runtime_bundle_resolver_should_reject_projection_or_source_symlinks(self) -> None:
        for case in ("projection_directory", "projection_manifest", "source_directory", "source_file"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                canonical, source = self._projection_fixture(root)
                if case == "projection_directory":
                    real_canonical = root / "real-canonical"
                    canonical.rename(real_canonical)
                    canonical.symlink_to(real_canonical, target_is_directory=True)
                elif case == "projection_manifest":
                    manifest = canonical / "bundle_manifest.json"
                    target = root / "linked-manifest.json"
                    manifest.rename(target)
                    manifest.symlink_to(target)
                elif case == "source_directory":
                    real_source = root / "real-source"
                    source.rename(real_source)
                    source.symlink_to(real_source, target_is_directory=True)
                else:
                    target = root / "linked-page.rst"
                    page = source / "page" / "00_preface.rst"
                    page.rename(target)
                    page.symlink_to(target)

                with self.assertRaisesRegex(RuntimeError, "symbolic link"):
                    resolve_runtime_bundle_for_sync(canonical)

    def test_main_should_sync_from_verified_full_web_source(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_build_dir = root / "docs" / "_build"
            build_root = docs_build_dir / "MODEL" / "EU" / "en"
            canonical, source = self._projection_fixture(build_root)
            generated = source / "generated" / "MODEL" / "fresh.rst"
            generated.parent.mkdir(parents=True)
            generated.write_text("fresh runtime params\n", encoding="utf-8")
            review = root / "docs" / "_review" / "MODEL" / "EU"
            (review / "page").mkdir(parents=True)
            (review / "index.rst").write_text("review index\n", encoding="utf-8")
            config = root / "config.yaml"
            config.write_text("build:\n  languages: [en]\n", encoding="utf-8")
            cfg = {
                "build": {"languages": ["en"]},
                "pages": [
                    {
                        "type": "rst_include",
                        "lang": "en",
                        "file": "templates/plain.rst",
                    }
                ],
            }
            target = SimpleNamespace(model="MODEL", region="EU", lang="en")

            with mock.patch.object(sync_review, "load_config", return_value=cfg), mock.patch.object(
                sync_review, "resolve_docs_dir", return_value=root / "docs"
            ), mock.patch.object(
                sync_review, "resolve_build_targets", return_value=[target]
            ), mock.patch.object(
                sync_review, "resolve_review_dir_for_sync", return_value=review
            ), mock.patch.object(
                sync_review, "restore_registry_asset_uris", return_value=0
            ):
                result = sync_review.main(
                    [
                        "--config",
                        str(config),
                        "--model",
                        "MODEL",
                        "--region",
                        "EU",
                        "--lang",
                        "en",
                        "--docs-build-dir",
                        str(docs_build_dir),
                    ]
                )

            self.assertEqual(0, result)
            self.assertEqual(
                "fresh runtime params\n",
                (review / "generated" / "MODEL" / "fresh.rst").read_text(
                    encoding="utf-8"
                ),
            )
            self.assertEqual(source, resolve_runtime_bundle_for_sync(canonical))

    def test_resolve_review_dir_for_sync_should_keep_shared_us_review_dir_for_secondary_language(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            shared_review_dir = docs_dir / "_review" / "JE-1000F" / "US"
            (shared_review_dir / "page").mkdir(parents=True)
            (shared_review_dir / "index.rst").write_text("shared review index\n", encoding="utf-8")

            resolved = resolve_review_dir_for_sync(
                docs_dir=docs_dir,
                model="JE-1000F",
                region="US",
                lang="es",
            )

            self.assertEqual(shared_review_dir, resolved)

    def test_resolve_review_dir_for_sync_should_keep_primary_us_language_on_shared_review_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            shared_review_dir = docs_dir / "_review" / "JE-1000F" / "US"
            (shared_review_dir / "page").mkdir(parents=True)
            (shared_review_dir / "index.rst").write_text("shared review index\n", encoding="utf-8")

            resolved = resolve_review_dir_for_sync(
                docs_dir=docs_dir,
                model="JE-1000F",
                region="US",
                lang="en",
            )

            self.assertEqual(shared_review_dir, resolved)

    def test_remap_sync_plan_for_review_dir_should_map_shared_us_review_pages_by_language(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US"
            (review_dir / "page").mkdir(parents=True)
            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            (review_dir / "manifest.json").write_text(
                '{\n  "lang": null,\n  "page_manifest": "docs/manifests/manual_us.yaml"\n}\n',
                encoding="utf-8",
            )

            remapped = remap_sync_plan_for_review_dir(
                (
                    SyncPlanEntry(relative_path=Path("page") / "01_fcc.rst"),
                    SyncPlanEntry(relative_path=Path("generated") / "JE-1000F" / "spec_fr.rst"),
                ),
                docs_dir=docs_dir,
                review_dir=review_dir,
                model="JE-1000F",
                region="US",
                lang="fr",
            )

            self.assertEqual(Path("page") / "p22_01_fcc.rst", remapped[0].relative_path)
            self.assertEqual(Path("page") / "01_fcc.rst", remapped[0].source_relative_path)
            self.assertEqual(Path("generated") / "JE-1000F" / "spec_fr.rst", remapped[1].relative_path)
            self.assertEqual(Path("generated") / "JE-1000F" / "spec_fr.rst", remapped[1].source_relative_path)

    def test_remap_sync_plan_for_review_dir_should_map_shared_eu_review_pages_by_language(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            review_dir = docs_dir / "_review" / "JE-1000F" / "EU"
            (review_dir / "page").mkdir(parents=True)
            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            (review_dir / "manifest.json").write_text(
                '{\n  "lang": null,\n  "page_manifest": "docs/manifests/manual_eu.yaml"\n}\n',
                encoding="utf-8",
            )

            remapped = remap_sync_plan_for_review_dir(
                (
                    SyncPlanEntry(relative_path=Path("page") / "02_whats_in_the_box.rst"),
                    SyncPlanEntry(relative_path=Path("generated") / "JE-1000F" / "spec_fr.rst"),
                ),
                docs_dir=docs_dir,
                review_dir=review_dir,
                model="JE-1000F",
                region="EU",
                lang="fr",
            )

            self.assertEqual(Path("page") / "p20_02_whats_in_the_box.rst", remapped[0].relative_path)
            self.assertEqual(Path("page") / "02_whats_in_the_box.rst", remapped[0].source_relative_path)
            self.assertEqual(Path("generated") / "JE-1000F" / "spec_fr.rst", remapped[1].relative_path)
            self.assertEqual(Path("generated") / "JE-1000F" / "spec_fr.rst", remapped[1].source_relative_path)

    def test_remap_sync_plan_for_review_dir_should_skip_unmapped_shared_eu_pages(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            review_dir = docs_dir / "_review" / "JE-1000F" / "EU"
            (review_dir / "page").mkdir(parents=True)
            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            (review_dir / "manifest.json").write_text(
                '{\n  "lang": null,\n  "page_manifest": "docs/manifests/manual_eu.yaml"\n}\n',
                encoding="utf-8",
            )

            remapped = remap_sync_plan_for_review_dir(
                (
                    SyncPlanEntry(relative_path=Path("page") / "00_preface.rst"),
                    SyncPlanEntry(relative_path=Path("page") / "02_whats_in_the_box.rst"),
                ),
                docs_dir=docs_dir,
                review_dir=review_dir,
                model="JE-1000F",
                region="EU",
                lang="fr",
            )

            self.assertEqual(1, len(remapped))
            self.assertEqual(Path("page") / "p20_02_whats_in_the_box.rst", remapped[0].relative_path)
            self.assertEqual(Path("page") / "02_whats_in_the_box.rst", remapped[0].source_relative_path)

    def test_resolve_sync_plan_should_mark_placeholder_backed_pages_for_param_merge(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            (runtime_dir / "generated" / "JE-1000F").mkdir(parents=True)
            (runtime_dir / "generated" / "JE-1000F" / "spec_en.rst").write_text("spec\n", encoding="utf-8")

            templates_dir = docs_dir / "templates" / "page_us-en"
            templates_dir.mkdir(parents=True)
            (templates_dir / "plain.rst").write_text("No placeholders\n", encoding="utf-8")
            (templates_dir / "product.rst").write_text("|PRODUCT_NAME_BOLD|\n", encoding="utf-8")

            cfg = {
                "build": {"languages": ["en"]},
                "pages": [
                    {"type": "rst_include", "lang": "en", "file": "templates/page_us-en/plain.rst"},
                    {"type": "rst_include", "lang": "en", "file": "templates/page_us-en/product.rst"},
                    {"type": "csv_page", "source": "phase2", "page": "spec", "langs": ["en"], "include_dir": "generated/{model}"},
                ],
            }

            sync_plan = resolve_sync_plan(
                cfg=cfg,
                docs_dir=docs_dir,
                runtime_bundle_dir=runtime_dir,
                model="JE-1000F",
                region="US",
                scope="params",
                page_files=(),
            )
            plan_by_path = {entry.relative_path: entry for entry in sync_plan}

            self.assertEqual("copy", plan_by_path[Path("generated") / "JE-1000F" / "spec_en.rst"].mode)
            self.assertEqual("copy", plan_by_path[Path("page") / "spec_en.rst"].mode)
            self.assertEqual("merge_params", plan_by_path[Path("page") / "product.rst"].mode)
            self.assertEqual(templates_dir / "product.rst", plan_by_path[Path("page") / "product.rst"].template_path)
            self.assertNotIn(Path("page") / "plain.rst", plan_by_path)

    def test_resolve_sync_relative_paths_should_include_all_placeholder_backed_pages(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "JP" / "rst"
            (runtime_dir / "generated" / "JE-1000F").mkdir(parents=True)
            (runtime_dir / "generated" / "JE-1000F" / "spec_ja.rst").write_text("spec\n", encoding="utf-8")
            (runtime_dir / "page").mkdir(parents=True)

            templates_dir = docs_dir / "templates" / "page_jp"
            templates_dir.mkdir(parents=True)
            (templates_dir / "plain.rst").write_text("No placeholders\n", encoding="utf-8")
            (templates_dir / "product.rst").write_text("|PRODUCT_NAME|\n", encoding="utf-8")
            (templates_dir / "ups.rst").write_text("UPS |UPS_BYPASS_OUTPUT_TEXT|\n", encoding="utf-8")

            cfg = {
                "build": {"languages": ["ja"]},
                "pages": [
                    {"type": "rst_include", "lang": "ja", "file": "templates/page_jp/plain.rst"},
                    {"type": "rst_include", "lang": "ja", "file": "templates/page_jp/product.rst"},
                    {"type": "rst_include", "lang": "ja", "file": "templates/page_jp/ups.rst"},
                    {"type": "csv_page", "source": "phase2", "page": "spec", "langs": ["ja"], "include_dir": "generated/{model}"},
                ],
            }

            relative_paths = resolve_sync_relative_paths(
                cfg=cfg,
                docs_dir=docs_dir,
                runtime_bundle_dir=runtime_dir,
                model="JE-1000F",
                region="JP",
                scope="params",
                page_files=(),
            )

            self.assertIn(Path("generated") / "JE-1000F" / "spec_ja.rst", relative_paths)
            self.assertIn(Path("page") / "product.rst", relative_paths)
            self.assertIn(Path("page") / "ups.rst", relative_paths)
            self.assertIn(Path("page") / "spec_ja.rst", relative_paths)
            self.assertNotIn(Path("page") / "plain.rst", relative_paths)

    def test_resolve_sync_plan_should_let_explicit_page_file_force_full_copy(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            runtime_dir.mkdir(parents=True)

            templates_dir = docs_dir / "templates" / "page_us-en"
            templates_dir.mkdir(parents=True)
            (templates_dir / "box.rst").write_text("|PRODUCT_NAME_BOLD|\n", encoding="utf-8")

            cfg = {
                "build": {"languages": ["en"]},
                "pages": [{"type": "rst_include", "lang": "en", "file": "templates/page_us-en/box.rst"}],
            }

            sync_plan = resolve_sync_plan(
                cfg=cfg,
                docs_dir=docs_dir,
                runtime_bundle_dir=runtime_dir,
                model="JE-1000F",
                region="US",
                scope="params",
                page_files=("box.rst",),
            )
            plan_by_path = {entry.relative_path: entry for entry in sync_plan}

            self.assertEqual("copy", plan_by_path[Path("page") / "box.rst"].mode)

    def test_resolve_sync_plan_should_mark_generated_pages_for_param_merge(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            runtime_dir.mkdir(parents=True)

            templates_dir = docs_dir / "templates" / "page_us-en"
            templates_dir.mkdir(parents=True)
            (templates_dir / "03_product_overview_placeholder.rst").write_text(
                "|FRONT_USB_C_LOW_SPEC|\n",
                encoding="utf-8",
            )

            cfg = {
                "build": {"languages": ["en"]},
                "pages": [
                    {
                        "type": "generated_page",
                        "page": "03_product_overview",
                        "engine": "draft_v1",
                        "recipe": "templates/recipes/us-en/03_product_overview.yaml",
                        "template": "templates/page_us-en/03_product_overview_placeholder.rst",
                        "langs": ["en"],
                        "include_dir": "generated/{model}/draft",
                    }
                ],
            }

            sync_plan = resolve_sync_plan(
                cfg=cfg,
                docs_dir=docs_dir,
                runtime_bundle_dir=runtime_dir,
                model="JE-1000F",
                region="US",
                scope="params",
                page_files=(),
            )
            plan_by_path = {entry.relative_path: entry for entry in sync_plan}

            self.assertEqual("merge_params", plan_by_path[Path("page") / "03_product_overview_placeholder.rst"].mode)
            self.assertEqual(
                templates_dir / "03_product_overview_placeholder.rst",
                plan_by_path[Path("page") / "03_product_overview_placeholder.rst"].template_path,
            )

    def test_resolve_sync_relative_paths_should_support_generated_only_scope(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            (runtime_dir / "generated" / "JE-1000F").mkdir(parents=True)
            (runtime_dir / "generated" / "JE-1000F" / "spec_en.rst").write_text("spec\n", encoding="utf-8")

            cfg = {
                "build": {"languages": ["en"]},
                "pages": [
                    {"type": "rst_include", "lang": "en", "file": "templates/page_us-en/00_preface.rst"},
                    {"type": "csv_page", "source": "phase2", "page": "spec", "langs": ["en"], "include_dir": "generated/{model}"},
                ],
            }

            relative_paths = resolve_sync_relative_paths(
                cfg=cfg,
                docs_dir=docs_dir,
                runtime_bundle_dir=runtime_dir,
                model="JE-1000F",
                region="US",
                scope="generated",
                page_files=(),
            )

            self.assertIn(Path("generated") / "JE-1000F" / "spec_en.rst", relative_paths)
            self.assertIn(Path("page") / "spec_en.rst", relative_paths)
            self.assertNotIn(Path("page") / "00_preface.rst", relative_paths)


if __name__ == "__main__":
    unittest.main()


class TestSyncRestoresSemanticAssetUris(unittest.TestCase):
    """The data-refresh path must not launder asset: URIs into bare paths.

    review_bundle.py restores semantic URIs when seeding docs/_review from a
    finalized runtime bundle; sync_review copies from the same finalized
    bundle, so it needs the same restore step (wired in sync_review.main).
    These tests pin the exact contract that wiring relies on.
    """

    @staticmethod
    def _runtime_bundle(root: Path, *, rewrites) -> Path:
        import json

        bundle = root / "bundle"
        bundle.mkdir(parents=True)
        (bundle / "asset_usage_manifest.json").write_text(
            json.dumps({"schema_version": 2, "assets": [], "rewrites": rewrites}),
            encoding="utf-8",
        )
        return bundle

    def test_copied_finalized_page_gets_its_asset_uri_back(self) -> None:
        from tools.asset_rewrites import restore_registry_asset_uris

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = self._runtime_bundle(root, rewrites=[{
                "asset_key": "operation/main_power",
                "original_value": "asset:operation/main_power",
                "rendered_value": "renderers/latex/assets/op_main_power.png",
                "reference_kind": "registry-uri",
                "reference_path": "generated/JE-1000F/draft/05_operation_guide_en.rst",
                "staged_path": "renderers/latex/assets/op_main_power.png",
                "ordinal": 1,
            }])
            review = root / "review"
            page = review / "generated" / "JE-1000F" / "draft" / "05_operation_guide_en.rst"
            page.parent.mkdir(parents=True)
            page.write_text(
                ".. image:: renderers/latex/assets/op_main_power.png\n",
                encoding="utf-8",
            )

            restored = restore_registry_asset_uris(
                source_bundle_dir=bundle, target_bundle_dir=review, strict=False)

            self.assertEqual(1, restored)
            self.assertEqual(
                ".. image:: asset:operation/main_power\n",
                page.read_text(encoding="utf-8"),
            )

    def test_legacy_path_rows_are_left_alone(self) -> None:
        """A bare path with no semantic provenance must stay a bare path."""
        from tools.asset_rewrites import restore_registry_asset_uris

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = self._runtime_bundle(root, rewrites=[{
                "asset_key": None,
                "original_value": "renderers/latex/assets/op_energy_saving.png",
                "rendered_value": "renderers/latex/assets/op_energy_saving.png",
                "reference_kind": "legacy-path",
                "reference_path": "generated/JE-1000F/draft/05_operation_guide_en.rst",
                "ordinal": 1,
            }])
            review = root / "review"
            page = review / "generated" / "JE-1000F" / "draft" / "05_operation_guide_en.rst"
            page.parent.mkdir(parents=True)
            original = ".. image:: renderers/latex/assets/op_energy_saving.png\n"
            page.write_text(original, encoding="utf-8")

            restored = restore_registry_asset_uris(
                source_bundle_dir=bundle, target_bundle_dir=review, strict=False)

            self.assertEqual(0, restored)
            self.assertEqual(original, page.read_text(encoding="utf-8"))

    def test_feishu_attachment_rows_are_left_alone(self) -> None:
        """Attachment attribution is manifest-side only; RST paths stay paths."""
        from tools.asset_rewrites import restore_registry_asset_uris

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            token = "_repo_assets/data/phase2/_attachments/lcd_icons/1_Wi-Fi_tok.png"
            bundle = self._runtime_bundle(root, rewrites=[{
                "asset_key": "feishu/lcd_icons_attachments",
                "original_value": token,
                "rendered_value": token,
                "reference_kind": "feishu-attachment",
                "reference_path": "generated/JE-1000F/lcd_icons_en.rst",
                "ordinal": 1,
            }])
            review = root / "review"
            page = review / "generated" / "JE-1000F" / "lcd_icons_en.rst"
            page.parent.mkdir(parents=True)
            original = f".. image:: {token}\n"
            page.write_text(original, encoding="utf-8")

            restored = restore_registry_asset_uris(
                source_bundle_dir=bundle, target_bundle_dir=review, strict=False)

            self.assertEqual(0, restored)
            self.assertEqual(original, page.read_text(encoding="utf-8"))

    def test_partial_sync_is_tolerated_without_strict(self) -> None:
        """sync copies a planned subset; uncopied references must not fail."""
        from tools.asset_rewrites import restore_registry_asset_uris

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = self._runtime_bundle(root, rewrites=[{
                "asset_key": "app/download",
                "original_value": "asset:app/download",
                "rendered_value": "x/download.png",
                "reference_kind": "registry-uri",
                "reference_path": "generated/JE-1000F/draft/12_app_setup_en.rst",
                "ordinal": 1,
            }])
            review = root / "review"
            review.mkdir()

            restored = restore_registry_asset_uris(
                source_bundle_dir=bundle, target_bundle_dir=review, strict=False)

            self.assertEqual(0, restored)
