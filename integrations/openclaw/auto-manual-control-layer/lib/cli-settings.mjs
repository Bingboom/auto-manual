import { execFileSync } from "node:child_process";
import path from "node:path";

export function parseRepositoryFromRemoteUrl(remoteUrl) {
  const text = String(remoteUrl || "").trim();
  if (!text) {
    return null;
  }

  let match = text.match(/^https?:\/\/[^/]+\/([^/]+)\/([^/]+?)(?:\.git)?$/i);
  if (match) {
    return { repoOwner: match[1], repoName: match[2] };
  }

  match = text.match(/^git@[^:]+:([^/]+)\/(.+?)(?:\.git)?$/i);
  if (match) {
    return { repoOwner: match[1], repoName: match[2] };
  }

  return null;
}

export function readGitHubToken() {
  const envToken = String(process.env.GITHUB_TOKEN || "").trim();
  if (envToken) {
    return envToken;
  }
  try {
    return execFileSync("gh", ["auth", "token"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
  } catch {
    return "";
  }
}

export function resolveRepositoryIdentity({ cwd = process.cwd() } = {}) {
  const envOwner = String(process.env.AUTO_MANUAL_GITHUB_REPO_OWNER || "").trim();
  const envName = String(process.env.AUTO_MANUAL_GITHUB_REPO_NAME || "").trim();
  if (envOwner && envName) {
    return { repoOwner: envOwner, repoName: envName };
  }

  const repository = String(process.env.GITHUB_REPOSITORY || "").trim();
  if (repository.includes("/")) {
    const [repoOwner, repoName] = repository.split("/", 2);
    if (repoOwner && repoName) {
      return { repoOwner, repoName };
    }
  }

  try {
    const remoteUrl = execFileSync("git", ["config", "--get", "remote.origin.url"], {
      cwd,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
    return parseRepositoryFromRemoteUrl(remoteUrl);
  } catch {
    return null;
  }
}

export function resolveCliSettings({ pluginRoot, cwd = process.cwd() }) {
  const repository = resolveRepositoryIdentity({ cwd }) || { repoOwner: "", repoName: "" };
  return {
    githubToken: readGitHubToken(),
    repoOwner: repository.repoOwner,
    repoName: repository.repoName,
    defaultBranch: String(process.env.AUTO_MANUAL_GITHUB_DEFAULT_BRANCH || "").trim() || "main",
    apiBaseUrl: String(process.env.AUTO_MANUAL_GITHUB_API_BASE_URL || "").trim() || "https://api.github.com",
    metadataArtifactName:
      String(process.env.AUTO_MANUAL_GITHUB_METADATA_ARTIFACT_NAME || "").trim() || "openclaw-run-metadata",
    dispatchTimeoutSeconds: Number.parseInt(process.env.AUTO_MANUAL_GITHUB_DISPATCH_TIMEOUT_SECONDS || "40", 10) || 40,
    stateFile:
      String(process.env.AUTO_MANUAL_OPENCLAW_STATE_FILE || "").trim() ||
      path.resolve(pluginRoot, "runtime", "auto-manual-control-layer-state.json"),
  };
}
