#!/usr/bin/env bash
# DM acceptance run required by rule Q (revised 2026-10-14): the locked DM recipe (config_R14_FINAL.json, frozen
# rtl_r14 snapshot; r14F_A / r14F_B = dm_grid3665x2900_r1 / _r2 were resumed after the 2026-09-30 session-end kill) as
# ONE complete flow from step 1 under the gated driver with its DEFAULT gates (r14F_A passes p1 / p2 / final with them).
# Expected: the r14F_A fill-insertion netlist byte for byte (sha256 83f38f7e0e7efa24...). Launch only when no detailed routing / sign-off of
# another run is active (one heavy phase at a time in the 24 GB WSL VM).
A=/mnt/e/Projects/RISCV-research/asic
cd $A && G5_UNLIMITED_LATE_PHASE=1 \
  ITEMS="soc_dm_4kb:dm_grid3665x2900_r3:config_R14_FINAL.json" \
  bash run_gated_pd.sh
