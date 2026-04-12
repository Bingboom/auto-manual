import test from "node:test";
import assert from "node:assert/strict";

import {
  extractMessageEvent,
  extractMessageText,
  hasMentionMarkup,
  isEncryptedEventPayload,
  isPublishConfirmationText,
  isUrlVerification,
  parseEventPayload,
  shouldIgnoreMessageEvent,
  stripMentionMarkup,
  validateVerificationToken,
} from "../lib/feishu-events.mjs";

test("parseEventPayload parses raw json", () => {
  assert.deepEqual(parseEventPayload('{"type":"url_verification","challenge":"abc"}'), {
    type: "url_verification",
    challenge: "abc",
  });
});

test("validateVerificationToken supports top-level and header token", () => {
  assert.equal(validateVerificationToken({ token: "tok" }, "tok"), true);
  assert.equal(validateVerificationToken({ header: { token: "tok" } }, "tok"), true);
  assert.equal(validateVerificationToken({ token: "bad" }, "tok"), false);
});

test("isUrlVerification detects challenge payloads", () => {
  assert.equal(isUrlVerification({ type: "url_verification", challenge: "abc" }), true);
  assert.equal(isUrlVerification({ type: "event_callback" }), false);
});

test("isEncryptedEventPayload detects unsupported encrypted callbacks", () => {
  assert.equal(isEncryptedEventPayload({ encrypt: "ciphertext" }), true);
  assert.equal(isEncryptedEventPayload({ encrypt: "" }), false);
  assert.equal(isEncryptedEventPayload({ token: "tok" }), false);
});

test("extractMessageText and mention stripping normalize text content", () => {
  const text = extractMessageText(JSON.stringify({ text: '<at user_id="ou_xxx">Bot</at> 开始 review JE-1000F_US_0.3' }));
  assert.equal(hasMentionMarkup(text), true);
  assert.equal(stripMentionMarkup(text), "开始 review JE-1000F_US_0.3");
});

test("extractMessageEvent reads Feishu im.message.receive_v1 payload", () => {
  const event = extractMessageEvent({
    header: {
      event_type: "im.message.receive_v1",
      event_id: "evt_123",
    },
    event: {
      sender: {
        sender_id: { open_id: "ou_sender" },
      },
      message: {
        message_id: "om_123",
        chat_id: "oc_123",
        chat_type: "group",
        message_type: "text",
        content: JSON.stringify({ text: '<at user_id="ou_bot">Bot</at> 发布 JE-1000F_US_0.3' }),
      },
    },
  });

  assert.equal(event.eventId, "evt_123");
  assert.equal(event.senderId, "ou_sender");
  assert.equal(event.normalizedText, "发布 JE-1000F_US_0.3");
});

test("shouldIgnoreMessageEvent enforces mentions in group chats", () => {
  const messageEvent = {
    messageId: "om_123",
    chatId: "oc_123",
    senderId: "ou_sender",
    senderType: "user",
    normalizedText: "开始 review JE-1000F_US_0.3",
    hasMention: false,
    chatType: "group",
  };
  assert.equal(shouldIgnoreMessageEvent(messageEvent, { requireMention: true }), "missing_mention");
  assert.equal(shouldIgnoreMessageEvent(messageEvent, { requireMention: false }), "");
});

test("isPublishConfirmationText supports chinese and english confirmation", () => {
  assert.equal(isPublishConfirmationText("确认发布"), true);
  assert.equal(isPublishConfirmationText("confirm"), true);
  assert.equal(isPublishConfirmationText("发布 JE-1000F"), false);
});
