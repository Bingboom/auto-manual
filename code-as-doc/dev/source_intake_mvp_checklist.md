# Source Intake MVP Checklist

Updated: 2026-06-26

Goal:

```text
spec/manual source -> candidate structured data -> human review -> source-table write -> sync-data -> build/review/backport
```

Boundary:

- Source of truth stays in the Feishu phase2 source tables.
- `data/phase2/*.csv` stays a local snapshot/read model.
- MVP writes no live rows directly. It emits reviewable candidates and, for existing rows only, the same approval-gated `source-table-change-request/v1` shape consumed by the current source-table writer.
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

- [ ] P4: human review workflow
  - [ ] Add an operator-facing approval convention for selected candidate/change hashes.
  - [ ] Document the exact `apply-source-table --approve ...` handoff.
  - [ ] Add an example reviewed candidates fixture.

- [ ] P5: live source-table apply
  - [ ] Apply only approved, resolved requests with the existing source-table writer.
  - [ ] GET-check before write and GET-verify after write.
  - [ ] Keep schema/linked-record/table-structure changes operator-gated.

- [ ] P6: sync-data verification
  - [ ] Run `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --table spec_master`.
  - [ ] Verify `source_record_index.json` refreshes after write.
  - [ ] Verify changed fields survive the sync normalizers.

- [ ] P7: build/review/backport closure
  - [ ] Run the relevant build/check command for the target.
  - [ ] Start or refresh review as appropriate.
  - [ ] Confirm cloud-doc backport still routes later reviewer edits without regression.

## MVP Command

```bash
python tools/source_intake.py run \
  --input <spec.md-or-cloud-doc-url> \
  --document-key JE-2000F_EU \
  --source-lang en \
  --data-root data/phase2 \
  --out reports/source_intake/<run-id>
```

Outputs:

- `source_intake_candidates.json`
- `source_intake_report.md`
- `source_intake_source_table_change_request.json` when `--data-root` is provided

## Current Non-Goals

- No automatic creation of new Feishu source rows.
- No automatic dictionary row creation for `Row_key` / `Slot_key`.
- No direct writes to `data/phase2/*.csv`.
- No replacement for `tools/cloud_doc_backport.py run-review-branch`.
- No long-form prose migration into `Manual_Copy_Source`.
