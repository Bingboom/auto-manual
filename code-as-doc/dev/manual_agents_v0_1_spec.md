# Manual Agents v0.1 Spec

Updated: 2026-06-07

## 1. Role

This file is the deferred implementation-facing v0.1 spec for the planned
`manual_agents` layer.

Use it as a shelf-ready contract for a future local Manual Production Agent
framework. Do not treat it as an active implementation workstream until the
trigger conditions in this file are met.

The companion long-term architecture plan is:

- [`../architecture/Control_Orchestration_Strategy.md`](../architecture/Control_Orchestration_Strategy.md)

This spec is deliberately narrower than the original full proposal. It is kept
because the boundaries are useful, but the full `manual_agents` layer is not the
right next implementation priority.

Current repo priority remains:

1. Phase A/B: move data and reusable prose into the structured content model.
2. Phase C: prove page assembly with stable contracts.
3. Only then revisit this orchestration layer, unless the small optional PR 1
   slice below directly helps repeatable manual builds.

Why defer:

- single-operator command friction is not the current bottleneck
- content contracts such as future block/page data are still moving
- adding an orchestration layer now would create maintenance drag over a
  changing foundation
- the layer pays back when OpenClaw or another agent is ready to drive builds,
  or when multi-operator/audit pressure appears

## 2. Placement Decision

The long-term plan is covered by the consolidated
[`../architecture/Control_Orchestration_Strategy.md`](../architecture/Control_Orchestration_Strategy.md),
not by editing
[`../architecture/System Evolution Strategy.md`](../architecture/System%20Evolution%20Strategy.md).

Reason:

- the stable layer model in the system strategy does not change
- this topic belongs with the broader control/orchestration boundary
- the v0.1 details belong in `code-as-doc/dev/` because they are an execution
  contract for the next implementation wave

## 3. Current Status

Status: `deferred`.

Do not start the full v0.1 implementation now.

Allowed now, if it is useful for fast manual production:

- implement only the PR 1 slice: `ManualTask` schema plus a command planner
  that turns a model/region/config target into a typed build recipe
- keep that slice independent of content model changes
- do not add mock clients, MCP, plugins, role services, or real external writes

Trigger conditions for resuming the full v0.1:

- OpenClaw or another agent is ready to drive build/review/publish workflows
- more than one operator needs repeatable handoff/audit behavior
- build actions become high-frequency enough that manual command sequencing is
  a real bottleneck
- content model contracts are stable enough that orchestration will not chase
  moving table/page schemas

## 4. v0.1 Goal

Add a non-invasive local `manual_agents` package that can:

- parse a local manual task JSON
- validate paths and required task fields
- turn a task into an allowlisted `build.py` command plan
- write a local JSONL audit log
- run in mock mode without real Feishu/Lark, document-library, DingTalk, Vercel,
  GitHub, or notification writes
- keep role boundaries explicit through small services and later skill docs

When resumed, v0.1 is a planning and local orchestration shell around existing
repo commands. It is not a new production queue system.

## 5. Corrections From The Original Proposal

v0.1 closes the main gaps in the original proposal before implementation
starts.

| Gap | v0.1 correction |
| --- | --- |
| Existing workflow boundaries were unclear | `manual_agents` wraps existing `build.py`, queue commands, `Review Init`, `Document_link`, OpenClaw, and GitHub workers instead of replacing them |
| Data model conflicted with current contracts | v0.1 follows `external_table_contracts.md` and requires a contract diff before adding live phase2 tables |
| Builder role could publish | builder can only build; reviewer checks; publisher is gated and separate |
| Dry-run was too vague | v0.1 defines `plan-only`, `local-execute`, and `external-write` modes |
| MCP, plugins, and real connectors were bundled too early | v0.1 starts with CLI, mock clients, command planning, and audit logs only |

## 6. Non-Goals For v0.1

Do not implement these in v0.1:

- a new production `ManualJobs` queue table
- a second production status model parallel to `Document_link`
- real Feishu/Lark Bitable writes
- real document-library uploads
- real notification dispatch
- MCP tools
- Codex plugin manifests
- production Feishu connector logic beyond a clear skeleton or interface note
- automatic publish approval
- any rewrite of `build.py`, queue workers, renderers, or review semantics
- migration of `page_registry.csv` into the phase2 synced-table contract
- making `content_blocks.csv` a required live phase2 synced table

## 7. Existing System Boundaries

The current system already owns the real workflow state and execution path.
`manual_agents` v0.1 must wrap these surfaces instead of replacing them.

| Surface | Current owner | v0.1 relationship |
| --- | --- | --- |
| `build.py` | primary command entrypoint | command planner targets this entrypoint only |
| `sync-data` | phase2 snapshot refresh | v0.1 may plan or dry-run it; no real write by default |
| `queue-query` | queue row lookup | future queue-aware stage may wrap it |
| `queue-resolve-action` | intent-to-row resolution | future queue-aware stage may wrap it |
| `queue-execute` | bounded queue dispatch | future queue-aware stage may wrap it |
| `Review Init` | start-review source table/view | remains production source for review start |
| `Document_link` | build/publish queue and writeback | remains production source for draft/publish state |
| OpenClaw | operator control layer | remains chat/control entrypoint |
| GitHub Actions | remote trusted execution plane | remains owner of remote secrets and production workers |
| `data/phase2/` | frozen local snapshot | v0.1 reads/plans against it; no schema migration |
| `docs/_review/` | review authoring surface | v0.1 does not mutate review prose |
| `docs/_build/` | generated runtime output | local-execute may produce it through `build.py` only |

Hard rule:

- `manual_agents` must not create a parallel production queue or a second
  workflow truth source. If a task needs live queue state, it must resolve
  through the existing queue commands and contracts.

## 8. Data Contract Alignment

v0.1 must follow the current table contract in
[`external_table_contracts.md`](external_table_contracts.md).

Required current phase2 synced/derived surfaces include the documented contract,
not only the subset from the original proposal. Important examples:

- `Spec_Master.csv`
- `Spec_Footnotes.csv`
- `Spec_Notes.csv`
- `symbols_blocks.csv`
- `troubleshooting_blocks.csv`
- `Manual_Copy_Source.csv`
- `Localized_Copy.csv`
- `Status_Words.csv`
- `spec_titles.csv`

v0.1 must not declare `page_registry.csv` or `content_blocks.csv` as newly
required live phase2 synced tables.

Rules:

- `page_registry.csv` remains repo-maintained unless a future contract change
  explicitly moves it.
- `content_blocks.csv` may appear in fixtures or future pilots, but v0.1 must
  not treat it as production-live data.
- Any future table addition, removal, or source-of-truth change must update
  [`external_table_contracts.md`](external_table_contracts.md), fixtures, schema
  drift checks, and relevant docs in the same change.

## 9. Contract Diff Gate

Before any implementation PR claims support for new live data tables, it must
answer these questions:

1. Is the table a live external source, a local read model, a derived file, or a
   repo-maintained file?
2. Which existing command writes it, if any?
3. Which build stage reads it?
4. Does it belong in `data/phase2/`, `data/`, `docs/templates/`, or fixtures?
5. What fields are required and which aliases are accepted?
6. What schema drift fixture proves the contract?
7. What happens when the table is missing?

If the answers change the live contract, update the contract doc first.

## 10. Execution Modes

v0.1 replaces the vague `dry_run` behavior with explicit execution modes.

| Mode | External writes | Local writes | Command execution | Intended use |
| --- | --- | --- | --- | --- |
| `plan-only` | no | audit log only | no build commands | default planning and review |
| `local-execute` | no | audit log, mock state, normal local build outputs | allowlisted local commands | local smoke testing |
| `external-write` | explicit yes | audit log and normal outputs | allowlisted commands plus approved external writes | future gated production use |

Defaults:

- task JSON defaults to `execution_mode="plan-only"`
- CLI defaults to `plan-only`
- `external-write` must require an explicit CLI flag and must fail closed when
  credentials, approvals, or preconditions are missing

Compatibility note:

- a user-facing `--dry-run` flag may remain as an alias for `plan-only`
- a future `--local-execute` flag may opt into local command execution
- a future `--external-write` flag may opt into real remote writes

## 11. Role Boundaries

v0.1 services may be named after agent roles, but they must keep a small
permission surface.

| Role | Allowed in v0.1 | Forbidden in v0.1 |
| --- | --- | --- |
| `manual-dispatcher` | parse task, select service, emit plan/result | direct CSV, review, build, or publish mutation |
| `bitable-data-clerk` | mock reads, mock export plan, contract checks | production Bitable writes |
| `manual-builder` | plan or run local build/review/sync-review commands | publish, upload, approval, queue writeback |
| `manual-reviewer` | plan or run `check`, `diff-report`, `release-manifest` | edit review prose, upload final artifacts |
| `manual-publisher` | future gated publish plan | publish without approval/check/manifest gates |
| `document-librarian` | mock registry and mock upload records | real upload or permission changes |

The original proposal allowed `manual-builder` to publish. v0.1 corrects that:
builder never publishes.

## 12. Publish Gate

Publish is a separate role and a separate phase.

Any real publish path must require all of:

- `approval_status="approved"`
- `check_passed=true`
- `release_manifest_exists=true`
- an explicit `external-write` request
- a resolved target source, preferably `Document_link.Git_ref` for
  queue-driven publish

v0.1 may generate a publish plan, but it must not perform a real publish.

## 13. ManualTask v0.1

Implement a small local task schema before any live table schema.

Required fields:

- `task_id`
- `task_type`

Required for target-aware build/check/release tasks:

- `model`
- `region`
- `config`

Optional fields:

- `lang`
- `source`
- `requested_by`
- `approval_status`, default `pending`
- `execution_mode`, default `plan-only`
- `options`
- `queue`

Supported v0.1 task types:

- `plan_build_manual`
- `plan_sync_bitable`
- `plan_check_manual`
- `plan_release_handoff`

Defer these until after the planner is stable:

- `sync_bitable`
- `build_manual`
- `publish_manual`
- `queue_execute`

## 14. Command Planner

All command plans must use `list[str]`, never shell strings.

Allowed initial commands:

- `python build.py validate --config <config>`
- `python build.py review --config <config> --model <model> --region <region>`
- `python build.py sync-review --config <config> --model <model> --region <region>`
- `python build.py check --config <config> --model <model> --region <region>`
- `python build.py diff-report --config <config> --model <model> --region <region>`
- `python build.py release-manifest --config <config> --model <model> --region <region>`
- `python build.py sync-data --config <config> --data-root data/phase2 --dry-run`

Rules:

- command arguments must be generated from validated task fields
- paths must resolve inside the repo root unless explicitly recognized as an
  existing external URL or remote identifier
- secrets must never be logged
- `sync-data` must be planned with `--dry-run` unless the execution mode and
  future permission gate explicitly allow real external writes
- publish planning must be separated from build planning

## 15. Mock State And Audit

v0.1 may create local runtime state under:

- `.manual_agents/logs/`
- `.manual_agents/mock_state/`

Audit line format:

```json
{"task_id":"20260606-001","role":"manual-builder","event":"command_planned","exit_code":null,"timestamp":"2026-06-06T00:00:00Z"}
```

Audit rules:

- JSONL, one event per line
- no secrets or access tokens
- command events store argument arrays or sanitized display strings
- failures store a short error summary, not unbounded stderr
- audit paths must remain inside the repo root

## 16. Minimal File Set

First implementation PRs should prefer this smaller surface:

```text
manual_agents/
  __init__.py
  cli.py
  core/
    task.py
    paths.py
    command_plan.py
    audit_log.py
  connectors/
    base.py
    mock_bitable_client.py
    mock_document_client.py
  services/
    orchestrator.py
    manual_build.py
    manual_review.py
    release_handoff.py

examples/
  tasks/
    plan_build_manual_je1000f_jp.json
  bitable/
    product_specs_sample.json
  docs/
    document_registry_sample.json

tests/
  test_manual_agents_task.py
  test_manual_agents_paths.py
  test_manual_agents_command_plan.py
  test_manual_agents_audit_log.py
  test_manual_agents_orchestrator.py

scripts/
  validate_manual_agents.py
```

Defer the original plugin directories, MCP server, and agent-plugin manifests
until the CLI contract is stable.

## 17. Tests

Minimum v0.1 tests:

- task JSON parses with defaults
- missing required task fields fail clearly
- path escape attempts fail
- `data/phase2` is used in examples and planned snapshot commands
- command planner emits expected `list[str]` commands
- non-allowlisted command requests fail
- plan-only does not run build commands
- local audit log is written
- mock clients write only under `.manual_agents/mock_state/`
- publish plan is blocked without approval/check/manifest gates

Validation for docs-only PRs:

```bash
python tools/check_doc_link_integrity.py
```

Validation once code exists:

```bash
python -m ruff check build.py integrations tools tests scripts manual_agents
python -m unittest
python scripts/validate_manual_agents.py
```

## 18. Suggested PR Sequence

This sequence is deferred. Do not execute it as the current roadmap.

The only slice with possible near-term value is PR 1, because it can act as a
small typed build recipe for fast manual production without depending on the
content model.

Keep the implementation incremental:

1. PR 1: add `ManualTask`, path guards, command plan models, and tests.
2. PR 2: add CLI `dispatch`, plan-only orchestration, and audit JSONL.
3. PR 3: add mock Bitable/document clients and mock state tests.
4. PR 4: add role services for builder/reviewer/release handoff with publish
   gates still plan-only.
5. PR 5: add `scripts/validate_manual_agents.py`, examples, README, and the
   first complete dry-run demo.
6. PR 6: add `local-execute` only after PRs 1 to 5 are stable.

Do not add MCP, plugin manifests, or real external-write connectors in these
first PRs.

## 19. v0.1 Exit Criteria

v0.1 is complete when:

1. `python -m manual_agents.cli dispatch --task examples/tasks/plan_build_manual_je1000f_jp.json`
   returns a deterministic JSON plan.
2. The default mode is `plan-only`.
3. No real external write can happen from the v0.1 CLI.
4. Audit JSONL is written for every dispatch.
5. Mock clients are repeatable and write only under `.manual_agents/mock_state/`.
6. Builder, reviewer, and publisher permissions are separated.
7. Publish is only represented as a gated handoff plan.
8. Tests prove path validation and command allowlisting.
9. New examples and docs use `data/phase2`.
10. The long-term architecture plan and this v0.1 spec agree on boundaries.

## 20. Deferred Milestones

After v0.1:

1. Add `local-execute` for allowlisted local command runs.
2. Add queue-aware planning that wraps `queue-query` and `queue-resolve-action`.
3. Add a read-only MCP surface after the CLI schema stabilizes.
4. Add Codex plugin manifests after MCP and skills have stable names.
5. Add real connector skeletons that fail closed when credentials are missing.
6. Add staged `external-write` support only after contract drift fixtures and
   operator approvals are in place.
