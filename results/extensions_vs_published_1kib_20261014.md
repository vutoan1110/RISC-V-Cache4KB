# Extensions of the research copy over the published 1 KiB design

Status 2026-10-14. Baseline: the published repository (`E:\Projects\RISCV-AHB-APB-UART`, README and `danh_gia.txt`):
five-stage RV32I + Zmmul SoC, DM / SA2 / DM_VC4 caches of 1 KiB, 8 KiB main RAM, 12 kernels (10 self-written
"Embench-style" + md5sum and depthconv from Embench-IoT), Quartus fits at four seeds (DM 15,188, SA2 18,168,
DM_VC4 19,882 LE at seed 2, about 52 MHz), board matrix of 36 SOFs with no archived logs, ASIC flow in progress and
not published. Everything below is new in the research copy (`E:\Projects\RISCV-research`). Numbers are the
double-executed values of `RESULTS.md`; evidence paths are given per item. Items marked OPEN are not finished.

## 1. Design (RTL)

| # | extension | what it is / why | evidence |
|---|---|---|---|
| 1 | 4 KiB I and D caches | the research profile (wrappers / QSFs); the generic HDL default stays 1 KiB | `RESULTS.md` 1 |
| 2 | Main RAM 8 -> 16 KiB | needed to run the upstream Embench-IoT kernels (the RAM, not the cache, limited the runnable set) | `RAM16K_CHANGES.md`, `NHAT_KY.md` 2026-09-29 |
| 3 | DM_DSE configuration (CACHE_CONFIG 3) | the ten-state DSE controller used as a plain direct-mapped cache: separates controller cost from organisation (review M1) | `REVIEW_RESPONSE.md` M1 |
| 4 | SA4 (four-way, N-way core, tree PLRU) | FPGA / simulation point of the design-space sweep | `RESULTS.md` 3 |
| 5 | `CACHE_FAST_HIT` parameter | DSE / N-way main-array hit answered in ST_LOOKUP, i.e. the DM controller's hit latency; FAST_HIT 0 proved equivalent to the previous RTL (module 16/16, SoC level for the exact PD inputs) | `asic/equiv/r16_eq/r16_eq_verdict.txt` |
| 6 | Parameterised line size (8 / 16 / 32 B) and victim depth (2 / 4 / 8) | needed for the sweep | `scripts/m2/run_m2_sweep.py` |
| 7 | Register file and BHT in M9K on the FPGA, cycle-exact | read-ahead addresses + write bypass; k-induction proofs with negative controls; every simulation identical; ASIC netlist unchanged byte for byte; -2,630 to -2,680 LE (-13.5 to -17 %); DM now 12.8k LE, below the published 1 KiB DM with 4x the cache | `results/a1_le_breakdown_rfbht.md`, `NHAT_KY.md` 8a |
| 8 | Cycle-exact ASIC timing fixes | half-cycle paths from the OpenRAM negedge `dout` (adder split, registered selects); proved by SAT; CPI unchanged | `NHAT_KY.md` section 3 and section 9 "OpenRAM suon xuong" |
| 9 | Frozen RTL manifests | every change frozen by aggregate hash (current `6c4ccffd`); PD reads frozen snapshots only | `results/rtl_manifest.json` |

## 2. Workloads and measurements

| # | extension | evidence |
|---|---|---|
| 10 | 12 upstream Embench-IoT kernels (commit 09c2ed8c), source byte-identical except a 5-line scale hook; self-written kernels removed | `RESULTS.md` 1 |
| 11 | CoreMark: 92-point short sweep with source-known CRCs (184 fresh simulations, independently audited) and a standard-duration matrix (4 configurations x performance / validation x 2, all intervals > 10 s) | `RESULTS.md` 1.1 |
| 12 | Unified metric table: CPI, hit rates, mispredict rate, Embench speed / MHz, IRQ entry (5 / 41 cycles), context switch (270 / 292 cycles), ASIC view vs FPGA view | `results/unified_metrics.md` |
| 13 | Design-space sweep (review M2): 256 B - 8 KiB x {DM, DM_DSE, SA2, DM_VC4, SA4}, lines 8 / 16 / 32 B, victim depth 2 / 4 / 8, 13 workloads, with and without FAST_HIT, each twice | `results/m2/M1_M2_REPORT.md` |
| 14 | Controller ablation result: at 4 KiB the controller costs +9.8 % and the organisation -0.3 %; with the hit latency matched, set associativity beats direct mapping at every capacity (3-10 % below 2 KiB) | `REVIEW_RESPONSE.md` M1 |
| 15 | Extended conflict probe: 35 patterns x 6 configurations x 2 capacities, 390 windows, each equal to an independent model; shows the shared victim buffer and the cyclic-order collapse | `results/conflict_probe.csv` |
| 16 | Associativity probe (cachesweep): break points DM 2, SA2 3, DM_VC4 6 | `sw_baremetal` BENCH=cachesweep |
| 17 | Branch predictor on / off: +6.5 to +6.7 % cycles without it | `results/bp0_upstream_r14_4kb_p{1,2}.csv` |
| 18 | Retire share vs minstret explained and proved on 24 / 24 kernels (review A4) | `results/a4_overlap/` |

## 3. Verification

| # | extension | evidence |
|---|---|---|
| 19 | Independent trace-driven cache model: every RTL hit / miss counter exact (48/48, 24/24 SA4/N-way, 60/60 FAST_HIT) | `scripts/cache_model.py`, `scripts/run_crossval.py` |
| 20 | ACT4 (riscv-arch-test, Spike reference) 43/43 twice, logs archived; corrected 1 MiB adapter with an upper-half test | `verification/results/act4/`, `results/architecture_window_20261009/` |
| 21 | Random differential at 50 seeds twice (was one seed), plus an independent Spike reference: 100 Spike runs match all 200 RTL traces, 300 wrong-trace controls detected | `results/random_diff_checked_20261009/`, `results/spike_random_reference_20261011/` |
| 22 | UVM: 48 cases per pass incl. AXI stress at line words 2 / 4 / 8 / 16 and UART RX; wrong-byte controls | `results/uvm_cache_uart_20261009/` |
| 23 | Full verification chain for every RTL change, executed twice (regression, UVM, AXI line sizes, Embench, CoreMark, random differential, ASIC view = FPGA view, directed ISA, synchronisers) | `QUY_TRINH.md` C |
| 24 | Formal proofs for restructurings (SAT / equivalence / k-induction, each with a negative control) | `NHAT_KY.md` |

## 4. FPGA

| # | extension | evidence |
|---|---|---|
| 25 | Ten common seeds x two independent passes for four configurations (was four seeds, one pass); paired comparison, no best seed | `RESULTS.md` 3 |
| 26 | Per-module LE breakdown (review A1) and CPI x LE | `results/a1_le_breakdown_rfbht.md` |
| 27 | Quartus power estimates for ten seeds x two passes (review A9) | `RESULTS.md` 3 |
| 28 | 100-SOF board matrix (25 firmware x 4 configurations, current RTL, seed 2) with hash-bound expected counters; physical session 2026-10-13: 42 of 100 cases measured, every counter equal to both RTL reference passes (OPEN: 58 cases) | `results/board_20261013/`, `results/board_20261013_independent_check/` |

## 5. ASIC (none of this exists in the published repository)

| # | extension | evidence |
|---|---|---|
| 29 | Full OpenLane 2 flows to sign-off (DRC / LVS / XOR / antenna 0, setup >= 0 at tt and ff, hold >= 0 at all 9 corners), each double-executed with identical final netlists: DM 10.63 mm2, SA2 11.56 mm2. DM_VC4 OPEN | `RESULTS.md` 4 |
| 30 | Local OpenLane extensions (off by default): post-route hold ECO on extracted parasitics (now with both RC passes in one step), macro-pin buffers, post-DRT antenna repair (with an allow-congestion option), RC calibration hooks, main-route save, gated four-phase driver with a convergence watchdog | `QUY_TRINH.md` D |
| 31 | Minimum-die search for SA2 (10.54 / 11.05 / 11.305 mm2 fail, 11.56 signs off) | `PROJECT_STATE.md` T4 |
| 32 | Gate-level simulation of the signed netlists: 12 / 12 kernels reproduce the ASIC-view cycle counts | `RESULTS.md` 4 |
| 33 | Activity-based power (GLS -> SAIF -> OpenSTA, RCX parasitics, nom_tt), exact 20 ns-multiple windows, two GLS + two STA passes each: DM mean 119.45 mW (EPI GM 3,608 pJ), SA2 129.64 mW (4,317 pJ) | `results/activity_power_exact_dm_20261013/`, `results/activity_power_exact_sa2_20261014/` |
| 34 | RTL-to-routed-netlist equivalence (register-mapped LEC + algebraic multiplier proof), DM and SA2, with closed premises: asynchronous reset audit, undefined-value independence, clock / edge audit, one-hot invariants | `RESULTS.md` 4.1, `results/lec_sa2_20261013/` |
| 35 | Timing per corner incl. the ss corner (reported, not gated), DRV classification | `RESULTS.md` 4 |

## 6. Method and records

| # | extension |
|---|---|
| 36 | Double execution of every measurement, field-by-field comparison, receipts with SHA-256 of every input |
| 37 | One history (`NHAT_KY.md`), one procedure file (`QUY_TRINH.md`), one results file, one review-status file |
| 38 | Point-by-point response to the review (`REVIEW_RESPONSE.md`) |

## Still open

- DM_VC4 ASIC sign-off (and its double execution, GLS, power, and the LEC step against the final netlist). The LEC part
  that depends only on the synthesis is done, two complete passes identical (`results/lec_vc4_20261014d/`). SA2 /
  DM_VC4 own-knob optimisation in progress (the signed SA2 recipe still carries knobs inherited from DM).
- Process: the signed DM and SA2 layouts were produced with resumes / branches; rule Q (revised 2026-10-14) accepts a
  result only after one complete flow from step 1. Each final netlist is reproduced byte for byte by its second run;
  the single-flow acceptance runs are pending (DM `dm_grid3665x2900_r4` running; SA2 after the E1 comparison;
  `PROJECT_STATE.md` section ASIC).
- Board: 58 of the 100 cases (10 short Embench cases, 48 full-iteration cases).
- Manuscript items (M3 related work and novelty framing, caption / footnote / title fixes).
