import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const CONTROL_LAYER_CLI = "integrations/openclaw/auto-manual-control-layer/cli.mjs";

// The control-layer `status` command prints `key: value` lines (workflow name,
// `status`, `state`, `conclusion`, `run`, failure_* ...). Parse them into an
// object so the adapter can read the live GitHub run state on demand.
function parseControlLayerStatus(stdout) {
  const result = { raw: String(stdout || "").trim() };
  for (const rawLine of result.raw.split("\n")) {
    const line = rawLine.trim();
    const separator = line.indexOf(":");
    if (separator <= 0) {
      continue;
    }
    const key = line.slice(0, separator).trim().toLowerCase().replace(/\s+/g, "_");
    if (!(key in result)) {
      result[key] = line.slice(separator + 1).trim();
    }
  }
  return result;
}

function workflowActionArg(actionName) {
  if (actionName === "start_review") {
    return "start-review";
  }
  if (actionName === "build_draft_package") {
    return "build-draft-package";
  }
  if (actionName === "publish") {
    return "publish";
  }
  return "";
}

async function runBuildJson(config, args) {
  const { stdout } = await execFileAsync(config.pythonBin, ["build.py", ...args], {
    cwd: config.repoRoot,
    env: process.env,
    maxBuffer: 1024 * 1024 * 8,
  });
  return JSON.parse(stdout);
}

export function createRepoControl(config) {
  return {
    async resolveAction({ messageText, confirmPublish = false }) {
      const args = [
        "queue-resolve-action",
        "--config",
        config.controlConfig,
        "--query-text",
        messageText,
        "--json",
      ];
      if (confirmPublish) {
        args.push("--confirm-publish");
      }
      return runBuildJson(config, args);
    },
    async queryRow({ queueScope, recordId, freshSince = "" }) {
      const args = [
        "queue-query",
        "--config",
        config.controlConfig,
        "--queue-scope",
        queueScope,
        "--record-id",
        recordId,
        "--json",
      ];
      if (freshSince) {
        args.push("--fresh-since", freshSince);
      }
      return runBuildJson(config, args);
    },
    async executeResolvedAction({ actionName, queueScope, recordId, confirmPublish = false, noWait = false }) {
      const args = [
        "queue-execute",
        "--config",
        config.controlConfig,
        "--queue-scope",
        queueScope,
        "--record-id",
        recordId,
        "--json",
      ];
      const workflowAction = workflowActionArg(actionName);
      if (workflowAction) {
        args.push("--query-workflow-action", workflowAction);
      }
      if (confirmPublish) {
        args.push("--confirm-publish");
      }
      if (noWait) {
        args.push("--no-wait");
      }
      return runBuildJson(config, args);
    },
    async queryManualIndex({ messageText, limit = 10 }) {
      const args = [
        "manual-index-query",
        "--config",
        config.controlConfig,
        "--query-text",
        messageText,
        "--limit",
        String(limit || 10),
        "--json",
      ];
      return runBuildJson(config, args);
    },
    async runStatus({ runId = "" } = {}) {
      const target = String(runId || "").trim() || "last";
      const { stdout } = await execFileAsync(config.nodeBin || "node", [CONTROL_LAYER_CLI, "status", target], {
        cwd: config.repoRoot,
        env: process.env,
        maxBuffer: 1024 * 1024 * 8,
      });
      return parseControlLayerStatus(stdout);
    },
  };
}
