# Feishu IM Adapter

This package owns both Feishu IM ingress modes for the repo control layer:

- webhook mode for a public HTTPS callback
- local long-connection mode for a no-server local machine

It does not build documents itself.
It receives Feishu events, normalizes text messages, calls the repo's existing
`build.py` control-surface commands, and replies back into the same Feishu thread.

Current command path:

```text
Feishu IM event
  -> feishu-im-webhook-adapter
  -> build.py queue-resolve-action
  -> build.py queue-query | build.py queue-execute
  -> Feishu reply
```

Current scope:

- `query_status`
- `start_review`
- `build_draft_package`
- batch `build_draft_package` when the message names a model, market, and manual copy or config scope, such as `输出JE-1000F的所有欧规说明书文案`, `构建JE-1000F的所有欧规说明书文案`, `基于配置构建JE-1000F的欧规`, or the implicit-all form `构建JE-1000F的欧规说明书文案`; if no market is named, phrases such as `构建JE-1000F说明书文案` use a model-wide `Task_id` prefix and match every triggered Build Draft Package row for that model
- read-only manual-index lookups from the Feishu Base table `发布文档管理`; messages such as `查 JE-2000F 的说明书链接`, `查询各产品的说明书`, or `获取说明书总览信息` call `build.py manual-index-query` before queue resolution and never dispatch builds
- `publish` with explicit confirmation
- `cloud-doc backport` for accepted Feishu cloud-doc review revisions, gated by
  `FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOWED_SENDERS`; the message must include one
  Feishu cloud-doc link plus an explicit `docs/_review/...rst` source path
- `cloud-doc approve <run-id> <delta_hash> …` / `cloud-doc reject <run-id> <delta_hash> …`
  to approve/reject **F6 source-table (Bitable) writes** of reviewer-confirmed
  Class D values, gated by `FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOWED_SENDERS` and the
  separate `FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOW_SOURCE_WRITE` flag (see the runbook
  `code-as-doc/dev/im_backport_approval_runbook.md`)

Current limitations:

- expects the callback security mode and runtime env to stay explicit
- uses the repo-local `build.py` CLI and the existing OpenClaw/GitHub dispatch path
- cloud-doc backport messages run `tools/cloud_doc_backport.py run-review`
  locally and reply with report paths / `PR_READY`
- cloud-doc backport PR messages call `tools/cloud_doc_backport.py open-pr`
  only after an explicit `backport-pr` message and the PR-create env gate; they
  still do not write Feishu source tables
- cloud-doc `approve`/`reject` messages call `tools/cloud_doc_backport.py
  apply-source-table`; **source-table writes default to dry-run** and only write
  Bitable when `FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOW_SOURCE_WRITE=true` and the
  approved request resolves to an exact `record_id` with a configured table
  binding — human approval is always mandatory and the agent never approves

## Environment

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `AUTO_MANUAL_REPO_ROOT`
- `AUTO_MANUAL_CONTROL_CONFIG`

Optional:

- `FEISHU_IM_VERIFICATION_TOKEN` or `FEISHU_VERIFICATION_TOKEN`
- `FEISHU_IM_ENCRYPT_KEY` or `FEISHU_ENCRYPT_KEY`
- `FEISHU_IM_WEBHOOK_HOST`
- `FEISHU_IM_WEBHOOK_PORT`
- `FEISHU_IM_WEBHOOK_PATH`
- `FEISHU_IM_HEALTH_PATH`
- `FEISHU_IM_REQUIRE_MENTION`
- `FEISHU_IM_ENABLE_MESSAGE_REACTIONS` or `FEISHU_IM_ENABLE_REACTIONS`
- `FEISHU_IM_PUBLISH_CONFIRM_TTL_SECONDS`
- `FEISHU_IM_CONTEXT_TTL_SECONDS`
- `FEISHU_IM_BATCH_DISPATCH_DELAY_MS`; defaults to `2000` so batch Draft dispatches do not burst all GitHub workflow requests at once
- `FEISHU_IM_BATCH_STATUS_TIMEOUT_SECONDS`; defaults to `60` for deployed adapters and controls how long the adapter waits for fresh batch writeback before sending a follow-up status summary
- `FEISHU_IM_BATCH_STATUS_POLL_SECONDS`; defaults to `5` for batch writeback polling
- `FEISHU_IM_MANUAL_INDEX_LIMIT`; defaults to `10` rows in manual-index replies
- `FEISHU_MANUAL_INDEX_BASE_TOKEN`; optional override for the `发布文档管理` Base token; defaults to the Base behind `AS02w8ZL2iDv44kDLHIcHCPqntd`
- `FEISHU_MANUAL_INDEX_TABLE_ID`; optional override for the manual-index table; defaults to `tbl1ypQJJPbKostu`
- `FEISHU_MANUAL_INDEX_VIEW_ID`; optional override for the manual-index view; defaults to `vewytqcvDc`, preserving the table's visible-record scope
- `FEISHU_MANUAL_INDEX_IDENTITY`; optional `user` / `bot` override; defaults to `FEISHU_PHASE2_IDENTITY` or `user`
- `FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOWED_SENDERS`; comma-separated Feishu
  `open_id` allowlist for cloud-doc backport messages, or `*` for local smoke
- `FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOW_WRITE`; defaults to `false`; when true,
  an allowed sender can include `--write` to patch guarded `_review` prose and
  run residual verification
- `FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOW_PR_CREATE`; defaults to `false`; when
  true, an allowed sender can send a separate `cloud-doc backport-pr ...`
  message to create a draft PR from a `PR_READY` run manifest
- `FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOW_SOURCE_WRITE`; defaults to `false`; gates
  **F6 Bitable source-table writes** SEPARATELY from `_review` writes (wider blast
  radius, no git revert). When false, `cloud-doc approve` runs a dry-run plan;
  when true, approved+resolved requests are written via the explicit bindings
- `FEISHU_IM_CLOUD_DOC_BACKPORT_SOURCE_TABLE_BINDINGS`; comma-separated
  `TABLE=BASE_TOKEN:TABLE_ID` writable bindings per change-request table (e.g.
  `Manual_Copy_Source=bascn…:tbl…`); required (per table) for live source writes
- `FEISHU_IM_CLOUD_DOC_BACKPORT_APPROVAL_LOG`; append-only JSONL audit of every
  approve/reject (approver, timestamp, decision, run-id, hashes, result);
  defaults to `reports/cloud_doc_backport/approval_audit.jsonl`
- `FEISHU_IM_STATE_FILE`
- `FEISHU_IM_LOCAL_PROFILE_DIR` or `OPENCLAW_LOCAL_PROFILE_DIR`
- `FEISHU_IM_DISABLE_LOCAL_PROFILE` or `OPENCLAW_DISABLE_LOCAL_PROFILE`
- `FEISHU_IM_ENCRYPT_KEY` or `FEISHU_ENCRYPT_KEY` when the Feishu app enables encrypted callbacks
- `FEISHU_IM_LARK_CLI_BIN` for local long-connection mode
- `FEISHU_IM_EVENT_IDENTITY` for local long-connection mode; defaults to `bot`
- `FEISHU_IM_LARK_CLI_HOME` for local long-connection mode when the new app must use an isolated `lark-cli` home and must not reuse the default `~/.lark-cli`

## Run

Webhook mode:

```bash
node server.mjs
```

Local no-server mode:

```bash
node local-listener.mjs --control-config ../../../configs/config.us.yaml
python ../../../build.py listen-message-control --config configs/config.us.yaml
```

Local mode uses `lark-cli event +subscribe` for `im.message.receive_v1`, so it
does not need any public callback URL or tunnel. The Feishu app still needs that
event enabled and published in the Open Platform console.

When the machine must keep an older Feishu app under the default `~/.lark-cli`,
point the new app listener at an isolated `lark-cli` home:

```bash
export FEISHU_IM_LARK_CLI_HOME="$HOME/.feishu-im-newapp"
mkdir -p "$FEISHU_IM_LARK_CLI_HOME"
HOME="$FEISHU_IM_LARK_CLI_HOME" printf '%s' "$FEISHU_IM_APP_SECRET" | lark-cli config init --app-id "$FEISHU_IM_APP_ID" --app-secret-stdin --brand feishu
python ../../../build.py listen-message-control --config configs/config.us.yaml
```

## Local-only OpenClaw profile

The adapter reads optional profile files from `<repo>/.openclaw/` by default.
This directory is intentionally git-ignored, so the repo can ship the reading
mechanism without committing private operator wording, real chat examples,
reaction preferences, or personal memory.

Supported local files:

- `aliases.local.json`: private phrase expansion before `queue-resolve-action`
- `reply-phrases.local.json`: private overrides for adapter reply headings
- `reactions.local.json`: private Feishu emoji reaction choices by stage
- `persona.local.md`: local note text kept in the loaded profile for future chat rendering layers

Example local alias shape:

```json
{
  "aliases": [
    { "from": ["short private phrase"], "to": "canonical queue wording" }
  ]
}
```

Example reaction shape:

```json
{
  "received": "Get",
  "accepted": "OK",
  "completed": "OK"
}
```

Use `FEISHU_IM_LOCAL_PROFILE_DIR` or `OPENCLAW_LOCAL_PROFILE_DIR` to point at a
different local directory. Set `FEISHU_IM_DISABLE_LOCAL_PROFILE=true` when you
want the adapter to ignore all local profile files. Restart the adapter after
editing local profile files because they are loaded at process startup.

## Message reactions and context

Native Feishu message reactions are off by default. Set
`FEISHU_IM_ENABLE_MESSAGE_REACTIONS=true` only after the Feishu app has the
message reaction permission. The adapter reacts best-effort; a reaction API
failure is logged but does not block the normal thread reply.
When enabled, the default reaction for the initial `received` stage is `Get`,
so every accepted incoming message gets the same GET acknowledgement before
the adapter resolves or executes the request.

The state file also keeps short-lived conversation context per chat and sender.
Follow-ups such as `这个好了没` can reuse the last resolved `record_id` without
storing that context in git.
Execution requests such as build, trigger, rerun, or batch Draft requests never
append a previous `record_id`; they reuse only safe target hints such as model,
market, version, and Git_ref, then resolve fresh rows from the current Feishu
queue table. This lets follow-ups such as `我来补跑英语和法语` target the same
JE-1000F/EU/version context without accidentally rebuilding the old row.

Batch Draft requests are intentionally opt-in. The resolver only returns a
build batch when the message carries a broad selector such as `所有` / `全部` / `all`
and still narrows to a bounded queue set, for example `JE-1000F` + `欧规`.
Multi-row status queries such as `当前所有已构建文档链接` are handled as read-only
status batches and are never dispatched as builds.
Manual-index queries are also read-only. They use the `发布文档管理` Base view to
answer product/manual-link inventory and overview questions, while phrases that
include build-copy intent such as `输出JE-1000F的所有欧规说明书文案` stay on the
existing Build Draft queue path.
For batch status or link replies, the adapter sends one status summary without
embedded `Document link` URLs, then sends each unique artifact link as its own
follow-up text message. That keeps Feishu's document-link renderer on the same
path as a human sending one document link per message instead of flattening all
links into one plain-text block.
Both `输出JE-1000F的所有欧规说明书文案` and `构建JE-1000F的所有欧规说明书文案`
are treated as batch draft-build requests.
That phrase becomes a `Task_id` prefix such as `JE-1000F_EU_`; only rows whose
`Task_id` maps to `Build Draft Package` and whose `是否触发文档构建` is enabled are
launched. The adapter dispatches each matched row by `record_id` with
`queue-execute --no-wait`, throttling each dispatch by `FEISHU_IM_BATCH_DISPATCH_DELAY_MS`,
then stores a short-lived batch context containing `request_id`, `accepted_at`,
`action_name`, `queryText`, and the launched rows. Batch status follow-ups such
as `这个好了没` or document-link follow-ups such as `发` / `发一下` re-read each
stored `record_id` with `--fresh-since accepted_at` and classify rows as fresh
success/failure, stale result, or writeback pending.
If Feishu no longer returns a remembered `record_id`, the adapter reports that
row as not found, clears the stale context when no live rows remain, and does not
replay the old row payload from local memory.
The GitHub draft workflow scopes its
concurrency group by `queue_record_id`, so multiple rows from one batch do not
cancel each other while they are pending.
`最新` does not collapse batch Draft requests by `Document_Key`; the trigger
checkbox remains the eligibility gate for each language row.
`是否强制刷新数据` remains a build-time row input read by `process-build-queue`.

Cloud-doc review backport messages bypass the queue resolver only after a typed
request is detected. Use this shape:

```text
cloud-doc backport <Feishu cloud-doc URL> docs/_review/<model>/<region>/page/<page>.rst
cloud-doc backport <Feishu cloud-doc URL>
cloud-doc backport-pr reports/cloud_doc_backport/<run-id>/cloud_doc_backport_run.json
```

The source path is optional only for the IM adapter. When omitted, the adapter
extracts a target hint from the message text or cloud-doc title, for example
`manual_je2000f_eu_en_0.7`, then looks under the current checkout's
`docs/_review/<model>/<region>/`. It runs only when there is one safe source
candidate or one unique message-hint match; otherwise it replies with candidate
paths and asks for the explicit `docs/_review/...rst` source.

The default mode is dry-run: the adapter calls
`python tools/cloud_doc_backport.py run-review ...`, writes
`cloud_doc_backport_report.*`, `cloud_doc_backport_apply.*`, and
`cloud_doc_backport_run.*` under `reports/cloud_doc_backport/<run-id>/`, writes
`cloud_doc_backport_source_table_suggestions.*` for report-only data-like
deltas, and replies with the manifest/report paths plus
`source_table_suggestions`. The run is source-scoped: it reports only evidence
from the chosen `docs/_review/...rst` file and the matched cloud-doc section. For
headingless `00_preface.rst` pages, the runner automatically compares only the
cloud document preamble before the first heading, so later sections such as
Safety, Symbols, or App Setup cannot be misreported as preface residuals. The
chat reply includes the source scope, matched section, and a short
manifest-backed evidence list; it must not invent a broader reviewed/backfill
checklist. If the message includes `--write`, the adapter refuses it unless
`FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOW_WRITE=true`; write mode still only patches
guarded review prose and reports source-table suggestions without writing Feishu
source tables.
After a write run replies `PR_READY`, the operator can send the separate
`cloud-doc backport-pr .../cloud_doc_backport_run.json` message. The adapter
refuses that request unless `FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOW_PR_CREATE=true`;
the helper checks the manifest, refuses unrelated working-tree changes, commits
only the changed `docs/_review/...rst` source, and opens a draft PR. Local
`reports/cloud_doc_backport/...` files stay evidence and are not committed.

Freshness fields come from `build.py queue-query --fresh-since ...` and are
included in Document_link JSON rows as `freshness_status`, `result_built_at`,
`result_is_fresh`, and `build_started_at`. When a previous failed build remains
in `构建结果` after a new dispatch, the adapter reports `stale_result` or
`writeback_pending` instead of presenting that old failure as the current run.
The underlying `queue-query --json` response also includes `matched_count`,
`returned_count`, `limit`, and `truncated`, so broad table reads expose whether a
default limit hid rows that still exist in Feishu.

## ECS systemd

For a long-lived ECS deployment, use the service wrappers and unit examples in
[`deploy/systemd/`](deploy/systemd):

- [`deploy/systemd/README.md`](deploy/systemd/README.md)
- [`../../../../scripts/run_feishu_im_webhook_adapter_service.sh`](../../../../scripts/run_feishu_im_webhook_adapter_service.sh)
- [`../../../../scripts/run_feishu_im_cloudflared_service.sh`](../../../../scripts/run_feishu_im_cloudflared_service.sh)

Recommended production split:

- run the adapter under `systemd`
- run a named `cloudflared` tunnel under `systemd`
- point the Feishu callback URL at the named tunnel hostname

`trycloudflare.com` is acceptable for smoke tests, but not for a stable
callback URL after restarts.

## Test

```bash
npm test
```
