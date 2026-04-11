import test from "node:test";
import assert from "node:assert/strict";

import {
  ensureRecordId,
  ensureStatusArg,
  renderStatusResult,
} from "../lib/commands.mjs";

test("ensureRecordId validates rec ids", () => {
  assert.equal(ensureRecordId("recABC123"), "recABC123");
  assert.throws(() => ensureRecordId(""), /Provide one record id/);
  assert.throws(() => ensureRecordId("record-1"), /Record id must start/);
});

test("ensureStatusArg accepts last or numeric run ids", () => {
  assert.equal(ensureStatusArg(""), null);
  assert.equal(ensureStatusArg("last"), null);
  assert.equal(ensureStatusArg("12345"), "12345");
  assert.throws(() => ensureStatusArg("run-1"), /manual-status/);
});

test("renderStatusResult includes metadata fields when present", () => {
  const text = renderStatusResult({
    workflowName: "Feishu Build Queue",
    queueRecordId: "rec123",
    runId: "999",
    runUrl: "https://github.com/example/actions/runs/999",
    status: "completed",
    conclusion: "success",
    artifacts: [{ name: "feishu-build-queue-output" }, { name: "openclaw-run-metadata" }],
    metadata: {
      publish_url: "https://publish.example.com",
      document_link_url: "https://docs.example.com/doc",
      publish_html_index: "reports/releases/latest/index.html",
    },
  });
  assert.match(text, /record_id: rec123/);
  assert.match(text, /publish_url: https:\/\/publish\.example\.com/);
  assert.match(text, /artifacts: feishu-build-queue-output, openclaw-run-metadata/);
});

test("renderStatusResult includes structured failure summary fields when present", () => {
  const text = renderStatusResult({
    workflowName: "Feishu Start Review",
    queueRecordId: "rec_review",
    runId: "1001",
    runUrl: "https://github.com/example/actions/runs/1001",
    status: "completed",
    conclusion: "failure",
    artifacts: [{ name: "openclaw-run-metadata" }],
    metadata: {
      failure_summary: {
        summary_code: "missing_spec_data",
        summary_message: "缺少 JE-1000F_CN 的规格数据，无法进入 review。",
        summary_next_step: "请先补齐 JE-1000F_CN 在 Spec_Master 中的规格数据，再重试。",
        failures: [
          {
            target: "JE-1000F_CN",
            detail: "Failed to resolve Product Name from Spec_Master.csv",
          },
        ],
      },
    },
  });

  assert.match(text, /failure_code: missing_spec_data/);
  assert.match(text, /failure_message: 缺少 JE-1000F_CN 的规格数据，无法进入 review。/);
  assert.match(text, /failure_next_step: 请先补齐 JE-1000F_CN 在 Spec_Master 中的规格数据，再重试。/);
  assert.match(text, /failure_target: JE-1000F_CN/);
});
