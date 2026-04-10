# DingTalk Integration Skeleton

This package is the minimal landing zone for a future `dingtalk_openapi` phase2 provider.

Current scope:

- define stable module boundaries
- host the Phase 0 capability spike helpers
- prove the verified App-Only token flow behind a reusable helper
- keep DingTalk-specific auth, record, file, and workspace behavior out of queue orchestration modules until the capability spike is complete

This package is intentionally not wired into `build.py` yet.

Planned ownership:

- `auth.py`: token acquisition and permission failure handling
- `alidocs_session.py`: browser-session upload spike for the current DingTalk docs node flow
- `records.py`: queue and snapshot table reads and row writeback
- `files.py`: artifact upload and share-link resolution
- `workspace.py`: optional attach-to-container behavior
- `spike.py`: capability-spike checklist and helper entrypoint
- `spike_cli.py`: manual endpoint-driven smoke runner for token, list, update, and upload checks
- `contracts.py`: provider-facing data contracts

Current verified helpers:

- `auth.get_app_only_token(...)` reads `DINGTALK_CLIENT_ID`, `DINGTALK_CLIENT_SECRET`, and `DINGTALK_CORP_ID`, then calls the official App-Only token endpoint
- `workspace.parse_node_id_from_url(...)` extracts a DingTalk docs node ID from a normal `alidocs.dingtalk.com/i/nodes/...` URL so the target workspace can be configured before the upload API is wired
- `alidocs_session_upload_cli.py` is the current manual bridge for the observed browser-session upload chain: `uploadinfo -> OSS object upload -> commit -> node URL`
- `tools/process_build_queue.py` can now use that same browser-session chain as an optional artifact sink while still reading queue rows from Feishu and writing `Document link` back to Feishu

## Quick Smoke

For a manual Phase 0 smoke check, point the helper at a throwaway DingTalk table and run the combined `all` step:

```powershell
$env:DINGTALK_CLIENT_ID="..."
$env:DINGTALK_CLIENT_SECRET="..."
$env:DINGTALK_CORP_ID="..."
$env:DINGTALK_SPIKE_LIST_URL="https://api.dingtalk.com/..."
$env:DINGTALK_SPIKE_UPDATE_URL="https://api.dingtalk.com/..."
$env:DINGTALK_SPIKE_UPLOAD_URL="https://api.dingtalk.com/..."
python tools\dingtalk\spike_cli.py all --record-id rec_phase0_smoke --update-set smoke_checked=true --upload-file .tmp\phase0-smoke.docx --upload-file-id-path data.file_id --upload-share-url-path data.share_url
```

`all` runs `token -> list -> update -> upload` in sequence. Prefer an explicit `--record-id <stable_row_id>` for manual smoke runs. Only use `--record-id-path ... --allow-listed-record-id` when your list call is already filtered to exactly one throwaway row.

## Queue Artifact Sink

The current repo-integrated DingTalk queue sink is `dingtalk_alidocs_session`.

It is selected with:

```powershell
$env:AUTO_MANUAL_ARTIFACT_SINK_PROVIDER="dingtalk_alidocs_session"
$env:DINGTALK_DOCS_TARGET_NODE_URL="https://alidocs.dingtalk.com/i/nodes/..."
$env:DINGTALK_DOCS_A_TOKEN="..."
$env:DINGTALK_DOCS_XSRF_TOKEN="..."
$env:DINGTALK_DOCS_COOKIE="..."
$env:DINGTALK_DOCS_BX_V="2.5.36"
```

Environment meanings:

- `AUTO_MANUAL_ARTIFACT_SINK_PROVIDER`: switch `process-build-queue` from the default `lark_drive` sink to the DingTalk browser-session sink
- `DINGTALK_DOCS_TARGET_NODE_URL`: target AliDocs folder or node that should receive generated `.docx` files
- `DINGTALK_DOCS_A_TOKEN`: current browser `a-token` header value
- `DINGTALK_DOCS_XSRF_TOKEN`: current `x-xsrf-token` header value
- `DINGTALK_DOCS_COOKIE`: current browser cookie string for `alidocs.dingtalk.com`
- `DINGTALK_DOCS_BX_V`: optional browser `bx-v` header override; defaults to `2.5.36`

This queue sink follows the same observed AliDocs browser-session chain used by the manual spike helper:

1. `uploadinfo`
2. OSS object upload
3. `commit`
4. DingTalk node URL writeback

The worker Python environment also needs `oss2`; it is now included in [`requirements.txt`](../../requirements.txt).

This is separate from the App-Only token helpers in `auth.py`. The current queue sink depends on a valid AliDocs browser session, so it is intended for local/operator workers unless you have a secure way to inject the same session into automation.
