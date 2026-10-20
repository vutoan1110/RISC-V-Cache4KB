# LEC of the 16 KiB-RAM DM chip, step A closure (2026-10-09): the 34 outputs that the per-output SAT of
# run_lec_r14.ps1 -Step A leaves open are the cone of the ALU multiplier (32 bits of d_req_addr + 2 duplicate checks of
# mem_byte_offset_m), exactly as for the 8 KiB-RAM final3 proof. Same closure as there (NHAT_KY section 9 "EQY va LEC"):
#   1. t1 replay of the r14F_A synthesis: the techmap split into `techmap -max_iter 1` + snapshot + `techmap`, so the
#      $and/$not/$fa/$alu network maccmap built in OpenLane's own process state is captured (t1_iter1.il)
#   2. macc_alg.py: algebraic proof (backward rewriting over Z/2^64) that this network and the RTL-gold network
#      (gold_pre_r14.il after `techmap -max_iter 2`) both compute product == signed33(A) * signed33(B) mod 2^64;
#      negative controls --neg-spec unsigned and --mutate pp must FAIL
#   3. the pure multipliers cut from the LEC AIGs (operand / product nets exposed, not cut) equal those networks (&cec)
#   4. mulsub.py subst: the gate's product nodes replaced by the proven gold multiplier, &cec of the 34 outputs
# Run with PowerShell 7 (pwsh): Windows PowerShell 5.1 breaks the quoted bash commands passed to wsl.exe.
$ErrorActionPreference = "Stop"
Set-Location E:\Projects\RISCV-research\asic\equiv\lec
$Y = "/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys"
$L = "/mnt/e/Projects/RISCV-research/asic/equiv/lec"
function Wsl([string]$cmd) { wsl.exe -d Ubuntu -e bash -c $cmd | Select-String -NotMatch bogus }
function Log([string]$m) { "$(Get-Date -Format s) R14mul $m" | Add-Content runs.log; $m }
$MA = '\u_soc.u_core.u_pipeline.datapath.alu.mul_a'
$MB = '\u_soc.u_core.u_pipeline.datapath.alu.mul_b'
$MP = '\u_soc.u_core.u_pipeline.datapath.alu.product'

# ---- 1. t1 replay (synthesize.py of synth_replay_r14 + the one-iteration techmap snapshot)
$t1 = "synth_replay_r14\dm_r14F_t1\t1_iter1.il"
if (-not (Test-Path $t1)) {
    $src = Get-Content synth_replay_r14\synthesize.py -Raw
    $anchor = '    d.run_pass("techmap")' + "`n"
    if (([regex]::Matches($src, [regex]::Escape($anchor))).Count -ne 1) { throw "techmap anchor not unique in synthesize.py" }
    $hook = "    # LEC R14 (t1 variant, 2026-10-09): one techmap iteration first, so the `$macc -> `$and/`$not/`$fa/`$alu network`n" +
            "    # maccmap builds in this process state can be captured; then the full techmap as in the flow.`n" +
            '    d.run_pass("techmap", "-max_iter", "1")' + "`n" +
            '    d.run_pass("write_rtlil", os.environ["SYNTH_SNAP"] + "/t1_iter1.il")  # LEC R14 replay (t1)' + "`n"
    ($src.Replace($anchor, $hook + $anchor)) | Set-Content -NoNewline -Encoding utf8 synth_replay_r14\synthesize_t1.py
    Log "t1 replay of r14F_A"
    Wsl "cd $L/synth_replay_r14 && SYNTH_PY=$L/synth_replay_r14/synthesize_t1.py bash run_replay_r14.sh soc_dm_4kb r14F_A dm_r14F_t1 && tail -1 runs.log"
}

# ---- 2. exposed-multiplier LEC pair (AXR14) and its pure multipliers
(Get-Content gold_x.ys) -replace 'read_ilang gold_flat.il', 'read_ilang gold_flat_r14.il' -replace 'write_ilang gold_x.il', 'write_ilang gold_x_r14.il' | Set-Content -Encoding ascii gold_x_r14.ys
(Get-Content n1_x.ys) -replace 'read_ilang n1_flat.il', 'read_ilang n1_flat_r14.il' -replace 'write_ilang n1_x.il', 'write_ilang n1_x_r14.il' | Set-Content -Encoding ascii n1_x_r14.ys
if (-not ((Get-Content gold_x_r14.ys -Raw) -match 'gold_flat_r14') -or -not ((Get-Content n1_x_r14.ys -Raw) -match 'n1_flat_r14')) { throw "x scripts not substituted" }
Wsl "cd $L && $Y -q -l gold_x_r14.log gold_x_r14.ys > /dev/null 2>&1; echo gold_x rc=`$?; $Y -q -l n1_x_r14.log n1_x_r14.ys > /dev/null 2>&1; echo n1_x rc=`$?"
.\build_pair.ps1 -Gold gold_x_r14.il -Gate n1_x_r14.il -Pairs pairsAR14.json -BaseSpec specAR14_c2.json -Tag AXR14
python mulsub.py extract AXR14_gold.aig mul_pure_gold_r14.aig
python mulsub.py extract AXR14_gate.aig mul_pure_gate_r14.aig

# ---- 3. snapshot networks: algebraic proofs and their pure multipliers
New-Item -ItemType Directory -Force mulproof_r14 | Out-Null
(Get-Content mulproof\t1_pure.ys) -replace '\.\./synth_replay_t1/t1_iter1\.il', '../synth_replay_r14/dm_r14F_t1/t1_iter1.il' | Set-Content -Encoding ascii mulproof_r14\t1_pure.ys
(Get-Content mulproof\rtl_t2.ys) -replace '\.\./\.\./sec/gold_pre\.il', '../../sec/gold_pre_r14.il' | Set-Content -Encoding ascii mulproof_r14\rtl_t2.ys
if (-not ((Get-Content mulproof_r14\t1_pure.ys -Raw) -match 'dm_r14F_t1') -or -not ((Get-Content mulproof_r14\rtl_t2.ys -Raw) -match 'gold_pre_r14')) { throw "mulproof scripts not substituted" }
Wsl "cd $L/mulproof_r14 && $Y -q -l t1_pure.log t1_pure.ys > /dev/null 2>&1; echo t1 rc=`$?; $Y -q -l rtl_t2.log rtl_t2.ys > /dev/null 2>&1; echo rtl_t2 rc=`$?"
python mulsub.py extract mulproof_r14\t1_ctx.aig mulproof_r14\t1_pure.aig
python mulsub.py extract mulproof_r14\rtl_t2_ctx.aig mulproof_r14\rtl_t2_pure.aig
foreach ($side in @(@{N = "gate"; F = $t1}, @{N = "gold"; F = "mulproof_r14\rtl_t2.il"})) {
    foreach ($v in @(@{T = "r14"; A = @()}, @{T = "negspec_unsigned"; A = @("--neg-spec", "unsigned")}, @{T = "mutate_pp"; A = @("--mutate", "pp")})) {
        $log = "mulproof_r14\alg_$($side.N)_$($v.T).log"
        python macc_alg.py $side.F --a $MA --b $MB --p $MP @($v.A) *> $log
        "$($side.N) $($v.T): $((Get-Content $log | Select-String 'RESULT') -join ' ')"
    }
}

# ---- 4. the networks equal the multipliers in the LEC pair; then the substitution
Wsl "cd $L && bash mulproof/cec_pairs.sh mulproof_r14/t1_pure.aig mul_pure_gate_r14.aig mulproof_r14/rtl_t2_pure.aig mul_pure_gold_r14.aig mul_pure_gold_r14.aig mul_pure_gate_r14.aig" | Tee-Object -FilePath mulproof_r14\chain_cec.txt
@(Get-Content AR14_open.txt | Where-Object { $_ -like "OPEN *" } | ForEach-Object { ($_ -split " ")[2] }) | Set-Content -Encoding ascii AR14_mul_outs.txt
"targets: $((Get-Content AR14_mul_outs.txt).Count)"
python mulsub.py subst AXR14_gold.aig AXR14_gate.aig AR14_mul_outs.txt mul_pure_gold_r14.aig AXsR14_gold.aig AXsR14_gate.aig
Wsl "bash $L/run_subcec.sh AXsR14_gold.aig AXsR14_gate.aig subcecAR14"
Log "step A closure end"
