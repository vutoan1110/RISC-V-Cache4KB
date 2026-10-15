# SA2 LEC front end of one pass (2026-10-14), the same steps and order as the prepared <pass>/run_frontends.sh
# (scripts/verification/prepare_sa2_lec.py), but every Python helper (sram_cut.py, evert.py pair) runs in Windows
# Python pinned to one logical CPU (QUY_TRINH.md section B) instead of WSL Python: pass 2 of 2026-10-13 died with a
# WSL Python segmentation fault inside evert.py pair. Yosys (native) and the Yosys-embedded synthesis replay stay in WSL.
# The folder must be fresh except for the copied *.ys scripts.
#   pwsh -File run_frontends_mixed.ps1 -Work <folder>
param([Parameter(Mandatory = $true)][string]$Work)
$ErrorActionPreference = "Stop"
$PY = "C:\Users\toanl\AppData\Local\Programs\Python\Python311\python.exe"
$R = "E:\Projects\RISCV-research"
$Y = "/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys"
$RY = "/nix/store/zdhr86kv5rxlp0s58rzxk1aki1igankx-yosys-with-plugins-python3-3.11.9-env/bin/yosys"
$S = "/mnt/e/Projects/RISCV-research/asic/soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1/06-yosys-synthesis"
$Work = (Resolve-Path $Work).Path
Set-Location $Work
$W = "/mnt/" + $Work.Substring(0, 1).ToLower() + ($Work.Substring(2) -replace '\\', '/')
if (Test-Path replay) { throw "replay exists: the folder is not fresh" }
function Wsl([string]$cmd) { wsl.exe -d Ubuntu -e bash -c $cmd; if ($LASTEXITCODE -ne 0) { throw "WSL step failed ($LASTEXITCODE): $cmd" } }
function Py([string]$a, [string]$log) {
    cmd /c "start /wait /b /affinity 4 `"`" `"$PY`" -B $a > `"$log`" 2>&1"
    "python $a" | Add-Content frontend_commands.txt
    Get-Content $log | Select-Object -Last 2
}
New-Item -ItemType Directory replay | Out-Null
Wsl "cd $W && SYNTH_SNAP=$W/replay $RY -y $($R -replace 'E:\\', '/mnt/e/' -replace '\\', '/')/asic/equiv/lec/synth_replay_r14/synthesize_n1only.py -- --config-in $S/config.json --extra-in $S/extra.json --output $W/replay/soc_asic_top.nl.v > replay/replay.log 2>&1"
Wsl "cmp $S/soc_asic_top.nl.v $W/replay/soc_asic_top.nl.v && echo replay netlist byte-identical to step 06"
Wsl "cd $W && $Y -l prove_fsm.log prove_fsm.ys > prove_fsm.stdout 2>&1 && echo prove_fsm ok"
Wsl "cd $W && $Y -l gold_pre.log gold_pre.ys > gold_pre.stdout 2>&1 && echo gold_pre ok"
Py "$R\asic\equiv\sec\sram_cut.py gold_pre.il gold_cut.il" gold_cut.log
Py "$R\asic\equiv\sec\sram_cut.py replay\n1_pre_abc_fast.il n1_cut.il" n1_cut.log
Wsl "cd $W && $Y -l gold_flat.log gold_flat.ys > gold_flat.stdout 2>&1 && echo gold_flat ok"
Wsl "cd $W && $Y -l n1_flat.log n1_flat.ys > n1_flat.stdout 2>&1 && echo n1_flat ok"
Py "$R\asic\equiv\lec\evert.py pair gold_flat.il n1_flat.il pairs_a.json" pairs_a.log
foreach ($n in 1, 2) {
    Wsl "cd $W && $Y -l gate${n}_pre.log gate${n}_pre.ys > gate${n}_pre.stdout 2>&1 && echo gate${n}_pre ok"
    Py "$R\asic\equiv\sec\sram_cut.py gate${n}_pre.il gate${n}_cut.il" "gate${n}_cut.log"
    Wsl "cd $W && $Y -l gate${n}_flat.log gate${n}_flat.ys > gate${n}_flat.stdout 2>&1 && echo gate${n}_flat ok"
    Py "$R\asic\equiv\lec\evert.py pair n1_flat.il gate${n}_flat.il pairs_b$n.json" "pairs_b$n.log"
}
foreach ($f in "pairs_a.json", "pairs_b1.json", "pairs_b2.json", "gold_flat.il", "n1_flat.il", "gate1_flat.il", "gate2_flat.il") {
    if (-not (Test-Path $f)) { throw "front end output missing: $f" }
}
"FRONT_ENDS_COMPLETE_ONLY (mixed: Windows pinned Python, WSL Yosys)"
