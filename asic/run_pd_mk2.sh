#!/usr/bin/env bash
# OpenLane 2 launcher for the research ASIC points.
# run_pd_mk2.sh = run_pd_mk.sh + GNU grep on PATH for EQY's partition scripts (Incident 91).
# run_pd_mk.sh = run_pd.sh + GNU make on PATH for EQY (Incident 78); a copy,
# because run_pd.sh was executing when the fix was found.
#
#   usage: run_pd.sh <DESIGN_DIR_NAME> <RUN_TAG> [extra openlane args...]
#   e.g.   run_pd.sh soc_dm_dse dmdse_synth --to Yosys.Synthesis
#   CONFIG=config_E1.json run_pd.sh ...   alternative config file in the design dir (experiments)
#
# Adapted from asic/openlane2/run_sram_wsl.sh. Two differences: it points at
# research/asic instead of the frozen design, and it does not touch
# RUN_TRACKER.md, which belongs to the published flow. Its own log goes to
# research/asic/pd_log.md.
set -uo pipefail

OPENLANE_ROOT=${OPENLANE_ROOT:-/home/toanl/tools/src/openlane2}
# Everything is located relative to this script, so the tree can be moved
# without editing anything. It used to hardcode an absolute path into the
# repository, which broke the moment research/ was relocated out of it.
ASIC_DIR=$(cd "$(dirname "$0")" && pwd)
DESDIR="$1"; shift
TAG="$1"; shift
DES=$ASIC_DIR/$DESDIR
LOG=$ASIC_DIR/pd_log.md

if [ ! -f "$DES/${CONFIG:-config.json}" ]; then
  echo "[FAIL] no config.json in $DES" >&2
  exit 2
fi

# Pin OpenMP to one thread. antenna_repair.tcl never calls set_thread_count, so
# OpenROAD runs that region across every core and has been caught in a data race
# there (SIGSEGV in AntennaChecker::calculateAreas). drt.tcl does call
# set_thread_count, so detailed routing still runs fully parallel.
OMP_THREADS=${OMP_THREADS:-1}

# Use the patched OpenLane if present: the stock antenna report summariser
# prints an unconditional 942-row rich table and crashes non-deterministically.
# A private copy of the OpenLane package lives in the tree, so its scripts can
# be fixed without touching the shared install. Two separate crashes in
# odbpy/disconnected_pins.py have now stopped the flow at step 47, and the
# second one reported an UnboundLocalError on the line that assigns the
# variable -- which cannot happen unless the running bytecode differs from the
# file on disk. The shared tree carried a __pycache__; this copy does not.
OL_PATCHED=${OL_PATCHED:-$(cd "$(dirname "$0")" && pwd)/openlane-local}
if [ -f "$OL_PATCHED/openlane/steps/openroad.py" ]; then
  PYPATH_PREFIX="PYTHONPATH='$OL_PATCHED'"
else
  echo "[!] no patched openlane at $OL_PATCHED - using the stock one" >&2
  PYPATH_PREFIX=""
fi

# Preserve each argument's quoting: some values contain spaces.
# Resuming into an existing run must NOT pass --overwrite, or OpenLane wipes
# the very state being resumed from. A --from into a fresh tag fails with
# "missing required input ODB", because step state belongs to the tag.
#   RESUME=1 run_pd.sh <design> <existing-tag> --from <StepID>
if [ "${RESUME:-0}" = "1" ]; then OVERWRITE=""; else OVERWRITE="--overwrite"; fi

ARGS=""
for a in "$@"; do ARGS="$ARGS $(printf '%q' "$a")"; done

# WSL reports a 131072x1 terminal, which breaks rich inside the antenna summary.
export COLUMNS=200 LINES=50 TERM=xterm-256color

printf '\n- START `%s` (%s) args: `%s` at %s\n' \
  "$TAG" "$DESDIR" "${ARGS:-full flow}" "$(date -Is)" >> "$LOG"

# Pin OpenMP before nix-shell as well as inside it. --pure strips the
# environment, so the inline assignment on --run is what actually reaches
# openroad, but exporting here too means anything spawned outside that
# command inherits it. OpenROAD has been caught segfaulting inside an
# OpenMP region in the antenna checker.
export OMP_NUM_THREADS=$OMP_THREADS
export OPENBLAS_NUM_THREADS=$OMP_THREADS

. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
cd "$DES"
# tarball-ttl: nix re-fetches a flake input once its TTL lapses, and this
# machine currently cannot reach api.github.com at all (TCP connects, the TLS
# ClientHello goes out, no ServerHello comes back -- same from Windows, so it
# is the network path). The inputs are already in the store, so pin the TTL to
# a year and nix uses them instead of trying to refresh.
# Global routing's timing-driven paths crash on this host: four segfaults in
# four different functions, every one of them inside the GRT-to-STA
# interaction. The patched common/grt.tcl honours these two when set; unset
# means stock behaviour. --pure strips the environment, so they are assigned
# inline on the --run command, which is what actually reaches openroad.
GRT_ENV=""
[ -n "${GRT_ROUTING_ALPHA:-}" ] && GRT_ENV="$GRT_ENV GRT_ROUTING_ALPHA=$GRT_ROUTING_ALPHA"
[ -n "${GRT_CRITICAL_NETS_PCT:-}" ] && GRT_ENV="$GRT_ENV GRT_CRITICAL_NETS_PCT=$GRT_CRITICAL_NETS_PCT"

# OpenLane's shell.nix has no GNU make and --pure hides the system one, so
# EQY's proof stage (make -f strategies.mk) died with 'make: command not
# found' right after a good partition (FLOW_JOURNAL Incident 78).
MAKE_BIN=/nix/store/9y5kd90fdbrq3r4yc9mpqn82f93zdgyq-gnumake-4.4.1/bin
# run_pd_mk2.sh (FLOW_JOURNAL Incident 91): the EQY partition scripts (strategy run.sh) also call grep,
# which --pure hides too ("./run.sh: line 2: grep: command not found", final2_A step 72). Same fix.
MAKE_BIN=$MAKE_BIN:/nix/store/28gpmx3z6ss3znd7fhmrzmvk3x5lnfbk-gnugrep-3.11/bin
nix-shell --option tarball-ttl 31536000 --pure --keep OMP_NUM_THREADS --keep OPENBLAS_NUM_THREADS "$OPENLANE_ROOT/shell.nix" --run \
  "PATH=$MAKE_BIN:\$PATH COLUMNS=200 LINES=50 OMP_NUM_THREADS=$OMP_THREADS$GRT_ENV $PYPATH_PREFIX openlane --log-level INFO --condensed --run-tag '$TAG' $OVERWRITE $ARGS '$DES/${CONFIG:-config.json}'"
RC=$?

LAST=$(ls -1d "$DES/runs/$TAG"/*/ 2>/dev/null | grep -v '/tmp/$' | tail -1 \
       | sed 's|.*/\([^/]*\)/$|\1|')
ERR=$(head -c 200 "$DES/runs/$TAG/error.log" 2>/dev/null | tr '\n' ' ')
if [ -d "$DES/runs/$TAG/final" ]; then
  printf -- '- DONE `%s` rc=%s last=`%s` final/ present\n' "$TAG" "$RC" "$LAST" >> "$LOG"
elif [ -n "$ERR" ]; then
  printf -- '- STOP `%s` rc=%s last=`%s` err: `%s`\n' "$TAG" "$RC" "$LAST" "$ERR" >> "$LOG"
else
  printf -- '- ODD `%s` rc=%s last=`%s` empty error.log, suspect a native crash\n' \
    "$TAG" "$RC" "$LAST" >> "$LOG"
fi
exit $RC
