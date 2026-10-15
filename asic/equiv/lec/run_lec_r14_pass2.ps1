# Second, independent execution of the 16 KiB-RAM DM LEC (2026-10-09; double-execution rule): every input is
# regenerated (N1 replay, t1 replay, gold / N1 flattening), then step A, its multiplier closure and step B run again;
# the hashes of every proof object must equal pass 1 (r14_pass1/hashes.txt). Then a negative control of step B: one
# cell of the r14F_A netlist mutated (the first sky130_fd_sc_hd__and2_1 becomes an or2_1) must give a counterexample.
# Run with PowerShell 7 (pwsh).
$ErrorActionPreference = "Stop"
Set-Location E:\Projects\RISCV-research\asic\equiv\lec
$L = "/mnt/e/Projects/RISCV-research/asic/equiv/lec"
function Log([string]$m) { "$(Get-Date -Format s) R14p2 $m" | Add-Content runs.log; $m }
Log "pass 2 start"
# move pass-1 inputs aside so every one is rebuilt
New-Item -ItemType Directory -Force r14_pass1\inputs | Out-Null
foreach ($f in "n1_cut_r14.il", "n1_flat_r14.il", "gold_flat_r14.il", "..\sec\gold_pre_r14.il", "..\sec\gold_cut_r14.il") {
    if (Test-Path $f) { Move-Item -Force $f r14_pass1\inputs\ }
}
foreach ($d in "dm_r14F", "dm_r14F_t1") {
    if (Test-Path "synth_replay_r14\$d") { Move-Item -Force "synth_replay_r14\$d" "synth_replay_r14\${d}_pass1" }
}
wsl.exe -d Ubuntu -e bash -c "cd $L/synth_replay_r14 && bash run_replay_r14.sh soc_dm_4kb r14F_A dm_r14F && tail -1 runs.log"
& .\run_lec_r14.ps1 -Step A *> lecA_r14_p2.out
& .\build_pair.ps1 -Gold gold_flat_r14.il -Gate n1_flat_r14.il -Pairs pairsAR14.json -BaseSpec specAR14_c2.json -Tag AR14 *>> lecA_r14_p2.out
wsl.exe -d Ubuntu -e bash -c "cd $L && G=AR14_gold.aig H=AR14_gate.aig bash run_msat.sh AR14" *>> lecA_r14_p2.out
python open_outputs.py msatAR14_b.aig AR14_gold.aig pairsAR14.json --list > AR14_open.txt
& .\run_lec_r14_mul.ps1 *> lecAmul_r14_p2.out
& .\run_lec_r14.ps1 -Step B *> lecB_r14_p2.out
# compare every proof object with pass 1
$diff = 0
foreach ($line in Get-Content r14_pass1\hashes.txt) {
    $h, $f = $line -split ' \*', 2
    $f = $f.Trim()
    if (-not (Test-Path $f)) { "MISSING $f"; $diff++; continue }
    $n = (Get-FileHash -Algorithm SHA256 $f).Hash.ToLower()
    if ($n -ne $h) { "DIFFERS $f"; $diff++ } else { "same    $f" }
}
foreach ($d in "dm_r14F", "dm_r14F_t1") {
    foreach ($f in "n1_pre_abc_fast.il", "t1_iter1.il") {
        $a = "synth_replay_r14\${d}_pass1\$f"; $b = "synth_replay_r14\$d\$f"
        if ((Test-Path $a) -and (Test-Path $b)) {
            $same = (Get-FileHash $a).Hash -eq (Get-FileHash $b).Hash
            "$(if ($same) {'same   '} else {'DIFFERS'}) $b"; if (-not $same) { $diff++ }
        }
    }
}
Log "pass 2 hash comparison: $diff difference(s)"
# negative control of step B: mutated r14F_A netlist
$src = "..\..\soc_dm_4kb\runs\r14F_A\55-openroad-fillinsertion\soc_asic_top.nl.v"
$neg = "r14_neg\soc_asic_top_mut.nl.v"
New-Item -ItemType Directory -Force r14_neg | Out-Null
$t = Get-Content $src -Raw
$i = $t.IndexOf("sky130_fd_sc_hd__and2_1 ")
if ($i -lt 0) { throw "no and2_1 cell to mutate" }
($t.Substring(0, $i) + "sky130_fd_sc_hd__or2_1 " + $t.Substring($i + "sky130_fd_sc_hd__and2_1 ".Length)) | Set-Content -NoNewline -Encoding ascii $neg
Log "negative control: first and2_1 of r14F_A turned into or2_1 ($neg)"
$fe = (Get-Content ..\sec\gate_front_end.ys) -replace '/mnt/e/Projects/RISCV-research/results/pd_run_archive/final_B/dependency_inputs/54-openroad-fillinsertion/soc_asic_top.nl.v', "$L/r14_neg/soc_asic_top_mut.nl.v"
$fe | Set-Content -Encoding ascii ..\sec\gate_front_end_R14NEG.ys
(Get-Content ..\sec\gate_pre.ys) -replace 'script gate_front_end.ys', "script gate_front_end_R14NEG.ys" -replace 'write_ilang gate_pre.il', "write_ilang gate_pre_R14NEG.il" | Set-Content -Encoding ascii ..\sec\gate_pre_R14NEG.ys
wsl.exe -d Ubuntu -e bash -c "cd /mnt/e/Projects/RISCV-research/asic/equiv/sec && /nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys -q -l gate_pre_R14NEG.log gate_pre_R14NEG.ys > /dev/null 2>&1; echo gate_pre rc=`$?"
python ..\sec\sram_cut.py ..\sec\gate_pre_R14NEG.il ..\sec\gate_cut_R14NEG.il | Select-Object -Last 1
(Get-Content gate_flat.ys) -replace '\.\./sec/gate_cut\.il', "../sec/gate_cut_R14NEG.il" -replace 'write_ilang gate_flat\.il', "write_ilang gate_flat_R14NEG.il" | Set-Content -Encoding ascii gate_flat_R14NEG.ys
wsl.exe -d Ubuntu -e bash -c "cd $L && /nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys -q -l gate_flat_R14NEG.log gate_flat_R14NEG.ys > /dev/null 2>&1; echo gate_flat rc=`$?"
python evert.py pair n1_flat_r14.il gate_flat_R14NEG.il pairsB_R14NEG.json | Select-Object -Last 2
python -c "import json,sys; P=json.load(open(sys.argv[1])); json.dump({'const': {}, 'dup': {}, 'free': list(range(len(P['gold_only'])))}, open(sys.argv[2], 'w'))" pairsB_R14NEG.json specB_R14NEG_base.json
& .\build_pair.ps1 -Gold n1_flat_r14.il -Gate gate_flat_R14NEG.il -Pairs pairsB_R14NEG.json -BaseSpec specB_R14NEG_base.json -Tag BR14NEG
wsl.exe -d Ubuntu -e bash -c "cd $L && G=BR14NEG_gold.aig H=BR14NEG_gate.aig bash run_msat.sh BR14NEG"
Log "pass 2 and negative control end"
