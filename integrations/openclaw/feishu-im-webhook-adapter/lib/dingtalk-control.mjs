const DINGTALK_NODE_URL_RE = /https:\/\/alidocs\.dingtalk\.com\/i\/nodes\/[A-Za-z0-9]+[^\s<>"']*/i;
const RECORD_ID_RE = /\brec[a-zA-Z0-9]+\b/;
const LABELED_OPERATOR_RE = /\b(?:operator[_-]?union[_-]?id|union[_-]?id|unionid)\s*[:=]\s*([A-Za-z0-9._-]+)/i;

function normalizeText(text) {
  return String(text || "").trim();
}

function normalizeLower(text) {
  return normalizeText(text).toLowerCase();
}

function extractRecordId(text) {
  const match = normalizeText(text).match(RECORD_ID_RE);
  return match ? match[0] : "";
}

export function extractDingTalkNodeUrl(text) {
  const match = normalizeText(text).match(DINGTALK_NODE_URL_RE);
  return match ? match[0] : "";
}

function extractOperatorUnionId(text, { targetNodeUrl = "" } = {}) {
  const normalized = normalizeText(text);
  const labeled = normalized.match(LABELED_OPERATOR_RE);
  if (labeled) {
    return labeled[1];
  }

  let residual = normalized;
  if (targetNodeUrl) {
    residual = residual.replace(targetNodeUrl, " ");
  }
  residual = residual.replace(RECORD_ID_RE, " ");
  residual = residual.replace(/\/?dingtalk-bind\b/gi, " ");
  residual = residual.replace(/(?:查看|查询)?钉钉(?:上传)?配置/g, " ");
  residual = residual.replace(/(?:绑定|设置|更新|写入)(?:默认)?钉钉(?:上传)?(?:配置|目录|节点)?/g, " ");
  residual = residual.replace(/(?:operator[_-]?union[_-]?id|union[_-]?id|unionid)\b/gi, " ");

  const tokens = residual
    .split(/\s+/)
    .map((token) => token.trim())
    .filter(Boolean);
  if (tokens.length === 1) {
    return tokens[0];
  }
  return "";
}

export function isDingTalkControlQueryText(text) {
  const normalized = normalizeText(text);
  const lowered = normalizeLower(text);
  if (!normalized) {
    return false;
  }
  if (lowered === "dingtalk-config" || lowered === "/dingtalk-config" || lowered.startsWith("dingtalk-config ")) {
    return true;
  }
  return normalized === "钉钉配置"
    || normalized === "查看钉钉配置"
    || normalized === "查询钉钉配置"
    || normalized.startsWith("查看钉钉配置 ")
    || normalized.startsWith("查询钉钉配置 ");
}

function isDingTalkControlUpdateText(text) {
  const normalized = normalizeText(text);
  const lowered = normalizeLower(text);
  if (!normalized) {
    return false;
  }
  if (lowered.startsWith("dingtalk-bind ") || lowered === "dingtalk-bind" || lowered.startsWith("/dingtalk-bind ")) {
    return true;
  }
  return /(?:绑定|设置|更新|写入)(?:默认)?钉钉(?:上传)?(?:配置|目录|节点)?/.test(normalized);
}

function updateUsage() {
  return [
    "钉钉绑定命令格式：",
    "`dingtalk-bind <operator_union_id> <https://alidocs.dingtalk.com/i/nodes/...>`",
    "或：`绑定钉钉 <operator_union_id> <https://alidocs.dingtalk.com/i/nodes/...>`",
    "也支持：`绑定钉钉 operator_union_id=<id> <url>`",
  ].join("\n");
}

export function parseDingTalkControlCommand(text) {
  if (isDingTalkControlQueryText(text)) {
    return {
      action: "query",
      recordId: extractRecordId(text),
      error: "",
    };
  }
  if (!isDingTalkControlUpdateText(text)) {
    return null;
  }

  const targetNodeUrl = extractDingTalkNodeUrl(text);
  const operatorUnionId = extractOperatorUnionId(text, { targetNodeUrl });
  if (!targetNodeUrl) {
    return {
      action: "update",
      recordId: extractRecordId(text),
      operatorUnionId,
      targetNodeUrl: "",
      error: "缺少钉钉知识库目录链接。\n" + updateUsage(),
    };
  }
  if (!operatorUnionId) {
    return {
      action: "update",
      recordId: extractRecordId(text),
      operatorUnionId: "",
      targetNodeUrl,
      error: "缺少 operator_union_id。\n" + updateUsage(),
    };
  }
  return {
    action: "update",
    recordId: extractRecordId(text),
    operatorUnionId,
    targetNodeUrl,
    error: "",
  };
}
