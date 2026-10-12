# Optimization checklist: Milestone F (backport reverse-sync and QC writeback)

Part of the [optimization checklist](../next_optimization_checklist.md); its index lists every milestone page,
and its §1 update rules apply here. Update item status on this page and add new
items for this milestone here, not to the hub.

## 6d. Milestone F: Backport Reverse-Sync & QC Writeback Enablement

Milestone status: `pending`
Milestone target: `after the Milestone E baseline`
Milestone note: PR-level breakdown of Workstream I's remaining tail (the
`record_id` sidecar + QC report writeback) and Workstream Q (backport
layer-routing, template-sync, and approval-gated source-table writes). The rules
are already codified in
[`architecture/Feishu_Cloud_Doc_Backport_Design.md`](../architecture/Feishu_Cloud_Doc_Backport_Design.md)
§5.1. Suggested order: F1 → (F2, F3) → F4 → F5 → F6 → F7; F8 may run in parallel
once F1 lands. **F1 is the shared prerequisite for F6 and F8.** Items touching
`sync-data`, `data/phase2` contracts, `build.py` behavior, or Feishu schema are
operator-gated (`AGENTS.md` §8.7). **Status: F1–F8 all merged.** F6/F8 are at the
dry-run boundary; live activation is the operator's, per
[`dev/backport_live_activation_checklist.md`](../dev/backport_live_activation_checklist.md).

- [x] PR F1: Sync-time `record_id` sidecar (Workstream I — shared prerequisite)
  - Status: `done`
  - Note: touches `sync-data` + the phase2 contract → operator-gated; this is the detailed form of Milestone E PR E2. Delivered by `tools/source_record_index.py` (builder/resolver, exact-or-abstain), the `sync_data_runtime` sidecar emission, and `content_lint` resolution (lcd_icons indexed; coverage expands in follow-ups). Live population needs an operator `sync-data`; logic is covered by `tests/test_source_record_index.py`. **Correctness fix:** `normalize_records` sorts rows, so pairing the *sorted* normalized list with the *unsorted* raw records mapped each business key to the WRONG `record_id` (live-verified: a `JE-1000F_CN/dc12_port` key resolved to a `JE-1000F_US/dc8020` row, across the two-table `Spec_Master` merge). Now each row's source `record_id` is threaded onto it (`SOURCE_RECORD_ID_KEY`) so it survives the sort; `collect_index_rows` reads it (positional fallback only for legacy/no-id rows).
  - Target files:
    - [`../tools/sync_data.py`](../../tools/data/sync_data.py)
    - [`../tools/content_lint.py`](../../tools/content_lint.py)
    - `data/phase2/source_record_index.json` (new derived sidecar)
    - [`dev/closed_loop_qc_implementation_plan.md`](../dev/closed_loop_qc_implementation_plan.md)
  - Done when:
    - `sync-data` emits a `source_record_index` sidecar mapping source keys to live `record_id`s, without adding `record_id` columns to existing CSV contracts
    - resolution is exact-or-abstain: zero or multiple matches yield `record_id: null` plus `resolution_status: unresolved`/`ambiguous`
    - `content_lint` and backport can resolve an exact `record_id` from the sidecar
    - the sidecar is listed under manifest `derived_files` and is reproducible from a snapshot

- [x] PR F2: Build-time token/copy resolution map (Workstream Q — Class `D` detection)
  - Status: `done`
  - Note: implemented as a snapshot-based value index (`tools/token_resolution_map.py`: `build_value_index` over `Spec_Master`/`Localized_Copy` per-lang columns + `classify_data_origin`), wired into `cloud_doc_backport` `_classify_route`/`diff_blocks` behind `--lang`/`--data-root` so a reviewer span that resolves to a data value is classified Class `D` (`source_table_suggestion`) with its `source_ref` — no build-engine change needed. `classify_data_origin` matches the whole normalized span **and** each table cell / `<br/>`-joined sub-value, so a real cloud-doc delta (a whole table ROW like `\| 12V⎓最大10A <br/> … \| label \|`, not a bare cell) resolves to its source row deterministically. When an index is present it is **authoritative**: a non-matching prose delta routes to `repo_review_text` instead of the `_looks_data_like` guess (which over-flagged unit/number-bearing prose as Class D); table rows stay Class `D` structurally. A value that maps to **more than one source row** (e.g. a port's `front.label` and `front.spec` both holding `12V⎓最大10A`) is marked `ambiguous` by `build_value_index` and **abstains** (no `source_ref`) — it never auto-resolves the arbitrary first slot, so `apply-source-table` skips it and a human picks the slot (live incident: it had written the wrong `front.spec`). Behavior preserved when no value index is supplied. Tests in `tests/test_token_resolution_map.py`.
  - Target files:
    - [`../tools/draft_engine.py`](../../tools/draft_engine.py)
    - [`../tools/gen_index_bundle.py`](../../tools/gen_index_bundle.py)
    - [`../tools/cloud_doc_backport.py`](../../tools/backport/cloud_doc.py)
  - Done when:
    - the build emits a per-target map of resolved token / copy / csv values back to their source key (the lightweight provenance of §5.1 R8)
    - backport uses it to classify a delta as Class `D` (data-origin) instead of guessing
    - a data-origin delta is never routed to `docs/_review/...` or a template

- [x] PR F3: Family-identical classification (Workstream Q — `R` vs `T` plus scope)
  - Status: `done`
  - Note: `tools/family_scope.py` (`build_family_index` over sibling sources + `classify_family_scope`) wired into `cloud_doc_backport` alongside the F2 value index. A review-doc prose span identical across the family is routed `needs_human_mapping` with its blast radius (`family_scope.targets`) — the §5.1 R5 intentional-divergence gate — instead of auto-routing; target-local spans stay `repo_review_text`. Explicit siblings via repeatable `--sibling`; **`run-review-branch` now auto-resolves the `page_shared/<lang>` shared templates as siblings** so the blessed path fires Class T with no manual flags (`--no-auto-sibling` disables; single-region `ja`/`zh` have no shared surface). Tests in `tests/test_family_scope.py`, `tests/test_cloud_doc_backport.py::RunReviewBranchFamilyScopeTests`.
  - Target files:
    - [`../tools/cloud_doc_backport.py`](../../tools/backport/cloud_doc.py)
    - [`../.agents/skills/manual-revision-backport/scripts/scan_residuals.py`](../../.agents/skills/manual-revision-backport/scripts/scan_residuals.py)
  - Done when:
    - backport derives `R` (target-local) vs `T` (shared) from whether the span is identical across the family, reusing the residual scanner
    - the sibling / blast-radius scope of a `T` or `D` delta is computed, not guessed
    - template-origin spans changed by the reviewer are flagged `needs_decision` (the §5.1 R5 intentional-divergence gate), not auto-classified

- [x] PR F4: Emit `template_sync_proposal` for Class `T` (Workstream Q)
  - Status: `done`
  - Note: `cloud_doc_backport` now emits `cloud_doc_backport_template_sync_proposal.json/.md` (report-only, `external_write=false`) from `verify-review`, `run-review`, and the blessed `run-review-branch` baseline path, one entry per Class `T` (shared-across-family) delta with the §5.1 R4 contract: target templates (family scope), old→new, evidence, delta hash, and the post-apply rebuild+sync-review step. Backport still writes only Class `R` to `docs/_review/...`; Class `T` is never written there. Tests in `tests/test_template_sync_proposal.py`.
  - Target files:
    - [`../tools/cloud_doc_backport.py`](../../tools/backport/cloud_doc.py)
    - [`architecture/Feishu_Cloud_Doc_Backport_Design.md`](../architecture/Feishu_Cloud_Doc_Backport_Design.md)
  - Done when:
    - a review-backport run emits `template_sync_proposal.json/.md` for Class `T` deltas with the §5.1 R4 contract (target template(s), family scope, old→new, evidence, post-apply rebuild step, delta hash)
    - backport still writes only Class `R` to `docs/_review/...`; it never writes templates
    - Class `T` deltas are not written to `_review` (strict)

- [x] PR F5: `rebuild + rediff` idempotency gate (Workstream Q — §5.1 R7)
  - Status: `done`
  - Note: `_rebuild_rediff_gate` re-diffs the baseline against the edited source and asserts the only changes are the intended `repo_review_text` deltas (no collateral `unexpected`, none `missing`); `build_review_verify_report` attaches the result and `build_review_run_report` requires it for `PR_READY` (verify PASS **and** gate pass). It runs against a distinct baseline snapshot, and now also against an **in-memory pre-edit baseline** — `run-review` passes the source it read before applying in place, so the prior in-place skip is closed. It is also wired into the blessed **`run-review-branch` baseline path**: each changed page's source pre→post diff must equal exactly the Class R deltas applied to it, else the seed-cursor advance **and** the PR push are blocked and the run exits non-zero. Tests in `tests/test_rebuild_rediff_gate.py`, `tests/test_cloud_doc_backport.py::RebuildRediffBlessedGateTests`.
  - Target files:
    - [`../tools/cloud_doc_backport.py`](../../tools/backport/cloud_doc.py)
  - Done when:
    - `verify-review` is extended to rebuild from edited sources and re-diff against the accepted doc
    - the gate passes only when residuals are zero AND no diff appears outside the intended spans (recorded intentional overrides excepted)
    - a `PR_READY` review run requires the gate to pass

- [x] PR F6: Approval-gated source-table-sync (Workstream Q — §5.1 R9; depends on F1)
  - Status: `done` (to the dry-run/fixture boundary; live activation operator-gated)
  - Note: `tools/source_table_sync.py` — `build_change_requests` turns Class D deltas into change requests (record_id resolved via the F1 sidecar, exact-or-abstain); `plan_apply`/`apply_change_requests` enforce the R9 gates (human approval required, exact-or-abstain skip, content-field only, delta-hash idempotency, GET-verify-after-write) with an injected transport — dry-run by default. The request carries the precise `old_value`/`new_value`: for a table-ROW delta the **changed cell** value is extracted (e.g. `IN1 (DC 12V点烟口)`) so the write targets the cell field, not the whole row markup; `plan_apply` writes `new_value` and abstains when the cell can't be aligned (a row-vs-row write would corrupt the cell). Each live write **GET-checks the cell first** (drift guard): idempotent-skip (`already_applied`) if it already holds the new value, **abstain** (`drift_abstained`) if it holds neither the expected `old_value` nor the new value (never clobber an externally-changed/stale cell), else upsert + GET-verify-after. `run-review` now emits `cloud_doc_backport_source_table_change_request.json`. **Operator follow-up (live):** wire `lark-cli --as bot` as the transport and a populated `record_id` sidecar; the operator approves by deliberately running `apply-source-table --write` (the cloud-doc-backport IM trigger was removed 2026-06-21, #453 — backport is CLI-only). An agent may propose/execute but never approve. Tests in `tests/test_source_table_sync.py`.
  - Target files:
    - [`../tools/cloud_doc_backport.py`](../../tools/backport/cloud_doc.py)
    - `tools/source_table_sync.py` (new executor)
  - Done when:
    - backport emits a `source_table_change_request` for Class `D` deltas (table, exact `record_id` from F1, field, old→new, scope, blast radius, evidence, delta hash)
    - a human approves by deliberately running `apply-source-table --write` with explicit `--table-binding`s; an agent may propose/execute but never approve
    - the executor applies only approved requests via `lark-cli --as bot`, with GET-verify-after-write and delta-hash idempotency; ambiguous/duplicate matches abstain
    - content fields only; table schema stays a separate operator-gated action; the change-request plus approval log is retained as the audit trail

- [x] PR F7: Template-sync operator runbook (Workstream Q)
  - Status: `done`
  - Note: added [`dev/template_sync_runbook.md`](../dev/template_sync_runbook.md) — the operator procedure to consume a `template_sync_proposal` (F4) and apply Class T changes to `docs/templates/...` via a normal PR, passing the F5 rebuild+rediff gate; with the R6 boundaries (templates-only, untrusted input, no self-merge) and the dedicated agent kept as an explicit deferred follow-up. Cross-referenced from `Feishu_Cloud_Doc_Backport_Design.md` §5.1 R6.
  - Target files:
    - `dev/template_sync_runbook.md` (new)
    - [`../user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md)
  - Done when:
    - a documented operator procedure consumes a `template_sync_proposal` and applies it to `docs/templates/...` via a normal PR, passing the F5 gate
    - the dedicated template-sync agent remains an explicit, deferred follow-up

- [x] PR F8: Feishu `QC_Report` table writeback (Workstream I — M4; depends on F1)
  - Status: `done` (to the dry-run/fixture boundary; table creation + live write operator-gated)
  - Note: `tools/qc_report.py` — `build_qc_report_rows` maps `content_lint` findings to QC_Report rows (run_id, finding_hash, severity, rule, source_ref, resolved record_id, suggested_action); `upsert_qc_report` is idempotent by `finding_hash`, dry-run by default, with a transport-injected live path that skips finding hashes already in the table. **Operator follow-up (live):** create the `QC_Report` Feishu table (schema) and wire a `lark-cli --as bot` transport. Content-row QC status fields stay out of scope. Tests in `tests/test_qc_report.py`.
  - Target files:
    - [`dev/external_table_contracts.md`](../dev/external_table_contracts.md)
    - [`../tools/content_lint.py`](../../tools/content_lint.py)
  - Done when:
    - `content_lint` findings can be appended/upserted to a `QC_Report` table in dry-run and live modes, idempotent by `finding_hash`
    - rows carry `run_id`, `finding_hash`, severity, rule, source ref, resolved `record_id` (from F1) when available, and suggested action
    - content-row QC status fields stay out of scope
