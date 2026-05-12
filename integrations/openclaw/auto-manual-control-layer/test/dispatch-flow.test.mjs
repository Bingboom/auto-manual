import test from "node:test";
import assert from "node:assert/strict";

import { dispatchBatchCommandFlow, dispatchCommandFlow } from "../lib/dispatch-flow.mjs";

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

test("batch dispatch sends each queue record id independently", async () => {
  const dispatchCalls = [];
  const savedRecords = [];
  const github = {
    async findActiveRunForRecord() {
      return null;
    },
    async dispatchWorkflow(payload) {
      dispatchCalls.push(payload);
    },
    async findDispatchedRun({ queueRecordId }) {
      return {
        id: queueRecordId === "rec_en" ? 101 : 102,
        html_url: `https://example.com/runs/${queueRecordId}`,
      };
    },
  };
  const stateStore = {
    async saveRecord(record) {
      savedRecords.push(record);
      return record;
    },
  };

  const result = await dispatchBatchCommandFlow({
    command: sharedDraftCommand,
    queueRecordIds: ["rec_en", "rec_fr"],
    github,
    stateStore,
    settings,
  });

  assert.equal(dispatchCalls.length, 2);
  assert.deepEqual(dispatchCalls.map((call) => call.inputs.queue_record_id), ["rec_en", "rec_fr"]);
  assert.deepEqual(savedRecords.map((record) => record.queueRecordId), ["rec_en", "rec_en", "rec_fr", "rec_fr"]);
  assert.match(result.text, /Feishu Draft Build Queue batch/);
  assert.match(result.text, /matched_count: 2/);
  assert.match(result.text, /rec_en \| accepted \| run_id=101/);
  assert.match(result.text, /rec_fr \| accepted \| run_id=102/);
});

test("batch dispatch reuses active runs per row", async () => {
  let dispatchCount = 0;
  const github = {
    async findActiveRunForRecord({ queueRecordId }) {
      if (queueRecordId === "rec_en") {
        return {
          id: 201,
          html_url: "https://example.com/runs/active",
          status: "queued",
        };
      }
      return null;
    },
    async dispatchWorkflow() {
      dispatchCount += 1;
    },
    async findDispatchedRun() {
      return {
        id: 202,
        html_url: "https://example.com/runs/new",
      };
    },
  };
  const stateStore = {
    async saveRecord(record) {
      return record;
    },
  };

  const result = await dispatchBatchCommandFlow({
    command: sharedDraftCommand,
    queueRecordIds: ["rec_en", "rec_fr"],
    github,
    stateStore,
    settings,
  });

  assert.equal(dispatchCount, 1);
  assert.match(result.text, /rec_en \| reused \| run_id=201/);
  assert.match(result.text, /rec_fr \| accepted \| run_id=202/);
});
