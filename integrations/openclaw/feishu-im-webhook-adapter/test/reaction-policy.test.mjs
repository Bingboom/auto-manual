import test from "node:test";
import assert from "node:assert/strict";

import { reactionEmojiForStage, sendStageReaction } from "../lib/reaction-policy.mjs";

test("reactionEmojiForStage prefers local reaction overrides", () => {
  assert.equal(reactionEmojiForStage("received", { reactions: { received: "EYES" } }), "EYES");
  assert.equal(reactionEmojiForStage("received", { reactions: {} }), "Get");
  assert.equal(reactionEmojiForStage("completed", { reactions: {} }), "OK");
});

test("sendStageReaction is disabled unless the adapter config enables it", async () => {
  let called = false;
  const sent = await sendStageReaction({
    config: { enableMessageReactions: false },
    feishuClient: {
      async addMessageReaction() {
        called = true;
      },
    },
    messageId: "om_123",
    stage: "received",
  });

  assert.equal(sent, false);
  assert.equal(called, false);
});

test("sendStageReaction adds a Feishu message reaction when enabled", async () => {
  const calls = [];
  const sent = await sendStageReaction({
    config: { enableMessageReactions: true },
    feishuClient: {
      async addMessageReaction(messageId, emojiType) {
        calls.push({ messageId, emojiType });
      },
    },
    localProfile: { reactions: { received: "EYES" } },
    messageId: "om_123",
    stage: "received",
  });

  assert.equal(sent, true);
  assert.deepEqual(calls, [{ messageId: "om_123", emojiType: "EYES" }]);
});
