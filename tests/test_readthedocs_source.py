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
