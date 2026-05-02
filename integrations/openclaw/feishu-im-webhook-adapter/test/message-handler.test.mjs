import crypto from "node:crypto";
import test from "node:test";
import assert from "node:assert/strict";

import { createMessageHandler } from "../lib/message-handler.mjs";

const silentLogger = {
  error() {},
};

function basePayload(text, { eventId = "evt_123", messageId = "om_123", chatId = "oc_123", senderId = "ou_sender", chatType = "p2p" } = {}) {
  return JSON.stringify({
    token: "verify_token",
    header: {
      event_type: "im.message.receive_v1",
      event_id: eventId,
    },
    event: {
      sender: {
        sender_id: { open_id: senderId },
      },
      message: {
        message_id: messageId,
        chat_id: chatId,
        chat_type: chatType,
        message_type: "text",
        content: JSON.stringify({ text }),
      },
    },
  });
}

function createMemoryStateStore() {
  const processed = new Set();
  const pending = new Map();
  return {
    async claimProcessedEvent(eventId) {
      if (processed.has(eventId)) {
        return false;
      }
      processed.add(eventId);
      return true;
    },
    async hasProcessedEvent(eventId) {
      return processed.has(eventId);
    },
    async markProcessedEvent(eventId) {
      processed.add(eventId);
    },
    async rememberPendingPublish(payload) {
      pending.set(`${payload.chatId}:${payload.senderId}`, payload);
    },
    async consumePendingPublish({ chatId, senderId }) {
      const key = `${chatId}:${senderId}`;
      const value = pending.get(key) || null;
      pending.delete(key);
      return value;
    },
    async clearExpiredPublishes() {},
  };
}

function encryptPayload(payload, encryptKey, ivHex = "00112233445566778899aabbccddeeff") {
  const key = crypto.createHash("sha256").update(encryptKey).digest();
  const iv = Buffer.from(ivHex, "hex");
  const cipher = crypto.createCipheriv("aes-256-cbc", key, iv);
  const encrypted = Buffer.concat([cipher.update(JSON.stringify(payload), "utf8"), cipher.final()]);
  return Buffer.concat([iv, encrypted]).toString("base64");
}

test("handleHttpRequest returns challenge for url verification", async () => {
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {},
    feishuClient: {},
    logger: silentLogger,
  });

  const result = await handler.handleHttpRequest(JSON.stringify({ token: "verify_token", type: "url_verification", challenge: "abc" }));
  assert.equal(result.statusCode, 200);
  assert.deepEqual(result.body, { challenge: "abc" });
});

test("handleHttpRequest rejects invalid token", async () => {
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {},
    feishuClient: {},
  });

  const result = await handler.handleHttpRequest(JSON.stringify({ token: "bad", type: "url_verification", challenge: "abc" }));
  assert.equal(result.statusCode, 403);
});

test("handleHttpRequest returns challenge for encrypted url verification", async () => {
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      encryptKey: "encrypt-key-demo",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {},
    feishuClient: {},
  });

  const result = await handler.handleHttpRequest(
    JSON.stringify({
      encrypt: encryptPayload({ token: "verify_token", type: "url_verification", challenge: "abc" }, "encrypt-key-demo"),
    })
  );
  assert.equal(result.statusCode, 200);
  assert.deepEqual(result.body, { challenge: "abc" });
});

test("handleHttpRequest rejects encrypted callbacks when encrypt key is missing", async () => {
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {},
    feishuClient: {},
  });

  const result = await handler.handleHttpRequest(
    JSON.stringify({
      encrypt: encryptPayload({ token: "verify_token", type: "url_verification", challenge: "abc" }, "encrypt-key-demo"),
    })
  );
  assert.equal(result.statusCode, 501);
  assert.match(result.body.msg, /FEISHU_IM_ENCRYPT_KEY/i);
});

test("message handler replies with queue status for resolved query_status", async () => {
  const replies = [];
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async resolveAction() {
        return {
          resolution_status: "resolved",
          action_name: "query_status",
          queue_scope: "document-link",
          row: {
            record_id: "rec_123",
            document_id: "JE-1000F_US_0.3",
            workflow_action: "Build Draft Package",
            result: "SUCCESS",
            document_link: "https://example.com/doc.docx",
          },
        };
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(basePayload("查 JE-1000F_US_0.3"));
  assert.equal(result.statusCode, 200);
  await result.backgroundTask();

  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /JE-1000F_US_0.3/);
  assert.match(replies[0].text, /SUCCESS/);
});

test("message handler applies local aliases before resolving actions", async () => {
  const replies = [];
  let resolvedMessage = "";
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
      localProfile: {
        aliases: [{ from: "private target", to: "JE-1000F US", caseSensitive: false, match: "literal" }],
        replyPhrases: {},
        reactions: {},
      },
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async resolveAction(payload) {
        resolvedMessage = payload.messageText;
        return {
          resolution_status: "resolved",
          action_name: "query_status",
          queue_scope: "document-link",
          row: {
            record_id: "rec_123",
            document_id: "JE-1000F_US_0.3",
            workflow_action: "Build Draft Package",
            result: "SUCCESS",
          },
        };
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(basePayload("查一下 private target 草稿包"));
  await result.backgroundTask();

  assert.equal(resolvedMessage, "查一下 JE-1000F US 草稿包");
  assert.equal(replies.length, 1);
});

test("message handler can resolve pronoun follow-ups from conversation context", async () => {
  let resolvedMessage = "";
  const stateStore = {
    ...createMemoryStateStore(),
    async readConversationContext() {
      return {
        row: {
          record_id: "rec_context",
        },
      };
    },
    async rememberConversationContext() {},
    async clearExpiredConversationContexts() {},
  };
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
      conversationContextTtlSeconds: 3600,
    },
    stateStore,
    repoControl: {
      async resolveAction(payload) {
        resolvedMessage = payload.messageText;
        return {
          resolution_status: "resolved",
          action_name: "query_status",
          queue_scope: "document-link",
          row: {
            record_id: "rec_context",
            document_id: "JE-1000F_US_0.3",
            workflow_action: "Build Draft Package",
            result: "SUCCESS",
          },
        };
      },
    },
    feishuClient: {
      async replyTextMessage() {},
    },
  });

  const result = await handler.handleHttpRequest(basePayload("这个好了没"));
  await result.backgroundTask();

  assert.equal(resolvedMessage, "这个好了没 record_id rec_context");
});

test("message handler sends stage reactions when enabled", async () => {
  const reactions = [];
  const replies = [];
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
      enableMessageReactions: true,
      localProfile: {
        aliases: [],
        replyPhrases: {},
        reactions: {
          received: "EYES",
          completed: "OK",
        },
      },
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async resolveAction() {
        return {
          resolution_status: "resolved",
          action_name: "query_status",
          queue_scope: "document-link",
          row: {
            record_id: "rec_123",
            document_id: "JE-1000F_US_0.3",
            workflow_action: "Build Draft Package",
            result: "SUCCESS",
          },
        };
      },
    },
    feishuClient: {
      async addMessageReaction(messageId, emojiType) {
        reactions.push({ messageId, emojiType });
      },
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(basePayload("查 JE-1000F_US_0.3"));
  await result.backgroundTask();

  assert.deepEqual(reactions, [
    { messageId: "om_123", emojiType: "EYES" },
    { messageId: "om_123", emojiType: "OK" },
  ]);
  assert.equal(replies.length, 1);
});

test("message handler stores pending publish confirmation", async () => {
  const replies = [];
  let remembered = null;
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
    },
    stateStore: {
      ...createMemoryStateStore(),
      async rememberPendingPublish(payload) {
        remembered = payload;
      },
    },
    repoControl: {
      async resolveAction() {
        return {
          resolution_status: "confirmation_required",
          action_name: "publish",
          queue_scope: "document-link",
          row: {
            record_id: "rec_publish",
            queue_scope: "document-link",
            document_id: "JE-1000F_US_0.3",
            workflow_action: "Publish",
          },
        };
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(basePayload("发布 JE-1000F_US_0.3"));
  await result.backgroundTask();

  assert.equal(remembered.row.record_id, "rec_publish");
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /确认发布/);
});

test("message handler replies with resolution errors", async () => {
  const replies = [];
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async resolveAction() {
        throw new Error("queue-query preflight failed: missing FEISHU_PHASE2_BASE_TOKEN");
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
    logger: silentLogger,
  });

  const result = await handler.handleHttpRequest(basePayload("你好 你回答我一下"));
  await result.backgroundTask();

  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /执行失败/);
  assert.match(replies[0].text, /FEISHU_PHASE2_BASE_TOKEN/);
});

test("message handler can process a direct event payload without webhook token validation", async () => {
  const replies = [];
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async resolveAction() {
        return {
          resolution_status: "resolved",
          action_name: "query_status",
          queue_scope: "document-link",
          row: {
            record_id: "rec_123",
            document_id: "JE-1000F_US_0.3",
            workflow_action: "Build Draft Package",
            result: "SUCCESS",
          },
        };
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleEventPayload(
    {
      header: {
        event_type: "im.message.receive_v1",
        event_id: "evt_local_1",
      },
      event: {
        sender: {
          sender_id: { open_id: "ou_sender" },
        },
        message: {
          message_id: "om_123",
          chat_id: "oc_123",
          chat_type: "p2p",
          message_type: "text",
          content: JSON.stringify({ text: "查 JE-1000F_US_0.3" }),
        },
      },
    },
    { skipVerification: true }
  );
  await result.backgroundTask();

  assert.equal(result.statusCode, 200);
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /SUCCESS/);
});

test("message handler suppresses duplicate event ids", async () => {
  const replies = [];
  let resolveCalls = 0;
  const stateStore = createMemoryStateStore();
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
    },
    stateStore,
    repoControl: {
      async resolveAction() {
        resolveCalls += 1;
        return {
          resolution_status: "resolved",
          action_name: "query_status",
          queue_scope: "document-link",
          row: {
            record_id: "rec_123",
            document_id: "JE-1000F_US_0.3",
            workflow_action: "Build Draft Package",
            result: "SUCCESS",
          },
        };
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const first = await handler.handleHttpRequest(basePayload("查 JE-1000F_US_0.3", { eventId: "evt_dup" }));
  await first.backgroundTask();
  const second = await handler.handleHttpRequest(basePayload("查 JE-1000F_US_0.3", { eventId: "evt_dup" }));
  await second.backgroundTask();

  assert.equal(resolveCalls, 1);
  assert.equal(replies.length, 1);
});

test("message handler executes confirmed publish from pending state", async () => {
  const replies = [];
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
    },
    stateStore: {
      ...createMemoryStateStore(),
      async consumePendingPublish() {
        return {
          row: {
            record_id: "rec_publish",
            queue_scope: "document-link",
          },
        };
      },
    },
    repoControl: {
      async executeResolvedAction(payload) {
        assert.equal(payload.recordId, "rec_publish");
        assert.equal(payload.confirmPublish, true);
      },
      async queryRow() {
        return {
          rows: [
            {
              record_id: "rec_publish",
              document_id: "JE-1000F_US_0.3",
              workflow_action: "Publish",
              result: "SUCCESS",
              document_link: "https://example.com/publish.pdf",
            },
          ],
        };
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(basePayload("确认发布"));
  await result.backgroundTask();

  assert.equal(replies.length, 2);
  assert.match(replies[0].text, /已确认发布/);
  assert.match(replies[1].text, /SUCCESS/);
});

test("message handler allows publish confirmation without mention in group chats", async () => {
  const replies = [];
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
    },
    stateStore: {
      ...createMemoryStateStore(),
      async consumePendingPublish() {
        return {
          row: {
            record_id: "rec_publish",
            queue_scope: "document-link",
          },
        };
      },
    },
    repoControl: {
      async executeResolvedAction() {},
      async queryRow() {
        return {
          rows: [
            {
              record_id: "rec_publish",
              document_id: "JE-1000F_US_0.3",
              workflow_action: "Publish",
              result: "SUCCESS",
            },
          ],
        };
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(basePayload("确认发布", { chatType: "group" }));
  await result.backgroundTask();

  assert.equal(replies.length, 2);
});
