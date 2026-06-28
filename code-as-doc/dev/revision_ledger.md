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
```

### reconcile

`reconcile` runs after the review PR merges. It reads the landed `docs/_review`
text for each pending row and fills the verdict fields, turning a proposal into a
true label:

```bash
python3 -m tools.revision_ledger reconcile \
  --merged-pr "#499" --merged-commit <sha> --merged-at <iso8601> --reviewer <name>
# scope/override:
python3 -m tools.revision_ledger reconcile --ledger <path.jsonl> --root <repo_root> [--force]
```

Verdict heuristic (works in the same normalized text space the deltas were
derived in, via the backport's `parse_blocks` / `_normalize_inline`):

- `accepted_as_proposed` — the reviewer's text is present in the merged source
  (or, for a deletion proposal, the machine text is gone). `final_text` = the
  reviewer text.
- `rejected` — the machine's original text is still present. `final_text` = the
  machine text.
- `edited_further` — neither landed verbatim; something else was written.
- `source_missing` — the source file could not be read; the row stays `pending`.

Decided rows are skipped on re-run (idempotent); pass `--force` to re-evaluate
them. Only the merge fields you supply are stamped.

### stats

`stats` aggregates the ledger into quality metrics:

```bash
python3 -m tools.revision_ledger stats
```

Reports verdict counts, overall and per-`route_class` acceptance rate
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

- Wire `ingest` into the review-start worker, `reconcile` into the post-merge
  step, and add a `build.py revision-ledger` subcommand once the shape is
  validated in use.
- Richer analytics (CSV/DuckDB materialized views, an eval harness over the
  exported pairs) on top of `stats` / `export` as the corpus grows.
