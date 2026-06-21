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

export function loadAdapterConfig() {
  const repoRoot = path.resolve(process.env.AUTO_MANUAL_REPO_ROOT || defaultRepoRoot);
  const localProfileDir = path.resolve(
    process.env.FEISHU_IM_LOCAL_PROFILE_DIR || process.env.OPENCLAW_LOCAL_PROFILE_DIR || path.join(repoRoot, ".openclaw")
  );
  const localProfileEnabled = !booleanEnv(
    "FEISHU_IM_DISABLE_LOCAL_PROFILE",
    booleanEnv("OPENCLAW_DISABLE_LOCAL_PROFILE", false)
  );
  return {
    host: String(process.env.FEISHU_IM_WEBHOOK_HOST || "").trim() || "127.0.0.1",
    port: integerEnv("FEISHU_IM_WEBHOOK_PORT", 9097),
    callbackPath: String(process.env.FEISHU_IM_WEBHOOK_PATH || "").trim() || "/feishu/events",
    healthPath: String(process.env.FEISHU_IM_HEALTH_PATH || "").trim() || "/healthz",
    verificationToken: String(process.env.FEISHU_IM_VERIFICATION_TOKEN || process.env.FEISHU_VERIFICATION_TOKEN || "").trim(),
    encryptKey: String(process.env.FEISHU_IM_ENCRYPT_KEY || process.env.FEISHU_ENCRYPT_KEY || "").trim(),
    appId: String(process.env.FEISHU_IM_APP_ID || process.env.FEISHU_APP_ID || "").trim(),
    appSecret: String(process.env.FEISHU_IM_APP_SECRET || process.env.FEISHU_APP_SECRET || "").trim(),
    apiBaseUrl: String(process.env.FEISHU_IM_API_BASE_URL || "").trim() || "https://open.feishu.cn/open-apis",
    repoRoot,
    pythonBin: String(process.env.AUTO_MANUAL_PYTHON || "").trim() || "python3",
    controlConfig: String(process.env.AUTO_MANUAL_CONTROL_CONFIG || "").trim() || "configs/config.us.yaml",
    requireMention: booleanEnv("FEISHU_IM_REQUIRE_MENTION", true),
    enableMessageReactions: booleanEnv("FEISHU_IM_ENABLE_MESSAGE_REACTIONS", booleanEnv("FEISHU_IM_ENABLE_REACTIONS", false)),
    publishConfirmTtlSeconds: integerEnv("FEISHU_IM_PUBLISH_CONFIRM_TTL_SECONDS", 600),
    conversationContextTtlSeconds: integerEnv("FEISHU_IM_CONTEXT_TTL_SECONDS", 3600),
    batchDispatchDelayMs: integerEnv("FEISHU_IM_BATCH_DISPATCH_DELAY_MS", 2000),
    batchStatusTimeoutSeconds: integerEnv("FEISHU_IM_BATCH_STATUS_TIMEOUT_SECONDS", 60),
    batchStatusPollSeconds: integerEnv("FEISHU_IM_BATCH_STATUS_POLL_SECONDS", 5),
    manualIndexLimit: integerEnv("FEISHU_IM_MANUAL_INDEX_LIMIT", 10),
    stateFile:
      String(process.env.FEISHU_IM_STATE_FILE || "").trim() ||
      path.resolve(adapterRoot, "runtime", "feishu-im-webhook-adapter-state.json"),
    localProfileDir,
    localProfileEnabled,
    localProfile: localProfileEnabled ? loadLocalProfile(localProfileDir) : emptyLocalProfile(localProfileDir),
  };
}

export function missingAdapterConfig(config) {
  return ["appId", "appSecret"].filter((field) => !config[field]);
}

export function adapterRootPath() {
  return adapterRoot;
}
