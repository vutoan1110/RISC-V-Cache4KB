#!/usr/bin/env bash
# 2026-10-20: LEC steps B / NegB (N1 == final netlist) of the DM recipe with the or3 / or4 exclusion, two independent
# passes in results/lec_dm_noor34_20261020/p1, p2 (gold / N1 part already PASS1_EQUALS_PASS2 the same day). Gate
# netlists: the acceptance run dm_grid3665x2900_rtl6c4c_rsztf_tdp_rszctsall_noor34_rcrep_r1 and the development run
# ..._noor34_r1; their final netlists are byte-identical (sha256 40d108e0...), so the proof binds that netlist hash.
# Per pass: front end Gates (run_frontends_vc4.ps1), step B, step NegB (negative control: a counterexample is required);
# then compare_lec_passes.py-style verdict comparison. Each step waits for >= 8 GB free in the WSL VM (PD shares it).
# Rule Q: the first failing step ends the chain. Cooperative stop: results/lec_6c4c_20261015.ABORT
set -u
R=/e/Projects/RISCV-research
LEC='E:/Projects/RISCV-research/asic/equiv/lec'
LOG=$R/results/lec_6c4c_20261015_chain.log
L=$R/results/lec_dm_noor34_20261020
WL='E:\Projects\RISCV-research\results\lec_dm_noor34_20261020'
say () { echo "$(date -u +%FT%TZ) $*" | tee -a $LOG; }
memwait () {
    until [ "$(MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu -e bash -c "free -m | awk '/Mem/{print \$7}'" 2>/dev/null | tr -dc 0-9)" -ge 8000 ] 2>/dev/null; do
        [ -e $R/results/lec_6c4c_20261015.ABORT ] && return 1
        sleep 60
    done
}
run () {
    local log=$1; shift
    [ -e $R/results/lec_6c4c_20261015.ABORT ] && { say "ABORT before $log"; return 2; }
    memwait || { say "ABORT while waiting for memory before $log"; return 2; }
    pwsh -NoProfile -File "$@" > "$log" 2>&1
    local rc=$?
    say "lec_dm_noor34_20261020/$(basename $(dirname $log))/$(basename $log) exit $rc"
    [ $rc -eq 0 ] || { say "STOP: $(basename $log) failed (rule Q)"; tail -5 "$log" | tee -a $LOG; }
    return $rc
}
say "dm noor34 steps B / NegB start (final netlist 40d108e0, acceptance r1 + development noor34_r1)"
for p in p1 p2; do
    run $L/$p/frontend_gates.out "$LEC/run_frontends_vc4.ps1" -Work "$WL\\$p" -Part Gates || exit 1
    run $L/$p/stepB.out "$LEC/run_lec_vc4.ps1" -Work "$WL\\$p" -Step B || exit 1
    run $L/$p/stepNegB.out "$LEC/run_lec_vc4.ps1" -Work "$WL\\$p" -Step NegB || exit 1
done
say "dm noor34 steps B / NegB done in both passes"
