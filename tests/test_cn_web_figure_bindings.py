"""CN reviewed-source figures must use the shared live-label contract."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest

from bs4 import BeautifulSoup

from tools.manual_ir.whole_document_components import discover_registered_components
from tools.web_figure_coverage import (
    build_web_figure_coverage,
    enforce_required_web_figure_coverage,
)
from tools.web_presentation import load_web_manual_contract
from tools.web_reference_figure_component import render_reference_figure_component


SOURCE = Path('page/08_charging_methods.rst')
LABELS = {
    'solar_direct': ['SolarSaga 200 × 2'],
    'solar_adapter': ['SolarSaga 100 Air × 4', '太阳能串联转接盒（单独售卖）'],
    'car_charge': ['车辆', '* 车载充电线需单独购买。'],
}


def source_html():
    return ''.join(
        f'<img src="assets/{name}.png" alt="充电示意图">'
        '<div class="line-block">'
        + ''.join(f'<div class="line">{label}</div>' for label in labels)
        + '</div>' for name, labels in LABELS.items()
    )


class ChineseFigureBindingTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_web_manual_contract(model='JE-2000F', region='CN')
        policy = self.contract['figure_coverage']['requirements'][0]
        policy['required_slots'] = [s for s in policy['required_slots'] if s.startswith('reference.charging-')]
        policy['slot_status_overrides'] = {s: v for s, v in policy['slot_status_overrides'].items() if s in policy['required_slots']}

    def render(self, html=None, contract=None):
        claims = discover_registered_components(
            BeautifulSoup(source_html() if html is None else html, 'html.parser'),
            source_path=SOURCE, contract=contract or self.contract,
            model='JE-2000F', region='CN', language='zh',
        )
        return ''.join(render_reference_figure_component(
            claim.spec, ''.join(str(node) for node in claim.owned_nodes),
            source_path=SOURCE, model='JE-2000F', region='CN', language='zh',
        ) for claim in claims)

    def document(self):
        assets = {
            'assets/' + figure['image_key'].split('/')[-1] + '.png':
                figure['base_art_layout']['art_sha256']
            for figure in self.contract['reference_figures']['figures']
            if figure.get('presentation_mode') == 'base-art-live-copy'
        }
        return SimpleNamespace(
            model='JE-2000F', region='CN', language='zh',
            pages=(SimpleNamespace(page_id=SOURCE.name, language='zh'),),
            metadata={'web_contract': self.contract, 'asset_sha256': assets,
                      'composites': [], 'illustration_provenance': {},
                      'declared_languages': ['zh']},
        )

    def test_reviewed_source_uses_shared_components_without_legacy_figure_opt_in(self):
        self.assertEqual(self.contract['figure_targets'], [])
        html = self.render()
        soup = BeautifulSoup(html, 'html.parser')
        self.assertEqual(len(soup.select('[data-component-id="HB-SPECIAL-REFERENCE-FIGURE"]')), 3)
        self.assertEqual(len(soup.select('[data-preserve-art-frame="true"]')), 3)
        self.assertEqual(len(soup.select('[data-mobile-labels="overlay"]')), 3)
        self.assertEqual(len(soup.select('.hb-reference-art-panel img')), 3)
        self.assertEqual(len(soup.select('.hb-reference-live-pill')), 1)
        self.assertIsNone(soup.find('figcaption'))
        for labels in LABELS.values():
            for label in labels:
                self.assertEqual(soup.get_text().count(label), 1)
        ir = self.document()
        coverage = build_web_figure_coverage(ir, [html])
        self.assertEqual([s['status'] for s in coverage['slots']], ['base-art-live-copy'] * 3)
        enforce_required_web_figure_coverage(ir, coverage)

    def test_omitted_binding_cannot_silently_fall_back_to_unstyled_image(self):
        contract = deepcopy(self.contract)
        contract['reference_figures']['figures'] = [
            f for f in contract['reference_figures']['figures'] if f['id'] != 'charging-car'
        ]
        html = self.render(contract=contract)
        ir = self.document()
        coverage = build_web_figure_coverage(ir, [html])
        with self.assertRaisesRegex(ValueError, 'charging-car'):
            enforce_required_web_figure_coverage(ir, coverage)

    def test_swapping_art_without_rebinding_geometry_fails(self):
        ir = self.document()
        ir.metadata['asset_sha256']['assets/car_charge.png'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'measured on art'):
            build_web_figure_coverage(ir, [self.render()])

    def test_missing_or_duplicate_native_label_is_rejected(self):
        line = '<div class="line">车辆</div>'
        for replacement in ('', line + line):
            with self.subTest(replacement=replacement), self.assertRaisesRegex(ValueError, 'labels; expected'):
                self.render(source_html().replace(line, replacement))


if __name__ == '__main__':
    unittest.main()
