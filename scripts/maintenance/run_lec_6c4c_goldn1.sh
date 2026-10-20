#!/usr/bin/env bash
# 2026-10-15: register-mapped LEC on RTL 6c4ccffd, the part that depends only on the synthesis (gold = RTL + fsm == N1),
# for DM (dm_grid3665x2900_rtl6c4c_r2, step-06 netlist da06d38f) and SA2 (sa2_..._eco2_rtl6c4c_r2, 7a0a289e); prepared
# by scripts/verification/prepare_lec_6c4c.py into results/lec_{dm,sa2}_6c4c_20261015. Same chain as the DM_VC4 proof
# (results/lec_vc4_20261014d/run_gold_n1_passes.sh): two independent passes p1, p2, each with its own fresh byte-exact N1
# replay: front end GoldN1 (run_frontends_vc4.ps1), steps A, Mul, Inv, NegFSM (run_lec_vc4.ps1; both drivers read every
# input from lec_inputs.json), the undefined-value sensitivity (run_xsens.ps1; negative control in p1), then
# compare_lec_vc4_goldn1.py --no-negalign (DM / SA2 synthesis removes no SRAM macro, so there is no NegAlign control).
# Steps B / NegB (N1 == final netlist) follow once the 6c4ccffd layouts are signed off (prepare_lec_6c4c.py --add-gates).
# Memory: PD flows share the 24 GB WSL VM and the kernel OOM killer would pick the largest process (a detailed routing);
# every step waits until at least 8 GB are available. Rule Q: the first failing step ends that design's chain.
# Cooperative stop: create results/lec_6c4c_20261015.ABORT
set -u
R=/e/Projects/RISCV-research
LEC='E:/Projects/RISCV-research/asic/equiv/lec'
PY='/c/Users/toanl/AppData/Local/Programs/Python/Python311/python.exe'
LOG=$R/results/lec_6c4c_20261015_chain.log
say () { echo "$(date -u +%FT%TZ) $*" | tee -a $LOG; }
memwait () {
    until [ "$(MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu -e bash -c "free -m | awk '/Mem/{print \$7}'" 2>/dev/null | tr -dc 0-9)" -ge 8000 ] 2>/dev/null; do
        [ -e $R/results/lec_6c4c_20261015.ABORT ] && return 1
        sleep 60
    done
}
run () {   # <log> <pwsh args...>
    local log=$1; shift
    [ -e $R/results/lec_6c4c_20261015.ABORT ] && { say "ABORT before $log"; return 2; }
    memwait || { say "ABORT while waiting for memory before $log"; return 2; }
    pwsh -NoProfile -File "$@" > "$log" 2>&1
    local rc=$?
    say "$(basename $(dirname $(dirname $log)))/$(basename $(dirname $log))/$(basename $log) exit $rc"
    [ $rc -eq 0 ] || { say "STOP: $(basename $log) failed (rule Q: no continuation)"; tail -5 "$log" | tee -a $LOG; }
    return $rc
}
chain () {   # <design> <results folder>
    local d=$1 L=$R/results/$2 WL="E:\\Projects\\RISCV-research\\results\\$2"
    say "$d gold/N1 passes start (RTL 6c4ccffd)"
    for p in p1 p2; do
        run $L/$p/frontend_goldn1.out "$LEC/run_frontends_vc4.ps1" -Work "$WL\\$p" -Part GoldN1 || return 1
        for s in A Mul Inv NegFSM; do
            run $L/$p/step$s.out "$LEC/run_lec_vc4.ps1" -Work "$WL\\$p" -Step $s || return 1
        done
        run $L/$p/xsens_main.out "$LEC/run_xsens.ps1" -Work "$WL\\$p" -Tag main || return 1
    done
    run $L/p1/xsens_neg.out "$LEC/run_xsens.ps1" -Work "$WL\\p1" -Neg || return 1
    "$PY" -B "$R/asic/equiv/lec/compare_lec_vc4_goldn1.py" "$WL\\p1" "$WL\\p2" "$WL\\pass_comparison_goldn1.json" --no-negalign > $L/compare.out 2>&1
    say "$d compare exit $?: $(tail -1 $L/compare.out)"
}
# 2026-10-20: with arguments <design> <results folder> only that chain runs (e.g. dm lec_dm_noor34_20261020, the DM
# recipe with the or3 / or4 exclusion, whose step-06 netlist 4f2993c2 differs from da06d38f).
if [ $# -ge 2 ]; then
    chain "$1" "$2"
    exit $?
fi
# 2026-10-15 02:20 UTC: DM restarted in lec_dm_6c4c_20261015b (replay source = the DM acceptance run); the first DM
# folder lost its replay source (failed run deleted) before p2 step Mul and is kept as a development record only.
chain dm lec_dm_6c4c_20261015b
chain sa2 lec_sa2_6c4c_20261015
say "LEC 6c4ccffd gold/N1 chains ended (read: prove_fsm proven, A 0 SAT, Mul PROVED + controls NOT PROVED, Inv ALL_PROVED, NegFSM unproven, xsens ALL_PROVED, xsens neg SAT)"
