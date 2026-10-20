# FLOW_JOURNAL Incident 89: rebuild the constrained LEC pair from the current proved constants
# (spec_c2.json = formal fixpoint) + RTL-justified duplicates (spec_manual.py) + one-hot groups,
# check the interfaces match, then random-simulate. usage: rebuild.ps1 <tag>
param([string]$Tag = "6")
Set-Location E:\Projects\RISCV-research\asic\equiv\lec
python spec_manual.py pairs.json spec_c2.json "spec_m$Tag.json" | Select-Object -Last 1
python mk_onehot_spec.py pairs.json "spec_m$Tag.json" "spec$Tag.json" | Out-Null
python evert.py cut gold_flat.il gold pairs.json "gold_lec$Tag.il" --spec "spec$Tag.json"
python evert.py cut gate_flat.il gate pairs.json "gate_lec$Tag.il" --spec "spec$Tag.json"
foreach ($n in "gold_lec$Tag", "gate_lec$Tag") { (Get-Content gold_god_aig.ys) -replace 'gold_god', $n | Set-Content -Encoding ascii "${n}_aig.ys" }
wsl.exe -d Ubuntu -e bash -c "cd /mnt/e/Projects/RISCV-research/asic/equiv/lec && for n in gold_lec$Tag gate_lec$Tag; do /nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys -q -l `${n}_aig.log `${n}_aig.ys > /dev/null 2>&1; echo `"`$n rc=`$?`"; done" | Select-String -NotMatch bogus
python aig_syms.py "gold_lec$Tag.aig" "gate_lec$Tag.aig"
python aigsim.py "gold_lec$Tag.aig" "gate_lec$Tag.aig" 16 4 | Out-File -Encoding ascii "sim$Tag.txt"
Get-Content "sim$Tag.txt" -TotalCount 1
