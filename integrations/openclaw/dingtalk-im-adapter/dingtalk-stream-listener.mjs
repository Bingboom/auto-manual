#!/usr/bin/env node

// DingTalk IM Stream-mode entrypoint — the DingTalk analogue of the Feishu
// adapter's local-listener.mjs. It opens a DingTalk Stream (long-connection)
// for an enterprise robot, so it needs no public webhook host/URL, and drives
// the same channel-neutral message handler (queue resolve/execute, batch
// dispatch, status polling) that the Feishu adapter uses.

import { DWClient, TOPIC_ROBOT } from "dingtalk-stream";

import { loadAdapterConfig, missingAdapterConfig } from "./lib/config.mjs";
import { createDingTalkClient } from "./lib/dingtalk-client.mjs";
import { extractMessageEvent, senderAllowed } from "./lib/dingtalk-events.mjs";
import { createMessageHandler } from "./lib/message-handler.mjs";
import { createRepoControl } from "./lib/repo-control.mjs";
import { createStateStore } from "./lib/state-store.mjs";

async function main() {
  const config = loadAdapterConfig();
  const missing = missingAdapterConfig(config);
  if (missing.length) {
    throw new Error(
      `Missing adapter config: ${missing.join(", ")}. Set DINGTALK_IM_CLIENT_ID and DINGTALK_IM_CLIENT_SECRET ` +
        "(the second DingTalk app's AppKey/AppSecret)."
    );
  }
  if (!config.allowFrom.length) {
    console.warn(
      "[dingtalk-im-adapter] DINGTALK_IM_ALLOW_FROM is empty — fail-closed: every sender is ignored. " +
        "Set it to staffId(s) (comma-separated) or '*' to open the bot."
    );
  }

  const stateStore = createStateStore(config.stateFile);
  const repoControl = createRepoControl(config);
  const imClient = createDingTalkClient(config);
  const handler = createMessageHandler({ config, stateStore, repoControl, imClient, logger: console });

  const client = new DWClient({
    clientId: config.clientId,
    clientSecret: config.clientSecret,
  });

  client.registerCallbackListener(TOPIC_ROBOT, (downStream) => {
    let data;
    try {
      data = JSON.parse(downStream?.data ?? "{}");
    } catch (error) {
      console.error("[dingtalk-im-adapter] ignored non-json stream event", error);
      return;
    }
    const messageEvent = extractMessageEvent(data);
    if (!messageEvent) {
      return;
    }
    if (!senderAllowed(messageEvent.senderId, config.allowFrom)) {
      console.warn(`[dingtalk-im-adapter] ignored sender not in allowFrom: ${messageEvent.senderId || "(unknown)"}`);
      return;
    }
    // Process asynchronously: the build.py dispatch and status polling can take
    // seconds, and the stream callback must return promptly. The DingTalk Stream
    // SDK acknowledges the message on callback return.
    handler.handleMessageEvent(messageEvent).catch((error) => {
      console.error("[dingtalk-im-adapter] message handling failed", error);
    });
  });

  await client.connect();
  console.log(
    `[dingtalk-im-adapter] connected via DingTalk Stream (robotCode=${config.robotCode}, ` +
      `control_config=${config.controlConfig}, allowFrom=${config.allowFrom.join(",") || "(none — fail-closed)"})`
  );
}

main().catch((error) => {
  console.error("[dingtalk-im-adapter] fatal", error?.message || error);
  process.exitCode = 1;
});
