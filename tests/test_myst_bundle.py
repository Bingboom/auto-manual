from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.myst_bundle import html_fragment_to_markdown


class MystBundleTests(unittest.TestCase):
    def test_html_fragment_to_markdown_should_preserve_headings_lists_and_tables(self) -> None:
        html = """
        <h1>Getting started</h1>
        <p>Use <strong>safe</strong> mode.</p>
        <ul><li>Connect power</li><li>Press Start</li></ul>
        <table><tr><th>Port</th><th>Output</th></tr><tr><td>USB-C</td><td>100 W</td></tr></table>
        """

        with tempfile.TemporaryDirectory() as td:
            markdown = html_fragment_to_markdown(html, output_dir=Path(td), prefer_pandoc=False)

        self.assertIn("# Getting started", markdown)
        self.assertIn("**safe**", markdown)
        self.assertIn("- Connect power", markdown)
        self.assertIn("| Port | Output |", markdown)
        self.assertIn("| USB-C | 100 W |", markdown)

    def test_html_fragment_to_markdown_should_normalize_docutils_line_divs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            markdown = html_fragment_to_markdown(
                '<div class="line">Keep this as a normal paragraph.</div>',
                output_dir=Path(td),
                prefer_pandoc=False,
            )

        self.assertEqual("Keep this as a normal paragraph.", markdown)

    def test_html_fragment_to_markdown_should_rewrite_local_file_image_uris(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td)
            image_path = output_dir / "assets" / "device.png"
            image_path.parent.mkdir()
            image_path.write_bytes(b"fake")

            markdown = html_fragment_to_markdown(
                f'<p><img alt="Device" src="{image_path.resolve().as_uri()}"/></p>',
                output_dir=output_dir,
                prefer_pandoc=False,
            )

        self.assertIn("![Device](assets/device.png)", markdown)


if __name__ == "__main__":
    unittest.main()
