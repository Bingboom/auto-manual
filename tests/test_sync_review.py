from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.sync_review import resolve_sync_relative_paths


class TestSyncReview(unittest.TestCase):
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

    def test_resolve_sync_relative_paths_should_support_generated_only_scope(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            (runtime_dir / "generated" / "JE-1000F").mkdir(parents=True)
            (runtime_dir / "generated" / "JE-1000F" / "safety_en.rst").write_text("safety\n", encoding="utf-8")

            cfg = {
                "build": {"languages": ["en"]},
                "pages": [
                    {"type": "rst_include", "lang": "en", "file": "templates/page_us-en/00_preface.rst"},
                    {"type": "csv_page", "source": "phase1", "page": "safety", "langs": ["en"], "include_dir": "generated/{model}"},
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

            self.assertIn(Path("generated") / "JE-1000F" / "safety_en.rst", relative_paths)
            self.assertIn(Path("page") / "safety_en.rst", relative_paths)
            self.assertNotIn(Path("page") / "00_preface.rst", relative_paths)


if __name__ == "__main__":
    unittest.main()

