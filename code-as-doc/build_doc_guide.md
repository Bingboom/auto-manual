# Windows Build Guide

Updated: 2026-08-17

This file is the maintainer-facing Windows and PowerShell build guide.
The current cross-platform entrypoint is [`build.py`](../build.py).
For the fixed four-language release pack, use [`../scripts/build_us_jp_manuals.ps1`](../scripts/build_us_jp_manuals.ps1) or [`../scripts/build_us_jp_manuals.py`](../scripts/build_us_jp_manuals.py).

For user-facing review workflow details, read:

- [`user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md)
- [`user-guide/quick_start_guide.md`](../user-guide/quick_start_guide.md)

For onboarding new external Markdown manuals into the template library, use:

- [`dev/manual_template_intake_checklist.md`](./dev/manual_template_intake_checklist.md)
- [`.agents/skills/markdown-rst-template-intake/SKILL.md`](../.agents/skills/markdown-rst-template-intake/SKILL.md) for the repo-local Codex workflow that maps Markdown manuals into the current RST template and recipe layout
- [`.agents/skills/manual-rewrite-with-tm/SKILL.md`](../.agents/skills/manual-rewrite-with-tm/SKILL.md) for TM-first structured Markdown/manual rewrite that preserves layout and highlights unmatched source text

## 1. Recommended Entrypoint

```powershell
python build.py validate
python build.py sync-data --config configs/config.us.yaml --data-root data/phase2
python tools/content_lint.py --data-root data/phase2 --json --write-report
python tools/source_intake.py run --input <spec.md-or-doc-url> --document-key <MODEL_REGION> --source-lang en --data-root data/phase2 --out reports/source_intake/<run-id>
python tools/source_intake.py spec-extract --input <spec.pdf> --rules <rules.json> --document-key <MODEL_REGION> --region <REGION> --reference <sibling-spec.json> --out reports/source_intake/<run-id>
python tools/source_intake.py stage-plan --spec-candidates reports/source_intake/<run-id>/spec_intake_candidates.json --spec-sibling <sibling-spec.json> --placeholder-sibling <sibling-placeholders.json> --overrides <target-differences.json> --document-key <MODEL_REGION> --localized-lang <lang> --out reports/source_intake/<run-id>
python tools/source_intake.py approve --report reports/source_intake/<run-id>/source_intake_source_table_change_request.json --approve <delta_hash> --out reports/source_intake/<run-id>
python tools/source_intake.py apply --report reports/source_intake/<run-id>/source_intake_source_table_change_request.json --approval reports/source_intake/<run-id>/source_intake_approval.json --out reports/source_intake/<run-id>
python tools/source_intake.py verify --candidates reports/source_intake/<run-id>/source_intake_candidates.json --change-request reports/source_intake/<run-id>/source_intake_source_table_change_request.json --approval reports/source_intake/<run-id>/source_intake_approval.json --apply-report reports/source_intake/<run-id>/source_intake_apply.json --check-command "sync-data=python build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --table spec_master" --check-command "build=python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US" --out reports/source_intake/<run-id>
python tools/cloud_doc_backport.py run-review-branch --doc-name <doc name> --cloud-doc <url>
python tools/cloud_doc_backport.py run-review-branch --doc-name <doc name> --cloud-doc <url> --write --push
python tools/cloud_doc_backport.py run-review --doc-url <doc-or-fixture.md> --source-path docs/_review/<model>/<region>/page/<page>.rst --out reports/cloud_doc_backport/<run-id>
python tools/cloud_doc_backport.py open-pr --manifest reports/cloud_doc_backport/<run-id>/cloud_doc_backport_run.json
python tools/cloud_doc_backport.py diff --doc-url <doc-or-fixture.md> --source-path docs/_review/<model>/<region>/page/<page>.rst --doc-type review --out reports/cloud_doc_backport/<run-id>
python tools/cloud_doc_backport.py apply-review --report reports/cloud_doc_backport/<run-id>/cloud_doc_backport_report.json --write --allow-rst-baseline
python tools/cloud_doc_backport.py verify-review --report reports/cloud_doc_backport/<run-id>/cloud_doc_backport_report.json
python tools/cloud_doc_backport.py diff --doc-url <doc-or-fixture.md> --template docs/templates/page_zh/00_preface.rst --doc-type template --out reports/cloud_doc_backport/<run-id>
python tools/cloud_doc_backport.py apply-template --report reports/cloud_doc_backport/<run-id>/cloud_doc_backport_report.json --write
python build.py rst
python build.py review
python scripts\local_build.py check
python build.py asset-check --json
python build.py asset-check --asset-key operation/ac_output --asset-format png --json
python build.py asset-intake --asset-source-key source/manual_je1000f_us_master --asset-source-file '<local-master.ai>' --asset-recipe data/asset_recipes/manual_je1000f_us_master.json --asset-output-root .tmp/asset-intake/manual_je1000f_us_master/run-01
python build.py sync-review
python build.py process-review-start-queue --config configs/config.us.yaml --data-root .tmp/review-start/phase2
python scripts\local_build.py publish --config configs/config.ja.yaml --model JE-1000F --region JP
python scripts\local_build.py release-manifest --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py process-build-queue --config configs/config.us.yaml
python build.py message-control-dry-run --message "publish JE-1000F us-merged from branch feature/review-123"
python build.py handoff --config configs/config.us-en.yaml --model JE-1000F --region US --version V0.1 --baseline docs/_build/JE-1000F/US/en/rst
python build.py preview --config configs/config.ja.yaml --model JE-1000F --region JP --page 03_product_overview_placeholder
python build.py fast --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py html
python build.py word
python build.py pdf
python build.py md
python build.py all
python build.py diff-report
python build.py clean
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html,word,pdf,md
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --build-action validate --languages en,fr
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html --open-html
```

### 1.1 Wukong MCP bridge source and intake contract

The DingTalk Wukong stdio MCP bridge is maintained in Git under
[`agent/wukong-bridge/`](../agent/wukong-bridge). Its runtime registration must
point to that checked-in `server.py`; credentials and `lark-cli` auth remain
external, while jobs/exports go to `~/.local/state/hello-docs-bridge` (or
`HELLO_DOCS_BRIDGE_STATE_DIR`).

The KR intake path is sibling-structured and source-first. Wukong passes the
target and an explicit sibling such as `JE-2000E_KR` + `JE-2000E_US`, writes
English `手册值`/`行标签` with `Source_lang=en`, and keeps Korean only in optional
`*_ko` fields. `intake_stage` rejects wrong page routing, unregistered keys,
wrong Slot/Section/Line order, combined input/output facts, and non-canonical
manual units before writing staging. Partial valid batches may be staged for
review, but `intake_commit` requires the union of the target and confirmed
staging rows to cover the sibling structures in both formal source tables.
Formal writes still require both the Base `确认` checkbox and explicit
conversational approval. See the bridge README for registration, security
boundaries, Wukong call order, and validation commands.

`JE-2000E_KR` is registered in the shared [`config.kr.yaml`](../configs/config.kr.yaml)
KR/ko family. Family-default discovery routes automatic close checks to that
config; a target-scoped verification uses `python build.py check --config
configs/config.kr.yaml --model JE-2000E --region KR`.

Local PDF font override:

- for local-only Gilroy preview, set `AUTO_MANUAL_LOCAL_GILROY_DIR=<absolute-font-dir>` before `python build.py pdf ...` or `python build.py publish ...`
- the font directory must contain `gilroy-regular-3.otf`, `gilroy-bold-4.otf`, `Gilroy-LightItalic-12.otf`, and `Gilroy-ExtraBoldItalic-10.otf`
- the helper only patches the generated `_build/latex/fonts.tex` copy for that run; unset the env var to return to the shared fallback chain, and remote CI workers are unaffected

Meaning:

- `validate`: validate config and [`data/layout_params.csv`](../data/layout_params.csv)
- new-line: Stage 3 scaffold plan or controlled write. The default is
  read-only: resolve one config's inheritance chain, target identity, page
  manifest, and template/recipe references, then print
  new-line-scaffold/v1 with whitelist_diff=0 for the KR/AU replay
  calibration. --write requires explicit --output-config and
  --output-manifest paths inside the repository, refreshes only the
  committed fixture through fixture-refresh, and runs build.py check
  against that fixture. It never writes data/phase2 or Feishu; production
  source-table writes remain the separately approved F6 operation. An
  optional `--asset-override-root docs/_review/<model>/<region>/overrides`
  creates only the controlled `_assets`, `_static`, and `renderers` review
  directories plus a README; it never replaces an existing user override
  unless `--force` is explicit. Use --skip-auto-check only when a caller
  will run the check as a separate gate, and use --plan-output <path> to
  retain the JSON plan/report.
- `python build.py new-line --seed-plan` is the Stage 3 F6 preflight. It is
  read-only and reports three separate actions: create the target
  `02_主数据_Document_key` row if absent, clone `Page_Placeholders_Source`
  rows from an explicitly selected source document, and inspect/create missing
  source-table fields from `phase2_source_tables.json`. It reads only the
  selected local snapshot, never calls Feishu, never writes `data/phase2`, and
  abstains with `needs_input` when the source document is ambiguous. Use
  `--seed-source-document-key <key>` to select the clone source; any actual
  row/field creation remains an approved F6 write operation.
- `sync-data`: use the local `lark-cli` login plus `sync.phase2.*` config/env bindings to write normalized CSV snapshots into [`../data/phase2/`](../data/phase2), using the CLI's `base` record listing flow under the hood; when `sync.phase2.spec_master_sources` is configured, `sync-data --table spec_master` reads the two split source tables instead of the legacy total table
- the daily Feishu schema-parity sensor is read-only and accepts explicit old-base → business-base aliases (`文档构建表=02_文档构建`, `数据入库表=01_数据入库`); it compares the existing renamed tables and never creates duplicate tables as part of alerting
- its parity configuration also ignores the retired `文档构建表.Document link`, which is replaced by the maintained `基线文档` and `飞书云文档` fields in the business Base
- `tools/content_lint.py --json --write-report`: local closed-loop QC observation step for the current phase2 snapshot. It writes `reports/content_qc/<run-id>/findings.json` and `report.md`, includes best-effort snapshot `source_ref` values, keeps `record_id` nullable, and does not write Feishu rows or add a `build.py` action yet. The default report covers the registered `ja`/`ko`/`zh` long-tail as `INFO`-only observations while the EU language findings retain the existing blocking `FAIL` behavior.
- `tools/source_intake.py run`: MVP ingress for structured spec/manual Markdown or Feishu cloud-doc content. It parses pipe-style tables into reviewable candidates for `Spec_Master`, `Page_Placeholders_Source`, `Manual_Copy_Source`, `Spec_Footnotes`, and `Spec_Notes`; with `--data-root`, it compares against the current phase2 snapshot and emits `source-table-change-request/v1` only for existing-row updates that can later be approved and applied through the existing source-table writer. It does not create online rows, edit `data/phase2/*.csv`, or replace cloud-doc backport. Track rollout in [`dev/source_intake_mvp_checklist.md`](./dev/source_intake_mvp_checklist.md).
- `tools/source_intake.py spec-extract` / `stage-plan`: the repeatable product-spec lane. `spec-extract` matches complete field labels before any unambiguous base-label fallback and abstains on shared-prefix ambiguity. `stage-plan` consumes its candidates plus the actual region sibling exports for both specs and placeholders, applies only target-specific overrides, and emits a complete `source-intake-staging-plan/v1` review plus the current lark-cli `{"create_records":[...]}` payload. It requires exact `Page + Section + Row_key + Slot_key + Line_order` parity, keeps localized values paired with source values, marks unproven sibling inheritance for review, and never performs a live write. Once inputs are ready, this is the 3–5 minute mechanical fast path; human confirmation and formal-table promotion remain separate gates.
- `tools/source_intake.py approve` / `apply` / `verify`: P4-P7 closure for that intake run. `approve` writes `source_intake_approval.json/.md` from explicit `--approve <delta_hash>` values or a controlled `--approve-all-resolved` review run. `apply` writes `source_intake_apply.json/.md` through the existing approval-gated source-table writer; it is dry-run by default and requires `--write --table-binding TABLE=BASE:TABLE_ID` before touching Feishu. `verify` runs labeled sync/build/review/backport commands, then writes `source_intake_closure.json/.md`; add `--require-write` when the closure must prove live source-table writes.
- `data/source_table_contracts/phase2_source_tables.json`: repo-maintained phase2 source-table contract for table keys, snapshot files, intake targets, writable fields, and `source_record_index` mapping. Update it with [`architecture/phase2_source_tables_reference.md`](./architecture/phase2_source_tables_reference.md) whenever an online source-table schema change could affect intake, backport, source-table writeback, or sync-data.
- `data/phase2/source_record_index.json`: optional sync-derived sidecar for exact-or-abstain source-row resolution. Its per-table `abstain_counts` make missing live IDs, missing required keys, and ambiguous primary keys visible without changing any CSV contract.
- `tools/cloud_doc_backport.py run-review-branch`: **the blessed backport path** (AGENTS.md §3). It resolves the cloud-doc's review branch from the build table, runs in a sparse worktree, and diffs the cloud-doc against a stored **render baseline** (the build-time `基线文档` copy, else the on-branch `.backport/` seed) so the deltas are the reviewer's real edits, not RST-source noise. `--write` applies only Class R prose to the matching `_review` page; `--push` opens a draft PR **into the review branch**. A whole-doc `--write` with no render baseline is refused (seed one or use `--page`). It also auto-resolves the `page_shared/<lang>` shared templates as family-scope siblings (F3): a reviewer delta whose old text matches a shared-template line is routed **Class T** (a report-only `template_sync_proposal`, blast radius = that shared template) instead of being written as target-local Class R — so a shared-prose edit is never silently buried in one target's `_review`. `--no-auto-sibling` disables it (every prose delta stays Class R); `--sibling <path>` supplies explicit siblings instead. Single-region languages (`ja`/`zh`) have no `page_shared` surface, so Class T does not apply. On `--write` the R7 rebuild+rediff gate runs per changed page — the source pre→post diff must be exactly the intended Class R deltas (no collateral); a mismatch blocks the seed-cursor advance and the PR push and exits non-zero, so a backport PR only ever opens from a verified-clean apply. It also emits the actionable Class D / Class T artifacts — the `cloud_doc_backport_source_table_change_request.json` report (the `apply-source-table` input, **not** the diff report), the `template_sync_proposal`, and the source-table suggestions — so a whole-doc backport hands the operator everything the `apply-source-table` and template-sync roles need.
- Cloud-doc backport normalizes Feishu review metadata before routing: inline `<text bgcolor=...>` highlight tags are stripped, image-only/token-only changes are reported as `image_asset_delta`, and page-value rows resolve to `Page_Placeholders_Source` change requests when the value index and `source_record_index.json` sidecar can identify the exact row. Edits that swap output terminology with button terminology are routed to `needs_human_mapping` with `semantic_review.required=true`; the tool does not auto-write those into `_review`.
- `tools/cloud_doc_backport.py run-review` / `apply-review`: **legacy single-page path, now guarded.** They diff/apply the rendered cloud-doc against the `_review` RST *source*, which over-reports and corrupts RST markup (`.. raw:: latex`, `|TOKEN|`, line-blocks). A review `--write` against an `.rst` baseline is therefore refused and steered to `run-review-branch` unless `--allow-rst-baseline` is passed (a deliberate single-page override uses it). The dry-run (no `--write`) still works for inspection.
- `tools/cloud_doc_backport.py run-review`: P4-ready review backport runner. It binds one accepted Feishu cloud doc to one current `docs/_review/...` source, writes `cloud_doc_backport_report.json/.md`, `cloud_doc_backport_apply.json/.md`, `cloud_doc_backport_source_table_suggestions.json/.md`, and `cloud_doc_backport_run.json/.md`, and stays dry-run by default. With `--write`, it patches guarded `repo_review_text` replacements, then writes `cloud_doc_backport_verify.json/.md`; the run manifest reports `PR_READY` only when the review source changed and verification passed. Source-table suggestions remain report-only with candidate table hints and operator steps.
- `tools/cloud_doc_backport.py open-pr`: P5 manifest-to-draft-PR helper. It accepts only a `PR_READY` review run manifest, refuses unrelated working-tree changes, requires the current branch to be `main`, commits only the changed `docs/_review/...rst` source, pushes a `review/...cloud-doc-backport...` branch, and opens a draft PR with the run summary in the body. If GitHub returns a permission error after the branch push, the helper returns/prints `PR_CREATE_FAILED`, a compare link, and the PR title/body for manual draft-PR creation. Local `reports/cloud_doc_backport/...` files remain evidence and are not committed by this helper.
- `tools/cloud_doc_backport.py diff`: P0/P1 Feishu cloud-doc backport prototype. It reads a real Feishu doc through `lark-cli docs +fetch` or a local markdown fixture, compares it with a baseline, writes `cloud_doc_backport_report.json` and `.md`, and does not edit templates, `_review`, generated output, or source bitable rows. Use `--source-path <docs/_review/...rst>` for in-review docs when the review file itself should be the fallback baseline and source target. Use `--template <docs/templates/...rst>` for template-maintenance docs when the template itself should be the fallback baseline and source target; the tool auto-selects the matching fetched section from the source file's first heading unless `--no-auto-section` is set. Use `--section-heading <title>` when the target section must be explicit.
- `tools/cloud_doc_backport.py apply-review`: P3 guarded review backport. It reads `cloud_doc_backport_report.json`, plans safe `repo_review_text` replacements, writes `cloud_doc_backport_apply.json` and `.md`, and only edits `docs/_review/...` when `--write` is supplied. Placeholder/spec/table-like deltas remain `source_table_suggestion` and are skipped into the apply report.
- `tools/cloud_doc_backport.py verify-review`: P3 residual check. It reads the same diff report against the current `docs/_review/...` source, writes `cloud_doc_backport_verify.json` and `.md`, classifies deltas as `applied_resolved`, `still_pending`, `source_table_suggestion`, or `unsafe_or_ambiguous`, exposes report-only data deltas under top-level `source_table_suggestions`, writes the companion `cloud_doc_backport_source_table_suggestions.json/.md`, and exits non-zero only for pending or ambiguous review-text residuals.
- `tools/cloud_doc_backport.py apply-template`: P2 guarded template backport. It reads `cloud_doc_backport_report.json`, plans safe `repo_template_text` replacements, writes `cloud_doc_backport_apply.json` and `.md`, and only edits the template when `--write` is supplied. Placeholder/spec/table-like deltas and non-unique current-template matches are skipped into the apply report.
- `spec-master-rebuild`: merge the Feishu source tables `规格参数明细` and `页面占位参数` into the read-model shape of `Spec_Master.csv`; it validates `spec_row_key` uniqueness, resolves Feishu linked-record footnote refs to stable `Footnote_id` values, and keeps `--write-back` only as a legacy bridge back to the old total table
- `sync.phase2.tables.<name>` should bind table/view IDs through `table_id_env` / `view_id_env`; literal `table_id` / `view_id` is still supported as a narrow escape hatch, but mirror repositories should avoid committed tenant IDs
- `sync.phase2.spec_master_sources` binds the two human-maintained source tables and their active views through `*_env` keys used by `spec-master-rebuild` and by `sync-data --table spec_master`; `sync.phase2.tables.spec_master` no longer needs a legacy total-table binding unless you intentionally use `spec-master-rebuild --write-back`
- The shared English, French, Spanish, Brazilian Portuguese, German, Italian, Ukrainian, and Korean charging-method templates consume `|PV_INPUT_RANGE|` from a `页面占位参数` row with `Page=charging_methods`, `Row_key=pv_input_range`, and `Slot_key=value`. The page contract requires both the resolved placeholder and that semantic row, so an unseeded target fails closed. Repo fixtures carry approved byte-preserving examples. The current JE-1000F US/EU/AU/KR and JE-1500D pt-BR production rows were F6-approved, seeded, and read back on 2026-07-31; every future target still requires its own approved exact values and post-sync `diff-report` evidence.
- The same eight shared charging templates consume `|DC_INPUT_CONNECTOR|` from `Page=charging_methods`, `Row_key=dc_input_connector`, `Slot_key=value`; their shared UPS templates consume `|UPS_TRANSFER_TIME|` from `Page=ups_mode`, `Row_key=ups_transfer_time`, `Slot_key=value`. Keep the UPS `0 ms` incompatibility cautions in prose and preserve localized units in the page value. Both contracts fail closed when their semantic row is absent. The five current document keys were seeded in the same 2026-07-31 F6 batch; do not clone those values into a new target without exact-value approval and a fresh readback.
- `lcd_icons`, `troubleshooting`, `symbols_blocks`, `variable_defaults`, `variable_lang_overrides`, and `manual_copy_source` sync as normal phase2 tables; the LCD icons renderer reads `lcd_icons_blocks.csv` and renders downloaded `figure` attachments from `data/phase2/_attachments/lcd_icons/`, the troubleshooting renderer reads `troubleshooting_blocks.csv`, the symbols renderer uses downloaded `Figure` attachments from `data/phase2/_attachments/symbols` when present, `symbols_blocks` also maintains signal structure with `block_type=signal_row`, page short copy such as LCD / Symbols titles, headers, Symbols signal labels / meanings, Product overview labels, and spec page / section titles is authored in `Manual_Copy_Source.csv`; `sync-data` renders generated runtime copy into `Localized_Copy.csv` and generated spec title metadata into `spec_titles.csv`, image alt text is derived from existing titles, `symbol_key`, or generated signal labels, LCD status-word bolding reads `Status_Words.csv` exported from Translation Memory rows marked `是否为 status word=Y`, and LCD description variables continue to resolve from `Variable_Defaults.csv` plus `Variable_Lang_Overrides.csv`. The US Spanish, French, and Brazilian Portuguese `03_product_overview_placeholder.rst` templates resolve their seven page/panel/part labels through `product_overview.*` copy keys; the EU raw-LaTeX Product Overview pages are intentionally outside this pilot.
- if the Base keeps `Model` as a linked-record field, maintain a text `Model_key` column for variable defaults so exact model matching stays independent of Feishu record ids
- `sync-data` normalizes `Spec_Master.csv Slot_key` back to plain slot tokens when the source table stores markdown-link wrappers for page-value placeholders
- `sync-data` also resolves full field names through Base field metadata, so long headers are not dropped when `lark-cli` shortens them in record-list output
- the same cached Base field metadata powers a non-blocking schema sensor: source columns missing from a phase2 schema are recorded as `MISSING_COLUMNS` warnings in `snapshot_manifest.json` and printed by `sync-data`; the historical `spec_footnotes` `pt-BR` alias is exempt, and CSV output / sync gates are unchanged
- when `spec_master` is synced from the split source tables, `sync-data` reads `spec_footnotes` as needed and rewrites Feishu linked-record footnote refs in `Spec_Master.csv` to stable `Footnote_id` values
- when one target references a `Footnote_id` that is missing only in its own region but exists as one unambiguous sibling-region row for the same model, validation and rendering now reuse that fallback definition instead of stopping the build immediately
- `sync-data` does not repair bad `Is_Latest` flags; leave those source-table problems visible so `check` and publish validation can fail loudly
- [`../tools/dingtalk/spike_cli.py`](../tools/dingtalk/spike_cli.py) is the manual Phase 0 smoke helper for future app-only DingTalk provider research; it defaults to the official App-Only token flow and lets maintainers inject product-specific list/update/upload endpoints without changing the current queue runtime. A minimal smoke run looks like `python tools\dingtalk\spike_cli.py all --record-id <stable_row_id> --update-set smoke_checked=true --upload-file .tmp\phase0-smoke.docx`.
- [`../tools/dingtalk/auth.py`](../tools/dingtalk/auth.py) now exposes the verified App-Only token helper behind `DINGTALK_CLIENT_ID`, `DINGTALK_CLIENT_SECRET`, and `DINGTALK_CORP_ID`, and [`../tools/dingtalk/workspace.py`](../tools/dingtalk/workspace.py) can parse a target node ID from a normal DingTalk docs URL such as `https://alidocs.dingtalk.com/i/nodes/<node_id>`.
- `rst`: materialize [`docs/_build/<model>/<region>/rst/`](../docs/_build)
- `review`: seed [`docs/_review/<model>/<region>/`](../docs/_review) from runtime draft
- `--source review-asis`: render the committed `docs/_review/<model>/<region>/` bundle exactly as-is — only the conf/asset skeleton is materialized and the review overlay supplies every content page, so no page is re-derived from the build data-root. Unlike `--source review` it neither pre-syncs review params from data nor runs the Spec_Master identity guard, so it renders a review target whose model is absent from the active data-root (e.g. the CI `Review Preview Package` fixtures under `tests/fixtures/phase2`). The `Review Preview Package` workflow uses this mode, which is why a newly onboarded model (not yet in the fixtures) previews instead of failing the whole package
- `check`: run validation + prepare bundle + content checks, including stale identity scan, contract validation, and duplicate RST/raw HTML text consistency checks
- `asset-check`: validate the image-asset registry and resolve approved exports for renderer imports. `--allow-temporary` is only a diagnostic/operator inspection option for this command; bundle assembly never enables it. `--publish` applies the stricter registry-wide status gate. `--refresh` recomputes hashes from materialized export bytes in a dry run; pair it with explicit `--write` only after reviewing the machine-generated CSV diff. Missing or malformed exports fail closed and never produce a partial write. Editable `.ai` masters belong in the dedicated Feishu asset-source table, while `data/asset_sources.csv` records their hash/scope and `data/asset_generation_candidates.csv` controls which candidates may be sent to image generation.
- `asset-intake`: deterministically package a PDF-compatible Illustrator master through a strict recipe. All four `--asset-source-key`, `--asset-source-file`, `--asset-recipe`, and `--asset-output-root` flags are required; the output root must not exist. The command snapshots and verifies the source, emits archive pages/previews plus approved/quarantined recipe exports, scans raw and decoded PDF objects for Illustrator private markers, verifies declared full hashes, and writes a deterministic ZIP with its manifest/index. It never edits the source, worktree, registry, or Base and exposes no promotion flag through `build.py`.
- Reviewed promotion is a separate, fail-closed maintainer action. A contract under `data/asset_promotions/` must bind the reviewer, decision time, exact model/region/languages, source AI, frozen reference PDF, recipe/evidence, candidate bytes, promoted output bytes, and deterministic composition. The JSON file is the reviewed carrier; during the migration, the Python compatibility shadow is read in parallel and exact parity plus a whole-carrier SHA-256 are required. The registry accepts `source=reviewed-promotion:<promotion_id>` only when every full SHA and whitelist still matches. Raw App/QR candidates remain quarantined; deleting or weakening the contract must make resolution fail rather than fall back to a shared legacy image.
- `.ai` source intake is an operator workflow, not a Git large-file path: follow [`../user-guide/closed_loop_ops_guide.md` §4.9.2](../user-guide/closed_loop_ops_guide.md#492-ai-交付与登记一页流程) to run and compare the package, avoid duplicate attachments, upload the source/ZIP/manifest through the three separately created `04_资产*` tables, and verify downloaded bytes before updating `data/asset_sources.csv`. The live Base/table/view/field binding is frozen in [`../data/asset_base_bindings.json`](../data/asset_base_bindings.json); the JE-1000F US master is the first round-trip-verified source. If those tables are inaccessible, stop and leave the source pointer empty. Never read, write, or fall back to the legacy illustration or staging intake table.
- RST image, figure, substitution-image, and raw-HTML `src` references may use a registry identity such as `.. image:: asset:operation/ac_output`. The finalizer runs only after runtime materialization, review overlay, and frozen attachment aliases. It requires an approved export matching the bundle model/region/language, accepts only PNG/JPG/JPEG/SVG/PDF, and never falls back to `.ai`, `🔧临时替代`, `❌缺失`, or `⛔隔离` rows.
- Every prepared bundle freezes `asset_usage_manifest.json`, `asset_registry_snapshot.csv`, and a finalized `bundle_manifest.json`. The usage manifest distinguishes `registry-uri`, explicit `review-override`, and `legacy-path` references; the bundle manifest hashes the final RST include closure, configuration, staged support trees, and the two asset sidecars into `bundle_sha256`. Review seeding restores semantic `asset:` references from rewrite provenance so a review round does not silently downgrade asset identity.
- Shared templates under `docs/templates/` are bulk-migrated: every `common_assets` image directive and raw-HTML `src` uses `asset:<asset_key>` and is therefore registry status/scope/hash gated at bundle prepare. Path-based references remain compatible (recorded as `legacy-path`) but are reserved for sources that have no registry key yet — new template references should use the registry identity. Release manifests do not yet carry this asset lineage; `bundle_manifest.json` is the current bundle-level provenance surface.
- Target-specific exports do not replace a shared registry key. They use a unique `asset_key` plus `override_for=<shared asset_key>` and a narrow model/region/language scope. A shared template keeps the stable base URI; the frozen registry resolver selects exactly one matching override or falls back to the shared row, and rejects ambiguous override matches.
- `build.py idml` prepares only RST when the exact model/region/language target is present in the approved reference-layout registry; its production exporter consumes that hash-bound physical plan directly. A matching approved contract on disk without its registry entry is a hard error, not permission to use fuzzy page matching. The historical LaTeX-PDF fallback remains available only when the target has no approved contract.
- A candidate `target_assembly` plan is frozen against a specific book, so the target's page manifest has to declare every page the plan names — otherwise `build.py idml` prepares a bundle the plan rejects and the target is only buildable with an explicit `--source review`, through a derivative. [`tests/test_assembly_plan_manifest_coverage.py`](../tests/test_assembly_plan_manifest_coverage.py) pins which targets are in that state; `JE-3000C_KR` is the one known case (its cover and back cover exist only under `docs/_review`, and `manual_kr.yaml` is shared with `JE-1000F_KR`/`JE-2000E_KR`, so declaring a per-model cover needs a cover asset for all three or a per-model manifest). A count mismatch names the offending pages in both directions; it is not a code regression.
- `sync-review`: refresh review files affected by CSV data changes
- `tools/check_review_branch_sync.py --base <ref> --remote origin --json`: emit
  the read-only shared-source propagation ledger. It resolves targets from each
  checked-in review `manifest.json` (including legacy `review/id-*` branches),
  narrows template/recipe impact through the seed and current page manifests,
  and marks each affected branch/source row `merge_params_safe` only when the
  placeholder-line proof succeeds. Missing refs, ambiguous derivatives,
  ordinary prose/layout changes, and authored edits on a replaceable line stay
  visible as `needs_human`; this command has no apply mode.
- `process-review-start-queue`: Start Review bridge; it consumes `sync.phase2.review_init` rows where `是否进入Review` is checked and `Workflow_action` maps to `Start Review`, resolves the exact model/region target from `Document_Key`, and combines that target with the row's language-range `Build_family` plus optional `Lang`. A target-specific config wins only when it declares that exact target; otherwise the shared regional config remains the fallback. Thus `JBP-2000B_US` with `Build_family=us-merged` selects `config.bp-us.yaml`, while an ordinary US host row with the same language range selects `config.us.yaml`. The worker groups only the rows whose resolved config enables `build.queue_by_document_key`, syncs the latest phase2 snapshot, always reseeds `docs/_review` from the latest `origin/main` template/data state, force-updates the routed review branch when it already exists, creates or reuses the PR, then writes back the same `Git_ref`, `PR_url`, `Review_status=InReview`, and cleared `是否进入Review` state to every pending row in that group
- Start Review eligibility is the conjunction of `Document_Key` being a non-empty `<MODEL>_<REGION>` value, `是否进入Review` being checked, and `Workflow_action` mapping to `Start Review`
- when `Document_Key` is a linked Base field, the API can expose only the linked record id, so chat-driven Start Review lookup should use `Task_id` as the stable selector and then verify `是否进入Review` plus `Workflow_action=Start Review`
- `Start Review` now means "force restart and reseed from the latest template". Existing committed `docs/_review/<model>/<region>/` content on `main` is no longer a duplicate guard, and re-checking `是否进入Review` on an `InReview` row will restart the review seed flow
- `process-build-queue`: Build Draft Package / Publish bridge; it consumes the historically named `sync.phase2.document_link` binding where `是否触发文档构建 = Y`, acquires and verifies a two-hour row-group lease in `构建结果` before sync/build work, writes `开始构建时间` when that optional field exists, resolves the config from the exact `Document_Key` target plus the language-range `Build_family` and optional `Lang`, groups only the rows whose resolved config enables `build.queue_by_document_key`, refreshes `data/phase2` only when the row's `是否强制刷新数据 = true`, builds Draft rows as `check + word + md`, and switches Publish rows to `check + diff-report + word + pdf + md + idml`. Delivery writeback is phase-aware: Draft writes the editable `飞书云文档` plus frozen `基线文档`, Publish writes the uploaded designer handoff ZIP to `idml_file`, and Web Publish writes `HTML_link`. The worker also records the local DOCX path in `Document directory`, optional mirror state in `Document link_dd`, status in `构建结果`, refresh state in `data_sync`, clears `是否强制刷新数据`, and flips the trigger to `已构建` on success. The retired `Document link` field is not an upload-success predicate.
- `tools/manifest_lint.py --json` is a report-only inventory sentinel for config-backed page manifests. It scans every `configs/config*.yaml` reference and every `docs/manifests/*.yaml` file, reporting orphan manifests, invalid/missing sources, and config/manifest language-set drift without blocking a build.
- Within one `process-build-queue` invocation, a successful forced phase2 sync is memoized per config/data-root pair; later groups reuse that snapshot, while a failed sync is not memoized and remains retryable.
- `tools/manifest_family.py` is the non-mutating family-manifest pilot. Use `diff --base <base.yaml> --target <target.yaml> --output <diff.json>` to create the deterministic `family-manifest-diff/v1` carrier, then use `roundtrip` with the same base, target, and diff to assert `"byte_identical": true`. This pilot does not rewrite `docs/manifests/`; checked-in generation is a later stage.
- `python tools/manifest_family.py fold --root . --index docs/manifests/family/index.yaml` checks the family index: four anchor YAML manifests plus 16 carrier diffs cover all 20 current YAML goldens with canonical byte identity. The two battery-pack cells own separate anchors (`manual_bp-us.yaml` for `BP@INTL`, target-neutral `manual_bp-jp.yaml` for `BP@JP`). Add `--write` only to refresh the tracked diff carriers; it never edits a YAML manifest.
- `tools/skeleton_resolve.py` keeps the public `emit` / `verify` / `plan` CLI surface unchanged. Its Python `resolve_plan(..., product_plan=...)` API now accepts target-owned `house_style_version`, `enabled_optional_slots`, and `terminal_slots` selections; when a blueprint declares order profiles, load and pass both carrier maps with `load_slot_template_catalog(...)` so a version cannot silently lose its safety/warranty variant. Blueprints declare the complete slot universe and named order profiles; optional front/body slots are opt-in, back slots have the single `terminal_slots` selector, and calls without a product plan still resolve the required/capability core. BP@INTL continues to use the legacy region-profile terminal selector and remains byte-identical. Do not put a model/title/file/page conditional in the resolver; R3c and later targets supply only plan/config/source/asset data.
- Family manifests carry capability annotations at the page entry, not in a target-specific side table. All current `06_ups_mode` entries declare `capability: UPS功能`, so JP/KR/EU and the other current families use the same assembly-time keep/drop decision as US. When adding a capability-governed page to another family, add the same annotation there and refresh the fold carriers with `fold --write`.
- `.github/workflows/manifest-regenerate-diff.yml` runs that fold check on pull requests touching configs, manifests, or carrier code; this is the CI red gate for a manually edited generated manifest. It also runs `manifest_lint` as a report-only inventory.
- for `build.queue_by_document_key` configs, Draft rows with a non-empty `Lang` are grouped by `Document_Key + normalized Lang`; `br` / `pt-br` normalizes to `pt-BR`, and the selected language is passed to the build/check/validate/bundle path. `configs/config.pt-br.yaml` now follows the single-language US build path, so Brazil Portuguese draft rows should use `Build_family = pt-br` with `Lang=br` or `Lang=pt-BR` instead of adding an English companion row.
- HTML language labels, review-preview language labels, and queue-query language tokens are derived from `tools/lang_registry.py`; keep new language codes and aliases in the registry rather than adding another per-surface map. Queue queries retain legacy Chinese and English aliases, but normalize them through the same registered canonical code before filtering. The isolated `tests/test_fake_language_e2e.py` probe injects a fake `xx` registry row and verifies the sync schema, copy/TM fields, signal words, content-lint map, queue query, and preview label surfaces without consumer-specific edits.
- row writeback has an explicit leased running stage: `process-build-queue` writes `RUNNING | ... started_at=... | claim_token=... | claim_expires_at=...` to every row in a group, reads those rows back with `view_id=None`, and proceeds only when every token still matches and is unexpired. Active leases are skipped by pending selection; a lease expires after two hours and can then be reclaimed. Success/failure replaces the RUNNING value and therefore releases the lease. The Feishu upsert API does not provide compare-and-swap, so this is a readback-verified K12-min lease; cross-workflow serialization remains a separate concurrency layer.
- if DingTalk mirror sync is enabled and the row also has `是否上传钉钉`, that checkbox becomes the row-level gate: checked rows also sync DingTalk and write `Document link_dd`, unchecked rows stay on the normal Feishu/wiki upload path for that run
- if the table does not have `是否上传钉钉`, the worker follows the current global worker mode for that whole row
- if that checked row also has `DingTalk_target_node_url`, the worker uploads to that row-level target first; otherwise it falls back to the global `DINGTALK_DOCS_TARGET_NODE_URL`
- if the row also has `operator_union_id`, the worker can resolve a per-operator DingTalk session file before falling back to the global browser-session envs
- `DingTalk_session_key` and `钉钉会话键` are accepted as aliases for `operator_union_id`; if the row uses `alice`, the worker expects `<session_root>/alice.json`
- if a DingTalk-enabled row points at a missing per-operator session or there is no usable global DingTalk session, the queue now fails that row before build starts and writes the exact missing-session reason back to `构建结果`
- `queue-query`: OpenClaw Phase 2 queue resolution helper; it reads the Feishu-bound review/build rows and returns the concrete `record_id`, optional `Task_id`, workflow intent, `Git_ref`, status fields, and explicit `delivery_kind / delivery_url / delivery_ready` contract that a natural-language control layer needs before dispatch or status reporting
- `queue-resolve-action`: structured OpenClaw dry-run resolver; it turns one natural-language ask into the bounded action contract from the control-layer plan, including `action_name`, `resolution_status`, required confirmation, missing required fields, and the matched queue row
- `manual-index-query`: read-only OpenClaw helper for the `发布文档管理` Base view. It answers product/manual-link inventory and overview asks such as `查 JE-2000F 的说明书链接`, `查询各产品的说明书`, or `获取说明书总览信息`; it respects `FEISHU_MANUAL_INDEX_*` overrides and does not dispatch builds.
- for this repo, treat **BlockClaw** as the OpenClaw-backed document-build operator rather than a generic assistant: its primary job is to work with content blocks, run review/build/publish work, inspect queue state, explain build failures, and only secondarily help with translation or copy work that supports the manuals
- `translation-memory`: query the repo-owned `data/phase2` multilingual snapshot and return compact translation memory context for OpenClaw or human translation tasks; combine it with `sync-data` when freshness matters
- `validate`: catches missing phase2 table base-token/table-id bindings and page-manifest languages that are not declared in `build.languages`, before `sync-data` or a build reaches runtime
- `python3 .agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py --query-text "<paragraph>" --source-lang en --target-lang fr --format prompt`: preferred live sentence-pair memory for OpenClaw translation; it reads the dedicated `Translation_Memory` base first and emits prompt-ready context. In chat replies, keep that lookup implicit, return the final translated wording first, prefer one foreground lookup over a background poll flow, and rely on the script's short local cache for repeat lookups unless you need `--no-cache`.
- For Taiwan Traditional Chinese, call the same script with `--source-lang zh --target-lang zh-TW`; `zh` is the Simplified Chinese source field and `zh-TW` is the target field.
- `python3 .agents/skills/manual-rewrite-with-tm/scripts/rewrite_markdown_with_tm.py input.md --target-lang de --use-feishu-term-source -o output.de.md`: preferred batch rewrite path for full Markdown/manual files; it uses `bitable-translation-memory` as the live lookup layer, preserves headings, tables, and images, reuses safe TM sentence patterns for parameter-only changes, and keeps unmatched source text in `==...==` instead of free-paraphrasing
- `message-control-dry-run`: maintainer-only parser probe retained for offline control-layer debugging; it resolves one raw message into structured JSON and guardrails without dispatching workflows or editing Feishu rows
- [`../integrations/openclaw/feishu-im-webhook-adapter/`](../integrations/openclaw/feishu-im-webhook-adapter): standalone Feishu IM ingress adapter; it validates callback payloads, normalizes text messages, answers read-only manual-index questions through `manual-index-query`, uses `queue-resolve-action|queue-query|queue-execute` as the repo-owned action surface for queue work, and replies back into the same Feishu thread. Cloud-doc backport is **not** routed through this adapter — it runs from Claude Code / Codex / a terminal via `tools/cloud_doc_backport.py` (see the backport commands above and AGENTS.md §3).
- `.openclaw/`: local-only OpenClaw profile directory for private aliases, reply phrasing, and message reaction choices; the adapter reads it by default, but the directory is git-ignored so personal operator memory and real chat examples stay off remote
- `FEISHU_IM_ENABLE_MESSAGE_REACTIONS=true`: optional native Feishu reaction layer for message stages such as received, accepted, needs confirmation, completed, and error; the received-stage default is `Get`, and the normal same-thread text reply still remains the canonical status surface
- [`../integrations/openclaw/scripts/patch_openclaw_feishu_received_reaction.mjs`](../integrations/openclaw/scripts/patch_openclaw_feishu_received_reaction.mjs): local OpenClaw gateway patcher for desktop deployments that receive Feishu events through the installed OpenClaw gateway; it adds the native `Get` reaction immediately inside `im.message.receive_v1`, before any agent reasoning, queue lookup, or build execution; it patches both the legacy bundled-`dist/` install and the OpenClaw ≥ 2026.6 `@openclaw/feishu` plugin layout under `~/.openclaw/npm/projects/openclaw-feishu-*/`
- `listen-message-control`: local no-server Feishu IM ingress; it opens the same `im.message.receive_v1` long connection through `lark-cli`, reuses the adapter's message handler, and replies in-thread without any public callback URL
- when that listener must coexist with an older local Feishu app, set `FEISHU_IM_LARK_CLI_HOME` so only the new app's `lark-cli` runs from the isolated home while the old app keeps the default `~/.lark-cli`
- [`../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/`](../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/): ECS deployment assets for the same adapter; use the wrapper scripts plus `systemd` unit examples when the Feishu ingress must restart automatically after reboots or crashes
- `queue-query --query-text` now accepts task ids like `JE-1000F_US_0.3_Build Draft Package`, exact underscore document ids like `JE-1000F_US_0.3`, and spaced asks like `JE-1000F US 0.3`; it also maps document-key-only review asks such as `review JE-1000F_EU`, `开始 review JE-1000F us-merged`, and failure-reason asks such as `为什么 JE-1000F US 0.3 构建失败`
- `queue-resolve-action` treats status-like workflow mentions such as `草稿包好了没` or `跑完了吗` as `query_status`, so mentioning a draft package while asking for progress does not dispatch a new build
- broad latest-link asks such as `构建好的文档链接发我` are narrowed to successful `Document_link` rows and collapse to the latest version per `Document_Key`, preventing stale `1.0` rows from being interpreted as failed `1.1` builds
- the Feishu IM adapter keeps batch link replies card-friendly: status summaries omit `delivery_url`, then each unique phase-aware delivery link is sent as its own follow-up message so Feishu can render it as a document entity when the chat client supports that; short follow-ups such as `发` / `发一下` reuse the stored batch context and resend those links
- when the operator needs a stable full inventory count rather than latest links, use `queue-scope=document-link`, `result-contains=success`, and a sufficiently high `limit`, then classify returned rows by `normalized_workflow_action` (`draft` or `publish`) across the relevant config families such as `configs/config.us.yaml` and `configs/config.ja.yaml`; `queue-query --json` exposes `matched_count`, `returned_count`, `limit`, and `truncated`, so default-limited broad queries are visibly incomplete instead of silently dropping rows
- conversation context is only a selector cache for Feishu IM follow-ups; deleted or moved rows must be reported as not found after a fresh table read, not reconstructed from remembered row data
- `queue-execute`: OpenClaw Phase 2 deterministic execution helper; it resolves one Feishu row from `--query-text`, dispatches the matching `main`-owned GitHub workflow through the local control-layer CLI, waits for completion, then re-reads the Feishu row and returns the final `record_id`, `Git_ref`, `构建结果`, and phase-aware delivery contract. Draft/Publish dispatch results also carry an advisory target-bound asset preflight for the current review/template sources; it is warning-only because exact lineage does not exist until the worker freezes the prepared bundle. The prepared-bundle publish gate remains authoritative. For `Start Review`, an already `InReview` row with `Git_ref` is treated as completed and returned without another dispatch.
- `queue-execute --allow-multiple`: multi-target batch dispatch. It resolves every matching row, validates each eligible one (`是否触发文档构建=Y`, not already completed), then sends one batch worker run per queue action with the exact `record_id` set (`--record-ids` is available for adapter callers). It returns one per-record JSON report (`matched_count`, `dispatched_count`, `skipped_count`, `error_count`, and a `results` list of `record_id`/`run_id`/`status`/`reason`). It is accept-first (no completion wait); every dispatched row shares the same run id, while already-built or not-triggered rows are reported as `skipped` rather than silently dropped.
- An explicit OpenClaw request to build or trigger a remote worker must not run local `check`, `word`, `sync-data`, or inspect `data/phase2/*.csv` first. Resolve the live `Document_link` row and dispatch with `queue-execute`; the remote `process-build-queue` worker honors `是否强制刷新数据` and runs `sync-data` before the build when it is true. Missing local snapshot rows are not a blocker, and missing `FEISHU_PHASE2_*` table bindings are reported as GitHub Actions environment errors only after the worker returns them.
- `python scripts/openclaw_git_guard.py status`: bounded local Git status for OpenClaw or Feishu chat flows; it returns JSON with the current branch, HEAD, and dirty-worktree summary
- `python scripts/openclaw_git_guard.py switch --branch main --pull`: bounded local Git branch switch helper for OpenClaw or Feishu chat flows; it fetches refs, refuses dirty non-generated worktrees, switches to an existing branch, and only fast-forward pulls
- the control layer is no longer at the old Phase 0 plan baseline; the repo-local Phase 2 stack is now in place, including queue resolution, deterministic execution, structured failure replies, explicit Publish confirmation, and the standalone Feishu IM ingress adapter. Encrypted callback support and ECS deployment assets are now repo-owned; the remaining work is shared state and a stable named ingress rollout.
- if the adapter runs on ECS, prefer a named Cloudflare Tunnel or your own HTTPS reverse proxy; `trycloudflare.com` is fine for smoke tests but its URL is not stable across restarts, even if the adapter itself is managed by `systemd`
- if the stable named-ingress rollout is deferred, keep the pending server checklist in [`../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/README.md`](../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/README.md): provision a Cloudflare-managed domain, create the named tunnel, write `/etc/cloudflared/config.yml`, export `CLOUDFLARED_TUNNEL_CONFIG`, enable the tunnel service, then cut Feishu over to the stable hostname
- if `queue-execute` resolves a Publish row, it now requires `--confirm-publish` before it will dispatch the `main`-owned Publish worker
- repo-local OpenClaw dispatch no longer treats `adm-zip` as a dispatch-time hard dependency; metadata artifact parsing is now best-effort so a plain ECS checkout can still dispatch and poll workflows even if the control-layer package dependencies have not been installed locally
- `process-review-start-queue` now writes a structured failure summary when the worker fails before Feishu writeback; that summary is packed into `openclaw-run-metadata`, and both `/manual-status` and `queue-execute` prefer the summary message over a generic GitHub failure
- one explicit Start Review workflow `record_id` that no longer resolves to a pending review-start row is also treated as a structured failure; if that same row is already `InReview`/`ReadyForPublish` with `Git_ref`, the worker treats the duplicate dispatch as an idempotent success — even when `Workflow_action` has already advanced to a later stage such as `Build Draft Package`. Batch queue scans with no pending rows still stay as normal idle runs.
- the merged US `configs/config.us.yaml` flow now emits one `docs/_build/<model>/US/word/manual_<model>_us.docx` bundle that contains `en`, `fr`, and `es` together; CSV-driven `Source_lang` / `*_source` text is required, while non-source language values may be blank because runtime lookup falls back to source-language text
- `Build_family` is the queue row's language range, not its product or skeleton identity: use values such as `us-merged`, `eu-merged`, `us-en`, `eu-en`, `us-es`, `us-fr`, `pt-br`, `jp-ja`, and `cn-zh`. The config's internal `build.family_id` may remain target-specific; `build.language_family` declares which row language range it accepts. `Document_Key` supplies the model/region target, and `Lang` remains an optional compatibility/narrowing field.
- queue rows should use `Workflow_action` only: `Start Review` to force restart/reseed review branches, `Build Draft Package` for review-stage rebuilds, `Publish` for print release outputs, and `Web Publish` for the responsive RTD manual; leave `Doc_phase` blank
- when review-init reuses the shared `Document_link` binding, each worker consumes only its own action: Start Review, Build Draft Package, Publish, or Web Publish
- merged US/EU rows for Start Review, Draft, and Publish should use `Build_family = us-merged` / `eu-merged` and may leave `Lang` blank; single-language rows should use the matching language family such as `us-en` / `eu-en` / `us-fr` / `us-es` / `pt-br`. For example, JBP and ordinary host US rows both use `us-merged`; exact target resolution selects the BP or MAIN skeleton config.
- config policy for `build.queue_by_document_key`: turn it on for merged whole-book families that intentionally build one shared manual across languages, such as today's `us-merged`, `eu-merged`, and future `cn-merged`; leave it off for single-language families such as `us-en`, `eu-en`, `us-fr`, `us-es`, `pt-br`, `jp-ja`, `cn-zh`, or future `eu-de` / `eu-fr`, which should continue to be isolated by `record_id`
- when the queue row carries `Version`, Build Draft Package DOCX/Markdown names stay version-suffixed such as `manual_je1000f_us_en_0.2.docx|md`, while Publish queue release artifact names become `manual_je1000f_us_en_publish_0.2.docx|pdf|md`; Draft imports the DOCX into `飞书云文档` plus `基线文档`, while Publish uploads the designer handoff ZIP to `idml_file`
- `Workflow_action = Build Draft Package` rows must carry `Git_ref`; queue builds now seed a temporary worktree from the latest `origin/main`, then overlay only `docs/_review` from that review branch, so the queue keeps the current `main` toolchain while still rendering the selected review content instead of silently falling back to `main`
- Print Publish keeps two source modes deliberately separate. A target registered in the approved reference-layout registry renders `check`, DOCX, PDF, Markdown, and IDML from the exact `review-asis` overlay; refreshing phase2 data may update the archived release snapshot and asset resolution, but it must not rewrite reviewed page bytes during Publish. Unregistered targets retain the historical `review` parameter-sync behavior. If current Base copy must replace an approved target's frozen review copy, sync/re-seed it before approval, review the resulting layout, and explicitly reapprove the reference content contract before Publish.
- on a local worker, if a same-named local branch for `Git_ref` already exists, the queue uses that branch directly so local review edits can be built before they are pushed upstream
- if that fetch hits a transient GitHub network failure but the worker already has the same `origin/<Git_ref>` or local branch cached, the queue reuses the cached ref and keeps building from the intended review content
- direct `build.py` actions still write Build Draft Package outputs to the current repo [`../docs/_build/`](../docs/_build) tree by default
- for local verification, use [`../scripts/local_build.py`](../scripts/local_build.py), [`../scripts/local_build.ps1`](../scripts/local_build.ps1), or [`../scripts/local_build.sh`](../scripts/local_build.sh); they default `check`, `diff-report`, `release-manifest`, `publish`, and other staging-safe local actions to `.tmp/staging`
- explicit `--staging-root <dir>` or `AUTO_MANUAL_STAGING_ROOT=<dir>` still redirect generated `docs/_build`, `reports/version_tracking`, and `reports/releases` under another isolated root when needed
- Print Publish stages IDML/LaTeX/DOCX/PDF/ZIP/Markdown under the Git-ignored runtime tree [`../reports/releases/<model>/<region>/<lang>/versions/<version>/`](../reports/releases), uploads formal deliverables to Feishu or short-lived GitHub Actions artifacts, and freezes the exact manifest-backed phase2 root under `versions/<version>/snapshot/`; it does not commit those binaries or build/deploy HTML. Web Publish is a separate action: it always refreshes approved Web assets, stages MyST and verification HTML under `versions/<version>/web/`, writes `latest/web/publish_meta.json`, incrementally assembles the `Hello-Docs/publish:docs/publish/` candidate, opens or updates a `docs/publish/**`-only PR into `Hello-Docs/main`, and writes the deterministic RTD URL to `HTML_link`.
- A versioned Publish must start from a clean tracked worktree. The queue's one
  bounded exception is the active `docs/_review/<model>/<region>` overlay: its
  bytes must exactly match the row's resolved review-branch commit, every
  tracked change must remain inside that target, and the manifest records the
  review ref, commit, target path, and Git tree SHA. That complete file/blob
  check happens once at publish entry; the verified tree SHA is then carried
  through review parameter sync and target-asset staging so the late manifest
  does not mistake deterministic build products for new source files. A
  missing or changed verified tree SHA, hand edit, sibling target change, or
  incomplete provenance still fails closed. Publish
  derives `SOURCE_DATE_EPOCH` from the trusted `main` toolchain commit, uses
  content-addressed staged assets, and canonicalizes DOCX metadata/container
  timestamps so the release DOCX, Markdown, and PDF have a byte-equivalence
  contract recorded in the manifest.
  Run `python build.py release-rebuild-verify --manifest <manifest.json>` on the
  recorded toolchain to validate it. The command verifies the archived snapshot,
  creates a detached worktree at `git_sha`, restores the exact recorded review
  overlay when present, republishes from the archive into a temporary staging
  root, and compares all three SHA-256 values. The default
  `rebuild_verification.json` report sits beside `snapshot/` in the version
  directory; snapshot drift, toolchain drift, missing provenance, or any output
  mismatch fails closed.
- Every versioned release manifest and queue `publish_meta.json` carries the
  same deterministic `release_tag`, formatted as
  `manual-release/<model>/<region>/<all-build-languages>/<version>`. The build
  does not mutate Git. After the release artifacts and rebuild evidence pass,
  use `python tools/release_tag.py --manifest <manifest.json>` to preview the
  binding, then `--write --push` to create the annotated tag. Its annotation
  binds the full `git_sha`, manifest SHA-256, and frozen snapshot SHA-256;
  retries are idempotent and any tag/manifest rebind fails closed. See the
  operator rollback procedure in
  [`../user-guide/closed_loop_ops_guide.md`](../user-guide/closed_loop_ops_guide.md#410-发布标记与回滚k14).
- [`../scripts/process_build_queue.ps1`](../scripts/process_build_queue.ps1): Windows automation wrapper for `process-build-queue`; it restores the local Node/npm path plus the `FEISHU_PHASE2_*` user env vars, runs with `--staging-root .tmp/staging`, forwards any extra queue args such as `--dry-run` or `--record-id`, and writes run logs into [`../.tmp/process-build-queue/`](../.tmp/process-build-queue)
- [`../scripts/process_build_queue_feishu.ps1`](../scripts/process_build_queue_feishu.ps1): one-click Windows wrapper that forces Feishu/wiki-only upload before calling the shared queue wrapper
- the DingTalk AliDocs mirror-upload chain was retired on 2026-07-02: its one-click queue wrapper, browser-session upload CLI, and setup guide were removed, and `lark_drive` (Feishu/wiki) is the only artifact upload provider in operation; the queue-side `dingtalk_alidocs_session` provider code remains dormant pending a separate removal decision
- `listen-build-queue`: start the push-based Feishu long-connection listener, auto-subscribe the current `Document_link` base to docs events with the current user identity, keep the long connection on the same user identity, and trigger `process-build-queue` immediately when the `是否立即构建` checkbox is checked on a `Document_link` row
- `python build.py listen-message-control --config configs/config.us.yaml`: start the local Feishu IM long-connection listener; it listens for `im.message.receive_v1`, routes the same bounded natural-language control actions as the webhook adapter, and avoids any HTTP callback server or tunnel
- `python build.py translation-memory --config configs/config.us.yaml --model JE-1000F --region US --query-text "USB-C 100W Port" --lang fr --table spec-master`: preferred compact lookup for multilingual terminology memory before asking OpenClaw to translate or rewrite manual copy
- use `bitable-translation-memory` alone for one-shot sentence or terminology lookups, and pair it with `manual-rewrite-with-tm` when the ask is a whole section/file rewrite or an explicit TM-guided preservation job
- `node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch ...`: local OpenClaw control CLI for `start-review`, `build-draft`, and `publish`; `publish` now requires an explicit `confirm` token so the command shape is `node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch publish <record_id> confirm`
- [`../scripts/listen_build_queue.ps1`](../scripts/listen_build_queue.ps1): Windows listener wrapper for `listen-build-queue`; it restores the local Node/npm path plus the `FEISHU_PHASE2_*` user env vars, runs with `--staging-root .tmp/staging`, and writes run logs into [`../.tmp/build-queue-listener/`](../.tmp/build-queue-listener)
- [`../.github/workflows/feishu-build-queue.yml`](../.github/workflows/feishu-build-queue.yml): `main`-owned GitHub-hosted Publish queue worker for the remote repo; it is normally woken by OpenClaw / natural-language control through `workflow_dispatch`, bootstraps `lark-cli` with `FEISHU_APP_ID/FEISHU_APP_SECRET`, sets `FEISHU_PHASE2_IDENTITY=bot`, and then consumes the selected `Document_link` queue row. Its former 5-minute `schedule` block is kept commented out in the workflow file and should only be re-enabled after the bot secrets and Feishu permissions are healthy enough for unattended runs.
- because the queue worker imports the cloud doc **as the bot** (`FEISHU_PHASE2_IDENTITY=bot`), the doc would otherwise be bot-owned and the operator could only make a 副本; right after the import the leaf calls [`../tools/queue_cloud_doc_finalize.py`](../tools/queue_cloud_doc_finalize.py) `finalize_cloud_doc` to (1) grant the operator `full_access` so they edit the registered doc directly, and (2) place the doc in a **dedicated review-doc wiki node** — `FEISHU_REVIEW_DOC_WIKI_NODE` (a `.../wiki/<token>` URL or bare token), resolved to its `space_id` + `parent_wiki_token`. The review doc lives in its own knowledge-base node (e.g. `过程文档管理`), **not** co-located with the Word artifact (which sits under the build table's node). Both steps are **best-effort** (a failure logs `[build-queue] WARNING` and never fails the build); the broad `drive:drive` (application identity) scope already covers the grant + move. When `FEISHU_REVIEW_DOC_WIKI_NODE` is unset the doc is left in the bot's drive. The `飞书云文档` written back is the post-move wiki URL when the move succeeds, else the import URL.
  - the grantee is resolved by `resolve_cloud_doc_grantee`: the build row's `operator_union_id` (a union id) when present, else a configured **`FEISHU_CLOUD_DOC_DEFAULT_EDITOR`** env (an `ou_…`/`on_…` id, or an explicit `openid:…`/`unionid:…`). The `operator_union_id` column (alias `钉钉会话键`) is currently unpopulated for every build row, so without the default-editor env the auto-grant is a no-op — set `FEISHU_CLOUD_DOC_DEFAULT_EDITOR` to the operator's open id in the queue-worker environment to make new builds auto-share. Existing docs can be back-filled out of band (one `drive permission.members create --as bot` per registered doc).
  - **baseline doc (copy-doc model):** right after the editable doc, the leaf imports the **same markdown a second time** as a frozen **baseline (R0)** — placed in the same review-doc node but with `grant=False` (no edit access, so it stays un-edited) — and records its link in the build table's **`基线文档`** field (the editable doc's link is in `飞书云文档`). `run-review-branch` later prefers this `基线文档` doc as the diff baseline: it fetches both docs and diffs them (render-vs-render → only the reviewer's real edits), which is cleaner than, and takes precedence over, the on-branch `.backport/` baseline. Best-effort + only on `can_write_feishu_cloud_doc` builds.
- [`../.github/workflows/feishu-start-review.yml`](../.github/workflows/feishu-start-review.yml): `main`-owned GitHub-hosted review-init worker for the remote repo; it consumes the review-init table, force-reseeds `docs/_review` from the latest base branch, force-updates the review branch when needed, pushes the branch, and writes back `Git_ref` plus `PR_url`
- the GitHub-hosted Feishu workers now share [`.github/actions/feishu-common-setup/action.yml`](../.github/actions/feishu-common-setup/action.yml) and [`../scripts/validate_required_env.sh`](../scripts/validate_required_env.sh), so setup and required-env changes only have one maintained source; that shared setup now pulls Pandoc from the official release action instead of Ubuntu `apt`, and it reuses pip/npm download caches to keep startup latency stable when GitHub-hosted network fetches are slow
- for local macOS/Linux Word bundle exports that use a reference DOCX, require `pandoc 3.9.0.2` or newer; the bundle exporter now auto-selects a compatible installed `pandoc` when multiple versions are present, and older versions can emit an invalid `/word/media/` content-type override that makes Microsoft Word repair the generated `.docx`
- the review-init worker now treats `Start Review` as a force-reseed action, so committed `docs/_review/<model>/<region>/` content on the base branch no longer blocks the worker
- for remote immediate builds after merge to `main`, use OpenClaw / Feishu automation to send a GitHub `workflow_dispatch` request to `feishu-build-queue.yml` on `main`; the queue worker still treats `是否触发文档构建 = Y` as the actual build request, while `是否立即构建` only decides whether to wake the remote workflow immediately
- before enabling that remote worker, make sure the Feishu app/bot has read access to the phase2 source tables and write access to the `Document_link` table; without write permission the run can build and upload but cannot write back queue status
- if the imported Draft cloud doc should be moved into wiki automatically, give that same user/bot identity edit/container permission on the destination review-doc wiki parent node; otherwise `飞书云文档` retains the import URL and the best-effort move warning stays visible in status
- `publish`: run `check -> diff-report -> word -> pdf -> md -> release-manifest` for one explicit target
- `release-manifest`: write JSON / CSV release traceability for one explicit target; when `--version <version>` is present, freeze and bind the phase2 input at the version archive path
- `handoff`: create a minimal explicit target design handoff package with rule-based diff outputs and traceability metadata
- `preview`: materialize one exact page selector under a preview-only output root
- `fast`: materialize a runtime draft only, with `prepare-only + no-clean`
- `html`, `word`, `pdf`, `md`: prepare RST first, then export; Markdown uses a native MyST writer when Pandoc provides one, otherwise a MyST-compatible CommonMark writer
- `all`: export `html + word + pdf + md`
- `diff-report`: export Git-based revision tables, defaulting to the resolved target review root
- `clean`: remove [`docs/_build/`](../docs/_build), [`docs/_review/`](../docs/_review), old legacy output directories, and generated [`params.tex`](../docs/renderers/latex/params.tex)
- `build_us_jp_manuals.ps1`: PowerShell wrapper over the shared Python matrix runner for the fixed `US/en + US/es + US/fr + JP/ja` target set; supports either `--formats` or one explicit `--build-action`
- `--open-html`: after the batch finishes, open the generated HTML entry pages for the selected language set
- DOCX export normalizes image relationships to embedded media before the final style pass so Feishu / other third-party viewers are less likely to hide image-backed table rows in preview

Start Review, Build Draft Package, Publish:

- the queue worker no longer refreshes `data/phase2` unconditionally; `Document_link.是否强制刷新数据` now decides whether that document group pulls a fresh phase2 snapshot or reuses the current local one
- `data_sync` is the row-level writeback for that decision: `refreshed`, `skipped`, or `failed`
- queue-driven builds treat Feishu phase2 tables as the structured-data source of truth; repo `data/phase2/*.csv` files are materialized snapshots, not the authoring source
- use `process-build-queue --workflow-action build-draft-package` when a Build Draft Package row should be built from the current review tree
- review-source checks scope blocking `Spec_Master` row validation, plus footnote definition/reference checks, to target identity and generated-page recipe inputs, so stale or retired target rows and unreferenced footnote definitions do not block an already seeded review bundle; runtime-source checks keep strict target-row validation
- use `process-build-queue --workflow-action publish` for the print release path: `build.py publish`, PDF upload, release staging and optional cloud-doc import
- use `process-build-queue --workflow-action web-publish` for the responsive path: forced `sync-data`, then web-profile `check -> md -> html`; `Git_ref` is mandatory and print artifact writebacks are intentionally skipped
- `process-build-queue --record-id <record_id>` narrows one run to one `Document_link` row
- `feishu-start-review.yml` is the Start Review worker on `main`; if Feishu triggers it, dispatch it on `main` so review-start always uses the latest workflow definition
- review PRs created by that trusted Feishu Start Review worker automatically approve their `Manual Validation` and `Review Preview Package` checks; ordinary external pull requests still use GitHub's approval gate
- `feishu-build-queue.yml` is the Publish-stage worker for `main`
- `feishu-draft-build-queue.yml` is the Build Draft Package worker on `main`
- `feishu-web-publish-queue.yml` is the Web Publish worker on `Hello-Docs/main`; it advances the generated `publish` candidate, enforces a `docs/publish/**`-only PR into `main`, and writes RTD `HTML_link`
- Draft and Publish use the same `feishu-document-queue-<record_id>` concurrency domain; a single-row run is serialized against the same Document_link row across both workflows, while batch dispatches share the conservative `batch` slot. Start Review consumes a different queue identity and uses `feishu-review-init-queue-<record_id>`.
- Web Publish owns one global `feishu-web-publish-branch` mutex because every target updates one aggregate RTD catalog and one `publish -> main` PR. It preserves existing target sources, reconciles the candidate history with current `main`, checks that the three-dot diff contains only `docs/publish/**`, and uses an ordinary non-force `HEAD:publish` push, so concurrency or branch drift fails instead of discarding another target.
- the repo ships one OpenClaw plugin package under [`../integrations/openclaw/auto-manual-control-layer/`](../integrations/openclaw/auto-manual-control-layer); it is the supported control-layer package for Start Review, Build Draft Package, Publish, and Web Publish
- OpenClaw dispatches still call only the `main`-owned workflows; they add `openclaw_dispatch_nonce` as a correlation input and the workflows upload `openclaw-run-metadata` as a machine-readable status artifact
- OpenClaw dispatches `start-review`, `build-draft`, and `publish` with the resolved Feishu `record_id`; the optional `Task_id = Document_ID + "_" + Workflow_action` field is used during lookup to distinguish same-document build/publish rows, while Start Review can be resolved from `Document_Key` alone. Later `start-review` retries against rows already updated to `InReview` with `Git_ref` return the completed row instead of creating extra GitHub Actions failures.
- Feishu IM natural-language control can execute config-scoped batch Draft builds when the message names a model, a market, and manual copy or config scope, for example `输出JE-1000F的所有欧规说明书文案`, `构建JE-1000F的所有欧规说明书文案`, `基于配置构建JE-1000F的欧规`, `触发 JE-2000E_EU 欧规整包构建`, or the implicit-all form `构建JE-1000F的欧规说明书文案`. The resolver infers a `Task_id` prefix such as `JE-1000F_EU_`, constrains the action to `Build Draft Package`, and only keeps rows where `是否触发文档构建` is enabled. When no market is named, `构建JE-1000F说明书文案` uses the broader `Task_id` prefix `JE-1000F_`, so every triggered Build Draft Package row for that model is eligible across markets. Versioned market-level asks such as `构建 JE-1000F_EU_1.0 的欧规说明书文案` also add `Version=1.0`. The adapter then dispatches one `queue-execute --allow-multiple --no-wait` batch with the exact record ids; all rows for the action share one run id and the worker receives the same `queue_record_ids` input. `最新` does not collapse batch Draft requests by shared `Document_Key`; each language row remains eligible when its trigger checkbox is enabled. `是否强制刷新数据` is not a target selector; the queue worker reads it as a build-time input and runs `sync-data` before the build when it is checked.
- Feishu IM manual-index questions are read-only and run before queue resolution. `查 JE-2000F 的说明书链接` returns rows from `发布文档管理`; `查询各产品的说明书` returns an inventory; `获取说明书总览信息` returns counts by region/source language/document type/category. Build-copy phrases containing `说明书文案` stay on the Build Draft queue path.
- exact Build Draft Package / Publish dispatches now fail fast when the selected Document_link row does not have `是否触发文档构建` enabled; this prevents a targeted workflow from exiting successfully without building anything.
- if Feishu triggers the Build Draft Package worker, dispatch it on `main`; the actual build source is resolved from `Document_link.Git_ref`, and rows missing `Git_ref` fail fast
- if Feishu triggers the Publish worker, dispatch it on `main`; the workflow definition stays on `main`, while `Document_link.Git_ref` still controls the fetched review branch when present
- if a Publish-stage row also carries `Git_ref`, the Publish worker keeps `main` only as the orchestration branch and fetches the actual build source from that review branch
- in both Draft and Publish queue builds, `Git_ref` is treated as a review-content branch: the worker keeps the latest `main` code/toolchain and overlays only `docs/_review` from `Git_ref`, so review-branch edits outside `docs/_review` are not part of queue builds
- Build Draft Package assumes the document is already in review; use `process-review-start-queue` or `feishu-start-review.yml` first to create the branch and seed `docs/_review`

Windows cleanup note:

- build actions except `fast` run with clean enabled unless you pass `--no-clean`
- if cleanup fails with a file-in-use error under [`docs/_build/`](../docs/_build), close File Explorer, browser, Word, or PDF windows pointing at that target output and rerun
- `--no-clean` is the temporary workaround when you only need to rebuild in place

GitHub validation note:

- `Manual Validation` is the repository CI workflow
- `Manual Validation` uses `tests/fixtures/phase2` for check/doctor/schema-drift smoke coverage so GitHub runners do not require a live `data/phase2` snapshot. The schema-drift gate also validates `data/source_table_contracts/phase2_source_tables.json` against fixture/local snapshot headers, so source-table identity or writable-field drift is caught before a live Feishu run.
- `python build.py doctor --data-plane --config <config> --model <model> --region <region> [--data-root <snapshot>]` is the read-only new-line data-plane preflight: it checks the complete phase2 manifest/files and required target `Spec_Master` rows before a build. It does not sync Feishu or write source data, and requires one explicit model/region.
- `Manual Validation` keeps the stable `check-en` and `check-jp` jobs and also runs [`../tools/ci_check_targets.py`](../tools/ci_check_targets.py), which discovers every `configs/config*.yaml`, runs `build.py check` for targets represented in the fixture snapshot, and reports missing `document_key` rows as explicit `SKIP`. Coverage is reported as `PASS/(PASS+SKIP+FAIL)`; the tracked [`../.github/ci_check_targets_skip_baseline.json`](../.github/ci_check_targets_skip_baseline.json) carries **two** no-increase ratchets, `skip_count` and `fail_count`. Stage 1 invokes the driver with `--observation`, so the FAIL rows already recorded in `fail_count` are reported without blocking the lane — but one more than that fails it, as does a SKIP-ratchet increase. The FAIL ratchet is what makes the observation lane meaningful: `--observation` alone reported a target sliding from `PASS` to `FAIL` without turning the job red, so only `check-en` and `check-jp` (JE-1000F/US and JE-1000F/JP) were genuinely gated. Both baselines are pinned by `tests/test_ci_check_targets.py`, so removing `fail_count` to silence a regression fails the unit suite instead.
- [`../.github/workflows/nightly-render.yml`](../.github/workflows/nightly-render.yml) runs daily and on manual dispatch. Its credential-free [`../tools/nightly_render.py`](../tools/nightly_render.py) driver derives one `doctor` run from every registered config, then builds and structurally checks the JE-1000F US English production IDML pilot against `tests/fixtures/phase2`. The JSON report records per-config failures plus the pilot path and SHA-256; no live Feishu snapshot is read.
- When a new config is added, add its fixture rows through the normal fixture-refresh workflow before lowering the skip ratchet. A config-derived `SKIP` is not counted as coverage.
- Refresh one target's committed fixture rows with `python tools/data_snapshot.py fixture-refresh --document-key <MODEL_REGION> --source-root data/phase2 --fixture-root tests/fixtures/phase2`; the default is a dry-run, and `--write` applies only that target's rows, copies referenced attachments, and recomputes manifest hashes. Do not replace the entire fixture tree from a live mirror.
- that workflow now runs `python -m ruff check build.py integrations tools tests scripts` as the minimal static gate before the heavier unit/build jobs
- that workflow now also runs `npm ci && npm test` in [`../integrations/openclaw/auto-manual-control-layer/`](../integrations/openclaw/auto-manual-control-layer) so the OpenClaw command bridge stays covered in CI
- that same workflow now also runs stable smoke paths for `build.py diff-report` and `build.py release-manifest`
- that same workflow now also runs `python tools/check_maintainability_guardrails.py` so the current hotspot wrappers and validators do not quietly grow back into giant files
- the maintainability gate includes `python tools/check_language_literal_ratchet.py check`, which records remaining multi-language literal tables and fails on new residue
- `build.py check` scans template and prepared bundle RST files for duplicated list text across normal RST and raw HTML branches; maintainers should treat the RST list as the source wording and keep renderer-specific copies aligned whenever manual prose changes
- `build.py check` preflights every prepared FCC page through the document and web renderer profiles with the resolved target language. FCC language coverage is derived from manifest entries in tests, so a new FCC locale must add its governed right-column marker and keep the required opening line-block structure before it can pass validation.
- pull requests run the required merge-gating checks
- pushes to `main` run the same workflow again after merge
- feature branches no longer run a duplicate `push` validation pass in GitHub
- `Review Preview Package` is a separate artifact workflow for design sharing and does not gate merge
- `Review Preview Package` now runs a smoke packaging pass with `--skip-word` and verifies the expected packaged preview files before artifact upload

Git branch safety note:

- start a new branch with `powershell -ExecutionPolicy Bypass -File scripts/start_branch.ps1 <type>/<area>-<topic>` on Windows or `./scripts/start_branch.sh <type>/<area>-<topic>` on mac/Linux so the branch is created from the latest `origin/main`; use a change-type prefix such as `feat/`, `fix/`, `refactor/`, or `docs/`, never an agent-name prefix
- enable the repo-managed pre-push guard with `git config core.hooksPath .githooks`
- that guard now runs through the shared [`../scripts/git_branch_guard.py`](../scripts/git_branch_guard.py) core instead of a bash-only hook, with [`.githooks/pre-push.cmd`](../.githooks/pre-push.cmd) and [`.githooks/pre-push.ps1`](../.githooks/pre-push.ps1) kept as Windows-native companion launchers
- the guard blocks pushes from branches that do not contain the latest `origin/main`; use `git push --no-verify` only when the older base is intentional
- if a PR adds a new helper boundary or changes workflow ownership, update the owning docs and [`dev/orchestration_module_map.md`](./dev/orchestration_module_map.md) in the same change instead of leaving the new rule as tribal knowledge

## 2. Config Rule

Do not create one config file per model.

Current shared config families:

- [`configs/config.us.yaml`](../configs/config.us.yaml): shared EN / US template family
- [`configs/config.us-en.yaml`](../configs/config.us-en.yaml): canonical US English single-language review / CI / explicit review-preview landing target
- [`configs/config.ja.yaml`](../configs/config.ja.yaml): shared JP template family
- [`configs/config.zh.yaml`](../configs/config.zh.yaml): shared CN zh template family backed by [`docs/manifests/manual_zh.yaml`](../docs/manifests/manual_zh.yaml)
- [`configs/config.eu.yaml`](../configs/config.eu.yaml): shared EU merged family backed by [`docs/manifests/manual_eu.yaml`](../docs/manifests/manual_eu.yaml)
- [`configs/config.eu-en.yaml`](../configs/config.eu-en.yaml), [`configs/config.eu-fr.yaml`](../configs/config.eu-fr.yaml), [`configs/config.eu-es.yaml`](../configs/config.eu-es.yaml), [`configs/config.eu-de.yaml`](../configs/config.eu-de.yaml), [`configs/config.eu-it.yaml`](../configs/config.eu-it.yaml), and [`configs/config.eu-uk.yaml`](../configs/config.eu-uk.yaml): explicit EU single-language entrypoints backed by [`../docs/manifests/manual_eu-en.yaml`](../docs/manifests/manual_eu-en.yaml) plus the corresponding [`../docs/manifests/manual_eu-single-*.yaml`](../docs/manifests) stacks
- [`configs/config.us-en.yaml`](../configs/config.us-en.yaml), [`configs/config.us-es.yaml`](../configs/config.us-es.yaml), [`configs/config.us-fr.yaml`](../configs/config.us-fr.yaml), and [`configs/config.pt-br.yaml`](../configs/config.pt-br.yaml) now inherit shared single-language US defaults from [`../configs/config-bases/us-single-language-base.yaml`](../configs/config-bases/us-single-language-base.yaml); keep shared defaults there and keep language-specific page stacks in [`../docs/manifests/manual_us-single-en.yaml`](../docs/manifests/manual_us-single-en.yaml), [`../docs/manifests/manual_us-single-es.yaml`](../docs/manifests/manual_us-single-es.yaml), [`../docs/manifests/manual_us-single-fr.yaml`](../docs/manifests/manual_us-single-fr.yaml), and [`../docs/manifests/manual_pt-br.yaml`](../docs/manifests/manual_pt-br.yaml)

Page-stack note:

- shared config families may resolve their page stack through `paths.page_manifest`
- keep manifest-driven page order changes under [`docs/manifests/`](../docs/manifests)
- for a genuine model-only generated-page layout exception, keep the family manifest and declare `model_overrides.<MODEL>.recipe` / `template` on that `generated_page`; the default recipe/template remains the path for every other model
- keep merged-language and single-language preface components separate: `manual_au-en.yaml` uses the English-only `page_shared/en/00_preface_single_language.rst`; the merged US preface remains the trilingual `page_shared/en/00_preface.rst`
- do not point a single-language manifest at a preface containing language-tagged blocks outside `build.languages`; the language-parity gate rejects that bundle

Pass target differences through:

- `--model`
- `--region`
- `build.targets`
- generated `data/phase2/*.csv` snapshots

Mirror repository sync rule:

- [`../.github/workflows/sync-hello-docs.yml`](../.github/workflows/sync-hello-docs.yml) runs only in `Bingboom/auto-manual` on `main` pushes or manual dispatches from `main`
- the workflow imports the exact source Git tree into `Bingboom/Hello-Docs` and creates a mirror commit from that tree, so checkout attributes cannot rewrite blobs such as mixed-line-ending CSV files; it does not copy repository Secrets or Variables
- configure `HELLO_DOCS_SYNC_TOKEN` in the source repo with write access to `Bingboom/Hello-Docs` contents and workflows, because the mirrored tree includes `.github/workflows/**`
- keep code changes in `Bingboom/auto-manual`; keep the alternate Feishu Base IDs, Feishu app credentials, OpenClaw credentials, and queue/runtime toggles as GitHub Secrets / Variables in `Bingboom/Hello-Docs`
- set the mirror repo variable `FEISHU_BUILD_QUEUE_PAUSED=true` until the alternate Feishu credentials and table/view bindings are present; Feishu runtime workflows such as `feishu-build-queue.yml`, `feishu-draft-build-queue.yml`, `feishu-start-review.yml`, and `cred-health-check.yml` skip only in `Bingboom/Hello-Docs` while this mirror variable is true, so a same-named variable in `Bingboom/auto-manual` does not change the source repo behavior
- copy [`../scripts/hello_docs_binding.env.example`](../scripts/hello_docs_binding.env.example) to a gitignored local file such as `.tmp/hello-docs-binding/env.sh`, fill the alternate Feishu/OpenClaw values there, then run [`../scripts/configure_hello_docs_binding.sh --env-file .tmp/hello-docs-binding/env.sh --dry-run`](../scripts/configure_hello_docs_binding.sh) first and rerun without `--dry-run`; add `--include-optional` when the env file also has mirror-only Vercel, DingTalk, Feishu IM, Cloudflare tunnel, or OpenClaw adapter variables, and add `--unpause` only when the audit should also flip `FEISHU_BUILD_QUEUE_PAUSED=false`
- run [`../scripts/audit_hello_docs_binding.sh --report-only`](../scripts/audit_hello_docs_binding.sh) to check source/mirror tree parity, the source sync token, mirror variables, required mirror secret names, the Actions PR-creation permission, and optional Feishu IM / OpenClaw entries without exposing secret values
- enable Actions PR creation on the mirror repo, otherwise `feishu-start-review.yml` pushes the review branch but the PR step fails with `403 "GitHub Actions is not permitted to create or approve pull requests."` — the workflow already declares `pull-requests: write`, but the account/repo toggle `can_approve_pull_request_reviews` must also be on. Turn it on with `gh api -X PUT /repos/Bingboom/Hello-Docs/actions/permissions/workflow -f default_workflow_permissions=read -F can_approve_pull_request_reviews=true` (the audit reports this as `Mirror Actions PR-creation permission`)
- before unpausing `Bingboom/Hello-Docs`, configure its own repository secrets for the remote Feishu workers: `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_PHASE2_BASE_TOKEN`, `FEISHU_PHASE2_MODEL_CAPABILITIES_TABLE_ID`, `FEISHU_PHASE2_SPEC_ROWS_SOURCE_TABLE_ID`, `FEISHU_PHASE2_SPEC_ROWS_SOURCE_VIEW_ID`, `FEISHU_PHASE2_PAGE_PLACEHOLDERS_SOURCE_TABLE_ID`, `FEISHU_PHASE2_PAGE_PLACEHOLDERS_SOURCE_VIEW_ID`, `FEISHU_PHASE2_SPEC_FOOTNOTES_TABLE_ID`, `FEISHU_PHASE2_SPEC_FOOTNOTES_VIEW_ID`, `FEISHU_PHASE2_SPEC_NOTES_TABLE_ID`, `FEISHU_PHASE2_SPEC_NOTES_VIEW_ID`, `FEISHU_TRANSLATION_MEMORY_BASE_TOKEN`, `FEISHU_TRANSLATION_MEMORY_TABLE_ID`, `FEISHU_TRANSLATION_MEMORY_VIEW_ID`, `FEISHU_PHASE2_SYMBOLS_BLOCKS_TABLE_ID`, `FEISHU_PHASE2_SYMBOLS_BLOCKS_VIEW_ID`, `FEISHU_PHASE2_LCD_ICONS_TABLE_ID`, `FEISHU_PHASE2_LCD_ICONS_VIEW_ID`, `FEISHU_PHASE2_TROUBLESHOOTING_TABLE_ID`, `FEISHU_PHASE2_TROUBLESHOOTING_VIEW_ID`, `FEISHU_PHASE2_VARIABLE_DEFAULTS_TABLE_ID`, `FEISHU_PHASE2_VARIABLE_DEFAULTS_VIEW_ID`, `FEISHU_PHASE2_VARIABLE_LANG_OVERRIDES_TABLE_ID`, `FEISHU_PHASE2_VARIABLE_LANG_OVERRIDES_VIEW_ID`, `FEISHU_PHASE2_MANUAL_COPY_SOURCE_TABLE_ID`, `FEISHU_PHASE2_MANUAL_COPY_SOURCE_VIEW_ID`, `FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID`, and `FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID`; add `FEISHU_PHASE2_DOCUMENT_LINK_WIKI_PARENT_TOKEN` only when the mirror should force a specific wiki parent
- configure optional mirror-only repository secrets as needed: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID` for publish HTML deploys; DingTalk secrets plus `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER=dingtalk_alidocs_session` only if the mirror should also sync DingTalk artifacts; Feishu IM adapter secrets such as `FEISHU_IM_APP_ID`, `FEISHU_IM_APP_SECRET`, `FEISHU_IM_VERIFICATION_TOKEN`, `FEISHU_IM_ENCRYPT_KEY`, optional `FEISHU_MANUAL_INDEX_BASE_TOKEN`, and `CLOUDFLARED_TUNNEL_TOKEN` only if that adapter is deployed for the mirror
- when OpenClaw dispatches into the mirror, point the OpenClaw runtime or gateway environment at `Bingboom/Hello-Docs` through `AUTO_MANUAL_GITHUB_REPO_OWNER=Bingboom` and `AUTO_MANUAL_GITHUB_REPO_NAME=Hello-Docs` or by running it from a `Hello-Docs` checkout; use the new Feishu app values for `FEISHU_IM_APP_ID` / `FEISHU_IM_APP_SECRET` when the Feishu IM adapter is deployed for the mirror, and keep the OpenClaw plugin GitHub token in the OpenClaw plugin config or runtime environment because repository secrets are not readable by a local gateway unless explicitly exported

Phase2 snapshot rule:

- keep the shared config families, but use a valid generated [`../data/phase2/`](../data/phase2) snapshot as the default build/review/publish source when it exists
- `data/phase2/` is gitignored local snapshot output; mirror repositories should sync their own Feishu Base into this path instead of committing tenant-specific CSVs or attachments
- the one exception is [`../data/phase2/page_registry.csv`](../data/phase2/page_registry.csv): it is the repo-maintained page-structure input that `sync-data` copies into the snapshot, so it stays tracked; without it a fresh checkout (including the CI cred health check) cannot sync at all
- [`../tests/fixtures/phase2`](../tests/fixtures/phase2) is the committed CI/test fixture snapshot; do not treat it as a live authoring source or mirror-specific Base export
- the automatic phase2 default requires a complete manifest-backed core snapshot: `spec_master`, `spec_footnotes`, `spec_notes`, `symbols_blocks`, `troubleshooting`, `lcd_icons`, `variable_defaults`, `variable_lang_overrides`, and `manual_copy_source` must all appear as requested/synced tables in `snapshot_manifest.json`; derived `row_key_mapping`, `spec_titles.csv`, `Localized_Copy.csv`, and `Status_Words.csv` must also be recorded; partial `sync-data --table ...` runs are allowed, but they are treated as explicit experiment snapshots unless you pass them through `--data-root`
- explicit `--data-root` still overrides the default, so you can point `rst`, `check`, `diff-report`, `release-manifest`, `publish`, and `process-build-queue` at a different root when needed
- `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2` is still the explicit refresh step for the phase2 snapshot
- static legal/support placeholders such as `WARRANTY_EMAIL` and `LEGAL_COMPANY_NAME` are injected from `build.rst_substitutions` in the active config; keep US values in US configs and override EU / pt-BR values there instead of hardcoding region-specific names in shared templates
- for the review-init worker, use an isolated snapshot root such as `.tmp/review-start/phase2`; the worker syncs fresh data there before it seeds `docs/_review`
- `python scripts/local_build.py check|diff-report|release-manifest|publish ...` keeps generated verification/build outputs under `.tmp/staging/docs/_build`, `.tmp/staging/reports/version_tracking`, and `.tmp/staging/reports/releases` without making the operator remember `--staging-root`
- `review` still writes the real repo `docs/_review` tree and does not accept `--staging-root`, so it is intentionally excluded from `local_build.py`
- [`../data/phase2/page_registry.csv`](../data/phase2/page_registry.csv) remains repo-maintained; `sync-data` copies it into isolated `--data-root` snapshots such as `.tmp/review-start/phase2` so runtime builds use the same page registry there
- page selection/applicability and [`../data/layout_params.csv`](../data/layout_params.csv) remain repo-maintained inputs

Only create a new config when one of these really changes:

- page stack
- template family
- output convention
- language family
- Word reference template

## 3. Standard Windows Flow

### 3.1 Validate Environment and Config

```powershell
python build.py validate --config configs/config.us.yaml
```

Equivalent low-level checks:

```powershell
python tools\validate_config.py --config configs/config.us.yaml
python tools\validate_layout_params.py --csv data\layout_params.csv
```

Minimal static check:

```powershell
python -m pip install ruff
python -m ruff check build.py tools tests scripts
```

The committed Ruff gate is intentionally small and low-noise. It currently checks bare `except`, undefined names, and unused local variables before CI runs the heavier unit/build validation paths.

If you use the Feishu-backed phase2 workflow, sync the frozen snapshot before runtime build:

```powershell
python build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --dry-run
python build.py sync-data --config configs/config.us.yaml --data-root data/phase2
python build.py process-build-queue --config configs/config.us.yaml
python build.py message-control-dry-run --message "publish JE-1000F us-merged from branch feature/review-123"
```

That command requires:

- a working `lark-cli` binary on `PATH`
- a valid local `lark-cli` login session
- the `FEISHU_PHASE2_*` environment variables referenced by [`../configs/config.us.yaml`](../configs/config.us.yaml) or [`../configs/config.ja.yaml`](../configs/config.ja.yaml)
- `FEISHU_TRANSLATION_MEMORY_BASE_TOKEN`, `FEISHU_TRANSLATION_MEMORY_TABLE_ID`, and `FEISHU_TRANSLATION_MEMORY_VIEW_ID` for Translation Memory rows that generate `Localized_Copy.csv` and `Status_Words.csv`
- `--dry-run` is the recommended machine-readiness check first; it now aggregates missing CLI, missing `FEISHU_PHASE2_*` bindings, and missing Translation Memory binding into one preflight error before any fetch
- `build.py` auto-loads `~/.auto-manual-phase2.env` at startup when that file exists (via [`../tools/local_env.py`](../tools/local_env.py)), so the bindings above can live in a single `$HOME` env file instead of being `source`-d into every shell — this is what lets a command runner such as the OpenClaw gateway run `sync-data` without a manual `source`. It does not override variables already set in the environment, and `AUTO_MANUAL_PHASE2_ENV_FILE` redirects the path
- on Windows, the default `sync.phase2.cli_bin: lark-cli` is resolved to the installed shim automatically during fetch, so you do not need a Windows-only config override
- when `spec_master` is included, the sync also refreshes [`../data/phase2/row_key_mapping.csv`](../data/phase2/row_key_mapping.csv) as the phase2 mirror of the row-label mapping table
- if you also use the Feishu `Document_link` build queue, set `FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID` and `FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID`; `process-build-queue` reuses the same `FEISHU_PHASE2_BASE_TOKEN`, auto-derives the current wiki destination from that base when possible, and optionally accepts `FEISHU_PHASE2_DOCUMENT_LINK_WIKI_PARENT_TOKEN` when you want to force a different parent wiki node
- `spec-master-rebuild --bootstrap-source-tables` also needs `FEISHU_PHASE2_DOCUMENT_KEY_TABLE_ID` and `FEISHU_PHASE2_ROW_KEY_TABLE_ID` so it can create source-table link fields against the copied Base's dictionary tables
- if you want Feishu/wiki primary plus DingTalk sync, set `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER=dingtalk_alidocs_session` plus either global `DINGTALK_DOCS_A_TOKEN`, `DINGTALK_DOCS_XSRF_TOKEN`, and `DINGTALK_DOCS_COOKIE` with optional `DINGTALK_DOCS_TARGET_NODE_URL` and `DINGTALK_DOCS_BX_V`, or a per-operator session registry under `AUTO_MANUAL_DINGTALK_SESSION_ROOT`; when a row carries `operator_union_id`, the worker first looks for `<session_root>/<operator_union_id>.json` before falling back to the global envs. `DINGTALK_DOCS_TARGET_NODE_URL` is only the default target, and checked rows with `DingTalk_target_node_url` can override it or supply the target on their own
- if Feishu/wiki remains primary, DingTalk mirror setup problems now degrade to `dingtalk_sync=failed` instead of aborting the whole build; blank or placeholder `-` target values are treated as unset and fall back to the default target when one exists
- if you want successful Publish runs to hand their artifacts to the DingTalk delivery agent, set `AUTO_MANUAL_DELIVERY_OUTBOX_ROOT` to an ignored directory (the repo ignores `/output/`); [`../tools/delivery_outbox.py`](../tools/delivery_outbox.py) then drops the print PDF, handoff zip, Word, and Markdown into `<root>/<job_id>/` with an immutable `delivery_manifest.json`, and the row records `delivery_outbox=ok|skipped|failed` alongside `dingtalk_sync=*`. `skipped` means the target is not listed in [`../data/dingtalk_delivery_map.csv`](../data/dingtalk_delivery_map.csv) and is a normal state; a delivery problem never fails a build whose artifact already reached the knowledge base. Verify a drop by hand with `python tools/delivery_outbox.py --manifest <root>/<job_id>/delivery_manifest.json`
- for local polling automation on Windows, schedule [`../scripts/process_build_queue.ps1`](../scripts/process_build_queue.ps1) instead of calling `python build.py process-build-queue ...` directly, so the scheduled run inherits the repo `.venv`, the local `lark-cli` shim path, and the saved `FEISHU_PHASE2_*` user env vars consistently; use [`../scripts/process_build_queue_feishu.ps1`](../scripts/process_build_queue_feishu.ps1) when you want the upload target fixed without touching env vars first
- for push-based immediate builds, add the `drive.file.bitable_record_changed_v1` event to the Feishu self-built app in Open Platform, publish the app change, then start [`../scripts/listen_build_queue.ps1`](../scripts/listen_build_queue.ps1) at login or from the Windows Startup folder; the listener will auto-subscribe the current base token on startup

### 3.2 Create a Runtime Draft

```powershell
python build.py rst --config configs/config.ja.yaml --model JE-1000F --region JP --source runtime
```

This creates:

- [`docs/_build/JE-1000F/JP/rst/`](../docs/_build/JE-1000F/JP/rst)

Use `--source runtime` when you want a fresh draft from template + data only.

If the model is only partially entered (for example a brand-new model still being populated), add `--draft-placeholders` to materialize anyway — missing required Spec_Master values render as `==MISSING:<FIELD>==` instead of aborting, so you can preview the layout and then fill the flagged rows. Strict builds (and `publish` / `release`) still fail fast with a report that names the model/region/lang and each missing binding. Do not use `--draft-placeholders` for publish.

### 3.3 Enter Review

```powershell
python build.py review --config configs/config.ja.yaml --model JE-1000F --region JP
```

This seeds:

- [`docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP)

After review starts, daily editing should happen in `_review`, not in `_build`.

### 3.4 Refresh Review After Data Changes

If you update any of these:

- [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- [`data/phase2/Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
- [`data/phase2/Spec_Notes.csv`](../data/phase2/Spec_Notes.csv)
- [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv), generated from `Manual_Copy_Source.csv` plus Translation Memory `manual_copy` rows
- [`data/phase2/symbols_blocks.csv`](../data/phase2/symbols_blocks.csv)
- [`data/phase2/troubleshooting_blocks.csv`](../data/phase2/troubleshooting_blocks.csv)

The dormant known `Spec_Master` value repairs are tracked in [`../data/spec_master_value_repairs.csv`](../data/spec_master_value_repairs.csv). The repair pass reads this CSV and fails closed on a missing, malformed, or duplicate repair key; do not add target/value patches back into Python.

Safety page note:

- US safety intro pages are maintained directly in [`docs/templates/page_us-en/safety_en.rst`](../docs/templates/page_us-en/safety_en.rst), [`docs/templates/page_us-fr/safety_fr.rst`](../docs/templates/page_us-fr/safety_fr.rst), and [`docs/templates/page_us-es/safety_es.rst`](../docs/templates/page_us-es/safety_es.rst)
- the standalone user maintenance instructions page is maintained in the shared templates, for example [`docs/templates/page_shared/en/01_user_maintenance_instructions.rst`](../docs/templates/page_shared/en/01_user_maintenance_instructions.rst), and each US/EU manifest includes it immediately before the `symbols` CSV page
- the JP manual maintains its safety intro in [`docs/templates/page_jp/safety_ja.rst`](../docs/templates/page_jp/safety_ja.rst) through [`docs/manifests/manual_jp.yaml`](../docs/manifests/manual_jp.yaml)
- edit those `safety_*.rst` files when a family's safety intro page needs copy/layout changes
- the detailed JP safety warnings remain in [`docs/templates/page_jp/01_meaning_of_symbols.rst`](../docs/templates/page_jp/01_meaning_of_symbols.rst)
- the old `content_blocks.csv` safety source has been removed from the active repo flow

Parallel-language template note:

- for manually maintained parallel-language prose templates, treat the source-language page as the structure owner
- when that source-language page changes shared headings, section order, placeholders, includes, or `.. only::` model gates, update the derived-language counterparts in the same change before review/build
- current example: keep the `charging.rst` JE-2000E battery-pack `.. only:: model_je_2000e` block aligned across `page_us-en`, `page_us-es`, `page_us-fr`, and `page_zh`
- before you touch page templates for a new Markdown intake, fill out [`dev/manual_template_intake_checklist.md`](./dev/manual_template_intake_checklist.md) to decide manifest mapping, placeholder policy, and validation scope first

Carrier tag axes:

- a page can gate a body on four axes: `model_<model>`, `region_<region>`, `lang_<lang>`, and `category_<product line>`
- the category is `build.skeleton_family` in the config (`BP` for the battery-pack line, `MAIN` when undeclared), resolved by `resolve_category` in [`tools/page_contracts.py`](../tools/page_contracts.py) — the same value the `category:` contract tier selects on, so a page's requirement and its `.. only::` body always agree
- both renderer planes emit it: Sphinx as `-t category_<value>` and the manual IR as a `category_<value>` base tag. Never add an axis to one plane only — `.. only::` omits an unmatched body silently, so a one-plane tag prints in the PDF and vanishes from IDML with no error
- prefer a category branch over cloning a page. Two carriers whose structure is identical and whose prose differs by product line belong in one file with two `.. only:: category_*` bodies; the parallel-language note above then applies once instead of twice

`symbols_blocks.csv` note:

- `image_path` stores the RST image reference path for each symbols-table icon
- when the phase2 authoring Base provides a `Figure` attachment, `sync-data` downloads it into `data/phase2/_attachments/symbols/` and writes that local file back to `image_path`
- use `block_type=table_row` for the normal symbol/meaning grid and `block_type=signal_row` for warning/caution/danger/note/tip signal metadata
- signal rows must include the four rendered `symbol_key` values `warning`, `caution`, `note`, and `tips`; add `danger` as a signal row for alert-label recognition when needed. Maintain visible signal labels and meanings in `Manual_Copy_Source.csv` with matching Translation Memory rows tagged `manual_copy`; `Localized_Copy.csv` is the generated runtime copy. The `label_*` and `aliases_*` columns in `symbols_blocks.csv` are compatibility mirrors for old variants and rewrite detection, not separate maintained copy; put editorial context in `notes`
- image alt text is derived from page titles, panel titles, `symbol_key`, or the corresponding signal-row `label_*`; do not maintain `copy_type=alt_text` rows in `Localized_Copy.csv`
- `Market` and `Model` select the target rows; `symbols_blocks.csv` does not use `Region`
- `Source_lang` stores the row's source-language code, using the same naming rule as [`Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- use `Market=Global` when one symbols row is shared across markets
- `sku_scope` is no longer used in [`symbols_blocks.csv`](../data/phase2/symbols_blocks.csv)

`troubleshooting_blocks.csv` note:

- maintain the online TROUBLESHOOTING Base table as the source, then refresh with `python build.py sync-data --config configs/config.us.yaml --table troubleshooting --data-root data/phase2`
- use `Region`, `Model`, and `Is_latest` to select rows for the target manual; blank placeholder rows are ignored by the renderer
- keep title, intro, headers, widths, and header-row settings in the active language RST template: `docs/templates/**/10_troubleshooting.rst`
- keep error-code rows and localized corrective measures in the TROUBLESHOOTING Base table; the RST template exposes `{{ troubleshooting_rows_rst }}` where those rows are inserted

`Spec_Master.csv` note:

- in Feishu, maintain `Page=specifications` rows in `规格参数明细` and maintain non-spec page placeholders in `页面占位参数`; `sync-data --table spec_master` reads those two source tables and writes the local read-model CSV
- `spec_row_key` is the first read-model key and `document_key` remains the target dimension field
- the `Page` column may now hold a comma-separated page list
- use `Product overview` for Product overview-only page-value rows
- use `Product overview, specifications,` when a row is intentionally shared by both pages
- `Row_label_source`, `Param_source`, and `Value_source` are the shared source-text columns; they should hold the row's source-manual text
- `Source_lang` stores that source-language code explicitly; use values such as `en`, `ja`, and `zh`, and do not rely on `Region` to infer it
- `document_key` is a derived helper column and may use either `[Model]_[Region]` or `[Model]_[Region]_[Source_lang]`
- `Row_order` is now the explicit row order inside each `document_key + Page + Section`, while `Line_order` controls the line order inside one logical row
- `Line_order` is required for rebuilds; use `1` for single-line rows and `1`, `2`, `3`, ... for multi-line rows under the same logical parameter
- generated `spec_titles.csv section_order` can hold the default order for visible spec sections, but a filled `Spec_Master.csv Section_order` overrides it
- `project_code` / `项目代码` is no longer part of `Spec_Master.csv`; target rows by `Region` + `Model`
- if a CLI/build target passes a document-key style model such as `JE-1000F_JP` or `JE-1000F-JP`, spec lookup first normalizes it back to the base model `JE-1000F` and still chooses rows by the explicit `Region`, so `JP` targets stay on `JP` spec rows
- `Row_label_en`, `Param_en`, and `Value_en` are no longer supported; rename them to `*_source` before importing or checking the sheet
- `Row_label_footnote_refs`, `Param_footnote_refs`, and `Value_footnote_refs` hold comma-separated `Footnote_id` values; do not handwrite `①②③` into the visible spec text columns

`Spec_Footnotes.csv` note:

- keep one row per reusable footnote definition
- CSV/PDF and IDML readers share the same reference-ID deduplication and numeric
  marker formatting. Put reference IDs in the desired order; repeated IDs print
  once. This shared rule does not alter target/language selection or text fallback.
- use `Footnote_id` as the stable reference key
- use `Footnote_order` to control the rendered superscript order
- keep `Type=Footnote` in the synced Feishu-backed rows so downstream renderers preserve the explicit trailer type
- keep only plain footnote body text in `Text_*`; the renderer derives the visible superscript marker automatically
- `project_code` / `项目代码` is no longer part of `Spec_Footnotes.csv`; target rows by `Region` + `Model`

`Spec_Notes.csv` note:

- use this file for bottom-of-spec notes that are not tied to a superscript reference
- use `Note_id` as the stable note key and `Note_order` as the rendered order
- keep `Type=Note` in the synced Feishu-backed rows so downstream renderers preserve the explicit trailer type
- keep only plain note text in `Text_*`
- when both note and footnote blocks appear at the bottom of one spec page, the final display order follows [`../docs/templates/spec_template.rst`](../docs/templates/spec_template.rst)

run:

```powershell
python build.py sync-review --config configs/config.ja.yaml --model JE-1000F --region JP
```

By default this updates data-driven files in the review bundle without resetting the entire review text.

That same parameter-only sync now also runs automatically before `check`, `html`, `word`, `pdf`, and `publish` when the target already builds from review.
Placeholder-backed RST pages keep manual review prose, while parameter-driven lines are refreshed from runtime.
That sync now also refreshes `generated_page` placeholder files under `page/*.rst`, so final review builds do not keep stale placeholder text after runtime/generated data changes.
If approved copy on a target-specific page must remain byte-stable, list its exact relative path under `sync_preserve_paths` in that review bundle's `manifest.json`. Protected paths are skipped even when they are data-driven or named with `--page-file`; the sync manifest records them in `last_sync_preserved_files`. The field accepts only relative `.rst` paths under `page/` or `generated/`. Remove the declaration before an intentional page refresh, or use `review --refresh-review` for a deliberate full reseed.
When a single-language build points at a merged review branch and only `docs/_review/<model>/US/` or `docs/_review/<model>/EU/` exists, that automatic sync falls back to the merged review root instead of skipping the refresh, then remaps shared-family review pages onto the requested single-language page layout.
For the single-language US English config, the canonical review root is `docs/_review/<model>/US/en/`; for `configs/config.pt-br.yaml`, it is `docs/_review/<model>/pt-BR/pt-BR/`; for the single-language EU configs, the canonical review roots remain `docs/_review/<model>/EU/<lang>/`. Do not use or recreate the old shared single-language `docs/_review/<model>/<region>/page/**` layout. For the merged `configs/config.us.yaml` / `configs/config.eu.yaml` queue/review flows, the canonical shared review roots are `docs/_review/<model>/US/` and `docs/_review/<model>/EU/`.

Useful variants:

```powershell
python build.py sync-review --config configs/config.ja.yaml --model JE-1000F --region JP --sync-scope generated
python build.py sync-review --config configs/config.ja.yaml --model JE-1000F --region JP --page-file 02_whats_in_the_box.rst
```

### 3.5 Build from Review

Once `_review` exists, these commands use review content by default because `--source auto` overlays review on top of the runtime bundle:

```powershell
python build.py check --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py html --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py word --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py pdf --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py all --config configs/config.zh.yaml --model JE-2000E --region CN
```

`check` now also catches stale foreign model names and contract-required spec keys, required page-value selectors, and assets.

PR review-preview note:

- when a PR changes `docs/_review/<model>/<region>/`, the review-preview workflow derives that exact target from the diff and uses the same target-aware language/config matching as the queue. A target-specific declaration wins before the shared regional fallback, so `JBP-2000B / US` resolves to `configs/config.bp-us.yaml` while ordinary US host targets keep the MAIN config.
- when a PR changes the zh manual family under `docs/templates/page_zh/`, `docs/templates/recipes/zh/`, or `docs/manifests/manual_zh.yaml`, the preview tool still switches the default landing target to the config-derived CN runtime target; the packaged workspace continues to include every existing review model

### 3.6 Package a Review Preview for Design

Use this when design needs the rendered review HTML plus the current family-level diff package:

```powershell
python tools/process_docs/build_review_preview.py --config configs/config.us-en.yaml --model JE-1000F --region US --source review --from-ref HEAD~1 --to-ref HEAD --all-review-models
```

Config note:

- omit `--config` to resolve the config from the explicit `--model` / `--region` target declaration; omitting `--model` and `--region` as well derives the default target from the changed review bundle, then from the existing review tree
- keep `--config configs/config.us-en.yaml` when you want the packaged workspace to open on the explicit US English single-language target by default
- the Vercel review-preview fallback scans the registered `configs/config*.yaml` files for those family defaults and uses the first registered target only when neither environment variables nor a review-tree target is available

Default packaged output:

- [`../site/review-preview/dist/`](../site/review-preview/dist)

This package contains:

- `index.html`: the workspace root for family/model/language navigation
- `manual/`: review-based HTML, grouped by family, model, and language
- `changes/`: family hubs plus model-level diff pages at `changes/<family>/<model>/`
- `downloads/`: model-scoped `review-manual.docx`, `change-report.xlsx`, and copied diff-report CSV files
- `generated/meta.json`: branch / commit metadata
- `generated/changes.json`: grouped changed files, review pages, and download metadata
- `generated/workspace.json`: the workspace data contract used by the root page
- `manual/index.html`: compatibility redirect to the default manual
- `changes/index.html`: family selector that links the packaged `US / JP` diff pages instead of dropping reviewers into one default family report

Packaging rule:

- the review preview output contract is `index.html`, `manual/`, `changes/`, `downloads/`, and `generated/`
- CI treats `index.html`, `manual/`, `changes/`, and `generated/` as the required smoke-packaging surface
- `--skip-word` is now used by the CI smoke workflow so review-preview packaging can stay stable without requiring the heavier Word path on every run
- the workspace hides families with no `_review` content, so the packaged site only shows available families
- with `--all-review-models`, the packaged site includes every existing review model and keeps the requested target as the default landing entry
- diff, workbook, and CSV outputs stay shared inside one `family + model` package, not per-language artifacts
- the default change entry in the packaged workspace now opens the selected model diff page, while `changes/index.html` and `changes/<family>/index.html` stay available as hubs

Web Publish / Read the Docs note:

- `Review Preview Package` uploads the review-preview workspace as a GitHub artifact only
- [`.github/workflows/feishu-build-queue.yml`](../.github/workflows/feishu-build-queue.yml) owns print Publish only; it no longer builds a Vercel candidate or writes `HTML_link`
- [`.github/workflows/feishu-web-publish-queue.yml`](../.github/workflows/feishu-web-publish-queue.yml) runs only on the Hello-Docs business plane, consumes `Workflow_action=Web Publish`, pushes frozen sources to the `Hello-Docs/publish:docs/publish/` candidate, rejects any PR diff outside `docs/publish/**`, opens or updates `publish -> main`, and writes the deterministic root-level RTD alias (for example `https://ht-doc.readthedocs.io/manual_je1000f_us.html`) to `HTML_link`
- Web Publish verification artifacts expire after 7 days; the generated `publish` branch is the durable candidate and `Hello-Docs/main:docs/publish/**` is the production snapshot. Print Publish artifacts retain their 14-day CI inspection window, and the nightly phase2 backup retains 90 days
- [`.readthedocs.yaml`](../.readthedocs.yaml) builds `docs/publish/web/` when the frozen Web Publish snapshot exists on `main`. Its review/fixture command is only a bootstrap fallback before the first merged snapshot
- RTD builds from a bare clone with no Feishu credentials. The project listens to `Hello-Docs/main`; it renders the PR-merged MyST source and never runs live `sync-data`
- `review/*` remains a build-input branch. Never merge it into `main`; the only Web release PR is the generated `publish -> main` PR containing only `docs/publish/**`
- full transaction, branch and rollback contracts: [`dev/web_publish_pipeline.md`](dev/web_publish_pipeline.md)
- **Plain-Markdown preview lane (not a publish path):** [`../tools/plain_markdown_site.py`](../tools/plain_markdown_site.py) renders ordinary hand-written `.md` (a single file, or a folder rendered as one site with a furo sidebar) into a self-contained static site that reuses the same presentation contract as the published web manual — furo + `myst_parser` + the concatenated `web_manual.css` from [`../tools/web_stylesheets.py`](../tools/web_stylesheets.py). Usage: `python tools/plain_markdown_site.py --source <file-or-folder> --output-dir <site-out> [--title T] [--assets DIR] [--stylesheet CSS] [--strict]`. For a legacy backlog, `--manifest inventory.csv` replaces `--source`: columns `source,title,section,order` (only `source` is required, paths resolve relative to the CSV, `#`-prefixed rows are skipped), and `section` groups the furo sidebar with captions. Non-Latin titles and sections are preserved in routes, so Chinese sections stay distinct instead of collapsing into one. Image references that do not resolve in the staged tree are repointed by basename to the staged file — a manual `.md` exported from the published catalog carries `../../../_static/manual-assets/<model>/<region>/md/assets/…` paths and needs no `sed` (210 references repointed for `JE-1000F / US`); `--keep-image-refs` disables that pass. A pipeline-generated manual `.md` fed in unchanged keeps its raw-HTML components and therefore renders with full `hb-*` styling — the tool is not limited to plain prose. Legacy Markdown is also upgraded where the markup allows it: a **headerless** pipe table (what a converter emits for a table that never had a header) is rewritten into the manual's real table markup — `<figure class="hb-spec-table-composition">` + `hb-spec-table`, a `<th scope="row">` label column, `rowspan` merging for rows whose label cell is blank, and `^(①)` as `<sup class="hb-spec-reference">` — because a pipe table cannot express any of the three things the stylesheet keys off (it forces a header row, cannot mark the label column, and has no rowspan). Tables with a genuine header are left untouched, and tables wider than two columns or whose first column is artwork become a plain `manual-table` instead of a spec composition. `--keep-tables` disables the pass. Cloud-editor exports need three more shapes, all verified against a real `HTE153 Explorer 1000 V0.5` export: a two-column table with **no body rows** whose first cell is a signal word (`WARNING`/`CAUTION`/`NOTE`/`TIP`/`DANGER`, with or without `**` or `###`) is a flattened callout box and becomes `manual-callout-table` (that export carried 16); a table whose delimiter sits after the first *data* row — the giveaway is a header cell holding an image, a circled index, or a `###` heading — is treated as headerless so the data stops rendering as column headings; and a spec table carrying in-table `### SECTION` rows is split into one composition per section, matching how the published manual groups them. Pandoc-style `^sup^` and `~sub~`, which MyST prints verbatim, are converted outside code spans. **The conversion writes an intermediate form, not HTML.** Shape detection can only infer intent, so the pass emits MyST directives — `{callout}`, `{spec-table}`, `{troubleshooting}`, `{lcd-icons}`, `{lcd-mode}`, `{symbols}`, `{comparison}`, `{manual-table}` — which [`../tools/manual_md_directives.py`](../tools/manual_md_directives.py), a Sphinx extension staged beside the generated `conf.py`, compiles into the exact component markup. Component HTML therefore has exactly one source. `--to-intermediate DIR` stops after that stage and writes the converted Markdown (assets alongside) for review or correction; rendering it is then an ordinary `--source` run, deterministic and free of heuristics. Across every multi-column component a blank cell means "merge with the cell above" — the source convention a pipe table cannot express, which is why an untouched legacy table renders an empty box where a row span belongs. `--download-images` fetches http(s) image references into the site (deduplicated per URL, failures reported and left remote) so a document whose artwork lives on a cloud editor's CDN — all 57 images of the HTE153 export — becomes self-contained. Two further staging fixes keep legacy content buildable: Markdown images whose path contains non-ASCII characters are pointed at an ASCII-named staged copy (MyST percent-encodes URIs, so Sphinx cannot resolve `图片/面板.png`), and a document with no level-1 heading gains one from its manifest title, since Sphinx refuses to link a titleless toctree entry. It refuses to write into `docs/_build`, `reports/releases` or `docs/publish`, and it cannot reach RTD: the catalog renders only the frozen `docs/publish/web` snapshot assembled by [`../tools/publish_branch_assembly.py`](../tools/publish_branch_assembly.py) from Web Publish release metadata. Plain Markdown picks up the prose layer (type ramp, paper card, H1/H2 treatments, table panels, figure sizing) but not the `hb-*` component compositions, which require pipeline-generated markup — measured on real content, plain Markdown binds 42 of 310 stylesheet selector groups against 271 for the generated manual. `tests/test_plain_markdown_site.py` pins the style-critical conf keys to the ones [`../tools/readthedocs_source.py`](../tools/readthedocs_source.py) generates so the preview cannot drift from the published contract
- Plain-Markdown directive options are typed and fail-closed: `\|` is a literal
  pipe inside a cell; `troubleshooting :headers:` must contain exactly two
  non-empty cells; `callout :variant:` is limited to `warning`, `danger`,
  `caution`, `note`, or `tip`; arbitrary `:class:` and unknown options fail a
  strict build. The eight directives, inline subset, examples, and triage are
  maintained in [`../user-guide/md_site_guide.md`](../user-guide/md_site_guide.md).
- Fixed PDF-like Web panels are selected through the versioned [`web-composite-manifest/v1`](../tests/fixtures/phase2/web_composite_manifest.json) snapshot. The live Base is only the control/intake plane: `04_资产定义.web_replace_key` identifies the governed HTML component, while one approved `04_资产导出物` row supplies exactly one `export_file`, its `web_locale`, `content_sha256`, and `source_fragment_sha256`. `sync-data` downloads approved bytes to `_attachments/web_composites/`; materialization verifies and copies target-matching bytes to `_assets/web_composites/` and includes the staged manifest in the bundle fingerprint. The Web contract contains semantic keys and locale mappings only, never live Base tokens or static artwork paths.
- Locale lookup is exact first and permits only `shared` as fallback. No approved match preserves the editable/searchable semantic HTML; multiple matches, a missing/extra attachment, an unapproved buildable row, attachment hash drift, or source-fragment drift stops the build. Section headings remain outside composite images. FCC, What's in the Box, Symbols, LCD, tables, warnings, and App add-device remain editable HTML components and do not enter this replacement manifest.
- After a reviewed live-Base change, approve the Web export rows and dispatch Web Publish with the HT-Docs bot. The worker freezes the exact manifest and attachments in Git before RTD can render them. `tests/fixtures/phase2` remains a CI/bootstrap fixture, not the production intake path
- to add a target to the catalog, prepare its review branch and presentation contract, then Web Publish it. The assembler preserves prior targets and rebuilds the aggregate catalog without another hardcoded `.readthedocs.yaml` command
- Web Publish sets `AUTO_MANUAL_PRESENTATION_PROFILE=web`; print Publish, local document exports and DOCX retain the default `document` profile
- the web profile omits `cover*`, `00_toc*`, and `99_back_cover*`, removes print page breaks, and starts the manual at `00_preface`. When the template carrier includes a merged-language inventory line, Web removes it so the first visible block is `IMPORTANT`; a legitimately de-templated/reseeded review carrier may already begin with the governed bold `IMPORTANT` marker and is accepted without deleting that live marker. Any other leading structure fails closed. Catalog links point directly to that generated manual entry instead of an intermediate target index
- For targets explicitly listed in the web figure contract (currently `JE-1000F / US`), Product Overview is first projected into one `HB-SPECIAL-OVERVIEW` ComponentSpec (two semantic views, two asset roles, 15 ordered callouts), then resolved through the versioned [`overview_component_instances.json`](../docs/renderers/contracts/overview_component_instances.json). Both views use locale-matched approved PDF artwork for English, French, and Spanish at every viewport width, including phones; the complete annotated image remains visible instead of falling back to a separately laid-out callout grid. With no approved manifest match, the same component keeps its complete searchable HTML/SVG fallback. Responsive Web coordinates and fixed-page IDML coordinates are separate fields of the target instance, not renderer-neutral semantics. The crops contain the complete annotated view but exclude the FRONT/RIGHT view headings, so the theme still owns heading text and styling. WHAT'S IN THE BOX turns the same three source cells into the PDF-derived numbered-card grid and converts the source TIP row into the full-width rounded strip; no localized copy is duplicated in CSS or web-only JSON. In App Setup, the store badges and QR are distinct shared images, centered independently in two equal columns; the adjacent localized descriptions remain live HTML below their matching artwork. Step 2.1 replaces the duplicate visible add-device button wording with the small themeable plus while retaining the localized label in `aria-label`. The App add-device panel combines one shared two-phone PDF crop that already contains the approved 2.1/2.2 positions with shared text-free device-control art and the three governed RST button labels as visible responsive HTML. The approved control art remains a full-width grey panel with complete leader geometry; CSS positions only the three localized labels over its reserved blank zones and must not recreate the lines with pseudo-elements. The five operation figures and car-charging connection panel retain locale-matched 2x PDF crops. The App connect-result panel uses one shared three-phone PDF crop with 2.3/2.4/2.5 included in the artwork; the reference note remains live HTML below the figure. Web CSS never synthesizes or independently places these five screenshot captions. Reference artwork never contains the section heading, so theme changes still control headings, typography, colors, and spacing. Ordinary standalone RST artwork ignores the source's small print-width hint in the web profile: every single image fills the same responsive content width, stays centered, and preserves its aspect ratio. Hidden semantic fallbacks remain only for components whose visible reference art still bakes localized labels. An unlisted target keeps ordinary source HTML instead of inheriting another product's presentation.
- FCC stays live/searchable HTML: the localized opening, note, body, four measures, and modification copy are arranged with the FCC mark in the PDF-derived two-column card, use one component-owned vertical rhythm instead of inherited paragraph/list margins, then reflow to one column on narrow screens. Keep its H1 in the document outline and RTD navigation, but visually hide that H1 so no black FCC title bar is rendered. The FCC card, H1 bars, generic table wrappers, and governed table compositions all use the same border-box component-band width contract, so padding and borders cannot make one component wider than another. Each localized MEANING OF SYMBOLS warning-definition table is normalized from its governed four-row source into semantic `hb-symbol-signal-*` HTML: complete dark grid, dark warning badges, and live localized label/meaning text with no inherited inline widths. Its following four-column safety-symbol source matrix is converted, by source pattern and structural contract rather than localized wording, into the PDF's two independent rounded Symbol/Meaning tables: the left six and right five body rows keep independent row tracks, while the two desktop panels stretch to one shared outer height so their top and bottom borders align; phones stack the panels. The artwork and localized text remain searchable HTML, and contract drift fails the build rather than silently applying another table's layout. The LCD icon page is also live HTML; its four-column table is protected from Pandoc so RST `line-block` status rows keep explicit line breaks. The theme supplies the rounded outer frame, full row/column grid, approximately 6%/11%/27%/56% column widths, light fill for number/icon/name, compact number badges centered in the first column, white description cells, and a horizontal-scroll fallback on phones.

LCD semantics now come from the assembly planner's `lcd_icons` CSV page identity
or an explicit `hb-lcd-icon-table` declaration, rather than a filename or US
figure grant. Renamed slots and JP targets use the same four-column projection;
ordinary undeclared tables stay ordinary. RST and standalone `{lcd-icons}` MyST
share validation: exactly four unspanned cells, one icon, and nonempty number,
name and description. Malformed rows fail instead of being padded or truncated.
Status line breaks, inline emphasis, lists, icon sources and row order remain
authored content. The scrollable table can also receive keyboard focus; artwork
approval rules remain unchanged.

- The LCD screen-mode panel remains live/searchable HTML and is normalized across EN/FR/ES into the template's rounded two-column composition: centered product illustration on the left, compact three-column operation grid on the right, and stacked art plus internally scrolling table on narrow screens. The AC/DC Auto Resume matrix also stays live HTML, using the same 50/50 template geometry, light left column, white right column, dark cell rules, and a real two-row Battery SOC span.
- Troubleshooting is normalized across EN/FR/ES as a protected searchable table with the source-verified `F0` through `FE` row order, a 14% light code column, an 86% white measures column, rounded dark outer frame, and complete internal grid. The F6/F7 RST `line-block` nodes stay intact through Pandoc so numbered actions remain separate lines; phones scroll inside the component instead of widening the page. Specifications uses the same protected-table boundary for all four localized groups, with a 31% light label column, 69% white value column, row-span semantics, and PDF-derived dark grid. Remove the authored `hb-spec-bullet` glyph during the web transform and let the shared H2 theme draw the only visible marker; otherwise Pandoc turns the source glyph into heading text and produces a duplicate dot. Convert the two governed circled references in each localized specification page into semantic `sup.hb-spec-reference` nodes so `①` is visibly raised without changing the searchable footnote text.
- Warranty is normalized across EN/FR/ES from the live RST structure rather than localized title matching. The HTML intake unwraps only the governed `warranty-lead` / `warranty-section` semantic containers used by the shared templates, so a newly seeded review bundle and the older flat review form produce the same six-section outline without discarding nested headings. Its two opening paragraphs become the rounded purchase notice and local-law note; the only section containing a table becomes the PDF-derived 3-year/2-year card; the other five sections become rounded copy cards. Keep all six H2 nodes so the theme and page outline still own the localized headings, but style them as floating dark card labels. The desktop period grid is approximately 61%/39%, uses localized year units and warranty labels from the source, and stacks to one column below 760 px. The transform removes the source 50/50 table and inline widths from final HTML while retaining email links, lists, and searchable copy.
- [`../docs/renderers/contracts/web_manual.css`](../docs/renderers/contracts/web_manual.css) is the responsive base visual contract for the catalog. FCC rules are isolated in [`../docs/renderers/contracts/web_fcc_components.css`](../docs/renderers/contracts/web_fcc_components.css); What's in the Box rules are isolated in [`../docs/renderers/contracts/web_inbox_components.css`](../docs/renderers/contracts/web_inbox_components.css); Symbols rules stay in [`../docs/renderers/contracts/web_symbols_fcc_components.css`](../docs/renderers/contracts/web_symbols_fcc_components.css); shared App artwork plus live-label rules stay in [`../docs/renderers/contracts/web_app_components.css`](../docs/renderers/contracts/web_app_components.css). The build concatenates the ordered modules into one public `web_manual.css`. Together they mirror the IDML hierarchy with the `#343031` H1 bar, compact level-two/three markers, rounded table and notice groups, shared spacing, and proportional figures. The FCC exception keeps its H1 semantic in navigation but visually renders only the approved editable FCC frame through `HB-SPECIAL-FCC` ComponentSpec. `HB-SPECIAL-INBOX` carries the three ordered card numbers, asset roles, accessible alt/localized labels, and adjacent tip copy; `HB-SPECIAL-OVERVIEW` carries the two views and 15 live callouts while its target instance owns renderer geometry. Web, LaTeX, IDML, and Word retain independent adapters. The font stack requests locally installed Gilroy first but does not redistribute the commercial font; public clients fall back to Avenir/Segoe UI/Helvetica/Arial. Keep this as visual-language parity, not fixed-page parity: mobile remains reflowable and IDML remains the formal pagination authority.
- Before the web-profile HTML-to-Markdown Pandoc pass, every `manual-callout-table` is replaced with a checked placeholder and restored byte-for-byte afterward. This keeps WARNING, DANGER, CAUTION, and NOTE on the same `manual-callout-table` / `manual-callout-label` / `manual-callout-body` contract and one shared light rounded treatment regardless of body markup, avoids Pandoc's empty table header and 50/50 `colgroup`, and leaves the responsive theme to render the intended approximately 16%/84% desktop split. The callout table uses fixed layout so localized label length cannot give adjacent boxes different first-column boundaries. Do not reintroduce selectors based on a callout being immediately adjacent to an H1.
- Semantic `<sub>` and `<sup>` elements are protected and restored through the same checked Pandoc boundary. Scientific notation such as `V<sub>oc</sub>` and specification references such as `<sup>①</sup>` therefore remain real, themeable HTML in EN/FR/ES instead of surfacing Pandoc's inline Markdown notation as literal text.
- Web Publish runs [`../tools/readthedocs_source.py`](../tools/readthedocs_source.py) indirectly through the publish-branch assembler, producing one link-only root index, collision-checked root alias pages named from each manual stem, and mirrored image assets under `docs/publish/web/_static/manual-assets/`. Each alias forwards relatively to the nested canonical page so the same frozen source works with or without RTD's `/en/latest` prefix.
- do not point RTD at the repo-root [`../docs/`](../docs) tree; `docs/publish/web/` is the frozen Sphinx source, while `docs/publish/sources/web/` retains each target's original MyST bundle
- RTD is the Web Publish presentation surface; it is not the release authority for formal IDML, LaTeX, PDF, DOCX or print Markdown outputs

### 3.7 Publish a Final Word Release

```powershell
python build.py publish --config configs/config.ja.yaml --model JE-1000F --region JP
```

This is the formal release command.
It requires an explicit `--model` and `--region`.

Outputs:

- direct `build.py publish`: review diff report plus final build outputs under [`../docs/_build/`](../docs/_build) by default, or under `<staging-root>/docs/_build/` when staging is enabled
- queue-driven print Publish: staged DOCX/PDF/Markdown under [`../reports/releases/<model>/<region>/<lang>/versions/<version>/`](../reports/releases), with Markdown sidecars such as `assets/`, `conf.py`, and `index.md` preserved when present
- queue-driven Web Publish: staged MyST plus verification HTML under `reports/releases/<model>/<region>/<lang>/versions/<version>/web/`, then frozen Sphinx candidate under `Hello-Docs/publish:docs/publish/` and a scope-guarded PR into `Hello-Docs/main`
- release manifest: [`reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv`](../reports/releases) by default, or `<staging-root>/reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv` when staging is enabled

## 4. Output Layout

Runtime outputs:

- default: [`docs/_build/<model>/<region>/rst/`](../docs/_build), [`docs/_build/<model>/<region>/preview/<page>/rst/`](../docs/_build), [`docs/_build/<model>/<region>/html/`](../docs/_build), [`docs/_build/<model>/<region>/word/`](../docs/_build), [`docs/_build/<model>/<region>/pdf/`](../docs/_build)
- staged verification/local queue runs: `<staging-root>/docs/_build/<model>/<region>/...`
- each prepared `rst/` bundle root contains `asset_usage_manifest.json`, `asset_registry_snapshot.csv`, and finalized `bundle_manifest.json`; `bundle_manifest.json.bundle_sha256` fingerprints the final RST include closure, configuration, support trees, and the two asset sidecars

HTML output starts at the first manual content section. Generated cover pages are preserved for PDF/LaTeX output, not rendered as a standalone HTML home screen.
In manual preview mode, the HTML view also suppresses most Furo navigation chrome, stays in a continuous reading flow instead of browser-side fake pagination, regenerates a lightweight left outline from manual headings, and applies a restrained neutral manual-reader treatment to generic headings, copy width, figures, ordinary docutils tables, and the multilingual preface notice while preserving dedicated component layouts such as `SPECIFICATIONS`.
For review-preview workspace packaging, the manual pages now reuse the same manual HTML/CSS/JS treatment as the local build, including the generated heading sidebar and the same no-top-switcher layout.

Review working bundle:

- [`docs/_review/<model>/<region>/`](../docs/_review)

Review handoff workspace:

- [`../site/review-preview/dist/`](../site/review-preview/dist)

Latest publish HTML site:

- [`../site/publish-latest/dist/`](../site/publish-latest/dist)

Read the Docs bundle source for the generated public catalog:

- [`../docs/_build/rtd/`](../docs/_build)
- per-manual entries under `../docs/_build/rtd/<model>/<region>/md/`

Revision reports:

- default: [`reports/version_tracking/<model>/<region>/`](../reports/version_tracking)
- staged verification/local queue runs: `<staging-root>/reports/version_tracking/<model>/<region>/`

Release manifests:

- default: [`reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv`](../reports/releases)
- staged verification/local queue runs: `<staging-root>/reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv`

## 5. Typical Commands

Build all targets defined in one config:

```powershell
python build.py rst --config configs/config.us.yaml
python build.py word --config configs/config.us.yaml
python build.py all --config configs/config.ja.yaml
```

Build one explicit target:

```powershell
python build.py word --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py word --config configs/config.eu-en.yaml --model JE-1000F --region EU
python build.py pdf --config configs/config.ja.yaml --model JE-1000F --region JP
```

### Approved-PDF native InDesign replica (option 2)

The production IDML path projects the prepared bundle through `manual.ir.json`
and shared layout tokens; `latex_page_plan.json` remains a same-source trace.
For ordinary targets without an approved reference-layout contract, the
measured LaTeX plan remains the fallback behavior. For the approved
`JE-1000F / US / en+fr+es` replica, the LaTeX PDF and its page plan are not the
visual approval master. The build must resolve the target through the
[`reference layout registry`](../docs/renderers/contracts/reference_layout_registry.json)
to the reviewed, hash-bound
[`JE-1000F US V2.0 contract`](../docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json).
The design and implementation rationale is recorded in
[`dev/idml_reference_replica_plan.md`](dev/idml_reference_replica_plan.md), and
the module boundary remains documented in
[`dev/idml_module_map.md`](dev/idml_module_map.md). When a new model, language,
page, or density should reuse an existing visual component, follow
[`dev/style_component_usage_guide.md`](dev/style_component_usage_guide.md) before
adding page-level geometry or finalizer behavior.

`JBP-2000B / EU / en+fr+es+de+it+uk` is the second target resolved from the
same `BP@INTL` skeleton. Build it with `configs/config.bp-eu.yaml`; `uk` is
Ukrainian and this target makes no UK-market claim. Its paired host is named
`Jackery Explorer 2000 Plus` in EU target data (the US target uses
`Jackery HomePower 2000 Plus`). The committed physical plan remains a
candidate, so a successful 54-page native PDF/X-4 pass proves candidate
assembly health but does not register an approved reference layout. Current
native evidence is recorded in
[`reviews/jbp2000b_eu_r2_native_validation_2026-08.md`](reviews/jbp2000b_eu_r2_native_validation_2026-08.md).

`JBP-2000B / JP / ja` is the first target resolved from the separate `BP@JP`
skeleton. Build it with `configs/config.bp-jp.yaml`; this config is exact-target
only and declares `family_default: false`, so ordinary MAIN JP continues to
resolve through `configs/config.ja.yaml`. Its paired host display name is
`Jackery ポータブル電源 2000 Plus`. The 12-page target plan adds only assembly
data: split signal/icon compositions, Inbox+Overview, LCD+Operation, a two-page
Connections stacking guide, Troubleshooting+Specifications, and the shared
warranty composition. New target behavior must stay in the manifest, Product
Manual Plan, target assembly JSON, region profile, localized carrier data, and
assets; do not add `JBP-2000B` or `JP` branches to page renderers. The plan
remains `candidate` until native InDesign/PDF/X and 12-page visual acceptance
are recorded and it is promoted separately.

IDML-localized symbol copy and table-of-contents language headers are language
packs derived from [`tools/lang_registry.py`](../tools/lang_registry.py),
not tables maintained by the individual IDML modules. For reference-bound
spacing and placement overrides the registry separates three sets:
`governed_languages()` gates approved-reference flow behavior (fixed approved
heights, reference offsets, planned composition — en/fr/es);
`layout_override_languages()` is the set whose `lang_<code>_` override rows the
shared token cascade reads (the governed languages plus lines in active layout
tuning, currently adding ko), with tuning languages keeping measured/fallback
flow behavior until their reference layout is approved; and each component's
`contract_languages` declares which override rows are contract-required under
approved-reference builds. Adding a language pack alone does not claim that
language has an approved physical layout.
The fixed-layout LaTeX `HBApplyLang` dispatcher also covers the warning label
for every registered language; its label values are parity-checked against the
registry's symbol language pack.

Contract selection is fail-closed before identity validation: if an approved
contract on disk exactly matches the Manual IR target but its registry row is
absent, production IDML stops and names the orphaned contract. Removing a row
must never turn an approved target into an ordinary measured-LaTeX target.
Fallback is valid only when neither the registry nor the contract directory
contains an approved contract for the exact model, region, and language list.

For a single-language config, `build.py idml` derives the exporter `--lang`
from `build.languages` when the CLI flag is omitted. This is required for
families such as JP and KR: passing only model/region must not let the low-level
exporter's historical English default select localized data. Multilingual
configs keep that historical default unless `--lang` is supplied explicitly.

The approved v2 contract separates enforced identity from provenance:

The committed engineering-plane review copy is synchronized to
`Bingboom/Hello-Docs:review/JE-1000F-US@e06def5e49e107e1a9595c1f38bb11b1d5496f94`.
The 2026-08-29 content reapproval covers the current editable IDML semantic
projection; its rebind changed zero page bindings and left the 58-page
composition map unchanged.

| Contract item | Approved value |
| --- | --- |
| Target | `JE-1000F / US / en+fr+es` |
| Reference PDF | `Jackery Explorer 1000 User Manual V2.0-2026-06-05.pdf` |
| Reference SHA-256 | `e72b1ba01882062e261b17d5ba54a2f7c3099e5ba531a6428be13888641083f2` |
| Page contract | 58 pages, `368.787 × 524.692 pt`, tolerance `0.02 pt` |
| Print contract | PDF/X-4, Output Intent `Japan Color 2001 Coated`, Output Condition `JC200103` |
| Content identity (enforced) | `b46905f6953e4c4684623f204890a55ad5826e0fbbc610119738a4c53929590a` |
| Assembly identity (enforced) | `c5d6d94c5bc6eaf18e767af3113aa9c766fb01c519062751003d310e9684eb57` |
| Style-contract identity (enforced) | `6db62e7780288ac073bc7502379112ddf10aae8d6c00de29875e9ea1a80d0003` |
| Layout-params identity (enforced) | `2a7e0ea1b75180acc52ff0f169f42322416bc881de860255f1ca778ce2858d82` |
| Snapshot provenance (not an activation gate) | `aa4bfb324cd12ff07be2507a51a634e61e2d6043e2dd4fb199bb873afd43f821` |

The 52 plan rows bind every IR source reference, by composition, to this
physical structure:

| Section | Physical pages | Count |
| --- | ---: | ---: |
| Front matter | 1–3 | 3 |
| English | 4–21 | 18 |
| French | 22–39 | 18 |
| Spanish | 40–57 | 18 |
| Back cover | 58 | 1 |

The build is fail-closed for this approval path. Target/language mismatch,
missing plan, enforced content/assembly/style drift, per-page source drift,
incomplete 52-source coverage, unclassified prose without an exact approved
exception, non-monotonic/out-of-bounds composition pages, or a final
page-count/geometry mismatch stops the build. Snapshot provenance drift alone
does not. The build must never partially use this plan and then silently fall
back to the fuzzy PDF mapper.

If source identity changes but the reviewed 58-page composition remains valid,
refresh it with the dedicated all-or-nothing rebind command. Run the dry-run
first:

```bash
python3 tools/reference_layout_rebind.py \
  --plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --manual-ir <manual.ir.json>
```

The dry-run builds a complete candidate from the validated Manual IR. For a v2
input, the ordinary route requires the semantic content hash, assembly hash,
`source_ref` order, page languages, and physical composition map to remain
unchanged; it refreshes style/provenance identities plus every page's
`source_sha256`, and writes nothing. A v1 input has no assembly pin, so it is
never treated as an ordinary unchanged rebind: migration requires the explicit
approval route below. After reviewing an ordinary v2 summary, apply the same
validated candidate and inspect the Git diff:

```bash
python3 tools/reference_layout_rebind.py \
  --plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --manual-ir <manual.ir.json> \
  --write
```

If semantic content or assembly identity changed—or the input is v1—the
ordinary route remains fail-closed. First prove against the final Manual IR that
`source_ref` order, page-language mapping, `skipped_raw` allowance, physical
page count, semantic page roles, and composition map are the reviewed assembly.
Record the operator's decision and evidence, then run the explicit identity
approval route without `--write`. The existing flag name remains for CLI
compatibility:

```bash
python3 tools/reference_layout_rebind.py \
  --plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --manual-ir <manual.ir.json> \
  --approve-content-change \
  --approved-by "<operator>" \
  --approved-at "<RFC3339>" \
  --approval-method "<recorded review evidence>"
```

Only after reviewing that candidate should the operator repeat the same command
with `--write`. All three approval values are mandatory and are persisted as
contract metadata. This route can update `manual_content_sha256` and the
assembly identity; it cannot change source order, page languages, or the
physical composition map. v1 migration defaults
`allowed_unclassified_source_refs` to an empty list and never manufactures
exceptions: if validation reports unclassified prose, stop and perform a new
reviewed layout approval.

To inspect every registered plan in one dry-run summary, use
`python3 tools/reference_layout_rebind.py --all-registered --manual-ir
<manual.ir.json>`. Batch mode is intentionally read-only and cannot approve a
content change; `--write` and content-approval metadata must be paired with one
explicit `--plan`.

When a refreshed Manual IR needs a new layout review, create a review-only
draft from the existing composition seed instead of hand-editing the 52 page
hashes:

```bash
python3 tools/reference_layout_scaffold.py \
  --seed-plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --manual-ir <manual.ir.json> \
  --output <review/reference-layout-draft.json>
```

The scaffold refreshes source identities, page digests, and the observed
`idml_contract.max_skipped_raw` baseline while preserving the seed's physical
composition map. The output is explicitly `approval.status=draft` and
`production_eligible=false`; it is not added to the registry and cannot
activate production IDML. Composition review, including that skipped-raw
baseline, and explicit approval must happen before a maintainer promotes a
contract and registers it.

The tool preserves file mode and uses an atomic replace only after full plan
validation. It is not a composition editor: a source-order or page-map change
requires a new layout review and approval. Never hand-edit a subset of hashes
or remove the registry entry to unblock a build.

`layout_params_sha256` is derived from the ordered parsed `key`, `value`, and
`unit` rows, not the raw CSV bytes. LF/CRLF changes, blank rows, and changes to
the comment column therefore do not invalidate an approved plan; changing a
token value/unit or reordering semantic rows does. This keeps the hash strict
about renderer behavior without treating formatting-only CSV edits as layout
drift.

Build from the frozen review and phase2 snapshot. For this registered target,
omitting `--source review-asis` is equivalent because `auto` selects the
approved review assembly:

```bash
python3 build.py idml \
  --config configs/config.us.yaml \
  --model JE-1000F \
  --region US \
  --source review-asis \
  --idml-mode production \
  --data-root <phase2-snapshot>
```

The editable-object boundary is part of acceptance, not a designer
preference:

- body text, headings, tables, callouts, Product Overview, and the back cover
  are native InDesign objects/stories;
- illustrations are governed linked assets; RST should identify them as, for
  example, `asset:operation/ac_output`;
- only approved PNG/JPG/JPEG/SVG/PDF exports that match model, region, and
  language may resolve; `.ai` is an immutable archive/source master and is
  never a renderer fallback;
- when live-text redaction cannot separate an illustration from outlined
  labels, a committed asset recipe may use `retain_vector_drawings` to replay
  only explicitly indexed source groups into a new crop-sized vector PDF.
  The retained indices must be ascending, the operator must be the sole
  transform after `crop`, zero-area line groups are overlap-checked safely,
  and unsupported path items or crop/index drift fail closed. Promote only
  after a 12x quarantine comparison and pin the resulting output SHA-256;
- missing, ambiguous, quarantined, stale, or hash-mismatched used assets stop
  assembly;
- `asset_usage_manifest.json`, `asset_registry_snapshot.csv`, and
  `bundle_manifest.json` are the bundle trace. A `legacy-path` entry is only
  accounted for and does not prove registry governance;
- the approved reference PDF may appear only on a non-printing comparison
  layer. It and visible whole-page body/back-cover files such as
  `product_overview-*.pdf` or `back_cover-en.pdf` must not be used as final
  printed content. A contract-approved finished-art front cover may remain.

`controls/je1000f_us/network_pairing_panel` is an ordinary approved recipe
export, not a reviewed App-promotion output. It shares the official source
recipe with `je1000f-us-app-ui-v1`; adding or changing that recipe therefore
changes the recipe SHA bound by the promotion contract. The promoted App
outputs remain eligible only after a fresh reviewer decision updates that
binding and `python build.py asset-check --json` passes. Never refresh the hash
without the matching review decision.

The extended US front-panel crop is registered as
`overview/je1000f_us/front_controls`, an override of the shared
`overview/front_controls` semantic key. Its PDF/PNG stay under
`docs/renderers/latex/assets` and resolve only for JE-1000F/US. Do not replace
the common Word-template PNG with this US outlet drawing; non-US and future
model targets must continue to receive the shared base asset unless they own a
separate scoped override.

For approved-reference pages, Product Overview composes two governed linked
art frames with native knockout-backed leader paths; the source-authored part
labels are emitted last as unlocked top-layer text frames, so an InDesign
operator can move or edit every label without altering the linked artwork.

The production gate also rejects skipped raw content. Cover/front matter,
Safety + Symbols, FCC + What's in the Box, LCD DISPLAY, specifications,
warranty, and the back cover are the explicit new-page anchors: each starts
its own page as a fixed composite built from explicit component frames,
while ordinary operation, UPS/charging, storage, and troubleshooting
content flows through linked story chains. The
assembler classifies source pages once through
[`tools/idml/page_roles.py`](../tools/idml/page_roles.py). Every current
template page has an explicit semantic role. If export prints
`[export-idml] WARNING: assembly coverage ...`, the named source page still
uses the historical ordinary-prose fallback and the build remains usable, but
its assembly intent has not been reviewed. Add a target-neutral semantic rule
and regression test before treating that page as governed; do not suppress the
warning with a model, region, language, or physical-page predicate.

The operation-panel renderer keeps the illustration at the bottom of its group,
then emits editable shape underlays, followed by separate unlocked text frames
for Prerequisite, standby, On, and Off. The text frames are therefore topmost
and may be moved or edited independently during final-mile InDesign alignment;
the Energy Saving paragraph after POWER remains full-width prose outside the
panel. Energy Saving then groups its two source guidance paragraphs into the
panel's grey header and exposes On/Off, 3s, and the localized action as separate
top-layer frames. LED groups its source lead into the grey header and exposes
1/2/3, SOS, and each of the three localized instructions separately. These
special layouts are detected from governed image identity plus neighbouring IR
structure, not localized English headings; the original Energy Saving PNG with
baked copy is not eligible for this overlay path. LCD SCREEN composes the
governed LCD illustration and a six-row native grid inside one rounded frame;
its two state, six action, and six description frames are emitted last and stay
independently movable. KEY COMBINATION is detected from its language-neutral
three-column, four-combination source shape. `KeyCombinationStyle.from_context()`
resolves a single base geometry/type token family from `data/layout_params.csv`;
the governed French and Spanish height/indent/gap differences are locale
overrides, not renderer forks or per-page literals. Button and clock assets
plus grid underlays are linked/drawn first; localized headers, button captions,
plus signs, durations, operations, and functions are separate top-layer frames
emitted last, so each remains independently editable and movable.
Approved-reference operation pages additionally apply locale-measured Auto
Resume, LCD SCREEN, and KEY COMBINATION geometry, localized flow gaps, and a
per-language translation of the final story frame. Components compensate that
host-frame translation with a non-negative first-line indent; keep the two
responsibilities separate because InDesign clamps or ignores equivalent
negative offsets on nested inline groups. Non-approved targets retain the
generic component fallbacks.

Approved-reference `referencefigure` promotion routes only by approved-plan
role, canonical source stem, asset basename, and adjacent IR shape; localized
headings are never routing keys. Charging-method compositions promote the AC
caption and the car `Vehicle`/cable note into independent top-layer stories.
The exact App composition applies to the approved English, French, and Spanish
`12_app_setup_placeholder` pages (including their physical-page-prefixed
stems): Download splits Store and QR into linked build-only crops with two copy
frames; Add Device places the approved pairing-panel export below independent
2.1/2.2 and POWER/AC/DC/USB frames; Connect Result crops the three screens and
emits 2.3/2.4/2.5 plus the reference note separately.
The source-page opt-in lives only in the approved contract at
`idml_contract.editable_components.app_add_device.page_owners`. Bundle asset
freezing and production composition consume that same list, including the
contracted page language. Do not add a model/region-named `is_*_page` helper
when onboarding another approved target; add its exact source refs to its own
approved contract.
The three Product Overview tables are the semantic source for Add Device
labels. Stable row/column slots resolve `main_power`, `dc_usb`, and `ac` by
language; the approved plan stores both that exact base snapshot and the
reviewed App display variant. The promotion step removes an adjacent label
block only when its three lines exactly match the base set, so unrelated copy
and Spanish step 2.3 cannot be consumed as overlay labels. Display variants do
not change the frozen source/IR content hash and are not a general content-edit
escape hatch. `AppFigureStyle` owns all nine shared overlay/fit tokens, and an
approved build fails when a required source role, variant, asset, or token is
missing or invalid. Every graphic, shape, and leader extension is emitted
before the unlocked text frames.

Source-authored TOC folios and back-cover copy come from the IR; InDesign must
not recompute or hardcode them. Content, translation, specification, legal,
table-structure, or asset-identity defects are corrected in the
Feishu/source-table/template/review/TM or asset-governance layer and then
rebuilt. The narrow approved App display-variant binding above changes
presentation only and does not authorize other renderer-side copy edits. INDD
is never a second content source.

Review bundles may retain an older opaque attachment hash after a live snapshot
refresh. The build resolves a unique current file by stable semantic identity,
stages it under the frozen basename, and rejects missing or ambiguous matches;
it does not silently emit a broken InDesign link. Rounded native tables remain
editable: a rounded background and a square table frame are grouped, and only
cell text receives the shared one-character inset. Formal body tables use the
full text measure; the one-character inset belongs to cell text, not to the
heading/table group. The finalizer fits LCD and
Meaning of Symbols shells to their composed row heights. The 26-row LCD table
normally stays at 7 rows plus 19 rows per language with a 5.6 mm maximum icon
box; its segment-specific vertical padding follows the approved
`Jackery Explorer 1000 User Manual V2.0` layout.
For governed LCD rows, the renderer first compacts short rows to a
deterministic content minimum and gives the recovered height to rows that need
more wrapped lines; each row is still emitted as an editable auto-growing row
so InDesign can honor the actual installed font metrics. If the complete
minimums still exceed the page budget, whole rows are moved to the next LCD
segment rather than allowing an overset row to remain on the current page. A
single indivisible row may grow beyond one segment's nominal budget. An
approved LCD presentation profile may select positive starting heights by
language and stable source number; the renderer rejects a partially governed
segment instead of mixing those values with InDesign-native growth. Targets
without that optional geometry retain native editable auto-growing rows.
On the combined maintenance/symbols page, the safety-tail panels use the
approved dark warning asset, and the symbol/meaning tables use a light-grey
first column. Signal badges are one-cell native tables with a
linked white warning symbol and editable localized text; French and Spanish
signal labels use the compact reference density, then fit horizontally to the
available badge width so long labels remain on one line. Symbol icon size,
icon-column width, and the gap between the two native tables resolve from the
IDML symbol tokens in `data/layout_params.csv`.
WARNING, CAUTION, NOTE, and TIP labels remain source-owned and are emitted
verbatim; a missing label stops export.

`idml` defaults to the production exporter. The separate design-template flow
mode writes semantic Markdown, a continuous-story editable IDML, a style map,
and trace files under `docs/_build/<model>/<region>/<lang>/idml/flow/`:

```bash
python3 build.py idml --model JE-1000F --region US --idml-mode flow
python3 build.py idml --model JE-1000F --region US --idml-mode both
```

When `--source auto` is used, a target with an approved reference-layout plan
is assembled from its committed review bundle exactly as `review-asis`; this
keeps the approved source order, including review-owned TOC/back-cover pages.
An explicit source selection is never rewritten. Targets without an approved
plan retain the runtime default and historical fallback pagination.

The flow artifacts remain generated handoff files, not a new content source.
Registered components become editable objects, images become linked frames,
and Markdown tables become native tables; raw serialized JSON must not become
visible document content.

On a provisioned macOS design host, close any older copy of the target INDD,
then create the native INDD, export with the frozen print contract, and write
the runtime preflight:

```bash
python3 tools/indesign_finalize.py \
  --idml docs/_build/JE-1000F/US/idml/manual_je1000f_us.idml \
  --indd output/indesign/JE-1000F_US_same_source.indd \
  --pdf output/pdf/JE-1000F_US_indesign.pdf \
  --report output/indesign/JE-1000F_US_preflight.json \
  --pdf-preset '[PDF/X-4:2008 (Japan)]' \
  --output-intent 'Japan Color 2001 Coated' \
  --output-condition JC200103 \
  --pdfx PDF/X-4
```

Keep the generated `Document fonts/` directory beside the output INDD.  The
finalizer now saves the INDD, closes it, reopens that saved file, recomposes it,
and repeats the overset/font/link preflight before exporting the PDF.  Reports
use `indesign-preflight/v2` and record this second pass under `post_reopen`.
The job fails when the saved document changes page/story count, reopens with a
`NOT_AVAILABLE`/substituted font, or gains an overset/bad link.  This catches
document-font failures that are invisible during the first IDML import.

For a design host processing more than one target, use an explicit
`indesign-finalize-jobs/v1` manifest. Every job must declare its PDF preset,
output intent, output condition, and PDF/X level; batch mode deliberately has
no print-contract defaults, so a missing ICC or preset cannot silently inherit
the wrong host setting:

```json
{
  "schema_version": "indesign-finalize-jobs/v1",
  "aggregate_report": "finalize.aggregate.json",
  "jobs": [
    {
      "id": "je1000f-us-en",
      "idml": "je1000f-us-en/manual_je1000f_us_en.idml",
      "indd": "je1000f-us-en/manual_je1000f_us_en.indd",
      "pdf": "je1000f-us-en/manual_je1000f_us_en_indesign.pdf",
      "report": "je1000f-us-en/finalize_report.json",
      "pdf_preset": "[PDF/X-4:2008 (Japan)]",
      "output_intent": "Japan Color 2001 Coated",
      "output_condition": "JC200103",
      "pdfx": "PDF/X-4",
      "application": "Adobe InDesign 2026"
    }
  ]
}
```

Run it with:

```bash
python3 tools/indesign_finalize.py --jobs /path/to/finalize.jobs.json
```

The batch validates the full manifest before opening InDesign, checks the
version pin once, isolates each job's failure, and writes one aggregate JSON
with per-job preflight summaries. It also scans each job's IDML directory
before and after the run and groups `indesign_package.complete=FALSE` results
for handoff follow-up. Jobs are grouped by their explicit `application` value.
Each group is dispatched to InDesign once, then an ExtendScript outer loop
finalizes the documents sequentially with a per-document try/catch and report.
One document can therefore fail without preventing the remaining documents in
that application group from running. Different InDesign application names use
separate dispatches, and single-job mode remains unchanged.

After PDF export, the Python wrapper also scans every retained text trace in
the final PDF. A visible replacement character (`U+FFFD`) or `.notdef` glyph
(`glyph_id=0`) fails the job even when InDesign reports every font as
installed. Because the scan runs on the assembled PDF, it covers native
InDesign stories and text retained inside placed PDF graphics. Findings are
recorded in `missing_glyphs` and `pdf_glyph_validation`; rasterized or outlined
art still requires visual review because it no longer contains inspectable PDF
glyphs.

Compare that InDesign export to the supplied approved PDF, not to the newly
built LaTeX PDF. `--latex-pdf` is retained as a legacy CLI flag name; its value
for this workflow is the approved reference PDF:

```bash
python3 tools/idml_pdf_parity.py \
  --latex-pdf <approved-reference.pdf> \
  --indesign-pdf output/pdf/JE-1000F_US_indesign.pdf \
  --preflight output/indesign/JE-1000F_US_preflight.json \
  --manual-ir docs/_build/JE-1000F/US/idml/manual.ir.json \
  --reference-layout-plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --idml docs/_build/JE-1000F/US/idml/manual_je1000f_us.idml \
  --indd output/indesign/JE-1000F_US_same_source.indd \
  --pages all \
  --out output/comparison/JE-1000F_US_same_source_parity.json
```

The approved contract supplies a visual hard gate; CLI overrides may not
loosen it:

| Render/check setting | Required value |
| --- | ---: |
| Rasterization | 300 dpi, RGB |
| Raster size | `1537 × 2187 px` on every page |
| Display ICC SHA-256 | `2b3aa1645779a9e634744faf9b01e9102b0c9b88fd6deced7934df86b949af7e` |
| Gaussian blur | 1 px |
| Per-page RGB MAD | `≤ 0.008` |
| Per-page changed-pixel ratio | `≤ 0.040` |
| Changed-channel threshold | `16` |

All 58 pages must be compared. A failure on any page fails the complete run;
mean RGB MAD or mean changed-pixel ratio cannot hide an out-of-tolerance page.
The blank-page/content-occupancy check is additional, not a replacement for
the visual hard gate.

The latest deliverable is acceptable only when all of these are true:

- exactly 58 pages, with every page inside the approved geometry tolerance;
- zero overset stories/table cells, zero missing fonts, zero missing glyphs,
  and zero bad links;
- PDF/X-4 and the required Output Intent/Condition are present in the exported
  PDF;
- all 52/52 source identities and the reference PDF match the approved plan;
- every one of the 58 page-level visual comparisons passes both thresholds;
- no visible body/back-cover whole-page PDF shortcut is present;
- every actually used asset is approved, scope-matched, current, and
  hash-correct, with the three bundle trace files retained;
- the parity JSON reports `accepted=true`.

Writing this workflow or generating an IDML/INDD/PDF does not prove parity.
Only reports from the latest actual InDesign export can satisfy the gate; do
not deliver an artifact while any item above is unknown or failing.

`--idml-mode both` also writes a compact design handoff package beside the
legacy production IDML:

```text
docs/_build/<model>/<region>/<lang>/idml/
  manual.ir.json
  latex_page_plan.json
  production/manual.production.idml
  production/source_trace.json
  production/asset_manifest.csv
  flow/manual.flow.md
  flow/manual.flow.idml
  missing_assets_report.md
  designer_checklist.md
  layout_feedback.md
```

The production `source_trace.json` records `skipped_raw_blocks` from the
production `manual.ir.json` sidecar. Ordinary targets without an approved
reference plan keep this as an observation field. An approved-reference plan
must freeze `idml_contract.max_skipped_raw`; production export fails closed
when the current total exceeds that baseline. `manual_ir_cli.py --strict`
remains the explicit zero-tolerance diagnostic independent of plan activation.
The same strict command also rejects unregistered Manual IR languages at the
top-level target, frozen manifest declaration, or page level. Approved-reference
production applies that language gate automatically before composition;
ordinary/fallback exports preserve their compatibility behavior. Language
aliases are resolved only through `tools/lang_registry.py`, while non-content
page roles `cover` and `toc` are exempt.

Japanese, Korean, and Chinese characters in editable IDML are serialized as
explicit script-aware character runs. Korean Hangul uses the committed
SIL-OFL `NanumGothic` face. Japanese uses the committed static TrueType
`HBManualSansJP-Regular.ttf` (`HB Manual Sans JP (OTF)` in InDesign,
OpenTypeTT) in both IDML and LaTeX. It is the Noto Sans JP Regular outline under
a project-unique family and PostScript identity, so a host-installed
`Noto Sans JP (OTF)` cannot shadow the document font after close/reopen. The
IDML token uses InDesign's normalized `(OTF)` family spelling while the TTF
name table and PostScript identity stay project-unique. The file is
hash-verified and packaged with the document. Chinese
continues through `CJK_FONT_FAMILY_TOKEN` (the renderer token
`idml_font_family_cjk`). Font-family routing intentionally stays outside
`data/layout_params.csv`: changing font delivery is not page geometry and does
not by itself require a reference-layout rebind.
Latin-market editable symbols are governed separately: the U+203B reference
mark is an inline native IDML vector with deterministic story-local object IDs,
so it has no font dependency after an INDD save/reopen cycle. Warranty-year
badges likewise use a native black circle plus an editable white ASCII digit;
do not replace the approved badge with either `❷` / `❸` or bare `2` / `3`.
The native badge renderer positions the localized year unit with a fixed tab
stop and reuses that exact x anchor for the warranty subtitle below it;
font-space advance must not separate `YEARS` from `Standard Warranty` or
`Extended Warranty` horizontally.
`Noto Sans` owns
ordinals and subscript digits; `Noto Sans Symbols` owns the
DC glyph and circled labels 1-20; `Noto Sans Symbols2` owns the filled-circle
fallback. LCD labels 21-27 are normalized to `(21)`-`(27)`, and both final
assembly modes enable native vector structure markers. Every declared
redistributable face is hash-verified from
`docs/templates/word_template/common_assets/fonts/idml_portable/` and copied
beside the IDML under `Document fonts/`; generated packages therefore do not
depend on `Segoe UI Symbol`, `Yu Gothic`, or `Noto Sans KR` on the host.
Line and coarse text-width budgeting is governed by
`tools/idml/line_metrics.py`: the existing per-component narrow-glyph ratios
remain stable, East Asian Width `W`/`F` characters consume one em, combining
marks consume no width, and ambiguous-width characters remain narrow for
cross-host determinism. The estimator does not load local font files and does
not replace native InDesign finalize/parity checks. Heading/suffix-pill sizing
also reserves a full em for wide/fullwidth glyphs while preserving the approved
Latin advances. Single-column contents use native tab leaders; multicolumn
contents retain the reference line geometry. An explicitly empty specification
group omits its heading and marker. Warranty lists retain their source numbering
or nested dash once, using the existing hanging-tab layout.

Japanese native finalization preserves each character's face when rebinding the
portable font, and fails if that requested face is unavailable. The report's
`portable_font_rebinds[].style_counts` exposes the result. Archive frozen inputs
and native reports outside the target build directory before another `idml` or
`check` run: preparation cleans that target. See the
[JP native acceptance ledger](reviews/bp_jp_r3c_native_validation_2026-09.md)
for an actual twelve-page run and its retained debt.

On the publish queue path (`Workflow_action = Publish`), the worker runs the
idml step with `--idml-mode both` and then packages the export into one
designer delivery zip via `tools/idml/delivery.py`:
`manual_<model>_<region>[_<lang>]_publish_<version>_handoff.zip` containing the
production and flow IDML with every `LinkResourceURI` rewritten to
`file:Links/<name>`, the linked images collected under `Links/`, the flow outputs, the handoff
reports, `source_trace.json` stamped with the queue row's real version, a
fonts manifest, the declared SIL-OFL faces under `Document fonts/`, optional
licensed Gilroy files when `AUTO_MANUAL_LOCAL_GILROY_DIR` is provisioned on the
build machine, and the versioned reference PDF. The zip is
the designer-facing package: its checklist points to the versioned root IDML,
`missing_assets_report.md` reports package-time link portability, and the
separate `source_asset_resolution_report.md` preserves unresolved semantic
source/flow diagnostics without presenting them as broken packaged links. The
zip is staged under `reports/releases/<model>/<region>/<lang>/versions/<version>/`,
uploaded to the knowledge base, and its link is written to the queue row's
`idml_file` field. The bare `.idml` is no longer uploaded: its image links are
absolute build-machine paths that die with the build worktree, so only the
packaged zip is a usable designer deliverable.

The remote Publish workflow reads its XeLaTeX/CJK apt package set from
`.github/texlive-apt-packages.txt` and binds the apt-archive cache key to that
file plus runner OS/architecture. Each run writes cache hit/miss and install
duration to the Actions summary. For cache acceptance without touching
`Document_link`, dispatch `feishu-build-queue.yml` with
`texlive_smoke_only=true`; that path compiles a deterministic smoke PDF,
reports its SHA-256, and skips `process-build-queue` entirely.

For approved reference figures, the package-time link set must include every
referenced file under `_generated/idml_reference_assets/` plus the pairing-panel
PDF, and `missing_assets_report.md` must report zero missing links. For release
acceptance, extract the final ZIP and run `indesign_finalize.py` against its
versioned root IDML. `check_idml`, ZIP integrity, or preflight of an earlier raw
IDML does not prove the delivered `Links/` package.

For queue rows with `Git_ref`, the build worktree is based on the current
`origin/main`; only the active `docs/_review/<model>/<region>` target is
overlaid from the row's review ref. The worker does not replace sibling target
directories. For a versioned Publish, the worker carries the resolved review
commit into the subprocess; the clean gate accepts the target only when its
complete file set and blob hashes match that commit, then writes the composite
provenance into the release manifest. The manifest consumes the tree SHA proof
frozen by that entry gate rather than re-reading the working subtree after the
build has staged target assets. Approved-reference targets do not run the
parameter-sync mutation at all: every print renderer consumes the same
`review-asis` bytes that the contract pins. This prevents both a stale local
`main` branch from silently running an older renderer and fresh Base values
from bypassing review on their way into a release.

The default flow style map lives at
`docs/templates/idml_template/style_mapping/flow_style_map.json` and is copied
to each flow output folder as `flow_style_map.json` so design can map the story
to an InDesign template without changing production styles.

`configs/config.eu.yaml` now represents the live `EU` region-family row as `eu-merged`, routes blank-`Lang` queue rows to the merged EU manual, and keeps `sync.phase2.tables.spec_master` pinned to the live Base view that contains `JE-1000F_EU` rows. `configs/config.eu-en.yaml`, `configs/config.eu-fr.yaml`, and `configs/config.eu-es.yaml` are the explicit English, French, and Spanish single-language EU surfaces when you need one language family at a time.

Word styling note:

- `configs/config.us-en.yaml` now post-processes the generated DOCX so non-safety / non-spec pages inherit the `reference_en.docx` heading, table, and default paragraph styling
- the multi-page bundle HTML remains unchanged as a trace artifact. Immediately
  before Pandoc only, the exporter removes opening and closing `<main ...>`
  wrappers with a bounded tag matcher, preserves their children byte order, and
  deletes the temporary HTML after conversion. This prevents Pandoc from
  selecting an earlier empty `<main></main>` and emitting an empty DOCX; do not
  replace this with DOM reserialization, which can reorder component markup

Single-page preview and fast draft:

```powershell
python build.py preview --config configs/config.us-en.yaml --model JE-1000F --region US --page 03_product_overview_placeholder
python build.py fast --config configs/config.us-en.yaml --model JE-1000F --region US
```

Standalone release traceability:

```powershell
python build.py release-manifest --config configs/config.ja.yaml --model JE-1000F --region JP
```

When `finalize_report.json` is present beside the production IDML, the release
JSON records native `page_count` and the overset-story count under
`indesign_package.preflight`. The release CSV flattens them as
`indesign_preflight_page_count` and
`indesign_preflight_overset_stories`. A blank value means native preflight did
not report that signal; the string `0` means it explicitly reported no overset
stories. Release-manifest generation remains non-blocking when native finalize
has not run.

Keep existing build artifacts:

```powershell
python build.py html --config configs/config.us.yaml --no-clean
```

Open generated artifacts if the backend supports it:

```powershell
python build.py pdf --config configs/config.us.yaml --open
```

Override PDF backend:

```powershell
python build.py pdf --config configs/config.us.yaml --pdf-mode latex
python build.py pdf --config configs/config.us.yaml --pdf-mode word
```

The LaTeX backend keeps presentation in
[components_base.tex](../docs/renderers/latex/components_base.tex) and
[components_safety.tex](../docs/renderers/latex/components_safety.tex).
Page RST should call those components and keep content separate from the
visual frame. Fixed-format boundaries use **HBPageBreak**; rounded tables use
an independent outer frame while their tabular content owns only the internal
grid. In LaTeX output, one-row label/body tables whose labels resolve to
WARNING, CAUTION, NOTE, or TIP (including the supported localized labels) are
automatically rendered by the shared rounded callout component; HTML and Word
keep the source table. Tune shared geometry in
[layout_params.csv](../data/layout_params.csv), then regenerate params.tex
with python tools/csv_to_tex_params.py.

## 5.1 Terminology Gate

`build.py check` also scans each built bundle for wording the Style Guide has retired:

- `data/terminology_rules.csv` — one row per retired wording: `rule_id`, `lang`, `deprecated_regex`, the `preferred` replacement quoted back in the message, an optional `allow_regex` for contexts where the old form is deliberate (an intentional first-mention gloss, a placeholder token), and a `note` pointing at the Style Guide clause.
- Pages are matched by language: generated pages take the language from their `_<lang>` filename suffix, authored pages inherit the target's language, so a `ko` rule never fires on a German page.

Findings surface as `TERMINOLOGY_DEPRECATED`, a warning-only code — a rule can be registered the day a wording is retired and its existing hits cleaned up afterwards without blocking builds. Flip it to a blocking code only once the tracked lines are at zero, the way the capability gate tightened.

The rule table is the machine-readable half of the Style Guide (飞书知识库「多语言语言资产规范」); when a clause there changes, update the matching row here in the same change.

The gate only sees built bundles. A retired wording sitting in the library stays invisible until some manual renders it — `python tools/lang_asset_sweep.py --terminology` reads Translation_Memory, Terms and the print source tables directly and reports those rows, including ones already marked `Approved`. Template hits are skipped there because the gate already covers rendered pages.

## 5.1 Capability Gate

`build.py check` validates each target against the product capability matrix:

- `data/model_capabilities.csv` — per-`Document_key` feature booleans, mirrored from the 文档构建表 checkboxes (说明书盘点 2026-07-06).
- `data/capability_known_missing.csv` — reviewed `Document_key,reason` exemptions for targets whose capability row is not yet mirrored; unlisted missing rows surface as non-blocking `CAPABILITY_ROW_MISSING` warnings.
- `data/capability_page_rules.csv` — capability -> chapter mapping. `scope=page` requires/forbids a bundle page stem; `scope=section` greps a regex inside matching pages. `required_when_true` / `forbidden_when_false` toggle enforcement per direction, so uncertain rules can be recorded without failing builds.
  The ordered `capability` values in this CSV are also the source for the `model_capabilities.csv` mirror header; do not add a capability to a second Python tuple.

Failure codes: `CAPABILITY_CONTENT_MISSING` (capability TRUE, chapter absent) and `CAPABILITY_CONTENT_UNEXPECTED` (capability FALSE, chapter present). `CAPABILITY_ROW_MISSING` is a warning-only inventory signal unless the target is listed in the known-missing ledger; missing capability rows continue to keep page selection fail-open.

The page assembler consumes the same capability names through manifest
`capability:` annotations. The current 17-manifest family inventory contains 24
UPS page entries, all bound to `UPS功能`; this is enforced by
`tests/test_capability_pages.py` so a new language or single-language carrier
cannot silently bypass assembly-time filtering.

`check` also runs the language-tree parity gate (`tools/check_docs_lang_parity.py`, Milestone I1): `LANG_PARITY_FOREIGN_SHELL` (a ko/ja/zh/uk page carrying almost no target-script text — an untranslated shell), `LANG_PARITY_FOREIGN_LANG_BLOCK` (language-tagged blocks such as `**FR IMPORTANT**` or `\HBApplyLang{xx}` outside the family's languages), `LANG_PARITY_MISSING_LANG_PAGE` / `LANG_PARITY_FOREIGN_LANG_PAGE` (per-language generated page set incomplete, or a leftover page from another language line). Pre-existing findings are registered in `data/lang_parity_known_exceptions.csv` (model, region, code, page, note) so only NEW drift fails; delete a row once its content decision lands.

## 5.2 Language Scope Gate

A family config's `build.languages` is the **union** across every model in that
region, not one model's shipping list: `configs/config.eu.yaml` declares six
languages because the EU line carries Ukrainian templates, while JE-1000F does
not ship Ukrainian. `data/model_languages.csv` holds the per-model answer, keyed
on the same `<MODEL>_<REGION>` document key the capability mirror uses:

- `Document_key,Project,languages,notes` — `languages` is a `;`-separated list
  of registry language codes (semicolon, because a half-width comma inside a
  CSV field has bitten this repo's contracts before).
- Resolution is an **intersection that preserves the family's declared order**,
  so the family config stays the only place that decides ordering and the table
  can only subtract.
- Fail-open, like the capability gate: no row keeps every family language, and a
  row that excludes *every* family language leaves the build unchanged and
  fails `check` instead.

`tools/model_languages.py` resolves the scope; `tools/gen_index_bundle_plan.py`
applies it before any page is planned, so an unshipped language's pages —
including its `csv_page` data pages (`spec_uk.rst`, `symbols_uk.rst`, …) — are
never materialized. Structural problems in the table (missing column, duplicate
key, blank cell, unregistered code) raise instead of parsing to a wrong set.

Pages that carry several languages *inside one file* — the prefaces — cannot be
handled by page selection. Those manifest entries opt in with `lang_blocks:
true`, and `tools/language_block_trim.py` drops the out-of-scope blocks
(`\HBLangTagLine{XX}` in `raw:: latex`, `**XX ...**` bold headers) while
preserving page-structure macros such as `\HBPrefacePageBegin` /
`\HBPrefacePageEnd`. The annotation is opt-in, never sniffed, because `**IT ...**`
is legitimate bold prose elsewhere. When nothing is out of scope the page text
is returned unchanged, so an untrimmed family keeps byte-identical output.
Trimming the shared trilingual preface to `en` reproduces the hand-forked
`00_preface_single_language.rst` byte-for-byte after the bundle's own
empty-line-block normalisation — enforced by
`tests/test_language_block_trim.py`.

A trimmed target also overrides the `MANUAL_LANGUAGE_SCOPE` substitution with
the label derived from its resolved languages, so a five-language EU book no
longer prints "… / Ukrainian" on its preface. The derivation reproduces each
whole-book family's configured literal exactly
(`tests/test_model_languages.py`), and single-language derivative configs keep
their configured literal because they are not trimmed.

Materialized page names disambiguate duplicates with a positional `pNN_`
prefix (`p22_01_fcc.rst` is the fr copy of `01_fcc.rst`), and those names are
pinned outside the build: committed review branches use them as file names and
the approved reference-layout contract lists them as ordered `source_ref`s.
Inserting a manifest entry mid-list would therefore renumber every later
duplicate and irreparably break the contract (`reference_layout_rebind`
refuses a changed `source_ref` sequence). Print-only insertions — the US
book's `00_toc.rst` and `99_back_cover.rst` — declare `ordinal_neutral: true`
on their `rst_include` entries instead: the page materializes in place but
does not consume a numbering ordinal, so every existing `pNN_` name stays
stable. `tools/gen_index_bundle_plan.py` applies the skip; the annotation is
`rst_include`-only and validated like `lang_blocks`
(`tests/test_gen_index_bundle_plan.py` pins the numbering behaviour).
Background: the 2026-08-13/14 same-source-gate incidents, where reseeds
dropped these two pages because they lived only in a hand-edited review index.

Failure codes (`tools/check_docs_language_scope.py`):
`LANG_SCOPE_UNSHIPPED_LANGUAGE` (the scope row is disjoint from the family the
config declares — e.g. `configs/config.eu-uk.yaml` pointed at a model that ships
no Ukrainian) and `LANG_SCOPE_FOREIGN_SCRIPT` (a bundle page carries the script
of a *dropped* language, catching leakage with neither a `_<lang>` page suffix
nor a language tag). Only dropped languages are scanned, so an EU bundle's
allowed CJK identity literal is not treated as drift. The scoped language set is
also what the per-language contract, generated-page, identity and parity
collectors see, so a model that ships five of six family languages no longer
fails on the sixth's missing source data.

Every Sphinx run also feeds the **warning ratchet** (`tools/warning_ratchet.py`, Milestone I2): the warning stream is written to `<out>/sphinx-warnings.log`, sanitized (paths, line numbers, ANSI, and target-specific `docs/_build/<model>/<region>[/<lang>]/rst/` prefixes), and diffed against the committed baseline `data/known_warnings/<stream>-known-warnings.txt`. A warning in the baseline is registered debt; a warning not in it is news. Enforcement is staged: the in-build hook reports by default and fails only with `AUTO_MANUAL_WARNING_RATCHET=strict` (set `off` to silence); the standalone CLI `check` is always strict (new warning → exit 1, missing baseline → exit 2). Seed or refresh a baseline with `python tools/warning_ratchet.py update --stream sphinx-html --log <warnings.log>` and review the diff like code. Flip the default to strict once a few queue rounds have stable baselines.

## 6. Diff Report

Typical usage:

```powershell
python build.py diff-report --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py diff-report --config configs/config.ja.yaml --model JE-1000F --region JP --from-ref HEAD~1 --to-ref HEAD
python build.py diff-report --config configs/config.ja.yaml --tracked-root docs/_review/JE-1000F/JP
python build.py diff-report --config configs/config.ja.yaml --tracked-root docs/_review/JE-1000F/JP --from-ref HEAD~1 --to-ref HEAD
python build.py diff-report --config configs/config.ja.yaml --tracked-root docs/_review/JE-1000F/JP --include-initial-adds
```

Generated report types:

- `*_files.csv` / `*_files.html`
- `*_pages.csv` / `*_pages.html`
- `*_fields.csv` / `*_fields.html`
- `*_index.html`

The current report defaults are review-oriented, not `_build`-oriented.
If `--tracked-root` is omitted, `build.py` resolves `docs/_review/<model>/<region>/` and `reports/version_tracking/<model>/<region>/` automatically from the target.
Initial baseline Added rows are now hidden by default so the first non-baseline review round is easier to read. Pass `--include-initial-adds` when you need the full initial import noise.
Field pairing now prefers stable source back-mapping before falling back to rendered labels, so placeholder/spec label rewrites are more likely to appear as one `M` row with clearer `old_value/new_value` instead of separate `A/D` rows.

## 7. Common Mistakes

- Editing [`docs/_build/**`](../docs/_build) as if it were the authoring surface
- Creating a new config only because the model changed
- Using `review --refresh-review` when only parameter pages need to be synced
- Forgetting to commit `_review/<model>/<region>/` after each review round
- Treating `_build/rst` and `_review` as the same thing
- Putting review metadata in `overrides/` and expecting it to overlay; only `_assets`, `_static`, and `renderers` are copied into the runtime bundle
- Letting `build.py`, `tools/build_docs.py`, or `tools/process_build_queue.py` absorb new low-level implementation instead of pushing that logic into helper modules

## 8. Minimal Troubleshooting

For JE-1000F/JP, `build.py md --config configs/config.ja.yaml --model JE-1000F
--region JP --source runtime` supports the authored text-only inbox table and
its following notes. The document adapter preserves a nonempty, one-row,
three-column inventory with no images and no immediately adjacent table.
Illustrated inbox compositions still require their three images and tip table.
No placeholder images or synthetic tip copy are added.

The prepared-bundle IR adapter distinguishes complete, multi-row signal-word
definitions from single notice callouts using the shared label vocabulary.
Each definition row needs two nonempty cells and a distinct recognized label;
malformed tables beginning with a known signal word still fail. See the
[same-source IR contract](dev/latex_indesign_same_source_plan.md) for the boundary.

The JP symbols introduction's plain boxed heading and two following paragraphs
now enter IR as editable heading/body blocks. The existing dedicated
`tools/manual_ir_cli.py --strict` check on the prepared runtime bundle reports
zero skipped blocks. The parser accepts only the complete supported shape;
unknown TeX content still fails strict extraction. PDF source geometry is
preserved; native InDesign layout acceptance remains a separate check.

`Failed to resolve Product Name from Spec_Master.csv`

- Check [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) for `Row_key=product_name`
- Check model / region / language coverage
- Run `python build.py check --config ... --model ... --region ...`

Review bundle not found

- Seed it first with `python build.py review --config ... --model ... --region ...`

Need to rebuild the first draft from template/data only

- Use `--source runtime`

Need to release from reviewed text only

- Use `python build.py publish --config ... --model ... --region ...`

`STALE_IDENTITY_LITERAL` or another model name is reported during `check`

- fix the template or review text if the model mention is stale
- if the foreign literal is intentional, add it to `checks.allowed_foreign_identity_literals`


Prepared-source integrity: a declared page include that is missing or is not a
file now stops source discovery with the index and source path. Registered
prose macros need complete arguments; unsupported content around recognized
macros increments `skipped_raw` and fails strict Manual IR validation. A valid
macro no longer hides adjacent unsupported copy. Existing language/tag
selection and successful payload formats remain unchanged.

IDML handoff validates the source `manual.ir.json` before copying artifacts or
writing reports. Missing IR is explicitly unavailable; corrupt IR is an error,
not a zero-skipped report. This integrity work does not migrate Web to whole
Manual IR and does not certify native JP layout. See the
[shared-source plan](dev/latex_indesign_same_source_plan.md) for remaining consumer and parser boundaries.


Web specification IR: declared `h2.hb-spec-section` / governed table pairs now
pass through the public ManualSource assembler and ManualIR validator before
Web rendering. Web-profile builds bypass Word specification text extraction,
preserving authored links, emphasis, line breaks and trailer content. Document
profile behavior stays with its existing Word reader. All declared sections
must pass before any section is replaced. The adapter is a scoped prepared-HTML
projection, not a whole-book IR; other Web components and neutral rich-text
parsing remain pending in the [shared-source plan](dev/latex_indesign_same_source_plan.md).


Web LCD and troubleshooting tables also consume public ManualIR. Both prepared
Web bundles and standalone `{lcd-icons}` / `{troubleshooting}` directives share
one source decoder and consumer, retaining the assembly planner's explicit page
identity or authored table class. Filenames and translated header vocabulary
never select a table. A later invalid table rejects the complete transformation
before changing the caller DOM. Rich lists, links, icon alt text, figure captions
and authored headers survive IR serialization/replay. A governed figure containing
multiple tables is ambiguous and fails closed rather than duplicating content.
Standalone staging includes the bounded IR runtime, language registry and existing
table stylesheet contract; it does not import the source checkout or legacy IDML
extractor. `web_source` is the shared provenance constructor, including the active
specification adapter. Remaining whole-manual and HTML-parser boundaries are
tracked in the [shared-source plan](dev/latex_indesign_same_source_plan.md).
