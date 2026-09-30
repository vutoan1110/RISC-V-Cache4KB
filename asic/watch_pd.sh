#!/usr/bin/env bash
# Watch whatever OpenLane run is currently in flight and say something when it
# matters. Written because a physical-design run can die silently -- twice now a
# crash has cost hours before anyone looked.
#
# Emits a line when:
#   * the flow advances to a new step
#   * the process disappears (crash, kill, or a clean finish)
#   * nothing has happened for ten minutes, as a heartbeat
#
# One line per event, because each line becomes a notification.
#
#   bash watch_pd.sh
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)

HEARTBEAT=600          # seconds between "still alive" lines
POLL=20                # seconds between checks

newest_run() {
    ls -1dt "$HERE"/*/runs/*/ 2>/dev/null | head -1
}

alive() {
    local n
    n=$(wsl.exe -d Ubuntu -e bash -lc 'pgrep -cf "openlane|openroad" 2>/dev/null || echo 0' 2>/dev/null \
        | tr -d "\r\n ")
    case "$n" in ''|*[!0-9]*) echo 0 ;; *) echo "$n" ;; esac
}

last_step() {
    ls -1 "$1" 2>/dev/null | grep -E '^[0-9]+-' | sort -n | tail -1
}

prev_step=""
prev_run=""
last_said=0
was_alive=1

while true; do
    run=$(newest_run)
    tag=$(basename "${run:-none}")
    step=$(last_step "${run:-/nonexistent}")
    n=$(alive)
    now=$(date +%s)
    stamp=$(date +%H:%M)

    if [ "$n" -eq 0 ] && [ "$was_alive" -ne 0 ]; then
        # Distinguish a finish from a death: the flow writes final/ when it ends
        # cleanly, and run_pd.sh appends a line to pd_log.md either way.
        verdict=$(tail -3 "$HERE/pd_log.md" 2>/dev/null | grep -oE '(DONE|STOP|ODD) `[^`]+`[^|]*' | tail -1)
        if [ -d "${run}final" ]; then
            echo "[$stamp] XONG SACH  $tag  buoc cuoi=$step  final/ da co"
        else
            echo "[$stamp] DUNG/CHET  $tag  buoc cuoi=$step  |  ${verdict:-khong co ghi chu trong pd_log}"
        fi
        was_alive=0
        last_said=$now
    elif [ "$n" -ne 0 ]; then
        if [ "$was_alive" -eq 0 ]; then
            echo "[$stamp] CHAY LAI   $tag  buoc=$step"
            was_alive=1
            prev_step=""
        fi
        if [ "$tag" != "$prev_run" ]; then
            echo "[$stamp] LUOT MOI   $tag  buoc=$step"
            prev_run=$tag
            prev_step=$step
            last_said=$now
        elif [ "$step" != "$prev_step" ] && [ -n "$step" ]; then
            echo "[$stamp] $tag  ->  $step"
            prev_step=$step
            last_said=$now
        elif [ $((now - last_said)) -ge $HEARTBEAT ]; then
            echo "[$stamp] con chay   $tag  van o $step  ($((n)) tien trinh)"
            last_said=$now
        fi
    fi
    sleep $POLL
done
