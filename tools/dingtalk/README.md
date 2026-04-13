# DingTalk Integration

This package is the repo-owned DingTalk integration surface for the current
hybrid Feishu queue flow.

Current maintained scope:

- Feishu phase2 tables remain the source of truth for queue rows and writeback
- `build.py process-build-queue` remains the execution entrypoint
- DingTalk is an optional artifact destination:
  - Feishu/wiki primary + DingTalk mirror
  - DingTalk primary replace mode when explicitly requested
- the current DingTalk upload path is the observed AliDocs browser-session
  chain, not a public OpenAPI knowledge-base upload provider

Current modules:

- `auth.py`: verified App-Only token helper for future endpoint-based work
- `workspace.py`: DingTalk docs node parsing helpers
- `alidocs_session.py`: current browser-session upload implementation
- `alidocs_session_upload_cli.py`: manual upload smoke helper for the same chain
- `spike.py` / `spike_cli.py`: endpoint-driven capability spike helpers kept for
  future provider work

## Queue Integration

The current queue integration is already wired into the repo:

- [`../queue_artifact_sink.py`](../queue_artifact_sink.py) resolves the primary
  artifact sink and optional mirror sink
- [`../queue_group_processing.py`](../queue_group_processing.py) publishes the
  built DOCX, optionally mirrors it to DingTalk, and writes `dingtalk_sync=*`
  status notes
- [`../process_build_queue.py`](../process_build_queue.py) and
  [`../process_build_queue_services.py`](../process_build_queue_services.py)
  provide the CLI/runtime entrypoint

The current DingTalk provider id is `dingtalk_alidocs_session`.

## Execution Modes

Feishu/wiki primary only:

```powershell
$env:AUTO_MANUAL_ARTIFACT_SINK_PROVIDER="lark_drive"
$env:AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER=""
```

Feishu/wiki primary + DingTalk mirror:

```powershell
$env:AUTO_MANUAL_ARTIFACT_SINK_PROVIDER="lark_drive"
$env:AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER="dingtalk_alidocs_session"
```

DingTalk primary replace mode:

```powershell
$env:AUTO_MANUAL_ARTIFACT_SINK_PROVIDER="dingtalk_alidocs_session"
$env:AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER=""
```

For the maintained hybrid path, prefer Feishu/wiki primary plus DingTalk mirror.
Only use DingTalk primary replace mode when you intentionally want the canonical
artifact link to point at DingTalk for that worker.

## Session Inputs

Global browser-session envs:

- `DINGTALK_DOCS_TARGET_NODE_URL`
- `DINGTALK_DOCS_A_TOKEN`
- `DINGTALK_DOCS_XSRF_TOKEN`
- `DINGTALK_DOCS_COOKIE`
- optional `DINGTALK_DOCS_BX_V`

Per-operator session registry:

- `AUTO_MANUAL_DINGTALK_SESSION_ROOT`
- default root: `~/.auto-manual/dingtalk-sessions`
- when the queue row carries `operator_union_id`, the worker looks for
  `<session_root>/<operator_union_id>.json`

Session-file payload keys:

- `a_token` or `aToken`
- `xsrf_token`, `xsrfToken`, or `x_xsrf_token`
- `cookie`
- optional `bx_version` or `bxVersion`

Resolution order:

1. if `operator_union_id` is present and
   `<session_root>/<operator_union_id>.json` exists, use that session
2. otherwise fall back to the global `DINGTALK_DOCS_*` env values

This lets one local/operator worker mirror different rows to DingTalk without
sharing one global browser session across every row.

## Row-Level Queue Contract

Current DingTalk-related queue fields:

- `Document link`: canonical writeback field
- `Document link_dd`: optional DingTalk supplemental writeback field
- `是否上传钉钉`: optional row-level DingTalk gate
- `DingTalk_target_node_url`: optional row-level DingTalk target override
- `operator_union_id`: optional session-file selector for per-operator uploads

Current behavior:

- if the worker runs in mirror mode and the row has `是否上传钉钉`, checked rows
  also sync DingTalk and unchecked rows stay Feishu/wiki-only
- if the row does not have `是否上传钉钉`, the worker follows the current global
  worker mode for that whole row
- if the row has `DingTalk_target_node_url`, that row-level target overrides the
  global `DINGTALK_DOCS_TARGET_NODE_URL`
- if `Document link_dd` exists, DingTalk mirror or DingTalk primary mode writes
  the DingTalk node URL there
- `构建结果` may include `dingtalk_sync=ok|failed|skipped`

## GitHub Worker Behavior

The remote Draft/Publish workflows keep Feishu/wiki as the primary sink:

- [`../../.github/workflows/feishu-draft-build-queue.yml`](../../.github/workflows/feishu-draft-build-queue.yml)
- [`../../.github/workflows/feishu-build-queue.yml`](../../.github/workflows/feishu-build-queue.yml)

When GitHub Secrets provide the DingTalk browser-session values, those workers
enable `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER=dingtalk_alidocs_session`.
They do not auto-switch the primary sink to DingTalk.

## Manual Smoke

For a local smoke run:

```powershell
$env:AUTO_MANUAL_ARTIFACT_SINK_PROVIDER="lark_drive"
$env:AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER="dingtalk_alidocs_session"
powershell -ExecutionPolicy Bypass -File scripts\process_build_queue_dingtalk.ps1 --record-id <record_id>
```

For a direct upload helper smoke:

```powershell
python tools\dingtalk\alidocs_session_upload_cli.py `
  --target-node-url https://alidocs.dingtalk.com/i/nodes/... `
  --file .tmp\phase0-smoke.docx
```

## Operational Gaps

The main remaining gaps are operational, not boundary discovery:

- browser-session rotation and storage hygiene
- live GitHub worker smoke validation with real secrets
- future migration to an app-only or officially supported DingTalk upload path
