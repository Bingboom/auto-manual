from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import copy
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from tests.test_web_lcd_component import _table as lcd_table
from tests.test_web_troubleshooting_component import source_table
from tools.web_lcd_component import transform_lcd_icon_tables
from tools.web_troubleshooting_component import transform_troubleshooting_tables


class WebTableIRTests(unittest.TestCase):
    def test_invalid_later_table_leaves_original_dom_unchanged(self):
        for transform, source, broken in (
            (
                transform_lcd_icon_tables,
                lcd_table(),
                lcd_table().replace("<td>1</td>", ""),
            ),
            (
                transform_troubleshooting_tables,
                source_table(),
                source_table().replace("<td>E42</td>", ""),
            ),
        ):
            with self.subTest(transform=transform.__name__):
                soup = BeautifulSoup(source + broken, "html.parser")
                original = str(soup)
                with self.assertRaises(ValueError):
                    transform(soup, source_path=Path("appendix.rst"))
                self.assertEqual(original, str(soup))

    def test_real_entrypoints_use_public_assembler_and_ir_renderer(self):
        from tools.manual_ir import build_manual_ir_from_source
        from tools.web_table_ir import render_web_table_ir

        for transform, markup, kind in (
            (transform_lcd_icon_tables, lcd_table(), "lcd"),
            (transform_troubleshooting_tables, source_table(), "troubleshooting"),
        ):
            with (
                self.subTest(kind=kind),
                patch(
                    "tools.web_table_ir.build_manual_ir_from_source",
                    wraps=build_manual_ir_from_source,
                ) as assemble,
                patch(
                    "tools.web_table_ir.render_web_table_ir", wraps=render_web_table_ir
                ) as render,
            ):
                soup = BeautifulSoup(markup, "html.parser")
                transform(
                    soup,
                    source_path=Path("appendix.rst"),
                    language="ja",
                    model="OTHER",
                    region="JP",
                )
                assemble.assert_called_once()
                render.assert_called_once()
                source = assemble.call_args.args[0]
                self.assertEqual(
                    ("OTHER", "JP", "ja"),
                    (source.model, source.region, source.language),
                )
                self.assertEqual("web-declared-tables", source.metadata["projection"])

    def test_serialized_replay_and_corruption_reject(self):
        from tools.manual_ir import (
            build_manual_ir_from_source,
            read_manual_ir,
            write_manual_ir,
        )
        from tools.manual_ir.web_tables import load_web_table_source
        from tools.web_table_ir import render_web_table_ir

        for kind, markup, transform in (
            ("lcd", lcd_table(), transform_lcd_icon_tables),
            (
                "troubleshooting",
                source_table(head=False),
                transform_troubleshooting_tables,
            ),
        ):
            with self.subTest(kind=kind):
                source = load_web_table_source(
                    markup, table_kind=kind, source_path=Path("not-on-disk.rst")
                )
                ir = build_manual_ir_from_source(source)
                with tempfile.TemporaryDirectory() as tmp:
                    restored = read_manual_ir(
                        write_manual_ir(ir, Path(tmp) / "ir.json")
                    )
                    replay = "".join(render_web_table_ir(restored))
                soup = BeautifulSoup(markup, "html.parser")
                transform(soup, source_path=Path("not-on-disk.rst"))
                self.assertEqual(str(soup), replay)
                with self.assertRaises(ValueError):
                    render_web_table_ir(replace(ir, content_sha256="0" * 64))
                if kind == "lcd":
                    self.assertEqual(("icon.png",), ir.asset_refs)

    def test_real_bundle_migrates_renamed_csv_consumers(self):
        from tools.manual_ir import build_manual_ir_from_source
        from tools.word_bundle_html import build_word_bundle_html

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pages = root / "page"
            pages.mkdir()
            (pages / "icon.png").write_bytes(b"frozen test icon")
            fixtures = [
                ("status_legend", "lcd_icons", lcd_table(False)),
                (
                    "error_help",
                    "troubleshooting",
                    source_table(declared=False, head=False),
                ),
            ]
            for slot, _, markup in fixtures:
                (pages / f"{slot}.rst").write_text(
                    ".. raw:: html\n\n   " + markup + "\n"
                )
            cfg = {
                "build": {"languages": ["ja"]},
                "pages": [
                    {
                        "type": "csv_page",
                        "source": "phase2",
                        "page": kind,
                        "langs": ["ja"],
                        "slot_id": slot,
                    }
                    for slot, kind, _ in fixtures
                ],
            }
            bundle = SimpleNamespace(
                bundle_dir=root,
                page_dir=pages,
                page_paths=tuple(pages / f"{slot}.rst" for slot, _, _ in fixtures),
                title="Manual",
                reference_doc=None,
                model="OTHER",
                region="JP",
                lang="ja",
                languages=("ja",),
            )
            with patch(
                "tools.web_table_ir.build_manual_ir_from_source",
                wraps=build_manual_ir_from_source,
            ) as assemble:
                output, _, _ = build_word_bundle_html(
                    cfg,
                    "OTHER",
                    "JP",
                    materialized_bundle=bundle,
                    output_dir=root / "web",
                    presentation_profile="web",
                )
            self.assertEqual(2, assemble.call_count)
            self.assertEqual(
                ["lcd", "troubleshooting"],
                [
                    call.args[0].pages[0].blocks[0][1]["table_kind"]
                    for call in assemble.call_args_list
                ],
            )
            for call in assemble.call_args_list:
                self.assertEqual(
                    ("OTHER", "JP", "ja"),
                    (call.args[0].model, call.args[0].region, call.args[0].language),
                )
            soup = BeautifulSoup(output.read_text(), "html.parser")
            self.assertEqual(1, len(soup.select("figure.hb-lcd-table-composition")))
            self.assertEqual(
                1, len(soup.select("figure.hb-troubleshooting-composition"))
            )
            self.assertEqual("Wireless", soup.img["alt"])
            self.assertEqual("#support", soup.a["href"])

    def test_rehashed_semantic_drift_and_unsupported_blocks_fail(self):
        from tools.manual_ir import build_manual_ir_from_source
        from tools.manual_ir.web_tables import load_web_table_source
        from tools.web_table_ir import render_web_table_ir

        source = load_web_table_source(
            source_table(), table_kind="troubleshooting", source_path=Path("x.rst")
        )
        page = source.pages[0]
        for kind, change in (
            ("web_table", lambda payload: payload["rows"][0].update(code="WRONG")),
            ("web_table", lambda payload: payload.update(table_kind="unknown")),
            ("other", lambda payload: None),
        ):
            payload = copy.deepcopy(page.blocks[0][1])
            change(payload)
            changed = replace(source, pages=(replace(page, blocks=((kind, payload),)),))
            with self.assertRaises(ValueError):
                render_web_table_ir(build_manual_ir_from_source(changed))

    def test_staged_runtime_replays_ir_without_checkout_or_legacy_adapter(self):
        from tools.plain_markdown_site import stage_component_extension

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertTrue(stage_component_extension(root))
            runtime = root / "_ext"
            self.assertFalse((runtime / "tools/manual_ir/prepared_rst.py").exists())
            script = f"""
import sys, importlib.abc
sys.path.insert(0, {str(runtime)!r})
class BlockLegacy(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(('tools.idml', 'idml')) or fullname == 'tools.manual_ir.prepared_rst':
            raise AssertionError(fullname)
sys.meta_path.insert(0, BlockLegacy())
from pathlib import Path
from tools.manual_ir import build_manual_ir_from_source, read_manual_ir, write_manual_ir
from tools.manual_ir.web_tables import load_web_table_source
from tools.web_table_ir import render_web_table_ir
source = load_web_table_source({lcd_table()!r}, table_kind='lcd', source_path=Path('missing.rst'))
ir = build_manual_ir_from_source(source)
assert ir.asset_refs == ('icon.png',)
write_manual_ir(ir, Path('ir.json'))
assert 'hb-lcd-table-composition' in ''.join(render_web_table_ir(read_manual_ir(Path('ir.json'))))
"""
            result = subprocess.run(
                [sys.executable, "-I", "-c", script],
                cwd=root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
