# ManualIR v2 Operation, Warranty, and LCD Mode plan

Date: 2026-09-05
Branch: `feat/manual-ir-operation-warranty-lcd`
Baseline: `cbdfa7e4` (cut 2)

## Discovery

### Current authority and replay boundary

Cut 2 writes registered semantic instances directly into ordered
`manual-flow/v2` nodes.  `tools/manual_ir/whole_document_components.py` still
has a deliberately small discovery registry: Overview, FCC, Inbox,
specification tables, and callout strips.  The Web consumer dispatches those
five families from `tools/web_embedded_components.py`; replay does not reopen
RST or source CSVs.

The style contract already defines these three warranty semantics and LCD
Mode, but none is in `component_registry.yaml`:

- `HB-WARRANTY-LEAD`
- `HB-WARRANTY-SECTION`
- `HB-WARRANTY-YEARS`
- `HB-TABLE-LCD-MODE`

Operation panels have mature Web and IDML renderers but no renderer-neutral
style ID.  They therefore need one new semantic ID, `HB-SPECIAL-OPERATION`,
instead of being mislabeled as a heading, generic image, or table.

### Real carrier inventory

The shared JE-1000F US/EU operation sources have the same structural carrier
in English, French, Spanish, German, and Italian:

- five governed operation illustrations (`main_power`, `ac_output`,
  `dc_usb_output`, `energy_saving`, and `led_light`);
- a line block adjacent to every illustration;
- an adjacent prerequisite paragraph for AC, DC/USB, and LED;
- one six-row LCD Mode table containing one illustration cell, two three-row
  state groups, and six action/description pairs;
- Auto Resume and Key Combination are distinct table semantics and must not be
  swallowed by the Operation or LCD Mode components.

All five shared warranty languages render the same carrier shape: two leading
top-level paragraphs followed by six sections, exactly one of which owns the
two-column `3` / `2` year table.  German and Italian source copy carries
localized units (`JAHRE`, `ANNI`) and must reach the same numeric badge adapter
as English, French, and Spanish.

### Existing renderer compatibility shapes

- Web: `web_presentation.py` turns each operation image plus adjacent copy into
  `hb-operation-figure`, LCD Mode into `hb-lcd-mode-composition`, and warranty
  content into the lead, section-card, and year-card compositions.
- LaTeX: LCD Mode already uses `HBLcdModeTable` plus two group macros; warranty
  already uses the `HBWarranty*` environments.  Operation keeps its existing
  source carrier in this cut and gains a typed adapter projection.
- IDML: `idml/oppanel.py` emits legacy `oppanel`, `lcdmode`, `warrantylead`,
  `warrantysection`, and `warrantyyears` dictionaries consumed by the existing
  native component registry.  These dictionaries are the compatibility target
  for the new adapters.
- Word: the prepared HTML/table path is still authoritative.  Its adapters
  therefore project semantic HTML classes and editable table/card content;
  no screenshot carrier is introduced.

### Traps

- Component claims cannot overlap and a component carrier cannot contain
  another component.  Warranty claims must leave section headings in neutral
  flow, and Operation claims must not consume later callout tables.
- Approved Web composite hashes are based on the exact transformed semantic
  fallback.  Operation Web replay must reuse the established transformation
  during this compatibility cut so existing frozen composite manifests remain
  valid.
- LCD Mode is intentionally hybrid.  Replacing the whole table with a bitmap
  would remove searchable/editable localized text and violate the source
  contract.
- Geometry and locale selection stay outside renderer-neutral slots.  Web
  operation rectangles remain in the Web presentation contract; IDML geometry
  remains in renderer tokens and approved target assembly.

## Implementation plan

### Phase 1 - Characterization safety net

Add targeted tests that pin:

- registry, theme, and style-contract parity for the five new IDs;
- semantic slot shapes and four renderer projections;
- EN/FR/ES/DE/IT warranty years and localized units;
- five ordered Operation instances and one LCD Mode instance per governed
  operation page;
- cold Web replay without the legacy Warranty/LCD/Operation source projectors;
- unchanged approved Web composite source hashes for the existing JE-1000F US
  fixture.

### Phase 2 - Neutral specs and adapters

Add focused ComponentSpec modules for Operation, Warranty Lead, Warranty
Section, Warranty Years, and LCD Mode.  Register all four renderers explicitly,
add theme ownership, and add `HB-SPECIAL-OPERATION` to the style contract and
style-definition inventory.  Keep all visible copy and asset identity in the
spec; keep renderer geometry out.

### Phase 3 - Whole-document embedding and Web dispatch

Extend the ordered claim pass before the generic specification/callout passes.
Bind operation and LCD artwork through the same content-addressed package path
as every other component asset.  Dispatch the embedded instances directly in
Web replay and skip the corresponding whole-page DOM projector when the IDs
are resolved.

### Phase 4 - Native compatibility routing

Expose adapter projections matching the existing LaTeX, IDML, and Word
carriers.  Where an existing compatibility boundary already receives the same
payload, route it through the new projection without changing page geometry.
Do not migrate the IDML page composer or LaTeX doctree lifecycle in this cut;
that retirement belongs to cut 7 after all remaining components are embedded.

### Phase 5 - Verification and closeout

Run, in order:

1. Ruff on touched Python.
2. Targeted ComponentSpec, ManualIR, Web, IDML, LaTeX, and Word tests.
3. Full `python3 -m unittest`.
4. Full repository Ruff and maintainability guardrails.
5. Documentation link integrity.
6. Fixture-backed JE-1000F/US `build.py check`, approved-reference style-pin
   verification, and frozen cold replay.
7. Browser-visible EN/FR/ES plus EU DE/IT assertions for Warranty numeric
   badges, Operation `On/Off` copy/composite behavior, and editable LCD tables.

## Non-goals

- No dependency, workflow, CLI, live-data, source-table schema, approved
  reference-layout content/assembly/composition change, or content reapproval.
  Adding `HB-SPECIAL-OPERATION` changes the shared style-contract identity, so
  the JE-1000F/US plan receives the required mechanical style-only rebind after
  the rebind tool proves zero page-binding and composition drift.
- No model-specific Python or CSS.
- No bitmap replacement of LCD Mode.
- No registration of LCD Icons, Troubleshooting, Symbols, App, or Reference
  Figures; those are cuts 4 and 5.
- No presentation inheritance migration; that is cut 6.

## Execution outcome

- The five new ComponentSpec types are registered with Web, LaTeX, IDML and
  Word adapters and owned by the shared theme contract. No model-specific
  Python or CSS was added.
- Whole-document discovery claims five Operation panels, one hybrid LCD Mode,
  one Warranty Lead, five Warranty Sections and one Warranty Years instance per
  governed language page. Source image matching accepts both logical asset keys
  and their finalized filenames.
- Cold replay dispatches Warranty and LCD Mode directly from embedded specs.
  Operation reuses the existing hash-governed Web composition transform through
  a temporary compatibility carrier; the source parser is not reopened.
- JE-1000F US review input preserves all five approved composite
  `source_fragment_sha256` values. The EU review branch
  `origin/review/JE-1000F-EU@7d764e22` was mounted in a detached worktree and its
  DE/IT pages produced `3/2 JAHRE` and `3/2 ANNI` through the same badge adapter.
- The approved JE-1000F/US reference-layout plan was rebound from style hash
  `6db62e77…` to `761eb877…`. The official tool reported
  `page_bindings=0`, `content_reapproved=no` and
  `composition_map=unchanged`; the JSON diff changes only
  `identity.style.style_contract_sha256`.
- Validation passed 127 focused tests and 3767 full-suite tests (19 skipped),
  full Ruff, 62 maintainability hotspots, 1708 documentation links, the
  reference-pin check, and a staged JE-1000F/US target check. Its real Web
  output contains five Operation components, one editable six-action LCD Mode
  component, and the shared `3/2 YEARS` warranty badges.
- Remaining work is intentionally limited to cuts 4–7: LCD
  Icons/Troubleshooting/Symbols, App/reference figures, presentation overlays,
  and final legacy-path/anti-copy acceptance.
