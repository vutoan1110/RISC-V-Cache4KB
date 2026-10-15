param([switch]$Execute)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
if ($projectRoot -ne 'E:\Projects\RISCV-research') { throw 'Unexpected workspace root' }
if (Get-Process -Name python,vsim,vopt,vlog -ErrorAction SilentlyContinue) { throw 'Possible simulation/coordinator reader still active' }
$auditDir = Join-Path $projectRoot 'results/workspace_audit'
$inventory = Get-Content -LiteralPath (Join-Path $auditDir 'inventory.json') -Raw | ConvertFrom-Json
$targets = @(Get-ChildItem -LiteralPath $projectRoot -Directory | Where-Object {
    $_.Name -in @('work','work_act4','work_asic','work_cprobe','work_glsp_dmuA',
      'work_glsp_sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1') -or
    $_.Name -match '^work_m2_[1-6]$' -or
    $_.Name -match '^work_board_reference_6c4ccffd_20261009_p[12]_c[0-3](_continued_20261009155010)?$'
})
if ($targets.Count -ne 22) { throw 'Expected the audited 22 simulator libraries' }
$rows = @()
foreach ($target in $targets) {
    $resolved = (Resolve-Path -LiteralPath $target.FullName).Path
    if ($resolved -ne (Join-Path $projectRoot $target.Name) -or $target.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Invalid cache target' }
    $entries = @(Get-ChildItem -LiteralPath $resolved -Force -Recurse)
    if (@($entries | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) { throw 'Reparse point inside cache' }
    $files = @($entries | Where-Object { -not $_.PSIsContainer })
    $bytes = ($files | Measure-Object Length -Sum).Sum
    $recorded = $inventory.folders.PSObject.Properties[$target.Name].Value
    if ($files.Count -ne $recorded.files -or $bytes -ne $recorded.bytes) { throw 'Cache changed since audit' }
    $rows += [ordered]@{path=$target.Name;resolved_absolute=$resolved;files=$files.Count;logical_bytes=$bytes}
}
if (-not $Execute) { Write-Output "PLAN ONLY: $($rows.Count) rebuildable simulator libraries"; return }
$receiptPath = Join-Path $auditDir 'cache_cleanup.json'
if (Test-Path -LiteralPath $receiptPath) { throw 'Receipt exists; inspect instead of repeating' }
$receipt = [ordered]@{status='IN_PROGRESS';started=(Get-Date).ToString('o');removed=@();logical_bytes_removed=0;
    evidence_preserved='16 board compile .do/.log artefacts, 200 case CSVs, raw test logs, ACT4 signatures, GLS SAIF/netlist/SPEF/power reports; none inside removed libraries'}
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receiptPath -Encoding utf8
$deletionLog = Join-Path $projectRoot 'results/cleanup_deleted.txt'
Add-Content -LiteralPath $deletionLog -Value "`n# $(Get-Date -Format 'yyyy-MM-dd HH:mm') 22 idle, rebuildable Questa libraries; raw compilation/result evidence retained" -Encoding utf8
foreach ($item in $rows) {
    Remove-Item -LiteralPath $item.resolved_absolute -Recurse -Force
    if (Test-Path -LiteralPath $item.resolved_absolute) { throw 'Incomplete cache removal' }
    $receipt.removed += $item
    $receipt.logical_bytes_removed += $item.logical_bytes
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receiptPath -Encoding utf8
    Add-Content -LiteralPath $deletionLog -Value "$($item.path)`t$($item.logical_bytes) logical bytes`tremoved compiled library; source and raw evidence retained" -Encoding utf8
}
$receipt.status='COMPLETE_22_SIMULATOR_CACHES_REMOVED'
$receipt | Add-Member -NotePropertyName completed -NotePropertyValue (Get-Date).ToString('o')
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receiptPath -Encoding utf8
Write-Output "COMPLETE $($rows.Count) caches, $($receipt.logical_bytes_removed) logical bytes"
