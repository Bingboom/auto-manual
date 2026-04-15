# OpenClaw Phase 1 Implementation Checklist

Updated: 2026-04-10

Archived note:

- this rollout checklist is kept for implementation history only
- the repo now has the Phase 1 command surface and the later Phase 2 natural-language surface
- use [`../BOOTSTRAP.md`](../BOOTSTRAP.md), [`../integrations/openclaw/README.md`](../integrations/openclaw/README.md), and [`architecture/OpenClaw_Control_Layer_Plan.md`](architecture/OpenClaw_Control_Layer_Plan.md) for current behavior

## 1. Role

This file is the execution checklist for Phase 1 of the OpenClaw control-layer rollout.

It refines:

- [`architecture/OpenClaw_Control_Layer_Plan.md`](architecture/OpenClaw_Control_Layer_Plan.md)

Use this file when the goal is:

- defining the first real operator command surface
- wiring OpenClaw to GitHub `workflow_dispatch`
- defining the minimum status-return contract

Do not use this file as:

- the long-term architecture document
- the current user workflow guide
- the full maintainer command reference

## 2. Decision Summary

Phase 1 should make these decisions explicit:

1. OpenClaw is the operator entrypoint, not the build executor.
2. GitHub Actions remains the only remote execution surface.
3. Feishu phase2 tables remain the source of truth for queue rows and writeback.
4. No ACP, no direct repo execution, and no `FEISHU_*` build secrets should move into OpenClaw.
5. The OpenClaw side should be one small plugin or extension that registers commands and calls GitHub's REST API.

## 3. Official Reference Surface

OpenClaw references:

- Feishu bot channel via WebSocket:
  [OpenClaw Feishu channel](https://docs.openclaw.ai/channels/feishu)
- custom slash commands through plugins:
  [OpenClaw plugins / command registration](https://docs.openclaw.ai/plugins)
- slash-command behavior and authorization:
  [OpenClaw slash commands](https://docs.openclaw.ai/tools/slash-commands)
- webhook routes if an external callback path becomes necessary later:
  [OpenClaw webhooks plugin](https://docs.openclaw.ai/plugins/webhooks)

GitHub references:

- workflow dispatch endpoint:
  [GitHub REST workflows API](https://docs.github.com/en/rest/actions/workflows)
- workflow run status and logs:
  [GitHub REST workflow runs API](https://docs.github.com/en/rest/actions/workflow-runs)
- workflow-run artifacts:
  [GitHub REST artifacts API](https://docs.github.com/en/rest/actions/artifacts)

## 4. Phase 1 Scope

Phase 1 should ship exactly four commands:

- `/start-review <review_init_record_id>`
- `/build-draft <document_link_record_id>`
- `/publish <document_link_record_id>`
- `/manual-status [run_id|last]`

Why `/manual-status` instead of `/status`:

- OpenClaw already has a built-in `/status`
- plugin commands cannot override reserved command names such as `status`

That makes `/manual-status` the safer Phase 1 command name.

## 5. Phase 1 Deliverables

### 5.1 OpenClaw Deliverables

- one plugin or extension package for this repo workflow
- four registered commands
- one GitHub API client wrapper
- one lightweight run-state store
- one status renderer for Feishu replies

### 5.2 Repo Deliverables

- one machine-readable implementation checklist in this repo
- one corrected plan doc that reflects the final command names
- one documented mapping from OpenClaw commands to existing GitHub workflow files
- one documented gap list for data that is still only visible in GitHub step summaries

### 5.3 Explicit Non-Deliverables

- no new `build.py` commands
- no repo-side replacement for `process-build-queue`
- no OpenClaw-owned queue router
- no OpenClaw-owned Feishu table writeback

## 6. Command Contract

### 6.1 `/start-review <review_init_record_id>`

Intent:

- wake the existing Start Review worker for one Feishu row

GitHub workflow:

- [`.github/workflows/feishu-start-review.yml`](../.github/workflows/feishu-start-review.yml)

Dispatch payload:

```json
{
  "ref": "main",
  "inputs": {
    "trigger_source": "openclaw",
    "queue_record_id": "rec_xxx"
  }
}
```

Required operator input:

- one `review_init` record id

OpenClaw-side validation:

- reject empty args
- reject non-`rec...` style ids
- reject attempts to choose another workflow ref

Immediate reply fields:

- command name
- workflow file
- record id
- run URL if available immediately

### 6.2 `/build-draft <document_link_record_id>`

Intent:

- wake the existing Build Draft Package worker for one Feishu queue row

GitHub workflow:

- [`.github/workflows/feishu-draft-build-queue.yml`](../.github/workflows/feishu-draft-build-queue.yml)

Dispatch payload:

```json
{
  "ref": "main",
  "inputs": {
    "trigger_source": "openclaw",
    "queue_record_id": "rec_xxx"
  }
}
```

Required operator input:

- one `Document_link` record id

OpenClaw-side validation:

- reject empty args
- reject non-`rec...` style ids
- remind the operator that the target row must already carry `Workflow_action = Build Draft Package`
- remind the operator that `Git_ref` must already exist on the row

Immediate reply fields:

- command name
- workflow file
- record id
- run URL if available immediately

### 6.3 `/publish <document_link_record_id>`

Intent:

- wake the existing Publish worker for one Feishu queue row

GitHub workflow:

- [`.github/workflows/feishu-build-queue.yml`](../.github/workflows/feishu-build-queue.yml)

Dispatch payload:

```json
{
  "ref": "main",
  "inputs": {
    "trigger_source": "openclaw",
    "queue_record_id": "rec_xxx"
  }
}
```

Required operator input:

- one `Document_link` record id

OpenClaw-side validation:

- reject empty args
- reject non-`rec...` style ids
- remind the operator that the row should already represent `Workflow_action = Publish`
- remind the operator that `Git_ref` still controls the real publish source when present

Immediate reply fields:

- command name
- workflow file
- record id
- run URL if available immediately

### 6.4 `/manual-status [run_id|last]`

Intent:

- let the operator ask for the latest known GitHub run state without opening GitHub

GitHub endpoints used:

- `GET /repos/{owner}/{repo}/actions/runs/{run_id}`
- `GET /repos/{owner}/{repo}/actions/runs/{run_id}/artifacts`

Accepted arguments:

- `last`
- one explicit numeric GitHub `run_id`
- no args, treated as `last`

Output fields:

- workflow name
- run id
- `status`
- `conclusion`
- run URL
- artifact names and download URLs when present
- publish URL when present in tracked metadata

## 7. GitHub Dispatch Interface

The OpenClaw side should call GitHub's workflow-dispatch endpoint:

- `POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches`

Required token capability:

- GitHub "Actions" repository permission: `write`

Required request headers:

- `Accept: application/vnd.github+json`
- `Authorization: Bearer <token>`
- `X-GitHub-Api-Version: 2026-03-10`

Required request body:

- `ref: "main"`
- `inputs.trigger_source: "openclaw"`
- `inputs.queue_record_id: "<record_id>"`
- `inputs.openclaw_dispatch_nonce: "<uuid>"`

Implementation note:

- GitHub now documents a response with `workflow_run_id`, `run_url`, and `html_url` when `return_run_details` is enabled in the request path/version
- if the chosen GitHub client path cannot rely on that behavior yet, Phase 1 should still dispatch successfully and fall back to `/manual-status` for the first status lookup

## 8. Status Return Interface

Phase 1 should separate status return into two layers.

### 8.1 Immediate Command Acknowledgement

Every dispatch command should answer immediately in the Feishu thread with:

```json
{
  "ok": true,
  "command": "start-review",
  "workflow": "feishu-start-review.yml",
  "record_id": "rec_xxx",
  "run_id": 123456789,
  "run_url": "https://github.com/OWNER/REPO/actions/runs/123456789",
  "source": "openclaw"
}
```

If `run_id` is not available immediately:

- still reply with `ok=true`
- include the workflow name and record id
- instruct the operator to use `/manual-status last`

### 8.2 Manual Status Lookup

`/manual-status` should map GitHub state into operator-facing text:

- `queued` / `in_progress` -> running
- `completed + success` -> success
- `completed + failure` -> failure
- `completed + cancelled` -> cancelled
- `completed + timed_out` -> timed out

For completed runs, return:

- artifact summary
- final conclusion
- publish URL when available

### 8.3 Automatic Completion Push

This is optional for the first cut of Phase 1.

If the OpenClaw runtime implementation can safely poll in the background and reply into the same thread, enable:

- started message
- completed message
- failed message

If not:

- keep `/manual-status` as the supported Phase 1 status-return path
- defer background completion push to Phase 2

## 9. Artifact And Publish Metadata Contract

Current workflow artifact names are already stable enough for Phase 1:

- `feishu-start-review-output`
- `feishu-draft-build-queue-output`
- `feishu-build-queue-output`
- `openclaw-run-metadata`

Current repo implementation:

- each worker writes one small JSON status file through [`../integrations/openclaw/scripts/write_workflow_run_metadata.py`](../integrations/openclaw/scripts/write_workflow_run_metadata.py)
- that file is uploaded as `openclaw-run-metadata`
- the publish worker now includes the Vercel `publish_url` in that metadata when the deploy step returns one

## 10. OpenClaw Plugin Shape

Recommended Phase 1 shape:

- one small custom plugin
- use `api.registerCommand(...)` for the four commands
- do not use ACP
- do not use TaskFlow webhooks for the main dispatch path
- current repo package path: [`../integrations/openclaw/auto-manual-control-layer/`](../integrations/openclaw/auto-manual-control-layer)

Why this is the preferred shape:

- plugin commands are processed directly by the Gateway
- they can return immediate operator-facing text without invoking the AI agent
- they are global across channels

Configuration items the plugin should accept:

- `github.owner`
- `github.repo`
- `github.token` or token reference
- `github.defaultRef`
- `commands.statusName` if the team wants a different non-reserved command name later

## 11. Phase 1 Step-By-Step Checklist

### 11.1 OpenClaw Gateway And Channel

- [ ] Install and configure OpenClaw Gateway
- [ ] Enable the Feishu channel
- [ ] Pair and authorize the operator account(s)
- [ ] Verify slash/text command parsing is enabled for the target channel

### 11.2 Plugin Bootstrap

- [x] Create one custom OpenClaw plugin for the repo workflow
- [x] Register four commands:
  - `/start-review`
  - `/build-draft`
  - `/publish`
  - `/manual-status`
- [x] Ensure the command handler requires authorized senders

### 11.3 GitHub Client

- [x] Add one GitHub client wrapper for:
  - workflow dispatch
  - get workflow run
  - list workflow run artifacts
- [x] Store the GitHub token outside repo code
- [x] Use Actions `write` permission for dispatch
- [x] Use Actions `read` permission for status/artifact queries

### 11.4 Run Correlation

- [x] Persist the last tracked `record_id -> workflow -> run_id`
- [x] If immediate `run_id` is unavailable, persist at least:
  - dispatch timestamp
  - workflow name
  - record id
- [x] Make `/manual-status last` resolve against that stored state

### 11.5 Status Rendering

- [x] Implement one shared renderer for:
  - queued
  - running
  - success
  - failure
  - cancelled
- [x] Include artifact names when the run is complete
- [x] Treat publish URL as optional until the workflow exposes it cleanly

### 11.6 Repo Workflow Hardening

- [x] Confirm all three workflows still accept:
  - `trigger_source`
  - `queue_record_id`
- [x] Add `openclaw_dispatch_nonce` as the repo-owned correlation input
- [x] Fix the Start Review doc mismatch around `FEISHU_PHASE2_DOCUMENT_LINK_*` vs `FEISHU_PHASE2_REVIEW_INIT_*`
- [x] Add a machine-readable `publish_url` path in Phase 1 metadata when the deploy step exposes one

### 11.7 Operator Documentation

- [x] Update the OpenClaw plan doc if command names change again
- [x] Update maintainer docs after the OpenClaw command surface is actually live
- [x] Keep the current repo docs honest about what is planned versus what is already deployed

## 12. Validation Checklist

### 12.1 Command Validation

- [ ] `/start-review rec_xxx` dispatches only `feishu-start-review.yml`
- [ ] `/build-draft rec_xxx` dispatches only `feishu-draft-build-queue.yml`
- [ ] `/publish rec_xxx` dispatches only `feishu-build-queue.yml`
- [ ] `/manual-status last` returns a valid run summary after a dispatch

### 12.2 Branch Safety Validation

- [ ] every dispatch uses `ref=main`
- [ ] no command exposes arbitrary workflow refs
- [ ] no command exposes arbitrary workflow file names

### 12.3 Operator Experience Validation

- [ ] the immediate reply always includes the chosen workflow and record id
- [ ] a failed dispatch returns a readable error without leaking tokens
- [ ] an operator can get the current run URL without opening the OpenClaw host logs

## 13. Decision Rule

Phase 1 is complete when:

1. Operators can wake the three existing GitHub workers from one OpenClaw chat surface.
2. The command set stays limited to the current queue semantics instead of inventing a second build router.
3. Operators can retrieve run state through `/manual-status` even if automatic completion push is deferred.
4. No build/runtime secrets move from GitHub Actions into OpenClaw.
