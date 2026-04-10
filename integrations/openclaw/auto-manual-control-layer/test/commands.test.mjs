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
