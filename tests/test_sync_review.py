from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.review_support import SyncPlanEntry
from tools.sync_review import (
    remap_sync_plan_for_review_dir,
    resolve_review_dir_for_sync,
    resolve_sync_plan,
    resolve_sync_relative_paths,
)


class TestSyncReview(unittest.TestCase):
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

            self.assertEqual(Path("page") / "p20_01_fcc.rst", remapped[0].relative_path)
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

            self.assertEqual(Path("page") / "p18_02_whats_in_the_box.rst", remapped[0].relative_path)
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
            self.assertEqual(Path("page") / "p18_02_whats_in_the_box.rst", remapped[0].relative_path)
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
                    {"type": "csv_page", "source": "phase1", "page": "spec", "langs": ["en"], "include_dir": "generated/{model}"},
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
                    {"type": "csv_page", "source": "phase1", "page": "spec", "langs": ["ja"], "include_dir": "generated/{model}"},
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
                    {"type": "csv_page", "source": "phase1", "page": "spec", "langs": ["en"], "include_dir": "generated/{model}"},
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
