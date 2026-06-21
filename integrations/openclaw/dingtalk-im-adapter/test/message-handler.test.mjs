import test from "node:test";
import assert from "node:assert/strict";

import { createMessageHandler } from "../lib/message-handler.mjs";

const silentLogger = { error() {}, warn() {} };

// Build the channel-neutral messageEvent the DingTalk stream listener produces
// (see dingtalk-events.extractMessageEvent). ackOnReceived defaults off here so
// reply-count assertions match the resolved/accepted/completed replies; one
// dedicated test exercises the received text ack.
function baseEvent(text, { eventId, messageId = "msg_123", chatId = "cidConv123", senderId = "staff_sender", isGroup = false, isInAtList = true } = {}) {
  const id = messageId;
  return {
    eventId: eventId || id,
    messageId: id,
    chatId,
    conversationType: isGroup ? "2" : "1",
    isGroup,
    senderId,
    senderNick: "Tester",
    isInAtList,
    rawText: text,
    normalizedText: text,
    sessionWebhook: "https://oapi.dingtalk.com/robot/sendBySession?session=demo",
    sessionWebhookExpiredTime: 0,
    openConversationId: isGroup ? chatId : "",
  };
}

function captureClient(replies) {
  return {
    async replyTextMessage(messageEvent, text) {
      replies.push({ text });
    },
  };
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

function baseConfig(extra = {}) {
  return {
    requireMention: true,
    publishConfirmTtlSeconds: 600,
    conversationContextTtlSeconds: 3600,
    ackOnReceived: false,
    ...extra,
  };
}

test("replies with queue status for a resolved query_status", async () => {
  const replies = [];
  const handler = createMessageHandler({
    config: baseConfig(),
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
    imClient: captureClient(replies),
    logger: silentLogger,
  });

  const result = await handler.handleMessageEvent(baseEvent("查 JE-1000F_US_0.3"));
  assert.equal(result.ignored, false);
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /JE-1000F_US_0.3/);
  assert.match(replies[0].text, /SUCCESS/);
});

test("answers manual index lookups before queue resolution", async () => {
  const replies = [];
  let resolvedQueue = false;
  const handler = createMessageHandler({
    config: baseConfig({ manualIndexLimit: 5 }),
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
    imClient: captureClient(replies),
    logger: silentLogger,
  });

  await handler.handleMessageEvent(baseEvent("查 JE-2000F 的说明书链接"));
  assert.equal(resolvedQueue, false);
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /JE-2000F/);
  assert.match(replies[0].text, /https:\/\/alidocs\.example\/je2000f/);
});

test("keeps build-copy requests on the queue path", async () => {
  let manualIndexQueries = 0;
  let resolvedQueue = false;
  const replies = [];
  const handler = createMessageHandler({
    config: baseConfig(),
    stateStore: createMemoryStateStore(),
    repoControl: {
      async queryManualIndex() {
        manualIndexQueries += 1;
        return { matched: true };
      },
      async resolveAction() {
        resolvedQueue = true;
        return { resolution_status: "target_not_found", summary: "No matching queue rows." };
      },
    },
    imClient: captureClient(replies),
    logger: silentLogger,
  });

  await handler.handleMessageEvent(baseEvent("输出JE-1000F的所有欧规说明书文案"));
  assert.equal(manualIndexQueries, 0);
  assert.equal(resolvedQueue, true);
  assert.match(replies[0].text, /No matching queue rows/);
});

test("dispatches resolved batch rows without waiting for completion", async () => {
  const replies = [];
  const executions = [];
  const handler = createMessageHandler({
    config: baseConfig(),
    stateStore: createMemoryStateStore(),
    repoControl: {
      async resolveAction() {
        return {
          resolution_status: "resolved_batch",
          action_name: "build_draft_package",
          queue_scope: "document-link",
          matched_count: 2,
          candidates: [
            { record_id: "rec_eu_en", queue_scope: "document-link", document_id: "JE-1000F_EU_en_0.5", lang: "en", workflow_action: "Build Draft Package" },
            { record_id: "rec_eu_fr", queue_scope: "document-link", document_id: "JE-1000F_EU_fr_0.5", lang: "fr", workflow_action: "Build Draft Package" },
          ],
        };
      },
      async executeResolvedAction(payload) {
        executions.push(payload);
      },
      async queryRow({ recordId }) {
        return { rows: [{ record_id: recordId, workflow_action: "Build Draft Package", result: "" }] };
      },
    },
    imClient: captureClient(replies),
    logger: silentLogger,
  });

  await handler.handleMessageEvent(baseEvent("输出JE-1000F的所有欧规说明书文案"));
  assert.equal(executions.length, 2);
  assert.deepEqual(
    executions.map((payload) => [payload.recordId, payload.noWait]),
    [["rec_eu_en", true], ["rec_eu_fr", true]]
  );
  assert.equal(replies.length, 2);
  assert.match(replies[0].text, /matched_count: 2/);
  assert.match(replies[1].text, /批量任务已发起/);
});

test("answers batch status follow-ups from stored rows", async () => {
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
    config: baseConfig(),
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
    imClient: captureClient(replies),
    logger: silentLogger,
  });

  await handler.handleMessageEvent(baseEvent("发"));
  assert.equal(queried.length, 2);
  assert.equal(queried[0].freshSince, "2026-05-04T10:00:00Z");
  assert.equal(replies.length, 3);
  assert.match(replies[0].text, /fresh_success/);
  assert.equal(replies[1].text, "https://example.com/en.docx");
  assert.equal(replies[2].text, "https://example.com/fr.docx");
});

test("stores then executes a confirmed publish", async () => {
  const replies = [];
  let remembered = null;
  let executed = null;
  const stateStore = {
    ...createMemoryStateStore(),
    async rememberPendingPublish(payload) {
      remembered = payload;
    },
    async consumePendingPublish() {
      return { row: { record_id: "rec_publish", queue_scope: "document-link" } };
    },
  };
  const handler = createMessageHandler({
    config: baseConfig(),
    stateStore,
    repoControl: {
      async resolveAction() {
        return {
          resolution_status: "confirmation_required",
          action_name: "publish",
          queue_scope: "document-link",
          row: { record_id: "rec_publish", queue_scope: "document-link", document_id: "JE-1000F_US_0.3", workflow_action: "Publish" },
        };
      },
      async executeResolvedAction(payload) {
        executed = payload;
      },
      async queryRow() {
        return { rows: [{ record_id: "rec_publish", document_id: "JE-1000F_US_0.3", workflow_action: "Publish", result: "SUCCESS", document_link: "https://example.com/publish.pdf" }] };
      },
    },
    imClient: captureClient(replies),
    logger: silentLogger,
  });

  await handler.handleMessageEvent(baseEvent("发布 JE-1000F_US_0.3"));
  assert.equal(remembered.row.record_id, "rec_publish");
  assert.match(replies.at(-1).text, /确认发布/);

  await handler.handleMessageEvent(baseEvent("确认发布", { eventId: "evt_confirm" }));
  assert.equal(executed.recordId, "rec_publish");
  assert.equal(executed.confirmPublish, true);
  assert.match(replies.at(-1).text, /SUCCESS/);
});

test("allows publish confirmation without an @mention in group chats", async () => {
  const replies = [];
  const handler = createMessageHandler({
    config: baseConfig(),
    stateStore: {
      ...createMemoryStateStore(),
      async consumePendingPublish() {
        return { row: { record_id: "rec_publish", queue_scope: "document-link" } };
      },
    },
    repoControl: {
      async executeResolvedAction() {},
      async queryRow() {
        return { rows: [{ record_id: "rec_publish", document_id: "JE-1000F_US_0.3", workflow_action: "Publish", result: "SUCCESS" }] };
      },
    },
    imClient: captureClient(replies),
    logger: silentLogger,
  });

  const result = await handler.handleMessageEvent(baseEvent("确认发布", { isGroup: true, isInAtList: false }));
  assert.equal(result.ignored, false);
  assert.equal(replies.length, 2);
});

test("suppresses duplicate event ids", async () => {
  const replies = [];
  let resolveCalls = 0;
  const handler = createMessageHandler({
    config: baseConfig(),
    stateStore: createMemoryStateStore(),
    repoControl: {
      async resolveAction() {
        resolveCalls += 1;
        return {
          resolution_status: "resolved",
          action_name: "query_status",
          queue_scope: "document-link",
          row: { record_id: "rec_123", document_id: "JE-1000F_US_0.3", workflow_action: "Build Draft Package", result: "SUCCESS" },
        };
      },
    },
    imClient: captureClient(replies),
    logger: silentLogger,
  });

  await handler.handleMessageEvent(baseEvent("查 JE-1000F_US_0.3", { eventId: "evt_dup" }));
  await handler.handleMessageEvent(baseEvent("查 JE-1000F_US_0.3", { eventId: "evt_dup" }));
  assert.equal(resolveCalls, 1);
  assert.equal(replies.length, 1);
});

test("single-record dispatch accepts immediately without polling", async () => {
  const replies = [];
  const executions = [];
  let queried = 0;
  const handler = createMessageHandler({
    config: baseConfig({ batchStatusTimeoutSeconds: 5 }),
    stateStore: createMemoryStateStore(),
    repoControl: {
      async resolveAction() {
        return {
          resolution_status: "resolved",
          action_name: "build_draft_package",
          queue_scope: "document-link",
          row: { record_id: "rec_eu_08", queue_scope: "document-link", document_id: "JE-1000F_EU_0.8", workflow_action: "Build Draft Package" },
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
    },
    imClient: captureClient(replies),
    logger: silentLogger,
  });

  await handler.handleMessageEvent(baseEvent("构建JE-1000F_EU_0.8文案"));
  assert.equal(executions.length, 1);
  assert.equal(executions[0].noWait, true);
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /处理中/);
  assert.equal(queried, 0);
});

test("sends a received text ack when ackOnReceived is enabled", async () => {
  const replies = [];
  const handler = createMessageHandler({
    config: baseConfig({ ackOnReceived: true }),
    stateStore: createMemoryStateStore(),
    repoControl: {
      async resolveAction() {
        return {
          resolution_status: "resolved",
          action_name: "query_status",
          queue_scope: "document-link",
          row: { record_id: "rec_123", document_id: "JE-1000F_US_0.3", workflow_action: "Build Draft Package", result: "SUCCESS" },
        };
      },
    },
    imClient: captureClient(replies),
    logger: silentLogger,
  });

  await handler.handleMessageEvent(baseEvent("查 JE-1000F_US_0.3"));
  assert.equal(replies.length, 2);
  assert.match(replies[0].text, /已收到/);
  assert.match(replies[1].text, /SUCCESS/);
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
    config: baseConfig(),
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
    imClient: captureClient(replies),
    logger: silentLogger,
  });
  return { handler, replies };
}

test("query reports 处理中 when the row is not fresh and the run is still running", async () => {
  let runStatusRunId = "";
  const { handler, replies } = queryStatusHandler({
    row: { record_id: "rec_eu_08", result: "", result_is_fresh: false, freshness_status: "writeback_pending" },
    runStatus: { state: "processing", status: "in_progress", conclusion: "" },
    onRunStatus: ({ runId }) => {
      runStatusRunId = runId;
    },
  });
  await handler.handleMessageEvent(baseEvent("这个好了没"));
  assert.equal(runStatusRunId, "346");
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /处理中/);
  assert.doesNotMatch(replies[0].text, /已完成/);
});

test("query reports 已完成 from a fresh successful row without reading the run", async () => {
  let runStatusCalls = 0;
  const { handler, replies } = queryStatusHandler({
    row: { record_id: "rec_eu_08", result: "SUCCESS", result_is_fresh: true, freshness_status: "fresh_success", document_link: "https://example.com/eu08.docx" },
    runStatus: {},
    onRunStatus: () => {
      runStatusCalls += 1;
    },
  });
  await handler.handleMessageEvent(baseEvent("这个好了没"));
  assert.equal(runStatusCalls, 0);
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /已完成/);
  assert.match(replies[0].text, /SUCCESS/);
});

test("query reports 失败 when the live run failed before any writeback", async () => {
  const { handler, replies } = queryStatusHandler({
    row: { record_id: "rec_eu_08", result: "", result_is_fresh: false, freshness_status: "writeback_pending" },
    runStatus: { state: "failed", status: "completed", conclusion: "failure", failure_message: "缺少 JE-1000F_CN 的规格数据" },
  });
  await handler.handleMessageEvent(baseEvent("这个好了没"));
  assert.equal(replies.length, 1);
  assert.match(replies[0].text, /失败/);
  assert.match(replies[0].text, /缺少 JE-1000F_CN 的规格数据/);
});
