const URL_RE = /https?:\/\/[^\s<>"'，。；、)）\]]+/gi;
const REVIEW_SOURCE_RE = /\bdocs\/_review\/[^\s<>"'，。；、)）\]]+?\.rst\b/i;
const RUN_MANIFEST_RE = /\breports\/cloud_doc_backport\/[^\s<>"'，。；、)）\]]+?\/cloud_doc_backport_run\.json\b/i;
const RUN_ID_RE = /(?:--run-id|run_id|run-id)\s*[=:]?\s*([A-Za-z0-9._-]+)/i;
const BRANCH_RE = /(?:--branch|branch)\s*[=:]?\s*([A-Za-z0-9._/-]+)/i;
const INTENT_RE = /(cloud[-_\s]?doc|backport|run-review|云文档|修订|修订稿|合入修改|改回|导回|回填|闭环合入)/i;
const PR_INTENT_RE = /(backport[-_\s]?pr|cloud[-_\s]?doc[-_\s]?pr|open\s+pr|create\s+pr|开\s*pr|开\s*PR|建\s*pr|建\s*PR|拉\s*PR)/i;
const WRITE_INTENT_RE = /(--write|\bwrite\b|写入|应用|合入到|落到|改到)/i;
const FEISHU_DOC_HOST_RE = /(?:^|\.)((feishu|larksuite)\.cn|feishu\.com|larksuite\.com)$/i;
const MANUAL_DOC_ID_RE = /\bmanual[_-]([A-Za-z]{1,8}[-_]?\d{3,5}[A-Za-z]?)[_-]([A-Za-z]{2,3}(?:-[A-Za-z]{2})?)(?:[_-]([A-Za-z]{2,3}(?:-[A-Za-z]{2})?))?(?:[_-](\d+(?:\.\d+)*))?\b/i;
const DOCUMENT_ID_RE = /\b([A-Za-z]{1,8}-\d{3,5}[A-Za-z]?)_([A-Za-z]{2,3}(?:-[A-Za-z]{2})?)(?:_([A-Za-z]{2,3}(?:-[A-Za-z]{2})?))?(?:_(\d+(?:\.\d+)*))?\b/i;
const MODEL_REGION_RE = /\b([A-Za-z]{1,8}-\d{3,5}[A-Za-z]?)\s+([A-Za-z]{2,3}(?:-[A-Za-z]{2})?)\b/i;

function compactText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function safeRunId(value) {
  return String(value || "")
    .replace(/[^A-Za-z0-9._-]+/g, "-")
    .replace(/^[.-]+|[.-]+$/g, "")
    .slice(0, 120);
}

function safeBranchName(value) {
  return String(value || "")
    .replace(/[^A-Za-z0-9._/-]+/g, "-")
    .replace(/\/{2,}/g, "/")
    .replace(/^[./-]+|[./-]+$/g, "")
    .slice(0, 160);
}

function normalizeModel(value) {
  const text = String(value || "").trim();
  const explicit = text.match(/^([A-Za-z]{1,8})-(\d{3,5}[A-Za-z]?)$/);
  if (explicit) {
    return `${explicit[1].toUpperCase()}-${explicit[2].toUpperCase()}`;
  }
  const compact = text.replace(/[-_\s]+/g, "").match(/^([A-Za-z]{1,8})(\d{3,5}[A-Za-z]?)$/);
  return compact ? `${compact[1].toUpperCase()}-${compact[2].toUpperCase()}` : "";
}

function normalizeRegion(value) {
  const text = String(value || "").trim().replace(/_/g, "-");
  if (/^pt-?br$/i.test(text)) {
    return "pt-BR";
  }
  return text ? text.toUpperCase() : "";
}

function normalizeLang(value) {
  const text = String(value || "").trim().replace(/_/g, "-");
  if (/^pt-?br$/i.test(text)) {
    return "pt-BR";
  }
  return text ? text.toLowerCase() : "";
}

function targetHint(model, region, lang = "", version = "") {
  return {
    model: normalizeModel(model),
    region: normalizeRegion(region),
    lang: normalizeLang(lang),
    version: String(version || "").trim(),
  };
}

export function inferCloudDocBackportTarget(messageText) {
  const text = compactText(messageText);
  let match = text.match(MANUAL_DOC_ID_RE);
  if (match) {
    return targetHint(match[1], match[2], match[3] || "", match[4] || "");
  }
  match = text.match(DOCUMENT_ID_RE);
  if (match) {
    return targetHint(match[1], match[2], match[3] || "", match[4] || "");
  }
  match = text.match(MODEL_REGION_RE);
  if (match) {
    return targetHint(match[1], match[2]);
  }
  return targetHint("", "");
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

function extractRunManifestPath(text) {
  const match = compactText(text).match(RUN_MANIFEST_RE);
  return match ? match[0] : "";
}

function extractBranchName(text) {
  const match = compactText(text).match(BRANCH_RE);
  return safeBranchName(match ? match[1] : "");
}

export function parseCloudDocBackportRequest(messageText) {
  const text = compactText(messageText);
  const docUrl = extractFirstFeishuDocUrl(text);
  const sourcePath = extractReviewSourcePath(text);
  const target = inferCloudDocBackportTarget(text);
  const hasIntent = INTENT_RE.test(text);
  const hasTargetHint = Boolean(target.model && target.region);
  const hasCloudDocCommand = Boolean((docUrl && (hasIntent || sourcePath)) || (hasIntent && hasTargetHint));
  if (!hasCloudDocCommand) {
    return {
      matched: false,
      missing: [],
      docUrl: "",
      sourcePath: "",
      targetHint: targetHint("", ""),
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
    targetHint: target,
    messageText: text,
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

export function parseCloudDocBackportPrRequest(messageText) {
  const text = compactText(messageText);
  const hasIntent = PR_INTENT_RE.test(text);
  if (!hasIntent) {
    return {
      matched: false,
      missing: [],
      manifestPath: "",
      branchName: "",
    };
  }
  const manifestPath = extractRunManifestPath(text);
  const missing = [];
  if (!manifestPath) {
    missing.push("reports/cloud_doc_backport/.../cloud_doc_backport_run.json manifest");
  }
  return {
    matched: true,
    missing,
    manifestPath,
    branchName: extractBranchName(text),
  };
}
