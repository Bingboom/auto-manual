// DingTalk Stream robot-message parsing, mirroring feishu-events.mjs but for the
// DingTalk `DWClientDownStream` envelope (TOPIC_ROBOT). The Stream payload's
// `data` is a JSON string of a DingTalkMessageData object.

function parseJson(value) {
  if (value && typeof value === "object") {
    return value;
  }
  try {
    return JSON.parse(String(value || ""));
  } catch {
    return null;
  }
}

// Shared with the Feishu adapter: a bare confirmation token that approves a
// pending publish even without an @mention.
export function isPublishConfirmationText(text) {
  const normalized = String(text || "").trim().toLowerCase();
  return normalized === "confirm" || normalized === "确认发布" || normalized === "确认" || normalized === "publish confirm";
}

// Build a channel-neutral messageEvent from a DingTalk robot message.
// `raw` is either the parsed DingTalkMessageData or the JSON string from
// DWClientDownStream.data.
export function extractMessageEvent(raw) {
  const data = parseJson(raw);
  if (!data) {
    return null;
  }
  if (String(data.msgtype || "") !== "text") {
    return null;
  }
  const conversationType = String(data.conversationType || "").trim(); // "1" = 1:1, "2" = group
  const isGroup = conversationType === "2";
  const text = String(data.text?.content || "").trim();
  const openConversationId = String(data.openConversationId || "").trim();
  return {
    // DingTalk msgId is unique per message; use it for dedup and as the id.
    eventId: String(data.msgId || "").trim(),
    messageId: String(data.msgId || "").trim(),
    // Conversation key for context/dedup; groups key on openConversationId.
    chatId: String((isGroup ? openConversationId || data.conversationId : data.conversationId) || "").trim(),
    conversationType,
    isGroup,
    senderId: String(data.senderStaffId || "").trim(),
    senderNick: String(data.senderNick || "").trim(),
    isInAtList: Boolean(data.isInAtList),
    rawText: text,
    // DingTalk Stream already delivers text without the @bot markup, so the
    // normalized text is the content as-is.
    normalizedText: text,
    // Reply routing carried on the event: DingTalk has no global "reply to
    // messageId", so the client answers via sessionWebhook or by conversation.
    sessionWebhook: String(data.sessionWebhook || "").trim(),
    sessionWebhookExpiredTime: Number(data.sessionWebhookExpiredTime || 0) || 0,
    openConversationId,
  };
}

export function shouldIgnoreMessageEvent(messageEvent, { requireMention } = {}) {
  if (!messageEvent) {
    return "not_supported";
  }
  if (!messageEvent.messageId || !messageEvent.chatId || !messageEvent.senderId) {
    return "missing_required_fields";
  }
  if (!messageEvent.normalizedText) {
    return "empty_text";
  }
  // DingTalk only delivers group messages that @the bot, but keep an explicit
  // guard so requireMention can stay authoritative.
  if (messageEvent.isGroup && requireMention && !messageEvent.isInAtList) {
    return "missing_mention";
  }
  return "";
}

// Whether a resolved sender staffId is allowed to drive the adapter.
// Empty allowFrom is fail-closed (deny) because this is a build/publish surface.
export function senderAllowed(senderId, allowFrom) {
  const list = (Array.isArray(allowFrom) ? allowFrom : []).map((entry) => String(entry).trim()).filter(Boolean);
  if (!list.length) {
    return false;
  }
  if (list.includes("*")) {
    return true;
  }
  return list.includes(String(senderId || "").trim());
}
