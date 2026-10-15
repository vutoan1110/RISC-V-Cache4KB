# Results

| item | value |
|---|---|
| Scope | research copy of the RISC-V SoC with configurable caches: 4 KiB I/D caches, 16 KiB main RAM |
| Last updated | 2026-10-15 (data as of 2026-10-15 07:45 +07) |
| Current RTL | manifest `6c4ccffd` (`results/rtl_manifest.json`, 227 files) |
| Related | history and reasons: `NHAT_KY.md`; procedures: `QUY_TRINH.md`; review items: `REVIEW_RESPONSE.md`; open work: `PROJECT_STATE.md` |

Rules for every number in this file:
1. Executed twice and compared field by field; single executions and screenings are labelled as such.
2. Every timing value names its corner; the timing corner is kept separate from the power corner.
3. Every power value names its method (Quartus default-toggle estimate, OpenSTA vectorless, or activity-based from GLS SAIF).
4. ASIC sign-off checks are listed before PPA.
5. Every result names the RTL it ran on: **[current]** = `6c4ccffd`; **[historical]** = an older RTL (R14 `3ea52396`, R15,
   R16). The `6c4ccffd` change is cycle-exact (k-induction proofs; full chain identical field by field), so historical
   numbers are expected to reproduce, but they are only evidence for `6c4ccffd` after a re-run.

## 0. Provenance summary

Source: `results/rtl_consistency_audit_20261014.md` (audit of every reported result against its RTL, 2026-10-14).

| Result group | RTL | Status on 2026-10-15 |
|---|---|---|
| Static checks, TB regression, UVM, ACT4, random differential / Spike, Embench, CoreMark (CRC, 92-point sweep, standard matrix), conflict probe | `6c4ccffd` [current] | final |
| FPGA ten common seeds x2, A1 LE breakdown, 100 board SOFs, 42 board cases | `6c4ccffd` [current] | final (board: single physical pass) |
| ASIC layouts DM / SA2 (all PD runs before 2026-10-14 21:20), GLS, activity power, LEC | snapshot `rtl_r14` = `3ea52396` [historical] | re-run on `6c4ccffd` in progress (section 5.7) |
| M1/M2 sweep, A3 cross-validation (R15/R16); A4 overlap, IRQ latency, BP on/off (R14/R15) | older RTL [historical] | re-execution x2 on `6c4ccffd` started 2026-10-15 |

## 1. Design, workloads and views

- Core: RV32I + Zmmul, five-stage in-order pipeline, 2-bit branch predictor (256-entry BHT) on, AXI4 memory port, AXI-Lite ->
  APB peripherals (UART, timer, LED/HEX/LCD), hardware cycle classifier and event counters (sysmon).
- Caches: I and D, 4 KiB each, 16 B lines, 8-entry I-cache L0. D-cache is write-through, no write-allocate.

  | CACHE_CONFIG | Name | Organisation | Controller (I$ / D$ states) | Platforms |
  |---:|---|---|---|---|
  | 0 | DM | direct-mapped | five-state DM controller (5 / 7) | FPGA, simulation, ASIC |
  | 3 | DM_DSE | direct-mapped | ten-state DSE core (10 / 11) | FPGA, simulation |
  | 1 | SA2 | two-way set-associative | DSE core (10 / 11) | FPGA, simulation, ASIC |
  | 2 | DM_VC4 | direct-mapped + 4-entry victim buffer | DSE core (10 / 11) | FPGA, simulation, ASIC |
  | 4 | SA4 | four-way, tree pseudo-LRU | N-way core | FPGA, simulation |

  `CACHE_FAST_HIT` = 1 answers a main-array hit of the DSE / N-way cores one cycle earlier (default 0). The research wrappers and
  QSFs select this 4 KiB profile; the generic HDL default remains 1 KiB.
- Main RAM: 16 KiB unified (8 KiB before 2026-09-29).
- Workloads: the 12 upstream Embench-IoT kernels that fit 16 KiB (aha-mont64, crc32, depthconv, edn, huffbench, matmult-int,
  md5sum, nettle-sha256, slre, statemate, tarfind, ud; not official Embench scores); preserved short CoreMark runs (-O2, one
  iteration, full-program `mcycle`, simulation RAM 32 KiB); the standard-duration CoreMark matrix (section 3.2). Results before
  2026-09-30 used 12 self-written kernels and are marked where they appear.
- CoreMark memory: the preserved -O2 rv32i_zmmul firmware needs .text 13,952 + .rodata 2,445 + .data 24 + .bss 2,020 + stack
  1,024 = 19,465 bytes (> 16 KiB), so `sw/coremark/coremark_link.ld` places the stack at 32 KiB. The isolated -Os APB-timer port
  needs image_end 14,032 + stack 1,024 = 15,056 bytes (static margin 1,328 bytes below 16 KiB; paired build
  `results/coremark_standard_apb_build_pair_20261011.json`), but its linker still places the stack at 32 KiB, so runtime fit in
  16 KiB is not shown. Cache parameters and RAM latency are identical across compared configurations.
- Views: **FPGA view** (RTL with FPGA memories; used for organisation comparison and the board), **ASIC view** (RTL with OpenRAM
  models; the chip's cycle counts, fewer cycles than the FPGA view because the ASIC RAM wrapper has no FPGA latency hooks),
  **gate level** (signed-off netlist; reproduces the ASIC view cycle for cycle).

## 2. Verification [current]

| Suite | Scope | Result | Date | Evidence | Not claimed |
|---|---|---|---|---|---|
| Full chain | static checks (latch sweep 33 combinations, lint), TB regression, UVM, Embench, CoreMark, random, ASIC view, ACT4 | 0 failures; regression 178/178 x2 | 2026-10-08 | `results/fullchain_rfbht.log` | - |
| UVM (supplemental) | DM / SA2 / DM_VC4 / DM_DSE x directed ISA, peripherals/IRQ, two-byte UART RX x seeds 1/2/3; AXI stress at line words 2/4/8/16 x seeds 1/2/3 | 48 cases per pass, scoreboard fields identical; wrong-byte UART controls fail in both passes | 2026-10-09 | `results/uvm_cache_uart_20261009/verification.json` | code coverage; SA4 / FAST_HIT coverage |
| ACT4 + memory window | riscv-arch-test `2e655961` (39 RV32I + 4 Zmmul) through a corrected 1 MiB adapter, plus an upper-half data/instruction test | 43/43 signatures, retirements and cycles equal the previous result; the upper-half test detects the original 512 KiB alias | 2026-10-09 | `results/architecture_window_20261009/verification.json` | privileged-ISA compliance |
| Random differential | 50 generated programs, predictor OFF vs ON on the same core | 50 paired rows and complete trace bytes match; gates on return code, PASS/termination, Error/Fatal, trace integrity | 2026-10-09 | `results/random_diff_checked_20261009/verification.json` | independent ISA oracle (see next row) |
| Spike reference | 50 seeds x 2 fresh Spike processes vs the 200 preserved RTL traces; PC, instruction, GPR writes, store address / enabled bytes / strobes | 100 native exits 0; 200/200 match; 7,105 retirements per pass; 300 wrong-trace controls detected | 2026-10-11 | `results/spike_random_reference_20261011/receipt.json` | SoC MMIO, interrupts, cache, timing |
| Embench-IoT | 12 kernels, base and FAST_HIT points | 72 + 72 and 60 + 60 rows identical | 2026-10-08 | `results/rfbht_4kb_p{1,2}.csv`, `results/rfbhtf_4kb_p{1,2}.csv` | official scores |
| CoreMark CRC (canonical) | six base + five FAST_HIT 4 KiB points, 22 fresh simulations, two compilations | CRCs seed/list/matrix/state/final = e9f5/e714/1fd7/8e3a/e714 (source references); all 40 counters equal both passes and the prior baseline; a separate DM pair matches all 43 CSV columns | 2026-10-09 | `results/coremark_crc_checked_20261009/verification.json`, `results/coremark_canonical_checked_20261009/verification.json` | official score (short full-program window, RAM 32 KiB) |
| CoreMark sweep | all 92 supported capacity / line / organisation points (49 base + 43 FAST) | 184 fresh simulations; source-known CRCs and all 40 counters equal both historical references; independent audit of 241 inputs / 379 artefacts | 2026-10-10 | `results/coremark_sweep_crc_20261010/verification.json`, `results/coremark_sweep_crc_independent_audit_20261010/receipt.json` | SA4_256B_L16 (excluded: four sets cannot index the eight-entry L0) |
| CoreMark standard duration | four configurations x performance / validation x 2 | 16/16 PASS (section 3.2) | 2026-10-11 | `results/coremark_standard_apb_matrix_20261011/receipt.json` | board measurement, EEMBC certification |

## 3. Architecture (FPGA view, 4 KiB caches, 16 KiB RAM, BP on)

### 3.1 Unified metrics

Source: `results/unified_metrics.md` (generated by `scripts/metrics/unified_table.py`).

| Metric | DM | SA2 | DM_VC4 | DM_DSE | RTL |
|---|---:|---:|---:|---:|---|
| CPI, 12 Embench-IoT kernels | 1.5136 | 1.6597 | 1.6780 | 1.6614 | [current] |
| I$ hit % | 99.70 | 99.65 | 99.72 | 99.70 | [current] |
| D$ read hit % | 99.16 | 99.59 | 99.59 | 99.16 | [current] |
| branch mispredict % | 10.57 | 10.57 | 10.57 | 10.57 | [current] |
| Embench speed / MHz, GM | 0.809 | 0.739 | 0.729 | 0.737 | [current] |
| CoreMark program `mcycle` (simulation RAM 32 KiB, CRCs verified x2) | 2,520,901 | 2,573,624 | 2,590,590 | 2,586,274 | [current] |
| IRQ entry, cycles (steady / first) | 5 / 41 | 5 / 41 | 5 / 41 | 5 / 41 | [historical] R14/R15 |
| context switch, cycles | 270 | 292 | 292 | 292 | [historical] R14/R15 |
| ASIC view vs FPGA view, `mcycle` | -4.18 % | -3.67 % | -3.23 % | - | [current] |
| BP off vs on, cycles (GM, 12 kernels) | +6.48 % | +6.60 % | +6.67 % | +6.62 % | [historical] R14 |

The differences between DM and the DSE-core configurations are mostly the DSE core's extra hit cycle, not the organisation.
With the hit latency matched (FAST_HIT), set associativity is faster than direct mapping at every capacity in the geometric mean;
DM_VC4 is slower because its eviction is serialised with the refill. Full sweep (256 B - 8 KiB, lines 8 / 16 / 32 B, 1 / 2 / 4
ways, victim depth 2 / 4 / 8; [historical] R15/R16): `REVIEW_RESPONSE.md` (M1, M2) and `results/m2/M1_M2_REPORT.md`.

### 3.2 Standard-duration CoreMark (simulation, RAM 32 KiB, 50 MHz) [current]

Completed 2026-10-11: four configurations x performance / validation x two independent executions, 16/16 PASS. The eight pairs
match all 108 scalar fields each (including 40 counters), 864 comparisons. Each pass uses separately compiled private RTL models
and independently built firmware; all native commands return 0.

| Configuration | Performance ticks | Seconds at 50 MHz | Iterations/s | CoreMark/MHz | Validation ticks |
|---|---:|---:|---:|---:|---:|
| DM | 719996901 | 14.39993802 | 76.389218 | 1.527784 | 722669045 |
| SA2 | 691866743 | 13.83733486 | 79.495077 | 1.589902 | 693576231 |
| DM_VC4 | 747676057 | 14.95352114 | 73.561270 | 1.471225 | 751155457 |
| DM_DSE | 802958516 | 16.05917032 | 68.496689 | 1.369934 | 806692095 |

- Method: FPGA simulation view, BP on, FAST_HIT = 0, 4 KiB I/D, 16 B lines, L0 = 8, RAM 32,768 bytes. Unchanged CoreMark
  algorithms, TOTAL_DATA_SIZE = 2000, single context, MEM_STATIC, HAS_FLOAT = 0, ITERATIONS = 0 calibration; every measured run
  selects 1100 iterations. Performance seeds 0/0/0x66 and validation seeds 0x3415/0x3415/0x66 pass the source-known CRCs. All final
  iterate intervals exceed 500,000,000 ticks (10 s; 13.84 - 16.13 s over performance and validation); only the upstream final iterate
  interval determines throughput.
- Timer: APB TIMER_CMP = 0xffffffff before timing (the default CMP = 40 stops COUNT). Every accepted COUNT delta equals the
  independently observed clock-edge delta and elapsed simulation time / 20 ns. Rates are computed from raw integer ticks.
- Compiler: riscv64-unknown-elf-gcc (14.2.0+19) 14.2.0, rv32i/ilp32 multilib; flags `-Os -march=rv32i_zmmul_zicsr -mabi=ilp32
  -ffreestanding -fno-builtin -msmall-data-limit=0 -ffunction-sections -fdata-sections -Wall -Wextra`, `-Dmain=coremark_main`.
  Simulator: Verilator 5.053 devel (built 20260917-1aa8791), assertions enabled.
- Different firmware, compiler options and timing window from the preserved -O2 one-iteration runs; simulation-derived, not a
  board measurement or EEMBC certification ([EEMBC rules](https://github.com/eembc/coremark/blob/main/README.md)).
- Evidence: `results/coremark_standard_apb_matrix_20261011/receipt.json`, `cases.csv` (16 cases), `performance_paired.csv`,
  `csv_export.json`; runner `scripts/verification/run_coremark_standard_apb_matrix.py`.

### 3.3 Extended conflict probe [current]

`sw_metrics/conflict/`, 2026-10-08: 35 patterns x 6 configurations x 4 KiB and 1 KiB, both runs identical, every one of the 390
windows equal to the independent cache model (`results/conflict_probe.csv`). Line (s, k) at 0x0C00 + k x span + s x 16 maps to one
set per s in every organisation. D-cache hit %:

| Pattern (4 KiB unless noted) | DM | DM_DSE | SA2 | SA4 | DM_VC4 |
|---|---:|---:|---:|---:|---:|
| cyclic, 1 set, N = 2 | 98.4 | 0 | 100 | 100 | 100 |
| cyclic, 1 set, N = 3 / 4 | 0 / 0 | 0 / 0 | 0 / 0 | 100 / 100 | 100 / 100 |
| cyclic, N = 2 per set, 4 / 5 / 32 sets | 0 | 0 | 100 | 100 | 100 / 50 / 50 |
| cyclic, N = 3 per set, 2 / 3 sets | 0 | 0 | 0 | 100 | 100 / 33.3 |
| random, N = 2 per set, 5 / 8 / 16 sets | 52 / 48 / 53 | 51 / 48 / 53 | 99 / 100 / 100 | 100 | 90 / 76 / 65 |
| 1 KiB, cyclic, 1 set, N = 5 / 6 / 7 | 0 | 0 | 0 | 0.3 / 0 / 0 | 100 / 66.7 / 0 |
| 1 KiB, random, 1 set, N = 8 | 24.4 | 9.6 | 24.4 | 49.0 | 59.0 |

- The victim buffer is shared: DM_VC4 holds two lines per set in at most four sets; SA2 in every set.
- The collapse of a cyclic sweep longer than the capacity (published Table 6, N = 7) is FIFO / round-robin replacement meeting a
  cyclic order: with the same lines in random order DM_VC4 keeps 59 % at N = 8 (1 KiB).
- The DM D-cache's two-entry L0 holds N = 2 lines of one set (98.4 %); DM_DSE, without L0, does not.
- Write miss neither fills nor evicts. A victim hit costs about 19-22 cycles per probe access, a main hit 10-14, a miss 26-30.

## 4. FPGA (Cyclone IV E EP4CE115, Quartus Prime Lite 20.1, 50 MHz)

### 4.1 Current RTL, ten common seeds [current]

RAM 16 KiB, register file and BHT in M9K (cycle-exact). Seeds 1..10 per point, two independent passes, all 40 paired rows equal on
115 hardware fields (runtime excluded). Seeds 1/3/4 retain their independently measured rfbht provenance; seeds 5..10 and the
common board seed 2 were refitted twice. Timing corner: Slow 1200 mV 85 C. Power: Quartus default toggle-rate estimate (12.5 %),
Typical VCCINT 1.20 V, ambient 25 C, low confidence.

| Point | LE [min, max] | Registers | M9K | Fmax Slow 85C, MHz [min, max] | Setup slack Slow 85C, ns (min) | Total power, mW [min, max] |
|---|---|---:|---:|---|---:|---|
| dm_4kb | 12,800 - 12,842 | 7,198 | 30 | 52.27 - 56.18 | +0.870 | 251.64 - 258.93 |
| dse_4kb | 14,302 - 14,364 | 7,480 | 30 | 51.02 - 55.21 | +0.399 | 262.46 - 270.41 |
| sa2_4kb | 16,670 - 16,739 | 7,877 | 40 | 51.96 - 54.54 | +0.754 | 278.61 - 283.04 |
| vc4_4kb | 17,096 - 17,148 | 9,265 | 30 | 51.52 - 54.40 | +0.591 | 276.31 - 282.35 |

Means (sample SD), order DM / SA2 / DM_VC4 / DM_DSE: LE 12,816.00 (12.37) / 16,699.90 (22.60) / 17,124.00 (15.76) / 14,332.60
(20.41); Fmax 54.73 (1.03) / 52.92 (0.83) / 53.28 (1.17) / 53.61 (1.38) MHz; power 255.11 (1.80) / 281.01 (1.24) / 279.52 (1.72) /
265.97 (2.62) mW. Compare organisations within the same seed; no per-configuration best seed is selected. Sources:
`results/fpga_points_fpga_common_seeds_continued_20261009_p{1,2}.csv`, `results/fpga_common_seeds_continued_20261009_ppa.{json,md}`.

### 4.2 Effect of moving the register file and BHT into M9K (2026-10-08)

| Point | R14..R16, flip-flop arrays [historical] | `6c4ccffd` | Saving |
|---|---|---|---|
| dm_4kb | 15,440 - 15,546 LE / 8,430 registers / 26 M9K | 12,800 - 12,842 LE / 7,198 / 30 | 2,630 LE |
| dse_4kb | 16,989 - 17,063 LE | 14,302 - 14,364 LE | |
| sa2_4kb | 19,360 - 19,474 LE | 16,670 - 16,739 LE | |
| vc4_4kb | 19,810 - 19,875 LE | 17,096 - 17,148 LE | 2,680 LE |

Saving 13.5 - 17.0 %. Per module (`results/a1_le_breakdown_rfbht.md`): register file 1,386 -> 52 LE, BHT 962 -> 636 LE (incl.
valid bits), CPU core 6,451 -> 3,818 LE; CPU-core block power estimate 39.68 -> 28.08 mW (DM, seed 2). Every simulation is
identical to R16. ASIC boundary: the `6c4ccffd` ASIC-view synthesis netlist is byte-identical to the R16 synthesis netlist (sha256
`da06d38f`); it is NOT the synthesis netlist of the historical R14 PD runs (sha256 `fc555d6b`), so no R14 layout is a `6c4ccffd`
layout. Historical sources: `results/fpga_points_r14_p{1,2}.csv`.

### 4.3 Other FPGA points [historical, not refitted after the M9K change]

- Seed 2 (`results/fpga_points_r15_p{1,2}.csv`): sa4_4kb 21,821 LE (Fmax 50.95 MHz); 8 KiB caches: DM 16,812, DM_DSE 19,364, SA2
  23,629, DM_VC4 22,262, SA4 28,891 LE; every point closes 50 MHz.
- FAST_HIT 0 -> 1 (seed 2, `results/le_r16_compare.log`): SA2 +456 LE, Fmax 53.71 -> 51.65 MHz; DM_VC4 +115 LE; DM_DSE +345 LE;
  SA4 +881 LE; worst setup slack +0.639 ns (SA2).
- 20,000 LE is a soft target; SA4 and the 8 KiB set-associative / victim points exceed it.

### 4.4 Board (DE2-115) [current]

- **Preparation (2026-10-09).** 100 SOFs from common seed 2 under `output_files_board_matrix_6c4ccffd_seed2/`; INDEX.csv binds
  each SOF hash to the expected MCYCLE / MINSTRET of the simulation reference (100 paired rows, every counter equal to R14 on
  `6c4ccffd`); canonical MIFs and assemblies restored. Receipt: `results/fpga_common_seeds_continued_20261009_board_audit.json`.
- **Session 2026-10-13.** Scope fixed by the owner at ONE physical pass of the 100 cases (4 ramsweep + 48 short Embench + 48
  full-iteration Embench). Measured: 42 cases = 4 ramsweep + 9 complete kernels x 4 configurations (aha-mont64, crc32, depthconv,
  edn, huffbench, matmult-int, md5sum, nettle-sha256, slre) + statemate on DM and SA2. Every complete UART log matches BOTH RTL
  reference passes on all 25 counters plus D_ACCESS; VERIFY_CODE is identical across the four configurations of each kernel; the
  HEX display equals MCYCLE wherever it was read back (41 display read-backs confirmed). Independent re-check 42/42, 0 problems
  (`results/board_20261013_independent_check/`); session evidence `results/board_20261013/`.
- **Remaining: 58 cases** (10 short: statemate DM_VC4 / DM_DSE, tarfind and ud on all four; 48 full-iteration). Board numbers are
  single physical executions.

## 5. ASIC (sky130A, sky130_fd_sc_hd, OpenLane 2.3.10 local copy, 20 ns clock)

**Sign-off gate:** route / Magic / KLayout DRC 0, LVS 0, XOR 0, illegal overlap 0, antenna 0, setup >= 0 at every tt and ff corner,
hold >= 0 at all nine corners. The ss corner (100 C, 1.60 V) is reported, not gated. The OpenRAM macros have TT Liberty only, so
ss / ff numbers are optimistic on paths through the SRAMs. Flow `power__total` is the max_ff corner; values below name their
corner and method.

**Provenance:** every layout in sections 5.1 - 5.6 was built from snapshot `rtl_r14` (`3ea52396`) and is [historical]. PD on
`6c4ccffd` started 2026-10-14 (section 5.7).

### 5.1 DM, 16 KiB RAM, floorplan grid3665x2900 (signed off 2026-10-02) [historical]

Runs `dm_grid3665x2900_r1` / `_r2` (log names r14F_A / r14F_B): identical on 319 flow metrics; final netlists byte-identical
(sha256 `83f38f7e...`). Source: `results/asic_compare_dm_r14.md`.

| Item | Value |
|---|---|
| sign-off gate | Magic DRC 0, KLayout DRC 0, route DRC 0, LVS 0, XOR 0, overlap 0, antenna 0, hold violations 0 |
| setup WNS, ns | nom_tt +1.894, max_tt +1.708; nom_ff +4.611, min_ff +4.811; nom_ss -6.897, max_ss -7.365 (TNS -11,439) |
| hold WNS, ns | nom_tt +0.186; worst +0.020 (max_ff_n40C_1v95) |
| area | die 10.63 mm2, std cells 1.3696 mm2 (197,878 cells), 16 SRAM macros 3.80 mm2, wire 6.585 m |
| power, vectorless (OpenSTA default activity, nom_tt) | 109.15 mW |
| power, activity-based, exact window (GLS -> SAIF -> OpenSTA, nom_tt_025C_1v80, RCX) | 114.81 - 122.99 mW (mean 119.45); dynamic 114.37 - 122.55 (mean 119.02); leakage 0.437 mW; unknown activity 5.38 % |
| energy per instruction (ASIC-view cycles) | 2,612 - 6,547 pJ; GM 3,608 pJ |
| gate-level simulation | 12/12 kernels, `mcycle` = ASIC-view RTL |
| equivalence | register-mapped LEC RTL == RTL + fsm == N1 == both final netlists, two executions, with closed premises (below); gold = `rtl_r14` |

Power evidence (all on the R14 layout):
- First activity capture, two independent OpenSTA executions from the same preserved SAIF (2026-10-10): every value of all six power
  groups and all activity-origin counts / shares match; both vectorless runs reproduce the flow. Receipts:
  `results/gls_power_r14F_A_power_verification.json`, `results/dm_activity_power_second_pass_20261010.json`; paired CSVs
  `results/gls_power_r14F_A_power_p{1,2}.csv` (second raw reports end in `.power.p2.rpt`). STAPostPNR is step 58 (step 57 is RCX).
- Capture-window audit (2026-10-10): all 24 preserved DM / SA2 SAIFs span `(mcycle+1) x 20 ns`, one period longer than the measured
  region; legacy columns `win_t0_ns` / `win_t1_ns` contain picoseconds. Old inputs are unchanged. Evidence:
  `results/embench_gls_evidence_audit_20261010/{receipt.json,gls_windows.csv}`.
- The replacement passive GLS observer is proved on the exact signed DM and SA2 netlists: 65 obligations per design (freeze
  predicate, all 32 MCYCLE increment bits and their D consumers), two executions; a separate raw-netlist / PDK implementation
  replayed 252 paired CNF certificates / 340,338 resolution steps, eight structural roots and 12 wrong-observer witnesses
  (`results/mapped_counter_freeze_checked_20261010/{verification.json,independent_review.json}`). Local observer contract only.
- Exact-window recapture (2026-10-13): two fresh GLS captures (each SAIF exactly `mcycle x 20 ns`, identical except DATE), then two
  OpenSTA passes per kernel (26 executions); pass 1 = pass 2 on every field; every kernel within 0.005 mW of the preserved-window
  value, so the extra 20 ns had no material effect. Receipt: `results/activity_power_exact_dm_20261013/receipt.json`
  (`VERIFIED_TWO_GLS_AND_TWO_STA_ACTIVITY_POWER_PASSES`), paired CSVs `activity_power_p{1,2}.csv`.

Equivalence evidence:
- The stock OpenLane `Yosys.EQY` step does not complete on this design (tool limits: FSM re-encoding, name matching, one partition
  > 23 GB). This is a tool failure, not a verdict. Equivalence comes from the custom register-mapped chain (`asic/equiv/lec/`,
  `run_lec_r14*.ps1`): 20,124 / 20,096 mapped outputs, multiplier closed by algebra (signed33 x signed33 mod 2^64) + `&cec`, negative
  control (and2 -> or2) detected with 184 SAT outputs.
- Premises closed 2026-10-13/14 (each twice, each with a failing negative control):
  - asynchronous reset between clock edges: all 19,087 final flop bits of r14F_A and of r14F_B pair by name with gold; 7,519 have an
    asynchronous reset with the same root (`reset_sync_q`, active low) and value on both sides, 11,568 have none; 0 mismatches
    (`asic/equiv/lec/arst_audit.py`, `results/lec_arst_audit_20261013/`);
  - undefined values: all 1,401 x / undriven sources of the gold model made free inputs: 20,124 / 20,124 outputs UNSAT (`run_xsens.ps1`);
    this supersedes the per-line closure of the 358 X/Z connect lines (310 closed, 48 open as of 2026-10-10);
  - one-hot invariant of the four re-encoded FSMs re-proved on the exact gold source (`results/lec_dm_inv_20261013{,_p2}/`);
  - clock / edge: positive-edge scalar `clk` for every flop in all four flat models (`results/dm_lec_clock_audit_20261010/receipt.json`);
    gold reset base (235 constants, 28 duplicates, 4 FSM groups; `results/dm_reset_base_structural_20261010_p{1,2}.json`).
- Outside the claim: sequential equivalence without the register mapping (not feasible at this size with open-source engines) and
  SRAM macro contents (black boxes; covered by GLS). The proof binds `rtl_r14` gold to the R14 layout, not to a `6c4ccffd` layout.

### 5.2 SA2, 16 KiB RAM, corridor floorplan corr3400x3400_f220 (signed off 2026-10-09) [historical]

Knobs (each measured, `NHAT_KY.md` section 8.2): post-GRT cap margin 20, `MAX_FANOUT_CONSTRAINT` 16, cell padding one site per
side, timing-driven global placement, clock trunks on met3-met5, resizer on tt / ff only, post-route hold ECO in two passes (max_*
extraction, then min_*). Runs `sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1` / `_r2` (r2 a full flow from step
1, branched after its first ECO like r1): identical on 319 flow metrics, final netlist and DEF byte-identical, SPEF identical except
its date line. Source: `results/asic_compare_dm_sa2_20261009.md`.

| Item | Value |
|---|---|
| sign-off gate | Magic DRC 0, KLayout DRC 0, route DRC 0, LVS 0, XOR 0, overlap 0, antenna 0, hold violations 0 |
| setup WNS, ns | nom_tt +1.118, max_tt +0.838, min_tt +1.331; nom_ff +4.056, min_ff +4.262, max_ff +3.803; nom_ss -7.304, max_ss -7.917 (TNS -13,417) |
| hold WNS, ns | nom_tt +0.152; worst +0.020 (min_ff, max_ff) |
| area | die 11.56 mm2, std cells 1.4711 mm2 (215,979 cells), 16 SRAM macros 3.80 mm2, wire 9.274 m |
| buffers | timing repair 15,240 (DM 24,448); clock buffers 4,519, clock inverters 824; hold buffers 139 + 11 (two ECO passes); macro pin buffers 775 |
| power, vectorless (nom_tt) | 121.99 mW (DM 109.15 mW) |
| power, activity-based, exact window (nom_tt_025C_1v80, RCX) | 127.45 - 131.75 mW (mean 129.64); dynamic 127.02 - 131.31 (mean 129.21); leakage 0.437 mW; unknown activity 4.42 % of output pins |
| energy per instruction | 2,848 - 7,354 pJ (GM 4,317), ASIC-view cycles |
| gate-level simulation | 12/12 kernels, `mcycle` = ASIC-view RTL = independent TB cycle count |
| DRVs left (reported, not gated) | nom_tt: max slew 1,084, max cap 1,036; worst corner: slew 7,885, cap 1,827, fanout 383 |
| equivalence | register-mapped LEC complete, two executions object-by-object identical; gold = `rtl_r14` |

- **Activity power.** First evaluation 2026-10-09: two independent OpenSTA executions from the same SAIF; all six power groups and
  activity-origin fields match; vectorless reproduces the flow (`results/gls_power_sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1_power_p{1,2}.csv`
  and the `_power_verification.json` of the same tag). Exact-window recapture 2026-10-14 by the DM method
  (`results/gls_exact_sa2_full_p{1,2}_20261014`, pair `results/gls_exact_sa2_full_pair_20261014.json`, 26 STA executions): pass 1 =
  pass 2 on every field; within 0.005 mW of the preserved values. Receipt `results/activity_power_exact_sa2_20261014/receipt.json`.
  These receipts bind the old signed SA2 layout (R14). DM vs SA2 (exact window): mean 119.45 vs 129.64 mW (+8.5 %), EPI GM 3,608 vs
  4,317 pJ (+19.7 %, which also carries SA2's extra ST_LOOKUP cycles).
- **Equivalence (2026-10-13/14)** by the DM method (`asic/equiv/lec/run_lec_sa2.ps1`), two independent executions, each with its own
  byte-exact synthesis replay (`results/lec_sa2_20261013/p1`, `p2b`):
  - RTL == RTL + fsm: 38,300 cells proven, 0 unproven;
  - RTL + fsm == N1: 20,803 gold flop bits, 20,465 paired; of 338 gold-only bits 231 proved constant, 18 duplicates, 89 free;
    21,489 outputs; 34 left by per-output SAT (multiplier fan-out) closed by the signed33 algebra (unsigned and partial-product
    mutation controls fail) and `&cec`; one-hot 4/4 UNSAT;
  - N1 == final netlist of `_r1` and `_r2`: 20,462 pairs, 21,471 outputs each, 0 SAT, 32 closed by `&cec`;
  - undefined values: 1,552 sources free: 21,489 / 21,489 UNSAT;
  - pass 1 = pass 2: 39 objects byte-identical, every verdict identical (`results/lec_sa2_20261013/pass_comparison.json`,
    `PASS1_EQUALS_PASS2`);
  - negative controls: FSM codes swapped -> 10 cells unproven; first and2_1 of the r1 netlist turned into or2_1 -> 60 SAT outputs.
- **Minimality (not established).** 10.54 mm2 (3400 x 3100) routes but fails max_tt -0.573 ns on the I$ way-1 half-cycle read path.
  11.05 mm2 (3400 x 3250) failed P2 in two independent full flows: nom_tt_025C_1v80 setup -0.331932 ns (10 endpoints), hold
  -0.0579186 ns (4), overflow 16; worst path I$ way1/bank1 `dout1[25]` -> `if_req_addr[31]`; 568 metric fields match
  (`results/sa2_minimality_screen_20261011_pair.json`). 11.305 mm2 (3400 x 3325) passed P2 once, routed to DRC 0, then after the
  post-route hold ECO the incremental route stalled at 24 met1/met2 short / spacing violations (iterations 13-18; 11.56 mm2 clears
  the same step in 4) and crashed in OpenROAD (`checkMetalSpacing_short_skipFixed`); closed as FAILED 2026-10-13. Whether 11.305
  routes needs a new full flow.

### 5.3 DM_VC4 [not signed off]

- The padded 3600 x 3400 floorplan (12.24 mm2) routes to 0 DRC (V2: 0 at iteration 31), but the post-route antenna repair does not
  converge: 1,031 violating nets, side-area, 70 % of the pins in the logic band between the I$ and D$ macro columns (both caches'
  read-data pins face the 220 um channel). GRT antenna margin, a 3800 um die (V4: 821 nets after GRT repair, stopped by the owner
  2026-10-14 14:01 UTC) and a 500 um maximum wire length (V5) did not reduce the violations. History: `NHAT_KY.md` section 8.3.
- Owner decision 2026-10-14: DM_VC4 deferred; to be rebuilt from `6c4ccffd` with its own floorplan (read pins away from the centre).
- LEC, synthesis-dependent part DONE (every DM_VC4 run has the same synthesis netlist; gold `rtl_r14`): RTL == RTL + fsm (39,000
  cells proven) == N1 (21,828 gold / 21,093 N1 flop bits, 364 constants, 18 duplicates; 22,117 outputs, 0 SAT; 34 multiplier-cone
  outputs closed by algebra + `&cec`; one-hot 4/4; undefined values 1,796 sources, 22,117 / 22,117 UNSAT), two complete executions
  object-by-object identical (`results/lec_vc4_20261014d/pass_comparison_goldn1.json`). The RTL instantiates way 1 of both DSE caches
  (8 SRAM macros) that DM_VC4 never reads and synthesis removes; their read data are free inputs (`asic/equiv/lec/sram_align.py`),
  and a control making one compared output depend on such read data is detected. N1 == final netlist waits for a layout.

### 5.4 Unified corridor floorplans (2026-10-06 .. 2026-10-09) [historical]

Same die and macro coordinates for all three organisations; first executions. Screening: `asic/fp_explore/fp_summary_20261006.md`.

| | corr3400x3325_f220 (11.305 mm2) | corr3400x3400_f220 (11.56 mm2) |
|---|---|---|
| DM | signed off clean | signed off clean |
| SA2 | detailed routing stalled at 173 violations (iteration 30) | signed off clean 2026-10-09 with its own knobs (5.2) |
| DM_VC4 | re-route in antenna repair: 19,114 overflow | clock-tree detours on the early global routes; the 12.24 mm2 candidate later failed DRT / antenna convergence (5.3) |

DM on the corridor floorplans (`dm_corr3400x3325_f220_r1` / `dm_corr3400x3400_f220_r1`, single executions; run directories deleted
2026-10-15 after archiving):

| Item | 11.305 mm2 | 11.56 mm2 |
|---|---|---|
| sign-off gate | all 0 | all 0 |
| setup WNS, ns | nom_tt +1.818, max_tt +1.595, worst ff +3.851; nom_ss -8.292, max_ss -8.754 | nom_tt +1.755, max_tt +1.481, worst ff +3.695; nom_ss -9.517, max_ss -10.043 |
| hold WNS, ns (worst corner) | +0.002 (min_ff) | +0.018 (nom_ff) |
| std cells | 1.3736 mm2, 204,622 cells | 1.3760 mm2, 208,101 cells |
| wire | 6.68 m | 6.71 m |
| power | GLS / SAIF captured; paired STA not established | not established |

### 5.5 DM, 8 KiB RAM, floorplan grid2800x2900 (signed off 2026-09-28; current golden) [historical, RTL 8b163675]

Runs `dm_ram8k_grid2800x2900_drtant_r1` / `_r2` (log names final3_A / final3_B): identical on 302 flow metrics, final netlist
byte-identical. Workloads: the 12 self-written kernels of that time. Detailed tables: `results/FINAL_METRICS.md` in git history
(before 2026-10-07).

| Item | Value |
|---|---|
| sign-off gate | all 0 (antenna 0 after post-detailed-route repair; the first sign-off of 2026-09-27 had 140 nets / 159 pins) |
| setup WNS, ns | nom_tt +2.086, max_tt +1.960, max_ff +4.603; nom_ss -7.413, min_ss -6.425, max_ss -8.311 (2,511 endpoints, ss Fmax ~35-38 MHz) |
| hold WNS, ns | nom_tt +0.224; worst +0.030 (max_ff) |
| area | die 8.12 mm2, std cells 1.400 mm2 (192,005 cells), 12 macros 2.664 mm2, wire 6.60 m |
| power | vectorless nom_tt 102.05 mW (leakage 0.295); flow metric 115.5 mW (max_ff); activity-based 110.61 - 115.43 mW |
| energy per instruction | 2,379 - 3,637 pJ |
| CPI of the chip (ASIC view) | 1.2755 (FPGA view 1.2869) |
| equivalence | register-mapped LEC RTL == RTL + fsm == N1 == routed netlist, twice, with negative controls |
| remaining DRV at nom_tt | slew 757 (310 diode pins, 200 SRAM inputs, 245 std-cell pins), cap 807, fanout 2,716 (clock leaves and diode loads) |

### 5.6 1 KiB caches, 8 KiB RAM (2026-09-18) [historical]

Run `dm_c1k_baseline` (`asic/soc_dm_control/runs/sync_final`): die 5.22 mm2, 186,877 cells, setup nom_tt +3.41 ns, worst ss -13.26
ns, power nom_tt 196.4 mW (vectorless). Timed with an SDC that dropped the clock uncertainty and I/O constraints; re-timed with the
corrected SDC: setup tt +3.16 ns, hold tt -0.048 / ss -0.123 / ff -0.146 ns (`asic/evidence/sdc_recheck_1kb_research/`).

### 5.7 PD on `6c4ccffd` (in progress, 2026-10-15)

PD reads snapshot `asic/snapshots/rtl_rfbht` since 2026-10-14 21:20 (owner decision). Snapshot size: 44 files on 2026-10-14
(checked byte-identical to the live tree twice), 47 files after adding the three frozen SA2 / DM_VC4 ASIC wrappers that were
outside the RTL manifest (SHA-256 in its `SNAPSHOT_ID.txt`).

| Run | Status |
|---|---|
| `dm_grid3665x2900_rtl6c4c_r1` (signed DM recipe, only `VERILOG_FILES` changed) | p1 FAIL 2026-10-14: STAMidPNR-2 setup nom_tt +0.307 ns < `P1_MIN_SETUP` 0.5; 71,006 cells (R14: 70,441); worst post-CTS path is the half-cycle RAM bank[3] -> D$ data-bank refill |
| `sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rtl6c4c_r1` | step 16 ManualMacroPlacement FAIL: from R15/R16 the cache macros are `u_soc.u_{i,d}cache.genblk1.g_dse.*`; fixed by `macro_placement_u2fg_rtl6c4c.cfg` (8 names, same coordinates) |
| `dm_grid3665x2900_rtl6c4c_r2`, `sa2_..._rsztf_eco2_rtl6c4c_r2` | running since 2026-10-15 00:18 UTC (`asic/sequence_heavy_20261015g.sh`); DM declares `P1_MIN_SETUP=0 P2_MIN_SETUP=0` at launch, sign-off gate unchanged |

Acceptance on `6c4ccffd` = sign-off gate + one complete clean flow from step 1 (QUY_TRINH rule of 2026-10-14), then GLS,
exact-window power and LEC with gold from `rtl_rfbht`.

## 6. Historical 1 KiB mirror results (2026-09-16 .. 17), corrected

The first ablation (CACHE_CONFIG 3 as "DM on the ten-state controller") was in fact DM+VC4 with the lookup disabled, because the
eviction copy was gated on the wrong flag. Corrected numbers (old self-written kernels, 1 KiB): controller cost +9.35 % (reported
+10.25 %), associativity -0.34 % (reported -1.16 %), SA2 wins / ties / losses 3 / 8 / 1 (reported 11 / 1 / 0), capacity sweep at
512 B -3.52 % (reported -9.57 %), line 64 B -1.39 % (reported -4.78 %). Superseded by the sweep of section 3.1.

## 7. What is not established

| Area | Gap | Reference |
|---|---|---|
| Timing | the ss corner does not close at 50 MHz on any layout (max_ss -7.4 to -10.0 ns); closing it needs a deeper pipeline, which would change CPI | section 5 |
| SRAM Liberty | OpenRAM macros have TT Liberty only; `addr0` / `addr1` / `wmask0` carry a 0.04 ns max_transition (10-90 %) that buffers cannot meet at the 10 um row halo; reported, not fixed | `NHAT_KY.md` section 9 |
| DRV | reported by category, not gated: nom_tt_025C_1v80 DM slew 142 / cap 298 / fanout 1,428, SA2 slew 1,084 / cap 1,036 / fanout 383 (violating pin rows; SRAM, then diode-loaded nets, then std cells; blank fanout slack kept as UNKNOWN_REPORTED_BLANK); identical across the two runs of each design at all nine corners | `results/asic_drv_categories_20261010/paired_final_reports/report.md` |
| PD on current RTL | no `6c4ccffd` layout is signed off yet; all signed layouts are R14 | section 5.7 |
| DM_VC4 | no signed-off layout; no activity power; LEC N1 == final pending | section 5.3 |
| SA2 minimality | the next smaller die has not been shown to fail with the same recipe (11.305 mm2 unresolved) | section 5.2 |
| Process (rule of 2026-10-14) | signed DM (r14F_A/B: resumed after a session end) and SA2 (ecomaxmin: branched after step 47, CONTINUE past p2, resumed at step 52) were produced with resumes / branches; each final netlist is reproduced byte for byte by its second run, but acceptance now requires one complete clean flow from step 1 per design (the 2026-10-13 "never resume" rule was superseded on 2026-10-14) | `PROJECT_STATE.md` section 3 |
| LEC | stock EQY never completes (tool limits, not a verdict); custom register-mapped proofs are complete for DM and SA2 against `rtl_r14` gold, not against a `6c4ccffd` layout; sequential equivalence without register mapping and SRAM contents are outside the claim | sections 5.1, 5.2 |
| Board | 58 of 100 cases not measured; single physical pass | section 4.4 |
| FAST_HIT | no ASIC build of a FAST_HIT point | - |
| Coverage | UVM coverage is functional; no complete code coverage or SA4 / FAST_HIT UVM coverage; the frozen original UVM top and the aggregate output of 2026-09-18 are historical | section 2 |
| CoreMark | short runs include initialization / reporting and use 32 KiB simulation RAM; the standard matrix is simulation; no official / board score | sections 2, 3.2 |
| Random / ACT4 | random differential compares predictor OFF/ON on one core (Spike covers the generated RV32I/Zmmul subset only); the frozen ACT4 harness indexes only 512 KiB (the maintained runner generates a separate 1 MiB correction) | section 2 |
| Provenance | the frozen manifest excludes the SA2 / DM_VC4 ASIC tops and the DSE SRAM adapter; their hashes are in `results/workspace_audit/asic_input_provenance.json` and, since 2026-10-14, in snapshot `rtl_rfbht` | section 5.7 |

DM LEC sub-proofs of 2026-10-10 (Boolean-model, two executions each, independently reviewed; superseded as premises by the
2026-10-13/14 audits in section 5.1): AXI one-hot cofactors (`results/dm_onehot_boolean_20261010_verification.json`,
`results/dm_axi_exhaustive_audit_20261010_receipt.json`), ALU cofactors (`results/dm_alu_onehot_cnf_20261010_verification.json`,
`results/lec_onehot_cnf_independent_review_20261010.json`), joint invariant 286 obligations
(`results/dm_joint_invariant_20261010_verification.json`, `results/lec_joint_invariant_independent_review_20261010.json`,
`results/lec_joint_reset_base_independent_review_20261010.json`), reset phase 1,716 obligations
(`results/dm_reset_phase_20261010_verification.json`, `results/lec_reset_phase_independent_review_20261010.json`), local
definedness of BHT / UART baud / I$ hot array / main RAM (`results/lec_source_definedness_20261010_verification.json`,
`results/bht_read_default_definedness_20261010_verification.json`, `results/bht_definedness_independent_review_20261010.json`,
`results/uart_baud_default_definedness_20261010_verification.json`, `results/uart_baud_definedness_independent_review_20261010.json`,
`results/icache_hot_default_definedness_20261010_verification.json`, `results/icache_hot_definedness_independent_review_20261010.json`,
`results/ram_bank_default_definedness_20261010_verification.json`, `results/ram_bank_definedness_independent_review_20261010.json`).
Details: `NHAT_KY.md` section 4.3.

## Appendix: sources

- Current architecture: `results/rfbht_4kb_p{1,2}.csv`, `results/rfbhtf_4kb_p{1,2}.csv`, `results/coremark_rfbht_4kb_p{1,2}.csv`,
  `results/unified_metrics.md`.
- Historical architecture / sweep baselines: `results/upstream_r14_4kb_p{1,2}.csv`, `results/coremark_r16_4kb_p{1,2}.csv`,
  `results/m2/`, `results/irq_metrics.csv`, `results/bp0_upstream_r14_4kb_p{1,2}.csv`.
- Current FPGA: `results/fpga_points_fpga_common_seeds_continued_20261009_p{1,2}.csv`,
  `results/fpga_common_seeds_continued_20261009_ppa.{json,md}` and the independent completion audit; the `rfbht` four-seed CSVs
  remain the reused-seed provenance.
- Historical FPGA: `results/fpga_points_r14_p{1,2}.csv`, `results/fpga_points_r15_p{1,2}.csv`, `results/le_r16_compare.log`.
- ASIC: run directories under `asic/<design>/runs/`, `results/asic_compare_dm_r14.md`, `results/asic_ppa_verified_subset_20261010.md`,
  `results/gls_power_*.csv`, `asic/gated_pd.log`, `results/pd_run_archive/` (evidence of deleted runs).

## Revision history

| Date | Change |
|---|---|
| 2026-09-28 | DM 8 KiB-RAM sign-off results (then `results/FINAL_METRICS.md`) |
| 2026-09-30 | file created with the final3 baseline (commit `0bf22b7`) |
| 2026-10-02 | DM 16 KiB-RAM sign-off (r14F_A/B) |
| 2026-10-07 | English results file, history moved to NHAT_KY (commit `507c3fb`) |
| 2026-10-08 | RF/BHT in M9K; extended conflict probe |
| 2026-10-09 | SA2 sign-off and activity power; UVM / ACT4 window / random hardening; FPGA ten common seeds; board SOFs |
| 2026-10-10 | CoreMark 92-point sweep; DRV categories; DM second STA; capture-window audit; LEC scope narrowed |
| 2026-10-11 | Spike reference; standard-duration CoreMark |
| 2026-10-13 | board session (42 cases); DM exact-window power; LEC premises (asynchronous reset, clock) |
| 2026-10-14 | SA2 LEC complete; SA2 exact-window power; DM_VC4 LEC synthesis part; RTL consistency audit; PD moves to `6c4ccffd` |
| 2026-10-15 07:46 | state of 2026-10-15 (commit `2d4202d`) |
| 2026-10-15 | restructured: provenance table, verification table, [current]/[historical] labels, board count corrected (9 complete kernels, not 10), R16 / R14 synthesis boundary, SA2 exact-window power marked done on the R14 layout, snapshot 44 -> 47 files, process rule of 2026-10-14, EQY vs custom LEC distinction |
| 2026-10-15 | references point to the single topic-structured `NHAT_KY.md` |
