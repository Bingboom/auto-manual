from __future__ import annotations

import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock

from tools import markdown_bundle


class MarkdownBundleTests(unittest.TestCase):
    def test_web_profile_preserves_language_navigation_across_pandoc(self) -> None:
        with TemporaryDirectory() as td:
            out_dir = Path(td) / "md"
            out_dir.mkdir(parents=True)
            bundle_html = out_dir / "manual_bundle.html"
            bundle_html.write_text(
                '<html><body><nav class="hb-language-nav" '
                'aria-label="Manual language navigation"><ul class="hb-language-list">'
                '<li><a class="hb-language-link" href="#hb-lang-en" lang="en" '
                'hreflang="en">English</a></li><li><a class="hb-language-link" '
                'href="#hb-lang-fr" lang="fr" hreflang="fr">Français</a></li>'
                '</ul></nav><span id="hb-lang-en" class="hb-language-anchor" '
                'aria-hidden="true"></span><h1>English</h1><span id="hb-lang-fr" '
                'class="hb-language-anchor" aria-hidden="true"></span><h1>Français</h1>'
                "</body></html>",
                encoding="utf-8",
            )
            out_path = out_dir / "manual_demo.md"
            bundle = SimpleNamespace(title="Demo Manual")

            def fake_pandoc(cmd: list[str], **_: object) -> SimpleNamespace:
                source = Path(cmd[1]).read_text(encoding="utf-8")
                tokens = re.findall(
                    r"AUTOMANUALWEBLANGUAGE\d{4}PLACEHOLDER",
                    source,
                )
                self.assertEqual(3, len(tokens))
                target = Path(cmd[cmd.index("-o") + 1])
                target.write_text("\n\n".join(tokens), encoding="utf-8")
                return SimpleNamespace(stdout="")

            with mock.patch.dict(
                markdown_bundle.os.environ,
                {"AUTO_MANUAL_PRESENTATION_PROFILE": "web"},
                clear=True,
            ), mock.patch.object(
                markdown_bundle,
                "build_word_bundle_html",
                return_value=(bundle_html, None, ()),
            ), mock.patch.object(
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
                    "EU",
                    str(out_path),
                    materialized_bundle=bundle,
                    output_dir=out_dir,
                )

            output = out_path.read_text(encoding="utf-8")
            self.assertIn('class="hb-language-nav"', output)
            self.assertIn('href="#hb-lang-fr"', output)
            self.assertIn('id="hb-lang-en"', output)
            self.assertIn('id="hb-lang-fr"', output)
            self.assertNotIn("AUTOMANUALWEBLANGUAGE", output)

    def test_web_profile_restores_scientific_subscripts_after_pandoc(self) -> None:
        with TemporaryDirectory() as td:
            out_dir = Path(td) / "md"
            out_dir.mkdir(parents=True)
            localized_copy = (
                "Open-circuit voltage V<sub>oc</sub>.",
                "Tension en circuit ouvert V<sub>oc</sub>.",
                "Tensión de circuito abierto V<sub>oc</sub>.",
            )
            bundle_html = out_dir / "manual_bundle.html"
            bundle_html.write_text(
                "<html><body>"
                + "".join(f"<p>{sentence}</p>" for sentence in localized_copy)
                + "</body></html>",
                encoding="utf-8",
            )
            out_path = out_dir / "manual_demo.md"
            bundle = SimpleNamespace(title="Demo Manual")

            def fake_pandoc(cmd: list[str], **_: object) -> SimpleNamespace:
                source = Path(cmd[1]).read_text(encoding="utf-8")
                tokens = re.findall(r"AUTOMANUALWEBINLINE\d{4}PLACEHOLDER", source)
                target = Path(cmd[cmd.index("-o") + 1])
                target.write_text(
                    "\n".join(f"Voltage V{token}." for token in tokens),
                    encoding="utf-8",
                )
                return SimpleNamespace(stdout="")

            with mock.patch.dict(
                markdown_bundle.os.environ,
                {"AUTO_MANUAL_PRESENTATION_PROFILE": "web"},
                clear=True,
            ), mock.patch.object(
                markdown_bundle,
                "build_word_bundle_html",
                return_value=(bundle_html, None, ()),
            ), mock.patch.object(
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

            output = out_path.read_text(encoding="utf-8")
            self.assertEqual(3, output.count("V<sub>oc</sub>"))
            self.assertNotIn("V~oc~", output)

    def test_web_profile_restores_callouts_without_pandoc_table_artifacts(self) -> None:
        with TemporaryDirectory() as td:
            out_dir = Path(td) / "md"
            out_dir.mkdir(parents=True)
            callouts = "".join(
                (
                    '<table class="manual-callout-table"><tbody><tr>'
                    f'<td class="manual-callout-label">{label}</td>'
                    '<td class="manual-callout-body"><p>Body</p></td>'
                    "</tr></tbody></table>"
                )
                for label in ("WARNING", "DANGER", "CAUTION", "NOTE")
            )
            bundle_html = out_dir / "manual_bundle.html"
            bundle_html.write_text(f"<html><body>{callouts}</body></html>", encoding="utf-8")
            out_path = out_dir / "manual_demo.md"
            bundle = SimpleNamespace(title="Demo Manual")

            def fake_pandoc(cmd: list[str], **_: object) -> SimpleNamespace:
                source = Path(cmd[1]).read_text(encoding="utf-8")
                tokens = re.findall(r"AUTOMANUALWEBCALLOUT\d{4}PLACEHOLDER", source)
                target = Path(cmd[cmd.index("-o") + 1])
                target.write_text("\n\n".join(tokens), encoding="utf-8")
                return SimpleNamespace(stdout="")

            with mock.patch.dict(
                markdown_bundle.os.environ,
                {"AUTO_MANUAL_PRESENTATION_PROFILE": "web"},
                clear=True,
            ), mock.patch.object(
                markdown_bundle,
                "build_word_bundle_html",
                return_value=(bundle_html, None, ()),
            ), mock.patch.object(
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

            output = out_path.read_text(encoding="utf-8")
            self.assertEqual(4, output.count('class="manual-callout-table"'))
            self.assertEqual(4, output.count('class="manual-callout-label"'))
            self.assertEqual(4, output.count('class="manual-callout-body"'))
            self.assertNotIn("|  |  |", output)
            self.assertNotIn("<colgroup", output)
            self.assertNotIn("<thead", output)

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
