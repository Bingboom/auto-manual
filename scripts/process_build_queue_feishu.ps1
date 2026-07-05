param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$BuildQueueArgs
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:AUTO_MANUAL_ARTIFACT_SINK_PROVIDER = "lark_drive"
# Explicit "no mirror". Assigning "" DELETES the env var in PowerShell, which
# process_build_queue.ps1's required-env backfill then treats as unset and
# re-imports the User-scope mirror — silently re-enabling the DingTalk mirror
# this lark_drive-only wrapper is meant to disable. "none" is non-empty (so the
# backfill leaves it alone) and _normalize_optional_provider reads it as no mirror.
$env:AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER = "none"

& (Join-Path $scriptDir "process_build_queue.ps1") @BuildQueueArgs
exit $LASTEXITCODE
