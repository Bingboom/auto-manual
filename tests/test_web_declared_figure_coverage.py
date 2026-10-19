"""Source-declared reference art evidence survives without a global model profile."""
from types import SimpleNamespace
import unittest
from tools.web.figure_coverage import _page_base_art_sha256


class DeclaredFigureCoverageTests(unittest.TestCase):
    def page(self, *hashes):
        return SimpleNamespace(blocks=[SimpleNamespace(payload={'kind': 'element', 'children': [
            {'kind': 'component', 'component_spec': {'metadata': {
                'web_replace_key': 'reference.solar',
                'base_art_layout': {'art_sha256': digest}}}} for digest in hashes]})])

    def test_frozen_declared_hash_without_profile(self):
        self.assertEqual(_page_base_art_sha256(self.page('a' * 64), {}, 'reference.solar'), 'a' * 64)

    def test_duplicate_or_invalid_evidence_is_rejected(self):
        for hashes in [('a' * 64, 'a' * 64), ('invalid',)]:
            with self.assertRaisesRegex(ValueError, 'invalid declared art evidence'):
                _page_base_art_sha256(self.page(*hashes), {}, 'reference.solar')

    def test_missing_evidence_still_requires_contract(self):
        with self.assertRaisesRegex(ValueError, 'no unique contract'):
            _page_base_art_sha256(self.page(), {}, 'reference.solar')
