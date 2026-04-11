# Auto Manual OpenClaw Control Layer

This package is the OpenClaw-side bridge for the repository's Phase 1 manual-ops flow.

It does not execute `build.py` directly.
It only dispatches the existing `main`-owned GitHub workflows and reports their status back into OpenClaw.

## Commands

- `/start-review <review_init_record_id>`
- `/build-draft <document_link_record_id>`
- `/publish <document_link_record_id>`
- `/manual-status [run_id|last]`

## Expected GitHub Workflow Inputs

The plugin dispatches:

- `feishu-start-review.yml`
- `feishu-draft-build-queue.yml`
- `feishu-build-queue.yml`

Every dispatch uses:

- `ref = main` by default
- `trigger_source = openclaw`
- `queue_record_id = rec_xxx`
- `openclaw_dispatch_nonce = <uuid>`

## Minimal Plugin Config

```json
{
  "plugins": {
    "entries": {
      "auto-manual-control-layer": {
        "enabled": true,
        "config": {
          "githubToken": "ghp_xxx",
          "repoOwner": "your-org",
          "repoName": "auto-manual",
          "defaultBranch": "main",
          "stateFile": "runtime/auto-manual-control-layer-state.json"
        }
      }
    }
  }
}
```

## Install Notes

1. Install the package from this directory in OpenClaw.
2. Configure the GitHub token with Actions read/write scope for the repository.
3. Keep the runtime state file outside Git if you override `stateFile`.

## Local Test

```bash
npm install
npm test
```
