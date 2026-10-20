# Core UVM environment. Same entry points as run_uvm.ps1, for Git Bash / make.
#
#   make -C verification/uvm smoke
#   make -C verification/uvm test TEST=core_smoke_test SEED=7
#   make -C verification/uvm regress
#   make -C verification/uvm random SEEDS=20
#   make -C verification/uvm clean
#
# One vsim process per test: sharing a session races with on-access virus
# scanning and produces spurious "(vopt-19) Failed to access library 'work'".

VSIM  ?= C:/questasim64_2024.1/win64/vsim.exe
SEED  ?= 1
TEST  ?= core_smoke_test
TESTS ?= core_smoke_test core_random_test axi_smoke_test axi_stress_test soc_directed_test soc_periph_test

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))../..)

.PHONY: smoke test regress random clean

smoke:
	@$(MAKE) --no-print-directory test TEST=core_smoke_test SEED=$(SEED)

test:
	cd $(ROOT) && $(VSIM) -c -do "do verification/uvm/run_uvm.do $(TEST) 1 $(SEED)"

# Compile for the first test only, then reuse work/.
regress:
	@cd $(ROOT) && compile=1; rc=0; \
	for t in $(TESTS); do \
	    echo "=== $$t (seed $(SEED), compile=$$compile) ==="; \
	    $(VSIM) -c -do "do verification/uvm/run_uvm.do $$t $$compile $(SEED)" || rc=1; \
	    compile=0; \
	done; \
	if [ $$rc -ne 0 ]; then echo "[FAIL] UVM regression"; else echo "[PASS] UVM regression"; fi; \
	exit $$rc

# Multi-seed random regression, one vsim process per seed.
SEEDS ?= 10
random:
	@cd $(ROOT) && compile=1; rc=0; \
	for s in $$(seq 1 $(SEEDS)); do \
	    echo "=== core_random_test seed $$s ==="; \
	    $(VSIM) -c -do "do verification/uvm/run_uvm.do core_random_test $$compile $$s" || rc=1; \
	    compile=0; \
	done; \
	if [ $$rc -ne 0 ]; then echo "[FAIL] UVM random regression"; \
	else echo "[PASS] UVM random regression $(SEEDS) seeds"; fi; \
	exit $$rc

clean:
	rm -rf $(ROOT)/work
	rm -f $(ROOT)/verification/uvm/out/*.log $(ROOT)/verification/uvm/out/*.status
	rm -f $(ROOT)/verification/uvm/out/*.vcd
