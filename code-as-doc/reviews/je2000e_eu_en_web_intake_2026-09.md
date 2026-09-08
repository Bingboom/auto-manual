# JE-2000E EU/en Web intake and implementation record

Date: 2026-09-08

Implementation baseline: `d1b12bf8686941b5e79d9b507d7cc991da3427b9`

Target: `JE-2000E / EU / en` (`HTE152`, Jackery Explorer 2000 Plus)

Status: implementation in progress.

## Authority and source inventory

| Source | Role | Verified state |
| --- | --- | --- |
| DingTalk requirement row `LANG-S4mhIE7S` | Request scope and current-file linkage | Model `JE-2000E`, project `HTE152`, current material `160102000398`, status `已定稿` |
| Current published PDF, DingTalk node `YndMj49yWjP03jNjCRnbG07jJ3pmz5aA` | Visible copy and artwork authority | `Jackery HomePower 2000 Plus User Manual (JE-2000E) EUUK V2.0-2026-08-03`; 120 pages; SHA-256 `734f89ad824d2436d2c79c7ac1231d2dc111dd83ef43e8ee6326674124c396d0` |
| Business-plane phase2 Base | Existing structured semantic source | Live read-only sync completed; `JE-2000E_EU` capability row and 47 specification/placeholder rows are present |

The PDF metadata title identifies material `16-0102-000398` and model source
`HTE1522000A-EU-JAK`. Its English body is physical PDF pages 6-24 (printed
pages 01-19). PDF text extraction is used only for inventory; all 19 English
pages were rendered for visual review.

## Confirmed pre-edit findings

- The current EU/en family and shared semantic components already cover Safety,
  Symbols, Inbox, Overview, LCD, Operations, UPS, Charging, Troubleshooting,
  Specifications, Warranty and App Setup. A new per-model config is not needed.
- The live target data builds through the normal `build.py check` entrypoint but
  currently fails on three missing page values: `UPS_TRANSFER_TIME`,
  `PV_INPUT_RANGE`, and `DC_INPUT_CONNECTOR`. The capability gate also requires
  the shared extra-battery page because `加电包扩容=TRUE`.
- The published PDF supplies the missing values: UPS switching within `10 ms`,
  solar open-circuit range `16 V-60 V`, and two `DC8020` input ports. These will
  be recorded only in the Git-tracked target snapshot; no live Base write is in
  scope.
- The published Specifications table states `Jackery Explorer 2000 Plus`,
  `JE-2000E`, `2048 Wh`, `6000 cycles to 70%+ capacity`, 2400 W rated output,
  and 4800 W surge. JE-2000F values and artwork are not acceptable substitutes.
- The LCD remains a source-device diagram plus the shared editable HTML/CSS
  icon table. Overview, operation, UPS and charging illustrations may use
  target-local crops, but semantic tables and prose remain editable.
- PR #1082 contains the target-aware shared-family illustration selector and
  the final shared Inbox/operation/LCD/App component behavior required here.
  This task will consume that branch as an explicit stacked dependency, not
  create another implementation of the same shared capability. PR #1081 is
  unrelated and is not consumed.

## Implementation plan

1. Merge the reviewed PR #1082 branch into this task branch as an explicit
   dependency, preserving its commit ancestry and leaving both PRs unmerged.
2. Freeze only the existing JE-2000E EU/en structured rows and referenced shared
   attachments into `manual_sources/JE-2000E/EU/en/2.0/phase2/`; add the three
   published-source page values locally and lock every file hash.
3. Add JE-2000E to the shared EU/en target list and target-keyed illustration
   mapping; include the shared extra-battery page under the existing capability
   gate.
4. Extract only target-local panels from the verified PDF with recorded page,
   bounding box and hash. Keep complete gray illustration frames where the
   artwork owns labels; do not rasterize LCD/specification/troubleshooting/
   warranty tables.
5. Add target acceptance tests for source isolation, source-manifest locks,
   semantic components, figure coverage, cold replay and tamper rejection.
6. Validate in the cheap-to-expensive order: target tests, Ruff, full unit
   suite, maintainability guardrails, documentation links, target check, Web
   build, strict Sphinx, desktop/mobile localhost inspection, then current-main
   ancestry and PR checks.

## Non-goals

- No live Bitable write, queue mutation, OSS upload, Hello-Docs edit, RTD
  publication, JP/IDML work, PR merge or public-release claim.
- No copied JE-2000F/JBP-2000B artwork, product names or target parameters.
- No hand edits under `docs/_build/` and no cleanup of unrelated generated or
  review artifacts.
