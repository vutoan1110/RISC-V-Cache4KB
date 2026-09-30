#!/usr/bin/env bash
set -uo pipefail
. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
ASIC=/mnt/e/Projects/RISCV-research/asic
export MACRO_GDS=$ASIC/soc_dm_control/macros/gds/sky130_sram_2kbyte_1rw1r_32x512_8.magicsafe.gds
cd "$ASIC/soc_dm_control"
nix-shell --option tarball-ttl 31536000 --pure --keep MACRO_GDS \
  /home/toanl/tools/src/openlane2/shell.nix --run "klayout -b -r $ASIC/list_gds_cells.py"
