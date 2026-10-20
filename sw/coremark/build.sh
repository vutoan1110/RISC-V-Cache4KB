#!/usr/bin/env bash
# Build CoreMark for the RV32I+Zmmul SoC (review item A6).
# Run from WSL: bash build.sh
set -euo pipefail
cd "$(dirname "$0")"

CROSS=${CROSS:-riscv64-unknown-elf-}
CFLAGS="-O2 -march=rv32i_zmmul -mabi=ilp32 -ffreestanding -fno-builtin \
 -Wall -I. -I.. -DPERFORMANCE_RUN=1 -DITERATIONS=1"
OBJDIR=obj
mkdir -p "$OBJDIR"

SRCS="core_list_join core_main core_matrix core_state core_util core_portme ee_printf"
for f in $SRCS; do
    echo "  CC  $f.c"
    ${CROSS}gcc -c $CFLAGS "$f.c" -o "$OBJDIR/$f.o"
done

echo "  sizes:"
${CROSS}size "$OBJDIR"/*.o | tail -n +2 | awk '{t+=$1; d+=$2; b+=$3} END {printf "    text=%d data=%d bss=%d\n", t, d, b}'
