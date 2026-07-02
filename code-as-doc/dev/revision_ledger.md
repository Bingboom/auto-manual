# Revision Ledger

The revision ledger turns reviewer corrections — already captured per run by the
cloud-doc backport — into a single, accumulating, queryable record. It is the
data foundation for measuring and improving generation quality: the
"machine produced X, a human corrected it to Y" signal that backport reports
currently produce and then scatter.

Implementation: [`tools/revision_ledger.py`](../../tools/revision_ledger.py).
Tests: [`tests/test_revision_ledger.py`](../../tests/test_revision_ledger.py).

## What it does today

### ingest

`ingest` reads one backport diff report (the dict written by
`cloud_doc_backport_reports.build_report`) and appends one row per delta to
`reports/revision_ledger/ledger.jsonl`:

```bash
python3 -m tools.revision_ledger ingest --report <backport_report.json>
# custom location:
python3 -m tools.revision_ledger ingest --report <report.json> --ledger <path.jsonl>
# skip the automatic post-ingest reconcile pass:
python3 -m tools.revision_ledger ingest --report <report.json> --no-reconcile
```

Every `ingest` also runs an automatic reconcile pass over the still-pending
rows from earlier rounds (with git-resolved merge metadata, see `--auto`
below). The ledger is a local artifact, so this per-round piggyback — not a CI
workflow — is the merge-time trigger: each backport round settles the previous
round's rows without a separately remembered step. `--no-reconcile` opts out.

### reconcile

`reconcile` runs after the review PR merges / the source-table sync applies. It
fills each pending row's verdict, turning a proposal into a true label. A
backport lands in two places, so reconcile routes by the delta's `route_class`:

```bash
# Class R with merge metadata resolved from git (recommended):
python3 -m tools.revision_ledger reconcile --auto

# Class R with explicit merge metadata (explicit values win over --auto):
python3 -m tools.revision_ledger reconcile \
  --merged-pr "#500" --merged-commit <sha> --merged-at <iso8601> --reviewer <name>

# Also resolve Class D (edits that landed in the online Feishu tables):
python3 -m tools.revision_ledger reconcile --apply-report <source_table_sync apply.json>

# scope/override:
python3 -m tools.revision_ledger reconcile --ledger <path.jsonl> --root <repo_root> [--force]
```

`--auto` resolves each review-route row's merge metadata from the last commit
touching its source file: commit SHA, commit date, author, and the PR number
when the squash-merge subject carries the conventional `(#123)` suffix.

**Class R — `repo_review_text` (branch `_review`).** Matched in the same
normalized text space the deltas were derived in (the backport's `parse_blocks` /
`_normalize_inline`), with a similarity layer on top of exact containment
(best-window partial ratio, threshold 0.90, needles ≥ 12 chars) so
punctuation / line-break level edits do not misclassify:

- `accepted_as_proposed` — the reviewer's text (near-)appears in the merged
  source (or, for a deletion, the machine text is gone). `final_text` =
  reviewer text; on a near match the landed text may differ from it by up to
  the threshold margin.
- `rejected` — the machine's original text still (near-)appears. `final_text` =
  machine text.
- `edited_further` — neither landed (even approximately); something else was
  written.
- `source_missing` — the source file could not be read; the row stays `pending`.

**Class D — `source_table_suggestion` (online Feishu tables).** Resolved from the
`source_table_sync` apply report (`--apply-report`), joined by `delta_hash`
against its `plan` + `applied` entries:

- `accepted_as_proposed` — sync status `written` / `already_applied`.
- `rejected` — a `skip` whose reason is "not approved by a human" (operator
  declined).
- `source_table_abstained` — `drift_abstained` / `verify_failed` / `error` /
  dry-run `planned` / unresolved-record skip; the system did not write and it is
  not a clean label. Surfaced for a human.
- A `delta_hash` absent from the apply report stays `pending` (not yet processed).

Other route classes (`repo_template_text`, `image_asset_delta`,
`needs_human_mapping`) are left `pending` — out of scope for this reconcile.

Decided rows are skipped on re-run (idempotent); pass `--force` to re-evaluate
them. Only the merge fields you supply are stamped.

### stats

`stats` aggregates the ledger into quality metrics:

```bash
python3 -m tools.revision_ledger stats
```

Reports verdict counts, the closed-loop health metric `reflow_rate` (share of
rows that have left `pending` — 0.0 means the ledger records but nobody closes
the loop), overall and per-`route_class` acceptance rate
(`accepted_as_proposed` / decided), and the files whose machine output was
corrected most often (`top_corrected_sources`).

### export

`export` emits `machine_text -> final_text` training pairs from reconciled rows:

```bash
python3 -m tools.revision_ledger export --out reports/revision_ledger/pairs.jsonl
python3 -m tools.revision_ledger export --include-rejected   # add no-change examples
```

One pair per `accepted_as_proposed` row where the text actually changed (a
genuine correction); `--include-rejected` also emits `rejected` rows as
no-change examples. `edited_further` rows are skipped (the landed text is
unknown). Each pair carries `verdict`, `route_class`, and `model/region/lang`
for filtering.

Properties:

- **Append-only JSON Lines**, one delta per row. Matches the repo's JSON-report
  convention; trivial to load later with pandas/duckdb.
- **Idempotent**: rows are de-duped by `row_key` (`run_id` + `delta_hash`, or the
  delta index when no hash is present), so re-ingesting the same report is a
  no-op. The same correction observed in a *later* run is kept as a new row.
- **Read-only on everything else**: it only reads reports and appends to the
  ledger file. It does not touch source tables, templates, the review bundle, or
  backport behaviour.

## Row schema (v1)

| Field | Source | Meaning |
| --- | --- | --- |
| `row_key` | derived | Idempotency key (`run_id` + `delta_hash`/index) |
| `delta_hash`, `run_id`, `generated_at`, `git_ref` | report | Provenance |
| `doc_type`, `doc_url` | report | Which cloud doc the edit came from |
| `model`, `region`, `lang` | parsed from `source_target.path` | Target identity (null when not a `_review` path) |
| `source_path`, `block_kind`, `heading_path`, `line_no` | delta location | Where in the manual |
| `change_type` | delta | `modify` / `insert` / `delete` |
| `route_class` | delta | `repo_review_text` / `repo_template_text` / `source_table_suggestion` / `image_asset_delta` / … |
| `confidence`, `semantic_review_required` | delta | Backport's own signals |
| `machine_text` | delta `old_text` | What the machine produced |
| `reviewer_text` | delta `new_text` | What the reviewer wrote in the cloud doc |
| `source_evidence` | delta | Data-origin evidence, when present |
| `final_status`, `final_text`, `merged_pr`, `merged_commit`, `merged_at`, `reviewer` | reconcile (later) | Human verdict; `pending` until filled |

## Roadmap

- Wire `ingest` into the backport orchestration itself (planned with the
  backport-CLI split, Milestone G PR G0), so each `run-review-branch` round
  ingests its report without a manual step; `reconcile` already piggybacks on
  every ingest.
- A `tm_pair_suggestion` route feeding accepted translated-prose corrections
  into `Translation_Memory` as operator-approved candidates (Milestone G PR G2).
- Richer analytics (CSV/DuckDB materialized views, an eval harness over the
  exported pairs) on top of `stats` / `export` as the corpus grows.
