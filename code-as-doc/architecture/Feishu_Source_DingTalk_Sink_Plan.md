# Feishu Source With DingTalk Artifact Sink Plan

Updated: 2026-04-13

This is the current DingTalk integration document that matches the repo's actual
implementation.

The maintained direction today is:

- Feishu phase2 stays the source of truth for structured data, queue rows, and writeback
- `build.py` plus the existing queue workers stay the execution plane
- DingTalk is an optional artifact sink, not the queue control plane

Use [`DingTalk_Build_Writeback_Plan.md`](DingTalk_Build_Writeback_Plan.md) and
[`DingTalk_Phase0_Spike_Checklist.md`](DingTalk_Phase0_Spike_Checklist.md) only as
historical background.

## 1. Current Repo Status

As of 2026-04-12, the hybrid path is already implemented in the repo:

- artifact-sink provider selection exists in [`../../tools/queue_artifact_sink.py`](../../tools/queue_artifact_sink.py)
- the queue workers already support `lark_drive` and `dingtalk_alidocs_session`
- the DingTalk browser-session upload path exists in [`../../tools/dingtalk/alidocs_session.py`](../../tools/dingtalk/alidocs_session.py)
- the manual smoke helper for that path exists in [`../../tools/dingtalk/alidocs_session_upload_cli.py`](../../tools/dingtalk/alidocs_session_upload_cli.py)
- the remote GitHub Draft/Publish workers already auto-switch to the DingTalk sink when the required secrets are present:
  - [`../../.github/workflows/feishu-draft-build-queue.yml`](../../.github/workflows/feishu-draft-build-queue.yml)
  - [`../../.github/workflows/feishu-build-queue.yml`](../../.github/workflows/feishu-build-queue.yml)

This means the remaining work is operational hardening and auth durability, not
provider-boundary discovery.

## 2. Maintained Scope

This integration keeps the current queue semantics unchanged:

- Feishu `Document_link` rows still trigger the work
- Feishu writeback still owns `Document directory`, `Document link`, `构建结果`, and `data_sync`
- `Document link` remains the canonical returned artifact URL
- `Document link_dd` is only an optional supplemental DingTalk writeback field

Current DingTalk-specific queue behavior:

- set `AUTO_MANUAL_ARTIFACT_SINK_PROVIDER=dingtalk_alidocs_session` to enable the DingTalk sink
- if a row also has `是否上传钉钉`, that checkbox becomes the row-level gate
- if a checked row also has `DingTalk_target_node_url`, that row-level target overrides the global target
- if the sink is DingTalk and `Document link_dd` exists, the worker dual-writes the same DingTalk URL there

## 3. Current Execution Shape

The current queue path is effectively:

```text
Feishu phase2 tables
  -> sync-data / existing snapshot
  -> process-build-queue
  -> build local DOCX
  -> resolve artifact sink provider
  -> upload to Feishu/wiki or DingTalk AliDocs session
  -> write canonical link back to Feishu Document_link
```

Current repo cut points:

- queue entry and orchestration:
  [`../../tools/process_build_queue.py`](../../tools/process_build_queue.py),
  [`../../tools/process_build_queue_services.py`](../../tools/process_build_queue_services.py)
- queue row execution:
  [`../../tools/queue_group_processing.py`](../../tools/queue_group_processing.py)
- sink provider selection and row-level target resolution:
  [`../../tools/queue_artifact_sink.py`](../../tools/queue_artifact_sink.py)
- current Feishu upload path:
  [`../../tools/queue_lark_ops.py`](../../tools/queue_lark_ops.py)
- DingTalk upload helpers:
  [`../../tools/dingtalk/README.md`](../../tools/dingtalk/README.md),
  [`../../tools/dingtalk/alidocs_session.py`](../../tools/dingtalk/alidocs_session.py)
- queue writeback field construction:
  [`../../tools/queue_writeback.py`](../../tools/queue_writeback.py)

## 4. Non-Goals

This path does not require:

- moving phase2 source tables to DingTalk
- moving queue ownership to DingTalk
- changing `build.py` command semantics
- replacing Feishu review-init automation
- making DingTalk AI table writeback part of the required success path

## 5. Remaining Gaps

The main remaining gaps are:

- the current DingTalk sink is based on browser-session credentials, so session durability and rotation still need operator care
- long-lived worker hardening and operational guidance still matter more than new queue refactors
- an app-only DingTalk upload path would still be cleaner long-term, but it is not required for today's maintained hybrid flow

## 6. Canonical References

- current maintainer command reference:
  [`../build_doc_guide.md`](../build_doc_guide.md)
- current user workflow:
  [`../../user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md)
- DingTalk local setup and smoke steps:
  [`../../user-guide/dingtalk_alidocs_upload_setup_guide.md`](../../user-guide/dingtalk_alidocs_upload_setup_guide.md)
- current OpenClaw and queue architecture context:
  [`OpenClaw_Control_Layer_Plan.md`](OpenClaw_Control_Layer_Plan.md)

## 7. Next Milestone: Sync Upload To DingTalk Knowledge Base

The next useful step is not "replace Feishu upload with DingTalk", but "keep the
current Feishu/wiki upload path working and also sync the same built document to
DingTalk knowledge base in the same queue run".

That means the target behavior becomes:

- build the DOCX once
- publish the primary artifact through the current Feishu/wiki path
- when DingTalk sync is enabled, upload the same DOCX to DingTalk knowledge base as a mirror step
- keep `Document link` as the canonical returned link for compatibility
- write the DingTalk node URL into `Document link_dd` when that field exists
- make the build result clearly show whether DingTalk sync succeeded, failed, or was skipped

This milestone should stay inside the current hybrid boundary:

- Feishu phase2 remains the source of truth
- Feishu `Document_link` remains the queue and writeback surface
- DingTalk stays an artifact mirror / secondary sink, not the queue control plane

## 8. Current Gap To Close

Today the repo can already upload to DingTalk, but the execution shape is
provider-select, not dual-publish:

- one active provider is resolved from `queue_artifact_sink.py`
- row-level `是否上传钉钉` decides whether a DingTalk-configured worker uses DingTalk or falls back to Feishu/wiki
- `Document link_dd` is only populated when DingTalk is the active artifact sink

So the missing capability is:

- Feishu/wiki upload and DingTalk upload in the same successful build

## 9. Proposed Implementation Plan

### Phase A. Publish Contract

Keep the queue row contract as stable as possible:

- keep `Document link` as the canonical main link
- keep `Document link_dd` as the DingTalk mirror link
- keep `DingTalk_target_node_url` as the row-level DingTalk destination override
- keep `是否上传钉钉` as the row-level gate for whether DingTalk sync is attempted

Add one explicit status convention in `构建结果`:

- `dingtalk_sync=skipped`
- `dingtalk_sync=ok`
- `dingtalk_sync=failed`

That makes partial mirror failures visible without breaking current consumers that
still rely only on `Document link`.

### Phase B. Artifact Publish Abstraction

Refactor the current single-destination publish model into:

- one primary artifact destination
- zero or more mirror destinations

Likely cut points:

- [`../../tools/queue_artifact_sink.py`](../../tools/queue_artifact_sink.py)
- [`../../tools/queue_group_processing.py`](../../tools/queue_group_processing.py)
- [`../../tools/queue_writeback.py`](../../tools/queue_writeback.py)

Target shape:

- primary destination remains Feishu/wiki by default
- DingTalk becomes a mirror destination that can be enabled globally and gated per row
- publish result should return:
  - primary `document_link_url`
  - optional DingTalk `document_link_dd_url`
  - status notes for mirror success / failure

### Phase C. Queue Execution Rules

Queue execution should follow this order:

1. build the DOCX once
2. upload to the primary Feishu/wiki destination
3. if the row requests DingTalk sync, upload the same DOCX to DingTalk
4. write back both links and one combined status

Failure policy should be explicit:

- if the primary Feishu/wiki publish fails, the whole task fails
- if the primary publish succeeds but DingTalk mirror upload fails, preserve the primary success and record `dingtalk_sync=failed`
- leave room for a future strict mode only if business rules later require "DingTalk sync must succeed or the build is failed"

This keeps the current workflow stable while making DingTalk sync observable.

### Phase D. Config And Environment

The current env model assumes one provider. For the sync-upload milestone, prefer:

- keep `AUTO_MANUAL_ARTIFACT_SINK_PROVIDER=lark_drive` as the primary default
- add a mirror-oriented switch such as config-driven or env-driven DingTalk enablement
- continue using the existing DingTalk browser-session env vars:
  - `DINGTALK_DOCS_A_TOKEN`
  - `DINGTALK_DOCS_XSRF_TOKEN`
  - `DINGTALK_DOCS_COOKIE`
  - optional `DINGTALK_DOCS_TARGET_NODE_URL`
  - optional `DINGTALK_DOCS_BX_V`

Recommended first rollout:

- do not redesign the whole config family structure
- add only the minimum extra switch needed to say "primary is Feishu/wiki, also mirror to DingTalk when requested"

### Phase E. Tests

Minimum test coverage for the implementation PR:

- primary-only Feishu/wiki upload still works unchanged
- primary Feishu/wiki plus DingTalk mirror succeeds and writes both links
- row without `是否上传钉钉` or unchecked row skips DingTalk sync cleanly
- row-level `DingTalk_target_node_url` overrides the global default target
- primary success plus DingTalk mirror failure preserves `Document link`, leaves `Document link_dd` empty or stale-safe, and writes `dingtalk_sync=failed`
- existing OpenClaw queue resolution still treats `Document link` as canonical

### Phase F. Rollout

Suggested rollout order:

1. local dry-run path using one controlled `record_id`
2. local real upload smoke to a non-critical DingTalk knowledge-base node
3. GitHub worker smoke with repository secrets
4. enable row-level DingTalk sync for selected rows only
5. after stability is confirmed, decide whether Publish-only is enough or Build Draft Package should also mirror to DingTalk

## 10. Open Questions Before Coding

These should be answered before the actual implementation PR:

- Is DingTalk sync needed for both `Build Draft Package` and `Publish`, or only `Publish`?
- When DingTalk sync fails, is "primary success + mirror failure" acceptable for your operation flow?
- Should one global DingTalk node be enough for now, with row-level override only as an escape hatch?
- Do you want `Document link` to remain Feishu/wiki forever, or eventually switch the canonical returned link to DingTalk for some workflows?

## 11. Recommended First Implementation Scope

The smallest safe implementation slice is:

- keep Feishu/wiki as the primary sink
- add DingTalk as an optional mirror upload for `Publish` first
- keep `Document link` canonical
- write DingTalk URL only to `Document link_dd`
- mark mirror status in `构建结果`

That slice is small enough to validate the product need without destabilizing the
existing OpenClaw, Feishu queue, or build-worker contract.
