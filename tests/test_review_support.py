from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.review_support import overlay_review_onto_bundle


class TestReviewSupport(unittest.TestCase):
    def test_overlay_review_onto_bundle_should_replace_runtime_page_and_copy_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "JP" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "JP"

            (bundle_dir / "page").mkdir(parents=True)
            (bundle_dir / "generated" / "JE-1000F").mkdir(parents=True)
            (bundle_dir / "_static" / "manual_template").mkdir(parents=True)
            (bundle_dir / "index.rst").write_text("runtime index\n", encoding="utf-8")
            (bundle_dir / "page" / "spec_ja.rst").write_text("runtime page\n", encoding="utf-8")
            (bundle_dir / "generated" / "JE-1000F" / "spec_ja.rst").write_text("runtime generated\n", encoding="utf-8")

            (review_dir / "page").mkdir(parents=True)
            (review_dir / "generated" / "JE-1000F").mkdir(parents=True)
            (review_dir / "overrides" / "_static" / "manual_template").mkdir(parents=True)
            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            (review_dir / "page" / "spec_ja.rst").write_text("review page\n", encoding="utf-8")
            (review_dir / "generated" / "JE-1000F" / "spec_ja.rst").write_text("review generated\n", encoding="utf-8")
            (review_dir / "overrides" / "_static" / "manual_template" / "slot.jpg").write_text(
                "override asset\n",
                encoding="utf-8",
            )

            overlay_review_onto_bundle(
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
                model="JE-1000F",
                region="JP",
            )

            self.assertEqual("review index\n", (bundle_dir / "index.rst").read_text(encoding="utf-8"))
            self.assertEqual("review page\n", (bundle_dir / "page" / "spec_ja.rst").read_text(encoding="utf-8"))
            self.assertEqual(
                "review generated\n",
                (bundle_dir / "generated" / "JE-1000F" / "spec_ja.rst").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                "override asset\n",
                (bundle_dir / "_static" / "manual_template" / "slot.jpg").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
