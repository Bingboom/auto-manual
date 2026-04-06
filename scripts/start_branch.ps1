[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$BranchName,

    [string]$Remote = "origin",

    [string]$BaseBranch = "main",

    [switch]$AllowDirty
)

$ErrorActionPreference = "Stop"

function Resolve-PythonCommand {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $repoRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptDir ".."))

    if ($env:PYTHON) {
        return @($env:PYTHON)
    }

    $venvWindows = Join-Path $repoRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvWindows) {
        return @($venvWindows)
    }

    $venvPosix = Join-Path $repoRoot ".venv\bin\python"
    if (Test-Path $venvPosix) {
        return @($venvPosix)
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @($python.Source)
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return @($py.Source, "-3")
    }

    throw "Python 3 is required to run scripts/git_branch_guard.py."
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptDir ".."))
$pythonCommand = @(Resolve-PythonCommand)
$pythonBinary = $pythonCommand[0]
$pythonPrefix = @()
if ($pythonCommand.Count -gt 1) {
    $pythonPrefix = $pythonCommand[1..($pythonCommand.Count - 1)]
}

$guardArgs = @(
    (Join-Path $repoRoot "scripts\git_branch_guard.py"),
    "start-branch",
    "--repo-root", $repoRoot,
    "--branch", $BranchName,
    "--remote", $Remote,
    "--base-branch", $BaseBranch
)

if ($AllowDirty) {
    $guardArgs += "--allow-dirty"
}

Push-Location $repoRoot
try {
    & $pythonBinary @pythonPrefix @guardArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
