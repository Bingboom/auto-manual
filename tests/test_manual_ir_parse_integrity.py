"""Source omissions must not produce a clean strict IR or trusted handoff."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace

from tools.idml.design_handoff import _skipped_raw_blocks, write_handoff_package
from tools.idml_rst_extract import ExtractResult, _extract_raw_latex, _parse_text
from tools.idml.latex_conditionals import active_lines
from tools.manual_ir import ManualIRValidationError

ROOT = Path(__file__).resolve().parents[1]


class ManualIRParseIntegrityTests(unittest.TestCase):
    def _strict_cli(self, raw, *, missing=False):
        with tempfile.TemporaryDirectory() as folder:
            bundle = Path(folder)
            (bundle / 'page').mkdir()
            (bundle / 'page/intro_ja.rst').write_text(
                'Title\n=====\n\n.. raw:: latex\n\n   ' + raw + '\n', encoding='utf-8')
            (bundle / 'index.rst').write_text('.. include:: page/intro_ja.rst\n' + (
                '\n.. include:: page/missing_ja.rst\n' if missing else ''), encoding='utf-8')
            output = bundle / 'existing.json'
            output.write_bytes(b'preserve existing output')
            run = subprocess.run([
                sys.executable, '-m', 'tools.manual_ir_cli', '--bundle-root', str(bundle),
                '--model', 'TEST', '--region', 'JP', '--lang', 'ja', '--strict',
                '--out', str(output),
            ], cwd=ROOT, capture_output=True, text=True, timeout=20)
            self.assertNotEqual(0, run.returncode, run.stdout + run.stderr)
            self.assertNotIn('Traceback', run.stdout + run.stderr)
            self.assertEqual(b'preserve existing output', output.read_bytes())
            return run.stdout + run.stderr

    def test_mixed_macro_residue_is_rejected_by_real_strict_cli(self):
        for raw in (r'\HBAppBody{KEPT}\UnknownMacro{LOST}',
                    r'\UnknownMacro{LOST}\HBAppBody{KEPT}',
                    r'\HBAppBody{ONE}unparsed prose\HBAppBody{TWO}'):
            with self.subTest(raw=raw):
                diagnostic = self._strict_cli(raw)
                self.assertIn('intro_ja', diagnostic)
                self.assertIn('skipped_raw', diagnostic)

    def test_incomplete_macro_is_not_emitted_as_a_success(self):
        for raw in (r'\HBAppBody{UNFINISHED', r'\HBAppStep{2}',
                    r'\HBNoticeBlock[tip]{NOTE}{UNFINISHED',
                    r'\HBNoticeBlock[tip no closing bracket'):
            with self.subTest(raw=raw):
                result = ExtractResult()
                _extract_raw_latex(raw, result)
                self.assertEqual([], result.blocks)
                self.assertGreater(result.skipped_raw, 0)
                self.assertIn('skipped_raw', self._strict_cli(raw))

    def test_declared_missing_page_is_rejected_before_existing_output_changes(self):
        diagnostic = self._strict_cli(r'\HBAppBody{KEPT}', missing=True)
        self.assertIn('missing_ja.rst', diagnostic)
        self.assertIn('index.rst', diagnostic)

    def test_complete_prose_macros_and_non_content_wrappers_remain_unchanged(self):
        result = ExtractResult()
        _extract_raw_latex(
            '\\HBApplyLang{ja}\n% ignored comment\n'
            + r'\HBAppBody{日本語}\HBAppStep{2}{Connect}\HBPageBreak{}', result)
        self.assertEqual([('body', '日本語'), ('h2', '2 Connect'),
                          ('layout', 'page_break')], result.blocks)
        self.assertEqual(0, result.skipped_raw)

    def test_existing_preface_and_page_break_wrappers_are_not_lost_content(self):
        raw = '\\HBPrefacePageBegin\n\\HBLangTagLine{EN}{IMPORTANT}'
        result = _parse_text('.. raw:: latex\n\n   ' + raw.replace('\n', '\n   '))
        self.assertEqual(0, result.skipped_raw)
        for marker in (r'\HBPageBreak', r'\HBPageBreak{}', r'\HBPageBreak {}'):
            with self.subTest(marker=marker):
                rst = '.. raw:: latex\n\n   ' + r'\HBAppBody{First}' + marker
                result = _parse_text(rst)
                self.assertEqual([('body', 'First'), ('layout', 'page_break')], result.blocks)
                self.assertEqual(0, result.skipped_raw)
        lines = [r'\HBPageBreak{}', r'\HBPageBreak', r'\HBPageBreakOther']
        normalized = active_lines(lines, {'latex'})
        self.assertEqual([r'\HBPageBreak{}', r'\HBPageBreak{}', r'\HBPageBreakOther'], normalized)
        self.assertEqual(normalized, active_lines(normalized, {'latex'}))

    def test_comment_braces_do_not_close_a_macro_argument(self):
        result = ExtractResult()
        _extract_raw_latex("\\HBAppBody{First % } ignored\n second}", result)
        self.assertEqual([('body', 'First second')], result.blocks)
        self.assertEqual(0, result.skipped_raw)
        broken = ExtractResult()
        _extract_raw_latex("\\HBAppBody{First % } ignored", broken)
        self.assertEqual([], broken.blocks)
        self.assertEqual(1, broken.skipped_raw)

    def test_handoff_bad_ir_rejected_before_any_output_is_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            production = root / 'source/manual.idml'
            production.parent.mkdir()
            production.write_bytes(b'not needed before IR validation')
            (production.parent / 'manual.ir.json').write_text(json.dumps({
                'schema_version': 'bad', 'pages': None, 'metadata': {'skipped_raw': 0},
            }))
            handoff = root / 'handoff'
            (handoff / 'production').mkdir(parents=True)
            existing = handoff / 'production/manual.production.idml'
            existing.write_bytes(b'keep old output')
            with self.assertRaises(ManualIRValidationError):
                write_handoff_package(
                    root=root, model='TEST', region='JP', lang='ja', data_root=root,
                    bundle_root=root, production_idml=production,
                    flow=SimpleNamespace(markdown=handoff / 'flow/manual.flow.md'),
                    build_command=[])
            self.assertEqual(b'keep old output', existing.read_bytes())
            self.assertEqual([existing], list((handoff / 'production').iterdir()))
            with self.assertRaises(ManualIRValidationError):
                _skipped_raw_blocks(production)

    def test_absent_ir_remains_explicitly_unavailable(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertIsNone(_skipped_raw_blocks(Path(folder) / 'manual.idml'))
