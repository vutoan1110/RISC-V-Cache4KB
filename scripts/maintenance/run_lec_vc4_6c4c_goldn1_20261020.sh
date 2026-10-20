#!/usr/bin/env bash
# 2026-10-20: register-mapped LEC of DM_VC4 on RTL 6c4ccffd, the part that depends only on the synthesis (gold = RTL +
# fsm == N1). Prepared by scripts/verification/prepare_lec_6c4c.py --design vc4 into results/lec_vc4_6c4c_d34_20261020
# (replay source vc4_corr3800x3400_f220_rszctsall_d34_rtl6c4c_scr_r1, step-06 netlist 031e1c67 = every DM_VC4 6c4ccffd
# run, r2 included). Same chain as the R14 DM_VC4 proof (results/lec_vc4_20261014d/run_gold_n1_passes.sh): two independent
# passes p1, p2, each with its own fresh byte-exact N1 replay: front end GoldN1, steps A, NegAlign (DM_VC4 synthesis
# removes the dead way-1 SRAM macros; sram_align.py and its negative control), Mul, Inv, NegFSM, the undefined-value
# sensitivity (run_xsens.ps1; negative control in p1), then compare_lec_vc4_goldn1.py (with the NegAlign check).
# Steps B / NegB (N1 == final netlist) follow after the DM_VC4 sign-off (prepare_lec_6c4c.py --add-gates).
# Memory: PD flows share the 24 GB WSL VM; every step waits until at least 8 GB are available.
# Rule Q: the first failing step ends the chain. Cooperative stop: create <results folder>/ABORT
# Attempt a (lec_vc4_6c4c_d34_20261020) stopped in p1 step NegAlign: run_lec_vc4.ps1 looked for the R14 port name
# (..._dcache_g_dse_...); RTL 6c4ccffd names it ..._dcache_genblk1_g_dse_... (pattern fixed, both names accepted).
#   bash run_lec_vc4_6c4c_goldn1_20261020.sh [results folder name, default lec_vc4_6c4c_d34_20261020b]
set -u
R=/e/Projects/RISCV-research
F=${1:-lec_vc4_6c4c_d34_20261020b}
L=$R/results/$F
WL="E:\\Projects\\RISCV-research\\results\\$F"
LEC='E:/Projects/RISCV-research/asic/equiv/lec'
PY='/c/Users/toanl/AppData/Local/Programs/Python/Python311/python.exe'
say () { echo "$(date -u +%FT%TZ) $*" | tee -a $L/chain.log; }
memwait () {
    until [ "$(MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu -e bash -c "free -m | awk '/Mem/{print \$7}'" 2>/dev/null | tr -dc 0-9)" -ge 8000 ] 2>/dev/null; do
        [ -e $L/ABORT ] && return 1
        sleep 60
    done
}
run () {   # <log> <pwsh args...>
    local log=$1; shift
    [ -e $L/ABORT ] && { say "ABORT before $log"; exit 2; }
    memwait || { say "ABORT while waiting for memory before $log"; exit 2; }
    pwsh -NoProfile -File "$@" > "$log" 2>&1
    local rc=$?
    say "$(basename $(dirname $log))/$(basename $log) exit $rc"
    if [ $rc -ne 0 ]; then say "STOP: $(basename $log) failed (rule Q: no continuation)"; tail -5 "$log" | tee -a $L/chain.log; exit 1; fi
}
say "DM_VC4 6c4ccffd gold/N1 passes start"
for p in p1 p2; do
    run $L/$p/frontend_goldn1.out "$LEC/run_frontends_vc4.ps1" -Work "$WL\\$p" -Part GoldN1
    for s in A NegAlign Mul Inv NegFSM; do
        run $L/$p/step$s.out "$LEC/run_lec_vc4.ps1" -Work "$WL\\$p" -Step $s
    done
    run $L/$p/xsens_main.out "$LEC/run_xsens.ps1" -Work "$WL\\$p" -Tag main
done
run $L/p1/xsens_neg.out "$LEC/run_xsens.ps1" -Work "$WL\\p1" -Neg
"$PY" -B "$R/asic/equiv/lec/compare_lec_vc4_goldn1.py" "$WL\\p1" "$WL\\p2" "$WL\\pass_comparison_goldn1.json" > $L/compare.out 2>&1
say "compare exit $?: $(tail -1 $L/compare.out)"
say "GOLD_N1_PASSES_COMPLETE (read the verdicts: NegAlign DETECTED, NegFSM unproven, xsens neg SAT)"
