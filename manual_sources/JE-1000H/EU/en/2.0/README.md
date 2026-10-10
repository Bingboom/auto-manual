# JE-1000H EU/en formal Git source

This directory is the audited, target-scoped build input for the Git-only Web
release of `JE-1000H / EU / en`, version `2.0`.

- Authority: `Jackery Explorer 1000 Plus User Manual (JE-1000H) EUUK
  V2.0-2026-08-03.pdf`, SHA-256
  `07e9ac4b9faabd0852f61702df06f2837caa952c2fa28151b599ad930b1c0bcc`.
- Structured source: [`phase2/`](phase2) contains the English target rows and
  shared dictionaries required for the build. It has no live Bitable dependency.
- Artwork: 20 target-local Web images are extracted by the hash-locked recipe.
  Text-bearing panels retain their complete source frame; the LCD uses a source
  numbered overview image beside a searchable semantic HTML/CSS table.
- Publication boundary: this Git source and its local preview are not a Web
  publication, merge, or live asset-register update.

Build it with:

```text
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off \
AUTO_MANUAL_PRESENTATION_PROFILE=web \
python build.py md \
  --config configs/config.eu-en.yaml \
  --model JE-1000H --region EU --lang en \
  --data-root manual_sources/JE-1000H/EU/en/2.0/phase2 \
  --staging-root <fresh-root>
```

Recipe gate (2026-09-25): the 18 App panels in `asset_recipe` are quarantined as App UI;
`source_manifest.json` rebinds the recipe hash. Pages are unchanged.

Translated specification cells (2026-09-25): the fr/es/de/it/uk specification and
storage cells of `phase2/Spec_Master.csv` are rebuilt from each language block of
the released PDF (table cells split by the page's ruling lines). The earlier
extraction had dropped `⎓`, truncated values and glued footnote numbers onto
labels. `source_manifest.json` re-locks the file; English is unchanged.

Ukrainian footnote ② (2026-09-25): the print omits "струму" ("…вихідних портів
змінного працюють разом"); the operator ruled to add it here and in JE-3000C.
`source_manifest.json` re-locks `phase2/Spec_Footnotes.csv`.

Product-overview callouts (2026-09-26): the fr/es/de/it/uk value slots of the
`Product overview` rows follow each block's printed overview (PDF pages
25/42/59/76/93) in the house format of the reviewed frozen sources. The earlier
extraction had dropped `⎓` and the PV/car prefixes and truncated values. The
finished overview figures keep this text as their alt text, so the five
`docs/renderers/web/je1000h_eu_<lang>_illustrations.json` overview bindings
change with it. The German 12 V port label takes the reviewed
`12-V-DC-Anschluss`; the print calls the port an output button
(`DC-12V-Ausgangstaste`), and the figure stays as printed. In
`phase2/Spec_Notes.csv`, the it/uk trademark note replaces the printed German
`und` with the reviewed `e` / `та`. `source_manifest.json` re-locks both files.

Ukrainian warning label (2026-09-27): the uk symbols table prints the Italian
`AVVERTENZA` (PDF page 91). The uk WARNING label now reads `ПОПЕРЕДЖЕННЯ`, as
the same page prints it on its safety callout, in `phase2/Localized_Copy.csv`
and `phase2/symbols_blocks.csv`. `source_manifest.json` re-locks both files.
The de/it temperature heading, which the print sets in English (PDF pages
70/87), now uses the reviewed `UMGEBUNGSTEMPERATUR IM BETRIEB` /
`TEMPERATURA OPERATIVA AMBIENTALE` in `phase2/spec_titles.csv` and
`phase2/Localized_Copy.csv` (operator ruling 2026-09-27); `source_manifest.json`
re-locks both files.

Specification tables follow the print (2026-09-27): the operator ruled that
values, structure and labels follow the print, formatting keeps the house rules,
and print defects keep the reviewed wording. In `phase2/Spec_Master.csv`, AC
input line 1 loses its charge-mode label in en/fr/es/de/it (only the uk block
prints `Режим заряджання:`, PDF page 104). The Italian bypass line reads the
printed `AC modalità bypass` (PDF page 87). Both English DC expansion rows read
`1 × DC Expansion Port` (PDF page 19). The Ukrainian USB-C row splits into the
printed `виходи USB-C 30W` / `виходи USB-C 140W` rows, whose value cells have no
parameter label. An empty `Param_uk` falls back to the English `Param_source`, so
the appended `line_text_uk` column (the documented `line_text_*` rendered-line
field) holds those two lines; each repeats `Value_uk`. `source_manifest.json`
re-locks the file.

Specification notes order (2026-09-27): every language block of the print sets
the footnotes above the ※ USB Type-C trademark note (PDF pages
19/36/53/70/87/104), while the Web put the ※ note first. The `spec` row of
`phase2/page_registry.csv` now names
`docs/templates/spec_template_footnotes_first.rst`, whose HTML branch (the Web,
and the Word bundle, which takes its order from the HTML) puts the footnotes
first. Its LaTeX branch is identical to `spec_template.rst`, so the PDF and IDML
are unchanged. `source_manifest.json` re-locks the registry.

LCD shared-component repair (2026-09-30): the 27 blank Figure references now
bind existing business-plane LCD attachments, shared by all six locale builds.
`lcd_icon_provenance.json` records each live record ID, attachment content hash and
indicator-to-approved-callout mapping. No translated copy, overview artwork or
numbering was changed. The existing `HB-TABLE-LCD-ICON` renderer preserves
source line blocks and bold status prefixes. The fresh-release contract now
requires this component for all six LCD chapters; their old text-only debt is
removed. Connected Batteries retains its existing 43 × 34 px source image as
explicit quality debt; no invented or newly cropped icon is approved here.

German status emphasis retains the authored `Blinkt:` wording. The target's
status dictionary includes it alongside `Blinken`, without rewriting the
released descriptions or changing the live translation-memory table.

Batch 1465 label backport (2026-10-10): the frozen German LCD callout 4 now
reads `Ladeplan`, and the Italian callout 11 reads `Tempo di carica rimanente`.
These exact labels match the delivered AI/PDF correction records and the live
business LCD rows `recvhBxMIMFPLf.icon_de` / `recvhBxNA2r0u7.icon_it`; no live
source table was written. `source_manifest.json` re-locks the target-local CSV.
The Spanish UPS heading already has its initial `F` in the published Web copy.
The print's Italian callout 13 solar wording is not applied: this Web callout
binds the car-charging icon, while callout 14 already names solar charging.
The operator confirmed the semantic repair on 2026-10-10: callout 12 uses
`Indicatore di ricarica CA a parete` and the AC-grid description from live row
`recvhBxNA2Y2s0`; callout 13 uses `Indicatore di ricarica da auto` and the DC
12 V car description from `recvhBxNA2WNYW`. Callout 14 remains solar charging.
Only target-local Italian copy changes; existing icon assets, numbers, English
and other languages are unchanged. This source correction and its candidate
are not publication.
