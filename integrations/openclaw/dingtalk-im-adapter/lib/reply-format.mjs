import { localReplyPhrase } from "./local-profile.mjs";

function compactOneLine(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

function truncateOneLine(value, maxLength = 96) {
  const text = compactOneLine(value);
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, Math.max(maxLength - 1, 1))}…`;
}

function formatLocation(location = {}) {
  const heading = Array.isArray(location.heading_path)
    ? location.heading_path.map(compactOneLine).filter(Boolean).join(" > ")
    : "";
  const kindLine = [location.kind || "", location.line_no ? `L${location.line_no}` : ""].filter(Boolean).join(":");
  return [heading, kindLine].filter(Boolean).join(" / ") || "-";
}

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

function listText(value) {
  if (!Array.isArray(value)) {
    return compactOneLine(value || "");
  }
  return value.map(compactOneLine).filter(Boolean).join(", ");
}

function formatCounts(counts = {}) {
  if (!counts || typeof counts !== "object" || Array.isArray(counts)) {
    return "-";
  }
  const entries = Object.entries(counts).filter(([_key, value]) => Number(value) > 0);
  if (!entries.length) {
    return "-";
  }
  return entries.map(([key, value]) => `${key}=${value}`).join("; ");
}

function summarizeManualIndexRow(row = {}) {
  const title = compactOneLine(row.manual_name || row.document_name || row.manual_link_text || "-");
  const pieces = [
    listText(row.product_models) || row.business_id || row.record_id || "-",
    title,
    listText(row.region),
    listText(row.source_lang),
    listText(row.version),
    compactOneLine(row.archived_at || ""),
  ].filter(Boolean);
  const link = compactOneLine(row.manual_link || "");
  return link ? `${pieces.join(" | ")}\n  ${link}` : pieces.join(" | ");
}

function formatManualIndexOverview(overview = {}) {
  const lines = [
    `total_manuals: ${overview.total_manuals ?? 0}`,
    `distinct_product_model_count: ${overview.distinct_product_model_count ?? 0}`,
    `by_region: ${formatCounts(overview.by_region)}`,
    `by_source_lang: ${formatCounts(overview.by_source_lang)}`,
    `by_doc_type: ${formatCounts(overview.by_doc_type)}`,
    `by_category: ${formatCounts(overview.by_category)}`,
  ];
  if (overview.latest_archive_date) {
    lines.push(`latest_archive_date: ${overview.latest_archive_date}`);
  }
  return lines;
}

export function formatManualIndexReply(result = {}, localProfile = null) {
  const lines = [
    localReplyPhrase(localProfile, "manualIndexPrefix", "已读取发布文档管理表："),
    result.summary || "",
  ];
  if (result.query_type === "overview") {
    lines.push(...formatManualIndexOverview(result.overview || {}));
    return lines.filter(Boolean).join("\n");
  }
  const rows = Array.isArray(result.rows) ? result.rows : [];
  if (result.query_type === "inventory" && result.overview) {
    lines.push(...formatManualIndexOverview(result.overview).slice(0, 4));
  }
  if (!rows.length) {
    lines.push("没有查到匹配的说明书记录。");
  }
  for (const row of rows.slice(0, 10)) {
    lines.push(`- ${summarizeManualIndexRow(row)}`);
  }
  if (result.truncated) {
    lines.push(`还有 ${Math.max((result.matched_count || 0) - rows.length, 0)} 条未显示；可以补充产品型号、区域、语言或版本继续缩小。`);
  }
  if (result.next_step) {
    lines.push(result.next_step);
  }
  return lines.filter(Boolean).join("\n");
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
