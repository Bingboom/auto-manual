# DingTalk Integration Skeleton

This package is the minimal landing zone for a future `dingtalk_openapi` phase2 provider.

Current scope:

- define stable module boundaries
- host the Phase 0 capability spike helpers
- keep DingTalk-specific auth, record, file, and workspace behavior out of queue orchestration modules until the capability spike is complete

This package is intentionally not wired into `build.py` yet.

Planned ownership:

- `auth.py`: token acquisition and permission failure handling
- `records.py`: queue and snapshot table reads and row writeback
- `files.py`: artifact upload and share-link resolution
- `workspace.py`: optional attach-to-container behavior
- `spike.py`: capability-spike checklist and helper entrypoint
- `spike_cli.py`: manual endpoint-driven smoke runner for token, list, update, and upload checks
- `contracts.py`: provider-facing data contracts

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
