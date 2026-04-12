function summarizeRow(row) {
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
    lines.push(`构建结果: ${row.result}`);
  }
  if (row.document_link) {
    lines.push(`Document link: ${row.document_link}`);
  }
  if (row.document_directory) {
    lines.push(`Document directory: ${row.document_directory}`);
  }
  return lines.join("\n");
}

export function formatResolutionReply(resolution) {
  const lines = [resolution.summary];
  if (resolution.next_step) {
    lines.push(resolution.next_step);
  }
  if (Array.isArray(resolution.candidates) && resolution.candidates.length) {
    lines.push("候选行：");
    for (const candidate of resolution.candidates) {
      lines.push(`- ${candidate.record_id} | ${candidate.document_id || candidate.document_key || "-"} | ${candidate.workflow_action || "-"}`);
    }
  }
  return lines.join("\n");
}

export function formatAcceptedReply(resolution) {
  const row = resolution.row || {};
  const actionLabel = {
    start_review: "Start Review",
    build_draft_package: "Build Draft Package",
    publish: "Publish",
    query_status: "Query Status",
  }[resolution.action_name] || resolution.action_name;
  return [`已接受：${actionLabel}`, summarizeRow(row)].filter(Boolean).join("\n");
}

export function formatCompletionReply(row) {
  return [`已完成，最新状态如下：`, summarizeRow(row)].filter(Boolean).join("\n");
}

export function formatPendingPublishReply(resolution) {
  const row = resolution.row || {};
  return [
    "已解析到一条 Publish 任务，但发布需要显式确认。",
    summarizeRow(row),
    "请在 10 分钟内回复 `确认发布` 或 `confirm` 继续。",
  ]
    .filter(Boolean)
    .join("\n");
}

export function formatExecutionErrorReply(error) {
  return `执行失败：${String(error?.message || error).trim()}`;
}

function summarizeDingTalkControl(payload) {
  const lines = [];
  if (payload.record_id) {
    lines.push(`record_id: ${payload.record_id}`);
  }
  if (payload.operator_union_id) {
    lines.push(`operator_union_id: ${payload.operator_union_id}`);
  }
  if (payload.default_target_node_id) {
    lines.push(`default_target_node_id: ${payload.default_target_node_id}`);
  }
  if (payload.default_target_node_url) {
    lines.push(`default_target_node_url: ${payload.default_target_node_url}`);
  }
  return lines.join("\n");
}

export function formatDingTalkControlQueryReply(payload) {
  return [
    "当前钉钉上传控制配置：",
    summarizeDingTalkControl(payload || {}),
  ]
    .filter(Boolean)
    .join("\n");
}

export function formatDingTalkControlUpdateReply(payload) {
  return [
    "已更新钉钉上传控制配置：",
    summarizeDingTalkControl(payload || {}),
  ]
    .filter(Boolean)
    .join("\n");
}
