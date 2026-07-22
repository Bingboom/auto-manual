# Windows Build Guide

Updated: 2026-07-16

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

Local PDF font override:

- for local-only Gilroy preview, set `AUTO_MANUAL_LOCAL_GILROY_DIR=<absolute-font-dir>` before `python build.py pdf ...` or `python build.py publish ...`
- the font directory must contain `gilroy-regular-3.otf`, `gilroy-bold-4.otf`, `Gilroy-LightItalic-12.otf`, and `Gilroy-ExtraBoldItalic-10.otf`
- the helper only patches the generated `_build/latex/fonts.tex` copy for that run; unset the env var to return to the shared fallback chain, and remote CI workers are unaffected

Meaning:

- `validate`: validate config and [`data/layout_params.csv`](../data/layout_params.csv)
- `sync-data`: use the local `lark-cli` login plus `sync.phase2.*` config/env bindings to write normalized CSV snapshots into [`../data/phase2/`](../data/phase2), using the CLI's `base` record listing flow under the hood; when `sync.phase2.spec_master_sources` is configured, `sync-data --table spec_master` reads the two split source tables instead of the legacy total table
- `tools/content_lint.py --json --write-report`: local closed-loop QC observation step for the current phase2 snapshot. It writes `reports/content_qc/<run-id>/findings.json` and `report.md`, includes best-effort snapshot `source_ref` values, keeps `record_id` nullable, and does not write Feishu rows or add a `build.py` action yet.
- `tools/source_intake.py run`: MVP ingress for structured spec/manual Markdown or Feishu cloud-doc content. It parses pipe-style tables into reviewable candidates for `Spec_Master`, `Page_Placeholders_Source`, `Manual_Copy_Source`, `Spec_Footnotes`, and `Spec_Notes`; with `--data-root`, it compares against the current phase2 snapshot and emits `source-table-change-request/v1` only for existing-row updates that can later be approved and applied through the existing source-table writer. It does not create online rows, edit `data/phase2/*.csv`, or replace cloud-doc backport. Track rollout in [`dev/source_intake_mvp_checklist.md`](./dev/source_intake_mvp_checklist.md).
- `tools/source_intake.py approve` / `apply` / `verify`: P4-P7 closure for that intake run. `approve` writes `source_intake_approval.json/.md` from explicit `--approve <delta_hash>` values or a controlled `--approve-all-resolved` review run. `apply` writes `source_intake_apply.json/.md` through the existing approval-gated source-table writer; it is dry-run by default and requires `--write --table-binding TABLE=BASE:TABLE_ID` before touching Feishu. `verify` runs labeled sync/build/review/backport commands, then writes `source_intake_closure.json/.md`; add `--require-write` when the closure must prove live source-table writes.
- `data/source_table_contracts/phase2_source_tables.json`: repo-maintained phase2 source-table contract for table keys, snapshot files, intake targets, writable fields, and `source_record_index` mapping. Update it with [`architecture/phase2_source_tables_reference.md`](./architecture/phase2_source_tables_reference.md) whenever an online source-table schema change could affect intake, backport, source-table writeback, or sync-data.
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
- `lcd_icons`, `troubleshooting`, `symbols_blocks`, `variable_defaults`, `variable_lang_overrides`, and `manual_copy_source` sync as normal phase2 tables; the LCD icons renderer reads `lcd_icons_blocks.csv` and renders downloaded `figure` attachments from `data/phase2/_attachments/lcd_icons/`, the troubleshooting renderer reads `troubleshooting_blocks.csv`, the symbols renderer uses downloaded `Figure` attachments from `data/phase2/_attachments/symbols` when present, `symbols_blocks` also maintains signal structure with `block_type=signal_row`, page short copy such as LCD / Symbols titles, headers, Symbols signal labels / meanings, Product overview labels, and spec page / section titles is authored in `Manual_Copy_Source.csv`; `sync-data` renders generated runtime copy into `Localized_Copy.csv` and generated spec title metadata into `spec_titles.csv`, image alt text is derived from existing titles, `symbol_key`, or generated signal labels, LCD status-word bolding reads `Status_Words.csv` exported from Translation Memory rows marked `是否为 status word=Y`, and LCD description variables continue to resolve from `Variable_Defaults.csv` plus `Variable_Lang_Overrides.csv`
- if the Base keeps `Model` as a linked-record field, maintain a text `Model_key` column for variable defaults so exact model matching stays independent of Feishu record ids
- `sync-data` normalizes `Spec_Master.csv Slot_key` back to plain slot tokens when the source table stores markdown-link wrappers for page-value placeholders
- `sync-data` also resolves full field names through Base field metadata, so long headers are not dropped when `lark-cli` shortens them in record-list output
- when `spec_master` is synced from the split source tables, `sync-data` reads `spec_footnotes` as needed and rewrites Feishu linked-record footnote refs in `Spec_Master.csv` to stable `Footnote_id` values
- when one target references a `Footnote_id` that is missing only in its own region but exists as one unambiguous sibling-region row for the same model, validation and rendering now reuse that fallback definition instead of stopping the build immediately
- `sync-data` does not repair bad `Is_Latest` flags; leave those source-table problems visible so `check` and publish validation can fail loudly
- [`../tools/dingtalk/spike_cli.py`](../tools/dingtalk/spike_cli.py) is the manual Phase 0 smoke helper for future app-only DingTalk provider research; it defaults to the official App-Only token flow and lets maintainers inject product-specific list/update/upload endpoints without changing the current queue runtime. A minimal smoke run looks like `python tools\dingtalk\spike_cli.py all --record-id <stable_row_id> --update-set smoke_checked=true --upload-file .tmp\phase0-smoke.docx`.
- [`../tools/dingtalk/auth.py`](../tools/dingtalk/auth.py) now exposes the verified App-Only token helper behind `DINGTALK_CLIENT_ID`, `DINGTALK_CLIENT_SECRET`, and `DINGTALK_CORP_ID`, and [`../tools/dingtalk/workspace.py`](../tools/dingtalk/workspace.py) can parse a target node ID from a normal DingTalk docs URL such as `https://alidocs.dingtalk.com/i/nodes/<node_id>`.
- `rst`: materialize [`docs/_build/<model>/<region>/rst/`](../docs/_build)
- `review`: seed [`docs/_review/<model>/<region>/`](../docs/_review) from runtime draft
- `--source review-asis`: render the committed `docs/_review/<model>/<region>/` bundle exactly as-is — only the conf/asset skeleton is materialized and the review overlay supplies every content page, so no page is re-derived from the build data-root. Unlike `--source review` it neither pre-syncs review params from data nor runs the Spec_Master identity guard, so it renders a review target whose model is absent from the active data-root (e.g. the CI `Review Preview Package` fixtures under `tests/fixtures/phase2`). The `Review Preview Package` workflow uses this mode, which is why a newly onboarded model (not yet in the fixtures) previews instead of failing the whole package
- `check`: run validation + prepare bundle + content checks, including stale identity scan, contract validation, and duplicate RST/raw HTML text consistency checks
- `asset-check`: validate the image-asset registry and resolve approved exports for renderer imports. `--allow-temporary` is only a diagnostic/operator inspection option for this command; bundle assembly never enables it. `--publish` applies the stricter registry-wide status gate. Editable `.ai` masters belong in the dedicated Feishu asset-source table, while `data/asset_sources.csv` records their hash/scope and `data/asset_generation_candidates.csv` controls which candidates may be sent to image generation.
- `asset-intake`: deterministically package a PDF-compatible Illustrator master through a strict recipe. All four `--asset-source-key`, `--asset-source-file`, `--asset-recipe`, and `--asset-output-root` flags are required; the output root must not exist. The command snapshots and verifies the source, emits archive pages/previews plus approved/quarantined recipe exports, scans raw and decoded PDF objects for Illustrator private markers, verifies declared full hashes, and writes a deterministic ZIP with its manifest/index. It never edits the source, worktree, registry, or Base and exposes no promotion flag through `build.py`.
- Reviewed promotion is a separate, fail-closed maintainer action. A contract under `data/asset_promotions/` must bind the reviewer, decision time, exact model/region/languages, source AI, frozen reference PDF, recipe/evidence, candidate bytes, promoted output bytes, and deterministic composition. The registry accepts `source=reviewed-promotion:<promotion_id>` only when every full SHA and whitelist still matches. Raw App/QR candidates remain quarantined; deleting or weakening the contract must make resolution fail rather than fall back to a shared legacy image.
- `.ai` source intake is an operator workflow, not a Git large-file path: follow [`../user-guide/closed_loop_ops_guide.md` §4.9.2](../user-guide/closed_loop_ops_guide.md#492-ai-交付与登记一页流程) to run and compare the package, avoid duplicate attachments, upload the source/ZIP/manifest through the three separately created `04_资产*` tables, and verify downloaded bytes before updating `data/asset_sources.csv`. The live Base/table/view/field binding is frozen in [`../data/asset_base_bindings.json`](../data/asset_base_bindings.json); the JE-1000F US master is the first round-trip-verified source. If those tables are inaccessible, stop and leave the source pointer empty. Never read, write, or fall back to the legacy illustration or staging intake table.
- RST image, figure, substitution-image, and raw-HTML `src` references may use a registry identity such as `.. image:: asset:operation/ac_output`. The finalizer runs only after runtime materialization, review overlay, and frozen attachment aliases. It requires an approved export matching the bundle model/region/language, accepts only PNG/JPG/JPEG/SVG/PDF, and never falls back to `.ai`, `🔧临时替代`, `❌缺失`, or `⛔隔离` rows.
- Every prepared bundle freezes `asset_usage_manifest.json`, `asset_registry_snapshot.csv`, and a finalized `bundle_manifest.json`. The usage manifest distinguishes `registry-uri`, explicit `review-override`, and `legacy-path` references; the bundle manifest hashes the final RST include closure, configuration, staged support trees, and the two asset sidecars into `bundle_sha256`. Review seeding restores semantic `asset:` references from rewrite provenance so a review round does not silently downgrade asset identity.
- Shared templates under `docs/templates/` are bulk-migrated: every `common_assets` image directive and raw-HTML `src` uses `asset:<asset_key>` and is therefore registry status/scope/hash gated at bundle prepare. Path-based references remain compatible (recorded as `legacy-path`) but are reserved for sources that have no registry key yet — new template references should use the registry identity. Release manifests do not yet carry this asset lineage; `bundle_manifest.json` is the current bundle-level provenance surface.
- Target-specific exports do not replace a shared registry key. They use a unique `asset_key` plus `override_for=<shared asset_key>` and a narrow model/region/language scope. A shared template keeps the stable base URI; the frozen registry resolver selects exactly one matching override or falls back to the shared row, and rejects ambiguous override matches.
- `build.py idml` prepares only RST when the exact model/region/language target is present in the approved reference-layout registry; its production exporter consumes that hash-bound physical plan directly. Targets without an approved entry retain the historical LaTeX-PDF preparation used for fuzzy page matching.
- `sync-review`: refresh review files affected by CSV data changes
- `process-review-start-queue`: Start Review bridge; it consumes `sync.phase2.review_init` rows where `是否进入Review` is checked and `Workflow_action` maps to `Start Review`, resolves the review target from `Document_Key` alone, uses `Build_family` / `Lang` only as optional config-routing hints, groups only the rows whose resolved config enables `build.queue_by_document_key`, syncs the latest phase2 snapshot, always reseeds `docs/_review` from the latest `origin/main` template/data state, force-updates the routed review branch when it already exists, creates or reuses the PR, then writes back the same `Git_ref`, `PR_url`, `Review_status=InReview`, and cleared `是否进入Review` state to every pending row in that group
- Start Review eligibility is the conjunction of `Document_Key` being a non-empty `<MODEL>_<REGION>` value, `是否进入Review` being checked, and `Workflow_action` mapping to `Start Review`
- when `Document_Key` is a linked Base field, the API can expose only the linked record id, so chat-driven Start Review lookup should use `Task_id` as the stable selector and then verify `是否进入Review` plus `Workflow_action=Start Review`
- `Start Review` now means "force restart and reseed from the latest template". Existing committed `docs/_review/<model>/<region>/` content on `main` is no longer a duplicate guard, and re-checking `是否进入Review` on an `InReview` row will restart the review seed flow
- `process-build-queue`: Build Draft Package / Publish bridge; it consumes `sync.phase2.document_link` rows where `是否触发文档构建 = Y`, write `开始构建时间` immediately when one row is picked up, resolve the matching config family from `Build_family` first and `Lang` second, group only the rows whose resolved config enables `build.queue_by_document_key`, refresh `data/phase2` only when `Document_link.是否强制刷新数据 = true`, build Draft rows as `check + word + md`, switch Publish rows to `check + diff-report + word + pdf + md`, upload the Draft DOCX or Publish PDF to the primary Feishu/wiki sink, optionally sync that same primary artifact to DingTalk, write the local DOCX release path into `Document directory`, keep `Document link` as DOCX for Draft and PDF for Publish, import Markdown into `飞书云文档` when that field exists, optionally write the DingTalk node URL into `Document link_dd`, write a timestamped build status into `构建结果`, write the refresh result into `data_sync`, clear `是否强制刷新数据`, and flip the trigger back to `已构建` on success
- for `build.queue_by_document_key` configs, Draft rows with a non-empty `Lang` are grouped by `Document_Key + normalized Lang`; `br` / `pt-br` normalizes to `pt-BR`, and the selected language is passed to the build/check/validate/bundle path. `configs/config.pt-br.yaml` now follows the single-language US build path, so Brazil Portuguese draft rows should use `Build_family = pt-br` with `Lang=br` or `Lang=pt-BR` instead of adding an English companion row.
- row writeback now has an explicit running stage: `process-build-queue` writes `RUNNING | ... started_at=...` to `构建结果` before build execution, then replaces it with `SUCCESS` or `FAILED`
- if DingTalk mirror sync is enabled and the row also has `是否上传钉钉`, that checkbox becomes the row-level gate: checked rows also sync DingTalk and write `Document link_dd`, unchecked rows stay on the normal Feishu/wiki upload path for that run
- if the table does not have `是否上传钉钉`, the worker follows the current global worker mode for that whole row
- if that checked row also has `DingTalk_target_node_url`, the worker uploads to that row-level target first; otherwise it falls back to the global `DINGTALK_DOCS_TARGET_NODE_URL`
- if the row also has `operator_union_id`, the worker can resolve a per-operator DingTalk session file before falling back to the global browser-session envs
- `DingTalk_session_key` and `钉钉会话键` are accepted as aliases for `operator_union_id`; if the row uses `alice`, the worker expects `<session_root>/alice.json`
- if a DingTalk-enabled row points at a missing per-operator session or there is no usable global DingTalk session, the queue now fails that row before build starts and writes the exact missing-session reason back to `构建结果`
- `queue-query`: OpenClaw Phase 2 queue resolution helper; it reads the Feishu-bound `Review Init` / `Document_link` rows and returns the concrete `record_id`, optional `Task_id`, workflow intent, `Git_ref`, `Document link`, and status fields that a natural-language control layer needs before dispatch
- `queue-resolve-action`: structured OpenClaw dry-run resolver; it turns one natural-language ask into the bounded action contract from the control-layer plan, including `action_name`, `resolution_status`, required confirmation, missing required fields, and the matched queue row
- `manual-index-query`: read-only OpenClaw helper for the `发布文档管理` Base view. It answers product/manual-link inventory and overview asks such as `查 JE-2000F 的说明书链接`, `查询各产品的说明书`, or `获取说明书总览信息`; it respects `FEISHU_MANUAL_INDEX_*` overrides and does not dispatch builds.
- for this repo, treat **BlockClaw** as the OpenClaw-backed document-build operator rather than a generic assistant: its primary job is to work with content blocks, run review/build/publish work, inspect queue state, explain build failures, and only secondarily help with translation or copy work that supports the manuals
- `translation-memory`: query the repo-owned `data/phase2` multilingual snapshot and return compact translation memory context for OpenClaw or human translation tasks; combine it with `sync-data` when freshness matters
- `validate`: catches missing phase2 table base-token/table-id bindings and page-manifest languages that are not declared in `build.languages`, before `sync-data` or a build reaches runtime
- `python3 .agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py --query-text "<paragraph>" --source-lang en --target-lang fr --format prompt`: preferred live sentence-pair memory for OpenClaw translation; it reads the dedicated `Translation_Memory` base first and emits prompt-ready context. In chat replies, keep that lookup implicit, return the final translated wording first, prefer one foreground lookup over a background poll flow, and rely on the script's short local cache for repeat lookups unless you need `--no-cache`.
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
- the Feishu IM adapter keeps batch link replies card-friendly: status summaries omit `Document link` URLs, then each unique artifact link is sent as its own follow-up message so Feishu can render it as a document entity when the chat client supports that; short follow-ups such as `发` / `发一下` reuse the stored batch context and resend those links
- when the operator needs a stable full inventory count rather than latest links, use `queue-scope=document-link`, `result-contains=success`, and a sufficiently high `limit`, then classify returned rows by `normalized_workflow_action` (`draft` or `publish`) across the relevant config families such as `configs/config.us.yaml` and `configs/config.ja.yaml`; `queue-query --json` exposes `matched_count`, `returned_count`, `limit`, and `truncated`, so default-limited broad queries are visibly incomplete instead of silently dropping rows
- conversation context is only a selector cache for Feishu IM follow-ups; deleted or moved rows must be reported as not found after a fresh table read, not reconstructed from remembered row data
- `queue-execute`: OpenClaw Phase 2 deterministic execution helper; it resolves one Feishu row from `--query-text`, dispatches the matching `main`-owned GitHub workflow through the local control-layer CLI, waits for completion, then re-reads the Feishu row and returns the final `record_id`, `Git_ref`, `构建结果`, and `Document link`. For `Start Review`, an already `InReview` row with `Git_ref` is treated as completed and returned without another dispatch.
- `queue-execute --allow-multiple`: multi-target batch dispatch. Instead of requiring one unique row, it resolves every matching row, dispatches each eligible one (`是否触发文档构建=Y`, not already completed) through the control-layer CLI in a single command call, and returns one per-record JSON report (`matched_count`, `dispatched_count`, `skipped_count`, `error_count`, and a `results` list of `record_id`/`run_id`/`status`/`reason`). It is accept-first (no completion wait); already-built or not-triggered rows are reported as `skipped` with a reason rather than silently dropped, so a multi-target ask fires every eligible target in one shot instead of only the first.
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
- queue routing now uses `Build_family` as the primary selector: `us-merged`, `eu-merged`, `us-en`, `eu-en`, `us-es`, `us-fr`, `pt-br`, `jp-ja`, and `cn-zh`; `Lang` is only a compatibility fallback when `Build_family` is missing
- queue rows should now use `Workflow_action` only: `Start Review` to force restart/reseed review branches, `Build Draft Package` for review-stage rebuilds, and `Publish` for publish-stage builds; leave `Doc_phase` blank
- when review-init reuses the shared `Document_link` binding, the start-review worker only consumes `Workflow_action = Start Review`, while the build queue only consumes `Workflow_action = Build Draft Package` or `Workflow_action = Publish`
- merged US/EU review-init and build-queue rows should use `Build_family = us-merged` / `eu-merged` and may leave `Lang` blank; single-language rows should use the matching single-language family such as `us-en` / `eu-en` / `us-fr` / `us-es` / `pt-br`
- config policy for `build.queue_by_document_key`: turn it on for merged whole-book families that intentionally build one shared manual across languages, such as today's `us-merged`, `eu-merged`, and future `cn-merged`; leave it off for single-language families such as `us-en`, `eu-en`, `us-fr`, `us-es`, `pt-br`, `jp-ja`, `cn-zh`, or future `eu-de` / `eu-fr`, which should continue to be isolated by `record_id`
- when the queue row carries `Version`, Build Draft Package DOCX/Markdown names stay version-suffixed such as `manual_je1000f_us_en_0.2.docx|md`, while Publish queue release artifact names become `manual_je1000f_us_en_publish_0.2.docx|pdf|md`; only the Draft DOCX or Publish PDF is uploaded back to `Document link`
- `Workflow_action = Build Draft Package` rows must carry `Git_ref`; queue builds now seed a temporary worktree from the latest `origin/main`, then overlay only `docs/_review` from that review branch, so the queue keeps the current `main` toolchain while still rendering the selected review content instead of silently falling back to `main`
- on a local worker, if a same-named local branch for `Git_ref` already exists, the queue uses that branch directly so local review edits can be built before they are pushed upstream
- if that fetch hits a transient GitHub network failure but the worker already has the same `origin/<Git_ref>` or local branch cached, the queue reuses the cached ref and keeps building from the intended review content
- direct `build.py` actions still write Build Draft Package outputs to the current repo [`../docs/_build/`](../docs/_build) tree by default
- for local verification, use [`../scripts/local_build.py`](../scripts/local_build.py), [`../scripts/local_build.ps1`](../scripts/local_build.ps1), or [`../scripts/local_build.sh`](../scripts/local_build.sh); they default `check`, `diff-report`, `release-manifest`, `publish`, and other staging-safe local actions to `.tmp/staging`
- explicit `--staging-root <dir>` or `AUTO_MANUAL_STAGING_ROOT=<dir>` still redirect generated `docs/_build`, `reports/version_tracking`, and `reports/releases` under another isolated root when needed
- Publish queue DOCX/PDF/Markdown outputs are staged under [`../reports/releases/<model>/<region>/<lang>/versions/<version>/`](../reports/releases), Markdown sidecars such as `assets/`, `conf.py`, and `index.md` are preserved when present, and the latest publish HTML snapshot is mirrored under [`../reports/releases/<model>/<region>/<lang>/latest/html/`](../reports/releases) for Vercel hosting; when `Document_link.HTML_link` exists, the remote publish worker writes the deployed Vercel URL back to that field after the production deploy step
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
- if you also want the uploaded Word file to be moved into wiki automatically, give that same user/bot identity edit/container permission on the destination wiki parent node; otherwise the upload still succeeds, the worker falls back to the latest Drive URL in `Document link`, and the status is marked `drive_only` with the wiki attach error
- `publish`: run `check -> diff-report -> word -> pdf -> md -> release-manifest` for one explicit target
- `release-manifest`: write JSON / CSV release traceability for one explicit target
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
- use `process-build-queue --workflow-action publish` when a Publish row should be built through `build.py publish` plus `build.py html --source review`, uploaded as PDF, staged with DOCX/Markdown kept in `reports/releases`, and imported to `飞书云文档` when that field exists
- `process-build-queue --record-id <record_id>` narrows one run to one `Document_link` row
- `feishu-start-review.yml` is the Start Review worker on `main`; if Feishu triggers it, dispatch it on `main` so review-start always uses the latest workflow definition
- review PRs created by that trusted Feishu Start Review worker automatically approve their `Manual Validation` and `Review Preview Package` checks; ordinary external pull requests still use GitHub's approval gate
- `feishu-build-queue.yml` is the Publish-stage worker for `main`
- `feishu-draft-build-queue.yml` is the Build Draft Package worker on `main`
- the repo now ships one OpenClaw plugin package under [`../integrations/openclaw/auto-manual-control-layer/`](../integrations/openclaw/auto-manual-control-layer); it is the supported control-layer package when you want one chat entrypoint for these three workers
- OpenClaw dispatches still call only the `main`-owned workflows; they add `openclaw_dispatch_nonce` as a correlation input and the workflows upload `openclaw-run-metadata` as a machine-readable status artifact
- OpenClaw dispatches `start-review`, `build-draft`, and `publish` with the resolved Feishu `record_id`; the optional `Task_id = Document_ID + "_" + Workflow_action` field is used during lookup to distinguish same-document build/publish rows, while Start Review can be resolved from `Document_Key` alone. Later `start-review` retries against rows already updated to `InReview` with `Git_ref` return the completed row instead of creating extra GitHub Actions failures.
- Feishu IM natural-language control can execute config-scoped batch Draft builds when the message names a model, a market, and manual copy or config scope, for example `输出JE-1000F的所有欧规说明书文案`, `构建JE-1000F的所有欧规说明书文案`, `基于配置构建JE-1000F的欧规`, `触发 JE-2000E_EU 欧规整包构建`, or the implicit-all form `构建JE-1000F的欧规说明书文案`. The resolver infers a `Task_id` prefix such as `JE-1000F_EU_`, constrains the action to `Build Draft Package`, and only keeps rows where `是否触发文档构建` is enabled. When no market is named, `构建JE-1000F说明书文案` uses the broader `Task_id` prefix `JE-1000F_`, so every triggered Build Draft Package row for that model is eligible across markets. Versioned market-level asks such as `构建 JE-1000F_EU_1.0 的欧规说明书文案` also add `Version=1.0`. The adapter then dispatches each matched row with `--no-wait` so the jobs can run independently. The draft workflow concurrency group includes the row `queue_record_id`, which prevents GitHub Actions from cancelling older pending rows in the same batch. `最新` does not collapse batch Draft requests by shared `Document_Key`; each language row remains eligible when its trigger checkbox is enabled. `是否强制刷新数据` is not a target selector; the queue worker reads it as a build-time input and runs `sync-data` before the build when it is checked.
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
- that workflow now runs `python -m ruff check build.py integrations tools tests scripts` as the minimal static gate before the heavier unit/build jobs
- that workflow now also runs `npm ci && npm test` in [`../integrations/openclaw/auto-manual-control-layer/`](../integrations/openclaw/auto-manual-control-layer) so the OpenClaw command bridge stays covered in CI
- that same workflow now also runs stable smoke paths for `build.py diff-report` and `build.py release-manifest`
- that same workflow now also runs `python tools/check_maintainability_guardrails.py` so the current hotspot wrappers and validators do not quietly grow back into giant files
- `build.py check` scans template and prepared bundle RST files for duplicated list text across normal RST and raw HTML branches; maintainers should treat the RST list as the source wording and keep renderer-specific copies aligned whenever manual prose changes
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

Pass target differences through:

- `--model`
- `--region`
- `build.targets`
- generated `data/phase2/*.csv` snapshots

Mirror repository sync rule:

- [`../.github/workflows/sync-hello-docs.yml`](../.github/workflows/sync-hello-docs.yml) runs only in `Bingboom/auto-manual` on `main` pushes or manual dispatches from `main`
- the workflow copies the source tree into `Bingboom/Hello-Docs` and commits the content change there; it does not copy repository Secrets or Variables
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

- when a PR changes the zh manual family under `docs/templates/page_zh/`, `docs/templates/recipes/zh/`, or `docs/manifests/manual_zh.yaml`, the review-preview workflow switches the default landing target to `configs/config.zh.yaml --model JE-2000E --region CN --source runtime`, but the packaged workspace still includes every existing review model

### 3.6 Package a Review Preview for Design

Use this when design needs the rendered review HTML plus the current family-level diff package:

```powershell
python tools/process_docs/build_review_preview.py --config configs/config.us-en.yaml --model JE-1000F --region US --source review --from-ref HEAD~1 --to-ref HEAD --all-review-models
```

Config note:

- omit `--config` when `--region` is `US`, `JP`, or `CN` and you want the shared family default config
- keep `--config configs/config.us-en.yaml` when you want the packaged workspace to open on the explicit US English single-language target by default

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

Vercel note:

- `Review Preview Package` now uploads the review-preview workspace as a GitHub artifact only
- [`.github/workflows/feishu-build-queue.yml`](../.github/workflows/feishu-build-queue.yml) is now the Vercel deployment path: after a successful queue-driven Publish row, it stages [`../site/publish-latest/dist/`](../site/publish-latest/dist), then runs `vercel pull`, `vercel build`, and `vercel deploy --prebuilt`; if `Document_link` exposes `HTML_link`, the workflow also writes that deployed URL back to the source row, while the raw deploy URL stays available in `publish_meta.json` and `openclaw-run-metadata` even when GitHub masks the summary/log display
- Vercel should host the latest publish HTML only; do not rely on Git-triggered Vercel Python builds for this flow
- configure `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID` in repository secrets for the deploy step

Read the Docs note:

- [`.readthedocs.yaml`](../.readthedocs.yaml) is the RTD catalog path for the generated public manuals; the catalog scope is every target whose review bundle is committed on `main` (currently `JE-1000F / US`)
- RTD builds from a bare clone with no Feishu credentials and no local `data/phase2` snapshot, so each catalog target is rendered with `python build.py md --source review-asis --data-root tests/fixtures/phase2`: the committed [`docs/_review/<model>/<region>/`](../docs/_review) bundle supplies the content and the tracked fixture snapshot supplies the frozen attachments and capability plan (`--source runtime` cannot resolve Spec_Master identity there and must not be used in `.readthedocs.yaml`)
- to add a target to the catalog, first land its `docs/_review/<model>/<region>` bundle on `main`, then add its `build.py md` line to `.readthedocs.yaml`
- RTD installs the system `pandoc` package, then runs [`../tools/readthedocs_source.py`](../tools/readthedocs_source.py) to assemble [`../docs/_build/rtd/`](../docs/_build) with one link-only root `index.md` that lists the generated manual entries and mirrors each manual's image assets under Sphinx `_static/manual-assets/`
- **Same-source print web edition:** the catalog leads with a print-layout page rendering of each manual, built from the layout contract's concrete output — the LaTeX publish PDF, which is generated from the *same* prepared bundle the IDML export consumes, through the repo's composition contract (`components_*.tex` / `page_*.py`) that replicates the approved InDesign reference. Because RTD has no TeX toolchain, the PDF is built at publish time (`python build.py pdf --pdf-mode latex --source review-asis …`) and committed to [`../reports/releases/<model>/<region>/web_edition/<name>.pdf`](../reports/releases) with a `<name>.json` provenance sidecar (title, version, source, `pdf_sha256`, and the refresh command). On RTD, after the `md` build, `.readthedocs.yaml` runs [`../tools/render_web_edition.py`](../tools/render_web_edition.py), which uses [`../tools/idml/web_edition.py`](../tools/idml/web_edition.py) + PyMuPDF (pinned in `requirements.lock`) to rasterize each PDF page into a page-card web reading flow at `docs/_build/<model>/<region>/webedition/` (`body.html` + `assets/` + `manifest.json`), with a visually-hidden per-page text layer (search / screen-reader) and Open/Download-PDF links. `readthedocs_source.py` grafts it as the **primary** catalog entry ("print edition"), keeping the flow HTML manual as the secondary "HTML edition" link. The pages are the exact print layout; text does not reflow. It is best-effort: if no committed PDF is found the CLI logs and skips, and the catalog keeps the HTML-only entry so the RTD build stays green. **Refresh discipline:** rebuild and re-commit the PDF whenever the manual content changes (the sidecar carries the exact command), so the print edition stays in sync with the committed review bundle
- do not point RTD at the repo-root [`../docs/`](../docs) tree for this flow; `docs/_build/rtd/` is the generated Sphinx source for the catalog, and each target-scoped `md` directory remains the generated MyST source for one manual
- RTD does not publish queue-driven Publish HTML or Word / PDF artifacts; keep Vercel and release outputs as the formal publish path

### 3.7 Publish a Final Word Release

```powershell
python build.py publish --config configs/config.ja.yaml --model JE-1000F --region JP
```

This is the formal release command.
It requires an explicit `--model` and `--region`.

Outputs:

- direct `build.py publish`: review diff report plus final build outputs under [`../docs/_build/`](../docs/_build) by default, or under `<staging-root>/docs/_build/` when staging is enabled
- queue-driven Publish: staged DOCX/PDF/Markdown under [`../reports/releases/<model>/<region>/<lang>/versions/<version>/`](../reports/releases), with Markdown sidecars such as `assets/`, `conf.py`, and `index.md` preserved when present, plus latest publish HTML under [`../reports/releases/<model>/<region>/<lang>/latest/html/`](../reports/releases)
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
[`dev/idml_module_map.md`](dev/idml_module_map.md).

The approved contract freezes these identities:

| Contract item | Approved value |
| --- | --- |
| Target | `JE-1000F / US / en+fr+es` |
| Reference PDF | `Jackery Explorer 1000 User Manual V2.0-2026-06-05.pdf` |
| Reference SHA-256 | `e72b1ba01882062e261b17d5ba54a2f7c3099e5ba531a6428be13888641083f2` |
| Page contract | 58 pages, `368.787 × 524.692 pt`, tolerance `0.02 pt` |
| Print contract | PDF/X-4, Output Intent `Japan Color 2001 Coated`, Output Condition `JC200103` |
| Manual content SHA-256 | `e38dad9c6e8d47ea2e1a3c5fe724786d22489861832beebd42cb5a4d953318b3` |
| Snapshot SHA-256 | `a3e77b847bdf372665b25a15bf441455fc5e4def5c3dd58ba3aa852b61e11203` |
| Style-contract SHA-256 | `83411e87ec9bbb45085fae5fbd9a590cef3f1acd776e568db807b78cfac57df6` |
| Layout-params SHA-256 | `4927215c0aca45ce6294dc75ef43628f1d02979add3141f6a3d90bda267685b9` |

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
missing plan, any of the bound source/hash identities drifting, incomplete
52-source coverage, non-monotonic/out-of-bounds composition pages, or a final
page-count/geometry mismatch stops the build. It must never partially use this
plan and then silently fall back to the fuzzy PDF mapper.

Build from the frozen review and phase2 snapshot:

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

The production gate also rejects skipped raw content. Fixed composite pages
use explicit component frames, while ordinary operation, UPS/charging,
storage, and troubleshooting content flows through linked story chains. The
operation-panel renderer keeps the illustration at the bottom of its group,
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
three-column, four-combination source shape. Button and clock assets plus grid
underlays are linked/drawn first; localized headers, button captions, plus
signs, durations, operations, and functions are separate top-layer frames.
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
To match the approved JE-1000F/US/en reference without changing the frozen
source/IR hash, this exact composition normalizes only the visible reference
labels `POWER Button` to `Main Power Button` and `DC / USB` to `DC/USB`.
Those normalized strings remain unlocked top-layer text frames; this is a
target-scoped reference-layout contract, not a general content rewrite.
`p34_12_app_setup_placeholder` and `p50_12_app_setup_placeholder` retain their
localized copy and labels but use the same approved page split and component
geometry. Every graphic, shape, and leader extension is emitted before the
unlocked text frames.

Source-authored TOC folios and back-cover copy come from the IR; InDesign must
not recompute or hardcode them. Content, translation, specification, legal,
table-structure, or asset-identity defects are corrected in the
Feishu/source-table/template/review/TM or asset-governance layer and then
rebuilt. The narrow approved App reference-label normalization above changes
presentation only and does not authorize other renderer-side copy edits. INDD
is never a second content source.

Review bundles may retain an older opaque attachment hash after a live snapshot
refresh. The build resolves a unique current file by stable semantic identity,
stages it under the frozen basename, and rejects missing or ambiguous matches;
it does not silently emit a broken InDesign link. Rounded native tables remain
editable: a rounded background and a square table frame are grouped, and only
cell text receives the shared one-character inset. The finalizer fits LCD and
Meaning of Symbols shells to their composed native row heights. The 26-row LCD
table stays at 7 rows plus 19 rows per language with a 5.6 mm maximum icon box.
WARNING, CAUTION, NOTE, and TIP labels remain source-owned and are emitted
verbatim; a missing label stops export.

`idml` defaults to the production exporter. The separate design-template flow
mode writes semantic Markdown, a continuous-story editable IDML, a style map,
and trace files under `docs/_build/<model>/<region>/<lang>/idml/flow/`:

```bash
python3 build.py idml --model JE-1000F --region US --idml-mode flow
python3 build.py idml --model JE-1000F --region US --idml-mode both
```

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
- zero overset stories, zero missing fonts, and zero bad links;
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

On the publish queue path (`Workflow_action = Publish`), the worker runs the
idml step with `--idml-mode both` and then packages the export into one
designer delivery zip via `tools/idml/delivery.py`:
`manual_<model>_<region>[_<lang>]_publish_<version>_handoff.zip` containing the
production and flow IDML with every `LinkResourceURI` rewritten to
`file:Links/<name>`, the linked images collected under `Links/`, the flow outputs, the handoff
reports, `source_trace.json` stamped with the queue row's real version, a
fonts manifest (plus `Document fonts/` when `AUTO_MANUAL_LOCAL_GILROY_DIR` is
provisioned on the build machine), and the versioned reference PDF. The zip is
the designer-facing package: its checklist points to the versioned root IDML,
`missing_assets_report.md` reports package-time link portability, and the
separate `source_asset_resolution_report.md` preserves unresolved semantic
source/flow diagnostics without presenting them as broken packaged links. The
zip is staged under `reports/releases/<model>/<region>/<lang>/versions/<version>/`,
uploaded to the knowledge base, and its link is written to the queue row's
`idml_file` field. The bare `.idml` is no longer uploaded: its image links are
absolute build-machine paths that die with the build worktree, so only the
packaged zip is a usable designer deliverable.

For approved reference figures, the package-time link set must include every
referenced file under `_generated/idml_reference_assets/` plus the pairing-panel
PDF, and `missing_assets_report.md` must report zero missing links. For release
acceptance, extract the final ZIP and run `indesign_finalize.py` against its
versioned root IDML. `check_idml`, ZIP integrity, or preflight of an earlier raw
IDML does not prove the delivered `Links/` package.

For queue rows with `Git_ref`, the build worktree is based on the current
`origin/main`; only the review content under `docs/_review/` is overlaid from
the row's review ref. This prevents a stale local `main` branch from silently
running an older renderer during Publish.

The default flow style map lives at
`docs/templates/idml_template/style_mapping/flow_style_map.json` and is copied
to each flow output folder as `flow_style_map.json` so design can map the story
to an InDesign template without changing production styles.

`configs/config.eu.yaml` now represents the live `EU` region-family row as `eu-merged`, routes blank-`Lang` queue rows to the merged EU manual, and keeps `sync.phase2.tables.spec_master` pinned to the live Base view that contains `JE-1000F_EU` rows. `configs/config.eu-en.yaml`, `configs/config.eu-fr.yaml`, and `configs/config.eu-es.yaml` are the explicit English, French, and Spanish single-language EU surfaces when you need one language family at a time.

Word styling note:

- `configs/config.us-en.yaml` now post-processes the generated DOCX so non-safety / non-spec pages inherit the `reference_en.docx` heading, table, and default paragraph styling

Single-page preview and fast draft:

```powershell
python build.py preview --config configs/config.us-en.yaml --model JE-1000F --region US --page 03_product_overview_placeholder
python build.py fast --config configs/config.us-en.yaml --model JE-1000F --region US
```

Standalone release traceability:

```powershell
python build.py release-manifest --config configs/config.ja.yaml --model JE-1000F --region JP
```

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

## 5.1 Capability Gate

`build.py check` validates each target against the product capability matrix:

- `data/model_capabilities.csv` — per-`Document_key` feature booleans, mirrored from the 文档构建表 checkboxes (说明书盘点 2026-07-06).
- `data/capability_page_rules.csv` — capability -> chapter mapping. `scope=page` requires/forbids a bundle page stem; `scope=section` greps a regex inside matching pages. `required_when_true` / `forbidden_when_false` toggle enforcement per direction, so uncertain rules can be recorded without failing builds.

Failure codes: `CAPABILITY_CONTENT_MISSING` (capability TRUE, chapter absent) and `CAPABILITY_CONTENT_UNEXPECTED` (capability FALSE, chapter present). Targets missing from the capabilities CSV are skipped — absence of inventory data is not a defect.

`check` also runs the language-tree parity gate (`tools/check_docs_lang_parity.py`, Milestone I1): `LANG_PARITY_FOREIGN_SHELL` (a ko/ja/zh/uk page carrying almost no target-script text — an untranslated shell), `LANG_PARITY_FOREIGN_LANG_BLOCK` (language-tagged blocks such as `**FR IMPORTANT**` or `\HBApplyLang{xx}` outside the family's languages), `LANG_PARITY_MISSING_LANG_PAGE` / `LANG_PARITY_FOREIGN_LANG_PAGE` (per-language generated page set incomplete, or a leftover page from another language line). Pre-existing findings are registered in `data/lang_parity_known_exceptions.csv` (model, region, code, page, note) so only NEW drift fails; delete a row once its content decision lands.

Every Sphinx run also feeds the **warning ratchet** (`tools/warning_ratchet.py`, Milestone I2): the warning stream is written to `<out>/sphinx-warnings.log`, sanitized (paths, line numbers, ANSI), and diffed against the committed baseline `data/known_warnings/<stream>-known-warnings.txt`. A warning in the baseline is registered debt; a warning not in it is news. Enforcement is staged: the in-build hook reports by default and fails only with `AUTO_MANUAL_WARNING_RATCHET=strict` (set `off` to silence); the standalone CLI `check` is always strict (new warning → exit 1, missing baseline → exit 2). Seed or refresh a baseline with `python tools/warning_ratchet.py update --stream sphinx-html --log <warnings.log>` and review the diff like code. Flip the default to strict once a few queue rounds have stable baselines.

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
