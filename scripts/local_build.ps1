[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$BuildArgs
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
    throw "Python 3 is required to run scripts/local_build.ps1."
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonCommand = @(Resolve-PythonCommand)
$pythonBinary = $pythonCommand[0]
$pythonPrefix = @()
if ($pythonCommand.Count -gt 1) {
    $pythonPrefix = $pythonCommand[1..($pythonCommand.Count - 1)]
}

$commandArgs = @((Join-Path $repoRoot "scripts\\local_build.py")) + $BuildArgs

Push-Location $repoRoot
try {
    & $pythonBinary @pythonPrefix @commandArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
