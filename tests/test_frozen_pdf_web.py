"""Exercise fresh intake and cold public replay; artwork fixtures are not acceptance art."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from tools.frozen_ai_web import replay_package
from tools.frozen_pdf_app import APP_ASSET_KEYS
from tools.frozen_pdf_media import MEDIA_ASSET_KEYS
from tools.frozen_pdf_lcd import LCD_ICON_ASSET_KEYS
from tools.frozen_pdf_web import build_pdf_book
from tools.frozen_pdf_source import PdfBook, _overview_binding
from tools.component_specs.overview_instance import resolve_overview_instance, overview_instance_sha256
from tools.manual_ir.hashing import file_sha256
from tools.manual_ir.components import component_specs_in_flow

ROOT = Path(__file__).resolve().parents[1]
PDF = Path('/private/tmp/je1000f-nine-language-intake/HTE153-nine-language-native-text-check.pdf')
RECIPE = ROOT / 'manual_sources/JE-1000F/EU/nine-language/git-20260927-c38415f5/four-language'


@unittest.skipUnless(PDF.is_file(), 'original native PDF is available only on the intake host')
class FreshPdfWebTests(unittest.TestCase):
    def _bindings(self, directory):
        # One existing icon is sufficient to test asset transport and rendering.
        # These deliberately synthetic bindings are NEVER candidate/acceptance art.
        art = ROOT / 'docs/renderers/contracts/assets/app/app_download_qr.png'
        keys = {*APP_ASSET_KEYS, *MEDIA_ASSET_KEYS, *LCD_ICON_ASSET_KEYS, 'lcd.mode', 'lcd.map'}
        reference_ids = ('ups_connection', 'ac_wall_charging', 'solar_single', 'solar_four', 'car_charging')
        keys.update('reference.' + slug for slug in reference_ids)
        records = json.loads((RECIPE / 'source/symbols.json').read_text())['locales']['pl']
        keys.update(f"symbol.{row['icon_id']}" for row in records['pictograms'])
        bindings = {}
        for key in keys:
            fixture = directory / f'{key}.png'
            fixture.write_bytes(art.read_bytes())
            bindings[key] = {'path': str(fixture), 'sha256': file_sha256(fixture),
                             'content_mode': 'textless'}
        manifest = directory / 'synthetic-assets.json'
        manifest.write_text(json.dumps({'target': {'model': 'JE-1000F', 'region': 'EU'},
                                        'technical_version': 'git-native-pdf-test',
                                        'text_source': {'filename': PDF.name, 'sha256': file_sha256(PDF)},
                                        'assets': bindings, 'figures': [
                                            {'slug': slug, 'asset_key': 'reference.' + slug}
                                            for slug in reference_ids]}))
        return manifest

    def test_pdf_identity_is_bound_to_artwork_manifest_before_extraction(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self._bindings(root)
            original = json.loads(manifest.read_text())
            for bad_identity in (None, {'filename': PDF.name, 'sha256': '0' * 64},
                                 {'filename': 'other.pdf', 'sha256': file_sha256(PDF)}):
                with self.subTest(identity=bad_identity):
                    manifest.write_text(json.dumps({**original, 'text_source': bad_identity}))
                    with patch('tools.frozen_pdf_source.load_pdf_book', side_effect=AssertionError('must reject before intake')):
                        with self.assertRaisesRegex(ValueError, 'text_source disagrees'):
                            build_pdf_book(PDF, RECIPE, manifest, root / 'candidate', 'uk')
                    self.assertFalse((root / 'candidate').exists())

    def test_modified_approved_errata_cannot_be_applied(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            recipe = root / 'recipe'
            (recipe / 'source').mkdir(parents=True)
            shutil.copy2(RECIPE / 'source_manifest.json', recipe / 'source_manifest.json')
            errata = json.loads((RECIPE / 'source/errata.json').read_text())
            errata['entries'][0]['corrected_text'] = 'UNAPPROVED COPY'
            (recipe / 'source/errata.json').write_text(json.dumps(errata))
            manifest = self._bindings(root)
            with self.assertRaisesRegex(ValueError, 'frozen recipe changed: source/errata.json'):
                build_pdf_book(PDF, recipe, manifest, root / 'candidate', 'uk')
            self.assertFalse((root / 'candidate').exists())

    def test_all_four_native_books_have_no_print_contents_or_screenshot_components(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self._bindings(root)
            bindings = json.loads(manifest.read_text())
            instance = resolve_overview_instance(model='JE-1000F', region='EU')
            instance['instance_id'] = 'test-frozen-canvas-v1'
            instance['views'][0]['web']['aspect_ratio'] = 1.5
            bindings.update(overview_instance=instance,
                            overview_instance_sha256=overview_instance_sha256(instance))
            manifest.write_text(json.dumps(bindings))
            for language in ('uk', 'pt', 'nl', 'pl'):
                with self.subTest(language=language):
                    package = root / language
                    ir = build_pdf_book(PDF, RECIPE, manifest, package, language)
                    self.assertEqual('frozen-pdf-json', ir.source)
                    self.assertEqual(instance, ir.metadata['overview_instance'])
                    self.assertEqual(overview_instance_sha256(instance), ir.metadata['overview_instance_sha256'])
                    self.assertEqual('git-native-pdf-test', ir.metadata['frozen_source_manifest']['target']['technical_version'])
                    self.assertNotIn('/private/tmp/', json.dumps(ir.metadata['pdf_intake_provenance']))
                    self.assertEqual(15, len(ir.pages))
                    fragments = replay_package(package)
                    soup = BeautifulSoup(''.join(fragments), 'html.parser')
                    self.assertNotIn('Contents', [n.get_text() for n in soup.select('h2')])
                    self.assertNotIn('\ufffd', soup.get_text())
                    self.assertNotIn('\x1f', soup.get_text())
                    self.assertEqual(5, len(soup.select('.hb-operation-figure')))
                    self.assertEqual(7, len(soup.select('.hb-reference-figure')))
                    lcd = soup.select_one('.hb-lcd-table-composition .hb-lcd-icon-table')
                    self.assertIsNotNone(lcd)
                    self.assertEqual(26, len(lcd.select('tbody tr')))
                    self.assertTrue(all(len(row.find_all('td', recursive=False)) == 4
                                        for row in lcd.select('tbody tr')))
                    self.assertEqual(26, len(lcd.select('.hb-lcd-icon-art')))

                    self.assertEqual('--hb-aspect-ratio:1.5', soup.select_one('.hb-annotated-stage')['style'])
                    specs = component_specs_in_flow([b.payload for p in ir.pages for b in p.blocks])
                    self.assertFalse(any(spec.variant == 'approved-composite' for spec in specs))
                    self.assertNotIn('енергозбережен ня', soup.get_text())
                    if language == 'nl':
                        self.assertNotIn('Aan/uit-knop voor DC<', str(soup))
                        for broken in ('Batterijbespar ingsmodus', 'Energiebespa ringsmodus'):
                            self.assertNotIn(broken, soup.get_text())
                    asset = next((package / 'assets').iterdir())
                    asset.write_bytes(b'changed')
                    with self.assertRaises(ValueError):
                        replay_package(package)

    def test_missing_reference_geometry_cannot_lower_coverage_expectation(self):
        original_read = PdfBook.read

        def incomplete_recipe(book, path):
            record = original_read(book, path)
            if path.endswith('_figure_manifest.json'):
                record['figures'] = [f for f in record['figures'] if f['slug'] != 'car_charging']
            return record

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self._bindings(root)
            with patch.object(PdfBook, 'read', incomplete_recipe):
                with self.assertRaisesRegex(ValueError, 'five required reference diagrams'):
                    build_pdf_book(PDF, RECIPE, manifest, root / 'candidate', 'pl')
            self.assertFalse((root / 'candidate').exists())

    def test_pending_artwork_rejects_build_before_any_output(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self._bindings(root)
            data = json.loads(manifest.read_text())
            data['pending'] = ['operation.ac-output: source has two UK sockets']
            manifest.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'artwork remains pending'):
                build_pdf_book(PDF, RECIPE, manifest, root / 'candidate', 'pl')
            self.assertFalse((root / 'candidate').exists())


class FrozenNativeDeliveryTests(unittest.TestCase):
    def test_committed_books_replay_without_pdf_or_historical_screenshots(self):
        source = ROOT / 'manual_sources/JE-1000F/EU/nine-language/git-20260928-c38415f5-native-ir/four-language'
        manifest = json.loads((source / 'source_manifest.json').read_text())
        for record in manifest['inputs']:
            path = source / record['path']
            self.assertEqual(record['size'], path.stat().st_size)
            self.assertEqual(record['sha256'], file_sha256(path))
        with TemporaryDirectory() as temporary:
            import shutil
            for language, relative in manifest['web_roots'].items():
                package = Path(temporary) / language
                shutil.copytree(source / relative, package)
                markdown = package / f'manual_je1000f_eu_{language}.md'
                before = file_sha256(markdown)
                with patch('fitz.open', side_effect=AssertionError('frozen replay must not reopen PDF/AI')):
                    fragments = replay_package(package)
                self.assertEqual(before, file_sha256(markdown))
                soup = BeautifulSoup(''.join(fragments), 'html.parser')
                self.assertEqual(5, len(soup.select('.hb-operation-figure')))
                self.assertEqual(6, len(soup.select('.hb-reference-figure')))
                self.assertTrue(soup.select_one('.hb-app-add-device-control-panel'))
                self.assertNotIn('approved-composite', str(soup))


if __name__ == '__main__':
    unittest.main()


class FrozenOverviewBindingTests(unittest.TestCase):
    def test_default_geometry_remains_the_shared_instance(self):
        expected = resolve_overview_instance(model='JE-1000F', region='EU')
        self.assertEqual(expected, _overview_binding({}, {'model': 'JE-1000F', 'region': 'EU'}))

    def test_bound_geometry_requires_matching_hash_and_target(self):
        target = {'model': 'JE-1000F', 'region': 'EU'}
        instance = resolve_overview_instance(**target)
        bindings = {'overview_instance': instance,
                    'overview_instance_sha256': overview_instance_sha256(instance)}
        self.assertEqual(instance, _overview_binding(bindings, target))
        bindings['overview_instance_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            _overview_binding(bindings, target)
        bindings['overview_instance_sha256'] = overview_instance_sha256(instance)
        with self.assertRaisesRegex(ValueError, 'target disagrees'):
            _overview_binding(bindings, {**target, 'region': 'US'})
        with self.assertRaisesRegex(ValueError, 'no bound instance'):
            _overview_binding({'overview_instance_sha256': '0' * 64}, target)
