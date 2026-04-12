#!/usr/bin/env node

import http from "node:http";

import { loadAdapterConfig, missingAdapterConfig } from "./lib/config.mjs";
import { createFeishuClient } from "./lib/feishu-client.mjs";
import { createMessageHandler } from "./lib/message-handler.mjs";
import { createRepoControl } from "./lib/repo-control.mjs";
import { createStateStore } from "./lib/state-store.mjs";

const config = loadAdapterConfig();
const missing = missingAdapterConfig(config);
if (missing.length) {
  console.error(`Missing adapter config: ${missing.join(", ")}`);
  process.exit(1);
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

function writeJson(res, statusCode, payload) {
  const body = `${JSON.stringify(payload)}\n`;
  res.writeHead(statusCode, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
  });
  res.end(body);
}

const server = http.createServer((req, res) => {
  if (req.method === "GET" && req.url === config.healthPath) {
    writeJson(res, 200, { ok: true });
    return;
  }
  if (req.method !== "POST" || req.url !== config.callbackPath) {
    writeJson(res, 404, { code: 404, msg: "not found" });
    return;
  }

  const chunks = [];
  req.on("data", (chunk) => chunks.push(chunk));
  req.on("end", async () => {
    try {
      const rawBody = Buffer.concat(chunks).toString("utf8");
      const result = await handler.handleHttpRequest(rawBody);
      writeJson(res, result.statusCode, result.body);
      if (typeof result.backgroundTask === "function") {
        queueMicrotask(() => {
          result.backgroundTask().catch((error) => {
            console.error("[feishu-im-webhook-adapter] background task failed", error);
          });
        });
      }
    } catch (error) {
      console.error("[feishu-im-webhook-adapter] request failed", error);
      writeJson(res, 500, { code: 500, msg: String(error?.message || error) });
    }
  });
});

server.listen(config.port, config.host, () => {
  console.log(
    `[feishu-im-webhook-adapter] listening on http://${config.host}:${config.port}${config.callbackPath}`
  );
});
