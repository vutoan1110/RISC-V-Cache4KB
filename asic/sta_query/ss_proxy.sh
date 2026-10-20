#!/usr/bin/env bash
# 2026-10-15 ss study: early ss estimate of a PD run from its post-GRT database (see ss_proxy.tcl).
#   bash ss_proxy.sh <run dir> <output file> [placement|grt] [step dir glob, default *-openroad-resizertimingpostgrt]
# Uses the step's own environment file and output database; overrides only the resizer corners (tt / ss / ff with the
# run's macro libraries), the database path and the RC scope. Read only for the run directory.
set -euo pipefail
RUN=$(realpath "$1"); OUT=$2; EST=${3:-placement}; GLOB=${4:-*-openroad-resizertimingpostgrt}
STEP=$(ls -d $RUN/$GLOB 2>/dev/null | tail -1)
[ -n "$STEP" ] && [ -f "$STEP/_env.tcl" ] && [ -f "$STEP/soc_asic_top.odb" ] || { echo "[FAIL] no step $GLOB with _env.tcl and odb in $RUN" >&2; exit 2; }
V=/home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A
L=$V/libs.ref/sky130_fd_sc_hd/lib
# macro libraries = everything after the first library of the step's first resizer corner
MAC=$(sed -n 's/^set ::env(RSZ_CORNER_0) "\(.*\)"$/\1/p' "$STEP/_env.tcl" | cut -d' ' -f3-)
[ -n "$MAC" ] || { echo "[FAIL] no RSZ_CORNER_0 in $STEP/_env.tcl" >&2; exit 2; }
TMP=$(mktemp -d)
trap 'rm -rf $TMP' EXIT
ENVF=$TMP/env.tcl
grep -v -E '^set ::env\((RSZ_CORNER_[0-9]+|CURRENT_ODB|LAYERS_RC_SCOPE|STEP_DIR)\)' "$STEP/_env.tcl" > $ENVF
{
    echo "set ::env(RSZ_CORNER_0) \"nom_tt_025C_1v80 $L/sky130_fd_sc_hd__tt_025C_1v80.lib $MAC\""
    echo "set ::env(RSZ_CORNER_1) \"nom_ss_100C_1v60 $L/sky130_fd_sc_hd__ss_100C_1v60.lib $MAC\""
    echo "set ::env(RSZ_CORNER_2) \"nom_ff_n40C_1v95 $L/sky130_fd_sc_hd__ff_n40C_1v95.lib $MAC\""
    echo "set ::env(CURRENT_ODB) $STEP/soc_asic_top.odb"
    echo "set ::env(LAYERS_RC_SCOPE) ${SQ_RC_SCOPE:-all}"
    echo "set ::env(STEP_DIR) $TMP"
} >> $ENVF
grep -q '^set ::env(LAYERS_RC) ' $ENVF || echo "set ::env(LAYERS_RC) \"$(cat /mnt/e/Projects/RISCV-research/asic/pd_exp/rc_corr/layers_rc_k2.txt)\"" >> $ENVF
export _TCL_ENV_IN=$ENVF SQ_EST=$EST _SDC_IN=$STEP/soc_asic_top.sdc
# 2026-10-15: without a thread limit the global route of the SA2 run hung in a futex wait (2 threads, 0 % CPU for
# 20 min); with 8 threads the same input finished in 3 min.
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-8}
export SCRIPTS_DIR=/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts
export _MACRO_LIBS="$MAC" _PNR_LIBS="$L/sky130_fd_sc_hd__tt_025C_1v80.lib $MAC"
export _PNR_EXCLUDED_CELLS="$(grep -v '^[[:space:]]*#' $V/libs.tech/openlane/sky130_fd_sc_hd/drc_exclude.cells | tr -s '[:space:]' ' ')"
OR=/nix/store/alhgaybdgmv706469rp57ggcyg3750yk-openroad-python3-3.11.9-env/bin/openroad
{ echo "SS_PROXY run $RUN step $(basename $STEP) est $EST"; /usr/bin/time -f "SS_PROXY time %e s peak %M kB" $OR -exit -no_splash "$(dirname "$(realpath "$0")")/ss_proxy.tcl" 2>&1; } > "$OUT"
grep -E '^SS_PROXY (run|nom_|time)' "$OUT"
