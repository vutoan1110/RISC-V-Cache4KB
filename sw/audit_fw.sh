#!/usr/bin/env bash
# Rebuild every kernel and compare against the frozen hex images.
#
# The firmware does not depend on the RTL, but the standing rule is to prove
# that rather than assume it: an RTL change must be shown not to have moved the
# software, not merely believed not to have.
set -uo pipefail
cd "$(dirname "$0")"

FROZEN=../../results/regression/embench_sim/fw
KERNELS="crc32 depthconv edn fdct huffbench insertsort matmult md5sum mont64 sha256 tarfind wikisort cachesweep"

same=0
diff=0
missing=0
for k in $KERNELS; do
    # The build writes the same benchmark.elf/.hex for every kernel, so the
    # objects must be removed or make reports the previous one up to date.
    make clean >/dev/null 2>&1
    if ! make BENCH="$k" >/dev/null 2>&1; then
        printf '  %-11s BUILD FAILED\n' "$k"
        diff=$((diff + 1))
        continue
    fi
    ref="$FROZEN/$k.hex"
    if [ ! -f "$ref" ]; then
        printf '  %-11s no frozen reference\n' "$k"
        missing=$((missing + 1))
        continue
    fi
    a=$(md5sum benchmark_rv32.hex | cut -d' ' -f1)
    b=$(md5sum "$ref" | cut -d' ' -f1)
    if [ "$a" = "$b" ]; then
        printf '  %-11s identical\n' "$k"
        same=$((same + 1))
    else
        printf '  %-11s DIFFERS  built=%s frozen=%s\n' "$k" "${a:0:12}" "${b:0:12}"
        diff=$((diff + 1))
    fi
done

echo ""
echo "  identical=$same  differs=$diff  no-reference=$missing"
[ "$diff" -eq 0 ]
