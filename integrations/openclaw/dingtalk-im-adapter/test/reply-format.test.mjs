import test from "node:test";
import assert from "node:assert/strict";

import {
  formatAcceptedReply,
  formatCloudDocBackportResultReply,
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

test("formatCloudDocBackportResultReply reports only manifest evidence", () => {
  const text = formatCloudDocBackportResultReply({
    result: "DRY_RUN",
    mode: "dry-run",
    source_target: { path: "docs/_review/JE-2000F/EU/page/00_preface.rst" },
    section_selection: { resolved_title: "document preamble", applied: true },
    summary: { pr_ready: false, changed: false, review_source_changes: 1, source_table_suggestions: 1 },
    review_source_changes: [
      {
        route_class: "repo_review_text",
        change_type: "delete",
        location: { kind: "paragraph", line_no: 7, heading_path: [] },
        old_text: "**UK ВАЖЛИВО**",
      },
    ],
    source_table_suggestions: [
      {
        route_class: "source_table_suggestion",
        change_type: "insert",
        location: { kind: "table_row", line_no: 88, heading_path: ["SPECIFICATIONS", "OUTPUT PORTS"] },
        new_text: "| 1 × USB-C 30W | 30 W max. |",
      },
    ],
  });

  assert.match(text, /scope: docs\/_review\/JE-2000F\/EU\/page\/00_preface\.rst/);
  assert.match(text, /section: document preamble \(applied=true\)/);
  assert.match(text, /review_source_changes: 1/);
  assert.match(text, /UK ВАЖЛИВО/);
  assert.match(text, /USB-C 30W/);
  assert.doesNotMatch(text, /AC Output/);
  assert.doesNotMatch(text, /App Setup/);
});
