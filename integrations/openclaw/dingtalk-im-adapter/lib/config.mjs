import path from "node:path";
import { fileURLToPath } from "node:url";

import { emptyLocalProfile, loadLocalProfile } from "./local-profile.mjs";

const adapterRoot = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const defaultRepoRoot = path.resolve(adapterRoot, "..", "..", "..");

function integerEnv(name, defaultValue) {
  const raw = String(process.env[name] || "").trim();
  if (!raw) {
    return defaultValue;
  }
  const parsed = Number.parseInt(raw, 10);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : defaultValue;
}

function booleanEnv(name, defaultValue) {
  const raw = String(process.env[name] || "").trim().toLowerCase();
  if (!raw) {
    return defaultValue;
  }
  if (raw === "true" || raw === "1" || raw === "yes") {
    return true;
  }
  if (raw === "false" || raw === "0" || raw === "no") {
    return false;
  }
  return defaultValue;
}

function listEnv(name) {
  return String(process.env[name] || "")
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);
}

// DingTalk IM Stream-mode adapter config.
//
// This mirrors the Feishu IM webhook adapter but for DingTalk's Stream
// (long-connection) ingress, so it has no public webhook host/port and no
// verification/encrypt tokens. Credentials are the DingTalk app's
// clientId (AppKey) + clientSecret (AppSecret); the same value doubles as the
// robotCode for outbound robot-API sends.
export function loadAdapterConfig() {
  const repoRoot = path.resolve(process.env.AUTO_MANUAL_REPO_ROOT || defaultRepoRoot);
  const localProfileDir = path.resolve(
    process.env.DINGTALK_IM_LOCAL_PROFILE_DIR || process.env.OPENCLAW_LOCAL_PROFILE_DIR || path.join(repoRoot, ".openclaw")
  );
  const localProfileEnabled = !booleanEnv(
    "DINGTALK_IM_DISABLE_LOCAL_PROFILE",
    booleanEnv("OPENCLAW_DISABLE_LOCAL_PROFILE", false)
  );
  const clientId = String(process.env.DINGTALK_IM_CLIENT_ID || process.env.DINGTALK_CLIENT_ID || "").trim();
  return {
    clientId,
    clientSecret: String(process.env.DINGTALK_IM_CLIENT_SECRET || process.env.DINGTALK_CLIENT_SECRET || "").trim(),
    // robotCode equals the AppKey/clientId for enterprise inner-robots; allow override for edge cases.
    robotCode: String(process.env.DINGTALK_IM_ROBOT_CODE || "").trim() || clientId,
    apiBaseUrl: String(process.env.DINGTALK_IM_API_BASE_URL || "").trim() || "https://api.dingtalk.com",
    repoRoot,
    pythonBin: String(process.env.AUTO_MANUAL_PYTHON || "").trim() || "python3",
    controlConfig: String(process.env.AUTO_MANUAL_CONTROL_CONFIG || "").trim() || "configs/config.us.yaml",
    // Group messages only act when the bot is @-mentioned (DingTalk isInAtList).
    requireMention: booleanEnv("DINGTALK_IM_REQUIRE_MENTION", true),
    // allowFrom gates which DingTalk staffIds may drive the adapter. Empty list
    // is fail-closed (ignore everyone) because this is a build/publish control
    // surface; set DINGTALK_IM_ALLOW_FROM to staffId(s) or "*" to open it.
    allowFrom: listEnv("DINGTALK_IM_ALLOW_FROM"),
    // DingTalk has no message-reaction API, so the Feishu "received" reaction
    // degrades to a one-line text acknowledgement. Toggle off to stay silent.
    ackOnReceived: booleanEnv("DINGTALK_IM_ACK_ON_RECEIVED", true),
    receivedAckText: String(process.env.DINGTALK_IM_RECEIVED_ACK_TEXT || "").trim(),
    publishConfirmTtlSeconds: integerEnv("DINGTALK_IM_PUBLISH_CONFIRM_TTL_SECONDS", 600),
    conversationContextTtlSeconds: integerEnv("DINGTALK_IM_CONTEXT_TTL_SECONDS", 3600),
    batchDispatchDelayMs: integerEnv("DINGTALK_IM_BATCH_DISPATCH_DELAY_MS", 2000),
    batchStatusTimeoutSeconds: integerEnv("DINGTALK_IM_BATCH_STATUS_TIMEOUT_SECONDS", 60),
    batchStatusPollSeconds: integerEnv("DINGTALK_IM_BATCH_STATUS_POLL_SECONDS", 5),
    manualIndexLimit: integerEnv("DINGTALK_IM_MANUAL_INDEX_LIMIT", 10),
    stateFile:
      String(process.env.DINGTALK_IM_STATE_FILE || "").trim() ||
      path.resolve(adapterRoot, "runtime", "dingtalk-im-adapter-state.json"),
    localProfileDir,
    localProfileEnabled,
    localProfile: localProfileEnabled ? loadLocalProfile(localProfileDir) : emptyLocalProfile(localProfileDir),
  };
}

export function missingAdapterConfig(config) {
  return ["clientId", "clientSecret"].filter((field) => !config[field]);
}

export function adapterRootPath() {
  return adapterRoot;
}
