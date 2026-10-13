# Orchestration module map: quality and release modules (§4)

Status: active · Part of the [orchestration module map](../orchestration_module_map.md); its index lists the other
module families. Update this page in the same PR that moves a boundary here; do not add
module notes to the hub.

## 4. Quality And Release Modules

Quality and release logic should follow concern-specific modules instead of drifting back into entry files:

- [`tools/check/docs.py`](../../../tools/check/docs.py)
  - quality gate facade over bundle/reference/contract/generated-page checks
- [`tools/check/docs_runtime.py`](../../../tools/check/docs_runtime.py)
  - target-scoped quality-check orchestration and collector sequencing
- [`tools/check/docs_renderer_contracts.py`](../../../tools/check/docs_renderer_contracts.py)
  - FCC document/web renderer preflight using the resolved target language
- [`tools/check/docs_generated.py`](../../../tools/check/docs_generated.py)
  - generated-page rule helpers
- [`tools/validate_spec_master_shared.py`](../../../tools/validate_spec_master_shared.py)
  owns shared validation predicates, including source-language recognition from
  the canonical registry plus legacy display aliases. This validation boundary
  does not change Spec_Master value lookup precedence.
- [`tools/validate_spec_master_runtime.py`](../../../tools/validate_spec_master_runtime.py)
  - runtime Spec_Master validation rules
- [`tools/page_contracts.py`](../../../tools/page_contracts.py)
  - page contract enforcement
- [`tools/diff_report.py`](../../../tools/diff_report.py)
  - compatibility facade for diff-report CLI
- [`tools/diff_report_git.py`](../../../tools/diff_report_git.py)
  - git/path extraction helpers
- [`tools/diff_report_fields.py`](../../../tools/diff_report_fields.py)
  - field and page diff extraction heuristics
- [`tools/diff_report_render.py`](../../../tools/diff_report_render.py)
  - report rendering
- [`tools/diff_report_reports.py`](../../../tools/diff_report_reports.py)
  - report assembly
- [`tools/release_manifest.py`](../../../tools/release_manifest.py)
  - release-manifest CLI facade
- [`tools/release_manifest_service.py`](../../../tools/release_manifest_service.py)
  - release traceability assembly
- [`tools/release_tag.py`](../../../tools/release_tag.py)
  - dry-run-first annotated release-tag creation and manifest/hash verification
  - idempotent local/remote collision checks; no tag is created during build
- [`tools/release_snapshot.py`](../../../tools/release_snapshot.py)
  - immutable version-scoped phase2 snapshot freezing, identity inventory, historical verification, and rebind/drift rejection
- [`tools/release_reproducibility.py`](../../../tools/release_reproducibility.py)
  - clean tracked-tree gate, Git commit epoch resolution, deterministic release environment, and manifest contract record
  - two-phase review-overlay provenance for composite `main` toolchain + review-branch releases: full file/blob verification at publish entry, then source-commit/tree binding after deterministic build mutations
- [`tools/release_rebuild.py`](../../../tools/release_rebuild.py)
  - fail-closed historical rebuild from manifest Git SHA plus frozen snapshot
  - exact review-overlay restoration before isolated publish and byte-equivalence verification for DOCX, Markdown, and PDF
- [`tools/release_indesign_package.py`](../../../tools/release_indesign_package.py)
  - InDesign package lineage plus native preflight layout signals; JSON owns
    the nested record and release CSV receives the flattened page/overset counts
- [`tools/check_review_branch_sync.py`](../../../tools/check_review_branch_sync.py)
  - advisory text entrypoint plus the read-only `--json` propagation ledger
  - changed shared-source scope, live review-branch inventory, and strict exit semantics
- [`tools/review_propagation_ledger.py`](../../../tools/review_propagation_ledger.py)
  - review-manifest target resolution, seed/current manifest applicability,
    derivative mapping, and exact-or-abstain `merge_params` safety proof
  - no branch mutation, sync, PR creation, or propagation apply surface

### Maintainability Guardrails

- [`tools/check_maintainability_guardrails.py`](../../../tools/check_maintainability_guardrails.py)
  - hotspot line caps, target-scoped IDML predicates, shared-Web target literals
  - runs the two ratchets below; each fails only on new or grown debt
- [`tools/check_language_literal_ratchet.py`](../../../tools/check_language_literal_ratchet.py)
  - hand-written language tables against `data/language_literal_baseline.txt`
- [`tools/check_complexity_ratchet.py`](../../../tools/check_complexity_ratchet.py)
  - stdlib per-function cyclomatic complexity against `data/complexity_baseline.tsv`: new functions stay at 20 or below, recorded ones may not grow, a lower value must be written back
- [`tools/check_facade_patch_ratchet.py`](../../../tools/check_facade_patch_ratchet.py)
  - per-test-file count of patches on facade modules against `data/facade_patch_baseline.tsv`: unlisted files may not patch a facade, recorded counts may not grow, a lower count must be written back
- [`tools/check_broad_except_ratchet.py`](../../../tools/check_broad_except_ratchet.py)
  - per-file count of `except Exception` / `except BaseException` in `build.py`, `tools/`, `scripts/`, `integrations/` against `data/broad_except_baseline.tsv`: unlisted files may not add one, recorded counts may not grow, a lower count must be written back. Audited handlers are not counted: one whose body ends in `raise`, or whose `except` line carries `# noqa: BLE001 - <reason>`. The baseline is empty since the CQ-5.3 audit
- [`tools/check_top_level_module_ratchet.py`](../../../tools/check_top_level_module_ratchet.py)
  - `tools/*.py` top-level modules and files carrying script bootstrap code against `data/top_level_module_baseline.tsv`: both lists may only shrink; a new top-level module needs `update --allow NAME=REASON`, and removals must be written back
- [`tools/check_mypy_ratchet.py`](../../../tools/check_mypy_ratchet.py)
  - per-file count of `mypy --disallow-untyped-defs` errors in `tools/manual_ir`, `tools/component_specs`, `tools/csv_pages` against `data/mypy_untyped_baseline.tsv`; runs in the CI `type-check` job (not in the guardrails, which have no mypy)
- [`tools/check_doc_link_integrity.py`](../../../tools/check_doc_link_integrity.py)
  - relative links under `code-as-doc/` and `user-guide/`; with the default roots it also runs the lifecycle check
- [`tools/check_doc_lifecycle.py`](../../../tools/check_doc_lifecycle.py)
  - plan/review docs under `code-as-doc/dev/` and `code-as-doc/reviews/` declare `Status:`; pre-rule docs are listed in `data/doc_lifecycle_baseline.txt`

### Review Preview Packaging

- [`tools/process_docs/build_review_preview.py`](../../../tools/process_docs/build_review_preview.py)
  - review-preview CLI facade, diff-based default-target inference, and package orchestration
- [`tools/process_docs/build_review_preview_config.py`](../../../tools/process_docs/build_review_preview_config.py)
  - delegates exact model/region config selection and ambiguity rejection to the shared queue target resolver
  - config-derived workspace target metadata
- [`tools/process_docs/build_review_preview_targets.py`](../../../tools/process_docs/build_review_preview_targets.py)
  - review availability, target discovery, output paths, and build/diff command assembly
- [`tools/process_docs/build_review_preview_workspace.py`](../../../tools/process_docs/build_review_preview_workspace.py)
  - per-target exports and workspace payload assembly
