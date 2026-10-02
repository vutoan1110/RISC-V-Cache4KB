# sw_metrics/irq -- interrupt latency and context-switch firmware (metric expansion, 2026-09-30).
# Same toolchain, flags, startup, linker script and hex post-processing as sw/Makefile, so the
# image runs on the unchanged SoC; it lives outside sw/ so it is not part of the RTL manifest.
#   make        -> irq_bench_rv32.hex (for $readmemh), irq_bench.dump, the unsupported-instruction guard
CROSS  ?= riscv64-unknown-elf-
CC      = $(CROSS)gcc
OBJCOPY = $(CROSS)objcopy
OBJDUMP = $(CROSS)objdump
PYTHON ?= python3
SW      = ../../sw

# rv32i_zmmul as in sw/Makefile, plus _zicsr: this image needs csrw/csrs/csrc/csrr (mtvec, mie,
# mstatus, mepc), which the core implements in register form; the sw/ images use none.
CFLAGS  = -march=rv32i_zmmul_zicsr -mabi=ilp32 -O2 -ffreestanding -fno-builtin \
	-msmall-data-limit=0 -mstrict-align -ffunction-sections -fdata-sections \
	-nostdlib -nostartfiles -Wall -Wextra -I$(SW)
LDFLAGS = -T $(SW)/link.ld -nostdlib -nostartfiles \
	-Wl,--gc-sections,-Map=irq_bench.map,--cref

all: irq_bench_rv32.hex irq_bench.dump guard

irq_bench.elf: $(SW)/startup.S irq_bench.c irq_entry.S $(SW)/platform.h $(SW)/link.ld
	$(CC) $(CFLAGS) $(LDFLAGS) $(SW)/startup.S irq_bench.c irq_entry.S -lgcc -o $@

irq_bench.hex: irq_bench.elf
	$(OBJCOPY) -O verilog $< $@

irq_bench_rv32.hex: irq_bench.hex
	$(PYTHON) $(SW)/fix_hex.py --input $< --output $@ --ram-bytes 16384

irq_bench.dump: irq_bench.elf
	$(OBJDUMP) -d $< > $@

guard: irq_bench.elf irq_bench.dump
	$(PYTHON) ../../scripts/fpga/check_unsupported_instructions.py --objdump $(OBJDUMP) --dump irq_bench.dump irq_bench.elf

clean:
	rm -f irq_bench.elf irq_bench.hex irq_bench_rv32.hex irq_bench.dump irq_bench.map

.PHONY: all guard clean
