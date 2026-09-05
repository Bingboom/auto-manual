"""Standalone callouts keep Sphinx rich nodes and consume shared public IR."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from bs4 import BeautifulSoup

from tools.manual_ir import read_manual_ir
from tools.plain_markdown_site import stage_component_extension, write_conf_py
from tools.web_callout_ir import render_callout_ir


DOCUMENT = '''# Manual

```{callout} CUSTOM LABEL
:variant: caution

Keep **dry** and *safe*. [Target](#target).

- One
- Two with `code`

![warning](warning.svg)
```

```{callout} WARNING
Default variant.
```

(target)=
## Reference target

Text.
'''

CAPTURE = '''
language = 'ja'
import manual_md_directives as carrier
from tools.manual_ir import write_manual_ir, read_manual_ir
from tools.web_callout_ir import render_callout_ir
from dataclasses import replace
_original = carrier.build_manual_ir_from_source
_count = 0
def capture(source):
    global _count
    _count += 1
    ir = _original(source)
    write_manual_ir(ir, Path(__file__).parent / f'captured-{_count}.json')
    if (Path(__file__).parent / 'corrupt').exists():
        return replace(ir, content_sha256='0' * 64)
    return ir
carrier.build_manual_ir_from_source = capture
def replay(ir):
    saved = write_manual_ir(ir, Path(__file__).parent / 'replay.json')
    return render_callout_ir(read_manual_ir(saved))
carrier.render_callout_ir = replay
'''


class MystCalloutIRTests(unittest.TestCase):
    def _stage(self, root: Path) -> tuple[Path, list[str]]:
        source = root / 'source'
        source.mkdir()
        (source / '_static').mkdir()
        self.assertTrue(stage_component_extension(source))
        conf = write_conf_py(source, title='Manual')
        with conf.open('a') as stream:
            stream.write(CAPTURE)
        (source / 'index.md').write_text(DOCUMENT)
        (source / 'warning.svg').write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12"><rect width="12" height="12"/></svg>'
        )
        command = [sys.executable, '-I', '-m', 'sphinx', '-E', '-W', '-b', 'html', str(source), str(root / 'html')]
        return source, command

    def test_isolated_sphinx_keeps_resolved_rich_content_through_ir(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, command = self._stage(root)
            result = subprocess.run(command, cwd=root, text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            irs = [read_manual_ir(p) for p in sorted(source.glob('captured-*.json'))]
            self.assertEqual(2, len(irs))
            self.assertTrue(all(ir.language == 'ja' for ir in irs))
            self.assertTrue(all(ir.metadata['projection'] == 'web-callout' for ir in irs))
            first = irs[0]
            payload = first.pages[0].blocks[0].payload
            self.assertEqual('caution', payload['component_spec']['variant'])
            self.assertIn('index:', first.pages[0].source_ref)
            self.assertTrue(first.asset_refs[0].endswith('warning.svg'))
            replay = BeautifulSoup(render_callout_ir(first), 'html.parser')
            self.assertEqual('CUSTOM LABEL', replay.select_one('.manual-callout-label').text)
            self.assertEqual('#target', replay.select_one('.manual-callout-body a')['href'])
            self.assertEqual(2, len(replay.select('li')))
            self.assertEqual('dry', replay.select_one('.manual-callout-body strong').text)
            actual = BeautifulSoup((root / 'html/index.html').read_text(), 'html.parser')
            self.assertEqual(str(replay.table), str(actual.select_one('table.manual-callout-table')))
            self.assertNotIn('data-ir', str(actual))

    def test_corrupt_ir_fails_isolated_sphinx(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, command = self._stage(root)
            (source / 'corrupt').touch()
            result = subprocess.run(command, cwd=root, text=True, capture_output=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn('Manual IR', result.stdout + result.stderr)

    def test_declaration_schema_and_rehashed_disagreement_reject(self):
        from dataclasses import replace
        from tools.manual_ir import build_manual_ir_from_source, validate_manual_ir
        from tools.manual_ir.web_callouts import load_web_callout_source
        from tests.test_web_callout_ir import TABLE

        html = TABLE.replace(' lang="en"', '')
        for declaration in ({}, {'language': 'ja'}, {'language': [], 'variant': None},
                            {'language': 'ja', 'variant': 'neon'},
                            {'language': 'ja', 'variant': ['warning']},
                            {'language': 'ja', 'variant': None, 'extra': True}):
            with self.subTest(declaration=declaration), self.assertRaisesRegex(ValueError, 'declaration'):
                load_web_callout_source(html, source_path=Path('index:3'), declaration=declaration)
        source = load_web_callout_source(
            html, source_path=Path('index:3'), declaration={'language': 'ja', 'variant': 'warning'},
        )
        # Recompute valid envelope hashes; consumer must still catch a conflict
        # between the explicit declaration and the stored ComponentSpec.
        source.pages[0].blocks[0][1]['declaration']['variant'] = 'tip'
        ir = build_manual_ir_from_source(source)
        self.assertEqual(validate_manual_ir(ir), [])
        with self.assertRaisesRegex(ValueError, 'semantics/assets'):
            render_callout_ir(ir)
        with self.assertRaises(ValueError):
            render_callout_ir(replace(ir, metadata={**ir.metadata, 'projection': 'wrong'}))

    def test_nested_tables_fail_explicitly_at_shared_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, command = self._stage(root)
            (source / 'index.md').write_text(
                '# Manual\n\n```{callout} WARNING\n\n| A | B |\n| --- | --- |\n| One | Two |\n```\n'
            )
            result = subprocess.run(command, cwd=root, text=True, capture_output=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn('index:3', result.stdout + result.stderr)
            self.assertIn('callout requires one row', result.stdout + result.stderr)

    def test_non_html_writer_keeps_body_without_unknown_node_error(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, command = self._stage(root)
            command[command.index('html')] = 'text'
            result = subprocess.run(command, cwd=root, text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn('Keep', (root / 'html/index.txt').read_text())
            self.assertEqual([], list(source.glob('captured-*.json')))
