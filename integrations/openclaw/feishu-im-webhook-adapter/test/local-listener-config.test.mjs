import test from "node:test";
import assert from "node:assert/strict";

import {
  buildLocalListenerConfig,
  buildLocalListenerSpawnEnv,
  localListenerUsage,
  parseLocalListenerArgs,
} from "../lib/local-listener-config.mjs";

test("parseLocalListenerArgs supports lark-cli-home", () => {
  const parsed = parseLocalListenerArgs([
    "--control-config",
    "configs/config.us.yaml",
    "--lark-cli-bin",
    "custom-lark-cli",
    "--event-identity",
    "user",
    "--lark-cli-home",
    ".tmp/lark-home",
  ]);

  assert.equal(parsed.controlConfig, "configs/config.us.yaml");
  assert.equal(parsed.larkCliBin, "custom-lark-cli");
  assert.equal(parsed.eventIdentity, "user");
  assert.match(parsed.larkCliHome, /\.tmp\/lark-home$/);
});

test("buildLocalListenerConfig prefers args over env", () => {
  const config = buildLocalListenerConfig(
    { controlConfig: "configs/config.us.yaml" },
    {
      controlConfig: "configs/config.ja.yaml",
      larkCliBin: "arg-cli",
      eventIdentity: "user",
      larkCliHome: "/tmp/arg-home",
    },
    {
      FEISHU_IM_LARK_CLI_BIN: "env-cli",
      FEISHU_IM_EVENT_IDENTITY: "bot",
      FEISHU_IM_LARK_CLI_HOME: "/tmp/env-home",
    }
  );

  assert.equal(config.controlConfig, "configs/config.ja.yaml");
  assert.equal(config.larkCliBin, "arg-cli");
  assert.equal(config.eventIdentity, "user");
  assert.equal(config.larkCliHome, "/tmp/arg-home");
});

test("buildLocalListenerSpawnEnv isolates HOME when larkCliHome is set", () => {
  const env = buildLocalListenerSpawnEnv(
    {
      larkCliHome: "/tmp/feishu-new-app",
    },
    {
      PATH: "/usr/bin:/bin",
      HOME: "/Users/pika",
      USERPROFILE: "C:\\Users\\pika",
    }
  );

  assert.equal(env.HOME, "/tmp/feishu-new-app");
  assert.equal(env.USERPROFILE, "/tmp/feishu-new-app");
  assert.equal(env.PATH, "/usr/bin:/bin");
});

test("localListenerUsage mentions lark-cli-home", () => {
  assert.match(localListenerUsage(), /lark-cli-home/);
});
