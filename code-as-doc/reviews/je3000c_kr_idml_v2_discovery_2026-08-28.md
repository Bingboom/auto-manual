# JE-3000C KR IDML v2 discovery and implementation plan

Date: 2026-08-28
Branch: `feat/je3000c-kr-idml-v2`
Baseline: `5db6f6f94a4a2cfc353daa634e299a85d9d711b2`

## Goal

Build a second JE-3000C/KR IDML handoff from current `main` by reusing the
shared JE component and composition contracts. The target may add assembly
data, target assets, and language capacity data; it must not copy the first
package's model-specific page renderer.

Reference inputs:

- shipped 18-page PDF: `说明书 HTE1563000A-KR-JAK RoHS REACH.pdf`
- frozen review bundle: 27 files from `review/JE-3000C-KR` at
  `c1550c5b3fffc11ba92a2263847256f72fe005e2`
- first-build candidate and extracted assets from the isolated first-build
  worktree, used as evidence and asset input only

## Discovery findings

1. Current `main` already registers the reusable composition types needed for
   the body: `operation`, `ups_charging`, `charging_methods`,
   `storage_troubleshooting`, `specifications`, `warranty`, `app`, `lcd`,
   `product_overview`, and `maintenance_symbols`.
2. The first package introduced `operation_ups` and
   `charging_charging_methods`, passed absolute `/private/tmp/.../quarantine`
   asset paths, and added about 1,900 lines of page rendering/validation code.
   That commit is not a reusable implementation and will not be cherry-picked.
3. The 18-page KR reference packs multiple source sections onto the same
   physical page:
   - page 2: preface + safety + maintenance;
   - page 4: inbox + product overview;
   - page 10: operation tail + UPS;
   - page 13: storage + troubleshooting.
4. Target assembly v1 groups source roles by one composition id and forbids
   overlapping physical ranges. It can express the registered
   `storage_troubleshooting` pair directly, but it cannot express page 2,
   page 4, or the page-10 operation/UPS handoff without either inventing a new
   combined composition type or adding a renderer-neutral packing contract.
5. The correct extension, if the baseline build confirms the limitation, is a
   generic page-slot/block-range assembly capability. It must route existing
   composition instances into target-owned external rectangles/page ranges;
   it must not duplicate component internals or branch on model, language,
   localized title, or physical page number.

## Reuse metrics

Primary component reuse rate:

```text
existing public component instances / all visible component instances
```

The final report also records:

- existing composition-type reuse rate;
- number of new renderer functions (target: 0);
- number of target assembly data entries;
- number of new target asset instances;
- total elapsed development time, pure IDML build time, and native InDesign
  finalize/export time.

## Implementation phases

### Phase 1 - frozen local build input

- Materialize the frozen review bundle in the isolated clone without staging
  it.
- Reuse the first-build phase2 fixture and approved text-free assets only as
  isolated build inputs.
- Create a local JE-3000C/KR config/manifest that selects the target assembly
  candidate and compact layout overlay.

Safety net: generate the real Manual IR through `build.py idml` and run the
target-assembly scaffold against the 18-page reference PDF.

### Phase 2 - target assembly data

- Replace first-build combined composition types with current shared types.
- Replace absolute quarantine links with repo-relative target asset paths.
- Add only target instance data required by public components.

Safety net: `normalize_target_assembly_plan` plus composition-plan tests.

### Phase 3 - generic packing extension, only if required

- Add a renderer-neutral target packing field that composes existing public
  component outputs into shared physical-page slots.
- Keep visible geometry ownership in the components; the assembly layer owns
  only external rectangles, page spans, ordering, and flow boundaries.
- Add negative tests forbidding model-specific branches and private component
  access.

Safety net: targeted target-assembly/page-boundary/component tests, then Ruff.

### Phase 4 - native artifact and visual QA

- Build production and flow IDML through `build.py`.
- Package all links with relative `Links/` URIs.
- Finalize through the installed InDesign, export PDF, and require zero
  overset/missing-font/bad-link findings.
- Render all 18 pages and compare page order, dominant component geometry,
  callouts/leaders, typography, and pagination against the shipped PDF and the
  approved JE component appearance.

## Verification ladder

1. `python -m ruff check` on changed Python/tests.
2. Targeted target-assembly, page-boundary, component, and finalize tests.
3. `python -m unittest`.
4. `python tools/check_maintainability_guardrails.py`.
5. `python tools/check_doc_link_integrity.py`.
6. JE-3000C/KR IDML build and package validation.
7. Native InDesign finalize/preflight and rendered-PDF visual comparison.

## Non-goals

- no source-table writes;
- no changes to the dirty primary worktree;
- no approval or production promotion of the candidate contract;
- no reuse of model-specific renderer code from the first package;
- no cleanup of user or generated artifacts outside the isolated clone.
