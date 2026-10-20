#!/usr/bin/env bash
# R14 (RAM16K_CHANGES.md): build the upstream Embench-IoT suite (sw/embench_upstream/) into fw/up_<kernel>.hex.
#
# LOCAL_SCALE_FACTOR override per kernel. The upstream values aim at seconds of real time (millions of
# cycles), too long for RTL simulation; these give roughly 130k-350k cycles per measured run on DM 4 KiB
# (probe: results/up_probe/scale1_dm.csv, one iteration each after one warm-up). The measurement is one
# warm-up iteration (WARMUP_HEAT=1, not counted) followed by SCALE counted iterations. These are NOT
# official Embench scores. Run in WSL: bash scripts/build_upstream_fw.sh
set -euo pipefail
cd "$(dirname "$0")/../sw"
declare -A SCALE=(
    [aha-mont64]=13 [crc32]=5 [depthconv]=52 [edn]=3 [huffbench]=1 [matmult-int]=1
    [md5sum]=2 [nettle-sha256]=7 [slre]=4 [statemate]=60 [tarfind]=2 [ud]=54
)
for k in aha-mont64 crc32 depthconv edn huffbench matmult-int md5sum nettle-sha256 slre statemate tarfind ud; do
    make clean >/dev/null 2>&1
    make MODE=upstream BENCH="$k" SCALE="${SCALE[$k]}" > "/tmp/up_build_$k.log" 2>&1 || { echo "[FAIL] $k (see /tmp/up_build_$k.log)"; exit 1; }
    cp benchmark_rv32.hex "../fw/up_$k.hex"
    printf '[OK] %-15s SCALE=%-3s %s\n' "$k" "${SCALE[$k]}" "$(grep -o '[0-9]* initialized bytes' "/tmp/up_build_$k.log")"
done
make clean >/dev/null 2>&1
