#!/usr/bin/env bash
# 2026-10-20: LEC steps B / NegB (N1 == final netlists) of an RTL 6c4ccffd LEC folder whose gold / N1 part passed
# (PASS1_EQUALS_PASS2) and whose gate scripts were added by prepare_lec_6c4c.py --add-gates (two signed runs; for SA2 /
# DM_VC4 possibly two different final netlists, --allow-different-finals: step B proves N1 == each, B1 / B2).
# Generalises run_lec_dm_noor34_gates_20261020.sh: per pass p1, p2 the gate front end (run_frontends_vc4.ps1 -Part
# Gates), step B, step NegB (negative control: a mutated final netlist must give a counterexample); then
# compare_lec_passes.py p1 p2 -> pass_comparison_full.json. Each step waits for >= 8 GB available in the WSL VM.
# Rule Q: the first failing step ends the chain. Cooperative stop: create <results folder>/ABORT
#   bash run_lec_gates_6c4c_20261020.sh <results folder name> <label>
set -u
R=/e/Projects/RISCV-research
F=$1; LABEL=$2
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
say "$LABEL steps B / NegB start"
for p in p1 p2; do
    run $L/$p/frontend_gates.out "$LEC/run_frontends_vc4.ps1" -Work "$WL\\$p" -Part Gates
    run $L/$p/stepB.out "$LEC/run_lec_vc4.ps1" -Work "$WL\\$p" -Step B
    run $L/$p/stepNegB.out "$LEC/run_lec_vc4.ps1" -Work "$WL\\$p" -Step NegB
done
"$PY" -B "$R/asic/equiv/lec/compare_lec_passes.py" "$WL\\p1" "$WL\\p2" "$WL\\pass_comparison_full.json" > $L/compare_full.out 2>&1
say "$LABEL full compare exit $?: $(tail -1 $L/compare_full.out)"
say "$LABEL steps B / NegB done in both passes"
