export function loadSettings(pluginConfig = {}, resolvePath = (value) => value) {
  const config = pluginConfig || {};
  const defaultBranch = typeof config.defaultBranch === "string" && config.defaultBranch.trim() ? config.defaultBranch.trim() : "main";
  const apiBaseUrl = typeof config.apiBaseUrl === "string" && config.apiBaseUrl.trim() ? config.apiBaseUrl.trim() : "https://api.github.com";
  const metadataArtifactName =
    typeof config.metadataArtifactName === "string" && config.metadataArtifactName.trim()
      ? config.metadataArtifactName.trim()
      : "openclaw-run-metadata";
  const dispatchTimeoutSeconds =
    Number.isInteger(config.dispatchTimeoutSeconds) && config.dispatchTimeoutSeconds > 0
      ? config.dispatchTimeoutSeconds
      : 40;
  const stateFile = typeof config.stateFile === "string" && config.stateFile.trim()
    ? resolvePath(config.stateFile.trim())
    : resolvePath("runtime/auto-manual-control-layer-state.json");

  return {
    githubToken: typeof config.githubToken === "string" ? config.githubToken.trim() : "",
    repoOwner: typeof config.repoOwner === "string" ? config.repoOwner.trim() : "",
    repoName: typeof config.repoName === "string" ? config.repoName.trim() : "",
    defaultBranch,
    apiBaseUrl,
    metadataArtifactName,
    dispatchTimeoutSeconds,
    stateFile,
  };
}

export function missingSettings(settings) {
  return ["githubToken", "repoOwner", "repoName"].filter((field) => !settings[field]);
}
