#!/usr/bin/env bash
# R16 SoC-level formal checks for the SA2 / DM_VC4 PD inputs, second attempt (2026-10-06): the first one paired no
# cache register (genblk1.g_dse vs g_dse, see equiv/r16_eq/rename_genblk.py) and was stopped. Runs, one at a time
# and alone (each needs ~16 GB): SA2 FAST_HIT 0 (must be equivalent), SA2 FAST_HIT 1 (negative control, must
# leave unproven cells), DM_VC4 FAST_HIT 0 (must be equivalent). Starts only with >= 16 GB available.
# Summary: equiv/r16_eq/r16_eq_summary_soc.txt + r16_eq_verdict.txt; log asic/r16_asic_checks.log (appended).
A=/mnt/e/Projects/RISCV-research/asic
L=$A/r16_asic_checks.log
say () { echo "$(date -Is) $*" | tee -a $L; }
for i in $(seq 1 240); do
  [ -f $A/.abort_r16_checks ] && { say "abort flag before the SoC checks"; exit 3; }
  [ "$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)" -ge 16000 ] && break
  sleep 60
done
say "3b. SoC equivalence (renamed gate) SA2 fast0, SA2 fast1 (negative control), DM_VC4 fast0 (avail $(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo) MB)"
bash $A/equiv/r16_eq/run_r16_eq_soc.sh >> $L 2>&1
rc=$?
cd /mnt/e/Projects/RISCV-research && python3 asic/equiv/r16_eq/summarize_r16_eq.py asic/equiv/r16_eq/r16_eq_summary_mod.txt \
    asic/equiv/r16_eq/r16_eq_summary_dm.txt asic/equiv/r16_eq/r16_eq_summary_soc.txt | tail -5 >> $L 2>&1
v=$?
say "   SoC runner rc=$rc, verdict rc=$v"
exit $v
