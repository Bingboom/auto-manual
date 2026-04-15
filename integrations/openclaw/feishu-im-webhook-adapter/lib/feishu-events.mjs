import crypto from "node:crypto";

function parseJson(value) {
  if (value && typeof value === "object") {
    return value;
  }
  return JSON.parse(String(value || ""));
}

export function parseEventPayload(rawBody) {
  return parseJson(rawBody);
}

export function validateVerificationToken(payload, expectedToken) {
  if (!expectedToken) {
    return true;
  }
  const actual = String(payload?.token || payload?.header?.token || "").trim();
  return actual === expectedToken;
}

export function isUrlVerification(payload) {
  return payload?.type === "url_verification" && typeof payload?.challenge === "string";
}

export function isEncryptedEventPayload(payload) {
  return typeof payload?.encrypt === "string" && !!payload.encrypt.trim();
}

function aesKeyForEncryptKey(encryptKey) {
  const hash = crypto.createHash("sha256");
  hash.update(String(encryptKey || ""));
  return hash.digest();
}

export function decryptEncryptedEventPayload(payload, encryptKey) {
  if (!isEncryptedEventPayload(payload)) {
    return payload;
  }
  const encrypt = String(payload.encrypt || "").trim();
  const resolvedEncryptKey = String(encryptKey || "").trim();
  if (!resolvedEncryptKey) {
    throw new Error("encrypted callback received but FEISHU_IM_ENCRYPT_KEY is not configured");
  }
  try {
    const encryptBuffer = Buffer.from(encrypt, "base64");
    if (encryptBuffer.length <= 16) {
      throw new Error("ciphertext_too_short");
    }
    const decipher = crypto.createDecipheriv("aes-256-cbc", aesKeyForEncryptKey(resolvedEncryptKey), encryptBuffer.subarray(0, 16));
    let decrypted = decipher.update(encryptBuffer.subarray(16).toString("hex"), "hex", "utf8");
    decrypted += decipher.final("utf8");
    const parsed = parseJson(decrypted);
    const { encrypt: _discardedEncrypt, ...rest } = payload;
    return { ...parsed, ...rest };
  } catch {
    throw new Error("encrypted callback decrypt failed");
  }
}

export function resolveEventPayload(rawBody, { encryptKey = "" } = {}) {
  const payload = parseEventPayload(rawBody);
  return decryptEncryptedEventPayload(payload, encryptKey);
}

export function extractMessageText(messageContent) {
  if (!messageContent) {
    return "";
  }
  const parsed = parseJson(messageContent);
  return String(parsed?.text || "").trim();
}

export function stripMentionMarkup(text) {
  return String(text || "")
    .replace(/<at\b[^>]*>.*?<\/at>/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function hasMentionMarkup(text) {
  return /<at\b[^>]*>.*?<\/at>/i.test(String(text || ""));
}

export function isPublishConfirmationText(text) {
  const normalized = String(text || "").trim().toLowerCase();
  return normalized === "confirm" || normalized === "确认发布" || normalized === "确认" || normalized === "publish confirm";
}

export function extractMessageEvent(payload) {
  const header = payload?.header || {};
  const event = payload?.event || {};
  const message = event?.message || {};
  if (String(header?.event_type || "") !== "im.message.receive_v1") {
    return null;
  }
  if (String(message?.message_type || "") !== "text") {
    return null;
  }

  const rawText = extractMessageText(message?.content);
  return {
    eventId: String(header?.event_id || message?.message_id || "").trim(),
    eventType: String(header?.event_type || "").trim(),
    messageId: String(message?.message_id || "").trim(),
    chatId: String(message?.chat_id || "").trim(),
    chatType: String(message?.chat_type || "").trim(),
    senderId: String(event?.sender?.sender_id?.open_id || event?.sender?.sender_id?.user_id || "").trim(),
    senderType: String(event?.sender?.sender_type || "").trim(),
    rawText,
    normalizedText: stripMentionMarkup(rawText),
    hasMention: hasMentionMarkup(rawText),
  };
}

export function shouldIgnoreMessageEvent(messageEvent, { requireMention }) {
  if (!messageEvent) {
    return "not_supported";
  }
  if (!messageEvent.messageId || !messageEvent.chatId || !messageEvent.senderId) {
    return "missing_required_fields";
  }
  if (messageEvent.senderType.toLowerCase() === "app") {
    return "bot_message";
  }
  if (!messageEvent.normalizedText) {
    return "empty_text";
  }
  if (messageEvent.chatType && messageEvent.chatType !== "p2p" && requireMention && !messageEvent.hasMention) {
    return "missing_mention";
  }
  return "";
}
