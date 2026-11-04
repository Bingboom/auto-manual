# JE-500A / JP / Japanese — Git-only Web release

Operator instruction, 2026-11-03: 「继续 转日语说明书」 (convert the JP single-language manuals that have a
customer model and a single-language PDF and are not yet on the Web). This package converts the Japanese
single-language manual of the Jackery ポータブル電源 500 New (model JE-500A) from the 发布文档管理 Base row
`reczz28SfbsHbzWg` (material 38-0001-000963, project HTE132). Route `JE-500A/JP/ja/md`, `legacy_default`.

**Status: `operator-approved-git-only-release`.** On 2026-11-04 the operator reviewed the 1280/390 renders beside the shared reference edition (PR #1657, reviewed commit `76fe0a13`) and said 「上线提交发布：JE-300B、JE-300C、JE-300D、JE-500A」 in the engineering session. `source/approval.json` binds that acceptance to these exact source inputs and the IR is publication-eligible. Source copy is published verbatim; `source_concerns` go to the source owner. The PR is merged only on the operator's own authorization (AGENTS.md §8.6).

## Source authority

- `original.pdf`: the row's 「单语言说明书」 Japanese PDF `【Jackery ポータブル電源 500 New】说明书-JP.pdf`,
  byte-exact (SHA-256 `368d993473c2ea840d660b976448f687ce2a049e70cd07593ebc024ee2a7da34`, 20 pages,
  129 × 184 mm). Every glyph is outlined, so the PDF has no text layer.
- Print master (「说明书文件」): `38-0001-000963 HTE132500A-JP-JAK 说明书 RoHS REACH 1016 Q.pdf`
  (SHA-256 `79cd50f14317dbffe5881a6048d7f1e25db6f67ccd10a457de35f55145d72347`), one artboard. Recorded in
  `source_manifest.json:print_master`; not archived here and not an extraction source.
- Identity (record id, material number, project, SKUs) is in `source_manifest.json:document_identity`.
  No Feishu file token is stored.

## Method

`source/intake.py` holds the Japanese copy, transcribed line by line from 300 dpi renders of the named
physical pages (500-600 dpi clips for small or ambiguous glyphs) and kept exactly as printed, wording,
punctuation and spacing included (print markup: bold, line break). It builds shared flow and shared
components only (`source/kit.py`); `source_manifest.json:component_map` maps every printed block. The 警告/注意
pictogram grids become one shared callout per row (JE-1000D JP V2 precedent). One printed table has no
fitting shared component and stays a plain shared table, declared with its reason in
`shared_component_exceptions`: the LCDディスプレイ on/off table (no drawing; HB-TABLE-LCD-MODE requires one).
Suspected source errors are kept verbatim and listed in `source_manifest.json:source_concerns`. The cover
(p1) and table of contents (p2) are not Web content; pages 3-20 (printed folios 01-17 plus the back cover
QR) are.

Shared reference edition: the same model's US English Web package
`manual_sources/JE-500A/US/en/git-20261028-5c065d11` (same outlined-PDF method). JP wording/structure
precedent: `manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2` (checked against this PDF, never copied).

## Artwork

- **Symbols** (7 rows, fixed 2% comparison): the six 絵表示の説明 symbols reuse shared bytes —
  unplug `native/je1500d-jp-6ddeef54-05`, no-wet-hands `native/je1500d-jp-6ddeef54-07`, do-not-dismantle /
  mandatory / keep-dry / prohibited `*/h1-jp-native`. The `*-dark-5c065d11` variants (no-open-flame,
  keep-away-from-children) belong to families this print does not use. The Li-ion 32 recycling mark (p7)
  sits outside the symbol table (recycling note); no variant passes the fixed comparison, so it reuses the
  operator-confirmed canonical of its group, `native/je3000c-kr-78316033-06` (PR #1659, SCG-20261103), byte for byte.
  It is not a symbol-table admission row. Nothing was added to the shared library.
- **LCD glyphs**: 12 of 13 reuse the JE-500A US/en glyphs unchanged (they pass the fixed comparison against
  this print); battery percentage is this print's native vector paths (the US package made the same call).
- **Panels** (`source/figures.json`, each with a `reuse_review`): the 本体 inbox card reuses the US
  `inbox-unit.png` (identical drawing). All other panels carry Japanese words, JP outlets or JP-only
  drawings (50Hz/60Hz) and are cut from `original.pdf` at 4x just inside the print panel frame.

## Rebuild

```sh
PKG=manual_sources/JE-500A/JP/ja/git-20261103-368d9934
python3 "$PKG/source/extract_assets.py"   # about 4 minutes (each page carries the whole artboard)
python3 "$PKG/source/intake.py"
python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --output tmp/je500a-jp/ja
python3 -m sphinx -n -W --keep-going -b html tmp/je500a-jp/ja tmp/je500a-jp-site
```

To re-freeze: remove `web/ja`, rebuild into `web/ja`, then run `source/refresh_manifest.py`.

## Boundaries

Git-only: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes. No phase2 or
print target is registered and no shared renderer, component, contract, symbol library or workflow changed.
Release follows the Git-only transaction
([web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction))
only after the operator accepts the renders and says 「上线提交发布」.
