# JE-600C-SJ / JP / Japanese — Git-only Web candidate

Operator instruction, 2026-11-03 (relayed by the coordinating window): 「继续 转日语说明书」 — convert the 24
Japanese single-language manuals in the 发布文档管理 Base 日规 view that have a customer model and a
single-language PDF and no Web edition yet. This package converts the Japanese manual of the Jackery
ポータブル電源 600 Plus in sand gold (model JE-600C-SJ) from the row `reczz28SfbsHcxpj` (material
38-0001-000584, project HTE112). Route `JE-600C-SJ/JP/ja/md`, `legacy_default` (no Web edition exists for
this model).

**Status: `operator-approved-git-only-release`.** On 2026-11-04 the operator confirmed 「上线提交发布：JE-600A、JE-600C-SJ、JE-900B-WH、JE-1000B」 in the PR #1654 session after reviewing the 1280/390 renders beside the shared reference edition (with the symbol rows bound to the canonical groups of shared PR #1659). `source/approval.json` binds that acceptance to these exact source inputs and the IR is publication-eligible. Merge needs a separate operator authorization. Review points are in [`audit/review.zh.md`](audit/review.zh.md).

## Source authority

- `original.pdf`: the row's 「单语言说明书」 Japanese PDF, byte-exact (SHA-256 `3837e9fd…`, 14 pages,
  130 × 185 mm, document code Jackery-UM-002). Every glyph is outlined, so the PDF has no text layer.
- Print master (「说明书文件」): `38-0001-000584 说明书 HTE112600A-JP-JAK 沙金色 RoHS REACH.ai`; name, size
  and SHA-256 in `source_manifest.json:print_master`. Not archived and not an extraction source.
- Identity (record id, material number, project, SKU) is in `source_manifest.json:document_identity`.
  No Feishu file token is stored.

## Method

The Explorer outlined-PDF kit (`manual_sources/JE-600A/US/en/git-20261028-9bf5bbb1`), adapted for Japanese:
`source/intake.py` holds the two-pass line-by-line transcription (300–1000 dpi renders) and binds every
printed block, in printed order, to shared flow or a shared component (`source_manifest.json:component_map`),
following the same-family JE-1000D JP Web edition. Two printed tables have no shared component and are
declared plain tables (`shared_component_exceptions`): the 充電式電池のリサイクルについて notice beside its
Li-ion 32 mark and the four-column 省エネモード port table. The cover (p1) is not Web content; this print has
no contents page and no back cover. Japanese copy is unchanged; suspected source errors stay as printed and
are listed in `source_manifest.json:source_concerns`. Review reference: JE-1000D JP Web
(`manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2`).

## Artwork

- **Inventory first**: no Web edition of this model exists. Reused where the fixed comparison passes:
  the Li-ion 32 recycling mark and four LCD glyphs (high/low temperature, quiet charging, battery saving)
  reuse the JE-1000D JP Web glyphs byte for byte.
- **Symbols**: 6 rows (絵表示の説明). Four reuse shared bytes within the fixed 2% comparison (`mandatory/h1-jp-native`, `native/je1000d-jp-00c43a89-02`, `-05`, `-06`). The unplug and no-wet-hands pictograms (white backing disc offset from the glyph) bind their groups' canonicals `unplug/h1-jp-native` and `native/je1000d-jp-00c43a89-03`. A row that passes no shared variant binds the operator-confirmed canonical of its symbol group (shared PR #1659, decision SCG-20261103) when its printed caption is listed for that group; the release admission re-runs that rule.
- **LCD glyphs**: battery ring, low battery, energy saving (88H) and fault code are this print's native
  vector paths (no released glyph passes).
- **Panels**: 17 figures cut from `original.pdf` at 4x (`source/figures.json`), labels kept in the art and
  the alt text; the 3.液晶画面 heading printed inside the 各部の名称 panel rectangle is masked.

## Rebuild

```sh
PKG=manual_sources/JE-600C-SJ/JP/ja/git-20261103-3837e9fd
python3 "$PKG/source/extract_assets.py"     # about 1 minute (each page carries the whole artboard)
python3 "$PKG/source/intake.py"
rm -rf "$PKG/web" && python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --output "$PKG/web/ja"
python3 "$PKG/source/refresh_manifest.py"
python3 -m sphinx -n -W --keep-going -b html "$PKG/web/ja" tmp/je600csj-jp-site
```

PyMuPDF 1.28.0 / MuPDF 1.29.0 (`requirements.lock`).

## Boundaries

Git-only: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes; the only Feishu
calls were read-only downloads. No phase2 or print target is registered and no shared renderer, component,
contract, symbol library or workflow changed. Release follows the Git-only transaction
([web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction))
only after the operator accepts the renders and says 「上线提交发布」.
