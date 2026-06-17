import test from "node:test";
import assert from "node:assert/strict";

import { receivedAckText, sendStageReaction } from "../lib/reaction-policy.mjs";

test("received stage sends a one-line text ack when ackOnReceived is on", async () => {
  const sent = [];
  const imClient = {
    async replyTextMessage(messageEvent, text) {
      sent.push({ messageEvent, text });
    },
  };
  const messageEvent = { messageId: "m1" };
  const ok = await sendStageReaction({ config: { ackOnReceived: true }, imClient, messageEvent, stage: "received" });
  assert.equal(ok, true);
  assert.equal(sent.length, 1);
  assert.equal(sent[0].messageEvent, messageEvent);
  assert.equal(sent[0].text, receivedAckText({}));
});

test("received ack respects a custom receivedAckText", async () => {
  const sent = [];
  const imClient = {
    async replyTextMessage(_messageEvent, text) {
      sent.push(text);
    },
  };
  await sendStageReaction({ config: { ackOnReceived: true, receivedAckText: "收到啦" }, imClient, messageEvent: {}, stage: "received" });
  assert.deepEqual(sent, ["收到啦"]);
});

test("received ack is suppressed when ackOnReceived is off", async () => {
  let called = false;
  const imClient = {
    async replyTextMessage() {
      called = true;
    },
  };
  const ok = await sendStageReaction({ config: { ackOnReceived: false }, imClient, messageEvent: {}, stage: "received" });
  assert.equal(ok, false);
  assert.equal(called, false);
});

test("non-received stages never send anything (DingTalk has no reactions)", async () => {
  let called = false;
  const imClient = {
    async replyTextMessage() {
      called = true;
    },
  };
  for (const stage of ["accepted", "completed", "error", "needs_confirmation", "needs_input", "unresolved"]) {
    const ok = await sendStageReaction({ config: { ackOnReceived: true }, imClient, messageEvent: {}, stage });
    assert.equal(ok, false);
  }
  assert.equal(called, false);
});

test("ack failures are swallowed", async () => {
  const imClient = {
    async replyTextMessage() {
      throw new Error("network");
    },
  };
  const ok = await sendStageReaction({
    config: { ackOnReceived: true },
    imClient,
    messageEvent: {},
    stage: "received",
    logger: { warn() {} },
  });
  assert.equal(ok, false);
});
