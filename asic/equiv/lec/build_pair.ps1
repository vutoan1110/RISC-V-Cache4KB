# FLOW_JOURNAL Incident 89: build one register-mapped LEC pair (generic over the two sides).
#   -Gold / -Gate : *_flat.il of the two sides; -Pairs : pairs json from `evert.py pair`
#   -BaseSpec     : spec with the proved constants (or an empty one); manual RTL-justified duplicates
#                   (spec_manual.py) and the one-hot FSM groups (mk_onehot_spec.py) are added here.
# Writes <Tag>_gold.aig / <Tag>_gate.aig, checks the interfaces match, random-simulates.
param([string]$Gold, [string]$Gate, [string]$Pairs, [string]$BaseSpec, [string]$Tag)
Set-Location E:\Projects\RISCV-research\asic\equiv\lec
python spec_manual.py $Pairs $BaseSpec "${Tag}_specm.json" | Select-Object -Last 1
python mk_onehot_spec.py $Pairs "${Tag}_specm.json" "${Tag}_spec.json"
python evert.py cut $Gold gold $Pairs "${Tag}_gold.il" --spec "${Tag}_spec.json"
python evert.py cut $Gate gate $Pairs "${Tag}_gate.il" --spec "${Tag}_spec.json"
foreach ($n in "${Tag}_gold", "${Tag}_gate") { (Get-Content gold_god_aig.ys) -replace 'gold_god', $n | Set-Content -Encoding ascii "${n}_aig.ys" }
wsl.exe -d Ubuntu -e bash -c "cd /mnt/e/Projects/RISCV-research/asic/equiv/lec && for n in ${Tag}_gold ${Tag}_gate; do /nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys -q -l `${n}_aig.log `${n}_aig.ys > /dev/null 2>&1; echo `"`$n rc=`$?`"; done" | Select-String -NotMatch bogus
python aig_syms.py "${Tag}_gold.aig" "${Tag}_gate.aig"
python aigsim.py "${Tag}_gold.aig" "${Tag}_gate.aig" 16 4 | Out-File -Encoding ascii "${Tag}_sim.txt"
Get-Content "${Tag}_sim.txt" -TotalCount 1
