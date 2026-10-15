# LEC of the locked 16 KiB-RAM DM chip (r14F_A / r14F_B, config_R14_FINAL.json, snapshot rtl_r14), 2026-10-08.
# Same register-mapped chain as the 8 KiB-RAM final3 proof (NHAT_KY.md section 9 "EQY va LEC"):
#   step A  RTL(rtl_r14)+fsm == N1, N1 = OpenLane's own synthesis state before `abc -fast`, replayed byte-exactly
#           (synth_replay_r14/dm_r14F, replay netlist == r14F_A step 06)
#   step B  N1 == the final netlist of r14F_A and of r14F_B
# Every side: SRAM macros cut (../sec/sram_cut.py: pins become outputs, dout becomes shared inputs), flops reduced to
# plain $dff, flops paired by name (evert.py), each paired flop's D compared (lec_d outputs), gold-only flops proved
# constant (greatest fixpoint, const_check.py) or RTL-justified duplicates (spec_manual.py), FSM one-hot groups
# restricted (mk_onehot_spec.py). Outputs proved one by one with ABC &sat (run_msat.sh); residual outputs listed.
#   .\run_lec_r14.ps1 -Step A        (then B; -Step B needs n1_flat_r14.il from A)
param([string]$Step = "A")
$ErrorActionPreference = "Stop"
Set-Location E:\Projects\RISCV-research\asic\equiv\lec
$Y = "/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys"
$ABC = "/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc"
$L = "/mnt/e/Projects/RISCV-research/asic/equiv/lec"
$S = "/mnt/e/Projects/RISCV-research/asic/equiv/sec"
function Wsl([string]$cmd) { wsl.exe -d Ubuntu -e bash -c $cmd | Select-String -NotMatch bogus }
function Log([string]$m) { "$(Get-Date -Format s) R14 $m" | Add-Content runs.log; $m }

# ---- N1 (step A and B)
if (-not (Test-Path n1_flat_r14.il)) {
    Log "N1: sram_cut + flatten of synth_replay_r14/dm_r14F/n1_pre_abc_fast.il"
    python ..\sec\sram_cut.py synth_replay_r14\dm_r14F\n1_pre_abc_fast.il n1_cut_r14.il | Select-Object -Last 2
    Wsl "cd $L && $Y -q -l n1_flat_r14.log n1_flat_r14.ys > /dev/null 2>&1; echo n1_flat rc=`$?"
}

if ($Step -eq "A") {
    Log "step A start"
    if (-not (Test-Path gold_flat_r14.il)) {
        Wsl "cd $S && $Y -q -l gold_pre_r14.log gold_pre_r14.ys > /dev/null 2>&1; echo gold_pre rc=`$?"
        python ..\sec\sram_cut.py ..\sec\gold_pre_r14.il ..\sec\gold_cut_r14.il | Select-Object -Last 2
        Wsl "cd $L && $Y -q -l gold_flat_r14.log gold_flat_r14.ys > /dev/null 2>&1; echo gold_flat rc=`$?"
    }
    python evert.py pair gold_flat_r14.il n1_flat_r14.il pairsAR14.json | Select-Object -Last 4
    # gold-only flops: duplicates and constant candidates (simulation), then the formal greatest fixpoint
    python evert.py cut gold_flat_r14.il gold pairsAR14.json gold_god_r14.il --gold-only-d | Out-Null
    (Get-Content gold_god_aig.ys) -replace 'gold_god', 'gold_god_r14' | Set-Content -Encoding ascii gold_god_r14_aig.ys
    Wsl "cd $L && $Y -q -l gold_god_r14_aig.log gold_god_r14_aig.ys > /dev/null 2>&1; echo gold_god rc=`$?"
    python const_check.py analyze gold_god_r14.aig pairsAR14.json specAR14_0.json | Select-Object -Last 3
    $cur = "specAR14_0.json"
    for ($r = 1; $r -le 12; $r++) {
        python evert.py cut gold_flat_r14.il gold pairsAR14.json clr14_tied.il --spec $cur --gold-only-d | Out-Null
        (Get-Content gold_god_aig.ys) -replace 'gold_god', 'clr14_tied' | Set-Content -Encoding ascii clr14_tied_aig.ys
        Wsl "cd $L && $Y -q -l clr14_tied_aig.log clr14_tied_aig.ys > /dev/null 2>&1; echo yosys rc=`$?"
        python const_check.py mkproof clr14_tied.aig $cur clr14_proof.aig
        Wsl "cd $L && $ABC -c '&r clr14_proof.aig; &sat -a -z -C 1000000; &w clr14_proof_sat.aig' > clr14_sat_r$r.log 2>&1; tail -n 3 clr14_sat_r$r.log"
        $next = "specAR14_c$r.json"
        $o = python const_check.py prune clr14_proof_sat.aig $cur $next
        $o
        $cur = $next
        if ($o -match "NOT proved 0 ") { Log "constants: fixpoint after round $r -> $cur"; break }
    }
    .\build_pair.ps1 -Gold gold_flat_r14.il -Gate n1_flat_r14.il -Pairs pairsAR14.json -BaseSpec $cur -Tag AR14
    Wsl "cd $L && G=AR14_gold.aig H=AR14_gate.aig bash run_msat.sh AR14"
    python open_outputs.py msatAR14_b.aig AR14_gold.aig pairsAR14.json --list | Tee-Object -FilePath AR14_open.txt | Select-Object -Last 8
    Log "step A end (open outputs: AR14_open.txt)"
}

if ($Step -eq "B") {
    foreach ($t in @(@{Tag = "R14FA"; Run = "r14F_A"}, @{Tag = "R14FB"; Run = "r14F_B"})) {
        $Tag = $t.Tag
        $netf = Get-ChildItem "..\..\soc_dm_4kb\runs\$($t.Run)" -Directory | Where-Object { $_.Name -match '^\d+-openroad-fillinsertion$' } | Select-Object -Last 1
        $Net = "/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/$($t.Run)/$($netf.Name)/soc_asic_top.nl.v"
        Log "step B $Tag start ($Net)"
        $fe = (Get-Content ..\sec\gate_front_end.ys) -replace '/mnt/e/Projects/RISCV-research/results/pd_run_archive/final_B/dependency_inputs/54-openroad-fillinsertion/soc_asic_top.nl.v', $Net
        if (-not ($fe -match [regex]::Escape($Net))) { throw "netlist path not substituted in gate_front_end" }
        $fe | Set-Content -Encoding ascii ..\sec\gate_front_end_$Tag.ys
        (Get-Content ..\sec\gate_pre.ys) -replace 'script gate_front_end.ys', "script gate_front_end_$Tag.ys" -replace 'write_ilang gate_pre.il', "write_ilang gate_pre_$Tag.il" |
            Set-Content -Encoding ascii ..\sec\gate_pre_$Tag.ys
        Wsl "cd $S && $Y -q -l gate_pre_$Tag.log gate_pre_$Tag.ys > /dev/null 2>&1; echo gate_pre rc=`$?"
        python ..\sec\sram_cut.py ..\sec\gate_pre_$Tag.il ..\sec\gate_cut_$Tag.il | Select-Object -Last 2
        (Get-Content gate_flat.ys) -replace '\.\./sec/gate_cut\.il', "../sec/gate_cut_$Tag.il" -replace 'write_ilang gate_flat\.il', "write_ilang gate_flat_$Tag.il" |
            Set-Content -Encoding ascii gate_flat_$Tag.ys
        Wsl "cd $L && $Y -q -l gate_flat_$Tag.log gate_flat_$Tag.ys > /dev/null 2>&1; echo gate_flat rc=`$?"
        python evert.py pair n1_flat_r14.il gate_flat_$Tag.il pairsB_$Tag.json | Select-Object -Last 4
        # base spec: every N1-only flop free (final3's specB_base.json listed its three by index)
        python -c "import json,sys; P=json.load(open(sys.argv[1])); json.dump({'const': {}, 'dup': {}, 'free': list(range(len(P['gold_only'])))}, open(sys.argv[2], 'w'))" pairsB_$Tag.json specB_${Tag}_base.json
        .\build_pair.ps1 -Gold n1_flat_r14.il -Gate gate_flat_$Tag.il -Pairs pairsB_$Tag.json -BaseSpec specB_${Tag}_base.json -Tag B$Tag
        Wsl "cd $L && G=B${Tag}_gold.aig H=B${Tag}_gate.aig bash run_msat.sh B$Tag"
        python open_outputs.py msatB${Tag}_b.aig B${Tag}_gold.aig pairsB_$Tag.json --list | Tee-Object -FilePath B${Tag}_open.txt | Select-Object -Last 6
        $open = @(Get-Content B${Tag}_open.txt | Where-Object { $_ -like "OPEN *" } | ForEach-Object { ($_ -split " ")[2] })
        if ($open.Count -gt 0) {
            $open | Set-Content -Encoding ascii B${Tag}_open_names.txt
            python outsel.py B${Tag}_gold.aig B${Tag}_gold_open.aig "@B${Tag}_open_names.txt"
            python outsel.py B${Tag}_gate.aig B${Tag}_gate_open.aig "@B${Tag}_open_names.txt"
            Wsl "cd $L && $ABC -c '&cec -v B${Tag}_gold_open.aig B${Tag}_gate_open.aig' > cecB${Tag}_open.log 2>&1; grep -a -E 'Networks are|NOT EQUIV' cecB${Tag}_open.log | tail -2"
        }
        Log "step B $Tag end"
    }
}
