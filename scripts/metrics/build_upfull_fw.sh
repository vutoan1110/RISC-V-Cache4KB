#!/usr/bin/env bash
# The 12 upstream Embench-IoT kernels at their ORIGINAL iteration counts (upstream LOCAL_SCALE_FACTOR, no
# SCALE override), for the DE2-115 board where a few million cycles take a tenth of a second. Output:
# fw_board/upfull_<kernel>.hex. fw_board/ is outside the RTL manifest roots, so these images do not change
# the frozen RTL id; the simulation images with reduced iteration counts stay in fw/up_<kernel>.hex.
# Run in WSL: bash scripts/metrics/build_upfull_fw.sh
set -euo pipefail
cd "$(dirname "$0")/../../sw"
mkdir -p ../fw_board
for k in aha-mont64 crc32 depthconv edn huffbench matmult-int md5sum nettle-sha256 slre statemate tarfind ud; do
    make clean > /dev/null 2>&1
    if ! make MODE=upstream BENCH="$k" > "/tmp/upfull_$k.log" 2>&1; then
        echo "[FAIL] $k (see /tmp/upfull_$k.log)"; exit 1
    fi
    cp benchmark_rv32.hex "../fw_board/upfull_$k.hex"
    printf '[OK] %-14s %s\n' "$k" "$(grep -o '[0-9]* initialized bytes' "/tmp/upfull_$k.log")"
done
make clean > /dev/null 2>&1
rm -f ./*.o ./*.i ./*.s
