# Intake assistance and shared-art review — 2026-10-03

Status: active

Packet/check tooling and selection import validated; solar visual grouping recorded.
Operator archive approval, full pipeline integration and actual Sol trial remain open.

## Evidence and cause

- Existing `asset_registry` and `asset_usage` already enforce scoped resolution,
  overrides and byte hashes. Feishu has separate LCD icons and Symbols tables;
  ordinary illustrations use the existing asset source/definition/export tables.
- Live read: 206 definitions, 444 exports and 4 source records (paginated).
  These counts do not imply that every local registered export is archived.
- Current main has 468 registry rows and 5,448 tracked raster/SVG files under
  docs and manual_sources. Many are copies of frozen exports, not new assets.
- JBP locale work currently needs temporary scripts to enumerate English copy,
  assemble source selections and detect omissions. A renderer or another
  family configuration is unnecessary; an explicit input checklist is missing.
- Existing baseline gate PR #1409 is a dependency for confirmed layout admission;
  intake assistance cannot promote an English candidate or bypass that gate.

## Bounded implementation

1. Generate a byte-deduplicated shared-art review from tracked files and live
   snapshots. Keep LCD/Symbols ownership, source references, model/region scopes,
   registry hashes and unmatched files visible. Similar images are candidates,
   never automatically merged. User confirms before Feishu writes.
2. Generate a source-pinned English/locale work packet from a reference IR and
   original PDF/AI pages. Expose content occurrences and component identities,
   keeping reference versus native source distinct. Check missing/extra/stale
   mappings and missing evidence mechanically. Produce source copy maps for
   the existing intake pipeline, not another renderer or publication path.
3. Validate with mutation tests and real JBP evidence. Test a Sol execution only
   when the exact requested model is available; do not claim model acceptance
   from deterministic tests alone.

Non-goals: schema changes, source approval, automatic translation, recropping,
new asset store, per-language CSS, historical package edits, automatic release.

## Safety and validation

Isolated `feat/manual-intake-assist` worktree; root `tmp/` and other windows
untouched. Reports are new directories. Source files remain read-only.
Targeted unittest → Ruff → full unittest → guardrails/doc links. No change to
build CLI flags or release gates in this phase. Validate report generation on
real current-main assets and final JBP English IR. Record exact boundaries.

## First review deliverable

- Main scanned: `96edce57`; 5,448 tracked images + 44 downloaded dedicated-table
  attachments, 1,736 distinct byte identities. Initial priority view has 293
  candidates, including 108 solar/connection and 70 car/charging versions.
  These are candidates including finished localized panels, not 293 approved
  universal images. Full inventory preserves excluded/uncertain items.
- LCD icons: 29 live rows; 27 attachment downloads. Symbols: 17 rows and 17
  downloads. All 44 downloaded originals match existing repository image bytes.
- Direct GET confirmed two JBP-2000B LCD rows have null `figure`:
  `recvsZG5nwlwlq` (Power Percentage/Fault Code) and `recvsZG5nwQVVQ`
  (Charging Indicator). Existing rows need review, not duplicate definitions.
- Gallery: `.tmp/intake-assist/art-review-v4/index.html`; server port 18974.
  Filters, original-image previews and Chinese dedicated labels browser checked.
- Intake packet trial: final published JBP English IR generates 195 copy items
  with exact occurrences; 169 existing French evidence mappings were matched
  in the first trial. Extra accessibility/aggregate/fixed strings remain explicit
  review work, not presumed translation defects. Internal layout enum slots
  are excluded. No original source, manual or other window file was changed.
- Nine final targeted tests (including twelve mutation subcases), full Ruff,
  maintainability guardrails and docs checks pass. Full suite: 5,106 tests OK / 35 skipped in 670.398 seconds,
  `.tmp/intake-assist/unittest-full.log`. After that run began, helper extraction,
  gallery labels and enum filtering were finalized; the final targeted suite
  and guardrails were rerun. No production build/admission behavior changed.
- No Feishu writes, no baseline approval, no completed Sol model trial.
  Asset confirmation and pipeline integration remain separate next steps.

## Selection import and solar normalization

- Imported all 69 operator choices unchanged (64 conditional, five exclusions),
  plus 92 hash-bound solar annotations through the real `art-review` CLI.
  Operation/button artwork cannot receive a reuse selection. No source image
  was altered, no registry scope enlarged and no Feishu record written.
- Compared all 108 solar-category byte versions: 92 files fold into 22 proposed
  canonical originals while keeping host/receptacle/topology differences;
  15 files remain in eight reference-only groups and one missing-subject PNG
  is excluded from recommendation. This is visual grouping, not byte equality
  or approval to substitute a canonical into any existing manual.
- Durable source paths, hashes, group decisions and exact operator selections:
  [normalization review](shared-art-normalization-20261003.json).
  Final local gallery: `.tmp/intake-assist/solar-review-v7/index.html`.
- All 11 SVGs were additionally inspected in the browser. The previous raster
  preview converter misrendered clipping/transforms; nine JE-100C SVGs and two
  JE-1000F JP SVGs are not corrupt originals. Intermediate v6 classification
  is superseded by v7. Never use a converted contact sheet alone to reject SVG.
- Full selection-policy suite: 5,110 tests OK / 35 skipped, 799.219 seconds,
  `.tmp/intake-assist/unittest-selection-policy.log`; after mechanical helper
  extraction, 12 targeted tests, Ruff, guardrails and doc links passed.
- Battery ×8 native extraction from HTE152 p13 is a separate transparent
  candidate; artwork confirmation and enrollment remain separate.
- Next bounded work: classify car/car-cable source variants and generate
  explicit textless/HTML/CSS work items; run an actual requested-model pilot
  when available. Tool tests are not GPT-6.1 Sol acceptance.

## Car grouping and main compatibility

- 70 car-connection versions grouped by actual host/receptacle/topology into
  17 groups: five have existing textless candidates; 12 still need native
  source preparation or an identity check. Empty caption pills are not accepted
  as textless artwork. Vehicle labels and sales notes remain native HTML;
  caption frames remain shared CSS. [Per-group work items](car-artwork-work-items-20261003.json)
  bind exact source IDs and next actions. This inventory does not claim to
  cover every unnamed standalone cable in package-content illustrations.
- After integrating main `02998d14`, its top-level module ratchet correctly
  rejected the three new helper files. Moved this PR's code mechanically into
  `tools/manual_intake_assist/` without increasing thresholds. The public
  `python -m tools.manual_intake_assist` command and `main` callable are unchanged.
- CLI output parity after the move: all 1,738 gallery/report/export files are
  byte-identical. 12 targeted tests, full Ruff, structural guardrails (398/398
  top-level modules) and doc links pass. Final full suite against
  this merged package layout: 5,118 tests OK / 35 skipped, 573.776 seconds,
  `.tmp/intake-assist/unittest-main-package-final.log`.
- Final gallery desktop is verified (22/22 hero images load, no horizontal
  overflow). This turn's attempted 390px override did not change the actual
  browser width; do not treat the saved `mobile.png` as mobile acceptance.
