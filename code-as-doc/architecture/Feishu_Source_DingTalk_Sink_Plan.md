# Feishu Source With DingTalk Artifact Sink Plan

Updated: 2026-04-12

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
