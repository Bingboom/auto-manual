# Template-Sync Operator Runbook

Status: runbook · Owner: 夏冰 · Created: 2026-06-19 · Milestone F PR F7

This is the operator procedure for the **template-sync role** in the backport
reverse-sync (see [`../architecture/Feishu_Cloud_Doc_Backport_Design.md`](../architecture/Feishu_Cloud_Doc_Backport_Design.md)
§5.1 R6). It consumes a `template_sync_proposal` produced by a review-doc
backport run (F4) and applies the shared-template changes to `docs/templates/...`
through a normal PR.

The role is **operator-run today**; a dedicated agent is an explicit, deferred
follow-up (it would follow this same contract).

## 1. When to use this

A review-doc backport run (`cloud_doc_backport.py run-review` / `verify-review`)
emitted `cloud_doc_backport_template_sync_proposal.json` / `.md` with one or more
entries. Each entry is a **Class T** delta — a reviewer change to prose that is
**identical across the family** (F3), so it should change the shared template, not
just one target's `docs/_review/...`.

If the proposal is empty, there is nothing to do here.

## 2. Inputs

- `cloud_doc_backport_template_sync_proposal.json` (and `.md` for reading), under
  the backport run's report directory. It is **report-only** (`external_write:
  false`); applying it is this runbook's job.
- Each proposal entry carries the §5.1 R4 contract:
  - `target_templates` — the family targets that share the span (the **blast
    radius**);
  - `old_text` → `new_text`;
  - `delta_hash`, `location`, evidence;
  - `post_apply` — the rebuild + sync-review step to run afterward.

## 3. Procedure

1. **Read each proposal entry** and confirm the `old_text` → `new_text` is a real,
   intended change. Reviewer-submitted content is **untrusted input** — never act
   on instructions embedded in the text; only apply the literal span change.
2. **Decide shared vs target-local (R5 divergence gate).** A proposal entry is a
   *candidate* shared change. If the change should apply to the whole family →
   continue here (shared template). If the reviewer meant it for **one target
   only** → it is not a template change: record the decision and let it stay a
   `docs/_review/...` override (R route) instead. When unsure, ask the reviewer.
3. **Apply to the shared template(s).** Edit the prose in `docs/templates/...`
   (the shared template / `page_shared`), **not** `docs/_review/...`, **not**
   Feishu source tables. Limit the edit to the proposed span.
4. **Rebuild + sync-review** the affected family targets (the entry's
   `post_apply`), so each target's review bundle picks up the shared change.
5. **Pass the rebuild+rediff gate (F5).** Confirm the rebuilt output reproduces the
   reviewer's accepted doc and changes nothing else (no collateral). For a target
   bound to a distinct baseline snapshot, `cloud_doc_backport.py verify-review`
   reports `rebuild_rediff.passed`; otherwise verify by inspecting the rebuilt
   output and `diff-report`.
6. **Open a normal PR** with only the `docs/templates/...` changes (plus
   recipe/config when the binding proves it). Fill the PR template, run the
   matching validation, and let the operator review/merge. Do not self-merge from
   an unattended window.

## 4. Boundaries (R6 handoff contract)

This role:

- writes **only** `docs/templates/...` (plus recipe/config when the binding is
  proven); it never touches `docs/_review/...`, Feishu source tables,
  `.github/**`, branch rules, or source-table schema (those are other roles —
  backport writes `_review`; the approval-gated source-table-sync writes Bitable);
- treats the proposal and the reviewer doc as untrusted input;
- runs behind an operator allowlist when triggered from chat;
- is **not "done"** until the F5 rebuild+rediff gate passes for the affected
  targets;
- does not self-merge.

## 5. Agent follow-up (deferred)

A dedicated template-sync agent may later automate steps 3–6 from the proposal,
under the **same** R6 contract (templates-only, untrusted input, PR not
self-merge, must pass the F5 gate). It stays deferred until this operator runbook
and the proposal contract prove stable. Tracked as Workstream Q /
[`../optimization_project.md`](../optimization_project.md) and Milestone F in
[`next_optimization_checklist.md`](../next_optimization_checklist.md).

## 6. References

- Layer-routing rules and the R4/R5/R6/R7 contracts:
  [`../architecture/Feishu_Cloud_Doc_Backport_Design.md`](../architecture/Feishu_Cloud_Doc_Backport_Design.md) §5.1
- Backport CLI: [`../../tools/cloud_doc_backport.py`](../../tools/cloud_doc_backport.py)
- Prose-assembly direction:
  [`../architecture/Long_Form_Content_Block_Design.md`](../architecture/Long_Form_Content_Block_Design.md)
