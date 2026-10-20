#!/usr/bin/env bash
# R14 (RAM16K_CHANGES.md): rebuild the project's frozen benchmark images fw/<kernel>.hex with the 16 KiB
# linker script (stack 0x3C00-0x3FFF instead of 0x1C00-0x1FFF), plus the new ramsweep test. CoreMark
# (fw/coremark.hex) has its own linker script and memory size and is not rebuilt here.
# Run in WSL: bash scripts/build_fw_r14.sh
set -euo pipefail
cd "$(dirname "$0")/../sw"
# The project's own Embench-style kernels were removed on 2026-09-30 (review item A6); the
# benchmarks are the upstream Embench-IoT images built by scripts/build_upstream_fw.sh.
for k in cachesweep ramsweep; do
    make clean >/dev/null 2>&1
    make BENCH="$k" > "/tmp/fw_build_$k.log" 2>&1 || { echo "[FAIL] $k (see /tmp/fw_build_$k.log)"; exit 1; }
    cp benchmark_rv32.hex "../fw/$k.hex"
    printf '[OK] %-15s %s\n' "$k" "$(grep -o '[0-9]* initialized bytes' "/tmp/fw_build_$k.log")"
done
make clean >/dev/null 2>&1
