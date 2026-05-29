import { randomUUID } from "node:crypto";

import {
  extractMessageEvent,
  isPublishConfirmationText,
  isUrlVerification,
  resolveEventPayload,
  shouldIgnoreMessageEvent,
  validateVerificationToken,
} from "./feishu-events.mjs";
import {
  formatAcceptedReply,
  formatBatchAcceptedReply,
  formatBatchCompletionReply,
  formatBatchStatusReply,
  formatCompletionReply,
  formatExecutionErrorReply,
  formatNoPendingPublishReply,
  formatPendingPublishReply,
  formatProcessingReply,
  formatPublishCompletedButUnreadableReply,
  formatPublishConfirmationAcceptedReply,
  formatRecordNoLongerAvailableReply,
  formatResolutionReply,
  formatRunCompletedButUnreadableReply,
} from "./reply-format.mjs";
import { normalizeIncomingMessage } from "./message-normalizer.mjs";
import { sendStageReaction } from "./reaction-policy.mjs";

async function replyAndIgnore(feishuClient, messageId, text) {
  if (messageId) {
    await feishuClient.replyTextMessage(messageId, text);
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

// Freshness values that mean "the dispatch fired but the authoritative Feishu
// writeback is not the current run's final result yet" — i.e. still processing.
const PENDING_FRESHNESS_STATUSES = ["pending", "writeback_pending", "stale_result", "not_requested"];

function isRowStillProcessing(row) {
  return PENDING_FRESHNESS_STATUSES.includes(String(row?.freshness_status || ""));
}

export function createMessageHandler({ config, stateStore, repoControl, feishuClient, logger = console }) {
  const localProfile = config?.localProfile || null;

  async function react(messageId, stage) {
    await sendStageReaction({ config, feishuClient, localProfile, logger, messageId, stage });
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

  async function processMessageEvent(messageEvent) {
    await stateStore.clearExpiredPublishes();
    await stateStore.clearExpiredConversationContexts?.();
    if (!(await stateStore.claimProcessedEvent(messageEvent.eventId))) {
      return;
    }
    await react(messageEvent.messageId, "received");

    if (isPublishConfirmationText(messageEvent.normalizedText)) {
      const pending = await stateStore.consumePendingPublish({
        chatId: messageEvent.chatId,
        senderId: messageEvent.senderId,
      });
      if (!pending) {
        await react(messageEvent.messageId, "needs_input");
        await replyAndIgnore(feishuClient, messageEvent.messageId, formatNoPendingPublishReply(localProfile));
        return;
      }
      try {
        await react(messageEvent.messageId, "accepted");
        await feishuClient.replyTextMessage(
          messageEvent.messageId,
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
        await react(messageEvent.messageId, "completed");
        await feishuClient.replyTextMessage(
          messageEvent.messageId,
          row ? formatCompletionReply(row, localProfile) : formatPublishCompletedButUnreadableReply(localProfile)
        );
      } catch (error) {
        logger.error?.("publish confirmation failed", error);
        await react(messageEvent.messageId, "error");
        await feishuClient.replyTextMessage(messageEvent.messageId, formatExecutionErrorReply(error, localProfile));
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
      await react(messageEvent.messageId, latest.failures.length ? "error" : "completed");
      await feishuClient.replyTextMessage(
        messageEvent.messageId,
        formatBatchStatusReply(latest, localProfile)
      );
      return;
    }

    let resolution;
    try {
      resolution = await repoControl.resolveAction({
        messageText: normalizedMessage.normalizedText,
        confirmPublish: false,
      });
    } catch (error) {
      logger.error?.("message resolution failed", error);
      await react(messageEvent.messageId, "error");
      await feishuClient.replyTextMessage(messageEvent.messageId, formatExecutionErrorReply(error, localProfile));
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
      await react(messageEvent.messageId, "needs_confirmation");
      await feishuClient.replyTextMessage(messageEvent.messageId, formatPendingPublishReply(resolution, localProfile));
      return;
    }

    if (!["resolved", "resolved_batch"].includes(resolution.resolution_status)) {
      const stage = resolution.resolution_status === "target_not_found" ? "unresolved" : "needs_input";
      await react(messageEvent.messageId, stage);
      await feishuClient.replyTextMessage(messageEvent.messageId, formatResolutionReply(resolution, localProfile));
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
      await react(messageEvent.messageId, "completed");
      await feishuClient.replyTextMessage(
        messageEvent.messageId,
        formatBatchStatusReply(
          {
            rows,
            failures: [],
            heading: "查到这些 Feishu 当前队列行：",
          },
          localProfile
        )
      );
      return;
    }

    if (resolution.action_name === "query_status") {
      let row = resolution.row || {};
      if (conversationContext?.acceptedAt && row?.record_id) {
        const latest = await repoControl.queryRow({
          queueScope: row.queue_scope || resolution.queue_scope,
          recordId: row.record_id,
          freshSince: conversationContext.acceptedAt,
        });
        const latestRow = Array.isArray(latest?.rows) ? latest.rows[0] : null;
        if (!latestRow) {
          await forgetConversationContext(messageEvent);
          await react(messageEvent.messageId, "unresolved");
          await feishuClient.replyTextMessage(messageEvent.messageId, formatRecordNoLongerAvailableReply(row, localProfile));
          return;
        }
        row = latestRow;
      }
      await rememberConversationContext(messageEvent, {
        row,
        queryText: normalizedMessage.normalizedText,
        actionName: resolution.action_name,
        acceptedAt: conversationContext?.acceptedAt || "",
        requestId: conversationContext?.requestId || "",
      });
      await react(messageEvent.messageId, "completed");
      await feishuClient.replyTextMessage(messageEvent.messageId, formatCompletionReply(row || {}, localProfile));
      return;
    }

    if (resolution.resolution_status === "resolved_batch") {
      const candidates = Array.isArray(resolution.candidates) ? resolution.candidates : [];
      const rows = [];
      const failures = [];
      const dispatchDelayMs = Math.max(Number(config?.batchDispatchDelayMs || 0), 0);
      const acceptedAt = nowIso();
      const requestId = randomUUID();
      await react(messageEvent.messageId, "accepted");
      await feishuClient.replyTextMessage(messageEvent.messageId, formatBatchAcceptedReply(resolution, localProfile));
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
      await react(messageEvent.messageId, failures.length ? "error" : "completed");
      await feishuClient.replyTextMessage(
        messageEvent.messageId,
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
        await feishuClient.replyTextMessage(
          messageEvent.messageId,
          formatBatchStatusReply(
            {
              rows: finalStatus.rows,
              failures: finalStatus.failures,
              heading: finalStatus.timedOut ? "批量任务仍在执行或等待写回：" : "批量任务最新写回：",
            },
            localProfile
          )
        );
      }
      return;
    }

    // Accept-and-poll, never block the chat turn on completion. The dispatch is
    // fired with noWait so the local command returns immediately (发起即受理);
    // a background poll then reports the result when it lands (完成回查/回调),
    // and an unfinished run is reported as "任务正在处理中", not a failure.
    const acceptedAt0 = nowIso();
    await rememberConversationContext(messageEvent, {
      row: resolution.row,
      queryText: normalizedMessage.normalizedText,
      actionName: resolution.action_name,
      acceptedAt: acceptedAt0,
    });
    await react(messageEvent.messageId, "accepted");
    await feishuClient.replyTextMessage(messageEvent.messageId, formatAcceptedReply(resolution, localProfile));

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
      await react(messageEvent.messageId, "error");
      await feishuClient.replyTextMessage(messageEvent.messageId, formatExecutionErrorReply(error, localProfile));
      return;
    }

    const acceptedAt = executionResult?.accepted_at || acceptedAt0;
    const seedRow = {
      ...resolution.row,
      ...executionResult,
      queue_scope: resolution.queue_scope,
      record_id: resolution.row.record_id,
      accepted_at: acceptedAt,
    };
    await rememberConversationContext(messageEvent, {
      row: seedRow,
      queryText: normalizedMessage.normalizedText,
      actionName: resolution.action_name,
      acceptedAt,
    });

    // The accepted reply already told the operator it is processing. If polling
    // is disabled we stop here and let them re-ask "这个好了没" for the result.
    const settled = await pollBatchRows({ rows: [seedRow], freshSince: acceptedAt });
    if (settled.skipped) {
      return;
    }

    const finalRow = (Array.isArray(settled.rows) && settled.rows[0]) || seedRow;
    await rememberConversationContext(messageEvent, {
      row: finalRow,
      queryText: normalizedMessage.normalizedText,
      actionName: resolution.action_name,
      acceptedAt,
    });
    if (settled.timedOut || isRowStillProcessing(finalRow)) {
      await feishuClient.replyTextMessage(messageEvent.messageId, formatProcessingReply(finalRow, localProfile));
    } else {
      await react(messageEvent.messageId, "completed");
      await feishuClient.replyTextMessage(
        messageEvent.messageId,
        finalRow ? formatCompletionReply(finalRow, localProfile) : formatRunCompletedButUnreadableReply(localProfile)
      );
    }
  }

  async function handleEventPayload(payload, { skipVerification = false } = {}) {
    if (!skipVerification && !validateVerificationToken(payload, config.verificationToken)) {
      return {
        statusCode: 403,
        body: { code: 403, msg: "invalid verification token" },
      };
    }
    if (isUrlVerification(payload)) {
      return {
        statusCode: 200,
        body: { challenge: payload.challenge },
      };
    }

    const messageEvent = extractMessageEvent(payload);
    const ignoreReason = shouldIgnoreMessageEvent(messageEvent, { requireMention: config.requireMention });
    if (ignoreReason && !(ignoreReason === "missing_mention" && isPublishConfirmationText(messageEvent?.normalizedText))) {
      return {
        statusCode: 200,
        body: { code: 0, msg: `ignored:${ignoreReason}` },
      };
    }

    return {
      statusCode: 200,
      body: { code: 0, msg: "ok" },
      backgroundTask: async () => processMessageEvent(messageEvent),
    };
  }

  return {
    async handleHttpRequest(rawBody) {
      let payload;
      try {
        payload = resolveEventPayload(rawBody, { encryptKey: config.encryptKey });
      } catch (error) {
        const message = String(error?.message || error);
        const statusCode = /not configured/i.test(message) ? 501 : 400;
        logger.error?.("failed to resolve callback payload", error);
        return {
          statusCode,
          body: { code: statusCode, msg: message },
        };
      }
      return handleEventPayload(payload);
    },
    handleEventPayload,
  };
}
