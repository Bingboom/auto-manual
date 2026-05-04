import fs from "node:fs";
import path from "node:path";

const ALIASES_FILE = "aliases.local.json";
const REACTIONS_FILE = "reactions.local.json";
const REPLY_PHRASES_FILE = "reply-phrases.local.json";
const PERSONA_FILE = "persona.local.md";

const REPLY_PHRASE_KEYS = new Set([
  "acceptedPrefix",
  "completionPrefix",
  "executionErrorPrefix",
  "noPendingPublish",
  "pendingPublishInstruction",
  "pendingPublishPrefix",
  "publishConfirmedPrefix",
  "publishCompletedButUnreadable",
  "resolutionCandidateHeader",
  "runCompletedButUnreadable",
]);

const REACTION_STAGE_KEYS = new Set([
  "received",
  "accepted",
  "completed",
  "needs_confirmation",
  "needs_input",
  "unresolved",
  "error",
]);

const EMOJI_TYPE_ALIASES = new Map([
  ["👍", "THUMBSUP"],
  ["👌", "OK"],
  ["✅", "OK"],
  ["🙂", "SMILE"],
  ["😄", "SMILE"],
  ["👀", "EYES"],
  ["❤️", "HEART"],
  ["❤", "HEART"],
  ["❓", "QUESTION"],
  ["?", "QUESTION"],
  ["GET", "Get"],
  ["Get", "Get"],
  ["get", "Get"],
]);

function readOptionalText(filePath) {
  try {
    return fs.readFileSync(filePath, "utf8");
  } catch (error) {
    if (error?.code === "ENOENT") {
      return "";
    }
    throw error;
  }
}

function readOptionalJson(filePath) {
  const text = readOptionalText(filePath);
  if (!text.trim()) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new Error(`Invalid local OpenClaw profile JSON at ${filePath}: ${error?.message || error}`);
  }
}

function compactString(value) {
  return String(value || "").trim();
}

function normalizeAliasEntry(entry) {
  if (!entry || typeof entry !== "object") {
    return [];
  }
  const fromValues = Array.isArray(entry.from) ? entry.from : [entry.from];
  const to = compactString(entry.to);
  if (!to) {
    return [];
  }
  return fromValues
    .map((from) => compactString(from))
    .filter(Boolean)
    .map((from) => ({
      from,
      to,
      caseSensitive: Boolean(entry.caseSensitive),
      match: compactString(entry.match) || "literal",
    }));
}

function normalizeAliases(payload) {
  const rawAliases = Array.isArray(payload) ? payload : Array.isArray(payload?.aliases) ? payload.aliases : [];
  return rawAliases.flatMap((entry) => normalizeAliasEntry(entry));
}

function normalizeReplyPhrases(payload) {
  const source = payload?.replyPhrases && typeof payload.replyPhrases === "object" ? payload.replyPhrases : payload;
  if (!source || typeof source !== "object" || Array.isArray(source)) {
    return {};
  }
  const phrases = {};
  for (const [key, value] of Object.entries(source)) {
    const phrase = compactString(value);
    if (REPLY_PHRASE_KEYS.has(key) && phrase) {
      phrases[key] = phrase;
    }
  }
  return phrases;
}

export function normalizeFeishuEmojiType(value) {
  const raw = compactString(value);
  if (!raw) {
    return "";
  }
  const mapped = EMOJI_TYPE_ALIASES.get(raw);
  if (mapped) {
    return mapped;
  }
  return raw.replace(/[^A-Za-z0-9_]/g, "").toUpperCase();
}

function normalizeReactions(payload) {
  const source = payload?.reactions && typeof payload.reactions === "object" ? payload.reactions : payload;
  if (!source || typeof source !== "object" || Array.isArray(source)) {
    return {};
  }
  const reactions = {};
  for (const [stage, value] of Object.entries(source)) {
    if (!REACTION_STAGE_KEYS.has(stage)) {
      continue;
    }
    const emojiType = normalizeFeishuEmojiType(value);
    if (emojiType) {
      reactions[stage] = emojiType;
    }
  }
  return reactions;
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function aliasPattern(alias) {
  const escaped = escapeRegExp(alias.from);
  const flags = alias.caseSensitive ? "g" : "gi";
  if (alias.match === "word") {
    return new RegExp(`(?<![A-Za-z0-9_])${escaped}(?![A-Za-z0-9_])`, flags);
  }
  return new RegExp(escaped, flags);
}

export function emptyLocalProfile(profileDir = "") {
  return {
    profileDir: compactString(profileDir),
    aliases: [],
    replyPhrases: {},
    reactions: {},
    personaText: "",
    loadedFiles: [],
  };
}

export function loadLocalProfile(profileDir) {
  const resolvedDir = path.resolve(profileDir);
  const profile = emptyLocalProfile(resolvedDir);

  const aliasesPath = path.join(resolvedDir, ALIASES_FILE);
  const aliasesPayload = readOptionalJson(aliasesPath);
  if (aliasesPayload) {
    profile.aliases = normalizeAliases(aliasesPayload);
    profile.loadedFiles.push(ALIASES_FILE);
  }

  const replyPhrasesPath = path.join(resolvedDir, REPLY_PHRASES_FILE);
  const replyPhrasesPayload = readOptionalJson(replyPhrasesPath);
  if (replyPhrasesPayload) {
    profile.replyPhrases = normalizeReplyPhrases(replyPhrasesPayload);
    profile.loadedFiles.push(REPLY_PHRASES_FILE);
  }

  const reactionsPath = path.join(resolvedDir, REACTIONS_FILE);
  const reactionsPayload = readOptionalJson(reactionsPath);
  if (reactionsPayload) {
    profile.reactions = normalizeReactions(reactionsPayload);
    profile.loadedFiles.push(REACTIONS_FILE);
  }

  const personaPath = path.join(resolvedDir, PERSONA_FILE);
  const personaText = readOptionalText(personaPath).trim();
  if (personaText) {
    profile.personaText = personaText;
    profile.loadedFiles.push(PERSONA_FILE);
  }

  return profile;
}

export function applyLocalAliases(messageText, localProfile) {
  const aliases = Array.isArray(localProfile?.aliases) ? localProfile.aliases : [];
  if (!aliases.length) {
    return String(messageText || "");
  }
  let normalized = String(messageText || "");
  const orderedAliases = [...aliases].sort((left, right) => right.from.length - left.from.length);
  for (const alias of orderedAliases) {
    normalized = normalized.replace(aliasPattern(alias), alias.to);
  }
  return normalized.replace(/\s+/g, " ").trim();
}

export function localReplyPhrase(localProfile, key, fallback) {
  const phrase = localProfile?.replyPhrases?.[key];
  return compactString(phrase) || fallback;
}

export function localReactionEmojiType(localProfile, stage) {
  return normalizeFeishuEmojiType(localProfile?.reactions?.[stage] || "");
}
