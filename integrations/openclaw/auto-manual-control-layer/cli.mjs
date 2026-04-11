#!/usr/bin/env node

import path from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID } from "node:crypto";

import {
  ensureRecordId,
  ensureStatusArg,
  renderDispatchResult,
  renderDuplicateRun,
  renderMissingConfig,
  renderNoTrackedRun,
  renderStatusResult,
} from "./lib/commands.mjs";
import { resolveCliSettings } from "./lib/cli-settings.mjs";
import { COMMAND_DEFINITIONS } from "./lib/constants.mjs";
import { createGitHubClient } from "./lib/github-client.mjs";
import { createStateStore } from "./lib/state-store.mjs";

const pluginRoot = path.dirname(fileURLToPath(import.meta.url));

function usage() {
  return [
    "Usage:",
    "  node cli.mjs dispatch <start-review|build-draft|publish> <record_id>",
    "  node cli.mjs status [last|<run_id>]",
  ].join("\n");
}

function missingSettings(settings) {
  return ["githubToken", "repoOwner", "repoName"].filter((field) => !settings[field]);
}

function commandByName(name) {
  const normalized = String(name || "").trim().toLowerCase();
  const aliases = {
    "start-review": "start-review",
    "start_review": "start-review",
    "build-draft": "build-draft",
    "build_draft": "build-draft",
    "publish": "publish",
  };
  const commandName = aliases[normalized];
  return COMMAND_DEFINITIONS.find((command) => command.commandName === commandName) || null;
}

function pluginRecordFromRun(command, queueRecordId, nonce, dispatchedAt, run) {
  return {
    commandName: command.commandName,
    workflowFile: command.workflowFile,
    workflowName: command.workflowName,
    queueRecordId,
    openclawDispatchNonce: nonce,
    dispatchedAt,
    runId: String(run.id),
    runUrl: run.html_url,
  };
}

async function dispatch(commandName, rawRecordId) {
  const settings = resolveCliSettings({ pluginRoot });
  const missing = missingSettings(settings);
  if (missing.length) {
    throw new Error(renderMissingConfig(missing));
  }

  const command = commandByName(commandName);
  if (!command) {
    throw new Error(`Unknown dispatch command: ${commandName}\n${usage()}`);
  }

  const queueRecordId = ensureRecordId(rawRecordId);
  const github = createGitHubClient(settings);
  const stateStore = createStateStore(settings.stateFile);
  const activeRun = await github.findActiveRunForRecord({
    workflowFile: command.workflowFile,
    queueRecordId,
    branch: settings.defaultBranch,
  });
  if (activeRun) {
    console.log(
      renderDuplicateRun({
        workflowName: command.workflowName,
        queueRecordId,
        runId: activeRun.id,
        runUrl: activeRun.html_url,
        status: activeRun.status,
      })
    );
    return;
  }

  const nonce = randomUUID();
  const dispatchedAt = new Date().toISOString();
  await github.dispatchWorkflow({
    workflowFile: command.workflowFile,
    ref: settings.defaultBranch,
    inputs: {
      trigger_source: "openclaw",
      queue_record_id: queueRecordId,
      openclaw_dispatch_nonce: nonce,
    },
  });

  await stateStore.saveRecord({
    commandName: command.commandName,
    workflowFile: command.workflowFile,
    workflowName: command.workflowName,
    queueRecordId,
    openclawDispatchNonce: nonce,
    dispatchedAt,
  });

  const run = await github.findDispatchedRun({
    workflowFile: command.workflowFile,
    queueRecordId,
    dispatchNonce: nonce,
    branch: settings.defaultBranch,
    dispatchedAfter: dispatchedAt,
  });

  if (!run) {
    console.log(
      renderDispatchResult({
        workflowName: command.workflowName,
        queueRecordId,
        runUrl: "",
        note: "Dispatch accepted. GitHub has not exposed the new run yet. Retry with `status last` after a few seconds.",
      })
    );
    return;
  }

  await stateStore.saveRecord(pluginRecordFromRun(command, queueRecordId, nonce, dispatchedAt, run));
  console.log(
    renderDispatchResult({
      workflowName: command.workflowName,
      queueRecordId,
      runUrl: run.html_url,
      runId: run.id,
      note: "Dispatch accepted.",
    })
  );
}

async function resolveTrackedRun(github, stateStore, settings, requestedRunId) {
  const tracked = requestedRunId ? await stateStore.getRecordByRunId(String(requestedRunId)) : await stateStore.getLastRecord();
  if (!tracked) {
    return { tracked: null, run: null, metadata: null, artifacts: [] };
  }

  let runId = requestedRunId ? String(requestedRunId) : tracked.runId;
  if (!runId && tracked.openclawDispatchNonce && tracked.workflowFile) {
    const run = await github.findDispatchedRun({
      workflowFile: tracked.workflowFile,
      queueRecordId: tracked.queueRecordId,
      dispatchNonce: tracked.openclawDispatchNonce,
      branch: settings.defaultBranch,
      dispatchedAfter: tracked.dispatchedAt,
    });
    if (run) {
      runId = String(run.id);
      await stateStore.saveRecord({
        ...tracked,
        runId,
        runUrl: run.html_url,
      });
    }
  }

  if (!runId) {
    return { tracked, run: null, metadata: null, artifacts: [] };
  }

  const run = await github.getRun(runId);
  const artifacts = await github.listArtifacts(runId);
  const metadata = await github.readMetadataArtifact(artifacts);
  await stateStore.saveRecord({
    ...tracked,
    runId,
    runUrl: run.html_url,
    queueRecordId: metadata?.queue_record_id || tracked.queueRecordId,
  });
  return { tracked, run, metadata, artifacts };
}

async function status(rawArg) {
  const settings = resolveCliSettings({ pluginRoot });
  const missing = missingSettings(settings);
  if (missing.length) {
    throw new Error(renderMissingConfig(missing));
  }

  const requestedRunId = ensureStatusArg(rawArg);
  const github = createGitHubClient(settings);
  const stateStore = createStateStore(settings.stateFile);
  const { tracked, run, metadata, artifacts } = await resolveTrackedRun(github, stateStore, settings, requestedRunId);
  if (!tracked && !requestedRunId) {
    console.log(renderNoTrackedRun());
    return;
  }
  if (!run) {
    console.log(
      renderStatusResult({
        workflowName: tracked?.workflowName || "Tracked workflow",
        queueRecordId: tracked?.queueRecordId || "",
        runId: requestedRunId || tracked?.runId || "",
        runUrl: tracked?.runUrl || "",
        status: "pending",
        conclusion: "",
        artifacts: [],
        metadata: metadata || {},
      })
    );
    return;
  }

  console.log(
    renderStatusResult({
      workflowName: tracked?.workflowName || run.name || "GitHub workflow",
      queueRecordId: metadata?.queue_record_id || tracked?.queueRecordId || "",
      runId: String(run.id),
      runUrl: run.html_url,
      status: run.status,
      conclusion: run.conclusion || "",
      artifacts,
      metadata: metadata || {},
    })
  );
}

async function main(argv) {
  const [action, ...rest] = argv;
  if (!action || action === "--help" || action === "-h") {
    console.log(usage());
    return 0;
  }
  if (action === "dispatch") {
    const [commandName, recordId] = rest;
    await dispatch(commandName, recordId);
    return 0;
  }
  if (action === "status") {
    await status(rest[0] || "");
    return 0;
  }
  throw new Error(`Unknown action: ${action}\n${usage()}`);
}

main(process.argv.slice(2)).catch((error) => {
  console.error(error?.message || String(error));
  process.exitCode = 1;
});
