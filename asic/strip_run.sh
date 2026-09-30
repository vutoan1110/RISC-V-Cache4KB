#!/usr/bin/env bash
# Strip the five unparseable annotation layers from the SRAM macro GDS and prove
# the result is geometry-identical. See strip_macro_annotation_layers.py.
set -uo pipefail
. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
ASIC=/mnt/e/Projects/RISCV-research/asic
G=$ASIC/soc_dm_control/macros/gds
export MACRO_GDS=$G/sky130_sram_2kbyte_1rw1r_32x512_8.gds
export MACRO_GDS_OUT=$G/sky130_sram_2kbyte_1rw1r_32x512_8.magicsafe.gds
cd "$ASIC/soc_dm_control"
nix-shell --option tarball-ttl 31536000 --pure --keep MACRO_GDS --keep MACRO_GDS_OUT \
  /home/toanl/tools/src/openlane2/shell.nix --run \
  "klayout -b -r $ASIC/strip_macro_annotation_layers.py"
