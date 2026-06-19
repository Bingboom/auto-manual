# Feishu IM Source-Table Approval Runbook (F6)

How an authorized operator approves or rejects **F6 source-table writes** (writing
reviewer-confirmed Class D values back to Feishu Bitable) from a Feishu IM message,
and how that routes to the executor.

This is the highest-stakes write in the backport system — Bitable is the source of
truth, the blast radius is every target sharing the row, and there is **no git
revert**. Every safety gate below is intentional.

## What this covers vs. what it does not

- **Covers:** approving/rejecting the `source_table_change_request`s a backport run
  produced, and applying the approved ones to Bitable.
- **Does NOT cover:** the `docs/_review` + draft-PR flow — that is the separate
  `cloud-doc backport` / `backport-pr` IM commands (gated by
  `FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOW_WRITE` / `_ALLOW_PR_CREATE`). Source-table
  writes are gated **separately** by `_ALLOW_SOURCE_WRITE` so enabling review
  writes never silently enables Bitable writes.

## The IM commands

Sent in a thread the adapter watches, from a sender in
`FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOWED_SENDERS`:

```
cloud-doc approve <run-id> <delta_hash> [<delta_hash> …]
cloud-doc reject  <run-id> <delta_hash> [<delta_hash> …]
```

- `<run-id>` — the backport run that produced the change requests (the adapter's
  earlier backport reply prints it; reports live under
  `reports/cloud_doc_backport/<run-id>/`).
- `<delta_hash>` — the full sha256 `delta_hash` of each change request you approve.
  Copy them from `cloud_doc_backport_source_table_change_request.json` (or the
  run's source-table report). **Only the hashes you list are eligible** — the
  agent never approves on your behalf.

`reject` is audit-only: it records the rejection and writes nothing.

## Safety model (all enforced)

1. **Sender allowlist** — non-allowlisted senders are refused.
2. **Human approval is mandatory** — `apply_change_requests` skips any request whose
   `delta_hash` is not in the approved set; the agent may propose/execute, never
   approve.
3. **Source-write defaults OFF** — with `FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOW_SOURCE_WRITE`
   unset/false, an `approve` runs a **dry-run** and replies with the plan; nothing
   is written. Flip it to `true` only when you intend live writes.
4. **Exact-or-abstain** — a request without an exact resolved `record_id` is skipped.
5. **Per-table bindings are explicit** — live writes need
   `FEISHU_IM_CLOUD_DOC_BACKPORT_SOURCE_TABLE_BINDINGS` (comma-separated
   `TABLE=BASE_TOKEN:TABLE_ID`); an unmapped change-request table is isolated as
   `error` and skipped, never mis-written.
6. **GET-verify + idempotent** — each write is read back and confirmed; re-running
   the same approved set is a no-op (idempotent by `delta_hash`).
7. **Audit log** — every approve/reject appends a line to
   `FEISHU_IM_CLOUD_DOC_BACKPORT_APPROVAL_LOG` (default
   `reports/cloud_doc_backport/approval_audit.jsonl`): approver, timestamp,
   decision, run-id, hashes, and result summary.

## Operator setup

In the environment where the adapter runs:

```sh
# who may approve (comma-separated Feishu open_ids); reused from the review flow
export FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOWED_SENDERS="ou_xxx"
# OFF by default — set true ONLY when you want live Bitable writes
export FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOW_SOURCE_WRITE=true
# one entry per writable change-request table
export FEISHU_IM_CLOUD_DOC_BACKPORT_SOURCE_TABLE_BINDINGS="Manual_Copy_Source=<base_token>:<table_id>"
```

The executor also needs the `lark-cli --as bot` plumbing already used by sync-data.

## Underneath: the CLI

The adapter routes `approve`/`reject` to
[`../../tools/cloud_doc_backport.py`](../../tools/cloud_doc_backport.py)
`apply-source-table`. You can run it directly for an out-of-band approval:

```sh
# dry-run plan (no bindings needed):
python tools/cloud_doc_backport.py apply-source-table \
  --report reports/cloud_doc_backport/<run-id>/cloud_doc_backport_source_table_change_request.json \
  --approve <delta_hash>

# live write:
python tools/cloud_doc_backport.py apply-source-table --report <…> \
  --approve <delta_hash> --write \
  --table-binding "Manual_Copy_Source=<base_token>:<table_id>" --identity bot
```

It writes `cloud_doc_backport_source_table_apply.{json,md}` next to the report.

## Copy write-back (source-language only) and remaining gaps

The change-request `table`/`field` are in the normalized (CSV) namespace
(`Spec_Master` / `Value_<lang>`, `Localized_Copy` / `text_<lang>`). A live binding's
Feishu columns must match that namespace — true for a Spec_Master-shaped sandbox.

- **Copy write-back is supported for source-language edits.** When the reviewed
  language equals the copy's `Source_lang`, a `Localized_Copy`-origin change request
  is mapped to write the authoring **`Manual_Copy_Source.source_text`** (the record
  id resolves to the authoring row via the F6 sidecar redirect). Bind it with
  `Manual_Copy_Source=<base_token>:<table_id>`.
- **Translation copy edits abstain.** When the reviewed language is not the copy's
  source language, the correction's home is the `Translation_Memory`, which is out
  of F6 scope — the request abstains at the write boundary
  (`resolution_status: translation_abstain`) and is never written. Routing
  translation edits to the TM is a future follow-up.
- **Spec_Master** is synced from two sub-tables (spec rows + placeholders); a record
  id does not by itself say which sub-table to write. Bind it only to a table whose
  rows the record ids actually belong to.

## References

- Design: [`../architecture/Feishu_Cloud_Doc_Backport_Design.md`](../architecture/Feishu_Cloud_Doc_Backport_Design.md) §5.1 R9
- Live-activation checklist: [`backport_live_activation_checklist.md`](backport_live_activation_checklist.md) Step 2
- Executor: [`../../tools/source_table_sync.py`](../../tools/source_table_sync.py),
  [`../../tools/feishu_record_transport.py`](../../tools/feishu_record_transport.py)
- Adapter: [`../../integrations/openclaw/feishu-im-webhook-adapter/`](../../integrations/openclaw/feishu-im-webhook-adapter/)
