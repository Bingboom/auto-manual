const URL_RE = /https?:\/\/[^\s<>"'，。；、)）\]]+/gi;
const REVIEW_SOURCE_RE = /\bdocs\/_review\/[^\s<>"'，。；、)）\]]+?\.rst\b/i;
const RUN_ID_RE = /(?:--run-id|run_id|run-id)\s*[=:]?\s*([A-Za-z0-9._-]+)/i;
const INTENT_RE = /(cloud[-_\s]?doc|backport|run-review|云文档|修订|修订稿|合入修改|改回|导回|回填|闭环合入)/i;
const WRITE_INTENT_RE = /(--write|\bwrite\b|写入|应用|合入到|落到|改到)/i;
const FEISHU_DOC_HOST_RE = /(?:^|\.)((feishu|larksuite)\.cn|feishu\.com|larksuite\.com)$/i;

function compactText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function safeRunId(value) {
  return String(value || "")
    .replace(/[^A-Za-z0-9._-]+/g, "-")
    .replace(/^[.-]+|[.-]+$/g, "")
    .slice(0, 120);
}

function looksLikeFeishuDocUrl(value) {
  try {
    const url = new URL(value);
    if (!FEISHU_DOC_HOST_RE.test(url.hostname)) {
      return false;
    }
    return /\/(?:wiki|docx|docs)\//i.test(url.pathname);
  } catch {
    return false;
  }
}

function extractFirstFeishuDocUrl(text) {
  const urls = compactText(text).match(URL_RE) || [];
  return urls.find((url) => looksLikeFeishuDocUrl(url)) || "";
}

function extractReviewSourcePath(text) {
  const match = compactText(text).match(REVIEW_SOURCE_RE);
  return match ? match[0] : "";
}

function extractRunId(text) {
  const match = compactText(text).match(RUN_ID_RE);
  return safeRunId(match ? match[1] : "");
}

export function parseCloudDocBackportRequest(messageText) {
  const text = compactText(messageText);
  const docUrl = extractFirstFeishuDocUrl(text);
  const sourcePath = extractReviewSourcePath(text);
  const hasIntent = INTENT_RE.test(text);
  const hasCloudDocCommand = Boolean(docUrl && (hasIntent || sourcePath));
  if (!hasCloudDocCommand) {
    return {
      matched: false,
      missing: [],
      docUrl: "",
      sourcePath: "",
      runId: "",
      write: false,
    };
  }

  const missing = [];
  if (!docUrl) {
    missing.push("Feishu cloud-doc URL");
  }
  if (!sourcePath) {
    missing.push("docs/_review/... .rst source path");
  }
  return {
    matched: true,
    missing,
    docUrl,
    sourcePath,
    runId: extractRunId(text),
    write: WRITE_INTENT_RE.test(text),
  };
}

export function cloudDocBackportSenderAllowed(senderId, config = {}) {
  const sender = compactText(senderId);
  const allowed = Array.isArray(config.cloudDocBackportAllowedSenderIds)
    ? config.cloudDocBackportAllowedSenderIds.map(compactText).filter(Boolean)
    : [];
  if (!allowed.length || !sender) {
    return false;
  }
  return allowed.includes("*") || allowed.includes(sender);
}
