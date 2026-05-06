# BlockClaw Auto Manual Control Layer

This package is the OpenClaw-side bridge for BlockClaw, the repository's Auto-Manual document-build operator.
BlockClaw is the repo-specific identity that helps operators work with content blocks, Feishu queue rows, review bundles, draft packages, and publish artifacts.

It does not execute `build.py` directly.
It only dispatches the existing `main`-owned GitHub workflows and reports their status back into OpenClaw as BlockClaw.

For local Phase 2 natural-language orchestration, the same package also ships a repo-local CLI:

```bash
node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch start-review rec_xxx
node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch build-draft rec_xxx
node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch publish rec_xxx confirm
node integrations/openclaw/auto-manual-control-layer/cli.mjs status last
```

That CLI reuses the same GitHub dispatch/status modules as the plugin.
Dispatch replies include `accepted_at`, `run_id`, and `run` when GitHub exposes
the workflow run. `queue-execute` passes that `accepted_at` back into
`queue-query --fresh-since` so OpenClaw can tell whether the Feishu row writeback
belongs to the current dispatch or is an older result from a previous run.
Dispatch no longer hard-fails just because the local repo checkout has not run
`npm install` for this package; metadata artifact parsing is treated as an
optional status enrichment step instead of a dispatch-time requirement.

## Identity

Use **BlockClaw** as the operator-facing name for this repo integration.
Use **OpenClaw** when referring to the underlying runtime, gateway, or plugin host.

BlockClaw currently handles bounded manual operations: queue lookup, Start Review, Build Draft Package, Publish with confirmation, run-status lookup, failure explanation, and manual wording helpers that support those flows. It should not invent queue state or bypass `build.py`, Feishu phase2 tables, or the `main`-owned GitHub workers.

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

Every dispatch sends:

- `queue_record_id = rec_xxx`

The control layer treats the selected Feishu `record_id` as the execution identity for `start-review`, `build-draft`, and `publish`. Queue lookup can also use the optional `Task_id` field, conventionally `Document_ID + "_" + Workflow_action`, to disambiguate same-document rows before dispatch.
For status freshness, the repo-local queue layer records the dispatch acceptance
time and returns `freshness_status` with the final row fields. If the workflow
has completed but Feishu still shows a pre-dispatch `FAILED` or `SUCCESS`, the
reply should surface `stale_result` or `writeback_pending` instead of treating
the old value as the current run result.

The Feishu IM adapter can sit above this single-record bridge for config-scoped batch Draft asks. For example, `输出JE-1000F的所有欧规说明书文案`, `构建JE-1000F的所有欧规说明书文案`, `基于配置构建JE-1000F的欧规`, or the implicit-all form `构建JE-1000F的欧规说明书文案` resolves the matching triggered `Task_id` rows from the Base queue, then calls the same `build-draft <record_id>` dispatch path once per row. When no market is named, asks such as `构建JE-1000F说明书文案` use the broader `Task_id` prefix `JE-1000F_`, so every triggered Build Draft Package row for that model is eligible across markets. Versioned market-level asks such as `构建 JE-1000F_EU_1.0 的欧规说明书文案` add `Version=1.0` while still matching each configured language row. The GitHub draft workflow also scopes concurrency by `queue_record_id`, so different rows from the same batch are not cancelled as duplicate pending work.

The repo-local `queue-execute` wrapper also treats a `Start Review` row that is already `InReview` with `Git_ref` as completed and returns it without a new dispatch. If an older caller still dispatches one explicit completed record, the GitHub worker exits successfully instead of reporting a false no-pending failure.

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
