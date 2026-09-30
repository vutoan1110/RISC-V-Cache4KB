#!/usr/bin/env bash
# Kill OpenLane runs that have stopped making progress -- by either measure.
#
# The host produces three kinds of stuck process, and the first version of this
# watchdog only caught one of them:
#
#  1. idle hang -- OpenROAD exits, the Python parent waits forever on a dead
#     reader thread's lock. Under 1 % CPU, state S, futex_wait_queue.
#  2. spinning hang -- the tool burns a full core and produces nothing. Observed
#     on Odb.ReportDisconnectedPins: 99.9 % CPU, RSS steady at 144 MB, step log
#     0 lines and the output table 0 bytes, unchanged over twenty seconds. The
#     CPU test never fires, so this blocked the retry driver for roughly twelve
#     hours.
#  3. honest long step -- two shapes, both must survive:
#       ResizerTimingPostGRT runs 32 minutes at 99 % and its log grows throughout
#       Magic.WriteLEF runs 4 minutes at 8 GiB and writes NOTHING until the end,
#       and Magic.DRC / CheckAntennas are similar. A five-window no-output rule
#       killed WriteLEF twice at 89 % CPU before this was understood.
#
# So "no output" alone is not enough either. What separated the real spin from
# WriteLEF was memory: the spin sat at 144 MB unchanged for twelve hours, while
# WriteLEF climbs to 8 GiB. The test below therefore requires no output growth
# AND no RSS movement, for thirty windows -- half an hour, which is longer than
# any legitimate silent step here and still catches a twelve-hour spin quickly.
#
# So CPU alone cannot separate (2) from (3). What separates them is output: a
# healthy step writes. This watchdog therefore kills when BOTH the step
# directory has stopped growing AND enough time has passed, regardless of CPU,
# and still kills the idle case on the CPU test alone.
set -uo pipefail
IDLE_PCT=${IDLE_PCT:-3}          # CPU below this over the window = idle hang
MIN_AGE=${MIN_AGE:-240}          # seconds, so a slow start is not killed
SAMPLE=${SAMPLE:-60}
STALL_WINDOWS=${STALL_WINDOWS:-30} # consecutive windows with no output AND no RSS movement
TAG=${TAG:-ch4kb}
RUN=${RUN:-/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/$TAG}

echo "[watchdog] start $(date -Is) idle<${IDLE_PCT}% age>${MIN_AGE}s window=${SAMPLE}s stall=${STALL_WINDOWS} windows"

# Total bytes written under the newest step directory.
out_size () {
  local d
  d=$(ls -1d "$RUN"/[0-9]*/ 2>/dev/null | sed 's|/$||' | sort -t- -k1,1n | tail -1)
  [ -n "$d" ] || { echo 0; return; }
  du -sb "$d" 2>/dev/null | cut -f1
}

# CPU ticks across the whole tree. Two traps, both hit in practice:
#
#  * the tool is not always openroad. Magic.WriteLEF runs `magic`, KLayout steps
#    run python; matching only "openroad" missed the process doing the work.
#  * the process set changes between samples, so a naive sum can FALL, giving a
#    negative delta. The idle test then reads cpu=-350% and fires on a step
#    running at 92 %. That killed Magic.WriteLEF about ninety times over four
#    hours before it was caught.
#
# So: match every tool this flow runs, and treat a negative delta as "the set
# moved", not as "idle".
tree_cpu () {
  local root=$1 total=0 p v
  for p in $root $(pgrep -P "$root" 2>/dev/null)            $(pgrep -f "openroad.*$TAG" 2>/dev/null)            $(pgrep -x magic 2>/dev/null) $(pgrep -f "magicdnull" 2>/dev/null)            $(pgrep -f "klayout.*$TAG" 2>/dev/null)            $(pgrep -f "netgen.*$TAG" 2>/dev/null)            $(pgrep -f "yosys.*$TAG" 2>/dev/null); do
    v=$(awk '{print $14+$15}' "/proc/$p/stat" 2>/dev/null) || continue
    total=$((total + v))
  done
  echo "$total"
}

stall=0; last_size=-1; last_rss=-1
while true; do
  pid=$(pgrep -f "openlane-wrapped.*$TAG" | head -1)
  if [ -z "$pid" ]; then sleep "$SAMPLE"; stall=0; last_size=-1; last_rss=-1; continue; fi
  age=$(ps -o etimes= -p "$pid" 2>/dev/null | tr -d ' ')
  [ -n "$age" ] || { sleep "$SAMPLE"; continue; }

  t1=$(tree_cpu "$pid"); s1=$(out_size)
  sleep "$SAMPLE"
  t2=$(tree_cpu "$pid"); s2=$(out_size)
  if [ "$t2" -lt "$t1" ]; then
    # the process set changed under us; this window says nothing
    stall=0; last_rss=-1; continue
  fi
  pct=$(( (t2 - t1) / SAMPLE ))

  # RSS of the whole tree, in KiB. A spin holds still; WriteLEF climbs.
  rss_now=0
  for p in $pid $(pgrep -P "$pid" 2>/dev/null) $(pgrep -f "openroad.*$TAG" 2>/dev/null); do
    v=$(awk '/^VmRSS:/{print $2}' "/proc/$p/status" 2>/dev/null) || continue
    rss_now=$((rss_now + ${v:-0}))
  done
  rss_delta=$(( rss_now > last_rss ? rss_now - last_rss : last_rss - rss_now ))
  # under 8 MiB of movement across a minute counts as held still
  if [ "$s2" = "$s1" ] && [ "$last_rss" -ge 0 ] && [ "$rss_delta" -lt 8192 ]; then
    stall=$((stall + 1))
  else
    stall=0
  fi
  last_rss=$rss_now

  if [ "$age" -lt "$MIN_AGE" ]; then continue; fi

  if [ "$pct" -lt "$IDLE_PCT" ]; then
    echo "[watchdog] $(date -Is) IDLE pid=$pid age=${age}s cpu=${pct}% -- killing"
    kill -TERM "$pid" 2>/dev/null; sleep 5; kill -KILL "$pid" 2>/dev/null
    pkill -9 -f "openroad.*$TAG" 2>/dev/null
    stall=0; continue
  fi

  if [ "$stall" -ge "$STALL_WINDOWS" ]; then
    echo "[watchdog] $(date -Is) NO-OUTPUT pid=$pid age=${age}s cpu=${pct}% no growth for $((stall*SAMPLE))s -- killing"
    kill -TERM "$pid" 2>/dev/null; sleep 5; kill -KILL "$pid" 2>/dev/null
    pkill -9 -f "openroad.*$TAG" 2>/dev/null
    stall=0
  fi
done
