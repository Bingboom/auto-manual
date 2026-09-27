# JE-2000E EU/en formal Git source

This directory is the audited, target-scoped build input for the Git-only Web
release of `JE-2000E / EU`, version `2.0`: the English route and the
fr/es/de/it/uk routes built from the same frozen rows.

- Authority: `Jackery HomePower 2000 Plus User Manual (JE-2000E) EUUK
  V2.0-2026-08-03.pdf`, SHA-256
  `734f89ad824d2436d2c79c7ac1231d2dc111dd83ef43e8ee6326674124c396d0`. Its
  en/fr/es/de/it/uk blocks print the specification table on PDF pages
  21/40/59/78/97/116.
- Structured source: [`phase2/`](phase2) holds the target rows and shared
  dictionaries. It has no live Bitable dependency.
- Locks: [`source_manifest.json`](source_manifest.json) pins every phase2 file,
  both asset recipes and the English illustration manifest. Its `notes` list
  the dated changes; its `audit_record`,
  `code-as-doc/reviews/je2000e_eu_en_web_intake_2026-09.md`, has the details.
- Publication boundary: this source and its local builds are not a Web
  publication, merge or live asset-register update.

Build a route with:

```text
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off \
AUTO_MANUAL_PRESENTATION_PROFILE=web \
python build.py md \
  --config configs/config.eu-<lang>.yaml \
  --model JE-2000E --region EU --lang <lang> \
  --data-root manual_sources/JE-2000E/EU/en/2.0/phase2 \
  --staging-root <fresh-root>
```

Specification tables (2026-09-27): the values, rows and labels of all six
specification tables follow their block's printed page. The cells keep this
source's house format: a space between a number and its unit, and `: ` after a
line prefix.

- Weight: fr/es/de/it/uk `18,8 kg` becomes `19,1 kg`, as every block prints
  it. English was corrected at intake.
- DC8020 lines: each block's printed order and prefix. fr prints PV first, like
  English, so its two value cells swap and its PV line gains the printed
  `max.` after 12 A. es/de/it/uk print the car line first, which their value
  cells already held. The `Param_<lang>` cells now carry each block's own
  prefix (fr `PV`/`Voiture`, es `Coche`/`PV`, de `Auto`/`PV`, it `Auto`/`FV`,
  uk `Автомобіль`/`PV`) in place of the English fallback. Line 1 and line 2 are
  therefore each block's first and second printed line; they are not the same
  port in every language.
- AC outputs: es/de/it/uk `2 ×` becomes `3 ×`.
- Expansion ports: the fr/es/de/it/uk input and output cells were empty, so
  the page showed the English `36.8 V-57.6 V⎓75 A max.` / `…55 A max.`. They now
  hold each block's printed cell with a decimal comma and the page's own units:
  fr/de/it `36,8 V-57,6 V⎓75 A max.`, es `… máx.`, uk
  `36,8 В-57,6 В⎓75 A макс.` (the output rows say 55 A). The Italian input cell
  gains the house space the print leaves out (`36,8V-57,6V`).
- USB-C: fr–uk print one row per port. The two rows had the same translated
  label, so the renderer merged them; each port now has its own label.
- Labels: en `Charge Temperature` / `Discharge Temperature`; fr `N° modèle`,
  `Mode charge`, `Mode dérivation`; es `1 × Puerto DC 12 V`; it `Modello n.`,
  `3 × Uscita CA`, `1 × Presa da 12 V CC`, `Temperatura di carica` /
  `di scarica`; uk `Байпасний режим`, `1 вихід USB-A 18 Вт`,
  `Порт постійного струму 12 В`, `Температура розряджання`.
- Headings (`phase2/spec_titles.csv` and `phase2/Localized_Copy.csv`): it
  `SPECIFICHE TECNICHE`, `INFORMAZIONI GENERALI`, `PORTE IN INGRESSO`,
  `PORTE IN USCITA`; uk `ТЕХНІЧНІ ХАРАКТЕРИСТИКИ`.
- Footnote (`phase2/Spec_Footnotes.csv`): de ① says `AC-Ausgangsanschlüsse`,
  as printed.

Where the print is wrong, the page keeps the reviewed wording:

- The German table prints `Ladtemperatur` (PDF page 78); the cell now reads
  `Ladetemperatur`, as the block's own prose prints it (page 75).
- The German port headings print as the mixed pair `EINGANGSPORTS` /
  `AUSGANGSPORTE` (page 78). They now read `EINGANGSANSCHLÜSSE` /
  `AUSGANGSANSCHLÜSSE` in `phase2/spec_titles.csv` and its
  `phase2/Localized_Copy.csv` twins, as the JE-1000H and JE-3600A EU prints set
  them (PDF page 70 of each) and as the table's own `DC8020-Anschlüsse` and
  `DC 12 V-Anschluss` read.
- Seven print defects that the page already corrected stay corrected.

`source_manifest.json` re-locks the four files.
