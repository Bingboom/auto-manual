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
