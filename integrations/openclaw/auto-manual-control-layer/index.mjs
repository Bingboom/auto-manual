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
import { COMMAND_DEFINITIONS } from "./lib/constants.mjs";
import { loadSettings, missingSettings } from "./lib/config.mjs";
import { createGitHubClient } from "./lib/github-client.mjs";
import { createStateStore } from "./lib/state-store.mjs";

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

async function dispatchCommand(ctx, api, command) {
  const settings = loadSettings(api.pluginConfig ?? {}, api.resolvePath);
  const missing = missingSettings(settings);
  if (missing.length) {
    return { text: renderMissingConfig(missing) };
  }

  let queueRecordId;
  try {
    queueRecordId = ensureRecordId(ctx.args);
  } catch (error) {
    return { text: error.message };
  }

  const github = createGitHubClient(settings);
  const stateStore = createStateStore(settings.stateFile);
  const activeRun = await github.findActiveRunForRecord({
    workflowFile: command.workflowFile,
    queueRecordId,
    branch: settings.defaultBranch,
  });
  if (activeRun) {
    return {
      text: renderDuplicateRun({
        workflowName: command.workflowName,
        queueRecordId,
        runId: activeRun.id,
        runUrl: activeRun.html_url,
        status: activeRun.status,
      }),
    };
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

  const pendingRecord = {
    commandName: command.commandName,
    workflowFile: command.workflowFile,
    workflowName: command.workflowName,
    queueRecordId,
    openclawDispatchNonce: nonce,
    dispatchedAt,
  };
  await stateStore.saveRecord(pendingRecord);

  const run = await github.findDispatchedRun({
    workflowFile: command.workflowFile,
    queueRecordId,
    dispatchNonce: nonce,
    branch: settings.defaultBranch,
    dispatchedAfter: dispatchedAt,
  });

  if (!run) {
    return {
      text: renderDispatchResult({
        workflowName: command.workflowName,
        queueRecordId,
        runUrl: "",
        note: `Dispatch accepted. GitHub has not exposed the new run yet. Retry with /manual-status last after a few seconds.`,
      }),
    };
  }

  const record = pluginRecordFromRun(command, queueRecordId, nonce, dispatchedAt, run);
  await stateStore.saveRecord(record);
  api.logger?.info?.(`Dispatched ${command.workflowFile} for ${queueRecordId} -> run ${run.id}`);
  return {
    text: renderDispatchResult({
      workflowName: command.workflowName,
      queueRecordId,
      runUrl: run.html_url,
      runId: run.id,
      note: "Dispatch accepted.",
    }),
  };
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

async function manualStatus(ctx, api) {
  const settings = loadSettings(api.pluginConfig ?? {}, api.resolvePath);
  const missing = missingSettings(settings);
  if (missing.length) {
    return { text: renderMissingConfig(missing) };
  }

  let requestedRunId;
  try {
    requestedRunId = ensureStatusArg(ctx.args);
  } catch (error) {
    return { text: error.message };
  }

  const github = createGitHubClient(settings);
  const stateStore = createStateStore(settings.stateFile);
  const { tracked, run, metadata, artifacts } = await resolveTrackedRun(github, stateStore, settings, requestedRunId);
  if (!tracked && !requestedRunId) {
    return { text: renderNoTrackedRun() };
  }
  if (!run) {
    return {
      text: renderStatusResult({
        workflowName: tracked?.workflowName || "Tracked workflow",
        queueRecordId: tracked?.queueRecordId || "",
        runId: requestedRunId || tracked?.runId || "",
        runUrl: tracked?.runUrl || "",
        status: "pending",
        conclusion: "",
        artifacts: [],
        metadata: metadata || {},
      }),
    };
  }

  return {
    text: renderStatusResult({
      workflowName: tracked?.workflowName || run.name || "GitHub workflow",
      queueRecordId: metadata?.queue_record_id || tracked?.queueRecordId || "",
      runId: String(run.id),
      runUrl: run.html_url,
      status: run.status,
      conclusion: run.conclusion || "",
      artifacts,
      metadata: metadata || {},
    }),
  };
}

const plugin = {
  id: "auto-manual-control-layer",
  name: "Auto Manual Control Layer",
  description: "Dispatches auto-manual GitHub workflows and reports run status.",
  register(api) {
    for (const command of COMMAND_DEFINITIONS) {
      api.registerCommand({
        name: command.commandName,
        description: command.description,
        acceptsArgs: true,
        requireAuth: true,
        handler: async (ctx) => dispatchCommand(ctx, api, command),
      });
    }

    api.registerCommand({
      name: "manual-status",
      description: "Show the latest tracked auto-manual GitHub workflow status or inspect one explicit run id.",
      acceptsArgs: true,
      requireAuth: true,
      handler: async (ctx) => manualStatus(ctx, api),
    });
  },
};

export default plugin;
