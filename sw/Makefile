# Parallelism note (host: 24 cores / 32 threads, 32 GB).
# `make -j` does NOT speed this build up: $(ELF) is produced by a single gcc
# invocation over all of $(COMMON_SRCS), so there is only ever one compile job.
# The remaining targets (bin/hex/dump/guard/size-report/rv32hex) are ordered by
# real prerequisites and each take milliseconds.
#
# Nor can several BENCH values be built concurrently in this directory: every
# benchmark writes the same benchmark.elf/.bin/.hex/.map, so parallel runs would
# clobber each other. Build them sequentially, or copy the tree per benchmark.
#
# For the DE2-115 flow the long pole is Quartus, not this Makefile; that is
# where the cores go (NUM_PARALLEL_PROCESSORS 16 in quartus/soc_core_common.qsf).
# The three configs share db/ in the project root, so they must be compiled
# one after another -- do not run build_de2_115.ps1 three times in parallel.

CROSS ?= riscv64-unknown-elf-
CC      = $(CROSS)gcc
OBJCOPY = $(CROSS)objcopy
OBJDUMP = $(CROSS)objdump
SIZE    = $(CROSS)size
NM      = $(CROSS)nm
PYTHON ?= python3

ELF      = benchmark.elf
BIN      = benchmark.bin
HEX      = benchmark.hex
DUMP     = benchmark.dump
MAP      = benchmark.map
SIZE_RPT = benchmark.size
RV32HEX  = benchmark_rv32.hex

# R14 (2026-09-29, RAM16K_CHANGES.md): the unified RAM is 16 KiB (was 8 KiB). Must match sw/link.ld,
#   sw/platform.h RAM_SIZE_BYTES and IMEM_DEPTH + DMEM_DEPTH of hdl/soc_top.v.
RAM_BYTES ?= 16384
RAM_WORDS = $(shell expr $(RAM_BYTES) / 4)

BENCH ?= cachesweep
MODE  ?= embench
# cachesweep is the default so that a bare `make install_hex` reproduces the
#   MIFs that ship in hdl/. It is the synthetic conflict probe, not a
#   workload: it measures cache geometry rather than performance.
# crc32..wikisort_trace: nine project-original acceptance kernels + a wikisort
#   trace variant (see docs/README.md and docs/guides/05 section 9). These
#   implement standard published algorithms; they are NOT Embench-IoT source
#   and their numbers are not an official Embench score.
# md5sum (MIT), depthconv (Apache-2.0): real Embench-IoT ports, permissively
#   licensed. Build+guard+ModelSim PASS on DM/SA2/DM_VC4 -- see
#   docs/guides/05_EXTENDED_EMBENCH_BENCHMARKS.md.
# insertsort: PROJECT-ORIGINAL store-bound kernel (textbook insertion sort,
#   own harness, no third-party copyright). It is the permissively-licensed
#   store-bound workload used as evidence for the posted-write buffer.
#
# The GPL-3.0 ports bubblesort (BEEBS) and slre (Embench) were REMOVED so the
#   whole tree is permissively licensed (Apache-2.0). insertsort replaces
#   bubblesort's store-bound role; to re-add either, re-port from upstream
#   (github.com/mageec/beebs, github.com/embench/embench-iot).
# ramsweep (R14, RAM16K_CHANGES.md): RAM test over every free word of the 16 KiB RAM, not a benchmark.
BENCHES = crc32 edn fdct huffbench matmult mont64 sha256 tarfind wikisort wikisort_trace md5sum depthconv insertsort cachesweep ramsweep
# R14 upstream Embench-IoT kernels that fit the 16 KiB RAM (MODE=upstream; GPL-3.0 except md5sum,
#   tarfind (MIT) and depthconv (Apache-2.0): research tree only, see embench_upstream/README.md).
#   nettle-aes and sglib-combined do not fit and are not ported.
UP_BENCHES = aha-mont64 crc32 depthconv edn huffbench matmult-int md5sum nettle-sha256 \
	slre statemate tarfind ud

ifeq ($(MODE),smoke)
COMMON_SRCS = startup.S main_synthetic_legacy.c
SOURCE_DEPS = platform.h platform_counter_map.h platform_branch_metrics.h platform_cache_metrics.h platform_benchmark.h
else ifeq ($(MODE),upstream)
# R14 upstream Embench-IoT suite (RAM16K_CHANGES.md, embench_upstream/README.md): BENCH is a kernel
#   directory under embench_upstream/, SCALE the LOCAL_SCALE_FACTOR override (scripts/build_upstream_fw.sh).
UP_DIR = embench_upstream
# software division (the core is rv32i_zmmul, no DIV) and 64-bit helpers from libgcc
LDLIBS = -lgcc
COMMON_SRCS = startup.S main_upstream.c $(UP_DIR)/libc_shim.c embench_beebs.c $(wildcard $(UP_DIR)/$(BENCH)/*.c)
SOURCE_DEPS = platform.h platform_counter_map.h platform_branch_metrics.h platform_cache_metrics.h platform_benchmark.h embench_beebs.h $(UP_DIR)/support.h
EXTRA_CFLAGS += -I$(UP_DIR) -I$(UP_DIR)/inc -I$(UP_DIR)/$(BENCH) -DUPSTREAM_NAME='"up_$(BENCH)"' \
	-DGLOBAL_SCALE_FACTOR=1 -DWARMUP_HEAT=1 $(if $(SCALE),-DLOCAL_SCALE_FACTOR_OVERRIDE=$(SCALE))
else
COMMON_SRCS = startup.S main_$(BENCH).c embench_$(BENCH).c embench_beebs.c
SOURCE_DEPS = platform.h platform_counter_map.h platform_branch_metrics.h platform_cache_metrics.h platform_benchmark.h embench_$(BENCH).h embench_beebs.h
endif

CFLAGS  = -march=rv32i_zmmul -mabi=ilp32 -O2 -ffreestanding -fno-builtin \
	-msmall-data-limit=0 -mstrict-align -ffunction-sections -fdata-sections \
	-nostdlib -nostartfiles -Wall -Wextra -I. $(EXTRA_CFLAGS)
LDFLAGS = -T link.ld -nostdlib -nostartfiles \
	-Wl,--gc-sections,-Map=$(MAP),--cref

all: check-bench $(BIN) $(HEX) $(DUMP) guard size-report rv32hex

check-bench:
	@if [ "$(MODE)" = "upstream" ]; then \
		case " $(UP_BENCHES) " in *" $(BENCH) "*) ;; \
		*) echo "[FAIL] unknown upstream BENCH=$(BENCH); valid: $(UP_BENCHES)"; exit 1 ;; esac; \
	elif [ "$(MODE)" != "smoke" ]; then \
		case " $(BENCHES) " in *" $(BENCH) "*) ;; \
		*) echo "[FAIL] unknown BENCH=$(BENCH); valid: $(BENCHES)"; exit 1 ;; esac; \
	fi

check-toolchain:
	@$(CC) --version | head -n 1
	@$(OBJDUMP) --version | head -n 1
	@$(PYTHON) --version

$(ELF): $(COMMON_SRCS) $(SOURCE_DEPS) link.ld
	$(CC) $(CFLAGS) $(LDFLAGS) $(COMMON_SRCS) $(LDLIBS) -o $@

$(BIN): $(ELF)
	$(OBJCOPY) -O binary $< $@

$(HEX): $(ELF)
	$(OBJCOPY) -O verilog $< $@

$(DUMP): $(ELF)
	$(OBJDUMP) -d $< > $@

guard: $(ELF) $(DUMP)
	$(PYTHON) ../scripts/fpga/check_unsupported_instructions.py --objdump $(OBJDUMP) --dump $(DUMP) $(ELF)

size-report: $(ELF)
	$(SIZE) -A -x $(ELF) | tee $(SIZE_RPT)
	@echo "[INFO] reserved stack: 0x400 bytes; linker ASSERT checks image/stack overlap"

rv32hex: $(HEX)
	$(PYTHON) fix_hex.py --input $(HEX) --output $(RV32HEX) --ram-bytes $(RAM_BYTES)

install_hex: rv32hex
	cp $(RV32HEX) ../hdl/riscv_full.hex
	$(PYTHON) ../scripts/fpga/hex_to_mif.py --input ../hdl/riscv_full.hex --output-dir ../hdl --depth $(RAM_WORDS)

smoke:
	$(MAKE) clean
	$(MAKE) MODE=smoke all

list-benches:
	@echo $(BENCHES)

clean:
	rm -f $(ELF) $(BIN) $(HEX) $(DUMP) $(MAP) $(SIZE_RPT) $(RV32HEX)

.PHONY: all check-bench check-toolchain guard size-report rv32hex install_hex smoke list-benches clean
