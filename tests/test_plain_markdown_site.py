from __future__ import annotations

import unittest
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from bs4 import BeautifulSoup

from tools import plain_markdown_site as pms
from tools import readthedocs_source
from tools.manual_md_directives import DIRECTIVES, _cells


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

    def test_component_extension_stages_shared_contract_runtime(self) -> None:
        with TemporaryDirectory() as td:
            staged = Path(td)
            self.assertTrue(pms.stage_component_extension(staged))
            extension = staged / "_ext"
            self.assertTrue((extension / "manual_md_directives.py").is_file())
            self.assertTrue((extension / "tools" / "component_specs" / "callout.py").is_file())
            self.assertTrue((extension / "tools" / "component_specs" / "spec_table.py").is_file())
            self.assertTrue((extension / "tools" / "rst_inline.py").is_file())
            self.assertTrue((extension / "tools" / "utils" / "path_utils.py").is_file())
            self.assertTrue(
                (
                    extension
                    / "docs"
                    / "renderers"
                    / "contracts"
                    / "component_registry.yaml"
                ).is_file()
            )
            self.assertTrue(
                (
                    extension
                    / "docs"
                    / "renderers"
                    / "contracts"
                    / "manual_theme.yaml"
                ).is_file()
            )


class ManualComponentDirectiveTests(unittest.TestCase):
    """The intermediate form must compile to the exact component markup.

    Shape heuristics can only guess; a document converted to declared intent has
    to render deterministically, which is the whole point of the intermediate.
    """

    INTERMEDIATE = """# Components

```{callout} CAUTION
High-power output port.

- Ensure fire safety protection.
- Use a 5A cable.
```

```{spec-table} INPUT PORTS
1 × AC Input | Charge Mode: 15 A max.
 | Bypass Mode^①^: 12 A max.
2 × DC8020 Ports | 8 A max.
```

```{troubleshooting} TROUBLESHOOTING
F0 | Restart the product.
F6 | 1. Wait for the grid. / 2. Check the vents.
```

```{comparison} Auto Resume | Not Auto Resume
Power-on restart | Manual output off
```

```{lcd-icons}
1 | ![wifi](icons/wifi.png) | Wi-Fi | On: connected. / Off: disconnected.
```

```{symbols}
![warn](icons/warn.png) | Read the manual before operation.
![fire](icons/fire.png) | Keep away from fire.
```
"""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = TemporaryDirectory()
        root = Path(cls._tmp.name)
        source = root / "src"
        (source / "icons").mkdir(parents=True)
        for name in ("wifi.png", "warn.png", "fire.png"):
            (source / "icons" / name).write_bytes(b"\x89PNG\r\n\x1a\n")
        (source / "index.md").write_text(cls.INTERMEDIATE, encoding="utf-8")
        output = root / "site"
        pms.render_markdown_site(source=source, output_dir=output, log=lambda _m: None)
        cls.html = (output / "index.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_callout_renders_with_a_real_list_in_the_body(self) -> None:
        self.assertIn("manual-callout-table", self.html)
        self.assertIn("<strong>CAUTION</strong>", self.html)
        body = self.html[self.html.index("manual-callout-body") :]
        self.assertIn("<ul", body[:800])  # bullets a pipe table cannot express
        self.assertIn("Use a 5A cable", self.html)

    def test_spec_table_renders_label_column_rowspan_and_superscript(self) -> None:
        self.assertIn('class="hb-spec-table-composition"', self.html)
        self.assertIn('aria-label="INPUT PORTS"', self.html)
        label = BeautifulSoup(self.html, "html.parser").select_one("th.hb-spec-label")
        self.assertEqual(["manual-spec-label", "hb-spec-label"], label["class"])
        self.assertEqual("row", label["scope"])
        self.assertEqual("2", label["rowspan"])
        self.assertIn("<sup>①</sup>", self.html)

    def test_troubleshooting_splits_steps_into_a_line_block(self) -> None:
        self.assertIn('class="hb-troubleshooting-composition"', self.html)
        self.assertIn("hb-troubleshooting-code", self.html)
        self.assertIn('class="line-block"', self.html)
        self.assertIn("Check the vents.", self.html)

    def test_comparison_and_lcd_and_symbols_compositions(self) -> None:
        self.assertIn("hb-auto-resume-composition", self.html)
        self.assertIn("hb-auto-resume-left", self.html)
        self.assertIn("hb-lcd-table-composition", self.html)
        self.assertIn("hb-lcd-icon-art", self.html)
        self.assertIn("hb-symbol-pair-composition", self.html)
        self.assertIn("hb-symbol-art", self.html)

    def test_blank_cells_merge_upward_in_every_multi_column_component(self) -> None:
        """A blank cell means "merge with the cell above" — a pipe table cannot.

        Left as a pipe table it renders an empty box, which is what the operator
        saw in the AC/DC resume table.
        """
        with TemporaryDirectory() as td:
            root = Path(td)
            source = root / "src"
            (source / "icons").mkdir(parents=True)
            (source / "icons" / "lcd.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            (source / "index.md").write_text(
                "# Merging\n\n"
                "```{comparison} Auto Resume | Not Auto Resume\n"
                "Power-on restart | Manual output off\n"
                "Battery SOC ≥ limit +10% | Energy Saving output off\n"
                " | Protection-triggered output off\n"
                "OTA upgrade completed | Discharge timer output off\n"
                "```\n\n"
                "```{lcd-mode} ![lcd](icons/lcd.png)\n"
                "Shortly On | Turn on | Press once.\n"
                " | Turn off | Press again.\n"
                " | Auto-off | After 2 minutes.\n"
                "Steady On | Turn on | Press twice.\n"
                " | Turn off | Press once.\n"
                "```\n\n"
                "```{manual-table} KEY COMBINATIONS\n"
                ":headers: Buttons | Operation | Function\n"
                "\n"
                "POWER + AC | Hold 3s | Energy Saving Mode\n"
                " | Hold 1s | Wi-Fi reset\n"
                "```\n",
                encoding="utf-8",
            )
            output = root / "site"
            pms.render_markdown_site(source=source, output_dir=output, log=lambda _m: None)
            html = (output / "index.html").read_text(encoding="utf-8")

            # the merged cell spans, and no empty cell is left behind
            self.assertIn('rowspan="2"', html)
            self.assertIn('hb-lcd-mode-state" rowspan="3"', html)
            self.assertIn("hb-lcd-mode-art-panel", html)
            self.assertIn("KEY COMBINATIONS", html)
            self.assertIn('<th class="head">Operation</th>', html)
            import re as _re

            self.assertEqual([], _re.findall(r"<td[^>]*>\s*</td>", html))

    def test_no_raw_html_leaks_as_escaped_text(self) -> None:
        for leak in ("&lt;figure", "&lt;table", "&lt;div", "&lt;sup"):
            self.assertNotIn(leak, self.html)

    def test_escaped_pipes_typed_headers_and_callout_variant_render(self) -> None:
        self.assertEqual(
            ["A | B", "C\\", "D"],
            _cells(r"A \| B | C\\| D"),
        )
        with TemporaryDirectory() as td:
            root = Path(td)
            source = root / "src"
            source.mkdir()
            (source / "index.md").write_text(
                "# Typed options\n\n"
                "```{callout} AVERTISSEMENT\n"
                ":variant: warning\n\n"
                "Keep clear.\n"
                "```\n\n"
                "```{troubleshooting} DIAGNOSTICS\n"
                ":headers: Code \\| status | Corrective measures\n\n"
                "F0 \\| stopped | Restart the product.\n"
                "```\n",
                encoding="utf-8",
            )
            output = root / "site"
            pms.render_markdown_site(
                source=source,
                output_dir=output,
                strict=True,
                log=lambda _m: None,
            )
            html = (output / "index.html").read_text(encoding="utf-8")
        self.assertIn("manual-callout-table", html)
        self.assertIn("<strong>AVERTISSEMENT</strong>", html)
        self.assertIn("Code | status", html)
        self.assertIn("F0 | stopped", html)

    def test_unknown_variant_and_obsolete_class_fail_closed(self) -> None:
        for name, directive in DIRECTIVES.items():
            with self.subTest(directive=name):
                self.assertNotIn("class", directive.option_spec)
        for option in (":variant: neon", ":class: warning"):
            with self.subTest(option=option), TemporaryDirectory() as td:
                root = Path(td)
                source = root / "src"
                source.mkdir()
                (source / "index.md").write_text(
                    "# Invalid\n\n"
                    "```{callout} WARNING\n"
                    f"{option}\n\n"
                    "Keep clear.\n"
                    "```\n",
                    encoding="utf-8",
                )
                with self.assertRaises(subprocess.CalledProcessError):
                    pms.render_markdown_site(
                        source=source,
                        output_dir=root / "site",
                        strict=True,
                        log=lambda _m: None,
                    )


class RemoteImageDownloadTests(unittest.TestCase):
    """A cloud export references every image on the editor's CDN.

    The HTE153 export has 57 of 57 images remote, so the site renders only while
    that host is reachable and dies with the link. Served locally here so the
    test does not depend on the internet.
    """

    PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32

    @classmethod
    def setUpClass(cls) -> None:
        import http.server
        import threading

        payload = cls.PNG

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 - http.server API
                if self.path.startswith("/img/"):
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                else:
                    self.send_error(404)

            def log_message(self, *_args: object) -> None:
                return

        cls._server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls._thread = threading.Thread(target=cls._server.serve_forever, daemon=True)
        cls._thread.start()
        cls.base = f"http://127.0.0.1:{cls._server.server_address[1]}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls._server.shutdown()
        cls._server.server_close()

    def test_remote_images_are_localized_and_deduplicated(self) -> None:
        with TemporaryDirectory() as td:
            staged = Path(td)
            (staged / "doc.md").write_text(
                f"# Doc\n\n"
                f"![a]({self.base}/img/one.png)\n\n"
                f"![again]({self.base}/img/one.png)\n\n"
                f'<img src="{self.base}/img/two.png"/>\n\n'
                f"![missing]({self.base}/nope/three.png)\n",
                encoding="utf-8",
            )
            downloaded, failures = pms.download_remote_images(staged, log=lambda _m: None)
            text = (staged / "doc.md").read_text(encoding="utf-8")
            self.assertEqual(2, downloaded)  # the repeat URL is fetched once
            self.assertEqual(1, len(failures))
            self.assertIn("nope/three.png", failures[0])
            files = sorted((staged / "_md_assets" / "remote").glob("*.png"))
            self.assertEqual(2, len(files))
            self.assertEqual(self.PNG, files[0].read_bytes())
            self.assertIn("_md_assets/remote/one-", text)
            self.assertIn("_md_assets/remote/two-", text)
            # a failed fetch keeps the original URL rather than dropping artwork
            self.assertIn(f"![missing]({self.base}/nope/three.png)", text)

    def test_downloaded_images_reach_the_built_site(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source = root / "src"
            source.mkdir()
            (source / "index.md").write_text(
                f"# Doc\n\n![a]({self.base}/img/one.png)\n", encoding="utf-8"
            )
            output = root / "site"
            pms.render_markdown_site(
                source=source, output_dir=output, download_images=True, log=lambda _m: None
            )
            html = (output / "index.html").read_text(encoding="utf-8")
            self.assertNotIn("127.0.0.1", html)  # no remote reference survives
            self.assertTrue(any(output.rglob("one-*.png")))

    def test_download_is_opt_in(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source = root / "src"
            source.mkdir()
            (source / "index.md").write_text(
                f"# Doc\n\n![a]({self.base}/img/one.png)\n", encoding="utf-8"
            )
            output = root / "site"
            pms.render_markdown_site(source=source, output_dir=output, log=lambda _m: None)
            html = (output / "index.html").read_text(encoding="utf-8")
        self.assertIn("127.0.0.1", html)  # left remote unless asked


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

    def test_raw_html_images_reach_the_output(self) -> None:
        """Sphinx does not track images inside raw HTML; the conf hook must copy them.

        Every pasted manual component and every pipeline-exported manual body
        references its artwork from raw ``<img>`` tags, so without this the
        pages render with broken images while the build still reports success.
        """
        with TemporaryDirectory() as td:
            root = Path(td)
            source = root / "src"
            (source / "assets").mkdir(parents=True)
            (source / "assets" / "art.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            (source / "index.md").write_text(
                "# Doc\n\n"
                '<figure class="hb-symbol-panel">'
                '<img class="hb-symbol-art" src="assets/art.png" alt="art"/>'
                "</figure>\n",
                encoding="utf-8",
            )
            output = root / "site"
            pms.render_markdown_site(source=source, output_dir=output, log=lambda _m: None)
            html = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn('src="assets/art.png"', html)
            self.assertIn("hb-symbol-panel", html)  # raw HTML passed through
            self.assertTrue(
                (output / "assets" / "art.png").is_file(),
                "raw-HTML image was not copied into the built site",
            )

    def test_conf_declares_the_asset_copy_hook(self) -> None:
        with TemporaryDirectory() as td:
            staged = Path(td)
            pms.write_conf_py(staged, title="Docs")
            conf = (staged / "conf.py").read_text(encoding="utf-8")
        self.assertIn("build-finished", conf)
        self.assertIn("def setup(app)", conf)

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

    def test_non_ascii_image_paths_get_an_ascii_staged_copy(self) -> None:
        """MyST percent-encodes image URIs and Sphinx then cannot find the file.

        A legacy backlog with Chinese asset names would render every such image
        broken, so the staged copy must point at an ASCII path.
        """
        with TemporaryDirectory() as td:
            staged = Path(td)
            (staged / "图片").mkdir()
            (staged / "图片" / "面板.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            (staged / "doc.md").write_text("# Doc\n\n![面板](图片/面板.png)\n", encoding="utf-8")
            pms.normalize_image_refs(staged, log=lambda _m: None)
            text = (staged / "doc.md").read_text(encoding="utf-8")
            self.assertNotIn("图片/面板.png", text)
            self.assertIn("_md_assets/", text)
            self.assertTrue(any((staged / "_md_assets").glob("*.png")))
            # the visible alt text is preserved
            self.assertIn("![面板]", text)

    def test_ascii_image_paths_are_left_untouched(self) -> None:
        with TemporaryDirectory() as td:
            staged = Path(td)
            (staged / "img").mkdir()
            (staged / "img" / "panel.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            original = "# Doc\n\n![p](img/panel.png)\n"
            (staged / "doc.md").write_text(original, encoding="utf-8")
            rewrites = pms.normalize_image_refs(staged, log=lambda _m: None)
            self.assertEqual(0, rewrites)
            self.assertEqual(original, (staged / "doc.md").read_text(encoding="utf-8"))
            self.assertFalse((staged / "_md_assets").exists())

    def test_headerless_two_column_table_becomes_a_spec_composition(self) -> None:
        """A pipe table cannot express what a spec block is; the upgrade must.

        GFM forces a header row (rendering a phantom grey strip), cannot mark
        the label column as <th>, and has no rowspan — exactly the three things
        the stylesheet keys off.
        """
        with TemporaryDirectory() as td:
            staged = Path(td)
            (staged / "spec.md").write_text(
                "## INPUT PORTS\n\n"
                "|                  |                            |\n"
                "|------------------|----------------------------|\n"
                "| 1 × AC Input     | Charge Mode: 15 A max.     |\n"
                "|                  | Bypass Mode^(①): 12 A max. |\n"
                "| 2 × DC8020 Ports | 8 A max.                   |\n",
                encoding="utf-8",
            )
            upgraded = pms.upgrade_spec_tables(staged, log=lambda _m: None)
            text = (staged / "spec.md").read_text(encoding="utf-8")
        self.assertEqual(1, upgraded)
        self.assertIn("```{spec-table} INPUT PORTS", text)
        self.assertIn("1 × AC Input | Charge Mode: 15 A max.", text)
        # a blank label is how the intermediate expresses a spanning label
        self.assertIn("\n | Bypass Mode", text)
        self.assertNotIn("|------", text)  # the pipe table is gone

    def test_signal_word_table_without_body_becomes_a_callout(self) -> None:
        """Cloud exports flatten callout boxes into a header-only two-column table.

        Rendered untouched they are a table with a heading row and no content,
        which is how a real legacy manual ends up with 17 of them.
        """
        with TemporaryDirectory() as td:
            staged = Path(td)
            (staged / "c.md").write_text(
                "# Doc\n\n"
                "| **WARNING** | Do not open the enclosure. |\n| --- | --- |\n\n"
                "| ### DANGER | Indoor use only. |\n| --- | --- |\n\n"
                "| NOTE | Mode resumes after power on. |\n| --- | --- |\n",
                encoding="utf-8",
            )
            upgraded = pms.upgrade_spec_tables(staged, log=lambda _m: None)
            text = (staged / "c.md").read_text(encoding="utf-8")
        self.assertEqual(3, upgraded)
        self.assertEqual(3, text.count("```{callout}"))
        for label in ("WARNING", "DANGER", "NOTE"):
            self.assertIn(f"```{{callout}} {label}", text)
        self.assertIn("Do not open the enclosure.", text)
        self.assertNotIn("| ---", text)

    def test_header_row_holding_data_is_treated_as_a_body_row(self) -> None:
        with TemporaryDirectory() as td:
            staged = Path(td)
            (staged / "lcd.md").write_text(
                "# LCD\n\n"
                "| ① | ![i](a.png) | Wi-Fi | Connected. |\n| --- | --- | --- | --- |\n"
                "| ② | ![i](b.png) | Bluetooth | Paired. |\n",
                encoding="utf-8",
            )
            pms.upgrade_spec_tables(staged, log=lambda _m: None)
            text = (staged / "lcd.md").read_text(encoding="utf-8")
        self.assertIn("```{lcd-icons}", text)
        self.assertIn("Wi-Fi", text)
        self.assertIn("Bluetooth", text)  # the stolen header row survived as data

    def test_in_table_section_headings_split_into_one_composition_each(self) -> None:
        with TemporaryDirectory() as td:
            staged = Path(td)
            (staged / "spec.md").write_text(
                "# SPECIFICATIONS\n\n"
                "| ### GENERAL INFO |  |\n| --- | --- |\n"
                "| Product Name | Explorer 1000 |\n"
                "| ### INPUT PORTS |  |\n"
                "| 1 × AC Input | 15 A max. |\n"
                "|  | Bypass: 12 A max. |\n",
                encoding="utf-8",
            )
            pms.upgrade_spec_tables(staged, log=lambda _m: None)
            text = (staged / "spec.md").read_text(encoding="utf-8")
        self.assertEqual(2, text.count("```{spec-table}"))
        self.assertIn("```{spec-table} GENERAL INFO", text)
        self.assertIn("```{spec-table} INPUT PORTS", text)
        self.assertIn("### INPUT PORTS", text)  # the heading is kept as a heading
        self.assertIn("\n | Bypass: 12 A max.", text)  # spanning label preserved

    def test_inline_superscript_and_subscript_are_rendered(self) -> None:
        with TemporaryDirectory() as td:
            staged = Path(td)
            (staged / "s.md").write_text(
                "# S\n\nBypass Mode^①^ and V~oc~ range.\n\n```\nkeep ^this^ and ~that~\n```\n",
                encoding="utf-8",
            )
            converted = pms.normalize_inline_syntax(staged, log=lambda _m: None)
            text = (staged / "s.md").read_text(encoding="utf-8")
        self.assertEqual(2, converted)
        self.assertIn("<sup>①</sup>", text)
        self.assertIn("<sub>oc</sub>", text)
        self.assertIn("keep ^this^ and ~that~", text)  # code fence untouched

    def test_table_with_a_real_header_is_left_alone(self) -> None:
        with TemporaryDirectory() as td:
            staged = Path(td)
            original = "# T\n\n| 参数 | 值 |\n|---|---|\n| 容量 | 1024Wh |\n"
            (staged / "t.md").write_text(original, encoding="utf-8")
            upgraded = pms.upgrade_spec_tables(staged, log=lambda _m: None)
            self.assertEqual(0, upgraded)
            self.assertEqual(original, (staged / "t.md").read_text(encoding="utf-8"))

    def test_wide_and_icon_tables_do_not_become_spec_tables(self) -> None:
        with TemporaryDirectory() as td:
            staged = Path(td)
            (staged / "wide.md").write_text(
                "# W\n\n|   |   |   |\n|---|---|---|\n| a | b | c |\n", encoding="utf-8"
            )
            (staged / "icons.md").write_text(
                "# I\n\n|   |   |\n|---|---|\n"
                "| ![warn](a.png) | Warning meaning |\n"
                "| ![note](b.png) | Note meaning |\n",
                encoding="utf-8",
            )
            pms.upgrade_spec_tables(staged, log=lambda _m: None)
            wide = (staged / "wide.md").read_text(encoding="utf-8")
            icons = (staged / "icons.md").read_text(encoding="utf-8")
        # neither becomes a spec table; unclassified shapes stay a pipe table
        for text in (wide, icons):
            self.assertNotIn("```{spec-table}", text)
            self.assertIn("md-site: unclassified table", text)
        self.assertIn("![warn](a.png)", icons)  # artwork left as markdown

    def test_upgrade_can_be_disabled(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source = root / "src"
            source.mkdir()
            (source / "index.md").write_text(
                "# T\n\n|   |   |\n|---|---|\n| L | V |\n", encoding="utf-8"
            )
            output = root / "site"
            pms.render_markdown_site(
                source=source, output_dir=output, upgrade_tables=False, log=lambda _m: None
            )
            html = (output / "index.html").read_text(encoding="utf-8")
            self.assertNotIn("hb-spec-table", html)

    def test_pages_without_a_heading_get_one(self) -> None:
        with TemporaryDirectory() as td:
            staged = Path(td)
            (staged / "index.md").write_text("# Root\n", encoding="utf-8")
            (staged / "legacy.md").write_text("Body text only, no heading.\n", encoding="utf-8")
            (staged / "titled.md").write_text("# Has One\n\nBody.\n", encoding="utf-8")
            added = pms.ensure_page_titles(
                staged, titles={"legacy.md": "从清单来的标题"}, log=lambda _m: None
            )
            self.assertEqual(1, added)
            self.assertTrue(
                (staged / "legacy.md").read_text(encoding="utf-8").startswith("# 从清单来的标题")
            )
            self.assertEqual("# Has One\n\nBody.\n", (staged / "titled.md").read_text(encoding="utf-8"))
            self.assertEqual("# Root\n", (staged / "index.md").read_text(encoding="utf-8"))

    def test_init_manifest_scaffolds_from_a_folder(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source = root / "backlog"
            (source / "产品手册").mkdir(parents=True)
            (source / "内部流程").mkdir(parents=True)
            (source / "产品手册" / "a.md").write_text("# 手册甲\n\nText.\n", encoding="utf-8")
            (source / "产品手册" / "b.md").write_text("no heading here\n", encoding="utf-8")
            (source / "内部流程" / "c.md").write_text("# 流程丙\n", encoding="utf-8")
            manifest = source / "inventory.csv"
            count = pms.write_manifest_scaffold(source, manifest, log=lambda _m: None)
            self.assertEqual(3, count)
            entries = pms.read_manifest(manifest)
            self.assertEqual(
                [("手册甲", "产品手册"), ("b", "产品手册"), ("流程丙", "内部流程")],
                [(entry.title, entry.section) for entry in entries],
            )

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
