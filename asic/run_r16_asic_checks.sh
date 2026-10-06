#!/usr/bin/env bash
# R16 (FAST_HIT, review M1), rule D.2 + D.6 for the ASIC side, one step at a time (the SoC-level formal checks are
# memory-hungry: two of them together with PD coincided with the WSL VM going down on 2026-10-03 08:22).
#   1. OpenLane lint + synthesis of the DM chip on the R16 snapshot (config_R16_synth.json, tag r16_synth):
#      OpenLane lint baseline gate (scripts/lint_baseline_check.py) + netlist hash against r15_synth (information
#      only: ABC output depends on the read order, which is why R15 was proved by RTL equivalence instead)
#   2. DM chip: R14 PD input == R16 (equiv/r16_eq/run_r16_eq_dm.sh)
#   3. SA2 and DM_VC4 PD inputs == R16 at FAST_HIT 0 (equiv/r16_eq/run_r16_eq_soc.sh, one after the other)
# Summary: asic/r16_asic_checks.log. Cooperative stop between steps: touch asic/.abort_r16_checks
A=/mnt/e/Projects/RISCV-research/asic
L=$A/r16_asic_checks.log
: > $L
say () { echo "$(date -Is) $*" | tee -a $L; }
ram () { awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo; }
gate () {   # wait for $1 MB available, at most 2 h, honouring the abort flag
  for i in $(seq 1 120); do
    [ -f $A/.abort_r16_checks ] && { say "abort flag"; exit 3; }
    [ "$(ram)" -ge "$1" ] && return 0
    sleep 60
  done
  say "gave up waiting for $1 MB (have $(ram))"; exit 4
}
fail=0
gate 6000
say "1. OpenLane lint + synthesis r16_synth (avail $(ram) MB)"
cd $A && CONFIG=config_R16_synth.json bash run_pd_mk.sh soc_dm_4kb r16_synth --to Yosys.Synthesis > $A/r16_synth.log 2>&1
rc=$?; say "   flow rc=$rc"; [ $rc -eq 0 ] || fail=$((fail+1))
LINT=$A/soc_dm_4kb/runs/r16_synth/01-verilator-lint/verilator-lint.log
cd /mnt/e/Projects/RISCV-research && python3 scripts/lint_baseline_check.py $LINT asic/soc_dm_4kb/lint_baseline.tsv >> $L 2>&1
rc=$?; say "   lint baseline gate rc=$rc"; [ $rc -eq 0 ] || fail=$((fail+1))
N=$A/soc_dm_4kb/runs/r16_synth/06-yosys-synthesis/soc_asic_top.nl.v
O=$A/soc_dm_4kb/runs/r15_synth/06-yosys-synthesis/soc_asic_top.nl.v
sha256sum $O $N | sed 's#^#   #' >> $L
cmp -s $O $N && say "   netlist: R16 == R15 byte for byte" || say "   netlist: R16 differs from R15 (information only; equivalence is step 2)"
[ -f $A/.abort_r16_checks ] && { say "abort flag"; exit 3; }
gate 8000
say "2. DM SoC equivalence R14 PD input == R16 (avail $(ram) MB)"
bash $A/equiv/r16_eq/run_r16_eq_dm.sh >> $L 2>&1
rc=$?; say "   rc=$rc"; [ $rc -eq 0 ] || fail=$((fail+1))
[ -f $A/.abort_r16_checks ] && { say "abort flag"; exit 3; }
gate 16000
say "3. SA2 + DM_VC4 SoC equivalence, PD input == R16 FAST_HIT 0 (avail $(ram) MB)"
bash $A/equiv/r16_eq/run_r16_eq_soc.sh >> $L 2>&1
rc=$?; say "   rc=$rc"; [ $rc -eq 0 ] || fail=$((fail+1))
say "done: $fail failure(s)"
exit $fail
