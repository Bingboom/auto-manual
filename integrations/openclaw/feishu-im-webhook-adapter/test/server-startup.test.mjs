import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";

import { missingWebhookAdapterConfig } from "../lib/config.mjs";

const adapterRoot = path.dirname(path.dirname(fileURLToPath(import.meta.url)));

test("missingWebhookAdapterConfig requires the verification token and names its env keys", () => {
  const missing = missingWebhookAdapterConfig({ appId: "cli_test", appSecret: "secret", verificationToken: "" });
  assert.equal(missing.length, 1);
  assert.match(missing[0], /FEISHU_IM_VERIFICATION_TOKEN/);
  assert.match(missing[0], /FEISHU_VERIFICATION_TOKEN/);
  assert.deepEqual(missingWebhookAdapterConfig({ appId: "cli_test", appSecret: "secret", verificationToken: "tok" }), []);
});

test("server.mjs refuses to start without a verification token", () => {
  const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), "feishu-im-adapter-startup-"));
  try {
    // Only an allowlisted environment reaches the child, so a token set in the
    // developer's shell cannot leak in; the port is irrelevant because startup
    // must fail before the server binds.
    const env = {
      PATH: process.env.PATH,
      HOME: tmpRoot,
      AUTO_MANUAL_REPO_ROOT: tmpRoot,
      FEISHU_IM_DISABLE_LOCAL_PROFILE: "true",
      FEISHU_IM_STATE_FILE: path.join(tmpRoot, "state.json"),
      FEISHU_IM_APP_ID: "cli_test",
      FEISHU_IM_APP_SECRET: "secret",
      FEISHU_IM_WEBHOOK_PORT: "1",
    };
    const result = spawnSync(process.execPath, [path.join(adapterRoot, "server.mjs")], {
      env,
      encoding: "utf8",
      timeout: 15000,
    });
    assert.equal(result.status, 1, `stdout=${result.stdout} stderr=${result.stderr}`);
    assert.match(result.stderr, /FEISHU_IM_VERIFICATION_TOKEN/);
    assert.match(result.stderr, /refusing to start/);
    assert.doesNotMatch(result.stdout, /listening on/);
  } finally {
    fs.rmSync(tmpRoot, { recursive: true, force: true });
  }
});
