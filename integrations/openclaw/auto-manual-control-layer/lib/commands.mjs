const RECORD_ID_PATTERN = /^rec[a-zA-Z0-9]+$/;
const RUN_ID_PATTERN = /^\d+$/;

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

export function renderMissingConfig(missingFields) {
  return [
    "The OpenClaw control-layer plugin is not configured yet.",
    `Missing config: ${missingFields.join(", ")}`,
  ].join("\n");
}

export function renderDispatchResult({ workflowName, queueRecordId, runId, runUrl, note }) {
  const lines = [
    `${workflowName}`,
    `record_id: ${queueRecordId}`,
  ];
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

export function renderDuplicateRun({ workflowName, queueRecordId, runId, runUrl, status }) {
  const lines = [
    `${workflowName}`,
    `record_id: ${queueRecordId}`,
    `status: ${status || "in_progress"}`,
  ];
  if (runId) {
    lines.push(`run_id: ${runId}`);
  }
  if (runUrl) {
    lines.push(`run: ${runUrl}`);
  }
  lines.push("A matching run is already active, so the plugin refused a duplicate retry.");
  return lines.join("\n");
}

export function renderNoTrackedRun() {
  return "No tracked OpenClaw-dispatched run was found yet. Trigger one command first or pass an explicit run id.";
}

export function renderStatusResult({ workflowName, queueRecordId, runId, runUrl, status, conclusion, artifacts, metadata }) {
  const lines = [
    `${workflowName}`,
    `status: ${status || "pending"}`,
  ];
  if (conclusion) {
    lines.push(`conclusion: ${conclusion}`);
  }
  if (queueRecordId) {
    lines.push(`record_id: ${queueRecordId}`);
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
