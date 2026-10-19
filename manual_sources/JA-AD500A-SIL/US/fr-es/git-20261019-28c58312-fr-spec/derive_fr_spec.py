"""Derive the JA-AD500A-SIL / US / fr spec-label correction edition from the live solar-Voc edition.

Run from the repository root:

    python manual_sources/JA-AD500A-SIL/US/fr-es/git-20261019-28c58312-fr-spec/derive_fr_spec.py

The live edition ``../git-20261016-28c58312-solar-voc`` (MA-312) stays
immutable and keeps serving Spanish. This script copies its French pages, the
shared ``source/`` inputs and ``assets/`` byte-for-byte (not its Spanish pages,
``source/approval.json`` or ``source/differences.md``), then:

- swaps the printed DC input/output labels of the French specification table
  (``CORRECTIONS``): the 11–16V and 16–60V rows are the module's inputs, the
  42–58V row its output, as in the English and Spanish editions;
- moves the French pages onto shared theme classes (``STYLE_EDITS``,
  ``STYLE_BLOCKS``, ``PRESENTATION_CSS``) so the re-frozen locale passes the
  prepared-document shared-style gate; copy is unchanged;
- refreshes ``source_manifest.json``.

A second run leaves the tree unchanged. Hand-written ``README.md``,
``render.py``, ``source/differences.md`` and (after acceptance)
``source/approval.json`` are not touched. ``source/native_copy.json`` stays the
verbatim transcription of the printed PDF.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

PACKAGE = Path(__file__).resolve().parent
BASE = PACKAGE.parent / 'git-20261016-28c58312-solar-voc'
REPO = next(parent for parent in PACKAGE.parents if (parent / 'build.py').is_file())

CANDIDATE = 'review-candidate-no-release-authorization'
APPROVED = 'operator-approved-git-only-release'
STATUS = APPROVED
LANGUAGE = 'fr'
COPIED_ROOTS = ('source', 'assets')
# The Spanish pages stay on the base edition; its acceptance and change record do not carry over.
NOT_COPIED = {'source/approval.json', 'source/differences.md'}
LABEL_CONCERN = 'Sortie CC labels 11–16/16–60 input rows; Entrée CC labels 42–58 output row'

# (prepared page, base markup, corrected markup); each must match exactly once.
CORRECTIONS = [
    ('spec_fr.rst', '<tr><th rowspan="2">Sortie CC</th>', '<tr><th rowspan="2">Entrée CC</th>'),
    ('spec_fr.rst', '<tr><th>Entrée CC</th><td>42V', '<tr><th>Sortie CC</th><td>42V'),
]

LED_TABLE_START = '.. raw:: html\n\n   <div class="table-wrapper docutils" style='
LED_TABLE = '''.. container:: hb-source-status

   .. list-table::
      :header-rows: 1
      :widths: auto
      :class: hb-source-status-table

      * - État du voyant DEL
        - Couleur
        - État du produit
      * - Clignotant
        - Vert
        - Charge en cours
      * - Fixe
        - Rouge
        - Condition anormale
      * - Fixe
        - Vert
        - Connecté avec succès et prêt à charger
      * - Éteint
        - Aucun
        - Éteint
'''
CONTACT = '''.. raw:: html

   <div class="hb-text-panel" role="contentinfo" aria-label="Jackery contact information">
   <p><strong>JACKERY INC.</strong></p>
   <p>5310 Bunche Dr., Fremont, CA 94538-8301</p>
   <p><a href="tel:18885022236">1-888-502-2236 (US)</a></p>
   <p><a href="mailto:hello@jackery.com">hello@jackery.com</a><br><a href="https://www.jackery.com">www.jackery.com</a></p>
   </div>
   <p><img src="../../assets/contact-qr.png" alt="Jackery contact QR from the original back cover"/></p>
'''
# Shared-style migration (prepared-document shared-style gate, #1556): (page, base markup, shared markup).
STYLE_EDITS = [
    ('product_overview_fr.rst',
     '   <div class="manual-overview-composition" style="width:min(100%,40rem);margin-inline:auto;">\n', ''),
    ('product_overview_fr.rst', '   </div>\n\n.. _led-light:', '\n.. _led-light:'),
]
# Whole blocks rebuilt on shared classes: (page, start marker, replacement up to end of page).
STYLE_BLOCKS = [
    ('product_overview_fr.rst', LED_TABLE_START, LED_TABLE),
    ('contact_fr.rst', '.. raw:: html\n\n   <div class="manual-contact-footer"', CONTACT),
]
STYLED_PAGES = sorted({name for name, _, _ in STYLE_EDITS} | {name for name, _, _ in STYLE_BLOCKS})
# The LED status table has no shared component; it is a plain table on the shared status-table classes.
LED_TABLE_EXCEPTION = {
    'language': LANGUAGE, 'page_id': 'product_overview_fr.rst', 'kind': 'table',
    'text_sha256': '92faf574c0344bf52f7d32a1cdf2660717d6ba29da621c8a7826835b17a373a5',
    'reason': 'module LED status/colour/meaning table: no shared ComponentSpec covers an LED-state table; '
              'it uses the shared hb-source-status-table classes',
}
PRESENTATION_CSS = '''/* JA-AD500A-SIL US fr spec-label edition: page-local geometry only.
   Colours, borders and panels come from the shared Web theme (prepared-document shared-style gate). */

/* The product overview figure keeps its print width. */
#furo-main-content .hb-reference-figure[data-reference-id="product-overview"] { width: min(100%, 40rem); margin-inline: auto; }

/* LED status table columns follow the print. */
#furo-main-content table.hb-source-status-table { min-width: 0; }
#furo-main-content table.hb-source-status-table :is(th, td) { text-align: left; }
#furo-main-content table.hb-source-status-table tr > :nth-child(1) { width: 25%; }
#furo-main-content table.hb-source-status-table tr > :nth-child(2) { width: 20%; }

/* Contact block and the back-cover QR code keep their print size. */
#furo-main-content div.hb-text-panel[role="contentinfo"] { margin-top: 2rem; }
#furo-main-content img[alt="Jackery contact QR from the original back cover"] { width: 96px !important; height: auto; }
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def copied(relative: str) -> bool:
    return relative not in NOT_COPIED and not relative.endswith('_es.rst')


def copy_base() -> None:
    for root in COPIED_ROOTS:
        for path in sorted((BASE / root).rglob('*')):
            relative = path.relative_to(BASE).as_posix()
            if path.is_file() and copied(relative):
                target = PACKAGE / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)


def edited_page(name: str) -> str:
    """The base page with its correction and shared-style edits applied."""
    text = (BASE / 'source' / 'page' / name).read_text(encoding='utf-8')
    for page, old, new in [*CORRECTIONS, *STYLE_EDITS]:
        if page == name:
            if text.count(old) != 1:
                raise SystemExit(f'{name}: expected the base text once, found {text.count(old)}')
            text = text.replace(old, new)
    for page, start, block in STYLE_BLOCKS:
        if page == name:
            if text.count(start) != 1:
                raise SystemExit(f'{name}: expected the base block once, found {text.count(start)}')
            text = text[:text.index(start)] + block
    return text


def correct_pages() -> None:
    for name in sorted({name for name, _, _ in CORRECTIONS} | set(STYLED_PAGES)):
        (PACKAGE / 'source' / 'page' / name).write_text(edited_page(name), encoding='utf-8')
    (PACKAGE / 'source' / 'presentation.css').write_text(PRESENTATION_CSS, encoding='utf-8')


def manifest() -> None:
    data = read(BASE / 'source_manifest.json')
    data['target']['languages'] = [LANGUAGE]
    data['target']['technical_version'] = PACKAGE.name
    data['source_role'] = 'Git-only French spec-label correction edition of the live solar-Voc edition'
    for key in ('page_order', 'chapter_source_panels', 'web_roots'):
        data[key] = {LANGUAGE: data[key][LANGUAGE]}
    data['publication_eligible'] = STATUS == APPROVED
    data['publication_status'] = STATUS
    data['derived_from'] = {
        'package': BASE.name, 'authorization': 'MA-312',
        'manifest_sha256': sha256(BASE / 'source_manifest.json'),
    }
    data['source_concerns'] = [c for c in data['source_concerns'] if c['language'] != 'es']
    (concern,) = [c for c in data['source_concerns'] if c['issue'] == LABEL_CONCERN]
    concern['disposition'] = ('corrected in this edition on operator instruction 2026-10-19 '
                              '(法语版规格表 Input/Output 写反了，改掉发布); native_copy.json keeps the printed labels')
    data['text_corrections'] = [
        *[row for row in data['text_corrections'] if row['page'].endswith('_fr.rst')],
        *[{'page': f'source/page/{name}', 'approved': old, 'corrected': new,
           'reason': 'The French specification table swapped the DC input and output labels: '
                     '11–16V and 16–60V are the module inputs, 42–58V its output (English and Spanish '
                     'editions and the module design agree).',
           'instruction': 'operator, 2026-10-19: 法语版规格表 Input/Output 写反了 == 这个改掉发布'}
          for name, old, new in CORRECTIONS],
    ]
    data['shared_component_exceptions'] = [LED_TABLE_EXCEPTION]
    data['style_migration'] = {
        'gate': 'prepared-document-shared-styles/v1',
        'pages': [f'source/page/{name}' for name in STYLED_PAGES],
        'stylesheet': 'source/presentation.css',
        'reason': 'a re-frozen locale must pass the shared-style gate: page-local classes and inline styles '
                  'replaced by shared theme classes and a geometry-only stylesheet; visible copy unchanged',
    }
    data['pending_source_review'] = [] if data['publication_eligible'] else [
        'operator review of the French spec-label correction before Git-only release']
    for entry in data['repo_inputs']:
        entry['sha256'] = sha256(REPO / entry['path'])
    files = sorted(
        p for p in PACKAGE.rglob('*')
        if p.is_file() and '__pycache__' not in p.parts
        and p.relative_to(PACKAGE).parts[0] in {'render.py', 'derive_fr_spec.py', *COPIED_ROOTS}
    )
    data['inputs'] = [{'path': p.relative_to(PACKAGE).as_posix(), 'size': p.stat().st_size, 'sha256': sha256(p)}
                      for p in files]
    (PACKAGE / 'source_manifest.json').write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def release_manifest() -> None:
    """Inventory every package file for the Git-only release (seal_frozen_web_evidence)."""
    data = read(PACKAGE / 'source_manifest.json')
    files = sorted(
        p for p in PACKAGE.rglob('*')
        if p.is_file() and '__pycache__' not in p.parts and p.name != 'frozen_source_manifest.json'
    )
    data['inputs'] = [{'path': p.relative_to(PACKAGE).as_posix(), 'size': p.stat().st_size, 'sha256': sha256(p)}
                      for p in files]
    (PACKAGE / 'frozen_source_manifest.json').write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> None:
    copy_base()
    correct_pages()
    manifest()
    if (PACKAGE / 'web' / LANGUAGE).is_dir():
        release_manifest()
    print(json.dumps({'package': PACKAGE.name, 'inputs': len(read(PACKAGE / 'source_manifest.json')['inputs'])}))


if __name__ == '__main__':
    main()
