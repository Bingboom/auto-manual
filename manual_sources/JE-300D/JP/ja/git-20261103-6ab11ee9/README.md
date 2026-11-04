# JE-300D / JP / Japanese — Git-only Web candidate

Operator decision, 2026-11-03 (「继续 转日语说明书」): convert the JP single-language manuals that have a customer
model and a single-language PDF and are not yet on the Web. This package converts the Japanese manual of the
Jackery ポータブル電源 300D (model JE-300D) from the 发布文档管理 Base row `reczz28SfbsHcCzi` (material
38-0001-000961, project HTE150). Route `JE-300D/JP/ja/md`, `legacy_default`.

**Status: `review-candidate-no-release-authorization`.** Not approved: there is no `source/approval.json`, the IR
is not publication-eligible, and nothing here authorizes a merge or release. The default layout decisions the
operator should check are listed in [`audit/review.zh.md`](audit/review.zh.md).

## Source authority

- `original.pdf`: the row's Japanese single-language PDF, supplied as `【Jackery ポータブル電源 300D】说明书-JP.pdf`,
  byte-exact (SHA-256 `6ab11ee92b1cc729e585084d6c3fecd14b9dd98cc97a6c52da48c5fd9fa83559`, 21 pages, 89 × 129 mm).
  Outlined, no text layer.
- Print master: `38-0001-000961 HTE150300A-JP-JAK 说明书  RoHS REACH.pdf` (SHA-256 `2ece0ecc…`, one 1519 × 1066 mm
  artboard); recorded in `source_manifest.json:print_master`, not archived here and not an extraction source.
- Identity (record id, material number, project, SKUs) is in `source_manifest.json:document_identity`.

## Method

The same outlined-PDF method as `manual_sources/JE-300C/US/en/git-20261027-a1128b25`: `source/intake.py` holds the
line-by-line Japanese transcription (300 dpi renders, 450–1200 dpi clips for small or ambiguous glyphs), built from
shared flow and shared components only (`source_manifest.json:component_map`, no declared exceptions). Physical
pages 3–20 (printed 01–18) are Web content; the cover (p1), the contents (p2) and the QR-only back cover (p21) are
not. Suspected source slips are kept as printed (`source_manifest.json:source_concerns`). Shared reference edition
for review: the same model's US English Web package `manual_sources/JE-300D/US/en/git-20261028-d3f47ff3`.

## Artwork

- **Panels** (`source/figures.json`, each with a `reuse_review`): six text-free panels identical to the same
  model's US Web assets are reused byte for byte (inbox unit, strap, LCD drawing, USB output, USB-C charging,
  solar charging). Nine panels with Japanese words in the art, or with no US counterpart (shoulder belt, Japanese
  manual cover), are cut from `original.pdf` at 4x just inside the print panel frame; grey note strips inside a
  panel are set as text.
- **LCD glyphs**: 10 of 11 reuse the JE-300D US Web glyphs after the fixed comparison against this print; the
  battery-percentage glyph is this print's native vector paths (the candidate failed the transparency check).
- **Symbols**: 10 of 12 rows reuse a shared symbol byte for byte. The unplug row (`unplug/h1-jp-native`) and the Li-ion
  recycling row (`native/je3000c-kr-78316033-06`) bind the operator-confirmed canonical of its shared symbol group (PR #1659, decision SCG-20261103): no variant passes the fixed comparison, and the release admission releases the group canonical because the printed caption is a source-verified caption of that group. Nothing was added to the shared library.

## Rebuild

```sh
PKG=manual_sources/JE-300D/JP/ja/git-20261103-6ab11ee9
python3 "$PKG/source/extract_assets.py"
python3 "$PKG/source/intake.py"
python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --output tmp/je300d-jp/ja
python3 -m sphinx -n -W --keep-going -b html tmp/je300d-jp/ja tmp/je300d-jp-site
```

A cold rebuild is byte-identical to `web/ja`.

## Boundaries

Git-only: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes. No phase2 or print
target is registered and no shared renderer, component, contract, symbol library or workflow changed. Release
follows the Git-only transaction
([web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction))
only after the operator accepts the renders and authorizes the release.
