# JE-300B / JP / 日本語 — Git-only Web candidate

Operator decision, 2026-11-03 (「继续 转日语说明书」): convert the JP single-language manuals that have a customer
model and a single-language PDF and are not yet on the Web. This package converts the Japanese manual of the
Jackery ポータブル電源 300 Plus (model JE-300B) from the 发布文档管理 Base row `reczz28SfbsHd3kB` (material
38-0001-000427, project HTE095, SKU 21-0001-000200). Route `JE-300B/JP/ja/md`, `legacy_default`.
**No package for this model existed in the repository** before this candidate (no US/EU/JP Web edition).

**Status: `review-candidate-no-release-authorization`.** Not approved: there is no `source/approval.json`, the IR
is not publication-eligible, and three symbol rows await an operator decision (see Artwork). The default layout
decisions and the source wording kept as printed are listed in [`audit/review.zh.md`](audit/review.zh.md).

## Source authority

- `original.pdf`: the row's Japanese single-language PDF 「【Jackery ポータブル電源 300 Plus】说明书-JP.pdf」,
  byte-exact (SHA-256 `456bb360c775dce0b13f4c24cce564ebf093a371963de431340e58c8d0b7087e`, 14 pages, 130 × 185 mm).
  Outlined, no text layer.
- Print master: `38-0001-000427 说明书 HTE095300B-JP-JAK RoHS REACH Q.pdf`
  (SHA-256 `2bc8847b03e02ece3ce1ae2d5d688f282b268a1142f3c7de5c9847d38170f3fa`); recorded in
  `source_manifest.json:print_master` for traceability, not archived here and not an extraction source.
- Identity (record id, material number, project, SKU) is in `source_manifest.json:document_identity`.
  No Feishu file token is stored.

## Method

The outlined-PDF method of the released same-generation US packages
(`manual_sources/JE-300C/US/en/git-20261027-a1128b25`, `manual_sources/JE-300E/US/en/git-20261027-04bd8b90`):
`source/intake.py` holds the line-by-line Japanese transcription from 300 dpi renders (450–700 dpi clips for dense
text), built from shared flow and shared components only (`source_manifest.json:component_map`). JP structure
patterns (pictogram warning rows as one shared callout each, 省エネモード tables, App chapter) follow
`manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2`; every line was checked against this PDF, not copied.
The cover (p1) is not Web content; the print has no paper contents page and no back-cover contact page.
Web content is physical pages 2–14 (printed folios 1–13). The two 省エネモード tables are the only declared plain
tables (`shared_component_exceptions`). Suspected source slips stay as printed (`source_concerns`).

Shared reference edition for review: the same-generation JE-300C US English Web package
(`manual_sources/JE-300C/US/en/git-20261027-a1128b25`), structure/components/theme only — no US facts reused.

## Artwork

- **Panels** (13): cut from `original.pdf` at 4x just inside each print panel (`source/figures.json`, each with a
  `reuse_review`). None reused: the 300 Plus is a different product from the JE-300C/300E drawings, most panels
  carry Japanese words, and the App screenshots/control panel belong to this edition. Phone frames kept whole.
- **LCD glyphs** (6): the battery icon reuses the JE-300C US `lcd-battery-power.svg` (fixed comparison passed);
  low battery, 省エネモード, fault code and the two temperature glyphs failed the comparison against their
  candidates (JE-300C US / JE-1000D JP) and are this print's native vector paths.
- **Symbols** (7 rows): 行為を指示する (`mandatory/h1-jp-native`), 分解・改造禁止, 濡らすこと禁止 and 行為禁止
  (`native/je1000d-jp-00c43a89-02/-05/-06`) reuse the shared library byte for byte. コンセントから電源プラグを抜く記号
  (`unplug/h1-jp-native`) and 製品に濡れた手で触れることを禁止する記号 (`native/je1000d-jp-00c43a89-03`, p8) bind the
  operator-confirmed canonical of its shared symbol group (PR #1659, decision SCG-20261103): no variant passes the fixed comparison, and the release admission releases the group canonical because the printed caption is a source-verified caption of that group. The Li-ion 32 recycling mark (p2) sits outside the symbol table (recycling note) and reuses the group
  canonical `native/je3000c-kr-78316033-06` byte for byte; it is not a symbol-table admission row.

## Rebuild

```sh
PKG=manual_sources/JE-300B/JP/ja/git-20261103-456bb360
python3 -W ignore "$PKG/source/extract_assets.py"
python3 -W ignore "$PKG/source/intake.py"
python3 -W ignore "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 -W ignore "$PKG/rebuild.py" --output tmp/je300b-jp/ja
python3 -m sphinx -n -W --keep-going -b html tmp/je300b-jp/ja tmp/je300b-jp-site
```

A cold rebuild is byte-identical to `web/ja`; the prepared-document shared-style admission reports no issues.

## Boundaries

Git-only: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes. No phase2 or print
target is registered and no shared renderer, component, contract, symbol library or workflow changed. Release
follows the Git-only transaction
([web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction))
only after the operator accepts the renders and says 「上线提交发布」.
