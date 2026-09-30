<#
.SYNOPSIS
    Run the core UVM environment with QuestaSim, one vsim process per test.

.EXAMPLE
    powershell -File verification/uvm/run_uvm.ps1
    powershell -File verification/uvm/run_uvm.ps1 -Test core_smoke_test -Seed 7
    powershell -File verification/uvm/run_uvm.ps1 -All
    powershell -File verification/uvm/run_uvm.ps1 -Test core_random_test -Seeds 20
    powershell -File verification/uvm/run_uvm.ps1 -Test core_smoke_test -NoCompile

.NOTES
    Exit code 0 only when every requested test wrote PASS into
    verification/uvm/out/<test>.status.
#>
[CmdletBinding()]
param(
    [string]   $Test      = 'core_smoke_test',
    [int]      $Seed      = 1,
    [int]      $Seeds     = 1,
    [switch]   $All,
    [switch]   $NoCompile,
    [string]   $Vsim      = 'C:/questasim64_2024.1/win64/vsim.exe'
)

$ErrorActionPreference = 'Stop'

# The script lives in <root>/verification/uvm.
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
Push-Location $root

# Every test class the environment can run. Add new ones here.
$allTests = @('core_smoke_test', 'core_random_test',
              'axi_smoke_test', 'axi_stress_test',
              'soc_directed_test', 'soc_periph_test')
$tests    = if ($All) { $allTests } else { @($Test) }

# One job per (test, seed). Only the random test benefits from extra seeds;
# the directed tests are deterministic, so they run once.
$jobs = @()
foreach ($t in $tests) {
    if ($t -eq 'core_random_test' -and $Seeds -gt 1) {
        foreach ($s in 1..$Seeds) { $jobs += ,@($t, $s) }
    }
    else {
        $jobs += ,@($t, $Seed)
    }
}

if (-not (Test-Path $Vsim)) {
    Write-Error "QuestaSim not found at $Vsim. Pass -Vsim <path to vsim.exe>."
}

$failed  = @()
# Compile once, then reuse work/ for the remaining tests.
$compile = if ($NoCompile) { 0 } else { 1 }

foreach ($job in $jobs) {
    $t = $job[0]
    $s = $job[1]
    Write-Host "=== $t (seed $s, compile=$compile) ==="
    & $Vsim -c -do "do verification/uvm/run_uvm.do $t $compile $s"
    $rc = $LASTEXITCODE
    $compile = 0

    $statusFile = Join-Path $root "verification/uvm/out/$t.status"
    $verdict = if (Test-Path $statusFile) { (Get-Content $statusFile -Raw).Trim() }
               else { 'MISSING' }
    Write-Host "$t seed $s -> $verdict (vsim exit $rc)"

    if ($rc -ne 0 -or -not $verdict.StartsWith('PASS')) { $failed += "$t(seed $s)" }
}

# Merge the per-test UCDBs into one functional coverage picture.
$ucdbs = Get-ChildItem -Path (Join-Path $root 'verification/uvm/out') -Filter '*.ucdb' -ErrorAction SilentlyContinue
if ($ucdbs -and $ucdbs.Count -gt 0) {
    $vcover = Join-Path (Split-Path $Vsim) 'vcover.exe'
    $merged = Join-Path $root 'verification/uvm/out/merged.ucdb'
    $report = Join-Path $root 'verification/uvm/out/coverage_summary.txt'
    if (Test-Path $vcover) {
        & $vcover merge -out $merged ($ucdbs | ForEach-Object { $_.FullName }) | Out-Null
        & $vcover report -details -output $report $merged | Out-Null
        Write-Host "[INFO] merged functional coverage from $($ucdbs.Count) run(s) -> $report"
    }
}

Pop-Location

if ($failed.Count -gt 0) {
    Write-Host "[FAIL] UVM regression: $($failed -join ', ')"
    exit 1
}
Write-Host "[PASS] UVM regression: $($jobs.Count) run(s)"
exit 0
