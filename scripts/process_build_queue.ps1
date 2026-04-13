param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$BuildQueueArgs
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$nodePaths = @(
    "C:\Program Files\nodejs",
    (Join-Path $env:APPDATA "npm")
)
foreach ($pathEntry in $nodePaths) {
    if ((Test-Path $pathEntry) -and (-not (($env:Path -split ";") -contains $pathEntry))) {
        $env:Path = "$pathEntry;$env:Path"
    }
}

$requiredEnvNames = @(
    "FEISHU_PHASE2_BASE_TOKEN",
    "FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID",
    "FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID",
    "AUTO_MANUAL_ARTIFACT_SINK_PROVIDER",
    "AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER",
    "DINGTALK_DOCS_TARGET_NODE_URL",
    "DINGTALK_DOCS_A_TOKEN",
    "DINGTALK_DOCS_XSRF_TOKEN",
    "DINGTALK_DOCS_COOKIE",
    "DINGTALK_DOCS_BX_V"
)
foreach ($envName in $requiredEnvNames) {
    if (-not (Get-Item -Path ("Env:" + $envName) -ErrorAction SilentlyContinue)) {
        $userValue = [Environment]::GetEnvironmentVariable($envName, "User")
        if ($userValue) {
            Set-Item -Path ("Env:" + $envName) -Value $userValue
        }
    }
}

$logDir = Join-Path $repoRoot ".tmp\process-build-queue"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$latestLogPath = Join-Path $logDir "latest.log"
$dailyLogPath = Join-Path $logDir ("process-build-queue-" + (Get-Date -Format "yyyyMMdd") + ".log")

$command = @(
    (Join-Path $repoRoot "build.py"),
    "process-build-queue",
    "--config",
    "config.us.yaml",
    "--data-root",
    "data/phase2",
    "--staging-root",
    ".tmp/staging"
)
if ($BuildQueueArgs) {
    $command += $BuildQueueArgs
}
$commandLine = ($command | ForEach-Object {
    if ($_ -match "\s") { '"' + $_ + '"' } else { $_ }
}) -join " "

$header = "[{0}] {1} {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $pythonExe, $commandLine
$header | Tee-Object -FilePath $latestLogPath | Tee-Object -FilePath $dailyLogPath -Append | Out-Null

$output = & $pythonExe @command 2>&1
$exitCode = $LASTEXITCODE
if ($output) {
    $output | Tee-Object -FilePath $latestLogPath -Append | Tee-Object -FilePath $dailyLogPath -Append
}
exit $exitCode

