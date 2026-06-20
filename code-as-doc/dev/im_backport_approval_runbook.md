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
# Translation_Memory writes are gated SEPARATELY (widest blast radius). OFF by default.
export FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOW_TM_WRITE=true
export FEISHU_IM_CLOUD_DOC_BACKPORT_TM_BINDING="<tm_base_token>:<tm_table_id>"
```

The executor also needs the `lark-cli --as bot` plumbing already used by sync-data.
The three write gates are independent: `_ALLOW_SOURCE_WRITE` (Bitable source tables),
`_ALLOW_TM_WRITE` (Translation_Memory). A single `approve` routes each approved
`delta_hash` to its correct target — source edits to the source table, translation
edits to the TM — each only when its own gate is on.

## Underneath: the CLI

The adapter routes `approve`/`reject` to
[`../../tools/cloud_doc_backport.py`](../../tools/cloud_doc_backport.py)
`apply-source-table`. You can run it directly for an out-of-band approval:

```sh
# dry-run plan (no bindings needed):
python tools/cloud_doc_backport.py apply-source-table \
  --report reports/cloud_doc_backport/<run-id>/cloud_doc_backport_source_table_change_request.json \
  --approve <delta_hash>

# live write — source table and/or Translation_Memory (each gated independently):
python tools/cloud_doc_backport.py apply-source-table --report <…> \
  --approve <delta_hash> \
  --write --table-binding "Manual_Copy_Source=<base_token>:<table_id>" \
  --tm-write --tm-binding "<tm_base_token>:<tm_table_id>" --identity bot
```

It writes `cloud_doc_backport_source_table_apply.{json,md}` next to the report (the
JSON carries both the source-table apply and a `translation_apply` section).

## Where each copy edit is written

The change-request `table`/`field` are in the normalized (CSV) namespace
(`Spec_Master` / `Value_<lang>`, `Localized_Copy` / `text_<lang>`). A live binding's
Feishu columns must match that namespace — true for a Spec_Master-shaped sandbox.

- **Source-language copy edit → `Manual_Copy_Source.source_text`.** When the
  reviewed language equals the copy's `Source_lang`, a `Localized_Copy`-origin change
  request is mapped to write the authoring source text (the record id resolves to the
  authoring row via the F6 sidecar redirect). Gated by `--write` +
  `Manual_Copy_Source=<base_token>:<table_id>`.
- **Translation copy edit → `Translation_Memory`.** When the reviewed language is
  not the copy's source language, the edit is a translation; it abstains at the
  source boundary (`resolution_status: translation_abstain`, never written to source)
  and is routed to the TM instead. The executor resolves the TM record by
  `(target-language column, old translation)` — **exact-or-abstain** (0 or >1 match
  abstains) — and writes the new translation into that column, GET-verified and
  idempotent (`already` when the column already holds the new text). Gated by
  `--tm-write` + `--tm-binding`. ⚠️ A TM write is the **widest blast radius**: it
  changes the shared translation for every copy/model using that source sentence on
  the next sync. Translations are still also reported as suggestions in the reply.
- **Spec_Master** is synced from two sub-tables (spec rows + placeholders); a record
  id does not by itself say which sub-table to write. Bind it only to a table whose
  rows the record ids actually belong to.

## Review-branch resolution (where `docs/_review/...` lives)

A target's `docs/_review/<model>/<region>/` tree exists only on its **review
branch** — recorded as `Git_ref` in the Document_link build table (`文档构建表`),
created when the review started — not on the default branch a backport runs from.
A `cloud-doc backport` that runs on the default checkout therefore reports the
`_review` source as "not found".

Map the edited cloud-doc to its review branch with:

```sh
python tools/cloud_doc_backport.py resolve-review-branch \
  --cloud-doc "<feishu cloud-doc URL>" --identity bot
# -> {git_ref, model, region, review_dir: docs/_review/<model>/<region>, pr_url, ...}
```

It matches the cloud-doc by its doc token against the `飞书云文档` column (needs
`FEISHU_PHASE2_BASE_TOKEN` + `FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID`), resolves the
`Git_ref` + `Document_ID` → `docs/_review/<model>/<region>` (the region is the
second `_`-segment; a language segment like `EU_en` does NOT widen it), and abstains
when a cloud-doc maps to more than one distinct branch.

**Resolve by doc name** (for a 副本/copy whose URL is not registered in the build
table): pass the name instead of (or alongside) the URL. The resolver falls back
to matching the doc NAME by **model + region** — e.g. `manual_je1000f_eu_en_0.8 副本`
→ `JE-1000F` / `EU` → its InReview branch. `run-review-branch` takes `--doc-name`
for this (it still fetches the doc via `--cloud-doc`).

### One-shot branch-targeted backport

`run-review-branch` does the whole chain so the bot never has to guess:

```sh
python tools/cloud_doc_backport.py run-review-branch \
  --doc-name "manual_je1000f_eu_en_0.8" --cloud-doc "<feishu cloud-doc URL>" \
  [--page 00_preface.rst] [--write] [--push]   # dry-run unless --write; --push needs --write
```

1. resolves the cloud-doc → review branch (by `--doc-name`, else `--cloud-doc`);
2. ensures a git **worktree** of that `Git_ref` (reuses an existing one, else
   fetch + `git worktree add` under `--worktrees-root`, default `../review-worktrees`).
   The worktree is **sparse by default** — a cone-mode sparse-checkout of only
   `docs/_review/<model>/<region>` (≈1 MB vs ≈250 MB full); pass `--full-checkout`
   for a complete checkout;
3. runs `run-review` against the worktree's `_review` file(s). **With `--page`:** that
   one page. **Without `--page`:** the WHOLE doc is fetched once and diffed against
   every `docs/_review/<model>/<region>/page/*.rst`; only pages whose section is
   actually located in the cloud doc (`section_selection.applied`) are reported as
   changed — pages whose section is absent fall back to a whole-document diff and are
   filtered out as false positives;
4. with `--push`, does **not** commit straight onto the review branch — it puts the
   changed page(s) on a `backport/<review-ref>-<run-id>` sub-branch and opens a
   **draft PR whose base is the review branch**, so the operator verifies before
   anything lands on the review branch (and thus before it flows into the review
   branch's own PR into `main`). The reply prints `backport_pr_url`. Merge that PR
   into the review branch after verifying.

> **Diff baseline (approach C, phased).** Diffing the fetched cloud-doc against the
> RST `page/*.rst` over-reports (RST source vs rendered cloud-doc — see
> [`../architecture/Backport_Rendered_Baseline_Design.md`](../architecture/Backport_Rendered_Baseline_Design.md)).
> The fix is a per-target render baseline.
> - **Phase 1 (shipped):** `run-review-branch --seed --cloud-doc <url> [--doc-name
>   <n>] [--push]` stores the current cloud-doc as the baseline under
>   `docs/_review/<model>/<region>/.backport/` (declares "already reviewed";
>   `--reseed` overwrites). Use it for a review with **no pending edits** (seeding a
>   doc that has un-backported edits would bury them).
> - **Phase 2 (shipped):** once a baseline exists, a whole-doc `run-review-branch`
>   (no `--page`) **automatically** diffs the cloud-doc against that baseline
>   (render-vs-render → only the reviewer's real edits; live: 2 vs 293 on the RST
>   path) and **classifies** them (phase 3): Class D (source value) → `apply-source-table`
>   (F6/TM), Class R (review prose) → the `_review` RST. With `--write` it applies only
>   the **Class R** deltas to the matching `_review` page via the guarded apply (unique,
>   safe matches; ambiguous skipped) — never Class D, never the per-page RST garbage —
>   and `--push` opens a draft PR INTO the review branch. The baseline cursor never
>   advances here (so an un-applied edit is never lost). With `--page`, or no baseline,
>   it falls back to the per-page RST diff.
> - **Copy-doc baseline (shipped, preferred):** the build creates a frozen baseline
>   doc (a second import of the markdown) and records its link in the build table's
>   **`基线文档`** field (editable doc → `飞书云文档`). `run-review-branch` prefers
>   this: it fetches both docs and diffs them (fetch-vs-fetch → clean), ahead of the
>   on-branch `.backport/` file. This is the going-forward baseline source; the
>   `.backport/` + `--seed` path remains as a fallback for docs with no baseline doc.
> - **No-baseline write guard (shipped):** a whole-doc `run-review-branch --write`
>   with **no baseline** is **refused** — that path is the over-reporting
>   per-page RST diff, and writing it splatters rendered text across many RST pages
>   (corrupting `.. raw:: latex` / line-blocks). Seed a baseline first (`--seed`)
>   for a clean diff, or pass `--page <file>` to write one targeted page. A dry-run
>   (no `--write`) report is still allowed.
> - **Direct-CLI RST-source apply guard (shipped):** the legacy `apply-review` /
>   `run-review --write` (which diff/apply the rendered cloud-doc against the
>   `_review` RST *source*) are now **refused** for a review `--write` against an
>   `.rst` baseline and steered to `run-review-branch` — this closes the foot-gun
>   where an improvising agent (no backport plugin) reached for the old command and
>   produced a many-file garbage PR. The dry-run still works for inspection. The IM
>   adapter and a deliberate single-page override pass `--allow-rst-baseline` to opt
>   past it; the blessed path remains `run-review-branch` (render-vs-render).

### Capturing R0 so a new review backports cleanly

A clean backport needs a render baseline (R0). Capture it **right after the build
creates the cloud doc, before anyone edits it** — at that moment the fetch is the
pristine render:

```sh
python3 tools/cloud_doc_backport.py run-review-branch --seed --push \
  --doc-name "<doc name>" --cloud-doc "<feishu cloud-doc URL>" --identity bot
```

Then, as the reviewer edits the cloud doc, `run-review-branch` (whole-doc, no
`--page`) automatically diffs against R0 and reports **only their real edits**
(phase 2), instead of the per-page RST garbage.

> ⚠️ Only seed an **edit-free** doc. Seeding a doc that already has un-backported
> edits declares them "already reviewed" (buries them). A review that started before
> R0 capture (e.g. one already edited) has no clean bootstrap — handle those edits
> directly at the source.
>
> Auto-running this `--seed` from the build pipeline (so no manual step is needed) is
> the planned **phase 4**; it is a build-path change and is not wired in yet.

**Template guard:** the source path is *derived* from the resolved
`docs/_review/<model>/<region>` + `--page` — never an arbitrary path — and is
hard-refused if it would resolve to `docs/templates/` or `docs/_build/`. So a
backport can only ever write the review derivative, not the shared template (the
failure mode where the bot guessed `docs/templates/page_eu/00_preface.rst`).

### Pre-create worktrees for every active review

```sh
python tools/cloud_doc_backport.py sync-review-worktrees   # one worktree per InReview Git_ref
```

Run this after reviews start so every InReview target's `docs/_review/...` tree is
already on disk for the bot to edit.

## References

- Design: [`../architecture/Feishu_Cloud_Doc_Backport_Design.md`](../architecture/Feishu_Cloud_Doc_Backport_Design.md) §5.1 R9
- Live-activation checklist: [`backport_live_activation_checklist.md`](backport_live_activation_checklist.md) Step 2
- Executor: [`../../tools/source_table_sync.py`](../../tools/source_table_sync.py),
  [`../../tools/feishu_record_transport.py`](../../tools/feishu_record_transport.py)
- Adapter: [`../../integrations/openclaw/feishu-im-webhook-adapter/`](../../integrations/openclaw/feishu-im-webhook-adapter/)
