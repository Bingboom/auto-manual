from __future__ import annotations

import json
import struct
import unittest
import zlib
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.idml.web_edition import render_web_edition
from tools.manual_ir import ManualBlock, ManualIR, ManualPage


def _png_bytes() -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"\x00\xff\xff\xff")
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def _block(kind: str, payload, *, block_id: str = "b", asset_refs=()) -> ManualBlock:
    return ManualBlock(
        block_id=block_id,
        source_ref="page/x.rst#1",
        kind=kind,
        payload=payload,
        content_sha256="0" * 64,
        asset_refs=list(asset_refs),
    )


def _page(page_id: str, blocks, *, skipped_raw: int = 0) -> ManualPage:
    return ManualPage(
        page_id=page_id,
        source_ref="page/x.rst",
        source_path="page/x.rst",
        language="en",
        source_sha256="0" * 64,
        skipped_raw=skipped_raw,
        blocks=list(blocks),
    )


def _ir(pages, *, bundle_root: Path) -> ManualIR:
    return ManualIR(
        model="JE-1000F",
        region="US",
        language="en",
        source="prepared-bundle",
        bundle_root=str(bundle_root),
        bundle_sha256="0" * 64,
        snapshot_sha256="0" * 64,
        layout_params_sha256="0" * 64,
        style_contract_sha256="0" * 64,
        content_sha256="0" * 64,
        pages=list(pages),
    )


class WebEditionTests(unittest.TestCase):
    def _render(self, pages, *, bundle_setup=None):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        bundle_root = root / "bundle"
        data_root = root / "data"
        (data_root / "_attachments").mkdir(parents=True)
        bundle_root.mkdir()
        if bundle_setup:
            bundle_setup(bundle_root, data_root)
        out_dir = root / "webedition"
        edition = render_web_edition(
            _ir(pages, bundle_root=bundle_root),
            bundle_root=bundle_root,
            data_root=data_root,
            out_dir=out_dir,
            title="Sample Manual",
            provenance={"version": "1.6"},
            log=lambda _m: None,
        )
        body = (out_dir / "body.html").read_text(encoding="utf-8")
        manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        return edition, body, manifest, out_dir

    def test_renders_one_card_per_page_with_provenance_toolbar(self) -> None:
        edition, body, manifest, _ = self._render(
            [_page("page-1", [_block("h1", "OPERATIONS")]), _page("page-2", [_block("body", "Hello.")])]
        )
        self.assertEqual(2, edition.page_count)
        self.assertEqual(2, body.count('class="we-page"'))
        self.assertIn("1 / 2", body)
        self.assertIn("Sample Manual", body)
        self.assertIn("v1.6", body)
        self.assertEqual(2, manifest["page_count"])

    def test_inline_bold_and_pipe_noise(self) -> None:
        _, body, _, _ = self._render(
            [_page("page-1", [_block("body", "Press **POWER**.\n|\nDone.")])]
        )
        self.assertIn("<strong>POWER</strong>", body)
        self.assertNotIn("**POWER**", body)
        self.assertNotIn("<p>|</p>", body)

    def test_table_cell_image_directive_becomes_image(self) -> None:
        def setup(bundle_root: Path, _data_root: Path) -> None:
            art = bundle_root / "renderers" / "latex" / "assets"
            art.mkdir(parents=True)
            (art / "sym.png").write_bytes(_png_bytes())

        _, body, manifest, _ = self._render(
            [_page("page-1", [_block("table", [["Symbol", "Meaning"], [".. image:: renderers/latex/assets/sym.png", "**Bold** cell"]])])],
            bundle_setup=setup,
        )
        self.assertIn("we-cell-img", body)
        self.assertNotIn(".. image::", body)
        self.assertIn("<strong>Bold</strong>", body)
        self.assertEqual(1, manifest["asset_count"])

    def test_image_block_resolves_from_bundle(self) -> None:
        def setup(bundle_root: Path, _data_root: Path) -> None:
            (bundle_root / "renderers" / "latex" / "assets").mkdir(parents=True)
            (bundle_root / "renderers" / "latex" / "assets" / "op.png").write_bytes(_png_bytes())

        edition, body, _, out_dir = self._render(
            [_page("page-1", [_block("image", "renderers/latex/assets/op.png", asset_refs=["renderers/latex/assets/op.png"])])],
            bundle_setup=setup,
        )
        self.assertIn('src="assets/', body)
        self.assertEqual((), edition.unresolved_assets)
        self.assertTrue(any(out_dir.joinpath("assets").glob("*.png")))

    def test_unresolved_image_is_reported_not_fatal(self) -> None:
        edition, body, manifest, _ = self._render(
            [_page("page-1", [_block("image", "renderers/latex/assets/missing.png")])]
        )
        self.assertIn("we-img-missing", body)
        self.assertIn("renderers/latex/assets/missing.png", edition.unresolved_assets)
        self.assertEqual(["renderers/latex/assets/missing.png"], manifest["unresolved_assets"])

    def test_data_blocks_spec_toc_backcover(self) -> None:
        _, body, _, _ = self._render(
            [
                _page("spec", [
                    _block("data", {"kind": "spec_start", "title": "SPECIFICATIONS"}),
                    _block("data", {"kind": "spec_section", "rows": [["Capacity", "1024 Wh"]]}),
                ]),
                _page("toc", [_block("data", {"kind": "toc", "languages": [{"label": "English", "entries": [{"folio": "01", "title": "SAFETY"}]}]})]),
                _page("back", [_block("data", {"kind": "back_cover", "company": "JACKERY INC.", "address": "Fremont"})]),
            ]
        )
        self.assertIn("SPECIFICATIONS", body)
        self.assertIn("1024 Wh", body)
        self.assertIn("we-toc", body)
        self.assertIn("SAFETY", body)
        self.assertIn("JACKERY INC.", body)

    def test_callout_component_and_list_grouping(self) -> None:
        _, body, _, _ = self._render(
            [_page("page-1", [
                _block("component", {"kind": "warnbox", "label": "DANGER", "texts": ["Indoor use only."]}),
                _block("list", "• First."),
                _block("list", "• Second."),
            ])]
        )
        self.assertIn("we-callout", body)
        self.assertIn("DANGER", body)
        self.assertIn("<ul", body)
        self.assertEqual(1, body.count("<ul"))
        self.assertEqual(2, body.count("<li"))

    def test_html_is_escaped(self) -> None:
        _, body, _, _ = self._render([_page("page-1", [_block("body", "a <script>bad</script> b")])])
        self.assertNotIn("<script>bad", body)
        self.assertIn("&lt;script&gt;", body)

    def test_skipped_raw_recorded_in_manifest(self) -> None:
        _, _, manifest, _ = self._render([_page("page-1", [_block("h1", "X")], skipped_raw=2)])
        self.assertEqual(2, manifest["skipped_raw_blocks"])


if __name__ == "__main__":
    unittest.main()
