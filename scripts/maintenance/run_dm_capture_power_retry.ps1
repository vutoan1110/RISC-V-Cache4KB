[CmdletBinding()]
param([switch]$Run, [switch]$Resume)
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $taskRoot
$taskP1 = 'results/gls_exact_dm_full_p1_20261011/receipt.json'
$taskFailed = 'results/gls_exact_dm_full_p2_20261011/receipt.json'
$taskReplay = 'results/gls_pin_conversion_retry_20261011/receipt.json'
$taskOutput = 'results/gls_exact_dm_full_p2_retry_20261011'
$taskQueue = 'results/exact_power_queue_dm_retry_20261011.json'
$taskPair = 'results/gls_exact_dm_full_pair_retry_20261011.json'
$taskPower = 'results/activity_power_exact_dm_retry_20261011'
$taskFirst = Get-Content -LiteralPath $taskP1 -Raw | ConvertFrom-Json
$taskOld = Get-Content -LiteralPath $taskFailed -Raw | ConvertFrom-Json
$taskDiagnostic = Get-Content -LiteralPath $taskReplay -Raw | ConvertFrom-Json
if ($taskFirst.status -ne 'VERIFIED_EXACT_CAPTURE_SINGLE_PASS' -or $taskOld.status -ne 'STOPPED_REQUIRES_INSPECTION' -or $taskDiagnostic.status -ne 'SINGLE_DIAGNOSTIC_PASS_PIN_SAIF_EQUALS_P1_EXCEPT_DATE') {
    throw 'Prerequisite receipts do not authorize this unchanged diagnostic retry'
}
$taskNative = $taskOld.native_commands[-1].command
$taskPython = $taskNative[0]
if ($taskNative.Count -ne 9 -or $taskNative[2] -ne 'asic/gls/saif_to_pins.py') { throw 'Unexpected failed conversion command' }
$taskArguments = @('-B', 'scripts/verification/run_gls_exact_window.py', '--design', 'DM', '--pass', '2', '--output', $taskOutput, '--freeze-proof', 'results/mapped_counter_freeze_checked_20261010/dm_p2.json', '--wait-for-memory', '--run')
foreach ($taskLibrary in $taskNative[6..8]) { $taskArguments += @('--liberty', $taskLibrary) }
if ($Resume) {
    $taskContinuation = 'results/gls_exact_dm_p2_continuation_20261012'
    $taskPlan = Get-Content -LiteralPath "$taskContinuation/plan.json" -Raw | ConvertFrom-Json
    if ($taskPlan.status -ne 'PREPARED_NOT_EXECUTED' -or $taskPlan.new_native_compilations -ne 0 -or
        (Get-FileHash -LiteralPath "$taskOutput/receipt.json" -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskPlan.stopped_receipt_sha256) {
        throw 'Continuation plan does not match the preserved stopped capture'
    }
    $taskArguments = @('-B', 'scripts/verification/resume_gls_exact_window.py', '--receipt', "$taskOutput/receipt.json", '--output', $taskContinuation, '--wait-for-memory', '--run')
}
if (-not $Run) {
    [pscustomobject]@{ status='PLAN_ONLY'; resume=$Resume.IsPresent; capture=$taskOutput; pair=$taskPair; power=$taskPower; preserved_failure=$taskFailed } | ConvertTo-Json
    return
}
if ($Resume) {
    $taskOldQueue = Get-Content -LiteralPath $taskQueue -Raw | ConvertFrom-Json
    if ($taskOldQueue.status -ne 'STOPPED_REQUIRES_INSPECTION' -or (Test-Path -LiteralPath "$taskContinuation/stopped_power_queue.json") -or (Test-Path -LiteralPath $taskPower)) {
        throw 'Refuse active, already resumed, or populated power artifacts'
    }
    [System.IO.File]::WriteAllBytes((Join-Path $taskRoot "$taskContinuation/stopped_power_queue.json"), [System.IO.File]::ReadAllBytes((Join-Path $taskRoot $taskQueue)))
} elseif ((Test-Path -LiteralPath $taskOutput) -or (Test-Path -LiteralPath $taskQueue) -or (Test-Path -LiteralPath $taskPower)) { throw 'Refuse existing retry artifacts' }
$taskRecord = [ordered]@{status='ENTERING_FRESH_SECOND_CAPTURE'; design='DM'; created_utc=[DateTime]::UtcNow.ToString('o'); original_failed_receipt=$taskFailed; diagnostic_receipt=$taskReplay; capture_receipts=@($taskP1, "$taskOutput/receipt.json"); pair_receipt=$taskPair; power_output=$taskPower}
if ($Resume) {
    $taskRecord.status='ENTERING_RESUMED_SECOND_CAPTURE'
    $taskRecord.continuation_evidence=$taskContinuation
    $taskRecord.preserved_native_commands=$taskPlan.preserved_native_commands
    $taskRecord.remaining_native_commands=$taskPlan.remaining_native_commands
}
function Save-TaskQueue { $taskRecord | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $taskQueue -Encoding utf8NoBOM }
Save-TaskQueue
try {
    & $taskPython @taskArguments
    if ($LASTEXITCODE -ne 0) { throw "Fresh capture exited $LASTEXITCODE; no paired STA launched" }
    $taskRecord.status='VERIFYING_CAPTURE_PAIR'; Save-TaskQueue
    & $taskPython -B scripts/verification/verify_gls_exact_pair.py --pass1 $taskP1 --pass2 "$taskOutput/receipt.json" --output $taskPair
    if ($LASTEXITCODE -ne 0) { throw 'Capture pair verification failed; no paired STA launched' }
    $taskRecord.status='WAITING_FOR_MEMORY_BEFORE_PAIRED_STA'; Save-TaskQueue
    while ([math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1024) -lt 7000) { Start-Sleep -Seconds 30 }
    $taskRecord.status='ENTERING_PAIRED_STA'; $taskRecord.sta_started_utc=[DateTime]::UtcNow.ToString('o'); Save-TaskQueue
    & $taskPython -B scripts/metrics/run_activity_power_exact.py --design DM --capture-pass1 $taskP1 --capture-pass2 "$taskOutput/receipt.json" --output $taskPower --run
    if ($LASTEXITCODE -ne 0) { throw "Power driver exited $LASTEXITCODE; inspect its receipt" }
    $taskRecord.status='PAIRED_STA_DRIVER_RETURNED_INSPECT_RECEIPT'
} catch {
    $taskRecord.status='STOPPED_REQUIRES_INSPECTION'; $taskRecord.error=$_.Exception.Message
    throw
} finally {
    $taskRecord.returned_utc=[DateTime]::UtcNow.ToString('o'); Save-TaskQueue
}
