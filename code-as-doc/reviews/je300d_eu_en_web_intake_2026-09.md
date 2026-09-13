# JE-300D EU/en Web intake — 2026-09

## Target and source boundary

- Target: `JE-300D / EU / en`; product name: `Jackery Explorer 300D`; internal material family: `HTE150`.
- DingTalk source: Base `YndMj49yWjP03jNjCDojvAQdJ3pmz5aA`, table `97v7518`, record `QviOQihBNj`.
- Frozen attachment: `HTE150300A-EU UK-JAK 说明书 20251024.ai`; Git filename: `JE-300D-eu-source.ai`; SHA-256: `53209e53bb5ca5bcfa08c8eeeedd9c7ee6cc2c0cd226e6c7c776bb68421f78bc`.
- Source geometry: one PDF-compatible Illustrator page, `6915.82 × 4873.62 pt`, containing four cover panels and a 14-page English body.

The demand record has no published-PDF link. This branch therefore records the
AI as the operator-designated engineering candidate and does not claim a
published revision. The operator explicitly waived version comparison. The
target identity comes from the record, cover and source specification table;
the `300A` substring in the attachment filename is not treated as a different
model.

## Batch scope reconciliation

Read-only source: committed `scope-snapshot.json`, checked 2026-09-09. It
contains no download signatures.

| Classification | Count |
| --- | ---: |
| Source rows | 38 |
| Independent manuals with AI source | 21 |
| Engineering-complete at snapshot time | 16 |
| Remaining independent manuals at snapshot time | 5 |
| No manual / nonexistent | 14 |
| Duplicate | 1 |
| Composite rows | 2 |

The two composite rows are explicitly excluded from executable batch work and
must not be listed as pending. This branch performs only the independent
JE-300D target; the independent JA-CA05B 5 m extension-cable target is handled
in its own worktree.

## Semantic mapping

The target is selected from shared `configs/config.eu-en.yaml`; no per-model
config or new parser is introduced. A target-resolved page manifest maps the
source's preface, safety, maintenance, symbols, two-item Inbox, product
overview, LCD, operations, USB-C/solar/car charging, storage, F0–F9
troubleshooting, complete multi-port specifications, shared EU warranty and
non-radio EU declaration into live RST/ManualIR/Web components.

The source does not contain AC output, UPS, App setup, extra-battery expansion
or Wi-Fi/Bluetooth chapters, so none are added. The warranty uses the current
shared EU 3-year standard plus 2-year extension wording because it matches the
source's applicable warranty facts.

## Illustration and LCD contract

`data/asset_recipes/manual_je300d_eu_web.json` records the single-board source
hash, exact PDF-point crop boxes, PyMuPDF/MuPDF normalization contract, 8×
outputs and locked hashes for 14 illustrations. All crops were also rendered
at 12× for visual review.

The complete source-owned overview, strap, operation and charging panels retain
their gray frames, product outlines, embedded labels and instructions. Native
Web headings and caution blocks are not baked into page screenshots. The LCD
uses the numbered device display art plus a semantic 11-row HTML table (the
source shares number 8 between its high- and low-temperature states). LCD
screen timing uses device/button art plus a separate semantic HTML table.

No live source, capability, asset-source or asset-registry table was written.
The Git snapshot and CSV registry rows are engineering-plane evidence only.

## Validation and publication boundary

Validation results are recorded in the PR after the target build, strict
Sphinx build, local media checks, narrow-screen inspection, tests, static
checks and cold-replay/tamper gates complete. A local preview, package, commit
or open PR establishes engineering readiness only; none establishes merge,
Hello-Docs publication, OSS upload, Read the Docs availability or a live-table
write.
