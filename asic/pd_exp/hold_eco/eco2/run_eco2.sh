#!/usr/bin/env bash
# FLOW_JOURNAL Incident 93: standalone post-route hold ECO test (reads x_E1, writes only here).
#   bash run_eco2.sh <full_grt|no_grt>
D=/mnt/e/Projects/RISCV-research/asic/pd_exp/hold_eco/eco2
MODE=$1
export ECO_MODE=$MODE
export SCRIPTS_DIR=/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts
export _TCL_ENV_IN=$D/env_main.tcl STEP_DIR=$D
export _ECO_SPEF=/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/x_E1H/01-openroad-postrouteholdeco/eco.spef
export _SDC_IN=/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/x_E1/15-openroad-detailedrouting/soc_asic_top.sdc
V=/home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A
M=/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/macros/lib
export _MACRO_LIBS="$M/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib $M/sky130_sram_1kbyte_1rw1r_32x256_8_TT_1p8V_25C.lib"
export _PNR_LIBS="$V/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib $_MACRO_LIBS"
export _PNR_EXCLUDED_CELLS="$(grep -v '^[[:space:]]*#' $V/libs.tech/openlane/sky130_fd_sc_hd/drc_exclude.cells | tr -s '[:space:]' ' ')"
export OMP_NUM_THREADS=1
OR=/nix/store/alhgaybdgmv706469rp57ggcyg3750yk-openroad-python3-3.11.9-env/bin/openroad
cd $D
echo "$(date -Is) start $MODE" >> status.txt
/usr/bin/time -f "%e s %M kB" $OR -exit -no_splash $D/eco2_test.tcl > eco2_$MODE.log 2>&1
echo "$(date -Is) end $MODE rc=$?" >> status.txt
