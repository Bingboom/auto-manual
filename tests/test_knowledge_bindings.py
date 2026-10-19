"""Where each claimed edition of the knowledge ledger is edited (machine-readable Phase 3a, P3-3)."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest

from tests.test_knowledge_findings import (APPLIED, APPROVED, BOUND, CHANGE, CLOSED, CONFIRMED, NL, PL, VERIFIED,
                                           finding, ledger)
from tools.manual_knowledge.bindings import BINDINGS, ENTRIES, STATES, binding_report
from tools.manual_knowledge.export import SCHEMA as CORPUS
from tools.manual_knowledge.findings import RELEASE_PATHS, check_ledger, main
from tools.manual_knowledge.governance import serialize
from tools.utils.path_utils import repo_root

DE, OTHER = 'JE-3000C/EU/de', 'JE-1000H/EU/nl'
PLAN = repo_root() / 'code-as-doc' / 'dev' / 'machine_readable_knowledge_governance.md'


def document(variant, release, version='git-20261001-8bcb378f-web'):
    model, region, language = variant.split('/')
    route = f'{model}/{region}/{language}/md'
    manifest = {'path': f'sources/web/{route}/evidence/frozen_source_manifest.json', 'sha256': 'b' * 64}
    return {'variant_key': variant, 'manual_variant_id': f'{variant}@{version}', 'publication_version': version,
            'source': {'route': route, 'release_path': release,
                       'authority': 'git_native' if release == 'git_only_frozen' else 'unknown',
                       'git_ref': 'c' * 40, 'built_at': '2026-10-01T15:37:14+00:00',
                       'source_manifest': manifest if release == 'git_only_frozen' else None}}


def corpus(*documents):
    return {'schema': CORPUS, 'region': 'EU', 'published_at': '2026-10-25T08:00:00+00:00', 'source_sha256': 'a' * 64,
            'documents': list(documents)}


PUBLISHED = corpus(document(NL, 'unclassified', '2.7'), document(PL, 'git_only_frozen'), document(DE, 'queue'),
                   document(OTHER, 'git_only_frozen'))
MIXED = {NL: 'unclassified', PL: 'git_only_frozen'}


class BindingReportTest(unittest.TestCase):
    def test_each_claimed_edition_names_its_source_or_is_flagged_unbound(self):
        report = binding_report(ledger(finding(authority=MIXED)), PUBLISHED)
        self.assertEqual(report['findings'], [{
            'finding_id': 'fd-je3000c-ups-warning', 'status': 'candidate', 'priority': 'high', 'editions': [
                {'variant': NL, 'release_path': 'unclassified', 'binding': 'unbound', 'sources': []},
                {'variant': PL, 'release_path': 'git_only_frozen', 'binding': 'declared',
                 'sources': ['docs/publish/sources/web/JE-3000C/EU/pl/md/evidence/frozen_source_manifest.json']}]}])
        self.assertEqual(report['unbound'], [{'variant': NL, 'findings': ['fd-je3000c-ups-warning']}])
        self.assertEqual(report['editions'][NL], {
            'manual_variant_id': f'{NL}@2.7', 'release_path': 'unclassified', 'authority': 'unknown',
            'version': '2.7', 'git_ref': 'c' * 40, 'built_at': '2026-10-01T15:37:14+00:00',
            'source_manifest': None, 'findings': ['fd-je3000c-ups-warning']})
        self.assertEqual(report['totals'], {
            'findings': 1, 'inactive': 0, 'editions': 2, 'release_paths': {'git_only_frozen': 1, 'unclassified': 1},
            'bindings': {'declared': 1, 'bound': 0, 'unbound': 1}, 'unbound_editions': 1})
        self.assertEqual((report['problems'], report['states'], report['entries']), ([], list(STATES), ENTRIES))
        self.assertEqual(report['corpus'], {'published_at': '2026-10-25T08:00:00+00:00', 'source_sha256': 'a' * 64})

    def test_a_bound_edition_lists_the_sources_and_who_bound_them(self):
        bound = {**BOUND, 'sources': ['manual_sources/JE-3000C/EU/nl/1.0/phase2', 'docs/templates'], 'note': 'x'}
        report = binding_report(ledger(finding(authority=MIXED, bindings={NL: bound})), PUBLISHED)
        self.assertEqual(report['findings'][0]['editions'][0], {
            'variant': NL, 'release_path': 'unclassified', 'binding': 'bound', 'sources': bound['sources'],
            'by': 'Operator', 'role': 'operator', 'date': '2026-10-13'})
        self.assertEqual((report['unbound'], report['totals']['bindings']),
                         ([], {'declared': 1, 'bound': 1, 'unbound': 0}))

    def test_queue_editions_are_declared_by_the_build_table_and_legacy_ones_need_a_binding(self):
        claims = [{'kind': 'manual', 'variants': [DE, 'JE-3000C/EU/pt'], 'references': [
            {'knowledge_id': None, 'source_ref': f'{DE}/md/manual.html#ups'}]}]
        record = finding(claims=claims, evidence={**finding()['evidence'], 'tier': 'manual'},
                         authority={DE: 'queue', 'JE-3000C/EU/pt': 'legacy'})
        self.assertEqual(check_ledger(ledger(record)), [])
        legacy = document('JE-3000C/EU/pt', 'legacy')
        del legacy['source']
        rows = binding_report(ledger(record), corpus(document(DE, 'queue'), legacy))['findings'][0]['editions']
        self.assertEqual([(row['release_path'], row['binding'], row['sources']) for row in rows],
                         [('queue', 'declared', []), ('legacy', 'unbound', [])])

    def test_editions_gather_every_open_finding_that_claims_them(self):
        other = finding(finding_id='fd-je3000c-energy-saving', priority='medium', authority=MIXED)
        rejected = finding(finding_id='fd-je3000c-rejected', status='rejected',
                           decisions=[{**CONFIRMED, 'status': 'rejected', 'note': 'the warning is in the box'}])
        closed = finding(finding_id='fd-je3000c-closed', status='closed', decisions=[CONFIRMED, APPROVED, APPLIED,
                                                                                    CLOSED],
                         changes=[CHANGE], verification=VERIFIED)
        applied = finding(finding_id='fd-je3000c-applied', status='applied', decisions=[CONFIRMED, APPROVED, APPLIED],
                          changes=[CHANGE], authority=MIXED, bindings={NL: BOUND})
        records = [finding(authority=MIXED), rejected, other, closed, applied]
        self.assertEqual(check_ledger(ledger(*records)), [])
        report = binding_report(ledger(*records), PUBLISHED)
        self.assertEqual([f['finding_id'] for f in report['findings']],
                         ['fd-je3000c-ups-warning', 'fd-je3000c-energy-saving', 'fd-je3000c-applied'])
        self.assertEqual(report['inactive'], ['fd-je3000c-rejected', 'fd-je3000c-closed'])
        self.assertEqual(report['editions'][PL]['findings'],
                         ['fd-je3000c-ups-warning', 'fd-je3000c-energy-saving', 'fd-je3000c-applied'])
        self.assertEqual(report['unbound'],
                         [{'variant': NL, 'findings': ['fd-je3000c-ups-warning', 'fd-je3000c-energy-saving']}])
        self.assertEqual((report['totals']['findings'], report['totals']['inactive'], report['totals']['bindings'],
                          report['problems']), (3, 2, {'declared': 3, 'bound': 1, 'unbound': 2}, []))

    def test_a_release_path_the_corpus_no_longer_publishes_is_a_problem(self):
        rebuilt = corpus(document(NL, 'git_only_frozen'), document(PL, 'unclassified'))
        report = binding_report(ledger(finding(authority=MIXED, bindings={NL: BOUND})), rebuilt)
        self.assertEqual(report['problems'], [
            'fd-je3000c-ups-warning: JE-3000C/EU/nl is published as git_only_frozen, the ledger records unclassified',
            'fd-je3000c-ups-warning: JE-3000C/EU/pl is published as unclassified, the ledger records git_only_frozen'])
        self.assertEqual([(row['binding'], row['release_path']) for row in report['findings'][0]['editions']],
                         [('declared', 'git_only_frozen'), ('unbound', 'unclassified')])
        withdrawn = binding_report(ledger(finding(authority=MIXED)), corpus(document(PL, 'git_only_frozen')))
        self.assertEqual(withdrawn['problems'], ['fd-je3000c-ups-warning: JE-3000C/EU/nl is not in the corpus'])
        self.assertEqual(withdrawn['editions'][NL]['release_path'], None)
        self.assertEqual(withdrawn['unbound'], [{'variant': NL, 'findings': ['fd-je3000c-ups-warning']}])

    def test_only_a_corpus_of_the_ledger_region_is_read(self):
        for wrong in ({**PUBLISHED, 'schema': 'auto-manual-knowledge-observations/v1'}, {**PUBLISHED, 'region': 'US'},
                      []):
            with self.assertRaisesRegex(ValueError, 'Not a EU manual-knowledge corpus'):
                binding_report(ledger(finding()), wrong)

    def test_entries_repeat_plan_section_4_2(self):
        text = PLAN.read_text(encoding='utf-8')
        section = text[text.index('### 4.2'):text.index('### 4.3')]
        rows = [line for line in section.splitlines() if line.startswith('| ') and '`' in line.split('|')[1]]
        self.assertEqual(set(ENTRIES), set(RELEASE_PATHS))
        for path, entry in ENTRIES.items():
            row = next(line for line in rows if re.search(rf'`{path}`', line.split('|')[1]))
            self.assertIn(entry['entry'], row)
            self.assertIn(entry['approval'], row)


class BindingCommandTest(unittest.TestCase):
    def run_bindings(self, *argv):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(['bindings', *argv])
        return code, json.loads(out.getvalue())

    def test_writes_the_report_next_to_the_corpus_and_never_the_ledger(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger_path, corpus_path = root / 'findings.json', root / 'site' / 'manual-knowledge.json'
            corpus_path.parent.mkdir()
            ledger_path.write_text(json.dumps(ledger(finding(authority=MIXED))), encoding='utf-8')
            corpus_path.write_text(json.dumps(PUBLISHED), encoding='utf-8')
            before = ledger_path.read_bytes()
            code, result = self.run_bindings('--corpus', str(corpus_path), '--ledger', str(ledger_path))
            output = corpus_path.parent / BINDINGS
            self.assertEqual((code, result['status'], result['path']), (0, 'written', str(output)))
            self.assertEqual(result['totals']['unbound_editions'], 1)
            first = output.read_bytes()
            self.assertEqual(first, serialize(binding_report(ledger(finding(authority=MIXED)), PUBLISHED)))
            self.run_bindings('--corpus', str(corpus_path), '--ledger', str(ledger_path))
            self.assertEqual((output.read_bytes(), ledger_path.read_bytes()), (first, before))

            corpus_path.write_text(json.dumps(corpus(document(PL, 'git_only_frozen'))), encoding='utf-8')
            code, result = self.run_bindings('--corpus', str(corpus_path), '--ledger', str(ledger_path),
                                             '--output', str(root / 'report.json'))
            self.assertEqual((code, result['problems']), (1, ['fd-je3000c-ups-warning: JE-3000C/EU/nl is not in the '
                                                              'corpus']))
            self.assertTrue((root / 'report.json').is_file())

            corpus_path.write_text(json.dumps({'schema': 'other'}), encoding='utf-8')
            code, result = self.run_bindings('--corpus', str(corpus_path), '--ledger', str(ledger_path))
            self.assertEqual((code, result['status']), (1, 'refused'))
            ledger_path.write_text(json.dumps(ledger(finding(status='confirmed'))), encoding='utf-8')
            code, result = self.run_bindings('--corpus', str(corpus_path), '--ledger', str(ledger_path))
            self.assertEqual((code, result['status']), (1, 'invalid'))


if __name__ == '__main__':
    unittest.main()
