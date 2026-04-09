param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$BuildQueueArgs
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:AUTO_MANUAL_ARTIFACT_SINK_PROVIDER = "lark_drive"

& (Join-Path $scriptDir "process_build_queue.ps1") @BuildQueueArgs
exit $LASTEXITCODE
