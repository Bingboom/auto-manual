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
  formatCompletionReply,
  formatExecutionErrorReply,
  formatNoPendingPublishReply,
  formatPendingPublishReply,
  formatPublishCompletedButUnreadableReply,
  formatPublishConfirmationAcceptedReply,
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

export function createMessageHandler({ config, stateStore, repoControl, feishuClient, logger = console }) {
  const localProfile = config?.localProfile || null;

  async function react(messageId, stage) {
    await sendStageReaction({ config, feishuClient, localProfile, logger, messageId, stage });
  }

  async function rememberConversationContext(messageEvent, { row, queryText, actionName }) {
    if (!row || typeof stateStore.rememberConversationContext !== "function") {
      return;
    }
    await stateStore.rememberConversationContext({
      chatId: messageEvent.chatId,
      senderId: messageEvent.senderId,
      messageId: messageEvent.messageId,
      row,
      queryText,
      actionName,
      ttlSeconds: config.conversationContextTtlSeconds || 3600,
    });
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
        await repoControl.executeResolvedAction({
          actionName: "publish",
          queueScope: pending.row.queue_scope,
          recordId: pending.row.record_id,
          confirmPublish: true,
        });
        const latest = await repoControl.queryRow({
          queueScope: pending.row.queue_scope,
          recordId: pending.row.record_id,
        });
        const row = Array.isArray(latest?.rows) ? latest.rows[0] : null;
        if (row) {
          await rememberConversationContext(messageEvent, {
            row,
            queryText: pending.queryText || messageEvent.normalizedText,
            actionName: "publish",
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

    if (resolution.action_name === "query_status") {
      await rememberConversationContext(messageEvent, {
        row: resolution.row,
        queryText: normalizedMessage.normalizedText,
        actionName: resolution.action_name,
      });
      await react(messageEvent.messageId, "completed");
      await feishuClient.replyTextMessage(messageEvent.messageId, formatCompletionReply(resolution.row || {}, localProfile));
      return;
    }

    if (resolution.resolution_status === "resolved_batch") {
      const candidates = Array.isArray(resolution.candidates) ? resolution.candidates : [];
      const rows = [];
      const failures = [];
      await react(messageEvent.messageId, "accepted");
      await feishuClient.replyTextMessage(messageEvent.messageId, formatBatchAcceptedReply(resolution, localProfile));
      for (const candidate of candidates) {
        try {
          await repoControl.executeResolvedAction({
            actionName: resolution.action_name,
            queueScope: candidate.queue_scope || resolution.queue_scope,
            recordId: candidate.record_id,
            confirmPublish: false,
            noWait: true,
          });
          const latest = await repoControl.queryRow({
            queueScope: candidate.queue_scope || resolution.queue_scope,
            recordId: candidate.record_id,
          });
          const row = Array.isArray(latest?.rows) ? latest.rows[0] : null;
          rows.push(row || candidate);
        } catch (error) {
          logger.error?.("batch message execution failed", error);
          failures.push({
            record_id: candidate.record_id,
            message: error?.message || String(error),
          });
        }
      }
      await react(messageEvent.messageId, failures.length ? "error" : "completed");
      await feishuClient.replyTextMessage(
        messageEvent.messageId,
        formatBatchCompletionReply({ resolution, rows, failures }, localProfile)
      );
      return;
    }

    try {
      await rememberConversationContext(messageEvent, {
        row: resolution.row,
        queryText: normalizedMessage.normalizedText,
        actionName: resolution.action_name,
      });
      await react(messageEvent.messageId, "accepted");
      await feishuClient.replyTextMessage(messageEvent.messageId, formatAcceptedReply(resolution, localProfile));
      await repoControl.executeResolvedAction({
        actionName: resolution.action_name,
        queueScope: resolution.queue_scope,
        recordId: resolution.row.record_id,
        confirmPublish: false,
      });
      const latest = await repoControl.queryRow({
        queueScope: resolution.queue_scope,
        recordId: resolution.row.record_id,
      });
      const row = Array.isArray(latest?.rows) ? latest.rows[0] : null;
      if (row) {
        await rememberConversationContext(messageEvent, {
          row,
          queryText: normalizedMessage.normalizedText,
          actionName: resolution.action_name,
        });
      }
      await react(messageEvent.messageId, "completed");
      await feishuClient.replyTextMessage(
        messageEvent.messageId,
        row ? formatCompletionReply(row, localProfile) : formatRunCompletedButUnreadableReply(localProfile)
      );
    } catch (error) {
      logger.error?.("message execution failed", error);
      await react(messageEvent.messageId, "error");
      await feishuClient.replyTextMessage(messageEvent.messageId, formatExecutionErrorReply(error, localProfile));
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
