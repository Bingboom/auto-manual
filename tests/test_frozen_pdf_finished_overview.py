"""Finished panels retain semantic copy and replay from only two local assets."""
from copy import deepcopy
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from tools.component_specs.overview import overview_component_spec
from tools.component_specs.overview_instance import resolve_overview_instance
from tools.frozen_ai_flow import cell, node, table, text
from tools.frozen_ai_web import assemble_book, replay_package
from tools.frozen_pdf_finished_overview import bind_finished_overview
from tools.manual_ir.components import component_flow_node
from tools.manual_ir.hashing import file_sha256, value_sha256
from tools.manual_ir.source import SourcePage
from tools.web.presentation import load_web_manual_contract


class FinishedOverviewTests(unittest.TestCase):
    def _fixture(self, root, language='pl'):
        bindings = {'overview_finished_panels': {}}
        for locale in ('uk', 'pt', 'nl', 'pl'):
            bindings['overview_finished_panels'][locale] = {}
            for view in ('front', 'right'):
                source = root / f'{locale}-{view}.png'
                # Transport fixture only; no image decoder participates in replay.
                source.write_bytes(f'{locale}/{view} fixture'.encode())
                bindings['overview_finished_panels'][locale][view] = {
                    'path': str(source), 'sha256': file_sha256(source), 'source_page': 95,
                    'source_ai_sha256': 'a' * 64, 'captions_embedded': True,
                }
        book = SimpleNamespace(
            language=language, assets={}, hashes={}, output=root/'package',
            target={'model': 'JE-1000F', 'region': 'EU'}, errata={},
            manifest={'schema_version': 'auto-manual-frozen-web-source/v1',
                      'target': {'model': 'JE-1000F', 'region': 'EU', 'languages': [language]}},
            figures=[], art={}, expected_reference_count=0,
            read=lambda _: {'original_source': {'sha256': 'a' * 64}},
            overview_instance=resolve_overview_instance(model='JE-1000F', region='EU'),
            contract=load_web_manual_contract(model='JE-1000F', region='EU'),
        )
        return book, bindings

    def _page(self, book):
        carriers, views = [], []
        for geometry in book.overview_instance['views']:
            view = geometry['id']
            title = view.title()
            ref = book.overview_finished_panels[view]['asset_ref']
            callouts = [{'id': c['id'], 'label': f"{view} {c['id']}", 'body': ['Source specification']}
                        for c in geometry['callouts']]
            views.append({'id': view, 'title': title, 'image_ref': ref, 'alt': title, 'callouts': callouts})
            carriers.append(node('section', [
                node('heading', [text(title)], level=2,
                     presentation={'html': {'attributes': {'hidden': '', 'style': 'display:none'}}}),
                node('image', source=ref, alt=title),
                table([[cell(c['label'] + ' ' + c['body'][0])] for c in callouts]),
            ]))
        spec = overview_component_spec(
            accessibility_label='Overview', views=views,
            geometry_ref=book.overview_instance['instance_id'], source_ref='fixture/overview',
            language=book.language,
        )
        payload = component_flow_node(spec, carrier_flow=carriers, root=True)
        return SourcePage('product_overview', 'fixture/overview', 'product_overview.rst',
                          book.language, value_sha256(payload), (('flow', payload),))

    def test_optional_binding_preserves_default(self):
        with TemporaryDirectory() as td:
            book, _ = self._fixture(Path(td))
            before = deepcopy(book.overview_instance)
            bind_finished_overview(book, {}, Path(td)/'manifest.json')
            self.assertEqual({}, book.assets)
            self.assertEqual(before, book.overview_instance)

    def test_all_locales_and_source_identity_are_required(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            book, bindings = self._fixture(root)
            bad = deepcopy(bindings)
            del bad['overview_finished_panels']['uk']
            with self.assertRaisesRegex(ValueError, 'uk/pt/nl/pl'):
                bind_finished_overview(book, bad, root/'manifest.json')
            bad = deepcopy(bindings)
            bad['overview_finished_panels']['uk']['right']['source_ai_sha256'] = 'b' * 64
            with self.assertRaisesRegex(ValueError, 'source identity disagrees'):
                bind_finished_overview(book, bad, root/'manifest.json')
            bad = deepcopy(bindings)
            del bad['overview_finished_panels']['pl']['right']
            with self.assertRaisesRegex(ValueError, 'requires front and right'):
                bind_finished_overview(book, bad, root/'manifest.json')

    def test_heading_placement_must_be_explicit_and_accepts_native_text(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            book, bindings = self._fixture(root)
            record = bindings['overview_finished_panels']['pl']['front']
            for invalid in (None, "false", 0):
                record['captions_embedded'] = invalid
                with self.assertRaisesRegex(ValueError, 'declare whether view headings'):
                    bind_finished_overview(book, bindings, root/'manifest.json')
            record['captions_embedded'] = False
            bind_finished_overview(book, bindings, root/'manifest.json')
            self.assertIs(False, book.overview_finished_panels['front']['captions_embedded'])
            self.assertIs(True, book.overview_finished_panels['right']['captions_embedded'])

    def test_tampered_unselected_locale_is_rejected(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            book, bindings = self._fixture(root)
            (root/'uk-front.png').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'artwork changed: uk/front'):
                bind_finished_overview(book, bindings, root/'manifest.json')

    def test_cold_replay_selects_two_assets_without_duplicate_staging(self):
        for locale in ('uk', 'pt', 'nl', 'pl'):
            with self.subTest(locale=locale), TemporaryDirectory() as td:
                root = Path(td)
                book, bindings = self._fixture(root, locale)
                bind_finished_overview(book, bindings, root/'manifest.json')
                self.assertEqual({'overview.finished.front', 'overview.finished.right'}, set(book.assets))
                for record in book.assets.values():
                    destination = book.output/record['asset_ref']
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(record['path'], destination)
                    book.hashes[record['asset_ref']] = record['sha256']
                ir = assemble_book(book, 'Finished Overview fixture', (self._page(book),))
                self.assertEqual([locale, locale], [entry['locale'] for entry in ir.metadata['composites']])
                for source in root.glob('*.png'):
                    source.unlink()
                with patch('fitz.open', side_effect=AssertionError('cold replay cannot read AI/PDF')):
                    for _ in range(2):
                        soup = BeautifulSoup(''.join(replay_package(book.output)), 'html.parser')
                        self.assertEqual(2, len(soup.select('.hb-has-composite-art')))
                        self.assertEqual(15, len(soup.select('.hb-figure-callout')))
                        self.assertEqual(2, len(soup.select('h2[hidden]')))
                        markdown = (book.output/ir.metadata['markdown_filename']).read_text()
                        self.assertNotIn('## Front', markdown)
                        self.assertNotIn('## Right', markdown)
                        self.assertEqual(2, len(BeautifulSoup(markdown, 'html.parser').select('h2[hidden]')))
                        self.assertEqual(2, len(list((book.output/'assets').iterdir())))
                asset = book.output/ir.metadata['composites'][0]['path']
                asset.write_bytes(b'tampered package image')
                with self.assertRaisesRegex(ValueError, 'document asset missing or changed'):
                    replay_package(book.output)


if __name__ == '__main__':
    unittest.main()
