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

function compactPathPart(value) {
  return String(value || "").replace(/[/:\\]+/g, "_").trim();
}

function normalizeSearchText(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[_-]+/g, " ")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function sourceLabelFromFileName(filePath) {
  return normalizeSearchText(path.basename(filePath, path.extname(filePath)).replace(/^\d+_/, ""));
}

function sourceLabelsFromText(text) {
  const labels = [];
  const lines = String(text || "").split(/\r?\n/);
  for (let index = 0; index < lines.length; index += 1) {
    const line = String(lines[index] || "").trim();
    if (!line || /^\|[A-Z0-9_]+\|$/.test(line) || line.startsWith(".. ")) {
      continue;
    }
    const bold = line.match(/^\*\*(.+?)\*\*$/);
    if (bold) {
      labels.push(normalizeSearchText(bold[1]));
      break;
    }
    const nextLine = String(lines[index + 1] || "").trim();
    if (/^[=\-~^"']{3,}$/.test(nextLine)) {
      labels.push(normalizeSearchText(line));
      break;
    }
    if (/^#+\s+\S+/.test(line)) {
      labels.push(normalizeSearchText(line.replace(/^#+\s+/, "")));
      break;
    }
  }
  return labels.filter(Boolean);
}

async function pathExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function collectReviewSourceCandidates(config, { model, region, lang = "" }) {
  const docsReviewRoot = path.join(config.repoRoot, "docs", "_review");
  const targetRoots = [];
  const modelPart = compactPathPart(model);
  const regionPart = compactPathPart(region);
  const langPart = compactPathPart(lang);
  if (!modelPart || !regionPart) {
    return [];
  }
  if (langPart) {
    targetRoots.push(path.join(docsReviewRoot, modelPart, regionPart, langPart));
  }
  targetRoots.push(path.join(docsReviewRoot, modelPart, regionPart));

  const candidates = [];
  const seen = new Set();
  for (const root of targetRoots) {
    const pageDir = path.join(root, "page");
    if (!(await pathExists(pageDir))) {
      continue;
    }
    const entries = await fs.readdir(pageDir, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isFile() || !entry.name.endsWith(".rst")) {
        continue;
      }
      const absPath = path.join(pageDir, entry.name);
      const relPath = path.relative(config.repoRoot, absPath).split(path.sep).join("/");
      if (seen.has(relPath)) {
        continue;
      }
      seen.add(relPath);
      let labels = [sourceLabelFromFileName(entry.name)].filter(Boolean);
      try {
        const text = await fs.readFile(absPath, "utf8");
        labels = [...labels, ...sourceLabelsFromText(text)];
      } catch {
        // Candidate listing should not fail just because one file is unreadable;
        // the runner will validate the chosen source before it writes anything.
      }
      candidates.push({
        sourcePath: relPath,
        reviewRoot: path.relative(config.repoRoot, root).split(path.sep).join("/"),
        label: labels[0] || "",
        labels: [...new Set(labels)],
      });
    }
  }
  return candidates.sort((left, right) => left.sourcePath.localeCompare(right.sourcePath));
}

function scoreReviewSourceCandidate(candidate, request) {
  const text = normalizeSearchText(`${request.messageText || ""} ${request.docUrl || ""}`);
  const label = normalizeSearchText(candidate.label);
  if (!text || !label) {
    return 0;
  }
  let score = 0;
  const fileStem = normalizeSearchText(path.basename(candidate.sourcePath, ".rst"));
  if (fileStem && text.includes(fileStem)) {
    score += 80;
  }
  for (const candidateLabel of candidate.labels || [label]) {
    const normalizedLabel = normalizeSearchText(candidateLabel);
    if (!normalizedLabel) {
      continue;
    }
    if (text.includes(normalizedLabel)) {
      score += 50;
    }
    for (const part of normalizedLabel.split(" ").filter(Boolean)) {
      if (part.length >= 4 && text.includes(part)) {
        score += 10;
      }
    }
  }
  return score;
}

async function inferCloudDocBackportSourceJson(config, request = {}) {
  if (request.sourcePath) {
    return {
      status: "resolved",
      reason: "explicit_source_path",
      sourcePath: request.sourcePath,
      candidates: [],
      targetHint: request.targetHint || {},
    };
  }
  const target = request.targetHint || {};
  if (!target.model || !target.region) {
    return {
      status: "needs_input",
      reason: "target_not_found",
      sourcePath: "",
      candidates: [],
      targetHint: target,
    };
  }
  const candidates = await collectReviewSourceCandidates(config, target);
  if (!candidates.length) {
    return {
      status: "needs_input",
      reason: "review_bundle_not_found",
      sourcePath: "",
      candidates: [],
      targetHint: target,
    };
  }
  if (candidates.length === 1) {
    return {
      status: "resolved",
      reason: "single_review_source_candidate",
      sourcePath: candidates[0].sourcePath,
      candidates,
      targetHint: target,
    };
  }

  const scored = candidates
    .map((candidate) => ({ ...candidate, score: scoreReviewSourceCandidate(candidate, request) }))
    .sort((left, right) => right.score - left.score || left.sourcePath.localeCompare(right.sourcePath));
  if (scored[0]?.score > 0 && scored[0].score > (scored[1]?.score || 0)) {
    return {
      status: "resolved",
      reason: "unique_message_hint_match",
      sourcePath: scored[0].sourcePath,
      candidates: scored.slice(0, 10),
      targetHint: target,
    };
  }
  return {
    status: "needs_input",
    reason: "review_source_ambiguous",
    sourcePath: "",
    candidates: scored.slice(0, 10),
    targetHint: target,
  };
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
    async runCloudDocBackportReview({ docUrl, sourcePath, runId = "", write = false }) {
      return runCloudDocBackportJson(config, { docUrl, sourcePath, runId, write });
    },
    async inferCloudDocBackportSource(request) {
      return inferCloudDocBackportSourceJson(config, request);
    },
    async openCloudDocBackportPr({ manifestPath, branchName = "" }) {
      return openCloudDocBackportPrJson(config, { manifestPath, branchName });
    },
  };
}
