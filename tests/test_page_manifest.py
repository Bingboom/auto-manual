from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.config_pages import GeneratedPage, RstIncludePage
from tools.page_manifest import resolve_config_pages, resolve_config_pages_or_raise


class TestPageManifest(unittest.TestCase):
    def test_resolve_config_pages_should_load_external_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = root / "manual.yaml"
            manifest_path.write_text(
                "\n".join(
                    [
                        "manifest_id: manual_us_en",
                        "pages:",
                        "  - type: rst_include",
                        "    lang: en",
                        "    file: templates/page_us-en/00_preface.rst",
                        "  - type: generated_page",
                        "    page: 03_product_overview",
                        "    engine: draft_v1",
                        "    recipe: templates/recipes/us-en/03_product_overview.yaml",
                        "    template: templates/page_us-en/03_product_overview_placeholder.rst",
                        "    langs: [en]",
                        "    include_dir: generated/{model}/draft",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            cfg = {
                "build": {"languages": ["en"]},
                "paths": {"page_manifest": manifest_path.as_posix()},
            }

            resolved = resolve_config_pages_or_raise(
                cfg,
                default_languages=["en"],
                root=root,
                model="JE-1000F",
                region="US",
                error_prefix="config.pages",
            )

            self.assertEqual(manifest_path, resolved.manifest_path)
            self.assertEqual("manual_us_en", resolved.manifest_id)
            self.assertIsInstance(resolved.pages[0], RstIncludePage)
            self.assertIsInstance(resolved.pages[1], GeneratedPage)

    def test_resolve_config_pages_should_fallback_to_inline_pages(self) -> None:
        cfg = {
            "build": {"languages": ["en"]},
            "pages": [{"type": "rst_include", "lang": "en", "file": "templates/page_us-en/00_preface.rst"}],
        }

        resolved = resolve_config_pages(
            cfg,
            default_languages=["en"],
            root=Path.cwd(),
        )

        self.assertIsNone(resolved.manifest_path)
        self.assertEqual([], resolved.issues)
        self.assertEqual(1, len(resolved.pages))


if __name__ == "__main__":
    unittest.main()
