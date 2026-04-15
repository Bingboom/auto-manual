import path from "node:path";

function normalizePath(value) {
  const trimmed = String(value || "").trim();
  return trimmed ? path.resolve(trimmed) : "";
}

export function parseLocalListenerArgs(argv) {
  const result = {
    controlConfig: "",
    larkCliBin: "",
    eventIdentity: "",
    larkCliHome: "",
  };
  for (let index = 0; index < argv.length; index += 1) {
    const current = String(argv[index] || "").trim();
    if (!current) {
      continue;
    }
    if (current === "--control-config") {
      result.controlConfig = String(argv[index + 1] || "").trim();
      index += 1;
      continue;
    }
    if (current === "--lark-cli-bin") {
      result.larkCliBin = String(argv[index + 1] || "").trim();
      index += 1;
      continue;
    }
    if (current === "--event-identity") {
      result.eventIdentity = String(argv[index + 1] || "").trim();
      index += 1;
      continue;
    }
    if (current === "--lark-cli-home") {
      result.larkCliHome = normalizePath(argv[index + 1] || "");
      index += 1;
      continue;
    }
    if (current === "--help" || current === "-h") {
      return { ...result, help: true };
    }
    throw new Error(`Unknown argument: ${current}`);
  }
  return result;
}

export function localListenerUsage() {
  return [
    "Usage:",
    "  node local-listener.mjs [--control-config <config.yaml>] [--lark-cli-bin <bin>] [--event-identity <bot|user>] [--lark-cli-home <dir>]",
  ].join("\n");
}

export function buildLocalListenerConfig(baseConfig, args, env = process.env) {
  return {
    ...baseConfig,
    controlConfig: args.controlConfig || baseConfig.controlConfig,
    larkCliBin: args.larkCliBin || String(env.FEISHU_IM_LARK_CLI_BIN || "").trim() || "lark-cli",
    eventIdentity: args.eventIdentity || String(env.FEISHU_IM_EVENT_IDENTITY || "").trim() || "bot",
    larkCliHome: normalizePath(args.larkCliHome || env.FEISHU_IM_LARK_CLI_HOME || ""),
  };
}

export function buildLocalListenerSpawnEnv(config, env = process.env) {
  if (!config.larkCliHome) {
    return env;
  }
  return {
    ...env,
    HOME: config.larkCliHome,
    USERPROFILE: config.larkCliHome,
  };
}
