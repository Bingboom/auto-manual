from dataclasses import replace
from pathlib import Path
import json
import hashlib
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from tools.manual_ir import read_manual_ir, write_manual_ir
from tools.manual_ir.document import validate_document
from tools.web_document_ir import render_document_fragments
from tools.web_document_source import _consume_covered_annotations
from tools.word_bundle_html import build_word_bundle_html


class WebDocumentIRTests(unittest.TestCase):
    def test_japanese_box_contents_uses_shared_inbox_outside_figure_target(self):
        from tools.web_presentation import transform_web_fragment
        cells = ''.join(f'<td><img src="{i}.png"><p>{label}</p></td>'
                        for i, label in enumerate(('本体', '拡張ケーブル', '取扱説明書')))
        markup = f'<h1>同梱品</h1><table><tr>{cells}</tr></table><table><tr><td>注意</td><td>付属品についての注意</td></tr></table>'
        result = transform_web_fragment(markup, source_path=Path('box_contents_ja.rst'),
                                        model='OTHER-BP', region='JP', language='ja')
        soup = BeautifulSoup(result, 'html.parser')
        self.assertEqual(len(soup.select('[data-component-id="HB-SPECIAL-INBOX"]')), 1)
        self.assertEqual([n.get_text(strip=True) for n in soup.select('.hb-inbox-label')],
                         ['本体', '拡張ケーブル', '取扱説明書'])
        self.assertEqual(len(soup.select('.hb-inbox-card')), 3)
        self.assertIn('付属品についての注意', soup.get_text())

    def test_finished_art_consumes_only_exact_bound_annotations(self):
        entry = {"covered_annotations": [{"selector": ".line-block", "text": "オン 1回押す オフ 3秒間長押し"}]}
        markup = '<img src="power.png"><div class="line-block">オン 1回押す オフ 3秒間長押し</div><p>保留する説明</p>'
        soup = BeautifulSoup(markup, "html.parser")
        _consume_covered_annotations(soup, entry, soup.img)
        self.assertIsNone(soup.select_one(".line-block"))
        self.assertEqual(soup.img["alt"], entry["covered_annotations"][0]["text"])
        self.assertEqual(soup.p.get_text(), "保留する説明")
        for changed in (markup.replace("1回押す", "2回押す"), markup + '<div class="line-block">オン 1回押す オフ 3秒間長押し</div>'):
            soup = BeautifulSoup(changed, "html.parser")
            with self.assertRaisesRegex(ValueError, "changed or ambiguous"):
                _consume_covered_annotations(soup, entry, soup.img)

    def build(self, root, manifest=None):
        pages = root / "source"
        pages.mkdir()
        (pages / "figure.png").write_bytes(b"frozen illustration")
        (pages / "intro_ja.rst").write_text(
            "日語文書\n========\n\n説明 **重要**。\n\n.. image:: figure.png\n   :alt: 帯字図\n"
        )
        (pages / "spec_ja.rst").write_text(
            "仕様\n====\n\n.. list-table::\n\n   * - 容量\n     - 2042.8Wh\n"
        )
        bundle = SimpleNamespace(
            bundle_dir=pages, page_dir=pages, page_paths=tuple(pages.glob("*.rst")),
            title="加電包", reference_doc=None, model="BP", region="JP", lang="", languages=("ja",),
        )
        output = root / "package"
        cfg = {"paths": {"web_illustration_manifest": str(manifest)}} if manifest else {}
        with patch("tools.word_bundle_html._convert_rst_fragment_to_html", side_effect=AssertionError("old reader")):
            build_word_bundle_html(cfg, "BP", "JP", materialized_bundle=bundle,
                                   output_dir=output, presentation_profile="web")
        return read_manual_ir(output / "manual.ir.json"), output, pages

    def test_finished_illustration_scope_hash_and_usage_are_enforced(self):
        for failure in (None, "target", "hash", "unused", "ambiguous"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                art = root / "finished.png"
                art.write_bytes(b"approved finished PDF crop")
                entry = {"path": art.name, "replaces": ["figure.png"],
                         "sha256": hashlib.sha256(art.read_bytes()).hexdigest()}
                manifest = {"schema_version": "web-illustrations/v1", "model": "BP", "region": "JP",
                            "language": "ja", "illustrations": [entry]}
                if failure == "target":
                    manifest["region"] = "US"
                elif failure == "hash":
                    entry["sha256"] = "0" * 64
                elif failure == "unused":
                    entry["replaces"] = ["absent.png"]
                elif failure == "ambiguous":
                    entry["replaces"].append("figure.png")
                path = root / "illustrations.json"
                path.write_text(json.dumps(manifest))
                if failure:
                    with self.assertRaises(ValueError):
                        self.build(root, path)
                else:
                    ir, package, _ = self.build(root, path)
                    self.assertEqual((package / ir.asset_refs[0]).read_bytes(), art.read_bytes())
                    self.assertIn("manual-finished-illustration", "".join(render_document_fragments(ir, package_root=package)))

    def test_whole_document_replays_after_source_removed_and_package_moved(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ir, output, pages = self.build(root)
            before = render_document_fragments(ir, package_root=output)
            shutil.rmtree(pages)
            relocated = root / "relocated"
            shutil.copytree(output, relocated)
            with patch("tools.web_document_source.load_web_document", side_effect=AssertionError("source reopened")):
                after = render_document_fragments(read_manual_ir(relocated / "manual.ir.json"), package_root=relocated)
            self.assertEqual([x.replace(str(output), "PACKAGE") for x in before],
                             [x.replace(str(relocated), "PACKAGE") for x in after])
            self.assertEqual(ir.language, "ja")
            self.assertEqual(len(ir.pages), 2)
            self.assertIn("2042.8Wh", "".join(after))
            self.assertTrue(ir.asset_refs)
            self.assertIn("<strong>重要</strong>", "".join(after))

    def test_missing_or_changed_asset_fails_before_render(self):
        with tempfile.TemporaryDirectory() as td:
            ir, output, _ = self.build(Path(td))
            file = output / ir.asset_refs[0]
            file.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "asset missing or changed"):
                render_document_fragments(ir, package_root=output)
            file.unlink()
            with self.assertRaisesRegex(ValueError, "asset missing or changed"):
                render_document_fragments(ir, package_root=output)

    def test_cold_process_replay_cannot_import_or_read_source_tables(self):
        with tempfile.TemporaryDirectory() as td:
            _, package, pages = self.build(Path(td))
            shutil.rmtree(pages)
            script = '''
from pathlib import Path
from unittest.mock import patch
import sys
original = Path.open
def guarded(path, *args, **kwargs):
    if path.suffix in {".rst", ".csv"}:
        raise AssertionError("source read during replay: " + str(path))
    return original(path, *args, **kwargs)
with patch.object(Path, "open", guarded):
    from tools.manual_ir import read_manual_ir
    from tools.web_document_ir import render_document_fragments
    package = Path(sys.argv[1])
    result = render_document_fragments(read_manual_ir(package / "manual.ir.json"), package_root=package)
    assert len(result) == 2
'''
            subprocess.run([sys.executable, "-c", script, str(package)], check=True, capture_output=True)

    def test_packaged_ir_images_survive_rtd_static_copy(self):
        from tools.readthedocs_source import _copy_manual_assets_to_static, _static_src_for_manual_asset
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ir, package, _ = self.build(root)
            rtd = root / "rtd"
            manual = Path("BP/JP/md")
            destination = rtd / manual
            shutil.copytree(package, destination)
            _copy_manual_assets_to_static(output_dir=rtd, destination_dir=destination, manual_relative=manual)
            for ref in ir.asset_refs:
                src = _static_src_for_manual_asset(
                    src=ref, markdown_path=destination / "manual.md", output_dir=rtd,
                    destination_dir=destination, manual_relative=manual,
                )
                self.assertIn("_static/manual-assets", src)
                self.assertTrue((destination / src).is_file())

    def test_tree_tampering_and_wrong_projection_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ir, output, _ = self.build(Path(td))
            with self.assertRaisesRegex(ValueError, "whole-document-content"):
                validate_document(replace(ir, metadata={**ir.metadata, "projection": "other"}))
            write_manual_ir(ir, output / "tampered.json")
            data = json.loads((output / "tampered.json").read_text())
            data["pages"][0]["blocks"][0]["payload"].append({"type": "text", "text": "changed"})
            (output / "tampered.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                read_manual_ir(output / "tampered.json")

    def test_declared_lcd_without_separate_icons_keeps_all_copy(self):
        from tools.csv_pages.renderers_lcd_icons import _rst_table
        from tools.word_bundle_html import _convert_rst_fragment_to_html
        rows = [{"no": "1", "figure": "", "name": "残量", "description": "現在の残量です。"}]
        with tempfile.TemporaryDirectory() as td:
            markup = _convert_rst_fragment_to_html(
                _rst_table(rows, status_labels=()), Path(td) / "lcd_ja.rst", Path(td),
                presentation_profile="web", language="ja", declared_lcd_icons=True,
            )
            soup = BeautifulSoup(markup, "html.parser")
            self.assertIn("現在の残量です。", soup.get_text())
            self.assertIsNone(soup.img)
            self.assertIsNotNone(soup.select_one(".hb-lcd-table-composition"))
