# Backport Live-Activation Checklist (F6 / F8)

Status: operator checklist · Owner: 夏冰 · Created: 2026-06-19

Milestone F (F1–F8) is implemented in-repo. **F1–F5 and F7 are fully live.**
**F6** (approval-gated source-table writes) and **F8** (`QC_Report` writeback) are
implemented to the **dry-run / fixture boundary** — every gate, plan, and report
works without network, but the actual Feishu writes are intentionally not wired.

This checklist activates those live writes. They touch the **source of truth**
(Feishu Bitable) and create a Feishu table, so they are **operator-gated** and
must be done by 夏冰 (or an authorized operator), not by an agent.

Read alongside:

- rules and gates: [`../architecture/Feishu_Cloud_Doc_Backport_Design.md`](../architecture/Feishu_Cloud_Doc_Backport_Design.md) §5.1 (R9)
- the human template-sync role: [`template_sync_runbook.md`](template_sync_runbook.md)
- QC plan M4: [`closed_loop_qc_implementation_plan.md`](closed_loop_qc_implementation_plan.md)

## Safety invariants (never break these)

- **Human approval is mandatory** for any Bitable content write (R9). An agent may
  propose and execute, but **never approve**.
- **Exact-or-abstain.** Never guess a `record_id`; a request without an exact match
  is skipped.
- **Content fields only.** Table schema changes are separate, explicit operator
  actions.
- **One writer per layer.** backport writes only `docs/_review/...`; the
  template-sync role writes only `docs/templates/...`; the source-table-sync role
  writes only Bitable content. Do not cross these.

## Prerequisites

- `lark-cli` configured with the bot identity (`--as bot`) and Feishu app
  permissions for the target base/tables.
- An operator allowlist for IM approvals (the senders allowed to approve writes).
- A review-doc backport run has produced its reports (from
  `python tools/cloud_doc_backport.py run-review ... --data-root data/phase2 --lang <lang> --sibling <...>`),
  including `cloud_doc_backport_source_table_change_request.json` (F6) and a
  `findings.json` from `content_lint` (F8).

---

## Step 1 — Populate the `record_id` sidecar (enables F6 resolution)

**Why:** F6 can only write an exact row when the finding resolves to a live
`record_id`. The sidecar provides that mapping; it is emitted by `sync-data`
(F1), but only a **live** sync populates it.

**Do:**

1. Run a live snapshot sync:
   `python build.py sync-data --config configs/config.<family>.yaml --model <MODEL> --region <REGION>`
2. Confirm `data/phase2/source_record_index.json` is written and listed under the
   snapshot manifest `derived_files`.

**Verify:** the sidecar's `tables.<table>.records` is non-empty for indexed
tables. `python tools/content_lint.py --data-root data/phase2 --json` now shows
`resolution_status: resolved` (not `snapshot_only`) for covered findings.

**Gate:** operator-gated (live Feishu read + `data/phase2` contract, `AGENTS.md`
§8.7).

---

## Step 2 — Activate F6 (approval-gated source-table write)

**Why:** apply reviewer-confirmed Class D (data-origin) changes to Bitable content,
human-approved, exact-or-abstain.

**Do:** the transport (`SourceTableLarkTransport` in
[`../../tools/feishu_record_transport.py`](../../tools/feishu_record_transport.py))
and the executor are built; the CLI entrypoint is **`cloud_doc_backport.py
apply-source-table`** (and the Feishu IM `approve`/`reject` commands route to it —
see [`im_backport_approval_runbook.md`](im_backport_approval_runbook.md)):

```
# dry-run plan (default; no writes, no bindings needed):
python tools/cloud_doc_backport.py apply-source-table \
  --report reports/cloud_doc_backport/<run-id>/cloud_doc_backport_source_table_change_request.json \
  --approve <delta_hash> [--approve <delta_hash> ...]

# live write (operator-deliberate): one --table-binding per writable table:
python tools/cloud_doc_backport.py apply-source-table --report <…> \
  --approve <delta_hash> --write \
  --table-binding "Manual_Copy_Source=<base_token>:<table_id>" --identity bot
```

1. **Human approval is mandatory; the agent never approves.** Only the
   `--approve`d `delta_hash`es are eligible; everything else is skipped.
2. **Per-table bindings are explicit.** `--write` requires a `--table-binding
   TABLE=BASE:TABLE_ID` for each change-request table you intend to write; an
   unmapped table (e.g. the derived `Localized_Copy`) is isolated per-request as
   `error` and skipped — never mis-written. ⚠️ The change-request `table`/`field`
   are in the normalized (CSV) namespace; a binding's Feishu columns must match
   (true for a Spec_Master-shaped sandbox). Copy write-back field mapping
   (`text_<lang>` → authoring `source_text`, source-lang vs TM routing) is a
   **follow-up** — copy-origin requests currently abstain at the write boundary.
3. The executor applies **only** approved **and** resolved requests, GET-verifies
   each write, isolates per-request failures, and is idempotent by `delta_hash`.

**Verify:** dry-run shows the expected `apply`/`skip` plan; with `--write`, the
apply report's `summary.written` matches and `verify_failed`/`error` are 0;
re-running the same approved set is a no-op (idempotent); unresolved or unapproved
requests are skipped.

**Gate:** writes Bitable content (source of truth, widest blast radius) — the
human-approval and exact-or-abstain invariants above are hard requirements.

---

## Step 3 — Activate F8 (`QC_Report` writeback)

**Why:** record `content_lint` findings in a Feishu `QC_Report` table for triage,
idempotent by `finding_hash`, without touching content rows.

**Do:**

1. **Create the `QC_Report` Feishu table** (a **schema** change → operator-gated)
   with columns matching the row contract: `run_id`, `finding_hash`, `severity`,
   `rule`, `source_ref`, `record_id`, `resolution_status`, `suggested_action`.
2. **Implement a `lark-cli` transport** for the `qc_report._Transport` protocol in
   [`../../tools/qc_report.py`](../../tools/qc_report.py):
   - `append_row(*, row)` → appends a row, returns its `record_id`;
   - `list_finding_hashes()` → existing `finding_hash` values (for idempotency).
3. **Run the writer:**
   `upsert_qc_report(build_qc_report_rows(load_findings("findings.json")), transport=<lark transport>, write=True)`.

**Verify:** new findings appear as rows; re-running is a no-op (idempotent by
`finding_hash`); per-content-row QC status fields are untouched.

**Gate:** creating the table is a schema change (operator-gated); writes are
append/upsert only.

---

## Step 4 — Extend the F1 sidecar coverage — DONE (raised F6 resolution rate)

**Why:** F1 originally indexed `lcd_icons` only, while F2's Class D `source_ref`s are
mostly `Spec_Master` / `Localized_Copy` — so F6 requests abstained
(`record_id: null`) for those. Coverage is now extended in
[`../../tools/source_record_index.py`](../../tools/source_record_index.py):

1. **`Spec_Master`** (#397): keyed by `document_key` + `Row_key` + `Slot_key`
   (`Slot_key` disambiguates the `usb_c` 30w/100w collision class).
2. **`Manual_Copy_Source`** (this is where a copy value is written back —
   operator decision: the source-of-truth is the **authoring** table, not the
   `Localized_Copy` rendered derivative). Keyed by `copy_key`, indexing only
   `Is_Latest` rows so historical versions never shadow the current row. The
   `Localized_Copy`-origin `source_ref` that F2 emits is resolved against the
   `Manual_Copy_Source` index via `TABLE_RESOLUTION`'s index-table redirect.

Genuine duplicate keys still abstain (exact-or-abstain), so resolution is never a
guess.

**Verify (live, env-gated):** run `sync-data` with the populated phase2 env, then
check `source_record_index.json` has non-empty `Spec_Master` / `Manual_Copy_Source`
`records`; F6 change requests for those tables resolve to a `record_id` instead of
abstaining. The verification needs the operator's `FEISHU_PHASE2_*` /
`FEISHU_TRANSLATION_MEMORY_BASE_TOKEN` values — a checkout without them (and without
a local `data/phase2/` snapshot) cannot exercise this path.

---

## Definition of done (go-live)

- The sidecar is populated by a live `sync-data`.
- F6 applies one **approved** change to Bitable, GET-verifies it, and re-running is
  idempotent; unapproved/unresolved are skipped.
- F8 appends a finding to the `QC_Report` table, idempotent by `finding_hash`.
- Every write was human-gated; the agent never approved anything.

## References

- Modules: [`../../tools/source_record_index.py`](../../tools/source_record_index.py),
  [`../../tools/source_table_sync.py`](../../tools/source_table_sync.py),
  [`../../tools/qc_report.py`](../../tools/qc_report.py)
- Workstream Q / roadmap: [`../optimization_project.md`](../optimization_project.md)
- PR-level history: [`next_optimization_checklist.md`](../next_optimization_checklist.md) Milestone F
