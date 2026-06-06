# Feishu Message OpenClaw Control Layer Plan

Updated: 2026-04-11

Superseded note:

- this plan predates the repo-local Feishu IM webhook adapter and the consolidated OpenClaw control-layer doc
- keep it only as implementation history
- use [`Control_Orchestration_Strategy.md`](../Control_Orchestration_Strategy.md), [`../../BOOTSTRAP.md`](../../../agent/BOOTSTRAP.md), and [`../../integrations/openclaw/README.md`](../../../integrations/openclaw/README.md) for current behavior

## 1. Role

This file describes the integration plan for a Feishu-message-driven natural-language
control layer powered by OpenClaw.

Scope of this plan:

- keep Feishu phase2 tables and queue rows as the source of truth and writeback surface
- keep the current `build.py`, queue workers, and GitHub-hosted workflows as the execution engine
- add a controlled message layer that:
  - receives Feishu IM messages
  - uses OpenClaw to map natural language into a bounded action contract
  - triggers the existing review/build/publish workers
  - replies with status fields grounded in queue or review-init writeback

This is not a build-core rewrite.
It is a control-layer integration plan on top of the existing repo workflow.

## 2. Current Repo Baseline

The repository already has the low-level execution pieces needed for this control layer:

- Feishu phase2 tables already act as structured content and workflow state
- `process-review-start-queue` already supports `Start Review` and writes back `Git_ref`, `PR_url`, and `Review_status`
- `process-build-queue` already supports `Build Draft Package` and `Publish` and writes back build result, link, and local output path fields
- GitHub-hosted workers already exist for:
  - [`../../.github/workflows/feishu-start-review.yml`](../../../.github/workflows/feishu-start-review.yml)
  - [`../../.github/workflows/feishu-draft-build-queue.yml`](../../../.github/workflows/feishu-draft-build-queue.yml)
  - [`../../.github/workflows/feishu-build-queue.yml`](../../../.github/workflows/feishu-build-queue.yml)
- immediate execution can already be accelerated by Feishu automation plus `workflow_dispatch`

What did not exist when this draft was written:

- no Feishu IM webhook adapter in-repo yet
- no natural-language intent schema yet
- no OpenClaw control adapter yet
- no message reply formatter yet
- no bounded confirmation flow for chat-triggered publish yet

## 3. Stage Assessment

At the whole-system level, Hello-Docs is already in Stage 2 of the strategy model:

- CMS or multidimensional-table workflow state is outside the repo
- the repo still owns templates, assembly, validation, rendering, and release tooling
- builds consume snapshots and queue rows rather than live free-form content

See:

- [`System Evolution Strategy.md`](../System%20Evolution%20Strategy.md)

At the message-control level, this capability is still at Phase 0:

- the execution engine exists
- operator workflow is still table-edit-driven
- no chat-native ingress exists
- no bounded NL action translator exists
- no chat-native status reply exists

In short:

- system stage: `Stage 2`
- message control stage: `Phase 0 / not started`

## 4. Why This Should Be The Next Layer

The current queue and review flows are stable enough that the next leverage point is no longer
another build-pipeline refactor.
The missing layer is operator control ergonomics.

Feishu message control is only worth adding if it reuses the current queue and writeback
contracts.
If it invents a second task model, it will split status truth and increase operator confusion.

## 5. Target V1 Outcome

An operator should be able to send a Feishu message such as:

- `start review for JE-1000F us-merged`
- `build draft package for JE-1000F us-merged from branch feature/review-123`
- `publish JE-1000F us-merged version 0.2 from branch feature/review-123`
- `what is the latest status for document 12345`

OpenClaw should turn that message into a structured action, route it through the existing
queue or review workers, and reply with authoritative status fields.

## 6. Explicit Non-Goals

This plan does not require:

- replacing Feishu tables with message-only state
- letting the model emit arbitrary shell or free-form CLI commands
- changing `build.py` command semantics
- bypassing queue or review-init tables for actions that already have a stable writeback contract
- moving review/build execution into the chat service itself
- treating chat history as the system of record for build state

## 7. Recommended Control Model

### 7.1 Use Chat As The Intent Surface, Not As The Build Engine

Recommended flow:

```text
Feishu IM
  -> OpenClaw controller
  -> structured action
  -> queue-row upsert or review-init upsert
  -> existing GitHub workflow or queue worker
  -> Feishu table writeback
  -> reply formatter
```

### 7.2 Keep Feishu Tables As The Audit Surface

The message layer should not invent a parallel task database.

For write actions, the source of truth should remain:

- review-init rows for `start_review`
- `Document_link` rows for `build_draft_package`
- `Document_link` rows for `publish`

### 7.3 Keep Execution Bounded To Existing Actions

OpenClaw should resolve only a small action set:

- `query_status`
- `start_review`
- `build_draft_package`
- `publish`

Everything else should fail closed with a clarification reply.

## 8. Target Architecture

```text
Feishu IM webhook
  -> OpenClaw message gateway
  -> intent resolver
  -> action normalizer
  -> execution adapter
       -> review-init row upsert + feishu-start-review.yml
       -> Document_link row upsert + feishu-draft-build-queue.yml
       -> Document_link row upsert + feishu-build-queue.yml
  -> status reader
  -> reply formatter
```

Recommended ownership split:

- OpenClaw service owns:
  - Feishu webhook ingress
  - user identity mapping
  - conversation state
  - clarification prompts
  - confirmation prompts
  - workflow dispatch credentials
- this repo owns:
  - the build engine
  - queue and review-init contracts
  - action semantics
  - status fields and writeback rules

Even if both parts temporarily live in one repository, the boundary should stay clear.

## 9. Structured Action Contract

### 9.1 `query_status`

Goal:

- return the latest authoritative state without editing any table fields

Accepted selectors:

- `record_id`
- `Document_ID`
- `Document_Key + Build_family`
- `Git_ref`

Returned fields should prefer existing writeback fields such as:

- `workflow_action`
- `build_family`
- `git_ref`
- `result`
- `document_link`
- `document_directory`
- `review_status`
- `pr_url`

### 9.2 `start_review`

Required inputs:

- one stable target selector
- resolved `Build_family`

Optional inputs:

- `Version`

Execution route:

- upsert the review-init row
- dispatch [`../../.github/workflows/feishu-start-review.yml`](../../../.github/workflows/feishu-start-review.yml) on `main`

Completion fields should come from the existing review-start writeback:

- `Git_ref`
- `PR_url`
- `Review_status`

### 9.3 `build_draft_package`

Required inputs:

- one stable target selector
- resolved `Build_family`
- explicit `Git_ref`

Optional inputs:

- `Version`

Execution route:

- upsert the `Document_link` row with `Workflow_action=Build Draft Package`
- set the existing trigger fields
- dispatch [`../../.github/workflows/feishu-draft-build-queue.yml`](../../../.github/workflows/feishu-draft-build-queue.yml) on `main`

Completion fields should come from the existing queue writeback:

- `Result`
- `Document link`
- `Document directory`

### 9.4 `publish`

Required inputs:

- one stable target selector
- resolved `Build_family`
- explicit `Git_ref`
- explicit confirmation

Optional inputs:

- `Version`

Execution route:

- upsert the `Document_link` row with `Workflow_action=Publish`
- set the existing trigger fields
- dispatch [`../../.github/workflows/feishu-build-queue.yml`](../../../.github/workflows/feishu-build-queue.yml) on `main`

Completion fields should come from the existing queue and publish writeback:

- `Result`
- `Document link`
- `Document directory`
- latest publish HTML location when available

## 10. Message-Level Guardrails

The control layer should preserve the current workflow safety model.

Required guardrails:

- never let OpenClaw emit arbitrary shell commands
- never bypass `Build_family`-first routing
- never guess when multiple rows or targets match
- require explicit `Git_ref` for `build_draft_package`
- require explicit confirmation for `publish`
- dispatch only the existing `main`-owned workflows
- separate `accepted` from `completed` in message replies

Recommended reply shape:

```text
accepted:
  action=build_draft_package
  target=JE-1000F / us-merged
  git_ref=feature/review-123
  queue_record_id=rec...
  dispatch=started

completed:
  result=SUCCESS | ...
  document_link=...
  document_directory=...
```

## 11. Recommended Delivery Phases

### Phase 0: Message Ingress And Contract Spike

Goal:

- verify Feishu IM webhook auth, reply path, row lookup, and workflow-dispatch auth

Success criteria:

- one message can be verified
- one dry-run action can be resolved deterministically
- one target can be matched without executing anything

### Phase 1: Query-First MVP

Goal:

- ship `query_status` first

Why first:

- no write path
- no workflow dispatch
- no publish risk
- proves the message-to-status loop before action execution

Success criteria:

- an operator can ask for status without opening the table UI

### Phase 2: Build Draft Package MVP

Goal:

- support one safe write action end to end

Implementation:

- resolve message to one `build_draft_package` action
- upsert the `Document_link` row
- dispatch the existing draft-build workflow
- reply first with acceptance, then with writeback-grounded completion

Success criteria:

- one Feishu message can trigger a draft build without manual table editing

### Phase 3: Start Review

Goal:

- support review bootstrapping from message

Success criteria:

- reply includes `Git_ref`, `PR_url`, and `Review_status`

### Phase 4: Publish With Confirmation

Goal:

- support publish from message with stronger guardrails

Success criteria:

- publish remains constrained to explicit target, explicit branch, and explicit confirmation

## 12. Current Repo Cut Points

The control layer should reuse these cut points instead of creating new execution paths:

- queue writeback and field contract:
  - [`../../tools/queue_contract.py`](../../../tools/queue_contract.py)
- build queue entrypoint:
  - [`../../tools/process_build_queue.py`](../../../tools/process_build_queue.py)
- review-start entrypoint:
  - [`../../tools/process_review_start_queue.py`](../../../tools/process_review_start_queue.py)
- current maintainer workflow:
  - [`../../build_doc_guide.md`](../../build_doc_guide.md)
- current user workflow:
  - [`../../user-guide/hello_auto-doc.md`](../../../user-guide/hello_auto-doc.md)
  - [`../../user-guide/quick_start_guide.md`](../../../user-guide/quick_start_guide.md)

No new build core should be inserted below these cut points for V1.

## 13. Suggested Execution Checklist

1. Define one JSON action schema for `query_status`, `start_review`, `build_draft_package`, and `publish`.
2. Decide the primary selector rule, with `record_id` preferred when known.
3. Implement Feishu message ingress with signature verification and idempotency keys.
4. Implement a dry-run resolver that returns structured actions without dispatch.
5. Implement `query_status`.
6. Implement `build_draft_package`.
7. Implement `start_review`.
8. Implement `publish` with explicit confirmation.
9. Add operator logs for message ID, resolved action, matched row ID, workflow dispatch, and final writeback state.
10. Add a small error taxonomy so replies distinguish `ambiguous_target`, `missing_git_ref`, `dispatch_failed`, and `queue_failed`.

## 14. Go Or No-Go Criteria

Start implementation only when all of the following are true:

- the Feishu bot can receive IM events and reply
- OpenClaw can call GitHub `workflow_dispatch`
- one row-selector strategy is agreed
- one confirmation policy is agreed for `publish`
- the team accepts that table writeback remains the authoritative status source

If those are not true yet, keep this work as a Phase 0 spike rather than treating it as a productized feature.

## 15. One-Sentence Summary

OpenClaw should become a bounded Feishu-message control layer on top of the current Feishu
queue and review workers, not a second build system.
