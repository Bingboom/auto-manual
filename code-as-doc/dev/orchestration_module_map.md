# Orchestration Module Map

Updated: 2026-08-24

This file records the current module boundaries for the repo's main workflow entrypoints.
Use it as the living map for "where should this logic go?" after the build, quality, release, and queue decomposition waves.

This is not the user workflow guide.
For day-to-day commands, use:

- [`code-as-doc/build_doc_guide.md`](../build_doc_guide.md)
- [`user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md)

For external table and queue-state contracts, use:

- [`code-as-doc/dev/external_table_contracts.md`](external_table_contracts.md)
- [`code-as-doc/dev/queue_state_model.md`](queue_state_model.md)

## 1. Entrypoint Rule

Keep these files orchestration-first:

- [`build.py`](../../build.py)
- [`tools/build_docs.py`](../../tools/build_docs.py)
- [`tools/process_build_queue.py`](../../tools/process_build_queue.py)

That means:

- parse and validate high-level entry arguments
- call stable helper modules
- keep compatibility wrappers when tests or external callers depend on existing names

Do not move new low-level implementation back into these files unless the behavior is truly entrypoint-specific.

## 2. Build Entrypoint Modules

[`build.py`](../../build.py) should stay thin and delegate to these helper modules:

- [`tools/build_main.py`](../../tools/build_main.py)
  - CLI bootstrap and top-level error boundary for `build.py`
- [`tools/local_env.py`](../../tools/local_env.py)
  - loads `~/.auto-manual-phase2.env` into the environment at startup (non-overriding, no-op when absent); called once by `build_main.run_main` so `sync-data`/review run without a manual `source`
- [`tools/build_cli.py`](../../tools/build_cli.py)
  - argument parsing
- [`tools/build_dispatch.py`](../../tools/build_dispatch.py)
  - registered top-level action routing for explicit non-build actions
  - fallback routing for standard build actions such as `rst`, `word`, `pdf`, `preview`, and `fast`
- [`tools/build_paths.py`](../../tools/build_paths.py)
  - config loading
  - config-driven docs_dir / layout-params resolution
  - staging-root resolution (CLI arg / env coupling)
  - review/build/release root selection
  - thin adapter: delegates all path-segment construction to [`tools/utils/path_utils.py`](../../tools/utils/path_utils.py)
- [`tools/utils/path_utils.py`](../../tools/utils/path_utils.py)
  - single source of truth for repo-relative path segments (`PathSegments`)
  - repo-root-anchored and config-anchored `Paths`, plus `*_of(base)` suffix helpers
  - consumed by `build_paths.py` and path-building sites across `tools/`
- [`tools/build_entry_commands.py`](../../tools/build_entry_commands.py)
  - CLI command assembly for build/check/review/sync/release/queue entrypoints
- [`tools/build_runtime.py`](../../tools/build_runtime.py)
  - validate/check/pre-build runtime helpers
  - review auto-sync and cleanup helpers
- [`tools/build_reports.py`](../../tools/build_reports.py)
  - diff-report target resolution
  - tracked-root/report-dir helpers
  - diff-report command assembly
- [`tools/build_publish.py`](../../tools/build_publish.py)
  - deterministic publish orchestration over `check -> diff-report -> word -> pdf -> md -> release-manifest`
  - versioned publish enters the Git-commit-derived reproducibility environment before any release work
  - approved-reference targets keep every print renderer on the frozen `review-asis` source; other targets retain review parameter sync
- [`tools/build_doctor.py`](../../tools/build_doctor.py)
  - environment and dependency diagnostics
  - doctor target/pdf/reference-doc resolution
  - doctor finding collection
- [`tools/asset_commands.py`](../../tools/asset_commands.py)
  - single `build.py` command facade for `asset-check` and `asset-intake`
  - fail-closed validation of the public AI-intake argument contract
- [`tools/asset_registry.py`](../../tools/asset_registry.py)
  - canonical asset-registry validation and target-scoped approved-export resolution
  - immutable CSV-byte parsing plus approved/temporary/missing/quarantined status contract
- [`tools/asset_usage.py`](../../tools/asset_usage.py)
  - target-bound `asset:` resolution, safe-format selection, frozen-byte staging, and legacy-path accounting
  - deterministic `asset_usage_manifest.json` plus exact `asset_registry_snapshot.csv` emission
- [`tools/contract_assets.py`](../../tools/contract_assets.py)
  - shared legacy-path / `asset:` resolver used by both contract checking and bundle materialization
- [`tools/asset_rewrites.py`](../../tools/asset_rewrites.py)
  - semantic `asset:` restoration from finalized-bundle rewrite provenance when review content is seeded or re-finalized
- [`tools/asset_intake.py`](../../tools/asset_intake.py)
  - repo-root-aware adapter from public CLI arguments to the deterministic intake pipeline
- [`tools/asset_pipeline/recipe.py`](../../tools/asset_pipeline/recipe.py)
  - strict recipe-schema parsing and extraction-contract validation
- [`tools/asset_pipeline/extract.py`](../../tools/asset_pipeline/extract.py)
  - source inspection, private-marker checks, page normalization, previews, and semantic exports
- [`tools/asset_pipeline/package.py`](../../tools/asset_pipeline/package.py)
  - private source snapshot, manifest/CSV assembly, deterministic ZIP, and atomic publication
- [`tools/asset_pipeline/models.py`](../../tools/asset_pipeline/models.py)
  - immutable recipe, artifact, inspection, and intake-result contracts

## 3. Build Bundle And Export Modules

[`tools/utils/csv_fields.py`](../../tools/utils/csv_fields.py) owns the pure
column spelling, header presence and cell text selection primitives. It has
no business-reader or language-registry imports.
[`tools/localized_copy.py`](../../tools/localized_copy.py) retains compatible
exports, registry-aware snapshot helpers and the strict copy-key resolver. IDML
compatibility loaders and CSV page readers keep using those exports;
[`tools/lang_registry.py`](../../tools/lang_registry.py) remains the language
metadata owner. Spec_Master row helpers and lookup consumers use `csv_fields`
directly, retaining their own narrow alias and source-language policy. The
dependency stays one-way: `localized_copy -> spec_master -> row_helpers ->
csv_fields`; no lazy import hides a return edge. Model canonicalization,
ranking, filtering, repair and cache owners are unchanged. Table fallback and
empty-cell policies are recorded in
[`external_table_contracts.md`](external_table_contracts.md#localized-columns-in-frozen-snapshots).

[`tools/build_docs.py`](../../tools/build_docs.py) should stay a wrapper-compatible facade and delegate to:

- [`tools/build_docs_main.py`](../../tools/build_docs_main.py)
  - CLI bootstrap for the low-level build entrypoint
- [`tools/build_docs_entry.py`](../../tools/build_docs_entry.py)
  - top-level build session orchestration
- [`tools/build_docs_targets.py`](../../tools/build_docs_targets.py)
  - build target resolution and configured target expansion
- [`tools/build_docs_bundle.py`](../../tools/build_docs_bundle.py)
  - ordered bundle preparation: runtime materialization, review overlay, attachment aliases, then asset finalization
- [`tools/bundle_asset_finalize.py`](../../tools/bundle_asset_finalize.py)
  - final `index.rst` include-closure scan with inherited language context and fail-closed conflict handling
  - post-overlay path rewrite, final page-path recomputation, support-tree/file hashes, and `bundle_sha256`
- [`tools/gen_index_bundle_assets.py`](../../tools/gen_index_bundle_assets.py)
  - RST image/figure/substitution and raw-HTML `src` path mapping
  - bundle-relative staging bridge for semantic and legacy asset references
- [`tools/gen_index_bundle_materialize.py`](../../tools/gen_index_bundle_materialize.py)
  - contract preflight and initial non-finalized bundle manifest assembly
- [`tools/build_docs_export.py`](../../tools/build_docs_export.py)
  - export orchestration shell for one build target
- [`tools/build_docs_artifacts.py`](../../tools/build_docs_artifacts.py)
  - export-plan derivation
  - word/pdf/html artifact steps
  - HTML postprocess handoff
- [`tools/build_docs_html.py`](../../tools/build_docs_html.py)
  - manual HTML metadata and switcher helpers
- [`tools/web_presentation.py`](../../tools/web_presentation.py)
  - web-profile figure/table composition and Pandoc-safe semantic restoration
- [`tools/manual_ir/web_specs.py`](../../tools/manual_ir/web_specs.py)
  - declared HTML specification source adapter into the public ManualSource contract;
    isolated from the neutral core and IDML extraction
- [`tools/web_spec_component.py`](../../tools/web_spec_component.py)
  - validated ManualIR specification consumer with rich markup replay and atomic DOM application;
    used by both the prepared Web bundle and standalone `SpecTableDirective`
  - Word extraction/re-rendering and directive-local grouping are absent from these Web paths
- [`tools/manual_ir/web_source.py`](../../tools/manual_ir/web_source.py)
  - shared scoped HTML-source provenance envelope; reused by specifications, declared tables, callouts, Inbox and FCC
- [`tools/manual_ir/web_tables.py`](../../tools/manual_ir/web_tables.py)
  - one declared LCD/troubleshooting source decoder and owned payload validation;
    explicit CSV/class identities select tables independently of filenames or artwork grants
- [`tools/web_table_ir.py`](../../tools/web_table_ir.py)
  - shared public IR replay and atomic DOM application for LCD/troubleshooting;
    `web_lcd_component` / `web_troubleshooting_component` are thin existing entrypoints
- [`tools/manual_ir/web_callouts.py`](../../tools/manual_ir/web_callouts.py)
  - declared/generated HTML callout decoder; owns one-row geometry, ComponentSpec, image references
    and optional explicit carrier language/variant declarations
- [`tools/web_callout_ir.py`](../../tools/web_callout_ir.py)
  - public IR replay for the Web/Pandoc placeholder handoff; verifies semantics against retained markup
  - `web_presentation` passes IR and `markdown_bundle` supplies actual source/target context;
    standalone MyST uses the same consumer after Sphinx renders its resolved child nodes;
    already-protected composite figures remain a separate path
- [`tools/manual_ir/web_inbox.py`](../../tools/manual_ir/web_inbox.py)
  - scoped Inbox source/payload adapter; reuses the existing three-card + internal TIP ComponentSpec
  - records retained markup/assets and validates complete geometry plus semantic agreement
- [`tools/web_inbox_component.py`](../../tools/web_inbox_component.py)
  - real Web entrypoint assembles public IR, replays on detached tags, then atomically applies the figure
  - existing target gate and projection remain; direct ComponentSpec-only Web reading has exited
- [`tools/manual_ir/web_fcc.py`](../../tools/manual_ir/web_fcc.py)
  - prepared FCC source and owned IR contract; carries existing semantic blocks and resolved mark binding
  - validates canonical semantics, source identity and asset binding without reparsing HTML at replay
- [`tools/web_fcc_component.py`](../../tools/web_fcc_component.py)
  - actual Web consumer assembles public IR and renders its semantic slots before mutating caller DOM
  - retains existing FCC projection/layout; source marker config is not a renderer input
- [`tools/web_reference_components.py`](../../tools/web_reference_components.py)
  - reusable reference-figure label validation, themeable captions, and shared App artwork with live localized control labels
- [`tools/web_stylesheets.py`](../../tools/web_stylesheets.py)
  - ordered assembly of the responsive base theme and focused component CSS modules into one public Sphinx stylesheet
- [`tools/utils/spec_footnotes.py`](../../tools/utils/spec_footnotes.py)
  - shared reference-ID parsing, numeric markers and marker attachment for CSV spec and IDML readers; row/language selection stays with callers
- [`tools/build_docs_io.py`](../../tools/build_docs_io.py)
  - Sphinx, cleanup, Word/PDF I/O helpers
- [`tools/build_docs_validation.py`](../../tools/build_docs_validation.py)
  - config/layout validation helpers for the build tool
- [`tools/word_bundle_docx.py`](../../tools/word_bundle_docx.py)
  - DOCX export assembly and Word post-processing orchestration
- [`tools/word_bundle_docx_styles.py`](../../tools/word_bundle_docx_styles.py)
  - DOCX heading/style remapping and outline-level normalization
- [`tools/word_bundle_docx_images.py`](../../tools/word_bundle_docx_images.py)
  - DOCX external image embedding and content-type updates
- [`tools/word_bundle_docx_pandoc.py`](../../tools/word_bundle_docx_pandoc.py)
  - pandoc version guardrails for reference-template DOCX exports
- [`tools/word_bundle_docx_xml.py`](../../tools/word_bundle_docx_xml.py)
  - namespace-preserving XML serialization helpers for DOCX package rewrites
- [`tools/word_bundle_docx_reproducible.py`](../../tools/word_bundle_docx_reproducible.py)
  - release-only DOCX canonicalization for timestamps, local file URIs, ZIP metadata, and member ordering

## 4. Quality And Release Modules

Quality and release logic should follow concern-specific modules instead of drifting back into entry files:

- [`tools/check_docs.py`](../../tools/check_docs.py)
  - quality gate facade over bundle/reference/contract/generated-page checks
- [`tools/check_docs_runtime.py`](../../tools/check_docs_runtime.py)
  - target-scoped quality-check orchestration and collector sequencing
- [`tools/check_docs_renderer_contracts.py`](../../tools/check_docs_renderer_contracts.py)
  - FCC document/web renderer preflight using the resolved target language
- [`tools/check_docs_generated.py`](../../tools/check_docs_generated.py)
  - generated-page rule helpers
- [`tools/validate_spec_master_runtime.py`](../../tools/validate_spec_master_runtime.py)
  - runtime Spec_Master validation rules
- [`tools/page_contracts.py`](../../tools/page_contracts.py)
  - page contract enforcement
- [`tools/diff_report.py`](../../tools/diff_report.py)
  - compatibility facade for diff-report CLI
- [`tools/diff_report_git.py`](../../tools/diff_report_git.py)
  - git/path extraction helpers
- [`tools/diff_report_fields.py`](../../tools/diff_report_fields.py)
  - field and page diff extraction heuristics
- [`tools/diff_report_render.py`](../../tools/diff_report_render.py)
  - report rendering
- [`tools/diff_report_reports.py`](../../tools/diff_report_reports.py)
  - report assembly
- [`tools/release_manifest.py`](../../tools/release_manifest.py)
  - release-manifest CLI facade
- [`tools/release_manifest_service.py`](../../tools/release_manifest_service.py)
  - release traceability assembly
- [`tools/release_tag.py`](../../tools/release_tag.py)
  - dry-run-first annotated release-tag creation and manifest/hash verification
  - idempotent local/remote collision checks; no tag is created during build
- [`tools/release_snapshot.py`](../../tools/release_snapshot.py)
  - immutable version-scoped phase2 snapshot freezing, identity inventory, historical verification, and rebind/drift rejection
- [`tools/release_reproducibility.py`](../../tools/release_reproducibility.py)
  - clean tracked-tree gate, Git commit epoch resolution, deterministic release environment, and manifest contract record
  - two-phase review-overlay provenance for composite `main` toolchain + review-branch releases: full file/blob verification at publish entry, then source-commit/tree binding after deterministic build mutations
- [`tools/release_rebuild.py`](../../tools/release_rebuild.py)
  - fail-closed historical rebuild from manifest Git SHA plus frozen snapshot
  - exact review-overlay restoration before isolated publish and byte-equivalence verification for DOCX, Markdown, and PDF
- [`tools/release_indesign_package.py`](../../tools/release_indesign_package.py)
  - InDesign package lineage plus native preflight layout signals; JSON owns
    the nested record and release CSV receives the flattened page/overset counts
- [`tools/check_review_branch_sync.py`](../../tools/check_review_branch_sync.py)
  - advisory text entrypoint plus the read-only `--json` propagation ledger
  - changed shared-source scope, live review-branch inventory, and strict exit semantics
- [`tools/review_propagation_ledger.py`](../../tools/review_propagation_ledger.py)
  - review-manifest target resolution, seed/current manifest applicability,
    derivative mapping, and exact-or-abstain `merge_params` safety proof
  - no branch mutation, sync, PR creation, or propagation apply surface

### Review Preview Packaging

- [`tools/process_docs/build_review_preview.py`](../../tools/process_docs/build_review_preview.py)
  - review-preview CLI facade, diff-based default-target inference, and package orchestration
- [`tools/process_docs/build_review_preview_config.py`](../../tools/process_docs/build_review_preview_config.py)
  - delegates exact model/region config selection and ambiguity rejection to the shared queue target resolver
  - config-derived workspace target metadata
- [`tools/process_docs/build_review_preview_targets.py`](../../tools/process_docs/build_review_preview_targets.py)
  - review availability, target discovery, output paths, and build/diff command assembly
- [`tools/process_docs/build_review_preview_workspace.py`](../../tools/process_docs/build_review_preview_workspace.py)
  - per-target exports and workspace payload assembly

## 5. Build Queue Modules

[`tools/process_build_queue.py`](../../tools/process_build_queue.py) should stay orchestration-first and delegate to:

- [`tools/process_build_queue_main.py`](../../tools/process_build_queue_main.py)
  - CLI bootstrap and data-root normalization for the queue entrypoint
- [`tools/process_build_queue_services.py`](../../tools/process_build_queue_services.py)
  - wrapper-compatible service grouping for queue entrypoint helpers
- [`tools/queue_contract.py`](../../tools/queue_contract.py)
  - canonical queue contract constants
  - shared queue dataclasses
  - binding / record / wiki destination type definitions
- [`tools/queue_delivery.py`](../../tools/queue_delivery.py)
  - phase-aware Agent delivery contract: Draft cloud doc, Publish IDML handoff, Web HTML
  - `delivery_kind / delivery_url / delivery_ready` derivation and queue-row serialization
  - strips the retired public `document_link` name while preserving internal binding compatibility
- [`tools/document_link_actions.py`](../../tools/document_link_actions.py)
  - normalized queue action vocabulary
  - legacy `Doc_phase` compatibility mapping
- [`tools/document_link_queue.py`](../../tools/document_link_queue.py)
  - row parsing
  - row filtering
  - record binding
  - queue preflight helpers
- [`tools/queue_bound_binding.py`](../../tools/queue_bound_binding.py)
  - queue preflight and Document_link binding adapters
  - repo entrypoint-facing access to environment-backed binding resolution
- [`tools/queue_bound_records.py`](../../tools/queue_bound_records.py)
  - queue record/action facade adapters
  - repo-root-aware config resolution that forwards the parsed model/region target into grouping and execution
- [`tools/queue_config_resolution.py`](../../tools/queue_config_resolution.py)
  - shared Start Review / Draft / Publish / Preview config resolver
  - exact declared model/region target override plus generic regional fallback
  - queue `Build_family` language-range matching through `build.language_family`, while `build.family_id` remains the internal config identity
  - target-only config exclusion from model-less fallback and fail-closed ambiguity handling
- [`tools/queue_runtime.py`](../../tools/queue_runtime.py)
  - worktree/runtime helpers
  - generated path and review/runtime input helpers, including subprocess-scoped environment overlays
- [`tools/queue_build_execution.py`](../../tools/queue_build_execution.py)
  - queue-triggered `build.py` command assembly
  - phase2 sync-before-build execution
  - worktree-scoped draft/print-publish/Web-Publish build orchestration
  - exact review commit/path provenance injection for versioned print Publish
  - IDML source parity with the earlier print render (`review-asis` for approved-reference targets)
- [`tools/queue_orchestration.py`](../../tools/queue_orchestration.py)
  - top-level queue session flow
  - dry-run vs real-run branch control
  - post-sync pending-state reload
- [`tools/queue_group_processing.py`](../../tools/queue_group_processing.py)
  - per-group queue processing
  - verified-claim acquisition before build/upload side effects
  - started/success/failure writeback orchestration
  - drive/wiki delivery for print tasks and frozen Web metadata handoff for Web Publish
  - delivery-outbox side channel on publish (env-gated, `delivery_outbox=*` row notes)
- [`tools/delivery_outbox.py`](../../tools/delivery_outbox.py)
  - atomic outbox job assembly (`.partial` staging, verify, rename) for the DingTalk hand-off
  - immutable `delivery_manifest.json` with per-file digests and a `delivery_key` idempotency handle
  - the queue's single entry point `drop_publish_delivery_outbox` never raises: outcomes are row status notes
  - `--manifest` CLI for verifying one dropped job by hand
- [`tools/dingtalk_delivery_map.py`](../../tools/dingtalk_delivery_map.py)
  - `(model, region)` to DingTalk 项目代码 / 安规 / 文案语言集合 lookup over `data/dingtalk_delivery_map.csv`
  - `DeliveryTargetNotMapped` (skip) kept distinct from malformed-map `RuntimeError` (fail-closed)
- [`tools/queue_claims.py`](../../tools/queue_claims.py)
  - bounded lease write across every row in a document group
  - no-view readback and exact-token ownership verification before dispatch
- [`tools/queue_dry_run.py`](../../tools/queue_dry_run.py)
  - dry-run preview payload assembly
  - grouped queue preview output formatting
- [`tools/queue_grouping.py`](../../tools/queue_grouping.py)
  - grouped record bucketing rules
  - document-key vs record-id grouping strategy
- [`tools/queue_session.py`](../../tools/queue_session.py)
  - queue-session bootstrap and preflight
  - pending-record fetch/select/group state with active sibling-lease exclusion
  - wiki destination reporting for a processing session
- [`tools/feishu_record_transport.py`](../../tools/feishu_record_transport.py)
  - shared `lark-cli` JSON subprocess boundary for queue, build-listener, spec-master, and schema callers
  - bounded 429 retry/backoff, shared pagination policy, and Feishu response validation
  - existing F6/F8 record transport adapters
- [`tools/spec_master_rebuild.py`](../../tools/spec_master_rebuild.py)
  - spec-master field/record orchestration
  - compatibility wrapper over the shared `lark-cli` base-command transport
- [`tools/bitable_schema.py`](../../tools/bitable_schema.py)
  - tenant schema and reference-row orchestration
  - profile/identity routing and compatibility wrapper over the shared transport
- [`tools/queue_lark_ops.py`](../../tools/queue_lark_ops.py)
  - Drive/Wiki remote I/O helpers and the compatibility wrapper for shared queue transport
- [`tools/queue_bound_lark_ops.py`](../../tools/queue_bound_lark_ops.py)
  - repo-root-aware Lark transport adapters used by queue entrypoints
  - bound CLI upload/node lookup helpers that still allow entrypoint-level patching
- [`tools/queue_outputs.py`](../../tools/queue_outputs.py)
  - separate print-publish and Web-Publish asset staging
  - immutable snapshot/manifest copy-out plus generic release/output path helpers
  - separate print-publish and Web-Publish metadata assembly
- [`tools/queue_bound_outputs.py`](../../tools/queue_bound_outputs.py)
  - repo-root-aware queue output adapters
  - bound output/release helpers that keep `process_build_queue.ROOT` patchable
- [`tools/queue_bound_runtime.py`](../../tools/queue_bound_runtime.py)
  - repo-root-aware command/worktree adapters for queue entrypoints
  - bound `build.py` command builders and worktree helpers that keep entrypoint compatibility names stable
- [`tools/queue_writeback.py`](../../tools/queue_writeback.py)
  - queue result formatting
  - row writeback payload assembly
  - `pending -> running -> success/failed` payload expectations documented in
    [`queue_state_model.md`](queue_state_model.md)
- [`tools/queue_transitions.py`](../../tools/queue_transitions.py)
  - explicit queue transition payload model for running, success, failure, and writeback-failed states
  - queue-claim parsing, expiry checks, and exact-token ownership checks
  - focused test target for queue writeback semantics before live Feishu/Lark transport is involved
- [`tools/publish_branch_assembly.py`](../../tools/publish_branch_assembly.py)
  - validates versioned Web Publish metadata and copies only the frozen MyST source
  - preserves other published targets, rebuilds the aggregate Sphinx source, and writes the SHA-256 inventory
- [`tools/write_web_publish_html_link.py`](../../tools/write_web_publish_html_link.py)
  - derives deterministic Read the Docs routes from Web Publish metadata
  - writes `HTML_link` only for the queue record ids bound to each frozen target

## 6. Cloud-Doc Backport Modules

The cloud-doc backport closed loop (fetch → diff → classify/route → write-back)
was decomposed from a single 4183-line `cloud_doc_backport.py` into focused
layers (debt-paydown, 2026-06). The entry path is unchanged: every
`from tools.cloud_doc_backport import X` and `python3 tools/cloud_doc_backport.py …`
still works because the entry file re-exports all public symbols.

- [`tools/cloud_doc_backport.py`](../../tools/cloud_doc_backport.py)
  - thin entry shim (~200 lines): re-exports every public symbol from the modules
    below + the `__main__` guard. Keep it shim-only.
- [`tools/cloud_doc_backport_model.py`](../../tools/cloud_doc_backport_model.py)
  - foundation: `Block` model, document fetch/normalization, markdown→block
    parsing, section selection. Imports only stdlib + `path_utils` (no cycle).
- [`tools/cloud_doc_backport_util.py`](../../tools/cloud_doc_backport_util.py)
  - shared constants (schema versions) + scaffolding (counters, git-ref,
    timestamp, source-path resolution).
- [`tools/cloud_doc_backport_routing.py`](../../tools/cloud_doc_backport_routing.py)
  - delta classification + routing (Class R / D / T / image / semantic) + `diff_blocks`.
- [`tools/cloud_doc_backport_apply.py`](../../tools/cloud_doc_backport_apply.py)
  - guarded Class-R write-back (literal-first + block-fallback RST rewrite) + apply-report builders.
- [`tools/cloud_doc_backport_render.py`](../../tools/cloud_doc_backport_render.py)
  - markdown report renderers (pure report-dict → markdown).
- [`tools/cloud_doc_backport_transports.py`](../../tools/cloud_doc_backport_transports.py)
  - live Feishu source-table / TM transports + `--table-binding` parsing.
- [`tools/cloud_doc_backport_reports.py`](../../tools/cloud_doc_backport_reports.py)
  - report builders (`build_report` + verify / source-table-suggestions / template-sync-proposal / review-run).
- [`tools/cloud_doc_backport_pr.py`](../../tools/cloud_doc_backport_pr.py)
  - PR/git helpers (`gh` PR creation + 403 compare-url fallback, branch naming, `open_backport_pr_from_manifest`).
- [`tools/cloud_doc_backport_args.py`](../../tools/cloud_doc_backport_args.py)
  - argparse surface + arg-interpretation helpers (`_parse_args`,
    `_value_index_from_args`, `_family_index_from_args`).
- [`tools/cloud_doc_backport_commands.py`](../../tools/cloud_doc_backport_commands.py)
  - single-command runners: `_run_diff` / `_run_apply*` / `_run_review` /
    `_run_verify_review` / `_run_open_pr` / `_run_apply_source_table`.
- [`tools/cloud_doc_backport_orchestration.py`](../../tools/cloud_doc_backport_orchestration.py)
  - multi-step flows: review-branch resolution, worktree sync, the
    render-baseline diff, sibling scope, the backport-PR flow, and the
    best-effort revision-ledger ingest hook
    (`AUTO_MANUAL_REVISION_LEDGER_PATH`; `off` disables). **Patch seams for
    review-branch tests live here**, not on the cli re-exports.
- [`tools/cloud_doc_backport_cli.py`](../../tools/cloud_doc_backport_cli.py)
  - thin dispatcher: `main` + the compatibility re-export hub the facade
    imports from.

Layering (import direction, bottom → top): `model` → `util` → `routing` /
`apply` / `render` / `transports` / `reports` / `pr` → `args` → `commands` /
`orchestration` → `cli` → entry shim. A new extraction must import from the
**leaf modules**, never from the entry file (that would cycle), and the entry
file re-exports it.

Record-resolution + source-table write are in sibling modules:
[`tools/source_record_index.py`](../../tools/source_record_index.py) (the
`source_record_index.json` sidecar: business key → Feishu `record_id`),
[`tools/token_resolution_map.py`](../../tools/token_resolution_map.py) (value →
source_ref), [`tools/source_table_sync.py`](../../tools/source_table_sync.py)
(exact-or-abstain F6 write).

Tests: `tests/test_backport_golden_corpus.py` (routing matrix),
`tests/test_source_table_sync_invariants.py` (F6 write-side fuzz),
`tests/test_backport_harness.py` (+ `tools/backport_harness.py`, offline
multi-edit integration), `tests/test_backport_noise_injection.py`,
`tests/test_backport_live_check.py` (+ `tools/backport_live_check.py`, operator
live round-trip).

Sync-env bootstrap (`sync-data` needs `FEISHU_PHASE2_*` + TM env): copy
[`scripts/hello_docs_binding.env.example`](../../scripts/hello_docs_binding.env.example),
fill values (table/view IDs are discoverable per tenant via `lark-cli base
+table-list` / `+view-list`; a wiki-wrapped base resolves to its app_token via
`lark-cli wiki +node-get`), and check with
[`scripts/validate_required_env.sh`](../../scripts/validate_required_env.sh).

## 7. Source Intake Modules

The source-intake closed loop converts structured specs/manual-source documents
into reviewable source-table candidates, then hands existing-row changes to the
same approval-gated source-table writer used by cloud-doc backport.

- [`tools/source_intake.py`](../../tools/source_intake.py)
  - CLI entrypoint and command orchestration for `run`, `approve`, `apply`, and `verify`.
- [`tools/source_intake_extract.py`](../../tools/source_intake_extract.py)
  - input acquisition and Markdown-table parsing from local Markdown, stdin, or Feishu/Lark cloud-doc text.
- [`tools/source_intake_model.py`](../../tools/source_intake_model.py)
  - candidate schema constants, target-table names, hash helpers, and text normalization.
- [`tools/source_intake_runtime.py`](../../tools/source_intake_runtime.py)
  - candidate extraction, snapshot enrichment, existing-row change-request building, and run/report writing.
- [`tools/source_intake_closure.py`](../../tools/source_intake_closure.py)
  - P4-P7 closure reports: approval artifact, apply handoff report, labeled verification command results, and closure checklist.

The write boundary stays in [`tools/source_table_sync.py`](../../tools/source_table_sync.py):
source intake may approve and invoke it, but does not own live Feishu write
semantics. Live transports are still constructed through
[`tools/cloud_doc_backport_transports.py`](../../tools/cloud_doc_backport_transports.py)
so table-binding parsing and source-table GET/verify behavior stay shared.

Tests: [`tests/test_source_intake.py`](../../tests/test_source_intake.py)
covers candidate extraction, snapshot enrichment, change-request bridging,
approval artifacts, dry-run/live-transport apply behavior, and CLI-level
P4-P7 closure.

## 8. Maintenance Rules

When adding or moving logic in this area:

1. Prefer adding to an existing helper module before expanding an orchestration file.
2. If a new helper module is introduced, update this file in the same change.
3. If a major boundary changes, also update:
   - [`code-as-doc/code_optimization_log.md`](../code_optimization_log.md)
   - [`optimization_project.md`](../optimization_project.md)
4. Keep wrapper names stable in entry files when tests or external scripts patch them directly.
5. If a wrapper stops being needed, remove it only after tests and call sites are updated together.
6. When encoded field names are normalized, prefer unicode-escaped canonical constants in helper modules before deleting old literals from entry files.

## 9. Known Next Decomposition Candidates

These areas still deserve follow-up only when a concrete hotspot reappears:

- [`tools/process_build_queue_services.py`](../../tools/process_build_queue_services.py)
- [`tools/queue_lark_ops.py`](../../tools/queue_lark_ops.py)
- [`tools/gen_index_bundle.py`](../../tools/gen_index_bundle.py)

Keep future extraction notes here once those boundaries stabilize again.
