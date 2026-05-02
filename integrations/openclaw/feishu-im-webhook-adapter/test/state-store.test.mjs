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
