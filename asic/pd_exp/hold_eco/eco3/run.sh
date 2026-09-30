#!/usr/bin/env bash
# FLOW_JOURNAL Incident 93: standalone run of the FLOW's post_route_hold_eco.tcl on x_E3's routed database
# with POST_ROUTE_ECO_REPAIR_DESIGN on (the x_E3R case that died with DRT-0218). Writes only here.
D=/mnt/e/Projects/RISCV-research/asic/pd_exp/hold_eco/eco3
export SCRIPTS_DIR=/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts
export _TCL_ENV_IN=$D/env_main.tcl STEP_DIR=$D SAVE_ODB=$D/eco3.odb
export _ECO_SPEF=/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/x_E3R/01-openroad-postrouteholdeco/eco.spef
export _SDC_IN=/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/x_E3/16-openroad-detailedrouting/soc_asic_top.sdc
V=/home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A
M=/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/macros/lib
export _MACRO_LIBS="$M/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib $M/sky130_sram_1kbyte_1rw1r_32x256_8_TT_1p8V_25C.lib"
export _PNR_LIBS="$V/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib $_MACRO_LIBS"
export _PNR_EXCLUDED_CELLS="$(grep -v '^[[:space:]]*#' $V/libs.tech/openlane/sky130_fd_sc_hd/drc_exclude.cells | tr -s '[:space:]' ' ')"
export RSZ_CORNER_0="nom_tt_025C_1v80 $V/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib $_MACRO_LIBS"
export RSZ_CORNER_1="nom_ss_100C_1v60 $V/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ss_100C_1v60.lib $_MACRO_LIBS"
export RSZ_CORNER_2="nom_ff_n40C_1v95 $V/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ff_n40C_1v95.lib $_MACRO_LIBS"
export OMP_NUM_THREADS=1
OR=/nix/store/alhgaybdgmv706469rp57ggcyg3750yk-openroad-python3-3.11.9-env/bin/openroad
cd $D
echo "$(date -Is) start" >> status.txt
/usr/bin/time -f "%e s %M kB" $OR -exit -no_splash ${S:-$SCRIPTS_DIR/openroad/post_route_hold_eco.tcl} > ${LOGN:-eco3.log} 2>&1
echo "$(date -Is) end rc=$?" >> status.txt
