# JE-1000H EU/en Web intake — 2026-09

## Scope

- Target: `JE-1000H / EU / en`
- Published source: `Jackery Explorer 1000 Plus User Manual (JE-1000H) EUUK V2.0-2026-08-03.pdf`
- Source SHA-256: `07e9ac4b9faabd0852f61702df06f2837caa952c2fa28151b599ad930b1c0bcc`
- Source size: 108 pages, 368.787 × 524.692 pt (approximately 130 × 185 mm)
- English manual body: physical PDF pages 6–22; EU radio declaration: physical page 108

## Controlled-source decisions

- The build reads only the target-scoped frozen snapshot under
  `manual_sources/JE-1000H/EU/en/2.0/phase2`; no live Bitable query is required.
- Product, port, LCD-map, battery-pack, charging, and App images are extracted
  from this JE-1000H source. No product illustration from another model is used.
- Product-overview crops exclude the source artwork's embedded FRONT VIEW and
  LEFT/RIGHT SIDE VIEW headings so the Web section headings are not duplicated.
- Text-bearing illustration frames consume their duplicated Web annotations.
  The LCD detail remains a searchable semantic HTML/CSS table beside the source
  numbered overview image; the manual is not published as PDF-page screenshots.
- Numeric values retain the published source notation, including 1024 Wh,
  1800 W rated / 3600 W surge, USB-C 140 W, 10 ms UPS transfer, and the DC
  expansion input/output limits.

## Verification and publication boundary

The extraction recipe, target illustration manifest, and every frozen source
file are SHA-256 locked. Local build, test, and preview evidence establish Web
readiness only. They do not establish merge, centralized publication, OSS
deployment, or a live asset-register write.

## Acceptance results

| Gate | Result |
| --- | --- |
| Approved-state asset replay | Pass: 108 archived pages, 108 previews, and 21 approved 12× illustration exports reproduced from the source PDF with locked hashes |
| Target source/manifest suite | Pass: frozen inputs, source manifest, illustration recipe/manifest, semantic output, cold IR replay, and asset-tamper rejection |
| Target build check | Pass: `build.py check` against the committed target-scoped frozen snapshot |
| Real Web build | Pass: 18 public-IR pages, 21 finished JE-1000H illustrations, 12/12 governed figure slots, 27 semantic LCD rows, and no unresolved placeholder token |
| Strict Sphinx | Pass: the generated MyST Web package builds with `python -m sphinx -W --keep-going -b html` |
| Generated-site media | Pass: 28 image references, zero missing files; localhost returned HTTP 200 for the manual and representative hash-addressed artwork |
| Browser layout | Pass: localhost preview was opened in the in-app browser; safety, LCD, charging, warranty, and App sections were visually inspected at the available narrow viewport without whole-page screenshot substitution |
| Asset registry | Pass: 219 records, 211 approved, zero registry errors; known missing/unmaterialized debt remains warning-only |
| Shared CI fixture | Pass: JE-1000H/EU/en runs instead of skipping; config-derived observation stays at 18 pass / 6 baseline skips / 2 baseline failures with both ratchets clean |
| Repository regression | Pass: 3,873 tests, 22 skipped |
| Static and policy checks | Pass: Ruff, maintainability guardrails, documentation links (170 files / 1,745 links / zero broken), Git diff check, and gitleaks |

## Remaining boundaries

- The Git-side target is ready for engineering review only; the branch and PR
  do not constitute merge or formal publication.
- No live Bitable source, capability, asset-source, or asset-registry row was
  written. The committed snapshot and CSV rows are the reproducible engineering
  input for this PR; any live synchronization requires separate authorization
  and exact record read-back.
- No Hello-Docs snapshot, OSS deployment, Read the Docs route, or production
  link has been created or verified.

## 2026-09-09 integration

The shared EU battery-pack slot uses generated-page model overrides so JE-1000H receives its reviewed chapter while JE-2000E retains its existing charging-page chapter without duplicates or foreign assets. Both target Web regression suites are included in integration validation.

## 2026-09-13 released-PDF specification reconciliation (candidate)

Rechecked physical PDF page 19 (printed 14) against the frozen source. Restore
the independent `AC Total Output` row (`1800W Rated, 3600W Surge peak`) and move
footnote 2 from the preceding AC value to this row's label. Preserve the PDF's
`2 × USB-C` parent label with explicit `USB-C 30W` and `USB-C 140W` parameter
labels, in that order, using existing source fields and native tables.

The source file lock and canonical compact/sorted JSON inventory hash are
refreshed. The previous inventory-level digest did not match this canonical
representation; a new regression now verifies it as well as each file digest.
Target regression: seven tests pass, including native HTML labels, footnote
placement, manifest locks and cold replay. This is not whole-book PDF parity,
browser acceptance or a new RTD deployment. The shared parser correction in
PR #1120 is merged at `fcfe46a6419a92eb751d4eed840c11e27e3538fc`; this
candidate is rebased onto it. Its target-data regression now explicitly checks
the source-authored parent/parameter representation and ordered power labels,
while the generic distinct-label preservation regression remains unchanged.

## 2026-09-25 App panels quarantined under the recipe gate

The 18 App panels of this source (`download_panel`, `control_panel` and `connect_result_panel` for en/fr/es/de/it/uk) were recipe-approved only because neither their keys nor their risk tags
carried a gate token (`app`, `qr`, `screenshot`, …). They are now quarantined
with `app-ui`/`screenshot`/`localized-ui` risk tags (plus `qr` for the download
panels); keys, outputs and hashes are unchanged, so the pages are unchanged.
`source_manifest.json` rebinds `asset_recipe`. The operator approved the fix on
2026-09-25.

## 2026-09-25 fr–uk specification cells rebuilt from the print

The live fr/es/de/it/uk specification tables showed 16–18 damaged rows out of 22
per language. Examples: `3600 W crêt`, `7,83 A Sort` and `12 В 10`, a lost `⎓`,
`Sortie totale CA 2` with the footnote number glued on, and English
`Product Name`/`Charge Mode`/`1 month`. The 2026-09-15 extraction had clustered
spans by baseline: the raised SegoeUISymbol `⎓` and cell ends fell out of their
lines. Its self-check compared digit sequences only, so none of this failed it.

The 25 specification and storage rows are now rebuilt from each block's table
cells, split by the page's ruling lines (PDF pages 36/53/70/87/104, storage
35/52/69/86/103). The rules, confirmed by the operator:

- Wording comes from the print.
- The house format of the reviewed frozen sources is applied: unit spacing,
  `V~ 50 Hz`, `max.`/`máx.`, fr/es `V CC`, `-10 °C`, `1 ×`, no `ﬁ` ligature,
  Cyrillic `В` and `мм` in Ukrainian, and French colon spacing.
- A cell whose current text already equals the print keeps its text.

Deviations from the print:

- **Print defects kept on reviewed cross-model wording:**
  - The de/it USB-C label is printed in French (`2 × Sortie USB-C`), so it reads
    `2 × USB-C-Ausgang` / `2 × Uscita USB-C`.
  - The German 12 V port is printed as `DC-12V-Ausgangstaste` (an output
    button), so it reads `1 × DC 12 V-Anschluss`.
  - Ukrainian prints the two USB-C ports as separate label rows, so they share
    the label `2 виходи USB-C` with the port names as parameters.
- **Newly substituted:**
  - The Italian bypass parameter is printed with the English `AC modalità
    bypass`, so it reads `Modalità bypass`.
  - The charge-mode parameter is not printed in fr/es/de/it, so it reads
    `Mode de charge`, `Modo de carga`, `Lademodus` and `Modalità di ricarica`.
    Ukrainian prints its own `Режим заряджання`.
- **Print typos fixed:** French `Oiture:` becomes `Voiture :`; Ukrainian
  `у байпасному режим` becomes `у байпасному режимі`.
- **Kept as printed although it differs from English:**
  - The German `3 × AC-Ausgang` value omits "rated".
  - The Ukrainian DC8020 lines omit the car/PV prefixes.
  - The de/it storage wording (`relative Luftfeuchtigkeit`, `tra … e …`)
    replaces earlier cross-model text.
  - Printed labels replace glossary labels, e.g. German `Ladetemperatur`. The
    reviewed JE-2000E/JE-2000F `Ladtemperatur` is itself a typo.

Verification:

- **Cells changed:** 167 in 25 rows (fr 31, es 30, de 35, it 37, uk 34). No
  source or English column is touched.
- **Independent print check:** 249 cells, each found in the plain PDF page
  text after canonicalisation. Only the listed substitutions are exempt.
- **Figures:** every value keeps the English digit sequence and `⎓` count.
- **Mapping control:** the English control lands 22/22 rows on their print
  cells.
- **Regression tests:** `Je1000hEuTranslatedSpecCellTests` fails 80 subtests
  on the previous file.
- **Trial Web build:** only the specification tables, the storage lines and the
  one safety sentence that quotes the temperature range change.

Remaining: the `Product overview` slot rows carry the same extraction damage into
the finished overview images' alt text, through `covered_annotations`. Fixing them
needs the five illustration manifests re-bound and is left as a follow-up.

## 2026-09-25 Ukrainian footnote ② completed

The Ukrainian footnote ② for the total AC output was printed without "струму"
("…вихідних портів змінного працюють разом"). The operator ruled to add the noun
in both JE-1000H and JE-3000C. One cell changes: `Spec_Footnotes.csv` `Text_uk`
for `ac_total_output`. The file is re-locked in `source_manifest.json`.

## 2026-09-26 Product-overview callouts and trademark note

This closes the follow-up left open on 2026-09-25. The finished fr–uk overview
figures consume their callout tables and keep the text as the image alt text
(`covered_annotations`). That alt text carried the 2026-09-15 extraction damage:
a lost `⎓`, truncated values (`1800 W nomi`, `12 В 10`, `…/400`), the PV/car
prefixes dropped, the `ﬁ` ligature and `~50 Hz` spacing. It also carried the
German print defect `DC-12V-Ausgangstaste`, which labels the 12 V socket as an
output button.

**What changed.** 41 `Spec_Master.csv` cells: the eight `Product overview` value
slots (DC 12 V, USB-C 140 W / 30 W, USB-A, AC output, AC input, PV, car) in each
of fr/es/de/it/uk, plus the German 12 V port label. Each value comes from its
block's printed overview (PDF pages 25/42/59/76/93). Callouts are grouped by font
(bold label, regular value lines) and located by column and position, which
all six blocks share. The rules are the same as for the specification cells:

- Wording comes from the print, in the house format of the reviewed frozen
  sources. JE-3000C's print-derived overview cells are the reference.
- Print defects use reviewed cross-model wording.

The five `je1000h_eu_<lang>_illustrations.json` overview bindings are re-bound
to the corrected tables, with the selectors unchanged. The other labels, the
controls and the total-output row are unchanged; total output is not printed
on this overview.

**Deviations from the print:**

- **German:** the 12 V port reads `12-V-DC-Anschluss`, as on JE-1000F, JE-2000E,
  JE-2000F and JE-3000C. The figure itself stays as printed.
- **French:** `Oiture:` becomes `Voiture :`; the truncated `1800 W nomina`
  becomes `1800 W nominal`, as in this model's specification table.
- **Spanish:** split decimals (`1, 5 A`) are joined.
- **Ukrainian:** the Latin `9V` becomes `9 В`.

**Trademark note.** The it and uk blocks print the German conjunction in
`※ USB Type-C® und USB-C® …`. `Spec_Notes.csv` now uses the reviewed `e`
(it) and `та` (uk) of the JE-1000F/JE-2000E/JE-2000F/JE-3000C EU rows. The live
notes table has no JE-1000H row, so there is nothing to write back.

**Verification:**

- **Independent print check:** every changed value, canonicalised, equals a run
  of whole lines in its overview page's plain `get_text("text")`. This is a
  different extraction path from the span extractor that built the cells, and
  it also catches truncation. Only the listed substitutions are exempt. The
  pre-change file fails 36 of the 41 cells.
- **Figures:** every value keeps the English digit sequence and `⎓` count.
- **English control:** 8 of 8 value slots land on their printed callout
  digits.
- **Regression tests:** `Je1000hEuOverviewSlotTests` also checks that every
  overview cell appears in its figure's binding. It and the trademark-note test
  fail 50 subtests on the previous files.
- **Trial Web build:** against the origin/main build, only the two overview
  `alt` attributes change on each fr–uk route, plus the trademark line on it and
  uk. English is unchanged. Against the live pages, the only other difference
  is the callout label-sizer spans that main already carries (#1288).
- **Live tables:** no `JE-1000H_EU` rows exist in 规格参数明细 or 页面占位参数
  (only AU/KR rows), so the frozen source is the only place to fix.

## 2026-09-27 Ukrainian warning label

The 2026-09-15 intake entered the uk symbols-table label as printed. The print
sets the Italian `AVVERTENZA` there (PDF page 91, printed 86). The same page
prints the uk WARNING callout as `ПОПЕРЕДЖЕННЯ`, and every other EU frozen
source uses that label.

**What changed.** Three cells in two files:

| File | Row | Columns | Before | After |
| --- | --- | --- | --- | --- |
| `Localized_Copy.csv` | `symbols.signal.warning.label` | `text_uk` | `AVVERTENZA` | `ПОПЕРЕДЖЕННЯ` |
| `symbols_blocks.csv` | `warning` | `label_uk`, `aliases_uk` | `AVVERTENZA` | `ПОПЕРЕДЖЕННЯ` |

**Verification:**

- **Trial Web build:** all six languages, compared with the live pages
  (`2.0-20260926`). Only the uk symbols-table row changes: its badge
  `aria-label` and its visible label. The other five languages have no line
  changes.
- **Regression test:** `Je1000hEuResidualCopyTests` resolves the uk label
  through the localized-copy loader. It also checks every fr–uk displayed signal
  label and heading: none may be empty, English or another block's word. The
  one exception is the heading the print sets in English (below). The test fails
  3 subtests on the previous files.
- **Live tables:** there is nothing to write back.
  - The approved Translation_Memory row `recvllSNnTchQq` (`WARNING`) has uk
    `ПОПЕРЕДЖЕННЯ`.
  - So does the shared 内容源_Symbols row `recviwLdx0HcdN`.

**Open question for the operator: the de/it temperature heading.** The de and
it blocks print `ENVIRONMENTAL OPERATING TEMPERATURE` in English (PDF page 70,
printed 65; page 87, printed 82). Under 以 PDF 为准 the frozen source keeps it
as printed. If it should be translated, a reviewed wording exists:

- de `UMGEBUNGSTEMPERATUR IM BETRIEB` and it `TEMPERATURA OPERATIVA AMBIENTALE`;
- the JE-2000F EU print sets this wording (PDF pages 66/82);
- the approved Translation_Memory row `recvgEwErzHV3h` holds it;
- the JE-2000E, JE-2000F, JE-3000C and JE-3600A sources carry it.

The JE-3600A EU print and the JE-3000C EU print (V2.0-2026-09-15) set the same
English heading, while their sources translate it.

**Still open.** These are the same kind of defect, but the print gives no
correct text in the block, or the text comes from a shared template:

- **LCD row 4:** the de/it description falls back to English. Both blocks print
  it in French (PDF pages 60/77). The German name prints as `Ladeplan Plan`.
- **Italian LCD rows 11–13:** PDF page 78 prints the German `Verbleibende
  Aufladezeit` and `Autoladeanzeige`. It also shifts the car and solar texts up
  one row. The source copies all of this.
- **Shared EU templates:** the fr–uk operation caution says `USB-C 100 W` and
  omits the `28 V/5 A, 140 W` cable rating. The print says 140 W in every block
  (PDF pages 12/29/46/63/80/97). The it heading `LUCE LED ON/OFF` prints as
  `LUCE LED ACCENSIONE/SPEGNIMENTO` (PDF page 80).
