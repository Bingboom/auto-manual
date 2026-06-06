#!/usr/bin/env node
// Ensure the BlockClaw persona wiring survives OpenClaw restarts / updates / reseeds.
//
// Background (see memory blockclaw-persona-loads-from-root):
// OpenClaw injects persona files (IDENTITY/SOUL/USER/BOOTSTRAP) by basename from
// the workspace ROOT and auto-reseeds blank default templates whenever a root file
// is missing. PR #286 moved the real persona into agent/, so OpenClaw reseeded blank
// templates at root and BlockClaw lost its identity (and started pasting bare URLs as
// plain text instead of card-renderable Markdown links).
//
// The fix has two runtime pieces this guard re-asserts, idempotently:
//   1. ~/.openclaw/openclaw.json hook `bootstrap-extra-files` -> agent/<persona>.md
//   2. Root stub files for IDENTITY/SOUL/USER so OpenClaw never reseeds blanks there
//      (and they don't conflict with the real agent/ persona injected by the hook).
//
// Safe by design: only writes when something is actually wrong; config write is
// atomic with a backup; never throws (so it can run on the gateway startup path).
//
// Usage:
//   node integrations/openclaw/scripts/ensure_blockclaw_persona_wiring.mjs   (manual recovery)
//   import { ensureBlockClawPersonaWiring } from "./ensure_blockclaw_persona_wiring.mjs"
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const CONFIG_PATH =
  process.env.OPENCLAW_CONFIG_PATH || path.join(os.homedir(), ".openclaw", "openclaw.json");
const HOOK_KEY = "bootstrap-extra-files";
// Persona files injected from agent/ via the hook. BOOTSTRAP carries the chat reply rules.
const PERSONA_BASENAMES = ["IDENTITY.md", "SOUL.md", "USER.md", "BOOTSTRAP.md"];
// Root files OpenClaw would otherwise reseed as blank templates; we keep them as stubs.
const ROOT_STUB_BASENAMES = ["IDENTITY.md", "SOUL.md", "USER.md"];
// Substrings unique to OpenClaw's blank default templates — if a root file contains any,
// it has been reseeded and must be overwritten with our stub.
const BLANK_TEMPLATE_SIGNATURES = [
  "Fill this in during your first conversation",
  "pick something you like",
  "You're not a chatbot",
  "Remember you're a guest",
  "About Your Human",
  "Learn about the person you're helping",
];

function resolveWorkspace(cfg) {
  const ws = cfg?.agents?.defaults?.workspace;
  if (typeof ws === "string" && ws.trim()) return ws.trim();
  // Fallback: this file lives at <workspace>/integrations/openclaw/scripts/.
  return path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
}

function stubContent(basename) {
  return (
    "<!--\n" +
    `BlockClaw 人设由 ~/.openclaw/openclaw.json 的 ${HOOK_KEY} hook 从 agent/ 加载。真正内容见 agent/${basename}。\n` +
    "此根目录文件仅为占位，防止 OpenClaw 重新播种空白默认模板；请勿在此填写人设。\n" +
    "维护脚本：integrations/openclaw/scripts/ensure_blockclaw_persona_wiring.mjs\n" +
    "-->\n"
  );
}

function ensureRootStubs(workspace, log) {
  for (const name of ROOT_STUB_BASENAMES) {
    const filePath = path.join(workspace, name);
    let needsWrite = false;
    if (!fs.existsSync(filePath)) {
      needsWrite = true;
    } else {
      const content = fs.readFileSync(filePath, "utf8");
      if (BLANK_TEMPLATE_SIGNATURES.some((sig) => content.includes(sig))) needsWrite = true;
    }
    if (needsWrite) {
      fs.writeFileSync(filePath, stubContent(name), "utf8");
      log.push(`rewrote root stub ${name}`);
    }
  }
}

function ensureHookConfig(cfg) {
  cfg.hooks = cfg.hooks || {};
  cfg.hooks.internal = cfg.hooks.internal || {};
  if (cfg.hooks.internal.enabled === undefined) cfg.hooks.internal.enabled = true;
  cfg.hooks.internal.entries = cfg.hooks.internal.entries || {};
  const wantPaths = PERSONA_BASENAMES.map((n) => `agent/${n}`);
  const cur = cfg.hooks.internal.entries[HOOK_KEY];
  const ok =
    cur &&
    cur.enabled !== false &&
    Array.isArray(cur.paths) &&
    wantPaths.every((p) => cur.paths.includes(p));
  if (ok) return false;
  cfg.hooks.internal.entries[HOOK_KEY] = { enabled: true, paths: wantPaths };
  return true;
}

function writeConfigAtomic(cfg, log) {
  const out = JSON.stringify(cfg, null, 2) + "\n";
  JSON.parse(out); // re-validate before writing
  try {
    fs.copyFileSync(CONFIG_PATH, `${CONFIG_PATH}.bak.persona-guard`);
  } catch {
    // best-effort backup
  }
  const tmp = `${CONFIG_PATH}.tmp.persona-guard`;
  fs.writeFileSync(tmp, out, "utf8");
  fs.renameSync(tmp, CONFIG_PATH);
  log.push(`re-applied ${HOOK_KEY} hook config`);
}

export function ensureBlockClawPersonaWiring() {
  const log = [];
  try {
    const cfg = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
    const workspace = resolveWorkspace(cfg);
    ensureRootStubs(workspace, log);
    if (ensureHookConfig(cfg)) writeConfigAtomic(cfg, log);
    if (log.length) console.error(`[blockclaw-persona-guard] repaired: ${log.join("; ")}`);
  } catch (err) {
    console.error(`[blockclaw-persona-guard] skipped: ${String(err)}`);
  }
  return log;
}

// Run when invoked directly (manual recovery), not when imported.
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  ensureBlockClawPersonaWiring();
}
