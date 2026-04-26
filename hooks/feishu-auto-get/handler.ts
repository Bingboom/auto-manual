import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const RECENT_MESSAGE_IDS = new Map<string, number>();
const RECENT_TTL_MS = 10 * 60 * 1000;
const FEISHU_GET_EMOJI = "Get";
const EXECUTION_REQUEST_PATTERNS = [
  /\b(?:translate|translation|rewrite|polish|build|publish|release)\b/i,
  /\b(?:start\s+review|enter\s+review|confirm(?:\s+publish)?)\b/i,
  /翻译|改写|润色|构建|发布|开始\s*review|进入\s*review|发起\s*review|确认发布/,
  /生成.{0,12}(?:初稿|草稿|文档)/,
  /(?:发|给|把|拿|查|看).{0,12}(?:链接|结果|状态|初稿|草稿|pr|html)/i,
  /(?:链接|结果|状态|初稿|草稿|pr|html).{0,12}(?:发我|给我|发给我|给我看|拿给我|查一下|查下)/i
] as const;
const REACTION_META_PATTERNS = [
  /reaction|表情|点赞|点个赞|ack/i,
  /\bget\b/i,
  /了解/,
] as const;
const REACTION_GOVERNANCE_PATTERNS = [
  /只在|只有|才用|别用|不要用|怎么又|什么时候|啥时候|规则|偏好|留给/,
] as const;
const TEXT_KEYS = [
  "normalizedText",
  "rawText",
  "messageText",
  "text",
  "content",
  "message",
  "body",
] as const;

function cleanupRecent(now: number) {
  for (const [messageId, ts] of RECENT_MESSAGE_IDS) {
    if (now - ts > RECENT_TTL_MS) RECENT_MESSAGE_IDS.delete(messageId);
  }
}

function isFeishuInbound(ctx: any) {
  return ctx?.channelId === "feishu" || ctx?.metadata?.provider === "feishu" || ctx?.metadata?.surface === "feishu";
}

function normalizeFeishuDmTarget(ctx: any): string | null {
  const candidates = [
    typeof ctx?.from === "string" ? ctx.from.trim() : "",
    typeof ctx?.to === "string" ? ctx.to.trim() : "",
    typeof ctx?.senderId === "string" ? ctx.senderId.trim() : "",
    typeof ctx?.metadata?.senderId === "string" ? ctx.metadata.senderId.trim() : ""
  ].filter(Boolean);

  for (const raw of candidates) {
    if (raw.startsWith("user:")) return raw;
    if (raw.startsWith("feishu:")) {
      const openId = raw.slice("feishu:".length).trim();
      if (openId) return `user:${openId}`;
    }
    if (/^(ou_|on_)/.test(raw)) return `user:${raw}`;
  }

  return null;
}

function normalizeMessageText(raw: string): string {
  return raw.replace(/<at\b[^>]*>.*?<\/at>/gi, " ").replace(/\s+/g, " ").trim();
}

function decodeStructuredText(value: unknown): string {
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return "";
    if ((trimmed.startsWith("{") && trimmed.endsWith("}")) || (trimmed.startsWith("[") && trimmed.endsWith("]"))) {
      try {
        return decodeStructuredText(JSON.parse(trimmed));
      } catch {
        return normalizeMessageText(trimmed);
      }
    }
    return normalizeMessageText(trimmed);
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      const text = decodeStructuredText(item);
      if (text) return text;
    }
    return "";
  }
  if (!value || typeof value !== "object") return "";

  const record = value as Record<string, unknown>;
  for (const key of TEXT_KEYS) {
    if (!(key in record)) continue;
    const text = decodeStructuredText(record[key]);
    if (text) return text;
  }
  return "";
}

export function extractInboundMessageText(event: any): string {
  const ctx = event?.context ?? {};
  const candidates = [
    event,
    event?.payload,
    ctx,
    ctx?.payload,
    ctx?.metadata,
    ctx?.message,
    ctx?.content,
  ];

  for (const candidate of candidates) {
    const text = decodeStructuredText(candidate);
    if (text) return text;
  }
  return "";
}

export function shouldAutoGetReactionForText(rawText: string): boolean {
  const text = normalizeMessageText(rawText);
  if (!text) return false;

  const hasReactionMeta = REACTION_META_PATTERNS.some((pattern) => pattern.test(text));
  const isGovernanceMessage = REACTION_GOVERNANCE_PATTERNS.some((pattern) => pattern.test(text));
  if (hasReactionMeta || isGovernanceMessage) return false;

  return EXECUTION_REQUEST_PATTERNS.some((pattern) => pattern.test(text));
}

const handler = async (event: any) => {
  if (event?.type !== "message" || event?.action !== "received") return;

  const ctx = event?.context ?? {};
  const messageId = typeof ctx.messageId === "string" ? ctx.messageId.trim() : "";
  const target = normalizeFeishuDmTarget(ctx);
  const accountId = typeof ctx.accountId === "string" ? ctx.accountId.trim() : "";
  const messageText = extractInboundMessageText(event);

  if (!isFeishuInbound(ctx)) return;
  if (!messageId || !target) return;
  if (!shouldAutoGetReactionForText(messageText)) return;

  const now = Date.now();
  cleanupRecent(now);
  if (RECENT_MESSAGE_IDS.has(messageId)) return;
  RECENT_MESSAGE_IDS.set(messageId, now);

  const args = [
    "message",
    "react",
    "--channel",
    "feishu",
    ...(accountId ? ["--account", accountId] : []),
    "--target",
    target,
    "--message-id",
    messageId,
    "--emoji",
    FEISHU_GET_EMOJI,
    "--json"
  ];

  try {
    await execFileAsync("openclaw", args, {
      timeout: 15000,
      env: process.env
    });
    console.log("[feishu-auto-get] added Get reaction", {
      messageId,
      target,
      accountId: accountId || undefined
    });
  } catch (error) {
    console.error("[feishu-auto-get] failed to add Get reaction", {
      messageId,
      target,
      accountId: accountId || undefined,
      error: error instanceof Error ? error.message : String(error)
    });
  }
};

export default handler;
