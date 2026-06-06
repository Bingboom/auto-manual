# DingTalk Build And Writeback Plan

Updated: 2026-04-09

Archived background note:

- this is the broader provider-migration plan
- the repo's current maintained DingTalk direction is the narrower hybrid path in [`Feishu_Source_DingTalk_Sink_Plan.md`](../Feishu_Source_DingTalk_Sink_Plan.md)
- keep this file for background and future expansion only

## 1. Role

This file is the implementation plan for supporting the current phase2 document build and writeback flow on DingTalk.

It focuses on:

- snapshot sync from DingTalk-managed structured data
- queue-driven build orchestration
- artifact upload
- result and link writeback
- permission, token, and event-subscription implications

It does not redefine the long-term architecture. For that, use [`System Evolution Strategy.md`](../System%20Evolution%20Strategy.md).

For the narrower first milestone that keeps Feishu as the source and queue system while only moving artifact upload to DingTalk, use
[`Feishu_Source_DingTalk_Sink_Plan.md`](../Feishu_Source_DingTalk_Sink_Plan.md).

## 2. Current Flow To Preserve

Today the repository already has a working Feishu/Lark-based flow:

```text
phase2 tables
  -> sync-data
  -> local CSV snapshot
  -> process-build-queue
  -> optional Git_ref worktree checkout
  -> check / word / publish
  -> upload artifact
  -> write Document_link / status fields back to queue rows
```

Current queue orchestration is intentionally build-provider-agnostic in the middle, but provider-specific at the edges:

- sync provider selection and auth bootstrap:
  [`../../tools/phase2_support.py`](../../../tools/phase2_support.py)
- phase2 sync runtime:
  [`../../tools/sync_data_runtime.py`](../../../tools/sync_data_runtime.py)
- build queue entrypoint and orchestration:
  [`../../tools/process_build_queue.py`](../../../tools/process_build_queue.py),
  [`../../tools/process_build_queue_services.py`](../../../tools/process_build_queue_services.py),
  [`../../tools/queue_orchestration.py`](../../../tools/queue_orchestration.py)
- provider-specific upload and wiki attach:
  [`../../tools/queue_lark_ops.py`](../../../tools/queue_lark_ops.py)
- queue binding and preflight:
  [`../../tools/queue_bound_binding.py`](../../../tools/queue_bound_binding.py)

The build core itself should stay unchanged:

- `build.py`
- `check`
- `word`
- `publish`
- release manifest generation
- review bundle generation and GitHub PR flow

## 3. DingTalk Reality Check

### 3.1 What The Official Surface Looks Like

Based on the current official DingTalk docs, the supported server-side integration surface is:

- OpenAPI SDK for application-initiated API calls
- Stream SDK for DingTalk-to-application callbacks such as event subscriptions

References:

- [DingTalk SDK overview](https://open-dingtalk.github.io/developerpedia/docs/develop/sdk/overview/)
- [Stream overview](https://open-dingtalk.github.io/developerpedia/docs/learn/stream/overview/)

Important implication:

- Stream mode is for DingTalk calling our worker, not for our worker calling DingTalk.
- Upload, table read/write, and link writeback still need OpenAPI calls.

### 3.2 Authentication Model Is Different From `lark-cli`

The official permission model distinguishes:

- application access with an App-Only token
- delegated access with a User + App token

References:

- [Permission glossary](https://open-dingtalk.github.io/developerpedia/docs/learn/permission/intro/permission-glossary/)
- [App-Only token](https://open-dingtalk.github.io/developerpedia/docs/learn/permission/token/app_only_token/)
- [Browser admin consent flow](https://open-dingtalk.github.io/developerpedia/docs/develop/permission/token/browser/get_app_only_token_browser/)
- [Browser user delegated token flow](https://open-dingtalk.github.io/developerpedia/docs/develop/permission/token/browser/get_user_app_token_browser/)

Important implication:

- Feishu currently assumes a local authenticated CLI session.
- DingTalk will likely require our worker to own token acquisition, token refresh, and 403 re-consent handling.
- The worker must be explicit about which actions are safe with App-Only access and which require delegated access.

### 3.3 There Is No Clear Official General-Purpose CLI Equivalent

Inference from the current official SDK overview:

- the official docs expose SDK-based integration patterns
- the official docs emphasize OpenAPI SDK and Stream SDK
- I did not find an official general-purpose server CLI analogous to `lark-cli` in the current official docs

Therefore this plan treats "DingTalk CLI" as:

- a repo-local command surface that we own
- backed by DingTalk OpenAPI and, when needed, Stream SDK
- shaped to fit the current `build.py` workflow rather than replacing it

## 4. Capability Mapping

| Current capability | Current Feishu/Lark implementation | DingTalk target | Notes |
| --- | --- | --- | --- |
| Read phase2 tables | `LarkCliSource.fetch_records()` | `DingTalkRecordSource.fetch_records()` | Requires choosing the DingTalk structured-data product first |
| Read queue rows with IDs | `fetch_records_with_ids()` | `fetch_records_with_ids()` | Needed for precise writeback |
| Sync local snapshot CSVs | `sync-data` + `sync_data_runtime.py` | Keep `sync-data`; swap provider | Snapshot shape should stay unchanged |
| Build queue polling | `process-build-queue` | Keep `process-build-queue`; swap provider | Queue grouping and target resolution can stay intact |
| Mark build start | queue row upsert | queue row upsert | Same writeback contract |
| Upload Word artifact | `queue_lark_ops.upload_word_to_drive()` | `DingTalkArtifactStore.upload_word()` | Needs file upload plus shareable URL resolution |
| Attach artifact into doc container | Feishu wiki attach | DingTalk doc/space attach if supported | If not supported, fall back to file-space link writeback |
| Write result and document link | queue row upsert | queue row upsert | Must preserve current field semantics |
| Immediate trigger / event-driven processing | queue polling today, possible Feishu-side triggers | DingTalk Stream or polling | Only if the chosen DingTalk data product emits usable events |

## 5. Product Decision Needed Before Coding

The first non-negotiable decision is not "which SDK", but "which DingTalk product owns the structured data and output links".

We need one product choice for the queue and content tables:

1. a DingTalk product with direct record-level OpenAPI read/write support
2. stable row identifiers usable for writeback
3. permissions that can be granted to an app
4. ideally change notifications, or at minimum efficient polling

Candidate directions:

- a structured form/table product such as Yida-style data models
- a custom middle layer that mirrors DingTalk data into the repo-friendly queue shape

The official admin-consent example explicitly references Yida form permissions such as `Yida.Form.Read`, which suggests app-level structured-data access is supported in at least some DingTalk data products:

- [Browser admin consent flow](https://open-dingtalk.github.io/developerpedia/docs/develop/permission/token/browser/get_app_only_token_browser/)

Recommendation:

- do not start implementation until we finish a one-day capability spike against the exact DingTalk product you want to use
- freeze that product choice before we write the provider layer

## 6. Proposed Architecture

### 6.1 Keep The Build Commands Stable

User-facing commands should stay stable:

- `python build.py sync-data ...`
- `python build.py process-build-queue ...`
- `python build.py process-review-start-queue ...` later if needed

We should not create a separate DingTalk-only build entrypoint.

### 6.2 Move From `lark_cli` To Provider Contracts

Current config still hardcodes `lark_cli` as the only supported provider in
[`../../tools/sync_data_config.py`](../../../tools/sync_data_config.py).

We should evolve this into real provider contracts:

- `phase2.provider = lark_cli | dingtalk_openapi`
- provider-specific auth and environment validation
- provider-specific record read/write implementation
- provider-specific artifact upload and link resolution

Recommended new contracts:

- `Phase2RecordSource`
  - `fetch_records(...)`
  - `fetch_records_with_ids(...)`
  - `upsert_record(...)`
- `Phase2ArtifactStore`
  - `upload_word(...)`
  - `resolve_share_url(...)`
  - `attach_to_workspace(...)`
- `Phase2AuthProvider`
  - `get_app_token(...)`
  - `get_user_token(...)`
  - `refresh_or_reconsent_on_403(...)`
- `Phase2EventSource`
  - `supports_queue_events()`
  - `subscribe_queue_events(...)`

### 6.3 File-Level Refactor Targets

Expected primary refactor surface:

- [`../../tools/sync_data_config.py`](../../../tools/sync_data_config.py)
  - stop collapsing every provider into `lark_cli`
  - add provider-specific env and auth settings
- [`../../tools/phase2_support.py`](../../../tools/phase2_support.py)
  - expose provider-neutral loader and provider factories
- [`../../tools/sync_data_runtime.py`](../../../tools/sync_data_runtime.py)
  - remove hard stop on `provider != "lark_cli"`
- [`../../tools/process_build_queue_services.py`](../../../tools/process_build_queue_services.py)
  - replace Lark-specific upload/move binding with provider-selected services
- [`../../tools/queue_lark_ops.py`](../../../tools/queue_lark_ops.py)
  - keep as Feishu implementation
  - add sibling `queue_dingtalk_ops.py`
- [`../../tools/queue_bound_binding.py`](../../../tools/queue_bound_binding.py)
  - generalize binding resolution away from Feishu-only env names
- [`../../tools/process_review_start_queue.py`](../../../tools/process_review_start_queue.py)
  - leave unchanged in phase 1 unless DingTalk also needs review-init queue parity

### 6.4 Prefer A Repo-Owned CLI Wrapper

Because there is no clear official general-purpose CLI equivalent, the practical approach is:

- implement a repo-owned `dingtalk` command wrapper under `tools/`
- use it as a thin boundary over OpenAPI SDK or REST calls
- keep its verbs aligned with current workflow needs, not with every DingTalk API

Recommended initial verbs:

- `dingtalk auth app-token`
- `dingtalk records list`
- `dingtalk records upsert`
- `dingtalk files upload`
- `dingtalk files share-link`
- `dingtalk workspace attach-file`

This preserves the good part of the current design:

- queue orchestration can stay simple
- provider-specific API complexity stays behind a narrow boundary

## 7. Recommended Delivery Phases

### Phase 0: Capability Spike

Goal:

- prove the chosen DingTalk product can support the queue contract end to end

Exit criteria:

- list rows from the candidate queue table
- update one row field by record ID
- upload one local `.docx`
- obtain a tenant-visible URL
- determine whether "attach into document space" exists

If phase 0 fails, stop and choose a different DingTalk storage product before refactoring the repo.

Current verified status:

- the official App-Only token flow for an internal DingTalk app is now verified in-repo through [`../../tools/dingtalk/auth.py`](../../../tools/dingtalk/auth.py)
- the spike tooling can already normalize a standard DingTalk docs URL of the form `https://alidocs.dingtalk.com/i/nodes/<node_id>` into a stable node identifier through [`../../tools/dingtalk/workspace.py`](../../../tools/dingtalk/workspace.py)
- the remaining unresolved phase-0 question is the public upload or attach API for the chosen DingTalk docs / knowledge-space product

### Phase 1: Snapshot Sync Parity

Goal:

- make `python build.py sync-data` work with `sync.phase2.provider=dingtalk_openapi`

Scope:

- read all configured tables
- preserve current CSV schemas and manifest format
- preserve footnote-ref normalization already implemented for phase2

Validation:

- compare exported CSV shape against the Feishu-backed baseline
- run `python -m unittest`

### Phase 2: Queue Read/Write Parity

Goal:

- make `python build.py process-build-queue --dry-run` and start/result writeback work against DingTalk rows

Scope:

- pending-row discovery
- grouping
- `BUILD_STARTED_AT`
- `SUCCESS` / `FAILED` result writeback
- `Document_link` and `Document_directory`

Validation:

- single-record smoke test
- one draft queue row
- one publish queue row

### Phase 3: Artifact Upload Parity

Goal:

- upload built Word artifacts and write back usable links

Scope:

- upload `.docx`
- resolve a durable link
- optionally attach into a DingTalk doc/space container

Fallback rule:

- if container attach is unsupported or under-granted, write back the file-space link and mark the status as link-only, similar to today's `drive_only` fallback

### Phase 4: Triggering Model

Goal:

- support either scheduled polling or near-real-time execution

Preferred order:

1. polling worker first
2. Stream-based trigger later if the selected product exposes usable change events

Official Stream docs confirm that Stream is suitable for DingTalk-to-app callbacks and event subscriptions, not app-initiated OpenAPI replacement:

- [Stream overview](https://open-dingtalk.github.io/developerpedia/docs/learn/stream/overview/)
- [Stream protocol](https://open-dingtalk.github.io/developerpedia/docs/learn/stream/protocol/)

### Phase 5: Review-Start Parity

This is optional for the first milestone.

Only start this phase after phases 1 to 4 are stable.

Scope:

- DingTalk-side review-init queue rows
- Git branch creation
- PR URL writeback

## 8. Permission Strategy

### 8.1 Default To App-Only Where Possible

Use App-Only access for:

- scheduled sync
- queue polling
- row writeback
- artifact upload

Use delegated access only when the target DingTalk resource model forces user-owned resource operations.

Rationale:

- worker execution is easier to automate with App-Only tokens
- user-delegated flows are harder to refresh non-interactively

### 8.2 Build 403 Recovery Into The Worker

The official docs explicitly recommend handling 403 permission loss by re-triggering the authorization flow:

- [Workbench consent management](https://open-dingtalk.github.io/developerpedia/docs/learn/permission/manage/workbench-consent/)

Required behavior:

- detect 403 and classify it as permission loss, not transient network failure
- stop queue execution for operations that truly require new consent
- surface a precise remediation message
- do not silently downgrade write operations

## 9. Configuration Proposal

Keep the current shared config pattern and add a second provider option.

Example direction:

```yaml
sync:
  phase2:
    provider: dingtalk_openapi
    auth:
      mode: app_only
      client_id_env: DINGTALK_CLIENT_ID
      client_secret_env: DINGTALK_CLIENT_SECRET
      corp_id_env: DINGTALK_CORP_ID
    tables:
      document_link:
        app_name_env: DINGTALK_PHASE2_APP_NAME
        table_id_env: DINGTALK_PHASE2_DOCUMENT_LINK_TABLE_ID
        view_id_env: DINGTALK_PHASE2_DOCUMENT_LINK_VIEW_ID
      spec_master:
        table_id_env: DINGTALK_PHASE2_SPEC_MASTER_TABLE_ID
        view_id_env: DINGTALK_PHASE2_SPEC_MASTER_VIEW_ID
```

Notes:

- keep `configs/config.us.yaml` and `configs/config.ja.yaml` shared
- do not create one config per model
- do not hardcode DingTalk IDs into tracked config files

## 10. Testing Strategy

### 10.1 Unit And Contract Tests

Add provider-neutral contract tests for:

- record listing
- record ID preservation
- row writeback payload mapping
- file upload response parsing
- permission-denied classification

### 10.2 Integration Smoke Tests

Required smoke matrix:

1. `sync-data` against DingTalk sandbox data
2. `process-build-queue --dry-run` against one draft row
3. `process-build-queue --record-id ...` for one draft row
4. `process-build-queue --record-id ...` for one publish row
5. verify link writeback in DingTalk UI

### 10.3 Non-Goals For The First Cut

Do not block the first milestone on:

- Stream-triggered execution
- review-start automation parity
- perfect document-space attachment parity with Feishu wiki

The first milestone is successful if:

- DingTalk data sync works
- build queue can execute
- Word artifact can be uploaded
- queue rows receive a usable output link

## 11. Recommended Build Order

Implementation should happen in this order:

1. phase 0 spike script outside the main flow
2. provider-neutral auth and source interfaces
3. `sync-data` parity
4. queue row read/write parity
5. artifact upload and share-link parity
6. optional workspace-attach enhancement
7. optional Stream trigger

## 12. Execution Summary

Recommended first milestone:

- keep all build/render logic unchanged
- implement DingTalk as a new phase2 provider
- ship a repo-owned DingTalk command wrapper instead of depending on a nonexistent or unstable external CLI abstraction
- accept link-writeback parity before document-space-attach parity

This gives us the fastest path to a working system without rewriting the existing build pipeline.
