"""Public IR is the real callout handoff across the Pandoc boundary."""
from __future__ import annotations

import unittest

from tools.manual_ir import ManualIR
from tools.web_presentation import protect_web_callouts_for_pandoc


TABLE = ('<table class="manual-callout-table" lang="en"><tbody><tr>'
         '<td class="manual-callout-label">WARNING</td>'
         '<td class="manual-callout-body"><p>Keep <strong>dry</strong>.</p>'
         '<ul><li>A &amp; B</li><li><img src="icons/warning.svg"/>Tip</li></ul>'
         '</td></tr></tbody></table>')


class WebCalloutIRTests(unittest.TestCase):
    def test_pandoc_handoff_carries_public_ir(self) -> None:
        _, protected = protect_web_callouts_for_pandoc(TABLE)
        self.assertEqual(len(protected), 1)
        self.assertIsInstance(next(iter(protected.values())), ManualIR)

    def test_serialized_replay_preserves_bytes_assets_and_provenance(self) -> None:
        from hashlib import sha256
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from tools.manual_ir import read_manual_ir, write_manual_ir
        from tools.web_callout_ir import render_callout_ir
        from tools.web_presentation import restore_web_callouts_after_pandoc

        with TemporaryDirectory() as td:
            source = Path(td) / 'bundle.html'
            source.write_text(TABLE)
            _, protected = protect_web_callouts_for_pandoc(
                TABLE, source_path=source, model='MODEL', region='US',
            )
            token, ir = next(iter(protected.items()))
            self.assertEqual((ir.model, ir.region, ir.language), ('MODEL', 'US', 'en'))
            self.assertEqual(ir.bundle_sha256, sha256(TABLE.encode()).hexdigest())
            self.assertIsNone(ir.snapshot_sha256)
            self.assertEqual(ir.asset_refs, ('icons/warning.svg',))
            self.assertEqual(ir.pages[0].source_path, f'{source}#{token}')
            saved = write_manual_ir(ir, Path(td) / 'ir.json')
            source.unlink()
            replay = read_manual_ir(saved)
            self.assertEqual(render_callout_ir(replay), TABLE)
            self.assertEqual(restore_web_callouts_after_pandoc(token, {token: replay}), f'\n\n{TABLE}\n\n')

    def test_corrupt_envelope_rejects_both_handoff_boundaries(self) -> None:
        from dataclasses import replace
        from unittest.mock import patch
        from tools import web_presentation
        from tools.manual_ir import build_manual_ir_from_source

        def corrupt(source):
            return replace(build_manual_ir_from_source(source), content_sha256='0' * 64)

        with patch.object(web_presentation, 'build_manual_ir_from_source', side_effect=corrupt):
            with self.assertRaisesRegex(web_presentation.WebPresentationError, 'Manual IR'):
                web_presentation.protect_web_callouts_for_pandoc(TABLE)
        _, protected = web_presentation.protect_web_callouts_for_pandoc(TABLE)
        token, ir = next(iter(protected.items()))
        protected[token] = replace(ir, content_sha256='0' * 64)
        with self.assertRaisesRegex(web_presentation.WebPresentationError, 'Manual IR'):
            web_presentation.restore_web_callouts_after_pandoc(token, protected)

    def test_rehashed_semantic_or_asset_drift_is_not_accepted(self) -> None:
        from dataclasses import replace
        from pathlib import Path
        from tools.manual_ir import build_manual_ir_from_source, validate_manual_ir
        from tools.manual_ir.web_callouts import load_web_callout_source
        from tools.web_callout_ir import render_callout_ir

        for change in ('body', 'variant', 'asset', 'kind', 'projection', 'extra-field'):
            with self.subTest(change=change):
                source = load_web_callout_source(TABLE, source_path=Path('demo.html'))
                payload = source.pages[0].blocks[0][1]
                if change == 'body':
                    payload['component_spec']['slots'][1]['content'] = 'Different copy'
                elif change == 'variant':
                    payload['component_spec']['variant'] = 'tip'
                elif change == 'asset':
                    payload['markup_assets'] = []
                elif change == 'extra-field':
                    payload['unexpected'] = 'not rendered'
                elif change == 'projection':
                    source.metadata['projection'] = 'another-projection'
                page = replace(source.pages[0], blocks=((
                    'another-kind' if change == 'kind' else 'web_callout', payload,
                ),))
                ir = build_manual_ir_from_source(replace(source, pages=(page,)))
                self.assertEqual(validate_manual_ir(ir), [])  # Valid envelope, invalid owned payload.
                with self.assertRaises(ValueError):
                    render_callout_ir(ir)

    def test_malformed_later_callout_fails_without_returning_partial_output(self) -> None:
        from tools.web_presentation import WebPresentationError
        malformed = [
            TABLE.replace('</tr>', '<td>Lost extra cell</td></tr>'),
            TABLE.replace('</tbody>', '<tr><td>Lost row</td></tr></tbody>'),
            TABLE.replace('manual-callout-body', 'missing-body'),
            TABLE.replace('manual-callout-label', 'manual-callout-body'),
            TABLE.replace('<td class="manual-callout-body"', '<td rowspan="2" class="manual-callout-body"'),
            TABLE.replace('Keep ', '<table><tr><td>Nested</td></tr></table>Keep '),
            TABLE.replace('WARNING', 'UNKNOWN-SIGNAL'),
        ]
        for html in malformed:
            with self.subTest(html=html):
                with self.assertRaises(WebPresentationError):
                    protect_web_callouts_for_pandoc(TABLE + html)
        ordinary = '<table><tr><td>Untyped</td></tr></table>'
        self.assertEqual(protect_web_callouts_for_pandoc(ordinary), (ordinary, {}))

    def test_real_pandoc_bridge_consumes_public_ir(self) -> None:
        import re
        import subprocess
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from types import SimpleNamespace
        from unittest.mock import patch
        from tools import markdown_bundle, web_presentation
        from tools.web_callout_ir import render_callout_ir
        from tools.manual_ir import build_manual_ir_from_source

        with TemporaryDirectory() as td:
            root = Path(td)
            source = root / 'bundle.html'
            source.write_text('<html><body>' + TABLE + '</body></html>')
            output = root / 'manual.md'
            # Actual Pandoc invocation; the upstream builder is the separate
            # RST/Word boundary and is replaced with prepared HTML in this test.
            try:
                pandoc = markdown_bundle.resolve_pandoc_binary(None)
                subprocess.run([pandoc, '--version'], check=True, capture_output=True)
            except (OSError, RuntimeError, subprocess.CalledProcessError):
                self.skipTest('Pandoc unavailable')
            with patch.dict(markdown_bundle.os.environ, {'AUTO_MANUAL_PRESENTATION_PROFILE': 'web'}), \
                 patch.object(markdown_bundle, 'build_word_bundle_html', return_value=(source, None, ())), \
                 patch.object(web_presentation, 'build_manual_ir_from_source', wraps=build_manual_ir_from_source) as assembler, \
                 patch.object(web_presentation, 'render_callout_ir', wraps=render_callout_ir) as renderer:
                markdown_bundle.export_markdown_from_bundle(
                    {}, 'MODEL', 'US', str(output),
                    materialized_bundle=SimpleNamespace(title='Demo'), output_dir=root,
                )
            self.assertEqual(assembler.call_count, 1)
            self.assertEqual(renderer.call_count, 2)
            ir = renderer.call_args.args[0]
            self.assertEqual(ir.model, 'MODEL')
            self.assertEqual(ir.region, 'US')
            self.assertTrue(ir.pages[0].source_path.startswith(str(source)))
            result = output.read_text()
            self.assertIn(TABLE, result)
            self.assertIsNone(re.search(r'AUTOMANUALWEBCALLOUT\d+', result))

    def test_rst_to_markdown_bundle_uses_ir_in_both_languages(self) -> None:
        import re
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from types import SimpleNamespace
        from unittest.mock import patch
        from tools import markdown_bundle, web_presentation
        from tools.manual_ir import build_manual_ir_from_source

        def fake_pandoc(command, **kwargs):
            # The CI unit runner has no Pandoc. Keep RST rendering and public
            # IR real here; the separate integration test exercises Pandoc.
            html = Path(command[1]).read_text()
            tokens = re.findall(r'AUTOMANUALWEBCALLOUT\d{4}PLACEHOLDER', html)
            Path(command[command.index('-o') + 1]).write_text('\n\n'.join(tokens))
            return SimpleNamespace(stdout='')

        for language, region, label in (('en', 'US', 'WARNING'), ('ja', 'JP', 'ご注意')):
            with self.subTest(language=language), TemporaryDirectory() as td:
                root = Path(td)
                page = root / f'safety_{language}.rst'
                page.write_text('Safety\n======\n\n.. list-table::\n   :widths: 16 84\n\n'
                                f'   * - **{label}**\n     - Keep **dry**.\n')
                bundle = SimpleNamespace(title='Demo', reference_doc=None, model='OTHER',
                                         region=region, lang=language, languages=(language,),
                                         page_paths=(page,))
                with patch.dict(markdown_bundle.os.environ, {'AUTO_MANUAL_PRESENTATION_PROFILE': 'web'}), \
                     patch.object(markdown_bundle, 'resolve_pandoc_binary', return_value='pandoc'), \
                     patch.object(markdown_bundle, 'resolve_markdown_writer', return_value='myst'), \
                     patch.object(markdown_bundle.subprocess, 'run', side_effect=fake_pandoc), \
                     patch.object(web_presentation, 'build_manual_ir_from_source', wraps=build_manual_ir_from_source) as assembler:
                    output = markdown_bundle.export_markdown_from_bundle(
                        {}, 'OTHER', region, str(root / 'manual.md'),
                        materialized_bundle=bundle, output_dir=root / 'out',
                    )
                assembler.assert_called_once()
                source = assembler.call_args.args[0]
                self.assertEqual((source.model, source.region), ('OTHER', region))
                text = output.read_text()
                self.assertIn(label, text)
                self.assertIn('manual-callout-table', text)
                self.assertNotIn('AUTOMANUALWEBCALLOUT', text)
