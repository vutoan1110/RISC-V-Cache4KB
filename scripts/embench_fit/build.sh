#!/usr/bin/env bash
# Build every upstream Embench-IoT kernel with the project's compiler flags and report the RAM it needs.
# FLOW_JOURNAL / NHAT_KY_RTL 2026-09-29: does upstream Embench fit the 8 KiB unified RAM? rv32i_zmmul, project flags,
# no libc (inc/ + shim.c supply the few functions), linked into a 1 MiB fake RAM; the RAM needed is image + bss + stack.
# Upstream Embench-IoT checkout (commit 09c2ed8c, recovered from the pack in C:/Temp/embench_src).
E=${EMBENCH:-$(dirname "$0")/../../../embench-iot}
O=${OPT:--O2}
printf "kernel\ttext\trodata\tdata\tbss\timage_plus_bss\tstatus\n"
for d in $E/src/*/; do
    k=$(basename $d)
    srcs=$(ls $d*.c)
    out=/tmp/emb_$k.elf
    if riscv64-unknown-elf-gcc -march=rv32i_zmmul -mabi=ilp32 $O -ffreestanding -nostdlib -nostartfiles \
        -ffunction-sections -fdata-sections -DWARMUP_HEAT=1 -DGLOBAL_SCALE_FACTOR=1 -I$(dirname "$0")/inc -I$E/support -I$d \
        start.S shim.c $E/support/main.c $E/support/beebsc.c $srcs -T big.ld -Wl,--gc-sections -lgcc \
        -o $out > /tmp/emb_$k.log 2>&1; then
        read t r da b <<< $(riscv64-unknown-elf-size -A $out | awk '$1==".text"{t=$2} $1==".rodata"{r=$2} $1==".data"{d=$2} $1==".bss"{b=$2} END{print t+0, r+0, d+0, b+0}')
        printf "%s\t%d\t%d\t%d\t%d\t%d\tok\n" $k $t $r $da $b $((t + r + da + b))
    else
        printf "%s\t-\t-\t-\t-\t-\tFAIL: %s\n" $k "$(grep -m1 -o 'undefined reference to .[a-zA-Z_0-9]*.\|error: .*' /tmp/emb_$k.log | head -1)"
    fi
done
