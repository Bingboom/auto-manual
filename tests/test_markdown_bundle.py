from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock

from tools import markdown_bundle


class MarkdownBundleTests(unittest.TestCase):
    def test_resolve_markdown_writer_should_prefer_native_myst(self) -> None:
        with mock.patch.object(
            markdown_bundle.subprocess,
            "run",
            return_value=SimpleNamespace(stdout="gfm\nmyst\ncommonmark_x\n"),
        ):
            self.assertEqual("myst", markdown_bundle.resolve_markdown_writer("pandoc"))

    def test_resolve_markdown_writer_should_fallback_to_myst_compatible_commonmark(self) -> None:
        with mock.patch.object(
            markdown_bundle.subprocess,
            "run",
            return_value=SimpleNamespace(stdout="gfm\ncommonmark_x\nmarkdown\n"),
        ):
            self.assertEqual(markdown_bundle.MYST_COMPATIBLE_WRITER, markdown_bundle.resolve_markdown_writer("pandoc"))

    def test_export_markdown_should_make_output_dir_a_myst_sphinx_source(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            out_dir = root / "md"
            assets_dir = out_dir / "assets"
            assets_dir.mkdir(parents=True)
            image_path = assets_dir / "demo.png"
            image_path.write_bytes(b"png")
            bundle_html = out_dir / "manual_bundle.html"
            bundle_html.write_text("<html></html>", encoding="utf-8")
            out_path = out_dir / "manual_demo.md"
            bundle = SimpleNamespace(title="Demo Manual")

            def fake_pandoc(cmd: list[str], **_: object) -> SimpleNamespace:
                target = Path(cmd[cmd.index("-o") + 1])
                target.write_text(f'<img src="{image_path.resolve().as_uri()}" />\n', encoding="utf-8")
                return SimpleNamespace(stdout="")

            with mock.patch.dict(
                markdown_bundle.os.environ,
                {},
                clear=True,
            ), mock.patch.object(
                markdown_bundle,
                "build_word_bundle_html",
                return_value=(bundle_html, None, ()),
            ) as build_html, mock.patch.object(
                markdown_bundle,
                "resolve_pandoc_binary",
                return_value="pandoc",
            ), mock.patch.object(
                markdown_bundle,
                "resolve_markdown_writer",
                return_value="myst",
            ), mock.patch.object(
                markdown_bundle.subprocess,
                "run",
                side_effect=fake_pandoc,
            ):
                result = markdown_bundle.export_markdown_from_bundle(
                    {},
                    "MODEL",
                    "US",
                    str(out_path),
                    materialized_bundle=bundle,
                    output_dir=out_dir,
                )

            self.assertEqual(out_path, result)
            self.assertIn('src="assets/demo.png"', out_path.read_text(encoding="utf-8"))
            self.assertIn("myst_parser", (out_dir / "conf.py").read_text(encoding="utf-8"))
            self.assertIn("manual_demo", (out_dir / "index.md").read_text(encoding="utf-8"))
            self.assertEqual("document", build_html.call_args.kwargs["presentation_profile"])

    def test_export_markdown_should_forward_web_presentation_profile_from_environment(self) -> None:
        with TemporaryDirectory() as td:
            out_dir = Path(td) / "md"
            out_dir.mkdir(parents=True)
            bundle_html = out_dir / "manual_bundle.html"
            bundle_html.write_text("<html></html>", encoding="utf-8")
            out_path = out_dir / "manual_demo.md"
            bundle = SimpleNamespace(title="Demo Manual")

            def fake_pandoc(cmd: list[str], **_: object) -> SimpleNamespace:
                target = Path(cmd[cmd.index("-o") + 1])
                target.write_text("# IMPORTANT\n", encoding="utf-8")
                return SimpleNamespace(stdout="")

            with mock.patch.dict(
                markdown_bundle.os.environ,
                {"AUTO_MANUAL_PRESENTATION_PROFILE": "web"},
                clear=True,
            ), mock.patch.object(
                markdown_bundle,
                "build_word_bundle_html",
                return_value=(bundle_html, None, ()),
            ) as build_html, mock.patch.object(
                markdown_bundle,
                "resolve_pandoc_binary",
                return_value="pandoc",
            ), mock.patch.object(
                markdown_bundle,
                "resolve_markdown_writer",
                return_value="myst",
            ), mock.patch.object(
                markdown_bundle.subprocess,
                "run",
                side_effect=fake_pandoc,
            ):
                markdown_bundle.export_markdown_from_bundle(
                    {},
                    "MODEL",
                    "US",
                    str(out_path),
                    materialized_bundle=bundle,
                    output_dir=out_dir,
                )

            self.assertEqual("web", build_html.call_args.kwargs["presentation_profile"])


if __name__ == "__main__":
    unittest.main()
