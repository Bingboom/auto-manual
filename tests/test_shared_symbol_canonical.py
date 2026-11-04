"""Shared-symbol canonical groups and the native SVG mapping fixes they rely on."""
import unittest
import xml.etree.ElementTree as ET

from tools.asset_pipeline.native_svg import _drawing_paths, _path_key
from tools.web.shared_symbol_assets import _catalog, canonical_decision, canonical_groups

# Operator decisions SCG-20261103 and SCG-20261104.
CONFIRMED = {
    'unplug': 'unplug/h1-jp-native',
    'no-wet-hands': 'native/je1000d-jp-00c43a89-03',
    'keep-dry': 'native/je1000d-jp-00c43a89-05',
    'do-not-dismantle': 'do-not-dismantle/screwdriver-prohibited',
    'prohibited': 'prohibited/h1-jp-native',
    'mandatory': 'mandatory/h1-jp-native',
    'read-manual': 'read-manual/book-information',
    'no-open-flame': 'no-open-flame/fire-match-prohibited',
    'keep-away-from-children': 'keep-away-from-children/adult-child-prohibited',
    'warning': 'warning/outline-triangle-tinted',
    'li-ion-32': 'native/je3000c-kr-78316033-06',
    'weee': 'native/je3000c-kr-78316033-07',
    # SCG-20261104
    'li-ion': 'li-ion/recycle-li-ion',
    'battery-weee': 'battery_disposal/je2000e-eu-nl-batch1465-native',
    'battery-weee-pb': 'battery-weee/crossed-bin-pb-hte154-ink',
    'explosive-material': 'explosive-material/burst-triangle-tinted',
    'heavy-object': 'heavy-object/person-load-triangle-tinted',
    'electric-shock': 'electric-shock/bolt-triangle-tinted',
    'battery-charging': 'battery-charging/flame-battery-triangle-tinted',
    'ingestion-hazard': 'ingestion-hazard/coin-battery-triangle-dark-804ebe78',
    'fcc': 'fcc/nested-c-native-dark',
    'tw-recycle': 'recycle/taiwan-restricted-battery-477dfbd7',
    'ce': 'ce/label-hte156-ink',
    'ukca': 'ukca/label-hte156-ink',
    'ua': 'ua-conformity/label-hte156-ink',
    'un38-3': 'un38-3/box-label-hte156-ink',
    'triman-packaging': 'triman/info-tri-packaging-hte156-ink',
    'triman-device': 'triman/info-tri-device-hte156-ink',
    'ec-rep': 'ec-rep/label-hte154-ink',
    'uk-rep': 'uk-rep/label-hte154-ink',
}


def path(d):
    return ET.Element('path', {'d': d})


class CanonicalCatalogTests(unittest.TestCase):
    def test_catalog_groups_every_variant_once_with_operator_canonicals(self):
        index = canonical_groups()
        _, data = _catalog()
        self.assertEqual(set(index), {row['key'] for row in data['assets']})
        groups = {g['id']: g for g, _ in index.values()}
        confirmed = {gid: g['canonical'] for gid, g in groups.items() if g['status'] == 'operator-confirmed'}
        self.assertEqual(confirmed, CONFIRMED)
        decision = canonical_decision('SCG-20261103')
        self.assertEqual(decision['date'], '2026-11-03')
        self.assertIn('用无底色的', [q['quote'] for q in decision['operator_quotes']])
        self.assertIn('native/je1000d-jp-00c43a89-02', groups['do-not-dismantle']['legacy_variants'])
        self.assertIn('battery-weee/crossed-bin-no-bar', groups['battery-weee']['legacy_variants'])
        self.assertEqual(canonical_decision('SCG-20261104')['date'], '2026-11-04')

    def test_proposed_groups_never_cite_a_decision(self):
        for group, _ in canonical_groups().values():
            if group['status'] == 'proposed':
                self.assertIsNone(group['decision'])


class NativeSvgMappingTests(unittest.TestCase):
    def test_coordinate_spelling_does_not_split_a_fill_stroke_pair(self):
        # JE-3000A JP: the stroke spells an H endpoint ``-.078``; the fill's
        # Z closure reaches the same point. Both must compare equal.
        fill = 'M0 0H.001ZM-.078 0 0-.001V0ZM-.034-.121C-.107-.121-.157-.074-.157 0'
        stroke = 'M0 0H.001 0ZM-.078 0 0-.001V0H-.078ZM-.034-.121C-.107-.121-.157-.074-.157 0'
        self.assertEqual(_path_key(path(fill)), _path_key(path(stroke)))
        self.assertNotEqual(_path_key(path(fill)), _path_key(path(fill.replace('-.078 0 0', '-.079 0 0'))))

    def test_moveto_only_svg_path_without_drawing_is_skipped(self):
        # JE-1000B JP: MuPDF emits ``M0 0Z`` that get_drawings() omits.
        drawings = [{'type': 'f'}, {'type': 'fs'}, {'type': 's'}]
        a, ghost, b1, b2, c = path('M1 1L2 2Z'), path('M0 0Z'), path('M3 3L4 4'), path('M3 3L4 4'), path('M5 5V6')
        mapped = _drawing_paths(drawings, [a, ghost, b1, b2, c])
        self.assertEqual(mapped, [[a], [b1, b2], [c]])

    def test_other_extra_paths_still_fail_closed(self):
        drawings = [{'type': 'f'}, {'type': 's'}]
        with self.assertRaisesRegex(ValueError, 'drawing/SVG path mapping'):
            _drawing_paths(drawings, [path('M1 1L2 2'), path('M0 0L0 1'), path('M3 3L4 4')])
        # Zero-length segments are drawings, not moveto-only paths.
        with self.assertRaisesRegex(ValueError, 'drawing/SVG path mapping'):
            _drawing_paths(drawings, [path('M1 1L2 2'), path('M0 0V0'), path('M3 3L4 4')])

    def test_moveto_only_path_is_kept_when_counts_already_match(self):
        drawings = [{'type': 'f'}, {'type': 's'}]
        a, b = path('M0 0Z'), path('M3 3L4 4')
        self.assertEqual(_drawing_paths(drawings, [a, b]), [[a], [b]])


if __name__ == '__main__':
    unittest.main()
