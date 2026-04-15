param(
    [ValidateSet("validate", "doctor", "check", "rst", "word", "html", "pdf", "all")]
    [string]$Action = "word",

    [Parameter(Mandatory = $true)]
    [string]$Model,

    [string]$Region = "US",

    [string[]]$Languages = @("en", "es", "fr"),

    [ValidateSet("auto", "runtime", "review")]
    [string]$Source = "auto",

    [ValidateSet("latex", "word")]
    [string]$PdfMode,

    [switch]$CheckFirst,

    [switch]$Open,

    [switch]$NoClean,

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$normalizedRegion = [string]$Region
$normalizedRegion = $normalizedRegion.Trim().ToUpperInvariant()
if ($normalizedRegion -and $normalizedRegion -ne "US") {
    throw "scripts/build_us_manuals.ps1 only supports the US single-language matrix. Use scripts/build_us_jp_manuals.py or build.py for other regions."
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$requestedLangs = @()
foreach ($lang in $Languages) {
    if ([string]::IsNullOrWhiteSpace($lang)) {
        continue
    }
    foreach ($part in ($lang -split ",")) {
        if ([string]::IsNullOrWhiteSpace($part)) {
            continue
        }
        $requestedLangs += $part.Trim().ToLowerInvariant()
    }
}
$requestedLangs = $requestedLangs | Select-Object -Unique

$supportedLangs = @("en", "es", "fr")
$unsupported = @($requestedLangs | Where-Object { $_ -notin $supportedLangs })
if ($unsupported.Count -gt 0) {
    throw ("Unsupported language(s): {0}. Supported values: en, es, fr." -f ($unsupported -join ", "))
}
if ($requestedLangs.Count -eq 0) {
    throw "No valid languages were provided."
}

$scriptPath = Join-Path $scriptDir "build_us_jp_manuals.py"
$commandArgs = @(
    $scriptPath,
    "--model", $Model,
    "--languages"
) + $requestedLangs + @(
    "--build-action", $Action,
    "--source", $Source
)

if ($PdfMode) {
    $commandArgs += @("--pdf-mode", $PdfMode)
}
if ($CheckFirst) {
    $commandArgs += "--check-first"
}
if ($Open) {
    $commandArgs += "--open"
}
if ($NoClean) {
    $commandArgs += "--no-clean"
}
if ($DryRun) {
    $commandArgs += "--dry-run"
}

Write-Host ("[build_us_manuals] {0} {1}" -f $pythonExe, ($commandArgs -join " ")) -ForegroundColor DarkGray
& $pythonExe @commandArgs
exit $LASTEXITCODE
