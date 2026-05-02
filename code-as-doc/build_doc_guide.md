# Windows Build Guide

Updated: 2026-04-27

This file is the maintainer-facing Windows and PowerShell build guide.
The current cross-platform entrypoint is [`build.py`](../build.py).
For the fixed four-language release pack, use [`../scripts/build_us_jp_manuals.ps1`](../scripts/build_us_jp_manuals.ps1) or [`../scripts/build_us_jp_manuals.py`](../scripts/build_us_jp_manuals.py). For the US-only subset, use [`../scripts/build_us_manuals.ps1`](../scripts/build_us_manuals.ps1) as the compatibility wrapper.

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
python build.py sync-data --config config.us.yaml --data-root data/phase2
python build.py rst
python build.py review
python scripts\local_build.py check
python build.py sync-review
python build.py process-review-start-queue --config config.us.yaml --data-root .tmp/review-start/phase2
python scripts\local_build.py publish --config config.ja.yaml --model JE-1000F --region JP
python scripts\local_build.py release-manifest --config config.ja.yaml --model JE-1000F --region JP
python build.py process-build-queue --config config.us.yaml
python build.py message-control-dry-run --message "publish JE-1000F us-merged from branch feature/review-123"
python build.py handoff --config config.us-en.yaml --model JE-1000F --region US --version V0.1 --baseline docs/_build/JE-1000F/US/en/rst
python build.py preview --config config.ja.yaml --model JE-1000F --region JP --page 03_product_overview_placeholder
python build.py fast --config config.ja.yaml --model JE-1000F --region JP
python build.py html
python build.py word
python build.py pdf
python build.py all
python build.py diff-report
python build.py clean
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html,word,pdf
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --build-action validate --languages en,fr
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html --open-html
.\scripts\build_us_manuals.ps1 -Action check -Model JE-1000F -Languages en,es -DryRun
```

Local PDF font override:

- for local-only Gilroy preview, set `AUTO_MANUAL_LOCAL_GILROY_DIR=<absolute-font-dir>` before `python build.py pdf ...` or `python build.py publish ...`
- the font directory must contain `gilroy-regular-3.otf`, `gilroy-bold-4.otf`, `Gilroy-LightItalic-12.otf`, and `Gilroy-ExtraBoldItalic-10.otf`
- the helper only patches the generated `_build/latex/fonts.tex` copy for that run; unset the env var to return to the shared fallback chain, and remote CI workers are unaffected

Meaning:

- `validate`: validate config and [`data/layout_params.csv`](../data/layout_params.csv)
- `sync-data`: use the local `lark-cli` login plus `sync.phase2.*` config/env bindings to write normalized CSV snapshots into [`../data/phase2/`](../data/phase2), using the CLI's `base` record listing flow under the hood
- `sync.phase2.tables.<name>` may now pin `table_id` and `view_id` directly in config; when present, those literal bindings take precedence over `table_id_env` / `view_id_env`, which is the safest way to keep one family on one known Base view
- `lcd_icons`, `symbols_blocks`, `variable_defaults`, and `variable_lang_overrides` may be synced as normal phase2 tables; the LCD icons renderer reads `lcd_icons_blocks.csv` and renders downloaded `figure` attachments from `data/phase2/_attachments/lcd_icons/`, the symbols renderer uses downloaded `Figure` attachments from `data/phase2/_attachments/symbols/` when present, and LCD variables resolve from `Variable_Defaults.csv` plus `Variable_Lang_Overrides.csv`
- if the Base keeps `Model` as a linked-record field, maintain a text `Model_key` column for variable defaults so exact model matching stays independent of Feishu record ids
- `sync-data` normalizes `Spec_Master.csv Slot_key` back to plain slot tokens when the source table stores markdown-link wrappers for page-value placeholders
- `sync-data` also resolves full field names through Base field metadata, so long headers are not dropped when `lark-cli` shortens them in record-list output
- when `spec_master` and `spec_footnotes` are synced in the same run, `sync-data` rewrites Feishu linked-record footnote refs in `Spec_Master.csv` to stable `Footnote_id` values
- when one target references a `Footnote_id` that is missing only in its own region but exists as one unambiguous sibling-region row for the same model, validation and rendering now reuse that fallback definition instead of stopping the build immediately
- `sync-data` does not repair bad `Is_Latest` flags; leave those source-table problems visible so `check` and publish validation can fail loudly
- [`../tools/dingtalk/spike_cli.py`](../tools/dingtalk/spike_cli.py) is the manual Phase 0 smoke helper for future app-only DingTalk provider research; it defaults to the official App-Only token flow and lets maintainers inject product-specific list/update/upload endpoints without changing the current queue runtime. A minimal smoke run looks like `python tools\dingtalk\spike_cli.py all --record-id <stable_row_id> --update-set smoke_checked=true --upload-file .tmp\phase0-smoke.docx`.
- [`../tools/dingtalk/auth.py`](../tools/dingtalk/auth.py) now exposes the verified App-Only token helper behind `DINGTALK_CLIENT_ID`, `DINGTALK_CLIENT_SECRET`, and `DINGTALK_CORP_ID`, and [`../tools/dingtalk/workspace.py`](../tools/dingtalk/workspace.py) can parse a target node ID from a normal DingTalk docs URL such as `https://alidocs.dingtalk.com/i/nodes/<node_id>`.
- [`../tools/dingtalk/alidocs_session_upload_cli.py`](../tools/dingtalk/alidocs_session_upload_cli.py) is the current manual spike for the observed AliDocs browser-session upload chain. It needs `DINGTALK_DOCS_A_TOKEN`, `DINGTALK_DOCS_XSRF_TOKEN`, and `DINGTALK_DOCS_COOKIE`, then follows `uploadinfo -> OSS upload -> commit` and returns a node URL for the uploaded file.
- `rst`: materialize [`docs/_build/<model>/<region>/rst/`](../docs/_build)
- `review`: seed [`docs/_review/<model>/<region>/`](../docs/_review) from runtime draft
- `check`: run validation + prepare bundle + content checks, including stale identity scan and contract validation
- `sync-review`: refresh review files affected by CSV data changes
- `process-review-start-queue`: Start Review bridge; it consumes `sync.phase2.review_init` rows where `是否进入Review` is checked and `Workflow_action` maps to `Start Review`, resolve each row from `Build_family` first and `Lang` second, group only the rows whose resolved config enables `build.queue_by_document_key`, sync the latest phase2 snapshot, always reseed `docs/_review` from the latest `origin/main` template/data state, force-update the routed review branch when it already exists, create or reuse the PR, then write back the same `Git_ref`, `PR_url`, `Review_status=InReview`, and cleared `是否进入Review` state to every pending row in that group
- `Start Review` now means "force restart and reseed from the latest template". Existing committed `docs/_review/<model>/<region>/` content on `main` is no longer a duplicate guard, and re-checking `是否进入Review` on an `InReview` row will restart the review seed flow
- `process-build-queue`: Build Draft Package / Publish bridge; it consumes `sync.phase2.document_link` rows where `是否触发文档构建 = Y`, write `开始构建时间` immediately when one row is picked up, resolve the matching config family from `Build_family` first and `Lang` second, group only the rows whose resolved config enables `build.queue_by_document_key`, refresh `data/phase2` only when `Document_link.是否强制刷新数据 = true`, keep Build Draft Package rows on DOCX upload, switch Publish rows to `check + diff-report + word + pdf`, upload the Publish PDF to the primary Feishu/wiki sink, optionally sync that same PDF to DingTalk, write the local DOCX release path into `Document directory`, write the canonical PDF link into `Document link`, optionally write the DingTalk node URL into `Document link_dd`, write a timestamped build status into `构建结果`, write the refresh result into `data_sync`, clear `是否强制刷新数据`, and flip the trigger back to `已构建` on success
- if DingTalk mirror sync is enabled and the row also has `是否上传钉钉`, that checkbox becomes the row-level gate: checked rows also sync DingTalk and write `Document link_dd`, unchecked rows stay on the normal Feishu/wiki upload path for that run
- if the table does not have `是否上传钉钉`, the worker follows the current global worker mode for that whole row
- if that checked row also has `DingTalk_target_node_url`, the worker uploads to that row-level target first; otherwise it falls back to the global `DINGTALK_DOCS_TARGET_NODE_URL`
- if the row also has `operator_union_id`, the worker can resolve a per-operator DingTalk session file before falling back to the global browser-session envs
- `DingTalk_session_key` and `閽夐拤浼氳瘽閿甡 are accepted as aliases for `operator_union_id`; if the row uses `alice`, the worker expects `<session_root>/alice.json`
- if a DingTalk-enabled row points at a missing per-operator session or there is no usable global DingTalk session, the queue now fails that row before build starts and writes the exact missing-session reason back to `鏋勫缓缁撴灉`
- `queue-query`: OpenClaw Phase 2 queue resolution helper; it reads the Feishu-bound `Review Init` / `Document_link` rows and returns the concrete `record_id`, workflow intent, `Git_ref`, `Document link`, and status fields that a natural-language control layer needs before dispatch
- `queue-resolve-action`: structured OpenClaw dry-run resolver; it turns one natural-language ask into the bounded action contract from the control-layer plan, including `action_name`, `resolution_status`, required confirmation, missing required fields, and the matched queue row
- for this repo, treat OpenClaw as the default document-build operator rather than a generic assistant: its primary job is to help run review/build/publish work, inspect queue state, explain build failures, and only secondarily help with translation or copy work that supports the manuals
- `translation-memory`: query the repo-owned `data/phase2` multilingual snapshot and return compact translation memory context for OpenClaw or human translation tasks; combine it with `sync-data` when freshness matters
- `python3 .agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py --query-text "<paragraph>" --source-lang en --target-lang fr --format prompt`: preferred live sentence-pair memory for OpenClaw translation; it reads the dedicated `Translation_Memory` base first and emits prompt-ready context. In chat replies, keep that lookup implicit, return the final translated wording first, prefer one foreground lookup over a background poll flow, and rely on the script's short local cache for repeat lookups unless you need `--no-cache`.
- `python3 .agents/skills/manual-rewrite-with-tm/scripts/rewrite_markdown_with_tm.py input.md --target-lang de --use-feishu-term-source -o output.de.md`: preferred batch rewrite path for full Markdown/manual files; it uses `bitable-translation-memory` as the live lookup layer, preserves headings, tables, and images, reuses safe TM sentence patterns for parameter-only changes, and keeps unmatched source text in `==...==` instead of free-paraphrasing
- `message-control-dry-run`: maintainer-only parser probe retained for offline control-layer debugging; it resolves one raw message into structured JSON and guardrails without dispatching workflows or editing Feishu rows
- [`../integrations/openclaw/feishu-im-webhook-adapter/`](../integrations/openclaw/feishu-im-webhook-adapter): standalone Feishu IM ingress adapter; it validates callback payloads, normalizes text messages, uses `queue-resolve-action|queue-query|queue-execute` as the repo-owned action surface, and replies back into the same Feishu thread
- `listen-message-control`: local no-server Feishu IM ingress; it opens the same `im.message.receive_v1` long connection through `lark-cli`, reuses the adapter's message handler, and replies in-thread without any public callback URL
- when that listener must coexist with an older local Feishu app, set `FEISHU_IM_LARK_CLI_HOME` so only the new app's `lark-cli` runs from the isolated home while the old app keeps the default `~/.lark-cli`
- [`../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/`](../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/): ECS deployment assets for the same adapter; use the wrapper scripts plus `systemd` unit examples when the Feishu ingress must restart automatically after reboots or crashes
- `queue-query --query-text` now accepts both exact underscore ids like `JE-1000F_US_0.3` and spaced asks like `JE-1000F US 0.3`; it also maps `开始 review JE-1000F us-merged` and failure-reason asks such as `为什么 JE-1000F US 0.3 构建失败`
- `queue-execute`: OpenClaw Phase 2 deterministic execution helper; it resolves one Feishu row from `--query-text`, dispatches the matching `main`-owned GitHub workflow through the local control-layer CLI, waits for completion, then re-reads the Feishu row and returns the final `record_id`, `Git_ref`, `构建结果`, and `Document link`. For `Start Review`, an already `InReview` row with `Git_ref` is treated as completed and returned without another dispatch.
- `python scripts/openclaw_git_guard.py status`: bounded local Git status for OpenClaw or Feishu chat flows; it returns JSON with the current branch, HEAD, and dirty-worktree summary
- `python scripts/openclaw_git_guard.py switch --branch main --pull`: bounded local Git branch switch helper for OpenClaw or Feishu chat flows; it fetches refs, refuses dirty non-generated worktrees, switches to an existing branch, and only fast-forward pulls
- the control layer is no longer at the old Phase 0 plan baseline; the repo-local Phase 2 stack is now in place, including queue resolution, deterministic execution, structured failure replies, explicit Publish confirmation, and the standalone Feishu IM ingress adapter. Encrypted callback support and ECS deployment assets are now repo-owned; the remaining work is shared state and a stable named ingress rollout.
- if the adapter runs on ECS, prefer a named Cloudflare Tunnel or your own HTTPS reverse proxy; `trycloudflare.com` is fine for smoke tests but its URL is not stable across restarts, even if the adapter itself is managed by `systemd`
- if the stable named-ingress rollout is deferred, keep the pending server checklist in [`../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/README.md`](../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/README.md): provision a Cloudflare-managed domain, create the named tunnel, write `/etc/cloudflared/config.yml`, export `CLOUDFLARED_TUNNEL_CONFIG`, enable the tunnel service, then cut Feishu over to the stable hostname
- if `queue-execute` resolves a Publish row, it now requires `--confirm-publish` before it will dispatch the `main`-owned Publish worker
- repo-local OpenClaw dispatch no longer treats `adm-zip` as a dispatch-time hard dependency; metadata artifact parsing is now best-effort so a plain ECS checkout can still dispatch and poll workflows even if the control-layer package dependencies have not been installed locally
- `process-review-start-queue` now writes a structured failure summary when the worker fails before Feishu writeback; that summary is packed into `openclaw-run-metadata`, and both `/manual-status` and `queue-execute` prefer the summary message over a generic GitHub failure
- one explicit Start Review workflow `record_id` that no longer resolves to a pending review-start row is also treated as a structured failure; if that same row is already `InReview` with `Git_ref`, the worker treats the duplicate dispatch as an idempotent success. Batch queue scans with no pending rows still stay as normal idle runs.
- the merged US `config.us.yaml` flow now emits one `docs/_build/<model>/US/word/manual_<model>_us.docx` bundle that contains `en`, `fr`, and `es` together; CSV-driven `Source_lang` / `*_source` text is required, while non-source language values may be blank because runtime lookup falls back to source-language text
- queue routing now uses `Build_family` as the primary selector: `us-merged`, `eu-merged`, `us-en`, `eu-en`, `us-es`, `us-fr`, `jp-ja`, and `cn-zh`; `Lang` is only a compatibility fallback when `Build_family` is missing
- queue rows should now use `Workflow_action` only: `Start Review` to force restart/reseed review branches, `Build Draft Package` for review-stage rebuilds, and `Publish` for publish-stage builds; leave `Doc_phase` blank
- when review-init reuses the shared `Document_link` binding, the start-review worker only consumes `Workflow_action = Start Review`, while the build queue only consumes `Workflow_action = Build Draft Package` or `Workflow_action = Publish`
- merged US/EU review-init and build-queue rows should use `Build_family = us-merged` / `eu-merged` and may leave `Lang` blank; single-language rows should use the matching single-language family such as `us-en` / `eu-en` / `us-fr` / `us-es`
- config policy for `build.queue_by_document_key`: turn it on only for merged whole-book families that intentionally build one shared manual across languages, such as today's `us-merged`, `eu-merged`, and future `cn-merged`; leave it off for single-language families such as `us-en`, `eu-en`, `us-fr`, `us-es`, `jp-ja`, `cn-zh`, or future `eu-de` / `eu-fr`, which should continue to be isolated by `record_id`
- when the queue row carries `Version`, Build Draft Package DOCX names stay version-suffixed such as `manual_je1000f_us_en_0.2.docx`, while Publish queue release artifact names become `manual_je1000f_us_en_publish_0.2.docx` and `manual_je1000f_us_en_publish_0.2.pdf`; only the PDF is uploaded back to `Document link`
- `Workflow_action = Build Draft Package` rows must carry `Git_ref`; queue builds now seed a temporary worktree from the latest `origin/main`, then overlay only `docs/_review` from that review branch, so the queue keeps the current `main` toolchain while still rendering the selected review content instead of silently falling back to `main`
- on a local worker, if a same-named local branch for `Git_ref` already exists, the queue uses that branch directly so local review edits can be built before they are pushed upstream
- if that fetch hits a transient GitHub network failure but the worker already has the same `origin/<Git_ref>` or local branch cached, the queue reuses the cached ref and keeps building from the intended review content
- direct `build.py` actions still write Build Draft Package outputs to the current repo [`../docs/_build/`](../docs/_build) tree by default
- for local verification, use [`../scripts/local_build.py`](../scripts/local_build.py), [`../scripts/local_build.ps1`](../scripts/local_build.ps1), or [`../scripts/local_build.sh`](../scripts/local_build.sh); they default `check`, `diff-report`, `release-manifest`, `publish`, and other staging-safe local actions to `.tmp/staging`
- explicit `--staging-root <dir>` or `AUTO_MANUAL_STAGING_ROOT=<dir>` still redirect generated `docs/_build`, `reports/version_tracking`, and `reports/releases` under another isolated root when needed
- Publish queue outputs are staged under [`../reports/releases/<model>/<region>/<lang>/versions/<version>/`](../reports/releases), and the latest publish HTML snapshot is mirrored under [`../reports/releases/<model>/<region>/<lang>/latest/html/`](../reports/releases) for Vercel hosting; when `Document_link.HTML_link` exists, the remote publish worker writes the deployed Vercel URL back to that field after the production deploy step
- [`../scripts/process_build_queue.ps1`](../scripts/process_build_queue.ps1): Windows automation wrapper for `process-build-queue`; it restores the local Node/npm path plus the `FEISHU_PHASE2_*` user env vars, and when optional DingTalk sync is enabled it also restores `AUTO_MANUAL_ARTIFACT_SINK_PROVIDER`, `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER`, `AUTO_MANUAL_DINGTALK_SESSION_ROOT`, and `DINGTALK_DOCS_*`, runs with `--staging-root .tmp/staging`, forwards any extra queue args such as `--dry-run` or `--record-id`, and writes run logs into [`../.tmp/process-build-queue/`](../.tmp/process-build-queue)
- [`../scripts/process_build_queue_feishu.ps1`](../scripts/process_build_queue_feishu.ps1): one-click Windows wrapper that forces Feishu/wiki-only upload before calling the shared queue wrapper
- [`../scripts/process_build_queue_dingtalk.ps1`](../scripts/process_build_queue_dingtalk.ps1): one-click Windows wrapper that keeps Feishu/wiki as primary and enables DingTalk mirror sync before calling the shared queue wrapper
- the remote GitHub Draft/Publish workers now keep `lark_drive` as primary even when the DingTalk browser-session values are present; they only enable DingTalk mirror sync when you explicitly set the GitHub Actions repository variable `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER=dingtalk_alidocs_session`
- for the full local DingTalk AliDocs configuration flow, including browser header capture and env setup, see [`../user-guide/dingtalk_alidocs_upload_setup_guide.md`](../user-guide/dingtalk_alidocs_upload_setup_guide.md)
- `listen-build-queue`: start the push-based Feishu long-connection listener, auto-subscribe the current `Document_link` base to docs events with the current user identity, keep the long connection on the same user identity, and trigger `process-build-queue` immediately when the `是否立即构建` checkbox is checked on a `Document_link` row
- `python build.py listen-message-control --config config.us.yaml`: start the local Feishu IM long-connection listener; it listens for `im.message.receive_v1`, routes the same bounded natural-language control actions as the webhook adapter, and avoids any HTTP callback server or tunnel
- `python build.py translation-memory --config config.us.yaml --model JE-1000F --region US --query-text "USB-C 100W Port" --lang fr --table spec-master`: preferred compact lookup for multilingual terminology memory before asking OpenClaw to translate or rewrite manual copy
- use `bitable-translation-memory` alone for one-shot sentence or terminology lookups, and pair it with `manual-rewrite-with-tm` when the ask is a whole section/file rewrite or an explicit TM-guided preservation job
- `node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch ...`: local OpenClaw control CLI for `start-review`, `build-draft`, and `publish`; `publish` now requires an explicit `confirm` token so the command shape is `node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch publish <record_id> confirm`
- [`../scripts/listen_build_queue.ps1`](../scripts/listen_build_queue.ps1): Windows listener wrapper for `listen-build-queue`; it restores the local Node/npm path plus the `FEISHU_PHASE2_*` user env vars, runs with `--staging-root .tmp/staging`, and writes run logs into [`../.tmp/build-queue-listener/`](../.tmp/build-queue-listener)
- [`../.github/workflows/feishu-build-queue.yml`](../.github/workflows/feishu-build-queue.yml): `main`-owned GitHub-hosted queue worker for the remote repo; it runs on a 5-minute schedule plus `workflow_dispatch`, bootstraps `lark-cli` with `FEISHU_APP_ID/FEISHU_APP_SECRET`, sets `FEISHU_PHASE2_IDENTITY=bot`, and then consumes the `Document_link` queue
- [`../.github/workflows/feishu-start-review.yml`](../.github/workflows/feishu-start-review.yml): `main`-owned GitHub-hosted review-init worker for the remote repo; it consumes the review-init table, force-reseeds `docs/_review` from the latest base branch, force-updates the review branch when needed, pushes the branch, and writes back `Git_ref` plus `PR_url`
- the GitHub-hosted Feishu workers now share [`.github/actions/feishu-common-setup/action.yml`](../.github/actions/feishu-common-setup/action.yml) and [`../scripts/validate_required_env.sh`](../scripts/validate_required_env.sh), so setup and required-env changes only have one maintained source; that shared setup now pulls Pandoc from the official release action instead of Ubuntu `apt`, and it reuses pip/npm download caches to keep startup latency stable when GitHub-hosted network fetches are slow
- for local macOS/Linux Word bundle exports that use a reference DOCX, require `pandoc 3.9.0.2` or newer; the bundle exporter now auto-selects a compatible installed `pandoc` when multiple versions are present, and older versions can emit an invalid `/word/media/` content-type override that makes Microsoft Word repair the generated `.docx`
- the review-init worker now treats `Start Review` as a force-reseed action, so committed `docs/_review/<model>/<region>/` content on the base branch no longer blocks the worker
- for remote immediate builds after merge to `main`, pair that workflow with a Feishu automation whose condition is `是否触发文档构建 = Y` and `是否立即构建 = true`, then send a GitHub `workflow_dispatch` request to `feishu-build-queue.yml` on `main`; the queue worker still treats `是否触发文档构建 = Y` as the actual build request, while `是否立即构建` only decides whether to wake the remote workflow immediately
- before enabling that remote worker, make sure the Feishu app/bot has read access to the phase2 source tables and write access to the `Document_link` table; without write permission the run can build and upload but cannot write back queue status
- if you also want the uploaded Word file to be moved into wiki automatically, give that same user/bot identity edit/container permission on the destination wiki parent node; otherwise the upload still succeeds, the worker falls back to the latest Drive URL in `Document link`, and the status is marked `drive_only` with the wiki attach error
- `publish`: run `check -> diff-report -> word -> pdf -> release-manifest` for one explicit target
- `release-manifest`: write JSON / CSV release traceability for one explicit target
- `handoff`: create a minimal explicit target design handoff package with rule-based diff outputs and traceability metadata
- `preview`: materialize one exact page selector under a preview-only output root
- `fast`: materialize a runtime draft only, with `prepare-only + no-clean`
- `html`, `word`, `pdf`: prepare RST first, then export
- `all`: export `html + word + pdf`
- `diff-report`: export Git-based revision tables, defaulting to the resolved target review root
- `clean`: remove [`docs/_build/`](../docs/_build), [`docs/_review/`](../docs/_review), old legacy output directories, and generated [`params.tex`](../docs/renderers/latex/params.tex)
- `build_us_jp_manuals.ps1`: PowerShell wrapper over the shared Python matrix runner for the fixed `US/en + US/es + US/fr + JP/ja` target set; supports either `--formats` or one explicit `--build-action`
- `build_us_manuals.ps1`: US-only compatibility wrapper over the same matrix runner; use PowerShell-style `-Action`, `-Model`, `-Languages`, and `-DryRun`, and pass `-Model` explicitly
- `--open-html`: after the batch finishes, open the generated HTML entry pages for the selected language set
- DOCX export normalizes image relationships to embedded media before the final style pass so Feishu / other third-party viewers are less likely to hide image-backed table rows in preview

Start Review, Build Draft Package, Publish:

- the queue worker no longer refreshes `data/phase2` unconditionally; `Document_link.是否强制刷新数据` now decides whether that document group pulls a fresh phase2 snapshot or reuses the current local one
- `data_sync` is the row-level writeback for that decision: `refreshed`, `skipped`, or `failed`
- queue-driven builds treat Feishu phase2 tables as the structured-data source of truth; repo `data/phase2/*.csv` files are materialized snapshots, not the authoring source
- use `process-build-queue --workflow-action build-draft-package` when a Build Draft Package row should be built from the current review tree
- review-source checks scope blocking `Spec_Master` row validation to target identity and generated-page recipe inputs, so stale or retired target rows do not block an already seeded review bundle; runtime-source checks keep strict target-row validation
- use `process-build-queue --workflow-action publish` when a Publish row should be built through `build.py publish` plus `build.py html --source review`, uploaded as PDF, and staged with DOCX kept only in `reports/releases`
- `process-build-queue --record-id <record_id>` narrows one run to one `Document_link` row
- `feishu-start-review.yml` is the Start Review worker on `main`; if Feishu triggers it, dispatch it on `main` so review-start always uses the latest workflow definition
- `feishu-build-queue.yml` is the Publish-stage worker for `main`
- `feishu-draft-build-queue.yml` is the Build Draft Package worker on `main`
- the repo now ships one OpenClaw plugin package under [`../integrations/openclaw/auto-manual-control-layer/`](../integrations/openclaw/auto-manual-control-layer); it is the supported control-layer package when you want one chat entrypoint for these three workers
- OpenClaw dispatches still call only the `main`-owned workflows; they add `openclaw_dispatch_nonce` as a correlation input and the workflows upload `openclaw-run-metadata` as a machine-readable status artifact
- rapid sibling-target `start-review` and multi-language `build-draft` bursts from OpenClaw now reuse one short-lived shared queue worker on `main`; the first dispatch wakes the worker, and near-simultaneous asks reuse that same worker instead of launching competing queue runs or blocking on the first matched record. Later `start-review` retries against rows already updated to `InReview` with `Git_ref` return the completed row instead of creating extra GitHub Actions failures.
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
- that workflow now runs `python -m ruff check build.py integrations tools tests scripts` as the minimal static gate before the heavier unit/build jobs
- that workflow now also runs `npm ci && npm test` in [`../integrations/openclaw/auto-manual-control-layer/`](../integrations/openclaw/auto-manual-control-layer) so the OpenClaw command bridge stays covered in CI
- that same workflow now also runs stable smoke paths for `build.py diff-report` and `build.py release-manifest`
- that same workflow now also runs `python tools/check_maintainability_guardrails.py` so the current hotspot wrappers and validators do not quietly grow back into giant files
- pull requests run the required merge-gating checks
- pushes to `main` run the same workflow again after merge
- feature branches no longer run a duplicate `push` validation pass in GitHub
- `Review Preview Package` is a separate artifact workflow for design sharing and does not gate merge
- `Review Preview Package` now runs a smoke packaging pass with `--skip-word` and verifies the expected packaged preview files before artifact upload

Git branch safety note:

- start a new branch with `powershell -ExecutionPolicy Bypass -File scripts/start_branch.ps1 codex/<topic>` on Windows or `./scripts/start_branch.sh codex/<topic>` on mac/Linux so the branch is created from the latest `origin/main`
- enable the repo-managed pre-push guard with `git config core.hooksPath .githooks`
- that guard now runs through the shared [`../scripts/git_branch_guard.py`](../scripts/git_branch_guard.py) core instead of a bash-only hook, with [`.githooks/pre-push.cmd`](../.githooks/pre-push.cmd) and [`.githooks/pre-push.ps1`](../.githooks/pre-push.ps1) kept as Windows-native companion launchers
- the guard blocks pushes from branches that do not contain the latest `origin/main`; use `git push --no-verify` only when the older base is intentional
- if a PR adds a new helper boundary or changes workflow ownership, update the owning docs and [`dev/orchestration_module_map.md`](./dev/orchestration_module_map.md) in the same change instead of leaving the new rule as tribal knowledge

## 2. Config Rule

Do not create one config file per model.

Current shared config families:

- [`config.us.yaml`](../config.us.yaml): shared EN / US template family
- [`config.us-en.yaml`](../config.us-en.yaml): canonical US English single-language review / CI / explicit review-preview landing target
- [`config.ja.yaml`](../config.ja.yaml): shared JP template family
- [`config.zh.yaml`](../config.zh.yaml): shared CN zh template family backed by [`docs/manifests/manual_zh.yaml`](../docs/manifests/manual_zh.yaml)
- [`config.eu.yaml`](../config.eu.yaml): shared EU merged family backed by [`docs/manifests/manual_eu.yaml`](../docs/manifests/manual_eu.yaml)
- [`config.eu-en.yaml`](../config.eu-en.yaml), [`config.eu-fr.yaml`](../config.eu-fr.yaml), [`config.eu-es.yaml`](../config.eu-es.yaml), [`config.eu-de.yaml`](../config.eu-de.yaml), [`config.eu-it.yaml`](../config.eu-it.yaml), and [`config.eu-uk.yaml`](../config.eu-uk.yaml): explicit EU single-language entrypoints backed by [`../docs/manifests/manual_eu-en.yaml`](../docs/manifests/manual_eu-en.yaml) plus the corresponding [`../docs/manifests/manual_eu-single-*.yaml`](../docs/manifests) stacks
- [`config.us-en.yaml`](../config.us-en.yaml), [`config.us-es.yaml`](../config.us-es.yaml), and [`config.us-fr.yaml`](../config.us-fr.yaml) now inherit shared single-language US defaults from [`../config-bases/us-single-language-base.yaml`](../config-bases/us-single-language-base.yaml); keep shared defaults there and keep language-specific page stacks in [`../docs/manifests/manual_us-single-en.yaml`](../docs/manifests/manual_us-single-en.yaml), [`../docs/manifests/manual_us-single-es.yaml`](../docs/manifests/manual_us-single-es.yaml), and [`../docs/manifests/manual_us-single-fr.yaml`](../docs/manifests/manual_us-single-fr.yaml)

Page-stack note:

- shared config families may resolve their page stack through `paths.page_manifest`
- keep manifest-driven page order changes under [`docs/manifests/`](../docs/manifests)

Pass target differences through:

- `--model`
- `--region`
- `build.targets`
- [`data/phase1/*.csv`](../data/phase1)

Phase2 snapshot rule:

- keep the shared config families, but use a valid [`../data/phase2/`](../data/phase2) snapshot as the default build/review/publish source when it exists
- explicit `--data-root` still overrides the default, so you can point `rst`, `check`, `diff-report`, `release-manifest`, `publish`, and `process-build-queue` at a different root when needed
- `python build.py sync-data --config config.us.yaml --data-root data/phase2` is still the explicit refresh step for the phase2 snapshot
- for the review-init worker, use an isolated snapshot root such as `.tmp/review-start/phase2`; the worker syncs fresh data there before it seeds `docs/_review`
- `python scripts/local_build.py check|diff-report|release-manifest|publish ...` keeps generated verification/build outputs under `.tmp/staging/docs/_build`, `.tmp/staging/reports/version_tracking`, and `.tmp/staging/reports/releases` without making the operator remember `--staging-root`
- `review` still writes the real repo `docs/_review` tree and does not accept `--staging-root`, so it is intentionally excluded from `local_build.py`
- [`../data/phase1/page_registry.csv`](../data/phase1/page_registry.csv), page selection/applicability, and [`../data/layout_params.csv`](../data/layout_params.csv) remain repo-maintained and are not changed by `--data-root`

Only create a new config when one of these really changes:

- page stack
- template family
- output convention
- language family
- Word reference template

## 3. Standard Windows Flow

### 3.1 Validate Environment and Config

```powershell
python build.py validate --config config.us.yaml
```

Equivalent low-level checks:

```powershell
python tools\validate_config.py --config config.us.yaml
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
python build.py sync-data --config config.us.yaml --data-root data/phase2 --dry-run
python build.py sync-data --config config.us.yaml --data-root data/phase2
python build.py process-build-queue --config config.us.yaml
python build.py message-control-dry-run --message "publish JE-1000F us-merged from branch feature/review-123"
```

That command requires:

- a working `lark-cli` binary on `PATH`
- a valid local `lark-cli` login session
- the `FEISHU_PHASE2_*` environment variables referenced by [`../config.us.yaml`](../config.us.yaml) or [`../config.ja.yaml`](../config.ja.yaml)
- `--dry-run` is the recommended machine-readiness check first; it now aggregates missing CLI and missing `FEISHU_PHASE2_*` bindings into one preflight error before any fetch
- on Windows, the default `sync.phase2.cli_bin: lark-cli` is resolved to the installed shim automatically during fetch, so you do not need a Windows-only config override
- when `spec_master` is included, the sync also refreshes [`../data/phase2/row_key_mapping.csv`](../data/phase2/row_key_mapping.csv) as the phase2 mirror of the row-label mapping table
- if you also use the Feishu `Document_link` build queue, set `FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID` and `FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID`; `process-build-queue` reuses the same `FEISHU_PHASE2_BASE_TOKEN`, auto-derives the current wiki destination from that base when possible, and optionally accepts `FEISHU_PHASE2_DOCUMENT_LINK_WIKI_PARENT_TOKEN` when you want to force a different parent wiki node
- if you want Feishu/wiki primary plus DingTalk sync, set `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER=dingtalk_alidocs_session` plus either global `DINGTALK_DOCS_A_TOKEN`, `DINGTALK_DOCS_XSRF_TOKEN`, and `DINGTALK_DOCS_COOKIE` with optional `DINGTALK_DOCS_TARGET_NODE_URL` and `DINGTALK_DOCS_BX_V`, or a per-operator session registry under `AUTO_MANUAL_DINGTALK_SESSION_ROOT`; when a row carries `operator_union_id`, the worker first looks for `<session_root>/<operator_union_id>.json` before falling back to the global envs. `DINGTALK_DOCS_TARGET_NODE_URL` is only the default target, and checked rows with `DingTalk_target_node_url` can override it or supply the target on their own
- if Feishu/wiki remains primary, DingTalk mirror setup problems now degrade to `dingtalk_sync=failed` instead of aborting the whole build; blank or placeholder `-` target values are treated as unset and fall back to the default target when one exists
- for local polling automation on Windows, schedule [`../scripts/process_build_queue.ps1`](../scripts/process_build_queue.ps1) instead of calling `python build.py process-build-queue ...` directly, so the scheduled run inherits the repo `.venv`, the local `lark-cli` shim path, and the saved `FEISHU_PHASE2_*` user env vars consistently; use [`../scripts/process_build_queue_feishu.ps1`](../scripts/process_build_queue_feishu.ps1) or [`../scripts/process_build_queue_dingtalk.ps1`](../scripts/process_build_queue_dingtalk.ps1) when you want the upload target fixed without touching env vars first
- for push-based immediate builds, add the `drive.file.bitable_record_changed_v1` event to the Feishu self-built app in Open Platform, publish the app change, then start [`../scripts/listen_build_queue.ps1`](../scripts/listen_build_queue.ps1) at login or from the Windows Startup folder; the listener will auto-subscribe the current base token on startup

### 3.2 Create a Runtime Draft

```powershell
python build.py rst --config config.ja.yaml --model JE-1000F --region JP --source runtime
```

This creates:

- [`docs/_build/JE-1000F/JP/rst/`](../docs/_build/JE-1000F/JP/rst)

Use `--source runtime` when you want a fresh draft from template + data only.

### 3.3 Enter Review

```powershell
python build.py review --config config.ja.yaml --model JE-1000F --region JP
```

This seeds:

- [`docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP)

After review starts, daily editing should happen in `_review`, not in `_build`.

### 3.4 Refresh Review After Data Changes

If you update any of these:

- [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- [`data/phase2/Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
- [`data/phase2/Spec_Notes.csv`](../data/phase2/Spec_Notes.csv)
- [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)
- [`data/phase2/symbols_blocks.csv`](../data/phase2/symbols_blocks.csv)

Safety page note:

- US safety intro pages are maintained directly in [`docs/templates/page_us-en/safety_en.rst`](../docs/templates/page_us-en/safety_en.rst), [`docs/templates/page_us-fr/safety_fr.rst`](../docs/templates/page_us-fr/safety_fr.rst), and [`docs/templates/page_us-es/safety_es.rst`](../docs/templates/page_us-es/safety_es.rst)
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
- `Region` and `Model` now match the target-selection field names used by [`Spec_Master.csv`](../data/phase1/Spec_Master.csv)
- `Source_lang` stores the row's source-language code, using the same naming rule as [`Spec_Master.csv`](../data/phase1/Spec_Master.csv)
- leave `Region` / `Model` blank when one symbols row is shared across manuals
- `sku_scope` is no longer used in [`symbols_blocks.csv`](../data/phase1/symbols_blocks.csv)

`Spec_Master.csv` note:

- the `Page` column may now hold a comma-separated page list
- use `Product overview` for Product overview-only page-value rows
- use `Product overview, specifications,` when a row is intentionally shared by both pages
- `Row_label_source`, `Param_source`, and `Value_source` are the shared source-text columns; they should hold the row's source-manual text
- `Source_lang` stores that source-language code explicitly; use values such as `en`, `ja`, and `zh`, and do not rely on `Region` to infer it
- `document_key` is a derived helper column and may use either `[Model]_[Region]` or `[Model]_[Region]_[Source_lang]`
- `Row_order` is now the explicit row order inside each `document_key + Page + Section`, while `Line_order` controls the line order inside one logical row
- `spec_titles.csv section_order` can hold the default order for visible spec sections, but a filled `Spec_Master.csv Section_order` overrides it
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
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP
```

By default this updates data-driven files in the review bundle without resetting the entire review text.

That same parameter-only sync now also runs automatically before `check`, `html`, `word`, `pdf`, and `publish` when the target already builds from review.
Placeholder-backed RST pages keep manual review prose, while parameter-driven lines are refreshed from runtime.
That sync now also refreshes `generated_page` placeholder files under `page/*.rst`, so final review builds do not keep stale placeholder text after runtime/generated data changes.
When a single-language build points at a merged review branch and only `docs/_review/<model>/US/` or `docs/_review/<model>/EU/` exists, that automatic sync falls back to the merged review root instead of skipping the refresh, then remaps shared-family review pages onto the requested single-language page layout.
For the single-language US English config, the canonical review root is `docs/_review/<model>/US/en/`; for the single-language EU configs, the canonical review roots remain `docs/_review/<model>/EU/<lang>/`. Do not use or recreate the old shared single-language `docs/_review/<model>/<region>/page/**` layout. For the merged `config.us.yaml` / `config.eu.yaml` queue/review flows, the canonical shared review roots are `docs/_review/<model>/US/` and `docs/_review/<model>/EU/`.

Useful variants:

```powershell
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP --sync-scope generated
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP --page-file 02_whats_in_the_box.rst
```

### 3.5 Build from Review

Once `_review` exists, these commands use review content by default because `--source auto` overlays review on top of the runtime bundle:

```powershell
python build.py check --config config.ja.yaml --model JE-1000F --region JP
python build.py html --config config.ja.yaml --model JE-1000F --region JP
python build.py word --config config.ja.yaml --model JE-1000F --region JP
python build.py pdf --config config.ja.yaml --model JE-1000F --region JP
python build.py all --config config.zh.yaml --model JE-2000E --region CN
```

`check` now also catches stale foreign model names and contract-required spec keys, required page-value selectors, and assets.

PR review-preview note:

- when a PR changes the zh manual family under `docs/templates/page_zh/`, `docs/templates/recipes/zh/`, or `docs/manifests/manual_zh.yaml`, the review-preview workflow switches the default landing target to `config.zh.yaml --model JE-2000E --region CN --source runtime`, but the packaged workspace still includes every existing review model

### 3.6 Package a Review Preview for Design

Use this when design needs the rendered review HTML plus the current family-level diff package:

```powershell
python tools/process_docs/build_review_preview.py --config config.us-en.yaml --model JE-1000F --region US --source review --from-ref HEAD~1 --to-ref HEAD --all-review-models
```

Config note:

- omit `--config` when `--region` is `US`, `JP`, or `CN` and you want the shared family default config
- keep `--config config.us-en.yaml` when you want the packaged workspace to open on the explicit US English single-language target by default

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

- [`.readthedocs.yaml`](../.readthedocs.yaml) is the minimal RTD path for one stable public runtime HTML target: `config.us-en.yaml --model JE-1000F --region US --source runtime`
- RTD uses `python build.py rst --config config.us-en.yaml --model JE-1000F --region US --source runtime --no-clean --skip-root-index`, then renders the generated bundle at [`../docs/_build/JE-1000F/US/en/rst/`](../docs/_build) with `python -m sphinx -b html`
- do not point RTD at the repo-root [`../docs/`](../docs) tree for this flow; the root `index.rst` is a wrapper include, while RTD should render the generated bundle directory directly
- RTD does not publish `_review`, queue-driven Publish HTML, or Word / PDF artifacts; keep Vercel and release outputs as the formal publish path

### 3.7 Publish a Final Word Release

```powershell
python build.py publish --config config.ja.yaml --model JE-1000F --region JP
```

This is the formal release command.
It requires an explicit `--model` and `--region`.

Outputs:

- direct `build.py publish`: review diff report plus final build outputs under [`../docs/_build/`](../docs/_build) by default, or under `<staging-root>/docs/_build/` when staging is enabled
- queue-driven Publish: staged DOCX under [`../reports/releases/<model>/<region>/<lang>/versions/<version>/`](../reports/releases) plus latest publish HTML under [`../reports/releases/<model>/<region>/<lang>/latest/html/`](../reports/releases)
- release manifest: [`reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv`](../reports/releases) by default, or `<staging-root>/reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv` when staging is enabled

## 4. Output Layout

Runtime outputs:

- default: [`docs/_build/<model>/<region>/rst/`](../docs/_build), [`docs/_build/<model>/<region>/preview/<page>/rst/`](../docs/_build), [`docs/_build/<model>/<region>/html/`](../docs/_build), [`docs/_build/<model>/<region>/word/`](../docs/_build), [`docs/_build/<model>/<region>/pdf/`](../docs/_build)
- staged verification/local queue runs: `<staging-root>/docs/_build/<model>/<region>/...`

HTML output starts at the first manual content section. Generated cover pages are preserved for PDF/LaTeX output, not rendered as a standalone HTML home screen.
In manual preview mode, the HTML view also suppresses most Furo navigation chrome, stays in a continuous reading flow instead of browser-side fake pagination, regenerates a lightweight left outline from manual headings, and applies a restrained neutral manual-reader treatment to generic headings, copy width, figures, ordinary docutils tables, and the multilingual preface notice while preserving dedicated component layouts such as `SPECIFICATIONS`.
For review-preview workspace packaging, the manual pages now reuse the same manual HTML/CSS/JS treatment as the local build, including the generated heading sidebar and the same no-top-switcher layout.

Review working bundle:

- [`docs/_review/<model>/<region>/`](../docs/_review)

Review handoff workspace:

- [`../site/review-preview/dist/`](../site/review-preview/dist)

Latest publish HTML site:

- [`../site/publish-latest/dist/`](../site/publish-latest/dist)

Read the Docs bundle source for the current minimal public build:

- [`../docs/_build/JE-1000F/US/en/rst/`](../docs/_build)

Revision reports:

- default: [`reports/version_tracking/<model>/<region>/`](../reports/version_tracking)
- staged verification/local queue runs: `<staging-root>/reports/version_tracking/<model>/<region>/`

Release manifests:

- default: [`reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv`](../reports/releases)
- staged verification/local queue runs: `<staging-root>/reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv`

## 5. Typical Commands

Build all targets defined in one config:

```powershell
python build.py rst --config config.us.yaml
python build.py word --config config.us.yaml
python build.py all --config config.ja.yaml
```

Build one explicit target:

```powershell
python build.py word --config config.us-en.yaml --model JE-1000F --region US
python build.py word --config config.eu-en.yaml --model JE-1000F --region EU
python build.py pdf --config config.ja.yaml --model JE-1000F --region JP
```

`config.eu.yaml` now represents the live `EU` region-family row as `eu-merged`, routes blank-`Lang` queue rows to the merged EU manual, and keeps `sync.phase2.tables.spec_master` pinned to the live Base view that contains `JE-1000F_EU` rows. `config.eu-en.yaml`, `config.eu-fr.yaml`, and `config.eu-es.yaml` are the explicit English, French, and Spanish single-language EU surfaces when you need one language family at a time.

Word styling note:

- `config.us-en.yaml` now post-processes the generated DOCX so non-safety / non-spec pages inherit the `reference_en.docx` heading, table, and default paragraph styling

Single-page preview and fast draft:

```powershell
python build.py preview --config config.us-en.yaml --model JE-1000F --region US --page 03_product_overview_placeholder
python build.py fast --config config.us-en.yaml --model JE-1000F --region US
```

Standalone release traceability:

```powershell
python build.py release-manifest --config config.ja.yaml --model JE-1000F --region JP
```

Keep existing build artifacts:

```powershell
python build.py html --config config.us.yaml --no-clean
```

Open generated artifacts if the backend supports it:

```powershell
python build.py pdf --config config.us.yaml --open
```

Override PDF backend:

```powershell
python build.py pdf --config config.us.yaml --pdf-mode latex
python build.py pdf --config config.us.yaml --pdf-mode word
```

## 6. Diff Report

Typical usage:

```powershell
python build.py diff-report --config config.ja.yaml --model JE-1000F --region JP
python build.py diff-report --config config.ja.yaml --model JE-1000F --region JP --from-ref HEAD~1 --to-ref HEAD
python build.py diff-report --config config.ja.yaml --tracked-root docs/_review/JE-1000F/JP
python build.py diff-report --config config.ja.yaml --tracked-root docs/_review/JE-1000F/JP --from-ref HEAD~1 --to-ref HEAD
python build.py diff-report --config config.ja.yaml --tracked-root docs/_review/JE-1000F/JP --include-initial-adds
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

- Check [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) for `Row_key=product_name`
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
