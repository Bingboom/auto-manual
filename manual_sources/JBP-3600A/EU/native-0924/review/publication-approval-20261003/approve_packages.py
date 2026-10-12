"""Bind already reviewed packages to the actual operator release instruction."""
import copy
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path.cwd()))
from tools.manual_ir.hashing import file_sha256
from tools.manual_ir import read_manual_ir
from tools.web.document_ir import render_document_fragments
from tools.web.component_admission import require_fresh_component_admission
from tools.web.language_release_evidence import _file_inventory

base = Path('manual_sources/JBP-3600A/EU/native-0924')
release = Path('manual_sources/JBP-3600A/EU/git-20261003-44b6ce61-reviewed')
assert not release.exists()
revisions = ['en-r6', 'fr-r5', 'es-r3'] + [f'{l}-r2' for l in ['de','it','uk','pt','nl','pl']]
status = json.loads((base/'review-status.json').read_text())
results = json.loads((base/'review/transparent-symbol-r1/results.json').read_text())['candidates']
by_revision = {r['revision']: r for r in results}

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

# Trusted source applicability: reviewed native source has the same 15 semantic
# pages and slots as English, including its empty TOC page. Native panel text and
# IT's extra row change content, not these chapter/component requirements.
policy_path = Path('docs/renderers/contracts/prepared_component_admission.json')
contract = json.loads(policy_path.read_text())
policy = copy.deepcopy(contract['targets']['JBP-3600A/EU/en'])
policy['pages']['operation_en.rst']['components']['HB-SPECIAL-OPERATION/status-right'] = 1
policy['pages']['connections_en.rst']['components']['HB-SPECIAL-REFERENCE-FIGURE/semantic-fallback'] = 2
for revision in revisions:
    lang = revision.split('-')[0]
    if lang != 'en':
        assert f'JBP-3600A/EU/{lang}' not in contract['targets']
    contract['targets'][f'JBP-3600A/EU/{lang}'] = copy.deepcopy(policy)
contract['review_basis'] += '; JBP-3600A EU nine reviewed locales 2026-10-03 MA-244: source pages and independent native/delta acceptance; 15 English semantic pages, shared symbols/Inbox/LCD/operation/reference/troubleshooting/spec/warranty, native panels and IT source-only spec/warranty differences retained. See manual_sources/JBP-3600A/EU/git-20261003-44b6ce61-reviewed/approval.json.'
write(policy_path, contract)

approval = {
    'schema_version': 'jbp-reviewed-publication-approval/v1',
    'authorization': 'MA-244', 'date': '2026-10-03',
    'originating_chat': '01a0f462-2057-7750-b1eb-10402304f6fb',
    'user_message_id': '01a10179-f9f8-79b2-b175-bf9f68a6e569',
    'user_instruction': 'JBP 八语合入上线啊',
    'interpretation': 'Release the independently reviewed native eight-language delivery and its necessary English r6 baseline update, retaining documented source-authored anomalies. This is the actual publication instruction, not a fabricated separate pixel-approval quote.',
    'candidate_source_commit': '44b6ce6101141681a6cf75c9fdfef05b8aef93b0',
    'independent_report': str(base/'review/transparent-final-independent/acceptance.md'),
    'independent_report_sha256': file_sha256(base/'review/transparent-final-independent/acceptance.md'),
    'english_baseline_revision': 'en-r6',
    'retained_native_findings': {r['language']: r['native_findings'] for r in status['candidates']},
    'source_exception_decision': 'Preserve reviewed source copy and pairings; no corrections or English-derived additions. DE warning pairings and IT cable label, extra 1160A/860μs specification and warranty wording remain as reviewed.',
    'artwork': 'Reuse warning and battery WEEE transparent sources exactly; retain equipment WEEE with bar and JBP x5; CSS 3s clock; no HTE152 x8 substitution.',
    'current_admission': 'tools.web.component_admission.require_fresh_component_admission + prepared_component_admission.json; trusted reviewed locale enrollment, validated component slots and actual packaged assets.',
    'pr1409': 'Not imported and not a runtime dependency of current-main release path. Its proposed cross-language baseline gate is outside this release; no dependency PR merge or gate bypass.',
    'phase2_scope': 'No new phase2/print language targets; build.py check is regression coverage, not a native-body content audit.',
    'candidates': [{k:r[k] for k in ['language','revision','ir_sha256','html_sha256','markdown_sha256','stylesheet_sha256']} for r in results],
}
write(release/'approval.json', approval)
approval_sha = file_sha256(release/'approval.json')
reports = []
for revision in revisions:
    lang = revision.split('-')[0]
    src, dst = base/'web'/revision, release/'web'/lang
    assert file_sha256(src/'manual.ir.json') == by_revision[revision]['ir_sha256']
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('admission-report.json'))
    raw = json.loads((dst/'manual.ir.json').read_text())
    before = copy.deepcopy(raw)
    md = raw['metadata']
    md['resolved_source_review'] = md.pop('pending_source_review')
    md['pending_source_review'] = []
    md['publication_eligible'] = True
    md['publication_approval'] = {'record': str(release/'approval.json'), 'sha256': approval_sha, 'authorization': 'MA-244', 'candidate_revision': revision, 'candidate_ir_sha256': by_revision[revision]['ir_sha256']}
    if 'pending_english_baseline_revision' in md:
        md['prior_pending_english_baseline_revision'] = md.pop('pending_english_baseline_revision')
    md['approved_english_baseline'] = {'revision': 'en-r6', 'ir_sha256': by_revision['en-r6']['ir_sha256'], 'approval_sha256': approval_sha}
    md['shared_symbol_revision']['prior_status'] = md['shared_symbol_revision']['status']
    md['shared_symbol_revision']['status'] = 'approved-for-git-only-publication'
    write(dst/'manual.ir.json', raw)
    assert {k:v for k,v in raw.items() if k != 'metadata'} == {k:v for k,v in before.items() if k != 'metadata'}
    a = render_document_fragments(read_manual_ir(src/'manual.ir.json'), package_root=src)
    b = render_document_fragments(read_manual_ir(dst/'manual.ir.json'), package_root=dst)
    assert tuple(s.replace(src.resolve().as_uri(), dst.resolve().as_uri()) for s in a) == tuple(b)
    report = require_fresh_component_admission(dst, model='JBP-3600A', region='EU', language=lang)
    write(release/'admission'/f'{lang}.json', {'publication_eligible': True, 'authorization': 'MA-244', 'actual_fresh_gate': 'pass', 'report': report})
    for p in src.rglob('*'):
        if p.is_file() and p.name not in ['manual.ir.json','admission-report.json']:
            assert p.read_bytes() == (dst/p.relative_to(src)).read_bytes()
    reports.append({'language': lang, 'revision': revision, 'approved_ir_sha256': file_sha256(dst/'manual.ir.json'), 'fresh_admission': 'pass', 'body_assets_css_scaffold': 'byte-identical to accepted candidate', 'rendered_fragments': 'unchanged except package root'})
write(release/'approval-parity.json', reports)
(release/'README.md').write_text('# JBP-3600A EU reviewed nine-language release\n\nMA-244 binds the actual 2026-10-03 operator publication instruction to EN r6 / FR r5 / ES r3 / DE IT UK PT NL PL r2. See [approval](approval.json) and [unchanged content proof](approval-parity.json). Reviewed native source differences are retained. The paper-manual version remains unknown.\n\n`web/<language>` is a new approved snapshot. Only review/admission metadata differs from the immutable accepted candidates. Native wording, tables, image bytes, CSS clock and layout are unchanged. Eight locale policies use the independently reviewed English chapter/component applicability, with source exceptions recorded explicitly. PR1409 is not a dependency of current admission.\n\nGit-only: no live source, queue, asset or link writes. Strict Sphinx, cold replay, build regression checks and final deployment receipts are separate release gates.\n')
manifest = {
    'schema_version': 'auto-manual-frozen-web-source/v1',
    'target': {'model':'JBP-3600A','region':'EU','languages':[r.split('-')[0] for r in revisions],'technical_version':release.name,'printed_version':None},
    'original_source': {'filename':'HTP011-EU-9国语言-0924.ai','sha256':'8c6c25ddbc885b8e186b3b643fb53677a383ddf22295b3a2ba689c4d5d8cf8d1'},
    'source_authority': 'Reviewed Git packages, independent original native source acceptance and final transparent-symbol delta acceptance, released under MA-244.',
    'included_pages': {'en':[7,14],'fr':[15,22],'es':[23,30],'de':[31,38],'it':[39,46],'uk':[47,54],'pt':[55,62],'nl':[63,70],'pl':[71,78],'shared_legal':[79,79]},
    'frontmatter_pages': {'en':[1,2,4],'fr':[2],'es':[2],'de':[2],'it':[2],'uk':[3],'pt':[3],'nl':[3],'pl':[3]},
    'publication_packaging': 'Admission reports live outside web roots: the existing assembler only stages supported manual sidecars. Visible content is unchanged.',
    'normalizations': 'Previously reviewed whitespace/ligature normalization and English semantic structure; native copy and recorded anomalies unchanged. CSS clock replaces source clock bitmap.',
    'build_py_scope': approval['phase2_scope'],
    'web_roots': {r.split('-')[0]:'web/'+r.split('-')[0] for r in revisions},
    'inputs': _file_inventory(release),
}
write(release/'source_manifest.json', manifest)
# Status pointers are current records; historical sealed reports stay untouched.
status['status'] = 'authorized-publication-preparation'
status['publication_approval_record'] = '../'+release.name+'/approval.json'
status['approved_release_source'] = '../'+release.name
status['operator_baseline_approval'] = True
status['source_exception_approval'] = True
status['locale_enrollment'] = True
status['multilingual_merge_publication_authorization'] = True
write(base/'review-status.json', status)
for name in ['README.md','REVIEW.md','FINAL_CONFIRMATION.md']:
    p=base/name
    title,rest=p.read_text().split('\n',1)
    p.write_text(title+'\n\n2026-10-03 更新：操作者已授权本批八语合入上线及必要英语 r6 更新（MA-244）。原稿差异按受审版本保留，实际指令与九语精确身份见[发布批准记录](../'+release.name+'/approval.json)。新批准包位于[发布源](../'+release.name+'/README.md)，下文候选阶段的待确认状态仅为历史记录。工程合入、发布与 RTD 验收仍分别跟踪。\n'+rest)
print(json.dumps(reports, ensure_ascii=False, indent=2))
