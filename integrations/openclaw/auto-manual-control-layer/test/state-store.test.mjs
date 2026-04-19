import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

import { createStateStore } from "../lib/state-store.mjs";

test("state store tracks the latest record per workflow file", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "auto-manual-state-store-"));
  const stateFile = path.join(root, "state.json");
  const store = createStateStore(stateFile);

  await store.saveRecord({
    workflowFile: "feishu-draft-build-queue.yml",
    queueRecordId: "rec_en",
    runId: "101",
  });
  await store.saveRecord({
    workflowFile: "feishu-build-queue.yml",
    queueRecordId: "rec_publish",
    runId: "202",
  });

  const latestDraft = await store.getLastRecordForWorkflow("feishu-draft-build-queue.yml");
  const latestPublish = await store.getLastRecordForWorkflow("feishu-build-queue.yml");
  const draftByRunId = await store.getRecordByRunId("101");

  assert.equal(latestDraft.queueRecordId, "rec_en");
  assert.equal(latestPublish.queueRecordId, "rec_publish");
  assert.equal(draftByRunId.workflowFile, "feishu-draft-build-queue.yml");
});
