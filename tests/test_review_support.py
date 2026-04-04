from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.review_support import (
    SyncPlanEntry,
    overlay_review_content_onto_bundle,
    overlay_review_onto_bundle,
    review_bundle_exists,
    review_content_exists,
    sync_review_from_runtime,
    sync_review_paths,
)


class TestReviewSupport(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
