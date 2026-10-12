# Create a local virtualenv that matches CI: the pinned Python from pyproject.toml
# ([tool.mypy] python_version) plus the exact pins in requirements.lock, then prove
# it with `tools/env_preflight.py --strict`. Mirrors scripts/setup_dev_env.sh.
#
# Usage: powershell -ExecutionPolicy Bypass -File scripts/setup_dev_env.ps1 [-Venv DIR] [-Python BIN] [-Recreate]
# Exit codes: 0 ready; 1 installed but preflight still reports drift; 2 usage or setup error.
[CmdletBinding()]
param(
    [string]$Venv = "",
    [string]$Python = "",
    [switch]$Recreate
)

$ErrorActionPreference = "Stop"
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
if (-not $Venv) { $Venv = Join-Path $repoRoot ".venv" }

function Fail([string]$message) {
    Write-Host "[setup-dev-env] $message" -ForegroundColor Red
    exit 2
}

function Get-PythonVersion([string[]]$command) {
    try {
        $exe = $command[0]
        $rest = @($command | Select-Object -Skip 1)
        $out = & $exe @rest -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>$null
        if ($LASTEXITCODE -eq 0) { return ([string]$out).Trim() }
    } catch {}
    return ""
}

$pyproject = Get-Content (Join-Path $repoRoot "pyproject.toml") -Encoding UTF8
$pinLine = $pyproject | Where-Object { $_ -match '^python_version\s*=\s*"(\d+\.\d+)"' } | Select-Object -First 1
if (-not $pinLine) { Fail "no [tool.mypy] python_version pin found in pyproject.toml" }
$null = $pinLine -match '"(\d+\.\d+)"'
$pinned = $Matches[1]

$pythonCommand = @()
if ($Python) {
    $pythonCommand = @($Python)
} else {
    foreach ($candidate in @(@("py", "-$pinned"), @("python$pinned"), @("python3"), @("python"))) {
        if (Get-Command $candidate[0] -ErrorAction SilentlyContinue) {
            if ((Get-PythonVersion $candidate) -eq $pinned) { $pythonCommand = $candidate; break }
        }
    }
}
if (-not $pythonCommand) { Fail "Python $pinned not found; install it or pass -Python C:\path\to\python.exe" }
$found = Get-PythonVersion $pythonCommand
if ($found -ne $pinned) { Fail "$($pythonCommand -join ' ') is Python $found, but the repo pins $pinned" }

$venvPy = Join-Path $Venv "Scripts\python.exe"
if (-not (Test-Path $venvPy)) { $venvPy = Join-Path $Venv "bin/python" }
if ((Test-Path $Venv) -and $Recreate) {
    Write-Host "[setup-dev-env] removing $Venv"
    Remove-Item -Recurse -Force $Venv
}
if (Test-Path $venvPy) {
    $existing = Get-PythonVersion @($venvPy)
    if ($existing -ne $pinned) { Fail "$Venv was built with Python $existing; rerun with -Recreate" }
    Write-Host "[setup-dev-env] reusing $Venv (Python $existing)"
} else {
    Write-Host "[setup-dev-env] creating $Venv with $($pythonCommand -join ' ') (Python $found)"
    $exe = $pythonCommand[0]
    $rest = @($pythonCommand | Select-Object -Skip 1)
    & $exe @rest -m venv $Venv
    if ($LASTEXITCODE -ne 0) { Fail "venv creation failed" }
    $venvPy = Join-Path $Venv "Scripts\python.exe"
    if (-not (Test-Path $venvPy)) { $venvPy = Join-Path $Venv "bin/python" }
}

Write-Host "[setup-dev-env] installing requirements.lock"
& $venvPy -m pip install --quiet --upgrade pip
if ($LASTEXITCODE -ne 0) { Fail "pip upgrade failed" }
& $venvPy -m pip install --quiet -r (Join-Path $repoRoot "requirements.lock")
if ($LASTEXITCODE -ne 0) { Fail "installing requirements.lock failed" }

Write-Host "[setup-dev-env] checking the environment against CI"
Push-Location $repoRoot
try {
    & $venvPy tools/env_preflight.py --strict
    $preflight = $LASTEXITCODE
} finally {
    Pop-Location
}
if ($preflight -ne 0) {
    Write-Host "[setup-dev-env] installed, but the environment still differs from CI (see WARN rows above)" -ForegroundColor Yellow
    exit 1
}
Write-Host "[setup-dev-env] ready: $Venv\Scripts\Activate.ps1"
exit 0
