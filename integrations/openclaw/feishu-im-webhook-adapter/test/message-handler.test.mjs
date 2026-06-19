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

test("message handler answers manual index lookups before queue resolution", async () => {
  const replies = [];
  let resolvedQueue = false;
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
      manualIndexLimit: 5,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async queryManualIndex(payload) {
        assert.equal(payload.limit, 5);
        return {
          matched: true,
          query_type: "lookup",
          summary: "Matched 1 manual index row(s).",
          matched_count: 1,
          returned_count: 1,
          rows: [
            {
              record_id: "rec_manual",
              product_models: ["JE-2000F"],
              manual_name: "Jackery Explorer 2000 User Manual V2.0",
              region: ["美加规"],
              source_lang: ["EN"],
              version: ["V2.0"],
              archived_at: "2026-04-30 00:00:00",
              manual_link: "https://alidocs.example/je2000f",
            },
          ],
        };
      },
      async resolveAction() {
        resolvedQueue = true;
        return { resolution_status: "target_not_found", summary: "unexpected" };
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(basePayload("查 JE-2000F 的说明书链接"));
  await result.backgroundTask();

  assert.equal(resolvedQueue, false);
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /发布文档管理表/);
  assert.match(replies[0].text, /JE-2000F/);
  assert.match(replies[0].text, /https:\/\/alidocs\.example\/je2000f/);
});

test("message handler keeps build-copy requests on the queue path", async () => {
  let manualIndexQueries = 0;
  let resolvedQueue = false;
  const replies = [];
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async queryManualIndex() {
        manualIndexQueries += 1;
        return { matched: true };
      },
      async resolveAction() {
        resolvedQueue = true;
        return {
          resolution_status: "target_not_found",
          summary: "No matching queue rows.",
        };
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(basePayload("输出JE-1000F的所有欧规说明书文案"));
  await result.backgroundTask();

  assert.equal(manualIndexQueries, 0);
  assert.equal(resolvedQueue, true);
  assert.match(replies[0].text, /No matching queue rows/);
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

test("message handler reuses safe selector context for execution follow-ups", async () => {
  let resolvedMessage = "";
  const stateStore = {
    ...createMemoryStateStore(),
    async readConversationContext() {
      return {
        row: {
          record_id: "rec_context",
          document_id: "JE-1000F_EU_en_0.7",
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
          resolution_status: "resolved_batch",
          action_name: "build_draft_package",
          queue_scope: "document-link",
          matched_count: 2,
          candidates: [
            { record_id: "rec_en", queue_scope: "document-link", document_id: "JE-1000F_EU_en_0.7", lang: "en" },
            { record_id: "rec_fr", queue_scope: "document-link", document_id: "JE-1000F_EU_fr_0.7", lang: "fr" },
          ],
        };
      },
      async executeResolvedAction() {
        return { freshness_status: "stale_result" };
      },
    },
    feishuClient: {
      async replyTextMessage() {},
    },
  });

  const result = await handler.handleHttpRequest(basePayload("我来补跑英语和法语"));
  await result.backgroundTask();

  assert.equal(resolvedMessage, "我来补跑英语和法语 JE-1000F EU 0.7");
  assert.doesNotMatch(resolvedMessage, /record_id/);
});

test("message handler answers batch status follow-ups from stored rows", async () => {
  const replies = [];
  const queried = [];
  const stateStore = {
    ...createMemoryStateStore(),
    async readConversationContext() {
      return {
        actionName: "build_draft_package",
        acceptedAt: "2026-05-04T10:00:00Z",
        rows: [
          { record_id: "rec_en", queue_scope: "document-link", document_id: "JE-1000F_EU_en_0.7" },
          { record_id: "rec_fr", queue_scope: "document-link", document_id: "JE-1000F_EU_fr_0.7" },
        ],
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
      async queryRow(payload) {
        queried.push(payload);
        return {
          rows: [
            {
              record_id: payload.recordId,
              document_id: payload.recordId === "rec_en" ? "JE-1000F_EU_en_0.7" : "JE-1000F_EU_fr_0.7",
              workflow_action: "Build Draft Package",
              result: "SUCCESS | built_at=2026-05-04T10:02:00+00:00",
              freshness_status: "fresh_success",
              document_link: payload.recordId === "rec_en" ? "https://example.com/en.docx" : "https://example.com/fr.docx",
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

  const result = await handler.handleHttpRequest(basePayload("发"));
  await result.backgroundTask();

  assert.equal(queried.length, 2);
  assert.equal(queried[0].freshSince, "2026-05-04T10:00:00Z");
  assert.equal(replies.length, 3);
  assert.match(replies[0].text, /fresh_success/);
  assert.doesNotMatch(replies[0].text, /https:\/\/example.com\/en.docx/);
  assert.equal(replies[1].text, "https://example.com/en.docx");
  assert.equal(replies[2].text, "https://example.com/fr.docx");
});

test("message handler does not replay deleted rows from batch context", async () => {
  const replies = [];
  let cleared = false;
  const stateStore = {
    ...createMemoryStateStore(),
    async readConversationContext() {
      return {
        actionName: "build_draft_package",
        acceptedAt: "2026-05-04T10:00:00Z",
        rows: [
          { record_id: "rec_deleted", queue_scope: "document-link", document_id: "JE-1000F_EU_de_1.0" },
          { record_id: "rec_deleted_2", queue_scope: "document-link", document_id: "JE-1000F_EU_it_1.0" },
        ],
      };
    },
    async rememberConversationContext() {
      throw new Error("deleted context should not be remembered again");
    },
    async clearConversationContext() {
      cleared = true;
    },
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
      async queryRow() {
        return { rows: [] };
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(basePayload("这个好了没"));
  await result.backgroundTask();

  assert.equal(cleared, true);
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /matched_count: 0/);
  assert.match(replies[0].text, /Feishu row not found/);
  assert.doesNotMatch(replies[0].text, /JE-1000F_EU_de_1\.0/);
});

test("message handler runs cloud-doc backport dry-run before queue resolution", async () => {
  const replies = [];
  let resolved = false;
  let backportPayload = null;
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
      cloudDocBackportAllowedSenderIds: ["ou_sender"],
      cloudDocBackportAllowWrite: false,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async resolveAction() {
        resolved = true;
        throw new Error("queue resolver should not run");
      },
      async runCloudDocBackportReview(payload) {
        backportPayload = payload;
        return {
          result: "DRY_RUN",
          mode: "dry-run",
          manifest_path: "reports/cloud_doc_backport/run-1/cloud_doc_backport_run.json",
          reports: {
            run_markdown: "reports/cloud_doc_backport/run-1/cloud_doc_backport_run.md",
            diff_markdown: "reports/cloud_doc_backport/run-1/cloud_doc_backport_report.md",
            apply_markdown: "reports/cloud_doc_backport/run-1/cloud_doc_backport_apply.md",
            source_table_suggestions_markdown:
              "reports/cloud_doc_backport/run-1/cloud_doc_backport_source_table_suggestions.md",
          },
          summary: {
            pr_ready: false,
            changed: false,
            source_table_suggestions: 1,
          },
          next_actions: ["Review the apply report, then rerun with --write."],
        };
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const text =
    "cloud-doc backport https://test.feishu.cn/wiki/MbI4w8xLyi8NYnkoe4acAs9Hnvc docs/_review/JE-2000F/EU/page/00_preface.rst";
  const result = await handler.handleHttpRequest(basePayload(text));
  await result.backgroundTask();

  assert.equal(resolved, false);
  assert.equal(backportPayload.docUrl, "https://test.feishu.cn/wiki/MbI4w8xLyi8NYnkoe4acAs9Hnvc");
  assert.equal(backportPayload.sourcePath, "docs/_review/JE-2000F/EU/page/00_preface.rst");
  assert.equal(backportPayload.write, false);
  assert.equal(replies.length, 2);
  assert.match(replies[0].text, /已接受云文档修订回填任务/);
  assert.match(replies[1].text, /result: DRY_RUN/);
  assert.match(replies[1].text, /source_table_suggestions: 1/);
  assert.match(replies[1].text, /source_table_report:/);
});

test("message handler infers cloud-doc backport source path before running", async () => {
  const replies = [];
  let inferencePayload = null;
  let backportPayload = null;
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
      cloudDocBackportAllowedSenderIds: ["ou_sender"],
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async inferCloudDocBackportSource(payload) {
        inferencePayload = payload;
        return {
          status: "resolved",
          reason: "single_review_source_candidate",
          sourcePath: "docs/_review/JE-2000F/EU/page/00_preface.rst",
          targetHint: payload.targetHint,
          candidates: [{ sourcePath: "docs/_review/JE-2000F/EU/page/00_preface.rst" }],
        };
      },
      async runCloudDocBackportReview(payload) {
        backportPayload = payload;
        return {
          result: "DRY_RUN",
          mode: "dry-run",
          manifest_path: "reports/cloud_doc_backport/run-1/cloud_doc_backport_run.json",
          reports: {},
          summary: {
            pr_ready: false,
            changed: false,
            source_table_suggestions: 0,
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

  const text =
    "根据这个文档回填修订 https://test.feishu.cn/wiki/MbI4w8xLyi8NYnkoe4acAs9Hnvc manual_je2000f_eu_en_0.7 副本";
  const result = await handler.handleHttpRequest(basePayload(text));
  await result.backgroundTask();

  assert.equal(inferencePayload.docUrl, "https://test.feishu.cn/wiki/MbI4w8xLyi8NYnkoe4acAs9Hnvc");
  assert.deepEqual(inferencePayload.targetHint, {
    model: "JE-2000F",
    region: "EU",
    lang: "en",
    version: "0.7",
  });
  assert.equal(backportPayload.sourcePath, "docs/_review/JE-2000F/EU/page/00_preface.rst");
  assert.equal(replies.length, 2);
  assert.match(replies[0].text, /source_inference: single_review_source_candidate/);
  assert.match(replies[1].text, /result: DRY_RUN/);
});

test("message handler requires cloud-doc backport allowlist", async () => {
  const replies = [];
  let backportCalled = false;
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
      cloudDocBackportAllowedSenderIds: ["ou_other"],
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async runCloudDocBackportReview() {
        backportCalled = true;
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(
    basePayload(
      "cloud-doc backport https://test.feishu.cn/wiki/MbI4w8xLyi8NYnkoe4acAs9Hnvc docs/_review/JE-2000F/EU/page/00_preface.rst"
    )
  );
  await result.backgroundTask();

  assert.equal(backportCalled, false);
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOWED_SENDERS/);
});

test("message handler asks for review source path before cloud-doc backport", async () => {
  const replies = [];
  let backportCalled = false;
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
      cloudDocBackportAllowedSenderIds: ["ou_sender"],
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async runCloudDocBackportReview() {
        backportCalled = true;
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(
    basePayload("把这个云文档修订回填 https://test.feishu.cn/wiki/MbI4w8xLyi8NYnkoe4acAs9Hnvc")
  );
  await result.backgroundTask();

  assert.equal(backportCalled, false);
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /docs\/_review/);
});

test("message handler blocks explicit cloud-doc backport write when adapter write mode is disabled", async () => {
  const replies = [];
  let backportCalled = false;
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
      cloudDocBackportAllowedSenderIds: ["ou_sender"],
      cloudDocBackportAllowWrite: false,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async runCloudDocBackportReview() {
        backportCalled = true;
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(
    basePayload(
      "cloud-doc backport --write https://test.feishu.cn/wiki/MbI4w8xLyi8NYnkoe4acAs9Hnvc docs/_review/JE-2000F/EU/page/00_preface.rst"
    )
  );
  await result.backgroundTask();

  assert.equal(backportCalled, false);
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /ALLOW_WRITE=true/);
});

test("message handler blocks cloud-doc backport PR creation when adapter PR mode is disabled", async () => {
  const replies = [];
  let prCalled = false;
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
      cloudDocBackportAllowedSenderIds: ["ou_sender"],
      cloudDocBackportAllowPrCreate: false,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async openCloudDocBackportPr() {
        prCalled = true;
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(
    basePayload("cloud-doc backport-pr reports/cloud_doc_backport/run-1/cloud_doc_backport_run.json")
  );
  await result.backgroundTask();

  assert.equal(prCalled, false);
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /ALLOW_PR_CREATE=true/);
});

test("message handler opens cloud-doc backport PR before queue resolution", async () => {
  const replies = [];
  let resolved = false;
  let prPayload = null;
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
      cloudDocBackportAllowedSenderIds: ["ou_sender"],
      cloudDocBackportAllowPrCreate: true,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async resolveAction() {
        resolved = true;
        throw new Error("queue resolver should not run");
      },
      async openCloudDocBackportPr(payload) {
        prPayload = payload;
        return {
          result: "PR_OPENED",
          pr_url: "https://github.com/Bingboom/auto-manual/pull/999",
          branch: "review/JE-2000F-EU-cloud-doc",
          commit: "abc123",
          source_path: "docs/_review/JE-2000F/EU/page/00_preface.rst",
          manifest_path: "reports/cloud_doc_backport/run-1/cloud_doc_backport_run.json",
          source_table_suggestions: 1,
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
    basePayload(
      "cloud-doc backport-pr reports/cloud_doc_backport/run-1/cloud_doc_backport_run.json --branch review/JE-2000F-EU-cloud-doc"
    )
  );
  await result.backgroundTask();

  assert.equal(resolved, false);
  assert.equal(prPayload.manifestPath, "reports/cloud_doc_backport/run-1/cloud_doc_backport_run.json");
  assert.equal(prPayload.branchName, "review/JE-2000F-EU-cloud-doc");
  assert.equal(replies.length, 2);
  assert.match(replies[0].text, /已接受云文档修订 PR 请求/);
  assert.match(replies[1].text, /PR_OPENED/);
  assert.match(replies[1].text, /pull\/999/);
});

const APPROVAL_HASH = "a".repeat(64);

function approvalHandler({
  allowSourceWrite = false,
  bindings = [],
  allowTmWrite = false,
  tmBinding = "",
  repoOverrides = {},
  replies,
  audits,
} = {}) {
  return createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
      cloudDocBackportAllowedSenderIds: ["ou_sender"],
      cloudDocBackportAllowSourceWrite: allowSourceWrite,
      cloudDocBackportSourceTableBindings: bindings,
      cloudDocBackportAllowTmWrite: allowTmWrite,
      cloudDocBackportTmBinding: tmBinding,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async resolveAction() {
        throw new Error("queue resolver should not run");
      },
      async recordCloudDocBackportApproval(entry) {
        audits.push(entry);
      },
      ...repoOverrides,
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });
}

test("source-table approval runs dry-run when source-write is disabled", async () => {
  const replies = [];
  const audits = [];
  let applyPayload = null;
  const handler = approvalHandler({
    allowSourceWrite: false,
    replies,
    audits,
    repoOverrides: {
      async applyCloudDocBackportSourceTable(payload) {
        applyPayload = payload;
        return {
          external_write: false,
          run_id: payload.runId,
          summary: { total: 1, apply: 1, skip: 0, written: 0, verify_failed: 0, error: 0 },
          applied: [{ status: "planned", table: "Spec_Master", field: "Value_uk", delta_hash: APPROVAL_HASH }],
          apply_path: "reports/cloud_doc_backport/feishu-im-run-1/cloud_doc_backport_source_table_apply.json",
        };
      },
    },
  });

  const result = await handler.handleHttpRequest(basePayload(`cloud-doc approve feishu-im-run-1 ${APPROVAL_HASH}`));
  await result.backgroundTask();

  assert.equal(applyPayload.write, false);
  assert.equal(applyPayload.runId, "feishu-im-run-1");
  assert.deepEqual(applyPayload.approvedHashes, [APPROVAL_HASH]);
  assert.equal(replies.length, 2);
  assert.match(replies[0].text, /mode: dry-run/);
  assert.match(replies[1].text, /plan: apply 1/);
  assert.match(replies[1].text, /ALLOW_SOURCE_WRITE/);
  assert.equal(audits.length, 1);
  assert.equal(audits[0].decision, "approve");
  assert.equal(audits[0].external_write, false);
});

test("source-table approval writes to Bitable when enabled with bindings", async () => {
  const replies = [];
  const audits = [];
  let applyPayload = null;
  const handler = approvalHandler({
    allowSourceWrite: true,
    bindings: ["Spec_Master=base1:tbl1"],
    replies,
    audits,
    repoOverrides: {
      async applyCloudDocBackportSourceTable(payload) {
        applyPayload = payload;
        return {
          external_write: true,
          run_id: payload.runId,
          summary: { total: 1, apply: 1, skip: 0, written: 1, verify_failed: 0, error: 0 },
          applied: [{ status: "written", table: "Spec_Master", field: "Value_uk", delta_hash: APPROVAL_HASH }],
          apply_path: "reports/cloud_doc_backport/feishu-im-run-1/cloud_doc_backport_source_table_apply.json",
        };
      },
    },
  });

  const result = await handler.handleHttpRequest(basePayload(`cloud-doc approve feishu-im-run-1 ${APPROVAL_HASH}`));
  await result.backgroundTask();

  assert.equal(applyPayload.write, true);
  assert.deepEqual(applyPayload.tableBindings, ["Spec_Master=base1:tbl1"]);
  assert.match(replies[0].text, /mode: write \(Bitable\)/);
  assert.match(replies[1].text, /written: 1/);
  assert.equal(audits[0].external_write, true);
});

test("source-table rejection records audit and never writes", async () => {
  const replies = [];
  const audits = [];
  const handler = approvalHandler({
    replies,
    audits,
    repoOverrides: {
      async applyCloudDocBackportSourceTable() {
        throw new Error("reject must never apply");
      },
    },
  });

  const result = await handler.handleHttpRequest(basePayload(`cloud-doc reject feishu-im-run-1 ${APPROVAL_HASH}`));
  await result.backgroundTask();

  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /已记录源表回写拒绝/);
  assert.equal(audits.length, 1);
  assert.equal(audits[0].decision, "reject");
  assert.equal(audits[0].result, "rejected");
});

test("source-table approval enforces the sender allowlist", async () => {
  const replies = [];
  const audits = [];
  let applied = false;
  const handler = approvalHandler({
    replies,
    audits,
    repoOverrides: {
      async applyCloudDocBackportSourceTable() {
        applied = true;
        return {};
      },
    },
  });

  const result = await handler.handleHttpRequest(
    basePayload(`cloud-doc approve feishu-im-run-1 ${APPROVAL_HASH}`, { senderId: "ou_intruder" })
  );
  await result.backgroundTask();

  assert.equal(applied, false);
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /ALLOWED_SENDERS/);
});

test("source-table approval forwards the TM write gate + binding to the executor", async () => {
  const replies = [];
  const audits = [];
  let applyPayload = null;
  const handler = approvalHandler({
    allowTmWrite: true,
    tmBinding: "bascnTM:tblTM",
    replies,
    audits,
    repoOverrides: {
      async applyCloudDocBackportSourceTable(payload) {
        applyPayload = payload;
        return {
          external_write: false,
          run_id: payload.runId,
          summary: { apply: 0, skip: 0, written: 0, verify_failed: 0, error: 0 },
          applied: [],
          translation_apply: { external_write: true, summary: { apply: 1, written: 1, already: 0, skip: 0, verify_failed: 0, error: 0 } },
        };
      },
    },
  });

  const result = await handler.handleHttpRequest(basePayload(`cloud-doc approve feishu-im-run-1 ${APPROVAL_HASH}`));
  await result.backgroundTask();

  assert.equal(applyPayload.tmWrite, true);
  assert.equal(applyPayload.tmBinding, "bascnTM:tblTM");
  assert.match(replies[1].text, /tm_writes: write/);
});

test("message handler does not fall back to a stale single row when fresh lookup is missing", async () => {
  const replies = [];
  let cleared = false;
  const stateStore = {
    ...createMemoryStateStore(),
    async readConversationContext() {
      return {
        actionName: "build_draft_package",
        acceptedAt: "2026-05-04T10:00:00Z",
        row: { record_id: "rec_deleted", queue_scope: "document-link" },
      };
    },
    async rememberConversationContext() {
      throw new Error("missing row should not be remembered again");
    },
    async clearConversationContext() {
      cleared = true;
    },
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
      async resolveAction() {
        return {
          resolution_status: "resolved",
          action_name: "query_status",
          queue_scope: "document-link",
          row: {
            record_id: "rec_deleted",
            queue_scope: "document-link",
            document_id: "JE-1000F_EU_de_1.0",
            result: "SUCCESS",
          },
        };
      },
      async queryRow() {
        return { rows: [] };
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(basePayload("这个好了没"));
  await result.backgroundTask();

  assert.equal(cleared, true);
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /重新查了 Feishu 多维表/);
  assert.doesNotMatch(replies[0].text, /SUCCESS/);
});

test("message handler formats multi-row query status without dispatching builds", async () => {
  const replies = [];
  let executed = false;
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
      conversationContextTtlSeconds: 3600,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async resolveAction() {
        return {
          resolution_status: "resolved_batch",
          action_name: "query_status",
          queue_scope: "document-link",
          matched_count: 2,
          candidates: [
            {
              record_id: "rec_de",
              queue_scope: "document-link",
              document_id: "JE-1000F_EU_de_1.0",
              workflow_action: "Build Draft Package",
              result: "SUCCESS",
              document_link: "https://example.com/de.docx",
            },
            {
              record_id: "rec_it",
              queue_scope: "document-link",
              document_id: "JE-1000F_EU_it_1.0",
              workflow_action: "Build Draft Package",
              result: "SUCCESS",
              document_link: "https://example.com/it.docx",
            },
          ],
        };
      },
      async executeResolvedAction() {
        executed = true;
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(basePayload("当前所有已构建文档链接"));
  await result.backgroundTask();

  assert.equal(executed, false);
  assert.equal(replies.length, 3);
  assert.match(replies[0].text, /matched_count: 2/);
  assert.doesNotMatch(replies[0].text, /https:\/\/example.com\/de.docx/);
  assert.equal(replies[1].text, "https://example.com/de.docx");
  assert.equal(replies[2].text, "https://example.com/it.docx");
});

test("message handler dispatches all EU copy package requests without clarification", async () => {
  const replies = [];
  const executed = [];
  let resolvedMessage = "";
  const candidates = ["en", "fr", "es", "de", "it", "uk"].map((lang) => ({
    record_id: `rec_eu_${lang}`,
    queue_scope: "document-link",
    document_id: `JE-2000E_EU_${lang}_0.1`,
    task_id: `JE-2000E_EU_${lang}_0.1_Build Draft Package`,
    lang,
    workflow_action: "Build Draft Package",
  }));
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
      conversationContextTtlSeconds: 3600,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async resolveAction(payload) {
        resolvedMessage = payload.messageText;
        return {
          resolution_status: "resolved_batch",
          action_name: "build_draft_package",
          queue_scope: "document-link",
          matched_count: candidates.length,
          ready: true,
          dispatch_command: "build-draft",
          selectors: {
            task_id_prefix: "JE-2000E_EU_",
          },
          candidates,
        };
      },
      async executeResolvedAction(payload) {
        executed.push(payload);
        return {
          accepted_at: "2026-05-12T14:00:00.000Z",
          run_id: String(executed.length),
        };
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(basePayload("构建JE-2000E_EU的所有欧规文案"));
  await result.backgroundTask();

  assert.equal(resolvedMessage, "构建JE-2000E_EU的所有欧规文案");
  assert.equal(executed.length, 6);
  assert.deepEqual(
    executed.map((payload) => payload.recordId),
    candidates.map((candidate) => candidate.record_id)
  );
  assert.equal(replies.length, 2);
  assert.match(replies[0].text, /Build Draft Package batch/);
  assert.match(replies[0].text, /matched_count: 6/);
  assert.doesNotMatch(replies[0].text, /确认|哪一种/);
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
    { messageId: "om_123", emojiType: "Get" },
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

test("message handler dispatches resolved batch rows without waiting for completion", async () => {
  const replies = [];
  const executions = [];
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
          resolution_status: "resolved_batch",
          action_name: "build_draft_package",
          queue_scope: "document-link",
          matched_count: 2,
          candidates: [
            {
              record_id: "rec_eu_en",
              queue_scope: "document-link",
              document_id: "JE-1000F_EU_en_0.5",
              lang: "en",
              workflow_action: "Build Draft Package",
            },
            {
              record_id: "rec_eu_fr",
              queue_scope: "document-link",
              document_id: "JE-1000F_EU_fr_0.5",
              lang: "fr",
              workflow_action: "Build Draft Package",
            },
          ],
        };
      },
      async executeResolvedAction(payload) {
        executions.push(payload);
      },
      async queryRow({ recordId }) {
        return {
          rows: [
            {
              record_id: recordId,
              workflow_action: "Build Draft Package",
              result: "",
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

  const result = await handler.handleHttpRequest(basePayload("输出JE-1000F的所有欧规说明书文案"));
  await result.backgroundTask();

  assert.equal(executions.length, 2);
  assert.deepEqual(
    executions.map((payload) => [payload.recordId, payload.noWait]),
    [["rec_eu_en", true], ["rec_eu_fr", true]]
  );
  assert.equal(replies.length, 2);
  assert.match(replies[0].text, /matched_count: 2/);
  assert.match(replies[1].text, /批量任务已发起/);
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

test("single-record dispatch accepts immediately without blocking or polling", async () => {
  const replies = [];
  const executions = [];
  let queried = 0;
  const handler = createMessageHandler({
    config: {
      verificationToken: "verify_token",
      requireMention: true,
      publishConfirmTtlSeconds: 600,
      conversationContextTtlSeconds: 3600,
      batchStatusTimeoutSeconds: 5,
    },
    stateStore: createMemoryStateStore(),
    repoControl: {
      async resolveAction() {
        return {
          resolution_status: "resolved",
          action_name: "build_draft_package",
          queue_scope: "document-link",
          row: {
            record_id: "rec_eu_08",
            queue_scope: "document-link",
            document_id: "JE-1000F_EU_0.8",
            workflow_action: "Build Draft Package",
          },
        };
      },
      async executeResolvedAction(payload) {
        executions.push(payload);
        return { accepted_at: "2026-05-29T11:46:00.000Z", run_id: "346" };
      },
      async queryRow() {
        queried += 1;
        return { rows: [] };
      },
      async runStatus() {
        return {};
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });

  const result = await handler.handleHttpRequest(basePayload("构建JE-1000F_EU_0.8文案"));
  await result.backgroundTask();

  // Dispatch fired once with noWait; only the accept reply is sent (no poll).
  assert.equal(executions.length, 1);
  assert.equal(executions[0].noWait, true);
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /处理中/);
  assert.equal(queried, 0);
});

function queryStatusHandler({ row, runStatus, onRunStatus = () => {} }) {
  const replies = [];
  const stateStore = {
    ...createMemoryStateStore(),
    async readConversationContext() {
      return { row: { record_id: "rec_eu_08", run_id: "346" }, acceptedAt: "2026-05-29T11:46:00.000Z" };
    },
    async rememberConversationContext() {},
    async clearConversationContext() {},
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
      async resolveAction() {
        return {
          resolution_status: "resolved",
          action_name: "query_status",
          queue_scope: "document-link",
          row: { record_id: "rec_eu_08", queue_scope: "document-link", document_id: "JE-1000F_EU_0.8" },
        };
      },
      async queryRow() {
        return { rows: [row] };
      },
      async runStatus(payload) {
        onRunStatus(payload);
        return runStatus;
      },
    },
    feishuClient: {
      async replyTextMessage(messageId, text) {
        replies.push({ messageId, text });
      },
    },
  });
  return { handler, replies };
}

test("query reports 处理中 when the Base row is not fresh and the run is still running", async () => {
  let runStatusRunId = "";
  const { handler, replies } = queryStatusHandler({
    row: { record_id: "rec_eu_08", result: "", result_is_fresh: false, freshness_status: "writeback_pending" },
    runStatus: { state: "processing", status: "in_progress", conclusion: "" },
    onRunStatus: ({ runId }) => {
      runStatusRunId = runId;
    },
  });

  const result = await handler.handleHttpRequest(basePayload("这个好了没"));
  await result.backgroundTask();

  assert.equal(runStatusRunId, "346");
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /处理中/);
  assert.doesNotMatch(replies[0].text, /已完成/);
});

test("query reports 已完成 from a fresh successful Base row without reading the run", async () => {
  let runStatusCalls = 0;
  const { handler, replies } = queryStatusHandler({
    row: {
      record_id: "rec_eu_08",
      result: "SUCCESS",
      result_is_fresh: true,
      freshness_status: "fresh_success",
      document_link: "https://example.com/eu08.docx",
    },
    runStatus: {},
    onRunStatus: () => {
      runStatusCalls += 1;
    },
  });

  const result = await handler.handleHttpRequest(basePayload("这个好了没"));
  await result.backgroundTask();

  assert.equal(runStatusCalls, 0);
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /已完成/);
  assert.match(replies[0].text, /SUCCESS/);
});

test("query reports 失败 when the live run failed before any Base writeback", async () => {
  const { handler, replies } = queryStatusHandler({
    row: { record_id: "rec_eu_08", result: "", result_is_fresh: false, freshness_status: "writeback_pending" },
    runStatus: { state: "failed", status: "completed", conclusion: "failure", failure_message: "缺少 JE-1000F_CN 的规格数据" },
  });

  const result = await handler.handleHttpRequest(basePayload("这个好了没"));
  await result.backgroundTask();

  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /失败/);
  assert.match(replies[0].text, /缺少 JE-1000F_CN 的规格数据/);
});
