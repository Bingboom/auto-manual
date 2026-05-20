import { applyLocalAliases } from "./local-profile.mjs";

const REGION_TOKEN_SOURCE = "(?:US|JP|CN|EU|BR|Brazil|pt-BR)";
const RECORD_ID_RE = /\brec[A-Za-z0-9_]+\b/;
const DOCUMENT_ID_RE = new RegExp(
  `\\b[A-Za-z]{1,8}-\\d{3,5}[A-Za-z]?_${REGION_TOKEN_SOURCE}(?:_[A-Za-z]{2})?(?:_\\d+(?:\\.\\d+)*)?\\b`,
  "i"
);
const TASK_ID_RE = new RegExp(
  `\\b[A-Za-z]{1,8}-\\d{3,5}[A-Za-z]?_${REGION_TOKEN_SOURCE}(?:_[A-Za-z]{2})?_\\d+(?:\\.\\d+)*(?:[\\s_:-]+)(?:Start[\\s_-]+Review|Build[\\s_-]+Draft[\\s_-]+Package|Publish)\\b`,
  "i"
);
const MODEL_TOKEN_RE = /\b[A-Za-z]{1,8}-\d{3,5}[A-Za-z]?\b/;
const MODEL_REGION_RE = new RegExp(`\\b[A-Za-z]{1,8}-\\d{3,5}[A-Za-z]?\\s+${REGION_TOKEN_SOURCE}\\b`, "i");
const MARKET_ALIAS_RE = /(欧规|欧洲|欧盟|美规|美国|日规|日本|中规|中国)/;
const EXECUTION_INTENT_RE = /(构建|生成|输出|发起|触发|补触发|重跑|重新跑|重新构建|开始|build|run|trigger|start)/i;
const RETRY_INTENT_RE = /(补跑|补构建|补触发|重试|retry|rerun)/i;
const STATUS_INTENT_RE = /(状态|进度|好了|好了没|好了吗|跑完|完成|完成了吗|结果|链接|失败|为什么|怎么回事|到哪|查不到|找不到|status|progress|done|finished|result|failure|failed|where)/i;
const PREVIOUS_TARGET_RE = /(刚才|刚刚|上一个|上一条|前面|这个|那个|它|同一个|same|previous|last|that|this)/i;
const DOCUMENT_ID_PARTS_RE = new RegExp(
  `^([A-Za-z]{1,8}-\\d{3,5}[A-Za-z]?)_(${REGION_TOKEN_SOURCE})(?:_([A-Za-z]{2}))?(?:_(\\d+(?:\\.\\d+)*))?$`,
  "i"
);

function compactText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function selectorRegionToken(region) {
  const text = String(region || "").trim();
  if (/^(br|brazil|pt-br)$/i.test(text)) {
    return "pt-BR";
  }
  return text.toUpperCase();
}

function hasExplicitTarget(messageText) {
  const text = compactText(messageText);
  const hasModelMarketAliasTarget = MODEL_TOKEN_RE.test(text) && MARKET_ALIAS_RE.test(text);
  return (
    RECORD_ID_RE.test(text) ||
    TASK_ID_RE.test(text) ||
    DOCUMENT_ID_RE.test(text) ||
    MODEL_REGION_RE.test(text) ||
    hasModelMarketAliasTarget
  );
}

function referencesPreviousTarget(messageText) {
  return PREVIOUS_TARGET_RE.test(compactText(messageText));
}

function isExecutionIntent(messageText) {
  return EXECUTION_INTENT_RE.test(compactText(messageText)) || RETRY_INTENT_RE.test(compactText(messageText));
}

function isStatusIntent(messageText) {
  return STATUS_INTENT_RE.test(compactText(messageText));
}

function contextRecordId(conversationContext) {
  return String(conversationContext?.row?.record_id || conversationContext?.record_id || "").trim();
}

function contextRows(conversationContext) {
  const rows = Array.isArray(conversationContext?.rows) ? conversationContext.rows : [];
  if (rows.length) {
    return rows;
  }
  return conversationContext?.row ? [conversationContext.row] : [];
}

function safeSelectorFromContext(conversationContext) {
  const rows = contextRows(conversationContext);
  const first = rows.find((row) => row && typeof row === "object") || null;
  if (!first) {
    return "";
  }
  const documentId = String(first.document_id || "").trim();
  const documentKey = String(first.document_key || "").trim();
  const match = documentId.match(DOCUMENT_ID_PARTS_RE);
  if (match) {
    const [, model, region, _lang, version] = match;
    return [model, selectorRegionToken(region), version || ""].filter(Boolean).join(" ");
  }
  if (new RegExp(`^[A-Za-z]{1,8}-\\d{3,5}[A-Za-z]?_${REGION_TOKEN_SOURCE}$`, "i").test(documentKey)) {
    const [model, region] = documentKey.split("_");
    return [model, selectorRegionToken(region)].join(" ");
  }
  const taskId = String(first.task_id || "").trim();
  const taskMatch = taskId.match(DOCUMENT_ID_PARTS_RE);
  if (taskMatch) {
    const [, model, region, _lang, version] = taskMatch;
    return [model, selectorRegionToken(region), version || ""].filter(Boolean).join(" ");
  }
  return "";
}

export function normalizeIncomingMessage({ messageText, localProfile = null, conversationContext = null } = {}) {
  const rawText = compactText(messageText);
  const aliasExpandedText = applyLocalAliases(rawText, localProfile);
  const recordId = contextRecordId(conversationContext);
  const batchRows = contextRows(conversationContext);
  const hasPreviousReference = referencesPreviousTarget(aliasExpandedText);
  const hasTarget = hasExplicitTarget(aliasExpandedText);
  const executionIntent = isExecutionIntent(aliasExpandedText);
  const statusIntent = isStatusIntent(aliasExpandedText);
  const shouldUseRecordContext = Boolean(
    recordId &&
      !executionIntent &&
      !hasTarget &&
      hasPreviousReference &&
      batchRows.length <= 1
  );
  const shouldUseSafeSelector = Boolean(
    executionIntent &&
      !hasTarget &&
      (hasPreviousReference || RETRY_INTENT_RE.test(aliasExpandedText)) &&
      safeSelectorFromContext(conversationContext)
  );
  const shouldUseBatchContext = Boolean(
    statusIntent &&
      !executionIntent &&
      !hasTarget &&
      hasPreviousReference &&
      batchRows.length > 1
  );
  const normalizedText = shouldUseRecordContext
    ? `${aliasExpandedText} record_id ${recordId}`
    : shouldUseSafeSelector
      ? `${aliasExpandedText} ${safeSelectorFromContext(conversationContext)}`
      : aliasExpandedText;

  return {
    rawText,
    normalizedText,
    aliasExpandedText,
    usedLocalAliases: rawText !== aliasExpandedText,
    usedConversationContext: shouldUseRecordContext || shouldUseSafeSelector || shouldUseBatchContext,
    usedSafeSelectorContext: shouldUseSafeSelector,
    usedBatchContext: shouldUseBatchContext,
    contextRecordId: shouldUseRecordContext ? recordId : "",
    contextRows: shouldUseBatchContext ? batchRows : [],
  };
}
