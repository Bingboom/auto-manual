import test from "node:test";
import assert from "node:assert/strict";

import { createMessageHandler } from "../lib/message-handler.mjs";

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

test("handleHttpRequest rejects encrypted callbacks explicitly", async () => {
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

  const result = await handler.handleHttpRequest(JSON.stringify({ encrypt: "ciphertext" }));
  assert.equal(result.statusCode, 501);
  assert.match(result.body.msg, /encrypted callbacks/i);
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

test("message handler returns current DingTalk control config", async () => {
  const replies = [];
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async queryDingTalkControlConfig() {
        return {
          record_id: "rec_control",
          operator_union_id: "union-123",
          default_target_node_id: "node-123",
          default_target_node_url: "https://alidocs.dingtalk.com/i/nodes/node-123",
        };
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(basePayload("查看钉钉配置"));
  await result.backgroundTask();

  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /operator_union_id: union-123/);
  assert.match(replies[0].text, /default_target_node_id: node-123/);
});

test("message handler updates DingTalk control config from explicit bind command", async () => {
  const replies = [];
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async updateDingTalkControlConfig(payload) {
        assert.deepEqual(payload, {
          operatorUnionId: "union-123",
          targetNodeUrl: "https://alidocs.dingtalk.com/i/nodes/node-123",
          recordId: "",
        });
        return {
          record_id: "rec_control",
          operator_union_id: payload.operatorUnionId,
          default_target_node_id: "node-123",
          default_target_node_url: payload.targetNodeUrl,
        };
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(
    basePayload("绑定钉钉 union-123 https://alidocs.dingtalk.com/i/nodes/node-123")
  );
  await result.backgroundTask();

  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /已更新钉钉上传控制配置/);
  assert.match(replies[0].text, /default_target_node_url: https:\/\/alidocs\.dingtalk\.com\/i\/nodes\/node-123/);
});

test("message handler returns DingTalk bind usage when operator id is missing", async () => {
  const replies = [];
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {},
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(
    basePayload("绑定钉钉 https://alidocs.dingtalk.com/i/nodes/node-123")
  );
  await result.backgroundTask();

  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /operator_union_id/);
  assert.match(replies[0].text, /dingtalk-bind/);
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
              document_link: "https://example.com/publish.docx",
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
