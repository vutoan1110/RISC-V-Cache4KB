# FLOW_JOURNAL Incident 89: greatest-fixpoint FORMAL proof of the gold-only constant flops.
# Each round: tie the current const set (and dups), expose gold-only D, build proof miter
# (D xor value per const flop), ABC &sat -a -z per output, demote every flop not proved.
# Stops when a round demotes nothing: then every remaining const flop is proved constant given
# that all of them are (induction), and their reset values equal the constants (analyze step).
param([string]$Spec = "spec3.json")
Set-Location E:\Projects\RISCV-research\asic\equiv\lec
$cur = $Spec
for ($r = 1; $r -le 12; $r++) {
    python evert.py cut gold_flat.il gold pairs.json cl_tied.il --spec $cur --gold-only-d | Out-Null
    (Get-Content gold_god_aig.ys) -replace 'gold_god', 'cl_tied' | Set-Content -Encoding ascii cl_tied_aig.ys
    wsl.exe -d Ubuntu -e bash -c "cd /mnt/e/Projects/RISCV-research/asic/equiv/lec && /nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys -q -l cl_tied_aig.log cl_tied_aig.ys > /dev/null 2>&1; echo yosys rc=`$?" | Select-String -NotMatch bogus
    python const_check.py mkproof cl_tied.aig $cur cl_proof.aig
    wsl.exe -d Ubuntu -e bash -c "cd /mnt/e/Projects/RISCV-research/asic/equiv/lec && /nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc -c '&r cl_proof.aig; &sat -a -z -C 1000000; &w cl_proof_sat.aig' > cl_sat_r$r.log 2>&1; tail -n 3 cl_sat_r$r.log" | Select-String -NotMatch bogus
    $next = "spec_c$r.json"
    $o = python const_check.py prune cl_proof_sat.aig $cur $next
    $o
    $cur = $next
    if ($o -match "NOT proved 0 ") { "FIXPOINT after round $r -> $cur"; break }
}
