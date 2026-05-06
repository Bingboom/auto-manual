import {
  ensureDispatchArgs,
  ensureStatusArg,
  renderMissingConfig,
  renderNoTrackedRun,
  renderStatusResult,
} from "./lib/commands.mjs";
import { COMMAND_DEFINITIONS } from "./lib/constants.mjs";
import { loadSettings, missingSettings } from "./lib/config.mjs";
import { dispatchCommandFlow, resolveTrackedRun } from "./lib/dispatch-flow.mjs";
import { createGitHubClient } from "./lib/github-client.mjs";
import { createStateStore } from "./lib/state-store.mjs";

async function dispatchCommand(ctx, api, command) {
  const settings = loadSettings(api.pluginConfig ?? {}, api.resolvePath);
  const missing = missingSettings(settings);
  if (missing.length) {
    return { text: renderMissingConfig(missing) };
  }

  let queueRecordId;
  try {
    queueRecordId = ensureDispatchArgs(command.commandName, ctx.args).queueRecordId;
  } catch (error) {
    return { text: error.message };
  }

  const github = createGitHubClient(settings);
  const stateStore = createStateStore(settings.stateFile);
  const result = await dispatchCommandFlow({
    command,
    queueRecordId,
    github,
    stateStore,
    settings,
  });
  if (result.text.includes("Dispatch accepted.") && result.text.includes("run_id:")) {
    const runIdLine = result.text
      .split("\n")
      .find((line) => line.startsWith("run_id:"));
    const runId = runIdLine ? runIdLine.split(":")[1].trim() : "";
    api.logger?.info?.(`Dispatched ${command.workflowFile} for ${queueRecordId} -> run ${runId}`);
  }
  return result;
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
  const { tracked, run, metadata, artifacts } = await resolveTrackedRun({
    github,
    stateStore,
    settings,
    requestedRunId,
  });
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
        acceptedAt: tracked?.dispatchedAt || "",
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
      acceptedAt: tracked?.dispatchedAt || "",
    }),
  };
}

const plugin = {
  id: "auto-manual-control-layer",
  name: "BlockClaw Auto Manual Operator",
  description: "Runs BlockClaw manual review/build/publish dispatches and reports GitHub run status.",
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
