import test from "node:test";
import assert from "node:assert/strict";

import { createDingTalkClient } from "../lib/dingtalk-client.mjs";

// Minimal fetch double that records calls and routes responses by URL.
function mockFetch(route) {
  const calls = [];
  const fetchImpl = async (url, options) => {
    const body = options?.body ? JSON.parse(options.body) : undefined;
    calls.push({ url, options, body });
    const res = route(url) || {};
    const status = res.status ?? 200;
    return {
      ok: status >= 200 && status < 300,
      status,
      async text() {
        return JSON.stringify(res.json ?? {});
      },
    };
  };
  return { fetchImpl, calls };
}

const baseConfig = {
  clientId: "ding_app",
  clientSecret: "secret",
  robotCode: "ding_app",
  apiBaseUrl: "https://api.dingtalk.com",
};

test("replies via sessionWebhook with markdown", async () => {
  const { fetchImpl, calls } = mockFetch((url) =>
    url.includes("/robot/sendBySession") ? { json: { errcode: 0 } } : { json: {} }
  );
  const client = createDingTalkClient(baseConfig, { fetchImpl });
  await client.replyTextMessage(
    { sessionWebhook: "https://oapi.dingtalk.com/robot/sendBySession?x=1", sessionWebhookExpiredTime: 0, senderId: "s" },
    "hello"
  );
  assert.equal(calls.length, 1);
  assert.match(calls[0].url, /sendBySession/);
  assert.equal(calls[0].body.msgtype, "markdown");
  assert.equal(calls[0].body.markdown.text, "hello");
});

test("falls back to the OTO robot API for 1:1 when there is no webhook", async () => {
  const { fetchImpl, calls } = mockFetch((url) => {
    if (url.endsWith("/v1.0/oauth2/accessToken")) return { json: { accessToken: "tok", expireIn: 7200 } };
    if (url.endsWith("/v1.0/robot/oToMessages/batchSend")) return { json: { processQueryKey: "pk" } };
    return { json: {} };
  });
  const client = createDingTalkClient(baseConfig, { fetchImpl });
  await client.replyTextMessage({ isGroup: false, senderId: "staff_9", sessionWebhook: "" }, "hi");
  const tokenCall = calls.find((c) => c.url.endsWith("/v1.0/oauth2/accessToken"));
  const sendCall = calls.find((c) => c.url.endsWith("/v1.0/robot/oToMessages/batchSend"));
  assert.ok(tokenCall);
  assert.equal(tokenCall.body.appKey, "ding_app");
  assert.ok(sendCall);
  assert.deepEqual(sendCall.body.userIds, ["staff_9"]);
  assert.equal(sendCall.body.msgKey, "sampleMarkdown");
  assert.equal(sendCall.options.headers["x-acs-dingtalk-access-token"], "tok");
});

test("falls back to the group robot API for group conversations", async () => {
  const { fetchImpl, calls } = mockFetch((url) => {
    if (url.endsWith("/v1.0/oauth2/accessToken")) return { json: { accessToken: "tok", expireIn: 7200 } };
    if (url.endsWith("/v1.0/robot/groupMessages/send")) return { json: { processQueryKey: "pk" } };
    return { json: {} };
  });
  const client = createDingTalkClient(baseConfig, { fetchImpl });
  await client.replyTextMessage({ isGroup: true, openConversationId: "cidGroup", senderId: "s", sessionWebhook: "" }, "团队你好");
  const sendCall = calls.find((c) => c.url.endsWith("/v1.0/robot/groupMessages/send"));
  assert.ok(sendCall);
  assert.equal(sendCall.body.openConversationId, "cidGroup");
});

test("falls back to the robot API when the webhook reply fails (e.g. expired)", async () => {
  const { fetchImpl, calls } = mockFetch((url) => {
    if (url.includes("sendBySession")) return { json: { errcode: 1, errmsg: "expired" } };
    if (url.endsWith("/v1.0/oauth2/accessToken")) return { json: { accessToken: "tok", expireIn: 7200 } };
    if (url.endsWith("/v1.0/robot/oToMessages/batchSend")) return { json: { processQueryKey: "pk" } };
    return { json: {} };
  });
  const client = createDingTalkClient(baseConfig, { fetchImpl });
  await client.replyTextMessage({ sessionWebhook: "https://x/sendBySession", senderId: "s9", isGroup: false }, "late reply");
  assert.ok(calls.some((c) => c.url.endsWith("/v1.0/robot/oToMessages/batchSend")));
});

test("caches the access token across calls", async () => {
  let tokenCalls = 0;
  const { fetchImpl } = mockFetch((url) => {
    if (url.endsWith("/v1.0/oauth2/accessToken")) {
      tokenCalls += 1;
      return { json: { accessToken: "tok", expireIn: 7200 } };
    }
    return { json: { processQueryKey: "pk" } };
  });
  const client = createDingTalkClient(baseConfig, { fetchImpl });
  await client.replyTextMessage({ senderId: "s", isGroup: false, sessionWebhook: "" }, "1");
  await client.replyTextMessage({ senderId: "s", isGroup: false, sessionWebhook: "" }, "2");
  assert.equal(tokenCalls, 1);
});

test("addMessageReaction is a no-op (DingTalk has no reaction API)", async () => {
  const client = createDingTalkClient(baseConfig, {
    fetchImpl: async () => {
      throw new Error("should not fetch");
    },
  });
  assert.equal(await client.addMessageReaction(), null);
});
