import test from "node:test";
import assert from "node:assert/strict";

import { dispatchCommandFlow } from "../lib/dispatch-flow.mjs";

const sharedDraftCommand = {
  commandName: "build-draft",
  workflowFile: "feishu-draft-build-queue.yml",
  workflowName: "Feishu Draft Build Queue",
};

const publishCommand = {
  commandName: "publish",
  workflowFile: "feishu-build-queue.yml",
  workflowName: "Feishu Build Queue",
};

const settings = {
  defaultBranch: "main",
};

test("shared draft dispatch omits queue_record_id and keeps the requested record in tracking", async () => {
  const dispatchCalls = [];
  const savedRecords = [];
  const github = {
    async findRecentActiveRun() {
      return null;
    },
    async findRecentRunByDispatch() {
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
  assert.equal(dispatchCalls[0].inputs.queue_record_id, "");
  assert.equal(savedRecords[0].queueRecordId, "rec_en");
  assert.match(result.text, /run_id: 321/);
});

test("shared draft dispatch reuses a very recent tracked dispatch instead of redispatching", async () => {
  let dispatchCount = 0;
  const github = {
    async findRecentRunByDispatch() {
      return null;
    },
    async findRecentActiveRun() {
      return null;
    },
    async dispatchWorkflow() {
      dispatchCount += 1;
    },
  };
  const stateStore = {
    async getLastRecordForWorkflow() {
      return {
        workflowFile: sharedDraftCommand.workflowFile,
        queueRecordId: "rec_es",
        openclawDispatchNonce: "nonce-123",
        dispatchedAt: new Date().toISOString(),
      };
    },
    async saveRecord() {
      throw new Error("saveRecord should not be called for duplicate shared dispatch reuse");
    },
  };

  const result = await dispatchCommandFlow({
    command: sharedDraftCommand,
    queueRecordId: "rec_fr",
    github,
    stateStore,
    settings,
  });

  assert.equal(dispatchCount, 0);
  assert.match(result.text, /record_id: rec_fr/);
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
