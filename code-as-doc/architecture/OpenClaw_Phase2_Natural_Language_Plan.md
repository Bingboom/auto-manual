# OpenClaw Phase 2 Natural Language Plan

Updated: 2026-04-12

## 1. Goal

Phase 2 extends the existing OpenClaw Phase 1 control layer from:

- explicit slash commands with manual `record_id`

to:

- natural-language operator requests
- Feishu queue row resolution
- deterministic workflow dispatch
- status / link / failure feedback in the same conversation

## 1.1 Current Repo Status

As of 2026-04-12, the repo-local Phase 2 surface is implemented:

- `build.py queue-query` resolves candidate queue rows
- `build.py queue-resolve-action` turns one natural-language ask into a bounded action contract
- `build.py queue-execute` dispatches the matching `main`-owned worker and waits for the final row state
- [`../../integrations/openclaw/feishu-im-webhook-adapter/`](../../integrations/openclaw/feishu-im-webhook-adapter/) provides the repo-external Feishu IM ingress layer for the same control surface

The main remaining gaps are deployment hardening, shared runtime state, and encrypted Feishu callback support.

## 2. Required Flow

The required Phase 2 flow is:

```text
Feishu operator natural language
  -> OpenClaw agent
  -> resolve target row from Feishu queue tables
  -> derive record_id + workflow intent
  -> dispatch the existing main-owned GitHub workflow
  -> read tracked run status and Feishu writeback fields
  -> reply with status / link / failure summary
```

The execution plane does not change:

- OpenClaw is still the operator entrypoint
- GitHub Actions is still the execution plane
- Feishu phase2 tables are still the source of truth and writeback surface

## 3. Phase 2 Deliverables

### 3.1 Query Surface

Add one deterministic queue query entrypoint:

- `python3 build.py queue-query ...`

This query surface must support:

- `Document_link`
- `Review Init`
- exact filters for `Document_ID`, `Document_Key`, `Build_family`, `Lang`, `Version`
- workflow intent filters for:
  - `start-review`
  - `build-draft-package`
  - `publish`
- machine-readable output for agent use

### 3.2 Control Surface

Add one reusable control CLI on top of the existing OpenClaw Phase 1 modules:

- `node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch ...`
- `node integrations/openclaw/auto-manual-control-layer/cli.mjs status ...`

This CLI should:

- dispatch only on `main`
- reuse the Phase 1 GitHub client and state store
- support local operator auth through `GITHUB_TOKEN` or `gh auth token`

### 3.3 Repo-Local Agent Guidance

Add repo-local guidance so the OpenClaw agent can consistently:

1. resolve the correct queue row
2. stop on ambiguity
3. dispatch the correct workflow
4. report `构建结果`, `Document link`, `PR_url`, or run URL

## 4. Operator Intents In Scope

Phase 2 must cover these first-class intents:

1. 生成草稿 / Build Draft Package
2. 发布 / Publish
3. 拉进 Review / Start Review
4. 查询最新链接
5. 查询当前状态
6. 查询失败原因

Batch execution can remain a later extension after single-row resolution is stable.

## 5. Data Boundary

Keep this boundary explicit:

- Feishu = queue rows, state, structured data, artifact link writeback
- GitHub Actions = actual review/build/publish execution
- OpenClaw = natural-language control plane

## 6. Explicit Non-Goal

`Document link_dd` is not part of Phase 2.

If DingTalk dual-write is required later, treat it as a separate V2 extension.
Phase 2 should continue to assume:

- one required link field: `Document link`
- that field may hold either a Feishu URL or a DingTalk node URL depending on the active sink

## 7. Acceptance Criteria

Phase 2 is acceptable when an operator can say things like:

- "帮我生成 JE-1000F US 0.3 草稿"
- "把 JE-1000F JP 0.3 发布出去"
- "这个型号最新链接发我"
- "为什么这次构建失败"

and OpenClaw can:

1. resolve the correct row from Feishu
2. avoid inventing a `record_id`
3. dispatch the right Phase 1 workflow
4. return row-level status and link information without leaving the chat
