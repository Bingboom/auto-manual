# DingTalk Phase 0 Spike Checklist

Updated: 2026-04-09

Archived background note:

- this spike checklist is no longer the current maintained DingTalk doc
- keep it only as evidence for the earlier API and product investigation
- use [`Feishu_Source_DingTalk_Sink_Plan.md`](Feishu_Source_DingTalk_Sink_Plan.md) for the current repo direction

## 1. Role

This file is the execution checklist for the DingTalk capability spike described in
[`DingTalk_Build_Writeback_Plan.md`](DingTalk_Build_Writeback_Plan.md).

Phase 0 is not a repo refactor.
It is a proof step to confirm the chosen DingTalk product can support the current phase2 queue contract before we touch `sync-data` or `process-build-queue`.

## 2. Spike Goal

Prove that one DingTalk-backed data source can support all of the following:

1. list queue rows
2. address one row by a stable record identifier
3. write a harmless field update back to that row
4. upload a local `.docx`
5. obtain a durable tenant-visible link
6. determine whether the uploaded file can be attached into a DingTalk doc or workspace container

## 3. Preconditions

Before running the spike, prepare:

- one DingTalk app with the minimum OpenAPI permissions needed for:
  - reading the chosen structured-data product
  - writing rows back to the chosen structured-data product
  - uploading or storing files
  - resolving a file link
  - optionally attaching a file into a doc or workspace container
- one sandbox queue table or equivalent data model with at least:
  - a stable primary key or record ID
  - one harmless writable text field for writeback verification
  - one row that can be safely edited during the spike
- one sample `.docx` under the repo, or a generated throwaway file path
- one agreed token mode:
  - App-Only first
  - delegated access only if App-Only cannot complete the required write operations

## 4. Execution Checklist

### 4.1 Auth

- Obtain an App-Only token.
- Record the token acquisition endpoint, required headers, and expiry behavior.
- Confirm whether token refresh is deterministic enough for a worker process.

Evidence to capture:

- token TTL
- refresh approach
- exact permission scope names granted to the app

### 4.2 Queue Row Listing

- List rows from the candidate queue table or data model.
- Verify the response includes a stable row identifier suitable for future writeback.
- Verify the response can be filtered or paged without downloading the entire dataset every time.

Evidence to capture:

- example list endpoint
- row ID field name
- pagination behavior
- filtering options relevant to `Workflow_action`, trigger state, and `record_id`

### 4.3 Single-Row Readback

- Read one row again by the stable identifier.
- Confirm the fields required by the current queue contract can be read exactly once from the DingTalk data shape:
  - `Document_ID`
  - `Document_Key`
  - `Version`
  - `Lang`
  - `Build_family`
  - `Workflow_action`
  - `Git_ref`
  - trigger fields

Evidence to capture:

- row lookup endpoint
- any field name translation needed
- whether multi-select or boolean fields need special normalization

### 4.4 Harmless Writeback

- Update one non-critical text field on the same row.
- Confirm writeback by refreshing the row in DingTalk.
- Then restore the original value if needed.

Evidence to capture:

- update endpoint
- optimistic concurrency requirement if any
- partial update vs full-row replace semantics

### 4.5 File Upload

- Upload one sample `.docx`.
- Confirm the response contains a durable file identifier.
- Confirm the uploaded object remains accessible to the intended tenant audience.

Evidence to capture:

- upload endpoint
- required multipart or pre-signed upload flow
- returned file ID fields

### 4.6 File Link Resolution

- Resolve a tenant-visible link for the uploaded file.
- Confirm the link is usable in a queue `Document_link` field.
- Confirm whether the link is stable or time-limited.

Evidence to capture:

- share-link endpoint or file metadata endpoint
- whether the resulting URL is durable
- any required access policy or audience scope

### 4.7 Workspace Attach Check

- Attempt to attach the uploaded file into the target DingTalk doc or workspace container, if such a container exists in the chosen product.
- If attach is unsupported, explicitly record that the first implementation milestone will use file-link writeback only.

Evidence to capture:

- attach endpoint if available
- permission names needed
- fallback decision: `attach_supported=true|false`

### 4.8 Eventing Check

- Check whether the chosen DingTalk product emits row-change events usable by a worker.
- If yes, record the event name and delivery model.
- If not, declare polling as the initial execution model.

Evidence to capture:

- event name or lack of event support
- whether it is available over Stream mode

## 5. Exit Criteria

Phase 0 is successful only if all of these are true:

- we can read rows with stable identifiers
- we can write a harmless field update back to a row
- we can upload a `.docx`
- we can obtain a tenant-visible link that is suitable for queue writeback
- we have a clear yes or no answer on container attach support

If any of the above fails, do not start the provider refactor.
Choose a different DingTalk data or file product first.

## 6. Expected Deliverables

At the end of Phase 0 we should have:

- one short spike report with screenshots or raw responses
- the final product choice for:
  - queue rows
  - snapshot tables
  - output file storage
- the confirmed permission list
- the confirmed auth mode
- a go or no-go decision for implementing `dingtalk_openapi`

## 7. Repo Follow-Up

Only after this checklist passes should we begin:

- provider-neutral contracts in `tools/`
- `sync.phase2.provider=dingtalk_openapi`
- DingTalk-backed `sync-data`
- DingTalk-backed queue writeback
