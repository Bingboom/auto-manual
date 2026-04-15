# Current Repository Component Map

Updated: 2026-04-08

## 1. Role

This file maps the current repository components and their ownership boundaries.
It describes how the current repo is organized today.

This file is not:

- the long-term strategy document
- the daily user workflow guide
- the full command reference

Use these documents for those topics:

- long-term strategy: [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md)
- current workflow and editing surfaces: [`../../user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md)
- maintainer command reference: [`../build_doc_guide.md`](../build_doc_guide.md)

## 2. Current Component Map

### 2.1 Entrypoint Layer

- [`../../build.py`](../../build.py)
- [`../../tools/build_main.py`](../../tools/build_main.py)

Current responsibility:

- top-level action routing
- target-aware command entry
- keeping user-facing command semantics stable

### 2.2 Build Orchestration Layer

- [`../../tools/build_docs.py`](../../tools/build_docs.py)
- [`../../tools/build_docs_main.py`](../../tools/build_docs_main.py)
- [`../../tools/build_docs_entry.py`](../../tools/build_docs_entry.py)
- [`../../tools/build_docs_export.py`](../../tools/build_docs_export.py)
- [`../../tools/build_docs_artifacts.py`](../../tools/build_docs_artifacts.py)
- [`../../tools/utils/targets.py`](../../tools/utils/targets.py)

Current responsibility:

- resolve targets
- prepare runtime bundles
- coordinate export order
- keep low-level build/export wrappers patchable while real artifact steps live in helper modules

### 2.3 Structured Content Layer

- [`../../data/phase1/Spec_Master.csv`](../../data/phase1/Spec_Master.csv)
- [`../../data/phase1/Spec_Footnotes.csv`](../../data/phase1/Spec_Footnotes.csv)
- [`../../data/phase1/spec_titles.csv`](../../data/phase1/spec_titles.csv)
- [`../../data/phase1/content_blocks.csv`](../../data/phase1/content_blocks.csv)
- [`../../data/phase1/page_registry.csv`](../../data/phase1/page_registry.csv)

Current responsibility:

- product identity
- placeholder values
- block-driven content
- spec section metadata

### 2.4 Shared Seed Layer

- [`../../docs/templates/`](../../docs/templates)
- [`../../tools/phase1_build.py`](../../tools/phase1_build.py)
- [`../../tools/phase1/`](../../tools/phase1)

Current responsibility:

- shared page structure
- CSV-driven page rendering
- first-draft generation before review starts

### 2.5 Runtime Bundle Layer

- [`../../tools/gen_index_bundle.py`](../../tools/gen_index_bundle.py)
- [`../../docs/_build/`](../../docs/_build)

Current responsibility:

- materialize target-specific RST bundles
- assemble generated pages, template pages, assets, and renderers
- provide the bundle consumed by HTML, Word, and PDF export

### 2.6 Review Layer

- [`../../tools/review_bundle.py`](../../tools/review_bundle.py)
- [`../../tools/review_support.py`](../../tools/review_support.py)
- [`../../tools/sync_review.py`](../../tools/sync_review.py)
- [`../../docs/_review/`](../../docs/_review)

Current responsibility:

- seed review bundles
- preserve target-specific editing surfaces
- sync data-driven runtime files back into review when CSV data changes

### 2.7 Validation Layer

- [`../../tools/validate_config.py`](../../tools/validate_config.py)
- [`../../tools/validate_layout_params.py`](../../tools/validate_layout_params.py)
- [`../../tools/check_docs.py`](../../tools/check_docs.py)
- [`../../tools/check_docs_generated.py`](../../tools/check_docs_generated.py)
- [`../../tools/check_identity_drift.py`](../../tools/check_identity_drift.py)
- [`../../tools/page_contracts.py`](../../tools/page_contracts.py)
- [`../../tools/validate_spec_master_runtime.py`](../../tools/validate_spec_master_runtime.py)

Current responsibility:

- config and layout validation
- bundle checks
- stale identity detection
- page contract enforcement

### 2.8 Queue Orchestration Layer

- [`../../tools/process_build_queue.py`](../../tools/process_build_queue.py)
- [`../../tools/process_build_queue_main.py`](../../tools/process_build_queue_main.py)
- [`../../tools/process_build_queue_services.py`](../../tools/process_build_queue_services.py)
- [`../../tools/queue_orchestration.py`](../../tools/queue_orchestration.py)
- [`../../tools/queue_group_processing.py`](../../tools/queue_group_processing.py)

Current responsibility:

- bridge queued review/build/publish work into the repo command surface
- keep queue entrypoints orchestration-first
- isolate transport, worktree, writeback, and release-output helpers behind queue-specific modules

### 2.9 Reporting and Release Layer

- [`../../tools/diff_report.py`](../../tools/diff_report.py)
- [`../../tools/diff_report_fields.py`](../../tools/diff_report_fields.py)
- [`../../tools/diff_report_render.py`](../../tools/diff_report_render.py)
- [`../../tools/diff_report_reports.py`](../../tools/diff_report_reports.py)
- [`../../tools/release_manifest.py`](../../tools/release_manifest.py)
- [`../../tools/release_manifest_service.py`](../../tools/release_manifest_service.py)
- [`../../reports/`](../../reports)

Current responsibility:

- revision tracking
- report generation
- release traceability

### 2.10 Test Layer

- [`../../tests/`](../../tests)

Current responsibility:

- regression coverage for target resolution, bundle generation, review support, validation, and release flow

## 3. Current Interaction Flow

```mermaid
flowchart TD
  A["build.py"] --> B["tools/build_dispatch.py"]
  B --> C["tools/build_docs.py"]
  B --> D["tools/build_runtime.py"]
  B --> E["tools/build_reports.py"]
  B --> F["tools/build_publish.py"]
  C --> G["tools/gen_index_bundle.py"]
  C --> H["tools/build_docs_export.py"]
  H --> I["docs/_build/<model>/<region>/rst"]
  I --> J["docs/_review/<model>/<region> overlay"]
  J --> K["html / word / pdf"]
  J --> L["check"]
  J --> M["diff-report"]
  K --> N["release-manifest"]
  A --> O["tools/process_build_queue.py"]
  O --> P["queue_* / queue_bound_* helpers"]
```

## 4. Ownership Rules

- command behavior changes belong first to [`../../build.py`](../../build.py) and the low-level script it wraps
- target resolution changes belong in shared target helpers, not duplicated across commands
- quality-gate changes belong in validation/check modules, not inline in entrypoints
- release and diff-report changes belong in release/reporting helpers, not inline in queue or build entry files
- queue transport/writeback changes belong in queue modules, not in generic build helpers
- review lifecycle changes belong in the review support modules and the user workflow docs
- current data-file semantics belong in [`../spec_master_user_guide.md`](../spec_master_user_guide.md)
- long-term architecture changes belong in [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md), not here

## 5. Next Review Trigger

Update this file when the current repository topology changes or when a component takes on a materially different responsibility.
