# JE-1500B JP (ポータブル電源 1500 Pro) — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- Feishu record `reczz28SfbsHeofK`: 子物料编码 38-0001-000276, 项目号 HTE080, SKU 21-0001-000003, 客户型号 JE-1500B, 区域 日规.
- Authoritative monolingual PDF 「【Jackery ポータブル電源 1500 Pro】说明书-JP.pdf」, 3,029,337 bytes,
  SHA-256 `f61d0d68f37c32ceb7441d0853da40ad1087e7241a4bf925089d86f8074b0a65` (stored as `JE-1500B-JP-JA.pdf`).
  PDF title 「Jackery ポータブル電源 1500 Pro 取扱説明書 - 日本語」, subject 「Japanese section only; source artwork and printed page numbers retained」.
- 14 portrait pages, 130 × 185 mm (367.1 × 523.0 pt), exported from one Illustrator artboard: every page
  shares the same 22,095-drawing content stream, clipped per page. No text layer and no fonts.
- p1 cover (Jackery ポータブル電源, JE-1500B, Jackery-UM-002, Jackery ポータブル電源 1500 Pro 取扱説明書,
  国内専用/For use only in Japan, support e-mail, reading notes, QR); p2–p13 printed 1–12; p14 (9.免責事項) prints
  no page number. There is no paper TOC and no back cover.
- Print master 「38-0001-000276 说明书 HTE0801500B-JP-JAK  RoHS REACH.ai」 (12,975,431 bytes,
  SHA-256 `cbc0fd6400dd1451a01596a16820b3c9749a25248b5a90552c8d4877be0c8927`): reference only; not committed and not
  extracted, because the monolingual PDF is the extraction authority.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-1500B/US/en/git-20261027-bb5a455b/assets` (same model) | overview, LCD map, six LCD icons, AC/solar/car panels, five package-list cards |
| `manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2/assets` | LCD icons, Li-ion recycling mark, JP in-box cable, symbols |
| `manual_sources/JE-1500D/JP/ja/git-20261019-6ddeef54-v2/assets` | JP in-box cable, LCD, charging panels |
| `manual_sources/JE-1000F/JP/ja/git-20260930-d88b32fe-jp-reviewed/web/ja/assets/shared-lcd` | LCD description icons |
| every `manual_sources/*/*/*/*/assets/lcd-*` and `recycle*` file, `docs/renderers/web/assets/shared/lcd` | LCD icons at the fixed 2% tolerance |
| `docs/renderers/web/assets/shared/symbols` (all variants incl. #1632/#1640/#1641) | the six 絵表示の説明 symbols |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason |
| --- | --- | --- |
| LCD battery ring, low battery, 12H low power mode, F8 fault code, low temperature | reuse JE-1500B US/en files byte-identically | same glyph and tint: 0.0166 / 0.0050 / 0.0104 / 0.0084 / 0.0086 mean error at the fixed 2% |
| LCD high temperature | native vector extraction | closest committed glyph 0.0202 (> 2%) |
| Li-ion 20 recycling mark | native vector extraction | JE-1000D JP mark reads Li-ion 32 |
| overview, LCD map, AC / solar (5) / transjack / car panels | new complete JP panels | Japanese leader labels and captions; the LCD map's leader layout differs from the US art |
| Quick Charge 3.0 mark (認証 row) | new complete crop | not committed as a single mark |
| seven package-list cards | new JP card crops | unit and transjack are the US drawings at another print scale with heavier relative strokes (not identical pixels or line weight); JP car charger, two-prong AC cable, manual, warranty and pouch are not in the repository |
| 絵表示の説明 six symbols | **pending, not built** | see below |

No body text or table is an image: all copy is native HTML from `transcription.json`. Two panels share their
rectangle with a native text line (the 2.各部の名称 title beside the overview detail circle; the last line of the
SolarSaga 80 paragraph beside its 並列ポート label); the recipe masks those glyph areas white.

## Symbol table blocked by the shared native selector

`tools.asset_pipeline.native_svg.native_symbol_svg` refuses every page of this PDF ("native PDF fill/stroke SVG
mapping is unsupported": the single-artboard page SVG contains fill/stroke pairs whose two paths close
differently), exactly as recorded for the JE-1500B US/en PDF. Symbol admission
(`tools.web.symbol_asset_admission`) rebuilds each row's reference with that selector, so no HB-TABLE-SYMBOL-ICON
row can pass the gate on this source, even where a shared variant matches. Measured against an unclipped
direct-path reference (indicative only), the closest shared variants are je1000d-jp-00c43a89-symbol-02 (0.017),
-03 (0.023), h1-jp-mandatory (0.014), je1000d-jp-00c43a89-symbol-05 (0.022) and -06 (0.009); the unplug glyph is
built from clip paths and cannot be compared without the shared selector. The binding data for the shared fix is
in `asset_recipe.json:pending_symbols`; nothing was written to the shared library.
