from __future__ import annotations

from dataclasses import replace
import copy
import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from tests.test_web_spec_component import declared_table
from tools.manual_ir import read_manual_ir, write_manual_ir
from tools.web_presentation import WebPresentationError, transform_web_fragment
from tools.word_bundle_html import build_word_bundle_html


class WebManualIRTests(unittest.TestCase):
    def test_real_web_bundle_exits_word_spec_parser_and_preserves_rich_content(self):
        from tools.manual_ir import build_manual_ir_from_source

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            preface = root / "00_preface.rst"
            preface.write_text("IMPORTANT\n=========\n\nRead first.\n")
            spec = root / "spec_en.rst"
            fragment = (
                "<h1>Specs</h1>"
                + declared_table(
                    '<tr><td>Input①</td><td><a href="#note">100 V</a><br/><em>200 V</em></td></tr>'
                )
                + '<p id="note">① Note.</p>'
            )
            spec.write_text(".. raw:: html\n\n   " + fragment + "\n")
            bundle = SimpleNamespace(
                title="Example",
                reference_doc=None,
                model="JE-1000F",
                region="US",
                lang="en",
                languages=("en",),
                page_paths=(preface, spec),
            )
            with (
                patch(
                    "tools.word_bundle_html._extract_spec_word_data",
                    side_effect=AssertionError("legacy Word parser"),
                ),
                patch(
                    "tools.web_spec_component.build_manual_ir_from_source",
                    wraps=build_manual_ir_from_source,
                ) as assemble,
            ):
                result, _, _ = build_word_bundle_html(
                    {},
                    "JE-1000F",
                    "US",
                    materialized_bundle=bundle,
                    output_dir=root / "out",
                    presentation_profile="web",
                )
            self.assertEqual(1, assemble.call_count)
            source = assemble.call_args.args[0]
            self.assertEqual(
                ("JE-1000F", "US", "en"), (source.model, source.region, source.language)
            )
            soup = BeautifulSoup(result.read_text(), "html.parser")
            self.assertEqual(
                "#note",
                soup.select_one("figure.hb-spec-table-composition td a")["href"],
            )
            self.assertEqual("200 V", soup.select_one("figure td em").text)
            self.assertEqual("① Note.", soup.select_one("#note").text)

    def test_later_malformed_section_does_not_partially_mutate_dom(self):
        from tools.web_spec_component import transform_specification_tables

        source = declared_table("<tr><td>A</td><td>B</td></tr>") + declared_table(
            "<tr><td>missing</td></tr>"
        )
        soup = BeautifulSoup(source, "html.parser")
        before = str(soup)
        with self.assertRaises(WebPresentationError):
            transform_specification_tables(
                soup,
                source_path=Path("x.rst"),
                language="ja",
                error_type=WebPresentationError,
            )
        self.assertEqual(before, str(soup))

    def test_serialized_projection_replays_without_source_file(self):
        from tools.manual_ir import build_manual_ir_from_source
        from tools.manual_ir.web_specs import load_web_spec_source
        from tools.web_spec_component import render_specification_ir

        source = declared_table("<tr><td>Input</td><td><em>100 V</em></td></tr>")
        adapter = load_web_spec_source(
            source, source_path=Path("nonexistent.rst"), language="ja"
        )
        ir = build_manual_ir_from_source(adapter)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manual_ir.json"
            write_manual_ir(ir, path)
            replay = "".join(render_specification_ir(read_manual_ir(path)))
        self.assertEqual(
            transform_web_fragment(
                source, source_path=Path("nonexistent.rst"), language="ja"
            ),
            replay,
        )
        with self.assertRaises(ValueError):
            render_specification_ir(replace(ir, content_sha256="0" * 64))

    def test_rich_markup_and_semantics_cannot_drift_even_with_valid_hashes(self):
        from tools.manual_ir import build_manual_ir_from_source
        from tools.manual_ir.web_specs import load_web_spec_source
        from tools.web_spec_component import render_specification_ir

        source = load_web_spec_source(
            declared_table("<tr><td>Input</td><td>100 V</td></tr>"),
            source_path=Path("input.rst"),
            language="ja",
        )
        page = source.pages[0]
        payload = copy.deepcopy(page.blocks[0][1])
        payload["table_html"] = payload["table_html"].replace("100 V", "200 V")
        changed = replace(
            source, pages=(replace(page, blocks=(("web_specification", payload),)),)
        )
        with self.assertRaisesRegex(ValueError, "semantics do not match"):
            render_specification_ir(build_manual_ir_from_source(changed))

    def test_component_locale_assets_and_scoped_provenance_survive_public_roundtrip(
        self,
    ):
        from tools.manual_ir import build_manual_ir_from_source, validate_manual_ir
        from tools.manual_ir.web_specs import load_web_spec_source

        html = declared_table(
            '<tr><td>入力</td><td><img src="symbol.svg"/>100 V</td></tr>'
        ).replace(
            'class="manual-spec-table"',
            'class="manual-spec-table" lang="ja"',
        )
        source = load_web_spec_source(
            html, source_path=Path("renamed.rst"), language="en"
        )
        ir = build_manual_ir_from_source(source)
        self.assertEqual([], validate_manual_ir(ir, require_zero_skipped_raw=True))
        self.assertEqual(("symbol.svg",), ir.asset_refs)
        self.assertEqual(
            "ja", ir.pages[0].blocks[0].payload["component_spec"]["language"]
        )
        self.assertEqual("web-specifications", ir.metadata["projection"])
        self.assertIsNone(ir.snapshot_sha256)
        self.assertNotEqual(
            source.bundle_sha256,
            load_web_spec_source(
                html.replace("100 V", "200 V"),
                source_path=Path("renamed.rst"),
                language="en",
            ).bundle_sha256,
        )

    def test_web_ir_path_cannot_import_legacy_idml_extraction(self):
        script = textwrap.dedent("""
            import importlib.abc
            import sys
            class ForbidLegacy(importlib.abc.MetaPathFinder):
                def find_spec(self, fullname, path=None, target=None):
                    if fullname.startswith(('tools.idml', 'idml')) or fullname == 'tools.manual_ir.prepared_rst':
                        raise AssertionError('legacy import: ' + fullname)
            sys.meta_path.insert(0, ForbidLegacy())
            from tools.web_spec_component import transform_specification_tables
            from bs4 import BeautifulSoup
            from pathlib import Path
            soup = BeautifulSoup('<h2 class="hb-spec-section"><span class="hb-spec-section-text">Test</span></h2><table class="hb-spec-table"><tbody><tr><td>A</td><td>B</td></tr></tbody></table>', 'html.parser')
            assert transform_specification_tables(soup, source_path=Path('x.rst'), language='en', error_type=ValueError)
            assert soup.select_one('figure.hb-spec-table-composition')
        """)
        result = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, text=True
        )
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
