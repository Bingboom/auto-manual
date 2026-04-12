import test from "node:test";
import assert from "node:assert/strict";

import {
  extractDingTalkNodeUrl,
  isDingTalkControlQueryText,
  parseDingTalkControlCommand,
} from "../lib/dingtalk-control.mjs";

test("extractDingTalkNodeUrl returns a stable node url", () => {
  assert.equal(
    extractDingTalkNodeUrl("绑定钉钉 union-123 https://alidocs.dingtalk.com/i/nodes/NkDwLng8ZLyr1dQ5Ha9gj6gBVKMEvZBY?utm_scene=team_space"),
    "https://alidocs.dingtalk.com/i/nodes/NkDwLng8ZLyr1dQ5Ha9gj6gBVKMEvZBY?utm_scene=team_space"
  );
});

test("isDingTalkControlQueryText recognizes supported query phrases", () => {
  assert.equal(isDingTalkControlQueryText("查看钉钉配置"), true);
  assert.equal(isDingTalkControlQueryText("dingtalk-config"), true);
  assert.equal(isDingTalkControlQueryText("查 JE-1000F_US"), false);
});

test("parseDingTalkControlCommand parses explicit dingtalk bind syntax", () => {
  const parsed = parseDingTalkControlCommand(
    "dingtalk-bind union-123 https://alidocs.dingtalk.com/i/nodes/node-123"
  );

  assert.deepEqual(parsed, {
    action: "update",
    recordId: "",
    operatorUnionId: "union-123",
    targetNodeUrl: "https://alidocs.dingtalk.com/i/nodes/node-123",
    error: "",
  });
});

test("parseDingTalkControlCommand parses labeled operator ids", () => {
  const parsed = parseDingTalkControlCommand(
    "绑定钉钉 operator_union_id=union-123 https://alidocs.dingtalk.com/i/nodes/node-123"
  );

  assert.equal(parsed.operatorUnionId, "union-123");
  assert.equal(parsed.targetNodeUrl, "https://alidocs.dingtalk.com/i/nodes/node-123");
});

test("parseDingTalkControlCommand reports missing operator union id", () => {
  const parsed = parseDingTalkControlCommand(
    "绑定钉钉 https://alidocs.dingtalk.com/i/nodes/node-123"
  );

  assert.equal(parsed.action, "update");
  assert.match(parsed.error, /operator_union_id/);
});

test("parseDingTalkControlCommand returns query command", () => {
  assert.deepEqual(parseDingTalkControlCommand("查看钉钉配置"), {
    action: "query",
    recordId: "",
    error: "",
  });
});
