# OpenClaw Control Layer Plan

Updated: 2026-04-10

## 1. Role

This file describes the first OpenClaw integration milestone for this repository.

Scope of this milestone:

- treat OpenClaw as the operator control layer and chat entrypoint
- keep `build.py` and GitHub Actions as the execution plane
- keep Feishu phase2 tables as the source of truth for queue rows and workflow state
- do not use ACP or remote coding sessions in the required path
- do not move build secrets or Feishu writeback logic out of the current GitHub workers

This is intentionally narrower than a general "chat-driven build platform" rollout.
The goal is to simplify operator entry and status visibility without changing the current build semantics.

Phase 1 execution details live in:

- [`../openclaw_phase1_implementation_checklist.md`](../openclaw_phase1_implementation_checklist.md)

## 2. Why This Is The Right First OpenClaw Milestone

The repository already has a working remote flow:

```text
Feishu phase2 tables
  -> GitHub workflow_dispatch or poller wake-up
  -> main-owned GitHub Actions workers
  -> build.py queue commands
  -> build / review / publish outputs
  -> status and document link writeback to Feishu
```

The least risky OpenClaw rollout is not to replace that flow.
It is to put one control layer in front of it so operators have one chat entrypoint for:

- waking the correct worker
- seeing the run URL
- seeing completion or failure summaries
- getting artifact or publish links back into the same thread

Benefits:

- no queue-routing rewrite
- no `build.py` command-surface rewrite
- no new runtime for `pandoc`, `lark-cli`, or Word/PDF export inside OpenClaw
- no duplication of Feishu table semantics in a second control system
- lower operator friction for manual review/build/publish actions

## 3. Target Control Flow

The target flow for V1 is:

```text
Feishu operator
  -> OpenClaw
  -> GitHub workflow_dispatch on main
  -> existing main-owned GitHub worker
  -> build.py queue command
  -> artifact upload / release output
  -> GitHub run result
  -> OpenClaw thread reply in Feishu
```

In other words:

- OpenClaw becomes the control plane entrypoint
- GitHub Actions remains the execution plane
- Feishu phase2 tables remain the workflow state and writeback system

### 3.1 Ownership Boundary

OpenClaw should own:

- operator chat commands
- dispatching the correct GitHub workflow on `main`
- correlating `record_id -> workflow -> run_id`
- replying with run status, artifact links, and publish URLs

GitHub Actions should keep owning:

- environment bootstrap
- secret handling for `FEISHU_*`, `VERCEL_*`, and other build credentials
- execution of `build.py process-review-start-queue`
- execution of `build.py process-build-queue`
- artifact upload, release staging, and Vercel deployment

Feishu phase2 tables should keep owning:

- queue rows
- `Workflow_action`
- `Build_family`
- `Version`
- `Git_ref`
- `Document link`
- `构建结果`

## 4. Explicit Non-Goals

This milestone does not require:

- deploying or using Codex ACP
- letting OpenClaw execute repo code directly
- moving `FEISHU_*` secrets into OpenClaw
- replacing Feishu phase2 tables as the state source
- replacing `build.py` queue commands with OpenClaw-native task logic
- adding free-form build commands such as `/build --model ... --region ...`
- changing the current `main`-owned worker rule for Start Review, Build Draft Package, or Publish

## 5. Minimal Operator Command Set

V1 should keep the command set intentionally small.

### 5.1 `/start-review <review_init_record_id>`

Behavior:

- dispatch [`.github/workflows/feishu-start-review.yml`](../../.github/workflows/feishu-start-review.yml) on `main`
- pass:
  - `queue_record_id=<review_init_record_id>`
  - `trigger_source=openclaw`

Rules:

- this command only wakes the existing Start Review worker
- the worker still resolves the actual target from the Feishu row
- success still means the worker writes back `Git_ref` and `PR_url`

### 5.2 `/build-draft <document_link_record_id>`

Behavior:

- dispatch [`.github/workflows/feishu-draft-build-queue.yml`](../../.github/workflows/feishu-draft-build-queue.yml) on `main`
- pass:
  - `queue_record_id=<document_link_record_id>`
  - `trigger_source=openclaw`

Rules:

- only for rows that already represent `Workflow_action = Build Draft Package`
- `Git_ref` must already exist on the target row
- the current worker remains responsible for resolving the review branch source

### 5.3 `/publish <document_link_record_id>`

Behavior:

- dispatch [`.github/workflows/feishu-build-queue.yml`](../../.github/workflows/feishu-build-queue.yml) on `main`
- pass:
  - `queue_record_id=<document_link_record_id>`
  - `trigger_source=openclaw`

Rules:

- only for rows that already represent `Workflow_action = Publish`
- if the row carries `Git_ref`, the current worker still uses that review branch as the real build source
- the existing 5-minute publish poller should stay enabled as a fallback

### 5.4 `/manual-status [run_id|last]`

Behavior:

- return the current status for the most recent tracked run or one explicit GitHub Actions run
- include:
  - workflow name
  - run URL
  - current state
  - artifact link when present
  - publish URL when present

V1 note:

- this command can stay GitHub-only in the first phase
- it does not need direct Feishu-table reads
- the name is intentionally not `/status` because OpenClaw already reserves that built-in command

## 6. Repo Touchpoints

OpenClaw V1 is deliberately thin because the current repo already exposes stable cut points.

Primary dispatch targets:

- [`.github/workflows/feishu-start-review.yml`](../../.github/workflows/feishu-start-review.yml)
- [`.github/workflows/feishu-draft-build-queue.yml`](../../.github/workflows/feishu-draft-build-queue.yml)
- [`.github/workflows/feishu-build-queue.yml`](../../.github/workflows/feishu-build-queue.yml)

Primary execution surface that stays unchanged:

- [`../../build.py`](../../build.py)
- [`../../tools/process_review_start_queue.py`](../../tools/process_review_start_queue.py)
- [`../../tools/process_build_queue.py`](../../tools/process_build_queue.py)
- [`../../scripts/validate_required_env.sh`](../../scripts/validate_required_env.sh)
- [`../../.github/actions/feishu-common-setup/action.yml`](../../.github/actions/feishu-common-setup/action.yml)

Primary documentation that should stay aligned once rollout begins:

- [`../build_doc_guide.md`](../build_doc_guide.md)
- [`../../user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md)
- [`../../user-guide/quick_start_guide.md`](../../user-guide/quick_start_guide.md)

## 7. Operational Rules

### 7.1 Always Dispatch On `main`

All three GitHub workers intentionally reject non-default-branch dispatches.
OpenClaw should treat this as a hard rule, not a user choice.

### 7.2 Prefer `record_id`-Scoped Runs

When an operator is acting on a specific document row, `queue_record_id` should be treated as required.
Without it, the worker may consume whichever pending rows currently qualify.

### 7.3 Do Not Recreate Queue Semantics In OpenClaw

OpenClaw should not try to infer:

- `Build_family`
- `Workflow_action`
- `Git_ref`
- `Version`
- whether a row is already valid for draft or publish

Those remain Feishu-owned workflow semantics.

### 7.4 Debounce Duplicate Manual Retries

The current GitHub workers use `cancel-in-progress: false`.
OpenClaw should refuse or warn on repeated manual retries when an active run is already in progress for the same workflow and `record_id`.

## 8. Known Risks And Constraints

### 8.1 Documentation Mismatch On Start Review Secrets

The repo has a current documentation mismatch:

- some docs still mention `FEISHU_PHASE2_REVIEW_INIT_*`
- the actual workflow and env validator use `FEISHU_PHASE2_DOCUMENT_LINK_*`

That mismatch should be corrected before OpenClaw setup instructions are treated as normative.

### 8.2 `trigger_source` Is Provenance, Not Routing

The existing workflows print `trigger_source`, but do not use it for routing or writeback.
OpenClaw should use `queue_record_id` as the real correlation key.

### 8.3 Build Correctness Still Depends On Feishu Row State

OpenClaw can simplify entry, but draft and publish correctness still depends on the row already carrying the right:

- `Workflow_action`
- `Git_ref`
- `Build_family`

That should be surfaced in operator guidance.

## 9. Rollout Phases

### Phase 1: Trigger Bridge

Goal:

- make OpenClaw the single operator entrypoint for Start Review, Build Draft Package, and Publish

Implementation:

- support the four commands in this document
- store only a GitHub token in OpenClaw
- keep all build and Feishu secrets in GitHub Actions

Exit criteria:

- operators can trigger all three worker types from one Feishu/OpenClaw entrypoint
- every manual trigger returns a GitHub run URL immediately

### Phase 2: Status Return Path

Goal:

- reply back into the same Feishu thread with started/completed/failed status

Implementation:

- track `thread_id -> record_id -> workflow -> run_id`
- post completion messages with:
  - result
  - run URL
  - artifact link when present
  - publish URL when present

Exit criteria:

- operators no longer need to open GitHub just to learn whether the action finished

### Phase 3: Control-Layer Guards

Goal:

- add safety without adding a second workflow engine

Implementation:

- reject unknown workflow names
- reject non-`main` dispatch
- require `record_id` for operator-targeted actions
- warn when draft or publish is requested without the expected review-state preconditions

Exit criteria:

- OpenClaw reduces bad dispatches without duplicating Feishu queue routing logic

## 10. Validation Plan

The first validation pass should stay operational, not architectural.

### 10.1 Dispatch Validation

Prove that OpenClaw can trigger:

- Start Review on one explicit `review_init` row
- Build Draft Package on one explicit `Document_link` row
- Publish on one explicit `Document_link` row

Expected result:

- each command creates exactly one GitHub Actions run on `main`
- each run records `trigger_source=openclaw`

### 10.2 Status Validation

Prove that OpenClaw can reply back with:

- run URL
- success/failure state
- artifact link for Start Review and Build Draft Package
- publish URL for Publish when present

### 10.3 No-Semantics-Drift Validation

Confirm that OpenClaw does not change:

- Feishu row writeback fields
- `Document_link.Git_ref` behavior
- the current `main`-owned worker rule
- the current 5-minute publish poller fallback

## 11. Decision Rule

Do not let OpenClaw absorb build execution, Feishu secrets, or queue-routing logic in V1.

If a future phase needs more than:

- chat entry
- workflow dispatch
- run status feedback

that should be treated as a new design milestone instead of silently expanding this one.
