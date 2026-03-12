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
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            (runtime_dir / "page").mkdir(parents=True)
            (runtime_dir / "generated" / "JE-1000F").mkdir(parents=True)

            (runtime_dir / "index.rst").write_text(".. include:: page/spec_en.rst\n", encoding="utf-8")
            (runtime_dir / "page" / "spec_en.rst").write_text("Spec page\n", encoding="utf-8")
            (runtime_dir / "generated" / "JE-1000F" / "spec_en.rst").write_text("Generated spec\n", encoding="utf-8")
            (runtime_dir / "conf.py").write_text("ignored\n", encoding="utf-8")

            bundle = review_bundle.materialize_review_bundle(
                docs_dir=docs_dir,
                model="JE-1000F",
                region="US",
            )

            self.assertTrue(bundle.index_path.exists())
            self.assertTrue((bundle.review_dir / "page" / "spec_en.rst").exists())
            self.assertTrue((bundle.review_dir / "generated" / "JE-1000F" / "spec_en.rst").exists())
            self.assertFalse((bundle.review_dir / "conf.py").exists())

            manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("JE-1000F", manifest["model"])
            self.assertEqual("US", manifest["region"])
            self.assertIn("docs/_build/JE-1000F/US/rst", manifest["runtime_bundle_dir"])
            self.assertIn("docs/_review/JE-1000F/US", manifest["review_dir"])

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


if __name__ == "__main__":
    unittest.main()
