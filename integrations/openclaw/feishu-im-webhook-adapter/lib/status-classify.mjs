// On-demand progress classification for "这个好了没"-style queries.
//
// The operator's question is simple: is this task still processing, already
// done, or failed? We answer it from two authoritative sources at ask time
// (no polling):
//   1. the Feishu/Base row writeback — authoritative for the delivered result
//      (a fresh result means the link/output is actually ready), and
//   2. the live GitHub run state (`state:` from the control-layer `status`
//      command) — authoritative for "still running vs finished vs failed",
//      which also catches a run that failed before any writeback landed.
//
// "completed" means the deliverable is ready (fresh successful writeback). A run
// that GitHub has finished but whose result has not been written back yet is
// still reported as "processing", because the operator cannot use it yet.

const FAILURE_RESULT_PATTERN = /fail|失败|error|错误|cancel|取消|timed?\s*out|超时/i;
const TERMINAL_FAILURE_CONCLUSIONS = new Set([
  "failure",
  "cancelled",
  "timed_out",
  "startup_failure",
  "action_required",
]);

export function rowLooksFreshSuccess(row) {
  if (row?.result_is_fresh !== true) {
    return false;
  }
  return !FAILURE_RESULT_PATTERN.test(String(row?.result || ""));
}

export function rowLooksFreshFailure(row) {
  return row?.result_is_fresh === true && FAILURE_RESULT_PATTERN.test(String(row?.result || ""));
}

export function classifyTaskState({ row = {}, runStatus = null } = {}) {
  // The table is authoritative for the delivered result.
  if (rowLooksFreshFailure(row)) {
    return "failed";
  }
  if (rowLooksFreshSuccess(row)) {
    return "completed";
  }

  // Result not written back yet — disambiguate with the live run when we have it.
  const runState = String(runStatus?.state || "").trim();
  const conclusion = String(runStatus?.conclusion || "").trim().toLowerCase();
  if (runState === "failed" || TERMINAL_FAILURE_CONCLUSIONS.has(conclusion)) {
    return "failed";
  }

  // queued / in_progress, or run finished but the writeback has not landed yet:
  // the deliverable is not usable, so it is still "processing" from the operator's
  // point of view.
  return "processing";
}
