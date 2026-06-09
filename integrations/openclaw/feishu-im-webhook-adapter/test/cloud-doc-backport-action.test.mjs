import test from "node:test";
import assert from "node:assert/strict";

import {
  cloudDocBackportSenderAllowed,
  parseCloudDocBackportRequest,
} from "../lib/cloud-doc-backport-action.mjs";

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
    "把这个云文档修订回填 https://test.feishu.cn/wiki/MbI4w8xLyi8NYnkoe4acAs9Hnvc"
  );

  assert.equal(request.matched, true);
  assert.equal(request.docUrl, "https://test.feishu.cn/wiki/MbI4w8xLyi8NYnkoe4acAs9Hnvc");
  assert.equal(request.sourcePath, "");
  assert.deepEqual(request.missing, ["docs/_review/... .rst source path"]);
});

test("parseCloudDocBackportRequest ignores ordinary queue messages", () => {
  const request = parseCloudDocBackportRequest("开始review JE-2000F_EU");

  assert.equal(request.matched, false);
});

test("cloudDocBackportSenderAllowed requires an explicit allowlist", () => {
  assert.equal(cloudDocBackportSenderAllowed("ou_1", {}), false);
  assert.equal(cloudDocBackportSenderAllowed("ou_1", { cloudDocBackportAllowedSenderIds: ["ou_2"] }), false);
  assert.equal(cloudDocBackportSenderAllowed("ou_1", { cloudDocBackportAllowedSenderIds: ["ou_1"] }), true);
  assert.equal(cloudDocBackportSenderAllowed("ou_1", { cloudDocBackportAllowedSenderIds: ["*"] }), true);
});
