import { randomUUID } from "node:crypto";

import {
  renderDispatchResult,
  renderDuplicateRun,
} from "./commands.mjs";

const SHARED_QUEUE_COMMANDS = new Set(["start-review", "build-draft"]);
const SHARED_QUEUE_REUSE_WINDOW_MS = 15_000;

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

function isSharedQueueCommand(command) {
  return SHARED_QUEUE_COMMANDS.has(String(command?.commandName || "").trim().toLowerCase());
}

function createdAfterIso(windowMs = SHARED_QUEUE_REUSE_WINDOW_MS) {
  return new Date(Date.now() - windowMs).toISOString();
}

function isRecentTrackedRecord(record, windowMs = SHARED_QUEUE_REUSE_WINDOW_MS) {
  if (!record?.dispatchedAt) {
    return false;
  }
  const dispatchedAtTime = Date.parse(record.dispatchedAt);
  if (Number.isNaN(dispatchedAtTime)) {
    return false;
  }
  return Date.now() - dispatchedAtTime <= windowMs;
}

async function resolveRecentTrackedSharedRun({ command, github, stateStore, settings }) {
  const tracked = await stateStore.getLastRecordForWorkflow(command.workflowFile);
  if (!isRecentTrackedRecord(tracked)) {
    return null;
  }
  if (tracked.runId) {
    try {
      const run = await github.getRun(tracked.runId);
      if (run?.status !== "completed") {
        return { tracked, run };
      }
    } catch {
      // If GitHub no longer returns the run, fall through to the nonce lookup.
    }
  }
  if (tracked.openclawDispatchNonce) {
    const run = await github.findRecentRunByDispatch({
      workflowFile: command.workflowFile,
      dispatchNonce: tracked.openclawDispatchNonce,
      branch: settings.defaultBranch,
      dispatchedAfter: tracked.dispatchedAt,
    });
    if (run && run.status !== "completed") {
      const resolvedTracked = tracked.runId
        ? tracked
        : {
            ...tracked,
            runId: String(run.id),
            runUrl: run.html_url,
          };
      if (!tracked.runId) {
        await stateStore.saveRecord(resolvedTracked);
      }
      return { tracked: resolvedTracked, run };
    }
  }
  return { tracked, run: null };
}

function duplicateDispatchResult({ command, queueRecordId, run, tracked }) {
  return {
    text: renderDuplicateRun({
      workflowName: command.workflowName,
      queueRecordId,
      runId: run?.id || tracked?.runId || "",
      runUrl: run?.html_url || tracked?.runUrl || "",
      status: run?.status || "queued",
    }),
  };
}

export async function dispatchCommandFlow({ command, queueRecordId, github, stateStore, settings }) {
  const sharedQueueCommand = isSharedQueueCommand(command);
  if (sharedQueueCommand) {
    const recentTracked = await resolveRecentTrackedSharedRun({
      command,
      github,
      stateStore,
      settings,
    });
    if (recentTracked) {
      return duplicateDispatchResult({
        command,
        queueRecordId,
        run: recentTracked.run,
        tracked: recentTracked.tracked,
      });
    }
    const recentActiveRun = await github.findRecentActiveRun({
      workflowFile: command.workflowFile,
      branch: settings.defaultBranch,
      createdAfter: createdAfterIso(),
    });
    if (recentActiveRun) {
      return duplicateDispatchResult({
        command,
        queueRecordId,
        run: recentActiveRun,
        tracked: null,
      });
    }
  } else {
    const activeRun = await github.findActiveRunForRecord({
      workflowFile: command.workflowFile,
      queueRecordId,
      branch: settings.defaultBranch,
    });
    if (activeRun) {
      return duplicateDispatchResult({
        command,
        queueRecordId,
        run: activeRun,
        tracked: null,
      });
    }
  }

  const dispatchQueueRecordId = sharedQueueCommand ? "" : queueRecordId;
  const nonce = randomUUID();
  const dispatchedAt = new Date().toISOString();
  await github.dispatchWorkflow({
    workflowFile: command.workflowFile,
    ref: settings.defaultBranch,
    inputs: {
      trigger_source: "openclaw",
      queue_record_id: dispatchQueueRecordId,
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
    queueRecordId: dispatchQueueRecordId,
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
        note: "Dispatch accepted. GitHub has not exposed the new run yet. Retry with `status last` after a few seconds.",
      }),
    };
  }

  const record = pluginRecordFromRun(command, queueRecordId, nonce, dispatchedAt, run);
  await stateStore.saveRecord(record);
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

export async function resolveTrackedRun({ github, stateStore, settings, requestedRunId }) {
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

export const __testOnly = {
  SHARED_QUEUE_REUSE_WINDOW_MS,
  isRecentTrackedRecord,
};
