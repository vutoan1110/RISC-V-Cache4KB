#!/usr/bin/env bash
# Hold-slack histogram at the input of OpenROAD.ResizerTimingPostCTS of one run.
#   bash run.sh <run name> <resizertimingpostcts step dir name>
# e.g. bash run.sh r14_E10 07-openroad-resizertimingpostcts
set -u
D=/mnt/e/Projects/RISCV-research/asic/pd_exp/hold_hist
RUN=/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/$1
STEP=$RUN/$2
export SCRIPTS_DIR=/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts
export _TCL_ENV_IN=$STEP/_env.tcl STEP_DIR=$D
export _SDC_IN=/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/soc.sdc
V=/home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A
M=/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/macros/lib
export _MACRO_LIBS="$M/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib $M/sky130_sram_1kbyte_1rw1r_32x256_8_TT_1p8V_25C.lib"
export _PNR_LIBS="$V/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib $_MACRO_LIBS"
export _PNR_EXCLUDED_CELLS="$(grep -v '^[[:space:]]*#' $V/libs.tech/openlane/sky130_fd_sc_hd/drc_exclude.cells | tr -s '[:space:]' ' ')"
export OMP_NUM_THREADS=1
cd $D && /nix/store/alhgaybdgmv706469rp57ggcyg3750yk-openroad-python3-3.11.9-env/bin/openroad -exit -no_splash \
    $D/hold_hist.tcl > $D/hold_hist_$1.log 2>&1
echo "rc=$? $1"
grep '^HH' $D/hold_hist_$1.log
