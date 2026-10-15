# LEC of the SA2 chip (sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1 / _r2, 11.56 mm2), 2026-10-13.
# The register-mapped chain of the DM proof (run_lec_r14.ps1, run_lec_r14_mul.ps1, run_lec_r14_pass2.ps1), run in a
# per-pass work folder whose front ends come from scripts/verification/prepare_sa2_lec.py
# (results/completion_preparation_20261009/sa2_lec_20261009) and <work>/run_frontends.sh: fresh byte-exact N1 replay of
# the signed run's synthesis, proof of the fsm re-encoding, gold (rtl_r14 + SA2 top + fsm) / N1 / both final netlists
# flattened with the SRAM macros cut, flops paired by name (pairs_a.json: gold-N1, pairs_b<n>.json: N1-final<n>).
#   A    gold-only flops: constants (greatest fixpoint, ABC &sat) and duplicates; mapped pair; per-output SAT; open list
#   Inv  one-hot invariant of the re-encoded FSM registers on gold (Q one-hot => D one-hot; reset code one-hot)
#   B    N1 == final netlist of r1 and of r2 (per-output SAT, &cec on residuals)
#   NegB negative control: the first and2_1 of the r1 final netlist becomes or2_1; a counterexample is required
# Windows Python helpers run pinned to one logical CPU at process creation (QUY_TRINH.md section B).
# Run with PowerShell 7:  pwsh -File run_lec_sa2.ps1 -Work <folder> -Step A|Inv|B|NegB
param([Parameter(Mandatory = $true)][string]$Work, [string]$Step = "A")
$ErrorActionPreference = "Stop"
$LEC = "E:\Projects\RISCV-research\asic\equiv\lec"
$SEC = "E:\Projects\RISCV-research\asic\equiv\sec"
$PY = "C:\Users\toanl\AppData\Local\Programs\Python\Python311\python.exe"
$Y = "/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys"
$ABC = "/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc"
$Work = (Resolve-Path $Work).Path
Set-Location $Work
$W = "/mnt/" + $Work.Substring(0, 1).ToLower() + ($Work.Substring(2) -replace '\\', '/')
function Wsl([string]$cmd) { wsl.exe -d Ubuntu -e bash -c $cmd | Select-String -NotMatch bogus }
function Log([string]$m) { "$(Get-Date -Format s) SA2LEC $m" | Add-Content (Join-Path $Work "runs.log"); $m }
$script:pyn = (Get-ChildItem $Work -Filter "py_*.log" -ErrorAction SilentlyContinue).Count
function Py([string]$a) {
    $script:pyn++
    $log = Join-Path $Work ("py_{0:D3}.log" -f $script:pyn)
    cmd /c "start /wait /b /affinity 4 `"`" `"$PY`" -B $a > `"$log`" 2>&1"
    "py_{0:D3}: python {1}" -f $script:pyn, $a | Add-Content (Join-Path $Work "py_commands.txt")
    Get-Content $log
}
function BuildPair([string]$Gold, [string]$Gate, [string]$Pairs, [string]$BaseSpec, [string]$Tag) {
    Py "$LEC\spec_manual.py $Pairs $BaseSpec ${Tag}_specm.json" | Select-Object -Last 1
    Py "$LEC\mk_onehot_spec.py $Pairs ${Tag}_specm.json ${Tag}_spec.json"
    Py "$LEC\evert.py cut $Gold gold $Pairs ${Tag}_gold.il --spec ${Tag}_spec.json"
    Py "$LEC\evert.py cut $Gate gate $Pairs ${Tag}_gate.il --spec ${Tag}_spec.json"
    foreach ($n in "${Tag}_gold", "${Tag}_gate") {
        (Get-Content "$LEC\gold_god_aig.ys") -replace 'gold_god', $n | Set-Content -Encoding ascii "${n}_aig.ys"
    }
    Wsl "cd $W && for n in ${Tag}_gold ${Tag}_gate; do $Y -q -l `${n}_aig.log `${n}_aig.ys > /dev/null 2>&1; echo `"`$n rc=`$?`"; done"
    Py "$LEC\aig_syms.py ${Tag}_gold.aig ${Tag}_gate.aig"
    Py "$LEC\aigsim.py ${Tag}_gold.aig ${Tag}_gate.aig 16 4" | Out-File -Encoding ascii "${Tag}_sim.txt"
    Get-Content "${Tag}_sim.txt" -TotalCount 1
}
function Msat([string]$T) {
    Wsl ("cd $W && $ABC -c '&r ${T}_gold.aig; &miter ${T}_gate.aig; &ps; &sat -a -z -C 2000 -v; &ps; &w msat${T}_a.aig' > msat${T}_a.log 2>&1; " +
         "$ABC -c '&r msat${T}_a.aig; &sat -a -z -C 200000 -v; &ps; &w msat${T}_b.aig' > msat${T}_b.log 2>&1; " +
         "grep -h -E 'Unsat calls|Sat   calls|Undef calls' msat${T}_a.log msat${T}_b.log")
}

if ($Step -eq "A") {
    foreach ($f in "gold_flat.il", "n1_flat.il", "pairs_a.json") { if (-not (Test-Path $f)) { throw "front end output missing: $f" } }
    Log "step A start"
    Py "$LEC\evert.py cut gold_flat.il gold pairs_a.json gold_god.il --gold-only-d"
    Copy-Item "$LEC\gold_god_aig.ys" gold_god_aig.ys -Force
    Wsl "cd $W && $Y -q -l gold_god_aig.log gold_god_aig.ys > /dev/null 2>&1; echo gold_god rc=`$?"
    Py "$LEC\const_check.py analyze gold_god.aig pairs_a.json specA_0.json" | Select-Object -Last 3
    $cur = "specA_0.json"
    for ($r = 1; $r -le 12; $r++) {
        Py "$LEC\evert.py cut gold_flat.il gold pairs_a.json cl_tied.il --spec $cur --gold-only-d" | Out-Null
        (Get-Content "$LEC\gold_god_aig.ys") -replace 'gold_god', 'cl_tied' | Set-Content -Encoding ascii cl_tied_aig.ys
        Wsl "cd $W && $Y -q -l cl_tied_aig.log cl_tied_aig.ys > /dev/null 2>&1; echo yosys rc=`$?"
        Py "$LEC\const_check.py mkproof cl_tied.aig $cur cl_proof.aig" | Out-Null
        Wsl "cd $W && $ABC -c '&r cl_proof.aig; &sat -a -z -C 1000000; &w cl_proof_sat.aig' > cl_sat_r$r.log 2>&1; tail -n 3 cl_sat_r$r.log"
        $next = "specA_c$r.json"
        $o = Py "$LEC\const_check.py prune cl_proof_sat.aig $cur $next"
        $o
        $cur = $next
        if ($o -match "NOT proved 0 ") { Log "constants: fixpoint after round $r -> $cur"; break }
    }
    Set-Content -Encoding ascii specA_final.txt $cur
    BuildPair -Gold gold_flat.il -Gate n1_flat.il -Pairs pairs_a.json -BaseSpec $cur -Tag A
    Msat A
    Py "$LEC\open_outputs.py msatA_b.aig A_gold.aig pairs_a.json --list" | Tee-Object -FilePath A_open.txt | Select-Object -Last 8
    Log "step A end (open outputs: A_open.txt)"
}

if ($Step -eq "Mul") {
    # step A closure as run_lec_r14_mul.ps1: the residual outputs of the per-output SAT are the ALU multiplier cone.
    #   1. t1 replay: the single-hook N1 replay with the techmap split into -max_iter 1 + snapshot + techmap
    #   2. macc_alg.py: both the t1 network and the RTL-gold network (gold_pre.il, techmap -max_iter 2) compute
    #      product == signed33(A) * signed33(B) mod 2^64; --neg-spec unsigned and --mutate pp must FAIL
    #   3. &cec: those networks equal the pure multipliers of the exposed LEC pair
    #   4. mulsub.py subst + &cec of the residual outputs
    Log "multiplier closure start"
    $MA = '\u_soc.u_core.u_pipeline.datapath.alu.mul_a'
    $MB = '\u_soc.u_core.u_pipeline.datapath.alu.mul_b'
    $MP = '\u_soc.u_core.u_pipeline.datapath.alu.product'
    $S06 = '/mnt/e/Projects/RISCV-research/asic/soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1/06-yosys-synthesis'
    $RY = '/nix/store/zdhr86kv5rxlp0s58rzxk1aki1igankx-yosys-with-plugins-python3-3.11.9-env/bin/yosys'
    if (-not (Test-Path t1\t1_iter1.il)) {
        New-Item -ItemType Directory -Force t1 | Out-Null
        Wsl ("cd $W && SYNTH_SNAP=$W/t1 $RY -y /mnt/e/Projects/RISCV-research/asic/equiv/lec/synth_replay_r14/synthesize_n1only_t1.py -- " +
             "--config-in $S06/config.json --extra-in $S06/extra.json --output $W/t1/soc_asic_top.nl.v > t1/replay.log 2>&1; echo t1 replay rc=`$?; " +
             "cmp -s $S06/soc_asic_top.nl.v t1/soc_asic_top.nl.v && echo t1 replay netlist byte-identical to step 06 || echo t1 replay netlist DIFFERS from step 06")
    }
    Copy-Item "$LEC\gold_x.ys" gold_x.ys -Force
    Copy-Item "$LEC\n1_x.ys" n1_x.ys -Force
    Wsl "cd $W && $Y -q -l gold_x.log gold_x.ys > /dev/null 2>&1; echo gold_x rc=`$?; $Y -q -l n1_x.log n1_x.ys > /dev/null 2>&1; echo n1_x rc=`$?"
    BuildPair -Gold gold_x.il -Gate n1_x.il -Pairs pairs_a.json -BaseSpec (Get-Content specA_final.txt) -Tag AX
    Py "$LEC\mulsub.py extract AX_gold.aig mul_pure_gold.aig"
    Py "$LEC\mulsub.py extract AX_gate.aig mul_pure_gate.aig"
    New-Item -ItemType Directory -Force mulproof | Out-Null
    (Get-Content "$LEC\mulproof\t1_pure.ys") -replace '\.\./synth_replay_t1/t1_iter1\.il', '../t1/t1_iter1.il' | Set-Content -Encoding ascii mulproof\t1_pure.ys
    (Get-Content "$LEC\mulproof\rtl_t2.ys") -replace '\.\./\.\./sec/gold_pre\.il', '../gold_pre.il' | Set-Content -Encoding ascii mulproof\rtl_t2.ys
    if (-not ((Get-Content mulproof\t1_pure.ys -Raw) -match '\.\./t1/t1_iter1\.il') -or -not ((Get-Content mulproof\rtl_t2.ys -Raw) -match '\.\./gold_pre\.il')) { throw "mulproof scripts not substituted" }
    Wsl "cd $W/mulproof && $Y -q -l t1_pure.log t1_pure.ys > /dev/null 2>&1; echo t1_pure rc=`$?; $Y -q -l rtl_t2.log rtl_t2.ys > /dev/null 2>&1; echo rtl_t2 rc=`$?"
    Py "$LEC\mulsub.py extract mulproof\t1_ctx.aig mulproof\t1_pure.aig"
    Py "$LEC\mulsub.py extract mulproof\rtl_t2_ctx.aig mulproof\rtl_t2_pure.aig"
    foreach ($side in @(@{N = "gate"; F = "t1\t1_iter1.il"}, @{N = "gold"; F = "mulproof\rtl_t2.il"})) {
        foreach ($v in @(@{T = "plain"; A = ""}, @{T = "negspec_unsigned"; A = "--neg-spec unsigned"}, @{T = "mutate_pp"; A = "--mutate pp"})) {
            $out = Py "$LEC\macc_alg.py $($side.F) --a $MA --b $MB --p $MP $($v.A)"
            $out | Set-Content -Encoding ascii "mulproof\alg_$($side.N)_$($v.T).log"
            "$($side.N) $($v.T): $(($out | Select-String 'RESULT') -join ' ')"
        }
    }
    Wsl ("cd $W && for p in 'mulproof/t1_pure.aig mul_pure_gate.aig' 'mulproof/rtl_t2_pure.aig mul_pure_gold.aig' 'mul_pure_gold.aig mul_pure_gate.aig'; do " +
         "set -- `$p; r=`$(timeout 300 $ABC -c `"&cec -v `$1 `$2`" 2>&1 | grep -a -E 'Networks are|NOT EQUIV|UNDECIDED' | tail -n 1); " +
         "printf '%-28s %-22s %s\n' `$1 `$2 `"`${r:-NO VERDICT (timeout)}`"; done") | Tee-Object -FilePath mulproof\chain_cec.txt
    @(Get-Content A_open.txt | Where-Object { $_ -like "OPEN *" } | ForEach-Object { ($_ -split " ")[2] }) | Set-Content -Encoding ascii A_mul_outs.txt
    "targets: $((Get-Content A_mul_outs.txt).Count)"
    Py "$LEC\mulsub.py subst AX_gold.aig AX_gate.aig A_mul_outs.txt mul_pure_gold.aig AXs_gold.aig AXs_gate.aig"
    Wsl "cd $W && $ABC -c '&cec -v AXs_gold.aig AXs_gate.aig' > subcecA.log 2>&1; grep -a -E 'Networks are|NOT EQUIV|UNDECIDED' subcecA.log | tail -n 3"
    Log "multiplier closure end"
}

if ($Step -eq "Inv") {
    Log "one-hot invariant start"
    Py "$LEC\evert.py cut gold_flat.il gold pairs_a.json gold_inv.il --spec A_spec.json --inv"
    Copy-Item "$LEC\gold_inv_aig.ys" gold_inv_aig.ys -Force
    Wsl "cd $W && $Y -q -l gold_inv_aig.log gold_inv_aig.ys > /dev/null 2>&1; echo gold_inv rc=`$?"
    Py "$LEC\inv_check.py mk gold_inv.aig inv_proof.aig"
    Wsl "cd $W && $ABC -c '&r inv_proof.aig; &ps; &sat -a -z -C 1000000 -v; &ps; &w inv_sat.aig' > inv_sat.log 2>&1; grep -h -E 'Unsat calls|Sat   calls|Undef calls' inv_sat.log"
    Py "$LEC\aig_outputs_zero.py inv_sat.aig"
    Py "$LEC\inv_check.py reset gold_inv.aig pairs_a.json"
    Log "one-hot invariant end"
}

if ($Step -eq "B") {
    foreach ($n in 1, 2) {
        foreach ($f in "gate${n}_flat.il", "pairs_b$n.json") { if (-not (Test-Path $f)) { throw "front end output missing: $f" } }
        Log "step B$n start"
        Py "$LEC\free_spec.py pairs_b$n.json specB${n}_base.json"
        BuildPair -Gold n1_flat.il -Gate "gate${n}_flat.il" -Pairs "pairs_b$n.json" -BaseSpec "specB${n}_base.json" -Tag "B$n"
        Msat "B$n"
        Py "$LEC\open_outputs.py msatB${n}_b.aig B${n}_gold.aig pairs_b$n.json --list" | Tee-Object -FilePath "B${n}_open.txt" | Select-Object -Last 6
        $open = @(Get-Content "B${n}_open.txt" | Where-Object { $_ -like "OPEN *" } | ForEach-Object { ($_ -split " ")[2] })
        if ($open.Count -gt 0) {
            $open | Set-Content -Encoding ascii "B${n}_open_names.txt"
            Py "$LEC\outsel.py B${n}_gold.aig B${n}_gold_open.aig @B${n}_open_names.txt"
            Py "$LEC\outsel.py B${n}_gate.aig B${n}_gate_open.aig @B${n}_open_names.txt"
            Wsl "cd $W && $ABC -c '&cec -v B${n}_gold_open.aig B${n}_gate_open.aig' > cecB${n}_open.log 2>&1; grep -a -E 'Networks are|NOT EQUIV' cecB${n}_open.log | tail -2"
        }
        Log "step B$n end"
    }
}

if ($Step -eq "NegFSM") {
    # negative control of the fsm proof (as asic/equiv/fsm_recode/prove_fsm_neg.ys for DM): equiv_make reads an
    # encoding with the u_lcd.en_phase codes 10 and 01 swapped, while fsm writes the real one; the proof must FAIL
    Log "negative control FSM start"
    $enc = Get-Content enc.txt
    $k = [Array]::IndexOf($enc, ".fsm soc_asic_top u_soc.u_lcd.en_phase")
    if ($k -lt 0) { throw "en_phase not in enc.txt" }
    $i10 = -1; $i01 = -1
    for ($j = $k + 1; $j -lt $enc.Count -and -not $enc[$j].StartsWith(".fsm"); $j++) {
        if ($enc[$j].StartsWith(".map 10 ")) { $i10 = $j }
        if ($enc[$j].StartsWith(".map 01 ")) { $i01 = $j }
    }
    if ($i10 -lt 0 -or $i01 -lt 0) { throw "en_phase codes 10 / 01 not found" }
    $neg = $enc.Clone()
    $neg[$i10] = ".map 10 " + ($enc[$i01] -split " ")[2]
    $neg[$i01] = ".map 01 " + ($enc[$i10] -split " ")[2]
    $neg | Set-Content -Encoding ascii enc_neg.txt
    (Get-Content prove_fsm.ys) -replace 'fsm -encfile enc.txt', 'fsm -encfile enc_neg_written.txt' -replace 'equiv_make -encfile enc.txt', 'equiv_make -encfile enc_neg.txt' |
        Set-Content -Encoding ascii prove_fsm_neg.ys
    if (-not ((Get-Content prove_fsm_neg.ys -Raw) -match 'equiv_make -encfile enc_neg.txt')) { throw "negative fsm script not substituted" }
    Wsl "cd $W && $Y -l prove_fsm_neg.log prove_fsm_neg.ys > prove_fsm_neg.stdout 2>&1; echo prove_fsm_neg rc=`$?; grep -a -E 'unproven|successfully proven|ERROR' prove_fsm_neg.log | tail -3"
    Log "negative control FSM end (a nonzero rc with unproven cells is required)"
}

if ($Step -eq "NegB" -and (Test-Path (Join-Path $Work "DEFER_HEAVY"))) {
    # cooperative deferral (2026-10-13): the mutated final netlist needs a full gate front end (several GB in WSL);
    # it waits while detailed routings use the host memory. Remove DEFER_HEAVY and run -Step NegB again later.
    Log "negative control B DEFERRED (DEFER_HEAVY present: host memory reserved for the PD runs)"
    exit 0
}

if ($Step -eq "NegB") {
    Log "negative control B start"
    $src = "E:\Projects\RISCV-research\asic\soc_sa2_4kb\runs\sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1\56-openroad-fillinsertion\soc_asic_top.nl.v"
    New-Item -ItemType Directory -Force neg | Out-Null
    $t = Get-Content $src -Raw
    $i = $t.IndexOf("sky130_fd_sc_hd__and2_1 ")
    if ($i -lt 0) { throw "no and2_1 cell to mutate" }
    ($t.Substring(0, $i) + "sky130_fd_sc_hd__or2_1 " + $t.Substring($i + "sky130_fd_sc_hd__and2_1 ".Length)) | Set-Content -NoNewline -Encoding ascii neg\soc_asic_top_mut.nl.v
    Log "negative control: first and2_1 of the r1 final netlist turned into or2_1"
    $orig = "/mnt/e/Projects/RISCV-research/asic/soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1/56-openroad-fillinsertion/soc_asic_top.nl.v"
    $fe = (Get-Content gate1_frontend.ys) -replace [regex]::Escape($orig), "$W/neg/soc_asic_top_mut.nl.v"
    if (-not (($fe -join "`n") -match "neg/soc_asic_top_mut")) { throw "netlist path not substituted in the negative front end" }
    $fe | Set-Content -Encoding ascii gateN_frontend.ys
    (Get-Content gate1_pre.ys) -replace 'gate1_frontend', 'gateN_frontend' -replace 'gate1_pre', 'gateN_pre' | Set-Content -Encoding ascii gateN_pre.ys
    (Get-Content gate1_flat.ys) -replace 'gate1_cut', 'gateN_cut' -replace 'gate1_flat', 'gateN_flat' | Set-Content -Encoding ascii gateN_flat.ys
    Wsl "cd $W && $Y -q -l gateN_pre.log gateN_pre.ys > /dev/null 2>&1; echo gateN_pre rc=`$?"
    Py "$SEC\sram_cut.py gateN_pre.il gateN_cut.il" | Select-Object -Last 1
    Wsl "cd $W && $Y -q -l gateN_flat.log gateN_flat.ys > /dev/null 2>&1; echo gateN_flat rc=`$?"
    Py "$LEC\evert.py pair n1_flat.il gateN_flat.il pairs_bN.json" | Select-Object -Last 2
    Py "$LEC\free_spec.py pairs_bN.json specBN_base.json"
    BuildPair -Gold n1_flat.il -Gate gateN_flat.il -Pairs pairs_bN.json -BaseSpec specBN_base.json -Tag BN
    Msat BN
    Py "$LEC\open_outputs.py msatBN_b.aig BN_gold.aig pairs_bN.json --list" | Tee-Object -FilePath BN_open.txt | Select-Object -Last 6
    Log "negative control B end (a SAT / counterexample output is required)"
}
