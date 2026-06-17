// DingTalk has no message-reaction API (unlike Feishu's messageReaction.create),
// so the Feishu adapter's per-stage emoji reactions degrade here to a single
// lightweight text acknowledgement when a message is first received. Every other
// stage already emits an explicit text reply from the message handler, so they
// stay no-ops to avoid chat noise.
const DEFAULT_RECEIVED_ACK = "✓ 已收到，处理中…";

export function receivedAckText(config = null) {
  return String(config?.receivedAckText || "").trim() || DEFAULT_RECEIVED_ACK;
}

export async function sendStageReaction({ config, imClient, logger = console, messageEvent, stage }) {
  if (stage !== "received" || !config?.ackOnReceived) {
    return false;
  }
  if (!messageEvent || typeof imClient?.replyTextMessage !== "function") {
    return false;
  }
  try {
    await imClient.replyTextMessage(messageEvent, receivedAckText(config));
    return true;
  } catch (error) {
    logger.warn?.("[dingtalk-im-adapter] received ack failed", error);
    return false;
  }
}
