param(
    [Parameter(Mandatory)][ValidateRange(1,100)][int]$Case,
    [Parameter(Mandatory)][ValidateRange(1,2)][int]$Pass,
    [ValidatePattern('^\d{8}$')][string]$SessionDate = '20261012',
    [ValidatePattern('^\d{8}$')][string]$MeasurementDate,
    [switch]$Program
)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$images = Join-Path $projectRoot 'output_files_board_matrix_6c4ccffd_seed2'
$session = Join-Path $projectRoot "results/board_$SessionDate"
$actualMeasurementDate = if ($MeasurementDate) { $MeasurementDate } else { $SessionDate }
$scheduledPasses = @(1, 2)
if (Test-Path -LiteralPath (Join-Path $session 'session.json')) {
    $sessionState = Get-Content -Raw -LiteralPath (Join-Path $session 'session.json') | ConvertFrom-Json
    if ($sessionState.PSObject.Properties.Name -contains 'scheduled_passes') { $scheduledPasses = @($sessionState.scheduled_passes) }
}
if ($actualMeasurementDate -ne $SessionDate -and
    (!$sessionState -or $actualMeasurementDate -notin @($sessionState.measurement_dates_approved))) {
    throw 'Measurement date is not approved for this continuing session'
}
if ($Pass -notin $scheduledPasses) { throw "Pass $Pass is not scheduled for this board session" }
$index = @(Import-Csv -LiteralPath (Join-Path $images 'INDEX.csv'))
$state = Get-Content -Raw -LiteralPath (Join-Path $images 'BUILD_STATE.json') | ConvertFrom-Json
$manifest = Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'results/rtl_manifest.json') | ConvertFrom-Json
if ($index.Count -ne 100 -or $state.state -ne 'READY_FOR_PHYSICAL_SESSION' -or
    $state.common_seed -ne 2 -or $state.canonical_restoration -ne 'PASS' -or
    $state.rtl_id -ne $manifest.aggregate) { throw 'Board build is not ready on current RTL/seed2' }
$row = $index[$Case-1]
if ($row.fit_seed -ne '2' -or $row.rtl_aggregate -ne $manifest.aggregate) { throw 'Wrong seed or RTL' }
$sof = Join-Path $images $row.sof
$firmware = Join-Path $projectRoot $row.fw
if ((Get-FileHash -LiteralPath $sof -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256 -or
    (Get-FileHash -LiteralPath $firmware -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.fw_sha256) {
    throw 'SOF/firmware hash differs from the verified index'
}
$manifestCheck = (& python (Join-Path $projectRoot 'scripts/rtl_manifest.py') --check 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0) { throw "RTL manifest check failed: $manifestCheck" }
$prefix = "p${Pass}_$($row.kernel)_$($row.config)"
Write-Host "Case $Case/100, pass ${Pass}: $($row.kernel), $($row.config), common seed2"
Write-Host "Expected LEDR=A5, HEX=$($row.expected_mcycle_hex), MINSTRET=$($row.expected_minstret_hex)"
Write-Host "Open Hercules and log to: $session/uart/$prefix.uart.log BEFORE programming"
Write-Host "SOF: $sof; SHA256: $($row.sha256)"
if (!$Program) { Write-Host 'PLAN ONLY: no JTAG operation performed'; return }
if ((Get-Date).ToString('yyyyMMdd') -ne $actualMeasurementDate) { throw 'Programming date differs from the declared measurement date' }
if (Get-Process -Name quartus_pgm,quartus_fit,quartus_map,quartus_asm,quartus_cdb -ErrorAction SilentlyContinue) {
    throw 'Another Quartus programming/build process is active'
}
$quartusRoot = if ($env:QUARTUS_ROOTDIR) { $env:QUARTUS_ROOTDIR } else { 'D:/altera/quartus' }
$programmer = Join-Path $quartusRoot 'bin64/quartus_pgm.exe'
if (!(Test-Path -LiteralPath $programmer)) { throw 'Quartus programmer not found' }
$folder = Join-Path $session 'programming'
New-Item -ItemType Directory -Path $folder -Force | Out-Null
$attempt = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
$log = Join-Path $folder "$prefix.$attempt.log"
$record = [ordered]@{status='PROGRAMMING_NOT_A_MEASUREMENT';case=$Case;pass=$Pass;kernel=$row.kernel;
    session_date=$SessionDate;measurement_date=$actualMeasurementDate;
    config=$row.config;fit_seed=2;rtl_aggregate=$manifest.aggregate;sof=$sof;sof_sha256=$row.sha256;
    firmware_sha256=$row.fw_sha256;programmer=$programmer;started=(Get-Date).ToString('o');log=$log}
& $programmer -c 'USB-Blaster' -m 'JTAG' -o "p;$sof" 2>&1 | Tee-Object -FilePath $log
$nativeExit = $LASTEXITCODE
$record.native_exit = $nativeExit
$record.completed = (Get-Date).ToString('o')
$record.status = if ($nativeExit -eq 0) { 'PROGRAMMED_ONLY_NOT_BOARD_PASS' } else { 'PROGRAMMING_FAILED' }
$record | ConvertTo-Json | Set-Content -LiteralPath "$log.json" -Encoding utf8NoBOM
if ($nativeExit -ne 0) { throw "JTAG failed (exit $nativeExit); evidence retained, no automatic retry" }
Write-Host 'Wait for UART DONE and final LEDR/HEX, then preserve the log/photo and check the UART capture.'
