# JHP-5000C / US — Web-layout differences

## 2026-10-10: page-by-page layout pass against the PDF

Operator request: 「继续调一下 这个的版面」 for the published JHP-5000C US manual, with the PDF from the Feishu record. Scope chosen: 「英法西一起改」 (EN, FR and ES together). Standing instructions: 「全部修，一次做完」 and 「封面和目录 不用体现在web版面上」. The reviewed JE-1000F Web manual is the layout reference.

Review correction on 2026-10-10, with the print p4 and the published JE-1000E-SIL page as references: 「不对 这个你要改两列的啊」「线上有很多现成的 都是双栏的啊」「不需要你重新另写」. The safety lists therefore reuse the existing two-column safety section instead of new styles.

Wording rule: the visible copy stays the approved copy. The only text edits restore the PDF where the approved intake disagreed with it; they are listed one by one under [Copy restorations](#copy-restorations). Every other change is structure, weight, line breaks or artwork.

Base: the approved edition `git-20261009-051169dd` (MA-279), same PDF (SHA-256 `051169dd…c26a`). It stays immutable. `derive_web_layout.py` regenerates this edition from it; each edit is logged in `source/<language>/web_layout.json` (`changes`, `copy_restorations`).

Page numbers are physical PDF pages of the English block. French is +24 and Spanish +48 (for example EN p16 = FR p40 = ES p64).

### Structure and layout (EN, FR and ES)

| EN page | Change | Log action |
| --- | --- | --- |
| 1–3 | The printed cover and the print TOC are not shown. Navigation has exactly the 14 chapters of the TOC on p3, under each chapter's own page heading. | `nested-under-print-chapter` |
| 4–6 | User maintenance, Meaning of symbols and the FCC statement are sub-sections of IMPORTANT SAFETY INFORMATION, as printed. | `nested-under-print-chapter` |
| 24–27 | The HomePower, Battery Pack, Smart Transfer Switch and Package List sections are sub-sections of the AC ESS installation guide. | `nested-under-print-chapter` |
| 2 | Each language block keeps its outlined region badge (US, FR, ES). | `print-badge` restoration (EN) |
| 4 | Both safety lists run in two columns, as printed. The page reuses the two-column safety section of the published template manuals (JE-1000E-SIL): the `hb-safety-instruction` risk banner, the `hb-safety-lead` WARNING panel heading the left column and two `manual-two-col-table` rows, styled by the shared `web_safety_components.css`. Each item stays in the print column it starts in (6 + 5 and 5 + 9 items); phones get one column. | `shared-safety-two-columns` |
| 4 | Safety sub-titles are white-on-dark pills. DANGER is an outlined lockup with the dark triangle; its body is bold, and `※` starts its own print line. | `print-pill-title`, `danger-lockup`, `danger-callout-lines` |
| 5 | The signal-word table has the print's three rows. | `signal-word-meanings` restoration |
| 5 | The FCC statement is a panel without a title; the print has none. | `unprinted-title-removed` |
| 6–7 | The front, left and right views are framed so the approved paths are whole: handle-button inset, wheels and panel edge. Edge labels align to the panel edge. Labels render at 95% so none collide at tablet and phone widths. | `full-frame` |
| 7, 10–11 | State words (on/off, marche/arrêt, encendido/apagado …) are regular weight, as printed. | `regular-state-words` |
| 8–9 | LCD glossary: circled numbers; one number cell per printed entry, so equal adjacent entries share one cell (12, 13, 20); each state starts its own line. | `lcd-icon-print-structure` |
| 11 | LCD SCREEN: the device art sits beside its table of two states × three actions. The cells are rebuilt from the print table geometry with exactly the approved words; the Spanish fragments are rejoined. | `lcd-screen-table` |
| 12 | Troubleshooting: codes and names are bold; each cause starts its own description line. | `codes-names-bold-cause-lines` |
| 13 | Online UPS: the activation steps and the numbered notes are ordered lists. | `paragraph-numbered-steps`, `callout-numbered-items` |
| 14 | SOLD SEPARATELY is a capsule beside its title. The numbered caution items are a list. | `sold-separately-capsule`, `callout-numbered-items` |
| 15 | "Fully charge …" is a white-on-dark prose capsule. | `prose-pill` |
| 16–17 | "• Connect to …" lines are bold bullet sub-heads. Low-PV caution item 2 is no longer nested in the example bullet. Numbered notes are lists. A sentence that ends a print line early starts a new paragraph. | `bullet-subhead`, `caution-item-2-unnested`, `callout-numbered-items`, `print-paragraph-break` |
| 16 | The Caution label the intake read into the middle of its body is the callout label again. ES p59 has the same fix for the car-charging Nota. | `inline-label-callout`, `misplaced-callout-label` restorations |
| 19 | Storage: paragraphs split at print line wraps are joined; the split bullet lists are one list each. | `soft-wrap-joined`, `adjacent-lists-merged` |
| 20–21 | App: notes whose label was read as its own block, or glued to the body, are callouts. | `glued-label-callout`, `split-label-callout` |
| 22 | Warranty cards: paragraphs follow the print, and each exclusion is its own paragraph. FR p46 and ES p70 have the year-card title/body boundary fixed. | `warranty-print-paragraphs` |
| 23, 25 | Specifications: each print line of a value cell is one value of that label. The `®` marks are superscripts at their print positions. | `spec-value-print-lines`, `trademark-note` |
| 23, 25, 26 | INGESTION HAZARD notes carry the print's warning glyph and bold label. They sit in their print place, before the trademark note (EN p25). FR p47 and ES p71 have the hazard note below the table instead of fused into the last temperature row. | `ingestion-note`, `ingestion-before-trademark`, `hazard-note-below-table` |
| 24 | AC ESS: the System Model sits in the title band. The caution requirements are one per print line. | `system-model-in-band`, `callout-print-lines` |
| 25–26 | Product sections: the model identity sits at the right of the print band, and "SPECIFICATIONS" is a plain bold title. | `model-in-band`, `plain-title` |
| 4–27 | Bold runs of the print (lead-ins, sub-heads) inside plain paragraphs and list items. | `print-emphasis` |
| 76 | Back cover: JACKERY INC., the address, and one contact panel with the print's phone, mail and web glyphs, plus the QR code in its own frame. The print has no "CONTACT US" title. | `back-cover-card` |

### Copy restorations

These are the only visible-text edits. Each one makes the Web match the PDF where the approved intake did not. `tests/test_jhp5000c_us_web_layout.py` checks that the visible text equals the approved text plus exactly these edits. The only other visible differences are layout: the shared LCD number cells and list numbers that the browser now draws.

**English** (9)

| Page | Approved Web | PDF (now) |
| --- | --- | --- |
| 2 | badge `EN` | `US` |
| 4 | DANGER body ends with a repeated `DANGER` | label printed once, as the lockup |
| 5 | two signal rows, with shifted meanings | three rows: WARNING (severe injury, death …), CAUTION (personal injury …), Note (equipment damage …) |
| 5 | heading `FCC` | no title |
| 16 | `… is Caution within 16V-60V …` | label `Caution`, body without it |
| 23, 25 | `® ® ※ USB Type-C and USB-C …` | `※ USB Type-C® and USB-C® …` (two notes) |
| 26 | `Model: JBP-5000A` under the STS section | in the Battery Pack band |
| 76 | heading `CONTACT US` | no title |

**French** (9)

| Page | Approved Web | PDF (now) |
| --- | --- | --- |
| 28 | DANGER body ends with a repeated `DANGER` | label printed once |
| 29 | AVERTISSEMENT / ATTENTION with shifted meanings | MISE EN GARDE, AVERTISSEMENT, Remarque |
| 29 | heading `FCC` | no title |
| 33 | `Indicateur d'entrée PV` / `élevée Indicateur d'entrée PV faible` | `Indicateur d'entrée PV élevée` / `Indicateur d'entrée PV faible` |
| 40 | `… la sortie de tension Mise en garde maximale …` | label `Mise en garde`, body without it |
| 46 | 5-year card: `Garantie standard` read into the body | title `Garantie standard`, body `La période de garantie standard …` |
| 47 | `RISQUE D’INGESTION` note fused into the discharge-temperature row | note below the table |
| 50 | `Modèle: JBP-5000A` under the STS section | in the Battery Pack band |
| 76 | heading `CONTACTEZ-NOUS` | no title |

**Spanish** (16)

| Page | Approved Web | PDF (now) |
| --- | --- | --- |
| 52 | DANGER body ends with a repeated `PELIGRO` | label printed once |
| 53 | ADVERTENCIA / PRECAUCIÓN with shifted meanings | PRECAUCIÓN, ADVERTENCIA, Nota |
| 53 | heading `FCC` | no title |
| 54 | `* Nota` | `Nota`: the `*` is painted over by the note box |
| 57 | `… baja tensión FV Indicador de` / `expansión de CA (Carregamento)` | `… baja tensión FV` / `Indicador de expansión de CA (Carregamento)` |
| 59 | `… cable de carga de batería Nota para automóvil …` | label `Nota`, body without it |
| 61 | title `FUENTE DE ALIMENTACIÓN ININTERRUMPIDA` plus a stray `(UPS)` | `FUENTE DE ALIMENTACIÓN ININTERRUMPIDA (UPS)` |
| 64 | `… de todos Precaución los paneles …` | label `Precaución`, body without it |
| 69 | last line `… la cuenta de la` (the rest was taken for the folio) | `… la cuenta de la aplicación conectada.` |
| 70 | 5- and 2-year cards: titles read into the bodies | titles `Garantía estándar`, `Garantía extendida` |
| 71 | `RIESGO DE INGESTA` note fused into the discharge-temperature row | note below the table |
| 71, 73 | `® ® ※ USB Tipo-C y USB-C …` | `※ USB Tipo-C® y USB-C® …` (two notes) |
| 74 | `Modelo: JBP-5000A` under the STS section | in the Battery Pack band |
| 76 | heading `CONTÁCTENOS` | no title |

### Artwork

Asset reuse order (STYLE_DEFINITION): existing assets are inventoried first, and each decision is in `source/asset_decisions.json`.

- **Reused byte-for-byte:**
  - the shared `warning_triangle_dark.svg` and `warning_triangle_white.svg`;
  - all approved art except the five files below.
- **Re-framed (only the SVG viewBox changed):** `overview-front.svg`, `overview-left.svg` and `overview-right.svg` grow to their full print frame.
- **New native glyphs** (no shared equivalent exists):
  - the ingestion-hazard warning glyph (p23, also on p25/26);
  - the p76 phone, mail and web glyphs and the manual's QR code.
- **FR/ES print panels.** The French and Spanish pages redraw these panels: scale, zoom circles, brackets and caption-plate positions differ, so the English panel cannot carry the localized label geometry. Each panel is acquired from its own locale page with the same drawing selection as English:
  - ac-output, usb-output, dc-output, sts-charge, car, low-pv-500, low-pv-200, ac-charge, high-pv, high-pv-lock, dual-pv, ess, battery-packs and app-control (FR and ES);
  - package-sts (FR only);
  - overview-left (FR and ES) and overview-front (FR only). These have the same drawing list as English, but the leader lines move for longer copy: 6.6 pt for the left view's NEMA 14-50, 2.9 pt for the front view.
- **Car panels:** the FR/ES car panels are re-acquired with their plug cable (`car-fr.svg`, `car-es.svg`); the approved records are marked superseded.
- **Per-language asset sets:** each `web/<language>/assets` carries only the art that its own copy and the source stylesheet reference. The other locales' panels stay in the package pool.

### Print-source issues kept as printed

The Web keeps these as printed; they are questions for the source owner, not Web fixes.

- **Text in the wrong language:**
  - FR p28: the DANGER body is printed in Spanish.
  - ES p52: the DANGER body is printed in French.
  - ES p65: caution item 1 ends in Portuguese (`… durante a manutenção`).
  - ES p62: the chapter title is the English `CONNECTIONS`.
  - ES p74/75: `VENDU SÉPARÉMENT` is in French.
  - ES p68: an App-control label is in French.
  - ES p57: the LCD terms `Carregamento` / `Descarregando` are Portuguese.
  - ES p70: the `Exclusions` heading is not translated.
- **Spelling and spacing:**
  - EN p23/p25: `Onine UPS`.
  - FR p43 and ES p67: a missing space (`adéquate.Température`, `adecuada.Temperatura`).
  - FR p42: `vehícule`.
  - FR p46: `offciel`.
- **Wording:**
  - EN p24/p26 name the Explorer 5000 Plus in the AC ESS text.
  - The French TOC (p3) shortens the AC ESS title; the Web uses the page heading.
- **Legibility:** the ES p65 caption `Desmonte los conectores MC4 con la llave MC4 proporcionada.` is printed almost white on white; the Web shows it as live text.
- **Order:** ES p53 prints PRECAUCIÓN above ADVERTENCIA; the Web keeps the print order.

The inherited `source/native_exceptions.json` records the same retained items.

### Known limitations

- `LiFePO4` keeps a regular 4. The specification table contract compares one text run per value, so a subscript cannot be expressed.
- The FCC statement does not mirror the print's column break.
- Specification values printed side by side (`Backup UPS … Online UPS …`, `Bypass AC Output`) stay on one line.
- The Furo theme chrome (search, navigation labels) is English on the FR/ES pages.
