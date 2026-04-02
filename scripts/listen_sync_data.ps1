$ErrorActionPreference = "Stop"
if ($PSVersionTable.PSVersion.Major -ge 7) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}
$env:PYTHONUNBUFFERED = "1"

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
    "FEISHU_PHASE2_SPEC_MASTER_TABLE_ID",
    "FEISHU_PHASE2_SPEC_MASTER_VIEW_ID",
    "FEISHU_PHASE2_SPEC_FOOTNOTES_TABLE_ID",
    "FEISHU_PHASE2_SPEC_FOOTNOTES_VIEW_ID",
    "FEISHU_PHASE2_SPEC_NOTES_TABLE_ID",
    "FEISHU_PHASE2_SPEC_NOTES_VIEW_ID",
    "FEISHU_PHASE2_SPEC_TITLES_TABLE_ID",
    "FEISHU_PHASE2_SPEC_TITLES_VIEW_ID",
    "FEISHU_PHASE2_SYMBOLS_BLOCKS_TABLE_ID",
    "FEISHU_PHASE2_SYMBOLS_BLOCKS_VIEW_ID"
)
foreach ($envName in $requiredEnvNames) {
    if (-not (Get-Item -Path ("Env:" + $envName) -ErrorAction SilentlyContinue)) {
        $userValue = [Environment]::GetEnvironmentVariable($envName, "User")
        if ($userValue) {
            Set-Item -Path ("Env:" + $envName) -Value $userValue
        }
    }
}

$logDir = Join-Path $repoRoot ".tmp\sync-data-listener"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$latestLogPath = Join-Path $logDir "latest.log"
$dailyLogPath = Join-Path $logDir ("sync-data-listener-" + (Get-Date -Format "yyyyMMdd") + ".log")

$command = @(
    (Join-Path $repoRoot "build.py"),
    "listen-sync-data",
    "--config",
    "config.yaml",
    "--data-root",
    "data/phase2"
)
$commandLine = ($command | ForEach-Object {
    if ($_ -match "\s") { '"' + $_ + '"' } else { $_ }
}) -join " "

$header = "[{0}] {1} {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $pythonExe, $commandLine
$header | Tee-Object -FilePath $latestLogPath | Tee-Object -FilePath $dailyLogPath -Append | Out-Null

$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $pythonExe @command 2>&1 | Tee-Object -FilePath $latestLogPath -Append | Tee-Object -FilePath $dailyLogPath -Append
$nativeExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorActionPreference
exit $nativeExitCode
