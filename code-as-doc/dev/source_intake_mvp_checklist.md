# Source Intake MVP Checklist

Updated: 2026-06-26

Goal:

```text
spec/manual source -> candidate structured data -> human review -> source-table write -> sync-data -> build/review/backport
```

Boundary:

- Source of truth stays in the Feishu phase2 source tables.
- `data/phase2/*.csv` stays a local snapshot/read model.
- MVP writes no live rows during intake. It emits reviewable candidates and, for existing rows only, the same approval-gated `source-table-change-request/v1` shape consumed by the current source-table writer.
- Live writes are available only through the explicit P5 `apply --write` handoff with table bindings; dry-run remains the default.
- New-row creation remains review-only until the create/upsert contract is deliberately added.

## Phase Checklist

- [x] P0: branch and implementation boundary created
  - [x] Use a new feature branch/worktree.
  - [x] Keep source intake parallel to cloud-doc backport.
  - [x] Keep live writes behind existing approval-gated source-table sync.

- [x] P1: structured candidate extraction
  - [x] Read local Markdown, stdin, or Feishu/Lark cloud-doc Markdown fetch output.
  - [x] Parse pipe-style Markdown tables with heading context.
  - [x] Classify explicit `Manual_Copy_Source`, `Spec_Footnotes`, and `Spec_Notes` tables.
  - [x] Classify spec-like tables into `Spec_Master` or `Page_Placeholders_Source` from page/heading context.
  - [x] Emit stable candidate hashes and source evidence.

- [x] P2: snapshot-aware review artifact
  - [x] Compare candidates with a provided phase2 snapshot.
  - [x] Mark candidates as `create`, `update`, `noop`, or `needs_review`.
  - [x] Keep missing/guessed `Row_key` rows out of the write path.
  - [x] Write `source_intake_candidates.json` and `source_intake_report.md`.

- [x] P3: existing-row change request bridge
  - [x] Convert existing-row updates into `source-table-change-request/v1`.
  - [x] Resolve `Spec_Master`, `Page_Placeholders_Source`, and `Manual_Copy_Source` through the snapshot sidecar when available.
  - [x] Leave unsupported/new-row writes as reviewed candidates, not live writes.

- [x] P4: human review workflow
  - [x] Add an operator-facing approval artifact for selected change hashes.
  - [x] Support `--approve-all-resolved` for controlled fixture and batch review runs.
  - [x] Write `source_intake_approval.json/.md` with approved, unknown, and blocked hashes.

- [x] P5: live source-table apply handoff
  - [x] Apply only approved, resolved requests with the existing source-table writer.
  - [x] Keep dry-run as the default apply mode.
  - [x] Support live `--write` only with explicit `--table-binding TABLE=BASE:TABLE_ID`.
  - [x] Preserve the existing GET-check before write and GET-verify after write behavior.
  - [x] Keep schema/linked-record/table-structure changes operator-gated.

- [x] P6: sync-data verification gate
  - [x] Add a closure verifier that records a labeled `sync-data...` command result.
  - [x] Let production runs use the normal command, for example `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --table spec_master`.
  - [x] Capture the command result in `source_intake_closure.json/.md`.

- [x] P7: build/review/backport closure gate
  - [x] Add a closure verifier that records labeled `build...`, `review...`, or `backport...` command results.
  - [x] Require P4 approval, P5 apply-plan/write evidence, P6 sync evidence, and P7 build/review/backport evidence for a PASS closure.
  - [x] Support `--require-write` when a production closure must prove a live source-table write, not only a dry-run plan.

## MVP Command

```bash
python tools/source_intake.py run \
  --input <spec.md-or-cloud-doc-url> \
  --document-key JE-2000F_EU \
  --source-lang en \
  --data-root data/phase2 \
  --out reports/source_intake/<run-id>
```

## Closure Command Chain

```bash
python tools/source_intake.py approve \
  --report reports/source_intake/<run-id>/source_intake_source_table_change_request.json \
  --approve <delta_hash> \
  --out reports/source_intake/<run-id>

python tools/source_intake.py apply \
  --report reports/source_intake/<run-id>/source_intake_source_table_change_request.json \
  --approval reports/source_intake/<run-id>/source_intake_approval.json \
  --out reports/source_intake/<run-id>

python tools/source_intake.py apply \
  --report reports/source_intake/<run-id>/source_intake_source_table_change_request.json \
  --approval reports/source_intake/<run-id>/source_intake_approval.json \
  --write \
  --table-binding 'Spec_Master=<base_token>:<table_id>' \
  --table-binding 'Page_Placeholders_Source=<base_token>:<table_id>' \
  --out reports/source_intake/<run-id>

python tools/source_intake.py verify \
  --candidates reports/source_intake/<run-id>/source_intake_candidates.json \
  --change-request reports/source_intake/<run-id>/source_intake_source_table_change_request.json \
  --approval reports/source_intake/<run-id>/source_intake_approval.json \
  --apply-report reports/source_intake/<run-id>/source_intake_apply.json \
  --check-command "sync-data=python build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --table spec_master" \
  --check-command "build=python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US" \
  --out reports/source_intake/<run-id>
```

Use `verify --require-write` after the live `apply --write` run when the run's acceptance criteria require actual online source-table writes.

Outputs:

- `source_intake_candidates.json`
- `source_intake_report.md`
- `source_intake_source_table_change_request.json` when `--data-root` is provided
- `source_intake_approval.json/.md` after P4 approval
- `source_intake_apply.json/.md` after P5 apply or dry-run
- `source_intake_closure.json/.md` after P6/P7 verification

## Current Non-Goals

- No automatic creation of new Feishu source rows.
- No automatic dictionary row creation for `Row_key` / `Slot_key`.
- No direct writes to `data/phase2/*.csv`.
- No replacement for `tools/cloud_doc_backport.py run-review-branch`.
- No long-form prose migration into `Manual_Copy_Source`.
