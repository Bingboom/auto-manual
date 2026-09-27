# JE-1000F EU/UK English and French Web input candidate

Released-PDF authority: V2.0 EU-UK, 2026-06-18. This shared snapshot supports
two separate language builds; `en-fr` is a storage label, not a build locale.
It is not a published release or approval of the other language columns.

The source inventory and provenance are in `source_manifest.json`. Reviewed
RST is retained under `docs/_review/JE-1000F/EU`; use `review-asis`, not runtime
templates, to preserve reviewed button labels and app setup instructions.
The historical review manifest is retained as imported provenance, not proof
of the current release version or freshness of its file hashes.

Only target-matching/shared CSV rows and referenced assets are included.
The composite manifest contains 55 approved EU panels (11 per locale for
EN/FR/ES/DE/IT), with embedded localized text, plus one `locale=shared` App
connect-result panel: all five language blocks of the PDF print the same
English App screens (PDF physical page 22 in the EN block). Specifications,
LCD mode and other semantic tables remain HTML, not screenshots. No online
table or queue is required.

PDF-backed normalizations in this candidate:

- Remove the extra AC-input bypass line from EN/FR reviewed specification
  carriers and the isolated specification data; it is absent on PDF physical
  pages 19 and 36. Keep the actual bypass-output row and its footnote.
- Add the PDF's exact EN/FR bypass-output footnote to the scoped snapshot.
  The old shared snapshot had it bound to other models only.
- Retain already approved 6.5 A AC output, 4000-cycle life, and 0 C minimum
  charging temperature. Historical row IDs/version columns remain source
  identifiers; the released-PDF version is 2.0, not the old row version 1.0.
- The EN/FR PDF parity pass restores the safety accessory condition, LCD
  mapping and charging description, 12 A maximum qualifier, troubleshooting
  wording, App step 2.5, separate USB-C rating rows and PDF section order.
  It removes the extra battery-disposal row and the unsupported Output Resume
  default/App instruction. See [PDF parity notes](pdf_parity_notes.md).

Build each locale with the existing family single-language configuration
(both inherit the shared EU single-language base; no new config is added):

```sh
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off AUTO_MANUAL_PRESENTATION_PROFILE=web \
python3 build.py check --config configs/config.eu-en.yaml \
  --model JE-1000F --region EU --lang en --source review-asis \
  --data-root manual_sources/JE-1000F/EU/en-fr/2.0/phase2 \
  --staging-root /tmp/je1000f-eu-en-verification
```

Repeat with `configs/config.eu-fr.yaml`, `--lang fr` and a different staging
root. Do not use the merged `config.eu.yaml`: its source index includes a
French preface absent from the accepted single-language preview.
Then run `build.py md`
with the same inputs, assemble RTD source below that staging build root, and
run strict Sphinx. Release identity must use the verified locale,
not infer it only from a filename. Immutable language evidence, visual checks and
the business release PR remain required before production publication.

ES/DE/IT build from the same data root with their `config.eu-<lang>.yaml`
and `--source review`, not `review-asis`: their reviewed LCD pages fail the
`review-asis` LCD-table validation (row 20). Use `review`, not the default
`auto`, for all three release actions. Under `auto`, `check` skips the review
sync that `md` runs, so the check, md and html language-projection captures
differ and staging refuses them. On 2026-09-24 the `review` build matched the
published 2026-09-14 ES/DE/IT pages except for the App connect-result figure,
which now uses the shared panel.

App screenshots (2026-09-24): the reviewed promotion `je1000f-eu-app-ui-v1`
(#1252) resolves `asset:app/add_device` and `asset:app/connect_result` to the
EU print's own screens for JE-1000F/EU. The EN page and the EN/FR generated
drafts already used those URIs. The FR/ES/DE/IT/UK pages (p31/p46/p61/p76/p91)
and the DE/ES/IT/UK generated drafts pointed at the shared JP-market
screenshots through raw `common_assets/app/*.png` paths; they now use the same
URIs, matching Hello-Docs #125 on `review/JE-1000F-EU`, and
`source_manifest.json` re-locks those nine files. The visible Web App panels
are unchanged; the connect-result figure's hidden semantic image becomes the
EU export in all five languages.

In-box, LCD display mode and UPS art (2026-09-26): these pages showed shared
art: a unit with US outlets in the box, and another, wheeled model in the LCD
mode and UPS figures. Target overrides cropped from this print
(`data/asset_recipes/manual_je1000f_eu_uk_20260618_block_art.json`) now serve
`in_the_box/main_unit1`, `operation/lcd_mode` and `operation/ups_mode` by
language: EN takes the English block (PDF pages 7, 14, 15; BS 1363 sockets),
FR/ES/DE/IT/UK the French block (pages 24, 31, 32; EU sockets). The LCD crops
keep the 536×404 px layout of `op_lcd_mode.png` that the IDML LCD panel assumes.
The FR/ES/DE/IT/UK pages, the DE/ES/IT/UK generated drafts and the EN in-box
LaTeX macro now reference them as `asset:` URIs (the charging pages'
`main_unit1` sits in a JE-2000E-only block and is unchanged), and
`source_manifest.json` re-locks those 20 files. On the Web, all five routes
change exactly these three visible figures; alt text and copy are unchanged.

Figure alt text (2026-09-27): the EN/DE/IT/ES review pages that feed the Web
carried template alt text that called each figure a placeholder (`… image
placeholder.`, `… als Platzhalter.`, `Platzhalter für …`, `Segnaposto …`,
`Marcador de posición …`). These 22 pages now describe the figure in the page
language, as the shared templates do. A composite's approval hash covers its
semantic fragment, alt text included, so the 33 EN/DE/IT
`source_fragment_sha256` values in `phase2/web_composite_manifest.json` are
re-approved against these pages; the approved panel art is unchanged. The UK
pages and the generated drafts, which no published Web route reads, keep their
wording. `source_manifest.json` re-locks the 23 files.

German 12 V caution (2026-09-27): the p53 page named the car socket
`Der DC-12-V-Anschluss`; it now reads as the print's DE block does (PDF page
64): `Die DC-12V-Buchse ist nur mit 12-V-Autobatterien kompatibel und nicht für
24-V-Systeme geeignet.` The other two bullets of that caution already match the
print. `source_manifest.json` re-locks p53.

French App alt text (2026-09-27): the p31 page's three App figures carried alt
text that called them a reserved slot (`… emplacement réservé aux boutiques.`,
`Emplacement réservé à …`); they now describe the figure, as the shared FR
templates do. No composite covers these figures. `source_manifest.json`
re-locks p31.

Storage durations (2026-09-26): the Spanish and German storage rows carried
each other's duration labels (es `1 monat/3 monate/12 monate`, de `1 mes/3
meses/12 meses`). `phase2/Spec_Master.csv` (`Param_es`, `Param_de`) and the
p42/p57 review pages now hold the print's es `1 mes/3 meses/12 meses` (PDF page
52) and de `1 Monat/3 Monate/12 Monate` (page 70). The print sets the German
labels in lowercase; they are capitalized as in JE-2000E's print and the other
models. `source_manifest.json` re-locks the three files.

Operating temperature heading (2026-09-27): the ES/DE/IT specification pages
showed the English heading `ENVIRONMENTAL OPERATING TEMPERATURE`, because the
`title_es`, `title_de` and `title_it` cells of that row in
`phase2/spec_titles.csv` held the English fallback. They now hold the print's
es `TEMPERATURA DE FUNCIONAMIENTO` (PDF page 53), de
`UMGEBUNGSBETRIEBSTEMPERATUR` (page 71) and it `TEMPERATURA OPERATIVA
AMBIENTALE` (page 88). The matching `phase2/Localized_Copy.csv` row
(`spec.section.environmental_operating_temperature`) does not render on the
Web but now holds the same values. The `--source review` build rebuilds the
spec pages from these cells, so the review pages are not edited. FR keeps its
reviewed heading and the FR/UK cells are unchanged. `source_manifest.json`
re-locks the two files.

Specification tables (2026-09-27): the FR/ES/DE/IT specification tables now
follow each print block in values, structure and labels (PDF pages 36, 53, 71
and 88). Unit spacing, case, the decimal comma, `⎓` and `max.` keep the house
format.

- FR, from the `page/spec_fr.rst` review page (`review-asis`), in both
  carriers: `N° modèle`, capacity `1024 Wh (20 Ah / 51,2 V DC)`, and the ①
  bypass footnote now comes before the ※ USB Type-C note, as printed.
- ES/DE/IT, from `phase2/Spec_Master.csv`: the merged USB-C row is split into
  the printed 30 W and 100 W rows (es `Salida USB-C 30 W`, de
  `1 × USB-C-Ausgang 30 W`, it `1 × Uscita USB-C 30 W`, and the same for
  100 W). The de/it 100 W line loses a temperature condition the print does
  not have, and the es DC8020 line 2 gains the printed `12 A máx.`. The other
  labels follow the print: es `Química de las celdas`, `Vida útil en ciclos`
  (with the printed value), `1 × Puerto CC 12 V` and capacity `… V DC`; de
  `2 × DC8020-Ports` and `1 × USB-A`; it capacity `1024 Wh (20 Ah / 51,2 V DC)`,
  `Vita ciclica`, `1 × USB-A` and `Temperatura di scarica`.
- `phase2/Spec_Footnotes.csv` (`ac_bypass`, `Text_es`/`Text_de`/`Text_it`) holds
  each block's printed bypass footnote, so the bypass row gets its ① marker.
- `phase2/spec_titles.csv` (`title_it`) and its non-rendering
  `phase2/Localized_Copy.csv` twins hold the printed `PORTE IN INGRESSO` and
  `PORTE IN USCITA`.

Print defects keep the reviewed wording: the IT block's `60 Hz` AC rows stay
50 Hz, the DE block's `máx.` stays `max.`, and the DE table's `Ladtemperatur`
becomes `Ladetemperatur`, as the DE block spells it in running text (PDF page
67). The DE port headings mix two nouns in the print (`EINGANGSPORTS` /
`AUSGANGSPORTE`, PDF page 71). `phase2/spec_titles.csv` (`title_de`) and its
`phase2/Localized_Copy.csv` twins now hold the reviewed pair
`EINGANGSANSCHLÜSSE` / `AUSGANGSANSCHLÜSSE`. The JE-1000H EU print
(V2.0-2026-08-03) and the JE-3600A EU print (2026-05-25) set that pair on PDF
page 70 of each. The IT DC8020 line 2 keeps the print's `12 A` without `max.`;
it may be a print defect, but it is left as printed. The ES/DE/IT review pages
are not edited, because the review sync rewrites them from these cells. Like
their print blocks, they now render the ① footnote before the ※ note, through
`docs/templates/spec_template_footnotes_first.rst` (#1306, see the notes-order
note below). EN is unchanged:
its block (PDF page 19) prints the ※ note first. `source_manifest.json`
re-locks the four CSV files and the FR review page.

Specification notes order (2026-09-27): the FR/ES/DE/IT blocks of the print set
the footnote above the ※ USB Type-C trademark note (PDF pages 36/53/71/88); the
EN block sets the ※ note first (page 19). The `spec` row of
`phase2/page_registry.csv` now names
`docs/templates/spec_template_footnotes_first.rst`, whose HTML branch (the Web,
and the Word bundle, which takes its order from the HTML) puts the footnotes
first. Its LaTeX branch is identical to `spec_template.rst`, so the PDF and IDML
are unchanged. The `--source review` build regenerates the ES/DE/IT spec pages
through this template, so the review pages are not edited. EN and FR build
`review-asis` from their reviewed pages, which this change does not touch; EN
keeps the printed ※-first order. `source_manifest.json` re-locks the registry
and records the change.
