#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import process from "node:process";

// Re-assert the BlockClaw persona wiring (bootstrap-extra-files hook -> agent/ + root
// stubs) on every gateway start, so an OpenClaw update/reseed or a config reset cannot
// silently regress it. Isolated in its own try/catch so it can never affect (or be
// affected by) the Feishu reaction patch below. See ensure_blockclaw_persona_wiring.mjs.
try {
  const personaGuard = await import("./ensure_blockclaw_persona_wiring.mjs");
  personaGuard.ensureBlockClawPersonaWiring();
} catch (err) {
  console.error(`[feishu-startup] persona guard skipped: ${String(err)}`);
}

const defaultRoot = "/opt/homebrew/opt/manual-node-v24.14.1/lib/node_modules/openclaw";
const root = process.env.OPENCLAW_INSTALL_ROOT || defaultRoot;
const distDir = path.join(root, "dist");
const marker = "openclaw-local-feishu-auto-get";
const reactionEmoji = process.env.OPENCLAW_FEISHU_RECEIVED_REACTION || "Get";

function findFeishuMonitor() {
  const candidates = fs
    .readdirSync(distDir)
    .filter((name) => name.endsWith(".js"))
    .map((name) => path.join(distDir, name));

  for (const file of candidates) {
    const source = fs.readFileSync(file, "utf8");
    if (
      source.includes("function registerEventHandlers(eventDispatcher, context)") &&
      source.includes('"im.message.receive_v1": async (data) => {') &&
      source.includes("createFeishuClient") &&
      source.includes("resolveFeishuRuntimeAccount")
    ) {
      return { file, source };
    }
  }

  throw new Error(`Unable to locate Feishu monitor in ${distDir}`);
}

function insertReactionFunction(source) {
  if (source.includes("const addReceivedGetReaction = async (event) =>")) {
    return source;
  }

  const needle = "\tconst inboundDebouncer = core.channel.debounce.createInboundDebouncer({";
  const index = source.indexOf(needle);
  if (index === -1) {
    throw new Error("Unable to find Feishu inboundDebouncer insertion point");
  }

  const emojiLiteral = JSON.stringify(reactionEmoji);
  const block = `\tconst addReceivedGetReaction = async (event) => {
\t\t// ${marker}: acknowledge every received Feishu IM before agent dispatch.
\t\tconst messageId = event.message?.message_id?.trim();
\t\tif (!messageId) return;
\t\ttry {
\t\t\tconst account = resolveFeishuRuntimeAccount({
\t\t\t\tcfg,
\t\t\t\taccountId
\t\t\t});
\t\t\tif (!account.configured) return;
\t\t\tawait createFeishuClient(account).im.messageReaction.create({
\t\t\t\tpath: { message_id: messageId },
\t\t\t\tdata: { reaction_type: { emoji_type: ${emojiLiteral} } }
\t\t\t});
\t\t\tlog(\`feishu[\${accountId}]: added received reaction ${reactionEmoji} for message \${messageId}\`);
\t\t} catch (err) {
\t\t\terror(\`feishu[\${accountId}]: failed to add received reaction ${reactionEmoji}: \${String(err)}\`);
\t\t}
\t};
`;

  return source.slice(0, index) + block + source.slice(index);
}

function insertReactionCall(source) {
  if (source.includes("void addReceivedGetReaction(event);")) {
    return source;
  }

  const handlerStart = source.indexOf('"im.message.receive_v1": async (data) => {');
  if (handlerStart === -1) {
    throw new Error("Unable to find im.message.receive_v1 handler");
  }

  const needle = "\t\t\tconst processMessage = async () => {\n\t\t\t\tawait inboundDebouncer.enqueue(event);\n\t\t\t};";
  const index = source.indexOf(needle, handlerStart);
  if (index === -1) {
    throw new Error("Unable to find Feishu processMessage insertion point");
  }

  return source.slice(0, index) + "\t\t\tvoid addReceivedGetReaction(event);\n" + source.slice(index);
}

const { file, source } = findFeishuMonitor();
const next = insertReactionCall(insertReactionFunction(source));

if (next === source) {
  console.log(`[feishu-received-reaction] already patched: ${file}`);
  process.exit(0);
}

const backupFile = `${file}.before-feishu-received-reaction`;
if (!fs.existsSync(backupFile)) {
  fs.writeFileSync(backupFile, source, "utf8");
}
fs.writeFileSync(file, next, "utf8");
console.log(`[feishu-received-reaction] patched: ${file}`);
