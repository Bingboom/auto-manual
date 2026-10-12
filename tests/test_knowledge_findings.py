"""Knowledge finding ledger contract (machine-readable Phase 3a, P3-0)."""
from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.manual_knowledge.findings import SCHEMA, check_ledger, default_ledger, main
from tools.utils.path_utils import repo_root

REAL_LEDGER = default_ledger(repo_root())
EN, NL, PL = 'JE-3000C/EU/en', 'JE-3000C/EU/nl', 'JE-3000C/EU/pl'
REFERENCE = {'knowledge_id': f'kn:{EN}:warning:823e5e18a1e9a174:0',
             'source_ref': f'{EN}/md/manual_je3000c_eu_en.html#uninterruptible-power-supply-ups'}
CANDIDATE = {
    'finding_id': 'fd-je3000c-ups-warning', 'status': 'candidate', 'priority': 'high', 'category': 'warning',
    'summary': 'nl and pl lack the UPS warning', 'registered': {'date': '2026-10-12', 'source': 'P2-4 §3.2 #7'},
    'claims': [{'kind': 'absent', 'variants': [NL, PL], 'references': [REFERENCE]}],
    'evidence': {'tier': 'medium', 'observation_ids': ['obs:language_parity:JE-3000C/EU:95db60b2597402b3'],
                 'generator': 'manual-observations/0.5', 'pilot_check': 'real'},
    'authority': {NL: 'git_only_frozen', PL: 'git_only_frozen'},
    'decisions': [], 'changes': [], 'verification': None,
}
CONFIRMED = {'status': 'confirmed', 'by': 'Owner A', 'role': 'content_owner', 'date': '2026-10-13'}
APPROVED = {'status': 'change_approved', 'by': 'Operator', 'role': 'operator', 'date': '2026-10-14'}
APPLIED = {'status': 'applied', 'by': 'Operator', 'role': 'operator', 'date': '2026-10-20'}
CLOSED = {'status': 'closed', 'by': 'Owner A', 'role': 'content_owner', 'date': '2026-10-21'}
CHANGE = {'variants': [NL, PL], 'wording': ['tm:recA1b2C3'], 'pr': 'https://github.com/Bingboom/Hello-Docs/pull/300',
          'published': {NL: f'{NL}@git-20261020-0a1b2c3d', PL: f'{PL}@git-20261020-0a1b2c3d'}}
VERIFIED = {'result': 'closed', 'observed_at': '2026-10-21', 'generator': 'manual-observations/0.5',
            'needs_recheck': False}


def finding(**fields):
    record = copy.deepcopy(CANDIDATE)
    record.update(copy.deepcopy(fields))
    return record


def ledger(*findings):
    return {'schema': SCHEMA, 'region': 'EU', 'findings': list(findings)}


def problems(record):
    return check_ledger(ledger(record))


class LedgerContractTest(unittest.TestCase):
    def assertProblem(self, record, fragment):
        found = problems(record)
        self.assertTrue(any(fragment in problem for problem in found), found)

    def test_every_lifecycle_stage_with_its_evidence_is_valid(self):
        stages = [
            finding(),
            finding(status='confirmed', decisions=[CONFIRMED]),
            finding(status='change_approved', decisions=[CONFIRMED, APPROVED], changes=[CHANGE]),
            finding(status='applied', decisions=[CONFIRMED, APPROVED, APPLIED], changes=[CHANGE]),
            finding(status='closed', decisions=[CONFIRMED, APPROVED, APPLIED, CLOSED], changes=[CHANGE],
                    verification=VERIFIED),
            finding(status='superseded', decisions=[CONFIRMED, {**APPROVED, 'status': 'superseded',
                                                                 'note': 'split per product'}]),
        ]
        for index, record in enumerate(stages):
            record['finding_id'] = f'fd-stage-{index}'
        self.assertEqual(check_ledger(ledger(*stages)), [])

    def test_statuses_follow_the_decision_history_one_step_at_a_time(self):
        self.assertProblem(finding(status='confirmed'), "does not follow from its decisions ('candidate')")
        self.assertProblem(finding(status='applied', decisions=[{**APPLIED, 'date': '2026-10-13'}],
                                   changes=[CHANGE]), "candidate cannot move to 'applied'")
        self.assertProblem(finding(status='rejected', decisions=[CONFIRMED, {**CONFIRMED, 'status': 'rejected',
                                                                              'note': 'x'}]),
                           "confirmed cannot move to 'rejected'")

    def test_human_decisions_need_a_person_a_role_and_a_date_in_order(self):
        self.assertProblem(finding(status='confirmed', decisions=[{**CONFIRMED, 'by': ' '}]), 'person (by)')
        self.assertProblem(finding(status='confirmed', decisions=[{**CONFIRMED, 'role': 'machine'}]), 'role in')
        self.assertProblem(finding(status='confirmed', decisions=[{**CONFIRMED, 'date': '2026-10-11'}]),
                           'not before the registration')
        self.assertProblem(finding(status='change_approved', changes=[CHANGE],
                                   decisions=[CONFIRMED, {**APPROVED, 'date': '2026-10-12'}]),
                           'not before the registration or the previous decision')

    def test_applicability_and_compliance_verdicts_belong_to_the_certification_owner(self):
        not_applicable = {**CONFIRMED, 'status': 'not_applicable', 'note': 'no Wi-Fi in this edition'}
        self.assertProblem(finding(status='not_applicable', decisions=[not_applicable]), "certification owner's")
        self.assertProblem(finding(status='not_applicable', decisions=[
            {**not_applicable, 'role': 'certification_owner', 'note': ''}]), 'needs a note with the reason')
        self.assertEqual(problems(finding(status='not_applicable', decisions=[
            {**not_applicable, 'role': 'certification_owner'}])), [])
        compliance = {'category': 'compliance', 'claims': [{'kind': 'absent', 'variants': [NL, PL], 'references': [
            {**REFERENCE, 'knowledge_id': f'kn:{EN}:compliance:4c076ffc9b1ecd8c:0'}]}]}
        self.assertProblem(finding(status='confirmed', decisions=[CONFIRMED], **compliance), "certification owner's")
        self.assertEqual(problems(finding(status='confirmed', decisions=[{**CONFIRMED, 'role': 'certification_owner'}],
                                          **compliance)), [])

    def test_the_operator_approves_changes_that_cite_wording_and_never_carry_it(self):
        self.assertProblem(finding(status='change_approved', changes=[CHANGE],
                                   decisions=[CONFIRMED, {**APPROVED, 'role': 'content_owner'}]),
                           'the operator approves')
        self.assertProblem(finding(status='change_approved', decisions=[CONFIRMED, APPROVED],
                                   changes=[{**CHANGE, 'wording': ['Gebruik dit product niet voor servers.']}]),
                           'never the text itself')
        self.assertProblem(finding(status='change_approved', decisions=[CONFIRMED, APPROVED]),
                           'needs the approved change')
        self.assertProblem(finding(status='confirmed', decisions=[CONFIRMED], changes=[CHANGE]),
                           'from change_approved on')

    def test_applied_and_closed_trace_every_claimed_edition_to_a_pr_and_a_new_version(self):
        history = [CONFIRMED, APPROVED, APPLIED]
        self.assertProblem(finding(status='applied', decisions=history, changes=[{**CHANGE, 'pr': None}]),
                           "for ['JE-3000C/EU/nl', 'JE-3000C/EU/pl']")
        only_nl = {**CHANGE, 'variants': [NL], 'published': {NL: CHANGE['published'][NL]}}
        self.assertProblem(finding(status='applied', decisions=history, changes=[only_nl]), "for ['JE-3000C/EU/pl']")
        self.assertProblem(finding(status='applied', decisions=history,
                                   changes=[{**CHANGE, 'published': {NL: f'{PL}@git-20261020-0a1b2c3d'}}]),
                           'new manual_variant_id')
        self.assertProblem(finding(status='applied', decisions=history, changes=[{**CHANGE, 'pr': 'PR 300'}]),
                           'pull request URL')

    def test_closed_needs_verification_unless_every_claim_is_manual(self):
        history = [CONFIRMED, APPROVED, APPLIED, CLOSED]
        self.assertProblem(finding(status='closed', decisions=history, changes=[CHANGE]), 'found the difference gone')
        self.assertProblem(finding(status='closed', decisions=history, changes=[CHANGE],
                                   verification={**VERIFIED, 'result': 'still_open'}), 'found the difference gone')
        self.assertProblem(finding(verification={**VERIFIED, 'needs_recheck': 'no'}), 'needs_recheck')
        manual = [{'kind': 'manual', 'variants': [NL, PL], 'references': [REFERENCE]}]
        self.assertEqual(problems(finding(status='closed', decisions=history, changes=[CHANGE], claims=manual,
                                          evidence={**CANDIDATE['evidence'], 'tier': 'manual'})), [])

    def test_compared_claims_are_anchored_in_a_reference_item_of_the_same_product(self):
        def claim(**fields):
            return finding(claims=[{'kind': 'absent', 'variants': [NL, PL], 'references': [{**REFERENCE, **fields}]}])
        self.assertProblem(claim(knowledge_id=None), "needs the reference item's knowledge_id")
        self.assertProblem(claim(knowledge_id='kn:JE-1000H/EU/en:warning:823e5e18a1e9a174:0',
                                 source_ref='JE-1000H/EU/en/md/manual_je1000h_eu_en.html#ups'),
                           "same product for ['JE-3000C/EU/nl', 'JE-3000C/EU/pl']")
        self.assertProblem(claim(knowledge_id=f'kn:{EN}:safety:823e5e18a1e9a174:0'), "the finding's category")
        self.assertProblem(claim(source_ref=f'{NL}/md/manual_je3000c_eu_nl.html#ups'), "the source_ref's edition")
        self.assertProblem(claim(source_ref='https://ht-doc.readthedocs.io/x.html#y'), 'anchor on a EU manual page')
        self.assertProblem(finding(claims=[{'kind': 'severity', 'variants': [EN, NL], 'references': [REFERENCE]}],
                                   authority={EN: 'unclassified', NL: 'git_only_frozen'}),
                           'cannot also be claimed')
        page_only = [{'kind': 'manual', 'variants': [NL], 'references': [
            {'knowledge_id': None, 'source_ref': f'{NL}/md/manual_je3000c_eu_nl.html#ups'}]}]
        self.assertEqual(problems(finding(category='other', claims=page_only, authority={NL: 'git_only_frozen'})), [])

    def test_evidence_and_authority_cover_the_claim(self):
        self.assertProblem(finding(evidence={**CANDIDATE['evidence'], 'observation_ids': []}),
                           'cites its observations')
        self.assertProblem(finding(evidence={**CANDIDATE['evidence'], 'generator': None}), 'generator version')
        self.assertProblem(finding(evidence={**CANDIDATE['evidence'], 'pilot_check': 'looks fine'}), 'pilot_check')
        self.assertProblem(finding(authority={NL: 'git_only_frozen'}), 'exactly the claimed editions')
        self.assertProblem(finding(authority={NL: 'git_only_frozen', PL: 'feishu'}), 'release path must be one of')

    def test_ledger_shape_ids_and_unknown_fields(self):
        self.assertEqual(check_ledger({'schema': 'v0'}), [f'ledger: schema must be {SCHEMA}'])
        self.assertIn('finding_id is not unique', ' '.join(check_ledger(ledger(finding(), finding()))))
        self.assertProblem(finding(finding_id='FD 7'), 'fd-<lower-case words>')
        self.assertProblem(finding(claims=[{'kind': 'absent', 'variants': ['JE-3000C/US/nl'], 'references': [REFERENCE]}],
                                   authority={'JE-3000C/US/nl': 'unclassified'}), 'distinct EU variant keys')
        self.assertProblem(finding(decision=[]), "unknown fields ['decision']")
        self.assertProblem(finding(priority='urgent'), 'priority')

    def test_malformed_values_are_reported_instead_of_crashing(self):
        for record in (finding(status=['confirmed']),
                       finding(claims=[{'kind': 'absent', 'variants': [{'x': 1}], 'references': [REFERENCE]}]),
                       finding(status='confirmed', decisions=[{**CONFIRMED, 'status': ['confirmed']}, CONFIRMED]),
                       finding(status='change_approved', decisions=[CONFIRMED, APPROVED],
                               changes=[{**CHANGE, 'variants': [[NL]], 'published': []}]),
                       finding(evidence={**CANDIDATE['evidence'], 'observation_ids': [{'id': 1}]}),
                       'not an object'):
            self.assertTrue(problems(record))

    @unittest.skipUnless(REAL_LEDGER.is_file(), 'the ledger is Hello-Docs business content (docs/knowledge/governance/)')
    def test_the_ledger_in_this_checkout_follows_the_contract(self):
        self.assertEqual(check_ledger(json.loads(REAL_LEDGER.read_text(encoding='utf-8'))), [])


class LedgerCommandTest(unittest.TestCase):
    def run_check(self, path):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(['check', '--ledger', str(path)])
        return code, json.loads(out.getvalue())

    def test_check_reports_totals_or_problems_and_never_writes(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'findings.json'
            path.write_text(json.dumps(ledger(finding())), encoding='utf-8')
            before = path.read_bytes()
            code, result = self.run_check(path)
            self.assertEqual((code, result['status']), (0, 'valid'))
            self.assertEqual(result['totals'], {'findings': 1, 'by_status': {'candidate': 1},
                                                'by_tier': {'medium': 1}, 'by_category': {'warning': 1},
                                                'claimed_editions': 2})
            self.assertEqual(path.read_bytes(), before)
            path.write_text(json.dumps(ledger(finding(status='closed'))), encoding='utf-8')
            code, result = self.run_check(path)
            self.assertEqual((code, result['status']), (1, 'invalid'))
            self.assertNotIn('totals', result)
            path.write_text('{', encoding='utf-8')
            self.assertEqual(self.run_check(path)[1]['status'], 'invalid')
            self.assertEqual(self.run_check(Path(tmp) / 'missing.json'), (1, {'status': 'missing', 'path': str(
                Path(tmp) / 'missing.json')}))


if __name__ == '__main__':
    unittest.main()
