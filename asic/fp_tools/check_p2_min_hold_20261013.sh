#!/usr/bin/env bash
# Controls for the P2_MIN_HOLD option of gate_check.py (2026-10-13), on finished runs, read-only.
A=/mnt/e/Projects/RISCV-research/asic
S2=$A/soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1
V4=$A/soc_vc4_4kb/runs/vc4_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_r1
for i in 1 2; do
  echo "== pass $i"
  echo -n "SA2 default (expect FAIL): ";                       python3 $A/fp_tools/gate_check.py $S2 p2; echo " rc=$?"
  echo -n "SA2 P2_MIN_SETUP=0 P2_MIN_HOLD=-0.5 (expect PASS): "; P2_MIN_SETUP=0 P2_MIN_HOLD=-0.5 python3 $A/fp_tools/gate_check.py $S2 p2; echo " rc=$?"
  echo -n "SA2 P2_MIN_HOLD=-0.1 (expect FAIL): ";               P2_MIN_SETUP=0 P2_MIN_HOLD=-0.1 python3 $A/fp_tools/gate_check.py $S2 p2; echo " rc=$?"
  echo -n "VC4 fallback default (expect FAIL): ";                P2_INITIAL_GRT_FALLBACK=1 P2_MIN_SETUP=0 python3 $A/fp_tools/gate_check.py $V4 p2; echo " rc=$?"
  echo -n "VC4 fallback P2_MIN_HOLD=-0.5 (expect PASS): ";       P2_INITIAL_GRT_FALLBACK=1 P2_MIN_SETUP=0 P2_MIN_HOLD=-0.5 python3 $A/fp_tools/gate_check.py $V4 p2; echo " rc=$?"
done
