#!/usr/bin/env bash
# Standalone check of the two-pass PostRouteHoldECO (2026-10-13): the step of
# sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1 (max_*) re-run from its own state_in with a second
# min_* pass. Expected: pass1/ reproduces r1 step 47, the final views reproduce step 48 of ..._ecomaxmin_r1.
set -uo pipefail
HERE=/mnt/e/Projects/RISCV-research/asic/soc_sa2_4kb/eco2pass_check_20261013
R1=/mnt/e/Projects/RISCV-research/asic/soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1
OL=/mnt/e/Projects/RISCV-research/asic/openlane-local
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 COLUMNS=200 LINES=50 TERM=xterm-256color
. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
cd "$HERE"
nix-shell --option tarball-ttl 31536000 --pure --keep OMP_NUM_THREADS --keep OPENBLAS_NUM_THREADS /home/toanl/tools/src/openlane2/shell.nix --run \
  "COLUMNS=200 LINES=50 OMP_NUM_THREADS=1 PYTHONPATH='$OL' python3 -m openlane.steps run -c '$HERE/config_2pass.json' -i '$R1/47-openroad-postrouteholdeco/state_in.json' -o '$HERE/step'"
echo "exit $?"
