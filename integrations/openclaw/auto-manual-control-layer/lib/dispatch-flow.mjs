import { randomUUID } from "node:crypto";

import {
  renderDispatchResult,
  renderDuplicateRun,
} from "./commands.mjs";
import { isTransientError } from "./transient.mjs";

const DISPATCH_UNCONFIRMED_NOTE =
  "Dispatch accepted. The workflow has been triggered on GitHub, but the run id " +
  "could not be confirmed locally yet (GitHub was slow or briefly unreachable). " +
  "This is a local read gap, not a failure — check progress with `status last`; " +
  "the remote run is unaffected.";

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

function duplicateDispatchResult({ command, queueRecordId, run, tracked }) {
  return {
    text: renderDuplicateRun({
      workflowName: command.workflowName,
      queueRecordId,
      runId: run?.id || tracked?.runId || "",
      runUrl: run?.html_url || tracked?.runUrl || "",
      status: run?.status || "queued",
      acceptedAt: tracked?.dispatchedAt || "",
    }),
  };
}

export async function dispatchCommandFlow({ command, queueRecordId, github, stateStore, settings }) {
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

  // The dispatch POST above already succeeded, so the action is committed.
  // Everything from here on is best-effort observation: discovering the run id
  // is convenience, not confirmation. A failure or timeout while looking it up
  // must never be reported as a dispatch failure — at worst we say "accepted,
  // run id not confirmed yet". The pending record (with the nonce) lets a later
  // `status` reconcile the run id.
  let run = null;
  try {
    run = await github.findDispatchedRun({
      workflowFile: command.workflowFile,
      queueRecordId,
      dispatchNonce: nonce,
      branch: settings.defaultBranch,
      dispatchedAfter: dispatchedAt,
    });
  } catch {
    run = null;
  }

  if (!run) {
    return {
      text: renderDispatchResult({
        workflowName: command.workflowName,
        queueRecordId,
        runUrl: "",
        acceptedAt: dispatchedAt,
        note: DISPATCH_UNCONFIRMED_NOTE,
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
      acceptedAt: dispatchedAt,
      note: "Dispatch accepted. The task is now processing — check the result later with `status last`; no need to wait synchronously.",
    }),
  };
}

export async function resolveTrackedRun({ github, stateStore, settings, requestedRunId }) {
  const tracked = requestedRunId ? await stateStore.getRecordByRunId(String(requestedRunId)) : await stateStore.getLastRecord();
  if (!tracked) {
    return { tracked: null, run: null, metadata: null, artifacts: [], observationError: null };
  }

  let runId = requestedRunId ? String(requestedRunId) : tracked.runId;
  if (!runId && tracked.openclawDispatchNonce && tracked.workflowFile) {
    try {
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
    } catch (error) {
      // Status is a read, not an action. A transient gap means "can't confirm
      // right now", not "failed" — surface the last known state instead.
      if (!isTransientError(error)) {
        throw error;
      }
      return { tracked, run: null, metadata: null, artifacts: [], observationError: error.message };
    }
  }

  if (!runId) {
    return { tracked, run: null, metadata: null, artifacts: [], observationError: null };
  }

  let run = null;
  try {
    run = await github.getRun(runId);
  } catch (error) {
    if (!isTransientError(error)) {
      throw error;
    }
    return { tracked, run: null, metadata: null, artifacts: [], observationError: error.message };
  }

  let artifacts = [];
  let metadata = null;
  let observationError = null;
  try {
    artifacts = await github.listArtifacts(runId);
    metadata = await github.readMetadataArtifact(artifacts);
  } catch (error) {
    if (!isTransientError(error)) {
      throw error;
    }
    // The run itself was read; only the artifact/metadata enrichment was missed.
    observationError = error.message;
  }

  await stateStore.saveRecord({
    ...tracked,
    runId,
    runUrl: run?.html_url || tracked.runUrl,
    queueRecordId: metadata?.queue_record_id || tracked.queueRecordId,
  });
  return { tracked, run, metadata, artifacts, observationError };
}
