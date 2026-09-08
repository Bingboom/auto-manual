"""The Inbox composite consumes public IR at the actual Web entrypoint."""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from tools import web_inbox_component
from tools.manual_ir import (
    build_manual_ir_from_source, read_manual_ir, validate_manual_ir, write_manual_ir,
)
from tools.web_presentation import WebPresentationError, transform_web_fragment


HTML = (
    '<h1>In <em>the box</em></h1>\n'
    '<table><tbody><tr>'
    '<td><img src="unit.svg" width="40"/><strong>Unit</strong></td>'
    '<td><img src="cable.svg"/>Cable</td>'
    '<td><img src="manual.svg"/>Manual</td>'
    '</tr></tbody></table>\n'
    '<table><tbody><tr><td>TIP</td><td><p>Keep <strong>dry</strong>.</p>'
    '<ul><li><a href="https://example.com">Support</a></li>'
    '<li><img src="tip.svg"/>Read first</li></ul></td></tr></tbody></table>'
    '<p id="after">Unrelated copy</p>'
)


FIVE_CARD_HTML = (
    '<h1>What\'s in the Box</h1>\n'
    '<table><tbody><tr>'
    + "".join(
        f'<td><img src="item-{index}.svg"/><strong>Item {index}</strong></td>'
        for index in range(1, 6)
    )
    + '</tr></tbody></table>\n'
    '<table><tbody><tr><td>NOTE</td><td>Item 3 is for JS-100I only.</td>'
    '</tr></tbody></table>'
)


class WebInboxIRTests(unittest.TestCase):
    def test_three_card_source_without_tip_is_a_complete_component(self) -> None:
        from tools.manual_ir.web_inbox import load_web_inbox_source
        from tools.web_inbox_component import render_inbox_ir

        html = HTML.split("\n<table><tbody><tr><td>TIP", 1)[0] + '<p id="after">After</p>'
        source = load_web_inbox_source(
            html,
            source_path=Path("box_contents_en.rst"),
            language="en",
            model="JBP-3600A",
            region="EU",
        )
        result = render_inbox_ir(build_manual_ir_from_source(source))
        soup = BeautifulSoup(result, "html.parser")

        self.assertEqual(3, len(soup.select(".hb-inbox-card")))
        self.assertIsNone(soup.select_one(".hb-inbox-tip"))
        spec = source.pages[0].blocks[0][1]["component_spec"]
        self.assertEqual("", spec["slots"][-1]["content"])

    def test_five_card_variant_round_trips_public_ir_and_reflows_on_web(self) -> None:
        from tools.manual_ir.web_inbox import load_web_inbox_source
        from tools.web_inbox_component import render_inbox_ir

        source = load_web_inbox_source(
            FIVE_CARD_HTML,
            source_path=Path("box_contents_js100i.rst"),
            language="en",
            model="JS-100I",
            region="EU",
        )
        ir = build_manual_ir_from_source(source)
        result = render_inbox_ir(ir)
        soup = BeautifulSoup(result, "html.parser")
        composition = soup.select_one("figure.hb-inbox-composition")
        self.assertIsNotNone(composition)
        self.assertEqual("responsive-card-grid", composition["data-inbox-variant"])
        self.assertEqual("5", composition["data-card-count"])
        self.assertEqual(5, len(soup.select(".hb-inbox-card")))
        self.assertEqual(
            [f"item-{index}.svg" for index in range(1, 6)],
            [image["src"] for image in soup.select("img.hb-inbox-art")],
        )
        self.assertEqual(
            {f"item-{index}.svg" for index in range(1, 6)},
            set(ir.asset_refs),
        )

    def test_five_card_source_without_tip_preserves_both_contract_extensions(self) -> None:
        from tools.manual_ir.web_inbox import load_web_inbox_source
        from tools.web_inbox_component import render_inbox_ir

        html = FIVE_CARD_HTML.split('<table><tbody><tr><td>NOTE', 1)[0]
        source = load_web_inbox_source(
            html, source_path=Path("box_contents_en.rst"), language="en",
            model="JS-100I", region="EU",
        )
        soup = BeautifulSoup(render_inbox_ir(build_manual_ir_from_source(source)), "html.parser")
        self.assertEqual(5, len(soup.select(".hb-inbox-card")))
        self.assertIsNone(soup.select_one(".hb-inbox-tip"))

    def test_real_rst_entrypoint_assembles_ir_for_three_locales(self) -> None:
        from tests.test_web_presentation import _web_fragment

        for name in ('02_whats_in_the_box.rst', 'p23_02_whats_in_the_box.rst',
                     'p39_02_whats_in_the_box.rst'):
            with self.subTest(name=name), patch.object(
                web_inbox_component, 'build_manual_ir_from_source',
                wraps=build_manual_ir_from_source, create=True,
            ) as assembler:
                result = _web_fragment(name)
                assembler.assert_called_once()
                source = assembler.call_args.args[0]
                self.assertEqual(source.metadata['projection'], 'web-inbox')
                self.assertEqual((source.model, source.region), ('JE-1000F', 'US'))
                soup = BeautifulSoup(result, 'html.parser')
                self.assertEqual(len(soup.select('.hb-inbox-card')), 3)
                self.assertIsNotNone(soup.select_one('.hb-inbox-tip-body'))

    def test_actual_context_and_common_source_pattern(self) -> None:
        for language, label in (('en', 'TIP'), ('fr', 'CONSEILS'), ('es', 'CONSEJOS')):
            with self.subTest(language=language), patch.object(
                web_inbox_component, 'build_manual_ir_from_source',
                wraps=build_manual_ir_from_source,
            ) as assembler:
                path = Path('/tmp/docs/_review/JE-1000F/US/page/02_whats_in_the_box.rst')
                result = transform_web_fragment(
                    HTML.replace('TIP', label), source_path=path,
                    language=language, model='JE-1000F', region='US',
                )
                assembler.assert_called_once()
                self.assertEqual(assembler.call_args.args[0].language, language)
                self.assertIn(label, result)
                self.assertIn('<p id="after">Unrelated copy</p>', result)
                self.assertIn('<h1>In <em>the box</em></h1>', result)
        with patch.object(
            web_inbox_component,
            'build_manual_ir_from_source',
            wraps=build_manual_ir_from_source,
        ) as assembler:
            result = transform_web_fragment(
                HTML, source_path=Path('/tmp/docs/_review/OTHER/XX/page/02_whats_in_the_box.rst'),
                language='en', model='OTHER', region='XX',
            )
            assembler.assert_called_once()
            soup = BeautifulSoup(result, 'html.parser')
            self.assertEqual(3, len(soup.select('.hb-inbox-card')))
            self.assertEqual(
                ['1', '2', '3'],
                [str(card['data-item-number']) for card in soup.select('.hb-inbox-card')],
            )

    def test_serialized_replay_preserves_rich_tip_assets_without_source(self) -> None:
        from tools.manual_ir.web_inbox import load_web_inbox_source
        from tools.web_inbox_component import render_inbox_ir

        with TemporaryDirectory() as td:
            source_path = Path(td) / 'inbox.html'
            source_path.write_text(HTML)
            source = load_web_inbox_source(
                HTML, source_path=source_path, language='ja', model='MODEL', region='JP',
            )
            ir = build_manual_ir_from_source(source)
            expected = render_inbox_ir(ir)
            self.assertEqual((ir.model, ir.region, ir.language), ('MODEL', 'JP', 'ja'))
            self.assertEqual(ir.bundle_sha256, sha256(HTML.encode()).hexdigest())
            self.assertIsNone(ir.snapshot_sha256)
            self.assertEqual(set(ir.asset_refs), {'unit.svg', 'cable.svg', 'manual.svg', 'tip.svg'})
            saved = write_manual_ir(ir, Path(td) / 'ir.json')
            source_path.unlink()
            result = render_inbox_ir(read_manual_ir(saved))
            self.assertEqual(result, expected)
            self.assertIn('<p>Keep <strong>dry</strong>.</p>', result)
            self.assertIn('<a href="https://example.com">Support</a>', result)
            self.assertIn('<li><img src="tip.svg"/>Read first</li>', result)

    def test_corrupt_ir_fails_before_mutating_caller(self) -> None:
        def corrupt(source):
            return replace(build_manual_ir_from_source(source), content_sha256='0' * 64)

        soup = BeautifulSoup(HTML, 'html.parser')
        before = str(soup)
        with patch.object(web_inbox_component, 'build_manual_ir_from_source', side_effect=corrupt):
            with self.assertRaisesRegex(WebPresentationError, 'Manual IR'):
                web_inbox_component.transform_inbox(
                    soup, source_path=Path('inbox.html'), language='en', error_type=WebPresentationError,
                )
        self.assertEqual(str(soup), before)

    def test_rehashed_payload_drift_is_rejected(self) -> None:
        from tools.manual_ir.web_inbox import load_web_inbox_source
        from tools.web_inbox_component import render_inbox_ir

        for change in ('tip', 'asset', 'kind', 'projection', 'extra'):
            with self.subTest(change=change):
                source = load_web_inbox_source(HTML, source_path=Path('inbox.html'), language='en')
                payload = source.pages[0].blocks[0][1]
                if change == 'tip':
                    payload['component_spec']['slots'][-1]['content'] = 'Different copy'
                elif change == 'asset':
                    payload['markup_assets'] = []
                elif change == 'projection':
                    source.metadata['projection'] = 'other'
                elif change == 'extra':
                    payload['lost_content'] = 'Not rendered'
                page = replace(source.pages[0], blocks=((
                    'other' if change == 'kind' else 'web_inbox', payload,
                ),))
                ir = build_manual_ir_from_source(replace(source, pages=(page,)))
                self.assertEqual(validate_manual_ir(ir), [])
                with self.assertRaises(ValueError):
                    render_inbox_ir(ir)

    def test_malformed_tip_or_cards_leave_caller_unchanged(self) -> None:
        cases = (
            HTML.replace('<td>TIP</td>', '<td colspan="2">TIP</td>'),
            HTML.replace('</tbody>', '<tr></tr></tbody>'),
            HTML.replace('Keep ', '<table><tr><td>Nested</td></tr></table>Keep '),
            HTML.replace('<td>TIP</td>', ''),
            HTML.replace('src="unit.svg"', 'src=""'),
        )
        for html in cases:
            with self.subTest(html=html):
                soup = BeautifulSoup(html, 'html.parser')
                before = str(soup)
                with self.assertRaises(WebPresentationError):
                    web_inbox_component.transform_inbox(
                        soup, source_path=Path('inbox.html'), language='en', error_type=WebPresentationError,
                    )
                self.assertEqual(str(soup), before)
