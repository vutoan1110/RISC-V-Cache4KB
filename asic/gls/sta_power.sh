#!/usr/bin/env bash
# Power of a signed-off run at one corner, vectorless or from a SAIF file.
#
#   bash asic/gls/sta_power.sh <STAPostPNR step dir> [saif] [corner]
#
# Runs in WSL. The libraries, netlist and SPEF are taken from what the step's
# own sta.log says it read for that corner, so this reproduces the flow's
# power.rpt exactly when no SAIF is given (checked before any SAIF result is
# trusted). Output: the report on stdout.
set -euo pipefail
STEP=$(realpath "$1"); SAIF=${2:-}; CORNER=${3:-nom_tt_025C_1v80}
D=$STEP/$CORNER
ENVF=$(ls "$D"/_env*.tcl | head -1)
LOG=$D/sta.log
LIBS=$(sed -n "s/^Reading cell library for the '$CORNER' corner at '\(.*\)'…$/\1/p" "$LOG" | tr '\n' ' ')
SPEF=$(sed -n "s/^Reading top-level design parasitics for the '$CORNER' corner at '\(.*\)'…$/\1/p" "$LOG")
SDC=$(sed -n "s/^Reading design constraints file at '\(.*\)'…$/\1/p" "$LOG" | head -1)
[ -n "$LIBS" ] && [ -n "$SPEF" ] && [ -n "$SDC" ] || { echo "[FAIL] could not parse libs/spef/sdc from $LOG" >&2; exit 2; }
# STAPostPNR's own settings (steps/openroad.py): signoff SDC, propagated clocks
export _SDC_IN=$SDC OPENLANE_SDC_IDEAL_CLOCKS=0
# the exact build OpenLane's devshell runs (devshell-dir/bin/sta resolves to it)
STA=/nix/store/q5ycjmn0d9awbcq05c75z2rmgwjgbc9g-opensta/bin/sta
echo "PW_INFO sta=$STA corner=$CORNER spef=$SPEF"
# SCRIPTS_DIR: the tree the step's COMMANDS file points at (the patched copy)
export SCRIPTS_DIR=$(sed -n 's|^sta .* \(/.*/scripts\)/openroad/sta/corner.tcl$|\1|p' "$STEP/COMMANDS" | head -1)
[ -d "$SCRIPTS_DIR" ] || { echo "[FAIL] SCRIPTS_DIR not found from $STEP/COMMANDS" >&2; exit 2; }
export _TCL_ENV_IN=$ENVF _CURRENT_CORNER_NAME=$CORNER _CURRENT_CORNER_LIBS="$LIBS" \
       _CURRENT_CORNER_NETLISTS="" _CURRENT_SPEF_BY_CORNER=$SPEF PW_SAIF=${SAIF:+$(realpath "$SAIF")}
exec "$STA" -no_splash -exit "$(dirname "$(realpath "$0")")/power_saif.tcl"
