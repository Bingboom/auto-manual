"""Derive this release from the reviewed 2026-10-19 draft package.

Run from the repository root. It reads only the immutable draft
``git-20261019-b16b82c6-jp-native`` and the shared symbol library, and rewrites
this package's Web IR, Markdown and symbol admission:

* six symbol-table rows bind their operator-confirmed group canonicals
  (SCG-20261103/SCG-20261104), because the draft's legacy variants print more
  than 2% away from the source glyphs;
* specification footnote 1 gets the operator-approved completion
  「できます。」 for the source text that visibly stops at 「できま」;
* the standalone document-title heading is dropped so the page opens with
  「安全上のご注意」 as its first top-level heading, like the other JP/ja
  manuals (operator 2026-11-06 review of the live page).

No other copy, layout or artwork changes. ``refresh_manifest.py`` then binds the
resulting inventory.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys

PACKAGE = Path(__file__).resolve().parent
REPO = next(p for p in PACKAGE.parents if (p / 'build.py').is_file())
sys.path.insert(0, str(REPO))

from tools.manual_ir.hashing import value_sha256  # noqa: E402
from tools.web.frozen_ai_web import replay_package  # noqa: E402
from tools.web.shared_symbol_assets import shared_symbol_file  # noqa: E402

DRAFT = PACKAGE.parent / 'git-20261019-b16b82c6-jp-native'
WEB = PACKAGE / 'web' / 'ja'
FOOTNOTE_BEFORE = '① 本製品は、ACコンセントからバッテリーを充電しながら、AC出力ポートを通じて給電することができま'
FOOTNOTE_AFTER = FOOTNOTE_BEFORE + 'す。'
CANONICALS = {
    'assets/shared-symbols/warning_triangle.svg': 'warning/outline-triangle-tinted',
    'assets/shared-symbols/read_manual.svg': 'read-manual/book-information',
    'assets/shared-symbols/keep_away_from_children.svg': 'keep-away-from-children/adult-child-prohibited',
    'assets/shared-symbols/no_wet_hands.svg': 'native/je1000d-jp-00c43a89-03',
    'assets/shared-symbols/battery_recycle.svg': 'li-ion/recycle-li-ion',
    'assets/shared-symbols/weee.svg': 'native/je3000c-kr-78316033-07',
}
ERRATUM = {
    'field': 'specification-footnote-1',
    'physical_page': 21,
    'source_text': FOOTNOTE_BEFORE,
    'web_text': FOOTNOTE_AFTER,
    'status': 'operator-approved',
    'operator_decision': '2026-11-06 operator chose option 2 (complete as 「できます。」) for the '
                         'footnote that visibly stops at 「できま」 in the source PDF',
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_footnote(node) -> int:
    count = 0
    if isinstance(node, dict):
        for key, value in node.items():
            if key == 'text' and value == FOOTNOTE_BEFORE:
                node[key] = FOOTNOTE_AFTER
                count += 1
            else:
                count += replace_footnote(value)
    elif isinstance(node, list):
        for value in node:
            count += replace_footnote(value)
    return count


def main() -> None:
    draft_ir = json.loads((DRAFT / 'web/ja/manual.ir.json').read_text(encoding='utf-8'))
    ir = json.loads(json.dumps(draft_ir))
    for ref, key in CANONICALS.items():
        source = shared_symbol_file(key)
        if source.suffix != Path(ref).suffix:
            raise ValueError('canonical symbol format differs: ' + key)
        shutil.copyfile(source, WEB / ref)
        ir['metadata']['asset_sha256'][ref] = sha256(WEB / ref)
    if sum(replace_footnote(block['payload']) for page in ir['pages'] for block in page['blocks']) != 1:
        raise ValueError('expected exactly one footnote occurrence')
    first = ir['pages'][0]['blocks'][0]
    if not (first['kind'] == 'flow' and first['payload'].get('kind') == 'heading'
            and first['payload'].get('level') == 1):
        raise ValueError('expected the document-title heading first')
    del ir['pages'][0]['blocks'][0]
    ir['metadata']['block_count'] -= 1
    block_hashes = []
    for page in ir['pages']:
        for block in page['blocks']:
            block['content_sha256'] = value_sha256({'kind': block['kind'], 'payload': block['payload']})
            block_hashes.append(block['content_sha256'])
    ir['content_sha256'] = value_sha256({'page_ids': [p['page_id'] for p in ir['pages']],
                                         'block_hashes': block_hashes})
    metadata = ir['metadata']
    metadata['pending_source_review'] = []
    metadata['pdf_intake_provenance']['pending_source_review'] = []
    metadata['publication_eligible'] = True
    metadata['source_errata'] = [ERRATUM]
    (WEB / 'manual.ir.json').write_text(json.dumps(ir, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    replay_package(WEB)


if __name__ == '__main__':
    main()
