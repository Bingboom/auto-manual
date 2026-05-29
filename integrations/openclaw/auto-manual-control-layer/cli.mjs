#!/usr/bin/env node

import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  appendObservationNote,
  ensureDispatchArgs,
  ensureStatusArg,
  renderMissingConfig,
  renderNoTrackedRun,
  renderStatusResult,
} from "./lib/commands.mjs";
import { resolveCliSettings } from "./lib/cli-settings.mjs";
import { COMMAND_DEFINITIONS } from "./lib/constants.mjs";
import { dispatchCommandFlow, resolveTrackedRun } from "./lib/dispatch-flow.mjs";
import { createGitHubClient } from "./lib/github-client.mjs";
import { createStateStore } from "./lib/state-store.mjs";

const pluginRoot = path.dirname(fileURLToPath(import.meta.url));

function usage() {
  return [
    "Usage:",
    "  node cli.mjs dispatch <start-review|build-draft> <record_id>",
    "  node cli.mjs dispatch publish <record_id> confirm",
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

async function dispatch(commandName, rawArgs) {
  const settings = resolveCliSettings({ pluginRoot });
  const missing = missingSettings(settings);
  if (missing.length) {
    throw new Error(renderMissingConfig(missing));
  }

  const command = commandByName(commandName);
  if (!command) {
    throw new Error(`Unknown dispatch command: ${commandName}\n${usage()}`);
  }

  const { queueRecordId } = ensureDispatchArgs(commandName, rawArgs);
  const github = createGitHubClient(settings);
  const stateStore = createStateStore(settings.stateFile);
  const result = await dispatchCommandFlow({
    command,
    queueRecordId,
    github,
    stateStore,
    settings,
  });
  console.log(result.text);
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
  const { tracked, run, metadata, artifacts, observationError } = await resolveTrackedRun({
    github,
    stateStore,
    settings,
    requestedRunId,
  });
  if (!tracked && !requestedRunId) {
    console.log(renderNoTrackedRun());
    return;
  }
  if (!run) {
    console.log(
      appendObservationNote(
        renderStatusResult({
          workflowName: tracked?.workflowName || "Tracked workflow",
          queueRecordId: tracked?.queueRecordId || "",
          runId: requestedRunId || tracked?.runId || "",
          runUrl: tracked?.runUrl || "",
          status: "pending",
          conclusion: "",
          artifacts: [],
          metadata: metadata || {},
          acceptedAt: tracked?.dispatchedAt || "",
        }),
        observationError
      )
    );
    return;
  }

  console.log(
    appendObservationNote(
      renderStatusResult({
        workflowName: tracked?.workflowName || run.name || "GitHub workflow",
        queueRecordId: metadata?.queue_record_id || tracked?.queueRecordId || "",
        runId: String(run.id),
        runUrl: run.html_url,
        status: run.status,
        conclusion: run.conclusion || "",
        artifacts,
        metadata: metadata || {},
        acceptedAt: tracked?.dispatchedAt || "",
      }),
      observationError
    )
  );
}

async function main(argv) {
  const [action, ...rest] = argv;
  if (!action || action === "--help" || action === "-h") {
    console.log(usage());
    return 0;
  }
  if (action === "dispatch") {
    const [commandName, ...commandArgs] = rest;
    await dispatch(commandName, commandArgs.join(" "));
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
