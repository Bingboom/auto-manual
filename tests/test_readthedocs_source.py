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
                    f"# {title}\n\n```{{toctree}}\n\n{manual_name[:-3]}\n```\n",
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
            self.assertIn("- [JE-1000F / JP - JP Manual](JE-1000F/JP/md/index.md)", index_text)
            self.assertIn("- [JE-1000F / US - US Manual](JE-1000F/US/md/index.md)", index_text)
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
            self.assertIn("build-finished", conf_text)
            self.assertIn("toc.not_included", conf_text)

    def _build_one_manual(self, build_root: Path, *, with_web_edition: bool) -> None:
        md_dir = build_root / "JE-1000F" / "US" / "md"
        md_dir.joinpath("assets").mkdir(parents=True)
        md_dir.joinpath("conf.py").write_text("project = 'nested'\n", encoding="utf-8")
        md_dir.joinpath("index.md").write_text("# US Manual\n", encoding="utf-8")
        md_dir.joinpath("manual_us.md").write_text("# Manual\n\nBody.\n", encoding="utf-8")
        if with_web_edition:
            web_dir = build_root / "JE-1000F" / "US" / "webedition"
            (web_dir / "assets").mkdir(parents=True)
            (web_dir / "assets" / "p1.png").write_bytes(b"png")
            web_dir.joinpath("body.html").write_text(
                '<style>.we-doc{}</style>\n<div class="we-doc">'
                '<div class="we-toolbar"><span class="we-title">US Manual</span></div>'
                '<section class="we-page"><img src="assets/p1.png" alt="p"/></section></div>\n',
                encoding="utf-8",
            )
            web_dir.joinpath("manifest.json").write_text('{"page_count": 1}', encoding="utf-8")

    def test_web_edition_becomes_primary_catalog_entry(self) -> None:
        with TemporaryDirectory() as td:
            build_root = Path(td) / "docs" / "_build"
            self._build_one_manual(build_root, with_web_edition=True)
            output_dir = build_root / "rtd"
            manuals = readthedocs_source.assemble_rtd_source(
                build_root=build_root, output_dir=output_dir, title="Manual Library"
            )
            self.assertEqual(1, len(manuals))
            self.assertEqual("JE-1000F/US/md/indesign_web", manuals[0].web_edition_ref)

            index_text = output_dir.joinpath("index.md").read_text(encoding="utf-8")
            primary = index_text.index("InDesign edition")
            secondary = index_text.index("HTML edition")
            self.assertLess(primary, secondary)
            self.assertIn("](JE-1000F/US/md/indesign_web.md)", index_text)
            self.assertIn("  - [", index_text)  # secondary is indented

            viewer = output_dir.joinpath("JE-1000F", "US", "md", "indesign_web.md").read_text(encoding="utf-8")
            self.assertIn("```{raw} html", viewer)
            self.assertIn('class="we-doc"', viewer)
            # image ref rewritten from assets/ to the _static web-edition location
            self.assertIn("_static/web-edition/JE-1000F/US/assets/p1.png", viewer)
            self.assertNotIn('src="assets/p1.png"', viewer)
            self.assertTrue(
                output_dir.joinpath("_static", "web-edition", "JE-1000F", "US", "assets", "p1.png").exists()
            )

    def test_without_web_edition_is_unchanged_passthrough(self) -> None:
        with TemporaryDirectory() as td:
            build_root = Path(td) / "docs" / "_build"
            self._build_one_manual(build_root, with_web_edition=False)
            output_dir = build_root / "rtd"
            manuals = readthedocs_source.assemble_rtd_source(
                build_root=build_root, output_dir=output_dir, title="Manual Library"
            )
            self.assertIsNone(manuals[0].web_edition_ref)
            index_text = output_dir.joinpath("index.md").read_text(encoding="utf-8")
            self.assertIn("- [JE-1000F / US - US Manual](JE-1000F/US/md/index.md)", index_text)
            self.assertNotIn("InDesign edition", index_text)
            self.assertFalse(output_dir.joinpath("JE-1000F", "US", "md", "indesign_web.md").exists())
            self.assertFalse(output_dir.joinpath("_static", "web-edition").exists())

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
