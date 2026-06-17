import { randomUUID } from "node:crypto";

import {
  isPublishConfirmationText,
  shouldIgnoreMessageEvent,
} from "./dingtalk-events.mjs";
import {
  cloudDocBackportSenderAllowed,
  parseCloudDocBackportPrRequest,
  parseCloudDocBackportRequest,
} from "./cloud-doc-backport-action.mjs";
import {
  formatAcceptedReply,
  formatBatchAcceptedReply,
  formatBatchCompletionReply,
  formatBatchStatusReply,
  formatCloudDocBackportAcceptedReply,
  formatCloudDocBackportDeniedReply,
  formatCloudDocBackportNeedInputReply,
  formatCloudDocBackportPrAcceptedReply,
  formatCloudDocBackportPrNeedInputReply,
  formatCloudDocBackportPrResultReply,
  formatCloudDocBackportResultReply,
  formatCompletionReply,
  formatExecutionErrorReply,
  formatFailedReply,
  formatManualIndexReply,
  formatNoPendingPublishReply,
  formatPendingPublishReply,
  formatProcessingReply,
  formatPublishCompletedButUnreadableReply,
  formatPublishConfirmationAcceptedReply,
  formatRecordNoLongerAvailableReply,
  formatResolutionReply,
} from "./reply-format.mjs";
import { classifyTaskState, rowLooksFreshFailure, rowLooksFreshSuccess } from "./status-classify.mjs";
import { normalizeIncomingMessage } from "./message-normalizer.mjs";
import { sendStageReaction } from "./reaction-policy.mjs";

async function replyAndIgnore(imClient, messageEvent, text) {
  if (messageEvent) {
    await imClient.replyTextMessage(messageEvent, text);
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function nowIso() {
  return new Date().toISOString();
}

function contextRows(conversationContext) {
  return Array.isArray(conversationContext?.rows) ? conversationContext.rows : [];
}

function documentLinksFromRows(rows) {
  const links = [];
  const seen = new Set();
  for (const row of rows || []) {
    const link = String(row?.document_link || "").trim();
    if (!link || seen.has(link)) {
      continue;
    }
    seen.add(link);
    links.push(link);
  }
  return links;
}

function looksLikeManualIndexQuery(messageText) {
  const text = String(messageText || "").replace(/\s+/g, " ").trim();
  if (!text) {
    return false;
  }
  const lowered = text.toLowerCase();
  const hasReadIntent =
    /(查|查询|查看|找|获取|给我|发我|链接|列表|清单|总览|概览|统计|多少|有哪些)/.test(text) ||
    /\b(show|find|search|list|overview|summary|count|link)\b/i.test(text);
  const hasManualKeyword = /(说明书|手册|发布文档|文档管理)/.test(text) || /\bmanual(?:\s+index|\s+table)?\b/i.test(text);
  const hasOverview = /(总览|概览|统计|多少)/.test(text) || /\b(overview|summary|count)\b/i.test(text);
  const hasInventory = /(所有|全部|全量|各产品|各个|列表|清单)/.test(text) || /\b(all|every|list|inventory)\b/i.test(text);
  const hasExecution =
    /(构建|生成|输出|发起|触发|补跑|补构建|重跑|重新构建|开始|发布)/.test(text) ||
    /\b(build|run|trigger|start|publish|review)\b/i.test(text);
  const hasQueueCopy = /(文案)/.test(text) || /\bmanual\s+copy\b/i.test(text) || /\bcopy\b/i.test(text);
  if (hasExecution && hasQueueCopy && !hasOverview && !/(链接|link)/i.test(text)) {
    return false;
  }
  if (hasOverview && !(hasExecution && !hasReadIntent)) {
    return true;
  }
  return hasManualKeyword && (hasReadIntent || hasInventory) && !(hasExecution && !hasReadIntent);
}

// Freshness values that mean "the dispatch fired but the authoritative Feishu
// writeback is not the current run's final result yet" — i.e. still processing.
const PENDING_FRESHNESS_STATUSES = ["pending", "writeback_pending", "stale_result", "not_requested"];

function isRowStillProcessing(row) {
  return PENDING_FRESHNESS_STATUSES.includes(String(row?.freshness_status || ""));
}

export function createMessageHandler({ config, stateStore, repoControl, imClient, logger = console }) {
  const localProfile = config?.localProfile || null;

  async function react(messageEvent, stage) {
    await sendStageReaction({ config, imClient, logger, messageEvent, stage });
  }

  async function rememberConversationContext(messageEvent, { row, rows = [], queryText, actionName, acceptedAt = "", requestId = "" }) {
    if ((!row && !rows.length) || typeof stateStore.rememberConversationContext !== "function") {
      return;
    }
    await stateStore.rememberConversationContext({
      chatId: messageEvent.chatId,
      senderId: messageEvent.senderId,
      messageId: messageEvent.messageId,
      row,
      rows,
      queryText,
      actionName,
      acceptedAt,
      requestId,
      ttlSeconds: config.conversationContextTtlSeconds || 3600,
    });
  }

  async function forgetConversationContext(messageEvent) {
    if (typeof stateStore.clearConversationContext !== "function") {
      return;
    }
    await stateStore.clearConversationContext({
      chatId: messageEvent.chatId,
      senderId: messageEvent.senderId,
    });
  }

  async function replyBatchStatus(messageEvent, statusPayload) {
    await imClient.replyTextMessage(
      messageEvent,
      formatBatchStatusReply(statusPayload, localProfile, { includeDocumentLinks: false })
    );
    for (const link of documentLinksFromRows(statusPayload?.rows).slice(0, 10)) {
      await imClient.replyTextMessage(messageEvent, link);
    }
  }

  async function queryContextRows({ rows, freshSince }) {
    const latestRows = [];
    const failures = [];
    for (const row of rows) {
      try {
        const latest = await repoControl.queryRow({
          queueScope: row.queue_scope || "document-link",
          recordId: row.record_id,
          freshSince,
        });
        const latestRow = Array.isArray(latest?.rows) ? latest.rows[0] : null;
        if (latestRow) {
          latestRows.push(latestRow);
          continue;
        }
        failures.push({
          record_id: row.record_id,
          message: "Feishu row not found; ignored stored context because the row may have been deleted or moved.",
        });
      } catch (error) {
        failures.push({
          record_id: row.record_id,
          message: error?.message || String(error),
        });
      }
    }
    return { rows: latestRows, failures };
  }

  async function pollBatchRows({ rows, freshSince }) {
    const timeoutSeconds = Math.max(Number(config?.batchStatusTimeoutSeconds || 0), 0);
    if (!timeoutSeconds) {
      return { rows, failures: [], timedOut: false, skipped: true };
    }
    const pollMs = Math.max(Number(config?.batchStatusPollSeconds || 5), 1) * 1000;
    const deadline = Date.now() + timeoutSeconds * 1000;
    let latest = { rows, failures: [] };
    while (Date.now() <= deadline) {
      latest = await queryContextRows({ rows, freshSince });
      const pending = latest.rows.filter((row) => isRowStillProcessing(row));
      if (!pending.length) {
        return { ...latest, timedOut: false, skipped: false };
      }
      await sleep(pollMs);
    }
    return { ...latest, timedOut: true, skipped: false };
  }

  // Answer a status query accurately at ask time: trust a fresh Base writeback
  // first, otherwise read the live GitHub run (no polling) to tell processing
  // from failed. runIdHint comes from the dispatch we remembered for this row.
  async function resolveAccurateRowState(row, { runIdHint = "" } = {}) {
    if (rowLooksFreshSuccess(row)) {
      return { state: "completed", runStatus: null };
    }
    if (rowLooksFreshFailure(row)) {
      return { state: "failed", runStatus: null };
    }
    const runId = String(runIdHint || row?.run_id || "").trim();
    let runStatus = null;
    if (runId && typeof repoControl.runStatus === "function") {
      try {
        runStatus = await repoControl.runStatus({ runId });
      } catch (error) {
        // A run-read blip must not break the query; fall back to the row state.
        logger.error?.("runStatus read failed", error);
        runStatus = null;
      }
    }
    return { state: classifyTaskState({ row, runStatus }), runStatus };
  }

  async function replyForRowState(messageEvent, { state, row, runStatus }) {
    await react(messageEvent, state === "failed" ? "error" : "completed");
    if (state === "completed") {
      await imClient.replyTextMessage(messageEvent, formatCompletionReply(row, localProfile));
      return;
    }
    if (state === "failed") {
      await imClient.replyTextMessage(messageEvent, formatFailedReply(row, runStatus, localProfile));
      return;
    }
    await imClient.replyTextMessage(messageEvent, formatProcessingReply(row, localProfile));
  }

  async function processMessageEvent(messageEvent) {
    await stateStore.clearExpiredPublishes();
    await stateStore.clearExpiredConversationContexts?.();
    if (!(await stateStore.claimProcessedEvent(messageEvent.eventId))) {
      return;
    }
    await react(messageEvent, "received");

    if (isPublishConfirmationText(messageEvent.normalizedText)) {
      const pending = await stateStore.consumePendingPublish({
        chatId: messageEvent.chatId,
        senderId: messageEvent.senderId,
      });
      if (!pending) {
        await react(messageEvent, "needs_input");
        await replyAndIgnore(imClient, messageEvent, formatNoPendingPublishReply(localProfile));
        return;
      }
      try {
        await react(messageEvent, "accepted");
        await imClient.replyTextMessage(
          messageEvent,
          formatPublishConfirmationAcceptedReply(pending.row, localProfile)
        );
        const executionResult = await repoControl.executeResolvedAction({
          actionName: "publish",
          queueScope: pending.row.queue_scope,
          recordId: pending.row.record_id,
          confirmPublish: true,
        });
        const acceptedAt = executionResult?.accepted_at || nowIso();
        const latest = await repoControl.queryRow({
          queueScope: pending.row.queue_scope,
          recordId: pending.row.record_id,
          freshSince: acceptedAt,
        });
        const row = Array.isArray(latest?.rows) ? latest.rows[0] : null;
        if (row) {
          await rememberConversationContext(messageEvent, {
            row,
            queryText: pending.queryText || messageEvent.normalizedText,
            actionName: "publish",
            acceptedAt,
          });
        }
        await react(messageEvent, "completed");
        await imClient.replyTextMessage(
          messageEvent,
          row ? formatCompletionReply(row, localProfile) : formatPublishCompletedButUnreadableReply(localProfile)
        );
      } catch (error) {
        logger.error?.("publish confirmation failed", error);
        await react(messageEvent, "error");
        await imClient.replyTextMessage(messageEvent, formatExecutionErrorReply(error, localProfile));
      }
      return;
    }

    const conversationContext = await stateStore.readConversationContext?.({
      chatId: messageEvent.chatId,
      senderId: messageEvent.senderId,
    });
    const normalizedMessage = normalizeIncomingMessage({
      messageText: messageEvent.normalizedText,
      localProfile,
      conversationContext,
    });

    if (normalizedMessage.usedBatchContext) {
      const latest = await queryContextRows({
        rows: normalizedMessage.contextRows,
        freshSince: conversationContext?.acceptedAt || "",
      });
      if (latest.rows.length) {
        await rememberConversationContext(messageEvent, {
          rows: latest.rows,
          queryText: normalizedMessage.normalizedText,
          actionName: conversationContext?.actionName || "query_status",
          acceptedAt: conversationContext?.acceptedAt || "",
          requestId: conversationContext?.requestId || "",
        });
      } else {
        await forgetConversationContext(messageEvent);
      }
      await react(messageEvent, latest.failures.length ? "error" : "completed");
      await replyBatchStatus(messageEvent, latest);
      return;
    }

    const cloudDocBackportPrRequest = parseCloudDocBackportPrRequest(normalizedMessage.normalizedText);
    if (cloudDocBackportPrRequest.matched) {
      if (!cloudDocBackportSenderAllowed(messageEvent.senderId, config)) {
        await react(messageEvent, "needs_input");
        await imClient.replyTextMessage(
          messageEvent,
          formatCloudDocBackportDeniedReply(
            "sender is not in DINGTALK_IM_CLOUD_DOC_BACKPORT_ALLOWED_SENDERS",
            localProfile
          )
        );
        return;
      }
      if (cloudDocBackportPrRequest.missing.length) {
        await react(messageEvent, "needs_input");
        await imClient.replyTextMessage(
          messageEvent,
          formatCloudDocBackportPrNeedInputReply(cloudDocBackportPrRequest, localProfile)
        );
        return;
      }
      if (!config.cloudDocBackportAllowPrCreate) {
        await react(messageEvent, "needs_input");
        await imClient.replyTextMessage(
          messageEvent,
          formatCloudDocBackportDeniedReply(
            "draft PR creation is disabled; set DINGTALK_IM_CLOUD_DOC_BACKPORT_ALLOW_PR_CREATE=true to allow explicit backport-pr requests",
            localProfile
          )
        );
        return;
      }
      await react(messageEvent, "accepted");
      await imClient.replyTextMessage(
        messageEvent,
        formatCloudDocBackportPrAcceptedReply(cloudDocBackportPrRequest, localProfile)
      );
      try {
        const prResult = await repoControl.openCloudDocBackportPr(cloudDocBackportPrRequest);
        await react(messageEvent, "completed");
        await imClient.replyTextMessage(
          messageEvent,
          formatCloudDocBackportPrResultReply(prResult, localProfile)
        );
      } catch (error) {
        logger.error?.("cloud-doc backport PR creation failed", error);
        await react(messageEvent, "error");
        await imClient.replyTextMessage(messageEvent, formatExecutionErrorReply(error, localProfile));
      }
      return;
    }

    let cloudDocBackportRequest = parseCloudDocBackportRequest(normalizedMessage.normalizedText);
    if (cloudDocBackportRequest.matched) {
      if (!cloudDocBackportSenderAllowed(messageEvent.senderId, config)) {
        await react(messageEvent, "needs_input");
        await imClient.replyTextMessage(
          messageEvent,
          formatCloudDocBackportDeniedReply(
            "sender is not in DINGTALK_IM_CLOUD_DOC_BACKPORT_ALLOWED_SENDERS",
            localProfile
          )
        );
        return;
      }
      if (
        cloudDocBackportRequest.missing.includes("docs/_review/... .rst source path") &&
        !cloudDocBackportRequest.missing.includes("Feishu cloud-doc URL") &&
        typeof repoControl.inferCloudDocBackportSource === "function"
      ) {
        let sourceInference;
        try {
          sourceInference = await repoControl.inferCloudDocBackportSource(cloudDocBackportRequest);
        } catch (error) {
          logger.error?.("cloud-doc backport source inference failed", error);
          sourceInference = {
            status: "needs_input",
            reason: "source_inference_failed",
            message: error?.message || String(error),
          };
        }
        if (sourceInference?.status === "resolved" && sourceInference.sourcePath) {
          cloudDocBackportRequest = {
            ...cloudDocBackportRequest,
            sourcePath: sourceInference.sourcePath,
            sourceInference,
            missing: cloudDocBackportRequest.missing.filter((item) => item !== "docs/_review/... .rst source path"),
          };
        } else {
          cloudDocBackportRequest = {
            ...cloudDocBackportRequest,
            sourceInference,
          };
        }
      }
      if (cloudDocBackportRequest.missing.length) {
        await react(messageEvent, "needs_input");
        await imClient.replyTextMessage(
          messageEvent,
          formatCloudDocBackportNeedInputReply(cloudDocBackportRequest, localProfile)
        );
        return;
      }
      if (cloudDocBackportRequest.write && !config.cloudDocBackportAllowWrite) {
        await react(messageEvent, "needs_input");
        await imClient.replyTextMessage(
          messageEvent,
          formatCloudDocBackportDeniedReply(
            "write mode is disabled; set DINGTALK_IM_CLOUD_DOC_BACKPORT_ALLOW_WRITE=true to allow explicit --write requests",
            localProfile
          )
        );
        return;
      }
      await react(messageEvent, "accepted");
      await imClient.replyTextMessage(
        messageEvent,
        formatCloudDocBackportAcceptedReply(cloudDocBackportRequest, localProfile)
      );
      try {
        const runResult = await repoControl.runCloudDocBackportReview(cloudDocBackportRequest);
        await react(messageEvent, runResult?.result === "FAIL" ? "error" : "completed");
        await imClient.replyTextMessage(messageEvent, formatCloudDocBackportResultReply(runResult, localProfile));
      } catch (error) {
        logger.error?.("cloud-doc backport failed", error);
        await react(messageEvent, "error");
        await imClient.replyTextMessage(messageEvent, formatExecutionErrorReply(error, localProfile));
      }
      return;
    }

    if (looksLikeManualIndexQuery(normalizedMessage.normalizedText) && typeof repoControl.queryManualIndex === "function") {
      try {
        const manualIndexResult = await repoControl.queryManualIndex({
          messageText: normalizedMessage.normalizedText,
          limit: config.manualIndexLimit || 10,
        });
        if (manualIndexResult?.matched) {
          await react(messageEvent, "completed");
          await imClient.replyTextMessage(
            messageEvent,
            formatManualIndexReply(manualIndexResult, localProfile)
          );
          return;
        }
      } catch (error) {
        logger.error?.("manual index query failed", error);
        await react(messageEvent, "error");
        await imClient.replyTextMessage(messageEvent, formatExecutionErrorReply(error, localProfile));
        return;
      }
    }

    let resolution;
    try {
      resolution = await repoControl.resolveAction({
        messageText: normalizedMessage.normalizedText,
        confirmPublish: false,
      });
    } catch (error) {
      logger.error?.("message resolution failed", error);
      await react(messageEvent, "error");
      await imClient.replyTextMessage(messageEvent, formatExecutionErrorReply(error, localProfile));
      return;
    }

    if (resolution.resolution_status === "confirmation_required") {
      await stateStore.rememberPendingPublish({
        chatId: messageEvent.chatId,
        senderId: messageEvent.senderId,
        messageId: messageEvent.messageId,
        row: resolution.row,
        queryText: normalizedMessage.normalizedText,
        ttlSeconds: config.publishConfirmTtlSeconds,
      });
      await rememberConversationContext(messageEvent, {
        row: resolution.row,
        queryText: normalizedMessage.normalizedText,
        actionName: resolution.action_name,
      });
      await react(messageEvent, "needs_confirmation");
      await imClient.replyTextMessage(messageEvent, formatPendingPublishReply(resolution, localProfile));
      return;
    }

    if (!["resolved", "resolved_batch"].includes(resolution.resolution_status)) {
      const stage = resolution.resolution_status === "target_not_found" ? "unresolved" : "needs_input";
      await react(messageEvent, stage);
      await imClient.replyTextMessage(messageEvent, formatResolutionReply(resolution, localProfile));
      return;
    }

    if (resolution.resolution_status === "resolved_batch" && resolution.action_name === "query_status") {
      const rows = Array.isArray(resolution.candidates) ? resolution.candidates : [];
      if (rows.length) {
        await rememberConversationContext(messageEvent, {
          rows,
          queryText: normalizedMessage.normalizedText,
          actionName: resolution.action_name,
          acceptedAt: conversationContext?.acceptedAt || "",
          requestId: conversationContext?.requestId || "",
        });
      }
      await react(messageEvent, "completed");
      await replyBatchStatus(messageEvent, {
        rows,
        failures: [],
        heading: "查到这些 Feishu 当前队列行：",
      });
      return;
    }

    if (resolution.action_name === "query_status") {
      let row = resolution.row || {};
      // The dispatched run id lives in the remembered context, not in the
      // freshly re-read Base row, so capture it before `row` is reassigned.
      const runIdHint = conversationContext?.row?.run_id || row.run_id || "";
      if (conversationContext?.acceptedAt && row?.record_id) {
        const latest = await repoControl.queryRow({
          queueScope: row.queue_scope || resolution.queue_scope,
          recordId: row.record_id,
          freshSince: conversationContext.acceptedAt,
        });
        const latestRow = Array.isArray(latest?.rows) ? latest.rows[0] : null;
        if (!latestRow) {
          await forgetConversationContext(messageEvent);
          await react(messageEvent, "unresolved");
          await imClient.replyTextMessage(messageEvent, formatRecordNoLongerAvailableReply(row, localProfile));
          return;
        }
        row = latestRow;
      }
      const { state, runStatus } = await resolveAccurateRowState(row, { runIdHint });
      await rememberConversationContext(messageEvent, {
        row: { ...row, run_id: row.run_id || runIdHint || "" },
        queryText: normalizedMessage.normalizedText,
        actionName: resolution.action_name,
        acceptedAt: conversationContext?.acceptedAt || "",
        requestId: conversationContext?.requestId || "",
      });
      await replyForRowState(messageEvent, { state, row, runStatus });
      return;
    }

    if (resolution.resolution_status === "resolved_batch") {
      const candidates = Array.isArray(resolution.candidates) ? resolution.candidates : [];
      const rows = [];
      const failures = [];
      const dispatchDelayMs = Math.max(Number(config?.batchDispatchDelayMs || 0), 0);
      const acceptedAt = nowIso();
      const requestId = randomUUID();
      await react(messageEvent, "accepted");
      await imClient.replyTextMessage(messageEvent, formatBatchAcceptedReply(resolution, localProfile));
      for (const [index, candidate] of candidates.entries()) {
        if (index > 0 && dispatchDelayMs > 0) {
          await sleep(dispatchDelayMs);
        }
        try {
          const executionResult = await repoControl.executeResolvedAction({
            actionName: resolution.action_name,
            queueScope: candidate.queue_scope || resolution.queue_scope,
            recordId: candidate.record_id,
            confirmPublish: false,
            noWait: true,
          });
          rows.push({
            ...candidate,
            ...executionResult,
            queue_scope: candidate.queue_scope || resolution.queue_scope,
            record_id: candidate.record_id,
            accepted_at: executionResult?.accepted_at || acceptedAt,
          });
        } catch (error) {
          logger.error?.("batch message execution failed", error);
          failures.push({
            record_id: candidate.record_id,
            message: error?.message || String(error),
          });
        }
      }
      await rememberConversationContext(messageEvent, {
        rows,
        queryText: normalizedMessage.normalizedText,
        actionName: resolution.action_name,
        acceptedAt,
        requestId,
      });
      await react(messageEvent, failures.length ? "error" : "completed");
      await imClient.replyTextMessage(
        messageEvent,
        formatBatchCompletionReply({ resolution, rows, failures }, localProfile)
      );
      const finalStatus = await pollBatchRows({ rows, freshSince: acceptedAt });
      if (!finalStatus.skipped && (finalStatus.timedOut || finalStatus.rows.some((row) => !["stale_result", "writeback_pending", "pending"].includes(String(row?.freshness_status || ""))))) {
        await rememberConversationContext(messageEvent, {
          rows: finalStatus.rows,
          queryText: normalizedMessage.normalizedText,
          actionName: resolution.action_name,
          acceptedAt,
          requestId,
        });
        await replyBatchStatus(messageEvent, {
          rows: finalStatus.rows,
          failures: finalStatus.failures,
          heading: finalStatus.timedOut ? "批量任务仍在执行或等待写回：" : "批量任务最新写回：",
        });
      }
      return;
    }

    // Accept first, report later — never block the chat turn on completion.
    // The dispatch fires with noWait so the local command returns immediately
    // (发起即受理), and the run id is remembered so a later "这个好了没" can read
    // the live run state and answer 处理中 / 已完成 / 失败 accurately. No polling.
    const acceptedAt0 = nowIso();
    await rememberConversationContext(messageEvent, {
      row: resolution.row,
      queryText: normalizedMessage.normalizedText,
      actionName: resolution.action_name,
      acceptedAt: acceptedAt0,
    });
    await react(messageEvent, "accepted");
    await imClient.replyTextMessage(messageEvent, formatAcceptedReply(resolution, localProfile));

    let executionResult;
    try {
      executionResult = await repoControl.executeResolvedAction({
        actionName: resolution.action_name,
        queueScope: resolution.queue_scope,
        recordId: resolution.row.record_id,
        confirmPublish: false,
        noWait: true,
      });
    } catch (error) {
      logger.error?.("message execution failed", error);
      await react(messageEvent, "error");
      await imClient.replyTextMessage(messageEvent, formatExecutionErrorReply(error, localProfile));
      return;
    }

    const acceptedAt = executionResult?.accepted_at || acceptedAt0;
    await rememberConversationContext(messageEvent, {
      row: {
        ...resolution.row,
        ...executionResult,
        queue_scope: resolution.queue_scope,
        record_id: resolution.row.record_id,
        accepted_at: acceptedAt,
      },
      queryText: normalizedMessage.normalizedText,
      actionName: resolution.action_name,
      acceptedAt,
    });
  }

  // DingTalk Stream delivers an already-decrypted robot message; there is no
  // URL-verification handshake or callback token to validate (unlike the Feishu
  // webhook). The stream listener builds the messageEvent and calls this; a
  // bare publish-confirmation is honoured even in a group without an @mention.
  async function handleMessageEvent(messageEvent) {
    const ignoreReason = shouldIgnoreMessageEvent(messageEvent, { requireMention: config.requireMention });
    if (ignoreReason && !(ignoreReason === "missing_mention" && isPublishConfirmationText(messageEvent?.normalizedText))) {
      return { ignored: true, reason: ignoreReason };
    }
    await processMessageEvent(messageEvent);
    return { ignored: false };
  }

  return {
    processMessageEvent,
    handleMessageEvent,
  };
}
