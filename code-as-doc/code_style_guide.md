# Code Style Guide

Updated: 2026-09-30

## 1. Role

This file defines codebase maintainability rules and module boundaries for the current repository.
It is not:

- the user workflow guide
- the maintainer command reference
- the long-term strategy document

Use these docs for those topics:

- current workflow and editing surfaces: [`../user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md)
- current command semantics: [`build_doc_guide.md`](build_doc_guide.md)
- long-term strategy: [`architecture/System Evolution Strategy.md`](architecture/System%20Evolution%20Strategy.md)

## 2. Primary Module Boundaries

### 2.1 Entrypoint and Orchestration

- [`../build.py`](../build.py)
- [`../tools/build/docs.py`](../tools/build/docs.py)

Responsibilities:

- CLI entrypoints
- action routing
- high-level build ordering
- target-aware workflow orchestration

### 2.2 Shared Target Logic

- [`../tools/utils/targets.py`](../tools/utils/targets.py)

Responsibilities:

- normalize target resolution
- provide shared `model / region / token` behavior
- prevent per-command drift in target semantics

### 2.3 Structured Rendering

- [`../tools/csv_page_build.py`](../tools/csv_page_build.py)
- [`../tools/csv_pages/`](../tools/csv_pages)

Responsibilities:

- read phase2 CSV snapshots
- render CSV-driven pages
- keep data rendering separate from bundle assembly

### 2.4 Bundle Materialization

- [`../tools/gen_index_bundle.py`](../tools/gen_index_bundle.py)

Responsibilities:

- resolve configured pages
- materialize bundle layout
- place assets, generated pages, and renderers into the runtime bundle

### 2.5 Review Lifecycle

- [`../tools/review_bundle.py`](../tools/review_bundle.py)
- [`../tools/review_support.py`](../tools/review_support.py)
- [`../tools/sync_review.py`](../tools/sync_review.py)

Responsibilities:

- seed review bundles
- overlay review content onto runtime bundles
- sync data-driven changes back into review

### 2.6 Validation and Contracts

- [`../tools/validate_config.py`](../tools/validate_config.py)
- [`../tools/validate_layout_params.py`](../tools/validate_layout_params.py)
- [`../tools/check/docs.py`](../tools/check/docs.py)
- [`../tools/check_identity_drift.py`](../tools/check_identity_drift.py)
- [`../tools/page_contracts.py`](../tools/page_contracts.py)

Responsibilities:

- config and layout checks
- bundle validation
- stale identity detection
- page contract enforcement

### 2.7 Export, Reporting, and Release

- [`../tools/word_bundle*.py`](../tools)
- [`../tools/diff_report.py`](../tools/diff_report.py)
- [`../tools/release_manifest.py`](../tools/release_manifest.py)

Responsibilities:

- format-specific export
- revision reporting
- release traceability

### 2.8 Build Queue and Delivery

- [`../tools/build_queue/`](../tools/build_queue) (since CQ-1.4: `process_build_queue*.py`, `process_review_start_queue*.py`, and the `queue_*.py` family without its prefix; the old top-level names are deprecated shims)
- `listen_*.py`, `message_*.py`, [`../tools/dingtalk/`](../tools/dingtalk)

Responsibilities:

- turn Feishu queue rows into build, review-start, and publish runs
- own queue state transitions, row write-back, and delivery mirrors
- details: [`dev/orchestration_module_map.md`](dev/orchestration_module_map.md) §5 and [`dev/queue_state_model.md`](dev/queue_state_model.md)

### 2.9 Cloud-Doc Backport

- [`../tools/backport/`](../tools/backport) (the `cloud_doc_backport*` family since CQ-1.3; the old top-level names are deprecated shims), `backport_*.py`

Responsibilities:

- diff a reviewed cloud doc against its review pages and route each delta to the surface that owns it
- write only through the gated review, template-sync, and source-table paths
- details: [`dev/orchestration_module_map.md`](dev/orchestration_module_map.md) §6

### 2.10 Source Intake and Data Sync

- `sync_data*.py`, `source_*.py`, `data_*.py`, [`../tools/utils/`](../tools/utils) `spec_master*.py`

Responsibilities:

- export Feishu source tables into phase2 snapshots and keep their contracts
- structured spec-sheet intake into the source tables
- details: [`dev/orchestration_module_map.md`](dev/orchestration_module_map.md) §7 and [`spec_master_user_guide.md`](spec_master_user_guide.md)

### 2.11 Web, Manual IR, and Components

- `web_*.py`, `document_*.py`, `frozen_ai_*.py`, `frozen_pdf_*.py`
- [`../tools/manual_ir/`](../tools/manual_ir), [`../tools/component_specs/`](../tools/component_specs), [`../tools/page_plan/`](../tools/page_plan)

Responsibilities:

- whole-document Web source → `manual-ir` → registered ComponentSpecs → the one shared Web renderer
- frozen AI/PDF intake adapters that feed the same IR, never a second renderer
- details: the "Whole-document Web boundary" in [`dev/orchestration_module_map.md`](dev/orchestration_module_map.md) and [`dev/web_publish_pipeline.md`](dev/web_publish_pipeline.md)

### 2.12 IDML / InDesign

- [`../tools/idml/`](../tools/idml), [`../tools/export_idml.py`](../tools/export_idml.py), `idml_rst_*.py`
- details: [`dev/idml_module_map.md`](dev/idml_module_map.md)

### 2.13 Read the Docs Portal

- `rtd_*.py`, [`../tools/rtd_portal_assets/`](../tools/rtd_portal_assets)
- details: [`dev/rtd_manual_portal.md`](dev/rtd_manual_portal.md)

### 2.14 Assets

- `asset_*.py`, `bundle_asset_*.py`, [`../tools/asset_pipeline/`](../tools/asset_pipeline)
- details: [`dev/asset_ai_master_intake_plan.md`](dev/asset_ai_master_intake_plan.md)

### 2.15 Maintainability Guardrails

- [`../tools/check_maintainability_guardrails.py`](../tools/check_maintainability_guardrails.py): hotspot line caps plus the language-literal and per-function complexity ratchets
- [`../tools/check_doc_link_integrity.py`](../tools/check_doc_link_integrity.py): relative doc links plus the plan/review lifecycle `Status:` rule
- [`../tools/env_preflight.py`](../tools/env_preflight.py): advisory drift against the pinned runtime and `requirements.lock`

Responsibilities:

- block new debt; existing debt lives in reviewed baselines under `data/` that may only shrink
- a baseline change is part of the PR that causes it and is explained in the PR description

### 2.16 Target Subpackages (proposed)

`tools/` is still mostly flat: a prefix names the domain. Workstream Y
([`dev/code_quality_iterability_plan.md`](dev/code_quality_iterability_plan.md) CQ-1)
moves each family into a real subpackage. The names below are proposals.

| Domain | Today | Proposed package |
| --- | --- | --- |
| Build orchestration | `build_*.py`, `build_docs_*.py` | `tools/build/` (`build_docs*` moved 2026-10-03) |
| Quality gates | `check_*.py`, `validate_*.py`, `content_lint*.py` | `tools/check/` (`check_docs*` moved 2026-10-03) |
| Build queue and delivery | `process_*queue*.py`, `queue_*.py`, `listen_*.py`, `message_*.py` | `tools/build_queue/` (not `tools/queue/`: a `queue` package would shadow the stdlib module whenever `tools/` is on `sys.path`; `process_*queue*`/`queue_*` moved 2026-10-03) |
| Cloud-doc backport | `cloud_doc_backport*.py`, `backport_*.py` | `tools/backport/` (CQ-1.3 pilot, `cloud_doc_backport*` moved 2026-10-03) |
| Web delivery | `web_*.py`, `document_*.py`, `frozen_*.py` | `tools/web/` (`web_*` moved 2026-10-03) |
| Read the Docs portal | `rtd_*.py` | `tools/rtd/` |
| Word export | `word_bundle*.py` | `tools/word/` |
| IDML | `export_idml.py`, `idml_rst_*.py` | existing `tools/idml/` |
| Source intake and sync | `sync_data*.py`, `source_*.py`, `data_*.py` | `tools/data/` |

`tools/manual_ir/`, `tools/component_specs/`, `tools/csv_pages/`, and
`tools/utils/` are already packages and stay where they are.

Rules for the migration:

- one family per PR, with a thin re-export shim at each old module path until no caller or test uses it
- moving a hotspot module needs operator confirmation first ([`../AGENTS.md`](../AGENTS.md) §8.4)
- until its family has moved, a new module keeps the family prefix at the top of `tools/`

## 3. Change Placement Rules

- command semantics belong first in [`../build.py`](../build.py); low-level scripts must stay consistent with it
- target resolution logic belongs in shared helpers, not copied into individual commands
- bundle-path and asset-placement logic belongs in bundle materialization code, not scattered across renderers
- review-only behavior belongs in review modules, not hidden inside generic build paths
- data-file semantics belong in [`spec_master_user_guide.md`](spec_master_user_guide.md), not in scattered comments or historical logs

## 4. Maintainability Rules

- Prefer one config per template family, not one config per model.
- Keep review and runtime responsibilities separate.
- Prefer explicit contracts over implicit placeholder assumptions.
- Fail fast on missing target identity, missing contract requirements, or missing assets.
- Reuse shared helpers for target-aware paths and defaults.
- Avoid model-specific branching when the logic can be expressed as structured data.

## 5. Documentation Sync Rule

When a code change alters behavior, update the document that owns that behavior in the same change:

- command behavior: [`build_doc_guide.md`](build_doc_guide.md)
- user workflow: [`../user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md)
- data semantics: [`spec_master_user_guide.md`](spec_master_user_guide.md)
- repo roadmap: [`../optimization_project.md`](optimization_project.md)
- completed optimization phases or workstreams: [`code_optimization_log.md`](code_optimization_log.md)

## 6. Testing Expectations

Baseline expectations:

- run `python3 -m unittest`
- run the workflow command most directly affected by the change when practical
- add or update regression tests for new target-resolution, bundle, review, or contract behavior

## 7. Next Review Trigger

Update this file when module responsibilities change or when new workflow logic introduces a new stable boundary in the codebase.
