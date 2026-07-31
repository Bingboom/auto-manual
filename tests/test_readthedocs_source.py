from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools import readthedocs_source


class ReadTheDocsSourceTests(unittest.TestCase):
    def test_assemble_rtd_source_should_create_home_index_for_generated_manuals(self) -> None:
        with TemporaryDirectory() as td:
            build_root = Path(td) / "docs" / "_build"
            us_dir = build_root / "JE-1000F" / "US" / "md"
            jp_dir = build_root / "JE-1000F" / "JP" / "md"
            for source_dir, title, manual_name in (
                (us_dir, "US Manual", "manual_us.md"),
                (jp_dir, "JP Manual", "manual_jp.md"),
            ):
                source_dir.joinpath("assets").mkdir(parents=True)
                source_dir.joinpath("conf.py").write_text("project = 'nested'\n", encoding="utf-8")
                source_dir.joinpath("index.md").write_text(
                    (
                        f"# {title}\n\n"
                        "```{toctree}\n"
                        ":maxdepth: 2\n\n"
                        f"{manual_name[:-3]}\n"
                        "appendix_not_the_landing_page\n"
                        "```\n"
                    ),
                    encoding="utf-8",
                )
                image_path = source_dir.joinpath("assets", "demo.png")
                image_path.write_bytes(b"png")
                source_dir.joinpath(manual_name).write_text(
                    f'# Manual\n\n<img src="{image_path.resolve().as_uri()}" />\n',
                    encoding="utf-8",
                )

            output_dir = build_root / "rtd"
            manuals = readthedocs_source.assemble_rtd_source(
                build_root=build_root,
                output_dir=output_dir,
                title="Manual Library",
            )

            self.assertEqual(2, len(manuals))
            index_text = output_dir.joinpath("index.md").read_text(encoding="utf-8")
            self.assertIn("# Manual Library", index_text)
            self.assertIn("- [JE-1000F / JP - JP Manual](JE-1000F/JP/md/manual_jp.md)", index_text)
            self.assertIn("- [JE-1000F / US - US Manual](JE-1000F/US/md/manual_us.md)", index_text)
            self.assertNotIn("](JE-1000F/US/md/index.md)", index_text)
            self.assertNotIn("```{toctree}", index_text)
            self.assertNotIn(":hidden:", index_text)
            self.assertNotIn(":maxdepth:", index_text)
            self.assertNotIn(":caption: Manuals", index_text)
            self.assertTrue(output_dir.joinpath("JE-1000F", "US", "md", "manual_us.md").exists())
            self.assertTrue(output_dir.joinpath("JE-1000F", "US", "md", "assets", "demo.png").exists())
            self.assertTrue(
                output_dir.joinpath(
                    "_static",
                    "manual-assets",
                    "JE-1000F",
                    "US",
                    "md",
                    "assets",
                    "demo.png",
                ).exists()
            )
            self.assertFalse(output_dir.joinpath("JE-1000F", "US", "md", "conf.py").exists())
            us_manual = output_dir.joinpath("JE-1000F", "US", "md", "manual_us.md").read_text(encoding="utf-8")
            self.assertIn('src="../../../_static/manual-assets/JE-1000F/US/md/assets/demo.png"', us_manual)
            self.assertNotIn("file://", us_manual)
            conf_text = output_dir.joinpath("conf.py").read_text(encoding="utf-8")
            self.assertIn("myst_parser", conf_text)
            self.assertIn('html_static_path = ["_static"]', conf_text)
            self.assertIn('html_css_files = ["web_manual.css"]', conf_text)
            self.assertIn("build-finished", conf_text)
            self.assertIn("toc.not_included", conf_text)
            web_css = output_dir.joinpath("_static", "web_manual.css")
            self.assertTrue(web_css.exists())
            css_text = web_css.read_text(encoding="utf-8")
            self.assertIn(".hb-annotated-figure", css_text)
            self.assertIn(".hb-operation-figure", css_text)
            self.assertIn(".hb-inbox-grid", css_text)
            self.assertIn(".hb-inbox-card::before", css_text)
            self.assertIn(".hb-reference-figure", css_text)
            self.assertIn(".hb-reference-semantic", css_text)
            self.assertIn(".hb-app-download-composition", css_text)
            self.assertIn(".hb-app-download-grid", css_text)
            self.assertIn(".hb-app-download-art-frame", css_text)
            self.assertIn(".hb-fcc-composition", css_text)
            self.assertIn(".hb-fcc-grid", css_text)
            self.assertIn(".hb-lcd-table-composition", css_text)
            self.assertIn("table.hb-lcd-icon-table", css_text)
            self.assertIn("padding-inline: 0 !important", css_text)
            self.assertIn("width: 1.4rem", css_text)
            self.assertIn(".hb-lcd-description .line", css_text)
            self.assertIn(".hb-auto-resume-composition", css_text)
            self.assertIn("table.hb-auto-resume-table", css_text)
            self.assertIn(".hb-lcd-mode-composition", css_text)
            self.assertIn("table.hb-lcd-mode-table", css_text)
            self.assertIn(".hb-symbol-pair-composition", css_text)
            self.assertIn(".hb-symbol-pair-grid", css_text)
            self.assertIn(".hb-symbol-panel", css_text)
            self.assertIn("table.hb-symbol-panel-table", css_text)
            self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr))", css_text)
            self.assertIn("align-items: stretch", css_text)
            symbol_panel_css = css_text.split(".hb-symbol-panel {", 1)[1].split("}", 1)[0]
            self.assertIn("display: flex", symbol_panel_css)
            symbol_table_css = css_text.split(
                "#furo-main-content table.hb-symbol-panel-table {",
                1,
            )[1].split("}", 1)[0]
            self.assertIn("height: 100%", symbol_table_css)
            self.assertIn(".hb-troubleshooting-composition", css_text)
            self.assertIn("table.hb-troubleshooting-table", css_text)
            self.assertIn(".hb-troubleshooting-col-code", css_text)
            self.assertIn(".hb-troubleshooting-measures .line + .line", css_text)
            troubleshooting_css = css_text.split(
                "/* Troubleshooting keeps the PDF's compact code column",
                1,
            )[1].split(
                "/* Specification groups stay searchable",
                1,
            )[0]
            self.assertIn("overflow-x: auto", troubleshooting_css)
            self.assertIn("min-width: 42rem", troubleshooting_css)
            self.assertIn("width: 14%", troubleshooting_css)
            self.assertIn("width: 86%", troubleshooting_css)
            self.assertIn("border-right: 1.25px solid var(--hb-brand-dark)", troubleshooting_css)
            self.assertIn(".hb-spec-table-composition", css_text)
            self.assertIn("table.hb-spec-table", css_text)
            self.assertIn(".hb-spec-col-label", css_text)
            self.assertIn(".hb-spec-reference", css_text)
            specification_css = css_text.split(
                "/* Specification groups stay searchable",
                1,
            )[1].split(
                "/* Every WARNING/DANGER/CAUTION/NOTE",
                1,
            )[0]
            self.assertIn("overflow-x: auto", specification_css)
            self.assertIn("min-width: 40rem", specification_css)
            self.assertIn("width: 31%", specification_css)
            self.assertIn("width: 69%", specification_css)
            self.assertIn("background: var(--hb-surface) !important", specification_css)
            self.assertIn("font-size: 0.62em", specification_css)
            self.assertIn("vertical-align: super", specification_css)
            self.assertIn(".hb-warranty-intro-composition", css_text)
            self.assertIn(".hb-warranty-intro-panel", css_text)
            self.assertIn("figure.hb-warranty-card", css_text)
            self.assertIn("figure.hb-warranty-period-card", css_text)
            self.assertIn("section:has(> figure.hb-warranty-card)", css_text)
            self.assertIn(".hb-warranty-period-grid", css_text)
            self.assertIn("minmax(0, 1.22fr) minmax(0, 0.78fr)", css_text)
            self.assertIn(".hb-warranty-year-badge", css_text)
            self.assertIn("border-radius: 50%", css_text)
            self.assertIn(".hb-inline-add-device-icon", css_text)
            self.assertIn("#furo-main-content sub", css_text)
            self.assertIn("#furo-main-content section > img", css_text)
            standalone_css = css_text.split(
                "/* Standalone RST artwork fills one shared content width;",
                1,
            )[1].split(".hb-inline-add-device-icon", 1)[0]
            self.assertIn("width: 100% !important", standalone_css)
            self.assertIn("max-width: var(--hb-reading-width) !important", standalone_css)
            self.assertIn("object-fit: contain", standalone_css)
            self.assertIn("#furo-main-content section:target", css_text)
            self.assertIn(
                ".hb-has-composite-art > .hb-operation-stage",
                css_text,
            )
            self.assertIn('--hb-font-family: "Gilroy"', css_text)
            self.assertIn("--hb-brand-dark: #343031", css_text)
            self.assertIn("#furo-main-content h1", css_text)
            self.assertIn("table.manual-callout-table", css_text)
            self.assertIn(".manual-callout-label", css_text)
            self.assertIn("#meaning-of-symbols", css_text)
            self.assertIn("#signification-des-symboles", css_text)
            self.assertIn("#significado-de-los-simbolos", css_text)
            self.assertIn("table-layout: fixed !important", css_text)
            self.assertIn("width: clamp(7.5rem, 16%, 9.5rem)", css_text)
            self.assertIn("width: 84%", css_text)
            self.assertNotIn("h1 + .table-wrapper", css_text)
            self.assertIn("@media (max-width: 520px)", css_text)
            narrow_css = css_text.split("@media (max-width: 760px)", 1)[1].split(
                "@media (max-width: 520px)", 1
            )[0]
            self.assertNotIn(".hb-has-composite-art > .hb-operation-stage", narrow_css)
            self.assertIn(
                ".hb-annotated-figure.hb-has-composite-art > .hb-composite-stage",
                narrow_css,
            )
            self.assertIn(".hb-lcd-mode-composition", narrow_css)
            self.assertIn(".hb-symbol-pair-grid", narrow_css)
            self.assertIn(".hb-warranty-period-grid", narrow_css)
            self.assertIn("grid-template-columns: minmax(0, 1fr)", narrow_css)
            self.assertIn("table.hb-lcd-mode-table", narrow_css)
            self.assertIn("min-width: 34rem", narrow_css)
            self.assertIn("@media", css_text)

    def test_assemble_rtd_source_should_require_output_inside_build_root(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaisesRegex(RuntimeError, "must stay under build root"):
                readthedocs_source.assemble_rtd_source(
                    build_root=root / "docs" / "_build",
                    output_dir=root / "public",
                    title="Manual Library",
                )


if __name__ == "__main__":
    unittest.main()
