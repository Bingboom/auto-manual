const RECORD_ID_PATTERN = /^rec[a-zA-Z0-9]+$/;
const RUN_ID_PATTERN = /^\d+$/;
const PUBLISH_CONFIRMATION_TOKENS = new Set(["confirm", "confirmed", "--confirm"]);

function dispatchUsageExample(commandName) {
  return commandName === "publish" ? "/publish rec_xxx confirm" : `/${commandName || "build-draft"} rec_xxx`;
}

export function ensureRecordId(rawArgs) {
  const value = (rawArgs || "").trim();
  if (!value) {
    throw new Error("Provide one record id, for example `/publish rec_xxx`.");
  }
  if (!RECORD_ID_PATTERN.test(value)) {
    throw new Error("Record id must start with `rec` and contain only letters or numbers.");
  }
  return value;
}

export function ensureStatusArg(rawArgs) {
  const value = (rawArgs || "").trim();
  if (!value || value.toLowerCase() === "last") {
    return null;
  }
  if (!RUN_ID_PATTERN.test(value)) {
    throw new Error("`/manual-status` accepts either `last` or one numeric GitHub run id.");
  }
  return value;
}

export function ensureDispatchArgs(commandName, rawArgs) {
  const normalizedCommand = String(commandName || "").trim().toLowerCase();
  const tokens = String(rawArgs || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (!tokens.length) {
    throw new Error(`Provide one record id, for example \`${dispatchUsageExample(normalizedCommand)}\`.`);
  }

  let queueRecordId = "";
  let publishConfirmed = false;
  for (const token of tokens) {
    if (RECORD_ID_PATTERN.test(token)) {
      if (queueRecordId) {
        throw new Error("Provide only one record id per dispatch.");
      }
      queueRecordId = token;
      continue;
    }
    if (normalizedCommand === "publish" && PUBLISH_CONFIRMATION_TOKENS.has(token.toLowerCase())) {
      publishConfirmed = true;
      continue;
    }
    if (normalizedCommand === "publish") {
      throw new Error("Publish requires `/publish rec_xxx confirm`.");
    }
    throw new Error("Provide one record id, for example `/build-draft rec_xxx`.");
  }

  if (!queueRecordId) {
    throw new Error(`Provide one record id, for example \`${dispatchUsageExample(normalizedCommand)}\`.`);
  }
  if (normalizedCommand === "publish" && !publishConfirmed) {
    throw new Error("Publish requires explicit confirmation. Use `/publish rec_xxx confirm`.");
  }
  return { queueRecordId, publishConfirmed };
}

export function renderMissingConfig(missingFields) {
  return [
    "The OpenClaw control-layer plugin is not configured yet.",
    `Missing config: ${missingFields.join(", ")}`,
  ].join("\n");
}

export function renderDispatchResult({ workflowName, queueRecordId, runId, runUrl, acceptedAt, note }) {
  const lines = [
    `${workflowName}`,
    `record_id: ${queueRecordId}`,
  ];
  if (acceptedAt) {
    lines.push(`accepted_at: ${acceptedAt}`);
  }
  if (runId) {
    lines.push(`run_id: ${runId}`);
  }
  if (runUrl) {
    lines.push(`run: ${runUrl}`);
  }
  if (note) {
    lines.push(note);
  }
  return lines.join("\n");
}

export function renderDuplicateRun({ workflowName, queueRecordId, runId, runUrl, status, acceptedAt }) {
  const lines = [
    `${workflowName}`,
    `record_id: ${queueRecordId}`,
    `status: ${status || "in_progress"}`,
  ];
  if (acceptedAt) {
    lines.push(`accepted_at: ${acceptedAt}`);
  }
  if (runId) {
    lines.push(`run_id: ${runId}`);
  }
  if (runUrl) {
    lines.push(`run: ${runUrl}`);
  }
  lines.push("A matching queue worker is already active, so this dispatch will reuse that run.");
  return lines.join("\n");
}

export function renderNoTrackedRun() {
  return "No tracked OpenClaw-dispatched run was found yet. Trigger one command first or pass an explicit run id.";
}

export function renderStatusResult({ workflowName, queueRecordId, runId, runUrl, status, conclusion, artifacts, metadata, acceptedAt }) {
  const lines = [
    `${workflowName}`,
    `status: ${status || "pending"}`,
  ];
  const failureSummary = metadata?.failure_summary && typeof metadata.failure_summary === "object" ? metadata.failure_summary : null;
  if (conclusion) {
    lines.push(`conclusion: ${conclusion}`);
  }
  if (queueRecordId) {
    lines.push(`record_id: ${queueRecordId}`);
  }
  if (acceptedAt) {
    lines.push(`accepted_at: ${acceptedAt}`);
  }
  if (runId) {
    lines.push(`run_id: ${runId}`);
  }
  if (runUrl) {
    lines.push(`run: ${runUrl}`);
  }
  if (artifacts?.length) {
    lines.push(`artifacts: ${artifacts.map((artifact) => artifact.name).join(", ")}`);
  }
  if (failureSummary?.summary_code) {
    lines.push(`failure_code: ${failureSummary.summary_code}`);
  } else if (failureSummary?.code) {
    lines.push(`failure_code: ${failureSummary.code}`);
  }
  if (failureSummary?.summary_message) {
    lines.push(`failure_message: ${failureSummary.summary_message}`);
  } else if (failureSummary?.message) {
    lines.push(`failure_message: ${failureSummary.message}`);
  }
  if (failureSummary?.summary_next_step) {
    lines.push(`failure_next_step: ${failureSummary.summary_next_step}`);
  } else if (failureSummary?.next_step) {
    lines.push(`failure_next_step: ${failureSummary.next_step}`);
  }
  const firstFailure = Array.isArray(failureSummary?.failures) ? failureSummary.failures[0] : null;
  if (firstFailure?.target) {
    lines.push(`failure_target: ${firstFailure.target}`);
  } else if (failureSummary?.target) {
    lines.push(`failure_target: ${failureSummary.target}`);
  }
  if (firstFailure?.detail) {
    lines.push(`failure_detail: ${String(firstFailure.detail).replace(/\s+/g, " ").trim()}`);
  } else if (failureSummary?.detail) {
    lines.push(`failure_detail: ${String(failureSummary.detail).replace(/\s+/g, " ").trim()}`);
  }
  if (metadata?.publish_url) {
    lines.push(`publish_url: ${metadata.publish_url}`);
  }
  if (metadata?.document_link_url) {
    lines.push(`document_link_url: ${metadata.document_link_url}`);
  }
  if (metadata?.publish_html_index) {
    lines.push(`publish_html_index: ${metadata.publish_html_index}`);
  }
  return lines.join("\n");
}
