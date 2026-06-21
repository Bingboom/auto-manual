import test from "node:test";
import assert from "node:assert/strict";

import {
  formatAcceptedReply,
  formatFailedReply,
  formatProcessingReply,
} from "../lib/reply-format.mjs";

test("formatAcceptedReply tells the operator the task was accepted and is processing", () => {
  const text = formatAcceptedReply({
    action_name: "build_draft_package",
    row: { record_id: "rec_eu_08", document_id: "JE-1000F_EU_0.8", workflow_action: "Build Draft Package" },
  });
  assert.match(text, /Build Draft Package/);
  assert.match(text, /record_id: rec_eu_08/);
  // 发起即受理: the accept reply already says it is processing.
  assert.match(text, /处理中/);
});

test("formatProcessingReply reports an in-flight task as 处理中, not done or failed", () => {
  const text = formatProcessingReply({
    record_id: "rec_eu_08",
    document_id: "JE-1000F_EU_0.8",
    workflow_action: "Build Draft Package",
    freshness_status: "writeback_pending",
    run_id: "346",
  });
  assert.match(text, /任务正在处理中/);
  assert.match(text, /record_id: rec_eu_08/);
  assert.match(text, /这个好了没/);
  assert.doesNotMatch(text, /已完成/);
});

test("formatFailedReply reports failure with the run's reason and next step", () => {
  const text = formatFailedReply(
    { record_id: "rec_eu_08", document_id: "JE-1000F_EU_0.8" },
    { conclusion: "failure", failure_message: "缺少 JE-1000F_CN 的规格数据", failure_next_step: "先补齐规格数据再重试" }
  );
  assert.match(text, /失败/);
  assert.match(text, /缺少 JE-1000F_CN 的规格数据/);
  assert.match(text, /先补齐规格数据再重试/);
  assert.match(text, /record_id: rec_eu_08/);
});
