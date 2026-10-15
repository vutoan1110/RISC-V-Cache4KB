# Structural audit of the asynchronous resets (arst_audit.py), 2026-10-13: the register-mapped LEC runs on async2sync
# models, so this closes the "reset asserted between clock edges" premise on the pre-async2sync models.
# For every listed pair (gold model : gate model : label) the audit runs twice (pinned Windows Python, QUY_TRINH B) and
# both JSON reports must be byte-identical. Negative controls on a copy of the gold model: one ARST_VALUE bit flipped,
# and one ARST input moved from reset_sync_q to reset_n; each must FAIL against the first gate model.
#   pwsh -File run_arst_audit.ps1 -Out <folder> -Pairs "<gold.il>|<gate.il>|<label>;<gold.il>|<gate.il>|<label>;..."
param([Parameter(Mandatory = $true)][string]$Out, [Parameter(Mandatory = $true)][string]$Pairs)
$Pair = @($Pairs -split ';' | Where-Object { $_.Trim() })
$ErrorActionPreference = "Stop"
$PY = "C:\Users\toanl\AppData\Local\Programs\Python\Python311\python.exe"
$A = "E:\Projects\RISCV-research\asic\equiv\lec\arst_audit.py"
New-Item -ItemType Directory -Force $Out | Out-Null
function Audit([string]$gold, [string]$gate, [string]$tag) {
    cmd /c "start /wait /b /affinity 8 `"`" `"$PY`" -B $A $gold $gate $Out\$tag.json > $Out\$tag.log 2>&1"
    $v = (Get-Content "$Out\$tag.log" | Select-String '^verdict:') -replace 'verdict: ', ''
    $mm = (Get-Content "$Out\$tag.log" | Select-String '^mismatches:') -replace 'mismatches: ', ''
    "{0,-34} verdict {1,-4} mismatches {2}" -f $tag, $v, $mm
}
$rows = @()
foreach ($p in $Pair) {
    $gold, $gate, $label = $p -split '\|'
    foreach ($r in 1, 2) { $rows += Audit $gold $gate "${label}_r$r" }
    $h1 = (Get-FileHash "$Out\${label}_r1.json").Hash; $h2 = (Get-FileHash "$Out\${label}_r2.json").Hash
    $rows += "{0,-34} pass1 = pass2: {1}" -f $label, ($h1 -eq $h2)
}
# negative controls on the first pair's gold model
$gold0, $gate0, $label0 = $Pair[0] -split '\|'
$src = Get-Content $gold0
$i = [Array]::FindIndex($src, [Predicate[string]] { param($l) $l -match "^    parameter \\ARST_VALUE \d+'[01]+$" })
if ($i -lt 0) { throw "no ARST_VALUE parameter to mutate" }
$m = [regex]::Match($src[$i], "(\d+)'([01]+)$")
$bits = $m.Groups[2].Value.ToCharArray(); $bits[-1] = if ($bits[-1] -eq '0') { '1' } else { '0' }
$neg1 = $src.Clone(); $neg1[$i] = $src[$i].Substring(0, $m.Index) + $m.Groups[1].Value + "'" + (-join $bits)
$neg1 | Set-Content -Encoding ascii "$Out\neg_arst_value_gold.il"
$rows += "negative control 1: line $($i + 1) '$($src[$i].Trim())' -> '$($neg1[$i].Trim())'"
$rows += Audit "$Out\neg_arst_value_gold.il" $gate0 "neg_arst_value"
$j = [Array]::FindIndex($src, [Predicate[string]] { param($l) $l -eq '    connect \ARST \reset_sync_q' })
if ($j -lt 0) { throw "no ARST connect to reset_sync_q to mutate" }
$neg2 = $src.Clone(); $neg2[$j] = '    connect \ARST \reset_n'
$neg2 | Set-Content -Encoding ascii "$Out\neg_arst_root_gold.il"
$rows += "negative control 2: line $($j + 1) ARST reset_sync_q -> reset_n"
$rows += Audit "$Out\neg_arst_root_gold.il" $gate0 "neg_arst_root"
$rows | Tee-Object -FilePath "$Out\summary.txt"
