import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const CONTROL_LAYER_CLI = "integrations/openclaw/auto-manual-control-layer/cli.mjs";
const CLOUD_DOC_BACKPORT_TOOL = "tools/cloud_doc_backport.py";

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

function safePathToken(value) {
  return String(value || "")
    .replace(/[^A-Za-z0-9._-]+/g, "-")
    .replace(/^[.-]+|[.-]+$/g, "") || "cloud-doc-backport";
}

function defaultCloudDocBackportRunId() {
  return `feishu-im-${new Date().toISOString().replace(/[^0-9A-Za-z]+/g, "-").replace(/-+$/g, "")}`;
}

function execFileResult(file, args, options) {
  return new Promise((resolve) => {
    execFile(file, args, options, (error, stdout, stderr) => {
      resolve({
        code: error ? (Number.isInteger(error.code) ? error.code : 1) : 0,
        stdout: String(stdout || ""),
        stderr: String(stderr || ""),
        error,
      });
    });
  });
}

async function runCloudDocBackportJson(config, { docUrl, sourcePath, runId = "", write = false }) {
  const resolvedRunId = safePathToken(runId || defaultCloudDocBackportRunId());
  const outDir = path.join("reports", "cloud_doc_backport", resolvedRunId);
  const args = [
    CLOUD_DOC_BACKPORT_TOOL,
    "run-review",
    "--doc-url",
    docUrl,
    "--source-path",
    sourcePath,
    "--run-id",
    resolvedRunId,
    "--out",
    outDir,
  ];
  if (write) {
    args.push("--write");
  }
  const result = await execFileResult(config.pythonBin, args, {
    cwd: config.repoRoot,
    env: process.env,
    maxBuffer: 1024 * 1024 * 16,
  });
  const manifestPath = path.join(config.repoRoot, outDir, "cloud_doc_backport_run.json");
  let manifest = null;
  try {
    manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));
  } catch (error) {
    if (result.code !== 0) {
      throw new Error(String(result.stderr || result.stdout || error?.message || "cloud-doc backport failed").trim());
    }
    throw error;
  }
  return {
    ...manifest,
    exit_code: result.code,
    stdout: result.stdout.trim(),
    stderr: result.stderr.trim(),
    run_id: resolvedRunId,
    manifest_path: path.relative(config.repoRoot, manifestPath),
  };
}

async function openCloudDocBackportPrJson(config, { manifestPath, branchName = "" }) {
  const args = [
    CLOUD_DOC_BACKPORT_TOOL,
    "open-pr",
    "--manifest",
    manifestPath,
    "--json",
  ];
  if (branchName) {
    args.push("--branch", branchName);
  }
  const result = await execFileResult(config.pythonBin, args, {
    cwd: config.repoRoot,
    env: process.env,
    maxBuffer: 1024 * 1024 * 8,
  });
  if (result.code !== 0) {
    throw new Error(String(result.stderr || result.stdout || "cloud-doc backport PR creation failed").trim());
  }
  return JSON.parse(result.stdout);
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
    async runStatus({ runId = "" } = {}) {
      const target = String(runId || "").trim() || "last";
      const { stdout } = await execFileAsync(config.nodeBin || "node", [CONTROL_LAYER_CLI, "status", target], {
        cwd: config.repoRoot,
        env: process.env,
        maxBuffer: 1024 * 1024 * 8,
      });
      return parseControlLayerStatus(stdout);
    },
    async runCloudDocBackportReview({ docUrl, sourcePath, runId = "", write = false }) {
      return runCloudDocBackportJson(config, { docUrl, sourcePath, runId, write });
    },
    async openCloudDocBackportPr({ manifestPath, branchName = "" }) {
      return openCloudDocBackportPrJson(config, { manifestPath, branchName });
    },
  };
}
