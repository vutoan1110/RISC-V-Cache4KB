# Undefined-value sensitivity of an LEC gold model (2026-10-13). In <Work>: A_gold.il (evert cut model of the gold side,
# flops cut, constants tied, one-hot restricted) and A_gold.aig (the LEC AIG built from it, the input reference).
#   x_free_aig.ys      every x constant bit and every undriven net becomes a new primary input -> A_gold_xf.aig
#   aig_tie_inputs.py  the same AIG with exactly those new inputs tied to 0 -> A_gold_xz.aig (same interface)
#   ABC &miter + &sat  every output UNSAT => it does not depend on any undefined value in any state
# -Neg: negative control in <Work>\neg: the next-state output lec_d_p00001 is driven by 1'x; a SAT output is required.
#   pwsh -File run_xsens.ps1 -Work <folder> [-Neg] [-Tag <name>]
# Windows Python runs pinned to ONE logical CPU (CPU 5): the start /affinity mask is HEXADECIMAL (20 = 0x20). Until
# 2026-10-14 the mask read 32 (= 0x32 = CPUs 1, 4, 5, two physical cores), not the intended single CPU. Earlier results
# stand: the DM passes are byte-identical except the 3-byte write timestamp ABC puts in the AIGER comment.
param([Parameter(Mandatory = $true)][string]$Work, [switch]$Neg, [string]$Tag = "p1")
$ErrorActionPreference = "Stop"
$LEC = "E:\Projects\RISCV-research\asic\equiv\lec"
$PY = "C:\Users\toanl\AppData\Local\Programs\Python\Python311\python.exe"
$Y = "/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys"
$ABC = "/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc"
$Work = (Resolve-Path $Work).Path
$Dir = if ($Neg) { Join-Path $Work "neg" } else { Join-Path $Work "xsens_$Tag" }
New-Item -ItemType Directory -Force $Dir | Out-Null
Set-Location $Dir
$W = "/mnt/" + $Dir.Substring(0, 1).ToLower() + ($Dir.Substring(2) -replace '\\', '/')
$src = Get-Content (Join-Path $Work "A_gold.il")
if ($Neg) {
    $i = [Array]::FindIndex($src, [Predicate[string]] { param($l) $l.StartsWith('  connect \lec_d_p00001 ') })
    if ($i -lt 0) { throw "no connect of lec_d_p00001" }
    "negative control: line $($i + 1) '$($src[$i].Trim())' -> '  connect \lec_d_p00001 1''x'" | Tee-Object -FilePath neg_note.txt
    $src[$i] = "  connect \lec_d_p00001 1'x"
}
$src | Set-Content -Encoding ascii A_gold.il
Copy-Item (Join-Path $Work "A_gold.aig") A_gold.aig -Force
Copy-Item "$LEC\x_free_aig.ys" x_free_aig.ys -Force
wsl.exe -d Ubuntu -e bash -c "cd $W && $Y -q -l x_free_aig.log x_free_aig.ys > /dev/null 2>&1; echo x_free_aig rc=`$?"
cmd /c "start /wait /b /affinity 20 `"`" `"$PY`" -B $LEC\aig_tie_inputs.py A_gold_xf.aig A_gold_xz.aig --ref A_gold.aig > xtie.log 2>&1"
Get-Content xtie.log
wsl.exe -d Ubuntu -e bash -c ("cd $W && $ABC -c '&r A_gold_xz.aig; &miter A_gold_xf.aig; &ps; &sat -a -z -C 2000 -v; &ps; &w xsens_a.aig' > xsens_a.log 2>&1; " +
    "$ABC -c '&r xsens_a.aig; &sat -a -z -C 200000 -v; &ps; &w xsens_b.aig' > xsens_b.log 2>&1; " +
    "grep -h -E 'Unsat calls|Sat   calls|Undef calls' xsens_a.log xsens_b.log; grep -a 'and =' xsens_b.log | tail -1")
cmd /c "start /wait /b /affinity 20 `"`" `"$PY`" -B $LEC\aig_outputs_zero.py xsens_b.aig > xzero.log 2>&1"
Get-Content xzero.log
