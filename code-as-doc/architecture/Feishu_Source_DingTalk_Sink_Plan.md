# Feishu Source With DingTalk Artifact Sink Plan

Updated: 2026-04-14

> **RETIRED — 2026-07-02.** The DingTalk AliDocs mirror-upload chain was
> withdrawn by operator decision: the one-click queue wrapper
> (`process_build_queue_dingtalk.ps1`), the browser-session upload CLI
> (`alidocs_session_upload_cli.py`), and the operator setup guide were removed.
> The queue-side `dingtalk_alidocs_session` provider code referenced below is
> dormant pending a separate removal decision. Kept as the historical record of
> the sink design.

This document matches the repo's DingTalk implementation as of 2026-04-14.

The maintained direction today is:

- Feishu phase2 stays the source of truth for structured data, queue rows, and
  writeback
- `build.py` plus the existing queue workers stay the execution plane
- DingTalk is an optional artifact destination, not the queue control plane

Use [`DingTalk_Build_Writeback_Plan.md`](DingTalk_Build_Writeback_Plan.md) and
[`DingTalk_Phase0_Spike_Checklist.md`](DingTalk_Phase0_Spike_Checklist.md) only
as historical background.

## 1. Current Repo Status

As of 2026-04-14, the hybrid path is already implemented:

- artifact sink selection exists in
  [`../../tools/queue_artifact_sink.py`](../../tools/queue_artifact_sink.py)
- queue execution supports `lark_drive` and `dingtalk_alidocs_session`
- DingTalk browser-session upload exists in
  [`../../tools/dingtalk/alidocs_session.py`](../../tools/dingtalk/alidocs_session.py)
- the manual smoke helper for that upload path was
  `tools/dingtalk/alidocs_session_upload_cli.py` (removed 2026-07-02)
- local wrappers existed for Feishu-only and Feishu-plus-DingTalk runs:
  [`../../scripts/process_build_queue_feishu.ps1`](../../scripts/process_build_queue_feishu.ps1),
  `scripts/process_build_queue_dingtalk.ps1` (removed 2026-07-02)
- the remote GitHub Draft/Publish workers keep Feishu/wiki as primary and
  enable DingTalk mirror mode when the required DingTalk secrets are present:
  [`../../.github/workflows/feishu-draft-build-queue.yml`](../../.github/workflows/feishu-draft-build-queue.yml),
  [`../../.github/workflows/feishu-build-queue.yml`](../../.github/workflows/feishu-build-queue.yml)

This means the remaining work is operational hardening and live validation, not
provider-boundary discovery.

## 2. Maintained Scope

This integration keeps the current queue semantics unchanged:

- Feishu `Document_link` rows still trigger the work
- Feishu writeback still owns `Document directory`, `Document link`, `构建结果`,
  and `data_sync`
- `Document link` remains the canonical returned artifact URL
- `Document link_dd` is only an optional supplemental DingTalk writeback field

Current DingTalk-specific queue behavior:

- set `AUTO_MANUAL_ARTIFACT_SINK_PROVIDER=dingtalk_alidocs_session` only when
  DingTalk should replace the primary sink
- set `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER=dingtalk_alidocs_session` when the
  primary sink should stay Feishu/wiki and the same DOCX should also sync to
  DingTalk
- if a row has `是否上传钉钉`, that checkbox becomes the row-level DingTalk gate
- if a row does not have `是否上传钉钉`, the worker follows the current global
  worker mode for the whole row
- if a checked row has `DingTalk_target_node_url`, that row-level target
  overrides the global target
- if a row has `operator_union_id`, the worker can resolve a per-operator
  AliDocs session file before falling back to global envs
- `DingTalk_session_key` and `钉钉会话键` are accepted as aliases for the same
  session selector field
- if a DingTalk-enabled row points at a missing per-operator session or there is
  no usable global session, the queue now fails that row before build starts
  and writes the missing-session reason back to Feishu

## 3. Current Execution Shape

The current queue path is effectively:

```text
Feishu phase2 tables
  -> sync-data / existing snapshot
  -> process-build-queue
  -> build local DOCX
  -> resolve primary artifact sink
  -> optional DingTalk mirror publish
  -> write canonical result back to Feishu Document_link
```

Current repo cut points:

- queue entry and orchestration:
  [`../../tools/process_build_queue.py`](../../tools/process_build_queue.py),
  [`../../tools/process_build_queue_services.py`](../../tools/process_build_queue_services.py)
- queue row execution:
  [`../../tools/queue_group_processing.py`](../../tools/queue_group_processing.py)
- sink provider selection and row-level target/session resolution:
  [`../../tools/queue_artifact_sink.py`](../../tools/queue_artifact_sink.py)
- current Feishu upload path:
  [`../../tools/queue_lark_ops.py`](../../tools/queue_lark_ops.py)
- DingTalk upload helpers:
  [`../../tools/dingtalk/README.md`](../../tools/dingtalk/README.md),
  [`../../tools/dingtalk/alidocs_session.py`](../../tools/dingtalk/alidocs_session.py)
- queue writeback field construction:
  [`../../tools/queue_writeback.py`](../../tools/queue_writeback.py)

## 4. Current Execution Modes

There are three supported runtime modes:

1. Feishu/wiki primary only
2. Feishu/wiki primary plus DingTalk mirror
3. DingTalk primary replace mode

The maintained default is still mode 2 for DingTalk rollout:

- Feishu/wiki remains the primary artifact sink
- `Document link` remains canonical
- DingTalk writes only the supplemental `Document link_dd` field when present

Mode 3 is supported for explicit operator-driven use, but it is not the default
GitHub worker behavior.

## 5. Row-Level Contract

Current queue row contract:

- `Document link`: canonical returned artifact link
- `Document link_dd`: optional DingTalk supplemental link
- `是否上传钉钉`: optional row-level DingTalk gate
- `DingTalk_target_node_url`: optional row-level DingTalk target override
- `operator_union_id`: optional per-operator DingTalk session selector

Status note conventions:

- `dingtalk_sync=skipped`
- `dingtalk_sync=ok`
- `dingtalk_sync=failed`

These notes are additive: they make mirror success or failure visible without
changing the existing Feishu queue contract.

## 6. Auth And Session Model

The current DingTalk sink is based on browser-session credentials, not an
official app-only knowledge-base upload API.

Supported session sources today:

- global env vars:
  `DINGTALK_DOCS_A_TOKEN`, `DINGTALK_DOCS_XSRF_TOKEN`,
  `DINGTALK_DOCS_COOKIE`, optional `DINGTALK_DOCS_BX_V`
- per-operator session registry:
  `AUTO_MANUAL_DINGTALK_SESSION_ROOT`, defaulting to
  `~/.auto-manual/dingtalk-sessions`

When `operator_union_id` is present on the row, the worker first looks for:

```text
<session_root>/<operator_union_id>.json
```

If that file is absent, the worker falls back to the global env-based session.

## 7. Non-Goals

This path does not require:

- moving phase2 source tables to DingTalk
- moving queue ownership to DingTalk
- changing `build.py` command semantics
- replacing Feishu review-init automation
- making DingTalk AI-table writeback part of the required success path

## 8. Remaining Gaps

The main remaining gaps are:

- browser-session rotation and storage hygiene for long-lived workers
- live local and GitHub smoke validation against a non-critical DingTalk node
- clear operator guidance for per-operator session-file provisioning
- a future app-only or officially supported DingTalk upload path if the browser
  session chain becomes too fragile

Current live-test note:

- the real `Document_link` queue row can already drive `Publish`,
  `DingTalk_target_node_url`, and `operator_union_id`
- the remaining blocker on the tested worker is not table routing; it is the
  absence of a matching local DingTalk session source:
  - either global `DINGTALK_DOCS_*`
  - or `<session_root>/<operator_union_id>.json`
- the queue now surfaces that missing-session problem before build starts, so
  the live blocker is explicit in row writeback instead of hiding until upload

## 9. Recommended Next Work

The recommended next work is operational, not architectural:

1. keep the current row-driven contract as the maintained rollout path:
   `是否上传钉钉` + `DingTalk_target_node_url` + `operator_union_id` or
   `DingTalk_session_key`
2. run workers in one of two explicit modes:
   - shared global-session worker: DingTalk-enabled rows may omit
     `operator_union_id`, and the worker uses one shared `DINGTALK_DOCS_*`
   - per-operator worker: DingTalk-enabled rows should carry
     `operator_union_id` or its alias so the worker can resolve
     `<session_root>/<key>.json`
3. validate one local Feishu primary + DingTalk mirror run against a controlled
   `Document_link` row
4. validate one GitHub Draft/Publish run with real DingTalk secrets
5. treat the rollout slice as complete only after:
   - one real `Build Draft Package` row succeeds
   - one real `Publish` row succeeds
   - `Document link_dd` is written back
   - `构建结果` contains `dingtalk_sync=ok`
6. only after that, decide whether a new DingTalk provider is worth the cost

Do not reopen the earlier "replace Feishu with DingTalk" plan unless the queue
control plane itself is intentionally being redesigned.

## 10. Canonical References

- current maintainer command reference:
  [`../build_doc_guide.md`](../build_doc_guide.md)
- current user workflow:
  [`../../user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md)
- current quick operator guide for maintaining the queue table:
  [`../../user-guide/quick_start_guide.md`](../../user-guide/quick_start_guide.md)
- DingTalk local setup and smoke steps: the setup guide
  (`user-guide/dingtalk_alidocs_upload_setup_guide.md`) was removed with the
  chain retirement (2026-07-02)
- current OpenClaw and queue architecture context:
  [`OpenClaw_Control_Layer_Plan.md`](OpenClaw_Control_Layer_Plan.md)
