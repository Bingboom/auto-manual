import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const RECENT_MESSAGE_IDS = new Map<string, number>();
const RECENT_TTL_MS = 10 * 60 * 1000;
const FEISHU_GET_EMOJI = "Get";

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

const handler = async (event: any) => {
  if (event?.type !== "message" || event?.action !== "received") return;

  const ctx = event?.context ?? {};
  const messageId = typeof ctx.messageId === "string" ? ctx.messageId.trim() : "";
  const target = normalizeFeishuDmTarget(ctx);
  const accountId = typeof ctx.accountId === "string" ? ctx.accountId.trim() : "";

  if (!isFeishuInbound(ctx)) return;
  if (!messageId || !target) return;

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
