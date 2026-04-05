# Orchestration Module Map

Updated: 2026-04-05

This file records the current module boundaries for the repo's main workflow entrypoints.
Use it as the living map for "where should this logic go?" after the build and queue decomposition wave.

This is not the user workflow guide.
For day-to-day commands, use:

- [`code-as-doc/build_doc_guide.md`](../build_doc_guide.md)
- [`user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md)

## 1. Entrypoint Rule

Keep these files orchestration-first:

- [`build.py`](../../build.py)
- [`tools/process_build_queue.py`](../../tools/process_build_queue.py)

That means:

- parse and validate high-level entry arguments
- call stable helper modules
- keep compatibility wrappers when tests or external callers depend on existing names

Do not move new low-level implementation back into these files unless the behavior is truly entrypoint-specific.

## 2. Build Entrypoint Modules

[`build.py`](../../build.py) should stay thin and delegate to these helper modules:

- [`tools/build_paths.py`](../../tools/build_paths.py)
  - config loading
  - repo-root path resolution
  - staging-root resolution
  - review/build/release root selection
- [`tools/build_entry_commands.py`](../../tools/build_entry_commands.py)
  - CLI command assembly for build/check/review/sync/release queue entrypoints
- [`tools/build_reports.py`](../../tools/build_reports.py)
  - diff-report target resolution
  - publish target/tracked-root/report-dir helpers
- [`tools/build_doctor.py`](../../tools/build_doctor.py)
  - environment and dependency diagnostics
  - doctor target/pdf/reference-doc resolution
  - doctor finding collection

## 3. Document Link Queue Modules

[`tools/process_build_queue.py`](../../tools/process_build_queue.py) should stay orchestration-first and delegate to:

- [`tools/queue_contract.py`](../../tools/queue_contract.py)
  - canonical queue contract constants
  - shared queue dataclasses
  - binding / record / wiki destination type definitions
- [`tools/document_link_actions.py`](../../tools/document_link_actions.py)
  - normalized queue action vocabulary
  - legacy `Doc_phase` compatibility mapping
- [`tools/document_link_queue.py`](../../tools/document_link_queue.py)
  - row parsing
  - row filtering
  - record binding
  - queue preflight helpers
- [`tools/queue_config_resolution.py`](../../tools/queue_config_resolution.py)
  - config-family routing
  - target/config resolution for queue rows
- [`tools/queue_runtime.py`](../../tools/queue_runtime.py)
  - worktree/runtime helpers
  - generated path and review/runtime input helpers
- [`tools/queue_build_execution.py`](../../tools/queue_build_execution.py)
  - queue-triggered `build.py` command assembly
  - phase2 sync-before-build execution
  - worktree-scoped draft/publish build orchestration
- [`tools/queue_group_processing.py`](../../tools/queue_group_processing.py)
  - per-group queue processing
  - started/success/failure writeback orchestration
  - drive upload and wiki attach flow for one grouped build task
- [`tools/queue_dry_run.py`](../../tools/queue_dry_run.py)
  - dry-run preview payload assembly
  - grouped queue preview output formatting
- [`tools/queue_grouping.py`](../../tools/queue_grouping.py)
  - grouped record bucketing rules
  - document-key vs record-id grouping strategy
- [`tools/queue_session.py`](../../tools/queue_session.py)
  - queue-session bootstrap and preflight
  - pending-record fetch/select/group state
  - wiki destination reporting for a processing session
- [`tools/queue_lark_ops.py`](../../tools/queue_lark_ops.py)
  - Lark/Drive/Wiki transport and remote I/O helpers
- [`tools/queue_outputs.py`](../../tools/queue_outputs.py)
  - publish asset staging
  - release/output path helpers
  - publish metadata assembly
- [`tools/queue_writeback.py`](../../tools/queue_writeback.py)
  - queue result formatting
  - row writeback payload assembly

## 4. Maintenance Rules

When adding or moving logic in this area:

1. Prefer adding to an existing helper module before expanding an orchestration file.
2. If a new helper module is introduced, update this file in the same change.
3. If a major boundary changes, also update:
   - [`code-as-doc/code_optimization_log.md`](../code_optimization_log.md)
   - [`optimization_project.md`](../../optimization_project.md)
4. Keep wrapper names stable in entry files when tests or external scripts patch them directly.
5. If a wrapper stops being needed, remove it only after tests and call sites are updated together.
6. When encoded field names are normalized, prefer unicode-escaped canonical constants in helper modules before deleting old literals from entry files.

## 5. Known Next Decomposition Candidates

These files still deserve further decomposition:

- [`tools/build_docs.py`](../../tools/build_docs.py)
- [`tools/gen_index_bundle.py`](../../tools/gen_index_bundle.py)
- [`tools/diff_report.py`](../../tools/diff_report.py)

Keep future extraction notes here once those boundaries stabilize.
