# Auto-Manual Tool

Updated: 2026-04-11

Auto-Manual is the repository that turns structured content into target-specific manual bundles and release outputs.
It owns the current build, review, validation, revision tracking, and publish flow for this repo.
The current maintained smoke-check baseline is centered on `JE-1000F` across the active US and JP config families.

For the fixed US + JP release matrix, you can also use:

- [`scripts/build_us_jp_manuals.py`](scripts/build_us_jp_manuals.py): shared matrix runner for `US/en + US/es + US/fr + JP/ja`, with `--languages`, `--formats`, `--build-action`, `--check-first`, `--open-html`, and `--dry-run`
- [`scripts/build_us_jp_manuals.ps1`](scripts/build_us_jp_manuals.ps1): PowerShell wrapper for the shared US + JP matrix runner
- [`scripts/build_us_manuals.ps1`](scripts/build_us_manuals.ps1): US-only compatibility wrapper over the same Python matrix runner; requires explicit `-Model`

## 1. Current Role

This repository is responsible for:

- generating target-specific runtime bundles from templates and frozen CSV snapshots, with a valid `data/phase2/` snapshot as the default build/review/publish source and explicit `--data-root` still overriding it
- moving target-specific editing into [`docs/_review/`](docs/_review) once review starts
- validating review/runtime bundles before release
- exporting revision reports and release manifests
- generating a minimal design handoff package for explicit target delivery prep

This repository is not the place to define the long-term platform strategy.
That boundary lives in [`code-as-doc/architecture/System Evolution Strategy.md`](code-as-doc/architecture/System%20Evolution%20Strategy.md).

CI note:

- GitHub `Manual Validation` runs on pull requests for merge gating
- the same workflow runs again on `main` after merge for post-merge validation
- feature-branch pushes do not need a second duplicate `push` validation run
- `Manual Validation` now includes smoke paths for `diff-report` and `release-manifest` alongside the existing `lint`, `unit`, `doctor`, and `check` jobs
- `Manual Validation` now also runs a low-noise maintainability guardrail check so known orchestration and validation hotspots do not silently regrow past their agreed size ceilings
- `Review Preview Package` is a separate non-gating workflow that packages the review-preview workspace and diff-report artifacts for sharing as a GitHub artifact
- `Review Preview Package` now runs a stable smoke package with `--skip-word` and verifies the core packaged preview files before upload
- the published review preview root is now a multi-model review handoff workspace: families are hidden when `_review` content is missing, models are grouped inside each family, and language switching happens inside each model group
- diff assets now stay shared across the languages of one `family + model` package, while the workspace keeps the top-level review actions and a compact document-identity card with product name, manual title, model, region, and language
- `manual/index.html` remains a compatibility redirect to the workspace default manual, while `changes/index.html` opens the family hub and each family hub fans out to model-specific diff packages

## 2. Primary Entrypoint

The primary entrypoint is [`build.py`](build.py).

Typical review-first flow:

```bash
python3 build.py sync-data --config config.us.yaml --data-root data/phase2
python3 build.py doctor --config config.us-en.yaml --model JE-1000F --region US
python3 build.py rst --config config.us-en.yaml --model JE-1000F --region US --source runtime
python3 build.py review --config config.us-en.yaml --model JE-1000F --region US
python3 scripts/local_build.py check --config config.us-en.yaml --model JE-1000F --region US
python3 build.py process-review-start-queue --config config.us.yaml --data-root .tmp/review-start/phase2
python3 build.py process-build-queue --config config.us.yaml
python3 scripts/local_build.py publish --config config.us-en.yaml --model JE-1000F --region US
```

Review sync note:

- once a review bundle exists, `check`, `html`, `word`, `pdf`, and `publish` automatically prepare the runtime bundle and run the same parameter sync before export
- that auto sync now refreshes parameter-driven lines in review-backed RST pages without overwriting the rest of the manual review prose
- use `sync-review --page-file ...` or `review --refresh-review` only when you intentionally want a whole review page or bundle replaced from runtime
- single-language US review bundles from `config.us-en.yaml` still live under `docs/_review/<model>/US/en/`; the merged US queue/review flow driven by `config.us.yaml` now uses `docs/_review/<model>/US/` and exports one combined `en + fr + es` Word under `docs/_build/<model>/US/word/`
- `config.us-en.yaml`, `config.us-es.yaml`, and `config.us-fr.yaml` now inherit shared single-language defaults from [`config-bases/us-single-language-base.yaml`](config-bases/us-single-language-base.yaml) and keep their page stacks in [`docs/manifests/manual_us-single-*.yaml`](docs/manifests), so common build defaults no longer need to be edited in three places

Phase2 snapshot note:

- `sync-data` uses the local `lark-cli` login and `sync.phase2.*` config/env bindings to write normalized CSV snapshots into [`data/phase2/`](data/phase2), using the CLI's `base` record listing flow under the hood
- when a valid phase2 snapshot exists, build/review/publish flows default to that snapshot; explicit `--data-root` still overrides the default for local experiments or alternate roots
- queue-driven build flows still treat Feishu phase2 tables as the structured-data source of truth; committed `data/phase2/*.csv` files are build-time snapshots refreshed by `sync-data`
- `process-build-queue` still reads its queue rows from Feishu `Document_link` and still writes status plus `Document link` back to Feishu even when the artifact upload target is switched
- `python build.py message-control-dry-run --message "publish JE-1000F us-merged from branch feature/review-123"` is the current Phase 0 maintainer probe for the planned Feishu message plus OpenClaw control layer; it resolves one raw message into structured JSON and guardrails without dispatching workflows or mutating Feishu rows
- `sync-data` normalizes `Spec_Master.csv Slot_key` back to plain tokens such as `front.label` when the source table stores markdown-link wrappers like `[front.label](front.label)`
- `sync-data` now resolves full field names through Base field metadata before writing CSVs, so long columns such as `Row_label_footnote_refs` are not lost when `lark-cli` abbreviates display headers in `base +record-list`
- when `spec_master` and `spec_footnotes` are synced together, `sync-data` also converts Feishu linked-record style footnote refs such as `{"id":"rec..."}` into stable `Footnote_id` values before writing `Spec_Master.csv`
- `sync-data` does not auto-correct invalid `Is_Latest` rows; mismatched latest flags stay in the snapshot so validation can catch the source-data issue
- when `spec_master` is part of the sync, `sync-data` also regenerates [`data/phase2/row_key_mapping.csv`](data/phase2/row_key_mapping.csv) from the synced snapshot while preserving any existing manual `Row_key` / `Remark` entries
- `python build.py sync-data --config config.us.yaml --data-root data/phase2 --dry-run` is the fastest preflight on a new machine; it now reports missing `lark-cli` and missing `FEISHU_PHASE2_*` bindings together before any API call
- on Windows, the default `sync.phase2.cli_bin: lark-cli` now resolves to the installed `lark-cli` shim automatically, so no config override is required just to run `sync-data`
- for the planned DingTalk provider, [`tools/dingtalk/spike_cli.py`](tools/dingtalk/spike_cli.py) is the manual Phase 0 smoke helper; it uses the official App-Only token flow by default and lets you inject product-specific list/update/upload endpoints before any repo-integrated provider refactor starts
- [`tools/dingtalk/auth.py`](tools/dingtalk/auth.py) now wraps the verified App-Only token flow behind `DINGTALK_CLIENT_ID`, `DINGTALK_CLIENT_SECRET`, and `DINGTALK_CORP_ID`, while [`tools/dingtalk/workspace.py`](tools/dingtalk/workspace.py) can already parse a DingTalk docs node ID from a standard `alidocs.dingtalk.com/i/nodes/...` URL before the upload API is finalized
- for the currently observed DingTalk docs upload path, [`tools/dingtalk/alidocs_session_upload_cli.py`](tools/dingtalk/alidocs_session_upload_cli.py) is the manual browser-session spike helper; it follows `uploadinfo -> OSS upload -> commit`, then returns the uploaded file's `dentryUuid` and node URL for same-tenant linking
- `python build.py process-review-start-queue --config config.us.yaml --data-root .tmp/review-start/phase2` consumes the `sync.phase2.review_init` table, finds rows where `是否进入Review` is checked and `Review_status` is empty / `NotStarted`, resolves each row to a config family from `Build_family` first and `Lang` second, groups only the rows whose target config enables `build.queue_by_document_key`, syncs a fresh phase2 snapshot, creates or reuses one review branch, seeds `docs/_review`, pushes the branch, opens or reuses a PR, then writes back the same `Git_ref`, `PR_url`, `Review_status=InReview`, and cleared `是否进入Review` state to every row in that routed group
- review-init duplicate guard: review start is now treated as one-time per `Document_Key` target. If `origin/main` already contains committed content under `docs/_review/<model>/<region>/`, the worker refuses duplicate seeding and writes back `Initial_result=不允许重复创建` plus `Remarks=如需强制刷新内容，请在vs通过相关git命令操作，具体详见文档quick_start_guide.md.`
- [`.github/workflows/feishu-start-review.yml`](.github/workflows/feishu-start-review.yml) is the `main`-owned GitHub-hosted review-init worker; it reuses `FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID` and `FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID`, and it is the recommended way to let a Feishu table create the review branch + PR automatically
- `python build.py process-build-queue --config config.us.yaml` consumes the `sync.phase2.document_link` task table, writes `开始构建时间` as soon as a pending row starts, resolves the build config from `Build_family` first and `Lang` second, groups only the rows whose resolved config enables `build.queue_by_document_key`, builds the generated Word file, publishes it to the primary Feishu/wiki destination, can then sync the same DOCX to DingTalk as a mirror, writes the local Word path back to `Document directory`, writes the canonical Feishu/wiki URL back to `Document link`, optionally writes the DingTalk node URL to `Document link_dd`, adds the sync note into `构建结果`, writes the refresh result back to `data_sync`, and flips the trigger back to `已构建`
- the merged US `config.us.yaml` bundle now exports one `JE-1000F / US` Word that contains `en`, `fr`, and `es` sections together; `Spec_Master.Source_lang` / `*_source` content is required, and CSV-driven non-source language fields may be blank because lookup falls back to source-language text automatically
- queue routing is now `Build_family`-first: use `us-merged`, `us-en`, `us-es`, `us-fr`, `jp-ja`, or `cn-zh`; `Lang` remains a compatibility field and no longer decides the target when `Build_family` is filled
- queue rows should now use `Workflow_action` only: `Start Review` to create or reuse review branches, `Build Draft Package` for review-stage rebuilds, and `Publish` for publish-stage builds; leave `Doc_phase` blank
- when review-init reuses the shared `Document_link` view, the start-review worker only consumes `Workflow_action = Start Review`, while the build queue only consumes `Workflow_action = Build Draft Package` or `Workflow_action = Publish`
- merged US review-init and build-queue rows should use `Build_family = us-merged` and may leave `Lang` blank; single-language rows should use the matching single-language family such as `us-en` / `us-fr` / `us-es`
- config policy for `build.queue_by_document_key`: enable it only on merged whole-book families that intentionally represent one shared manual across languages, such as today's `us-merged` and any future `eu-merged` / `cn-merged`; keep it disabled for single-language families such as `us-en`, `us-fr`, `us-es`, `jp-ja`, `cn-zh`, or future `eu-de` / `eu-fr`, which should continue to route one row per `record_id`
- when the queue row includes `Version`, Build Draft Package DOCX names use `manual_<model>_<region>_<lang>_<Version>.docx`, while Publish queue DOCX names use `manual_<model>_<region>_<lang>_publish_<Version>.docx`
- `Workflow_action = Build Draft Package` rows must carry `Git_ref`; the worker fetches that review branch into a temporary worktree and builds from that branch content instead of silently falling back to `main`
- on a local worker, if a same-named local branch already exists for `Git_ref`, `process-build-queue` uses that local branch content directly so unpushed review updates can still be verified and uploaded
- if GitHub fetch is temporarily unavailable but the same `origin/<Git_ref>` or local branch already exists on the worker, `process-build-queue` reuses that cached ref instead of failing the build immediately
- direct `build.py` actions still write Build Draft Package outputs to the repo [`docs/_build/`](docs/_build) tree by default; for local verification use [`scripts/local_build.py`](scripts/local_build.py), [`scripts/local_build.ps1`](scripts/local_build.ps1), or [`scripts/local_build.sh`](scripts/local_build.sh) so `check`, `diff-report`, `release-manifest`, and `publish` default to `.tmp/staging`
- explicit `--staging-root <dir>` and `AUTO_MANUAL_STAGING_ROOT=<dir>` still override that default when you need another isolated root
- `release-manifest` writes traceability files to [`reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv`](reports/releases) by default, or to `<staging-root>/reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv` when staging is enabled; Publish queue outputs are staged under [`reports/releases/<model>/<region>/<lang>/versions/<version>/`](reports/releases), and the latest publish HTML snapshot is mirrored under [`reports/releases/<model>/<region>/<lang>/latest/html/`](reports/releases) for Vercel hosting
- [`scripts/process_build_queue.ps1`](scripts/process_build_queue.ps1) is the Windows-friendly queue wrapper for automation: it restores the local Node/npm path plus `FEISHU_PHASE2_*` user env vars, and if optional DingTalk sync is enabled it also restores `AUTO_MANUAL_ARTIFACT_SINK_PROVIDER`, `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER`, and `DINGTALK_DOCS_*`, then runs `build.py process-build-queue --staging-root .tmp/staging`, forwards any extra CLI args such as `--dry-run` or `--record-id`, and writes logs into [`.tmp/process-build-queue/`](.tmp/process-build-queue)
- [`scripts/process_build_queue_feishu.ps1`](scripts/process_build_queue_feishu.ps1) is the one-click Feishu-only wrapper: it forces `AUTO_MANUAL_ARTIFACT_SINK_PROVIDER=lark_drive` and disables the DingTalk mirror before delegating to [`scripts/process_build_queue.ps1`](scripts/process_build_queue.ps1)
- [`scripts/process_build_queue_dingtalk.ps1`](scripts/process_build_queue_dingtalk.ps1) is the one-click DingTalk sync wrapper: it keeps `AUTO_MANUAL_ARTIFACT_SINK_PROVIDER=lark_drive`, enables `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER=dingtalk_alidocs_session`, and then delegates to [`scripts/process_build_queue.ps1`](scripts/process_build_queue.ps1)
- for the full local DingTalk AliDocs setup steps, including how to capture `a-token`, `x-xsrf-token`, and the full cookie string, see [`user-guide/dingtalk_alidocs_upload_setup_guide.md`](user-guide/dingtalk_alidocs_upload_setup_guide.md)
- `python build.py listen-build-queue --config config.us.yaml` starts the push-based queue listener: it auto-subscribes the current `Document_link` base to docs events with the current user identity, waits on the Feishu long connection with the same user identity, and triggers `process-build-queue` immediately when the `是否立即构建` checkbox is checked on a `Document_link` row
- [`scripts/listen_build_queue.ps1`](scripts/listen_build_queue.ps1) is the Windows-friendly listener wrapper; on this machine it is launched from the Windows Startup folder so the listener starts after login, runs `listen-build-queue --staging-root .tmp/staging`, and writes logs into [`.tmp/build-queue-listener/`](.tmp/build-queue-listener)
- [`.github/workflows/feishu-build-queue.yml`](.github/workflows/feishu-build-queue.yml) is the `main`-owned remote GitHub Actions worker: after merge to the default branch and after repo secrets are configured, it runs every 5 minutes plus `workflow_dispatch`, uses `FEISHU_PHASE2_IDENTITY=bot`, then consumes the `Document_link` queue without relying on any local machine
- the remote Draft/Publish queue workers can also keep Feishu/wiki as the primary sink while enabling DingTalk mirror sync when GitHub Secrets provide `DINGTALK_DOCS_A_TOKEN`, `DINGTALK_DOCS_XSRF_TOKEN`, and `DINGTALK_DOCS_COOKIE`; `DINGTALK_DOCS_TARGET_NODE_URL` is optional and acts only as the remote default target
- the three GitHub-hosted Feishu workers now share [`.github/actions/feishu-common-setup/action.yml`](.github/actions/feishu-common-setup/action.yml) plus [`scripts/validate_required_env.sh`](scripts/validate_required_env.sh), so Python/Node/pandoc/lark setup and required-env validation only need to change in one place
- for remote immediate builds after merge to `main`, create a Feishu workflow with the combined condition `是否触发文档构建 = Y` and `是否立即构建 = true`, then call the GitHub `workflow_dispatch` API for `feishu-build-queue.yml` on `main`; the queue still only processes rows whose trigger field is `Y`, and the checkbox acts as an accelerator instead of a standalone build request
- the Document_link worker reuses `FEISHU_PHASE2_BASE_TOKEN`, expects `FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID` plus `FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID`, and can optionally honor `FEISHU_PHASE2_DOCUMENT_LINK_WIKI_PARENT_TOKEN` when you want to override the default knowledge-base destination
- the remote bot flow also needs the Feishu app behind `FEISHU_APP_ID/FEISHU_APP_SECRET` to have read access to the phase2 source tables and write access to the `Document_link` table; otherwise the poller can read pending rows but cannot write back `开始构建时间` / `构建结果`
- if the queue should move uploaded Word files into a wiki knowledge base, the same user/bot identity also needs edit/container permission on the destination wiki parent node; otherwise upload still succeeds, `Document link` falls back to the latest Drive URL, and the success status is annotated with `drive_only` plus the wiki attach failure
- to keep Feishu/wiki as the primary sink and also sync DingTalk on a local worker, set `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER=dingtalk_alidocs_session` and provide `DINGTALK_DOCS_A_TOKEN`, `DINGTALK_DOCS_XSRF_TOKEN`, and `DINGTALK_DOCS_COOKIE` with optional `DINGTALK_DOCS_TARGET_NODE_URL` and `DINGTALK_DOCS_BX_V`; Feishu `FEISHU_PHASE2_*` bindings stay required because the queue control plane and writeback table remain in Feishu. Only set `AUTO_MANUAL_ARTIFACT_SINK_PROVIDER=dingtalk_alidocs_session` when you explicitly want DingTalk to replace the primary sink.
- on Windows, prefer [`scripts/process_build_queue_feishu.ps1`](scripts/process_build_queue_feishu.ps1) when you want Feishu-only uploads and [`scripts/process_build_queue_dingtalk.ps1`](scripts/process_build_queue_dingtalk.ps1) when you want Feishu primary plus DingTalk sync; both wrappers still accept extra queue args such as `--dry-run` and `--record-id`
- the current DingTalk sink is a browser-session worker mode built on the observed AliDocs `uploadinfo -> OSS upload -> commit -> node URL` flow; local workers can use env vars directly, and remote GitHub workers can use the same flow when the DingTalk session values are injected through repository secrets
- the push listener requires the Feishu self-built app to have the `drive.file.bitable_record_changed_v1` event added and published in the Open Platform console; without that event, the long connection stays idle even though the local listener is running
- `page_registry.csv`, page selection/applicability, and [`data/layout_params.csv`](data/layout_params.csv) stay repo-maintained and are not overridden by `--data-root`

Start Review, Build Draft Package, Publish:

- `process-build-queue` no longer refreshes `data/phase2` unconditionally; it only runs `sync-data` when `Document_link.是否强制刷新数据 = true`
- when `是否强制刷新数据` is checked, the queue refreshes phase2 immediately before that document group, clears the checkbox afterward, and writes `data_sync=refreshed` on success or `data_sync=failed` if the refresh step itself fails
- when `是否强制刷新数据` is left unchecked, the queue builds directly from the current local `data/phase2` snapshot plus the current review branch content and writes `data_sync=skipped`
- `process-review-start-queue` consumes rows whose `Workflow_action` maps to `Start Review`, then creates or reuses the review branch and seeds [`docs/_review/`](docs/_review)
- `process-build-queue --workflow-action build-draft-package` uses the current `data/phase2` snapshot plus the PR branch's current [`docs/_review/`](docs/_review) content; Build Draft Package is for documents that have already entered review
- `process-build-queue --workflow-action publish` uses the current `data/phase2` snapshot plus `Document_link.Git_ref` when present, runs `build.py publish` and `build.py html --source review`, then stages the formal release bundle under `reports/releases`
- `Doc_phase` no longer participates in queue routing; if a row should run, fill `Workflow_action` instead
- `process-build-queue --record-id <record_id>` lets one workflow rebuild exactly one `Document_link` row
- when optional DingTalk mirror sync is enabled, `Document link` remains the canonical Feishu/wiki writeback URL for compatibility, and if the table also contains `Document link_dd` the mirrored DingTalk node URL is written there while the queue rows, trigger state, and build status continue to live in Feishu
- when optional DingTalk mirror sync is enabled and the row also contains `是否上传钉钉`, that checkbox becomes the row-level gate: checked rows also sync DingTalk and write `Document link_dd`, unchecked rows stay Feishu/wiki-only for that run
- when a checked DingTalk row also contains `DingTalk_target_node_url`, that row-level target wins over the global `DINGTALK_DOCS_TARGET_NODE_URL`; if the row field is blank, the worker falls back to the env default
- `钉钉上传节点` is accepted as a compatibility alias for the same row-level target, but prefer `DingTalk_target_node_url` as the canonical column name
- [`.github/workflows/feishu-start-review.yml`](.github/workflows/feishu-start-review.yml) is the `main`-owned Start Review worker; dispatch it on `main` so the branch/PR bootstrap always uses the latest workflow definition
- [`.github/workflows/feishu-build-queue.yml`](.github/workflows/feishu-build-queue.yml) is the `main`-owned Publish queue worker
- [`.github/workflows/feishu-draft-build-queue.yml`](.github/workflows/feishu-draft-build-queue.yml) is the `main`-owned Build Draft Package worker
- the OpenClaw command bridge now lives under [`integrations/openclaw/auto-manual-control-layer/`](integrations/openclaw/auto-manual-control-layer); it exposes `/start-review`, `/build-draft`, `/publish`, and `/manual-status` without moving build execution out of GitHub Actions
- the repo now also ships [`integrations/openclaw/feishu-im-webhook-adapter/`](integrations/openclaw/feishu-im-webhook-adapter), a standalone Feishu IM webhook ingress that receives text messages, calls `queue-resolve-action|queue-query|queue-execute`, and replies back into the same Feishu thread
- `python build.py listen-message-control --config config.us.yaml` is the no-server local Feishu IM ingress: it starts `lark-cli event +subscribe` for `im.message.receive_v1`, reuses the same repo-local message handler, and replies in-thread without exposing any public callback URL
- for ECS deployment, the adapter now also ships `systemd` service wrappers and unit templates under [`integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/`](integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/); use a named Cloudflare Tunnel or your own HTTPS proxy if the callback URL must stay stable after restarts
- against the control-layer plan, the repo now has the full repo-local Phase 2 control stack: `queue-query`, `queue-resolve-action`, `queue-execute`, structured failure replies, explicit Publish confirmation, and a standalone Feishu IM webhook adapter. Encrypted callback support and ECS deployment assets are now repo-owned; the remaining gaps are shared multi-instance state and a stable named ingress rollout.
- `python build.py queue-query --config config.us.yaml --queue-scope all --document-id JE-1000F_US_0.3 --json` is the Phase 2 natural-language helper surface for resolving Feishu queue rows into one concrete `record_id`, `Workflow_action`, `Git_ref`, `Document link`, and `构建结果`
- `python build.py queue-resolve-action --config config.us.yaml --query-text "发布 JE-1000F_US_0.3" --json` is the structured action dry-run surface for OpenClaw; it turns one natural-language ask into `action_name`, `resolution_status`, confirmation / missing-field guardrails, and the matched row fields without dispatching anything
- `python build.py queue-query --config config.us.yaml --query-text "查 JE-1000F_US_0.3 的 Build Draft Package" --json` is the preferred natural-language entry for Phase 2; it applies document_id-first parsing so tokens like `JE-1000F_US_0.3` are treated as exact `Document_ID` before any broader field inference happens
- `python build.py translation-memory --config config.us.yaml --model JE-1000F --region US --query-text "USB-C 100W Port" --lang fr --table spec-master` queries the repo-owned `data/phase2` snapshot and returns compact multilingual translation memory context for OpenClaw or maintainer translation work
- `python .agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py --query-text "Always follow these basic precautions when using this product." --source-lang en --target-lang fr --format prompt` queries the dedicated live sentence-pair table first, auto-splits longer source text, and emits prompt-ready context for OpenClaw translation
- the same parser also understands spaced operator asks such as `帮我生成 JE-1000F US 0.3 草稿`, `开始 review JE-1000F us-merged`, and `为什么 JE-1000F US 0.3 构建失败`; when it can build an exact `Document_ID`, that exact id still wins over broader inferred filters
- `python build.py queue-execute --config config.us.yaml --query-text "请帮我构建 JE-1000F_US_en_0.3，并返回 Build Draft Package 记录。只返回 record_id、Git_ref、构建结果、Document link。"` is the deterministic execution entry for Phase 2; it resolves one Feishu row, dispatches the matching GitHub workflow on `main`, waits for completion, then re-reads the Feishu row and prints the final record fields
- when `queue-execute` resolves `Workflow_action = Publish`, it now refuses to dispatch until you add `--confirm-publish`
- `python scripts/openclaw_git_guard.py status` and `python scripts/openclaw_git_guard.py switch --branch main --pull` are the bounded local Git helpers for OpenClaw or Feishu-triggered operator flows; they only expose branch status plus safe switch/fetch/ff-only-pull behavior and refuse branch changes from a dirty non-generated worktree
- `node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch <start-review|build-draft> <record_id>` and `node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch publish <record_id> confirm` are the matching local control CLI forms; they reuse the same GitHub workflow-dispatch and state-tracking logic as the OpenClaw plugin
- `node integrations/openclaw/auto-manual-control-layer/cli.mjs status last` returns the latest tracked GitHub run state for that local control CLI
- the local `listen-message-control` listener stays on the same bounded action set as the webhook adapter: `query_status`, `start_review`, `build_draft_package`, `publish`, plus natural-language failure/status asks such as `为什么 JE-1000F US 0.3 构建失败`
- the three GitHub workers now accept one OpenClaw-only correlation input, `openclaw_dispatch_nonce`, and upload a small `openclaw-run-metadata` artifact so status lookups can map one manual dispatch back to one workflow run cleanly
- repo-local OpenClaw dispatch no longer hard-requires the optional `adm-zip` package just to send a workflow dispatch from a plain repo checkout; metadata artifact parsing is now a best-effort status enhancement instead of a dispatch-time dependency
- the review-start worker now writes a structured failure summary into `openclaw-run-metadata`, so `/manual-status` and `queue-execute` can return user-facing causes such as `缺少 JE-1000F_CN 的规格数据，无法进入 review。` instead of only a generic workflow failure
- when OpenClaw dispatches one explicit review-start `record_id` but the GitHub worker cannot re-read that row as pending from the bound Feishu view, the worker now records that as a structured failure instead of a silent no-op success
- dispatch the Build Draft Package worker on `main`; the actual review content comes from `Document_link.Git_ref`, and rows without `Git_ref` now fail fast instead of silently building from `main`
- dispatch the Publish worker on `main`; `main` only carries the workflow definition, while `Document_link.Git_ref` still decides the review branch source when present
- when a Publish row carries `Git_ref`, the `main`-owned Publish queue worker now builds that review branch instead of rebuilding from `main`
- for the current OpenClaw Phase 2 scope, keep `Document link` as the canonical artifact link field returned by the control layer; `Document link_dd` is now an optional DingTalk-only supplemental writeback field and is not required by queue resolution or OpenClaw replies

- recommended stage split:
  - use the review-init table to move one document into review and create its branch / PR once
  - use the `Document_link` queue with `Workflow_action=Build Draft Package` to rebuild a Build Draft Package from that PR branch repeatedly
  - use the `Document_link` queue with `Workflow_action=Publish` plus `Git_ref` to publish from that same review branch

Dedicated zh bundle example:

```bash
python3 build.py check --config config.zh.yaml --model JE-2000E --region CN
python3 build.py all --config config.zh.yaml --model JE-2000E --region CN
```

Batch export example:

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html,word,pdf
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --build-action validate --languages en,fr
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html --open-html
.\scripts\build_us_manuals.ps1 -Action check -Model JE-1000F -Languages en,es -DryRun
```

Word export note:

- `config.us-en.yaml` now reapplies the `reference_en.docx` heading, table, and default paragraph styling after DOCX generation, while keeping the generated `safety` and `spec` pages unchanged
- generated DOCX images are now normalized to embedded relationships before post-processing so third-party viewers such as Feishu are less likely to drop image-backed table cells during preview

HTML output note:

- generated cover pages remain part of the PDF/LaTeX flow; the HTML entry page starts at the first manual content section instead of rendering a standalone cover screen
- manual HTML now suppresses most Furo documentation chrome in preview mode, uses a continuous reading layout instead of browser-side fake pagination, regenerates a lightweight left outline from manual headings, and presents generic headings, copy width, figures, ordinary tables, and the multilingual preface notice with a restrained neutral manual-reader style while preserving dedicated layouts such as the `SPECIFICATIONS` table treatment
- review-preview workspace manual pages now reuse the same manual HTML/CSS/JS treatment as the local build, including the generated heading sidebar and the same no-top-switcher layout
- when a PR changes the zh manual family under `docs/templates/page_zh/`, `docs/templates/recipes/zh/`, or `docs/manifests/manual_zh.yaml`, review-preview keeps `JE-2000E / CN` as the primary runtime target but still packages every existing review model into the same workspace
- `build.py diff-report` now ignores initial baseline Added rows by default; pass `--include-initial-adds` when you need the full first-import churn
- diff-report field matching now prefers stable source back-mapping before falling back to rendered labels, so placeholder/spec label rewrites are more likely to surface as one `M` row with clearer `old_value/new_value` instead of separate `A/D` noise

Review-sharing example:

```powershell
python tools/process_docs/build_review_preview.py --config config.us-en.yaml --model JE-1000F --region US --source review --from-ref HEAD~1 --to-ref HEAD --all-review-models
```

Review-sharing config note:

- omit `--config` when `--region` is `US`, `JP`, or `CN` and you want the shared family default config
- keep `--config config.us-en.yaml` when you want the review-preview workspace to land on the explicit US English single-language target by default

Vercel note:

- the repo-level [`vercel.json`](vercel.json) now points at the latest publish HTML flow, not the review-preview package
- [`.github/workflows/feishu-build-queue.yml`](.github/workflows/feishu-build-queue.yml) builds queue-driven Publish rows, stages the latest publish HTML under [`site/publish-latest/dist/`](site/publish-latest/dist), then runs `vercel pull`, `vercel build`, and `vercel deploy --prebuilt`
- the Vercel bridge entrypoint is [`tools/process_docs/vercel_build_publish_latest.py`](tools/process_docs/vercel_build_publish_latest.py), which reuses an already staged latest publish site when it exists
- `Review Preview Package` no longer deploys to Vercel; it uploads the review-sharing package as an artifact only

Read the Docs note:

- [`.readthedocs.yaml`](.readthedocs.yaml) now provides a minimal RTD entrypoint for the default runtime HTML manual only: `config.us-en.yaml + JE-1000F + US + en`
- the RTD job runs `python build.py rst --config config.us-en.yaml --model JE-1000F --region US --source runtime --no-clean --skip-root-index`, then points Sphinx at [`docs/_build/JE-1000F/US/en/rst/`](docs/_build) instead of the repo-root [`docs/`](docs)
- RTD is for a stable public reading target only; it does not replace review-preview packaging, queue-driven Publish releases, Vercel latest-publish hosting, or Word / PDF export

Windows note:

- build actions except `fast` clean the current target output first
- if File Explorer, a browser, Word, or a PDF viewer is open under [`docs/_build/`](docs/_build), close it before rerunning
- if you only need an in-place rebuild, add `--no-clean`

Git workflow note:

- start new work with `powershell -ExecutionPolicy Bypass -File scripts/start_branch.ps1 codex/<topic>` on Windows or `./scripts/start_branch.sh codex/<topic>` on mac/Linux instead of branching manually from a possibly stale local `main`
- the repo can use a managed pre-push guard from [`.githooks/pre-push`](.githooks/pre-push); enable it locally with `git config core.hooksPath .githooks`
- that guard now runs through the shared [`scripts/git_branch_guard.py`](scripts/git_branch_guard.py) core instead of a bash-only hook, and the repo also ships [`.githooks/pre-push.cmd`](.githooks/pre-push.cmd) plus [`.githooks/pre-push.ps1`](.githooks/pre-push.ps1) as Windows-native companion launchers
- the guard blocks pushes from branches that do not contain the latest `origin/main`; bypass only intentionally with `git push --no-verify`
- for chat-driven local operator flows, use [`scripts/openclaw_git_guard.py`](scripts/openclaw_git_guard.py) instead of exposing arbitrary `git` commands to OpenClaw; it only supports `status` and safe `switch --pull`
- if a Windows GUI client still does not honor repo-managed hooks, keep the hook optional there and treat the start-branch wrapper as the required freshness guard

Do not treat this file as the full command reference.
The command semantics and output layout are maintained in [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md).

## 3. Editing Surfaces

Use different surfaces for different stages:

- shared template changes: [`docs/templates/`](docs/templates)
- structured data changes: preferred snapshot root [`data/phase2/`](data/phase2), with [`data/phase1/`](data/phase1) kept as the legacy baseline
  `Spec_Footnotes.csv` is now the footnote-definition table only. Keep one row per reusable `Footnote_id`, target rows by `Region` + `Model`, and let the system derive the visible superscript marker from `Footnote_order`.
`Spec_Master.csv` `Page` may now be a comma-separated page list. Use `Product overview` for Product overview-only placeholder rows, and use `Product overview, specifications,` when the same row is shared by both pages. For page-value rows, keep `Row_key` as the concept and use `Slot_key` to describe the placeholder slot. The shared source-text columns are `Row_label_source`, `Param_source`, and `Value_source`; they hold the row's source-manual text. `Source_lang` stores that source-language code explicitly, for example `en`, `ja`, or `zh`, and code no longer infers it from `Region`. `document_key` is a derived helper column and may use either `[Model]_[Region]` or `[Model]_[Region]_[Source_lang]`. `Row_order` is now a formal column and controls the row display order inside each `document_key + Page + Section`, while `Line_order` controls the order of multiple lines inside one logical row. Visible section defaults can live in `spec_titles.csv section_order`, but if `Spec_Master.csv Section_order` is filled, that explicit value has the highest priority. `Row_label_en`, `Param_en`, and `Value_en` are no longer supported; source-language text must live in `*_source`. The old `project_code` / `项目代码` column has been removed; row targeting now uses `Region` + `Model`. Spec-cell footnotes are now referenced through `Row_label_footnote_refs`, `Param_footnote_refs`, and `Value_footnote_refs`; do not handwrite `①②③` into visible spec text.
  `Spec_Notes.csv` now stores bottom-of-spec notes that are not tied to a superscript reference, such as trademark statements.
  `symbols_blocks.csv` stores symbols-page table copy, uses `Region` and `Model` to match target manuals like `Spec_Master.csv`, keeps `Source_lang` aligned with the same source-language code pattern, and includes an `image_path` field for the referenced icon asset. Leave `Region` / `Model` blank when one symbols row should be shared.
  Safety intro pages are now maintained as fixed RST templates under [`docs/templates/page_*/safety_*.rst`](docs/templates), wired through each family's manifest or page list. JP still keeps its detailed warning content in [`docs/templates/page_jp/01_meaning_of_symbols.rst`](docs/templates/page_jp/01_meaning_of_symbols.rst). The old `content_blocks.csv` safety source has been removed from the active repo flow.
- target-specific review edits after review starts: [`docs/_review/`](docs/_review)
- generated runtime and export outputs: [`docs/_build/`](docs/_build)

Rule:

- before review starts, seed the draft from templates and data
- after review starts, edit `_review`
- do not use `_build` as the long-lived editing surface

The current user workflow and source-of-truth rules are maintained in [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md).

## 4. Document Map

Use the document that owns the topic:

- maintainer doc index and ownership map: [`code-as-doc/README.md`](code-as-doc/README.md)
- current maintainer command reference: [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md)
- current JP / US family difference boundary: [`code-as-doc/manual_family_guide.md`](code-as-doc/manual_family_guide.md)
- current Git branching and GitHub protection rules: [`code-as-doc/dev/git_branching_guide.md`](code-as-doc/dev/git_branching_guide.md)
- current Vercel latest-publish HTML flow: [`code-as-doc/dev/vercel_review_preview_guide.md`](code-as-doc/dev/vercel_review_preview_guide.md)
- current user workflow and editing rules: [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md)
- happy-path example: [`user-guide/quick_start_guide.md`](user-guide/quick_start_guide.md)
- architecture doc index: [`code-as-doc/architecture/README.md`](code-as-doc/architecture/README.md)
- current repository component map: [`code-as-doc/architecture/Hello_Docs_Architecture.md`](code-as-doc/architecture/Hello_Docs_Architecture.md)
- current OpenClaw bootstrap: [`BOOTSTRAP.md`](BOOTSTRAP.md)
- current OpenClaw integration package: [`integrations/openclaw/README.md`](integrations/openclaw/README.md)
- repo-local translation memory skill for OpenClaw-assisted multilingual work: [`.agents/skills/bitable-translation-memory/SKILL.md`](.agents/skills/bitable-translation-memory/SKILL.md)
- future canonical content model: [`code-as-doc/architecture/Content_Data_Model.md`](code-as-doc/architecture/Content_Data_Model.md)
- long-term strategy and stable architecture boundaries: [`code-as-doc/architecture/System Evolution Strategy.md`](code-as-doc/architecture/System%20Evolution%20Strategy.md)
- repo-level execution roadmap: [`optimization_project.md`](optimization_project.md)

## 5. Key Directories

- [`build.py`](build.py): top-level CLI entrypoint
- [`.readthedocs.yaml`](.readthedocs.yaml): minimal Read the Docs build config for the default US English runtime HTML target
- [`tools/`](tools): orchestration, rendering, validation, diff, and release helpers
- [`docs/manifests/`](docs/manifests): page-stack manifests for manifest-driven manual families
- [`docs/templates/page_zh/`](docs/templates/page_zh): shared zh prose-template family for the CN manual stack
- [`data/phase2/`](data/phase2): preferred Feishu-synced CSV snapshot inputs
- [`data/phase1/`](data/phase1): legacy baseline snapshot inputs
- [`docs/templates/`](docs/templates): shared seed templates
- [`docs/_review/`](docs/_review): target-specific review layer
- [`docs/_build/`](docs/_build): runtime bundles and export outputs
- [`reports/`](reports): revision reports and release manifests
- [`tests/`](tests): automated regression coverage

## 6. Maintenance Rule

When command behavior, workflow ownership, or architecture boundaries change:

- update the owning document in the same change
- keep `python tools/check_maintainability_guardrails.py` green when touching the guarded hotspot files
- keep the PR checklist honest: if a helper boundary moves, update the module map in the same change
- avoid restating the same rules in multiple docs
- keep history in [`code-as-doc/code_optimization_log.md`](code-as-doc/code_optimization_log.md), not in the current guides
