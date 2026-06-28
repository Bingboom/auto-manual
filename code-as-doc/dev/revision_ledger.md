# Revision Ledger

The revision ledger turns reviewer corrections — already captured per run by the
cloud-doc backport — into a single, accumulating, queryable record. It is the
data foundation for measuring and improving generation quality: the
"machine produced X, a human corrected it to Y" signal that backport reports
currently produce and then scatter.

Implementation: [`tools/revision_ledger.py`](../../tools/revision_ledger.py).
Tests: [`tests/test_revision_ledger.py`](../../tests/test_revision_ledger.py).

## What it does today (MVP — ingest only)

`ingest` reads one backport diff report (the dict written by
`cloud_doc_backport_reports.build_report`) and appends one row per delta to
`reports/revision_ledger/ledger.jsonl`:

```bash
python3 -m tools.revision_ledger ingest --report <backport_report.json>
# custom location:
python3 -m tools.revision_ledger ingest --report <report.json> --ledger <path.jsonl>
```

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

- **P1 — reconcile**: after the review PR merges, read the landed `docs/_review`
  text and fill the verdict fields (`accepted_as_proposed` / `edited_further` /
  `rejected`, plus `final_text`). This is what makes each row a true label.
- **P2 — analytics views**: materialize CSV/DuckDB views and ship queries such as
  most-corrected sections, per-`route_class` acceptance rate, and an eval set for
  the generation step.
- **P3 — training corpus**: export `machine_text` → `final_text` pairs for
  domain model tuning.

Wiring an `ingest` step into the review-start worker and a `build.py`
subcommand is deferred until the ledger shape is validated in use.
