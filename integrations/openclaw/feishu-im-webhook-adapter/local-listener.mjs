#!/usr/bin/env node

import { spawn } from "node:child_process";
import readline from "node:readline";

import { loadAdapterConfig, missingAdapterConfig } from "./lib/config.mjs";
import { createFeishuClient } from "./lib/feishu-client.mjs";
import { createMessageHandler } from "./lib/message-handler.mjs";
import { createRepoControl } from "./lib/repo-control.mjs";
import { createStateStore } from "./lib/state-store.mjs";

const IM_EVENT_TYPE = "im.message.receive_v1";

function parseArgs(argv) {
  const result = {
    controlConfig: "",
    larkCliBin: "",
    eventIdentity: "",
  };
  for (let index = 0; index < argv.length; index += 1) {
    const current = String(argv[index] || "").trim();
    if (!current) {
      continue;
    }
    if (current === "--control-config") {
      result.controlConfig = String(argv[index + 1] || "").trim();
      index += 1;
      continue;
    }
    if (current === "--lark-cli-bin") {
      result.larkCliBin = String(argv[index + 1] || "").trim();
      index += 1;
      continue;
    }
    if (current === "--event-identity") {
      result.eventIdentity = String(argv[index + 1] || "").trim();
      index += 1;
      continue;
    }
    if (current === "--help" || current === "-h") {
      return { ...result, help: true };
    }
    throw new Error(`Unknown argument: ${current}`);
  }
  return result;
}

function usage() {
  return [
    "Usage:",
    "  node local-listener.mjs [--control-config <config.yaml>] [--lark-cli-bin <bin>] [--event-identity <bot|user>]",
  ].join("\n");
}

function buildListenerConfig(baseConfig, args) {
  return {
    ...baseConfig,
    controlConfig: args.controlConfig || baseConfig.controlConfig,
    larkCliBin: args.larkCliBin || String(process.env.FEISHU_IM_LARK_CLI_BIN || "").trim() || "lark-cli",
    eventIdentity: args.eventIdentity || String(process.env.FEISHU_IM_EVENT_IDENTITY || "").trim() || "bot",
  };
}

function pumpStream(stream, prefix, writer = console.error) {
  if (!stream) {
    return;
  }
  const lineReader = readline.createInterface({ input: stream, crlfDelay: Infinity });
  lineReader.on("line", (line) => {
    if (line.trim()) {
      writer(`${prefix}${line}`);
    }
  });
}

async function main(argv) {
  const args = parseArgs(argv);
  if (args.help) {
    console.log(usage());
    return 0;
  }

  const config = buildListenerConfig(loadAdapterConfig(), args);
  const missing = missingAdapterConfig(config);
  if (missing.length) {
    throw new Error(`Missing adapter config: ${missing.join(", ")}`);
  }

  const stateStore = createStateStore(config.stateFile);
  const repoControl = createRepoControl(config);
  const feishuClient = createFeishuClient(config);
  const handler = createMessageHandler({
    config,
    stateStore,
    repoControl,
    feishuClient,
    logger: console,
  });

  const subscribeArgs = [
    "event",
    "+subscribe",
    "--as",
    config.eventIdentity,
    "--event-types",
    IM_EVENT_TYPE,
    "--quiet",
  ];
  const proc = spawn(config.larkCliBin, subscribeArgs, {
    cwd: config.repoRoot,
    env: process.env,
    stdio: ["ignore", "pipe", "pipe"],
    shell: process.platform === "win32",
  });

  pumpStream(proc.stderr, "[feishu-im-local-listener] ");
  console.log(
    `[feishu-im-local-listener] listening for ${IM_EVENT_TYPE} via ${config.larkCliBin} (identity=${config.eventIdentity}, control_config=${config.controlConfig})`
  );

  const stdoutReader = readline.createInterface({
    input: proc.stdout,
    crlfDelay: Infinity,
  });

  stdoutReader.on("line", async (line) => {
    const trimmed = String(line || "").trim();
    if (!trimmed) {
      return;
    }
    let payload;
    try {
      payload = JSON.parse(trimmed);
    } catch (error) {
      console.error(`[feishu-im-local-listener] ignored non-json event: ${trimmed}`);
      return;
    }

    try {
      const result = await handler.handleEventPayload(payload, { skipVerification: true });
      if (result.statusCode !== 200) {
        console.error(
          `[feishu-im-local-listener] event rejected: ${result.statusCode} ${String(result.body?.msg || "")}`.trim()
        );
        return;
      }
      if (typeof result.backgroundTask === "function") {
        void result.backgroundTask().catch((error) => {
          console.error("[feishu-im-local-listener] background task failed", error);
        });
      }
    } catch (error) {
      console.error("[feishu-im-local-listener] event handling failed", error);
    }
  });

  const exitCode = await new Promise((resolve, reject) => {
    proc.once("error", reject);
    proc.once("exit", (code, signal) => {
      stdoutReader.close();
      if (signal) {
        resolve(1);
        return;
      }
      resolve(Number.isInteger(code) ? code : 1);
    });
  });
  return exitCode;
}

main(process.argv.slice(2)).then(
  (exitCode) => {
    process.exitCode = exitCode;
  },
  (error) => {
    console.error(error?.message || String(error));
    process.exitCode = 1;
  }
);
