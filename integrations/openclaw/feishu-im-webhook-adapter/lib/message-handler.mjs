import {
  extractMessageEvent,
  isEncryptedEventPayload,
  isPublishConfirmationText,
  isUrlVerification,
  parseEventPayload,
  shouldIgnoreMessageEvent,
  validateVerificationToken,
} from "./feishu-events.mjs";
import { parseDingTalkControlCommand } from "./dingtalk-control.mjs";
import {
  formatAcceptedReply,
  formatCompletionReply,
  formatDingTalkControlQueryReply,
  formatDingTalkControlUpdateReply,
  formatExecutionErrorReply,
  formatPendingPublishReply,
  formatResolutionReply,
} from "./reply-format.mjs";

async function replyAndIgnore(feishuClient, messageId, text) {
  if (messageId) {
    await feishuClient.replyTextMessage(messageId, text);
  }
}

export function createMessageHandler({ config, stateStore, repoControl, feishuClient, logger = console }) {
  async function processMessageEvent(messageEvent) {
    await stateStore.clearExpiredPublishes();
    if (!(await stateStore.claimProcessedEvent(messageEvent.eventId))) {
      return;
    }

    if (isPublishConfirmationText(messageEvent.normalizedText)) {
      const pending = await stateStore.consumePendingPublish({
        chatId: messageEvent.chatId,
        senderId: messageEvent.senderId,
      });
      if (!pending) {
        await replyAndIgnore(feishuClient, messageEvent.messageId, "当前没有待确认的 Publish 请求。");
        return;
      }
      try {
        await feishuClient.replyTextMessage(
          messageEvent.messageId,
          `已确认发布，开始执行。\nrecord_id: ${pending.row.record_id}`
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
        await feishuClient.replyTextMessage(
          messageEvent.messageId,
          row ? formatCompletionReply(row) : "发布已执行，但当前未能重新读取最新队列行。"
        );
      } catch (error) {
        logger.error?.("publish confirmation failed", error);
        await feishuClient.replyTextMessage(messageEvent.messageId, formatExecutionErrorReply(error));
      }
      return;
    }

    const dingtalkControlCommand = parseDingTalkControlCommand(messageEvent.normalizedText);
    if (dingtalkControlCommand) {
      if (dingtalkControlCommand.error) {
        await feishuClient.replyTextMessage(messageEvent.messageId, dingtalkControlCommand.error);
        return;
      }
      try {
        if (dingtalkControlCommand.action === "query") {
          const payload = await repoControl.queryDingTalkControlConfig({
            recordId: dingtalkControlCommand.recordId,
          });
          await feishuClient.replyTextMessage(messageEvent.messageId, formatDingTalkControlQueryReply(payload));
          return;
        }
        const payload = await repoControl.updateDingTalkControlConfig({
          operatorUnionId: dingtalkControlCommand.operatorUnionId,
          targetNodeUrl: dingtalkControlCommand.targetNodeUrl,
          recordId: dingtalkControlCommand.recordId,
        });
        await feishuClient.replyTextMessage(messageEvent.messageId, formatDingTalkControlUpdateReply(payload));
      } catch (error) {
        logger.error?.("dingtalk control command failed", error);
        await feishuClient.replyTextMessage(messageEvent.messageId, formatExecutionErrorReply(error));
      }
      return;
    }

    const resolution = await repoControl.resolveAction({
      messageText: messageEvent.normalizedText,
      confirmPublish: false,
    });

    if (resolution.resolution_status === "confirmation_required") {
      await stateStore.rememberPendingPublish({
        chatId: messageEvent.chatId,
        senderId: messageEvent.senderId,
        messageId: messageEvent.messageId,
        row: resolution.row,
        queryText: messageEvent.normalizedText,
        ttlSeconds: config.publishConfirmTtlSeconds,
      });
      await feishuClient.replyTextMessage(messageEvent.messageId, formatPendingPublishReply(resolution));
      return;
    }

    if (resolution.resolution_status !== "resolved") {
      await feishuClient.replyTextMessage(messageEvent.messageId, formatResolutionReply(resolution));
      return;
    }

    if (resolution.action_name === "query_status") {
      await feishuClient.replyTextMessage(messageEvent.messageId, formatCompletionReply(resolution.row || {}));
      return;
    }

    try {
      await feishuClient.replyTextMessage(messageEvent.messageId, formatAcceptedReply(resolution));
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
      await feishuClient.replyTextMessage(
        messageEvent.messageId,
        row ? formatCompletionReply(row) : "执行已结束，但当前未能重新读取最新队列行。"
      );
    } catch (error) {
      logger.error?.("message execution failed", error);
      await feishuClient.replyTextMessage(messageEvent.messageId, formatExecutionErrorReply(error));
    }
  }

  return {
    async handleHttpRequest(rawBody) {
      const payload = parseEventPayload(rawBody);
      if (isEncryptedEventPayload(payload)) {
        return {
          statusCode: 501,
          body: { code: 501, msg: "encrypted callbacks are not supported by this adapter yet" },
        };
      }
      if (!validateVerificationToken(payload, config.verificationToken)) {
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
    },
  };
}
