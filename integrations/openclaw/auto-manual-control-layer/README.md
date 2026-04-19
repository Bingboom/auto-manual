# Auto Manual OpenClaw Control Layer

This package is the OpenClaw-side bridge for the repository's Phase 1 manual-ops flow.

It does not execute `build.py` directly.
It only dispatches the existing `main`-owned GitHub workflows and reports their status back into OpenClaw.

For local Phase 2 natural-language orchestration, the same package also ships a repo-local CLI:

```bash
node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch build-draft rec_xxx
node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch publish rec_xxx confirm
node integrations/openclaw/auto-manual-control-layer/cli.mjs status last
```

That CLI reuses the same GitHub dispatch/status modules as the plugin.
Dispatch no longer hard-fails just because the local repo checkout has not run
`npm install` for this package; metadata artifact parsing is treated as an
optional status enrichment step instead of a dispatch-time requirement.

## Commands

- `/start-review <review_init_record_id>`
- `/build-draft <document_link_record_id>`
- `/publish <document_link_record_id> confirm`
- `/manual-status [run_id|last]`

## Expected GitHub Workflow Inputs

The plugin dispatches:

- `feishu-start-review.yml`
- `feishu-draft-build-queue.yml`
- `feishu-build-queue.yml`

Every dispatch uses:

- `ref = main` by default
- `trigger_source = openclaw`
- `openclaw_dispatch_nonce = <uuid>`

Record-scoped dispatches also send:

- `queue_record_id = rec_xxx`

For `build-draft`, the control layer now reuses one short-lived shared GitHub queue worker when several language rows are dispatched back-to-back. The worker is still triggered on `main`, but the workflow dispatch itself is sent without one fixed `queue_record_id` so it can drain the pending Build Draft Package rows together instead of launching one competing Actions run per language.

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

Installing the package dependencies is still recommended for local development
and full status-metadata coverage.
