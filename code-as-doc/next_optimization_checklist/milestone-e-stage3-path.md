# Optimization checklist: Milestone E (Stage-3 path)

Part of the [optimization checklist](../next_optimization_checklist.md); its index lists every milestone page,
and its §1 update rules apply here. Update item status on this page and add new
items for this milestone here, not to the hub.

## 6b. Milestone E: Stage-3 Path — Lock Stage 2 + Safe Prose Cut

Milestone status: `pending`
Milestone target: `next wave`
Milestone note: this is the active wave for the path to Stage 3 — the
deliberate-hybrid end state. E1+E2 lock Stage 2 traceability; E3+E4 take the safe
first cut into prose without moving body prose. E4 (page_registry authority) is
the main lever for eliminating template forks, which is the real Stage 3 win and
is independent of structuralizing prose bodies. What gets structured vs
deliberately kept in templates/config follows the content-truth allocation rule
(§3.1) in [`architecture/Long_Form_Content_Block_Design.md`](../architecture/Long_Form_Content_Block_Design.md).
The long-form prose assembly re-launch (Workstream N) stays out of this milestone,
gated on the same design.

- [ ] PR E1: Freeze release snapshots (Workstream J)
  - Status: `in_progress` — E1-PR1 freeze/binding implemented; E1-PR2 rebuild-equivalence proof remains
  - Target files:
    - [`../tools/release_manifest.py`](../../tools/release_manifest.py)
    - [`../tools/utils/path_utils.py`](../../tools/utils/path_utils.py)
    - [`../tools/sync_data.py`](../../tools/data/sync_data.py)
  - Done when:
    - a timestamped snapshot (source revision, exported files, target matrix) is archived at release time
    - `release-manifest` binds to that frozen snapshot through `path_utils`, not a re-pulled live snapshot
    - rebuilding from the archived snapshot reproduces the release output
  - E1-PR1 note (2026-07-31): versioned Publish archives exported data and attachments under the approved `versions/<version>/snapshot/` lifetime-retained path, writes an immutable identity, binds JSON/CSV manifests to it, and carries the archive out of temporary queue worktrees. Same-version rebinding and archive drift fail closed.

- [ ] PR E2: QC closed-loop tail — sync-time `record_id` sidecar (Workstream I)
  - Status: `pending`
  - Note: touches `sync-data` and the phase2 source contract → operator-gated per `AGENTS.md` §8.7
  - Target files:
    - [`../tools/sync_data.py`](../../tools/data/sync_data.py)
    - [`../tools/content_lint.py`](../../tools/content_lint.py)
    - [`dev/closed_loop_qc_implementation_plan.md`](../dev/closed_loop_qc_implementation_plan.md)
  - Done when:
    - `sync-data` emits a `source_record_index` sidecar without adding `record_id` columns to existing CSV contracts
    - `content_lint` findings resolve to an exact live `record_id` or abstain (`unresolved`/`ambiguous`)
    - the optional Feishu `QC_Report` writer stays dry-run/operator-gated

- [ ] PR E3: Extend short-copy to operation-guide and app-setup chrome (Workstream L)
  - Status: `pending`
  - Target files:
    - [`dev/content_block_migration_assessment.md`](../dev/content_block_migration_assessment.md)
    - [`../tools/check_docs_generated.py`](../../tools/check/docs_generated.py)
  - Done when:
    - operation-guide and app-setup section headings, button/UI labels, table labels, and image alt text resolve from `Manual_Copy_Source` via `{{ copy:<copy_key> }}`
    - missing copy keys fail in `build.py check`
    - no body prose is moved, and app-market/support/manufacturer/URL text is routed to config, not the copy table

- [ ] PR E4: Make `page_registry` the single composition authority (Workstream M)
  - Status: `pending`
  - Note: touches the phase2 source contract → operator-gated per `AGENTS.md` §8.7
  - Target files:
    - [`../tools/check_docs_generated.py`](../../tools/check/docs_generated.py)
    - [`../tools/gen_index_bundle.py`](../../tools/gen_index_bundle.py)
  - Done when:
    - every shipped page (including prose pages) is declared in `page_registry` with explicit applicability (`sku_scope`, `langs`, region/model)
    - page composition and applicability are read from data, not inferred from per-language folder layout
    - RST rendering output is unchanged for prose pages (fallback path preserved)
