import test from "node:test";
import assert from "node:assert/strict";

import { dispatchCommandFlow, resolveTrackedRun } from "../lib/dispatch-flow.mjs";

const sharedDraftCommand = {
  commandName: "build-draft",
  workflowFile: "feishu-draft-build-queue.yml",
  workflowName: "Feishu Draft Build Queue",
};

const sharedStartReviewCommand = {
  commandName: "start-review",
  workflowFile: "feishu-start-review.yml",
  workflowName: "Feishu Start Review",
};

const publishCommand = {
  commandName: "publish",
  workflowFile: "feishu-build-queue.yml",
  workflowName: "Feishu Build Queue",
};

const settings = {
  defaultBranch: "main",
};

test("draft dispatch sends queue_record_id and keeps the requested record in tracking", async () => {
  const dispatchCalls = [];
  const savedRecords = [];
  const github = {
    async findActiveRunForRecord() {
      return null;
    },
    async dispatchWorkflow(payload) {
      dispatchCalls.push(payload);
    },
    async findDispatchedRun() {
      return {
        id: 321,
        html_url: "https://example.com/runs/321",
      };
    },
  };
  const stateStore = {
    async getLastRecordForWorkflow() {
      return null;
    },
    async saveRecord(record) {
      savedRecords.push(record);
      return record;
    },
  };

  const result = await dispatchCommandFlow({
    command: sharedDraftCommand,
    queueRecordId: "rec_en",
    github,
    stateStore,
    settings,
  });

  assert.equal(dispatchCalls.length, 1);
  assert.equal(dispatchCalls[0].inputs.queue_record_id, "rec_en");
  assert.equal(savedRecords[0].queueRecordId, "rec_en");
  assert.match(result.text, /run_id: 321/);
});

test("start-review dispatch sends queue_record_id so the worker targets one row", async () => {
  const dispatchCalls = [];
  const savedRecords = [];
  const github = {
    async findActiveRunForRecord() {
      return null;
    },
    async dispatchWorkflow(payload) {
      dispatchCalls.push(payload);
    },
    async findDispatchedRun() {
      return {
        id: 654,
        html_url: "https://example.com/runs/654",
      };
    },
  };
  const stateStore = {
    async getLastRecordForWorkflow() {
      return null;
    },
    async saveRecord(record) {
      savedRecords.push(record);
      return record;
    },
  };

  const result = await dispatchCommandFlow({
    command: sharedStartReviewCommand,
    queueRecordId: "rec_jp",
    github,
    stateStore,
    settings,
  });

  assert.equal(dispatchCalls.length, 1);
  assert.equal(dispatchCalls[0].inputs.queue_record_id, "rec_jp");
  assert.equal(savedRecords[0].queueRecordId, "rec_jp");
  assert.match(result.text, /run_id: 654/);
});

test("draft dispatch reuses an active run for the same record id", async () => {
  let dispatchCount = 0;
  const github = {
    async findActiveRunForRecord({ queueRecordId }) {
      return {
        id: 777,
        html_url: `https://example.com/runs/${queueRecordId}`,
        status: "queued",
      };
    },
    async dispatchWorkflow() {
      dispatchCount += 1;
    },
  };
  const stateStore = {
    async saveRecord() {
      throw new Error("saveRecord should not be called for duplicate dispatch reuse");
    },
  };

  const result = await dispatchCommandFlow({
    command: sharedDraftCommand,
    queueRecordId: "rec_draft",
    github,
    stateStore,
    settings,
  });

  assert.equal(dispatchCount, 0);
  assert.match(result.text, /record_id: rec_draft/);
  assert.match(result.text, /run_id: 777/);
  assert.match(result.text, /status: queued/);
});

test("record-scoped commands still dedupe on the same record id", async () => {
  let dispatchCount = 0;
  const github = {
    async findActiveRunForRecord({ queueRecordId }) {
      return {
        id: 888,
        html_url: `https://example.com/runs/${queueRecordId}`,
        status: "in_progress",
      };
    },
    async dispatchWorkflow() {
      dispatchCount += 1;
    },
  };
  const stateStore = {
    async getLastRecordForWorkflow() {
      return null;
    },
    async saveRecord() {
      throw new Error("saveRecord should not be called when a record-scoped duplicate run exists");
    },
  };

  const result = await dispatchCommandFlow({
    command: publishCommand,
    queueRecordId: "rec_publish",
    github,
    stateStore,
    settings,
  });

  assert.equal(dispatchCount, 0);
  assert.match(result.text, /record_id: rec_publish/);
  assert.match(result.text, /run_id: 888/);
});

test("dispatch reports accepted (not failure) when post-dispatch discovery throws", async () => {
  const dispatchCalls = [];
  const savedRecords = [];
  const github = {
    async findActiveRunForRecord() {
      return null;
    },
    async dispatchWorkflow(payload) {
      dispatchCalls.push(payload);
    },
    async findDispatchedRun() {
      const error = new TypeError("fetch failed");
      error.cause = { code: "ECONNRESET" };
      throw error;
    },
  };
  const stateStore = {
    async saveRecord(record) {
      savedRecords.push(record);
      return record;
    },
  };

  const result = await dispatchCommandFlow({
    command: sharedDraftCommand,
    queueRecordId: "rec_en",
    github,
    stateStore,
    settings,
  });

  // The dispatch POST succeeded, so a failed run-id lookup must not be reported
  // as a failure: the workflow is still triggered exactly once.
  assert.equal(dispatchCalls.length, 1);
  assert.match(result.text, /Dispatch accepted/);
  assert.doesNotMatch(result.text, /run_id:/);
  // The pending record (with the nonce) is persisted so a later status reconciles.
  assert.equal(savedRecords.length, 1);
  assert.equal(savedRecords[0].queueRecordId, "rec_en");
  assert.equal(savedRecords[0].runId, undefined);
});

test("dispatch reports accepted-pending when the run is not exposed yet", async () => {
  const github = {
    async findActiveRunForRecord() {
      return null;
    },
    async dispatchWorkflow() {},
    async findDispatchedRun() {
      return null;
    },
  };
  const stateStore = {
    async saveRecord(record) {
      return record;
    },
  };

  const result = await dispatchCommandFlow({
    command: sharedStartReviewCommand,
    queueRecordId: "rec_jp",
    github,
    stateStore,
    settings,
  });

  assert.match(result.text, /Dispatch accepted/);
  assert.doesNotMatch(result.text, /run_id:/);
});

test("resolveTrackedRun degrades to last-known state on a transient getRun error", async () => {
  const tracked = {
    workflowName: "Feishu Draft Build Queue",
    workflowFile: "feishu-draft-build-queue.yml",
    queueRecordId: "rec_en",
    runId: "321",
    runUrl: "https://example.com/runs/321",
    dispatchedAt: "2026-05-29T10:00:00.000Z",
  };
  const github = {
    async getRun() {
      const error = new TypeError("fetch failed");
      error.cause = { code: "ETIMEDOUT" };
      throw error;
    },
  };
  const stateStore = {
    async getLastRecord() {
      return tracked;
    },
  };

  const resolved = await resolveTrackedRun({ github, stateStore, settings, requestedRunId: null });
  assert.equal(resolved.run, null);
  assert.equal(resolved.tracked.runId, "321");
  assert.match(resolved.observationError, /fetch failed/);
});

test("resolveTrackedRun rethrows a definitive (non-transient) getRun error", async () => {
  const tracked = { runId: "321", queueRecordId: "rec_en" };
  const github = {
    async getRun() {
      const error = new Error("GitHub API 404: not found");
      error.httpStatus = 404;
      throw error;
    },
  };
  const stateStore = {
    async getLastRecord() {
      return tracked;
    },
  };

  await assert.rejects(
    resolveTrackedRun({ github, stateStore, settings, requestedRunId: null }),
    /GitHub API 404/
  );
});

test("resolveTrackedRun keeps the run but flags observationError when the artifacts read transiently fails", async () => {
  const tracked = { runId: "321", queueRecordId: "rec_en", runUrl: "" };
  const savedRecords = [];
  const github = {
    async getRun() {
      return {
        id: 321,
        html_url: "https://example.com/runs/321",
        status: "completed",
        conclusion: "success",
      };
    },
    async listArtifacts() {
      throw new Error("GitHub API 502: bad gateway");
    },
    async readMetadataArtifact() {
      return null;
    },
  };
  const stateStore = {
    async getLastRecord() {
      return tracked;
    },
    async saveRecord(record) {
      savedRecords.push(record);
      return record;
    },
  };

  const resolved = await resolveTrackedRun({ github, stateStore, settings, requestedRunId: null });
  assert.equal(resolved.run.id, 321);
  assert.equal(resolved.run.conclusion, "success");
  assert.deepEqual(resolved.artifacts, []);
  assert.match(resolved.observationError, /502/);
  assert.equal(savedRecords.length, 1);
});

test("resolveTrackedRun observes an explicit run id with no local record (external dispatch)", async () => {
  // The IM adapters dispatch via `build.py queue-execute`, so the run id is not
  // in this state store. A status query must still fetch the real state instead
  // of returning null (which downstream renders as "processing" forever).
  const savedRecords = [];
  const github = {
    async getRun(runId) {
      assert.equal(runId, "999");
      return {
        id: 999,
        html_url: "https://example.com/runs/999",
        status: "completed",
        conclusion: "failure",
      };
    },
    async listArtifacts() {
      return [];
    },
    async readMetadataArtifact() {
      return null;
    },
  };
  const stateStore = {
    async getRecordByRunId() {
      return null; // externally dispatched: nothing tracked here
    },
    async saveRecord(record) {
      savedRecords.push(record);
      return record;
    },
  };

  const resolved = await resolveTrackedRun({ github, stateStore, settings, requestedRunId: "999" });
  assert.equal(resolved.tracked, null);
  assert.equal(resolved.run.id, 999);
  assert.equal(resolved.run.conclusion, "failure");
  assert.equal(savedRecords.length, 0); // must not fabricate a record it does not own
});

test("resolveTrackedRun still returns empty when there is no id and no last record", async () => {
  const github = {
    async getRun() {
      throw new Error("getRun should not be called");
    },
  };
  const stateStore = {
    async getLastRecord() {
      return null;
    },
  };

  const resolved = await resolveTrackedRun({ github, stateStore, settings, requestedRunId: null });
  assert.equal(resolved.tracked, null);
  assert.equal(resolved.run, null);
});
