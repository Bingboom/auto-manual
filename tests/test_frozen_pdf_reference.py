"""Figure labels must stay live, occur once, and remain bound to their artwork."""
from copy import deepcopy
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from tools.frozen_ai_web import replay_package
from tools.frozen_pdf_reference import (
    bind_reference_labels, labeled_artwork_node, reference_label_regions,
)
from tools.manual_ir.flow import flow_nodes_to_html
from tools.web_embedded_components import render_embedded_web_component


def fixture():
    figure = {'slug': 'solar', 'asset_key': 'diagram', 'physical_page': 5,
              'section_id': 'charging', 'clip_points': [20, 30, 340, 190]}
    block = {'bbox': [245, 165, 310, 172], 'text': 'SolarSaga 100 Air × 4\n'}
    book = SimpleNamespace(
        figures=[figure], language='pl', assets={'diagram': {'sha256': 'a' * 64}}, correct=lambda s: s,
        source={'pages': [{'physical_page': 5, 'blocks_visual_order': [
            block, {'bbox': [20, 200, 340, 220], 'text': 'Keep adjacent charging instructions.'},
        ]}]},
    )
    binding = {'solar': {'live_labels': ['SolarSaga 100 Air × 4'], 'base_art_layout': {
        'art_sha256': 'a' * 64, 'panel_top': 0, 'panel_fill': '#f2f3f3',
        'labels': [{'line': 0, 'rect': [70, 89, 28, 6]}],
    }}}
    return book, binding


class FrozenPdfReferenceTests(unittest.TestCase):
    def test_four_committed_books_replay_labels_without_reopening_pdf(self):
        source = (Path(__file__).resolve().parents[1] / 'manual_sources' / 'JE-1000F' /
                  'EU/nine-language/git-20260928-c38415f5-figure-labels/four-language/web')
        with TemporaryDirectory() as directory, patch('fitz.open', side_effect=AssertionError('PDF reopened')):
            for language in ('uk', 'pt', 'nl', 'pl'):
                with self.subTest(language=language):
                    target = Path(directory) / language
                    shutil.copytree(source / language, target)
                    soup = BeautifulSoup(''.join(replay_package(target)), 'html.parser')
                    for label in ('SolarSaga 200 × 2', 'SolarSaga 100 Air × 4'):
                        self.assertEqual(1, soup.get_text().count(label))
                        element = next(item for item in soup.select('.hb-reference-live-label')
                                       if item.text == label)
                        self.assertIn('hb-reference-art-panel', element.parent['class'])
                        self.assertIsNotNone(element.parent.img)
                    vehicle = {'uk': 'Автомобіль', 'pt': 'Veículo', 'nl': 'Voertuig', 'pl': 'Pojazd'}[language]
                    car = soup.select_one('figure[data-reference-id="car_charging"]')
                    self.assertEqual(vehicle, car.select_one('.hb-reference-live-label').text)
                    self.assertFalse(any(p.get_text(' ', strip=True) == vehicle for p in soup.find_all('p')))

    def test_public_shared_renderer_keeps_text_inside_same_panel_exactly_once(self):
        book, bindings = fixture()
        original = deepcopy(book.source)
        bind_reference_labels(book, bindings)
        value = labeled_artwork_node(book.figures[0], 'assets/solar.png', 'pl')
        html = flow_nodes_to_html((value,), component_renderer=lambda component:
            render_embedded_web_component(
                component, source_path=Path('charging.rst'), model='JE-1000F',
                region='EU', language='pl', composite_manifest=None, contract={}))
        soup = BeautifulSoup(html, 'html.parser')
        panel = soup.select_one('.hb-reference-art-panel')
        self.assertIsNotNone(panel)
        self.assertEqual('assets/solar.png', panel.img['src'])
        self.assertEqual('SolarSaga 100 Air × 4', panel.select_one('.hb-reference-live-label').text)
        self.assertEqual(1, soup.get_text().count('SolarSaga 100 Air × 4'))
        self.assertFalse(soup.select('p, .line-block'))
        self.assertEqual(original, book.source)
        self.assertEqual([{'physical_page': 5, 'section': 'charging',
                           'consume_bbox': [245, 165, 310, 172]}],
                         reference_label_regions(book.figures))

    def test_missing_duplicate_or_outside_figure_text_fails_closed(self):
        for mode in ('missing', 'duplicate', 'outside', 'repeated-declaration'):
            with self.subTest(mode=mode):
                book, binding = fixture()
                blocks = book.source['pages'][0]['blocks_visual_order']
                if mode == 'missing':
                    blocks.pop(0)
                elif mode == 'duplicate':
                    blocks.insert(0, deepcopy(blocks[0]))
                elif mode == 'outside':
                    blocks[0]['bbox'] = [245, 195, 310, 202]
                else:
                    binding['solar']['live_labels'] *= 2
                    binding['solar']['base_art_layout']['labels'].append(
                        {'line': 1, 'rect': [70, 80, 28, 6]})
                with self.assertRaisesRegex(ValueError, 'match exactly once'):
                    bind_reference_labels(book, binding)

    def test_changed_art_or_unplaced_label_is_rejected(self):
        book, bindings = fixture()
        book.assets['diagram']['sha256'] = 'b' * 64
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            bind_reference_labels(book, bindings)
        book, bindings = fixture()
        bindings['solar']['base_art_layout']['labels'] = []
        with self.assertRaises(ValueError):
            bind_reference_labels(book, bindings)

    def test_unlabeled_historical_art_remains_unchanged(self):
        book, _ = fixture()
        original = deepcopy(book.figures)
        bind_reference_labels(book, {'solar': {}})
        self.assertEqual(original, book.figures)
        self.assertEqual([], reference_label_regions(book.figures))

    def test_language_specific_labels_never_fall_back_to_another_language(self):
        book, bindings = fixture()
        book.source['pages'][0]['blocks_visual_order'][0]['text'] = 'Pojazd'
        bindings['solar']['live_labels'] = {'pl': ['Pojazd'], 'nl': ['Voertuig']}
        bind_reference_labels(book, bindings)
        self.assertEqual('Pojazd', book.figures[0]['live_captions'][0]['text'])
        book.language = 'uk'
        with self.assertRaisesRegex(ValueError, 'live_labels'):
            bind_reference_labels(book, bindings)
