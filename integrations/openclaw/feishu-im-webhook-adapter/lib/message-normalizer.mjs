import { applyLocalAliases } from "./local-profile.mjs";

const RECORD_ID_RE = /\brec[A-Za-z0-9_]+\b/;
const DOCUMENT_ID_RE = /\b[A-Za-z]{1,8}-\d{3,5}[A-Za-z]?(?:_[A-Za-z]{2,3}){1,2}(?:_\d+(?:\.\d+)*)?\b/;
const TASK_ID_RE = /\b[A-Za-z]{1,8}-\d{3,5}[A-Za-z]?(?:_[A-Za-z]{2,3}){1,2}_\d+(?:\.\d+)*(?:[\s_:-]+)(?:Start[\s_-]+Review|Build[\s_-]+Draft[\s_-]+Package|Publish)\b/i;
const MODEL_REGION_RE = /\b[A-Za-z]{1,8}-\d{3,5}[A-Za-z]?\s+(?:US|JP|CN|EU)\b/i;
const PREVIOUS_TARGET_RE = /(刚才|刚刚|上一个|上一条|前面|这个|那个|它|同一个|same|previous|last|that|this)/i;

function compactText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function hasExplicitTarget(messageText) {
  const text = compactText(messageText);
  return RECORD_ID_RE.test(text) || TASK_ID_RE.test(text) || DOCUMENT_ID_RE.test(text) || MODEL_REGION_RE.test(text);
}

function referencesPreviousTarget(messageText) {
  return PREVIOUS_TARGET_RE.test(compactText(messageText));
}

function contextRecordId(conversationContext) {
  return String(conversationContext?.row?.record_id || conversationContext?.record_id || "").trim();
}

export function normalizeIncomingMessage({ messageText, localProfile = null, conversationContext = null } = {}) {
  const rawText = compactText(messageText);
  const aliasExpandedText = applyLocalAliases(rawText, localProfile);
  const recordId = contextRecordId(conversationContext);
  const shouldUseContext = Boolean(recordId && !hasExplicitTarget(aliasExpandedText) && referencesPreviousTarget(aliasExpandedText));
  const normalizedText = shouldUseContext ? `${aliasExpandedText} record_id ${recordId}` : aliasExpandedText;

  return {
    rawText,
    normalizedText,
    aliasExpandedText,
    usedLocalAliases: rawText !== aliasExpandedText,
    usedConversationContext: shouldUseContext,
    contextRecordId: shouldUseContext ? recordId : "",
  };
}
