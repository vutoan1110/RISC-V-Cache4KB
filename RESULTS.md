# Results

Measured results of the research copy of the RISC-V SoC, per configuration. Rules for every number: it was executed
twice and compared field by field (the exceptions are named where they occur: the single physical board pass and
screening runs); the corner is named for every timing value; the power method is stated (flow estimate or measured
switching activity); sign-off checks are listed before PPA. The review items are answered in `REVIEW_RESPONSE.md`.

Verification beyond the per-revision chain (the frozen design inputs are unchanged by all of it):

- UVM: 48 cases in each of two independent passes, identical scoreboard fields. SoC directed ISA, peripherals / IRQ and
  two-byte serial UART RX run on DM / SA2 / DM_VC4 / DM_DSE with seeds 1 / 2 / 3; AXI stress uses line words
  2 / 4 / 8 / 16 with seeds 1 / 2 / 3. Wrong-byte UART controls fail in both passes.
  Receipt: `results/uvm_cache_uart_20261009/verification.json`.
- Architecture adapter: the 43 ACT4 cases plus an upper-half data / instruction test, run twice. All 43 signatures,
  retirement counts and cycles equal the previous result; the upper-half test detects the 512 KiB alias of the frozen
  harness. The maintained runner generates a corrected 1 MiB adapter separately from the frozen testbench
  (`results/architecture_window_20261009/verification.json`). This is unprivileged I / Zmmul verification, not full
  privileged-ISA compliance.
- Random differential: 50 generated programs per pass, two fresh compilations and independent measurements; all 50 paired
  summary rows and the complete trace bytes match. Each case gates the simulator return code, complete PASS /
  termination, absence of Error / Fatal and full trace integrity (`results/random_diff_checked_20261009/verification.json`).
  This test compares predictor off / on on the same core.
- Independent Spike reference (2026-10-11): 50 seeds x 2 fresh Spike executions, all 100 native exits 0, all 200
  preserved current-RTL traces match; 7,105 retirements per pass; 300 wrong-trace controls detected. PC, instruction, GPR
  writes and store address / enabled bytes / strobes are compared (`results/spike_random_reference_20261011/receipt.json`).
  Scope: the generated RV32I / Zmmul core subset, not SoC MMIO, interrupts, caches or timing.
- RF / BHT in M9K, formal repetition (2026-10-16): two fresh complete passes, each regenerating the harness and models and
  running the register-file, BHT and datapath read-ahead proofs plus their three mutations. All six real runs prove
  induction, all six mutated runs give the required base counterexample, and every compared proof / SAT / assertion field
  matches across passes (`results/rf_bht_m9k_formal_repeat_20261016/receipt.json`). Assumptions as in the original proof
  (async2sync, zero initial state, reset asserted at step 1, the read-ahead protocol checked separately in the datapath);
  this is module / protocol evidence, not full-SoC or ASIC-netlist equivalence.

## 1. Configurations, workloads, views

- Core: RV32I + Zmmul, five-stage in-order pipeline, branch predictor on (BHT), AXI4 memory port, APB peripherals,
  hardware cycle classifier and event counters (sysmon).
- Caches (I and D), 4 KiB each, 16 B lines, 8-entry I-cache L0:
  - DM: direct-mapped, five-state controller (CACHE_CONFIG 0);
  - DM_DSE: direct-mapped on the ten-state DSE core (3);
  - SA2: two-way set-associative on the DSE core (1);
  - DM_VC4: direct-mapped with a 4-entry victim buffer on the DSE core (2);
  - SA4: four-way on the N-way core (4), FPGA and simulation only.
  `CACHE_FAST_HIT` = 1 answers a main-array hit of the DSE / N-way cores one cycle earlier (default 0).
- Main RAM 16 KiB (8 KiB before 2026-09-29).
- The research wrappers / QSFs select this 4 KiB profile; the generic HDL default remains 1 KiB. The five / ten-state
  controller descriptions refer to the I-cache; the D-cache controllers have seven (DM) and eleven (DSE) states.
- The preserved CoreMark results use a 32 KiB simulation RAM (`sw/coremark/coremark_link.ld` places the stack at 32 KiB).
  That -O2 rv32i_zmmul firmware needs .text 13,952 + .rodata 2,445 + .data 24 + .bss 2,020 + stack 1,024 = 19,465 bytes,
  more than 16 KiB; this applies to that firmware, not to every possible CoreMark port. Cache parameters and RAM latency
  are the same in every compared configuration.
- The isolated -Os integer APB-timer port was built independently twice; the performance and validation ELF / HEX bytes
  match. Both profiles end at 14,032 bytes + 1,024 bytes of reserved stack = 15,056 bytes, 1,328 bytes below 16 KiB
  (`results/coremark_standard_apb_build_pair_20261011.json`). This is a static footprint, not a score or a proof of a
  runtime fit in 16 KiB: the unchanged linker script still places the stack at 32 KiB.
- Workloads: the 12 upstream Embench-IoT kernels that fit 16 KiB (aha-mont64, crc32, depthconv, edn, huffbench,
  matmult-int, md5sum, nettle-sha256, slre, statemate, tarfind, ud; not official Embench scores), the short CoreMark sweeps
  (one iteration, full-program mcycle) and the standard-duration matrix of section 1.1. Older results used 12 project
  kernels; they are marked where they appear.
- CoreMark numeric CRCs: verified for the six base and five FAST_HIT 4 KiB points (22 fresh simulations, two independent
  compilations, all 40 snapshot fields equal between passes and to the prior baseline). The accepted APB UART bytes give
  the seed / list / matrix / state / final CRCs e9f5 / e714 / 1fd7 / 8e3a / e714 of the source reference
  (`results/coremark_crc_checked_20261009/verification.json`). The maintained runner rejects missing or wrong CRCs before
  writing a CSV row. The full supported capacity / line / organisation sweep is verified at all 92 points (49 base,
  43 FAST): 184 fresh simulations in two separately compiled passes, source-known CRCs and all 40 counters identical to both
  historical references; an independent raw audit checks 241 inputs and 379 artifacts
  (`results/coremark_sweep_crc_20261010/verification.json`, `results/coremark_sweep_crc_independent_audit_20261010/receipt.json`).
  SA4_256B_L16 is excluded: four sets cannot hold the fixed eight-entry L0 index.
- Views: FPGA view (RTL with the FPGA memories; organisation comparison), ASIC view (RTL with the OpenRAM models; the
  chip's cycle counts, fewer than the FPGA view because the ASIC RAM wrapper has no FPGA latency hooks), gate level (the
  signed-off netlist; reproduces the ASIC view cycle for cycle).

### 1.1 Standard-duration CoreMark, 32 KiB simulation RAM, 50 MHz

Completed 2026-10-11: four 4 KiB cache configurations x performance / validation x two independent executions, 16 / 16
PASS. The eight pairs match on all 108 scalar measurement fields each (including the 40 counters), 864 comparisons. Each
pass uses separately compiled private RTL models and independently built firmware; all native commands return 0.

| configuration | performance ticks | seconds at 50 MHz | CoreMark iterations/s | CoreMark/MHz | validation ticks |
|---|---:|---:|---:|---:|---:|
| DM | 719996901 | 14.39993802 | 76.389218 | 1.527784 | 722669045 |
| SA2 | 691866743 | 13.83733486 | 79.495077 | 1.589902 | 693576231 |
| DM_VC4 | 747676057 | 14.95352114 | 73.561270 | 1.471225 | 751155457 |
| DM_DSE | 802958516 | 16.05917032 | 68.496689 | 1.369934 | 806692095 |

Method: current-RTL FPGA simulation view, BP on, FAST_HIT = 0, 4 KiB I / D caches, 16 B lines, L0 = 8, RAM 32,768 bytes.
The unchanged CoreMark algorithms use TOTAL_DATA_SIZE = 2000, a single context, MEM_STATIC, HAS_FLOAT = 0 and
ITERATIONS = 0 calibration; every measured run selects 1,100 iterations. The performance seeds 0 / 0 / 0x66 and the
validation seeds 0x3415 / 0x3415 / 0x66 pass the source-known CRCs. Every final iterate interval exceeds 500,000,000 ticks
(10 s). Only the upstream final iterate interval determines throughput; the stored whole-program counters cover a
different window. APB TIMER_CMP = 0xffffffff is set before timing; every accepted COUNT delta equals the independently
observed clock-edge delta and the elapsed simulation time / 20 ns. Exact rates come from raw integer ticks.

Compiler: riscv64-unknown-elf-gcc 14.2.0, rv32i / ilp32 multilib, flags `-Os -march=rv32i_zmmul_zicsr -mabi=ilp32
-ffreestanding -fno-builtin -msmall-data-limit=0 -ffunction-sections -fdata-sections -Wall -Wextra`, `-Dmain=coremark_main`
for the isolated wrapper. Simulator: Verilator 5.053, assertions enabled. These are simulation-derived scores with a 32 KiB
RAM, not board measurements or EEMBC certification
([EEMBC CoreMark rules](https://github.com/eembc/coremark/blob/main/README.md)).
Evidence: `results/coremark_standard_apb_matrix_20261011/receipt.json`, `cases.csv`, `performance_paired.csv`; runner
`scripts/verification/run_coremark_standard_apb_matrix.py`.

## 2. Architecture (FPGA view, 4 KiB caches, 16 KiB RAM, BP on)

The review experiments were re-executed on the current sources on 2026-10-15. The M1 / M2 Embench sweep has 637 base and
559 FAST rows per pass, equal on all 48 CSV columns and equal to the historical reference
(`results/m2_6c4ccffd/comparison.json`); the 13 unsupported SA4_256B_L16 workload attempts per pass stay excluded. The A4
overlap, BP-off and IRQ evidence is under `results/review_sims_6c4ccffd/` (48 BP-off rows, 12 A4 workloads, 16 IRQ rows,
each paired). The A3 FAST cross-validation is complete: the 59 original pass-2 rows plus the isolated up_crc32 / SA4 retry
form exactly the 60 cases of pass 1 and match all 21 columns; all 120 FAST native logs agree with their CSV snapshots
(`results/crossval_fast_receipt_20261016/receipt.json`).

Source: `results/unified_metrics.md` (generated by `scripts/metrics/unified_table.py`).

| metric | DM | SA2 | DM_VC4 | DM_DSE |
|---|---:|---:|---:|---:|
| CPI, 12 Embench-IoT kernels | 1.5136 | 1.6597 | 1.6780 | 1.6614 |
| I$ hit % | 99.70 | 99.65 | 99.72 | 99.70 |
| D$ read hit % | 99.16 | 99.59 | 99.59 | 99.16 |
| branch mispredict % | 10.57 | 10.57 | 10.57 | 10.57 |
| Embench speed / MHz, GM | 0.809 | 0.739 | 0.729 | 0.737 |
| CoreMark program, 32 KiB simulation RAM, mcycle (CRCs verified x2) | 2,520,901 | 2,573,624 | 2,590,590 | 2,586,274 |
| IRQ entry, cycles (steady / first) | 5 / 41 | 5 / 41 | 5 / 41 | 5 / 41 |
| context switch, cycles | 270 | 292 | 292 | 292 |
| ASIC view vs FPGA view, mcycle | -4.18 % | -3.67 % | -3.23 % | - |

The differences between DM and the DSE-core configurations are mostly the DSE core's extra hit cycle, not the
organisation. With the hit latency matched (FAST_HIT), set associativity is faster than direct mapping at every capacity
in the geometric mean; DM_VC4 is slower because its eviction is serialised with the refill. Full sweep (256 B - 8 KiB,
lines 8 / 16 / 32 B, 1 / 2 / 4 ways, victim depth 2 / 4 / 8): `REVIEW_RESPONSE.md` (M1, M2) and `results/m2/M1_M2_REPORT.md`.

Branch predictor off: +6.48 % (DM) to +6.67 % (DM_VC4) cycles, geometric mean over the 12 kernels.

Extended conflict probe (`sw_metrics/conflict/`, 2026-10-08; 35 patterns x 6 configurations x 4 KiB and 1 KiB, both runs
identical, every window equal to the independent cache model, 390 windows; `results/conflict_probe.csv`). Line (s, k) at
0x0C00 + k * span + s * 16 maps to one set per s in every organisation. D-cache hit %:

| pattern (4 KiB unless noted) | DM | DM_DSE | SA2 | SA4 | DM_VC4 |
|---|---:|---:|---:|---:|---:|
| cyclic, 1 set, N = 2 | 98.4 | 0 | 100 | 100 | 100 |
| cyclic, 1 set, N = 3 / 4 | 0 / 0 | 0 / 0 | 0 / 0 | 100 / 100 | 100 / 100 |
| cyclic, N = 2 per set, 4 / 5 / 32 sets | 0 | 0 | 100 | 100 | 100 / 50 / 50 |
| cyclic, N = 3 per set, 2 / 3 sets | 0 | 0 | 0 | 100 | 100 / 33.3 |
| random, N = 2 per set, 5 / 8 / 16 sets | 52 / 48 / 53 | 51 / 48 / 53 | 99 / 100 / 100 | 100 | 90 / 76 / 65 |
| 1 KiB, cyclic, 1 set, N = 5 / 6 / 7 | 0 | 0 | 0 | 0.3 / 0 / 0 | 100 / 66.7 / 0 |
| 1 KiB, random, 1 set, N = 8 | 24.4 | 9.6 | 24.4 | 49.0 | 59.0 |

- The victim buffer is shared: DM_VC4 holds two lines per set in at most four sets; SA2 in every set.
- The collapse of a cyclic sweep longer than the capacity (published Table 6, N = 7) is the FIFO / round-robin replacement
  meeting a cyclic order: with the same lines in random order DM_VC4 keeps 59 % at N = 8 (1 KiB).
- The direct-mapped D-cache's two-entry L0 holds N = 2 lines of one set (98.4 %); DM_DSE, without L0, does not.
- Write-through, no write-allocate: a write miss neither fills nor evicts. A victim hit costs about 19-22 cycles per probe
  access, a main hit 10-14, a miss 26-30.

## 3. FPGA (Cyclone IV E EP4CE115, Quartus 20.1, 50 MHz)

Current RTL (16 KiB RAM, FPGA register file / BHT in M9K, cycle-exact): ten common seeds 1..10 per point, two independent
passes, all 40 paired rows equal on 115 hardware fields (runtime excluded). Sources:
`results/fpga_points_fpga_common_seeds_continued_20261009_p{1,2}.csv` and the paired seed summaries of the same tag.
Timing corner: Slow 1200 mV 85 C. Power: Quartus default toggle-rate estimate (typical VCCINT 1.20 V, ambient 25 C, 12.5 %
toggle activity, low confidence); the power temperature is separate from the timing corner.

| point | LE [min, max] | registers | M9K | Fmax Slow 85C, MHz [min, max] | setup slack Slow 85C, ns (min) | power total, mW [min, max] |
|---|---|---:|---:|---|---:|---|
| dm_4kb | 12,800 - 12,842 | 7,198 | 30 | 52.27 - 56.18 | +0.870 | 251.64 - 258.93 |
| dse_4kb | 14,302 - 14,364 | 7,480 | 30 | 51.02 - 55.21 | +0.399 | 262.46 - 270.41 |
| sa2_4kb | 16,670 - 16,739 | 7,877 | 40 | 51.96 - 54.54 | +0.754 | 278.61 - 283.04 |
| vc4_4kb | 17,096 - 17,148 | 9,265 | 30 | 51.52 - 54.40 | +0.591 | 276.31 - 282.35 |

Means (sample SD), in the order DM / SA2 / DM_VC4 / DM_DSE: LE 12,816.00 (12.37) / 16,699.90 (22.60) / 17,124.00 (15.76) /
14,332.60 (20.41); Fmax at Slow 85 C 54.73 (1.03) / 52.92 (0.83) / 53.28 (1.17) / 53.61 (1.38) MHz; estimated total power
255.11 (1.80) / 281.01 (1.24) / 279.52 (1.72) / 265.97 (2.62) mW. Organisations are compared within the same seed; no
per-configuration best seed is selected.

Board (DE2-115), measured 2026-10-13 and 2026-10-16 with the current RTL and common seed 2: all 100 cases passed (4 RAM
sweeps, 48 short and 48 full-iteration Embench cases over the four configurations). An independent raw-log audit confirms
one complete PASS / DONE frame per accepted capture and all 28 comparable numeric UART fields equal to both RTL reference
passes; SOF / firmware hashes, the 227 RTL files and the programming receipts match. Scope: one physical pass (a second
board pass is not scheduled); cases 1..42 have manual LED / HEX confirmation, cases 43..100 UART evidence only. Audit:
`results/board_20261013/final_board_audit_20261016.json`; observed counters: `results/board_20261013/board_counters_pass1.csv`.
Full-iteration workloads do not establish a normalised or certified Embench score.

Before the register-file / BHT change (R14 .. R16, flip-flop arrays; `results/fpga_points_r14_p{1,2}.csv`): dm_4kb
15,440 - 15,546 LE / 8,430 registers / 26 M9K, dse_4kb 16,989 - 17,063, sa2_4kb 19,360 - 19,474, vc4_4kb 19,810 - 19,875;
the change saves 2,630 (DM) to 2,680 (DM_VC4) LE, 13.5 - 17.0 %. Per module (`results/a1_le_breakdown_rfbht.md`):
register file 1,386 -> 52 LE, BHT 962 -> 636 LE incl. its valid bits, CPU core 6,451 -> 3,818 LE.

- Other points (seed 2, `results/fpga_points_r15_p{1,2}.csv`): sa4_4kb 21,821 LE (Fmax 50.95 MHz); 8 KiB caches: DM 16,812,
  DM_DSE 19,364, SA2 23,629, DM_VC4 22,262, SA4 28,891 LE; every point closes 50 MHz.
- FAST_HIT 0 -> 1 (seed 2, `results/le_r16_compare.log`): SA2 +456 LE, Fmax 53.71 -> 51.65 MHz; DM_VC4 +115 LE; DM_DSE
  +345 LE; SA4 +881 LE; worst setup slack +0.639 ns (SA2).
- 20,000 LE is a soft target; SA4 and the 8 KiB set-associative / victim points exceed it.
- The other points listed above are R15 / R16 (flip-flop arrays) and were not re-fitted.

## 4. ASIC (sky130A, sky130_fd_sc_hd, OpenLane 2.3.10 local copy, 20 ns clock)

Sign-off gate: route / Magic / KLayout DRC 0, LVS 0, XOR 0, illegal overlap 0, antenna 0, setup >= 0 at every tt and ff
corner, hold >= 0 at every corner. The ss corner (100 C, 1.60 V) is reported, not gated. The OpenRAM macros have TT
Liberty only, so ss / ff numbers are optimistic on paths through the SRAMs. Every PD run reads a frozen RTL snapshot; the
current one is `asic/snapshots/rtl_rfbht` (RTL manifest 6c4ccffd, run names `*_rtl6c4c_*`).

### 4.1 Accepted layouts on RTL 6c4ccffd

Each configuration was run twice as a complete flow from step 1 with fresh tags and gates declared at launch (one planned
pause after the second gate, then the detailed routing and the sign-off part). Both runs of each pair produced the same
final netlist and DEF byte for byte and the same KLayout GDS once the GDS timestamps are ignored. The Magic GDS of every
pair differs only in the random two-letter prefix Magic gives the sub-cells of the 2 KiB SRAM macro (320 structure names
and 56,677 references, identical record count; checked record by record), so the geometry is the same.

| item | DM | SA2 | DM_VC4 |
|---|---:|---:|---:|
| runs | `dm_grid3665x2900_rtl6c4c_rsztf_tdp_rszctsall_noor34_rcrep_r1` / `_r2` | `sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rszctsall_rtl6c4c_r2` / `_r3` | `vc4_corr3800x3400_f220_rszctsall_d34_rtl6c4c_scr_r1` / `_r2` |
| die | 3665 x 2900 um, 10.63 mm2 | 3400 x 3400 um, 11.56 mm2 | 3800 x 3400 um, 12.92 mm2 |
| std cells | 1.4036 mm2, 200,623 cells | 1.4874 mm2, 218,156 cells | 1.5851 mm2, 241,820 cells |
| routed wire | 6.958 m | 9.370 m | 10.906 m |
| route / Magic / KLayout DRC, LVS, XOR, antenna | 0 | 0 | 0 |
| setup max_tt / nom_tt / min_tt, ns | +0.635 / +0.890 / +1.133 | +0.616 / +0.995 / +1.283 | +1.274 / +1.497 / +1.707 |
| setup max_ff / nom_ff / min_ff, ns | +3.570 / +3.957 / +4.168 | +3.572 / +3.947 / +4.193 | +3.699 / +4.229 / +4.571 |
| setup max_ss / nom_ss / min_ss, ns (reported) | -6.755 / -5.941 / -5.594 | -8.373 / -7.441 / -6.491 | -7.039 / -6.504 / -5.908 |
| worst hold, ns (9 corners) | +0.010 (min_ff) | +0.020 (max_ff) | +0.020 (max_ff) |
| timing-repair buffers / clock buffers / antenna diodes | 26,198 / 3,685 / 7,580 | 16,302 / 4,561 / 15,355 | 15,979 / 5,118 / 16,832 |
| DRV at nom_tt (reported): max slew / cap / fanout | 317 / 368 / 1,398 | 1,847 / 1,195 / 427 | 1,459 / 1,334 / 437 |
| DRV, worst corner (reported): max slew / cap / fanout | 1,449 / 446 / 1,398 | 7,610 / 2,015 / 427 | 7,181 / 2,601 / 437 |
| power, vectorless (OpenSTA default activity, nom_tt) | 109.43 mW | 121.69 mW | 127.85 mW |
| power, flow estimate (`power__total`, max_ff) | 122.27 mW | 136.68 mW | 143.90 mW |
| power, activity-based exact window (12 kernels, nom_tt, RCX) | 115.40 - 123.98 mW, mean 120.28 | in progress | in progress |
| energy per instruction, exact window | 2,633 - 6,580 pJ, GM 3,633 | in progress | in progress |
| gate-level simulation, 12 kernels x 2 | mcycle = ASIC-view RTL, windows equal | in progress | in progress |
| register-mapped LEC RTL == final netlist | proved, two passes | gold == N1 proved; N1 == final in progress | proved, two passes |

Recipe per configuration (each knob was measured as one change against the previous recipe, section 4.2):
DM: the signed R14 grid floorplan and knobs, post-CTS timing repair also at ss (`PL_RESIZER_CORNERS` tt / ss / ff, a local
OpenLane variable), the other resizer steps at tt / ff, timing-driven placement, and the or3 / or4 cell families excluded
(`config_R14_FINAL_rtl6c4c_rsztf_tdp_rszctsall_noor34_rcrep.json`). SA2: the corridor floorplan and the SA2 knobs (cap
margin 20 %, fanout 16, one site of cell padding, timing-driven placement, clock on met3 - met5, two-pass post-route hold
ECO) with post-CTS timing repair at ss (`config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rszctsall_rtl6c4c.json`).
DM_VC4: the SA2 recipe on a 3800 x 3400 corridor floorplan with placement target density 34 % instead of 42 %
(`config_corr3800x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rszctsall_d34_rtl6c4c.json`). The acceptance drivers are
`asic/pipeline_acceptance_20261020.sh` (DM), `asic/pipeline_sa2_acc_20261020.sh` and `asic/pipeline_vc4_d34_20261020.sh`.

Compared with the R14 reference layouts (same cycle counts: the DM ASIC-view reference matches on all 43 fields of all 12
kernels, and the 6c4ccffd DM netlist reproduces every reference mcycle in GLS):

| item | DM R14 (r14F) | DM 6c4ccffd | SA2 R14 (ecomaxmin) | SA2 6c4ccffd |
|---|---:|---:|---:|---:|
| max_ss / nom_ss, ns | -7.365 / -6.897 | -6.755 / -5.941 | -7.917 / -7.304 | -8.373 / -7.441 |
| max_tt / nom_tt, ns | +1.708 / +1.894 | +0.635 / +0.890 | +0.838 / +1.118 | +0.616 / +0.995 |
| std cells | 1.3696 mm2 | 1.4036 mm2 (+2.5 %) | 1.4711 mm2 | 1.4874 mm2 (+1.1 %) |
| routed wire | 6.585 m | 6.958 m (+5.7 %) | 9.274 m | 9.370 m (+1.0 %) |
| vectorless nom_tt | 109.15 mW | 109.43 mW | 121.99 mW | 121.69 mW |
| exact-window mean | 119.45 mW | 120.28 mW (+0.7 %) | 129.64 mW | in progress |
| DRV at nom_tt: max slew / cap / fanout | 142 / 298 / 1,428 | 317 / 368 / 1,398 | 1,084 / 1,036 / 383 | 1,847 / 1,195 / 427 |

DM trades tt margin for ss: max_tt is 1.07 ns lower than R14 but still positive, ss is 0.61 - 0.96 ns better. SA2 is
0.46 ns (max_ss) / 0.14 ns (nom_ss) worse than R14 at ss (section 4.2). The remaining max slew / cap violations at nom_tt
rose against R14 in both designs (slew DM 142 -> 317, SA2 1,084 -> 1,847); they are reported, not gated. There is no
DM_VC4 reference: R14 had no signed DM_VC4 layout.

### 4.2 The ss corner on RTL 6c4ccffd

The first 6c4ccffd sign-offs used the R14 practice of running every resizer step at tt / ff only; they signed off clean but
with max_ss -16.838 ns (DM, `dm_grid3665x2900_rtl6c4c_rsztf_tdp_r2`) and -10.325 ns (SA2,
`sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rtl6c4c_r2`), far below R14, and were not accepted. The
paths that fail only at ss are the trap / stall cone fed by W-stage load data (DM) and if_req_addr -> I$ hit compare ->
next PC (SA2). One change at a time, screened after the second gate with an ss estimate on the global-route parasitics
(`asic/sta_query/ss_proxy.sh`, within about 0.8 ns of the post-route nom_ss), then a full flow:

| change | design | measured | kept |
|---|---|---|---|
| post-CTS timing repair also at ss (`PL_RESIZER_CORNERS`) | DM, SA2 | DM max_ss -16.84 -> -9.99; SA2 -10.33 -> -8.37 (signed); area almost unchanged | yes |
| exclude the or3 / or4 families (ss / tt delay ratio 2.15 - 2.27, library median 1.68; `asic/sta_query/lib_ss_tt_ratio.py`) | DM | max_ss -6.755 / nom_ss -5.941 (signed), max_tt +0.635, std cells +2.5 % | yes |
| the same exclusion | SA2 | synthesis rebuilds the half-cycle SRAM read path of I$ way 1 deeper: max_tt -0.514 ns | no |
| exclude or4 only | SA2 | worse at both tt and ss (ss estimate nom_ss -7.820 vs -6.889) | no |
| post-GRT timing repair also at ss (`GRT_RESIZER_CORNERS`) | SA2 | no gain (ss estimate -6.998 vs -6.889) | no |
| per-layer calibrated RC also inside the timing repairs (`LAYERS_RC_SCOPE "repair"`) | DM, SA2 | DM: no effect (DEFs byte-identical through step 43); SA2: layout changes from step 37, max_ss -8.876 / nom_ss -7.837 (both runs of the pair byte-identical), 0.4 - 0.5 ns worse | no (kept in the DM file only because it has no effect there) |
| hold repair limited to small delay cells (dlygate4sd*, dlymetal6s4s / 6s6s, clkdlybuf4s25 / 50 excluded) | SA2 | hold repair uses buf_2; ss estimate -6.890 with a worse TNS and thinner hold margins | no |

Why SA2 remains behind R14: its worst ss path (about 28 ns at ss against a 20 ns clock) runs through a six-buffer chain on a
high-fanout net (about 2.4 ns) and several four-stack gates that are slow at ss; the same logic decides the half-cycle
SRAM read path at tt, so every change that speeds up ss there costs tt. On the rejected `LAYERS_RC_SCOPE` variant 685 of
the 1,000 worst max_ss paths carried hold delay cells (mean 1.21 ns at ss; R14 354, DM 23); on the chosen SA2 recipe only
15 do, and none on the worst path (`asic/sta_query/hold_cells_on_setup_paths.py`). Closing the remaining gap needs an RTL
change in the I$ hit / next-PC cone, which is outside the agreed scope (no RTL or CPI change).

### 4.3 DM_VC4: congestion root cause and fix

Every DM_VC4 attempt before 2026-10-20 failed: on R14 RTL the post-route antenna repair did not converge (3600 and
3800 um dies), and on 6c4ccffd the second gate failed (3800 um die: setup nom_tt -0.913 / hold -0.615 ns with the clock on
met3 - met5, -0.598 / -1.482 ns without that limit; the alternative macro orientation on 3600 um: overflow 1,066, setup
-1.425 ns; post-GRT repairs off: setup -1.289 / hold -1.663 ns).

| measured (3800 x 3400 um die) | placement target density 42 % | 34 % |
|---|---:|---:|
| logic density in the cache corridor after the post-placement DRV repair (most of the corridor / peaks) | 35 - 45 % / 60 - 68 % | 28 - 35 % / 46 - 62 % |
| FastRoute "Extra Run for hard benchmark" in the re-routes of steps 41 and 44 | yes | no |
| wire added by the re-route after the post-GRT DRV repair (step 41) | +16 % (12.82 -> 14.91 m) | +0.4 % (12.96 -> 13.01 m) |
| global-route overflow before detailed routing | 277 - 350 | 0 |
| worst clock skew at the second gate | 3.35 - 3.47 ns | 0.955 ns |
| max slew / cap / fanout violations at the second gate | 8,216 / 1,861 / 605 | 1,108 / 737 / 399 |
| second gate, setup nom_tt / hold | -0.913 / -0.615 ns | +1.118 / +0.064 ns |

Mechanism: after global placement the DRV repair inserts about 13,400 buffers, mostly for the select nets of the two
256-entry DSE tag arrays (read with two indices) of I$ and D$, which sit in the corridor between the two cache macro
clusters. Their local density jumps to 60 - 68 %; in the full re-routes FastRoute cannot remove the overflow within 20
iterations and switches to its hard-benchmark mode, which detours wires (clock nets included) over long distances. The
routability-driven placement of OpenROAD reverts its own cell inflation in all three designs ("Revert Routability
Procedure"), so the placement target density is the lever. A smaller die does not work: 3600 x 3400 um at density 34 %
fails the first gate with an initial global-route overflow of 8,441. Tools: `asic/sta_query/grt_hotspot.sh` (global route
with few iterations and a congestion report), `congestion_bins.py`, `density_map.py`.

### 4.4 Equivalence (register-mapped LEC) on RTL 6c4ccffd

The chain is RTL == RTL + fsm (re-encoded FSMs) == N1 (byte-exact replay of the OpenLane synthesis before ABC) == final
netlist, every step in two independent passes compared object by object, every step with a negative control
(`scripts/verification/prepare_lec_6c4c.py`, drivers `asic/equiv/lec/run_frontends_vc4.ps1`, `run_lec_vc4.ps1`).

- DM (synthesis with the or3 / or4 exclusion): N1 is byte-identical to the previous DM N1 (the exclusion acts in ABC only);
  20,124 outputs, 34 left by per-output SAT closed by the algebraic multiplier proof (signed33 x signed33 mod 2^64);
  one-hot and undefined-value checks ALL_PROVED; N1 == final netlist: 20,096 outputs, 0 SAT, 32 residual outputs
  equivalent by `&cec`; the AND2 -> OR2 mutant is detected; full chain PASS1_EQUALS_PASS2.
- SA2: gold == N1 PASS1_EQUALS_PASS2 (the synthesis of every SA2 acceptance run is byte-identical to the replay source);
  N1 == final netlist (ceab735e, shared by the development run and the acceptance runs) in progress.
- DM_VC4: gold == N1 PASS1_EQUALS_PASS2: 22,117 outputs, 34 closed by the multiplier proof; the eight way-1 SRAM macros the
  RTL instantiates but DM_VC4 never reads are removed by synthesis and their read data are free inputs of the proof
  (`asic/equiv/lec/sram_align.py`), with a negative control that is detected. N1 == final netlist, both signed netlists
  (byte-identical, ca3a7314): 22,099 outputs, 0 SAT, 40 residual outputs equivalent by `&cec`; the AND2 -> OR2 mutant
  is detected (184 SAT outputs); full chain PASS1_EQUALS_PASS2 (`results/lec_vc4_6c4c_d34_20261020b/`).

The exact-window activity power needs a counter-freeze observer mapped onto each netlist; it is proved per netlist
(`scripts/verification/mapped_counter_freeze_rtl6c4c.py`, 65 obligations, twice): DM `~dut._029269_`, SA2 `~dut._031071_`,
DM_VC4 `~dut._033564_`.

### 4.5 Reference layouts on R14 RTL

These layouts read the R14 snapshot (`asic/snapshots/rtl_r14`); they are kept as the comparison point of section 4.1.

DM, 16 KiB RAM, grid3665x2900 (runs `dm_grid3665x2900_r1` / `_r2`, log names r14F_A / r14F_B), signed off 2026-10-02,
identical on 319 flow metrics, final netlist byte-identical (`results/asic_compare_dm_r14.md`):

| item | value |
|---|---|
| sign-off gate | all 0 |
| setup WNS, ns | nom_tt +1.894, max_tt +1.708; nom_ff +4.611, min_ff +4.811; nom_ss -6.897, max_ss -7.365 (TNS -11,439) |
| hold WNS, ns | nom_tt +0.186; worst +0.020 (max_ff) |
| area | die 10.63 mm2, std cells 1.3696 mm2 (197,878 cells), 16 SRAM macros 3.80 mm2, wire 6.585 m |
| power | vectorless nom_tt 109.15 mW; exact window 114.81 - 122.99 mW (mean 119.45), leakage 0.437 mW, EPI 2,612 - 6,547 pJ (GM 3,608), unknown activity 5.38 % (`results/activity_power_exact_dm_20261013/receipt.json`) |
| equivalence | register-mapped LEC RTL == N1 == both netlists, two executions; premises closed 2026-10-13 (asynchronous reset roots, undefined values, one-hot invariants, clock / edge audit), see below |

SA2, 16 KiB RAM, corridor 3400 x 3400 um (runs `sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1` /
`_r2`), signed off 2026-10-09, identical on 319 flow metrics, final netlist and DEF byte-identical
(`results/asic_compare_dm_sa2_20261009.md`):

| item | value |
|---|---|
| sign-off gate | all 0 |
| setup WNS, ns | nom_tt +1.118, max_tt +0.838, min_tt +1.331; nom_ff +4.056, min_ff +4.262, max_ff +3.803; nom_ss -7.304, max_ss -7.917 (TNS -13,417) |
| hold WNS, ns | nom_tt +0.152; worst +0.020 (min_ff, max_ff) |
| area | die 11.56 mm2, std cells 1.4711 mm2 (215,979 cells), wire 9.274 m |
| power | vectorless nom_tt 121.99 mW; exact window 127.45 - 131.75 mW (mean 129.64), leakage 0.437 mW, EPI 2,848 - 7,354 pJ (GM 4,317), unknown activity 4.42 % (`results/activity_power_exact_sa2_20261014/receipt.json`) |
| equivalence | RTL == RTL + fsm (38,300 cells) == N1 (21,489 outputs; 34 multiplier-cone outputs closed algebraically) == both netlists (21,471 outputs, 0 SAT), two executions object-by-object identical; AND2 -> OR2 mutant detected in two executions (`results/lec_sa2_negb_repeat_20261016/receipt.json`) |

Exact-window activity power method (both references and the 6c4ccffd layouts): two fresh GLS captures of the signed
netlist, each SAIF spanning exactly mcycle x 20 ns between the proved counter-freeze boundaries, then two independent
OpenSTA passes per kernel (nom_tt_025C_1v80, RCX parasitics); pass 1 must equal pass 2 on every field. The older captures
spanned (mcycle + 1) x 20 ns; every kernel of both references is within 0.005 mW of its exact-window value.

LEC premises closed on 2026-10-13 / 14 for the R14 DM proof (each twice, each with a failing negative control):
asynchronous reset between edges (all 19,087 final flop bits pair with gold; 7,519 share the reset root `reset_sync_q` and
the reset value, 11,568 have no reset on either side; `asic/equiv/lec/arst_audit.py`), undefined values (all 1,401
undefined sources of the gold model made free inputs: 20,124 / 20,124 outputs UNSAT), the one-hot invariant of the four
re-encoded FSMs, and a clock / edge audit of every flop. Outside the claim: sequential equivalence without the register
mapping and the SRAM macro contents (black boxes, covered by GLS).

### 4.6 DM, 8 KiB RAM, grid2800x2900 (signed off 2026-09-28)

Runs `dm_ram8k_grid2800x2900_drtant_r1` / `_r2` (final3_A / final3_B): identical on 302 flow metrics, final netlist
byte-identical. Workloads: the 12 project kernels of that time.

| item | value |
|---|---|
| sign-off gate | all 0 (antenna 0 after the post-detailed-route repair) |
| setup WNS, ns | nom_tt +2.086, max_tt +1.960, max_ff +4.603; nom_ss -7.413, min_ss -6.425, max_ss -8.311 |
| hold WNS, ns | nom_tt +0.224; worst +0.030 (max_ff) |
| area | die 8.12 mm2, std cells 1.400 mm2 (192,005 cells), 12 macros 2.664 mm2, wire 6.60 m |
| power | vectorless nom_tt 102.05 mW; flow metric 115.5 mW (max_ff); activity-based 110.61 - 115.43 mW |
| equivalence | RTL == RTL + fsm == N1 == routed netlist (register-mapped LEC, twice, with negative controls) |

### 4.7 1 KiB caches, 8 KiB RAM (2026-09-18)

Run `dm_c1k_baseline` (`asic/soc_dm_control/runs/sync_final`): die 5.22 mm2, 186,877 cells, setup nom_tt +3.41 ns, worst ss
-13.26 ns, power nom_tt 196.4 mW (vectorless). Timed with an SDC that dropped the clock uncertainty and the I/O
constraints; re-timed with the corrected SDC: setup tt +3.16 ns, hold tt -0.048 / ss -0.123 / ff -0.146 ns
(`asic/evidence/sdc_recheck_1kb_research/`).

### 4.8 Floorplan and die screening

- Corridor floorplan (the three organisations on one floorplan, 2026-10-06): DM signs off on 11.305 and 11.56 mm2; SA2 needs
  its own knobs (above); `asic/fp_explore/fp_summary_20261006.md`.
- SA2 die: 10.54 mm2 routes but fails the half-cycle I$ way-1 read at max_tt (-0.573 ns); 11.05 mm2 failed the second gate
  twice (setup -0.332 ns at nom_tt, `results/sa2_minimality_screen_20261011_pair.json`); 11.305 mm2 stalled in the
  incremental detailed route after the hold ECO; 11.56 mm2 is the smallest signed SA2 die.
- DM_VC4 die: 3600 x 3400 um fails at density 34 % (section 4.3); 3800 x 3400 um is the signed die.

## 5. Historical 1 KiB mirror results (2026-09-16 .. 17), corrected

The first ablation (CACHE_CONFIG 3 as "DM on the ten-state controller") was in fact DM + VC4 with the lookup disabled,
because the eviction copy was gated on the wrong flag. Corrected numbers (old project kernels, 1 KiB): controller cost
+9.35 % (reported +10.25 %), associativity -0.34 % (reported -1.16 %), SA2 wins / ties / losses 3 / 8 / 1 (reported
11 / 1 / 0), capacity sweep at 512 B -3.52 % (reported -9.57 %), line 64 B -1.39 % (reported -4.78 %). These results are
superseded by the sweep of section 2.

## 6. What is not established

- The ss corner does not close at 50 MHz on any layout (max_ss -6.8 to -8.4 ns on the accepted 6c4ccffd layouts); CPI must
  not change, and closing ss needs a deeper pipeline or RTL changes in the critical cones.
- The OpenRAM macros have TT Liberty only; their address / write-mask inputs carry a 0.04 ns max_transition that buffers
  cannot meet at the 10 um row halo; these slew violations are reported, not fixed. DRV counts are reported, not gated.
- The stock OpenLane EQY step does not pass on this design; the register-mapped LEC above is the equivalence evidence.
  Sequential equivalence without the register mapping, asynchronous events between edges, paired initialisation and the
  SRAM contents remain outside the claim.
- Board: one physical pass of the 100 cases; cases 43..100 lack manual LED / HEX observations and photos are not verified.
  FPGA power is a Quartus default-activity estimate, not a board measurement.
- No ASIC build of a FAST_HIT point.
- UVM coverage is functional for DM / SA2 / DM_VC4 / DM_DSE; no complete code coverage or SA4 / FAST_HIT UVM coverage is
  claimed.
- CoreMark: simulation with a 32 KiB RAM; no official score.
- The frozen ACT4 harness indexes only 512 KiB; the maintained runner generates the 1 MiB correction separately.
- The frozen RTL manifest excludes the SA2 / DM_VC4 ASIC tops and the DSE SRAM adapter; their hashes are recorded with each
  PD run and in `results/workspace_audit/asic_input_provenance.json`.

## Appendix: sources

- Architecture: `results/rfbht_4kb_p{1,2}.csv`, `results/rfbhtf_4kb_p{1,2}.csv`, `results/coremark_rfbht_4kb_p{1,2}.csv`,
  `results/unified_metrics.md`; sweep baselines `results/upstream_r14_4kb_p{1,2}.csv`, `results/m2/`,
  `results/bp0_upstream_r14_4kb_p{1,2}.csv`.
- FPGA: `results/fpga_points_fpga_common_seeds_continued_20261009_p{1,2}.csv`,
  `results/fpga_common_seeds_continued_20261009_ppa.{json,md}`; historical `results/fpga_points_r14_p{1,2}.csv`,
  `results/fpga_points_r15_p{1,2}.csv`, `results/le_r16_compare.log`.
- ASIC: run directories `asic/<design>/runs/<tag>/`, the gate log `asic/gated_pd.log`, the comparison tables
  `results/acceptance_20261020/` (`ppa_three_configs_20261020.md`, `ppa_dm_r1_vs_r14.md`, `ppa_sa2_r1_r2_vs_r14.md`,
  `ppa_vc4_r1_r2.md`), the ss study `results/ss_study_20261015/`, the DM_VC4 congestion study
  `results/vc4_congestion_20261020/`, exact-window GLS and power `results/gls_exact_*_20261020/`,
  `results/activity_power_exact_dm_noor34_20261020/`, LEC `results/lec_dm_noor34_20261020/`,
  `results/lec_sa2_6c4c_20261015/`, `results/lec_vc4_6c4c_d34_20261020b/`, archived evidence of deleted runs
  `results/pd_run_archive/`.
