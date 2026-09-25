# JE-3600A EU/en Web intake and implementation record

Date: 2026-09-08

Implementation baseline: `d1b12bf8686941b5e79d9b507d7cc991da3427b9`

Target: `JE-3600A / EU / en` (`HTE139`, Jackery Explorer 3600 Plus)

Status: Git implementation complete and ready for engineering review. The
frozen-source build, strict Sphinx site, asset hashes, semantic LCD content and
localhost desktop/mobile checks pass. This record does not claim a live table
write, merge or formal publication.

## Authority and frozen inputs

| Source | Role | Revision / hash |
| --- | --- | --- |
| Current published PDF from DingTalk record `QRo3FviEOb` | Visible content and artwork authority | `Jackery Explorer 3600 Plus User Manual-EU-UK-2026-05-25.pdf`; 91 pages; SHA-256 `bfbcc4377fb474952f5e0850818289449016c8df11b1df48aff192b646eedf6d` |
| English structure source | Structure and editable-copy reference | `EN-3600Plus-DVT（原文HTE139美规）`; exported AI/PDF SHA-256 `d87b5474fca3008f2ad8578d8da7b6001f81bb8e1969c351a87043cfe05f6656`; text inventory SHA-256 `ca480fda5f11334e6dd20d618dd152ef9f76736019bf0a723dc48272fb50be9f` |
| Target-scoped phase2 snapshot | Reproducible Git build input | `manual_sources/JE-3600A/EU/en/2026-05-25/phase2/` |

The published PDF wins visible-content conflicts. The source manifest locks the
published document metadata, phase2 files, asset recipe and Web illustration
manifest; the target build has no live Bitable dependency.

## Source-to-structure mapping

| Published content | Web carrier |
| --- | --- |
| Safety, symbols, maintenance, charging, storage and warranty | Shared English semantic templates and phase2 tables |
| Package contents, overview, operations, UPS, charging and App panels | Complete approved PDF-derived panels with embedded panel-owned labels |
| LCD map | Device-only artwork plus the 21-row semantic LCD table |
| LCD display modes | Device-only illustration beside a native six-row CSS/HTML table; the table is never rasterized |
| Battery-pack connection | Target-local semantic section with the complete connection/accessory panels and live caution copy |
| Troubleshooting and specifications | Frozen phase2 tables, including `F0`-`FC` and target electrical ratings |

Only exact-bound copy owned by a finished panel is consumed. Section headings,
cautions, specifications, troubleshooting and LCD tables remain searchable,
editable Web content.

## Implemented scope

1. Added `JE-3600A / EU / en` to the shared EU English config and manifest; no
   per-model config was introduced.
2. Added target recipes/templates for Overview, Operations, battery-pack
   connections and App Setup, plus the target illustration manifest.
3. Added a deterministic 91-page archive/quarantine asset recipe and 26
   approved target exports. Eighteen Web assets are bound to the finished page.
4. Froze the audited phase2 data and eight symbol images under
   `manual_sources/JE-3600A/EU/en/2026-05-25/`.
5. Added target tests for source locks, published facts, 21 LCD rows, `F0`-`FC`,
   18-page output and 10/10 finished governed figures.

## Acceptance evidence

| Gate | Result |
| --- | --- |
| Approved-state asset replay | Pass: 91 source-page archives, 91 previews and 26 exports; all expected hashes matched |
| Target Web build | Pass: 18 public-IR pages, 16 finished illustrations, 10/10 governed figure slots, zero unresolved placeholders |
| Strict Sphinx Web build | Pass: `python -m sphinx -W --keep-going -b html` |
| Content checks | Pass: 3584 Wh, 3600 W/7200 W, 6000 cycles, 10 ms UPS, five battery packs, 200 mm clearance, 21 LCD rows and `F0`-`FC` |
| Target check | Pass with the frozen target phase2 source |
| Browser review | Pass on localhost at desktop and 375 px mobile width; LCD content remains readable and semantic |

| Existing-target regression | Pass: JE-1000F EU/en with the shared fixture source |
| CI shared-fixture target check | Pass after adding the target specification, note, footnote, LCD, troubleshooting and table-symbol rows; verified Battery Pack 3600 compatibility copy is narrowly allowlisted in the EU English config |
| Manifest-family fold | Pass: all 24 manifests rebuilt byte-identically from six anchors and 18 diff carriers |
| Python lint | Pass: Ruff reported no errors |
| Unit tests | Pass: 3,871 tests, 22 skipped |
| Maintainability guardrails | Pass: zero new violations |
| Documentation links | Pass: 170 Markdown files, 1,747 links, zero broken |

A localhost preview is engineering evidence only and is not a public release
URL.

## Dependencies and non-goals

- The branch depends on the open `feat/web-je2000f-eu-en` target-selection
  foundation and therefore targets that branch until its PR is merged.
- No live Base/table mutation, queue dispatch, OSS upload, credential access,
  clipboard access, review reseed or publication metadata write occurred.
- No merge, formal Web publication or generated publish-branch mutation is in
  scope.
- The legacy RST-to-HTML lane's staged-extension import issue remains inherited
  from the dependency. The accepted Web lane is generated MyST plus strict
  Sphinx and is passing.

## Main integration

The EU family manifest selects the JE-3600A expansion chapter through the shared generated-page model override, preserving the JE-1000H and JE-2000E carriers. Fixture integration retains complete CSV records, including quoted multiline descriptions. The final merge gate uses the updated main and full regression checks.

## 2026-09-24 App connect-result panel

The English route, and the fr/es routes wired later from this frozen source,
showed the shared JP-market `connect_result.png` for App setup step 2.5. The
print's language blocks place the same App bitmaps (device name overlaid as
"E3600 Plus" / "Explorer 3600 Plus"), so one panel cut from EN-block p22 (bbox
58 138.4 313.25 287.75 at 12x: the three screens with their 2.3/2.4/2.5
captions, excluding the "screenshots are for reference only" sentence) now
replaces it: as a 17th entry in the English manifest and through one-entry
fr/es manifests. Each route keeps its own reference sentence as live text. As
App UI, its recipe `manual_je3600a_eu_web_app.json` stays quarantined; the
source manifest binds it as `app_asset_recipe` and rebinds the English
manifest. The operator confirmed the crop on 2026-09-24.

## 2026-09-24 Localized control-panel button names

The fr/es routes showed the English button names in the App page (step 2.2,
the add-device labels and the Wi-Fi reset notes): the three `CONTROLS` label
rows in the frozen `Spec_Master.csv` held only `Value_source`. They now carry
the names each language block prints next to the control-panel drawing:

| Row | fr (p38) | es (p55) | de (p72) | it (p89) |
| --- | --- | --- | --- | --- |
| main_power_button | Bouton d'alimentation principal | Botón de encendido principal | POWER-Taste | Pulsante di accensione principale |
| dc_usb_power_button | Bouton d'alimentation USB | Botón de energía USB | USB-Stromtaste | Pulsante Alimentazione USB |
| ac_power_button | Bouton d'alimentation CA | Botón de energía CA | AC-Ausgangstaste | Pulsante AC |

A trial build against the live fr/es pages removes 12 of their 14 English
button names. The remaining two sit in whole English sentences that the
fr/es routes still carry from the English source (for example the
energy-saving and parallel-connection notes), which is a separate
translation gap. de/it are filled from the print for completeness but are not
published. The live Feishu placeholder table has no JE-3600A_EU rows, so
nothing was written there. The operator approved the change on 2026-09-24.

## 2026-09-24 App add-device figure with this model's control panel

The es/fr routes composed generic App screens with the JE-1000F/US control-panel drawing, and the English route bound a crop of the control-panel box alone (`control_panel`, no screens). The English print labels the AC button "AC Button"; the English page has no label lines to cover. Each language block prints the 2.1/2.2 screens and this model's own
control-panel box, with the block's button labels, as one region. The en/es/fr routes now
bind a 12x crop of that region from their own block (quarantined App recipe
entries `web/je3600a/eu/<lang>/app_add_device_panel`, PDF pages 21/55/38). Each
crop ends in the white gap before the next paragraph and has pure-white edges.
The page's button-label lines become covered annotations, kept as the figure's
alt text. The operator approved the crops on 2026-09-24.

## 2026-09-25 fr/es LCD, fault, specification and note cells from the print

The fr/es routes showed about 70 English segments. The LCD table, the fault
codes, the specification table, the storage durations and the standby duration
were all in English, and the spec note and two footnotes were missing. The
reason is that the fr/es columns of `lcd_icons_blocks.csv`,
`troubleshooting_blocks.csv`, `Spec_Master.csv`, `Spec_Notes.csv` and
`Spec_Footnotes.csv` were empty, and rendering fell back to English. 216 cells
now hold each language block's printed text:

| Table | Cells | PDF pages (fr / es) |
| --- | --- | --- |
| LCD | 21 rows × name + description | 26–27 / 43–44 |
| Fault codes | 12 | 35 / 52 |
| Specification rows | 21 | 36 / 53 |
| Storage lines | 3 | 35 / 52 |
| Standby duration | 1 | 28 / 45 |
| Spec note and footnotes | 3 | 36 / 53 |

The cells are split by each page's own ruling lines. On the first LCD page the
fr/es name/description divider sits at x = 155, not at 165 as in English.

Rules, confirmed by the operator:

- **Wording comes from the print.** Format follows the reviewed fr/es frozen
  sources: unit spacing, `V~ 50 Hz`, `max.`/`máx.`, decimal comma, `V CC`,
  `-20 °C`, spaced `×` and `%`. Ligatures and line-end hyphenation are resolved.
  Missing spaces after a full stop are restored. Neutral values (product name,
  model number, IEC code, cell chemistry) are kept as printed.
- **LCD rows keep the English row's structure without rewriting a printed
  sentence.**
  - Item 4 merges the two modes into one row with the mode names as prefixes
    and drops the Off sentence, as English does.
  - Item 19 is flattened, as English does.
  - Item 18 keeps both printed sentences, because English rewrote them into one.
  - Item 5 keeps the printed wording, because English rephrased it.
- **Print defects use reviewed cross-model wording:**
  - The Spanish temperature labels are printed in French
    (`Température de charge/décharge`), so they read
    `Temperatura de carga/descarga`.
  - The French total AC output carries the English `Rated`, so it reads
    `3600 W nominal, 7200 W crête`, following JE-1000H/fr.
  - The Spanish `Nº` glyph has no text mapping (U+001F), so the label reads
    `Nº de modelo` as rendered.
- **Kept as printed:**
  - `IEC code` is kept in both languages; no reviewed wording exists.
  - The Spanish LCD item 7 omits "when the AC output is turned on".
  - The fr/es F6 give 20 cm where English says 200 mm.

The de/it columns are left empty because no de/it routes exist.

Verification:

- **Independent print check:** every written sentence is found in the plain
  text of its PDF page after canonicalisation. This is a different extraction
  path from the one that built the cells; only the listed substitutions are
  exempt.
- **English controls:**
  - LCD: 14 of 21 English rows reproduce the English CSV exactly; the other 7
    differ only by the English editors' own edits.
  - Specification: 19 of 21 rows land on their print cells; the 2 expansion-port
    values differ only by an English edit.
- **Figures:** every specification and storage value keeps the English digits
  and `⎓` count.
- **Regression tests:** `Je3600aEuTranslatedCellTests` fails 162 subtests on the
  previous files.
- **Trial Web build:** 0 English segments identical to English remain on either
  page, against 70 and 67 before. Two sentences that quote the standby time and
  the temperature range (`2 hours`, `-20 °C to 45 °C`) are corrected along with
  the tables.
