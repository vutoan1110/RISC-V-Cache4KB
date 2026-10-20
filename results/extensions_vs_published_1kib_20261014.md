# Extensions of the research copy over the published 1 KiB design

Status 2026-10-20 (first written 2026-10-14). Baseline: the published repository `RISCV-AHB-APB-UART` as reviewed:
five-stage RV32I + Zmmul SoC, DM / SA2 / DM_VC4 caches of 1 KiB, 8 KiB main RAM, 12 kernels (10 self-written
"Embench-style" + md5sum and depthconv from Embench-IoT), Quartus fits at four seeds (DM 15,188, SA2 18,168,
DM_VC4 19,882 LE at seed 2, about 52 MHz), a board matrix of 36 SOFs with no archived logs, an ASIC flow in progress and
not published. Everything below is new in this research copy. Numbers are the double-executed values of `RESULTS.md`;
evidence paths are given per item. Items marked OPEN or in progress are not finished.

## 1. Design (RTL)

| # | extension | what it is / why | evidence |
|---|---|---|---|
| 1 | 4 KiB I and D caches | the research profile (wrappers / QSFs); the generic HDL default stays 1 KiB | `RESULTS.md` 1 |
| 2 | Main RAM 8 -> 16 KiB | needed to run the upstream Embench-IoT kernels (the RAM, not the cache, limited the runnable set) | `RESULTS.md` 1, `REVIEW_RESPONSE.md` A6 |
| 3 | DM_DSE configuration (CACHE_CONFIG 3) | the ten-state DSE controller used as a plain direct-mapped cache: separates controller cost from organisation (review M1) | `REVIEW_RESPONSE.md` M1 |
| 4 | SA4 (four-way, N-way core, tree PLRU) | FPGA / simulation point of the design-space sweep | `RESULTS.md` 3 |
| 5 | `CACHE_FAST_HIT` parameter | DSE / N-way main-array hit answered in ST_LOOKUP, i.e. the DM controller's hit latency; FAST_HIT 0 proved equivalent to the previous RTL (module 16 / 16, SoC level for the exact PD inputs) | `asic/equiv/r16_eq/r16_eq_verdict.txt` |
| 6 | Parameterised line size (8 / 16 / 32 B) and victim depth (2 / 4 / 8) | needed for the sweep | `scripts/m2/run_m2_sweep.py` |
| 7 | Register file and BHT in M9K on the FPGA, cycle-exact | read-ahead addresses + write bypass; k-induction proofs with negative controls, repeated in two fresh passes; every simulation identical; ASIC netlist unchanged byte for byte; -2,630 to -2,680 LE (-13.5 to -17 %); DM now 12.8k LE, below the published 1 KiB DM with four times the cache | `results/a1_le_breakdown_rfbht.md`, `results/rf_bht_m9k_formal_repeat_20261016/` |
| 8 | Cycle-exact ASIC timing fixes | half-cycle paths from the falling-edge `dout` of the OpenRAM macros (adder split, registered selects); each restructuring proved by SAT / equivalence with a negative control; CPI unchanged | `asic/equiv/` |
| 9 | Frozen RTL manifests | every change frozen by an aggregate hash (current `6c4ccffd`); PD reads frozen snapshots only | `results/rtl_manifest.json`, `asic/snapshots/` |

## 2. Workloads and measurements

| # | extension | evidence |
|---|---|---|
| 10 | 12 upstream Embench-IoT kernels (commit 09c2ed8c), source byte-identical except a 5-line scale hook; self-written kernels removed | `RESULTS.md` 1 |
| 11 | CoreMark: 92-point short sweep with source-known CRCs (184 fresh simulations, independently audited) and a standard-duration matrix (4 configurations x performance / validation x 2, all intervals > 10 s) | `RESULTS.md` 1.1 |
| 12 | Unified metric table: CPI, hit rates, mispredict rate, Embench speed / MHz, IRQ entry (5 / 41 cycles), context switch (270 / 292 cycles), ASIC view vs FPGA view | `results/unified_metrics.md` |
| 13 | Design-space sweep (review M2): 256 B - 8 KiB x {DM, DM_DSE, SA2, DM_VC4, SA4}, lines 8 / 16 / 32 B, victim depth 2 / 4 / 8, 13 workloads, with and without FAST_HIT, each twice, repeated on the current RTL | `results/m2/M1_M2_REPORT.md` |
| 14 | Controller ablation result: at 4 KiB the controller costs +9.8 % and the organisation -0.3 %; with the hit latency matched, set associativity beats direct mapping at every capacity (3 - 10 % below 2 KiB) | `REVIEW_RESPONSE.md` M1 |
| 15 | Extended conflict probe: 35 patterns x 6 configurations x 2 capacities, 390 windows, each equal to an independent model; shows the shared victim buffer and the cyclic-order collapse | `RESULTS.md` 2 |
| 16 | Associativity probe (cachesweep): break points DM 2, SA2 3, DM_VC4 6 | `fw/cachesweep.hex` |
| 17 | Branch predictor on / off: +6.5 to +6.7 % cycles without it | `REVIEW_RESPONSE.md` A8 |
| 18 | Retire share vs minstret explained and reproduced (review A4) | `REVIEW_RESPONSE.md` A4 |

## 3. Verification

| # | extension | evidence |
|---|---|---|
| 19 | Independent trace-driven cache model: every RTL hit / miss counter exact (48 / 48, 24 / 24 SA4 / N-way, 60 / 60 FAST_HIT) | `scripts/cache_model.py`, `scripts/run_crossval.py` |
| 20 | ACT4 (riscv-arch-test, Spike reference) 43 / 43 twice, logs archived; corrected 1 MiB adapter with an upper-half test | `verification/results/act4/` |
| 21 | Random differential at 50 seeds twice (was one seed), plus an independent Spike reference: 100 Spike runs match all 200 RTL traces, 300 wrong-trace controls detected | `REVIEW_RESPONSE.md` A7 |
| 22 | UVM: 48 cases per pass incl. AXI stress at line words 2 / 4 / 8 / 16 and UART RX; wrong-byte controls | `verification/uvm/`, `REVIEW_RESPONSE.md` A7 |
| 23 | Full verification chain for every RTL change, executed twice (regression, UVM, AXI line sizes, Embench, CoreMark, random differential, ASIC view = FPGA view, directed ISA, synchronisers) | `scripts/run_fullchain_rfbht.sh` |
| 24 | Formal proofs for restructurings (SAT / equivalence / k-induction, each with a negative control) | `asic/equiv/` |

## 4. FPGA

| # | extension | evidence |
|---|---|---|
| 25 | Ten common seeds x two independent passes for four configurations (was four seeds, one pass); paired comparison, no best seed | `RESULTS.md` 3 |
| 26 | Per-module LE breakdown (review A1) and CPI x LE | `results/a1_le_breakdown_rfbht.md` |
| 27 | Quartus power estimates for ten seeds x two passes (review A9) | `RESULTS.md` 3 |
| 28 | 100-SOF board matrix (25 firmware x 4 configurations, current RTL, seed 2) with hash-bound expected counters; all 100 cases passed in one physical pass (2026-10-13 / 16), every counter equal to both RTL reference passes | `RESULTS.md` 3 |

## 5. ASIC (none of this exists in the published repository)

| # | extension | evidence |
|---|---|---|
| 29 | Full OpenLane 2 flows to sign-off on the current RTL (DRC / LVS / XOR / antenna 0, setup >= 0 at tt and ff, hold >= 0 at all 9 corners), each run twice from step 1 with byte-identical final netlists: DM 10.63 mm2, SA2 11.56 mm2, DM_VC4 12.92 mm2 | `RESULTS.md` 4.1 |
| 30 | ss-corner optimisation, one change at a time with a global-route ss estimate and full flows: DM max_ss -16.8 -> -6.8 ns | `RESULTS.md` 4.2 |
| 31 | DM_VC4 congestion root cause (buffer hot spots in the cache corridor, FastRoute hard-benchmark detours) and its fix (placement target density) | `RESULTS.md` 4.3 |
| 32 | Local OpenLane extensions (off by default): resizer corners per step, post-route hold ECO on extracted parasitics, macro-pin buffers, post-detailed-route antenna repair, RC calibration hooks; gated four-phase driver with a convergence watchdog | `README.md`, `asic/openlane-local/`, `asic/run_gated_pd.sh` |
| 33 | Minimum-die search for SA2 (10.54 / 11.05 / 11.305 mm2 fail, 11.56 signs off) and DM_VC4 (3600 um fails, 3800 um signs off) | `RESULTS.md` 4.8 |
| 34 | Gate-level simulation of the signed netlists: the ASIC-view cycle counts of all 12 kernels are reproduced (DM current RTL, DM / SA2 R14 references; SA2 / DM_VC4 current RTL in progress) | `RESULTS.md` 4.1, 4.5 |
| 35 | Activity-based power (GLS -> SAIF -> OpenSTA, RCX parasitics, nom_tt), exact mcycle x 20 ns windows, two GLS + two STA passes each: DM current RTL mean 120.28 mW (EPI GM 3,633 pJ); R14 DM 119.45 mW, SA2 129.64 mW; SA2 / DM_VC4 current RTL in progress | `REVIEW_RESPONSE.md` A9 |
| 36 | RTL-to-routed-netlist equivalence (register-mapped LEC + algebraic multiplier proof) with closed premises (asynchronous reset audit, undefined-value independence, clock / edge audit, one-hot invariants): DM and DM_VC4 current RTL and DM / SA2 R14 complete; SA2 current RTL: RTL == pre-ABC netlist proved, final netlist in progress | `RESULTS.md` 4.4, 4.5 |
| 37 | Timing per corner incl. the ss corner (reported, not gated), DRV classification | `RESULTS.md` 4 |

## 6. Method and records

| # | extension |
|---|---|
| 38 | Double execution of every measurement, field-by-field comparison, receipts with SHA-256 of every input |
| 39 | One results file (`RESULTS.md`) and one review-status file (`REVIEW_RESPONSE.md`) |

## Still open

- SA2 / DM_VC4 on the current RTL: gate-level simulation and activity power are in progress; for SA2 also the LEC step
  against the final netlist.
- The ss corner does not close at 50 MHz (max_ss -6.8 to -8.4 ns); closing it needs RTL changes in the critical cones,
  which are outside the agreed scope (no CPI change).
- Board: a second physical pass is not scheduled; cases 43..100 have UART evidence only.
- Manuscript items (M3 related work and novelty framing, caption / footnote / title fixes).
