# Response to the review (IEEE Access style, "reject, encourage resubmission")

Point-by-point status of the review of "A RISC-V SoC for Controlled Cache Design-Space Exploration" (review text:
`danh_gia.txt` in the published repository). For each item: what the reviewer asked, what was done, the number, where
the evidence is, and what is still open. Final results require two independent executions compared field by field;
incomplete execution evidence is identified as pending. The
manuscript itself is not edited in this workspace; items that are manuscript-only are marked as such.

## Summary

| item | reviewer's point | status |
|---|---|---|
| M1 | the headline result is a controller artifact | addressed: controller cost isolated and removed (FAST_HIT), organisation measured on one controller |
| M2 | three points, one capacity, one line size | addressed: 256 B - 8 KiB, lines 8/16/32 B, 1/2/4 ways, victim depth 2/4/8, 13 workloads |
| M3 | weak novelty, related work misses FPGA emulation, open cache IP, RTL-validated DSE | manuscript work, open |
| A1 | 15-20k LE for RV32I + 1 KiB cache looks unoptimised | addressed: per-module table; register file and BHT moved into M9K, cycle-exact: DM 12.8k, SA2 16.7k, DM_VC4 17.1k LE (-13.5 to -17 %), both Quartus passes identical |
| A2 | Fmax ~52 MHz, core misses 20 ns on Sky130 | FPGA 51.02-56.18 MHz at Slow 85C (ten common seeds, paired); DM/SA2 ASIC close 50 MHz at tt and ff post-route; ss reported; DM_VC4 sign-off pending |
| A3 | no cross-validation against an independent model | addressed: independent trace-driven cache model, every counter exact |
| A4 | retire share vs minstret look inconsistent | explained and proved on 24/24 kernels |
| A5 | Figure 3 caption "numerically identical" | manuscript fix (absolute counts identical, shares differ) |
| A6 | self-written "Embench-style" kernels | 12 upstream Embench kernels;92 short CoreMark sweep points verified x2; additional four-config performance/validation CoreMark matrix verified x2 with >=10s iterate-only timing, simulation RAM32KiB; physical scores pending |
| A7 | board evidence not archived, random-differential at one seed, ACT4 logs missing | ACT4 43/43 x2;50 random seeds x2 with completion gates and additional independent Spike matching all200 RTL traces; board: 42 of 100 cases measured, every counter equals both RTL reference passes; 58 cases left |
| A8 | BP on/off build without results | addressed: BP off costs +6.5 % to +6.7 % cycles |
| A9 | no power / energy per configuration | FPGA default-activity power estimate for ten common seeds x2; DM/SA2 ASIC activity power verified in two STA executions; DM_VC4 pending sign-off |
| minor | ASIC section (ss -11.7 ns, 646 antenna, 8,718 slew), limitations, seed table, definitions | DM/SA2 ASIC re-done (antenna 0, tt/ff closed, DRV reduced and classified); DM_VC4 sign-off pending; text items are manuscript work |

## M1: controller confound

- The published DM point uses a five-state controller; SA2 and DM_VC4 use a ten-state DSE core whose main-array hit
  (L0 miss, main hit) costs one more cycle (ST_IDLE -> ST_LOOKUP -> ST_HIT_RESP / ST_CPU_RESP). DM_DSE (CACHE_CONFIG 3)
  is the DSE core used as a plain direct-mapped cache, so DM_DSE vs DM isolates the controller and X vs DM_DSE isolates
  the organisation.
- New RTL parameter `CACHE_FAST_HIT` (default 0 = previous RTL): with 1, the DSE and N-way cores answer a main-array hit
  in ST_LOOKUP, i.e. with the DM controller's hit latency. FAST_HIT 0 is proved equivalent to the previous RTL at module
  level (16/16, negative controls 8/8 detected) and at SoC level for the exact PD inputs (DM 35,067 / SA2 36,741 / DM_VC4
  37,441 cells, 0 unproven; SoC negative control: 1,824 cells unproven). Full verification chain 45 checks, 0 failures.
- Controller cost, geometric mean of cycles over the 12 Embench-IoT kernels (R15 sweep):

  | capacity | DM_DSE / DM | SA2 / DM_DSE | SA4 / DM_DSE | VC4 / DM_DSE | published-style SA2 / DM |
  |---:|---:|---:|---:|---:|---:|
  | 256 B | +4.33 % | -5.29 % | n/a | +5.97 % | -1.19 % |
  | 512 B | +5.58 % | -6.75 % | -8.64 % | +4.53 % | -1.55 % |
  | 1 KiB | +6.93 % | -2.98 % | -4.78 % | +3.32 % | +3.74 % |
  | 2 KiB | +8.86 % | -0.70 % | -1.44 % | +2.10 % | +8.10 % |
  | 4 KiB | +9.83 % | -0.26 % | -0.07 % | +1.03 % | +9.55 % |
  | 8 KiB | +10.83 % | -0.16 % | -0.17 % | +0.01 % | +10.65 % |

  At the research 4 KiB point the controller accounts for +9.8 % and the organisation for -0.3 %: "DM beats SA2" is a
  controller result.
- Organisation on one controller with DM's hit latency, GM(X_fast / DM_DSE_fast):

  | capacity | SA2 | SA4 | VC4 | CoreMark SA2 | CoreMark SA4 | CoreMark VC4 |
  |---:|---:|---:|---:|---:|---:|---:|
  | 256 B | -5.74 % | n/a | +5.99 % | -1.01 % | n/a | +2.23 % |
  | 512 B | -7.43 % | -9.51 % | +4.61 % | -2.72 % | -3.99 % | -0.19 % |
  | 1 KiB | -3.39 % | -5.56 % | +3.29 % | -1.18 % | -1.20 % | +0.31 % |
  | 2 KiB | -0.86 % | -1.70 % | +2.04 % | -0.67 % | -0.71 % | +0.21 % |
  | 4 KiB | -0.28 % | -0.09 % | +1.07 % | -0.53 % | -0.56 % | +0.17 % |
  | 8 KiB | -0.18 % | -0.20 % | -0.01 % | -0.33 % | -0.33 % | +0.12 % |

  With the controller matched, set associativity is faster than direct mapping in the GM at every capacity, on Embench
  and on CoreMark: 3-10 % below 2 KiB, 0.1-0.6 % at 4-8 KiB. The residual DM_DSE_fast vs DM difference (D-cache L0 and
  store-miss policy) is +1.09 % at 256 B and 0.00 % at 8 KiB.
  The entire supported92-point CoreMark sweep now has source-known numeric CRCs and every counter checked
  in184 fresh simulations against both historical passes. Independent raw verification confirms all inputs,
  actual elaborated profiles, logs/UART streams and paired CSVs:
  `results/coremark_sweep_crc_independent_audit_20261010/receipt.json`.
  Every CoreMark point uses simulation RAM32KiB and the full-program window; none is an official score.
- Per-kernel effects are large in both directions, so claims must be per workload: at 4 KiB nettle-sha256 is +16.2 %
  (SA2) / +22.1 % (SA4) slower (its instruction loop thrashes under LRU), statemate -8.9 %, matmult-int -4.5 / -4.7 %.
- DM_VC4 misses least yet is slowest: the core copies the evicted line into the victim buffer before every refill (I$
  ~5 cycles, D$ ~8 cycles per miss to a valid line). nettle-sha256 at 4 KiB has zero victim hits, the same I$ misses as
  DM, and runs +17.9 % slower: the eviction cost alone. This is a property of this micro-architecture (eviction
  serialised with the refill), not of victim caches in general.
- FPGA cost of FAST_HIT (Quartus seed 2, pass 2 = pass 1): SA2 +456 LE, Fmax 53.71 -> 51.65 MHz; DM_VC4 +115 LE; DM_DSE
  +345 LE; SA4 +881 LE. Every point still closes 50 MHz at Slow 85C (worst setup slack +0.639 ns).
- Evidence: `results/m2/M1_M2_REPORT.md`, `results/m2/M1_M2_analysis.md`, `asic/equiv/r16_eq/r16_eq_verdict.txt`,
  `results/fullchain_r16.log`, `results/le_r16_compare.log`.

## M2: design space

- Grid (`scripts/m2/run_m2_sweep.py`): capacity 256 B .. 8 KiB x {DM, DM_DSE, SA2, DM_VC4, SA4} at 16 B lines; 1 and 4
  KiB x lines 8 / 32 B; 1 and 4 KiB x victim depth 2 / 8; 50 points x 13 workloads (R15) and 44 points with FAST_HIT,
  each run twice (637 / 559 rows, pass 2 = pass 1). The 4 KiB / 16 B rows reproduce the frozen chain results.
- Line size, vs 16 B at the same capacity (Embench GM, FAST): 32 B is better at 4 KiB for every organisation (-4.7 to
  -5.4 %); 8 B is worse (+12 to +13.6 %). The controller confound nearly doubles the apparent 8 B penalty (+19-22 %),
  because shorter lines make the 8-entry L0 cover fewer bytes.
- Victim depth (FAST, vs VC4): VC2 +2.58 % (1 KiB) / +0.23 % (4 KiB); VC8 -1.34 % / -0.45 %; small next to the eviction
  cost.
- The review's point that the old kernels did not stress the cache is answered by the capacity sweep down to 256 B and
  by the upstream Embench-IoT suite (A6).

## M3: novelty and related work

Manuscript work, open. The finding the measurements support: in small FPGA caches the controller's FSM depth can
outweigh the miss-rate benefit of associativity, and the sweep quantifies where the relation reverses; with the hit
latency matched, associativity wins at every capacity in the GM, by 3-10 % below 2 KiB.

The conflict probe is no longer a single-set confirmation of the geometry (`RESULTS.md` section 2, extended probe): over
several sets it shows that the victim buffer is shared (DM_VC4 keeps two lines per set in at most four sets, SA2 in
all), which is what limits DM_VC4 on real workloads; with random instead of cyclic order the victim buffer degrades
gradually (90 -> 65 % over 5 -> 16 sets) instead of collapsing; every one of the 390 windows equals an independent cache
model.

## A1: area

- Quartus hierarchy table (`results/le_breakdown.csv`, 2026-09-22 RTL): the RV32I+Zmmul core is 6,249-6,404 LE in all
  twelve builds, in the range of the cores the reviewer cites; the rest of the 15-20k LE is the two caches, the AXI
  fabric, the APB peripherals and the instrumentation.
- The instrumentation alone (performance counters off vs on, 1 KiB DM): 2,702 LE (18.5 %), 2,038 registers (25.4 %),
  10.88 mW core dynamic power.
- Historical RTL before the RF/BHT M9K change (R16: 4 KiB caches, 16 KiB RAM; seed 2; pass 1 and pass 2 identical on every row):
  `results/a1_le_breakdown_r16.md` / `.csv`, generated by `scripts/le_breakdown.py` from the archived fit reports.
- DM, 15,440 LE: CPU core 6,451 (41.8 %), I-cache 2,439, D-cache 1,896, observability 2,356 (15.3 %; system monitor 1,318,
  performance counters 1,038), SoC glue 656, UART 633, buses 334, board I/O 261, cache AXI master 238, timer 178, RAM
  controller 144 (the 16 KiB RAM itself is 16 M9K).
- Inside the core: register file 1,386 LE (32 x 32 held in flip-flops), branch history table 962 LE (256 x 2 in
  flip-flops), ALU with the multiplier 545 LE + 8 DSP, rest of the datapath 3,199, control 359. The two arrays held in
  flip-flops are 2,348 LE, 36 % of the core.
- Both arrays moved into M9K on the FPGA (2026-10-08, RTL manifest 6c4ccffd), cycle-exact: the read addresses are the
  values the pipeline registers take at the edge (read-ahead), the RAM's old-data read is completed by a bypass of the
  write of that edge, the BHT keeps its reset semantics with one valid bit per entry. Proved by k-induction (register
  file, BHT, read-ahead protocol; three negative controls caught), sim-only checkers beside the arrays, new unit benches;
  the full chain reproduces R16 on every field (Embench, CoreMark, random differential, ASIC view, ACT4) and the ASIC
  netlist is unchanged byte for byte (`ifndef __openlane__`). Four seeds, both passes identical on every field: DM
  12,810 - 12,842 LE (was 15,440 - 15,546), DM_DSE 14,308 - 14,364, SA2 16,675 - 16,739, DM_VC4 17,130 - 17,139; every point
  closes 50 MHz (Fmax 51.96 - 55.52 MHz); DM is below the published 1 KiB design (15,188 LE) with 4x the cache. Per module
  (`results/a1_le_breakdown_rfbht.md`): register file 1,386 -> 52 LE, BHT 962 -> 636 LE, CPU core 6,451 -> 3,818 LE.
- CPI x LE (seed 2, CPI unchanged): DM 19,397; DM_DSE 23,824; SA2 27,699; DM_VC4 28,744 (flip-flop arrays: 23,370 /
  28,226 / 32,321 / 33,245).
- What SA2 and DM_VC4 add over DM is in the caches: SA2 +3,787 (I$ +1,524, D$ +2,263), DM_VC4 +4,004 (I$ +1,670,
  D$ +2,334). The ten-state DSE controller alone (DM_DSE vs DM) is +1,453 (I$ +396, D$ +1,057). The victim buffers of
  DM_VC4 add +2,551 over DM_DSE: there is one in each cache (I$ +1,274, D$ +1,277), each with 4 x 16 B of line data
  plus tags in flip-flops (+795 registers per cache), the 4-way compare and the swap path. The reviewer's "4,694 LE for
  64 B and 4 comparators" (1 KiB, published RTL) is therefore controller + two victim buffers.

## A2: Fmax and ASIC timing

- FPGA (Cyclone IV E, ten common seeds 1..10, two independent passes, Slow 1200 mV 85 C): DM 52.27-56.18 MHz,
  DM_DSE 51.02-55.21, SA2 51.96-54.54, DM_VC4 51.52-54.40 MHz. All 40 point/seed pairs close 50 MHz; hardware fields
  match. No per-configuration best seed is used. Sources: `results/fpga_common_seeds_continued_20261009_ppa.md`.
- ASIC (sky130A, OpenLane 2.3.10, 20 ns): the signed-off DM layouts close setup at every tt and ff corner after routing
  (16 KiB-RAM DM: max_tt +1.708 ns). The ss corner (100 C, 1.60 V) misses by 7.4-10.0 ns depending on the floorplan;
  closing it needs a deeper pipeline, which would change CPI and is outside the study (`RESULTS.md` section 4).

## A3: cross-validation

The RTL hit / miss counters are compared with an independent trace-driven cache model (`scripts/cache_model.py`,
`scripts/run_crossval.py`): every counter exact on 48/48 runs (DM with L0, SA2, DM_VC4, DM_DSE), 24/24 (SA4, SA2 on the
N-way core) and 60/60 FAST_HIT runs.

## A4: retire share vs minstret

`minstret - retire_cycles` equals the number of cycles in which an instruction retired but the exclusive cycle
classifier assigned the cycle to a higher-priority class (CONTROL or LOAD_USE). Proved on 24/24 kernels with a
monitor (`scripts/metrics/overlap_mon.sv`, `results/a4_overlap/`).

## A5: Figure 3 caption

Manuscript fix: absolute counts are identical between configurations, shares differ because the denominators differ.

## A6: standard benchmarks

- 12 upstream Embench-IoT kernels (commit 09c2ed8c; every kernel of that commit that fits a 16 KiB RAM with the result
  reporting frame) and CoreMark. The source is byte-identical to upstream except a 5-line `LOCAL_SCALE_FACTOR` override
  hook. The 12 self-written kernels were removed.
- The main RAM was raised from 8 to 16 KiB for this (the RAM, not the cache, limited the runnable set); the change list
  and its verification are in `NHAT_KY.md` (2026-09-29). Results are not official Embench scores.
- Preserved CoreMark results use simulation RAM32KiB and the preserved -O2 firmware needs19,465 bytes including
  its1KiB stack, exceeding16KiB. This is a restriction of that firmware. The new isolated integer -Os port has
  a smaller static footprint; runtime execution in16KiB and physical-board scores have not been established.
  The canonical CoreMark simulation RAM remains32KiB, with the same cache parameters and memory latency.
- Source-known CoreMark numeric CRCs are now checked for six base and five FAST_HIT 4 KiB points, with 22 fresh
  simulations and every counter matching both passes and the prior baseline. The maintained runner also rejects
  missing/wrong CRCs before CSV/PASS; receipts are under `results/coremark_crc_checked_20261009/` and
  `results/coremark_canonical_checked_20261009/`. Its full-program window includes initialization/reporting, uses
  32 KiB simulation RAM and is too short for an official score. The expanded92-point supported capacity/line/
  organization sweep is now CRC-verified in184 fresh cases and independently audited; all40 counters equal both
  historical sweep references. `results/coremark_sweep_crc_20261010/verification.json` records this complete
  supported grid. SA4_256B_L16 remains excluded because four sets cannot implement the fixed eight-entry L0.
- The additional standard-duration matrix completed16/16 cases: DM/SA2/DM_VC4/DM_DSE x performance/validation
  x2 independent executions, all108 scalar measurement fields equal per pair. The timer is validated against
  independent physical simulation clock edges/time; all final iterate intervals exceed10s. Uniform GCC14.2
  -Os/2000B/single-context firmware,1100 iterations, unchanged algorithms, simulation RAM32KiB. The paired
  rates are76.389218/79.495077/73.561270/68.496689 iterations/s at50MHz. Full method/flags and raw evidence:
  RESULTS.md section1.1 and `results/coremark_standard_apb_matrix_20261011/receipt.json`. This closes the
  short-duration/timer gap for the simulation matrix; physical-board measurements remain pending.

## A7: reproducibility evidence

- ACT4 (riscv-arch-test 2e655961, Spike reference): 43/43 PASS twice (39 RV32I + 4 Zmmul), signatures identical, logs
  kept in `verification/results/act4/`. The corrected 1 MiB adapter independently repeats these 43 cases plus an
  upper-half data/instruction case twice; old signatures/cycles/retirements are identical and the alias control
  detects the frozen original harness defect (`results/architecture_window_20261009/verification.json`).
- Random differential (branch predictor off vs on, architectural traces hashed): 50 seeds, 50/50 match, twice, on every
  RTL revision since 2026-09-23; traces kept in `results/random_diff/`.
  The original result is BP OFF/ON comparison of the same core. The runner now preserves each
  invocation's raw traces and checks process/PASS/fatal/completion/full-trace integrity. A fresh 50-seed pair is
  byte-identical to the prior result (`results/random_diff_checked_20261009/verification.json`).
  The additional independent Spike comparison now passes50seeds twice:100 fresh Spike executions match all200
  preserved RTL traces,7105 retirements/pass. Native Spike engine results are compared on PC/instruction/GPR
  writes/store address/enabled bytes/strobes. Receipt: `results/spike_random_reference_20261011/receipt.json`.
  Scope is the generated RV32I/Zmmul core subset, not MMIO, interrupts, cache behavior or timing.
- Board logs (DE2-115, session of 2026-10-13, current RTL 6c4ccffd, common Quartus seed 2, scope fixed by the owner
  at one physical pass of 100 cases: 4 ramsweep + 48 short Embench + 48 full-iteration Embench): 42 cases measured
  (ramsweep and 10 Embench kernels on all four configurations, statemate on DM and SA2). Every complete UART log
  (boot to DONE, RESULT=PASS) matches BOTH regenerated RTL reference passes on all 25 counters plus D_ACCESS;
  VERIFY_CODE (the kernel's own result value) is identical across the four configurations of each kernel; the HEX
  display equals MCYCLE wherever it was read back. Independent re-check: `results/board_20261013_independent_check/`
  (42/42, 0 problems); session evidence `results/board_20261013/`. These are single physical executions. Remaining:
  10 short cases (statemate DM_VC4/DM_DSE, tarfind and ud on all four) and the 48 full-iteration cases.
- Supplemental UVM independently repeats 48 cases: all four 4 KiB cache configurations, seeds 1/2/3, directed,
  peripheral/IRQ and two-byte serial UART RX, plus AXI stress at line words 2/4/8/16. Scoreboard summaries agree;
  wrong-byte controls fail as required (`results/uvm_cache_uart_20261009/verification.json`). This establishes the
  stated functional scope, not complete code coverage or SA4/FAST_HIT coverage. Older aggregate output is historical.

## A8: branch predictor

BP off vs on, 12 Embench-IoT kernels, 4 KiB, double-executed (`results/bp0_upstream_r14_4kb_p{1,2}.csv`): +6.48 % (DM),
+6.60 % (SA2), +6.67 % (DM_VC4), +6.62 % (DM_DSE) cycles, geometric mean.

## A9: power and energy

- FPGA (Quartus Power Analyzer, default toggle-rate estimate, ten common seeds 1..10, two passes): DM 251.64-258.93 mW,
  DM_DSE 262.46-270.41, SA2 278.61-283.04, DM_VC4 276.31-282.35 mW total. Typical VCCINT1.20V, ambient25C,
  default12.5% toggle activity, low confidence. Compare within each seed; common board seed2 is fixed for all four.
  No per-configuration best seed is used as the representative result. All100 SOFs are ready; board NOT_RUN.
- ASIC, activity-based (gate-level simulation -> SAIF -> OpenSTA, nom_tt, RCX parasitics), DM with 16 KiB RAM:
  114.81-122.99 mW (mean119.45), dynamic114.37-122.55 mW, leakage0.437 mW; EPI2,612-6,547 pJ (GM3,608).
  Unknown activity5.38%; two independent OpenSTA executions match all power groups/origins and reproduce vectorless
  flow power. The second STA reused preserved GLS/SAIF; no second GLS or DM PD rerun is claimed. Corner is
  nom_tt_025C_1v80. Receipts: `results/gls_power_r14F_A_power_verification.json` and
  `results/dm_activity_power_second_pass_20261010.json`. Locked PD sign-off is unchanged.
- SA2, same activity-based method and nom_tt power corner: 127.45-131.75 mW (mean 129.64), dynamic 127.02-131.31 mW,
  leakage 0.437 mW; EPI 2,848-7,354 pJ (GM 4,317); unknown-activity share 4.42 %. Twelve GLS kernels match the ASIC-view
  cycles; two independent OpenSTA executions match all power groups and activity-origin fields, and vectorless
  reproduces the flow. DM_VC4 power awaits sign-off and double execution (`RESULTS.md` section 4).
  A later raw audit found that all 24 preserved DM/SA2 SAIFs include one extra 20 ns period and that legacy
  `win_t*_ns` fields actually contain picoseconds. The paired STA values remain reproducible for their inputs.
  Evidence: `results/embench_gls_evidence_audit_20261010/receipt.json`. Old SAIF/power reports are retained unchanged.
- DM exact-window recapture DONE (2026-10-13): two fresh GLS captures whose SAIF spans exactly mcycle x 20 ns, then
  two independent STA passes per kernel; pass 1 = pass 2 on every field; mean 119.45 mW, every kernel within 0.005 mW
  of the preserved-window value (`results/activity_power_exact_dm_20261013/receipt.json`). SA2 exact window pending
  (to be captured on the final SA2 netlist).

## Minor points

- ASIC section: DM/SA2 redone; DM_VC4 sign-off pending. DM/SA2 antenna 0 (post-detailed-route repair), setup closed at every tt and ff corner, hold closed at
  every corner, slew / cap violations reduced and classified by cause; the ss corner and the SRAM Liberty limits are
  reported as limits (`RESULTS.md` section 6).
- "Weighted CPI" is sum(mcycle) / sum(minstret).
- Table 6, N = 7 (one victim hit): measured, not only explained. At 1 KiB a cyclic sweep keeps DM_VC4 at 100 % up to
  N = 5, 66.7 % at N = 6 and 0 % from N = 7: with round-robin replacement and a cyclic order every replacement evicts
  the line needed next. The same eight lines in random order keep 59 % (SA4 with tree PLRU: 0.3 % cyclic at N = 5,
  49 % random at N = 8).
- Limitations list, seed table, footnotes, title: manuscript work.
