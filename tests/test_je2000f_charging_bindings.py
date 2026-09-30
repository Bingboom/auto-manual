"""Regression coverage for inherited charging-label ownership and shared artwork."""
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from PIL import Image
from bs4 import BeautifulSoup

from tools.frozen_pdf_reference import (
    bind_reference_labels, labeled_artwork_node, reference_label_regions,
)
from tools.manual_ir.flow import flow_nodes_to_html
from tools.web_embedded_components import render_embedded_web_component


SOURCE = (Path(__file__).resolve().parents[1] / 'manual_sources/JE-2000F/EU/nine-language'
          '/git-20260929-eb899f44-intake/four-language')
FIGURES = {'solar_single', 'solar_four', 'car_charging'}


class ChargingBindingRegressionTests(unittest.TestCase):
    def test_new_locales_inherit_live_labels_and_share_same_model_art(self):
        shared_paths = {slug: set() for slug in FIGURES}
        for language in ('nl', 'pt', 'pl'):
            with self.subTest(language=language):
                bindings = json.loads((SOURCE / f'{language}_assets_manifest.json').read_text())
                source = json.loads((SOURCE / f'source/{language}_direct_source.json').read_text())
                figures = json.loads((SOURCE / f'source/{language}_figure_manifest.json').read_text())
                selected = [dict(f, asset_key=f'reference.{f["slug"]}')
                            for f in figures['figures'] if f['slug'] in FIGURES]
                book = SimpleNamespace(figures=selected, source=source, language=language,
                                       assets=bindings['assets'], correct=lambda value: value)
                bind_reference_labels(book, {f['slug']: f for f in bindings['figures']})
                self.assertEqual(4, len(reference_label_regions(book.figures)))
                for figure in book.figures:
                    record = bindings['assets'][figure['asset_key']]
                    path = SOURCE / record['path']
                    self.assertEqual(record['sha256'], sha256(path.read_bytes()).hexdigest())
                    shared_paths[figure['slug']].add(path.resolve())
                    self.assertTrue(figure.get('live_captions'), figure['slug'])
                    flow = labeled_artwork_node(figure, record['path'], language)
                    html = flow_nodes_to_html((flow,), component_renderer=lambda spec:
                        render_embedded_web_component(
                            spec, source_path=Path('charging.rst'), model='JE-2000F',
                            region='EU', language=language, composite_manifest=None, contract={}))
                    soup = BeautifulSoup(html, 'html.parser')
                    self.assertIsNone(soup.find('figcaption'))
                    for label in figure['live_captions']:
                        self.assertEqual(1, soup.get_text().count(label['text']))
                    if figure['slug'] == 'car_charging':
                        self.assertEqual(1, len(soup.select('.hb-reference-live-pill')))
        self.assertTrue(all(len(paths) == 1 for paths in shared_paths.values()))

    def test_car_note_background_is_empty_art_not_a_baked_white_pill(self):
        # Source-page note rectangle projected into the 12x English artwork.
        # A white baked pill, residual English text, or clipping repair damage
        # must fail even if the HTML label bindings remain intact.
        with Image.open(SOURCE / 'artwork/shared/english-charging_car.png') as image:
            region = image.convert('RGB').crop((1956, 84, 3672, 216))
            self.assertEqual(((242, 242), (243, 243), (243, 243)), region.getextrema())
