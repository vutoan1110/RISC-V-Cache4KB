#!/usr/bin/env bash
# 2026-10-20 DM_VC4 congestion study (see grt_hotspot.tcl): global-route a step's output database with few congestion
# iterations and report where overflow remains.
#   bash grt_hotspot.sh <run dir> <step dir glob> <output dir> [iterations, default 15]
# Uses the step's own environment file; overrides only the database path and STEP_DIR. Read only for the run.
set -euo pipefail
RUN=$(realpath "$1"); GLOB=$2; OUT=$(realpath -m "$3"); IT=${4:-15}
STEP=$(ls -d $RUN/$GLOB 2>/dev/null | tail -1)
[ -n "$STEP" ] && [ -f "$STEP/_env.tcl" ] && [ -f "$STEP/soc_asic_top.odb" ] || { echo "[FAIL] no step $GLOB with _env.tcl and odb in $RUN" >&2; exit 2; }
mkdir -p "$OUT"
TMP=$(mktemp -d)
trap 'rm -rf $TMP' EXIT
ENVF=$TMP/env.tcl
grep -v -E '^set ::env\((CURRENT_ODB|STEP_DIR)\)' "$STEP/_env.tcl" > $ENVF
{ echo "set ::env(CURRENT_ODB) $STEP/soc_asic_top.odb"; echo "set ::env(STEP_DIR) $TMP"; } >> $ENVF
V=/home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A
L=$V/libs.ref/sky130_fd_sc_hd/lib
MAC=$(sed -n 's/^set ::env(RSZ_CORNER_0) "\(.*\)"$/\1/p' "$STEP/_env.tcl" | cut -d' ' -f3-)
export _MACRO_LIBS="$MAC" _PNR_LIBS="$L/sky130_fd_sc_hd__tt_025C_1v80.lib $MAC"
export _PNR_EXCLUDED_CELLS="$(grep -v '^[[:space:]]*#' $V/libs.tech/openlane/sky130_fd_sc_hd/drc_exclude.cells | tr -s '[:space:]' ' ')"
export _TCL_ENV_IN=$ENVF SQ_GRT_ITERS=$IT SQ_CONG_OUT=$OUT/congestion_it$IT.rpt
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-8}
export SCRIPTS_DIR=/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts
OR=/nix/store/alhgaybdgmv706469rp57ggcyg3750yk-openroad-python3-3.11.9-env/bin/openroad
{ echo "GRT_HOTSPOT run $RUN step $(basename $STEP) iterations $IT"; /usr/bin/time -f "GRT_HOTSPOT time %e s peak %M kB" $OR -exit -no_splash "$(dirname "$(realpath "$0")")/grt_hotspot.tcl" 2>&1; } > "$OUT/grt_it$IT.log"
grep -E '^GRT_HOTSPOT|GRT-0096|GRT-0103|GRT-0018|^Total' "$OUT/grt_it$IT.log"
