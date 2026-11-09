import { siteBase } from "../auto-manual-control-layer/lib/manual-query/client.mjs";

const loopback = (host) => ["localhost", "127.0.0.1", "[::1]"].includes(host);

export function httpUrl(value, originOnly = false) {
  const url = new URL(value);
  if ((url.protocol !== "https:" && !(url.protocol === "http:" && loopback(url.hostname)))
      || url.username || url.password || url.search || url.hash
      || (originOnly && !["", "/"].includes(url.pathname))) throw new Error("Expected an HTTPS URL without credentials.");
  return originOnly ? url.origin : url.href;
}

export function loadConfig(env = process.env) {
  const config = {
    host: "127.0.0.1", port: Number(env.HT_DOCS_CHAT_PORT || 8793),
    origins: (env.HT_DOCS_CHAT_ALLOWED_ORIGINS || "").split(",").filter(Boolean).map((s) => httpUrl(s.trim(), true)),
    passwordHash: env.HT_DOCS_CHAT_PASSWORD_SHA256 || "",
    baseUrl: siteBase(env.HT_DOCS_CHAT_MANUAL_BASE_URL || ""),
    rtdToken: env.HT_DOCS_CHAT_RTD_TOKEN || "",
    modelUrl: httpUrl(env.HT_DOCS_CHAT_MODEL_URL || ""),
    model: env.HT_DOCS_CHAT_MODEL || "", modelKey: env.HT_DOCS_CHAT_MODEL_KEY || "",
  };
  if (!Number.isInteger(config.port) || config.port < 1 || config.port > 65535 || !config.origins.length
      || !/^[a-f0-9]{64}$/.test(config.passwordHash) || !config.model
      || (!loopback(new URL(config.modelUrl).hostname) && !config.modelKey)) {
    throw new Error("Configure allowed origins, password SHA-256, manual base URL and model connection before starting.");
  }
  return config;
}

export function corpusFetch(config, fetchImpl = globalThis.fetch) {
  const origin = new URL(config.baseUrl).origin;
  return (input, options = {}) => {
    if (new URL(input).origin !== origin) throw new Error("Unexpected manual source origin.");
    const headers = new Headers(options.headers);
    if (config.rtdToken) headers.set("Authorization", "Token " + config.rtdToken);
    return fetchImpl(input, { ...options, headers });
  };
}
