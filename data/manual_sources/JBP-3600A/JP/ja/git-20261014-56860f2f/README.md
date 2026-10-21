# JBP-3600A / JP / ja — Git-only production-sheet intake

This package freezes the supplied Japanese production drawing for the Jackery Battery Pack 3600 (model JBP-3600A, internal code HTP0113600A, part number 16-0102-000060, printed version V0.1). It converts the printed manual pages 01–10 into a Japanese Web edition.

**Status: operator-accepted Git-only release.** After the layout review (PR #1528), the operator accepted this edition for release on 2026-10-14 (「合入了，上线授权你合入」), keeping the defaults of the three points listed for their decision. `source/approval.json` binds that acceptance to these exact source inputs, and the replayed IR is `publication_eligible: true`. Merge and release run under MA-303 in `code-as-doc/dev/merge_authorizations.md`.

## The source is one production sheet

`16-0102-000060 说明书 HTP0113600A-JP-JAK RoHS REACH.pdf` (8,785,016 bytes) is one 3715 × 2605 pt page:

- Inside a drawing frame sit twelve 130 × 185 mm panels in a 6 × 2 grid. Exact origins are in `source_manifest.json` → `panel_grid`.
- The top row is the front of the sheet and the bottom row is the back (production note: 正反面印刷, 折页).
- Reading order is left to right, top row first. Panel 1 is the cover and panel 2 the contents (JP 日本語 01-10). Panels 3–12 carry folios 01–10, so the set is complete.
- Identity comes from the content: cover 型番：JBP-3600A, "Jackery Battery Pack 3600", 国内専用; specification 型番 JBP-3600A.

The PDF is an Illustrator 26 master (PDF 1.6 with Illustrator editing data). Text comes from its live text objects, never OCR.

Of its 22 optional-content layers (all named 图层 1), the page uses only one, and that one wraps the whole sheet; the other 21 are unused. The layers therefore do not separate the panels from the production frame; the drawn panel grid does.

Each panel is read as one page in panel-local PDF points. The cover and contents are not in the Web body (operator: 「封面和目录 不用体现在web版面上」). Nor is the production metadata outside the panels: frame zone grid, title block, revision table (V0.1 第一次发行) and production notes. Every one of the sheet's 588 words is classified, each excluded region with its recorded reason (`source_manifest.json` → `excluded_pages`, `source/ja/coverage.json`).

## Reconstruction

- `source/native.py` reassembles and verifies the archived PDF. It maps words and spans to panels and holds the print rules:
  - Japanese wraps join without a space.
  - A line the print ends at least one em short after closing punctuation, or three ems short anywhere, keeps its line break. There are 18, logged in the coverage file.
  - Bold runs stay strong.
- `source/intake.py` maps reviewed panel regions to shared flow nodes and components and writes `source/ja/content.json` and `source/ja/coverage.json`. The coverage gate refuses any unclassified word, any duplicate live copy and any unused text recovery.
- `source/text-recovery.json` restores two visible marks drawn as outlines: UN38.3 and the ■ before the p03 notice.
- `source/extract_assets.py` acquires every asset from its recorded decision in `source/figures.json` (reuse, 4x panel crop, 4x text-free panel, native vector glyph or embedded image). `--check` verifies the recorded hashes.
- `rebuild.py` verifies the archived PDF, every inventoried input and the pinned shared repository inputs, then replays through the shared Manual IR APIs.

Component inventory: HB-CALLOUT-STRIP 4, HB-SPECIAL-INBOX 1, HB-SPECIAL-REFERENCE-FIGURE 10, HB-TABLE-TROUBLESHOOTING 1, HB-WARRANTY-SECTION 6.

## Print fidelity

| Print | Web |
| --- | --- |
| Chapter bands; sub-bands and ● subheads | h2 chapters (10, as the contents lists them); h3 for 絵表示について, 絵表示の説明, オン/オフ, LCDディスプレイのオン/オフ, AC充電, ソーラー充電（別売）, 免責事項 |
| 警告 / 注意 / 説明 / ヒント signal table | Native two-column grid; the filled triangle of 警告 and 注意 is the shared JP battery-pack glyph |
| 説明 and ご注意 boxes, the p07 警告 box | Shared callout strip; the 警告 box uses the shared warning lockup |
| Symbol table (8 rows) | Native grid; shared native-v1 symbols, matched to the print by raster comparison and side-by-side review |
| Inbox cards ①②③ | Shared inbox component |
| Troubleshooting table | Shared troubleshooting component, as in JBP-2000B / JBP-3600A EU, with the print's エラーコード / 対処方法 header row |
| LCD and specification tables | Native grids, as printed, with no header row; 保存温度 keeps its three lines; LiFePO4 keeps its subscript |
| Warranty cards (保証期間 … 保証内容) | Shared warranty sections. The grey introduction and the grey 免責事項 panel stay grey panels. |
| Labelled figures (overview, LCD, on/off, clearance, lock, AC and solar charging) | Text-free art with the printed labels as live Japanese text on their print positions (shared base-art reference, as JBP-2000B / JBP-3600A EU). On phones, list-style labels stack under the art in reading order; short marks stay on the art. |
| Other figures | Complete panels with no visible captions; alt text carries the caption |

All two- and three-column tables fit a 390 px phone, and none scrolls at any width from 320 to 1920 px (`audit/browser-validation.json`).

Print-source wording is kept as printed. Examples: "Jackery Explorer 3600 Plus" exists only as hidden 0.8 pt art text inside the illustrations, and the warranty intro says "Jackery ポータブル電源製品" in a battery-pack manual. Nothing is corrected here.

## JBP-2000B reference

Operator, 2026-10-14: 「用JBP-2000B的参考」. JBP-2000B EU and JBP-3600A EU are the layout and structure references. Content stays as printed. Where following them would change printed content, the print wins and the difference is listed here:

- **Troubleshooting:** uses the shared troubleshooting component, as in the reference.
- **Signal-word table:** stays a native grid. The shared signal component always renders a header row (記号 / 意味), which the JP print does not have.
- **LCD table:** stays a native grid. The shared LCD icon component adds an icon to each row, which the JP print table does not have.
- **Specification table:** stays a native grid. The shared spec component needs a printed group title; the JP print has one untitled table, not the reference's three groups.
- **Symbol table:** stays a native grid of shared native-v1 symbols (operator, option a). The shared symbol component needs source-bound symbol admission, and its vector mapper (`tools/asset_pipeline/native_svg.py`) fails on this Illustrator sheet, whose fills paint through glyph clip paths.
- **Chapter order:** follows the print, which puts 充電方法 before トラブルシューティング. The print has no STORAGE chapter.
- **Figures:** text-free art with live labels, as in the reference. The operator chose option (a), 「不改共享工具」, on 2026-10-14, so the art is 4x raster PNG, not vector.

## Artwork reuse

Inventories were checked before extracting; decisions are in `source/figures.json` and `audit/asset-decisions.json`. Of 26 assets:

- **13 reused byte-identically:**
  - from the published JBP-3600A EU English Web, where the print matches: inbox unit, inbox cable, LCD on/off panel, stacking panel;
  - from the shared native-v1 library: eight symbols and the filled triangle.
- **7 text-free panels**, where the JP print differs from every candidate: the JP plug, the ≥ 20cm dimensions, the ロック tags, the オフ/オン labels, the three-quarter overview, the LCD leaders.
  - The printed label lines are removed on an in-memory copy with the shared pipeline's `redact_text` operator (text removed, line art and images kept), then rendered at 4x.
  - The labels become live copy.
  - Step numbers ①② and the 0.8 pt nameplate text stay in the art.
- **1 complete-panel crop:** this manual's cover thumbnail on the inbox card.
- **4 native vector glyphs:** the outlined ⊟×5 connection icon and the three filled contact icons. The existing JBP-5000A / JE-3600A versions are a dark badge and outline icons.
- **1 embedded image:** the QR code.

## Run

From the repository root (PyMuPDF 1.28.0 / MuPDF 1.29.0, `requirements.lock`):

```sh
PKG=data/manual_sources/JBP-3600A/JP/ja/git-20261014-56860f2f
python3 "$PKG/source/extract_assets.py" --check
python3 "$PKG/source/intake.py"
python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --output tmp/jbp3600a-jp/ja
python3 -m sphinx -n -W --keep-going -b html tmp/jbp3600a-jp/ja tmp/jbp3600a-jp-site/ja
```

To re-freeze:

1. Remove `web/ja`.
2. Run `source/refresh_manifest.py`.
3. Rebuild into `web/ja`.
4. Run `source/refresh_manifest.py` again.

Test: `python3 -m unittest tests.test_jbp3600a_jp_ja_web`.

## Boundaries and source archive

Git-only boundary:

- No Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes. The only Feishu call was the read-only download of the operator-supplied file (wiki node `M55Xw0ZLqiLjDDkJMW3cND7anSg`, file token `ZNSpbZq5LohTN2xM8aQcRSbknEh`).
- No phase2 or print target is registered.
- JBP-3600A is already in the portal navigation's battery group, so the product matrix is unchanged.

The unchanged original PDF is archived as one binary part, `source/pdf-archive/part-001.bin`, within the 32 MiB per-file budget. Its SHA-256 is `56860f2f24a11f4a1ccc7fa8392299b6400b3aa36b669451c376fd310eb9160e`. `native.py` and `rebuild.py` verify it before they run.
