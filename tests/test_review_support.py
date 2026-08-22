from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.review_support import (
    SyncPlanEntry,
    overlay_review_content_onto_bundle,
    overlay_review_onto_bundle,
    resolve_existing_review_bundle_dir,
    review_bundle_exists,
    review_content_exists,
    sync_review_from_runtime,
    sync_review_paths,
)


class TestReviewSupport(unittest.TestCase):
    def test_overlay_review_onto_bundle_should_reject_page_symlink_before_modifying_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US"

            (bundle_dir / "page").mkdir(parents=True)
            (bundle_dir / "index.rst").write_text("runtime index\n", encoding="utf-8")
            (bundle_dir / "page" / "runtime.rst").write_text("runtime page\n", encoding="utf-8")

            (review_dir / "page").mkdir(parents=True)
            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            outside_page = root / "outside-page.rst"
            outside_page.write_text("outside review page\n", encoding="utf-8")
            (review_dir / "page" / "escaped.rst").symlink_to(outside_page)

            before_paths = tuple(sorted(path.relative_to(bundle_dir) for path in bundle_dir.rglob("*")))
            before_files = {
                path.relative_to(bundle_dir): path.read_bytes()
                for path in bundle_dir.rglob("*")
                if path.is_file()
            }

            with self.assertRaisesRegex(RuntimeError, "review bundle must not contain symbolic links"):
                overlay_review_onto_bundle(
                    bundle_dir=bundle_dir,
                    docs_dir=docs_dir,
                    model="JE-1000F",
                    region="US",
                )

            self.assertEqual(before_paths, tuple(sorted(path.relative_to(bundle_dir) for path in bundle_dir.rglob("*"))))
            self.assertEqual(
                before_files,
                {
                    path.relative_to(bundle_dir): path.read_bytes()
                    for path in bundle_dir.rglob("*")
                    if path.is_file()
                },
            )

    def test_overlay_review_onto_bundle_should_reject_symlinked_override_assets_directory(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US"

            (bundle_dir / "page").mkdir(parents=True)
            (bundle_dir / "index.rst").write_text("runtime index\n", encoding="utf-8")
            (bundle_dir / "page" / "runtime.rst").write_text("runtime page\n", encoding="utf-8")

            (review_dir / "page").mkdir(parents=True)
            (review_dir / "overrides").mkdir()
            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            (review_dir / "page" / "review.rst").write_text("review page\n", encoding="utf-8")
            outside_assets = root / "outside-assets"
            outside_assets.mkdir()
            (outside_assets / "managed.png").write_bytes(b"external asset")
            (review_dir / "overrides" / "_assets").symlink_to(outside_assets, target_is_directory=True)

            with self.assertRaisesRegex(RuntimeError, "review bundle must not contain symbolic links"):
                overlay_review_onto_bundle(
                    bundle_dir=bundle_dir,
                    docs_dir=docs_dir,
                    model="JE-1000F",
                    region="US",
                )

            self.assertEqual("runtime index\n", (bundle_dir / "index.rst").read_text(encoding="utf-8"))
            self.assertEqual("runtime page\n", (bundle_dir / "page" / "runtime.rst").read_text(encoding="utf-8"))
            self.assertFalse((bundle_dir / "page" / "review.rst").exists())
            self.assertFalse((bundle_dir / "_assets").exists())

    def test_overlay_review_onto_bundle_should_merge_review_pages_and_keep_runtime_only_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "JP" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "JP"

            (bundle_dir / "page").mkdir(parents=True)
            (bundle_dir / "generated" / "JE-1000F").mkdir(parents=True)
            (bundle_dir / "_assets" / "templates" / "word_template" / "common_assets").mkdir(parents=True)
            (bundle_dir / "index.rst").write_text("runtime index\n", encoding="utf-8")
            (bundle_dir / "page" / "spec_ja.rst").write_text("runtime page\n", encoding="utf-8")
            (bundle_dir / "page" / "cover.rst").write_text("runtime cover\n", encoding="utf-8")
            (bundle_dir / "generated" / "JE-1000F" / "spec_ja.rst").write_text("runtime generated\n", encoding="utf-8")
            (bundle_dir / "generated" / "JE-1000F" / "safety_ja.rst").write_text("runtime safety\n", encoding="utf-8")

            (review_dir / "page").mkdir(parents=True)
            (review_dir / "generated" / "JE-1000F").mkdir(parents=True)
            (review_dir / "overrides" / "_assets" / "templates" / "word_template" / "common_assets").mkdir(parents=True)
            (review_dir / "overrides" / "_static").mkdir(parents=True)
            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            (review_dir / "page" / "spec_ja.rst").write_text("review page\n", encoding="utf-8")
            (review_dir / "generated" / "JE-1000F" / "spec_ja.rst").write_text("review generated\n", encoding="utf-8")
            (review_dir / "overrides" / "README.md").write_text("metadata\n", encoding="utf-8")
            (review_dir / "overrides" / "_assets" / "templates" / "word_template" / "common_assets" / "slot.jpg").write_text(
                "override asset\n",
                encoding="utf-8",
            )
            (review_dir / "overrides" / "_static" / "replacement.css").write_text("body {}\n", encoding="utf-8")

            overlay_review_onto_bundle(
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
                model="JE-1000F",
                region="JP",
            )

            self.assertEqual("review index\n", (bundle_dir / "index.rst").read_text(encoding="utf-8"))
            self.assertEqual("review page\n", (bundle_dir / "page" / "spec_ja.rst").read_text(encoding="utf-8"))
            self.assertEqual("runtime cover\n", (bundle_dir / "page" / "cover.rst").read_text(encoding="utf-8"))
            self.assertEqual(
                "review generated\n",
                (bundle_dir / "generated" / "JE-1000F" / "spec_ja.rst").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                "runtime safety\n",
                (bundle_dir / "generated" / "JE-1000F" / "safety_ja.rst").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                "override asset\n",
                (bundle_dir / "_assets" / "templates" / "word_template" / "common_assets" / "slot.jpg").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                "body {}\n",
                (bundle_dir / "_static" / "replacement.css").read_text(encoding="utf-8"),
            )
            self.assertFalse((bundle_dir / "README.md").exists())

    def test_overlay_review_onto_bundle_should_require_lang_scoped_review_dir_when_lang_is_requested(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US"

            (bundle_dir / "page").mkdir(parents=True)
            (bundle_dir / "generated").mkdir(parents=True)
            (bundle_dir / "index.rst").write_text("runtime index\n", encoding="utf-8")
            (bundle_dir / "page" / "overview.rst").write_text("runtime overview\n", encoding="utf-8")

            (review_dir / "page").mkdir(parents=True)
            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            (review_dir / "page" / "overview.rst").write_text("review overview\n", encoding="utf-8")

            self.assertFalse(review_bundle_exists(docs_dir=docs_dir, model="JE-1000F", region="US", lang="en"))

            applied_dir = overlay_review_onto_bundle(
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
                model="JE-1000F",
                region="US",
                lang="en",
            )

            self.assertIsNone(applied_dir)
            self.assertEqual("runtime index\n", (bundle_dir / "index.rst").read_text(encoding="utf-8"))
            self.assertEqual("runtime overview\n", (bundle_dir / "page" / "overview.rst").read_text(encoding="utf-8"))

    def test_review_content_exists_should_detect_legacy_partial_review_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            legacy_review_dir = docs_dir / "_review" / "JE-1000F" / "US"
            (legacy_review_dir / "page").mkdir(parents=True)
            (legacy_review_dir / "page" / "overview.rst").write_text("review overview\n", encoding="utf-8")

            self.assertFalse(review_bundle_exists(docs_dir=docs_dir, model="JE-1000F", region="US", lang=None))
            self.assertTrue(review_content_exists(docs_dir=docs_dir, model="JE-1000F", region="US", lang=None))

    def test_resolve_existing_review_bundle_dir_should_fallback_to_legacy_dir_for_lang_targets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            legacy_review_dir = docs_dir / "_review" / "JE-1000F" / "US"
            (legacy_review_dir / "page").mkdir(parents=True)
            (legacy_review_dir / "index.rst").write_text("review index\n", encoding="utf-8")

            resolved = resolve_existing_review_bundle_dir(
                docs_dir=docs_dir,
                model="JE-1000F",
                region="US",
                lang="en",
            )

            self.assertEqual(legacy_review_dir, resolved)

    def test_overlay_review_content_onto_bundle_should_preserve_runtime_index_when_legacy_review_dir_has_no_index(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US"

            (bundle_dir / "page").mkdir(parents=True)
            (bundle_dir / "generated").mkdir(parents=True)
            (bundle_dir / "index.rst").write_text("runtime index\n", encoding="utf-8")
            (bundle_dir / "page" / "overview.rst").write_text("runtime overview\n", encoding="utf-8")

            (review_dir / "page").mkdir(parents=True)
            (review_dir / "page" / "overview.rst").write_text("review overview\n", encoding="utf-8")

            applied_dir = overlay_review_content_onto_bundle(
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
                model="JE-1000F",
                region="US",
            )

            self.assertEqual(review_dir, applied_dir)
            self.assertEqual("runtime index\n", (bundle_dir / "index.rst").read_text(encoding="utf-8"))
            self.assertEqual("review overview\n", (bundle_dir / "page" / "overview.rst").read_text(encoding="utf-8"))

    def test_overlay_review_content_onto_bundle_should_skip_source_only_pages_when_reusing_legacy_review_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "es" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US"

            (bundle_dir / "page").mkdir(parents=True)
            (bundle_dir / "generated" / "JE-1000F").mkdir(parents=True)
            (bundle_dir / "index.rst").write_text("runtime index\n", encoding="utf-8")
            (bundle_dir / "page" / "overview.rst").write_text("runtime overview\n", encoding="utf-8")
            (bundle_dir / "generated" / "JE-1000F" / "spec_es.rst").write_text("runtime spec\n", encoding="utf-8")

            (review_dir / "page").mkdir(parents=True)
            (review_dir / "generated" / "JE-1000F").mkdir(parents=True)
            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            (review_dir / "page" / "overview.rst").write_text("review overview\n", encoding="utf-8")
            (review_dir / "page" / "00_preface.rst").write_text("review source preface\n", encoding="utf-8")
            (review_dir / "generated" / "JE-1000F" / "spec_es.rst").write_text("review spec\n", encoding="utf-8")

            applied_dir = overlay_review_content_onto_bundle(
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
                model="JE-1000F",
                region="US",
                lang=None,
                allowed_relative_paths=(
                    Path("page") / "overview.rst",
                    Path("generated") / "JE-1000F" / "spec_es.rst",
                ),
                allow_index=False,
            )

            self.assertEqual(review_dir, applied_dir)
            self.assertEqual("runtime index\n", (bundle_dir / "index.rst").read_text(encoding="utf-8"))
            self.assertEqual("review overview\n", (bundle_dir / "page" / "overview.rst").read_text(encoding="utf-8"))
            self.assertFalse((bundle_dir / "page" / "00_preface.rst").exists())
            self.assertEqual(
                "review spec\n",
                (bundle_dir / "generated" / "JE-1000F" / "spec_es.rst").read_text(encoding="utf-8"),
            )

    def test_overlay_review_content_onto_bundle_should_map_shared_us_review_pages_to_single_language_targets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "fr" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US"

            (bundle_dir / "page").mkdir(parents=True)
            (bundle_dir / "index.rst").write_text("runtime index\n", encoding="utf-8")
            (bundle_dir / "page" / "01_fcc.rst").write_text("runtime french page\n", encoding="utf-8")

            (review_dir / "page").mkdir(parents=True)
            (review_dir / "index.rst").write_text("shared review index\n", encoding="utf-8")
            (review_dir / "manifest.json").write_text(
                '{\n  "lang": null,\n  "page_manifest": "docs/manifests/manual_us.yaml"\n}\n',
                encoding="utf-8",
            )
            (review_dir / "page" / "01_fcc.rst").write_text("shared english page\n", encoding="utf-8")
            (review_dir / "page" / "p22_01_fcc.rst").write_text("shared french page\n", encoding="utf-8")

            applied_dir = overlay_review_content_onto_bundle(
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
                model="JE-1000F",
                region="US",
                lang=None,
                target_lang="fr",
                allowed_relative_paths=(Path("page") / "01_fcc.rst",),
                allow_index=False,
            )

            self.assertEqual(review_dir, applied_dir)
            self.assertEqual("runtime index\n", (bundle_dir / "index.rst").read_text(encoding="utf-8"))
            self.assertEqual("shared french page\n", (bundle_dir / "page" / "01_fcc.rst").read_text(encoding="utf-8"))

    def test_overlay_review_content_onto_bundle_should_map_shared_eu_review_pages_to_single_language_targets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "EU" / "fr" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "EU"

            (bundle_dir / "page").mkdir(parents=True)
            (bundle_dir / "index.rst").write_text("runtime index\n", encoding="utf-8")
            (bundle_dir / "page" / "02_whats_in_the_box.rst").write_text("runtime french page\n", encoding="utf-8")

            (review_dir / "page").mkdir(parents=True)
            (review_dir / "index.rst").write_text("shared review index\n", encoding="utf-8")
            (review_dir / "manifest.json").write_text(
                '{\n  "lang": null,\n  "page_manifest": "docs/manifests/manual_eu.yaml"\n}\n',
                encoding="utf-8",
            )
            (review_dir / "page" / "02_whats_in_the_box.rst").write_text("shared english page\n", encoding="utf-8")
            (review_dir / "page" / "p20_02_whats_in_the_box.rst").write_text("shared french page\n", encoding="utf-8")

            applied_dir = overlay_review_content_onto_bundle(
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
                model="JE-1000F",
                region="EU",
                lang=None,
                target_lang="fr",
                allowed_relative_paths=(Path("page") / "02_whats_in_the_box.rst",),
                allow_index=False,
            )

            self.assertEqual(review_dir, applied_dir)
            self.assertEqual("runtime index\n", (bundle_dir / "index.rst").read_text(encoding="utf-8"))
            self.assertEqual("shared french page\n", (bundle_dir / "page" / "02_whats_in_the_box.rst").read_text(encoding="utf-8"))

    def test_sync_review_from_runtime_should_refresh_parameter_driven_files_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "JP" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "JP"

            (runtime_dir / "page").mkdir(parents=True)
            (runtime_dir / "generated" / "JE-1000F").mkdir(parents=True)
            (review_dir / "page").mkdir(parents=True)
            (review_dir / "generated" / "JE-1000F").mkdir(parents=True)

            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            (review_dir / "manifest.json").write_text("{}\n", encoding="utf-8")

            (runtime_dir / "page" / "03_product_overview_placeholder.rst").write_text("runtime placeholder\n", encoding="utf-8")
            (runtime_dir / "page" / "02_whats_in_the_box.rst").write_text("runtime ordinary\n", encoding="utf-8")
            (runtime_dir / "page" / "spec_ja.rst").write_text("runtime spec page\n", encoding="utf-8")
            (runtime_dir / "page" / "cover_jp.rst").write_text("runtime cover\n", encoding="utf-8")
            (runtime_dir / "generated" / "JE-1000F" / "spec_ja.rst").write_text("runtime generated\n", encoding="utf-8")

            (review_dir / "page" / "03_product_overview_placeholder.rst").write_text("review placeholder\n", encoding="utf-8")
            (review_dir / "page" / "02_whats_in_the_box.rst").write_text("review ordinary\n", encoding="utf-8")
            (review_dir / "page" / "spec_ja.rst").write_text("review spec page\n", encoding="utf-8")
            (review_dir / "page" / "cover_jp.rst").write_text("review cover\n", encoding="utf-8")
            (review_dir / "generated" / "JE-1000F" / "spec_ja.rst").write_text("review generated\n", encoding="utf-8")

            copied = sync_review_from_runtime(
                runtime_bundle_dir=runtime_dir,
                review_dir=review_dir,
                scope="params",
            )

            self.assertGreaterEqual(len(copied), 4)
            self.assertEqual(
                "runtime placeholder\n",
                (review_dir / "page" / "03_product_overview_placeholder.rst").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                "review ordinary\n",
                (review_dir / "page" / "02_whats_in_the_box.rst").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                "runtime spec page\n",
                (review_dir / "page" / "spec_ja.rst").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                "runtime cover\n",
                (review_dir / "page" / "cover_jp.rst").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                "runtime generated\n",
                (review_dir / "generated" / "JE-1000F" / "spec_ja.rst").read_text(encoding="utf-8"),
            )

            manifest = json.loads((review_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("params", manifest["last_sync_scope"])
            self.assertIn("page/03_product_overview_placeholder.rst", manifest["last_sync_files"])

    def test_sync_review_paths_should_merge_parameter_lines_without_overwriting_review_text(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US" / "en"
            template_path = docs_dir / "templates" / "page_us-en" / "02_whats_in_the_box.rst"

            (runtime_dir / "page").mkdir(parents=True)
            (review_dir / "page").mkdir(parents=True)
            template_path.parent.mkdir(parents=True)

            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            (review_dir / "manifest.json").write_text("{}\n", encoding="utf-8")

            template_path.write_text(
                "Heading\n|PRODUCT_NAME_BOLD|\n**User Manual**\n**Warranty Card**\n",
                encoding="utf-8",
            )
            (runtime_dir / "page" / "02_whats_in_the_box.rst").write_text(
                "Heading\n**Jackery Explorer 1000**\n**User Manual**\n**Warranty Card**\n",
                encoding="utf-8",
            )
            (review_dir / "page" / "02_whats_in_the_box.rst").write_text(
                "Heading\n**Old Product Name**\n**Documents**\n\n",
                encoding="utf-8",
            )

            copied = sync_review_paths(
                runtime_bundle_dir=runtime_dir,
                review_dir=review_dir,
                scope="params",
                plan=(
                    SyncPlanEntry(
                        relative_path=Path("page") / "02_whats_in_the_box.rst",
                        mode="merge_params",
                        template_path=template_path,
                    ),
                ),
            )

            self.assertEqual(1, len(copied))
            self.assertEqual(
                "Heading\n**Jackery Explorer 1000**\n**Documents**\n\n",
                (review_dir / "page" / "02_whats_in_the_box.rst").read_text(encoding="utf-8"),
            )
            manifest = json.loads((review_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("params", manifest["last_sync_scope"])
            self.assertIn("page/02_whats_in_the_box.rst", manifest["last_sync_files"])

    def _merge_params_case(
        self,
        *,
        template_body: str,
        runtime_body: str,
        review_body: str,
    ) -> str:
        """Run one merge_params sync and return the resulting review page text."""
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US" / "en"
            template_path = docs_dir / "templates" / "page_us-en" / "02_whats_in_the_box.rst"

            (runtime_dir / "page").mkdir(parents=True)
            (review_dir / "page").mkdir(parents=True)
            template_path.parent.mkdir(parents=True)
            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            (review_dir / "manifest.json").write_text("{}\n", encoding="utf-8")

            template_path.write_text(template_body, encoding="utf-8")
            (runtime_dir / "page" / "02_whats_in_the_box.rst").write_text(runtime_body, encoding="utf-8")
            (review_dir / "page" / "02_whats_in_the_box.rst").write_text(review_body, encoding="utf-8")

            sync_review_paths(
                runtime_bundle_dir=runtime_dir,
                review_dir=review_dir,
                scope="params",
                plan=(
                    SyncPlanEntry(
                        relative_path=Path("page") / "02_whats_in_the_box.rst",
                        mode="merge_params",
                        template_path=template_path,
                    ),
                ),
            )
            return (review_dir / "page" / "02_whats_in_the_box.rst").read_text(encoding="utf-8")

    def test_merge_params_should_refresh_a_placeholder_sharing_a_line_with_prose(self) -> None:
        """The normal case: the review line still matches the template's shape.

        The sibling tests below pin the two divergent cases. This one exists so a
        fix for those cannot be "never touch prose-bearing lines".
        """
        line = "      \\HBInBoxThree{a.png}{%s}{b.png}{AC Charging Cable}{c.png}{Documents}\n"

        merged = self._merge_params_case(
            template_body="Heading\n" + line % "|PRODUCT_NAME|",
            runtime_body="Heading\n" + line % "Jackery Explorer 1000",
            review_body="Heading\n" + line % "Jackery Explorer 900",
        )

        self.assertEqual("Heading\n" + line % "Jackery Explorer 1000", merged)

    def test_merge_params_should_not_revert_authored_prose_on_a_placeholder_line(self) -> None:
        """Authored text on a placeholder-bearing line must survive the refresh.

        `Doucuments` is a real, deliberately preserved printed anomaly recorded in
        code-as-doc/reviews/je1000f_us_source_parity_discovery_2026-07-26.md. It sits
        on the same physical line as |PRODUCT_NAME|, and rebuilding that line from
        the template silently reverted it to the template's `Documents`.

        The line diverged from the template, so its parameters are left stale rather
        than the authored text being destroyed. tools/check_review_branch_sync.py is
        the notice path for a shared-source change that a review branch still needs.
        """
        template_line = "      \\HBInBoxThree{a.png}{|PRODUCT_NAME|}{b.png}{AC Charging Cable}{c.png}{Documents}\n"
        authored_line = "      \\HBInBoxThree{a.png}{Jackery Explorer 900}{b.png}{AC Charging Cable}{c.png}{Doucuments}\n"

        merged = self._merge_params_case(
            template_body="Heading\n" + template_line,
            runtime_body="Heading\n      \\HBInBoxThree{a.png}{Jackery Explorer 1000}{b.png}{AC Charging Cable}{c.png}{Documents}\n",
            review_body="Heading\n" + authored_line,
        )

        self.assertEqual("Heading\n" + authored_line, merged)
        self.assertIn("Doucuments", merged)

    def test_merge_params_should_not_reindent_a_diverged_review_line(self) -> None:
        """A review line at a different indent must keep its own indentation.

        _render_placeholder_values rebuilt the line from the template, including the
        template's leading whitespace, so a review line that had been re-indented
        (moved into a list-table cell, or out of one) was silently moved back — which
        in RST changes the block structure, not just the whitespace.
        """
        merged = self._merge_params_case(
            template_body="Heading\n**|PRODUCT_NAME|**\n",
            runtime_body="Heading\n**Jackery Explorer 1000**\n",
            review_body="Heading\n          **Jackery Explorer 900**\n",
        )

        self.assertEqual("Heading\n          **Jackery Explorer 900**\n", merged)

    def test_sync_review_paths_should_preserve_declared_target_page_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            protected_review_dir = docs_dir / "_review" / "JE-1000F" / "US"
            sibling_review_dir = docs_dir / "_review" / "JE-2000F" / "US"
            template_path = docs_dir / "templates" / "page_us-en" / "safety_en.rst"
            relative_path = Path("page") / "safety_en.rst"

            (runtime_dir / "page").mkdir(parents=True)
            template_path.parent.mkdir(parents=True)
            template_path.write_text(
                '<div>Press the |MAIN_POWER_BUTTON_LABEL| to turn them off.</div>\n',
                encoding="utf-8",
            )
            (runtime_dir / relative_path).write_text(
                '<div>Press the POWER button to turn them off.</div>\n',
                encoding="utf-8",
            )

            for review_dir, manifest in (
                (protected_review_dir, {"sync_preserve_paths": [relative_path.as_posix()]}),
                (sibling_review_dir, {}),
            ):
                (review_dir / "page").mkdir(parents=True)
                (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
                (review_dir / "manifest.json").write_text(
                    json.dumps(manifest) + "\n",
                    encoding="utf-8",
                )
                # Diverge from the template ONLY in the placeholder slot. This
                # test is about sync_preserve_paths, not about what merge_params
                # does to authored prose: an authored change to the surrounding
                # wording now freezes the line (see
                # test_merge_params_should_not_revert_authored_prose_on_a_placeholder_line),
                # which would mask the preserve-list contrast this test exists
                # to prove.
                (review_dir / relative_path).write_text(
                    '<div>Press the power button to turn them off.</div>\n',
                    encoding="utf-8",
                )

            plan = (
                SyncPlanEntry(
                    relative_path=relative_path,
                    mode="merge_params",
                    template_path=template_path,
                ),
            )
            protected_copied = sync_review_paths(
                runtime_bundle_dir=runtime_dir,
                review_dir=protected_review_dir,
                scope="params",
                plan=plan,
            )
            sibling_copied = sync_review_paths(
                runtime_bundle_dir=runtime_dir,
                review_dir=sibling_review_dir,
                scope="params",
                plan=plan,
            )

            self.assertEqual((), protected_copied)
            self.assertEqual(
                '<div>Press the power button to turn them off.</div>\n',
                (protected_review_dir / relative_path).read_text(encoding="utf-8"),
            )
            protected_manifest = json.loads((protected_review_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual([], protected_manifest["last_sync_files"])
            self.assertEqual([relative_path.as_posix()], protected_manifest["last_sync_preserved_files"])

            self.assertEqual(1, len(sibling_copied))
            self.assertEqual(
                '<div>Press the POWER button to turn them off.</div>\n',
                (sibling_review_dir / relative_path).read_text(encoding="utf-8"),
            )
            sibling_manifest = json.loads((sibling_review_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual([relative_path.as_posix()], sibling_manifest["last_sync_files"])
            self.assertEqual([], sibling_manifest["last_sync_preserved_files"])

    def test_sync_review_paths_should_reject_escaping_preserve_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US"
            (runtime_dir / "page").mkdir(parents=True)
            (review_dir / "page").mkdir(parents=True)
            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            (review_dir / "manifest.json").write_text(
                '{"sync_preserve_paths": ["../templates/safety_en.rst"]}\n',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "only accepts relative .rst paths"):
                sync_review_paths(
                    runtime_bundle_dir=runtime_dir,
                    review_dir=review_dir,
                    scope="params",
                    plan=(),
                )

    def test_sync_review_paths_should_merge_placeholder_values_from_shifted_runtime_lines(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US" / "en"
            template_path = docs_dir / "templates" / "page_us-en" / "06_ups_mode.rst"

            (runtime_dir / "page").mkdir(parents=True)
            (review_dir / "page").mkdir(parents=True)
            template_path.parent.mkdir(parents=True)

            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            (review_dir / "manifest.json").write_text("{}\n", encoding="utf-8")

            template_path.write_text(
                "Heading\nUPS |UPS_BYPASS_OUTPUT_TEXT|\nTail\n",
                encoding="utf-8",
            )
            (runtime_dir / "page" / "06_ups_mode.rst").write_text(
                ".. raw:: latex\n\n   \\HBApplyLang{en}\n\nHeading\nUPS 20 ms bypass transfer\nTail\n",
                encoding="utf-8",
            )
            (review_dir / "page" / "06_ups_mode.rst").write_text(
                "Heading\nUPS 10 ms bypass transfer\nTail\n",
                encoding="utf-8",
            )

            copied = sync_review_paths(
                runtime_bundle_dir=runtime_dir,
                review_dir=review_dir,
                scope="params",
                plan=(
                    SyncPlanEntry(
                        relative_path=Path("page") / "06_ups_mode.rst",
                        mode="merge_params",
                        template_path=template_path,
                    ),
                ),
            )

            self.assertEqual(1, len(copied))
            self.assertEqual(
                "Heading\nUPS 20 ms bypass transfer\nTail\n",
                (review_dir / "page" / "06_ups_mode.rst").read_text(encoding="utf-8"),
            )

    def test_sync_review_paths_should_not_overwrite_adjacent_non_placeholder_lines(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US" / "en"
            template_path = docs_dir / "templates" / "page_us-en" / "02_whats_in_the_box.rst"

            (runtime_dir / "page").mkdir(parents=True)
            (review_dir / "page").mkdir(parents=True)
            template_path.parent.mkdir(parents=True)

            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            (review_dir / "manifest.json").write_text("{}\n", encoding="utf-8")

            template_path.write_text(
                "Heading\n"
                ".. image:: templates/word_template/common_assets/in_the_box/main_unit1.png\n"
                "|PRODUCT_NAME_BOLD|\n"
                ".. image:: templates/word_template/common_assets/in_the_box/ac_charging_cable.png\n",
                encoding="utf-8",
            )
            (runtime_dir / "page" / "02_whats_in_the_box.rst").write_text(
                ".. raw:: latex\n\n   \\HBApplyLang{en}\n\n"
                "Heading\n"
                ".. image:: _assets/templates/word_template/common_assets/in_the_box/main_unit1.png\n"
                "**Jackery Explorer 1000**\n"
                ".. image:: _assets/templates/word_template/common_assets/in_the_box/ac_charging_cable.png\n",
                encoding="utf-8",
            )
            (review_dir / "page" / "02_whats_in_the_box.rst").write_text(
                "Heading\n"
                ".. image:: _assets/templates/word_template/common_assets/in_the_box/main_unit.png\n"
                "**Old Product Name**\n"
                ".. image:: _assets/templates/word_template/common_assets/in_the_box/ac_charging.png\n",
                encoding="utf-8",
            )

            copied = sync_review_paths(
                runtime_bundle_dir=runtime_dir,
                review_dir=review_dir,
                scope="params",
                plan=(
                    SyncPlanEntry(
                        relative_path=Path("page") / "02_whats_in_the_box.rst",
                        mode="merge_params",
                        template_path=template_path,
                    ),
                ),
            )

            self.assertEqual(1, len(copied))
            self.assertEqual(
                "Heading\n"
                ".. image:: _assets/templates/word_template/common_assets/in_the_box/main_unit.png\n"
                "**Jackery Explorer 1000**\n"
                ".. image:: _assets/templates/word_template/common_assets/in_the_box/ac_charging.png\n",
                (review_dir / "page" / "02_whats_in_the_box.rst").read_text(encoding="utf-8"),
            )

    def test_sync_review_paths_should_skip_diverged_review_lines_instead_of_splicing(self) -> None:
        # Regression: run 30680211845 — a template bullet carrying a newly
        # parameterized token line-mapped onto the review page's second
        # `.. list-table::` directive (the pages had diverged), and the blind
        # overwrite spliced the two tables into malformed RST.
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US" / "en"
            template_path = docs_dir / "templates" / "page_shared" / "es" / "08_charging_methods.rst"

            (runtime_dir / "page").mkdir(parents=True)
            (review_dir / "page").mkdir(parents=True)
            template_path.parent.mkdir(parents=True)

            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            (review_dir / "manifest.json").write_text("{}\n", encoding="utf-8")

            template_path.write_text(
                ".. list-table::\n"
                "\n"
                "   * - **PRECAUCIÓN**\n"
                "     - Un puerto de entrada |DC_INPUT_CONNECTOR| puede conectarse como máximo a dos paneles.\n"
                "\n"
                "       - Utilizar paneles del mismo modelo en ambos puertos |DC_INPUT_CONNECTOR|.\n",
                encoding="utf-8",
            )
            (runtime_dir / "page" / "p45.rst").write_text(
                ".. list-table::\n"
                "\n"
                "   * - **PRECAUCIÓN**\n"
                "     - Un puerto de entrada DC8020 puede conectarse como máximo a dos paneles.\n"
                "\n"
                "       - Utilizar paneles del mismo modelo en ambos puertos DC8020.\n",
                encoding="utf-8",
            )
            # Reviewer-diverged page: different phrasing, and the second table
            # directive sits where the template's bullet line maps to.
            diverged = (
                ".. list-table::\n"
                "\n"
                "   * - **PRECAUCIÓN**\n"
                "     - Un puerto de entrada DC8020 puede conectarse a un máximo de dos paneles.\n"
                "\n"
                ".. list-table::\n"
            )
            (review_dir / "page" / "p45.rst").write_text(diverged, encoding="utf-8")

            sync_review_paths(
                runtime_bundle_dir=runtime_dir,
                review_dir=review_dir,
                scope="params",
                plan=(
                    SyncPlanEntry(
                        relative_path=Path("page") / "p45.rst",
                        mode="merge_params",
                        template_path=template_path,
                    ),
                ),
            )

            merged = (review_dir / "page" / "p45.rst").read_text(encoding="utf-8")
            merged_lines = merged.splitlines()
            self.assertEqual(
                ".. list-table::",
                merged_lines[5],
                "the second table directive must survive the refresh (no splice)",
            )
            self.assertEqual(
                len(diverged.splitlines()),
                len(merged_lines),
                "the refresh must not add or drop lines",
            )

    def test_sync_review_paths_should_rewrite_substitution_asset_paths(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "JP" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "JP"
            asset_dir = docs_dir / "templates" / "word_template" / "common_assets" / "operation"

            (runtime_dir / "page").mkdir(parents=True)
            (review_dir / "page").mkdir(parents=True)
            asset_dir.mkdir(parents=True)
            (asset_dir / "energy_saving_12h.svg").write_text("<svg />", encoding="utf-8")
            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            (runtime_dir / "page" / "05_operation_guide_placeholder.rst").write_text(
                ".. |energy_saving| image:: templates/word_template/common_assets/operation/energy_saving_12h.svg\n",
                encoding="utf-8",
            )

            with mock.patch("tools.review_support.ROOT", root):
                copied = sync_review_paths(
                    runtime_bundle_dir=runtime_dir,
                    review_dir=review_dir,
                    scope="params",
                    plan=(SyncPlanEntry(relative_path=Path("page") / "05_operation_guide_placeholder.rst"),),
                )

            self.assertEqual(1, len(copied))
            self.assertIn(
                ".. |energy_saving| image:: _assets/templates/word_template/common_assets/operation/energy_saving_12h.svg",
                (review_dir / "page" / "05_operation_guide_placeholder.rst").read_text(encoding="utf-8"),
            )
            self.assertTrue(
                (review_dir / "_assets" / "templates" / "word_template" / "common_assets" / "operation" / "energy_saving_12h.svg").exists()
            )

    def test_sync_review_paths_should_refresh_product_identity_placeholder_lines(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-2000E" / "EU" / "en" / "rst"
            review_dir = docs_dir / "_review" / "JE-2000E" / "EU"
            template_path = docs_dir / "templates" / "page_eu-en" / "05_operation_guide_placeholder.rst"

            (runtime_dir / "page").mkdir(parents=True)
            (review_dir / "page").mkdir(parents=True)
            template_path.parent.mkdir(parents=True)

            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            (review_dir / "manifest.json").write_text("{}\n", encoding="utf-8")

            template_path.write_text(
                "CAUTION\nOnly connect |PRODUCT_NAME| to compatible accessories.\nTail\n",
                encoding="utf-8",
            )
            (runtime_dir / "page" / "05_operation_guide_placeholder.rst").write_text(
                "CAUTION\nOnly connect Jackery HomePower 2000 Plus to compatible accessories.\nTail\n",
                encoding="utf-8",
            )
            (review_dir / "page" / "05_operation_guide_placeholder.rst").write_text(
                "CAUTION\nOnly connect the Jackery Explorer 1000 to compatible accessories.\nTail\n",
                encoding="utf-8",
            )

            copied = sync_review_paths(
                runtime_bundle_dir=runtime_dir,
                review_dir=review_dir,
                scope="params",
                plan=(
                    SyncPlanEntry(
                        relative_path=Path("page") / "05_operation_guide_placeholder.rst",
                        mode="merge_params",
                        template_path=template_path,
                    ),
                ),
            )

            self.assertEqual(1, len(copied))
            self.assertEqual(
                "CAUTION\nOnly connect Jackery HomePower 2000 Plus to compatible accessories.\nTail\n",
                (review_dir / "page" / "05_operation_guide_placeholder.rst").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
