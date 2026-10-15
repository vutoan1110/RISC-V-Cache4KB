# Response to the review (IEEE Access style, "reject, encourage resubmission")

| item | value |
|---|---|
| Paper | "A RISC-V SoC for Controlled Cache Design-Space Exploration" (review text: `danh_gia.txt` in the published repository) |
| Last updated | 2026-10-15 (data as of 2026-10-15 07:45 +07) |
| Current RTL | manifest `6c4ccffd`; results on older RTL are marked [historical] (cycle-exact change, re-runs in progress; `RESULTS.md` section 0) |
| Rule | a result is final only after two independent executions compared field by field; incomplete evidence is marked pending |
| Manuscript | not edited in this workspace; manuscript-only items are marked as such |

For each item: what the reviewer asked, what was done, the number, the evidence, and what is still open. Per-point status
counting (20 points, RESOLVED / PARTIAL / OPEN-MS): `results/review_status_20261014.md`.

## Summary

| Item | Reviewer's point | Status | Key number | RTL of the evidence |
|---|---|---|---|---|
| M1 | the headline result is a controller artifact | addressed | at 4 KiB the controller costs +9.8 %, the organisation -0.3 %; with FAST_HIT, set associativity wins at every capacity | [historical] R15/R16 sweep; re-run on `6c4ccffd` started 2026-10-15 |
| M2 | three points, one capacity, one line size | addressed | 256 B - 8 KiB, lines 8/16/32 B, 1/2/4 ways, victim depth 2/4/8, 13 workloads | [historical] R15/R16; re-run started |
| M3 | weak novelty; related work misses FPGA emulation, open cache IP, RTL-validated DSE | manuscript work, open | - | - |
| A1 | 15-20k LE for RV32I + 1 KiB cache looks unoptimised | addressed | RF/BHT in M9K, cycle-exact: DM 12.8k, SA2 16.7k, DM_VC4 17.1k LE (-13.5 to -17 %) | [current] |
| A2 | Fmax ~52 MHz; core misses 20 ns on Sky130 | partial | FPGA 51.02-56.18 MHz (Slow 85C, ten common seeds, paired); DM / SA2 ASIC close 50 MHz at tt and ff post-route; ss reported | FPGA [current]; ASIC [historical] R14 layouts |
| A3 | no cross-validation against an independent model | addressed | every counter exact (48/48, 24/24, 60/60) | [historical] R16; re-run started |
| A4 | retire share vs minstret look inconsistent | explained and proved | 24/24 kernels | [historical] R14; re-run started |
| A5 | Figure 3 caption "numerically identical" | manuscript fix | absolute counts identical, shares differ | - |
| A6 | self-written "Embench-style" kernels | addressed | 12 upstream Embench kernels; 92 CoreMark sweep points CRC-verified x2; standard-duration CoreMark matrix x2 (>= 10 s, simulation RAM 32 KiB) | [current] |
| A7 | board evidence not archived; random differential at one seed; ACT4 logs missing | partial | ACT4 43/43 x2; 50 random seeds x2 + Spike 200/200 traces; board 42 of 100 cases measured, all equal to both RTL reference passes | [current] |
| A8 | BP on/off build without results | addressed | BP off costs +6.48 to +6.67 % cycles | [historical] R14; re-run started |
| A9 | no power / energy per configuration | partial | FPGA estimate ten seeds x2; ASIC exact-window activity power DM 119.45 mW / SA2 129.64 mW (mean), two GLS + two STA passes each | FPGA [current]; ASIC [historical] R14 layouts |
| minor | ASIC section (ss -11.7 ns, 646 antenna, 8,718 slew), limitations, seed table, definitions | partial | DM / SA2 re-done (antenna 0, tt/ff closed, hold closed at nine corners, DRV classified); text items are manuscript work | ASIC [historical] |

Open for every ASIC item: no `6c4ccffd` layout is signed off yet (PD on `6c4ccffd` started 2026-10-14; `RESULTS.md` 5.7) and
DM_VC4 has no signed-off layout.

## M1: controller confound

- The published DM point uses a five-state controller; SA2 and DM_VC4 use a ten-state DSE core whose main-array hit (L0 miss,
  main hit) costs one more cycle (ST_IDLE -> ST_LOOKUP -> ST_HIT_RESP / ST_CPU_RESP). DM_DSE (CACHE_CONFIG 3) is the DSE core used as
  a plain direct-mapped cache: DM_DSE vs DM isolates the controller, X vs DM_DSE isolates the organisation.
- New RTL parameter `CACHE_FAST_HIT` (default 0 = previous RTL): with 1, the DSE and N-way cores answer a main-array hit in
  ST_LOOKUP, i.e. with the DM controller's hit latency. FAST_HIT 0 is proved equivalent to the previous RTL at module level (16/16,
  negative controls 8/8 detected) and at SoC level for the exact PD inputs (DM 35,067 / SA2 36,741 / DM_VC4 37,441 cells, 0 unproven;
  SoC negative control: 1,824 cells unproven). Full verification chain 45 checks, 0 failures.
- Controller cost, geometric mean of cycles over the 12 Embench-IoT kernels (R15 sweep, [historical]):

  | Capacity | DM_DSE / DM | SA2 / DM_DSE | SA4 / DM_DSE | VC4 / DM_DSE | published-style SA2 / DM |
  |---:|---:|---:|---:|---:|---:|
  | 256 B | +4.33 % | -5.29 % | n/a | +5.97 % | -1.19 % |
  | 512 B | +5.58 % | -6.75 % | -8.64 % | +4.53 % | -1.55 % |
  | 1 KiB | +6.93 % | -2.98 % | -4.78 % | +3.32 % | +3.74 % |
  | 2 KiB | +8.86 % | -0.70 % | -1.44 % | +2.10 % | +8.10 % |
  | 4 KiB | +9.83 % | -0.26 % | -0.07 % | +1.03 % | +9.55 % |
  | 8 KiB | +10.83 % | -0.16 % | -0.17 % | +0.01 % | +10.65 % |

  At the research 4 KiB point the controller accounts for +9.8 % and the organisation for -0.3 %: "DM beats SA2" is a controller result.
- Organisation on one controller with DM's hit latency, GM(X_fast / DM_DSE_fast):

  | Capacity | SA2 | SA4 | VC4 | CoreMark SA2 | CoreMark SA4 | CoreMark VC4 |
  |---:|---:|---:|---:|---:|---:|---:|
  | 256 B | -5.74 % | n/a | +5.99 % | -1.01 % | n/a | +2.23 % |
  | 512 B | -7.43 % | -9.51 % | +4.61 % | -2.72 % | -3.99 % | -0.19 % |
  | 1 KiB | -3.39 % | -5.56 % | +3.29 % | -1.18 % | -1.20 % | +0.31 % |
  | 2 KiB | -0.86 % | -1.70 % | +2.04 % | -0.67 % | -0.71 % | +0.21 % |
  | 4 KiB | -0.28 % | -0.09 % | +1.07 % | -0.53 % | -0.56 % | +0.17 % |
  | 8 KiB | -0.18 % | -0.20 % | -0.01 % | -0.33 % | -0.33 % | +0.12 % |

  With the controller matched, set associativity is faster than direct mapping in the GM at every capacity, on Embench and on
  CoreMark: 3-10 % below 2 KiB, 0.1-0.6 % at 4-8 KiB. The residual DM_DSE_fast vs DM difference (D-cache L0 and store-miss policy)
  is +1.09 % at 256 B and 0.00 % at 8 KiB. The whole supported 92-point CoreMark sweep has source-known numeric CRCs and every
  counter checked in 184 fresh simulations against both historical passes
  (`results/coremark_sweep_crc_independent_audit_20261010/receipt.json`); every CoreMark point uses simulation RAM 32 KiB and the
  full-program window; none is an official score.
- Per-kernel effects are large in both directions, so claims must be per workload: at 4 KiB nettle-sha256 is +16.2 % (SA2) / +22.1 %
  (SA4) slower (its instruction loop thrashes under LRU), statemate -8.9 %, matmult-int -4.5 / -4.7 %.
- DM_VC4 misses least yet is slowest: the core copies the evicted line into the victim buffer before every refill (I$ ~5 cycles,
  D$ ~8 cycles per miss to a valid line). nettle-sha256 at 4 KiB has zero victim hits, the same I$ misses as DM, and runs +17.9 %
  slower: the eviction cost alone. This is a property of this micro-architecture (eviction serialised with the refill), not of
  victim caches in general.
- FPGA cost of FAST_HIT (Quartus seed 2, pass 2 = pass 1): SA2 +456 LE, Fmax 53.71 -> 51.65 MHz; DM_VC4 +115 LE; DM_DSE +345 LE;
  SA4 +881 LE. Every point still closes 50 MHz at Slow 85C (worst setup slack +0.639 ns).
- Evidence: `results/m2/M1_M2_REPORT.md`, `results/m2/M1_M2_analysis.md`, `asic/equiv/r16_eq/r16_eq_verdict.txt`,
  `results/fullchain_r16.log`, `results/le_r16_compare.log`. Re-execution on `6c4ccffd`: `scripts/m2/rerun_m2_6c4ccffd.py` ->
  `results/m2_6c4ccffd/` (started 2026-10-15).

## M2: design space

- Grid (`scripts/m2/run_m2_sweep.py`): capacity 256 B .. 8 KiB x {DM, DM_DSE, SA2, DM_VC4, SA4} at 16 B lines; 1 and 4 KiB x lines
  8 / 32 B; 1 and 4 KiB x victim depth 2 / 8; 50 points x 13 workloads (R15) and 44 points with FAST_HIT, each run twice (637 / 559
  rows, pass 2 = pass 1). The 4 KiB / 16 B rows reproduce the frozen chain results.
- Line size vs 16 B at the same capacity (Embench GM, FAST): 32 B is better at 4 KiB for every organisation (-4.7 to -5.4 %); 8 B is
  worse (+12 to +13.6 %). The controller confound nearly doubles the apparent 8 B penalty (+19-22 %), because shorter lines make the
  8-entry L0 cover fewer bytes.
- Victim depth (FAST, vs VC4): VC2 +2.58 % (1 KiB) / +0.23 % (4 KiB); VC8 -1.34 % / -0.45 %; small next to the eviction cost.
- The review's point that the old kernels did not stress the cache is answered by the capacity sweep down to 256 B and by the
  upstream Embench-IoT suite (A6).

## M3: novelty and related work

Manuscript work, open. The finding the measurements support: in small FPGA caches the controller's FSM depth can outweigh the
miss-rate benefit of associativity, and the sweep quantifies where the relation reverses; with the hit latency matched,
associativity wins at every capacity in the GM, by 3-10 % below 2 KiB.

The conflict probe is no longer a single-set confirmation of the geometry (`RESULTS.md` section 3.3): over several sets it shows
that the victim buffer is shared (DM_VC4 keeps two lines per set in at most four sets, SA2 in all), which is what limits DM_VC4 on
real workloads; with random instead of cyclic order the victim buffer degrades gradually (90 -> 65 % over 5 -> 16 sets) instead of
collapsing; every one of the 390 windows equals an independent cache model. List of the 38 extensions over the published 1 KiB
design: `results/extensions_vs_published_1kib_20261014.md`.

## A1: area

- Quartus hierarchy table (`results/le_breakdown.csv`, 2026-09-22 RTL): the RV32I+Zmmul core is 6,249-6,404 LE in all twelve builds,
  in the range of the cores the reviewer cites; the rest of the 15-20k LE is the two caches, the AXI fabric, the APB peripherals and
  the instrumentation. The instrumentation alone (performance counters off vs on, 1 KiB DM): 2,702 LE (18.5 %), 2,038 registers
  (25.4 %), 10.88 mW core dynamic power.
- Before the RF/BHT change (R16, 4 KiB caches, 16 KiB RAM, seed 2, pass 1 = pass 2; `results/a1_le_breakdown_r16.md` / `.csv`,
  `scripts/le_breakdown.py`): DM 15,440 LE = CPU core 6,451 (41.8 %), I-cache 2,439, D-cache 1,896, observability 2,356 (15.3 %;
  system monitor 1,318, performance counters 1,038), SoC glue 656, UART 633, buses 334, board I/O 261, cache AXI master 238, timer 178,
  RAM controller 144 (the 16 KiB RAM itself is 16 M9K). Inside the core: register file 1,386 LE (32 x 32 in flip-flops), branch
  history table 962 LE (256 x 2 in flip-flops), ALU with the multiplier 545 LE + 8 DSP, rest of the datapath 3,199, control 359. The
  two flip-flop arrays are 2,348 LE, 36 % of the core.
- Both arrays moved into M9K on the FPGA (2026-10-08, RTL `6c4ccffd`), cycle-exact: the read addresses are the values the pipeline
  registers take at the edge (read-ahead), the RAM's old-data read is completed by a bypass of the write of that edge, the BHT keeps
  its reset semantics with one valid bit per entry. Proved by k-induction (register file, BHT, read-ahead protocol; three negative
  controls caught), sim-only checkers beside the arrays and new unit benches; the full chain reproduces R16 on every field (Embench,
  CoreMark, random differential, ASIC view, ACT4). ASIC boundary: the ASIC view is untouched (`ifndef __openlane__`) and the
  `6c4ccffd` synthesis netlist is byte-identical to the R16 synthesis netlist (sha256 `da06d38f`); it differs from the netlist of
  the historical R14 PD runs (sha256 `fc555d6b`).
- Result (ten common seeds, both passes identical; `RESULTS.md` 4.1): DM 12,800 - 12,842 LE (was 15,440 - 15,546), DM_DSE 14,302 -
  14,364, SA2 16,670 - 16,739, DM_VC4 17,096 - 17,148; every point closes 50 MHz; DM is below the published 1 KiB design (15,188 LE)
  with 4x the cache. Per module (`results/a1_le_breakdown_rfbht.md`): register file 1,386 -> 52 LE, BHT 962 -> 636 LE, CPU core
  6,451 -> 3,818 LE.
- CPI x LE (seed 2, CPI unchanged): DM 19,397; DM_DSE 23,824; SA2 27,699; DM_VC4 28,744 (flip-flop arrays: 23,370 / 28,226 / 32,321 /
  33,245).
- What SA2 and DM_VC4 add over DM is in the caches: SA2 +3,787 (I$ +1,524, D$ +2,263), DM_VC4 +4,004 (I$ +1,670, D$ +2,334). The
  ten-state DSE controller alone (DM_DSE vs DM) is +1,453 (I$ +396, D$ +1,057). The victim buffers of DM_VC4 add +2,551 over DM_DSE:
  one in each cache (I$ +1,274, D$ +1,277), each with 4 x 16 B of line data plus tags in flip-flops (+795 registers per cache), the
  4-way compare and the swap path. The reviewer's "4,694 LE for 64 B and 4 comparators" (1 KiB, published RTL) is therefore
  controller + two victim buffers.

## A2: Fmax and ASIC timing

- FPGA (Cyclone IV E, ten common seeds 1..10, two independent passes, Slow 1200 mV 85 C): DM 52.27-56.18 MHz, DM_DSE 51.02-55.21,
  SA2 51.96-54.54, DM_VC4 51.52-54.40 MHz. All 40 point/seed pairs close 50 MHz; hardware fields match; no per-configuration best
  seed. Source: `results/fpga_common_seeds_continued_20261009_ppa.md`.
- ASIC (sky130A, OpenLane 2.3.10, 20 ns) [historical R14 layouts]: the signed-off DM and SA2 layouts close setup at every tt and ff
  corner after routing (16 KiB-RAM DM max_tt +1.708 ns; SA2 max_tt +0.838 ns). The ss corner (100 C, 1.60 V) misses by 7.4-10.0 ns
  depending on the floorplan; closing it needs a deeper pipeline, which would change CPI and is outside the study (`RESULTS.md`
  section 5). Open: `6c4ccffd` layouts (first DM attempt failed its p1 margin gate at +0.307 ns, 2026-10-14) and DM_VC4.

## A3: cross-validation [historical R16]

The RTL hit / miss counters are compared with an independent trace-driven cache model (`scripts/cache_model.py`,
`scripts/run_crossval.py`): every counter exact on 48/48 runs (DM with L0, SA2, DM_VC4, DM_DSE), 24/24 (SA4, SA2 on the N-way core)
and 60/60 FAST_HIT runs. Re-execution on `6c4ccffd`: `scripts/maintenance/rerun_review_sims_6c4ccffd.py` (started 2026-10-15).

## A4: retire share vs minstret [historical R14]

`minstret - retire_cycles` equals the number of cycles in which an instruction retired but the exclusive cycle classifier assigned
the cycle to a higher-priority class (CONTROL or LOAD_USE). Proved on 24/24 kernels with a monitor (`scripts/metrics/overlap_mon.sv`,
`results/a4_overlap/`). Re-execution on `6c4ccffd` started 2026-10-15.

## A5: Figure 3 caption

Manuscript fix: absolute counts are identical between configurations; shares differ because the denominators differ.

## A6: standard benchmarks [current]

- 12 upstream Embench-IoT kernels (commit `09c2ed8c`; every kernel of that commit that fits a 16 KiB RAM with the result-reporting
  frame) and CoreMark. The source is byte-identical to upstream except a 5-line `LOCAL_SCALE_FACTOR` override hook. The 12
  self-written kernels were removed. The main RAM was raised from 8 to 16 KiB for this (the RAM, not the cache, limited the runnable
  set); change list and verification: `NHAT_KY.md` section 1.2 (2026-09-29). Not official Embench scores.
- CoreMark memory: the preserved -O2 firmware needs 19,465 bytes including its 1 KiB stack (> 16 KiB), so preserved CoreMark results
  use simulation RAM 32 KiB with the same cache parameters and memory latency. The isolated -Os integer port has a smaller static
  footprint (15,056 bytes); runtime execution in 16 KiB and board scores are not established.
- Short CoreMark: source-known numeric CRCs checked for six base and five FAST_HIT 4 KiB points (22 fresh simulations, every counter
  matching both passes and the prior baseline); the maintained runner rejects missing / wrong CRCs before CSV/PASS
  (`results/coremark_crc_checked_20261009/`, `results/coremark_canonical_checked_20261009/`). The supported 92-point
  capacity / line / organisation sweep is CRC-verified in 184 fresh cases and independently audited
  (`results/coremark_sweep_crc_20261010/verification.json`); SA4_256B_L16 is excluded because four sets cannot implement the fixed
  eight-entry L0.
- Standard-duration matrix (2026-10-11): 16/16 cases (four configurations x performance / validation x two executions), all 108 scalar
  fields equal per pair; timer validated against independent simulation clock edges / time; every final iterate interval > 10 s.
  GCC 14.2 -Os, 2000 B, single context, 1100 iterations, simulation RAM 32 KiB. Rates at 50 MHz: 76.389218 / 79.495077 / 73.561270 /
  68.496689 iterations/s (DM / SA2 / DM_VC4 / DM_DSE). Method and evidence: `RESULTS.md` section 3.2,
  `results/coremark_standard_apb_matrix_20261011/receipt.json`. Board measurements remain pending.

## A7: reproducibility evidence [current]

- ACT4 (riscv-arch-test `2e655961`, Spike reference): 43/43 PASS twice (39 RV32I + 4 Zmmul), signatures identical, logs in
  `verification/results/act4/`. The corrected 1 MiB adapter repeats the 43 cases plus an upper-half data/instruction case twice; old
  signatures / cycles / retirements are identical and the alias control detects the frozen harness defect
  (`results/architecture_window_20261009/verification.json`).
- Random differential (branch predictor off vs on, architectural traces hashed): 50 seeds, 50/50 match, twice, on every RTL revision
  since 2026-09-23 (traces in `results/random_diff/`). The hardened runner preserves each invocation's raw traces and checks
  process / PASS / fatal / completion / full-trace integrity; a fresh 50-seed pair is byte-identical to the prior result
  (`results/random_diff_checked_20261009/verification.json`). Independent Spike comparison (2026-10-11): 100 fresh Spike executions
  match all 200 preserved RTL traces, 7,105 retirements per pass, compared on PC / instruction / GPR writes / store address / enabled
  bytes / strobes (`results/spike_random_reference_20261011/receipt.json`). Scope: the generated RV32I/Zmmul core subset, not MMIO,
  interrupts, cache behaviour or timing.
- Board (DE2-115, session of 2026-10-13, RTL `6c4ccffd`, common Quartus seed 2; scope fixed by the owner at ONE physical pass of 100
  cases = 4 ramsweep + 48 short Embench + 48 full-iteration Embench): 42 cases measured = 4 ramsweep + 9 complete kernels x 4
  configurations + statemate on DM and SA2. Every complete UART log (boot to DONE, RESULT=PASS) matches BOTH regenerated RTL reference
  passes on all 25 counters plus D_ACCESS; VERIFY_CODE (the kernel's own result value) is identical across the four configurations of
  each kernel; the HEX display equals MCYCLE wherever it was read back (41 read-backs). Independent re-check:
  `results/board_20261013_independent_check/` (42/42, 0 problems); session evidence `results/board_20261013/`. Single physical
  executions. Remaining: 10 short cases (statemate DM_VC4 / DM_DSE, tarfind and ud on all four) and the 48 full-iteration cases.
- Supplemental UVM: 48 cases twice (four cache configurations, seeds 1/2/3, directed, peripheral/IRQ and two-byte UART RX, AXI stress
  at line words 2/4/8/16); scoreboard summaries agree; wrong-byte controls fail as required
  (`results/uvm_cache_uart_20261009/verification.json`). Functional scope only, not code coverage or SA4 / FAST_HIT coverage.

## A8: branch predictor [historical R14]

BP off vs on, 12 Embench-IoT kernels, 4 KiB, double-executed (`results/bp0_upstream_r14_4kb_p{1,2}.csv`): +6.48 % (DM), +6.60 % (SA2),
+6.67 % (DM_VC4), +6.62 % (DM_DSE) cycles, geometric mean. Re-execution on `6c4ccffd` started 2026-10-15.

## A9: power and energy

- FPGA [current] (Quartus Power Analyzer, default toggle-rate estimate 12.5 %, Typical VCCINT 1.20 V, ambient 25 C, low confidence;
  ten common seeds x two passes): DM 251.64-258.93 mW, DM_DSE 262.46-270.41, SA2 278.61-283.04, DM_VC4 276.31-282.35 mW total. Compare
  within each seed; no per-configuration best seed. The board (42 of 100 cases measured) records counters, not power.
- ASIC [historical R14 layouts], activity-based (GLS -> SAIF -> OpenSTA, corner nom_tt_025C_1v80, RCX parasitics):

  | Design | Total, mW (mean) | Dynamic, mW | Leakage, mW | EPI, pJ (GM) | Unknown activity | Receipt |
  |---|---|---|---|---|---|---|
  | DM 16 KiB RAM | 114.81 - 122.99 (119.45) | 114.37 - 122.55 | 0.437 | 2,612 - 6,547 (3,608) | 5.38 % | `results/activity_power_exact_dm_20261013/receipt.json` |
  | SA2 | 127.45 - 131.75 (129.64) | 127.02 - 131.31 | 0.437 | 2,848 - 7,354 (4,317) | 4.42 % | `results/activity_power_exact_sa2_20261014/receipt.json` |

  Both are exact-window recaptures (2026-10-13 DM, 2026-10-14 SA2): two fresh GLS captures whose SAIF spans exactly `mcycle x 20 ns`,
  then two independent STA passes per kernel; pass 1 = pass 2 on every field; every kernel within 0.005 mW of the earlier
  preserved-window value. The earlier evaluation (two STA executions from one preserved SAIF; `results/gls_power_r14F_A_power_verification.json`,
  `results/dm_activity_power_second_pass_20261010.json`) and the audit that found the extra 20 ns period and picosecond `win_t*_ns`
  fields (`results/embench_gls_evidence_audit_20261010/receipt.json`) are retained unchanged. DM_VC4 power awaits a signed layout;
  DM / SA2 power must be redone on the accepted `6c4ccffd` layouts.

## Minor points

- ASIC section: DM / SA2 re-done [historical R14 layouts]: antenna 0 (post-detailed-route repair), setup closed at every tt and ff
  corner, hold closed at every corner, slew / cap violations reduced and classified by cause; the ss corner and the SRAM Liberty limits
  are reported as limits (`RESULTS.md` section 7). DM_VC4 sign-off pending.
- "Weighted CPI" is sum(mcycle) / sum(minstret).
- Table 5 seeds 1, 2, 3, 5: replaced by ten common seeds 1..10, paired, two passes.
- Table 6, N = 7 (one victim hit): measured, not only explained. At 1 KiB a cyclic sweep keeps DM_VC4 at 100 % up to N = 5, 66.7 % at
  N = 6 and 0 % from N = 7: with round-robin replacement and a cyclic order every replacement evicts the line needed next. The same
  eight lines in random order keep 59 % (SA4 with tree PLRU: 0.3 % cyclic at N = 5, 49 % random at N = 8).
- Limitations list, GCC footnote, title: manuscript work.

## Revision history

| Date | Change |
|---|---|
| 2026-09-22 | review items inventoried and tracked from this date |
| 2026-10-07 | English point-by-point file (commit `507c3fb`) |
| 2026-10-09 .. 11 | A1 (M9K), A6 (CoreMark CRC, standard matrix), A7 (UVM, ACT4 window, random, Spike), A9 (SA2 power) updated |
| 2026-10-13 | A7 board session (42 cases); A9 DM exact window |
| 2026-10-14 | A9 SA2 exact window; per-point status draft `results/review_status_20261014.md` |
| 2026-10-15 07:46 | state of 2026-10-15 (commit `2d4202d`) |
| 2026-10-15 | restructured: RTL column in the summary; board count corrected (9 complete kernels; 41 display read-backs); A9 "board NOT_RUN" and "SA2 exact window pending" corrected; A1 synthesis boundary R16 `da06d38f` vs R14 PD `fc555d6b`; historical items marked with their re-run status |
| 2026-10-15 | references point to the single topic-structured `NHAT_KY.md` |
