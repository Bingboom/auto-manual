import test from "node:test";
import assert from "node:assert/strict";

import {
  cloudDocBackportSenderAllowed,
  inferCloudDocBackportTarget,
  parseCloudDocBackportApprovalRequest,
  parseCloudDocBackportPrRequest,
  parseCloudDocBackportRequest,
} from "../lib/cloud-doc-backport-action.mjs";

const HASH_A = "a".repeat(64);
const HASH_B = "b".repeat(64);

test("parseCloudDocBackportRequest extracts Feishu doc, review source, run id, and write mode", () => {
  const request = parseCloudDocBackportRequest(
    "cloud-doc backport --write --run-id run-123 https://test.feishu.cn/wiki/MbI4w8xLyi8NYnkoe4acAs9Hnvc docs/_review/JE-2000F/EU/page/00_preface.rst"
  );

  assert.equal(request.matched, true);
  assert.equal(request.docUrl, "https://test.feishu.cn/wiki/MbI4w8xLyi8NYnkoe4acAs9Hnvc");
  assert.equal(request.sourcePath, "docs/_review/JE-2000F/EU/page/00_preface.rst");
  assert.equal(request.runId, "run-123");
  assert.equal(request.write, true);
  assert.deepEqual(request.missing, []);
});

test("parseCloudDocBackportRequest asks for source path when only a cloud doc link is present", () => {
  const request = parseCloudDocBackportRequest(
    "把这个云文档修订回填 https://test.feishu.cn/wiki/MbI4w8xLyi8NYnkoe4acAs9Hnvc manual_je2000f_eu_en_0.7 副本"
  );

  assert.equal(request.matched, true);
  assert.equal(request.docUrl, "https://test.feishu.cn/wiki/MbI4w8xLyi8NYnkoe4acAs9Hnvc");
  assert.equal(request.sourcePath, "");
  assert.deepEqual(request.targetHint, {
    model: "JE-2000F",
    region: "EU",
    lang: "en",
    version: "0.7",
  });
  assert.deepEqual(request.missing, ["docs/_review/... .rst source path"]);
});

test("inferCloudDocBackportTarget reads manual cloud doc titles", () => {
  assert.deepEqual(inferCloudDocBackportTarget("manual_je2000f_eu_en_0.7 副本"), {
    model: "JE-2000F",
    region: "EU",
    lang: "en",
    version: "0.7",
  });
  assert.deepEqual(inferCloudDocBackportTarget("根据 JE-1000F_EU_fr_0.5 回填"), {
    model: "JE-1000F",
    region: "EU",
    lang: "fr",
    version: "0.5",
  });
});

test("parseCloudDocBackportRequest ignores ordinary queue messages", () => {
  const request = parseCloudDocBackportRequest("开始review JE-2000F_EU");

  assert.equal(request.matched, false);
});

test("parseCloudDocBackportPrRequest extracts manifest path and branch", () => {
  const request = parseCloudDocBackportPrRequest(
    "cloud-doc backport-pr reports/cloud_doc_backport/run-1/cloud_doc_backport_run.json --branch review/JE-2000F-EU-fix"
  );

  assert.equal(request.matched, true);
  assert.equal(request.manifestPath, "reports/cloud_doc_backport/run-1/cloud_doc_backport_run.json");
  assert.equal(request.branchName, "review/JE-2000F-EU-fix");
  assert.deepEqual(request.missing, []);
});

test("parseCloudDocBackportPrRequest asks for manifest path", () => {
  const request = parseCloudDocBackportPrRequest("开 PR cloud-doc backport-pr");

  assert.equal(request.matched, true);
  assert.deepEqual(request.missing, ["reports/cloud_doc_backport/.../cloud_doc_backport_run.json manifest"]);
});

test("cloudDocBackportSenderAllowed requires an explicit allowlist", () => {
  assert.equal(cloudDocBackportSenderAllowed("ou_1", {}), false);
  assert.equal(cloudDocBackportSenderAllowed("ou_1", { cloudDocBackportAllowedSenderIds: ["ou_2"] }), false);
  assert.equal(cloudDocBackportSenderAllowed("ou_1", { cloudDocBackportAllowedSenderIds: ["ou_1"] }), true);
  assert.equal(cloudDocBackportSenderAllowed("ou_1", { cloudDocBackportAllowedSenderIds: ["*"] }), true);
});

test("parseCloudDocBackportApprovalRequest extracts run-id and hashes, not mistaking one for the other", () => {
  const request = parseCloudDocBackportApprovalRequest(`cloud-doc approve feishu-im-run-1 ${HASH_A} ${HASH_B}`);
  assert.equal(request.matched, true);
  assert.equal(request.decision, "approve");
  assert.equal(request.runId, "feishu-im-run-1");
  assert.deepEqual(request.hashes, [HASH_A, HASH_B]);
  assert.deepEqual(request.missing, []);
});

test("parseCloudDocBackportApprovalRequest honors an explicit run-id marker", () => {
  const request = parseCloudDocBackportApprovalRequest(`批准 run-id=cloud-doc-backport-local ${HASH_A}`);
  assert.equal(request.matched, true);
  assert.equal(request.decision, "approve");
  assert.equal(request.runId, "cloud-doc-backport-local");
  assert.deepEqual(request.hashes, [HASH_A]);
});

test("parseCloudDocBackportApprovalRequest treats reject as the decision and never approves on ambiguity", () => {
  const reject = parseCloudDocBackportApprovalRequest(`cloud-doc reject feishu-im-run-9 ${HASH_A}`);
  assert.equal(reject.matched, true);
  assert.equal(reject.decision, "reject");
  // both intents present -> reject wins (fail-safe).
  const ambiguous = parseCloudDocBackportApprovalRequest(`approve but reject feishu-im-run-9 ${HASH_A}`);
  assert.equal(ambiguous.decision, "reject");
});

test("parseCloudDocBackportApprovalRequest reports missing run-id and hashes", () => {
  const noHash = parseCloudDocBackportApprovalRequest("cloud-doc approve feishu-im-run-1");
  assert.equal(noHash.matched, true);
  assert.ok(noHash.missing.some((item) => item.includes("delta_hash")));
  const noRun = parseCloudDocBackportApprovalRequest(`approve ${HASH_A}`);
  assert.ok(noRun.missing.some((item) => item.includes("run-id")));
});

test("parseCloudDocBackportApprovalRequest ignores ordinary backport/review messages", () => {
  const request = parseCloudDocBackportApprovalRequest(
    "cloud-doc backport https://test.feishu.cn/wiki/X docs/_review/JE-2000F/EU/page/00_preface.rst"
  );
  assert.equal(request.matched, false);
});

test("parseCloudDocBackportApprovalRequest does not hijack a bare approval word without a handle", () => {
  // an approval word but no hash and no run-id -> not an approval command.
  assert.equal(parseCloudDocBackportApprovalRequest("批准这个修改").matched, false);
  assert.equal(parseCloudDocBackportApprovalRequest("looks good, approve please").matched, false);
});
