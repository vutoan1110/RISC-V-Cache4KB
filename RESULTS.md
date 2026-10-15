# Results

Current measured results of the research copy of the RISC-V SoC, per configuration. Rules for every number: executed
twice and compared field by field; the corner is named for every timing value; the power method is stated (flow
estimate or measured switching activity); sign-off checks are listed before PPA. History and reasons: `NHAT_KY.md`;
procedures: `QUY_TRINH.md`; review items: `REVIEW_RESPONSE.md`.

Supplemental verification on 2026-10-09 (the frozen design inputs remain unchanged):

- UVM: 48 cases in each independent pass, identical scoreboard fields. SoC directed ISA, peripherals/IRQ and
  two-byte serial UART RX run on DM/SA2/DM_VC4/DM_DSE, seeds 1/2/3; AXI stress uses line words 2/4/8/16 and
  seeds 1/2/3. Wrong-byte UART controls fail in both passes. Receipt: `results/uvm_cache_uart_20261009/verification.json`.
- Architecture adapter: 43 ACT4 cases plus an upper-half data/instruction test run twice. All 43 ACT4 signatures,
  retirement counts and cycles equal the previous result; the upper-half test detects the original 512 KiB alias.
  The maintained runner generates a corrected 1 MiB adapter separately from the frozen TB; its exact delta and
  inputs are recorded in `results/architecture_window_20261009/verification.json`. This is unprivileged I/Zmmul
  verification, not full privileged-ISA compliance.
- Random differential: 50 generated programs per pass, two fresh compilations and independent measurements;
  all 50 paired summary rows and complete trace bytes match the preceding RF/BHT result. Each case now gates the
  simulator return code, complete PASS/termination, absence of Error/Fatal and full trace integrity. Separate raw
  evidence for both passes: `results/random_diff_checked_20261009/verification.json`. This original test compares
  predictor OFF/ON on the same core.
- Independent Spike reference completed2026-10-11:50seeds x2 fresh Spike processes, all100 native exits0, all200
  preserved independently executed current-RTL traces match;7105 retirements/pass and300 wrong-trace controls
  detected. PC/instruction/GPR writes and store address/enabled bytes/strobes are compared. Receipt:
  `results/spike_random_reference_20261011/receipt.json`. Scope is the generated RV32I/Zmmul core subset, not
  SoC MMIO/interrupt/cache/timing or complete privileged-ISA compliance.

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
- The research wrappers/QSFs select this 4 KiB profile; the generic HDL default remains 1 KiB. The five/ten-state
  controller descriptions above refer to I-cache; D-cache DM/DSE have seven/eleven states.
- Preserved CoreMark results use simulation RAM32KiB (`sw/coremark/coremark_link.ld` places the stack at32KiB).
  That preserved -O2 rv32i_zmmul firmware needs .text13,952 + .rodata2,445 + .data24 + .bss2,020 + stack1,024
  =19,465 bytes, exceeding16KiB. This footprint applies to that firmware, not every possible CoreMark port.
  The cache parameters and RAM latency are unchanged across the compared configurations.
- The isolated -Os integer APB-timer port was built independently twice; performance and validation ELF/HEX bytes
  match. Both profiles have image_end14,032 bytes + reserved stack1,024 =15,056 bytes, a static margin of1,328
  below16KiB. Receipt: `results/coremark_standard_apb_build_pair_20261011.json`. This is a paired build footprint,
  not a score or proof of runtime fit in16KiB: its unchanged linker still places the stack at32KiB.
- Workloads: the 12 upstream Embench-IoT kernels that fit 16 KiB (aha-mont64, crc32, depthconv, edn, huffbench,
  matmult-int, md5sum, nettle-sha256, slre, statemate, tarfind, ud; not official Embench scores), preserved short
  CoreMark sweeps (one iteration, full-program mcycle), and the standard-duration matrix below. Earlier results
  used12 self-written kernels; they are marked where they appear.
- CoreMark numeric CRCs are verified for the current six base and five FAST_HIT 4 KiB points: 22 fresh simulations,
  two independent compilations, all 40 snapshot fields equal between passes and the prior baseline. Accepted APB
  UART transmit bytes give seed/list/matrix/state/final CRCs e9f5/e714/1fd7/8e3a/e714, matching the source references.
  Receipt: `results/coremark_crc_checked_20261009/verification.json`. The maintained canonical runner now rejects
  missing/wrong CRCs before CSV/PASS; a separate DM pair matches all 43 CSV columns. Its full-program snapshot still
  includes initialization/CRC/UART reporting, RAM is 32 KiB, and the short run is not an official CoreMark score.
  The expanded supported capacity/line/organization sweep is now verified at all92 points (49 base,43 FAST):
  184 fresh simulations in two separately compiled passes, source-known CRCs and all40 counters identical to
  both historical references. Independent raw verification checks241 inputs and379 artifacts, exact elaborated
  parameters, native completion and all paired CSVs. Receipts:
  `results/coremark_sweep_crc_20261010/verification.json` and
  `results/coremark_sweep_crc_independent_audit_20261010/receipt.json`.
  SA4_256B_L16 is excluded because four sets cannot support the fixed eight-entry L0 index; it is not a result.
- Views: FPGA view (RTL with the FPGA memories; organisation comparison), ASIC view (RTL with the OpenRAM models; the
  chip's cycle counts; fewer cycles than the FPGA view because the ASIC RAM wrapper has no FPGA latency hooks), gate
  level (signed-off netlist; reproduces the ASIC view cycle for cycle).

### 1.1 Standard-duration CoreMark, simulation RAM32KiB,50MHz

Completed2026-10-11: four4KiB cache configurations x performance/validation x two independent executions,
16/16 PASS. Eight pairs match all108 scalar measurement fields each (including40 counters),864 comparisons.
Each pass uses separately compiled private RTL models and independently built firmware; the complete first DM
performance screen supplies that pair's first execution. Native commands all return0. Inputs remain unchanged.

| configuration | performance ticks | seconds at50MHz | CoreMark iterations/s | CoreMark/MHz | validation ticks |
|---|---:|---:|---:|---:|---:|
| DM | 719996901 | 14.39993802 | 76.389218 | 1.527784 | 722669045 |
| SA2 | 691866743 | 13.83733486 | 79.495077 | 1.589902 | 693576231 |
| DM_VC4 | 747676057 | 14.95352114 | 73.561270 | 1.471225 | 751155457 |
| DM_DSE | 802958516 | 16.05917032 | 68.496689 | 1.369934 | 806692095 |

Method: current-RTL FPGA simulation view, BP on, FAST_HIT=0,4KiB I/D caches,16B lines,L0=8, RAM32768 bytes.
The unchanged CoreMark algorithms use TOTAL_DATA_SIZE=2000, single context, MEM_STATIC, HAS_FLOAT=0 and
ITERATIONS=0 calibration; every measured run selects1100 iterations. Performance seeds0/0/0x66 and validation
seeds0x3415/0x3415/0x66 pass the source-known CRCs. All final iterate intervals exceed500,000,000 ticks (10s).
Only the upstream final iterate interval determines throughput; the stored whole-program counters have a
different window. APB TIMER_CMP=0xffffffff is configured before timing. Every accepted COUNT delta equals
independently observed clock-edge delta and elapsed simulation time/20ns; timer and core both run at50MHz.
Exact rates are calculated from raw integer ticks; integer UART seconds/rates retain upstream rounding.

Compiler: riscv64-unknown-elf-gcc(14.2.0+19)14.2.0, rv32i/ilp32 multilib. Uniform flags for benchmark C sources:
`-Os -march=rv32i_zmmul_zicsr -mabi=ilp32 -ffreestanding -fno-builtin -msmall-data-limit=0
-ffunction-sections -fdata-sections -Wall -Wextra`; the uniform `-Dmain=coremark_main` redirects entry to the
isolated wrapper. Simulator: Verilator5.053 devel,vUNKNOWN-built20260917-1aa8791, assertions enabled.
This matrix uses a different firmware/compiler and timing window from the preserved -O2 one-iteration sweep.
These are simulation-derived scores with RAM32KiB, not physical-board measurements or EEMBC certification.
Reporting requirements: [EEMBC CoreMark rules](https://github.com/eembc/coremark/blob/main/README.md).

Evidence: `results/coremark_standard_apb_matrix_20261011/receipt.json`, `cases.csv` (all16 cases),
`performance_paired.csv` (four paired performance rows with exact decimal strings) and `csv_export.json`.
Reproducible runner: `scripts/verification/run_coremark_standard_apb_matrix.py`; two independent build receipts
and the initial screen are pinned in its receipt. Raw UART/compile/simulation logs and executables are retained.

## 2. Architecture (FPGA view, 4 KiB caches, 16 KiB RAM, BP on)

Source: `results/unified_metrics.md` (generated by `scripts/metrics/unified_table.py`).

| metric | DM | SA2 | DM_VC4 | DM_DSE |
|---|---:|---:|---:|---:|
| CPI, 12 Embench-IoT kernels | 1.5136 | 1.6597 | 1.6780 | 1.6614 |
| I$ hit % | 99.70 | 99.65 | 99.72 | 99.70 |
| D$ read hit % | 99.16 | 99.59 | 99.59 | 99.16 |
| branch mispredict % | 10.57 | 10.57 | 10.57 | 10.57 |
| Embench speed / MHz, GM | 0.809 | 0.739 | 0.729 | 0.737 |
| CoreMark program, simulation RAM 32 KiB, mcycle (numeric CRCs verified x2) | 2,520,901 | 2,573,624 | 2,590,590 | 2,586,274 |
| IRQ entry, cycles (steady / first) | 5 / 41 | 5 / 41 | 5 / 41 | 5 / 41 |
| context switch, cycles | 270 | 292 | 292 | 292 |
| ASIC view vs FPGA view, mcycle | -4.18 % | -3.67 % | -3.23 % | - |

The differences between DM and the DSE-core configurations are mostly the DSE core's extra hit cycle, not the
organisation. With the hit latency matched (FAST_HIT), set associativity is faster than direct mapping at every
capacity in the geometric mean; DM_VC4 is slower because its eviction is serialised with the refill. Full sweep
(256 B - 8 KiB, lines 8 / 16 / 32 B, 1 / 2 / 4 ways, victim depth 2 / 4 / 8): `REVIEW_RESPONSE.md` (M1, M2) and
`results/m2/M1_M2_REPORT.md`.

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
- The collapse of a cyclic sweep longer than the capacity (published Table 6, N = 7) is the FIFO / round-robin
  replacement meeting a cyclic order: with the same lines in random order DM_VC4 keeps 59 % at N = 8 (1 KiB).
- The direct-mapped D-cache's two-entry L0 holds N = 2 lines of one set (98.4 %); DM_DSE, without L0, does not.
- Write-through, no write-allocate: a write miss neither fills nor evicts. A victim hit costs about 19-22 cycles per probe
  access, a main hit 10-14, a miss 26-30.

## 3. FPGA (Cyclone IV E EP4CE115, Quartus 20.1, 50 MHz)

Current RTL (RAM 16 KiB, FPGA register file/BHT in M9K, cycle-exact): ten common seeds 1..10 per point, two
independent passes, all 40 paired rows equal on 115 hardware fields (runtime excluded). Sources:
`results/fpga_points_fpga_common_seeds_continued_20261009_p{1,2}.csv` and the paired seed summaries of the same tag.
Seeds 1/3/4 retain independently measured rfbht provenance; seeds 5..10 and common seed 2 were refitted twice.
Timing corner: Slow 1200 mV 85 C. Power: Quartus default toggle-rate estimate, Typical VCCINT 1.20 V, ambient 25 C,
12.5% default toggle activity, low confidence; power temperature is separate from the timing corner.

| point | LE [min, max] | registers | M9K | Fmax Slow 85C, MHz [min, max] | setup slack Slow 85C, ns (min) | power total, mW [min, max] |
|---|---|---:|---:|---|---:|---|
| dm_4kb | 12,800 - 12,842 | 7,198 | 30 | 52.27 - 56.18 | +0.870 | 251.64 - 258.93 |
| dse_4kb | 14,302 - 14,364 | 7,480 | 30 | 51.02 - 55.21 | +0.399 | 262.46 - 270.41 |
| sa2_4kb | 16,670 - 16,739 | 7,877 | 40 | 51.96 - 54.54 | +0.754 | 278.61 - 283.04 |
| vc4_4kb | 17,096 - 17,148 | 9,265 | 30 | 51.52 - 54.40 | +0.591 | 276.31 - 282.35 |

Means (sample SD), in configuration order DM / SA2 / DM_VC4 / DM_DSE:
LE 12,816.00 (12.37) / 16,699.90 (22.60) / 17,124.00 (15.76) / 14,332.60 (20.41);
Fmax at Slow 85 C 54.73 (1.03) / 52.92 (0.83) / 53.28 (1.17) / 53.61 (1.38) MHz;
estimated total power 255.11 (1.80) / 281.01 (1.24) / 279.52 (1.72) / 265.97 (2.62) mW.
Compare organisations within the same seed; no per-configuration best seed is selected.

Board preparation is complete: 100 current-RTL SOFs under `output_files_board_matrix_6c4ccffd_seed2/`, all from
common seed 2. INDEX.csv binds each SOF hash to the expected MCYCLE/MINSTRET; BOARD_RESULTS_TEMPLATE.csv has
200 NOT_RUN rows for the two physical passes. Four canonical MIFs and canonical assemblies were restored.
Receipt: `results/fpga_common_seeds_continued_20261009_board_audit.json`.

Board session 2026-10-13 (DE2-115, scope fixed by the owner at one physical pass of the 100 cases): 42 cases measured
(ramsweep and 10 Embench kernels on all four configurations, statemate on DM and SA2). Every complete UART log matches
BOTH RTL reference passes on all 25 counters plus D_ACCESS; VERIFY_CODE is identical across the four configurations of
each kernel; the HEX display equals MCYCLE wherever it was read back. Independent re-check 42/42, 0 problems
(`results/board_20261013_independent_check/`); session evidence `results/board_20261013/`. Single physical executions;
58 cases remain (statemate DM_VC4 / DM_DSE, tarfind and ud on all four, and the 48 full-iteration cases).

Before the change (R14 .. R16, flip-flop arrays; `results/fpga_points_r14_p{1,2}.csv`): dm_4kb 15,440 - 15,546 LE / 8,430
registers / 26 M9K, dse_4kb 16,989 - 17,063, sa2_4kb 19,360 - 19,474, vc4_4kb 19,810 - 19,875; the change saves 2,630
(DM) to 2,680 (DM_VC4) LE, 13.5 - 17.0 %. Per module: `results/a1_le_breakdown_rfbht.md` (register file 1,386 -> 52 LE,
BHT 962 -> 636 LE incl. its valid bits, CPU core 6,451 -> 3,818 LE).

- Other points (seed 2, `results/fpga_points_r15_p{1,2}.csv`): sa4_4kb 21,821 LE (Fmax 50.95 MHz); 8 KiB caches: DM 16,812,
  DM_DSE 19,364, SA2 23,629, DM_VC4 22,262, SA4 28,891 LE; every point closes 50 MHz.
- FAST_HIT 0 -> 1 (seed 2, `results/le_r16_compare.log`): SA2 +456 LE, Fmax 53.71 -> 51.65 MHz; DM_VC4 +115 LE; DM_DSE
  +345 LE; SA4 +881 LE; worst setup slack +0.639 ns (SA2).
- 20,000 LE is a soft target; SA4 and the 8 KiB set-associative / victim points exceed it.
- Register file and BHT in M9K (2026-10-08): every simulation identical to R16, the ASIC netlist identical byte for byte;
  CPU core block power estimate 39.68 -> 28.08 mW (DM, seed 2).
- The other points listed above are R15 / R16 (flip-flop arrays) and were not re-fitted.

## 4. ASIC (sky130A, sky130_fd_sc_hd, OpenLane 2.3.10 local copy, 20 ns clock)

Sign-off gate: route / Magic / KLayout DRC 0, LVS 0, XOR 0, illegal overlap 0, antenna 0, setup >= 0 at every tt and ff
corner, hold >= 0 at every corner. The ss corner (100 C, 1.60 V) is reported, not gated. The OpenRAM macros have TT
Liberty only, so ss / ff numbers are optimistic on paths through the SRAMs. Power of the flow (`power__total`) is the
max_ff corner; the figures below name their corner and method.

### 4.1 DM, 16 KiB RAM, floorplan grid3665x2900 (signed off 2026-10-02)

Runs dm_grid3665x2900_r1 / _r2 (log names r14F_A / r14F_B): identical on 319 flow metrics, final netlist byte-identical.
Source: `results/asic_compare_dm_r14.md`.

| item | value |
|---|---|
| sign-off gate | Magic DRC 0, KLayout DRC 0, route DRC 0, LVS 0, XOR 0, overlap 0, antenna 0, hold violations 0 |
| setup WNS, ns | nom_tt +1.894, max_tt +1.708; nom_ff +4.611, min_ff +4.811; nom_ss -6.897, max_ss -7.365 (TNS -11,439) |
| hold WNS, ns | nom_tt +0.186; worst +0.020 (max_ff_n40C_1v95) |
| area | die 10.63 mm2, std cells 1.3696 mm2 (197,878 cells), 16 SRAM macros 3.80 mm2, wire 6.585 m |
| power, vectorless (OpenSTA default activity, nom_tt) | 109.15 mW |
| power, activity-based (GLS -> SAIF -> OpenSTA, nom_tt_025C_1v80, RCX) | 114.81-122.99 mW (mean 119.45); dynamic 114.37-122.55 mW (mean 119.02); leakage 0.437 mW; two independent STA passes |
| energy per instruction | 2,612-6,547 pJ; geometric mean 3,608 pJ |
| gate-level simulation | 12/12 kernels, mcycle = ASIC-view RTL |
| equivalence evidence | Legacy register-mapped SAT/CEC and multiplier algebra executions x2 (`asic/equiv/lec/run_lec_r14*.ps1`), 20,124 / 20,096 mapped outputs and negative control retained; complete sequential reset/clock/reachability closure is under audit, not an unconditional full LEC verdict |

DM activity power is now independently repeated and strictly verified for all 12 kernels: every value of all six
power groups and all activity-origin counts/shares match. Both vectorless runs reproduce the flow. Unknown activity
is 5.38%. The second execution reuses the preserved GLS/SAIF as fixed activity input; this is two independent STA
executions, not a second GLS. All 33 frozen inputs match before/after; locked DM PD layouts were not changed.
Receipts: `results/gls_power_r14F_A_power_verification.json`, `results/dm_activity_power_second_pass_20261010.json`.
Paired CSVs: `results/gls_power_r14F_A_power_p{1,2}.csv`; every second raw report ends in `.power.p2.rpt`.

Capture-window audit: all 24 preserved DM/SA2 SAIFs span `(mcycle+1)*20 ns`, one clock period longer than the
measured region, although the independent TB cycle counts match MCYCLE. Legacy CSV columns `win_t0_ns` and
`win_t1_ns` actually contain picoseconds. The paired STA results remain reproducible for those preserved inputs;
exact-window activity power requires fresh capture and repeated STA. No old SAIF, transition count or power
value was altered. Evidence: `results/embench_gls_evidence_audit_20261010/{receipt.json,gls_windows.csv}`.

The replacement passive GLS observer is locally justified on the exact signed DM and SA2 netlists by two
independent proof executions per design,65 obligations each: the full freeze predicate, all32 MCYCLE increment
bits and their actual clear/hold/increment D consumers. A separate raw-netlist/PDK implementation replayed all
252 paired CNF certificates/340,338 resolution steps, eight structural roots and12 actual wrong-observer witnesses.
Receipts: `results/mapped_counter_freeze_checked_20261010/{verification.json,independent_review.json}`.
These Boolean subproofs establish the local observer contract; they do not establish full LEC, initialization,
other counters, asynchronous events or timing behavior. Fresh exact-window GLS/SAIF and paired STA: DM done
(next paragraph), SA2 done (section 4.2).

Exact-window DM activity power (2026-10-13): two fresh GLS captures of the signed DM netlist, each SAIF spanning
exactly `mcycle*20 ns` and checked identical to the other except DATE, then two independent OpenSTA passes per
kernel (26 native STA executions, nom_tt_025C_1v80, RCX). Pass 1 = pass 2 on every field for all 12 kernels.
Total 114.81-122.99 mW (mean 119.45), dynamic 114.37-122.55 mW (mean 119.02), leakage 0.437 mW, EPI 2,612-6,547 pJ
(GM 3,608 pJ), unknown activity 5.38 %. Every kernel is within 0.005 mW of the preserved-SAIF value in the table
above, so the extra 20 ns window had no material effect on the DM numbers. Receipt:
`results/activity_power_exact_dm_20261013/receipt.json` (`VERIFIED_TWO_GLS_AND_TWO_STA_ACTIVITY_POWER_PASSES`);
paired CSVs `activity_power_p{1,2}.csv` in the same folder.

The maintained equivalence claim is deliberately narrower than the historical LEC verdict. Legacy helpers sampled
reset states and removed clocks from the mapped D-function check. A new unrestricted symbolic reset check has
proved the gold reset bases for 235 constant flops, 28 duplicates and 4 FSM groups in two independent executions;
paired reports: `results/dm_reset_base_structural_20261010_p{1,2}.json`. That sub-proof alone does not
close the raw N1/final paired reset relation or exact-input invariant bridge. A separate two-pass streaming audit
now verifies positive-edge scalar input `clk` for every flop in all four preserved functional flat models:
`results/dm_lec_clock_audit_20261010/receipt.json`. The source-to-model undefined-net abstraction is also an open
proof premise; clock and gold-reset sub-proofs do not establish full sequential equivalence.
These obligations must close before publishing an unconditional sequential RTL-to-routed-netlist proof.
PD sign-off, byte-identical routed artifacts, GLS and activity-power results are unchanged.

Premises closed on 2026-10-13/14 (each executed twice with identical results, each with a negative control that fails):

- Asynchronous reset between clock edges (the mapped proof runs on async2sync models): structural audit of the
  pre-async2sync gold and final models (`asic/equiv/lec/arst_audit.py`, `results/lec_arst_audit_20261013/`). All
  19,087 final flop bits of r14F_A and of r14F_B pair by name with gold; 7,519 have an asynchronous reset with the same
  root (`reset_sync_q`, active low, through aliases / buffers / inverters) and the same reset value on both sides,
  11,568 have none on either side; 0 mismatches. Controls: one ARST_VALUE bit flipped, one ARST moved to `reset_n`.
- Undefined values (the x / undriven := 0 abstraction of the LEC models): every one of the 1,401 undefined sources of
  the DM LEC gold model made a free input and mitered against the same model with them at 0 (`run_xsens.ps1`):
  20,124 / 20,124 outputs (every paired next state, duplicate check and output) UNSAT, i.e. independent of every
  undefined value in every state. This replaces the per-line closure of the 358 x lines (48 were still open).
  Control: an output driven by 1'x is found (SAT).
- One-hot invariant of the four re-encoded FSMs, re-proved on the exact current gold source (bridge of the older
  proof): Q one-hot => D one-hot (4 UNSAT) and one-hot reset codes (`results/lec_dm_inv_20261013{,_p2}/`); control: a
  group with a foreign bit fails.

Still outside the claim: sequential equivalence without the register mapping (not feasible at this size with the
available open-source engines) and the SRAM macro contents (black boxes; covered by GLS).

### 4.2 Unified corridor floorplans for DM, SA2 and DM_VC4 (2026-10-06 ..)

The three organisations on one floorplan (same die, same macro coordinates); first executions. Floorplan screening:
`asic/fp_explore/fp_summary_20261006.md`.

| | corr3400x3325_f220 (11.305 mm2) | corr3400x3400_f220 (11.56 mm2) |
|---|---|---|
| DM | signed off clean | signed off clean |
| SA2 | detailed routing stalled at 173 violations (iteration 30) | signed off clean 2026-10-09 with its own knobs (below) |
| DM_VC4 | re-route in antenna repair: 19,114 overflow | clock-tree detours on earlier global routes (NHAT_KY.md section 8); 12.24 mm2 candidate failed DRT convergence |

DM on the corridor floorplans (dm_corr3400x3325_f220_r1 / dm_corr3400x3400_f220_r1):

| item | 11.305 mm2 | 11.56 mm2 |
|---|---|---|
| sign-off gate | all 0 | all 0 |
| setup WNS, ns | nom_tt +1.818, max_tt +1.595, worst ff +3.851; nom_ss -8.292, max_ss -8.754 | nom_tt +1.755, max_tt +1.481, worst ff +3.695; nom_ss -9.517, max_ss -10.043 |
| hold WNS, ns (worst corner) | +0.002 (min_ff) | +0.018 (nom_ff) |
| std cells | 1.3736 mm2, 204,622 cells | 1.3760 mm2, 208,101 cells |
| wire | 6.68 m | 6.71 m |
| power | GLS/SAIF captured; paired STA power not established (archived screening) | not established (archived screening) |

SA2 on corr3400x3400_f220 (11.56 mm2), signed off 2026-10-09. Knobs (each measured, NHAT_KY.md section 8): post-GRT cap
margin 20, `MAX_FANOUT_CONSTRAINT` 16, cell padding 1 site per side, timing-driven global placement, clock trunks on
met3-met5, resizer on tt / ff only, post-route hold ECO in two passes (max_* extraction, then min_*). The 10.54 mm2 die
(3400 x 3100) routes but cannot close the I$ way-1 half-cycle SRAM read path (sign-off max_tt -0.573 ns). Runs
sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1 / _r2 (r2 a full flow from step 1, branched after
its first ECO like r1): identical on 319 flow metrics, final netlist and DEF byte-identical, SPEF identical except its
date line. Source: `results/asic_compare_dm_sa2_20261009.md`.

| item | value |
|---|---|
| sign-off gate | Magic DRC 0, KLayout DRC 0, route DRC 0, LVS 0, XOR 0, overlap 0, antenna 0, hold violations 0 |
| setup WNS, ns | nom_tt +1.118, max_tt +0.838, min_tt +1.331; nom_ff +4.056, min_ff +4.262, max_ff +3.803; nom_ss -7.304, max_ss -7.917 (TNS -13,417) |
| hold WNS, ns | nom_tt +0.152; worst +0.020 (min_ff, max_ff) |
| area | die 11.56 mm2, std cells 1.4711 mm2 (215,979 cells), 16 SRAM macros 3.80 mm2, wire 9.274 m |
| buffers | timing repair 15,240 (DM 24,448), clock buffers 4,519 and clock inverters 824, hold buffers 139 + 11 (two ECO passes), macro pin buffers 775 |
| power, vectorless (OpenSTA default activity, nom_tt) | 121.99 mW (DM 109.15 mW) |
| power, activity-based (GLS -> SAIF -> OpenSTA, nom_tt, RCX) | 127.45 - 131.75 mW over 12 kernels (mean 129.64); dynamic 127.02 - 131.31 mW, leakage 0.437 mW; unknown-activity share 4.42 % of output pins |
| energy per instruction | 2,848 - 7,354 pJ (GM 4,317), ASIC-view cycles |
| gate-level simulation | 12/12 kernels, mcycle = ASIC-view RTL = independent TB cycle count; exact-window recapture done (two fresh GLS passes, paragraph below) |
| DRVs left (reported, not gated) | nom_tt: max slew 1,084, max cap 1,036; worst corner: slew 7,885, cap 1,827, fanout 383 |
| equivalence | register-mapped LEC RTL == RTL+fsm == N1 == both final netlists, two independent executions object-by-object identical (paragraph below) |

SA2 activity power was evaluated by two independent OpenSTA executions from the same GLS SAIF inputs. All six power
groups (internal, switching, leakage and total) and activity-origin counts/shares match for every kernel; both
vectorless executions reproduce all six groups of the flow's nom_tt report. Evidence:
`results/gls_power_sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1_power_p{1,2}.csv`,
the per-kernel `.power.rpt` / `.power.p2.rpt`, and the `_power_verification.json` of the same tag.

Exact-window SA2 activity power (2026-10-14), the DM method: two fresh GLS captures of the signed SA2 netlist
(`results/gls_exact_sa2_full_p{1,2}_20261014`, counter-freeze mapping proved on this netlist), each SAIF spanning exactly
`mcycle*20 ns`, pair verified (`results/gls_exact_sa2_full_pair_20261014.json`), then two independent OpenSTA passes per
kernel (26 native STA executions, nom_tt_025C_1v80, RCX). Pass 1 = pass 2 on every field for all 12 kernels. Total
127.45-131.75 mW (mean 129.64), dynamic 127.02-131.31 mW (mean 129.21), leakage 0.437 mW, EPI 2,848-7,354 pJ (GM 4,317),
unknown activity 4.42 %. Every kernel is within 0.005 mW of the preserved-SAIF value in the table, so the extra 20 ns
period had no material effect, as for DM. Receipt: `results/activity_power_exact_sa2_20261014/receipt.json`
(`VERIFIED_TWO_GLS_AND_TWO_STA_ACTIVITY_POWER_PASSES`). Exact-window DM vs SA2: mean 119.45 vs 129.64 mW (+8.5 %), EPI
GM 3,608 vs 4,317 pJ (+19.7 %, which also carries SA2's extra ST_LOOKUP cycles).

SA2 equivalence (2026-10-13/14), the DM method (`asic/equiv/lec/run_lec_sa2.ps1`), two independent executions, each with
its own fresh byte-exact replay of the synthesis (`results/lec_sa2_20261013/p1`, `p2b`):
- RTL == RTL + fsm: Yosys `equiv_make -encfile` / `equiv_induct`, 38,300 cells proven, 0 unproven (four re-encoded FSMs).
- RTL + fsm == N1 (pre-ABC synthesis): 20,803 gold flop bits, 20,465 paired by name; of the 338 gold-only bits 231 are
  proved constant (greatest fixpoint), 18 are proved duplicates, 89 stay free inputs. 21,489 outputs: per-output SAT
  leaves 34 undecided (32 data-address bits and 2 duplicate checks, all in the fan-out of the ALU multiplier), closed by the
  multiplier proof: N1-side and RTL-side networks both equal signed33(A) x signed33(B) mod 2^64 (algebraic proof; the
  unsigned-specification and partial-product-mutation controls fail), `&cec` links to the LEC pair, residual `&cec`
  equivalent. One-hot invariant of the four FSM groups: 4 / 4 UNSAT and one-hot reset codes.
- N1 == final netlist of `_ecomaxmin_r1` and of `_r2`: 20,462 pairs, 3 N1-only bits free; 21,471 outputs each, 0 SAT,
  32 left by per-output SAT and closed by `&cec` (equivalent).
- Undefined values: 1,552 x / undriven sources of the gold model made free inputs: 21,489 / 21,489 outputs UNSAT.
- Pass 1 = pass 2: 39 objects (front-end models, pairings, specifications, LEC networks, residual lists) byte-identical
  and every verdict line identical (`results/lec_sa2_20261013/pass_comparison.json`, `PASS1_EQUALS_PASS2`).
- Negative controls: FSM encoding with two codes swapped fails (10 cells unproven, rc 1); the multiplier controls above;
  the first and2_1 of the r1 final netlist turned into or2_1 gives 60 SAT outputs (counterexamples on if_req_addr and
  predict_taken_d) in the N1 == final step (2026-10-14).

The smaller3400x3250 SA2 geometry (11.05 mm2) failed P2 in two independent full flows from step1, both stopped
before DRT/sign-off. All568 fresh metric fields, resolved config, N1 and first-GRT netlist/DEF/guide match.
At nom_tt_025C_1v80, setup is -0.331932 ns at10 endpoints, hold -0.0579186 ns at4 endpoints, overflow16.
The worst setup path is the half-cycle I-cache way1/bank1 SRAM dout1[25] to if_req_addr[31]. Other inherited
corner values are not fresh sign-off evidence. This paired screening failure does not establish the minimum
routable die. Receipt: `results/sa2_minimality_screen_20261011_pair.json`. The 3400x3325 die (11.305 mm2,
`sa2_corr3400x3325_..._rsztf_r1`) is CLOSED as failed: after the post-route hold ECO the incremental detailed route
stalled at 24 met1/met2 short / spacing violations (iterations 13-18; the 11.56 mm2 die clears the same step in 4)
and then crashed in OpenROAD (`checkMetalSpacing_short_skipFixed`). Not resumed (rule Q); whether it routes needs a new
full flow, planned after the SA2-own knob experiments.

### 4.3 DM, 8 KiB RAM, floorplan grid2800x2900 (signed off 2026-09-28; current golden)

Runs dm_ram8k_grid2800x2900_drtant_r1 / _r2 (log names final3_A / final3_B): identical on 302 flow metrics, final
netlist byte-identical. Workloads: the 12 self-written kernels of that time. Detailed tables: `results/FINAL_METRICS.md`
in git history (before 2026-10-07).

| item | value |
|---|---|
| sign-off gate | all 0 (antenna 0 after post-detailed-route repair; the first sign-off of 2026-09-27 had 140 nets / 159 pins) |
| setup WNS, ns | nom_tt +2.086, max_tt +1.960, max_ff +4.603; nom_ss -7.413, min_ss -6.425, max_ss -8.311 (2,511 endpoints, ss Fmax ~35-38 MHz) |
| hold WNS, ns | nom_tt +0.224; worst +0.030 (max_ff) |
| area | die 8.12 mm2, std cells 1.400 mm2 (192,005 cells), 12 macros 2.664 mm2, wire 6.60 m |
| power | vectorless nom_tt 102.05 mW (leakage 0.295); flow metric 115.5 mW (max_ff); activity-based 110.61 - 115.43 mW |
| energy per instruction | 2,379 - 3,637 pJ |
| CPI of the chip (ASIC view) | 1.2755 (FPGA view 1.2869) |
| equivalence | proved RTL == RTL+fsm == N1 == routed netlist (register-mapped LEC, twice, with negative controls) |
| remaining DRV at nom_tt | slew 757 (310 diode pins, 200 SRAM inputs, 245 std-cell pins), cap 807, fanout 2,716 (clock leaves and diode loads) |

### 4.4 1 KiB caches, 8 KiB RAM (2026-09-18)

Run dm_c1k_baseline (`asic/soc_dm_control/runs/sync_final`): die 5.22 mm2, 186,877 cells, setup nom_tt +3.41 ns, worst ss
-13.26 ns, power nom_tt 196.4 mW (vectorless). Timed with an SDC that dropped the clock uncertainty and I/O constraints;
re-timed with the corrected SDC: setup tt +3.16 ns, hold tt -0.048 / ss -0.123 / ff -0.146 ns
(`asic/evidence/sdc_recheck_1kb_research/`).

## 5. Historical 1 KiB mirror results (2026-09-16 .. 17), corrected

The first ablation (CACHE_CONFIG 3 as "DM on the ten-state controller") was in fact DM+VC4 with the lookup disabled
because the eviction copy was gated on the wrong flag. Corrected numbers (old self-written kernels, 1 KiB): controller
cost +9.35 % (reported +10.25 %), associativity -0.34 % (reported -1.16 %), SA2 wins / ties / losses 3 / 8 / 1 (reported
11 / 1 / 0), capacity sweep at 512 B -3.52 % (reported -9.57 %), line 64 B -1.39 % (reported -4.78 %). These results are
superseded by the sweep of section 2.

## 6. What is not established

- The ss corner does not close at 50 MHz on any layout (max_ss -7.4 to -10.0 ns); the rule is that CPI must not change,
  and closing ss needs a deeper pipeline.
- The OpenRAM macros have TT Liberty only; their address / write-mask inputs carry a 0.04 ns max_transition (10-90 %)
  that buffers cannot meet at the 10 um row halo; these slew violations are reported, not fixed.
- Final-STAPostPNR DRV categories now match every pin identity/limit/actual/slack/net/master/diode-load field
  across the two DM and two SA2 PD runs at all9 corners. At nom_tt_025C_1v80, DM slew142/cap298/fanout1428 and
  SA2 slew1084/cap1036/fanout383. Counts are violating pin rows, with SRAM-first, then diode-loaded-net, then
  standard-cell categories; fanout slack printed blank remains UNKNOWN_REPORTED_BLANK. No unclassified pins,
  no new STA measurements and no changed hard gate. Full category counts and units:
  `results/asic_drv_categories_20261010/paired_final_reports/report.md` and the adjacent receipt/CSVs.
- The stock OpenLane EQY step does not pass on this design. Separate register-mapped LEC results for the 8 KiB-RAM
  and 16 KiB-RAM DM netlists are historical evidence; the current 16 KiB audit keeps complete sequential closure
  open until paired reset/initial-state relations, exact-input invariants and source-model bridges are verified.
  The current gold reset base and four-model clock/edge audit have passed twice. Six AXI one-hot transition
  cofactors also pass twice without extra state ties, independently confirmed by all36,864 free-input assignments
  per pass. All fourteen ALU cofactors now pass two independent exact-CNF executions; an independent parser/CNF
  constructor and resolution verifier replay every stored proof and the actual-model negative controls.
  Evidence: `results/dm_onehot_boolean_20261010_verification.json`,
  `results/dm_axi_exhaustive_audit_20261010_receipt.json`, `results/dm_alu_onehot_cnf_20261010_verification.json`
  and `results/lec_onehot_cnf_independent_review_20261010.json`. These remain Boolean-model subproofs;
  the simultaneous current-gold invariant has since passed 286 obligations in two byte-identical executions:
  235 constants, 28 duplicate equalities and 23 legal group codes. Independent reconstruction/replay passed
  all targets and 74,938 paired resolution steps; a separate raw reset-base review uses no invariant premises
  or zero ties on unreset state. Receipts: `results/dm_joint_invariant_20261010_verification.json`,
  `results/lec_joint_invariant_independent_review_20261010.json` and
  `results/lec_joint_reset_base_independent_review_20261010.json`. The sampled reset-phase bridge has also
  passed twice: 1,716 obligations per pass, 1,696 structural and 20 exact CNF. Independent review reconstructs
  all six phases and replays 40 certificates / 74,938 resolution steps. Receipts:
  `results/dm_reset_phase_20261010_verification.json` and `results/lec_reset_phase_independent_review_20261010.json`.
  Local BHT update/read, UART baud, I-cache hot-array and main-RAM proofs establish that310 of358 classified GOLD functional
  X/Z connect lines cannot select their undefined defaults for arbitrary Boolean state/address/configuration;
  48 remain open. These are connect-line counts, not bit counts or defects. Receipts:
  `results/lec_source_definedness_20261010_verification.json` and
  `results/bht_read_default_definedness_20261010_verification.json`. An independent module-scoped raw-IR
  parser and bit-vector interpreter confirm all 256 read addresses, 1,024 update selector cases and 2,048
  actual state/taken data-cone cases, including concat order:
  `results/bht_definedness_independent_review_20261010.json`. UART has its own paired proof and separate
  parser/data-order review: `results/uart_baud_default_definedness_20261010_verification.json` and
  `results/uart_baud_definedness_independent_review_20261010.json`. The three I-cache targets pass twice with
  24 free index cases and1,224 symbolic array-data bits. Independent parser/data-order review replays all six
  actual selector/data faults: `results/icache_hot_default_definedness_20261010_verification.json` and
  `results/icache_hot_definedness_independent_review_20261010.json`. Only the unused A-defaults are closed;
  selected B-data and whole-output definedness remain outside these scoped Boolean subproofs.
  The49 main-RAM A-defaults pass392 free-bank cases and98 actual selector/data faults per pass, twice;
  398 actual B-data atoms remain arbitrary. A separate module parser/data-order implementation verifies the
  raw target cones and macro/source parameter bindings: `results/ram_bank_default_definedness_20261010_verification.json`
  and `results/ram_bank_definedness_independent_review_20261010.json`. RAM initialization is not proved.
  Asynchronous events between edges, paired GOLD/N1/final initialization, the whole-source undefined-value
  bridge and full sequential LEC remain OPEN.
  SRAM macros are black boxes
  in the mapped proof; GLS covers the exercised SRAM behavior.
- SA2 is signed off (section 4.2, 11.56 mm2; activity-based power verified in two STA executions). Its register-mapped
  LEC is complete in two identical executions with all negative controls (section 4.2), and its exact-window activity
  power is done (section 4.2).
  DM_VC4 has no signed-off layout yet: the padded 3600 x 3400 floorplan routes to 0 DRC (V2: 0 at iteration 31), but
  the post-route antenna repair (1,031 violating nets, side-area, 70 % of the pins in the logic band between the I$ and
  D$ macro columns) does not converge; run V4 (same recipe, 3800 x 3400 die) is in progress (NHAT_KY.md section 8 and
  the 2026-10-13/14 entries). Its LEC part that depends only on the synthesis is DONE (every DM_VC4 run has the same
  synthesis netlist): RTL == RTL + fsm (39,000 cells proven) == N1 (21,828 gold / 21,093 N1 flop bits, 364 constants, 18
  duplicates; 22,117 outputs, 0 SAT, the 34 multiplier-cone outputs closed by the signed33 algebra + `&cec`; one-hot 4 / 4;
  undefined values 1,796 sources, 22,117 / 22,117 UNSAT), in two complete executions object-by-object identical
  (`results/lec_vc4_20261014d/pass_comparison_goldn1.json`). DM_VC4-specific: the RTL instantiates way 1 of both DSE
  caches (8 SRAM macros) that DM_VC4 never reads and synthesis removed; their read data are free inputs of the proof
  (`asic/equiv/lec/sram_align.py`), and a control that makes one compared output depend on such read data is detected.
  N1 == final netlist waits for the layout.
- Process (rule Q of 2026-10-13: never continue from a failed step): the signed DM (r14F_A/B) and SA2 (ecomaxmin)
  layouts were produced with resumes / branches that this rule no longer allows. Each final netlist is reproduced byte
  for byte by its second run, but a single-flow re-execution is still pending (DM: owner decision, DM is locked; SA2:
  the E1 / E0 runs). Details: PROJECT_STATE.md section ASIC.
- Board: 42 of the 100 cases are measured (section 3, one physical pass, all equal to the RTL references); the other
  58 cases (10 short, 48 full-iteration) are not measured yet.
- No ASIC build of a FAST_HIT point.
- Supplemental UVM now covers DM/SA2/DM_VC4/DM_DSE with three seeds, AXI stress and two-byte serial UART RX, twice.
  Coverage is functional; no complete code coverage or SA4/FAST_HIT UVM coverage is claimed. The frozen original
  top and the aggregate output dated 2026-09-18 remain historical evidence.
- CoreMark has source-known numeric CRC checks for all92 supported sweep points, paired fresh simulations and
  independent raw verification, in addition to the canonical/current11 checks. Its window
  still includes initialization/reporting; the simulation RAM is 32 KiB and the short run is not an official score.
- The random runner now checks process status, completion and complete traces, retaining distinct raw files per
  pass. Fifty seeds were independently rerun twice; predictor OFF/ON on the same core is the tested scope.
- The frozen ACT4 harness indexes only 512 KiB. The maintained runner generates a separate 1 MiB correction and
  has rerun all 43 signatures plus an upper-half data/instruction case twice, with an alias-detecting control.
- The frozen manifest excludes SA2/VC4 ASIC tops and the DSE SRAM adapter. The separately observed input hashes in
  `results/workspace_audit/asic_input_provenance.json` supplement provenance; they do not replace historical proofs.

## Appendix: sources

- Current architecture: `results/rfbht_4kb_p{1,2}.csv`, `results/rfbhtf_4kb_p{1,2}.csv`,
  `results/coremark_rfbht_4kb_p{1,2}.csv`, `results/unified_metrics.md`.
- Historical architecture / sweep baselines: `results/upstream_r14_4kb_p{1,2}.csv`, `results/coremark_r16_4kb_p{1,2}.csv`, `results/m2/`,
  `results/irq_metrics.csv`, `results/bp0_upstream_r14_4kb_p{1,2}.csv`, `results/unified_metrics.md`.
- Current FPGA: `results/fpga_points_fpga_common_seeds_continued_20261009_p{1,2}.csv`,
  `results/fpga_common_seeds_continued_20261009_ppa.{json,md}` and the independent completion audit.
  The `rfbht` four-seed CSVs remain the reused-seed provenance.
- Historical FPGA: `results/fpga_points_r14_p{1,2}.csv`, `results/fpga_points_r15_p{1,2}.csv`, `results/le_r16_compare.log`.
- ASIC: run directories under `asic/<design>/runs/`, `results/asic_compare_dm_r14.md`, `results/gls_power_*.csv`,
  `asic/gated_pd.log`, `results/pd_run_archive/` (evidence of deleted runs).
