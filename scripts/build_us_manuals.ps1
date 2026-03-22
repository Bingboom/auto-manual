param(
    [ValidateSet("validate", "doctor", "check", "rst", "word", "html", "pdf", "all")]
    [string]$Action = "word",

    [string]$Model = "JE-1000F",

    [string]$Region = "US",

    [string[]]$Languages = @("en", "es", "fr"),

    [ValidateSet("auto", "runtime", "review")]
    [string]$Source = "auto",

    [ValidateSet("latex", "word")]
    [string]$PdfMode,

    [switch]$CheckFirst,

    [switch]$Open,

    [switch]$NoClean
)

$ErrorActionPreference = "Stop"

function Get-Slug {
    param(
        [AllowNull()]
        [string]$Value
    )

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return ""
    }

    return (($Value.ToLowerInvariant()) -replace "[^a-z0-9]+", "")
}

function Get-ExpectedOutputs {
    param(
        [string]$RepoRoot,
        [string]$ActionName,
        [string]$ModelName,
        [string]$RegionName,
        [string]$LangName
    )

    $baseDir = Join-Path $RepoRoot ("docs\_build\{0}\{1}\{2}" -f $ModelName, $RegionName, $LangName)
    $modelSlug = Get-Slug $ModelName
    $regionSlug = Get-Slug $RegionName
    $langSlug = Get-Slug $LangName

    $outputs = New-Object System.Collections.Generic.List[string]
    switch ($ActionName) {
        "rst" {
            $outputs.Add((Join-Path $baseDir "rst\index.rst"))
        }
        "word" {
            $outputs.Add((Join-Path $baseDir ("word\manual_{0}_{1}_{2}.docx" -f $modelSlug, $regionSlug, $langSlug)))
        }
        "html" {
            $outputs.Add((Join-Path $baseDir "html\index.html"))
        }
        "pdf" {
            $outputs.Add((Join-Path $baseDir ("pdf\manual_{0}_{1}_{2}.pdf" -f $modelSlug, $regionSlug, $langSlug)))
        }
        "all" {
            $outputs.Add((Join-Path $baseDir "html\index.html"))
            $outputs.Add((Join-Path $baseDir ("word\manual_{0}_{1}_{2}.docx" -f $modelSlug, $regionSlug, $langSlug)))
            $outputs.Add((Join-Path $baseDir ("pdf\manual_{0}_{1}_{2}.pdf" -f $modelSlug, $regionSlug, $langSlug)))
        }
    }

    return $outputs
}

function Invoke-BuildCommand {
    param(
        [string]$PythonExe,
        [string]$RepoRoot,
        [string[]]$Arguments,
        [string]$Label
    )

    Write-Host ""
    Write-Host ("==> {0}" -f $Label) -ForegroundColor Cyan
    Write-Host ("    {0} {1}" -f $PythonExe, ($Arguments -join " ")) -ForegroundColor DarkGray

    & $PythonExe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw ("Command failed with exit code {0}: {1}" -f $LASTEXITCODE, $Label)
    }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$configMap = @{
    "en" = "config.us-en.yaml"
    "es" = "config.us-es.yaml"
    "fr" = "config.us-fr.yaml"
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

$unsupported = @($requestedLangs | Where-Object { -not $configMap.ContainsKey($_) })
if ($unsupported.Count -gt 0) {
    throw ("Unsupported language(s): {0}. Supported values: en, es, fr." -f ($unsupported -join ", "))
}

if ($requestedLangs.Count -eq 0) {
    throw "No valid languages were provided."
}

$artifactPaths = New-Object System.Collections.Generic.List[string]

Push-Location $repoRoot
try {
    foreach ($lang in $requestedLangs) {
        $configPath = $configMap[$lang]

        if ($CheckFirst -and $Action -ne "check") {
            $checkArgs = @(
                "build.py",
                "check",
                "--config", $configPath,
                "--model", $Model,
                "--region", $Region
            )
            Invoke-BuildCommand -PythonExe $pythonExe -RepoRoot $repoRoot -Arguments $checkArgs -Label ("[{0}] check" -f $lang)
        }

        $buildArgs = @(
            "build.py",
            $Action,
            "--config", $configPath,
            "--model", $Model,
            "--region", $Region,
            "--source", $Source
        )

        if ($PdfMode) {
            $buildArgs += @("--pdf-mode", $PdfMode)
        }
        if ($Open) {
            $buildArgs += "--open"
        }
        if ($NoClean) {
            $buildArgs += "--no-clean"
        }

        Invoke-BuildCommand -PythonExe $pythonExe -RepoRoot $repoRoot -Arguments $buildArgs -Label ("[{0}] {1}" -f $lang, $Action)

        foreach ($artifact in (Get-ExpectedOutputs -RepoRoot $repoRoot -ActionName $Action -ModelName $Model -RegionName $Region -LangName $lang)) {
            if (Test-Path $artifact) {
                $artifactPaths.Add($artifact)
            }
        }
    }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Completed." -ForegroundColor Green
if ($artifactPaths.Count -gt 0) {
    Write-Host "Artifacts:" -ForegroundColor Green
    foreach ($artifact in $artifactPaths) {
        Write-Host (" - {0}" -f $artifact)
    }
}
