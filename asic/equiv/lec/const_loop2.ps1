# FLOW_JOURNAL Incident 89: generic greatest-fixpoint FORMAL proof of the gold-only constant flops
# (const_loop.ps1 with the sides as parameters). -Gold: gold *_flat.il, -Pairs: pairs json,
# -Spec: starting spec (from `const_check.py analyze`), -Prefix: file prefix for this run.
param([string]$Gold, [string]$Pairs, [string]$Spec, [string]$Prefix)
Set-Location E:\Projects\RISCV-research\asic\equiv\lec
$cur = $Spec
for ($r = 1; $r -le 12; $r++) {
    if ((Get-Content $cur -Raw | ConvertFrom-Json).const.PSObject.Properties.Count -eq 0) { "FIXPOINT (no constants left) -> $cur"; break }
    python evert.py cut $Gold gold $Pairs "${Prefix}_tied.il" --spec $cur --gold-only-d | Out-Null
    (Get-Content gold_god_aig.ys) -replace 'gold_god', "${Prefix}_tied" | Set-Content -Encoding ascii "${Prefix}_tied_aig.ys"
    wsl.exe -d Ubuntu -e bash -c "cd /mnt/e/Projects/RISCV-research/asic/equiv/lec && /nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys -q -l ${Prefix}_tied_aig.log ${Prefix}_tied_aig.ys > /dev/null 2>&1; echo yosys rc=`$?" | Select-String -NotMatch bogus
    python const_check.py mkproof "${Prefix}_tied.aig" $cur "${Prefix}_proof.aig"
    wsl.exe -d Ubuntu -e bash -c "cd /mnt/e/Projects/RISCV-research/asic/equiv/lec && /nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc -c '&r ${Prefix}_proof.aig; &sat -a -z -C 1000000; &w ${Prefix}_proof_sat.aig' > ${Prefix}_sat_r$r.log 2>&1" | Select-String -NotMatch bogus
    $next = "${Prefix}_c$r.json"
    $o = python const_check.py prune "${Prefix}_proof_sat.aig" $cur $next
    $o
    $cur = $next
    if ($o -match "NOT proved 0 ") { "FIXPOINT after round $r -> $cur"; break }
}
