"""Prepare new review-only revisions; never rewrite historical seals."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from bs4 import BeautifulSoup
from PIL import Image, ImageDraw
from tools.manual_ir import read_manual_ir
from tools.manual_ir.document import validate_document
from tools.manual_ir.hashing import file_sha256, value_sha256
from tools.frozen_ai_web import replay_package
from tools.web_document_ir import render_document_fragments
from tools.web_component_admission import require_fresh_component_admission
from tools.prepared_component_policy import resolve_prepared_component_policy
from tools.prepared_component_coverage import audit_prepared_component_coverage

repo = Path.cwd()
base = repo / 'manual_sources/JBP-3600A/EU/native-0924'
scratch = repo / '.tmp/jbp3600a-native-languages'
review = base / 'review/transparent-symbol-r1'
delivery = Path('/Users/pika/.codex/worktrees/manual-intake-assist/auto-manual2/.tmp/intake-assist/transparent-symbol-review')
revisions = [('en-r5', 'en-r6'), ('fr-r4', 'fr-r5'), ('es-r2', 'es-r3')] + [(f'{l}-r1', f'{l}-r2') for l in ['de', 'it', 'uk', 'pt', 'nl', 'pl']]
assert not review.exists(), 'Use a new evidence revision.'
assert all(not (base / 'web' / new).exists() for _, new in revisions)

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def files(root):
    return {str(p.relative_to(repo)): file_sha256(p) for p in sorted(root.rglob('*')) if p.is_file()}

historical = {}
for old, _ in revisions:
    historical.update(files(base / 'web' / old))
    historical.update(files(base / 'review' / old))
    historical.update(files(base / 'review' / f'{old}-independent'))
historical.update(files(base / 'review/count-errata-independent'))
historical.update(files(base / 'review/copy-count-errata'))
review.mkdir(parents=True)
write(review / 'historical-seals.json', historical)

supplied = {
    'warning-triangle-transparent.png': 'ead6abb99089c0c223d8d89588c1a48bc158bb93be15ed402bbcfc7563a02bf8',
    'weee2-transparent.png': 'cf04ff00bdeb8de5971a55e5d8be6ef91e1a4ddad479f817f0c535914a392d45',
    'hte152-x8/connected-batteries-x8-transparent.png': '81983db46972ddbd56bfd4dbd97ff16629d3179eeb710727a2a0fb518c111dc3',
}
for name, digest in supplied.items():
    assert file_sha256(delivery / name) == digest
    destination = review / 'inputs' / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(delivery / name, destination)
for name in ['warning-triangle-transparent.pdf', 'extract_candidate.py', 'hte152-x8/evidence.json', 'hte152-x8/extract_native.py', 'hte152-x8/connected-batteries-x8-transparent.pdf', 'hte152-x8/connected-batteries-x8-transparent.svg', 'hte152-x8/before-after.png', 'hte152-x8/verification-12x.png']:
    destination = review / 'inputs' / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(delivery / name, destination)
# The archived parent extraction script documents warning paths only; its old x8 branch is not used.
common = Path('/Users/pika/.codex/worktrees/manual-intake-assist/auto-manual2/docs/templates/word_template/common_assets/symbols/weee2.png')
assert file_sha256(common) == supplied['weee2-transparent.png']

en = base / 'web/en-r5'
replacements = {}
inventory = []
canvas = Image.new('RGB', (1080, 670), '#f8fafc')
draw = ImageDraw.Draw(canvas)
for row, (old_name, new_name, role) in enumerate([
    ('symbol_warning.png', 'warning-triangle-transparent.png', 'Warning triangle'),
    ('symbol_battery_weee.png', 'weee2-transparent.png', 'Battery disposal: NO bottom bar'),
]):
    old_path = next(en.rglob(old_name))
    new_path = review / 'inputs' / new_name
    old_ref = str(old_path.relative_to(en))
    new_ref = f'assets/ir/{file_sha256(new_path)}/{old_name}'
    replacements[old_ref] = (new_ref, new_path)
    stats = []
    masks = []
    for col, (label, path) in enumerate([('SEALED / already alpha', old_path), ('CANDIDATE / reused source', new_path)]):
        im = Image.open(path).convert('RGBA')
        alpha = im.getchannel('A'); hist = alpha.histogram()
        assert hist[0] and hist[255]
        stats.append({'path': str(path.relative_to(repo)), 'sha256': file_sha256(path), 'size': im.size, 'alpha_extrema': alpha.getextrema(), 'fully_transparent_pixels': hist[0], 'partial_alpha_pixels': sum(hist[1:255]), 'opaque_pixels': hist[255], 'alpha_bbox': alpha.getbbox()})
        masks.append(alpha.crop(alpha.getbbox()).resize((256, 256)).point(lambda p: 255 if p >= 128 else 0))
        x, y = col * 540, row * 330
        draw.text((x + 18, y + 12), role + ' | ' + label, fill='#111111')
        for yy in range(y + 42, y + 310, 18):
            for xx in range(x + 18, x + 510, 18):
                draw.rectangle((xx, yy, xx + 17, yy + 17), fill='#dfe5ed' if (xx // 18 + yy // 18) % 2 else '#ffffff')
        # Diagnostic composite only; the packaged PNGs stay byte-identical to the supplied assets.
        thumb = im.copy(); thumb.thumbnail((240, 240))
        canvas.paste(thumb, (x + (530 - thumb.width) // 2, y + 55), thumb)
    a, b = list(masks[0].get_flattened_data()), list(masks[1].get_flattened_data())
    iou = sum(bool(x) and bool(y) for x, y in zip(a, b)) / sum(bool(x) or bool(y) for x, y in zip(a, b))
    inventory.append({'role': role, 'old': stats[0], 'candidate': stats[1], 'normalized_alpha_mask_iou': iou, 'decision': 'Local high-resolution transparent-source reuse proposal. Old asset already has alpha; not a newly proven background repair. Pixel bounds/padding differ; requires visual confirmation.', 'new_asset_ref': new_ref})
canvas.save(review / 'symbol-before-after.png')
write(review / 'asset-inventory.json', {
    'status': 'candidate-not-approved', 'changes': inventory,
    'warning_source': {'path': '/Users/pika/Downloads/HTP011-EU-9国语言-0924.ai', 'sha256': '8c6c25ddbc885b8e186b3b643fb53677a383ddf22295b3a2ba689c4d5d8cf8d1', 'physical_page': 23, 'retained_drawings': [906, 907], 'excluded_drawings': [896, 905], 'note': 'Backdrop and interior shade excluded in supplied native extraction; shared warning shape.'},
    'battery_weee_source': {'path': str(common), 'sha256': file_sha256(common), 'reuse': 'unchanged bytes', 'meaning': 'battery disposal without bottom bar'},
    'equipment_weee': {'decision': 'unchanged; equipment disposal with bottom bar', 'sha256': '6883f899f43ac0642f43b8f9cf4118a394c1382ee409f4498544f90ba37b56a5'},
    'connection_icon': {'decision': 'Keep JBP native x5 unchanged. HTE152 x8 is archived for review only and is not a JBP asset.', 'jbp_x5_sha256': '8f7a4344e1d965ea755614244602fb78162c697a9ebe5865f560d890c4a1e6cd', 'hte152_x8_sha256': supplied['hte152-x8/connected-batteries-x8-transparent.png'], 'variant': 'HTE152 x8 has no outer capsule; not equivalent to prior low-resolution capsule icon.'},
    'registry_enrollment': False,
})

path_map = {old: value[0] for old, value in replacements.items()}
digest_map = {Path(old).parent.name: Path(new).parent.name for old, new in path_map.items()}
def replace(value):
    if isinstance(value, dict):
        return {replace(k): replace(v) for k, v in value.items()}
    if isinstance(value, list):
        return [replace(v) for v in value]
    if isinstance(value, str):
        for old, new in {**path_map, **digest_map}.items():
            value = value.replace(old, new)
    return value

def run_build(package, html, log):
    assert not html.exists()
    with log.open('w') as stream:
        subprocess.run([sys.executable, '-m', 'sphinx', '-b', 'html', '-W', '--keep-going', str(package), str(html)], check=True, stdout=stream, stderr=subprocess.STDOUT)

results = []
for previous, revision in revisions:
    language = revision.split('-')[0]
    old = base / 'web' / previous
    new = base / 'web' / revision
    evidence = review / revision
    evidence.mkdir()
    new.mkdir()
    raw_before = json.loads((old / 'manual.ir.json').read_text())
    raw = replace(copy.deepcopy(raw_before))
    filename = f'manual_jbp3600a_eu{"" if language == "en" else "_" + language}.md'
    for name in ['conf.py', 'index.md']:
        shutil.copyfile(old / name, new / name)
    shutil.copytree(en / '_static', new / '_static')
    for ref in raw['asset_refs']:
        dest = new / ref
        dest.parent.mkdir(parents=True, exist_ok=True)
        pair = next((pair for pair in replacements.values() if pair[0] == ref), None)
        shutil.copyfile(pair[1] if pair else old / ref, dest)
        assert file_sha256(dest) == raw['metadata']['asset_sha256'][ref]
    raw['metadata']['publication_eligible'] = False
    raw['metadata'].setdefault('pending_source_review', []).append('transparent-symbol-r1: operator approval of final English baseline and shared symbol reuse remains pending')
    raw['metadata']['shared_symbol_revision'] = {'status': 'candidate-not-approved', 'previous_revision': previous, 'previous_ir_sha256': file_sha256(old / 'manual.ir.json'), 'evidence': 'review/transparent-symbol-r1/asset-inventory.json', 'evidence_sha256': file_sha256(review / 'asset-inventory.json'), 'changes': [{'previous': a, 'candidate': b, 'sha256': Path(b).parent.name} for a, b in path_map.items()], 'x5_retained': language != 'en', 'registry_enrollment': False}
    if language != 'en':
        raw['metadata']['frozen_stylesheet_sha256'] = file_sha256(new / '_static/web_manual.css')
        raw['metadata']['pending_english_baseline_revision'] = 'en-r6 candidate; not approved'
        # The old locale trial retained the released hash after changing the locking contract.
        # Bind the new candidate to its actual contract; preserve the historical value explicitly.
        raw['metadata']['shared_symbol_revision']['previous_style_contract_sha256'] = raw['style_contract_sha256']
        raw['style_contract_sha256'] = value_sha256(raw['metadata']['web_contract'])
    for page in raw['pages']:
        for block in page['blocks']:
            block['content_sha256'] = value_sha256({'kind': block['kind'], 'payload': block['payload']})
    raw['content_sha256'] = value_sha256({'page_ids': [p['page_id'] for p in raw['pages']], 'block_hashes': [b['content_sha256'] for p in raw['pages'] for b in p['blocks']]})
    write(new / 'manual.ir.json', raw)
    ir = read_manual_ir(new / 'manual.ir.json')
    validate_document(ir)
    before_fragments = render_document_fragments(read_manual_ir(old / 'manual.ir.json'), package_root=old)
    after_fragments = render_document_fragments(ir, package_root=new)
    assert list(after_fragments) == [replace(f).replace(old.as_uri(), new.as_uri()) for f in before_fragments], 'Unexpected rendered semantic delta'
    expected_md = replace((old / filename).read_text())
    if language == 'en':
        # English uses the prepared-document Markdown seal. Do not claim a frozen-IR replay.
        (new / filename).write_text(expected_md)
    else:
        replay_package(new)
        assert (new / filename).read_text() == expected_md
    assert raw['pages'] == replace(raw_before['pages']) or all(
        {k: v for k, v in a.items() if k != 'content_sha256'} == {k: v for k, v in b.items() if k != 'content_sha256'}
        for p, q in zip(raw['pages'], replace(raw_before['pages']), strict=True)
        for a, b in zip(p['blocks'], q['blocks'], strict=True)
    )
    admission = {'publication_eligible': False}
    try:
        require_fresh_component_admission(new, model='JBP-3600A', region='EU', language=language)
        raise AssertionError('Candidate admission unexpectedly passed')
    except RuntimeError as exc:
        admission['actual_fresh_gate'] = str(exc)
    try:
        policy = resolve_prepared_component_policy(model='JBP-3600A', region='EU', language=language)
        admission['locale_policy'] = audit_prepared_component_coverage(raw, policy)
    except ValueError as exc:
        admission['locale_policy_blocker'] = str(exc)
    policy = resolve_prepared_component_policy(model='JBP-3600A', region='EU', language='en')
    policy['target']['language'] = language
    admission['english_applicability_trial'] = audit_prepared_component_coverage(raw, policy)
    assert not admission['english_applicability_trial']['issues']
    admission['trial_note'] = 'Read-only applicability audit; not locale enrollment. Renderer validated all actual packaged asset bytes.'
    write(new / 'admission-report.json', admission)
    html = scratch / 'html' / revision
    run_build(new, html, evidence / 'strict-sphinx.log')
    cold = scratch / 'transparent-cold' / revision
    assert not cold.exists()
    shutil.copytree(new, cold)
    if language != 'en':
        replay_package(cold)
    assert (new / filename).read_bytes() == (cold / filename).read_bytes()
    cold_html = scratch / 'html' / f'transparent-cold-{revision}'
    run_build(cold, cold_html, evidence / 'cold-sphinx.log')
    assert (html / filename).with_suffix('.html').read_bytes() == (cold_html / filename).with_suffix('.html').read_bytes()
    result = {'language': language, 'revision': revision, 'previous_revision': previous, 'ir_sha256': file_sha256(new / 'manual.ir.json'), 'html_sha256': file_sha256((html / filename).with_suffix('.html')), 'markdown_sha256': file_sha256(new / filename), 'stylesheet_sha256': file_sha256(new / '_static/web_manual.css'), 'previous_stylesheet_sha256': file_sha256(old / '_static/web_manual.css'), 'preview': f'http://127.0.0.1:56059/{revision}/{Path(filename).with_suffix(".html")}', 'publication_eligible': False, 'checks': {'strict_sphinx': 'pass', 'cold_rebuild': 'byte-identical Markdown and HTML', 'cold_method': 'packaged prepared Markdown rebuild' if language == 'en' else 'frozen IR replay then strict Sphinx', 'rendered_fragments': 'only two asset references changed; exact equality after path substitution', 'body_tables_components': 'unchanged', 'asset_count': len(raw['asset_refs']), 'unchanged_asset_count': len(raw['asset_refs']) - 2, 'x5_retained': language != 'en'}, 'admission': admission, 'independent_acceptance': 'Historical previous revision only; no new independent acceptance claimed', 'browser_status': 'pending'}
    write(evidence / 'comparison.json', result)
    write(evidence / 'package-manifest.json', files(new))
    results.append(result)
    print(revision, 'strict build and cold rebuild passed', flush=True)
assert all(file_sha256(repo / name) == digest for name, digest in historical.items())
write(review / 'results.json', {'status': 'candidate-not-approved', 'historical_seals_unchanged': True, 'candidates': results})
shutil.copyfile(Path(__file__), review / 'prepare_transparent_revision.py')
