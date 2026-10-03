# Intake assistance and shared-art review — 2026-10-03

Status: active

Discovery complete; implementation validation and operator asset selection pending.

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
