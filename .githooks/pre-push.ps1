[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Remote = "origin"
)

$ErrorActionPreference = "Stop"

function Resolve-PythonCommand {
    if ($env:PYTHON) {
        return @($env:PYTHON)
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    throw "Python 3 is required to run the repo branch guard."
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonCommand = @(Resolve-PythonCommand)
$pythonBinary = $pythonCommand[0]
$pythonPrefix = @()
if ($pythonCommand.Count -gt 1) {
    $pythonPrefix = $pythonCommand[1..($pythonCommand.Count - 1)]
}

$baseBranch = if ($env:AUTO_MANUAL_BASE_BRANCH) { $env:AUTO_MANUAL_BASE_BRANCH } else { "main" }
$guardArgs = @(
    (Join-Path $repoRoot "scripts\git_branch_guard.py"),
    "pre-push",
    "--repo-root", $repoRoot,
    "--remote", $Remote,
    "--base-branch", $baseBranch
)

Push-Location $repoRoot
try {
    & $pythonBinary @pythonPrefix @guardArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
