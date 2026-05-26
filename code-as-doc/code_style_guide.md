# Code Style Guide

Updated: 2026-03-17

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
- [`../tools/build_docs.py`](../tools/build_docs.py)

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
- [`../tools/check_docs.py`](../tools/check_docs.py)
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
- repo roadmap: [`../optimization_project.md`](../optimization_project.md)
- completed optimization phases or workstreams: [`code_optimization_log.md`](code_optimization_log.md)

## 6. Testing Expectations

Baseline expectations:

- run `python3 -m unittest`
- run the workflow command most directly affected by the change when practical
- add or update regression tests for new target-resolution, bundle, review, or contract behavior

## 7. Next Review Trigger

Update this file when module responsibilities change or when new workflow logic introduces a new stable boundary in the codebase.
