# FLOW_JOURNAL Incident 91: step B of the equivalence chain (N1 == N3) for a NEW final netlist of the same
# synthesis (a PD-only change: N1, the synthesis state before `abc -fast`, is unchanged, so step A
# RTL+fsm == N1 still holds and only N1 == new N3 must be proved).
#   -Tag   : short tag for file names (e.g. F2A)
#   -Net   : WSL path of the new final netlist (<run>/NN-openroad-fillinsertion/soc_asic_top.nl.v)
# Steps: (1) N1: byte-exact synthesis replay -> sram_cut -> n1_flat (skipped if n1_flat.il exists);
# (2) gate: EQY-style front end on the new netlist -> sram_cut -> flat; (3) evert pair; (4) build_pair
# (cut + spec + AIG); (5) per-output SAT (run_msat.sh); (6) &cec of the residual outputs.
param([string]$Tag, [string]$Net)
$ErrorActionPreference = "Stop"
Set-Location E:\Projects\RISCV-research\asic\equiv\lec
$Y = "/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys"
$L = "/mnt/e/Projects/RISCV-research/asic/equiv/lec"
$S = "/mnt/e/Projects/RISCV-research/asic/equiv/sec"
"$(Get-Date -Format s) stepB_new $Tag start ($Net)" | Add-Content runs.log

# (1) N1
if (-not (Test-Path n1_flat.il)) {
    wsl.exe -d Ubuntu -e bash $L/synth_replay/run_replay.sh | Select-Object -Last 3
    python ..\sec\sram_cut.py synth_replay\n1_pre_abc_fast.il n1_cut.il | Select-Object -Last 2
    wsl.exe -d Ubuntu -e bash -c "cd $L && $Y -q -l n1_flat.log n1_flat.ys > /dev/null 2>&1; echo n1_flat rc=`$?"
}

# (2) gate side of the new netlist
$fe = (Get-Content ..\sec\gate_front_end.ys) -replace '/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/final_B/54-openroad-fillinsertion/soc_asic_top.nl.v', $Net
if (-not ($fe -match [regex]::Escape($Net))) { throw "netlist path not substituted in gate_front_end" }
$fe | Set-Content -Encoding ascii ..\sec\gate_front_end_$Tag.ys
(Get-Content ..\sec\gate_pre.ys) -replace 'script gate_front_end.ys', "script gate_front_end_$Tag.ys" -replace 'write_ilang gate_pre.il', "write_ilang gate_pre_$Tag.il" |
    Set-Content -Encoding ascii ..\sec\gate_pre_$Tag.ys
wsl.exe -d Ubuntu -e bash -c "cd $S && $Y -q -l gate_pre_$Tag.log gate_pre_$Tag.ys > /dev/null 2>&1; echo gate_pre rc=`$?"
python ..\sec\sram_cut.py ..\sec\gate_pre_$Tag.il ..\sec\gate_cut_$Tag.il | Select-Object -Last 2
(Get-Content gate_flat.ys) -replace '\.\./sec/gate_cut\.il', "../sec/gate_cut_$Tag.il" -replace 'write_ilang gate_flat\.il', "write_ilang gate_flat_$Tag.il" |
    Set-Content -Encoding ascii gate_flat_$Tag.ys
wsl.exe -d Ubuntu -e bash -c "cd $L && $Y -q -l gate_flat_$Tag.log gate_flat_$Tag.ys > /dev/null 2>&1; echo gate_flat rc=`$?"

# (3) pairing, (4) LEC pair
python evert.py pair n1_flat.il gate_flat_$Tag.il pairsB_$Tag.json | Select-Object -Last 4
.\build_pair.ps1 -Gold n1_flat.il -Gate gate_flat_$Tag.il -Pairs pairsB_$Tag.json -BaseSpec specB_base.json -Tag B$Tag

# (5) per-output SAT
wsl.exe -d Ubuntu -e bash -c "cd $L && G=B${Tag}_gold.aig H=B${Tag}_gate.aig bash run_msat.sh B$Tag"

# (6) residual outputs -> &cec
python open_outputs.py msatB${Tag}_b.aig B${Tag}_gold.aig pairsB_$Tag.json --list | Tee-Object -FilePath B${Tag}_open.txt | Select-Object -Last 6
$open = @(Get-Content B${Tag}_open.txt | Where-Object { $_ -like "OPEN *" } | ForEach-Object { ($_ -split " ")[2] })
if ($open.Count -gt 0) {
    $open | Set-Content -Encoding ascii B${Tag}_open_names.txt
    python outsel.py B${Tag}_gold.aig B${Tag}_gold_open.aig "@B${Tag}_open_names.txt"
    python outsel.py B${Tag}_gate.aig B${Tag}_gate_open.aig "@B${Tag}_open_names.txt"
    wsl.exe -d Ubuntu -e bash -c "cd $L && /nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc -c '&cec -v B${Tag}_gold_open.aig B${Tag}_gate_open.aig' > cecB${Tag}_open.log 2>&1; grep -a -E 'Networks are|NOT EQUIV' cecB${Tag}_open.log | tail -2"
} else {
    "all $((Get-Content B${Tag}_open.txt | Select-String 'outputs ').Line) proved by the per-output SAT pass"
}
"$(Get-Date -Format s) stepB_new $Tag end" | Add-Content runs.log
