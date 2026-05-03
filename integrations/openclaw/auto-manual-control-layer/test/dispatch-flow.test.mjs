import test from "node:test";
import assert from "node:assert/strict";

import { dispatchCommandFlow } from "../lib/dispatch-flow.mjs";

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
