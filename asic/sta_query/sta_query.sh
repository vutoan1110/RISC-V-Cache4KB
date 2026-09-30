#!/usr/bin/env bash
# Load one signed-off run at one corner exactly as STAPostPNR did (same
# libraries, SPEF, SDC, environment file; see asic/gls/sta_power.sh) and run
# a query script against it.
#
#   bash asic/sta_query/sta_query.sh <STAPostPNR step dir> <corner> <query.tcl>
set -euo pipefail
STEP=$(realpath "$1"); CORNER=$2; Q=$(realpath "$3")
D=$STEP/$CORNER
ENVF=$(ls "$D"/_env*.tcl | head -1)
LOG=$D/sta.log
LIBS=$(sed -n "s/^Reading cell library for the '$CORNER' corner at '\(.*\)'…$/\1/p" "$LOG" | tr '\n' ' ')
SPEF=$(sed -n "s/^Reading top-level design parasitics for the '$CORNER' corner at '\(.*\)'…$/\1/p" "$LOG")
SDC=$(sed -n "s/^Reading design constraints file at '\(.*\)'…$/\1/p" "$LOG" | head -1)
[ -n "$LIBS" ] && [ -n "$SPEF" ] && [ -n "$SDC" ] || { echo "[FAIL] could not parse libs/spef/sdc from $LOG" >&2; exit 2; }
export _SDC_IN=$SDC OPENLANE_SDC_IDEAL_CLOCKS=0
STA=/nix/store/q5ycjmn0d9awbcq05c75z2rmgwjgbc9g-opensta/bin/sta
export SCRIPTS_DIR=$(sed -n 's|^sta .* \(/.*/scripts\)/openroad/sta/corner.tcl$|\1|p' "$STEP/COMMANDS" | head -1)
[ -d "$SCRIPTS_DIR" ] || { echo "[FAIL] SCRIPTS_DIR not found from $STEP/COMMANDS" >&2; exit 2; }
export _TCL_ENV_IN=$ENVF _CURRENT_CORNER_NAME=$CORNER _CURRENT_CORNER_LIBS="$LIBS" \
       _CURRENT_CORNER_NETLISTS="" _CURRENT_SPEF_BY_CORNER=$SPEF SQ_QUERY=$Q
exec "$STA" -no_splash -exit "$(dirname "$(realpath "$0")")/sta_query.tcl"
