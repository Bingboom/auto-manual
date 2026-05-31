# Hello Auto Doc

Updated: 2026-05-25

This file replaces `Template_maintenance_and_using_guide.md`.
It documents the current build layout, maintenance rules, the review bundle layer under [`docs/_review/<model>/<region>/`](../docs/_review), and the current review-first publishing flow.
It is the current workflow and editing-surface guide.
It is not the full maintainer command reference; use [`../code-as-doc/build_doc_guide.md`](../code-as-doc/build_doc_guide.md) for command semantics.
For the current JP / US family difference boundary, use [`../code-as-doc/manual_family_guide.md`](../code-as-doc/manual_family_guide.md).
For onboarding new external Markdown manuals into templates, use [`../code-as-doc/dev/manual_template_intake_checklist.md`](../code-as-doc/dev/manual_template_intake_checklist.md).
For Codex-assisted Markdown-to-template intake, use [`../.agents/skills/markdown-rst-template-intake/SKILL.md`](../.agents/skills/markdown-rst-template-intake/SKILL.md).
For Codex-assisted TM-first manual rewrite or translation that must preserve Markdown structure, use [`../.agents/skills/manual-rewrite-with-tm/SKILL.md`](../.agents/skills/manual-rewrite-with-tm/SKILL.md).

---

## 1. Environment Setup

Before running any build, review, check, or publish command, prepare the local environment in the repository root.

### 1.1 Python Environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

The dependency install step is mandatory.
Do not skip `python -m pip install -r requirements.txt` or `python3 -m pip install -r requirements.txt` when preparing a fresh environment.

### 1.2 External Tools

- PDF export requires `xelatex`.
- Word export requires `pandoc` on macOS / Linux and on non-Word-COM paths.
- If the target uses a Word reference template such as the bundle flow, install `pandoc 3.9.0.2` or newer. The bundle exporter now auto-selects a compatible installed `pandoc` when multiple versions are present, and older versions can emit an invalid `/word/media/` content-type override that makes Microsoft Word repair the generated `.docx`.
- The Python dependencies in [`requirements.txt`](../requirements.txt) include the Sphinx theme and build libraries used by the current workflow.

If you want Gilroy only on your own machine for PDF preview, set `AUTO_MANUAL_LOCAL_GILROY_DIR` to the extracted font folder before running `pdf` or `publish`.
That folder must contain `gilroy-regular-3.otf`, `gilroy-bold-4.otf`, `Gilroy-LightItalic-12.otf`, and `Gilroy-ExtraBoldItalic-10.otf`.
If the env var is not set, or the folder is incomplete, the build keeps the normal shared fallback fonts and CI does not change.

If you only need the exact command semantics for one export path, use [`../code-as-doc/build_doc_guide.md`](../code-as-doc/build_doc_guide.md) as the authoritative reference.

GitHub note:

- pull requests are gated by the `Manual Validation` workflow
- after merge, `main` runs the same validation workflow again
- feature-branch pushes are not expected to run a second duplicate `push` validation pass
- `Manual Validation` now includes smoke checks for `diff-report` and `release-manifest` in addition to the existing validation jobs
- the shared GitHub-hosted Feishu worker setup now installs `pandoc` from the official release action instead of `apt-get`, and it reuses pip/npm download caches, so remote queue runs are less likely to spend 10+ minutes waiting on slow dependency downloads before the actual build starts
- `Manual Validation` now also runs `python tools/check_maintainability_guardrails.py` as a low-noise guard against the main orchestration and validation hotspots growing back into giant files
- `build.py check` also compares duplicated RST and raw HTML list text so renderer-specific copies cannot silently drift from the source wording
- `Review Preview Package` is the separate packaging path when you need to share rendered review HTML with design
- that workflow now runs a lighter smoke packaging pass with `--skip-word` and verifies the packaged preview files before upload

Git branch hygiene note:

- after one PR is merged or closed, start the next change with `powershell -ExecutionPolicy Bypass -File scripts/start_branch.ps1 codex/<topic>` on Windows or `./scripts/start_branch.sh codex/<topic>` on mac/Linux so the new branch comes from the latest `origin/main`
- enable the repo-managed pre-push guard with `git config core.hooksPath .githooks`
- that guard now runs through the shared [`../scripts/git_branch_guard.py`](../scripts/git_branch_guard.py) core instead of a bash-only hook, and the repo also ships [`.githooks/pre-push.cmd`](../.githooks/pre-push.cmd) plus [`.githooks/pre-push.ps1`](../.githooks/pre-push.ps1) as Windows-native companion launchers
- that guard blocks pushes from branches that do not contain the latest `origin/main`; bypass only when intentional with `git push --no-verify`
- if OpenClaw on your local machine needs to report branch state or switch to an existing branch from a Feishu chat flow, use [`../scripts/openclaw_git_guard.py`](../scripts/openclaw_git_guard.py) instead of exposing raw Git commands; it only supports `status` and safe `switch --pull`, and it refuses non-generated dirty worktrees
- if you need to keep `main` open while editing one or more review branches in parallel, use the repo worktree flow in [`../code-as-doc/dev/git_worktree_guide.md`](../code-as-doc/dev/git_worktree_guide.md); on Windows, prefer worktree paths under your current user such as `C:\Users\<you>\Documents\cms2docs\worktrees\...` instead of another user's home directory

---

## 2. Source of Truth

The manual system now has four layers, but they are used at different stages.

1. Template seed layer
   - [`docs/templates/page_us-en/*.rst`](../docs/templates/page_us-en)
   - [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)
   - [`docs/manifests/*.yaml`](../docs/manifests)
   - Responsibility: reusable page structure, headings, shared prose, and initial draft layout
   - Some templates intentionally duplicate prose across normal RST and renderer-specific branches such as `.. raw:: html` or `.. raw:: latex`; when changing wording, treat the RST list as the source wording and keep renderer-specific copies aligned

2. Data layer
   - preferred snapshot root [`data/phase2/`](../data/phase2)
   - [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv)
   - [`data/phase2/Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
   - [`data/phase2/Spec_Notes.csv`](../data/phase2/Spec_Notes.csv)
   - [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)
   - [`data/phase2/symbols_blocks.csv`](../data/phase2/symbols_blocks.csv)
   - [`data/phase2/lcd_icons_blocks.csv`](../data/phase2/lcd_icons_blocks.csv)
   - [`data/phase2/Localized_Copy.csv`](../data/phase2/Localized_Copy.csv)
   - [`data/phase2/troubleshooting_blocks.csv`](../data/phase2/troubleshooting_blocks.csv)
   - [`data/phase2/Variable_Defaults.csv`](../data/phase2/Variable_Defaults.csv)
   - [`data/phase2/Variable_Lang_Overrides.csv`](../data/phase2/Variable_Lang_Overrides.csv)
   - [`data/phase2/page_registry.csv`](../data/phase2/page_registry.csv)
   - Responsibility: model-specific parameters, spec content, symbols content, troubleshooting content, and placeholder values
   - When a valid phase2 snapshot exists, build/review/publish flows default to `data/phase2`; explicit `--data-root` still overrides that default.
   - A phase2 snapshot is valid for automatic default use only when `snapshot_manifest.json` records the complete core table set from one sync run: `spec_master`, `spec_footnotes`, `spec_notes`, `spec_titles`, `symbols_blocks`, and `troubleshooting`, plus the derived `row_key_mapping`. Partial `sync-data --table ...` refreshes are still useful for focused checks, but use explicit `--data-root` when building from them.
   - For queue-driven builds, Feishu phase2 tables remain the structured-data source of truth. `data/phase2` is the materialized snapshot refreshed before build, not the daily authoring surface.
   - For spec data authoring, edit `规格参数明细` for `Page=specifications` rows and `页面占位参数` for non-spec page placeholders. `sync-data --table spec_master` now reads those two source tables directly and writes the local `Spec_Master.csv` read model.
   - After changing either spec source table, run `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --table spec_master` for the normal snapshot refresh, or `python build.py spec-master-rebuild --config configs/config.ja.yaml --expect-spec-rows 157 --expect-placeholder-rows 222` for a focused rebuild; add `--write-back` only when the merged source data should update the legacy Feishu total table.
   - `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2` refreshes the frozen snapshot from Feishu/Lark using the local `lark-cli` login and the CLI's `base` record listing flow
   - `configs/config.eu.yaml` now represents the live `EU` region-family row as `Build_family = eu-merged`, reads `JE-1000F / EU` specs from the shared split spec source tables, and is the config that blank-`Lang` queue rows should resolve to
   - `configs/config.eu-en.yaml`, `configs/config.eu-fr.yaml`, and `configs/config.eu-es.yaml` are the explicit English, French, and Spanish EU single-language surfaces when you want one language family at a time; `configs/config.pt-br.yaml` follows the same single-language pattern for Brazil Portuguese
   - when one family must always read from one known Base view, `sync.phase2.tables.<name>` can pin `table_id` and `view_id` directly in config; those literal bindings override the corresponding `*_env` values for that table
   - `python build.py validate --config ...` now catches missing phase2 table base-token/table-id bindings and page-manifest languages that are not listed in `build.languages`
   - the LCD icons page is table-driven from `lcd_icons_blocks.csv`; `figure` attachments sync into `data/phase2/_attachments/lcd_icons/` and render as the LCD table image column, while symbols `Figure` attachments sync into `data/phase2/_attachments/symbols/` and render through `symbols_blocks.csv`; troubleshooting error-code rows render from `troubleshooting_blocks.csv`; the signal-word symbols table lives in `symbols_blocks.csv` as `block_type=signal_row`; reusable short copy such as LCD / Symbols page titles, table headers, state words, image alt text, and Product overview labels lives in `Localized_Copy.csv`; LCD `{{VARIABLE_KEY}}` placeholders resolve through `Variable_Defaults.csv`, then language-specific substitutions come from `Variable_Lang_Overrides.csv`
   - for variable defaults, keep `Model_key` as the text model selector when the Base `Model` field is a linked record; linked model fields can export as record ids and are not stable enough for build matching
   - `python build.py translation-memory --config configs/config.us.yaml --model JE-1000F --region US --query-text "USB-C 100W Port" --lang fr --table spec-master` reads the same snapshot as a compact multilingual memory lookup, which is useful when OpenClaw or a maintainer needs terminology grounded in the current Base content before translating copy
   - `python3 .agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py --query-text "Always follow these basic precautions when using this product." --source-lang en --target-lang fr --format prompt` is the higher-priority sentence-pair lookup when you already maintain a dedicated translation memory table in Feishu Base; on chat surfaces, treat it as background wording memory and answer with the translation itself instead of a narrated lookup step. The script keeps a short local cache for repeat lookups; use `--no-cache` only when you need a forced refresh.
   - `python3 .agents/skills/manual-rewrite-with-tm/scripts/rewrite_markdown_with_tm.py input.md --target-lang de --use-feishu-term-source -o output.de.md` is the batch rewrite path when a full Markdown page or manual must follow TM wording, keep headings, tables, lists, and image links stable, and preserve unmatched source text as `==...==` instead of silently paraphrasing it
   - during that refresh, `Spec_Master.csv Slot_key` is normalized back to plain tokens like `front.label` when the source table stores markdown-link wrappers
   - the sync also resolves full field names through Base field metadata, so long columns like `Row_label_footnote_refs` do not disappear when the CLI view output abbreviates them
   - when `spec_master` is refreshed from the split source tables, linked-record style footnote refs like `{"id":"rec..."}` are converted to `Footnote_id` values before `Spec_Master.csv` is written
   - when one target references a `Footnote_id` that is missing only in its own region but exists as one unambiguous sibling-region row for the same model, validation and rendering now reuse that fallback definition instead of stopping the build immediately
   - the sync does not auto-fix bad `Is_Latest` data; if a latest row is wrong, keep it wrong in the snapshot and let validation stop the build
   - `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --dry-run` is the recommended first check on a new machine; it reports missing `lark-cli` and missing `FEISHU_PHASE2_*` bindings together before any API fetch
   - on Windows, the default `sync.phase2.cli_bin: lark-cli` is resolved to the installed shim automatically, so the normal shared config still works
   - when `spec_master` is part of that refresh, the command also regenerates [`../data/phase2/row_key_mapping.csv`](../data/phase2/row_key_mapping.csv) while preserving existing manual `Row_key` and `Remark` entries when possible
   - for future app-only DingTalk provider research, [`../tools/dingtalk/spike_cli.py`](../tools/dingtalk/spike_cli.py) is the manual Phase 0 smoke helper; it gets an App-Only token by default, then lets you supply the exact DingTalk list/update/upload endpoints for the chosen product without changing the current queue runtime
   - [`../tools/dingtalk/auth.py`](../tools/dingtalk/auth.py) now wraps the verified App-Only token flow behind `DINGTALK_CLIENT_ID`, `DINGTALK_CLIENT_SECRET`, and `DINGTALK_CORP_ID`, and [`../tools/dingtalk/workspace.py`](../tools/dingtalk/workspace.py) can already extract a target docs node ID from a standard `alidocs.dingtalk.com/i/nodes/...` URL
   - [`../tools/dingtalk/alidocs_session_upload_cli.py`](../tools/dingtalk/alidocs_session_upload_cli.py) is the current manual spike for the observed DingTalk docs browser-session upload chain; it needs the current browser `a-token`, XSRF token, and cookie, then follows `uploadinfo -> OSS upload -> commit` to produce a tenant node URL
   - `python build.py process-review-start-queue --config configs/config.us.yaml --data-root .tmp/review-start/phase2` is the Start Review bridge: it reads `sync.phase2.review_init` rows where `是否进入Review` is checked and `Workflow_action` maps to `Start Review`, resolves the review target from `Document_Key` alone, uses `Build_family` / `Lang` only as optional config-routing hints, groups only the rows whose resolved config enables `build.queue_by_document_key`, syncs a fresh phase2 snapshot, always reseeds `docs/_review` from the latest `origin/main` template/data state, force-updates the review branch when it already exists, creates or reuses the PR, then writes the same `Git_ref`, `PR_url`, `Review_status=InReview`, and cleared `是否进入Review` state back to every row in that routed group
   - Start Review only starts when `Document_Key` is a non-empty `<MODEL>_<REGION>` value, `是否进入Review` is checked, and `Workflow_action` maps to `Start Review`
 - `Start Review` now means "force restart and reseed from the latest template". Existing committed `docs/_review/<model>/<region>/` content on `main` is no longer a duplicate guard, and re-checking `是否进入Review` on an `InReview` row will restart the review seed flow
 - [`../.github/workflows/feishu-start-review.yml`](../.github/workflows/feishu-start-review.yml) is the `main`-owned remote review-init worker that performs the same review-start flow from GitHub Actions after a Feishu workflow dispatch
 - `python build.py queue-query --config configs/config.us.yaml --queue-scope all --task-id "JE-1000F_US_0.3_Build Draft Package" --json` is the recommended local Phase 2 lookup before a natural-language OpenClaw action; it resolves the exact Feishu row and returns the `record_id`, `Task_id`, `Workflow_action`, `Git_ref`, `Document link`, and `构建结果`
 - `python build.py queue-resolve-action --config configs/config.us.yaml --query-text "发布 JE-1000F_US_0.3" --json` is the structured dry-run resolver for the control layer; it returns the bounded `action_name`, `resolution_status`, confirmation requirement, and matched row fields before any dispatch happens
 - for a fixed "现在库里构建了多少文档" lookup, run `python build.py queue-query --config configs/config.us.yaml --queue-scope document-link --result-contains success --limit 200 --json` and the same command with `configs/config.ja.yaml`, then count rows whose `normalized_workflow_action` is `draft` or `publish`; natural-language asks such as `当前所有已构建文档链接` now resolve to the same successful `Document_link` surface with a larger default limit
 - inside this repo, the OpenClaw-backed assistant is named **BlockClaw** because it works with content blocks; treat it as the default document-build operator that helps you build, review, publish, inspect queue rows, and explain failures for `auto-manual`, with translation and copy work acting as supporting helpers
 - `python build.py translation-memory --config configs/config.us.yaml --model JE-1000F --region US --query-text "USB-C 100W Port" --lang fr --table spec-master` is the repo-local terminology lookup that pairs well with OpenClaw translation asks; it keeps the prompt small by returning matched multilingual rows instead of dumping raw CSV tables
 - for one-shot sentence translation, prefer `bitable-translation-memory`; for whole-page or whole-file rewrite jobs that must preserve Markdown structure or unmatched-source fallback, pair it with `manual-rewrite-with-tm`
 - [`../integrations/openclaw/feishu-im-webhook-adapter/`](../integrations/openclaw/feishu-im-webhook-adapter/) is the repo-external Feishu IM webhook adapter for this control layer; it receives Feishu text messages, calls `queue-resolve-action|queue-query|queue-execute`, and replies back into the same Feishu thread
 - the adapter reads optional local-only profile files from `.openclaw/` for private aliases, reply phrasing, and Feishu message reaction choices; keep personal memory, real chat samples, and custom wording there instead of committing them to remote
 - set `FEISHU_IM_ENABLE_MESSAGE_REACTIONS=true` only after the Feishu app has message reaction permission; reactions are best-effort, the initial received-stage reaction defaults to `Get`, and the same-thread text reply remains the reliable status surface
 - when the live desktop entrypoint is the installed OpenClaw gateway rather than the repo adapter, run [`../integrations/openclaw/scripts/patch_openclaw_feishu_received_reaction.mjs`](../integrations/openclaw/scripts/patch_openclaw_feishu_received_reaction.mjs) before `openclaw gateway` starts; it adds the native Feishu `Get` reaction directly inside the `im.message.receive_v1` handler, before agent reasoning, table lookup, or build dispatch
 - `python build.py listen-message-control --config configs/config.us.yaml` is the no-server local Feishu IM entry for the same control layer; it listens to `im.message.receive_v1` through `lark-cli` and replies in-thread without exposing a public callback URL
 - if the same machine must keep the old Feishu app for local phase2 operations, set `FEISHU_IM_LARK_CLI_HOME` before starting `listen-message-control`; that makes the new app use its own isolated `lark-cli` home instead of rewriting the default `~/.lark-cli`
 - for a long-lived ECS host, use the adapter `systemd` deployment assets under [`../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/`](../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/); the wrapper script sources the same `env.sh` you already use for manual startup
 - the same `queue-query --query-text` parser also understands `Task_id` strings such as `JE-1000F_US_0.3_Build Draft Package`, spaced asks like `帮我生成 JE-1000F US 0.3 草稿`, document-key-only review asks like `review JE-1000F_EU`, `开始 review JE-1000F us-merged`, and `为什么 JE-1000F US 0.3 构建失败`; if it can derive an exact `Task_id`, that selector takes priority
 - OpenClaw can also resolve config-scoped batch Draft asks such as `输出JE-1000F的所有欧规说明书文案`, `构建JE-1000F的所有欧规说明书文案`, `基于配置构建JE-1000F的欧规`, or the implicit-all form `构建JE-1000F的欧规说明书文案`; it maps `欧规` into a `Task_id` prefix like `JE-1000F_EU_`, keeps only `Build Draft Package` rows with `是否触发文档构建` enabled, and dispatches those rows by Feishu `record_id`. When no market is named, `构建JE-1000F说明书文案` uses the broader prefix `JE-1000F_`, so every triggered Build Draft Package row for that model is eligible across markets. Versioned market-level asks such as `构建 JE-1000F_EU_1.0 的欧规说明书文案` keep the same prefix and add `Version=1.0`, so each configured language row for that version remains eligible. The draft GitHub workflow uses row-scoped concurrency, so one batch does not cancel its own older pending rows. `最新` does not collapse these batch requests by `Document_Key`; the trigger checkbox remains the eligibility gate for each language row. `是否强制刷新数据` is still honored by the build script as the row-level refresh input.
 - exact OpenClaw Build Draft Package / Publish dispatches require the selected row's `是否触发文档构建` to be enabled; unchecked rows fail fast instead of launching a GitHub run that exits without output.
 - status-like asks such as `草稿包好了没`, `这个跑完了吗`, or `这个到哪了` resolve as status checks even when they mention draft/publish wording; pronoun follow-ups can reuse the last resolved `record_id` from the local adapter state, but build/trigger/rerun requests always resolve fresh from the current Feishu table instead of appending a remembered `record_id`
 - retry-style asks such as `补跑英语和法语`, `补构建法语`, or `重试这个` are treated as Build Draft Package intent; the adapter reuses only safe context such as model, market, version, and Git_ref, then resolves fresh queue rows instead of reusing the previous `record_id`
 - `queue-query` and `queue-resolve-action` accept `--langs en,fr` for bounded multi-language selection; natural-language asks can also use Chinese language names such as `英语`, `法语`, `西语`, `德语`, `意语`, and `日语`
 - `queue-query`, `queue-resolve-action`, and `queue-execute` accept `--fresh-since <iso-or-epoch>` so status replies can distinguish this-run writeback from older row results; Document_link JSON rows include `freshness_status`, `result_built_at`, `result_is_fresh`, and `build_started_at`
 - `queue-query --json` includes `matched_count`, `returned_count`, `limit`, and `truncated`; if a broad query hits the default limit, treat `truncated=true` as an incomplete answer and re-run with narrower filters or a higher `--limit`
 - broad latest-link asks such as `构建好的文档链接发我` return successful latest-version rows per `Document_Key`, while inventory asks such as `当前所有已构建文档链接` keep all successful rows up to the larger inventory limit
 - adapter conversation memory is never the build truth source: `这个好了没` re-reads Feishu by `record_id`, and if a remembered row has been deleted or moved, BlockClaw reports it as not found and clears that context instead of replaying the old row
 - `python build.py queue-execute --config configs/config.us.yaml --query-text "请帮我构建 JE-1000F_US_en_0.3，并返回 Build Draft Package 记录。只返回 record_id、Git_ref、构建结果、Document link。"` is the recommended deterministic execution entry for natural-language OpenClaw build asks; it resolves the Feishu row, dispatches the matching `main`-owned workflow, waits for completion, and then re-reads the Feishu row before returning the final fields plus `accepted_at`, `run_id`, `run_url`, and `freshness_status`
 - if the GitHub run finishes but the Feishu row still only has a pre-dispatch `FAILED` or `SUCCESS`, OpenClaw reports `freshness_status=stale_result` or `writeback_pending` instead of treating that old row value as the current run result
 - a local observation gap is never reported as an action failure: once GitHub accepts a dispatch, a transient `status`/poll error, a `control-layer ... fetch failed`, or a wait-deadline timeout makes `queue-execute` defer to the authoritative Feishu/Base writeback (`freshness_status`) instead of raising — it reports a failure only when the GitHub run reaches a genuine terminal failure **and** the row is still not fresh; `/manual-status` likewise returns the last known run state plus an `observation_error` line rather than erroring out, because the remote run keeps going regardless of whether the local poller could read it back
 - builds report results on an accept-first lifecycle, never by holding the chat turn open: the dispatch reply and `/manual-status` carry `state: accepted|processing|completed|failed` plus a `note:` pointing back to `status last`, so an in-flight run reads as `任务正在处理中` (not a failure). On the Feishu IM adapter a single-record build replies "已受理（处理中）" immediately, dispatches with `--no-wait`, and does **not** poll; progress is delivered **on demand** — when you re-ask "这个好了没", the adapter reads the authoritative state at that moment (a fresh Base writeback wins → `已完成`/`失败`; otherwise it reads the live GitHub run once via the remembered `run_id` → 仍在跑=`处理中`, run 已失败但未写回=`失败`, run 完成但结果未落表=`处理中`) and answers 处理中/已完成/失败. Single read per question, not polling
 - against the Feishu message control plan, the repo now has the full repo-local Phase 2 stack: query, deterministic execute, structured failure replies, explicit Publish confirmation, and a standalone Feishu IM webhook adapter are all live. Encrypted callback support and ECS deployment assets are now repo-owned; the remaining gaps are shared state and a stable named ingress rollout.
 - if you keep using `trycloudflare.com`, only the process restart becomes stable; the callback URL itself still changes after a tunnel restart. For a stable URL, switch the same adapter to a named Cloudflare Tunnel or another fixed HTTPS ingress
 - if `queue-execute` resolves `Workflow_action = Publish`, add `--confirm-publish`; otherwise it now stops before dispatch
 - repo-local OpenClaw dispatch no longer treats `adm-zip` as a required local install just to send a Build Draft Package or Publish dispatch from ECS; metadata artifact parsing is now best-effort, so missing package installs degrade status detail instead of blocking dispatch
 - when a `Start Review` worker fails before Feishu writeback, the worker now writes a structured failure summary into `openclaw-run-metadata`; OpenClaw status and `queue-execute` surface that summary directly, for example `缺少 JE-1000F_CN 的规格数据，无法进入 review。`
 - `queue-execute` treats a `Start Review` row that already has `Review_status=InReview` and `Git_ref` as completed and returns the current row without dispatching another Action; otherwise OpenClaw dispatches `start-review`, `build-draft`, and `publish` with the resolved Feishu `record_id` so the GitHub run and final writeback stay tied to that exact queue row
 - if the Start Review workflow is dispatched with one explicit `record_id` but the GitHub worker cannot re-read that row as pending from the current Feishu view, that run now emits a structured failure summary instead of ending as a silent success; if the row is already `InReview` with `Git_ref`, the duplicate dispatch is treated as an idempotent success
 - for a multi-target build (several targets at once, or one model across regions), use `queue-execute --allow-multiple` so every matching row is dispatched in **one** command call — `queue-execute` is otherwise single-row, and packing several targets into one `--query-text` fires only the first. The batch resolves all matching rows, dispatches each eligible one (`是否触发文档构建=Y`, not already completed), and returns a per-record JSON report (`matched_count` / `dispatched_count` / `skipped_count` / `error_count` + a `results` list with each `record_id`/`run_id`/`status`/`reason`). It is accept-first (no completion wait); already-built or not-triggered rows come back as `skipped` with a reason. Report only rows the command returns as `dispatched` (with a `run_id`) as actually started — never infer "已进队" from the trigger flag — and ask for a complete target name (e.g. `JE-1000F_CN_1.3`, not `JE-1000F_CN`) when a version is missing
- `python build.py process-build-queue --config configs/config.us.yaml` is the optional Feishu task-table bridge: it reads `sync.phase2.document_link` rows where `是否触发文档构建 = Y`, writes `开始构建时间` as soon as one row is picked up, resolves the matching config family from `Build_family` first and `Lang` second, groups only the rows whose resolved config enables `build.queue_by_document_key`, runs `sync-data` only when that row group has `是否强制刷新数据 = true`, builds Draft rows as `check -> word -> md`, upgrades Publish rows to `check -> diff-report -> word -> pdf -> md`, uploads the Draft DOCX or Publish PDF to the primary Feishu/wiki destination, can also sync that same primary artifact to DingTalk as an optional mirror, writes the local DOCX release path into `Document directory`, keeps `Document link` as the DOCX link for Draft and PDF link for Publish, imports the generated Markdown into `飞书云文档` when that field exists, optionally writes the mirrored DingTalk node URL into `Document link_dd`, writes a timestamped status into `构建结果`, writes the refresh result into `data_sync`, clears `是否强制刷新数据`, and flips the trigger back to `已构建` on success
   - for `build.queue_by_document_key` configs, Draft rows with a non-empty `Lang` are grouped by `Document_Key + normalized Lang`; `br` / `pt-br` normalizes to `pt-BR`, and the selected language is passed to build/check/validate/bundle/output resolution. `configs/config.pt-br.yaml` is now a single-language entrypoint, so Brazil Portuguese draft rows should use `Build_family = pt-br` with `Lang=br` or `Lang=pt-BR` instead of adding an English companion row.
   - when a row starts, `构建结果` is first written as `RUNNING | ... started_at=...`; the final writeback replaces it with `SUCCESS` or `FAILED`
   - if that `Document_link` row has a `Version`, Build Draft Package DOCX/Markdown names use `manual_<model>_<region>_<lang>_<Version>.docx|md`, while Publish queue release artifact names use `manual_<model>_<region>_<lang>_publish_<Version>.docx|pdf|md`; only the Draft DOCX or Publish PDF is uploaded back to `Document link`
- `Workflow_action = Build Draft Package` rows must carry `Git_ref`; queue builds now seed a temporary worktree from the latest `origin/main`, then overlay only `docs/_review` from that review branch, so they use the current `main` toolchain while still rendering the selected review content instead of silently falling back to `main`
  - on a local worker, if a same-named local `Git_ref` branch already exists, the queue uses that local branch directly so you can verify and upload review updates before pushing them
  - if GitHub is briefly unstable but that same `origin/<Git_ref>` or local branch is already cached on the worker, the queue will reuse the cached ref and continue building from the intended review branch
   - queue rows should now use `Workflow_action` only: `Start Review` to force restart/reseed review branches, `Build Draft Package` for review-stage rebuilds, and `Publish` for publish-stage builds; leave `Doc_phase` blank. For Start Review, `Document_Key` is enough; if the table exposes `Task_id`, use `Document_ID + "_" + Workflow_action` mainly for versioned build/publish rows.
   - if `Document_Key` is a linked Base field, OpenClaw uses `Task_id` as the stable Start Review selector and then checks `是否进入Review` plus `Workflow_action=Start Review`
   - when review-init reuses the shared `Document_link` view, the start-review worker only consumes `Workflow_action = Start Review`, while the build queue only consumes `Workflow_action = Build Draft Package` or `Workflow_action = Publish`
   - Build Draft Package outputs stay under the current repo [`../docs/_build/`](../docs/_build) tree by default; pass `--staging-root <dir>` or set `AUTO_MANUAL_STAGING_ROOT=<dir>` to isolate generated `docs/_build`, `reports/version_tracking`, and `reports/releases` under that root instead
- queue routing now uses `Build_family` as the primary selector: `us-merged`, `eu-merged`, `us-en`, `eu-en`, `us-es`, `us-fr`, `pt-br`, `jp-ja`, and `cn-zh`; `Lang` is now an optional compatibility field
- merged US/EU review-init and build-queue rows should use `Build_family = us-merged` / `eu-merged` and may leave `Lang` blank; single-language rows should use the matching single-language family such as `us-en` / `eu-en` / `us-fr` / `us-es` / `pt-br`
- config policy for `build.queue_by_document_key`: enable it for merged whole-book families that intentionally produce one shared manual across multiple languages, such as today's `us-merged`, `eu-merged`, and future `cn-merged`; keep it disabled for single-language families such as `us-en`, `eu-en`, `us-fr`, `us-es`, `pt-br`, `jp-ja`, `cn-zh`, or future `eu-de` / `eu-fr`, which should continue to run one queue row per `record_id`
   - Publish queue DOCX/PDF/Markdown outputs are staged under [`../reports/releases/<model>/<region>/<lang>/versions/<version>/`](../reports/releases), Markdown sidecars such as `assets/`, `conf.py`, and `index.md` are preserved when present, and the latest publish HTML snapshot is mirrored under [`../reports/releases/<model>/<region>/<lang>/latest/html/`](../reports/releases) for Vercel hosting; if the `Document_link` table has an `HTML_link` field, the remote publish workflow writes the deployed Vercel URL back to that field after deploy, while the unmasked raw URL is also preserved in `publish_meta.json` and `openclaw-run-metadata`
   - [`../scripts/process_build_queue.ps1`](../scripts/process_build_queue.ps1) is the Windows automation wrapper for that queue bridge; it restores the local Node/npm path plus the saved `FEISHU_PHASE2_*` user env vars, and if optional DingTalk sync is enabled it also restores `AUTO_MANUAL_ARTIFACT_SINK_PROVIDER`, `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER`, `AUTO_MANUAL_DINGTALK_SESSION_ROOT`, and `DINGTALK_DOCS_*`, then writes logs into [`../.tmp/process-build-queue/`](../.tmp/process-build-queue) and forwards extra queue args such as `--dry-run` or `--record-id`
   - [`../scripts/process_build_queue_feishu.ps1`](../scripts/process_build_queue_feishu.ps1) is the one-click Feishu-only queue entry on Windows; it fixes the primary upload target to Feishu/wiki and disables DingTalk sync
   - [`../scripts/process_build_queue_dingtalk.ps1`](../scripts/process_build_queue_dingtalk.ps1) is the one-click DingTalk sync queue entry on Windows; it keeps Feishu/wiki as primary and enables DingTalk mirror upload for the same build
   - for the full local DingTalk AliDocs setup steps, including how to capture `a-token`, `x-xsrf-token`, and the full cookie string, see [`./dingtalk_alidocs_upload_setup_guide.md`](./dingtalk_alidocs_upload_setup_guide.md)
   - `python build.py listen-build-queue --config configs/config.us.yaml` is the push-based immediate-build listener: after the Feishu app has the `drive.file.bitable_record_changed_v1` event enabled, it subscribes the table and keeps the long connection on the same current user identity, then triggers `process-build-queue` immediately when `Document_link` rows are checked in `是否立即构建`
   - [`../scripts/listen_build_queue.ps1`](../scripts/listen_build_queue.ps1) is the Windows wrapper for that listener; it restores the local Node/npm path plus the saved `FEISHU_PHASE2_*` user env vars and writes logs into [`../.tmp/build-queue-listener/`](../.tmp/build-queue-listener)
  - [`../.github/workflows/feishu-build-queue.yml`](../.github/workflows/feishu-build-queue.yml) is the `main`-owned remote-repo alternative: once it is merged into the default branch and the required GitHub Secrets are configured, GitHub Actions can poll the Feishu queue every 5 minutes with `FEISHU_PHASE2_IDENTITY=bot`, without depending on a local always-on machine
   - if you want remote immediate builds instead of waiting for the next poll, create a Feishu workflow whose combined condition is `是否触发文档构建 = Y` and `是否立即构建 = true`, then call the GitHub `workflow_dispatch` API for `feishu-build-queue.yml` on `main`; the queue still only builds rows whose trigger field is `Y`
 - that remote bot flow requires the Feishu app/bot to have read access to the phase2 source tables and write access to the `Document_link` table; otherwise it can detect pending rows but cannot write back `开始构建时间` or `构建结果`
 - if you also want the uploaded Word file to land inside wiki automatically, give that same user/bot identity edit/container permission on the destination wiki parent node; otherwise the upload still succeeds, `Document link` falls back to the latest Drive URL, and the status is marked `drive_only` with the wiki attach error
 - `python build.py md` and queue Markdown outputs reuse the Word bundle HTML path; the exporter prefers native MyST when Pandoc provides it and otherwise emits MyST-compatible CommonMark with pipe tables. Each generated `md` directory carries `conf.py`, `index.md`, and local `assets/`; RTD then uses `tools/readthedocs_source.py` to assemble the selected target directories into one catalog source under `docs/_build/rtd/`.
 - if you also want the remote GitHub Draft/Publish workers to mirror to DingTalk, configure GitHub Secrets `DINGTALK_DOCS_A_TOKEN`, `DINGTALK_DOCS_XSRF_TOKEN`, and `DINGTALK_DOCS_COOKIE`, then explicitly set the GitHub Actions repository variable `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER=dingtalk_alidocs_session`; `DINGTALK_DOCS_TARGET_NODE_URL` is optional and only acts as the remote default target
 - when DingTalk mirror sync is enabled, Feishu still remains the queue control plane and canonical writeback surface; `Document link` stays the primary returned link, and if your table also has `Document link_dd` the queue writes the mirrored DingTalk node URL there
 - when Feishu is primary and DingTalk is only the mirror, mirror target/session errors no longer abort the whole row; the queue still writes the Feishu result and records the DingTalk problem as `dingtalk_sync=failed`
 - if the row also has `是否上传钉钉`, that checkbox becomes the row-level DingTalk gate: checked rows also sync DingTalk, unchecked rows stay on the normal Feishu/wiki path for that run
 - if the table does not have `是否上传钉钉`, the worker follows the current global worker mode for that whole row
 - if that checked row also has `DingTalk_target_node_url`, the worker uploads to that row-level target first; if it is blank, the worker falls back to the global `DINGTALK_DOCS_TARGET_NODE_URL` when present
 - if the row also has `operator_union_id`, the worker can resolve a per-operator DingTalk session file from `AUTO_MANUAL_DINGTALK_SESSION_ROOT` before falling back to the global browser-session envs
 - `DingTalk_session_key` and `钉钉会话键` are accepted as aliases for `operator_union_id`; if a row uses `alice`, the worker expects `<session_root>/alice.json`
 - if a DingTalk-enabled row points at a missing per-operator session or there is no usable global DingTalk session, the queue now fails that row before build starts and writes the missing-session reason back to `构建结果`
 - `钉钉上传节点` is accepted as a compatibility alias, but prefer `DingTalk_target_node_url` for new tables
 - for OpenClaw Phase 2, keep `Document link` as the canonical artifact link field used by queue resolution and replies; `Document link_dd` is optional supplemental writeback for DingTalk and is not required by the control layer
  - that queue worker reuses `FEISHU_PHASE2_BASE_TOKEN`, additionally needs `FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID` plus `FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID`, auto-derives the current wiki destination from the same base when possible, and optionally accepts `FEISHU_PHASE2_DOCUMENT_LINK_WIKI_PARENT_TOKEN` to force a different parent wiki node
   - [`data/phase2/page_registry.csv`](../data/phase2/page_registry.csv) remains repo-maintained; `sync-data` copies it into isolated `--data-root` snapshots such as `.tmp/review-start/phase2`
   - page selection/applicability and [`data/layout_params.csv`](../data/layout_params.csv) remain repo-maintained inputs
   - Safety intro pages are maintained in [`docs/templates/page_*/safety_*.rst`](../docs/templates); the standalone user maintenance instructions page is maintained in shared templates such as [`docs/templates/page_shared/en/01_user_maintenance_instructions.rst`](../docs/templates/page_shared/en/01_user_maintenance_instructions.rst) and is included immediately before `symbols`; JP keeps the detailed safety warnings in [`docs/templates/page_jp/01_meaning_of_symbols.rst`](../docs/templates/page_jp/01_meaning_of_symbols.rst). The old `content_blocks.csv` safety source has been removed from the active repo flow
   - `Spec_Footnotes.csv` now holds only reusable spec footnote definitions; `Footnote_order` controls the rendered superscript marker order and `Footnote_id` is referenced from `Spec_Master.csv`
   - `Spec_Footnotes.csv` and `Spec_Notes.csv` both carry a `Type` field from the Feishu source; keep it explicit as `Footnote` or `Note` so downstream renderers do not infer type from the visible text
   - `Spec_Notes.csv` holds bottom-of-spec notes that are not tied to superscript references, such as trademark statements
   - `Spec_Footnotes.csv` and `Spec_Notes.csv` now match rows by `Region` + `Model`; `project_code` / `项目代码` is no longer used there either
   - when one spec page renders both bottom notes and bottom footnotes, the final output order follows [`docs/templates/spec_template.rst`](../docs/templates/spec_template.rst)
   - `Spec_Master.csv` uses `Row_label_source`, `Param_source`, and `Value_source` as the shared source-language columns; `Source_lang` stores that source-language code explicitly, for example `en`, `ja`, and `zh`, and code no longer infers it from `Region`
   - `Spec_Master.csv` now starts with `spec_row_key`; `document_key` is still the target dimension, but not the unique row key
   - `document_key` is a derived helper column and may use either `[Model]_[Region]` or `[Model]_[Region]_[Source_lang]`
   - `Line_order` is required for spec rebuilds: use `1` for one-line rows and `1`, `2`, `3`, ... for multi-line values
   - `Row_label_en`, `Param_en`, and `Value_en` are no longer supported; rename them to `*_source`
   - `Row_label_footnote_refs`, `Param_footnote_refs`, and `Value_footnote_refs` store comma-separated `Footnote_id` values; do not handwrite `①②③` into visible spec text
   - `symbols_blocks.csv` uses `Region`, `Model`, and `Source_lang` with the same naming as `Spec_Master.csv`; leave `Region` / `Model` blank when one symbols row is shared
   - `symbols_blocks.csv` uses `image_path` for the icon asset referenced by each symbols-table row; phase2 sync fills it from the Base `Figure` attachment when present
   - `symbols_blocks.csv` can also use `Is_Latest` and `Market` as row conditions: rows marked false are skipped, and `Market` must include the current build region such as `US` or `EU`
   - use `block_type=table_row` for the normal symbol/meaning grid; use `block_type=signal_row` for the top warning/caution/note/tip table, with uppercase `symbol_key` values `WARNING`, `CAUTION`, `NOTE`, and `TIPS`
   - `order` values must be unique within each symbols table section; normal symbols rows are sorted and split evenly into two columns, so `column_group` is no longer needed

3. Review working layer
   - [`docs/_review/<model>/<region>/index.rst`](../docs/_review)
   - [`docs/_review/<model>/<region>/page/*.rst`](../docs/_review)
   - [`docs/_review/<model>/<region>/generated/<model>/*.rst`](../docs/_review)
   - [`docs/_review/<model>/<region>/manifest.json`](../docs/_review)
   - [`docs/_review/<model>/<region>/overrides/**`](../docs/_review)
   - Responsibility: target-specific review editing, Git review, revision history, final release source after review starts

4. Runtime build layer
   - [`docs/_build/<model>/<region>/rst/**`](../docs/_build)
   - [`docs/_build/<model>/<region>/html/**`](../docs/_build)
   - [`docs/_build/<model>/<region>/word/**`](../docs/_build)
   - [`docs/_build/<model>/<region>/pdf/**`](../docs/_build)
   - [`docs/index.rst`](../docs/index.rst)
   - Responsibility: generated bundle plus final outputs

Rules:

- Before review starts, use template/data to create the first draft.
- To move one document into review automatically, trigger the review-init flow first; that flow creates the branch, seeds `docs/_review`, and opens the PR.
- After review starts, use [`docs/_review/...`](../docs/_review/) as the daily editing surface for that target.
- Edit templates only when the change should be shared by multiple manuals.
- For manually maintained parallel-language template pages, keep one source-language template as the structure owner and update the derived-language templates in the same change when shared headings, section order, placeholder sets, includes, or `.. only::` model gates change.
- Current example: if `charging.rst` changes in the source-language family template, keep the same battery-pack `.. only:: model_je_2000e` block boundary in the corresponding derived-language templates instead of updating only one language.
- Edit CSV when product parameters change.
- Treat [`docs/_build/...`](../docs/_build/) as generated runtime output.
- Keep region-family differences explicit where they are real: spec data, certification text, unit conventions, and `meaning_of_symbols` stay family-specific.
- When design needs to review layout or page effect, share a review handoff workspace built from `_review`, not the raw `.rst`.
- when that workspace is packaged for review sharing, let GitHub Actions build the package first and keep it as an artifact; Vercel is reserved for the latest publish HTML only
- Read the Docs is reserved for the generated public manual catalog built from [`.readthedocs.yaml`](../.readthedocs.yaml), currently indexing `JE-1000F / US`, `JE-1000F / EU`, and `JE-1000F / JP`; it does not replace review-preview packaging or the Vercel latest-publish flow
- designers should start from the workspace root, then pick a family, model, and language before opening the rendered manual or family diff page
- the workspace root now keeps the primary review actions plus a compact document-identity card with product name, manual title, model, region, and language
- the packaged preview now also includes model-scoped `downloads/<family>/<model>/<lang>/review-manual.docx`, `downloads/<family>/<model>/change-report.xlsx`, the raw diff CSV files, and `generated/workspace.json`
- families without `_review` content are hidden, so the preview only shows available families
- the packaged `changes/index.html` now opens a family hub first, and each family hub fans out to model-specific change pages
- if the target branch already has an open pull request, each new push to that PR branch will rerun `Review Preview Package` automatically when the changed files match the workflow paths
- after that workflow finishes, download the uploaded artifact when you need the packaged review workspace; it is no longer pushed to Vercel automatically
- if there is no open pull request yet, trigger `Review Preview Package` manually from the `Actions` tab

---

## 3. Current Build Pipeline

The cross-platform entrypoint is [`build.py`](../build.py).
It wraps [`tools/build_docs.py`](../tools/build_docs.py), which still drives the actual build logic.
If you need the fixed `US/en + US/es + US/fr + JP/ja` export set, use [`../scripts/build_us_jp_manuals.ps1`](../scripts/build_us_jp_manuals.ps1) as a thin wrapper over [`../scripts/build_us_jp_manuals.py`](../scripts/build_us_jp_manuals.py). For the US-only subset, use [`../scripts/build_us_manuals.ps1`](../scripts/build_us_manuals.ps1) as the compatibility wrapper.

Current flow:

1. `python build.py sync-data|process-build-queue|message-control-dry-run|rst|html|word|pdf|all|review|check|sync-review|publish|diff-report|release-manifest|handoff|preview|fast|doctor`
1. `python build.py listen-message-control --config configs/config.us.yaml`
2. [`tools/build_docs.py`](../tools/build_docs.py) validates config and layout params
3. target `model` and `region` are resolved from CLI or `build.targets`
4. `product_name` is resolved from the active snapshot root, defaulting to [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv); explicit `--data-root` still overrides the default
5. CSV-backed pages are generated by [`tools/csv_page_build.py`](../tools/csv_page_build.py)
6. [`tools/gen_index_bundle.py`](../tools/gen_index_bundle.py) materializes the runtime bundle
7. the runtime bundle is written to [`docs/_build/<model>/<region>/rst/`](../docs/_build)
8. if source mode is `auto` or `review` and a review bundle exists, review content is overlaid onto the runtime bundle
9. [`docs/index.rst`](../docs/index.rst) is refreshed to point at all existing bundle roots
10. `html`, `word`, and `pdf` outputs are built from the prepared bundle when requested
11. `python build.py review` seeds [`docs/_review/<model>/<region>/`](../docs/_review) from the runtime bundle when review starts
12. `python build.py sync-review` refreshes parameter-driven review files from the runtime bundle without replacing the whole review bundle
13. `python build.py check` runs config/layout validation, prepares the bundle, and scans for bundle issues
14. `python tools/process_docs/build_review_preview.py` packages review HTML, diff-report HTML/CSV/XLSX, and optional review Word output for design sharing
15. `python build.py diff-report` exports review diffs, defaulting to the resolved target review root
16. `python build.py release-manifest` writes release traceability JSON / CSV for one explicit target
17. `python build.py preview` materializes one exact page selector under a preview-only output root
18. `python build.py fast` materializes a runtime-only draft without export

Important:

- `python build.py rst` only materializes the RST bundle.
- `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2` is the explicit local refresh step for Feishu/Lark content; build commands default to a valid phase2 snapshot when one exists and only fetch online data when you run `sync-data`.
- `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --dry-run` is the safest readiness probe for a new machine because it checks the local CLI/env prerequisites before attempting the real sync.
- `python build.py process-build-queue --config configs/config.us.yaml` is the explicit local consume-and-build step for the Feishu `Document_link` task table; it never runs implicitly from `sync-data`, `check`, or `publish`.
- static legal/support placeholders such as `WARRANTY_EMAIL` and `LEGAL_COMPANY_NAME` are injected from `build.rst_substitutions` in the active config; keep US values in US configs and override EU / pt-BR values there instead of hardcoding region-specific names in shared templates.
- `python build.py message-control-dry-run --message "publish JE-1000F us-merged from branch feature/review-123"` is a maintainer-only Phase 0 helper for the planned Feishu message plus OpenClaw control layer; it returns structured JSON only and does not dispatch GitHub workflows or write back any Feishu fields yet.
- `python build.py listen-message-control --config configs/config.us.yaml` is the matching no-server runtime entry: it keeps one local Feishu IM long connection through `lark-cli`, supports the same bounded action set as the webhook adapter, and is the recommended path when you want one local machine to receive Feishu app messages and trigger remote GitHub Actions directly
- when you need the same machine to keep the old local Feishu app unchanged, initialize the new app under `FEISHU_IM_LARK_CLI_HOME` first and then start `listen-message-control`; that isolates the new app's `lark-cli` config from the default home used by the old app
- when the queue row carries `Git_ref`, that queue step keeps the latest `main` code/toolchain and overlays only `docs/_review` from the named review branch; queue Draft/Publish builds treat `Git_ref` as review content, not as an alternate worker/toolchain branch.
- `python build.py word`, `python build.py html`, and `python build.py pdf` all prepare the RST bundle first.
- `python build.py all` runs `html`, `word`, and `pdf` after the same prepare step.
- build actions except `fast` clean the current target output first; on Windows, close File Explorer, browser, Word, or PDF windows opened under [`docs/_build/`](../docs/_build) before rerunning, or use `--no-clean` for an in-place rebuild.
- `python scripts/local_build.py check|diff-report|release-manifest|publish ...` keeps generated verification/build outputs under `.tmp/staging/docs/_build`, `.tmp/staging/reports/version_tracking`, and `.tmp/staging/reports/releases` without making the operator remember `--staging-root`.
- `review` does not accept `--staging-root` because it seeds the real repo `docs/_review`, so it is intentionally excluded from `scripts/local_build.py`.
- `python build.py review` prepares a runtime draft from template/data, then seeds review only if review does not already exist.
- `python build.py review --refresh-review` intentionally replaces an existing review bundle from template/data.
- `python build.py sync-review` is the safe path after snapshot data changes during review.
- review builds now auto-run the same parameter sync before `check`, `html`, `word`, `pdf`, and `publish`, so parameter lines stay current without overwriting the rest of the review prose.
- when a single-language build targets a merged review branch and only `docs/_review/<model>/US/` or `docs/_review/<model>/EU/` exists, that auto sync falls back to the merged review root instead of silently skipping the refresh, then remaps the shared-family review pages onto the requested single-language page order before export.
- if you intentionally want one review page replaced from runtime, keep using `sync-review --page-file <file>`; if you need the whole review bundle replaced, use `review --refresh-review`.
- single-language US English review targets still use `docs/_review/<model>/US/en/`, Brazil Portuguese review targets use `docs/_review/<model>/pt-BR/pt-BR/`, and single-language EU review targets still use `docs/_review/<model>/EU/<lang>/`, but the merged `configs/config.us.yaml` / `configs/config.eu.yaml` queue/review flows use the shared roots `docs/_review/<model>/US/` and `docs/_review/<model>/EU/`.
- for that merged US flow, `Spec_Master.Source_lang` / `*_source` values are required, while CSV-driven non-source language columns may be blank because runtime lookup falls back to the source-language text automatically.
- for the recommended new flow, sync Feishu/Lark into [`data/phase2/`](../data/phase2) first; once a valid snapshot exists, `rst`, `check`, `diff-report`, `release-manifest`, and `publish` default to it, while explicit `--data-root` still overrides the source root.
- `python build.py check`, `word`, `html`, and `pdf` use `source=auto` by default, so they build from `_review` once review exists.
- `python build.py publish` uses review content only, then runs `check -> diff-report -> word -> pdf -> md -> release-manifest` as one formal release command.
- when `Document_link.Workflow_action = Publish` is consumed through the queue, keep `Document_link.Git_ref` pointed at the active review branch so the formal Publish PDF, the release-only DOCX, and the latest publish HTML are all built from that same branch instead of drifting back to `main`.
- `python build.py handoff` now generates a minimal handoff package under [`docs/_handoff/`](../docs): it resolves explicit baseline/current inputs, loads supported `rst/html` inputs, generates rule-based add/delete/replace records, copies referenced draft images into `draft/assets/`, and writes `draft/manual.md`, `draft/manual.docx`, optional `draft/manual.html`, `changes/change_log.csv`, `changes/change_log.xlsx`, `changes/change_summary.md`, `handoff/design_handoff.md`, and `manifest.json`. It does not yet provide final page mapping or advanced semantic change classification.
- `.\scripts\build_us_jp_manuals.ps1 --model <MODEL> --formats html,word,pdf` is the one-command wrapper for the fixed four-language export pack.
- `.\scripts\build_us_jp_manuals.ps1 --model <MODEL> --build-action validate --languages en,fr` runs one explicit `build.py` action across the selected matrix targets instead of deriving actions from `--formats`.
- `.\scripts\build_us_jp_manuals.ps1 --model <MODEL> --formats html --open-html` builds the selected HTML set and opens the generated HTML entry pages.
- `.\scripts\build_us_manuals.ps1 -Action check -Model <MODEL> -Languages en,es -DryRun` is the US-only compatibility wrapper over the same matrix runner and now requires an explicit `-Model`.
- `check` now catches stale foreign model names, unresolved placeholders, missing assets, and contract-required spec keys / page-value selectors / assets.
- review overrides only overlay `overrides/_assets/**`, `overrides/_static/**`, and `overrides/renderers/**` into the runtime bundle.

---

## 4. Materialized Bundle Layout

For a target such as `JE-1000F / US`, the working bundle now lives here:

- [`docs/_build/JE-1000F/US/rst/index.rst`](../docs/_build/JE-1000F/US/rst/index.rst)
- [`docs/_build/JE-1000F/US/rst/page/*.rst`](../docs/_build/JE-1000F/US/rst/page)
- [`docs/_build/JE-1000F/US/rst/generated/JE-1000F/*.rst`](../docs/_build/JE-1000F/US/rst/generated/JE-1000F)
- [`docs/_build/JE-1000F/US/rst/conf.py`](../docs/_build/JE-1000F/US/rst/conf.py)
- [`docs/_build/JE-1000F/US/rst/conf_base.py`](../docs/_build/JE-1000F/US/rst/conf_base.py)
- [`docs/_build/JE-1000F/US/rst/_static/**`](../docs/_build/JE-1000F/US/rst/_static)
- [`docs/_build/JE-1000F/US/rst/renderers/**`](../docs/_build/JE-1000F/US/rst/renderers)

This is the generated bundle consumed by Sphinx, HTML export, Word export, and PDF export.
It is not the editing surface. After review starts, `_review/...` is overlaid onto this bundle before publish.

---

## 5. Git Tracking Rule for Review Bundles

The current repo allows two Git-visible surfaces:

- [`docs/_build/**/**/rst/**`](../docs/_build) is no longer ignored
- [`docs/_review/**`](../docs/_review) is emitted as a review-first snapshot
- sibling outputs such as [`docs/_build/**/**/html/**`](../docs/_build), `word/**`, and `pdf/**` remain build artifacts

This gives you two benefits:

1. You can commit generated review bundles per target and keep reviewable history.
2. You can export Git diffs for a single model or region as CSV and HTML reports.

What this does not change:

- `_build/.../rst/**` is still regenerated on the next build.
- `_review/.../**` is now the durable review-editing surface for that target once review starts.
- `python build.py review --refresh-review` is the only path that intentionally replaces the existing review content from template/data.

Recommended use:

1. Seed the target review bundle once with `python build.py review --config ...`
2. Edit [`docs/_review/<model>/<region>/**`](../docs/_review)
3. Build preview/final outputs with `check/html/word/pdf`
4. Commit the resulting review bundle
5. Use `python build.py diff-report ...` when you need a table-style change export

For the current maintainer branch model, pull request rules, and GitHub protection settings, use [`../code-as-doc/dev/git_branching_guide.md`](../code-as-doc/dev/git_branching_guide.md).

---

## 5. Which Files You Should Edit

Edit these when the change should be shared across products or when creating the first draft:

- [`docs/templates/page_us-en/*.rst`](../docs/templates/page_us-en)
- [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)

Parallel-language template rule:

- `docs/templates/page_us-en/*.rst` is the current source-language structure owner for manually maintained US prose templates.
- `docs/templates/page_us-es/*.rst` and `docs/templates/page_us-fr/*.rst` are derived-language counterparts and must be updated in the same round when the source-language page changes shared section structure or `.. only::` gating.
- JP currently has only `ja`, so there is no second JP derived-language template to mirror today, but any future JP derived-language page should follow the same rule.
- before adding a new Markdown manual into the template library, fill out [`../code-as-doc/dev/manual_template_intake_checklist.md`](../code-as-doc/dev/manual_template_intake_checklist.md) so section mapping and placeholder rules are decided before page edits start.

Edit these when safety/spec parameters change:

- [`data/phase2/symbols_blocks.csv`](../data/phase2/symbols_blocks.csv)
- [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- [`data/phase2/Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
- [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)

Edit these when a safety intro page needs copy/layout changes:

- edit [`docs/templates/page_us-en/safety_en.rst`](../docs/templates/page_us-en/safety_en.rst), [`docs/templates/page_us-fr/safety_fr.rst`](../docs/templates/page_us-fr/safety_fr.rst), or [`docs/templates/page_us-es/safety_es.rst`](../docs/templates/page_us-es/safety_es.rst) for US safety intro changes
- edit [`docs/templates/page_jp/safety_ja.rst`](../docs/templates/page_jp/safety_ja.rst) when the Japanese safety intro page needs copy or layout changes
- edit [`docs/templates/page_jp/01_meaning_of_symbols.rst`](../docs/templates/page_jp/01_meaning_of_symbols.rst) when the detailed Japanese safety warnings need changes

Edit these during target review and final polish:

- [`docs/_review/<model>/<region>/index.rst`](../docs/_review)
- [`docs/_review/<model>/<region>/page/*.rst`](../docs/_review)
- [`docs/_review/<model>/<region>/generated/<model>/*.rst`](../docs/_review)
- [`docs/_review/<model>/<region>/overrides/_assets/**`](../docs/_review)
- [`docs/_review/<model>/<region>/overrides/_static/**`](../docs/_review)
- [`docs/_review/<model>/<region>/overrides/renderers/**`](../docs/_review)

Do not use these as the primary authoring source:

- [`docs/_build/<model>/<region>/rst/page/*.rst`](../docs/_build)
- [`docs/_build/<model>/<region>/rst/generated/<model>/*.rst`](../docs/_build)
- [`docs/_build/<model>/<region>/rst/index.rst`](../docs/_build)
- [`docs/index.rst`](../docs/index.rst)

You may commit `_review/...` for review history because it is now the target editing surface after review starts.

---

## 6. How Safety and Spec Pages Work

Safety intro pages are now maintained as fixed RST templates and then materialized into the bundle.
The standalone user maintenance instructions page lives in shared templates and is included before the `symbols` page.

Primary inputs:

- [`docs/templates/page_us-en/safety_en.rst`](../docs/templates/page_us-en/safety_en.rst)
- [`docs/templates/page_us-fr/safety_fr.rst`](../docs/templates/page_us-fr/safety_fr.rst)
- [`docs/templates/page_us-es/safety_es.rst`](../docs/templates/page_us-es/safety_es.rst)
- [`docs/templates/page_shared/en/01_user_maintenance_instructions.rst`](../docs/templates/page_shared/en/01_user_maintenance_instructions.rst)
- [`docs/templates/page_jp/safety_ja.rst`](../docs/templates/page_jp/safety_ja.rst)

JP manual note:

- [`docs/manifests/manual_jp.yaml`](../docs/manifests/manual_jp.yaml) includes [`docs/templates/page_jp/safety_ja.rst`](../docs/templates/page_jp/safety_ja.rst) directly
- edit that template when the JP safety intro page must change
- the detailed JP warning content remains in [`docs/templates/page_jp/01_meaning_of_symbols.rst`](../docs/templates/page_jp/01_meaning_of_symbols.rst)
- the old `content_blocks.csv` safety source has been removed from the active repo flow

Generated bundle output:

- materialized page include: [`docs/_build/<model>/<region>/rst/page/safety_<lang>.rst`](../docs/_build)

Symbols content is generated from:

- [`data/phase2/page_registry.csv`](../data/phase2/page_registry.csv)
- [`data/phase2/symbols_blocks.csv`](../data/phase2/symbols_blocks.csv)

`symbols_blocks.csv` notes:

- use one `table_row` per symbols-table entry
- use four `signal_row` entries for the warning/caution/note/tip signal-word table; the signal token (`symbol_key`) and localized meaning text are maintained in `symbols_blocks.csv`, not duplicated in `Localized_Copy.csv`
- use `Region` and `Model` to target the same way as `Spec_Master.csv`
- use `Source_lang` for the row's source-language code, for example `en` or `ja`
- leave `Region` / `Model` blank when one row should be shared
- `image_path` stores the RST image reference path for that icon
- keep `symbol_key` stable so renderer alt text and layout metadata still resolve correctly

Troubleshooting content is generated from:

- [`data/phase2/troubleshooting_blocks.csv`](../data/phase2/troubleshooting_blocks.csv)
- [`docs/templates/**/10_troubleshooting.rst`](../docs/templates/page_shared/en/10_troubleshooting.rst)

`troubleshooting_blocks.csv` notes:

- maintain the online TROUBLESHOOTING Base table, then run `python build.py sync-data --config configs/config.us.yaml --table troubleshooting --data-root data/phase2`
- use `Region`, `Model`, and `Is_latest` to select active rows; blank placeholder records are ignored
- keep page title, intro, table headers, widths, and header-row settings in each language's `10_troubleshooting.rst`
- keep error-code rows and corrective-measure copy in the TROUBLESHOOTING Base table; the RST template exposes `{{ troubleshooting_rows_rst }}` where those rows are inserted

Spec content is generated from:

- [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- optional [`data/phase2/Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
- optional [`data/phase2/Spec_Notes.csv`](../data/phase2/Spec_Notes.csv)
- optional [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)

Generated bundle output:

- [`docs/_build/<model>/<region>/rst/generated/<model>/spec_<lang>.rst`](../docs/_build)
- materialized page include: [`docs/_build/<model>/<region>/rst/page/spec_<lang>.rst`](../docs/_build)

[`Spec_Master.csv`](../data/phase2/Spec_Master.csv) remains the build-time read model for spec sections, rows, and page-value placeholder records.
In Feishu, maintain those rows through `规格参数明细` and `页面占位参数`, then refresh the local snapshot with `sync-data --table spec_master` or a focused `spec-master-rebuild`.

---

## 7. Placeholder Rules

Core placeholders resolved from [`Spec_Master.csv`](../data/phase2/Spec_Master.csv):

- `|PRODUCT_NAME|`
- `|PRODUCT_NAME_BOLD|`
- `|PRODUCT_SHORT_NAME|`
- `|PRODUCT_SHORT_NAME_BOLD|`
- `|MODEL_NO|`

Resolution source:

- `product_name` comes from `Row_key=product_name`
- `model_no` comes from `Row_key=model_no`
- `PRODUCT_SHORT_NAME` is derived from `PRODUCT_NAME`

`Spec_Master.csv` `Page` note:

- `Page` can be a comma-separated list
- use `Product overview` for Product overview-only page-value rows such as front/side-view callouts
- use `Product overview, specifications,` when the same row is intentionally shared by both pages
- `Row_label_source`, `Param_source`, and `Value_source` should store the row's source-manual text
- `Source_lang` should store the normalized source-language code for the row, such as `en`, `ja`, or `zh`; do not expect code to infer it from `Region`
- `document_key` should be either `[Model]_[Region]` or `[Model]_[Region]_[Source_lang]`
- `Row_order` is now the explicit row order inside each `document_key + Page + Section`; `Line_order` only controls the order of multiple lines inside one logical row
- `Line_order` is required; single-line rows use `1`
- `spec_titles.csv section_order` can hold the default order for visible spec sections, but a filled `Spec_Master.csv Section_order` overrides it
- `project_code` / `项目代码` is no longer used in `Spec_Master.csv`; choose rows by `Region` + `Model`
- when a build target is passed in document-key style such as `JE-1000F_JP` or `JE-1000F-JP`, the spec lookup normalizes it back to the base model `JE-1000F` and still uses the explicit `Region`, so a `JP` target continues to read `JP` rows
- source-language rows must keep their actual source text in `Row_label_source`, `Param_source`, and `Value_source`

For page-value rows, `Row_key` now keeps only the concept itself. Human editing should happen through `Slot_key`.

Examples:

- `Row_key=main_power_button`, `Slot_key=label` -> `|MAIN_POWER_BUTTON_LABEL|`
- `Row_key=ac_input`, `Slot_key=side.spec` -> `|SIDE_AC_INPUT_SPEC|`
- `Row_key=battery_pack_name`, `Slot_key=value` -> `|BATTERY_PACK_NAME|`

Derived behavior:

- non-empty placeholders also get `..._BOLD`
- placeholders ending in `_LABEL` also get `..._LOWER`
- multi-line page-value rows produce suffixed placeholders such as `|EXAMPLE_KEY_2|`

---

## 8. Build Commands

Cross-platform entrypoint:

```powershell
python build.py doctor --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py rst
python build.py review
python build.py check
python build.py sync-review
python build.py publish
python build.py release-manifest
python build.py preview --config configs/config.us-en.yaml --model JE-1000F --region US --page 03_product_overview_placeholder
python build.py fast --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py html
python build.py word
python build.py pdf
python build.py all
```

Config scope rule:

- [`configs/config.us.yaml`](../configs/config.us.yaml): shared EN / US template-family config
- [`configs/config.us-en.yaml`](../configs/config.us-en.yaml): canonical US English single-language review / CI / explicit review-preview landing target
- [`configs/config.ja.yaml`](../configs/config.ja.yaml): shared JP template-family config
- [`configs/config.zh.yaml`](../configs/config.zh.yaml): shared CN zh template-family config using [`docs/manifests/manual_zh.yaml`](../docs/manifests/manual_zh.yaml)
- [`configs/config.eu.yaml`](../configs/config.eu.yaml): shared EU merged template-family config using [`docs/manifests/manual_eu.yaml`](../docs/manifests/manual_eu.yaml)
- [`configs/config.eu-en.yaml`](../configs/config.eu-en.yaml), [`configs/config.eu-fr.yaml`](../configs/config.eu-fr.yaml), [`configs/config.eu-es.yaml`](../configs/config.eu-es.yaml), [`configs/config.eu-de.yaml`](../configs/config.eu-de.yaml), [`configs/config.eu-it.yaml`](../configs/config.eu-it.yaml), and [`configs/config.eu-uk.yaml`](../configs/config.eu-uk.yaml): explicit EU single-language configs using [`../docs/manifests/manual_eu-en.yaml`](../docs/manifests/manual_eu-en.yaml) plus the corresponding [`../docs/manifests/manual_eu-single-*.yaml`](../docs/manifests) stacks
- [`configs/config.us-en.yaml`](../configs/config.us-en.yaml), [`configs/config.us-es.yaml`](../configs/config.us-es.yaml), [`configs/config.us-fr.yaml`](../configs/config.us-fr.yaml), and [`configs/config.pt-br.yaml`](../configs/config.pt-br.yaml) now inherit their shared single-language US defaults from [`../configs/config-bases/us-single-language-base.yaml`](../configs/config-bases/us-single-language-base.yaml); keep common single-language build defaults there and keep language-specific page order in [`../docs/manifests/manual_us-single-en.yaml`](../docs/manifests/manual_us-single-en.yaml), [`../docs/manifests/manual_us-single-es.yaml`](../docs/manifests/manual_us-single-es.yaml), [`../docs/manifests/manual_us-single-fr.yaml`](../docs/manifests/manual_us-single-fr.yaml), and [`../docs/manifests/manual_pt-br.yaml`](../docs/manifests/manual_pt-br.yaml)
- the current maintained baseline target is `JE-1000F` across these active config families, including `JE-1000F / US`, `JE-1000F / EU`, and `JE-1000F / JP`
- do not create a new config only because the model changed; pass `--model` and `--region` instead
- create a new config only when the page stack, template family, or output conventions are genuinely different

Useful target-scoped examples:

```powershell
python build.py doctor --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py rst --config configs/config.ja.yaml
python build.py review --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py review --config configs/config.us-en.yaml --model JE-1000F --region US --refresh-review
python build.py sync-review --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py publish --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py check --config configs/config.zh.yaml --model JE-2000E --region CN
python build.py rst --config configs/config.us.yaml
python build.py word --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py pdf --config configs/config.ja.yaml --model JE-2000F --region JP
```

Source mode examples:

```powershell
python build.py rst --config configs/config.ja.yaml --model JE-1000F --region JP --source runtime
python build.py word --config configs/config.ja.yaml --model JE-1000F --region JP --source review
```

Source mode meaning:

- `auto`: use `_review` if it exists, otherwise use template/data runtime draft
- `runtime`: ignore `_review` and build from template/data
- `review`: require `_review` and build from it

PR preview note:

- when a PR changes the zh manual family under `docs/templates/page_zh/`, `docs/templates/recipes/zh/`, or `docs/manifests/manual_zh.yaml`, GitHub review-preview switches the default landing target to `configs/config.zh.yaml` for `JE-2000E / CN` automatically, but the packaged workspace still includes every existing review model
- when `--region` is `US`, `JP`, or `CN`, `python tools/process_docs/build_review_preview.py` can omit `--config` and fall back to the shared family default; keep `--config configs/config.us-en.yaml` when you want the packaged workspace to open on the explicit US English single-language target by default

`publish` behavior:

- requires explicit `--model` and `--region`
- requires an existing `_review/<model>/<region>/`
- exports revision reports to [`reports/version_tracking/<model>/<region>/`](../reports/version_tracking) by default
- writes a release manifest to [`reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv`](../reports/releases)
- queue-driven `Workflow_action=Publish` additionally stages the formal DOCX, PDF, and Markdown under [`../reports/releases/<model>/<region>/<lang>/versions/<version>/`](../reports/releases), uploads the PDF URL back to `Document link`, imports Markdown into `飞书云文档` when that field exists, mirrors the newest publish HTML under [`../reports/releases/<model>/<region>/<lang>/latest/html/`](../reports/releases) for Vercel, and writes the deployed Vercel URL back to `HTML_link` when that field exists

`preview` behavior:

- requires explicit `--model`, `--region`, and `--page`
- `--page` must match one exact page selector
- writes to [`docs/_build/<model>/<region>/preview/<page>/rst/`](../docs/_build)
- does not rewrite root [`docs/index.rst`](../docs/index.rst)

RTD catalog behavior:

- RTD installs the system `pandoc` package and builds the selected public runtime Markdown targets from `configs/config.us.yaml`, `configs/config.eu.yaml`, and `configs/config.ja.yaml`
- the RTD config first materializes target-scoped `md` directories without rewriting the repo-root [`docs/index.rst`](../docs/index.rst), then assembles [`docs/_build/rtd/`](../docs/_build) as the homepage catalog and renders that source with Sphinx
- RTD is not the release authority for formal Publish outputs; queue-driven Publish and Vercel latest-publish remain the release-facing path

`fast` behavior:

- equivalent to a runtime-only `rst --prepare-only --no-clean`
- useful for template or placeholder debugging without export steps

`sync-review` behavior:

- first refreshes the runtime bundle from template/data
- then updates only data-driven review files by default
- does not replace ordinary review prose pages unless you explicitly name them with `--page-file`
- data-driven means:
  - all generated CSV pages
  - all materialized `spec_*` / `safety_*` pages
  - all template pages whose source contains placeholders such as `|PRODUCT_NAME|` or `|MAIN_POWER_BUTTON_LABEL|`
  - cover pages generated from title/product identity
- generated cover pages still feed PDF/LaTeX output, but HTML now opens directly on the first manual content section instead of a blank cover-style landing screen
- manual HTML preview also suppresses most default Furo sidebar / TOC chrome, stays in a continuous reading flow instead of browser-side fake pagination, regenerates a lightweight left outline from the manual headings, and renders generic headings, copy width, figure presentation, ordinary table spacing, and the multilingual preface notice in a restrained neutral manual-reader style while keeping dedicated component layouts such as `SPECIFICATIONS`, so the result feels like a manual reader instead of a documentation site
- review-preview workspace manual pages now reuse the same manual HTML/CSS/JS treatment as the local build, including the generated heading sidebar and the same no-top-switcher layout

Equivalent lower-level examples:

```powershell
.\.venv\Scripts\python.exe tools\build_docs.py --config configs/config.us-en.yaml --model JE-1000F --region US --prepare-only
.\.venv\Scripts\python.exe tools\build_docs.py --config configs/config.us-en.yaml --model JE-1000F --region US --formats word --no-open
```

Word styling note:

- the US English Word path now reapplies the `reference_en.docx` heading, table, and default paragraph styling after DOCX generation, while leaving the generated `safety` and `spec` pages as-is
- Word output now also normalizes image relationships to embedded media before the final DOCX post-processing step, which improves Feishu and other third-party preview compatibility for image-backed tables

---

## 9. Version Tracking and Diff Export

Because [`docs/_review/**`](../docs/_review) is now the preferred review surface, you can keep cleaner RST history per target.

Recommended everyday workflow:

1. Pick the target you want to track.
2. Seed the review bundle once for that target.
3. Commit the review bundle as a Git baseline.
4. Edit the review bundle for normal review rounds.
5. If parameters changed in CSV, run `sync-review`.
6. Rebuild preview outputs from that review bundle and commit again.
7. Run `publish` for the formal release output, or run `diff-report` separately when needed.

### 9.1 First-Time Baseline

Use this when a target has never been tracked in Git before.

Example baseline:

```powershell
python build.py review --config configs/config.us-en.yaml --model JE-1000F --region US
git add docs/_review/JE-1000F/US
git commit -m "Add JE-1000F US review baseline"
```

What this means:

- `review` prepares [`docs/_build/<model>/<region>/rst/**`](../docs/_build) from template/data
- then it seeds [`docs/_review/<model>/<region>/**`](../docs/_review)
- the commit becomes the starting point for future report comparisons

### 9.2 Daily Update Flow

After the baseline exists, the normal update loop is:

```powershell
python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py word --config configs/config.us-en.yaml --model JE-1000F --region US
git add docs/_review/JE-1000F/US
git commit -m "Update JE-1000F US manual"
```

Recommended rule:

- `_review` is now the normal authoring source after review starts
- if a round also changed shared template/data, commit those with `_review`
- use `review --refresh-review` only when intentionally reseeding from the shared seed layer
- use `sync-review` after parameter changes in [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) so review keeps up with regenerated values

### 9.3 Which `tracked-root` to Use

Use the tracked root that matches the scope you want to compare:

- one model across all tracked regions:
  [`docs/_review/JE-1000F`](../docs/_review/JE-1000F)
- one model and one region:
  [`docs/_review/JE-1000F/US`](../docs/_review/JE-1000F/US)
- temporary runtime-only comparison:
  [`docs/_build/JE-1000F`](../docs/_build/JE-1000F)

Recommended default:

- prefer `_review`
- use `_build` only for temporary debugging when you have not emitted a review bundle yet

Example report export for one model:

```powershell
python build.py diff-report --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py diff-report --config configs/config.us-en.yaml --tracked-root docs/_review/JE-1000F --from-ref HEAD~1 --to-ref HEAD
python build.py diff-report --config configs/config.us-en.yaml --tracked-root docs/_review/JE-1000F --from-ref HEAD~1 --to-ref HEAD --include-initial-adds
```

Example report export for one region:

```powershell
python build.py diff-report --config configs/config.us-en.yaml --tracked-root docs/_review/JE-1000F/US --from-ref HEAD~3 --to-ref HEAD
```

### 9.4 How to Compare Two Specific Commits

If you want to compare a baseline commit with the latest manual state:

```powershell
python build.py diff-report --config configs/config.us-en.yaml --tracked-root docs/_review/JE-1000F/US --from-ref <old_commit> --to-ref <new_commit>
```

Examples:

- compare the previous commit to the current one:
  `--from-ref HEAD~1 --to-ref HEAD`
- compare the baseline commit to current head:
  `--from-ref a1b2c3d --to-ref HEAD`
- compare two tags or branches:
  `--from-ref release/v1 --to-ref release/v2`

Default outputs:

- [`reports/version_tracking/JE-1000F/US/*_files.csv`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_files.html`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_pages.csv`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_pages.html`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_fields.csv`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_fields.html`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_index.html`](../reports/version_tracking/JE-1000F/US)
- legacy report path aliases remain available as [`reports/version_tracking/JE-1000F/US/*.csv`](../reports/version_tracking/JE-1000F/US) and `*.html`

Use `--report-dir` if you want a different output folder.

Useful option:

- `--include-initial-adds`
  The default report already hides one-time initial baseline Added rows. Use this only when you want to see the full first-import churn.

Automatic behavior:

- if the tracked subtree does not exist at `from-ref` but exists at `to-ref`, the report now shows an explicit note that this is an initial baseline and all Added rows are expected
- by default, the generated reports keep the note but suppress those initial Added rows
- if you pass `--include-initial-adds`, those initial Added rows are kept in the generated reports

### 9.5 Which Report to Open First

Open order:

1. `*_index.html`
2. `*_fields.html`
3. `*_pages.html`
4. `*_files.html`

Why:

- `index` gives the report homepage and target jump links
- `fields` is usually the most useful review view because it shows rendered value changes and source back-mapping
- `pages` is the next best rollup when you want page-level impact
- `files` is best when you need raw file churn, insertions, and deletions

What each report means:

- `files`: which tracked `.rst` files changed, plus insertions and deletions
- `pages`: page-level rollup with `fields_changed` counts
- `fields`: structured field/value changes extracted from list-tables and `Label: Value` lines
  For generated `spec_*.rst` pages, the report now also tries to fill `source_row_key`, `source_section_key`, `source_line_order`, and `source_csv_line` from [`Spec_Master.csv`](../data/phase2/Spec_Master.csv).
  For template-based pages such as `03_product_overview`, `05_operation_guide`, and `12_app_setup`, the report also tries to back-map changed field text to matching page-value rows by comparing rendered values against resolved placeholders.
  `fields.html` now includes built-in filters for `model`, `region`, `page_key`, `source_row_key`, `change_type`, plus a full-text search box.
- `index`: homepage that links `files/pages/fields` together and provides target-level jump links with filters pre-applied

### 9.6 How to Read `fields` Back-Mapping

Important columns in `*_fields.csv` and `*_fields.html`:

- `field_key`: the rendered field label found in the RST content
- `old_value` / `new_value`: the rendered before/after values
- `source_row_key`: the matched source row in [`Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- `source_section_key`: the matched source section in [`Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- `source_line_order`: the matched source line order for multiline rows
- `source_csv_line`: the original CSV line number
- when a field label itself changes, the diff now first tries to pair old/new rows through stable source back-mapping before falling back to rendered label text, so placeholder/spec renames are more likely to show up as one `M` row with both `old_value` and `new_value`

Interpretation rule:

- if `source_row_key` is filled, the report found a source row match
- if it is blank, the row is still useful as a rendered text diff, but the source mapping was not reliable enough to fill automatically

### 9.7 Typical Review Example

For a normal JE-1000F US review cycle:

```powershell
python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py check --config configs/config.eu-en.yaml --model JE-1000F --region EU
git add docs/_review/JE-1000F/US
git commit -m "Refresh JE-1000F US manual"
python build.py publish --config configs/config.us-en.yaml --model JE-1000F --region US
```

Then:

1. open [`reports/version_tracking/JE-1000F/US/*_index.html`](../reports/version_tracking/JE-1000F/US)
2. click the `JE-1000F/US` target link
3. open `fields`
4. filter `source_row_key` when you want to inspect one spec or placeholder family

### 9.8 Common Mistakes

- Comparing `_build` after a fresh clean without rebuilding the same target first
- Running `review --refresh-review` without realizing it will replace the current review bundle
- Changing parameter CSV data during review and forgetting to run `sync-review`
- Forgetting that `check/html/word/pdf` now use review content by default once review exists
- Committing only `_review` when the round also changed shared template or CSV logic
- Reading `files.html` first and missing the more useful field-level diff in `fields.html`

---

## 10. Page Contracts

The repo now supports page contract checks under:

- [`docs/templates/contracts/03_product_overview.yaml`](../docs/templates/contracts/03_product_overview.yaml)
- [`docs/templates/contracts/05_operation_guide.yaml`](../docs/templates/contracts/05_operation_guide.yaml)
- [`docs/templates/contracts/12_app_setup.yaml`](../docs/templates/contracts/12_app_setup.yaml)

Current scope:

- contracts are matched by source template path from `config.pages`
- `check` validates required placeholders, spec row keys, page-value selectors, and required assets
- current coverage includes `03_product_overview`, `05_operation_guide`, and `12_app_setup`
- the active US and JP template families can each declare their own required placeholder sets
- contracts can be scoped by `allowed_languages`, `allowed_regions`, and `allowed_models`

Current contract keys:

- `required_placeholders`
- `required_spec_keys`
- `required_page_values`
- `required_assets`
- `allowed_languages`
- `allowed_regions`
- `allowed_models`

Why this matters:

- a page can fail early when required page-value bindings are missing
- fallback values in [`conf_base.py`](../docs/conf_base.py) no longer hide missing product-specific spec data
- new model onboarding becomes easier to validate before Word/PDF export

---

## 11. Common Pitfalls

### 11.1 Editing the wrong layer

Before review starts:

- edit template/data

After review starts:

- edit [`docs/_review/<model>/<region>/**`](../docs/_review)

Never edit:

- [`docs/_build/<model>/<region>/rst/**`](../docs/_build)

Use template/data only for shared reusable changes or intentional reseeding.

### 11.2 `?` appears in output

This is usually caused by dirty page-value rows in [`Spec_Master.csv`](../data/phase2/Spec_Master.csv), not by the template structure itself.

### 11.3 Old model names survive in the new manual

This usually means one of these happened:

- a template still contains hard-coded model text
- `product_name` in [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) was not updated
- the wrong `config`, `model`, or `region` was used

`check` now reports this as `STALE_IDENTITY_LITERAL`.
If a foreign model mention is intentional, add it to `checks.allowed_foreign_identity_literals` in the config.

### 11.4 Hard-coded title in config

If `build.word_title` is fixed to an old model name, the generated Word title will stay wrong even if `PRODUCT_NAME` is correct.
Prefer a placeholder-based title such as:

```yaml
word_title: "|PRODUCT_NAME| User Manual"
```

---

## 12. Verification Checklist

After changing templates or CSV values, verify at least the following:

1. `python build.py check --config ...` succeeds
2. `python build.py doctor --config ... --model ... --region ...` reports no blocking errors for the current Word/PDF path
3. the target bundle appears under [`docs/_build/<model>/<region>/rst/`](../docs/_build)
4. the review bundle appears under [`docs/_review/<model>/<region>/`](../docs/_review)
5. generated pages contain no unresolved placeholders such as `|PRODUCT_NAME|`
6. generated pages contain no stale model names from older products
7. safety and spec still resolve from the intended source, including the JP template-backed safety page and the remaining CSV-backed generated pages
8. the expected `.docx`, `.html`, or `.pdf` file is generated when requested
9. `publish` or `release-manifest` produced a JSON / CSV record under [`reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv`](../reports/releases)

Useful checks:

```powershell
Select-String -Path docs\_build\JE-1000F\US\rst\page\*.rst -Pattern '\|[A-Z0-9_]+\|'
Select-String -Path docs\_build\JE-1000F\US\rst\page\*.rst -Pattern '\?'
git status --short -- docs/_review/JE-1000F/US
```

---

## 13. One-Sentence Rule

Templates and CSV create the first draft.
[`docs/_review/**`](../docs/_review) becomes the target editing source after review starts.
[`docs/_build/**/**/rst/**`](../docs/_build) remains the runtime publish bundle behind the final outputs.
## Start Review, Build Draft Package, Publish

- `process-build-queue` no longer runs `sync-data` unconditionally; it now refreshes phase2 only when `Document_link.是否强制刷新数据 = true`.
- `Document_link.data_sync` is the writeback field for that decision: `refreshed`, `skipped`, or `failed`.
- `sync-review` now also refreshes `generated_page` placeholder files under `page/*.rst`, so forced-refresh queue builds update the final rendered page text instead of keeping stale review placeholder content.
- `build.py check --source review` validates the rows needed to identify the target and render generated-page recipe inputs, plus footnotes referenced by those inputs, but retired `Spec_Master` rows and unreferenced `Spec_Footnotes` definitions that the review bundle does not consume no longer block Build Draft Package.
- `Workflow_action=Build Draft Package` and `Workflow_action=Publish` are now the primary queue actions.
- queue routing only looks at `Workflow_action`: use `Start Review`, `Build Draft Package`, or `Publish`, and keep `Doc_phase` blank.
- `feishu-draft-build-queue.yml` is the Build Draft Package worker on `main`; dispatch it on `main`, and let `Document_link.Git_ref` decide which review branch gets fetched and built.
- `feishu-start-review.yml` is the Start Review worker on `main`; dispatch it on `main` so review-init always uses the latest worker definition.
- `feishu-build-queue.yml` is the Publish-stage worker on `main`; dispatch it on `main`, and let `Document_link.Git_ref` decide the review-branch source when present.
- if your team uses OpenClaw as the operator entrypoint, install the repo package under [`../integrations/openclaw/auto-manual-control-layer/`](../integrations/openclaw/auto-manual-control-layer) and use `/start-review`, `/build-draft`, `/publish`, and `/manual-status` instead of hand-calling the GitHub API.
- the OpenClaw bridge does not move `build.py`, Feishu secrets, or queue writeback out of GitHub Actions. It only dispatches the existing workers on `main` and tracks them through `openclaw_dispatch_nonce` plus the `openclaw-run-metadata` artifact.
- OpenClaw dispatches `start-review`, `build-draft`, and `publish` with the resolved Feishu `record_id`; Start Review can resolve from `Document_Key` alone, while versioned build/publish rows can still use `Task_id = Document_ID + "_" + Workflow_action`. If a later `start-review` resolution lands on a row already marked `InReview` with `Git_ref`, `queue-execute` returns that completed row instead of launching another workflow.
