#!/usr/bin/env bash
# Build a CoreMark firmware image for the SoC (review item A6).
#
# CoreMark needs about 17 KiB of text plus bss, so it does not fit the frozen
# 8-KiB RAM. This build uses a 32-KiB linker script and the matching
# IMEM_DEPTH/DMEM_DEPTH at simulation time. The caches are unchanged: at 1 KiB
# with a 16-byte line the index is addr[9:4], so a larger RAM changes what the
# program can hold, not how the cache maps it.
#
#   bash build_hex.sh            -> ../fw/coremark.hex
set -euo pipefail
cd "$(dirname "$0")"

CROSS=${CROSS:-riscv64-unknown-elf-}
OUT=../../fw/coremark.hex
LD=coremark_link.ld
CFLAGS="-O2 -march=rv32i_zmmul -mabi=ilp32 -ffreestanding -fno-builtin -Wall \
 -I. -I.. -DPERFORMANCE_RUN=1 -DITERATIONS=1"

rm -rf obj && mkdir -p obj

# CoreMark's own main becomes coremark_main; main_coremark.c wraps it.
${CROSS}gcc -c $CFLAGS -Dmain=coremark_main core_main.c -o obj/core_main.o
for f in core_list_join core_matrix core_state core_util core_portme ee_printf; do
    ${CROSS}gcc -c $CFLAGS "$f.c" -o "obj/$f.o"
done

# Startup and platform glue from the existing firmware tree.
${CROSS}gcc -c $CFLAGS ../startup.S -o obj/startup.o
${CROSS}gcc -c $CFLAGS ../main_coremark.c -o obj/main_coremark.o

${CROSS}gcc -nostdlib -nostartfiles -T "$LD" -march=rv32i_zmmul -mabi=ilp32 \
    obj/*.o -o coremark.elf -lgcc

${CROSS}size coremark.elf
${CROSS}objcopy -O verilog coremark.elf coremark.hex
python3 ../fix_hex.py --input coremark.hex --output "$OUT" --ram-bytes 32768
echo "  wrote $OUT"
