from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools import plain_markdown_site as pms
from tools import readthedocs_source


class PlainMarkdownSiteStyleContractTests(unittest.TestCase):
    """The preview lane must not drift from the published presentation contract."""

    def test_style_conf_matches_the_published_rtd_conf(self) -> None:
        with TemporaryDirectory() as td:
            rtd_dir = Path(td) / "rtd"
            rtd_dir.mkdir()
            readthedocs_source._write_conf_py(output_dir=rtd_dir, title="Ref")
            rtd_conf = (rtd_dir / "conf.py").read_text(encoding="utf-8")
        for line in pms.STYLE_CONF_LINES:
            with self.subTest(line=line):
                self.assertIn(line, rtd_conf)

    def test_written_conf_declares_theme_and_stylesheet(self) -> None:
        with TemporaryDirectory() as td:
            staged = Path(td)
            pms.write_conf_py(staged, title="My Docs")
            conf = (staged / "conf.py").read_text(encoding="utf-8")
        self.assertIn("project = 'My Docs'", conf)
        self.assertIn('html_theme = "furo"', conf)
        self.assertIn('html_css_files = ["web_manual.css"]', conf)


class PlainMarkdownSiteTests(unittest.TestCase):
    def _source_tree(self, root: Path) -> None:
        (root / "guides").mkdir(parents=True)
        (root / "assets").mkdir(parents=True)
        (root / "assets" / "pic.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (root / "guides" / "one.md").write_text(
            "# One\n\nText with **bold**.\n\n| A | B |\n|---|---|\n| 1 | 2 |\n",
            encoding="utf-8",
        )
        (root / "guides" / "two.md").write_text("# Two\n\n![pic](../assets/pic.png)\n", encoding="utf-8")
        (root / ".hidden").mkdir()
        (root / ".hidden" / "skip.md").write_text("# Skipped\n", encoding="utf-8")
        (root / "_build").mkdir()
        (root / "_build" / "stale.md").write_text("# Stale\n", encoding="utf-8")

    def test_discovery_skips_hidden_and_build_dirs(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            self._source_tree(root)
            found = {page.as_posix() for page in pms.discover_markdown(root)}
        self.assertEqual({"guides/one.md", "guides/two.md"}, found)

    def test_generated_root_index_lists_every_page(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            self._source_tree(root)
            pages = pms.discover_markdown(root)
            children = pms._write_root_index(root, title="Docs", pages=pages)
            index = (root / "index.md").read_text(encoding="utf-8")
        self.assertEqual(2, len(children))
        self.assertIn("# Docs", index)
        self.assertIn("```{toctree}", index)
        self.assertIn("guides/one", index)
        self.assertIn("guides/two", index)

    def test_existing_index_is_kept_and_gains_a_toctree(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            self._source_tree(root)
            (root / "index.md").write_text("# Welcome\n\nMy own landing copy.\n", encoding="utf-8")
            pages = pms.discover_markdown(root)
            children = pms._write_root_index(root, title="Docs", pages=pages)
            index = (root / "index.md").read_text(encoding="utf-8")
        self.assertIn("My own landing copy.", index)
        self.assertIn("```{toctree}", index)
        self.assertNotIn("index", [page.as_posix() for page in children])

    def test_readme_becomes_the_landing_page(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            self._source_tree(root)
            (root / "README.md").write_text("# Readme Landing\n", encoding="utf-8")
            pages = pms.discover_markdown(root)
            pms._write_root_index(root, title="Docs", pages=pages)
            index = (root / "index.md").read_text(encoding="utf-8")
        self.assertIn("Readme Landing", index)
        self.assertFalse((root / "README.md").exists())

    def test_stylesheet_comes_from_the_repo_contract(self) -> None:
        with TemporaryDirectory() as td:
            staged = Path(td)
            path, origin = pms.resolve_stylesheet(staged)
            self.assertEqual("web_manual.css", path.name)
            self.assertIn("repo contract", origin)
            self.assertGreater(path.stat().st_size, 1000)

    def test_explicit_stylesheet_wins(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            custom = root / "custom.css"
            custom.write_text("body { color: red; }\n", encoding="utf-8")
            staged = root / "staged"
            staged.mkdir()
            path, origin = pms.resolve_stylesheet(staged, explicit=custom)
            self.assertIn("explicit", origin)
            self.assertEqual("body { color: red; }\n", path.read_text(encoding="utf-8"))

    def test_render_builds_a_site_from_a_folder(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source = root / "src"
            source.mkdir()
            self._source_tree(source)
            output = root / "site"
            site = pms.render_markdown_site(
                source=source, output_dir=output, title="Folder Docs", log=lambda _m: None
            )
            self.assertEqual(3, site.page_count)
            self.assertTrue((output / "index.html").is_file())
            self.assertTrue((output / "guides" / "one.html").is_file())
            self.assertTrue((output / "_static" / "web_manual.css").is_file())
            index_html = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn("web_manual.css", index_html)
            self.assertIn("guides/one.html", index_html)

    def test_render_builds_a_single_file_site_with_assets(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            doc = root / "note.md"
            doc.write_text("# Note\n\n![pic](assets/pic.png)\n", encoding="utf-8")
            assets = root / "assets"
            assets.mkdir()
            (assets / "pic.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            output = root / "site"
            site = pms.render_markdown_site(
                source=doc, output_dir=output, assets_dir=assets, log=lambda _m: None
            )
            self.assertEqual(1, site.page_count)
            self.assertTrue((output / "index.html").is_file())
            self.assertIn("Note", (output / "index.html").read_text(encoding="utf-8"))

    def test_empty_source_is_rejected(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source = root / "empty"
            source.mkdir()
            with self.assertRaises(RuntimeError):
                pms.render_markdown_site(
                    source=source, output_dir=root / "site", log=lambda _m: None
                )

    def test_image_refs_are_repointed_to_staged_files(self) -> None:
        with TemporaryDirectory() as td:
            staged = Path(td)
            (staged / "assets").mkdir()
            (staged / "assets" / "pic.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            (staged / "doc.md").write_text(
                "# Doc\n\n"
                "![stale](../../../_static/manual-assets/JE-1000F/US/md/assets/pic.png)\n\n"
                '<img src="../../../_static/manual-assets/JE-1000F/US/md/assets/pic.png"/>\n\n'
                "![ok](assets/pic.png)\n\n"
                "![remote](https://example.com/pic.png)\n\n"
                "![unknown](assets/nothere.png)\n",
                encoding="utf-8",
            )
            rewrites = pms.normalize_image_refs(staged, log=lambda _m: None)
            text = (staged / "doc.md").read_text(encoding="utf-8")
            self.assertEqual(2, rewrites)
            self.assertNotIn("manual-assets", text)
            self.assertIn("![stale](assets/pic.png)", text)
            self.assertIn('<img src="assets/pic.png"', text)
            # untouched: already resolvable, remote, and genuinely missing
            self.assertIn("![ok](assets/pic.png)", text)
            self.assertIn("https://example.com/pic.png", text)
            self.assertIn("![unknown](assets/nothere.png)", text)

    def test_manifest_is_read_and_sorted_by_section_then_order(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            for name in ("a.md", "b.md", "c.md"):
                (root / name).write_text(f"# {name}\n", encoding="utf-8")
            manifest = root / "inventory.csv"
            manifest.write_text(
                "source,title,section,order\n"
                "c.md,Third,Guides,2\n"
                "a.md,First,Guides,1\n"
                "b.md,Loose,,1\n"
                "# skipped.md,Ignored,,9\n",
                encoding="utf-8",
            )
            entries = pms.read_manifest(manifest)
            self.assertEqual(["Loose", "First", "Third"], [entry.title for entry in entries])
            self.assertEqual(["", "Guides", "Guides"], [entry.section for entry in entries])

    def test_manifest_requires_a_source_column(self) -> None:
        with TemporaryDirectory() as td:
            manifest = Path(td) / "bad.csv"
            manifest.write_text("path,title\nx.md,X\n", encoding="utf-8")
            with self.assertRaises(RuntimeError) as ctx:
                pms.read_manifest(manifest)
            self.assertIn("source", str(ctx.exception))

    def test_manifest_staging_keeps_non_latin_sections_distinct(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source_dir = root / "src"
            source_dir.mkdir()
            for name in ("one.md", "two.md"):
                (source_dir / name).write_text(f"# {name}\n", encoding="utf-8")
            entries = [
                pms.ManifestEntry(source=source_dir / "one.md", title="产品手册页", section="产品手册", order=1),
                pms.ManifestEntry(source=source_dir / "two.md", title="现场笔记", section="内部资料", order=1),
            ]
            staged = root / "staged"
            staged.mkdir()
            routes = pms.stage_manifest(entries, staged, title="库")
            route_texts = {route.as_posix() for route in routes}
            self.assertEqual({"产品手册/产品手册页.md", "内部资料/现场笔记.md"}, route_texts)
            index = (staged / "index.md").read_text(encoding="utf-8")
            self.assertIn("## 产品手册", index)
            self.assertIn("## 内部资料", index)
            self.assertIn(":caption: 产品手册", index)

    def test_render_from_manifest_builds_grouped_site(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source_dir = root / "src"
            source_dir.mkdir()
            (source_dir / "assets").mkdir()
            (source_dir / "assets" / "pic.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            (source_dir / "guide.md").write_text("# Guide\n\n![p](assets/pic.png)\n", encoding="utf-8")
            (source_dir / "note.md").write_text("# Note\n\nText.\n", encoding="utf-8")
            manifest = root / "inventory.csv"
            manifest.write_text(
                "source,title,section,order\n"
                "src/guide.md,Guide,Manuals,1\n"
                "src/note.md,Note,Notes,1\n",
                encoding="utf-8",
            )
            output = root / "site"
            site = pms.render_markdown_site(
                manifest=manifest, output_dir=output, title="Library", log=lambda _m: None
            )
            self.assertEqual(3, site.page_count)
            self.assertTrue((output / "manuals" / "guide.html").is_file())
            self.assertTrue((output / "notes" / "note.html").is_file())
            index_html = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn("Manuals", index_html)
            self.assertIn("Notes", index_html)

    def test_source_and_manifest_are_mutually_exclusive(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaises(RuntimeError):
                pms.render_markdown_site(output_dir=root / "site", log=lambda _m: None)

    def test_pipeline_owned_output_dirs_are_refused(self) -> None:
        from tools.utils.path_utils import get_paths, releases_of, repo_root

        for guarded in (
            get_paths().docs_build_dir / "md-site",
            releases_of(repo_root()) / "md-site",
            get_paths().docs_dir / "publish" / "md-site",
        ):
            with self.subTest(guarded=guarded):
                with self.assertRaises(RuntimeError) as ctx:
                    pms._guard_output_dir(guarded)
                self.assertIn("pipeline-owned", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
