#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
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

// Two supported OpenClaw layouts:
// - "legacy": Feishu channel bundled into the install root's dist/ (pre-2026.6
//   Homebrew installs); the im.message.receive_v1 handler is an inline async fn
//   inside registerEventHandlers.
// - "plugin": Feishu is the community plugin @openclaw/feishu installed under
//   ~/.openclaw/npm/projects/openclaw-feishu-*/; the handler is built by the
//   createFeishuMessageReceiveHandler factory.
const legacyDefaultRoot = "/opt/homebrew/opt/manual-node-v24.14.1/lib/node_modules/openclaw";
const installRoot = process.env.OPENCLAW_INSTALL_ROOT || legacyDefaultRoot;
const stateDir = process.env.OPENCLAW_STATE_DIR || path.join(os.homedir(), ".openclaw");
const marker = "openclaw-local-feishu-auto-get";
const reactionEmoji = process.env.OPENCLAW_FEISHU_RECEIVED_REACTION || "Get";

function listCandidateDistDirs() {
  const dirs = [];
  const seen = new Set();
  const push = (dist, origin) => {
    const resolved = path.resolve(dist);
    if (seen.has(resolved) || !fs.existsSync(resolved)) return;
    seen.add(resolved);
    dirs.push({ dist: resolved, origin });
  };

  push(path.join(installRoot, "dist"), "install root");

  const pluginOverride = process.env.OPENCLAW_FEISHU_PLUGIN_DIR;
  if (pluginOverride) {
    const nested = path.join(pluginOverride, "dist");
    push(fs.existsSync(nested) ? nested : pluginOverride, "OPENCLAW_FEISHU_PLUGIN_DIR");
  }

  const projectsDir = path.join(stateDir, "npm", "projects");
  if (fs.existsSync(projectsDir)) {
    for (const name of fs.readdirSync(projectsDir).sort()) {
      if (!name.startsWith("openclaw-feishu-")) continue;
      push(
        path.join(projectsDir, name, "node_modules", "@openclaw", "feishu", "dist"),
        `plugin project ${name}`,
      );
    }
  }

  return dirs;
}

function detectLayout(source) {
  if (!source.includes("createFeishuClient") || !source.includes("resolveFeishuRuntimeAccount")) {
    return null;
  }
  if (
    source.includes("function registerEventHandlers(eventDispatcher, context)") &&
    source.includes('"im.message.receive_v1": async (data) => {')
  ) {
    return "legacy";
  }
  if (
    source.includes("function createFeishuMessageReceiveHandler(") &&
    source.includes('"im.message.receive_v1": createFeishuMessageReceiveHandler({')
  ) {
    return "plugin";
  }
  return null;
}

function findFeishuMonitors() {
  const candidates = listCandidateDistDirs();
  const monitors = [];

  for (const { dist, origin } of candidates) {
    const files = fs
      .readdirSync(dist)
      .filter((name) => name.endsWith(".js"))
      .map((name) => path.join(dist, name));

    for (const file of files) {
      const source = fs.readFileSync(file, "utf8");
      const layout = detectLayout(source);
      if (layout) {
        monitors.push({ file, source, layout, origin });
      }
    }
  }

  if (monitors.length === 0) {
    const scanned = candidates.length
      ? candidates.map((c) => `${c.dist} (${c.origin})`).join(", ")
      : "<no candidate dist directories exist>";
    throw new Error(`Unable to locate Feishu monitor; scanned: ${scanned}`);
  }

  return monitors;
}

// Anchor just above the inboundDebouncer declaration. In both layouts that sits
// at one-tab depth in a scope where cfg, accountId, log, and error are defined.
const functionAnchors = {
  legacy: "\tconst inboundDebouncer = core.channel.debounce.createInboundDebouncer({",
  plugin: "\tconst inboundDebouncer = channelRuntime.debounce.createInboundDebouncer({",
};

function insertReactionFunction(source, layout) {
  if (source.includes("const addReceivedGetReaction = async (event) =>")) {
    return source;
  }

  const needle = functionAnchors[layout];
  const index = source.indexOf(needle);
  if (index === -1) {
    throw new Error(`Unable to find Feishu inboundDebouncer insertion point (${layout} layout)`);
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

// The dispatch site sits at three-tab depth in the legacy inline handler and at
// two-tab depth in the plugin factory's returned handler.
const callAnchors = {
  legacy: {
    scopeStart: '"im.message.receive_v1": async (data) => {',
    needle:
      "\t\t\tconst processMessage = async () => {\n\t\t\t\tawait inboundDebouncer.enqueue(event);\n\t\t\t};",
    call: "\t\t\tvoid addReceivedGetReaction(event);\n",
  },
  plugin: {
    scopeStart: "function createFeishuMessageReceiveHandler(",
    needle:
      "\t\tconst processMessage = async () => {\n\t\t\tawait inboundDebouncer.enqueue(event);\n\t\t};",
    call: "\t\tvoid addReceivedGetReaction(event);\n",
  },
};

function insertReactionCall(source, layout) {
  if (source.includes("void addReceivedGetReaction(event);")) {
    return source;
  }

  const { scopeStart, needle, call } = callAnchors[layout];
  const handlerStart = source.indexOf(scopeStart);
  if (handlerStart === -1) {
    throw new Error(`Unable to find im.message.receive_v1 handler (${layout} layout)`);
  }

  const index = source.indexOf(needle, handlerStart);
  if (index === -1) {
    throw new Error(`Unable to find Feishu processMessage insertion point (${layout} layout)`);
  }

  return source.slice(0, index) + call + source.slice(index);
}

for (const { file, source, layout, origin } of findFeishuMonitors()) {
  const next = insertReactionCall(insertReactionFunction(source, layout), layout);

  if (next === source) {
    console.log(`[feishu-received-reaction] already patched (${layout}, ${origin}): ${file}`);
    continue;
  }

  const backupFile = `${file}.before-feishu-received-reaction`;
  if (!fs.existsSync(backupFile)) {
    fs.writeFileSync(backupFile, source, "utf8");
  }
  fs.writeFileSync(file, next, "utf8");
  console.log(`[feishu-received-reaction] patched (${layout}, ${origin}): ${file}`);
}
