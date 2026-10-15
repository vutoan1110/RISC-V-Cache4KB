param([switch]$Execute)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
if ($projectRoot -ne 'E:\Projects\RISCV-research') { throw 'Unexpected workspace root' }
$auditDir = Join-Path $projectRoot 'results/workspace_audit'
$preflight = Get-Content -LiteralPath (Join-Path $auditDir 'cleanup_preflight.json') -Raw | ConvertFrom-Json
if ($preflight.status -ne 'ARCHIVES_VERIFIED_NO_DELETION' -or $preflight.plans.Count -ne 19) { throw 'Unexpected preflight' }
$retainedTags = @('final_B', 'vc4_corr3400x3400_f220_capm20_antoff_rsztf_nogrtt_clkm3_pad1_r1')
$plans = @($preflight.plans | Where-Object { (Split-Path $_.path -Leaf) -notin $retainedTags })
if ($plans.Count -ne 17) { throw 'Expected exactly 17 dependency-free archived runs' }
$receiptPath = Join-Path $auditDir 'cleanup_execution.json'
if (Test-Path -LiteralPath $receiptPath) { throw 'Execution receipt exists; inspect instead of repeating' }
# Validate all resolved targets and their current sizes before any removal.
foreach ($item in $plans) {
    $target = (Resolve-Path -LiteralPath (Join-Path $projectRoot $item.path)).Path
    $expected = Join-Path $projectRoot ($item.path -replace '/', '\')
    if ($target -ne $expected -or $target -ne $item.resolved_absolute) { throw "Resolved target differs: $target" }
    if ($target -notmatch '^E:\\Projects\\RISCV-research\\asic\\soc_(dm|sa2|vc4)_4kb\\runs\\[^\\]+$') { throw "Target escapes named run directories: $target" }
    if ($item.dependent_retained_states.Count -ne 0) { throw 'Retained state dependency' }
    $archive = Join-Path $projectRoot $item.archive
    if ((Get-FileHash -LiteralPath (Join-Path $archive 'archive_manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.archive_manifest_sha256) { throw 'Archive manifest changed' }
    $entries = @(Get-ChildItem -LiteralPath $target -Force -Recurse)
    if (@($entries | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) { throw 'Reparse point in target' }
    $files = @($entries | Where-Object { -not $_.PSIsContainer })
    $bytes = ($files | Measure-Object -Property Length -Sum).Sum
    if ($files.Count -ne $item.files -or $bytes -ne $item.logical_bytes) { throw "Source changed since preflight: $target" }
    Write-Output "VERIFIED $target ($bytes logical bytes)"
}
if (-not $Execute) { Write-Output 'PLAN ONLY: 17 archived runs, no deletion'; return }
if (Get-Process -Name wsl,openroad,yosys,magic,netgen,klayout -ErrorAction SilentlyContinue) { throw 'Possible ASIC job active; inspect before deleting' }
$receipt = [ordered]@{
    status = 'IN_PROGRESS'
    started = (Get-Date).ToString('o')
    authorization = 'Explicit project-owner request: audit then clean obsolete folders, 2026-10-09'
    archived_evidence_preserved = $true
    removed = @()
    retained_dependencies = $retainedTags
    logical_bytes_removed = 0
}
$receipt | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $receiptPath -Encoding utf8
$deletionLog = Join-Path $projectRoot 'results/cleanup_deleted.txt'
Add-Content -LiteralPath $deletionLog -Value "`n# $(Get-Date -Format 'yyyy-MM-dd HH:mm') workspace audit cleanup: source/archive hashes verified; 17 obsolete runs; final_B and VC4 pad1 source retained for real dependencies" -Encoding utf8
foreach ($item in $plans) {
    $target = $item.resolved_absolute
    Remove-Item -LiteralPath $target -Recurse -Force
    if (Test-Path -LiteralPath $target) { throw "Removal incomplete: $target" }
    $receipt.removed += [ordered]@{
        path = $item.path
        logical_bytes = $item.logical_bytes
        file_count = $item.files
        archive = $item.archive
        archive_manifest_sha256 = $item.archive_manifest_sha256
        completed = (Get-Date).ToString('o')
    }
    $receipt.logical_bytes_removed += $item.logical_bytes
    $receipt | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $receiptPath -Encoding utf8
    Add-Content -LiteralPath $deletionLog -Value "$($item.path)`t$($item.logical_bytes) logical bytes`tdeleted; evidence $($item.archive)" -Encoding utf8
    Write-Output "DELETED $($item.path)"
}
$receipt.status = 'COMPLETE_17_ARCHIVED_RUNS_REMOVED'
$receipt.completed = (Get-Date).ToString('o')
$receipt | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $receiptPath -Encoding utf8
Write-Output "COMPLETE $($receipt.removed.Count) runs, $($receipt.logical_bytes_removed) logical bytes"
