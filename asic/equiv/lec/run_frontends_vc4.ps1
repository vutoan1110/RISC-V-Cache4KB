# DM_VC4 LEC front end of one pass (2026-10-14): the steps and order of run_frontends_mixed.ps1 (SA2), in two parts,
# with the scripts written by scripts/verification/prepare_vc4_lec.py and the inputs named in <Work>\..\lec_inputs.json.
#   -Part GoldN1  fresh byte-exact N1 replay of the DM_VC4 step-06 synthesis, proof of the fsm re-encoding, gold
#                 (RTL + fsm) and N1 flattened with the SRAM macros cut, gold-N1 flop pairing (pairs_a.json), and the
#                 SRAM port alignment gold_flat_al.il / n1_flat_al.il (sram_align.py: the RTL way-1 macros that DM_VC4
#                 never reads and synthesis removed)
#   -Part Gates   (after prepare_vc4_lec.py --add-gates) both signed final netlists: front end, cut, flatten, N1-final
#                 pairing (pairs_b1.json, pairs_b2.json)
# Yosys runs in WSL. Every Python helper runs in Windows Python pinned to ONE logical CPU at creation (CPU 12: the
# start /affinity mask is HEX, 1000 = 0x1000); its exit code is taken with cmd /v:on ... & exit !ERRORLEVEL! (plain
# cmd /c start /wait returns 0 whatever the child does). Any failure stops the part (rule Q: retry = a fresh pass folder).
#   pwsh -NoProfile -File run_frontends_vc4.ps1 -Work <pass folder> -Part GoldN1|Gates
param([Parameter(Mandatory = $true)][string]$Work, [Parameter(Mandatory = $true)][ValidateSet("GoldN1", "Gates")][string]$Part)
$ErrorActionPreference = "Stop"
$PY = "C:\Users\toanl\AppData\Local\Programs\Python\Python311\python.exe"
$R = "E:\Projects\RISCV-research"
$Y = "/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys"
$RY = "/nix/store/zdhr86kv5rxlp0s58rzxk1aki1igankx-yosys-with-plugins-python3-3.11.9-env/bin/yosys"
$Work = (Resolve-Path $Work).Path
$Inputs = Get-Content (Join-Path (Split-Path $Work -Parent) "lec_inputs.json") -Raw | ConvertFrom-Json
$S = $Inputs.replay_step06_wsl
Set-Location $Work
$W = "/mnt/" + $Work.Substring(0, 1).ToLower() + ($Work.Substring(2) -replace '\\', '/')
function Wsl([string]$cmd) { wsl.exe -d Ubuntu -e bash -c $cmd; if ($LASTEXITCODE -ne 0) { throw "WSL step failed ($LASTEXITCODE): $cmd" } }
function Py([string]$a, [string]$log) {
    cmd /v:on /c "start /wait /b /affinity 1000 `"`" `"$PY`" -B $a > `"$log`" 2>&1 & exit !ERRORLEVEL!"
    $rc = $LASTEXITCODE
    "rc=$rc python $a" | Add-Content frontend_commands.txt
    Get-Content $log | Select-Object -Last 2
    if ($rc -ne 0) { throw "python exit ${rc}: $a" }
}
if ($Part -eq "GoldN1") {
    if (Test-Path replay) { throw "replay exists: the folder is not fresh" }
    New-Item -ItemType Directory replay | Out-Null
    Wsl "cd $W && SYNTH_SNAP=$W/replay $RY -y /mnt/e/Projects/RISCV-research/asic/equiv/lec/synth_replay_r14/synthesize_n1only.py -- --config-in $S/config.json --extra-in $S/extra.json --output $W/replay/soc_asic_top.nl.v > replay/replay.log 2>&1"
    Wsl "cmp $S/soc_asic_top.nl.v $W/replay/soc_asic_top.nl.v && echo replay netlist byte-identical to step 06"
    Wsl "cd $W && $Y -l prove_fsm.log prove_fsm.ys > prove_fsm.stdout 2>&1 && echo prove_fsm ok"
    Wsl "cd $W && $Y -l gold_pre.log gold_pre.ys > gold_pre.stdout 2>&1 && echo gold_pre ok"
    Py "$R\asic\equiv\sec\sram_cut.py gold_pre.il gold_cut.il" gold_cut.log
    Py "$R\asic\equiv\sec\sram_cut.py replay\n1_pre_abc_fast.il n1_cut.il" n1_cut.log
    Wsl "cd $W && $Y -l gold_flat.log gold_flat.ys > gold_flat.stdout 2>&1 && echo gold_flat ok"
    Wsl "cd $W && $Y -l n1_flat.log n1_flat.ys > n1_flat.stdout 2>&1 && echo n1_flat ok"
    Py "$R\asic\equiv\lec\evert.py pair gold_flat.il n1_flat.il pairs_a.json" pairs_a.log
    Py "$R\asic\equiv\lec\sram_align.py gold_flat.il n1_flat.il gold_flat_al.il n1_flat_al.il" align.log
    foreach ($f in "enc.txt", "pairs_a.json", "gold_pre.il", "gold_flat.il", "n1_flat.il", "gold_flat_al.il", "n1_flat_al.il") {
        if (-not (Test-Path $f)) { throw "front end output missing: $f" }
    }
    "FRONT_END_GOLD_N1_COMPLETE (Windows pinned Python, WSL Yosys)"
}
if ($Part -eq "Gates") {
    if ($null -eq $Inputs.gates) { throw "no gates in lec_inputs.json: run prepare_vc4_lec.py --add-gates first" }
    if (-not (Test-Path n1_flat.il)) { throw "GoldN1 part missing" }
    if (Test-Path gate1_pre.il) { throw "gate front end exists: the folder is not fresh for gates" }
    foreach ($n in 1, 2) {
        Wsl "cd $W && $Y -l gate${n}_pre.log gate${n}_pre.ys > gate${n}_pre.stdout 2>&1 && echo gate${n}_pre ok"
        Py "$R\asic\equiv\sec\sram_cut.py gate${n}_pre.il gate${n}_cut.il" "gate${n}_cut.log"
        Wsl "cd $W && $Y -l gate${n}_flat.log gate${n}_flat.ys > gate${n}_flat.stdout 2>&1 && echo gate${n}_flat ok"
        Py "$R\asic\equiv\lec\evert.py pair n1_flat.il gate${n}_flat.il pairs_b$n.json" "pairs_b$n.log"
    }
    foreach ($f in "pairs_b1.json", "pairs_b2.json", "gate1_flat.il", "gate2_flat.il") {
        if (-not (Test-Path $f)) { throw "front end output missing: $f" }
    }
    "FRONT_END_GATES_COMPLETE (Windows pinned Python, WSL Yosys)"
}
