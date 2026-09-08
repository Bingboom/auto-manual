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
