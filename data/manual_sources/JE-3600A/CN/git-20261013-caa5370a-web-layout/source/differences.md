# JE-3600A / CN — Web-layout differences

## 2026-10-13: page-by-page layout pass against the PDF

Operator request: 「再审阅校正一下 这俩文档的版面 文档对应 发布 PR #220」 — re-review and correct the Web layout of the JE-3600A CN and JP manuals published by Bingboom/Hello-Docs#220. The method and standing instructions are the JHP-3000D ones: 「全部修，一次做完」, 「封面和目录 不用体现在web版面上」, and reuse of the existing shared components.

Review: the operator reviewed candidate `16368b7` on its chapter-by-chapter comparison page (print PDF beside the desktop and phone Web, CN and JP) and instructed 「上线发布」 on 2026-10-13.

Wording rule: the visible copy stays the reviewed copy. The only text edits restore the PDF where the reviewed intake disagreed with it; they are listed under [Copy restorations](#copy-restorations). Every other change is structure, weight, line breaks or artwork.

Base: the reviewed edition `git-20261012-caa5370a-reviewed` (MA-298), same PDF (SHA-256 `caa5370a…81bb`). It stays immutable. `derive_web_layout.py` (the same file as in the JP edition) regenerates this edition from it; each edit is logged in `source/zh/web_layout.json` (`changes`, `copy_restorations`).

Page numbers are physical PDF pages; the printed folio is one less. The CN print has no TOC page: navigation is its 13 dark title bands, as in the reviewed edition, and the printed cover (p1) stays out of the Web edition.

### Structure and layout

| Page | Change | Log action |
| --- | --- | --- |
| 2–4, 8–10 | Print bold runs are restored: the p2 lead line and service line, the product-overview labels and the operation labels (开机, 关机, 总电源开关键 …). | `print-weights`, `reference-figures-rebound` |
| 5–7 | LCD glossary: one table (the print splits it over three pages), circled entry numbers, bold names left, descriptions left with one print line per state. | `one-glossary-table` |
| 5–7 | Eight glossary glyphs are this print's own vectors, and so are the two temperature glyphs inside the ⑲ descriptions. The reviewed edition reused JHP-3600A glyphs that lack this display's round and triangular frames, and its battery-pack glyph counts ×8 where this product prints ×5. | `native-lcd-glyph` |
| 5–7 | Every glossary glyph shows at its print height relative to the table text; the two glyphs inside sentences keep text height. The reused bitmaps had rendered at their own pixel sizes, from about half (the readouts) to 1.4 times print size. Names wrap where the print wraps them. | `lcd-glyph-print-height` |
| 9 | Screen display modes: mode and action keep one line each. | `lcd-mode-columns` |
| 10 | Button combinations: every cell is centred, the key column is grey from head to foot and the other heads are white, as printed. | `source/presentation.css` |
| 12 | 与加电包连接（单独售卖） is a plain bold title without the section dot. | `plain-title` |
| 13 | The figure label `Jackery Explorer 2000 Plus` is not shown: the print paints it over with the device drawing. | `hidden-print-label-removed` |
| 15 | 首次使用前请先将本设备充满电！ prints as a bold line behind an open warning triangle (the shared triangle), not as a section heading. | `print-warning-line` |
| 16 | V<sub>oc</sub> has its subscript, as the reviewed troubleshooting table already sets it. | `print-subscript` |
| 18 | Troubleshooting: the code column is grey from head to foot, 处理方法 heads a white column, rows are print-compact and remedies sit mid-row. | `source/presentation.css` |
| 19 | Specifications: the four grids share one grey label column (a third of the width) with labels mid-row, and print-compact rows. ① ② and ® are superscripts. | `spec-label-column`, `print-superscripts` |
| 20 | App: `1. 下载并登录App` keeps its print case. The three download lines form one block beside the QR code. The button-panel art no longer carries a grey sliver of the 备注 box above it: its crop started 1.2 pt inside that box. | `art-crop-sliver-removed` |
| all | Lines break where the print breaks them (17). Spaces the intake inserted at print line wraps between Chinese characters are removed (41). Titles keep their print case, and medium print faces (方正兰亭中黑, 兰亭黑) read as regular weight. | `print-line-breaks`, `print-wrap-spaces` |

Notes on the stylesheet choices:
- `.ht-print-medium` renders at weight 400. Chinese system fonts on Windows have no 500 weight while the Latin ones do, so 500 would set Latin words heavier than the Chinese around them.
- On phones, the dense figures and the wide tables keep the reviewed edition's internal horizontal scroll. The merged glossary is one scrolling table instead of three.

### Copy restorations

These are the only visible-text edits. `tests/test_je3600a_cn_jp_web_layout.py` checks that the visible text equals the reviewed text minus the painted-over label, and that the log holds exactly these entries.

| Page | Reviewed Web | PDF (now) | Count |
| --- | --- | --- | --- |
| all | a space where a print line wraps between Chinese characters | no space | 41 (`print-wrap-space`, each with its line ids) |
| 7 | a run of spaces where the ⑲ temperature glyph prints in the sentence | the glyph | 2 (`inline-glyph-placeholder`) |
| 13 | label `Jackery Explorer 2000 Plus` | not visible in print | 1 (`hidden-print-text`) |

### Kept as printed

These match the PDF text layer and are listed for the source owner:
- p2 `使使用本产品时，应始终遵循基本注意事项，包括:` repeats 使.
- p10 `Wi-Fi＆蓝牙开关` uses the full-width ＆; the next row prints `Wi-Fi&蓝牙重置`.
