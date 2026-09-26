# JE-3000C EU English Web intake — 2026-09

## Scope and authority

- Target: `JE-3000C / EU / en`, Web manual only.
- Current authority: `Jackery Explorer 3000 User Manual (JE-3000C)-EUUK-V2.0-2026-07-31.pdf`, DingTalk node `a9E05BDRVQ6mQG3GhyyglLX9J63zgkYA`.
- Source lock: 102 pages; SHA-256 `55fee5a2f7538e58ebce17fc2bcfe3b0e4a8959233251961f6122ef7f420602d`; English body on physical pages 6–21 and EU declaration on physical page 102.
- Requirement record: Base `YndMj49yWjP03jNjCDojvAQdJ3pmz5aA`, table `97v7518`, record `FBHsOuFTMQ`; read only. It identifies HTE156 / E3000V2 / material `160102000382`, status `已定稿`, and the same formal source node.
- No calibration or version comparison was performed. The current PDF governs visible copy, parameters, ordering, and illustrations.

## Structure and reuse boundaries

The target snapshot uses the public phase2 schema and the existing EU English shared carriers. The existing `JE-3000C_PH` rows were used only as a structural starting point for the same hardware model; every voltage, frequency, current, power, temperature, port count, and product label used by the EU target was audited against the current EUUK PDF. Non-target parameters are not inherited.

Shared components remain responsible for safety, warning/callout treatment, inbox layout, LCD icon table, UPS, charging, storage, troubleshooting, specification, warranty, App setup, and EU regulatory copy. Target-local templates are limited to Overview and Operations because JE-3000C has no LED light or emergency charging section and its source order differs from the family default.

## Source-to-Web mapping

| Source pages | Web carrier | Treatment |
| --- | --- | --- |
| 6–7 | Safety, Symbols, Inbox | shared semantic components; current-source product/cable/manual object crops |
| 8 | Product Overview | two complete annotated source panels; duplicate live tables are exact-bound and consumed |
| 9–10 | LCD Display | current device display map plus 26 semantic description rows numbered 1–25; number 21 covers both temperature rows |
| 11–13 | Operations | complete grey-frame source panels; duplicate image-owned copy is exact-bound and consumed |
| 13 | LCD mode and output resume | device-only LCD crop beside an HTML/CSS semantic table; output-resume comparison remains a semantic table |
| 14 | UPS | shared carrier with current 10 ms / 12 A facts and current-source full panel |
| 15–16 | Charging | current-source full grey panels for AC, solar, and car charging; no emergency charging section |
| 17–19 | Storage, troubleshooting, specifications, warranty | shared semantic components with current-source values and `F0`–`FE` rows |
| 20–21 | App setup | current-source download, add-device/control, and connection-result panels inside the shared carrier |
| 102 | EU compliance | shared EU regulatory carrier |

## Asset provenance

`data/asset_recipes/manual_je3000c_eu_web.json` defines 18 deterministic 12x crops from the locked source. The approved replay produced 222 artifacts: 102 page PDFs, 102 previews, and 18 target exports. Every export has an expected SHA-256. Operation and charging panels retain their complete grey frames and image-owned text. No whole-page screenshot is used. The LCD mode crop deliberately excludes the source table.

The source and export records are registered locally in `data/asset_sources.csv` and `data/asset_registry.csv`. No live Base write, source upload, OSS archive, or centralized publication was performed.

## Dependency and delivery boundary

This branch is stacked on `feat/web-je2000f-eu-en` / PR #1082 because it consumes that target-aware Web illustration resolver and semantic LCD/auto-resume presentation work. PR #1085 (JE-2000E) and PR #1086 (JE-1000H, itself based on #1082) are sibling Web-target efforts and may overlap shared fixtures or the EU family manifest; they are not content sources for this target. The PR must remain unmerged until dependency review and normal CI complete.

Local build, localhost preview, and green checks are engineering evidence only. They do not mean the PR is merged or that a formal public Web route has been published.

## Main integration

### 2026-09-13 PV qualifier reconciliation candidate

Released PDF physical page 18 / printed 13 places `Max` after the 12 A input
rating and after 1000 W, not after the combined 24 A phrase. Restore that
qualifier placement in the frozen English Value_source without changing any
numeric limit or other language column. Native HTML regression verifies the
complete PV wording. Seven target tests pass.

Refresh the file lock and canonical compact/sorted JSON inventory hash. The
previous aggregate mismatch existed at initial intake (`e045ad35`); it is not
recent content drift. Add explicit aggregate-digest verification. No online
data, artwork, workflow or publication changes; full-book acceptance is open.

The target now integrates the merged EU Web baseline. Shared fixture CSVs retain complete logical records when combining target additions, including quoted multiline symbol descriptions; this preserves the existing JP and US consumers. The final integration is validated against the current main and the full test suite before merge.

## 2026-09-24 App connect-result panel for fr/es/de/it/uk

The fr/es/de/it/uk routes, wired later from this frozen source, had no
illustration manifest, so their App setup step 2.5 showed the shared
JP-market `connect_result.png`. The print's other five language blocks
(p37/p53/p69/p85/p101) place the same five bitmaps as the English block, so
one panel cut from p21 (bbox 51.75 142.25 323.75 302.75 at 12x, the scale of
the English App panels) now replaces it in five one-entry manifests; the
localized "screenshots are for reference only" sentence stays live text. As
App UI, its recipe `manual_je3000c_eu_web_app.json` stays quarantined, and the
source manifest binds it as `app_asset_recipe`. English is unchanged. The
operator confirmed the crop on 2026-09-24.

## 2026-09-24 Localized control-panel button names

The fr/es/de/it/uk routes showed the English button names in the Product
Overview callouts, the energy-saving and UPS text, and the App add-device
labels: the three `CONTROLS` label rows in the frozen `Spec_Master.csv` held
only `Value_source`. They now carry the names each language block prints next
to the control-panel drawing:

| Row | fr (p36) | es (p52) | de (p68) | it (p84) | uk (p100) |
| --- | --- | --- | --- | --- | --- |
| main_power_button | Bouton d'alimentation principal | Botón de encendido principal | POWER-Taste | Pulsante di accensione principale | Кнопка POWER |
| dc_usb_power_button | Bouton d'alimentation CC/USB | Botón de energía CC/USB | DC/USB-Stromtaste | Pulsante Alimentazione DC/USB | Кнопка живлення DC/USB |
| ac_power_button | Bouton d'alimentation CA | Botón de energía CA | AC-Ausgangstaste | Pulsante AC | Кнопка живлення AC |

French uses the straight apostrophe that dominates the French pages (the print
mixes both forms). A trial build against the live pages removes every English
button name (fr 19, es 17, de 16, it 16, uk 6 occurrences); English is unchanged.
The live Feishu placeholder table has no JE-3000C_EU rows (this source has no
live dependency), so nothing was written there. The operator approved the
change on 2026-09-24.

## 2026-09-24 App add-device figure with this model's control panel

The fr/es/de/it/uk routes composed generic App screens with the JE-1000F/US control-panel drawing; the English route already bound its own complete `setup_add_device` panel and is unchanged. Each language block prints the 2.1/2.2 screens and this model's own
control-panel box, with the block's button labels, as one region. The five routes now
bind a 12x crop of that region from their own block (quarantined App recipe
entries `web/je3000c/eu/<lang>/app_add_device_panel`, PDF pages 36/52/68/84/100). Each
crop ends in the white gap before the next paragraph and has pure-white edges.
The page's button-label lines become covered annotations, kept as the figure's
alt text. The operator approved the crops on 2026-09-24.

## 2026-09-25 App panels quarantined under the recipe gate

The three English App panels (`setup_download`, `setup_add_device`, `setup_connect_result`) were recipe-approved only because neither their keys nor their risk tags
carried a gate token (`app`, `qr`, `screenshot`, …). They are now quarantined
with `app-ui`/`screenshot`/`localized-ui` risk tags (plus `qr` for the download
panel); keys, outputs and hashes are unchanged, so the pages are unchanged.
`source_manifest.json` rebinds `asset_recipe`. The operator approved the fix on
2026-09-25.

## 2026-09-25 fr–uk English fallbacks filled from the print

The fr–uk routes showed English in several places:

- the specification table;
- the storage durations;
- the front and right-side overview callouts, which are rendered as HTML tables;
- the standby and auto-off times quoted in the text (`2 hours`, `12 hours`);
- Latin units in Ukrainian sentences;
- footnote ② was missing.

The cause was that the fr/es/de/it/uk columns of those `Spec_Master.csv` rows and
of `Spec_Footnotes.csv` `ac_total` were empty.

**What changed.** 324 JE-3000C cells hold each language block's printed text from
this source's V2.0-2026-07-31 PDF. Specification and overview cells are split by
the pages' ruling lines or grouped by callout font (7 pt bold label, 5 pt value
lines).

| Rows | Cells per language |
| --- | --- |
| Specification | 19 |
| Storage | 3 |
| Overview slots | 15 |
| Standby/auto-off | 2 |
| Ukrainian units | 4 (Ukrainian only) |
| Footnote ② | 1 |

**Rules, operator-confirmed.** These are the same rules as for JE-1000H and JE-3600A:

- Wording comes from the print, in the house format of the reviewed frozen
  sources.
- Print defects use reviewed cross-model wording.
- Cells whose printed wording matches the English value (for example `25 W`,
  `10 ms` outside Ukrainian) keep their fallback.

**Deviations from the print:**

- **German:**
  - the 12 V port label is printed as `DC-12V-Ausgangstaste` (an output button),
    so it reads `1 × DC 12 V-Anschluss` in the spec and `12-V-DC-Anschluss` in
    the overview;
  - the car line of the spec table is printed in English (`Car:`), so it reads
    `Auto:` as this block's own overview prints.
- **Italian:** the bypass parameter is printed with the English `AC modalità
  bypass`, so it reads `Modalità bypass`.
- **Spanish:**
  - the USB-A row is labelled `USB-C 18W`;
  - the PV value reads 400 W, which the 2026-09-15 revision of the same print
    corrects to 1000 W, as in English.
- **French:** `Oiture:` becomes `Voiture :`.
- **Ukrainian:**
  - the bypass label (`режим` → `режимі`), the plural `2 виходи USB-A` and a
    stray `від` glued to the charging-temperature label are fixed;
  - the energy-saving threshold is printed `25 В` (volts) and reads `25 Вт`;
  - footnote ② gains the missing `струму` by operator ruling, also applied to
    JE-1000H.
- **Kept as printed:** the Ukrainian dimensions in mm (`435 × 326 × 281 мм`) and
  the spec rows without car/PV prefixes; the German and Ukrainian overview AC
  output without "rated".

**The newer revision.** The 2026-09-15 revision on the design share differs only
in that Spanish PV value and in an added vehicle-charging caution block on the
storage/fault pages. The storage lines and the other specification text are
identical. The authority stays V2.0-2026-07-31, because every recipe is
hash-locked to it.

**Verification:**

- **Independent print check:** every written cell is found in the plain text of
  its PDF page after canonicalisation, a different extraction path from the one
  that built it. Only the listed substitutions are exempt (22 cells).
- **Figures:** values keep the English digits and `⎓` count, except the
  Ukrainian dimensions in mm and the cell-chemistry subscript.
- **English controls:**
  - specification: 16 of 19 rows land on their print cells;
  - overview: 11 of 13 slots land on their callouts;
  - the misses are English edits (`Vehicle:` for the printed `Car:`, `MAX`
    dropped).
- **Regression tests:** `Je3000cEuTranslatedCellTests` fails 214 subtests on the
  previous file.
- **Trial Web build:** 0 English segments identical to English remain on any
  fr–uk route. The changes are confined to the overview, specification, storage
  and footnote sections plus the sentences that quote the standby time, the
  thresholds, the UPS time and the temperature range.

## 2026-09-25 fr–uk figures from each print block

Problem:

- The fr/es/de/it/uk illustration manifests bound only the two App panels. The
  other 16 figure slots fell back to the shared art extracted from the JE-1000F/US
  master, which shows another product and US outlets.
- This print is region-variant: the English block draws UK sockets on the unit;
  the fr–uk blocks draw EU sockets. Each route therefore takes its own block's
  figures. The English route keeps the English block's figures.

Change:

- `data/asset_recipes/manual_je3000c_eu_web.json` gains 75 approved crops, 15 per
  language, from the fr (PDF pages 22–37), es (38–53), de (54–69), it (70–85)
  and uk (86–101) blocks:
  - The positions come from raster matching with the text removed, then each
    block's own panel frame or art extent. The blocks' layouts drift from English
    by up to 30 pt.
  - Crop edges exclude the neighbouring section headings and table rows.
  - The DC panel keeps the English whiteouts, and `web_manual.css` gives the
    five fr–uk DC figures the English figure's border.
- The five illustration manifests bind the crops to the English slots. Their
  `recipe` is now the web recipe; the App entries keep their own.
- Copy printed in a crop moves from the page into the figure's alt text, as on
  English: the overview callout tables, the operation panel lines, the
  energy-saving note and the car-panel lines. These entries set
  `consume_before_presentation`, because registered components claim those
  nodes.
- **Print defects (operator ruling):**
  - The German front view prints `DC-12V-Ausgangstaste` and a French `Bouton
    d'alimentation CA`, and the French side view prints `Oiture:`. These two
    figures stay as printed and keep the page's corrected callout table.
  - The Italian and Ukrainian blocks print the energy-saving caption in English
    (`Press and hold both buttons for more than 3s`). That line is redacted, and
    the page keeps the localized sentence (the JE-3600A fr car precedent).
- `source_manifest.json` re-locks the web recipe.

Verification:

- **Recipe:** `tools/asset_intake.py` reproduces all 93 outputs against their
  expected hashes; the 18 English crops are byte-identical.
- **Visual review:** every crop was checked next to the English crop and its
  page. No English line remains in a block crop apart from the redacted captions
  and the product name `SolarSaga 200 ×4`.
- **Trial Web builds:** each fr–uk route replaces 15 figures, drops the second
  solar figure (as English does) and moves the covered copy into alt text; no
  shared JE-1000F figure remains.
- **Regression tests:** `Je3000cEuBlockIllustrationTests` and the French build
  test fail on the previous recipe and manifests (three failures, one error).

Still open (not changed here):

- The English route shows the English block's UK sockets. (Operator ruling
  2026-09-26: kept as printed, as JE-1000F/EU does.)
- The App download panel stays the shared QR image on fr–uk. The image matches
  the print and is language-neutral.

## 2026-09-26 Emergency Charging Mode gate

The fr/es/de/it/uk routes printed an Emergency Charging Mode block under AC wall
charging, although JE-3000C_EU has the capability FALSE in
`data/model_capabilities.csv` and no language block of the V2.0-2026-07-31
print has it. (The uk block's `аварійного використання` is the car panel's
"emergency use only" caution, a different sentence.)

- Only the English shared charging template carried the
  `hb-capability-begin: 应急快充模式` markers.
- `docs/templates/page_shared/{fr,es,de,it,uk}/charging.rst` now carry them too.
  TRUE targets keep byte-identical pages, and FALSE targets drop the block.

Trial Web builds: each fr–uk route loses exactly that block; English is
unchanged. `Je3000cEuFrenchAppPanelTests.test_no_emergency_charging_block` fails
on the previous templates.
