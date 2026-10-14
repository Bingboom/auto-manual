# JE-3600A / JP — Web-layout differences

## 2026-10-13: page-by-page layout pass against the PDF

Operator request: 「再审阅校正一下 这俩文档的版面 文档对应 发布 PR #220」 — re-review and correct the Web layout of the JE-3600A CN and JP manuals published by Bingboom/Hello-Docs#220. The method and standing instructions are the JHP-3000D ones: 「全部修，一次做完」, 「封面和目录 不用体现在web版面上」, and reuse of the existing shared components.

Review: the operator reviewed candidate `16368b7` on its chapter-by-chapter comparison page (print PDF beside the desktop and phone Web, CN and JP) and instructed 「上线发布」 on 2026-10-13.

Wording rule: the visible copy stays the reviewed copy. The only text edits restore the PDF where the reviewed intake disagreed with it; they are listed under [Copy restorations](#copy-restorations). Every other change is structure, weight, line breaks or artwork.

Base: the reviewed edition `git-20261012-fd06cd04-reviewed` (MA-298), same PDF (SHA-256 `fd06cd04…8dd6`). It stays immutable. `derive_web_layout.py` regenerates this edition from it; each edit is logged in `source/ja/web_layout.json` (`changes`, `copy_restorations`).

Page numbers are physical PDF pages; the printed folio is two less (p3 prints `01`).

### Structure and layout

| Page | Change | Log action |
| --- | --- | --- |
| 1–2 | The printed cover and the TOC are not shown. The cover title, `国内専用/For use only in Japan`, the support capsule and the お買い上げ notice go; the support address stays in the p27 contact block. Navigation has exactly the 14 chapters of the print TOC. | `printed-cover-removed` |
| 3 | 絵表示について and 絵表示の説明 are white-on-dark full-width bands. The four signal labels share the grey, centred label column. | `print-pill-title`, `signal-label-column` |
| 4–5 | The 警告 and 注意 lockups above the precaution tables print at about twice the body size. | `source/presentation.css` |
| 5 | The five symptoms run in three columns, read row by row, in print order. | `print-grid` |
| 6 | ご注意 is an outlined panel with the dark triangle; its body sits on white. | `signal-lockup` |
| 6–7 | The precaution lists print compact, one line per item. | `source/presentation.css` |
| 8 | The closing remark has the drawn square. The three notes sit in a white panel with a grey outline. The inbox art crop stops above that panel. | `print-square-note`, `print-outline-panel` |
| 10–11 | LCD glossary: one table (the print splits it at the page break), circled entry numbers, names left with the App note in small type below the name. | `one-glossary-table`, `lcd-name-note-lines` |
| 10–11 | Eight glossary glyphs are this print's own vectors. The reviewed edition reused JHP-3600A glyphs that lack this display's round and triangular frames, and its battery-pack glyph counts ×8 where this product prints ×5. | `native-lcd-glyph` |
| 10–11 | Every glossary glyph shows at its print height relative to the table text. The reused bitmaps had rendered at their own pixel sizes, from about half (the readouts) to 1.4 times print size. Names wrap where the print wraps them. | `lcd-glyph-print-height` |
| 14 | The 12H glyph sits in its two text lines and after the section title. The figure art drops the two in-text glyphs (24 paths); the live text carries the print's own glyph. The energy-saving table centres every cell. | `in-text-glyph` |
| 15 | Display modes: the mode and action columns are grey, one line each, and the table takes more of the panel than the art. | `lcd-mode-columns` |
| 15 | Button operations: the key column is grey from head to foot, the other heads are white and centred, and operations and functions read left, as printed. | `source/presentation.css` |
| 16 | UPS: the body under the figure sits in a grey panel. | `print-grey-panel` |
| 18 | The parallel icon closes the first check line (the reviewed edition put it before the second). ご使用前の確認 prints two bullets. | `inline-icon-position`, `print-bullets` |
| 18 | The figure label `Jackery Explorer 2000 Plus` is not shown: the print paints it over with the device drawing. | `hidden-print-label-removed` |
| 21 | ■ 必要なアクセサリー is a grey panel, not a section. | `print-grey-panel` |
| 22 | The adapter steps are a nested list. V<sub>OC</sub> has its subscript. | `print-nested-list`, `print-subscript` |
| 24 | Troubleshooting: the code column is grey from head to foot, 対処方法 heads a white column, and remedies sit mid-row. | `source/presentation.css` |
| 25 | Specifications: the four grids share one grey label column (a third of the width) with labels mid-row, and print-compact rows. ① ② are superscripts. | `spec-label-column`, `print-superscripts` |
| 26–27 | The ※ notes are grey capsules inside the warranty cards. | `print-note-capsules` |
| 28 | The App phone art no longer carries a line from the 備考 box under it: its crop reached into that box's outline. | `art-crop-sliver-removed` |
| 29 | 4.1 prints two bullets. | `print-bullets` |
| all | Lines break where the print breaks them (37). Spaces the intake inserted at print line wraps between Japanese characters are removed (153). Print bold runs are restored (19 containers). Titles keep their print case (`Jackery`, `50Hz`), and medium print faces read as regular weight. | `print-line-breaks`, `print-wrap-spaces`, `print-weights` |

Notes on the stylesheet choices:
- `.ht-print-medium` renders at weight 400. The Japanese fallback fonts have no 500 weight while the Latin ones do, so 500 would set Latin words heavier than the Japanese around them.
- On phones, the dense figures and the wide tables keep the reviewed edition's internal horizontal scroll. The merged glossary is one scrolling table instead of two.

### Copy restorations

These are the only visible-text edits. `tests/test_je3600a_cn_jp_web_layout.py` checks that the visible text equals the reviewed text minus the printed cover and the painted-over label, and that the log holds exactly these entries.

| Page | Reviewed Web | PDF (now) | Count |
| --- | --- | --- | --- |
| all | a space where a print line wraps between Japanese characters | no space | 153 (`print-wrap-space`, each with its line ids) |
| 5 | symptoms 4 and 5 in swapped order | print order: 内部に水や異物が入ったとき before 電源コード(AC充電ケーブル)が傷んだとき | 1 (`print-order`) |
| 14 | a run of spaces where the 12H glyph prints | the glyph | 2 (`inline-glyph-placeholder`) |
| 18 | parallel icon before 設定に失敗した場合は | after 並列アイコンが点灯表示されます。 | 1 (`print-icon-position`) |
| 18 | label `Jackery Explorer 2000 Plus` | not visible in print | 1 (`hidden-print-text`) |

### Kept as printed

These match the PDF text layer and are listed for the source owner:
- p25 `1×DC拡張ポ一卜（入力）` and `1×AC拡張ポ一卜（出力）`: the PDF sets 一 and 卜 (kanji) for ー and ト.
- p18–19 `ユニート`.
- p15 `Wi-Fi＆Bluetooth` uses the full-width ＆.
- p16 `UPSとして` has no space in the text layer.
- p30: the back-cover App block stays as printed.
