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
  cloudDocBackportSenderAllowed,
  parseCloudDocBackportApprovalRequest,
  parseCloudDocBackportPrRequest,
  parseCloudDocBackportRequest,
} from "./cloud-doc-backport-action.mjs";
import {
  formatAcceptedReply,
  formatBatchAcceptedReply,
  formatBatchCompletionReply,
  formatBatchStatusReply,
  formatCloudDocBackportAcceptedReply,
  formatCloudDocBackportApprovalAcceptedReply,
  formatCloudDocBackportApprovalNeedInputReply,
  formatCloudDocBackportApprovalResultReply,
  formatCloudDocBackportDeniedReply,
  formatCloudDocBackportNeedInputReply,
  formatCloudDocBackportPrAcceptedReply,
  formatCloudDocBackportPrNeedInputReply,
  formatCloudDocBackportPrResultReply,
  formatCloudDocBackportRejectReply,
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

  async function replyBatchStatus(messageEvent, statusPayload) {
    await feishuClient.replyTextMessage(
      messageEvent.messageId,
      formatBatchStatusReply(statusPayload, localProfile, { includeDocumentLinks: false })
    );
    for (const link of documentLinksFromRows(statusPayload?.rows).slice(0, 10)) {
      await feishuClient.replyTextMessage(messageEvent.messageId, link);
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
    await react(messageEvent.messageId, state === "failed" ? "error" : "completed");
    if (state === "completed") {
      await feishuClient.replyTextMessage(messageEvent.messageId, formatCompletionReply(row, localProfile));
      return;
    }
    if (state === "failed") {
      await feishuClient.replyTextMessage(messageEvent.messageId, formatFailedReply(row, runStatus, localProfile));
      return;
    }
    await feishuClient.replyTextMessage(messageEvent.messageId, formatProcessingReply(row, localProfile));
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
      await replyBatchStatus(messageEvent, latest);
      return;
    }

    const cloudDocBackportApproval = parseCloudDocBackportApprovalRequest(normalizedMessage.normalizedText);
    if (cloudDocBackportApproval.matched) {
      if (!cloudDocBackportSenderAllowed(messageEvent.senderId, config)) {
        await react(messageEvent.messageId, "needs_input");
        await feishuClient.replyTextMessage(
          messageEvent.messageId,
          formatCloudDocBackportDeniedReply(
            "sender is not in FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOWED_SENDERS",
            localProfile
          )
        );
        return;
      }
      if (cloudDocBackportApproval.missing.length) {
        await react(messageEvent.messageId, "needs_input");
        await feishuClient.replyTextMessage(
          messageEvent.messageId,
          formatCloudDocBackportApprovalNeedInputReply(cloudDocBackportApproval, localProfile)
        );
        return;
      }
      const auditBase = {
        at: new Date().toISOString(),
        sender: messageEvent.senderId,
        decision: cloudDocBackportApproval.decision,
        run_id: cloudDocBackportApproval.runId,
        hashes: cloudDocBackportApproval.hashes,
      };
      const recordApproval = async (entry) => {
        if (typeof repoControl.recordCloudDocBackportApproval !== "function") {
          return;
        }
        try {
          await repoControl.recordCloudDocBackportApproval(entry);
        } catch (error) {
          logger.error?.("cloud-doc backport approval audit append failed", error);
        }
      };
      if (cloudDocBackportApproval.decision === "reject") {
        // Reject is an audit-only action: it never touches Bitable.
        await recordApproval({ ...auditBase, result: "rejected" });
        await react(messageEvent.messageId, "completed");
        await feishuClient.replyTextMessage(
          messageEvent.messageId,
          formatCloudDocBackportRejectReply(cloudDocBackportApproval, localProfile)
        );
        return;
      }
      // approve: source-table writes are gated SEPARATELY and default OFF, so an
      // approve runs dry-run until the operator enables ALLOW_SOURCE_WRITE.
      const sourceWrite = config.cloudDocBackportAllowSourceWrite === true;
      await react(messageEvent.messageId, "accepted");
      await feishuClient.replyTextMessage(
        messageEvent.messageId,
        formatCloudDocBackportApprovalAcceptedReply({ ...cloudDocBackportApproval, write: sourceWrite }, localProfile)
      );
      try {
        const applyResult = await repoControl.applyCloudDocBackportSourceTable({
          runId: cloudDocBackportApproval.runId,
          approvedHashes: cloudDocBackportApproval.hashes,
          write: sourceWrite,
          tableBindings: config.cloudDocBackportSourceTableBindings || [],
          tmWrite: config.cloudDocBackportAllowTmWrite === true,
          tmBinding: config.cloudDocBackportTmBinding || "",
        });
        await recordApproval({
          ...auditBase,
          write: sourceWrite,
          external_write: applyResult?.external_write === true,
          result: applyResult?.summary || {},
        });
        const failed = Boolean(
          applyResult?.summary && (applyResult.summary.verify_failed || applyResult.summary.error)
        );
        await react(messageEvent.messageId, failed ? "error" : "completed");
        await feishuClient.replyTextMessage(
          messageEvent.messageId,
          formatCloudDocBackportApprovalResultReply(applyResult, localProfile)
        );
      } catch (error) {
        logger.error?.("cloud-doc backport source-table apply failed", error);
        await react(messageEvent.messageId, "error");
        await feishuClient.replyTextMessage(messageEvent.messageId, formatExecutionErrorReply(error, localProfile));
      }
      return;
    }

    const cloudDocBackportPrRequest = parseCloudDocBackportPrRequest(normalizedMessage.normalizedText);
    if (cloudDocBackportPrRequest.matched) {
      if (!cloudDocBackportSenderAllowed(messageEvent.senderId, config)) {
        await react(messageEvent.messageId, "needs_input");
        await feishuClient.replyTextMessage(
          messageEvent.messageId,
          formatCloudDocBackportDeniedReply(
            "sender is not in FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOWED_SENDERS",
            localProfile
          )
        );
        return;
      }
      if (cloudDocBackportPrRequest.missing.length) {
        await react(messageEvent.messageId, "needs_input");
        await feishuClient.replyTextMessage(
          messageEvent.messageId,
          formatCloudDocBackportPrNeedInputReply(cloudDocBackportPrRequest, localProfile)
        );
        return;
      }
      if (!config.cloudDocBackportAllowPrCreate) {
        await react(messageEvent.messageId, "needs_input");
        await feishuClient.replyTextMessage(
          messageEvent.messageId,
          formatCloudDocBackportDeniedReply(
            "draft PR creation is disabled; set FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOW_PR_CREATE=true to allow explicit backport-pr requests",
            localProfile
          )
        );
        return;
      }
      await react(messageEvent.messageId, "accepted");
      await feishuClient.replyTextMessage(
        messageEvent.messageId,
        formatCloudDocBackportPrAcceptedReply(cloudDocBackportPrRequest, localProfile)
      );
      try {
        const prResult = await repoControl.openCloudDocBackportPr(cloudDocBackportPrRequest);
        await react(messageEvent.messageId, "completed");
        await feishuClient.replyTextMessage(
          messageEvent.messageId,
          formatCloudDocBackportPrResultReply(prResult, localProfile)
        );
      } catch (error) {
        logger.error?.("cloud-doc backport PR creation failed", error);
        await react(messageEvent.messageId, "error");
        await feishuClient.replyTextMessage(messageEvent.messageId, formatExecutionErrorReply(error, localProfile));
      }
      return;
    }

    let cloudDocBackportRequest = parseCloudDocBackportRequest(normalizedMessage.normalizedText);
    if (cloudDocBackportRequest.matched) {
      if (!cloudDocBackportSenderAllowed(messageEvent.senderId, config)) {
        await react(messageEvent.messageId, "needs_input");
        await feishuClient.replyTextMessage(
          messageEvent.messageId,
          formatCloudDocBackportDeniedReply(
            "sender is not in FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOWED_SENDERS",
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
        await react(messageEvent.messageId, "needs_input");
        await feishuClient.replyTextMessage(
          messageEvent.messageId,
          formatCloudDocBackportNeedInputReply(cloudDocBackportRequest, localProfile)
        );
        return;
      }
      if (cloudDocBackportRequest.write && !config.cloudDocBackportAllowWrite) {
        await react(messageEvent.messageId, "needs_input");
        await feishuClient.replyTextMessage(
          messageEvent.messageId,
          formatCloudDocBackportDeniedReply(
            "write mode is disabled; set FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOW_WRITE=true to allow explicit --write requests",
            localProfile
          )
        );
        return;
      }
      await react(messageEvent.messageId, "accepted");
      await feishuClient.replyTextMessage(
        messageEvent.messageId,
        formatCloudDocBackportAcceptedReply(cloudDocBackportRequest, localProfile)
      );
      try {
        const runResult = await repoControl.runCloudDocBackportReview(cloudDocBackportRequest);
        await react(messageEvent.messageId, runResult?.result === "FAIL" ? "error" : "completed");
        await feishuClient.replyTextMessage(messageEvent.messageId, formatCloudDocBackportResultReply(runResult, localProfile));
      } catch (error) {
        logger.error?.("cloud-doc backport failed", error);
        await react(messageEvent.messageId, "error");
        await feishuClient.replyTextMessage(messageEvent.messageId, formatExecutionErrorReply(error, localProfile));
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
          await react(messageEvent.messageId, "completed");
          await feishuClient.replyTextMessage(
            messageEvent.messageId,
            formatManualIndexReply(manualIndexResult, localProfile)
          );
          return;
        }
      } catch (error) {
        logger.error?.("manual index query failed", error);
        await react(messageEvent.messageId, "error");
        await feishuClient.replyTextMessage(messageEvent.messageId, formatExecutionErrorReply(error, localProfile));
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
          await react(messageEvent.messageId, "unresolved");
          await feishuClient.replyTextMessage(messageEvent.messageId, formatRecordNoLongerAvailableReply(row, localProfile));
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
