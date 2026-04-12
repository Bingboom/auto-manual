param()

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$adapterDir = Join-Path $repoRoot "integrations\openclaw\feishu-im-webhook-adapter"

$nodePaths = @(
    "C:\Program Files\nodejs",
    (Join-Path $env:APPDATA "npm")
)
foreach ($pathEntry in $nodePaths) {
    if ((Test-Path $pathEntry) -and (-not (($env:Path -split ";") -contains $pathEntry))) {
        $env:Path = "$pathEntry;$env:Path"
    }
}

$fallbackEnvNames = @(
    "FEISHU_APP_ID",
    "FEISHU_APP_SECRET",
    "FEISHU_IM_APP_ID",
    "FEISHU_IM_APP_SECRET",
    "FEISHU_IM_VERIFICATION_TOKEN",
    "FEISHU_VERIFICATION_TOKEN",
    "FEISHU_IM_WEBHOOK_HOST",
    "FEISHU_IM_WEBHOOK_PORT",
    "FEISHU_IM_WEBHOOK_PATH",
    "FEISHU_IM_HEALTH_PATH",
    "FEISHU_IM_REQUIRE_MENTION",
    "AUTO_MANUAL_CONTROL_CONFIG"
)
foreach ($envName in $fallbackEnvNames) {
    if (-not (Get-Item -Path ("Env:" + $envName) -ErrorAction SilentlyContinue)) {
        $userValue = [Environment]::GetEnvironmentVariable($envName, "User")
        if ($userValue) {
            Set-Item -Path ("Env:" + $envName) -Value $userValue
        }
    }
}

if (-not $env:AUTO_MANUAL_REPO_ROOT) {
    $env:AUTO_MANUAL_REPO_ROOT = $repoRoot
}
if (-not $env:AUTO_MANUAL_CONTROL_CONFIG) {
    $env:AUTO_MANUAL_CONTROL_CONFIG = "config.us.yaml"
}
if (-not $env:FEISHU_IM_STATE_FILE) {
    $stateDir = Join-Path $repoRoot ".tmp\feishu-im-webhook-adapter"
    New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
    $env:FEISHU_IM_STATE_FILE = Join-Path $stateDir "state.json"
}

Push-Location $adapterDir
try {
    npm start
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
