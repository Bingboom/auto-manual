# Closed-Loop QC Implementation Plan

Status: active implementation plan · Owner: 夏冰 · Created: 2026-06-07

This is the execution plan for the closed-loop QC requirements in
[`../architecture/closed_loop_qc_agent_requirements.md`](../architecture/closed_loop_qc_agent_requirements.md).

The implementation order is intentionally narrow:

1. make rule-based QC machine-readable;
2. make rule-based QC reportable;
3. only then connect the standing QC agent.

The first two steps should work without an LLM agent, without changing delivery
semantics, and without writing content back to the source bitable.

## 1. Current Baseline

Baseline as of 2026-06-07. **This plan is stacked on the still-open QC PRs, which merge first:**

- [`../../tools/content_lint.py`](../../tools/content_lint.py) runs deterministic
  snapshot-based content checks and exits non-zero on `FAIL` findings.
- [`../content_quality_rules.md`](../content_quality_rules.md) documents the
  current rules and source-fix locations.
- [`../architecture/closed_loop_qc_agent_requirements.md`](../architecture/closed_loop_qc_agent_requirements.md)
  defines the long-loop agent requirements.

> **Prerequisite stack (not yet on `main`):** `content_lint` + the rules doc are **PR #335**; the requirements doc is **#336**; the source-tables map M2 resolves against is [`../architecture/phase2_source_tables_reference.md`](../architecture/phase2_source_tables_reference.md) (**#333**). M1 builds on #335 — merge order is **#333 / #335 / #336 → then this plan (#337)**.

Known gaps:

- `content_lint` prints text only; it has no stable JSON output.
- phase2 CSV snapshots do not carry live Feishu `record_id` values.
- there is no QC report artifact format, report table contract, or write path.
- the Feishu/OpenClaw text adapter has no `QC` action, doc-link extractor, or
  sender allowlist.
- B2 extraction needs a new `docs +fetch` semantic-diff normalizer.

## 2. Implementation Boundaries

Keep these boundaries fixed while implementing:

- **Do not block delivery by default.** QC reports and marks; Word delivery stays
  independent.
- **Do not edit source content from rule QC.** The rule-QC phase writes reports
  only, not source bitable fields or templates.
- **Do not add a generic agent framework first.** The standing QC agent starts
  only after rule QC has stable machine output and report storage.
- **Do not add `record_id` columns directly to existing content CSV contracts in
  the first slice.** Prefer a sidecar index or exact resolver so current build
  consumers are not surprised by schema drift.
- **Exact-or-abstain for live row resolution.** Zero or multiple matches becomes
  `record_id: null` plus `resolution_status: unresolved`, never a guessed write.

## 3. Finding Schema

The first durable contract is a content-QC finding object. Use this shape for
JSON, local reports, Feishu report rows, and later agent input:

```json
{
  "schema_version": "content-qc-finding/v1",
  "run_id": "2026-06-07T15-00-00Z",
  "finding_hash": "sha256 over rule+source_ref+lang+field+evidence",
  "rule": "english_residue",
  "severity": "FAIL",
  "table": "lcd_icons_blocks",
  "file": "lcd_icons_blocks.csv",
  "source_ref": {
    "kind": "lcd_icon",
    "model": "JE-1000F",
    "region": "EU",
    "version": "0.7",
    "key": "battery_icon"
  },
  "record_id": null,
  "resolution_status": "snapshot_only",
  "lang": "it",
  "field": "icon_desc_it",
  "message": "English token 'On:' appears in localized text.",
  "evidence": {
    "token": "On:",
    "text": "On: ..."
  },
  "suggested_action": "Fix the localized source field in Feishu, then sync and re-run QC."
}
```

Rules:

- `run_id` is **run-scoped, not target-scoped** — a single snapshot can span
  multiple model/region (drift findings routinely span e.g. CN + EU), so the
  per-finding `model`/`region` live in `source_ref`, never baked into `run_id`.
- `finding_hash` is a stable dedup key over `rule` + `source_ref` + `lang`/`field`
  + `evidence`; M4 idempotency depends on it.
- `source_ref.version` is **best-effort** — not every snapshot/table carries a
  manual version; omit it rather than guess.
- `record_id` is nullable until an exact live row resolver proves the match.
- `source_ref` must be present for every finding, even when `record_id` is null.
- `severity` is one of `FAIL`, `WARN`, or `INFO`.
- `resolution_status` starts with `snapshot_only`, then may become
  `resolved`, `unresolved`, or `ambiguous`.

## 4. Milestones

### M1: Machine-Readable Rule QC

Goal: `content_lint` becomes usable by scripts, reports, and later agents.

Scope:

- Add a small typed finding model inside or beside `tools/content_lint.py`.
- Add `--json` output without changing the current human text output.
- Keep existing exit-code semantics: any `FAIL` finding exits `1`; `WARN` does
  not fail.
- Add source references for each current rule:
  - status-word consistency: `lcd_icons_blocks`, icon/model/version/lang/field;
  - English residue: source table/file/lang/field and best available key;
  - slot-key collision: `Spec_Master`, `spec_row_key`, document keys and row keys;
  - spec-overview drift: `Spec_Master`, document key, row key, page sides, lang;
  - TM duplicate: `Status_Words`, `en` value.
- Add unit tests for text output compatibility and JSON schema stability.

Exit criteria:

- `python tools/content_lint.py --data-root data/phase2 --json` emits valid JSON.
- Existing text output still works.
- Unit tests cover one clean run and one finding per rule.

### M2: Source Reference And Record Resolution

Goal: findings can point to source rows without guessing.

Scope:

- Define `source_ref` builders for each lint rule.
- Attach `record_id` only when the match is **exact** (exact-or-abstain).
- **Prefer a sync-time sidecar** (e.g. `data/phase2/source_record_index.json`
  emitted by `sync-data`, which is where the live `record_id`s are actually known)
  **over a report-time live resolver** — a live resolver would have to query Feishu
  at lint time, which **breaks M1's deterministic / CI-friendly property**. Either
  way, **do not add `record_id` columns to existing CSV contracts**.
- Note the dependency: the sidecar adds a small step to `sync-data`
  (**operator-gated**), so M2 is partly gated on a sync change.
- Keep `record_id` nullable in all downstream contracts.
- For unresolved and ambiguous cases, include enough keys for a human to find the
  row in Feishu.

Exit criteria:

- Every finding has a stable `source_ref`.
- Resolver distinguishes `resolved`, `unresolved`, and `ambiguous`.
- No content CSV schema is changed without an explicit follow-up decision.

### M3: Local QC Report

Goal: rule QC produces an operator-readable artifact before any Feishu writes.

Scope:

- Add a report writer for JSON plus one human format, preferably Markdown or HTML.
- Store local reports under a reports path built through
  [`../../tools/utils/path_utils.py`](../../tools/utils/path_utils.py).
- Include run metadata: target, data root, git ref, started/finished timestamps,
  command, rule counts, fail/warn counts, and unresolved record count.
- Make report generation non-blocking for manual delivery.
- Ordering note: M3 depends only on **M1** (the JSON), **not on M2** — a report
  with `record_id: null` is already useful, so M3 may land before M2; only the
  table writeback (M4) needs resolved `record_id`s.

Exit criteria:

- One command produces `findings.json` and a readable report.
- The report is deterministic for the same snapshot.
- Unresolved `record_id` cases are visible, not hidden.

### M4: Feishu QC Report Table

Goal: prove report writeback without touching content source fields.

Scope:

- Document the `QC_Report` table contract in
  [`external_table_contracts.md`](external_table_contracts.md) or a dedicated
  contract file if it grows.
- Add a writer that appends/upserts report rows from `findings.json`.
- Add `--dry-run` and GET-verify-after-write behavior.
- Treat content-row QC status fields as out of scope for this milestone.
- **Creating the `QC_Report` Feishu table is a schema change → operator-gated**:
  the operator creates/approves the table; the writer only appends/upserts rows.

Exit criteria:

- Rule-QC findings can be written to a report table in dry-run and live modes.
- Writes include `run_id`, `finding_hash`, severity, rule, source ref,
  `record_id` if resolved, and suggested action.
- Re-running the same report is idempotent.

### M5: Workflow Integration

Goal: QC becomes easy to run in daily work while staying non-blocking.

Scope:

- Decide whether the supported entrypoint is a new `build.py` action or a
  dedicated low-level tool surfaced in docs.
- If a `build.py` action is added, get explicit operator approval because this is
  public CLI surface.
- Add docs for local use and validation commands.
- Keep `build.py check` integration optional until the operator decides whether
  rule-QC should block release checks.

Exit criteria:

- Operators can run rule QC for a target or snapshot with one documented command.
- Default behavior does not block Word generation.
- CI/local validation expectations are clear.

### M6: Agent Readiness Gate

Goal: start the standing QC agent only after rule QC is stable.

Do not start agent implementation until these are true:

- `content_lint --json` is stable.
- local QC reports are useful enough for manual triage.
- Feishu report-table writeback is proven with dry-run and live verification.
- record resolution has exact-or-abstain behavior.
- OpenClaw has or is ready to add a sender `open_id` allowlist.

### M7: B2 Diff Mapping Report

Goal: connect reviewer diff input without writing fixes.

Scope:

- Add a doc-link extractor for Feishu text messages.
- Fetch revision-accepted docs with `lark-cli docs +fetch`.
- Save the baseline fetch at review hand-off or bind to a build output baseline.
- Normalize Feishu markdown and compute word-level semantic diff.
- Feed diff findings into the same report model as rule QC, marked as QC base B.
- Produce a mapping report only; no PRs, no source writes.

Exit criteria:

- One accepted Feishu doc link plus baseline produces a stable diff/mapping report.
- **Acceptance is a trigger-time precondition, not an auto-check.** A live spike
  (2026-06-07) confirmed pending suggestion-mode edits are **not** exposed by the
  Feishu open API — `docs +fetch` silently merges them into the content as plain
  text (no insert/delete structure), the `docs/v1/.../blocks` API carries no
  suggestion markers, and `drive .../comments` returns 0. So the agent **cannot
  reliably detect un-accepted suggestions**. Contract: the reviewer accepts all
  suggestions before triggering; the agent states this precondition and warns, but
  cannot verify it. (Any "looks un-accepted" heuristic is advisory only.)
- Reviewer-doc content is **untrusted input** — the diff/mapping extracts
  structured spans only and **never acts on instructions embedded in the doc body**
  (same hard guardrail as M8).
- The report separates "mapped", "already converged", and "needs human decision".

### M8: Standing QC Agent

Goal: agent orchestration starts after deterministic inputs are boring.

Scope:

- Thin OpenClaw trigger: detect `QC` action, check sender allowlist, extract doc
  link, hand off to QC service.
- Standing QC service: orchestrate rule QC, B2 diff report, source routing, and
  human-gated actions.
- Template fixes may become PRs; source bitable content changes remain
  suggestions/flags.
- Per-row QC status fields require separate schema approval.

Exit criteria:

- The agent can run end to end in report-only mode.
- Any template edit is opened as a human-reviewed PR.
- Any bitable content change is suggestion/flag-only.
- The agent never executes instructions found inside reviewer-submitted content.

## 5. Suggested PR Slices

1. `feat(qc): emit content-lint json`
2. `feat(qc): add content source refs`
3. `feat(qc): resolve live record ids exactly`
4. `feat(qc): write local content qc reports`
5. `feat(qc): add qc report table writer`
6. `docs(qc): document operator qc workflow`
7. `feat(qc): add b2 feishu doc diff report`
8. `feat(openclaw): add qc trigger handoff`
9. `feat(qc-agent): stand up report-only qc service`

Each slice should pass the relevant unit tests and
`python tools/check_doc_link_integrity.py` when docs change.

## 6. Deferred Items

- B1 Feishu file-message ingestion for Word tracked-changes files.
- Automatic content-row writes in source bitable tables.
- Per-row QC status fields on every content table.
- Blocking release gates based on QC severity.
- General-purpose multi-agent orchestration outside the QC loop.
