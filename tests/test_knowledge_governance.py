"""Ledger verification and candidate proposals (machine-readable Phase 3a, P3-1)."""
from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.manual_knowledge.findings import SCHEMA, check_finding, check_ledger, main
from tools.manual_knowledge.governance import (PROPOSALS, VERIFICATION, apply_verification, propose_findings,
                                               serialize, verify_ledger)
from tools.manual_knowledge.observe import SCHEMA as OBSERVATIONS

MODEL, OTHER = 'JE-3000C', 'JE-1000H'
EN, DE, NL, PL = (f'{MODEL}/EU/{language}' for language in ('en', 'de', 'nl', 'pl'))
GENERATOR = 'manual-observations/0.5'
UPS = 'Do not use this product for data servers or medical devices.'


def item(variant, text=UPS, digest='823e5e18a1e9a174', severity='warning', label='WARNING', anchor='ups'):
    return {'knowledge_id': f'kn:{variant}:warning:{digest}:0', 'variant_key': variant, 'category': 'warning',
            'severity': severity, 'label': label, 'text': text, 'observed_context': {'release_path': 'git_only_frozen'},
            'source': {'source_ref': f'{variant}/md/manual.html#{anchor}', 'section_title': anchor.upper()}}


def parity(members, absent=(), confidence='medium', number='1', differences=None):
    model = members[0]['variant_key'].split('/')[0]
    return {'observation_id': f'obs:language_parity:{model}/EU:{number * 16}', 'kind': 'language_parity',
            'category': 'warning', 'scope': {'model': model, 'region': 'EU'},
            'members': [{'knowledge_id': m['knowledge_id'], 'variant_key': m['variant_key'], 'severity': m['severity'],
                         'source_ref': m['source']['source_ref']} for m in members],
            'absent_in': [{'variant_key': variant, 'confidence': confidence} for variant in absent],
            'differences': differences if differences is not None else ['absent'] if absent else [],
            'confidence': confidence}


def artifact(items, relations, region='EU', bare=()):
    """Every edition a relation names carries items, as each published manual does, unless it is ``bare``."""
    named = {entry['variant_key'] for relation in relations for entry in relation['absent_in']}
    items = items + [item(variant, text='Store the product dry.', digest='f' * 16, anchor='storage')
                     for variant in sorted(named - {i['variant_key'] for i in items} - set(bare))]
    return {'schema': OBSERVATIONS, 'region': region, 'generator_version': GENERATOR,
            'published_at': '2026-10-25T08:00:00+00:00', 'source_sha256': 'a' * 64, 'corpus_sha256': 'b' * 64,
            'items': items, 'relations': relations}


def reference(record):
    return {'knowledge_id': record['knowledge_id'], 'source_ref': record['source']['source_ref']}


REFERENCE = item(EN)
FINDING = {
    'finding_id': 'fd-je3000c-ups-warning', 'status': 'candidate', 'category': 'warning',
    'summary': 'nl and pl lack the UPS warning', 'registered': {'date': '2026-10-12', 'source': 'P2-4 §3.2 #7'},
    'claims': [{'kind': 'absent', 'variants': [NL, PL], 'references': [reference(REFERENCE)]}],
    'evidence': {'tier': 'medium', 'observation_ids': [f'obs:language_parity:{MODEL}/EU:{"1" * 16}'],
                 'generator': GENERATOR, 'pilot_check': 'real'},
    'authority': {NL: 'git_only_frozen', PL: 'git_only_frozen'}, 'decisions': [], 'changes': [], 'verification': None,
}
CONFIRMED = {'status': 'confirmed', 'by': 'Owner A', 'role': 'content_owner', 'date': '2026-10-13'}
APPROVED = {'status': 'change_approved', 'by': 'Operator', 'role': 'operator', 'date': '2026-10-14'}
APPLIED = {'status': 'applied', 'by': 'Operator', 'role': 'operator', 'date': '2026-10-20'}
CLOSED = {'status': 'closed', 'by': 'Owner A', 'role': 'content_owner', 'date': '2026-10-26'}
CHANGE = {'variants': [NL, PL], 'wording': ['tm:recA1b2C3'], 'pr': 'https://github.com/Bingboom/Hello-Docs/pull/300',
          'published': {NL: f'{NL}@git-20261020-0a1b2c3d', PL: f'{PL}@git-20261020-0a1b2c3d'}}


def finding(**fields):
    record = copy.deepcopy(FINDING)
    record.update(copy.deepcopy(fields))
    return record


def ledger(*findings):
    return {'schema': SCHEMA, 'region': 'EU', 'findings': list(findings)}


def edition(members, absent=(), **fields):
    """An artifact with one UPS cluster of ``members`` (languages) and ``absent`` editions."""
    items = [item(f'{MODEL}/EU/{language}') for language in members]
    return artifact(items, [parity(items, [f'{MODEL}/EU/{language}' for language in absent], **fields)])


def verified(record, observations):
    return verify_ledger(ledger(record), observations)['findings'][0]


class VerifyTest(unittest.TestCase):
    def results(self, entry):
        return [(pair['variant'], pair['result'], pair['reason']) for pair in entry['pairs']]

    def test_a_difference_still_present_stays_open(self):
        entry = verified(finding(), edition(['en', 'de'], ['nl', 'pl']))
        self.assertEqual(entry['verification'], {'result': 'still_open', 'observed_at': '2026-10-25',
                                                 'generator': GENERATOR, 'needs_recheck': False})
        self.assertEqual(self.results(entry), [(NL, 'still_open', None), (PL, 'still_open', None)])
        self.assertEqual(entry['pairs'][0]['observation_id'], f'obs:language_parity:{MODEL}/EU:{"1" * 16}')

    def test_fixed_editions_join_the_reference_cluster_and_close(self):
        entry = verified(finding(), edition(['en', 'de', 'nl', 'pl']))
        self.assertEqual(entry['verification']['result'], 'closed')
        self.assertFalse(entry['verification']['needs_recheck'])
        partly = verified(finding(), edition(['en', 'de', 'nl'], ['pl']))
        self.assertEqual(partly['verification']['result'], 'still_open')
        self.assertEqual(self.results(partly), [(NL, 'closed', None), (PL, 'still_open', None)])

    def test_a_changed_reference_is_not_comparable_and_needs_a_recheck(self):
        reworded = item(EN, text=f'{UPS} Revised.', digest='0123456789abcdef')
        observations = artifact([reworded, item(NL)], [parity([reworded, item(NL)], [PL])])
        entry = verified(finding(), observations)
        self.assertEqual(entry['verification']['result'], 'not_comparable')
        self.assertTrue(entry['verification']['needs_recheck'])
        self.assertEqual(self.results(entry), [(NL, 'not_comparable', 'reference_missing'),
                                               (PL, 'not_comparable', 'reference_missing')])
        alone = artifact([REFERENCE], [])
        self.assertEqual(self.results(verified(finding(), alone))[0], (NL, 'not_comparable', 'reference_uncompared'))

    def test_an_edition_outside_the_comparison_is_not_comparable(self):
        entry = verified(finding(), edition(['en', 'de', 'nl']))
        self.assertEqual(self.results(entry), [(NL, 'closed', None), (PL, 'not_comparable', 'edition_uncompared')])
        self.assertEqual(entry['verification']['result'], 'not_comparable')
        self.assertTrue(entry['verification']['needs_recheck'])
        still = verified(finding(), edition(['en'], ['nl']))
        self.assertEqual(still['verification']['result'], 'still_open')
        self.assertTrue(still['verification']['needs_recheck'])

    def test_severity_and_numbers_compare_the_aligned_member(self):
        claim = {'kind': 'severity', 'variants': [NL], 'references': [reference(REFERENCE)]}
        record = finding(claims=[claim], authority={NL: 'git_only_frozen'})
        for severity, label, result in (('unknown', 'WAARSCHU', 'still_open'), ('warning', 'WAARSCHUWING', 'closed')):
            member = item(NL, severity=severity, label=label)
            observations = artifact([REFERENCE, member], [parity([REFERENCE, member])])
            self.assertEqual(verified(record, observations)['verification']['result'], result)
        missing = verified(record, edition(['en'], ['nl']))
        self.assertEqual(self.results(missing), [(NL, 'not_comparable', 'counterpart_missing')])
        spaced = item(EN, text='Keep 1.5 m clear; 30 cm above.', digest='1111111111111111')
        claim = {'kind': 'numbers', 'variants': [NL], 'references': [reference(spaced)]}
        record = finding(claims=[claim], authority={NL: 'git_only_frozen'})
        for text, result in (('Houd 1,5 m vrij.', 'still_open'), ('Houd 1,5 m vrij; 30 cm erboven.', 'closed')):
            member = item(NL, text=text, digest='2222222222222222')
            observations = artifact([spaced, member], [parity([spaced, member])])
            self.assertEqual(verified(record, observations)['verification']['result'], result)

    def test_each_edition_is_judged_against_references_of_its_own_product(self):
        other = item(f'{OTHER}/EU/en')
        claim = {'kind': 'absent', 'variants': [NL, f'{OTHER}/EU/nl'],
                 'references': [reference(REFERENCE), reference(other)]}
        record = finding(claims=[claim], authority={NL: 'git_only_frozen', f'{OTHER}/EU/nl': 'git_only_frozen'})
        observations = artifact([REFERENCE, item(NL), other], [parity([REFERENCE, item(NL)]),
                                                               parity([other], [f'{OTHER}/EU/nl'], number='2')])
        entry = verified(record, observations)
        self.assertEqual([(pair['variant'], pair['reference']) for pair in entry['pairs']],
                         [(NL, REFERENCE['knowledge_id']), (f'{OTHER}/EU/nl', other['knowledge_id'])])
        self.assertEqual(entry['verification']['result'], 'still_open')

    def test_manual_only_and_superseded_findings_are_not_verified(self):
        manual = finding(finding_id='fd-manual', claims=[{'kind': 'manual', 'variants': [NL], 'references': [
            {'knowledge_id': None, 'source_ref': f'{NL}/md/manual.html#app'}]}], authority={NL: 'git_only_frozen'})
        superseded = finding(finding_id='fd-old', status='superseded', decisions=[
            {**CONFIRMED, 'status': 'superseded', 'note': 'split per product'}])
        report = verify_ledger(ledger(finding(), manual, superseded), edition(['en'], ['nl', 'pl']))
        self.assertEqual(report['not_verified'], [{'finding_id': 'fd-manual', 'reason': 'manual_claims_only'},
                                                  {'finding_id': 'fd-old', 'reason': 'superseded'}])
        self.assertEqual(report['totals']['verified'], 1)
        self.assertEqual(report['totals']['pairs'], {'closed': 0, 'still_open': 2, 'not_comparable': 0})

    def test_the_same_artifact_gives_identical_bytes(self):
        records = ledger(finding(), finding(finding_id='fd-second'))
        observations = edition(['en', 'nl'], ['pl'])
        self.assertEqual(serialize(verify_ledger(records, observations)),
                         serialize(verify_ledger(copy.deepcopy(records), copy.deepcopy(observations))))

    def test_only_an_artifact_of_the_ledger_region_is_read(self):
        with self.assertRaisesRegex(ValueError, 'region EU'):
            verify_ledger(ledger(finding()), artifact([], [], region='US'))
        with self.assertRaisesRegex(ValueError, 'publication date'):
            verify_ledger(ledger(finding()), {**edition(['en']), 'published_at': None})

    def test_writing_changes_verification_only_and_keeps_the_closing_evidence(self):
        verification = {'result': 'closed', 'observed_at': '2026-10-21', 'generator': GENERATOR, 'needs_recheck': False}
        closed = finding(finding_id='fd-closed', status='closed', decisions=[CONFIRMED, APPROVED, APPLIED, CLOSED],
                         changes=[CHANGE], verification=verification)
        records = ledger(finding(), closed)
        report = verify_ledger(records, edition(['en', 'nl'], ['pl']))
        self.assertEqual(report['totals']['reopened'], ['fd-closed'])
        unclear = verify_ledger(records, artifact([item(EN, digest='0123456789abcdef')], []))
        self.assertEqual((unclear['totals']['reopened'], unclear['totals']['needs_recheck']),
                         ([], ['fd-je3000c-ups-warning', 'fd-closed']))
        updated, changed = apply_verification(records, report)
        self.assertEqual(changed, ['fd-je3000c-ups-warning'])
        self.assertEqual(check_ledger(updated), [])
        self.assertEqual(updated['findings'][0]['verification']['result'], 'still_open')
        self.assertEqual(updated['findings'][1], closed)
        self.assertEqual({key: value for key, value in updated['findings'][0].items() if key != 'verification'},
                         {key: value for key, value in finding().items() if key != 'verification'})
        self.assertIsNone(records['findings'][0]['verification'])
        self.assertEqual(apply_verification(updated, report)[1], [])


class ProposeTest(unittest.TestCase):
    def propose(self, records, observations, explained=frozenset(), minimum='medium'):
        result = propose_findings(records, observations, set(explained), minimum)
        self.assertEqual(result['problems'], [])
        for proposal in result['findings']:
            self.assertEqual(check_finding(proposal, 'EU'), [])
        return result

    def test_an_uncovered_absence_becomes_a_valid_candidate(self):
        result = self.propose(ledger(), edition(['en', 'de'], ['nl', 'pl']))
        [proposal] = result['findings']
        self.assertRegex(proposal['finding_id'], r'^fd-je3000c-absent-[0-9a-f]{8}$')
        self.assertEqual((proposal['status'], proposal['category'], proposal['decisions'], proposal['verification']),
                         ('candidate', 'warning', [], None))
        self.assertNotIn('priority', proposal)
        self.assertEqual(proposal['claims'], [{'kind': 'absent', 'variants': [NL, PL],
                                               'references': [reference(REFERENCE)]}])
        self.assertEqual(proposal['evidence'], {'tier': 'medium', 'generator': GENERATOR, 'pilot_check': None,
                                                'observation_ids': [f'obs:language_parity:{MODEL}/EU:{"1" * 16}']})
        self.assertEqual(proposal['authority'], {NL: 'git_only_frozen', PL: 'git_only_frozen'})
        self.assertEqual(proposal['registered']['date'], '2026-10-25')
        self.assertIn('nl、pl 版缺少参照条目', proposal['summary'])
        self.assertEqual(result['totals'], {'relations': {'reviewed': 0, 'no_claim': 0, 'covered': 0, 'proposed': 1},
                                            'proposals': 1, 'claimed_editions': 2})

    def test_cited_or_covered_relations_are_not_proposed_again(self):
        observations = edition(['en', 'de'], ['nl', 'pl'])
        self.assertEqual(self.propose(ledger(finding()), observations)['totals']['relations']['reviewed'], 1)
        elsewhere = [f'obs:language_parity:{MODEL}/EU:{"9" * 16}']
        uncited = finding(evidence={**FINDING['evidence'], 'observation_ids': elsewhere})
        self.assertEqual(self.propose(ledger(uncited), observations)['totals']['relations']['covered'], 1)
        partly = finding(evidence=uncited['evidence'], claims=[{**FINDING['claims'][0], 'variants': [NL]}],
                         authority={NL: 'git_only_frozen'})
        [proposal] = self.propose(ledger(partly), observations)['findings']
        self.assertEqual(proposal['claims'][0]['variants'], [PL])
        manual = finding(evidence=uncited['evidence'], claims=[{**FINDING['claims'][0], 'kind': 'manual'}])
        self.assertEqual(self.propose(ledger(manual), observations)['findings'], [])
        other_kind = finding(evidence=uncited['evidence'], claims=[{**FINDING['claims'][0], 'kind': 'numbers'}])
        self.assertEqual(len(self.propose(ledger(other_kind), observations)['findings']), 1)

    def test_low_confidence_absences_need_an_explicit_threshold(self):
        observations = edition(['en'], ['nl'], confidence='low')
        self.assertEqual(self.propose(ledger(), observations)['findings'], [])
        [proposal] = self.propose(ledger(), observations, minimum='low')['findings']
        self.assertEqual(proposal['evidence']['tier'], 'low')
        mixed = artifact([REFERENCE], [{**parity([REFERENCE], [NL, PL], confidence='medium'),
                                        'absent_in': [{'variant_key': NL, 'confidence': 'medium'},
                                                      {'variant_key': PL, 'confidence': 'low'}]}])
        self.assertEqual(self.propose(ledger(), mixed)['findings'][0]['claims'][0]['variants'], [NL])

    def test_severity_from_an_explained_label_is_no_difference(self):
        icon = item(NL, severity='unknown', label='⚠')
        split = item(PL, severity='unknown', label='OSTRZE')
        observations = artifact([REFERENCE, icon, split], [parity([REFERENCE, icon, split], differences=['severity'])])
        [proposal] = self.propose(ledger(), observations, explained={(NL, '⚠')})['findings']
        self.assertEqual(proposal['claims'][0]['kind'], 'severity')
        self.assertEqual(proposal['claims'][0]['variants'], [PL])
        result = self.propose(ledger(), observations, explained={(NL, '⚠'), (PL, 'OSTRZE')})
        self.assertEqual(result['totals']['relations']['no_claim'], 1)

    def test_numbers_and_absences_of_one_section_group_into_one_candidate(self):
        second = item(EN, text='Keep 30 cm clear.', digest='3333333333333333')
        changed = item(DE, text='Abstand halten.', digest='4444444444444444')
        elsewhere = item(EN, text='Store dry.', digest='5555555555555555', anchor='storage')
        observations = artifact([REFERENCE, second, changed, elsewhere], [
            parity([REFERENCE], [NL], number='1'), parity([second, changed], [NL], number='2',
                                                          differences=['absent', 'numbers']),
            parity([elsewhere], [NL], number='3')])
        findings = self.propose(ledger(), observations)['findings']
        self.assertEqual([[claim['kind'] for claim in found['claims']] for found in findings],
                         [['absent'], ['absent', 'numbers'], ['absent']])
        regrouped = artifact([REFERENCE, second], [parity([REFERENCE], [NL], number='1'),
                                                   parity([second], [NL], number='2')])
        [grouped] = self.propose(ledger(), regrouped)['findings']
        self.assertEqual(grouped['claims'][0]['references'], [reference(REFERENCE), reference(second)])
        self.assertEqual(grouped['evidence']['observation_ids'], [f'obs:language_parity:{MODEL}/EU:{n * 16}'
                                                                  for n in '12'])
        self.assertIn('的 2 条，首条', grouped['summary'])

    def test_an_edition_without_items_leaves_its_release_path_to_a_person(self):
        result = propose_findings(ledger(), artifact([REFERENCE], [parity([REFERENCE], [NL])], bare=[NL]), set())
        self.assertEqual(result['findings'][0]['authority'], {NL: None})
        self.assertEqual(len(result['problems']), 1)
        self.assertIn('release path must be one of', result['problems'][0])

    def test_proposals_are_deterministic(self):
        observations = edition(['en', 'de'], ['nl', 'pl'])
        self.assertEqual(serialize(propose_findings(ledger(), observations, set())),
                         serialize(propose_findings(ledger(), copy.deepcopy(observations), set())))


class CommandTest(unittest.TestCase):
    def run_main(self, *argv):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(list(argv))
        return code, json.loads(out.getvalue())

    def test_verify_writes_a_report_and_only_verification_into_the_ledger(self):
        with TemporaryDirectory() as tmp:
            path, observations = Path(tmp) / 'findings.json', Path(tmp) / 'run' / 'manual-observations.json'
            path.write_bytes(serialize(ledger(finding())))
            observations.parent.mkdir()
            observations.write_text(json.dumps(edition(['en', 'nl'], ['pl'])), encoding='utf-8')
            code, result = self.run_main('verify', '--ledger', str(path), '--observations', str(observations))
            self.assertEqual((code, result['status'], result['path']),
                             (0, 'written', str(observations.parent / VERIFICATION)))
            self.assertEqual(json.loads(path.read_text(encoding='utf-8'))['findings'][0]['verification'], None)
            code, result = self.run_main('verify', '--ledger', str(path), '--observations', str(observations),
                                         '--write')
            self.assertEqual(result['ledger']['updated'], ['fd-je3000c-ups-warning'])
            written = json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(written['findings'][0]['verification']['result'], 'still_open')
            self.assertEqual(path.read_bytes(), serialize(written))
            self.assertEqual(self.run_main('check', '--ledger', str(path))[0], 0)
            code, result = self.run_main('propose', '--ledger', str(path), '--observations', str(observations))
            self.assertEqual((code, result['path'], result['totals']['proposals']),
                             (0, str(observations.parent / PROPOSALS), 0))

    def test_an_invalid_ledger_or_unreadable_artifact_is_refused(self):
        with TemporaryDirectory() as tmp:
            path, observations = Path(tmp) / 'findings.json', Path(tmp) / 'manual-observations.json'
            path.write_bytes(serialize(ledger(finding(status='closed'))))
            code, result = self.run_main('verify', '--ledger', str(path), '--observations', str(observations))
            self.assertEqual((code, result['status']), (1, 'invalid'))
            path.write_bytes(serialize(ledger(finding())))
            code, result = self.run_main('propose', '--ledger', str(path), '--observations', str(observations))
            self.assertEqual((code, result['status']), (1, 'refused'))
            observations.write_text(json.dumps(artifact([], [], region='US')), encoding='utf-8')
            code, result = self.run_main('verify', '--ledger', str(path), '--observations', str(observations))
            self.assertEqual((code, result['status']), (1, 'refused'))
            self.assertFalse((Path(tmp) / VERIFICATION).exists())


if __name__ == '__main__':
    unittest.main()
