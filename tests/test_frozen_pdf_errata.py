from copy import deepcopy
import unittest

from tools.web.frozen_pdf_errata import apply_native_errata


class NativeErrataTests(unittest.TestCase):
    def fixture(self):
        data = {'source': {'spec': 'car 16 A; PV 24 A'},
                'records': {'button': {'text': 'DC', 'raw_text': 'DC'}, 'usb': 'DC/USB'},
                'provenance': {'corrections_applied': []}}
        entry = {'id': 'approved-correction', 'locale': 'nl', 'status': 'operator-approved',
                 'source_sha256': 'a' * 64, 'operator_decision': {'quote': 'confirmed'},
                 'reason': 'confirmed source defect', 'native_bindings': [
                     {'path': ['source', 'spec'], 'source_text': 'car 16 A; PV 24 A',
                      'corrected_text': 'car 8 A; PV 24 A', 'physical_page': 132},
                     {'path': ['records', 'button', 'text'], 'source_text': 'DC',
                      'corrected_text': 'AC', 'physical_page': 128}]}
        return data, {'entries': [entry]}

    def test_corrects_component_inputs_and_preserves_raw_and_unrelated_copy(self):
        data, ledger = self.fixture()
        result = apply_native_errata(data, ledger, 'nl', 'a' * 64)
        self.assertEqual('car 8 A; PV 24 A', result['source']['spec'])
        self.assertEqual({'text': 'AC', 'raw_text': 'DC'}, result['records']['button'])
        self.assertEqual('DC/USB', result['records']['usb'])
        self.assertEqual(2, len(result['provenance']['corrections_applied']))
        self.assertEqual('DC', data['records']['button']['text'])
        self.assertEqual(data, apply_native_errata(data, ledger, 'pt', 'a' * 64))

    def test_rejects_unapproved_or_other_source_before_mutation(self):
        for key, value in [('status', 'pending'), ('operator_decision', None),
                           ('source_sha256', 'b' * 64)]:
            data, ledger = self.fixture()
            ledger['entries'][0][key] = value
            before = deepcopy(data)
            with self.assertRaises(ValueError):
                apply_native_errata(data, ledger, 'nl', 'a' * 64)
            self.assertEqual(before, data)

    def test_rejects_drift_duplicate_fields_and_raw_evidence_edits(self):
        for variant in ('drift', 'duplicate', 'raw'):
            data, ledger = self.fixture()
            bindings = ledger['entries'][0]['native_bindings']
            if variant == 'drift':
                bindings[1]['source_text'] = 'unexpected'
            elif variant == 'duplicate':
                bindings.append(deepcopy(bindings[0]))
            else:
                bindings[1]['path'][-1] = 'raw_text'
            before = deepcopy(data)
            with self.assertRaises(ValueError):
                apply_native_errata(data, ledger, 'nl', 'a' * 64)
            self.assertEqual(before, data)
