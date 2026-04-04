[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$BranchName,

    [string]$Remote = "origin",

    [string]$BaseBranch = "main",

    [switch]$AllowDirty
)

$ErrorActionPreference = "Stop"

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    $output = & git @Args 2>&1
    if ($LASTEXITCODE -ne 0) {
        $message = ($output -join "`n").Trim()
        if ($message) {
            throw "git $($Args -join ' ') failed.`n$message"
        }
        throw "git $($Args -join ' ') failed."
    }
    if ($output) {
        $output | ForEach-Object { Write-Host $_ }
    }
}

function Invoke-GitCapture {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    $lines = & git @Args 2>&1
    if ($LASTEXITCODE -ne 0) {
        $message = ($lines -join "`n").Trim()
        if ($message) {
            throw "git $($Args -join ' ') failed.`n$message"
        }
        throw "git $($Args -join ' ') failed."
    }
    return ($lines -join "`n").Trim()
}

function Get-DirtyRepoLines {
    $allowedPrefixes = @(
        ".tmp/",
        "docs/_build/",
        "reports/version_tracking/",
        "reports/releases/"
    )
    $statusLines = & git status --porcelain=v1 --untracked-files=all
    if ($LASTEXITCODE -ne 0) {
        throw "git status failed."
    }

    $dirty = @()
    foreach ($line in $statusLines) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }
        $pathText = ""
        if ($line.Length -ge 4) {
            $pathText = $line.Substring(3).Trim()
        } else {
            $pathText = $line.Trim()
        }
        if ($pathText -like "* -> *") {
            $pathText = ($pathText -split " -> ", 2)[1].Trim()
        }
        $normalized = $pathText.Replace("\", "/")
        $isAllowed = $false
        foreach ($prefix in $allowedPrefixes) {
            if ($normalized.StartsWith($prefix)) {
                $isAllowed = $true
                break
            }
        }
        if (-not $isAllowed) {
            $dirty += $line
        }
    }
    return $dirty
}

$repoRoot = Invoke-GitCapture -Args @("rev-parse", "--show-toplevel")
Set-Location $repoRoot

if (-not $AllowDirty) {
    $dirtyLines = Get-DirtyRepoLines
    if ($dirtyLines.Count -gt 0) {
        Write-Error "Refusing to create a new branch from a dirty worktree. Commit, stash, or clean these paths first:`n$($dirtyLines -join "`n")"
        exit 1
    }
}

$existingLocal = & git show-ref --verify --quiet "refs/heads/$BranchName"
if ($LASTEXITCODE -eq 0) {
    Write-Error "Local branch '$BranchName' already exists."
    exit 1
}

$existingRemote = & git show-ref --verify --quiet "refs/remotes/$Remote/$BranchName"
if ($LASTEXITCODE -eq 0) {
    Write-Error "Remote branch '$Remote/$BranchName' already exists."
    exit 1
}

Invoke-Git -Args @("fetch", $Remote, $BaseBranch)
Invoke-Git -Args @("switch", $BaseBranch)
Invoke-Git -Args @("pull", "--ff-only", $Remote, $BaseBranch)
Invoke-Git -Args @("switch", "-c", $BranchName)

$headSha = Invoke-GitCapture -Args @("rev-parse", "--short", "HEAD")
Write-Host "[start-branch] Created $BranchName from $Remote/$BaseBranch at $headSha"
