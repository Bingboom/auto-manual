from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import review_bundle


class TestReviewBundle(unittest.TestCase):
    def test_materialize_review_bundle_should_copy_reviewable_rst_files_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            (runtime_dir / "page").mkdir(parents=True)
            (runtime_dir / "generated" / "JE-1000F").mkdir(parents=True)

            (runtime_dir / "index.rst").write_text(".. include:: page/spec_en.rst\n", encoding="utf-8")
            (runtime_dir / "page" / "spec_en.rst").write_text("Spec page\n", encoding="utf-8")
            (runtime_dir / "generated" / "JE-1000F" / "spec_en.rst").write_text("Generated spec\n", encoding="utf-8")
            (runtime_dir / "conf.py").write_text("ignored\n", encoding="utf-8")
            (runtime_dir / "bundle_manifest.json").write_text(
                json.dumps(
                    {
                        "page_manifest": "docs/manifests/manual_us-en.yaml",
                        "recipe_ids": ["03_product_overview"],
                        "snippet_ids": ["wireless_reset_buttons"],
                        "spec_master": {"path": "data/phase1/Spec_Master.csv", "sha256": "abc"},
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            bundle = review_bundle.materialize_review_bundle(
                docs_dir=docs_dir,
                model="JE-1000F",
                region="US",
                lang="en",
            )

            self.assertTrue(bundle.index_path.exists())
            self.assertTrue((bundle.review_dir / "page" / "spec_en.rst").exists())
            self.assertTrue((bundle.review_dir / "generated" / "JE-1000F" / "spec_en.rst").exists())
            self.assertFalse((bundle.review_dir / "conf.py").exists())

            manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("JE-1000F", manifest["model"])
            self.assertEqual("US", manifest["region"])
            self.assertEqual("en", manifest["lang"])
            self.assertIn("docs/_build/JE-1000F/US/en/rst", manifest["runtime_bundle_dir"])
            self.assertIn("docs/_review/JE-1000F/US/en", manifest["review_dir"])
            self.assertEqual("docs/manifests/manual_us-en.yaml", manifest["page_manifest"])
            self.assertEqual(["03_product_overview"], manifest["recipe_ids"])
            self.assertEqual(["wireless_reset_buttons"], manifest["snippet_ids"])

    def test_materialize_review_bundle_should_keep_existing_review_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            review_dir = docs_dir / "_review" / "JE-1000F" / "JP"
            (review_dir / "page").mkdir(parents=True)
            (review_dir / "generated" / "JE-1000F").mkdir(parents=True)
            (review_dir / "index.rst").write_text(".. include:: page/custom.rst\n", encoding="utf-8")
            (review_dir / "page" / "custom.rst").write_text("Edited review content\n", encoding="utf-8")
            (review_dir / "generated" / "JE-1000F" / "spec_ja.rst").write_text("Edited generated\n", encoding="utf-8")

            bundle = review_bundle.materialize_review_bundle(
                docs_dir=docs_dir,
                model="JE-1000F",
                region="JP",
            )

            self.assertTrue(bundle.reused_existing)
            self.assertEqual("Edited review content\n", (review_dir / "page" / "custom.rst").read_text(encoding="utf-8"))

    def test_materialize_review_bundle_should_support_lang_scoped_runtime_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "es" / "rst"
            (runtime_dir / "page").mkdir(parents=True)
            (runtime_dir / "generated" / "JE-1000F").mkdir(parents=True)

            (runtime_dir / "index.rst").write_text(".. include:: page/spec_es.rst\n", encoding="utf-8")
            (runtime_dir / "page" / "spec_es.rst").write_text("Spec page\n", encoding="utf-8")
            (runtime_dir / "generated" / "JE-1000F" / "spec_es.rst").write_text("Generated spec\n", encoding="utf-8")

            bundle = review_bundle.materialize_review_bundle(
                docs_dir=docs_dir,
                model="JE-1000F",
                region="US",
                lang="es",
            )

            manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("es", manifest["lang"])
            self.assertIn("docs/_build/JE-1000F/US/es/rst", manifest["runtime_bundle_dir"])
            self.assertIn("docs/_review/JE-1000F/US/es", manifest["review_dir"])


if __name__ == "__main__":
    unittest.main()
