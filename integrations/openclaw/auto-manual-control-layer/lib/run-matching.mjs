function runTitle(run) {
  return [run.display_title, run.name].filter(Boolean).join(" / ");
}

function createdAtTime(run) {
  if (!run?.created_at) {
    return 0;
  }
  const parsed = Date.parse(run.created_at);
  return Number.isNaN(parsed) ? 0 : parsed;
}

export function findRunByDispatch(runs, { dispatchNonce, dispatchedAfter }) {
  const dispatchedAfterTime = dispatchedAfter ? Date.parse(dispatchedAfter) - 15000 : 0;
  return runs.find((run) => {
    const title = runTitle(run);
    return title.includes(dispatchNonce) && createdAtTime(run) >= dispatchedAfterTime;
  }) || null;
}

export function findActiveRunForRecord(runs, queueRecordId) {
  return runs.find((run) => {
    if (!queueRecordId) {
      return false;
    }
    if (run.status === "completed") {
      return false;
    }
    return runTitle(run).includes(queueRecordId);
  }) || null;
}

export function findRecentActiveRun(runs, { createdAfter }) {
  const createdAfterTime = createdAfter ? Date.parse(createdAfter) : 0;
  return runs.find((run) => {
    if (run.status === "completed") {
      return false;
    }
    return createdAtTime(run) >= createdAfterTime;
  }) || null;
}
