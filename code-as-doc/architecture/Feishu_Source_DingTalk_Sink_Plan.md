# Feishu Source With DingTalk Artifact Sink Plan

Updated: 2026-04-09

## 1. Role

This file describes the first hybrid integration milestone for DingTalk.

Scope of this milestone:

- keep Feishu phase2 tables as the source of truth
- keep Feishu `Document_link` queue rows as the build trigger and writeback target
- keep the current `build.py -> process-build-queue` orchestration shape
- replace only the artifact sink:
  - upload the generated document to DingTalk
  - resolve a DingTalk link
  - write that DingTalk link back into the Feishu queue row

This is intentionally narrower than the full provider migration described in
[`DingTalk_Build_Writeback_Plan.md`](DingTalk_Build_Writeback_Plan.md).

Current verified status for this hybrid path:

- Feishu remains the already working source and queue system
- DingTalk App-Only auth for the current internal-app model is now verified in-repo through [`../../tools/dingtalk/auth.py`](../../tools/dingtalk/auth.py)
- DingTalk workspace target URLs can already be normalized to node IDs through [`../../tools/dingtalk/workspace.py`](../../tools/dingtalk/workspace.py)
- the remaining unknown for V1 is the exact DingTalk upload or attach API that maps a local `.docx` into a tenant-visible link under the chosen docs node

## 2. Why This Should Be The First DingTalk Milestone

The current repository already has a stable Feishu-backed queue flow:

```text
Feishu phase2 tables
  -> sync-data
  -> local CSV snapshot
  -> process-build-queue
  -> check / word / publish
  -> upload artifact
  -> write status and link back to Feishu Document_link
```

The least risky way to introduce DingTalk is not to move the queue first.
It is to preserve the working Feishu orchestration and swap only the upload destination.

Benefits:

- no immediate migration of source tables
- no immediate migration of trigger/workflow rows
- no immediate reimplementation of `sync-data`
- no queue routing changes
- no review-start flow changes
- DingTalk can be introduced where the coupling is narrowest: artifact upload and share-link resolution

## 3. Target Flow

The target hybrid flow for V1 is:

```text
Feishu phase2 tables
  -> sync-data
  -> local CSV snapshot
  -> process-build-queue
  -> build DOCX / HTML
  -> upload DOCX to DingTalk
  -> resolve DingTalk document/file link
  -> write DingTalk link back to Feishu Document_link
```

In other words:

- Feishu remains the control plane
- DingTalk becomes the artifact storage plane

## 4. Explicit Non-Goals For V1

This milestone does not require:

- moving phase2 content tables to DingTalk
- moving the build queue itself to DingTalk
- updating a DingTalk AI table row as part of the required success path
- replacing Feishu review-init automation
- replacing Feishu queue listeners
- changing `build.py` command semantics

If DingTalk table writeback is later required, that should be treated as a V2 extension, not as a prerequisite for V1.

## 5. Current Repo Cut Points

The current queue flow is already structured so the upload path is isolated.

Primary integration points:

- queue orchestration:
  [`../../tools/process_build_queue_services.py`](../../tools/process_build_queue_services.py)
- queue row execution:
  [`../../tools/queue_group_processing.py`](../../tools/queue_group_processing.py)
- current Feishu upload and wiki attach helpers:
  [`../../tools/queue_lark_ops.py`](../../tools/queue_lark_ops.py)
- queue writeback field construction:
  [`../../tools/queue_writeback.py`](../../tools/queue_writeback.py)

Current success path inside `process_queue_record_group()` is effectively:

1. build the local Word file
2. upload to Feishu Drive
3. try to move the file into Feishu wiki
4. write the resolved link into Feishu `Document_link`

That means the narrowest refactor is:

- keep steps 1 and 4
- replace steps 2 and 3 with DingTalk upload + DingTalk link resolution

## 6. Proposed V1 Architecture

### 6.1 Introduce An Artifact Sink Boundary

Instead of treating upload as inherently Feishu-specific, introduce a provider-neutral artifact sink boundary for queue output.

Recommended contract:

- `upload_word(word_output_path) -> UploadedArtifact`
- `resolve_public_link(uploaded_artifact) -> str`
- `attach_to_workspace(uploaded_artifact) -> str | None`

Recommended model:

```text
Queue worker
  -> build document locally
  -> artifact sink provider
     -> upload
     -> optional attach
     -> link resolution
  -> Feishu queue writeback
```

### 6.2 Keep Feishu Queue Writeback Unchanged

The queue row update contract should remain:

- `Document directory` = local built file path
- `Document link` = resolved DingTalk URL
- `构建结果` = `SUCCESS | ...`
- trigger = reset to done
- immediate trigger = cleared

This is important because all operator workflow stays in Feishu.

### 6.3 Make DingTalk Upload Configurable Per Queue Worker

The queue worker should not infer the DingTalk destination from the Feishu base.

Instead, provide explicit DingTalk sink configuration such as:

```yaml
queue:
  artifact_sink:
    provider: dingtalk
    mode: upload_only
    target_node_env: DINGTALK_ARTIFACT_TARGET_NODE
    share_link_mode: direct
```

The exact final config shape can change, but the intent should stay:

- DingTalk destination is explicit
- Feishu queue binding remains explicit
- one worker can still be switched back to Feishu sink if needed

## 7. Recommended Delivery Phases

### Phase A: Add Artifact Sink Abstraction

Goal:

- separate build result upload from Feishu-specific code paths

Implementation:

- keep current Lark upload behavior behind a `lark` sink implementation
- add a `dingtalk` sink placeholder
- route queue execution through `artifact_sink.upload_word(...)`

Expected code touch points:

- [`../../tools/process_build_queue_services.py`](../../tools/process_build_queue_services.py)
- [`../../tools/queue_group_processing.py`](../../tools/queue_group_processing.py)
- new `tools/dingtalk/` helper modules as needed

### Phase B: Implement DingTalk Upload-Only Sink

Goal:

- upload `.docx` to the target DingTalk knowledge-space node
- return a stable DingTalk link

Success criteria:

- local DOCX uploads successfully
- returned DingTalk link opens for the intended tenant audience
- Feishu queue row stores the DingTalk link

### Phase C: Add Optional DingTalk Workspace Attach

Goal:

- if DingTalk exposes a separate "attach to node" or "move into space" step, support it

Fallback:

- if attach is unavailable or under-granted, keep upload-only mode and still write back the resolved DingTalk file link

### Phase D: Optional Dual Write

Goal:

- optionally write the same DingTalk link into a DingTalk AI table row

This is explicitly deferred.
The V1 required success path is still:

- upload to DingTalk
- write DingTalk URL back to Feishu

## 8. Error-Handling Rules

### 8.1 DingTalk Upload Failure

If DingTalk upload fails:

- queue row should remain failed in Feishu
- `构建结果` should include the DingTalk upload error
- if the local file exists, keep `Document directory`
- do not silently fall back to Feishu Drive unless the operator explicitly enables dual-sink fallback

### 8.2 DingTalk Link Resolution Failure

If upload succeeds but link resolution fails:

- queue row should remain failed
- include any preserved DingTalk file identifier in the error if safe
- do not write a guessed URL into `Document link`

### 8.3 DingTalk Attach Failure

If attach-to-node fails but upload succeeded and a usable DingTalk file URL exists:

- treat the run as successful in upload-only mode
- annotate `构建结果` with a status note such as:
  - `dingtalk_link_only`
  - `workspace_attach_failed=...`

This mirrors today's `drive_only` fallback pattern.

## 9. Configuration Proposal

V1 should keep the existing Feishu config and add DingTalk artifact settings only.

Illustrative direction:

```yaml
sync:
  phase2:
    provider: lark_cli

queue:
  artifact_sink:
    provider: dingtalk
    auth:
      mode: app_only
      client_id_env: DINGTALK_CLIENT_ID
      client_secret_env: DINGTALK_CLIENT_SECRET
      corp_id_env: DINGTALK_CORP_ID
    dingtalk:
      target_node_env: DINGTALK_ARTIFACT_TARGET_NODE
      share_link_mode: direct
      upload_mode: knowledge_space
```

Notes:

- Feishu environment variables remain required
- DingTalk settings are additive, not replacing Feishu queue bindings
- the shared `config.us.yaml` and `config.ja.yaml` pattern remains intact

## 10. Inputs Required To Implement V1

To build this for real, we need only the DingTalk artifact-side details.

Required:

1. DingTalk app credentials
   - `client_id`
   - `client_secret`
   - `corp_id`

2. Upload target
   - the DingTalk node or knowledge-space location where DOCX files should land

3. Upload API details
   - actual upload endpoint or working request example
   - whether upload is multipart, staged, or tokenized
   - the file identifier returned on success

4. Link resolution details
   - whether the upload response already returns a shareable URL
   - or the follow-up endpoint to resolve one

Optional for V1:

5. Attach-to-node details
   - only if upload and attach are separate operations

Not required for V1:

6. DingTalk AI table writeback details
   - can be deferred

## 11. Validation Plan

### 11.1 Local Smoke

Use the new DingTalk smoke helper:

- [`../../tools/dingtalk/spike_cli.py`](../../tools/dingtalk/spike_cli.py)

Smoke scope for this hybrid milestone:

1. obtain App-Only token
2. upload one `.docx`
3. resolve a usable DingTalk link

### 11.2 Queue Integration Smoke

After the upload sink is wired in:

1. trigger one Feishu `Document_link` row
2. build a local DOCX
3. upload the DOCX to DingTalk
4. confirm the Feishu `Document link` field now stores the DingTalk URL
5. confirm `构建结果=SUCCESS...`

### 11.3 Publish Smoke

Run one publish row and confirm:

- release manifest still points to the final DingTalk URL
- queue writeback still happens in Feishu
- no existing Feishu review/build routing regresses

## 12. Recommended First Implementation Slice

The first coding slice should be:

1. add an artifact sink abstraction behind the existing queue flow
2. keep the current Lark upload path as one implementation
3. add a DingTalk upload-only implementation
4. wire the DingTalk URL back into Feishu `Document_link`

This is the smallest useful change that introduces DingTalk without destabilizing the current Feishu-based production workflow.
