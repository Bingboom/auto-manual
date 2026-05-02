import test from "node:test";
import assert from "node:assert/strict";

import { createFeishuClient } from "../lib/feishu-client.mjs";

function jsonResponse(payload, { ok = true } = {}) {
  return {
    ok,
    async text() {
      return JSON.stringify(payload);
    },
  };
}

test("addMessageReaction sends the Feishu reaction payload", async () => {
  const calls = [];
  const client = createFeishuClient(
    {
      apiBaseUrl: "https://open.feishu.cn/open-apis",
      appId: "app_id",
      appSecret: "secret",
    },
    {
      async fetchImpl(url, options) {
        calls.push({ url, options });
        if (String(url).includes("/auth/v3/tenant_access_token/internal")) {
          return jsonResponse({ code: 0, tenant_access_token: "tenant_token", expire: 7200 });
        }
        return jsonResponse({ code: 0, data: {} });
      },
    }
  );

  await client.addMessageReaction("om_123", "OK");

  assert.equal(calls.length, 2);
  assert.equal(calls[1].url, "https://open.feishu.cn/open-apis/im/v1/messages/om_123/reactions");
  assert.equal(calls[1].options.method, "POST");
  assert.deepEqual(JSON.parse(calls[1].options.body), {
    reaction_type: {
      emoji_type: "OK",
    },
  });
});
