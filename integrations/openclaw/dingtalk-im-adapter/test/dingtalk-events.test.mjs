import test from "node:test";
import assert from "node:assert/strict";

import {
  extractMessageEvent,
  isPublishConfirmationText,
  senderAllowed,
  shouldIgnoreMessageEvent,
} from "../lib/dingtalk-events.mjs";

test("extractMessageEvent parses a 1:1 text message and trims content", () => {
  const event = extractMessageEvent({
    msgtype: "text",
    msgId: "msg_1",
    conversationId: "cidp2p",
    conversationType: "1",
    senderStaffId: "staff_1",
    senderNick: "Ada",
    isInAtList: false,
    sessionWebhook: "https://hook/x",
    text: { content: "  查 JE-1000F_US_0.3  " },
  });
  assert.equal(event.messageId, "msg_1");
  assert.equal(event.eventId, "msg_1");
  assert.equal(event.chatId, "cidp2p");
  assert.equal(event.senderId, "staff_1");
  assert.equal(event.isGroup, false);
  assert.equal(event.normalizedText, "查 JE-1000F_US_0.3");
  assert.equal(event.sessionWebhook, "https://hook/x");
});

test("extractMessageEvent keys group messages on openConversationId", () => {
  const event = extractMessageEvent({
    msgtype: "text",
    msgId: "msg_2",
    conversationId: "cidGroupRaw",
    conversationType: "2",
    openConversationId: "cidGroupOpen",
    senderStaffId: "staff_2",
    isInAtList: true,
    text: { content: "构建 JE-2000F" },
  });
  assert.equal(event.isGroup, true);
  assert.equal(event.chatId, "cidGroupOpen");
  assert.equal(event.openConversationId, "cidGroupOpen");
  assert.equal(event.isInAtList, true);
});

test("extractMessageEvent accepts a JSON string and rejects non-text / bad json", () => {
  const event = extractMessageEvent(
    JSON.stringify({ msgtype: "text", msgId: "m", conversationId: "c", conversationType: "1", senderStaffId: "s", text: { content: "hi" } })
  );
  assert.equal(event.normalizedText, "hi");
  assert.equal(extractMessageEvent({ msgtype: "picture", msgId: "m" }), null);
  assert.equal(extractMessageEvent("not json"), null);
});

test("shouldIgnoreMessageEvent enforces fields, empty text, and group mention", () => {
  const ok = extractMessageEvent({ msgtype: "text", msgId: "m", conversationId: "c", conversationType: "1", senderStaffId: "s", text: { content: "hi" } });
  assert.equal(shouldIgnoreMessageEvent(ok, { requireMention: true }), "");
  assert.equal(shouldIgnoreMessageEvent(null, {}), "not_supported");
  assert.equal(shouldIgnoreMessageEvent({ messageId: "", chatId: "c", senderId: "s", normalizedText: "x" }, {}), "missing_required_fields");
  assert.equal(shouldIgnoreMessageEvent({ messageId: "m", chatId: "c", senderId: "s", normalizedText: "" }, {}), "empty_text");

  const group = extractMessageEvent({
    msgtype: "text",
    msgId: "m",
    conversationId: "c",
    conversationType: "2",
    openConversationId: "g",
    senderStaffId: "s",
    isInAtList: false,
    text: { content: "hi" },
  });
  assert.equal(shouldIgnoreMessageEvent(group, { requireMention: true }), "missing_mention");
  assert.equal(shouldIgnoreMessageEvent(group, { requireMention: false }), "");
});

test("senderAllowed is fail-closed on an empty allowlist and supports wildcard", () => {
  assert.equal(senderAllowed("staff_1", []), false);
  assert.equal(senderAllowed("staff_1", ["staff_2"]), false);
  assert.equal(senderAllowed("staff_1", ["staff_1"]), true);
  assert.equal(senderAllowed("anyone", ["*"]), true);
});

test("isPublishConfirmationText matches confirm tokens only", () => {
  assert.equal(isPublishConfirmationText("确认发布"), true);
  assert.equal(isPublishConfirmationText("confirm"), true);
  assert.equal(isPublishConfirmationText("构建"), false);
});
