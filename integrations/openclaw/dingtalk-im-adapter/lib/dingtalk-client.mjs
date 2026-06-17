// Outbound DingTalk client, the DingTalk analogue of feishu-client.mjs.
//
// DingTalk replies are not "reply to a messageId" (there is no such API);
// instead a reply goes back via the inbound message's sessionWebhook (preferred,
// short-lived) or, as a fallback, the authenticated robot API addressed by
// conversation/user. So `replyTextMessage` takes the whole messageEvent rather
// than a Feishu-style messageId. DingTalk also has no message-reaction API, so
// `addMessageReaction` is a no-op kept for interface parity with the handler.

const DEFAULT_API_BASE = "https://api.dingtalk.com";

function markdownTitle(text) {
  return String(text || "").slice(0, 12).replace(/\s+/g, " ").trim() || "manual";
}

export function createDingTalkClient(config, { fetchImpl = fetch } = {}) {
  const apiBase = String(config?.apiBaseUrl || DEFAULT_API_BASE).replace(/\/$/, "");
  const clientId = String(config?.clientId || "").trim();
  const clientSecret = String(config?.clientSecret || "").trim();
  const robotCode = String(config?.robotCode || clientId).trim();
  let cachedToken = "";
  let cachedExpiresAt = 0;

  async function dingtalkApi(pathName, body, accessToken = "") {
    const headers = { "Content-Type": "application/json" };
    if (accessToken) {
      headers["x-acs-dingtalk-access-token"] = accessToken;
    }
    const response = await fetchImpl(`${apiBase}${pathName}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });
    const raw = await response.text();
    let payload = {};
    try {
      payload = raw ? JSON.parse(raw) : {};
    } catch {
      payload = { raw };
    }
    if (!response.ok) {
      throw new Error(`DingTalk API ${pathName} failed [${response.status}]: ${raw}`);
    }
    return payload;
  }

  async function getAccessToken() {
    if (cachedToken && cachedExpiresAt > Date.now() + 5 * 60 * 1000) {
      return cachedToken;
    }
    const payload = await dingtalkApi("/v1.0/oauth2/accessToken", {
      appKey: clientId,
      appSecret: clientSecret,
    });
    if (!payload?.accessToken) {
      throw new Error(`DingTalk accessToken failed: ${JSON.stringify(payload)}`);
    }
    cachedToken = String(payload.accessToken);
    cachedExpiresAt = Date.now() + (Number(payload.expireIn) || 7200) * 1000;
    return cachedToken;
  }

  async function replyViaWebhook(webhook, text) {
    const body = {
      msgtype: "markdown",
      markdown: { title: markdownTitle(text), text: String(text || "") },
      at: { atUserIds: [], isAtAll: false },
    };
    const response = await fetchImpl(webhook, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const raw = await response.text();
    let payload = {};
    try {
      payload = raw ? JSON.parse(raw) : {};
    } catch {
      payload = { raw };
    }
    if (!response.ok || Number(payload?.errcode || 0) !== 0) {
      throw new Error(`DingTalk webhook reply failed: ${JSON.stringify(payload)}`);
    }
    return payload;
  }

  async function sendMarkdown({ isGroup, openConversationId, userId }, text) {
    const accessToken = await getAccessToken();
    const msgParam = JSON.stringify({ title: markdownTitle(text), text: String(text || "") });
    if (isGroup && openConversationId) {
      return dingtalkApi(
        "/v1.0/robot/groupMessages/send",
        { robotCode, openConversationId, msgKey: "sampleMarkdown", msgParam },
        accessToken
      );
    }
    if (userId) {
      return dingtalkApi(
        "/v1.0/robot/oToMessages/batchSend",
        { robotCode, userIds: [userId], msgKey: "sampleMarkdown", msgParam },
        accessToken
      );
    }
    throw new Error("DingTalk reply has no sessionWebhook and no resolvable conversation/user target");
  }

  function webhookUsable(messageEvent) {
    if (!messageEvent?.sessionWebhook) {
      return false;
    }
    const expiresAt = Number(messageEvent.sessionWebhookExpiredTime || 0);
    // Expiry is epoch ms; an absent/zero value means "unknown" — still try it.
    return !expiresAt || Date.now() < expiresAt - 5000;
  }

  // Reply primitive consumed by the message handler. Prefers the inbound
  // sessionWebhook and falls back to the authenticated robot API so late
  // replies (e.g. after batch polling) still land if the webhook has expired.
  async function replyTextMessage(messageEvent, text) {
    if (!messageEvent) {
      return null;
    }
    if (webhookUsable(messageEvent)) {
      try {
        return await replyViaWebhook(messageEvent.sessionWebhook, text);
      } catch {
        // sessionWebhook may have expired between receipt and a late reply;
        // fall through to the authenticated robot API.
      }
    }
    return sendMarkdown(
      {
        isGroup: Boolean(messageEvent.isGroup),
        openConversationId: messageEvent.openConversationId,
        userId: messageEvent.senderId,
      },
      text
    );
  }

  // DingTalk has no message-reaction API; no-op kept for handler interface parity.
  async function addMessageReaction() {
    return null;
  }

  return {
    getAccessToken,
    replyTextMessage,
    addMessageReaction,
  };
}
