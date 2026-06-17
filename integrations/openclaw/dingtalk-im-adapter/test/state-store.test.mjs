import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import assert from "node:assert/strict";

import { createStateStore } from "../lib/state-store.mjs";

test("claimProcessedEvent serializes concurrent duplicate claims", async () => {
  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "feishu-im-state-"));
  const stateFile = path.join(tempDir, "state.json");
  const store = createStateStore(stateFile);

  const [first, second] = await Promise.all([
    store.claimProcessedEvent("evt_dup"),
    store.claimProcessedEvent("evt_dup"),
  ]);

  assert.deepEqual([first, second].sort(), [false, true]);
});

test("conversation context is stored per chat and sender", async () => {
  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "feishu-im-state-"));
  const stateFile = path.join(tempDir, "state.json");
  const store = createStateStore(stateFile, { now: () => 1000 });

  await store.rememberConversationContext({
    chatId: "oc_123",
    senderId: "ou_sender",
    messageId: "om_123",
    row: {
      record_id: "rec_context",
      document_id: "JE-1000F_US_0.3",
    },
    queryText: "查 JE-1000F_US_0.3",
    actionName: "query_status",
    ttlSeconds: 600,
  });

  const context = await store.readConversationContext({ chatId: "oc_123", senderId: "ou_sender" });

  assert.equal(context.row.record_id, "rec_context");
  assert.equal(context.actionName, "query_status");
});

test("conversation context can store batch rows and accepted time", async () => {
  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "feishu-im-state-"));
  const stateFile = path.join(tempDir, "state.json");
  const store = createStateStore(stateFile, { now: () => 1000 });

  await store.rememberConversationContext({
    chatId: "oc_123",
    senderId: "ou_sender",
    messageId: "om_123",
    rows: [
      { record_id: "rec_en", document_id: "JE-1000F_EU_en_0.7" },
      { record_id: "rec_fr", document_id: "JE-1000F_EU_fr_0.7" },
    ],
    queryText: "构建 JE-1000F EU 英语和法语",
    actionName: "build_draft_package",
    acceptedAt: "2026-05-04T10:00:00Z",
    requestId: "req_123",
    ttlSeconds: 600,
  });

  const context = await store.readConversationContext({ chatId: "oc_123", senderId: "ou_sender" });

  assert.equal(context.row.record_id, "rec_en");
  assert.equal(context.rows.length, 2);
  assert.equal(context.acceptedAt, "2026-05-04T10:00:00Z");
  assert.equal(context.requestId, "req_123");
});

test("conversation context can be cleared when Feishu rows disappear", async () => {
  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "feishu-im-state-"));
  const stateFile = path.join(tempDir, "state.json");
  const store = createStateStore(stateFile, { now: () => 1000 });

  await store.rememberConversationContext({
    chatId: "oc_123",
    senderId: "ou_sender",
    messageId: "om_123",
    row: { record_id: "rec_deleted" },
    queryText: "这个好了没",
    actionName: "query_status",
    ttlSeconds: 600,
  });

  await store.clearConversationContext({ chatId: "oc_123", senderId: "ou_sender" });
  const context = await store.readConversationContext({ chatId: "oc_123", senderId: "ou_sender" });

  assert.equal(context, null);
});
