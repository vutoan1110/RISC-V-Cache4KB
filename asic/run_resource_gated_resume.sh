#!/usr/bin/env bash
# Opt-in foreground resource queue for the existing gated sign-off driver.
# --check-resource-only performs one read-only query and never starts a flow.
set -u
A=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
CHECK=0
if [ "${1:-}" = --check-resource-only ]; then
    CHECK=1; shift
    [ "$#" -eq 0 ] || { echo 'RESOURCE UNKNOWN: unexpected check arguments'; exit 2; }
elif [ "${P4_RESOURCE_WAIT:-0}" != 1 ] || [[ "${5:-drt}" != hold && "${5:-drt}" != sta ]]; then
    exec bash "$A/run_gated_resume.sh" "$@"
fi
MIN_WSL=${P4_MIN_AVAILABLE_MB:-15000}
MIN_WIN=${P4_MIN_WINDOWS_FREE_MIB:-15000}
tag=${2:-resource_check}
say () { echo "$(date -Is) $*" | tee -a "$A/gated_pd.log" >> "$A/dse_pd.log"; }
unknown () {
    if [ "$CHECK" = 1 ]; then echo "RESOURCE UNKNOWN: $*";
    else say "STOP $tag P4 resource UNKNOWN: $*"; fi
    exit 2
}
[[ "$MIN_WSL" =~ ^[1-9][0-9]*$ && "$MIN_WIN" =~ ^[1-9][0-9]*$ ]] || unknown 'invalid resource thresholds'
read_resources () {
    local rc
    WSL_AVAILABLE=$(LC_ALL=C free -m | awk '$1=="Mem:" {print $7}')
    [[ "$WSL_AVAILABLE" =~ ^[0-9]+$ ]] || unknown 'invalid WSL available-memory query'
    WINDOWS_FREE=$(timeout 15s '/mnt/c/Program Files/PowerShell/7/pwsh.exe' -NoProfile -NonInteractive -Command '[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1024)' 2>&1)
    rc=$?; WINDOWS_FREE=${WINDOWS_FREE//$'\r'/}
    [ "$rc" -eq 0 ] && [[ "$WINDOWS_FREE" =~ ^[0-9]+$ ]] || unknown "Windows free-memory query failed or invalid (rc=$rc): ${WINDOWS_FREE//$'\n'/ }"
}
last_wait=-600
while :; do
    if [ "$CHECK" = 0 ] && [ -e "$A/.abort_gated_pd" ]; then say "STOP $tag before P4 (abort flag)"; exit 0; fi
    read_resources
    READY=0
    if (( 10#$WSL_AVAILABLE >= 10#$MIN_WSL && 10#$WINDOWS_FREE >= 10#$MIN_WIN )); then READY=1; fi
    if [ "$CHECK" = 1 ]; then
        STATUS=WAITING; [ "$READY" = 1 ] && STATUS=READY
        echo "RESOURCE $STATUS WSL_AVAILABLE_MIB=$WSL_AVAILABLE WINDOWS_FREE_MIB=$WINDOWS_FREE MIN_WSL_MIB=$MIN_WSL MIN_WINDOWS_MIB=$MIN_WIN"
        exit 0
    fi
    if [ -e "$A/.abort_gated_pd" ]; then say "STOP $tag before P4 (abort flag)"; exit 0; fi
    if [ "$READY" = 1 ]; then
        say "NOTE $tag P4 resource READY WSLavailable ${WSL_AVAILABLE}MiB Windowsfree ${WINDOWS_FREE}MiB; thresholds ${MIN_WSL}/${MIN_WIN}MiB; exec unchanged gated resume"
        exec bash "$A/run_gated_resume.sh" "$@"
    fi
    if (( SECONDS - last_wait >= 600 )); then
        say "WAIT $tag P4 resources WSLavailable ${WSL_AVAILABLE}/${MIN_WSL}MiB Windowsfree ${WINDOWS_FREE}/${MIN_WIN}MiB"
        last_wait=$SECONDS
    fi
    sleep 30
done
