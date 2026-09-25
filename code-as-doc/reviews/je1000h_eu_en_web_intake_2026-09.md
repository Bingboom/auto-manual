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
