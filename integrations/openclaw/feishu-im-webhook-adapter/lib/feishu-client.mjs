function responseJson(response) {
  return response.text().then((text) => (text ? JSON.parse(text) : {}));
}

export function createFeishuClient(config, { fetchImpl = fetch } = {}) {
  let cachedToken = "";
  let cachedExpiresAt = 0;

  async function getTenantAccessToken() {
    if (cachedToken && cachedExpiresAt > Date.now() + 30_000) {
      return cachedToken;
    }
    const response = await fetchImpl(`${config.apiBaseUrl.replace(/\/$/, "")}/auth/v3/tenant_access_token/internal`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json; charset=utf-8",
      },
      body: JSON.stringify({
        app_id: config.appId,
        app_secret: config.appSecret,
      }),
    });
    const payload = await responseJson(response);
    if (!response.ok || Number(payload?.code || 0) !== 0 || !payload?.tenant_access_token) {
      throw new Error(`Feishu tenant_access_token failed: ${JSON.stringify(payload)}`);
    }
    cachedToken = String(payload.tenant_access_token);
    cachedExpiresAt = Date.now() + Math.max(Number(payload.expire || 0) - 60, 60) * 1000;
    return cachedToken;
  }

  async function replyTextMessage(messageId, text) {
    const token = await getTenantAccessToken();
    const response = await fetchImpl(
      `${config.apiBaseUrl.replace(/\/$/, "")}/im/v1/messages/${encodeURIComponent(messageId)}/reply`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json; charset=utf-8",
        },
        body: JSON.stringify({
          msg_type: "text",
          content: JSON.stringify({ text }),
        }),
      }
    );
    const payload = await responseJson(response);
    if (!response.ok || Number(payload?.code || 0) !== 0) {
      throw new Error(`Feishu reply failed: ${JSON.stringify(payload)}`);
    }
    return payload;
  }

  return {
    getTenantAccessToken,
    replyTextMessage,
  };
}
