from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path

from tools.build_docs_export import (
    _copy_attachment_images_for_latex,
    _copy_raw_html_assets_for_html,
)


class TestBuildDocsExport(unittest.TestCase):
    def test_raw_html_assets_are_copied_to_their_browser_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle_dir = root / "bundle"
            html_out_dir = root / "html"
            reference = bundle_dir / "page" / "fragment.rst"
            asset = bundle_dir / "_assets" / "assets" / "managed.png"
            reference.parent.mkdir(parents=True)
            asset.parent.mkdir(parents=True)
            reference.write_text(
                '.. raw:: html\n\n   <img src="_assets/assets/managed.png">\n',
                encoding="utf-8",
            )
            asset.write_bytes(b"managed image")
            (bundle_dir / "asset_usage_manifest.json").write_text(
                json.dumps(
                    {
                        "rewrites": [
                            {
                                "reference_path": "page/fragment.rst",
                                "rendered_value": "_assets/assets/managed.png",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            messages: list[str] = []

            _copy_raw_html_assets_for_html(bundle_dir, html_out_dir, messages.append)

            self.assertEqual(
                b"managed image",
                (html_out_dir / "_assets" / "assets" / "managed.png").read_bytes(),
            )
            self.assertEqual(1, len(messages))

    def test_dynamic_latex_assets_are_copied_to_output(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle_dir = root / "bundle"
            latex_out_dir = root / "latex"
            dynamic = bundle_dir / "renderers" / "latex" / "assets" / "managed-cover.pdf"
            dynamic.parent.mkdir(parents=True)
            latex_out_dir.mkdir()
            dynamic.write_bytes(b"dynamic registry pdf")
            messages: list[str] = []

            _copy_attachment_images_for_latex(bundle_dir, latex_out_dir, messages.append)

            self.assertEqual(
                b"dynamic registry pdf",
                (latex_out_dir / "managed-cover.pdf").read_bytes(),
            )
            self.assertEqual(1, len(messages))

    def test_latex_flat_copy_rejects_same_name_with_different_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle_dir = root / "bundle"
            latex_out_dir = root / "latex"
            dynamic = bundle_dir / "renderers" / "latex" / "assets" / "cover.pdf"
            dynamic.parent.mkdir(parents=True)
            latex_out_dir.mkdir()
            dynamic.write_bytes(b"registry bytes")
            (latex_out_dir / "cover.pdf").write_bytes(b"sphinx bytes")

            with self.assertRaisesRegex(RuntimeError, "LaTeX asset basename collision"):
                _copy_attachment_images_for_latex(bundle_dir, latex_out_dir, lambda _message: None)

            self.assertEqual(b"sphinx bytes", (latex_out_dir / "cover.pdf").read_bytes())


if __name__ == "__main__":
    unittest.main()
