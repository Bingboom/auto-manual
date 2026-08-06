# IDML approved-layout contract v2 discovery

Date: 2026-08-05

## Decision

Keep the approved reference-layout contract, but split its identity into
independently meaningful scopes. The current v1 contract correctly fails
closed, yet it treats a repository-wide phase2 snapshot digest as if it were a
target-specific rendering input. That makes unrelated source-table refreshes
block an otherwise identical approved manual.

The refactor must also close the opposite failure mode: an approved production
manual may currently emit a warning and continue when a source page is routed
through `UNCLASSIFIED_PROSE`. The FR/ES Product Overview incident proved that a
complete 52-source IR with `skipped_raw=0` can still use the wrong compositor.

## Current load-bearing path

1. `tools/manual_ir/builder.py` produces target content, page digests, global
   `snapshot_sha256`, style-contract identity, and layout-token identity.
2. `tools/idml/reference_layout_plan.py` activates a registered approved plan
   and currently requires five flat `source_identity` fields to match.
3. `tools/idml/ir_projection.py` exposes that normalized plan to
   `tools/export_idml.py`.
4. `tools/idml/page_roles.py` selects special-page compositors. Unknown roles
   currently degrade to prose with a warning.
5. `tools/idml/reference_layout_rebind.py` refreshes pins without changing the
   physical composition map; content changes require explicit approval.
6. `tools/idml/pdf_parity_contract.py` and
   `tools/check_reference_layout_pins.py` independently inspect the same flat
   identity structure.

## Observed contract defects

### D1: provenance is enforced as target identity

`_snapshot_sha256()` hashes every table declared by the phase2 snapshot
manifest. The approved JE-1000F US contract pins `2d77eff6...`, while another
valid local snapshot computes `3549175d...`. Production stops before assembly
even when the resolved target content and page bindings are the objects that
the approved contract actually governs.

### D2: assembly semantics have no independent identity

The plan pins source content and physical composition fields, but it does not
name the semantic page role used by the IDML router. A filename-classification
regression can therefore preserve page count and content while selecting a
different compositor.

### D3: approved fallback is warn-and-continue

`assembly_coverage_warning()` reports `UNCLASSIFIED_PROSE`, but approved
production export does not reject it. This is inappropriate for a plan whose
purpose is to guarantee an approved physical assembly.

## v2 identity boundary

The approved plan will use these scopes:

- `content`: Manual IR schema and target-resolved semantic content hash.
- `assembly`: one digest of ordered source refs, languages, semantic page
  roles, composition IDs, physical starts/counts, and flow splits.
- `style`: shared style-contract and layout-token hashes.
- `provenance`: the global phase2 snapshot hash, recorded for traceability but
  deliberately not used as an activation equality gate.

Per-page `source_sha256` values remain mandatory. Reference PDF identity,
render thresholds, approval metadata, and the physical composition map remain
unchanged.

## Compatibility and migration

- v2 is the emitted and migrated schema.
- v1 plans remain readable during migration and retain their current strict
  snapshot behavior; no existing approved target is silently weakened.
- A v2 plan validates every enforced scope and validates provenance shape, but
  snapshot drift is reported as trace data rather than an activation failure.
- Rebind keeps its public CLI and atomic-write behavior. Content or assembly
  changes still require the existing explicit approval route.
- Approved production rejects every unclassified source page unless its exact
  source ref appears in an explicit plan exception list. The initial migrated
  contract has no exceptions.

## Non-goals

- Do not change Manual IR schema or public build/rebind CLI flags.
- Do not change reference PDF, physical page count, composition map, source
  order, language mapping, or renderer output.
- Do not weaken release-snapshot/rebuild contracts; this change is limited to
  approved IDML layout activation.
- Do not regenerate visual goldens as part of the contract refactor.

## Safety net

- Characterize v1 strict snapshot matching.
- Prove v2 accepts provenance-only snapshot drift but rejects content, style,
  layout, assembly, and per-page drift.
- Prove v2 assembly identity changes when a page role changes.
- Prove approved production rejects unclassified prose and accepts only exact
  declared exceptions.
- Keep v1 registry discovery and unregistered-contract guards working.
- Run targeted tests, full unittest, Ruff, maintainability, reference-pin and
  documentation-link checks, then the production JE-1000F US IDML entrypoint.
