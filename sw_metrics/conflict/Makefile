# sw_metrics/conflict -- extended conflict probe (2026-10-08). Same toolchain, flags, startup and hex
# post-processing as sw/Makefile; its own linker script (link_probe.ld) keeps 0x0C00-0x3DFF free for the probe.
# Outside sw/, so it is not part of the RTL manifest.
#   make  -> conflict_probe_4k_rv32.hex (SPAN 4096: 4 KiB caches), conflict_probe_1k_rv32.hex (SPAN 1024: 1 KiB),
#            their .dump files, and the unsupported-instruction guard
CROSS  ?= riscv64-unknown-elf-
CC      = $(CROSS)gcc
OBJCOPY = $(CROSS)objcopy
OBJDUMP = $(CROSS)objdump
PYTHON ?= python3
SW      = ../../sw

# -fno-shrink-wrap: the probe window must hold only probe accesses. With shrink-wrapping GCC saved s0 after the
# window opened in the SPAN 1024 build (one stack store and one load counted; conflict_probe.c caught it and failed),
# so every callee-saved register is saved in the prologue, before sysmon_clear_start().
CFLAGS  = -march=rv32i_zmmul -mabi=ilp32 -O2 -fno-shrink-wrap -ffreestanding -fno-builtin \
	-msmall-data-limit=0 -mstrict-align -ffunction-sections -fdata-sections \
	-nostdlib -nostartfiles -Wall -Wextra -I$(SW)
LDFLAGS = -T link_probe.ld -nostdlib -nostartfiles -Wl,--gc-sections

all: conflict_probe_4k_rv32.hex conflict_probe_1k_rv32.hex conflict_probe_4k.dump conflict_probe_1k.dump guard

conflict_probe_4k.elf: $(SW)/startup.S conflict_probe.c link_probe.ld $(SW)/platform.h
	$(CC) $(CFLAGS) -DSPAN=4096u $(LDFLAGS) -Wl,-Map=conflict_probe_4k.map $(SW)/startup.S conflict_probe.c -lgcc -o $@

conflict_probe_1k.elf: $(SW)/startup.S conflict_probe.c link_probe.ld $(SW)/platform.h
	$(CC) $(CFLAGS) -DSPAN=1024u $(LDFLAGS) -Wl,-Map=conflict_probe_1k.map $(SW)/startup.S conflict_probe.c -lgcc -o $@

%.hex: %.elf
	$(OBJCOPY) -O verilog $< $@

%_rv32.hex: %.hex
	$(PYTHON) $(SW)/fix_hex.py --input $< --output $@ --ram-bytes 16384

%.dump: %.elf
	$(OBJDUMP) -d $< > $@

guard: conflict_probe_4k.elf conflict_probe_4k.dump conflict_probe_1k.elf conflict_probe_1k.dump
	$(PYTHON) ../../scripts/fpga/check_unsupported_instructions.py --objdump $(OBJDUMP) --dump conflict_probe_4k.dump conflict_probe_4k.elf
	$(PYTHON) ../../scripts/fpga/check_unsupported_instructions.py --objdump $(OBJDUMP) --dump conflict_probe_1k.dump conflict_probe_1k.elf

clean:
	rm -f *.elf *.hex *.dump *.map

.PHONY: all guard clean
