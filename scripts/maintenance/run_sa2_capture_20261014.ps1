# Exact-window GLS capture pair of the signed SA2 layout (ecomaxmin, 11.56 mm2), 2026-10-14: two independent passes in
# fresh folders with private libraries (scripts/verification/run_gls_exact_window.py), then the pair check
# (verify_gls_exact_pair.py). The paired STA power phase (run_activity_power_exact.py, WSL OpenSTA) is a PLANNED separate
# step, started only when no detailed route is running (P4 beside a DRT already exhausted the 24 GB WSL VM once).
# Rule Q: a failed step ends this chain; a retry is a new full pass in a new folder, never a continuation.
# Windows Python runs pinned to ONE logical CPU at creation (CPU 8: start /affinity takes HEX, 100 = 0x100); vsim and
# saif_to_pins inherit the pin. Plain `cmd /c start /wait` returns 0 whatever the child does, so the exit code is taken
# with delayed expansion (cmd /v:on ... & exit !ERRORLEVEL!).
#   pwsh -NoProfile -File scripts/maintenance/run_sa2_capture_20261014.ps1 [-Run]
# Cooperative stop: create <pass folder>\abort_before_next_native (honoured before the next native tool).
[CmdletBinding()]
param([switch]$Run)
$ErrorActionPreference = 'Stop'
$Root = 'E:\Projects\RISCV-research'
Set-Location -LiteralPath $Root
$PY = 'C:\Users\toanl\AppData\Local\Programs\Python\Python311\python.exe'
$Libs = @(
    '\\wsl.localhost\Ubuntu\home\toanl\.volare\volare\sky130\versions\0fe599b2afb6708d281543108caf8310912f54af\sky130A\libs.ref\sky130_fd_sc_hd\lib\sky130_fd_sc_hd__tt_025C_1v80.lib',
    'E:\Projects\RISCV-research\asic\soc_dm_4kb\macros\lib\sky130_sram_1kbyte_1rw1r_32x256_8_TT_1p8V_25C.lib',
    'E:\Projects\RISCV-research\asic\soc_dm_4kb\macros\lib\sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib')
$Pass = [ordered]@{ '1' = 'results/gls_exact_sa2_full_p1_20261014'; '2' = 'results/gls_exact_sa2_full_p2_20261014' }
$Proof = [ordered]@{ '1' = 'results/mapped_counter_freeze_checked_20261010/sa2_p1.json'; '2' = 'results/mapped_counter_freeze_checked_20261010/sa2_p2.json' }
$PairOut = 'results/gls_exact_sa2_full_pair_20261014.json'
$Queue = 'results/exact_capture_queue_sa2_20261014.json'
$Logs = 'results/exact_capture_queue_sa2_20261014_logs'

function PinnedPy([string[]]$ArgList, [string]$Log) {
    $q = ($ArgList | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }) -join ' '
    cmd /v:on /c "start /wait /b /affinity 100 `"`" `"$PY`" -B $q > `"$Log`" 2>&1 & exit !ERRORLEVEL!"
    return $LASTEXITCODE
}
function Status([string]$receipt) { (Get-Content -LiteralPath $receipt -Raw | ConvertFrom-Json).status }

foreach ($p in $Pass.Values + @($PairOut, $Queue, $Logs)) {
    if (Test-Path -LiteralPath $p) { throw "Refuse existing artifact $p (a retry needs new names)" }
}
foreach ($p in $Proof.Values + $Libs) { if (-not (Test-Path -LiteralPath $p)) { throw "Missing input $p" } }
if (-not $Run) {
    [pscustomobject]@{ status = 'PLAN_ONLY'; passes = $Pass; proofs = $Proof; pair = $PairOut; queue = $Queue } | ConvertTo-Json
    return
}
New-Item -ItemType Directory $Logs | Out-Null
$rec = [ordered]@{ status = 'RUNNING'; design = 'SA2'; created_utc = [DateTime]::UtcNow.ToString('o')
    PD_tag = 'sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1'; pinned_cpu_hex_mask = '100'
    passes = $Pass; pair = $PairOut; steps = @() }
function Save { $rec | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $Queue -Encoding utf8NoBOM }
function Step([string]$name, [string[]]$ArgList, [string]$receipt, [string]$want) {
    $log = Join-Path $Logs "$name.log"
    $s = [ordered]@{ name = $name; started_utc = [DateTime]::UtcNow.ToString('o'); log = $log }
    $rec.steps += $s; Save
    $rc = PinnedPy $ArgList $log
    $s.exit = $rc; $s.completed_utc = [DateTime]::UtcNow.ToString('o')
    $s.receipt_status = if (Test-Path -LiteralPath $receipt) { Status $receipt } else { 'MISSING' }
    Save
    if ($rc -ne 0 -or $s.receipt_status -ne $want) {
        $rec.status = 'STOPPED_FAILED_STEP_NO_CONTINUATION'; $rec.failed_step = $name; Save
        throw "$name failed (exit $rc, receipt $($s.receipt_status)); chain ends (rule Q)"
    }
}
foreach ($n in 1, 2) {
    $a = @('scripts/verification/run_gls_exact_window.py', '--design', 'SA2', '--pass', "$n", '--output', $Pass["$n"],
        '--freeze-proof', $Proof["$n"], '--wait-for-memory', '--run')
    foreach ($l in $Libs) { $a += @('--liberty', $l) }
    Step "capture_p$n" $a "$($Pass["$n"])/receipt.json" 'VERIFIED_EXACT_CAPTURE_SINGLE_PASS'
}
Step 'pair' @('scripts/verification/verify_gls_exact_pair.py', '--pass1', "$($Pass["1"])/receipt.json",
    '--pass2', "$($Pass["2"])/receipt.json", '--output', $PairOut) $PairOut 'VERIFIED_TWO_INDEPENDENT_EXACT_GLS_CAPTURES'
$rec.status = 'CAPTURE_PAIR_VERIFIED_POWER_PHASE_PENDING'; $rec.returned_utc = [DateTime]::UtcNow.ToString('o'); Save
'CAPTURE_PAIR_VERIFIED_POWER_PHASE_PENDING'
