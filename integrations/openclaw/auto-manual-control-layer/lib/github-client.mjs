import { findActiveRunForRecord, findRecentActiveRun, findRunByDispatch } from "./run-matching.mjs";
import { isTransientError, withRetry } from "./transient.mjs";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function readJson(response) {
  if (response.status === 204) {
    return null;
  }
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

function isOptionalMetadataDependencyError(error) {
  const message = String(error?.message || "");
  return error?.code === "ERR_MODULE_NOT_FOUND" && message.includes("adm-zip");
}

export async function extractMetadataFromArtifactBuffer(
  buffer,
  { loadExtractor = () => import("./metadata-artifact.mjs") } = {}
) {
  try {
    const { extractMetadataFromZipBuffer } = await loadExtractor();
    return extractMetadataFromZipBuffer(buffer);
  } catch (error) {
    if (isOptionalMetadataDependencyError(error)) {
      return null;
    }
    throw error;
  }
}

export function createGitHubClient(settings) {
  const apiBaseUrl = settings.apiBaseUrl.replace(/\/$/, "");
  const repoBase = `${apiBaseUrl}/repos/${settings.repoOwner}/${settings.repoName}`;
  const headers = {
    Accept: "application/vnd.github+json",
    Authorization: `Bearer ${settings.githubToken}`,
    "X-GitHub-Api-Version": "2022-11-28",
  };

  async function requestUrl(url, init = {}) {
    const response = await fetch(url, {
      ...init,
      headers: {
        ...headers,
        ...(init.headers || {}),
      },
    });
    if (!response.ok) {
      const body = await response.text();
      const error = new Error(`GitHub API ${response.status}: ${body || response.statusText}`);
      error.httpStatus = response.status;
      throw error;
    }
    return response;
  }

  async function request(path, init = {}) {
    return requestUrl(`${repoBase}${path}`, init);
  }

  // GET reads are idempotent: a transient blip should retry, not fail the
  // command. The dispatch POST below is deliberately left unwrapped so a
  // retry can never double-trigger a workflow.
  async function getJson(path) {
    return withRetry(async () => readJson(await request(path)));
  }

  async function listWorkflowRuns(workflowFile, branch) {
    const payload = await getJson(
      `/actions/workflows/${encodeURIComponent(workflowFile)}/runs?branch=${encodeURIComponent(branch)}&per_page=20`
    );
    return payload?.workflow_runs || [];
  }

  return {
    async dispatchWorkflow({ workflowFile, ref, inputs }) {
      await request(`/actions/workflows/${encodeURIComponent(workflowFile)}/dispatches`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ ref, inputs }),
      });
    },
    async findActiveRunForRecord({ workflowFile, queueRecordId, branch }) {
      const runs = await listWorkflowRuns(workflowFile, branch);
      return findActiveRunForRecord(runs, queueRecordId);
    },
    async findRecentActiveRun({ workflowFile, branch, createdAfter }) {
      const runs = await listWorkflowRuns(workflowFile, branch);
      return findRecentActiveRun(runs, { createdAfter });
    },
    async findRecentRunByDispatch({ workflowFile, dispatchNonce, branch, dispatchedAfter }) {
      const runs = await listWorkflowRuns(workflowFile, branch);
      return findRunByDispatch(runs, {
        dispatchNonce,
        dispatchedAfter,
      });
    },
    async findDispatchedRun({ workflowFile, queueRecordId, dispatchNonce, branch, dispatchedAfter }) {
      const timeoutMs = settings.dispatchTimeoutSeconds * 1000;
      const deadline = Date.now() + timeoutMs;
      while (Date.now() < deadline) {
        try {
          const runs = await listWorkflowRuns(workflowFile, branch);
          const matched = findRunByDispatch(runs, {
            queueRecordId,
            dispatchNonce,
            dispatchedAfter,
          });
          if (matched) {
            return matched;
          }
        } catch (error) {
          // A transient blip mid-poll must not abort discovery: the dispatch is
          // already running, so keep trying until the deadline. A definitive
          // error (bad workflow file, auth) still surfaces to the caller.
          if (!isTransientError(error)) {
            throw error;
          }
        }
        await sleep(2000);
      }
      return null;
    },
    async getRun(runId) {
      return getJson(`/actions/runs/${encodeURIComponent(runId)}`);
    },
    async listArtifacts(runId) {
      const payload = await getJson(`/actions/runs/${encodeURIComponent(runId)}/artifacts?per_page=20`);
      return payload?.artifacts || [];
    },
    async readMetadataArtifact(artifacts) {
      const artifact = artifacts.find((candidate) => candidate.name === settings.metadataArtifactName);
      if (!artifact?.archive_download_url) {
        return null;
      }
      const arrayBuffer = await withRetry(async () => {
        const response = await requestUrl(artifact.archive_download_url);
        return response.arrayBuffer();
      });
      return extractMetadataFromArtifactBuffer(Buffer.from(arrayBuffer));
    },
  };
}
