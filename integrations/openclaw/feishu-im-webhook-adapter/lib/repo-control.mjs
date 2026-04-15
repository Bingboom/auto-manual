import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

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
    async queryRow({ queueScope, recordId }) {
      return runBuildJson(config, [
        "queue-query",
        "--config",
        config.controlConfig,
        "--queue-scope",
        queueScope,
        "--record-id",
        recordId,
        "--json",
      ]);
    },
    async executeResolvedAction({ actionName, queueScope, recordId, confirmPublish = false }) {
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
      return runBuildJson(config, args);
    },
  };
}
