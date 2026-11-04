# JE-1000B / JP / Japanese — Git-only Web candidate

Operator instruction, 2026-11-03 (relayed by the coordinating window): 「继续 转日语说明书」 — convert the 24
Japanese single-language manuals in the 发布文档管理 Base 日规 view that have a customer model and a
single-language PDF and no Web edition yet. This package converts the Japanese manual of the Jackery
ポータブル電源 1000 Pro (model JE-1000B) from the row `reczz28SfbsHcrCU` (material 38-0001-000030, project
HTE081). Route `JE-1000B/JP/ja/md`, `legacy_default` (no Web edition exists for this model).

**Status: `operator-approved-git-only-release`.** On 2026-11-04 the operator confirmed 「上线提交发布：JE-600A、JE-600C-SJ、JE-900B-WH、JE-1000B」 in the PR #1654 session after reviewing the 1280/390 renders beside the shared reference edition (with the symbol rows bound to the canonical groups of shared PR #1659). `source/approval.json` binds that acceptance to these exact source inputs and the IR is publication-eligible. Merge needs a separate operator authorization. Review points are in [`audit/review.zh.md`](audit/review.zh.md).

## Source authority

- `original.pdf`: the row's 「单语言说明书」 Japanese PDF, byte-exact (SHA-256 `46f1c569…`, 12 pages,
  130 × 185 mm, document code Jackery-UM-002). Every glyph is outlined, so the PDF has no text layer.
- Print master (「说明书文件」): `38-0001-000030 说明书 HTE0811000A-JP-JAK 说明书  RoHS REACH.ai`; name, size
  and SHA-256 in `source_manifest.json:print_master`. Not archived and not an extraction source.
- Identity (record id, material number, project, SKU) is in `source_manifest.json:document_identity`.
  No Feishu file token is stored.

## Method

The Explorer outlined-PDF kit (`manual_sources/JE-600A/US/en/git-20261028-9bf5bbb1`), adapted for Japanese
as in the JE-600C-SJ JP package: `source/intake.py` holds the two-pass line-by-line transcription and binds
every printed block, in printed order, to shared flow or a shared component
(`source_manifest.json:component_map`). The LCD run-ins print their glyph inline inside parentheses
(「バッテリーアイコン（◯）：」), so they are paragraphs with the glyph as an inline image and the text kept as
printed. The Qualcomm Quick Charge 3.0 logo printed in the 認証 cell follows the specification table as its
cropped source mark (HB-TABLE-SPEC cells carry text only). Two printed tables have no shared component and
are declared plain tables (`shared_component_exceptions`): the 充電式電池のリサイクルについて notice beside its
Li-ion 20 mark and the three-column 低電力モード port table. The cover (p1) is not Web content (its support
e-mail is not repeated elsewhere in the print); this print has no contents page and no back cover. Japanese
copy is unchanged; suspected source errors and the four uncertain transcript readings stay as printed (first
reading) and are listed in `source_manifest.json:source_concerns`. Review references: JE-1000D JP Web
(`manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2`) and JE-1000F JP Web
(`manual_sources/JE-1000F/JP/ja/git-20260930-d88b32fe-jp-reviewed`).

## Artwork

- **Inventory first**: no Web edition of this model exists (no JE-1000B US/en package either). Reused where
  the fixed comparison passes: the high/low temperature glyphs reuse the JE-1000D JP Web glyphs, the battery
  ring and the F8 fault-code glyph reuse the JE-600C-SJ JP glyphs, byte for byte. Art from US/en packages
  carries English words and is not reused for panels.
- **Symbols**: 6 rows (絵表示の説明). Four reuse shared bytes within the fixed 2% comparison (`mandatory/h1-jp-native`, `native/je1000d-jp-00c43a89-02`, `-05`, `-06`). The unplug and no-wet-hands pictograms (white backing disc offset from the glyph, as in JE-600C-SJ JP) bind their groups' canonicals `unplug/h1-jp-native` and `native/je1000d-jp-00c43a89-03`. A row that passes no shared variant binds the operator-confirmed canonical of its symbol group (shared PR #1659, decision SCG-20261103) when its printed caption is listed for that group; the release admission re-runs that rule.
- **LCD glyphs**: low battery and 12H low-power mode are this print's native vector paths (no released glyph
  passes / none exists); the Li-ion 20 recycling mark is native too (the JE-1000D JP mark is Li-ion 32).
- **Panels**: 16 figures cut from `original.pdf` at 4x (`source/figures.json`), labels kept in the art and
  the alt text; the 2.各部の名称 heading inside the parts panel rectangle and a body line inside the
  SolarSaga 80 panel rectangle are masked.
- **Extraction**: this PDF repeats the whole artboard on every page; its off-artboard path records are mapped since the shared `native_svg` fix in PR #1659, so `source/extract_assets.py` rebuilds the assets from scratch.

## Rebuild

```sh
PKG=manual_sources/JE-1000B/JP/ja/git-20261103-46f1c569
python3 "$PKG/source/extract_assets.py"   
python3 "$PKG/source/intake.py"
rm -rf "$PKG/web" && python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --output "$PKG/web/ja"
python3 "$PKG/source/refresh_manifest.py"
python3 -m sphinx -n -W --keep-going -b html "$PKG/web/ja" tmp/je1000b-jp-site
```

PyMuPDF 1.28.0 / MuPDF 1.29.0 (`requirements.lock`).

## Boundaries

Git-only: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes; the only Feishu
calls were read-only downloads. No phase2 or print target is registered and no shared renderer, component,
contract, symbol library or workflow changed. Release follows the Git-only transaction
([web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction))
only after the operator accepts the renders and says 「上线提交发布」.
