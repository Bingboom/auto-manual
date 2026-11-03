# JE-900B-WH / JP / Japanese — Git-only Web candidate

Operator instruction, 2026-11-03 (relayed by the coordinating window): 「继续 转日语说明书」 — convert the 24
Japanese single-language manuals in the 发布文档管理 Base 日规 view that have a customer model and a
single-language PDF and no Web edition yet. This package converts the Japanese manual of the Jackery
ポータブル電源 900 (models JE-900B / JE-900B-WH) from the row `reczz28SfbsHf180` (material 16-0102-000412,
project HTE2610). Route `JE-900B-WH/JP/ja/md`, `legacy_default` (no Web edition exists for this model).

**Status: `review-candidate-no-release-authorization`.** No `source/approval.json`; the IR is not
publication-eligible until the operator reviews the 1280/390 renders beside the reference editions and says
「上线提交发布」 in this package's PR session. Review points are in [`audit/review.zh.md`](audit/review.zh.md).

## Source authority

- `original.pdf`: the row's 「单语言说明书」 Japanese PDF, byte-exact (SHA-256 `66c65187…`, 27 pages,
  130 × 185 mm). Every glyph is outlined, so the PDF has no text layer.
- Print master (「说明书文件」): `16-0102-000412 HTE2610960A-JP-JAK 电子版说明书A1 RoHS REACH Q.pdf`; name, size
  and SHA-256 in `source_manifest.json:print_master`. Not archived and not an extraction source.
- Identity (record id, material number, project, four SKUs) is in `source_manifest.json:document_identity`.
  No Feishu file token is stored.

## Method

The Explorer outlined-PDF kit (`manual_sources/JE-600A/US/en/git-20261028-9bf5bbb1`), adapted for Japanese
as in the JE-600C-SJ JP package: `source/intake.py` holds the two-pass line-by-line transcription (300–600 dpi
renders, bounding boxes re-measured) and binds every printed block, in printed order, to shared flow or a
shared component (`source_manifest.json:component_map`). Two printed tables have no shared component and are
declared plain tables (`shared_component_exceptions`): the three-column 省エネモード table with its merged
デフォルト設定 cell and the LEDライト steps with their pictograms. The cover (p1) and the contents page (p2) are
not Web content; the back cover (p27) carries the App download note, store badges and QR code and closes the
App chapter (it has no contact data of its own; the contact pills are on p24 in 保証について). Japanese copy is
unchanged; suspected source errors stay as printed and are listed in `source_manifest.json:source_concerns`.
Review references: the same-family JP Web editions JE-1000F
(`manual_sources/JE-1000F/JP/ja/git-20260930-d88b32fe-jp-reviewed`) and JE-1000D
(`manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2`).

## Artwork

- **Inventory first**: no Web edition of this model exists. Art in the Explorer US/en packages carries English
  words and is not reused for panels; all panels are cut from this print.
- **Symbols**: 13 rows (絵表示の説明 ten pictograms, and the three disposal marks on p04), each compared with
  every shared variant by the symbol admission's fixed comparison. Eleven reuse shared bytes. The unplug
  pictogram (solid disc without the shared variant's ring) and the Li-ion 32 recycling mark (heavier arrows
  and larger label than every shared Li-ion variant) pass no shared variant; they stay as pending native
  candidates and were reported to the coordinating window for the batch shared-symbol PR — release admission
  refuses them until the shared library carries them. The per-row pictograms of the 警告/注意 tables
  (including the protective-earth mark) repeat the legend and are not repeated (template form).
- **LCD glyphs**: 26 rows; the battery ring and the F8 fault-code glyphs reuse the JE-600C-SJ JP Web glyphs
  byte for byte. Six candidates from the JE-1000D JP Web edition (quiet charging, battery saving, high/low
  temperature, low battery, 88H) fail the fixed comparison; those and the remaining icons are this print's
  native vector paths, as are the inline 12H mark and the three LED step pictograms.
- **Panels**: 28 crops from `original.pdf` at 4x (`source/figures.json`): 22 reference figures, three inbox
  cards, the LCDスクリーン drawing (HB-TABLE-LCD-MODE artwork) and the App store badges and QR code
  (HB-SPECIAL-APP download). Labels stay in the art and the alt text. The pointer of the p12 speech bubble below
  the power-button drawing is masked; the bubble text is set as a shared text panel. The UPS panel keeps its
  in-panel speech bubble in the art and its text once more as the following paragraph (declared in
  `component_map`).

## Rebuild

```sh
PKG=manual_sources/JE-900B-WH/JP/ja/git-20261103-66c65187
python3 "$PKG/source/extract_assets.py"     # about 20 seconds
python3 "$PKG/source/intake.py"
rm -rf "$PKG/web" && python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --output "$PKG/web/ja"
python3 "$PKG/source/refresh_manifest.py"
python3 -m sphinx -n -W --keep-going -b html "$PKG/web/ja" tmp/je900bwh-jp-site
```

PyMuPDF 1.28.0 / MuPDF 1.29.0 (`requirements.lock`).

## Boundaries

Git-only: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes; the only Feishu
calls were read-only downloads. No phase2 or print target is registered and no shared renderer, component,
contract, symbol library or workflow changed. Release follows the Git-only transaction
([web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction))
only after the operator accepts the renders and says 「上线提交发布」.
