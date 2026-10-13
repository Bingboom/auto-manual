# JHP-3000D / US — Web-layout differences

## 2026-10-13: page-by-page layout pass against the PDF

Operator request: 「把这个版面调整一下」 for the published JHP-3000D US manual (`JHP-3000D/US/en/md/manual_jhp3000d_us_en.html`). As for JHP-5000C, the scope is EN, FR and ES together (「英法西一起改」). Standing instructions: 「全部修，一次做完」 and 「封面和目录 不用体现在web版面上」. Layouts reuse the existing shared components (「线上有很多现成的 都是双栏的啊」「不需要你重新另写」).

Review correction on 2026-10-13, on the first comparison page (POWER ON/OFF figure): 「这个对话框太圆了 没有统一样式吗」. The figure note boxes therefore take the shared panel radius instead of the one-line capsule. After reviewing the updated page, the operator instructed 「上线提交发布」.

Wording rule: the visible copy stays the approved copy. The only text edits restore the PDF where the approved intake disagreed with it; they are listed one by one under [Copy restorations](#copy-restorations). Every other change is structure, weight, line breaks or artwork.

Base: the approved edition `git-20261009-cebe4aab` (MA-278), same PDF (SHA-256 `cebe4aab…cf27`). It stays immutable. `derive_web_layout.py` regenerates this edition from it; each edit is logged in `source/<language>/web_layout.json` (`changes`, `copy_restorations`).

Page numbers are physical PDF pages of the English block. French is +18 and Spanish +36 (for example EN p13 = FR p31 = ES p49). p2 holds the three prefaces and p58 the shared back cover.

### Structure and layout (EN, FR and ES)

| EN page | Change | Log action |
| --- | --- | --- |
| 1, 3 | The printed cover and the print TOC are not shown. Navigation has exactly the 13 chapters of the TOC on p3, under each chapter's own page heading: the FCC statement belongs to MEANING OF SYMBOLS, and the back-cover contact card closes APP SETUP. | `unprinted-title-removed`, `back-cover-card` |
| 4 | Both safety lists run in two columns, as printed. The page reuses the two-column safety section of the published template manuals: the `hb-safety-instruction` risk banner with the dark triangle, the `hb-safety-lead` WARNING panel heading the left column, and two `manual-two-col-table` rows styled by the shared `web_safety_components.css`. Each item stays in the print column it starts in (6 + 5 and 5 + 9 items). `SAVE THESE INSTRUCTIONS` heads the left column of the operating instructions, as printed. Phones get one column. | `shared-safety-two-columns` |
| 4–5 | OPERATING INSTRUCTIONS and USER MAINTENANCE INSTRUCTIONS are white-on-dark pills. GROUNDING INSTRUCTION is a plain bold title without the section dot. | `print-pill-title`, `plain-title` |
| 5 | The grounding WARNING and the indoor-use DANGER are outlined lockups with the shared dark triangle. Their bodies are bold, and the DANGER `※` sentence starts its own print line. | `signal-lockup` |
| 6 | The FCC statement is a panel without a title, after the symbol tables; the print has none. | `unprinted-title-removed` |
| 8–9 | LCD glossary: circled entry numbers. The two entries printed under ㉑ share one number cell. Each state (`On:`, `Blink:`, `Off:` …) and each `Note:` starts its own print line, in the print's weight. | `lcd-icon-print-structure`, `lcd-label-print-weight` |
| 8–12, 20–21 | State words are regular weight, as printed: EN `Blink`, `powered on`; FR `Allumé`, `Clignotant`, `Éteint`, `allumé`; ES `Encendido`, `Parpadeo`, `Apagado`, `encendido`. | `regular-state-words` |
| 10–11 | The speech bubbles and notes of the operation panels are left-aligned, as printed. The standby note no longer breaks in mid-sentence. The live caption slots are re-derived from the print lines and their hashes rebound. | `standby-bubble-sentence-wrap`, `reference-figures-rebound` |
| 10, 11, 16 | Every note box in the figures has the shared panel radius (`--hb-panel-radius`). Print draws all of them with one corner radius, so the multi-line notes are rounded rectangles, not the shared one-line capsule. The approved stylesheet asks for this radius, but its rule lost to the capsule rule. | `source/presentation.css` |
| 11 | Car charging: the CAUTION label the intake glued to stray body words is the callout label again (EN). | `callout-label-restored` |
| 11 | The auto-resume conditions use the shared auto-resume table (`HB-TABLE-AUTO-RESUME`); the middle condition spans two rows, as printed. | `shared-auto-resume` |
| 12 | Energy saving mode: a sentence that ends a print line early starts a new paragraph (EN, ES). | `print-paragraph-break` |
| 13 | Button operations use the shared key-combination table (`HB-TABLE-KEY-COMBINATIONS`). It shows the print's vertical POWER, AC and DC/USB buttons, the button names in print order and the printed hold times with the clock glyph. | `shared-key-combinations` |
| 13 | UPS: one paragraph per print paragraph (EN 4, FR 4, ES 3; the ES print has no 10 ms sentence). | `print-paragraph-break` |
| 14 | "Fully charge the product before its first use." is a white-on-dark prose capsule. | `prose-pill` |
| 14–15 | `Green energy first:` is a bold lead-in. FR and ES split the charging paragraphs where the print does. | `print-emphasis`, `print-paragraph-break` |
| 17 | Troubleshooting: the codes F0, F1, F2 and F3 are stacked one per line, as printed. | `stacked-fault-codes` |
| 18 | Specifications: each print line of an INPUT PORTS value cell is one value of that label. The `®` marks are superscripts at their print positions. | `spec-value-print-lines`, `trademark-note` |
| 19 | Warranty cards: paragraphs follow the print. | `warranty-print-paragraphs` |
| 20–21 | App: bold words of the print (EN `POWER`, `"Icon Flashed"`, `OK`, `Settings`, `Unbind`, and `"the device has been bound"` in the NOTE). The Unbind paragraph that the intake split at print line wraps is one paragraph again. | `print-emphasis`, `soft-wrap-joined` |
| 21 | Steps 2.3–2.5 show this product's App screens, as printed. | `native-app-screens` |
| 58 | Back cover: JACKERY INC., the address, and one contact panel with the print's phone, mail and web glyphs (phone number bold), plus the QR code in its own frame. | `back-cover-card` |

### Copy restorations

These are the only visible-text edits. Each one makes the Web match the PDF where the approved intake did not. `tests/test_jhp3000d_us_web_layout.py` checks that the visible text equals the approved text plus exactly these edits. The only other visible differences are layout: the shared LCD number cell and the separators that the shared key-combination table draws.

**English** (5)

| Page | Approved Web | PDF (now) |
| --- | --- | --- |
| 6 | heading `FCC` | no title |
| 11 | label `The product can cable, which is CAUTION` | label `CAUTION`; the stray words were copies of the body |
| 13 | rows 2 and 3: `DC/USB power button POWER button`, `AC power button DC/USB power button` | `POWER button` + `DC/USB power button`, `DC/USB power button` + `AC power button` |
| 13 | no hold times | `3s`, `3s`, `1s` |
| 17 | `F0 / F1 / F2 / F3` | `F0`, `F1`, `F2`, `F3`, one per line |

**French** (5)

| Page | Approved Web | PDF (now) |
| --- | --- | --- |
| 24 | heading `FCC` | no title |
| 29 | auto-resume: `SOC de la batterie ≥ limite de décharge` and `+10% après avoir atteint la limite` as two conditions | one condition, `SOC de la batterie ≥ limite de décharge +10% après avoir atteint la limite`, spanning two rows |
| 31 | rows 2 and 3: `Bouton d'alimentation CC/USB Bouton d'alimentation principal`, `Bouton d'alimentation CA Bouton d'alimentation CC/USB` | `Bouton d'alimentation principal` + `Bouton d'alimentation CC/USB`, `Bouton d'alimentation CC/USB` + `Bouton d'alimentation CA` |
| 31 | no hold times | `3s`, `3s`, `1s` |
| 35 | `F0 / F1 / F2 / F3` | `F0`, `F1`, `F2`, `F3`, one per line |

**Spanish** (5)

| Page | Approved Web | PDF (now) |
| --- | --- | --- |
| 42 | heading `FCC` | no title |
| 47 | auto-resume: `SOC de la batería ≥ límite de descarga` and `+10 % después de alcanzar el límite` as two conditions | one condition, `SOC de la batería ≥ límite de descarga +10 % después de alcanzar el límite`, spanning two rows |
| 49 | rows 2 and 3: `Botón de energía CC/USB Botón de encendido principal`, `Botón de energía CA Botón de energía CC/USB` | `Botón de encendido principal` + `Botón de energía CC/USB`, `Botón de energía CC/USB` + `Botón de energía CA` |
| 49 | no hold times | `3s`, `3s`, `1s` |
| 53 | `F0 / F1 / F2 / F3` | `F0`, `F1`, `F2`, `F3`, one per line |

### Artwork

Asset reuse order (STYLE_DEFINITION): existing assets are inventoried first, and each decision is in `source/asset_decisions.json`.

- **Reused byte-for-byte:**
  - the shared `warning_triangle_dark.svg` (p4 banner, p5 lockups) and `warning_triangle_white.svg` (p4 WARNING lead);
  - all approved art, which stays in the package pool unchanged.
- **New native glyphs** (no shared equivalent exists):
  - the vertical POWER, AC and DC/USB button faces of the p13 table (`button-power-p13.svg`, `button-ac-p13.svg`, `button-dc-usb-p13.svg`). Every shared button draws a horizontal switch.
  - the p58 phone, mail and web glyphs and the manual's own QR code (the App download QR is a different code).
- **p13 POWER button:** the approved table showed a shrunken copy of the p10 POWER ON/OFF panel in place of the POWER button. The shared button face and the p10 panel art share the file name `power.svg`, and the package carries the panel. The new button faces fix this; `power.svg` stays the p10 panel.
- **App steps 2.3–2.5:** the approved edition reused JHP-3600C screens, which show an Explorer 1000 with a 1000 W input. Print p21 shows this product (3000) with an 1800 W input, so `app-steps-2-3-to-2-5.png` is rendered from p21 at 600 dpi with the complete phone frames and step numbers. FR p39 and ES p57 print the same screens.
- **Superseded records:** the approved decisions for the shared `power.svg`, `ac.svg` and `dc_usb.svg` button faces and for `app_connect_result_steps.png` are marked `superseded_by_web_layout`. `ac.svg`, `dc_usb.svg` and `app_connect_result_steps.png` are no longer referenced.
- **Per-language asset sets:** each `web/<language>/assets` carries only the art that its own copy and the source stylesheet reference.

### Print-source issues kept as printed

The Web keeps these as printed; they are questions for the source owner, not Web fixes.

- **FR p23:** the indoor-use DANGER lockup is labelled `AVERTISSEMENT`, like the grounding WARNING above it.
- **ES p50:** the prose capsule is printed in French (`Chargez complètement le produit avant sa première utilisation.`).
- **ES p49:** the UPS text has no 10 ms switching sentence.
- The approved edition's native exceptions stay as printed: English TOU / Discharge Timer text in FR/ES, French energy labels in English, the Spanish warranty unit `ÑOS`, and the others in `source/native_exceptions.json`.

### Known limitations

- `LiFePO4` keeps a regular 4. The specification table contract compares one text run per value, so a subscript cannot be expressed.
- The App setup sub-headings use the shared heading style, without the print's dot.
- Troubleshooting: F0–F3 share one row of the shared troubleshooting table, so the print's rules between the four codes are not drawn.
- The Furo theme chrome (search, navigation labels) is English on the FR/ES pages.
