import { localReplyPhrase } from "./local-profile.mjs";

function summarizeRow(row, { includeDocumentLink = true } = {}) {
  const lines = [];
  if (row.document_id) {
    lines.push(`Document_ID: ${row.document_id}`);
  } else if (row.document_key) {
    lines.push(`Document_Key: ${row.document_key}`);
  }
  if (row.record_id) {
    lines.push(`record_id: ${row.record_id}`);
  }
  if (row.workflow_action) {
    lines.push(`Workflow_action: ${row.workflow_action}`);
  }
  if (row.build_family) {
    lines.push(`Build_family: ${row.build_family}`);
  }
  if (row.review_status) {
    lines.push(`Review_status: ${row.review_status}`);
  }
  if (row.git_ref) {
    lines.push(`Git_ref: ${row.git_ref}`);
  }
  if (row.pr_url) {
    lines.push(`PR_url: ${row.pr_url}`);
  }
  if (row.result) {
    lines.push(`${row.freshness_status === "stale_result" ? "旧构建结果" : "构建结果"}: ${row.result}`);
  }
  if (row.freshness_status && row.freshness_status !== "not_requested") {
    lines.push(`freshness_status: ${row.freshness_status}`);
  }
  if (row.result_built_at) {
    lines.push(`result_built_at: ${row.result_built_at}`);
  }
  if (row.accepted_at) {
    lines.push(`accepted_at: ${row.accepted_at}`);
  }
  if (row.run_id) {
    lines.push(`run_id: ${row.run_id}`);
  }
  if (row.run_url) {
    lines.push(`run: ${row.run_url}`);
  }
  if (includeDocumentLink && row.document_link) {
    lines.push(`Document link: ${row.document_link}`);
  }
  if (row.document_directory) {
    lines.push(`Document directory: ${row.document_directory}`);
  }
  return lines.join("\n");
}

function summarizeCandidate(candidate) {
  const pieces = [
    candidate.record_id,
    candidate.document_id || candidate.document_key || "-",
    candidate.lang || "",
    candidate.workflow_action || "-",
  ].filter(Boolean);
  return pieces.join(" | ");
}

export function formatResolutionReply(resolution, localProfile = null) {
  const lines = [resolution.summary];
  if (resolution.next_step) {
    lines.push(resolution.next_step);
  }
  if (Array.isArray(resolution.candidates) && resolution.candidates.length) {
    lines.push(localReplyPhrase(localProfile, "resolutionCandidateHeader", "候选行："));
    for (const candidate of resolution.candidates) {
      lines.push(`- ${candidate.record_id} | ${candidate.document_id || candidate.document_key || "-"} | ${candidate.workflow_action || "-"}`);
    }
  }
  return lines.join("\n");
}

export function formatBatchAcceptedReply(resolution, localProfile = null) {
  const actionLabel = {
    start_review: "Start Review",
    build_draft_package: "Build Draft Package",
    publish: "Publish",
    query_status: "Query Status",
  }[resolution.action_name] || resolution.action_name;
  const prefix = localReplyPhrase(localProfile, "acceptedPrefix", "已接受：");
  const candidates = Array.isArray(resolution.candidates) ? resolution.candidates : [];
  const lines = [`${prefix}${actionLabel} batch`, `matched_count: ${resolution.matched_count || candidates.length}`];
  for (const candidate of candidates.slice(0, 10)) {
    lines.push(`- ${summarizeCandidate(candidate)}`);
  }
  if (candidates.length > 10) {
    lines.push(`... 还有 ${candidates.length - 10} 条`);
  }
  return lines.join("\n");
}

export function formatAcceptedReply(resolution, localProfile = null) {
  const row = resolution.row || {};
  const actionLabel = {
    start_review: "Start Review",
    build_draft_package: "Build Draft Package",
    publish: "Publish",
    query_status: "Query Status",
  }[resolution.action_name] || resolution.action_name;
  const prefix = localReplyPhrase(localProfile, "acceptedPrefix", "已接受：");
  const processingNote = localReplyPhrase(
    localProfile,
    "acceptedProcessingNote",
    "任务正在处理中，远端开始执行了。完成后我会再更新，你也可以随时问我「这个好了没」。"
  );
  return [`${prefix}${actionLabel}`, summarizeRow(row), processingNote].filter(Boolean).join("\n");
}

export function formatProcessingReply(row, localProfile = null) {
  return [
    localReplyPhrase(localProfile, "processingPrefix", "任务正在处理中，最新状态如下："),
    summarizeRow(row),
    "（远端仍在执行或等待写回；完成后再问我「这个好了没」即可拿到结果。）",
  ]
    .filter(Boolean)
    .join("\n");
}

export function formatFailedReply(row, runStatus = null, localProfile = null) {
  const reason =
    String(runStatus?.failure_message || "").trim() ||
    String(runStatus?.failure_detail || "").trim() ||
    String(runStatus?.conclusion || "").trim() ||
    String(row?.result || "").trim();
  const lines = [localReplyPhrase(localProfile, "failedPrefix", "任务失败，最新状态如下：")];
  if (reason) {
    lines.push(`原因: ${reason}`);
  }
  const nextStep = String(runStatus?.failure_next_step || "").trim();
  if (nextStep) {
    lines.push(`建议: ${nextStep}`);
  }
  lines.push(summarizeRow(row));
  return lines.filter(Boolean).join("\n");
}

export function formatCompletionReply(row, localProfile = null) {
  return [localReplyPhrase(localProfile, "completionPrefix", "已完成，最新状态如下："), summarizeRow(row)].filter(Boolean).join("\n");
}

export function formatBatchCompletionReply({ resolution, rows = [], failures = [] }, localProfile = null) {
  const prefix = failures.length
    ? localReplyPhrase(localProfile, "batchPartialPrefix", "批量任务已处理完成，部分任务失败：")
    : localReplyPhrase(localProfile, "batchCompletionPrefix", "批量任务已发起，正在等待写回：");
  const lines = [prefix, `matched_count: ${resolution.matched_count || rows.length}`];
  for (const row of rows.slice(0, 10)) {
    lines.push(`- ${summarizeRow(row).replace(/\n/g, " | ")}`);
  }
  if (rows.length > 10) {
    lines.push(`... 还有 ${rows.length - 10} 条`);
  }
  for (const failure of failures.slice(0, 5)) {
    lines.push(`失败: ${failure.record_id || "-"} | ${String(failure.message || failure).trim()}`);
  }
  return lines.filter(Boolean).join("\n");
}

export function formatBatchStatusReply(
  { rows = [], failures = [], heading = "" },
  localProfile = null,
  { includeDocumentLinks = true } = {}
) {
  const lines = [
    heading || localReplyPhrase(localProfile, "batchStatusPrefix", "这批任务的最新状态如下："),
    `matched_count: ${rows.length}`,
  ];
  for (const row of rows.slice(0, 10)) {
    lines.push(`- ${summarizeRow(row, { includeDocumentLink: includeDocumentLinks }).replace(/\n/g, " | ")}`);
  }
  if (rows.length > 10) {
    lines.push(`... 还有 ${rows.length - 10} 条`);
  }
  for (const failure of failures.slice(0, 5)) {
    lines.push(`读取失败: ${failure.record_id || "-"} | ${String(failure.message || failure).trim()}`);
  }
  return lines.filter(Boolean).join("\n");
}

export function formatPendingPublishReply(resolution, localProfile = null) {
  const row = resolution.row || {};
  return [
    localReplyPhrase(localProfile, "pendingPublishPrefix", "已解析到一条 Publish 任务，但发布需要显式确认。"),
    summarizeRow(row),
    localReplyPhrase(localProfile, "pendingPublishInstruction", "请在 10 分钟内回复 `确认发布` 或 `confirm` 继续。"),
  ]
    .filter(Boolean)
    .join("\n");
}

export function formatExecutionErrorReply(error, localProfile = null) {
  return `${localReplyPhrase(localProfile, "executionErrorPrefix", "执行失败：")}${String(error?.message || error).trim()}`;
}

export function formatNoPendingPublishReply(localProfile = null) {
  return localReplyPhrase(localProfile, "noPendingPublish", "当前没有待确认的 Publish 请求。");
}

export function formatPublishConfirmationAcceptedReply(row, localProfile = null) {
  const prefix = localReplyPhrase(localProfile, "publishConfirmedPrefix", "已确认发布，开始执行。");
  return [prefix, row?.record_id ? `record_id: ${row.record_id}` : ""].filter(Boolean).join("\n");
}

export function formatPublishCompletedButUnreadableReply(localProfile = null) {
  return localReplyPhrase(localProfile, "publishCompletedButUnreadable", "发布已执行，但当前未能重新读取最新队列行。");
}

export function formatRunCompletedButUnreadableReply(localProfile = null) {
  return localReplyPhrase(localProfile, "runCompletedButUnreadable", "执行已结束，但当前未能重新读取最新队列行。");
}

export function formatRecordNoLongerAvailableReply(row = {}, localProfile = null) {
  const prefix = localReplyPhrase(
    localProfile,
    "recordNoLongerAvailable",
    "我重新查了 Feishu 多维表，这条记录现在查不到；旧会话记忆已忽略。"
  );
  const recordLine = row?.record_id ? `record_id: ${row.record_id}` : "";
  return [prefix, recordLine].filter(Boolean).join("\n");
}

export function formatCloudDocBackportNeedInputReply(request = {}, localProfile = null) {
  const missing = Array.isArray(request.missing) ? request.missing : [];
  return [
    localReplyPhrase(localProfile, "cloudDocBackportNeedInput", "云文档修订回填需要补齐输入。"),
    missing.length ? `missing: ${missing.join(", ")}` : "",
    "请发送：cloud-doc backport <飞书云文档链接> docs/_review/<model>/<region>/page/<page>.rst",
    "默认只 dry-run 出报告；要写入需显式开启 adapter 写入开关并在消息里写 --write。",
  ]
    .filter(Boolean)
    .join("\n");
}

export function formatCloudDocBackportDeniedReply(reason, localProfile = null) {
  return [
    localReplyPhrase(localProfile, "cloudDocBackportDenied", "云文档修订回填没有执行。"),
    String(reason || "").trim(),
  ]
    .filter(Boolean)
    .join("\n");
}

export function formatCloudDocBackportAcceptedReply(request = {}, localProfile = null) {
  return [
    localReplyPhrase(localProfile, "cloudDocBackportAccepted", "已接受云文档修订回填任务，开始生成报告。"),
    request.write ? "mode: write" : "mode: dry-run",
    request.sourcePath ? `source: ${request.sourcePath}` : "",
  ]
    .filter(Boolean)
    .join("\n");
}

export function formatCloudDocBackportResultReply(result = {}, localProfile = null) {
  const summary = result.summary || {};
  const reports = result.reports || {};
  const lines = [
    localReplyPhrase(localProfile, "cloudDocBackportResult", "云文档修订回填完成。"),
    `result: ${result.result || "-"}`,
    `mode: ${result.mode || "-"}`,
    `pr_ready: ${summary.pr_ready === true}`,
    `changed: ${summary.changed === true}`,
    `source_table_suggestions: ${summary.source_table_suggestions ?? 0}`,
  ];
  if (result.manifest_path) {
    lines.push(`manifest: ${result.manifest_path}`);
  }
  if (reports.run_markdown) {
    lines.push(`run_report: ${reports.run_markdown}`);
  }
  if (reports.diff_markdown) {
    lines.push(`diff_report: ${reports.diff_markdown}`);
  }
  if (reports.apply_markdown) {
    lines.push(`apply_report: ${reports.apply_markdown}`);
  }
  if (reports.verify_markdown) {
    lines.push(`verify_report: ${reports.verify_markdown}`);
  }
  if (Array.isArray(result.next_actions) && result.next_actions.length) {
    lines.push("next:");
    for (const action of result.next_actions.slice(0, 3)) {
      lines.push(`- ${action}`);
    }
  }
  return lines.filter(Boolean).join("\n");
}

export function formatCloudDocBackportPrNeedInputReply(request = {}, localProfile = null) {
  const missing = Array.isArray(request.missing) ? request.missing : [];
  return [
    localReplyPhrase(localProfile, "cloudDocBackportPrNeedInput", "云文档修订 PR 需要补齐输入。"),
    missing.length ? `missing: ${missing.join(", ")}` : "",
    "请发送：cloud-doc backport-pr reports/cloud_doc_backport/<run-id>/cloud_doc_backport_run.json",
  ]
    .filter(Boolean)
    .join("\n");
}

export function formatCloudDocBackportPrAcceptedReply(request = {}, localProfile = null) {
  return [
    localReplyPhrase(localProfile, "cloudDocBackportPrAccepted", "已接受云文档修订 PR 请求，开始检查 manifest 并创建 draft PR。"),
    request.manifestPath ? `manifest: ${request.manifestPath}` : "",
    request.branchName ? `branch: ${request.branchName}` : "",
  ]
    .filter(Boolean)
    .join("\n");
}

export function formatCloudDocBackportPrResultReply(result = {}, localProfile = null) {
  return [
    localReplyPhrase(localProfile, "cloudDocBackportPrResult", "云文档修订 draft PR 已创建。"),
    `result: ${result.result || "-"}`,
    result.pr_url ? `PR: ${result.pr_url}` : "",
    result.branch ? `branch: ${result.branch}` : "",
    result.commit ? `commit: ${result.commit}` : "",
    result.source_path ? `source: ${result.source_path}` : "",
    result.manifest_path ? `manifest: ${result.manifest_path}` : "",
    `source_table_suggestions: ${result.source_table_suggestions ?? 0}`,
  ]
    .filter(Boolean)
    .join("\n");
}
