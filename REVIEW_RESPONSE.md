# Response to the review (IEEE Access style, "reject, encourage resubmission")

Point-by-point status of the review of "A RISC-V SoC for Controlled Cache Design-Space Exploration" (review text:
`danh_gia.txt` in the published repository). For each item: what the reviewer asked, what was done, the number, where
the evidence is, and what is still open. All measurements are executed twice and compared field by field. The
manuscript itself is not edited in this workspace; items that are manuscript-only are marked as such.

## Summary

| item | reviewer's point | status |
|---|---|---|
| M1 | the headline result is a controller artifact | addressed: controller cost isolated and removed (FAST_HIT), organisation measured on one controller |
| M2 | three points, one capacity, one line size | addressed: 256 B - 8 KiB, lines 8/16/32 B, 1/2/4 ways, victim depth 2/4/8, 13 workloads |
| M3 | weak novelty, related work misses FPGA emulation, open cache IP, RTL-validated DSE | manuscript work, open |
| A1 | 15-20k LE for RV32I + 1 KiB cache looks unoptimised | core measured at 6.2-6.4k LE; current-RTL per-module table open |
| A2 | Fmax ~52 MHz, core misses 20 ns on Sky130 | FPGA 52-55 MHz at Slow 85C (four seeds); ASIC closes 50 MHz at tt and ff post-route; ss reported |
| A3 | no cross-validation against an independent model | addressed: independent trace-driven cache model, every counter exact |
| A4 | retire share vs minstret look inconsistent | explained and proved on 24/24 kernels |
| A5 | Figure 3 caption "numerically identical" | manuscript fix (absolute counts identical, shares differ) |
| A6 | self-written "Embench-style" kernels | addressed: 12 upstream Embench-IoT kernels + CoreMark; own kernels removed |
| A7 | board evidence not archived, random-differential at one seed, ACT4 logs missing | ACT4 43/43 and random differential 50 seeds archived; board logs need the board (not available) |
| A8 | BP on/off build without results | addressed: BP off costs +6.5 % to +6.7 % cycles |
| A9 | no power / energy per configuration | addressed: FPGA power four seeds; ASIC activity-based power for DM |
| minor | ASIC section (ss -11.7 ns, 646 antenna, 8,718 slew), limitations, seed table, definitions | ASIC re-done (antenna 0, tt/ff closed, DRV reduced and classified); text items are manuscript work |

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

  At the published 4 KiB point the controller accounts for +9.8 % and the organisation for -0.3 %: "DM beats SA2" is a
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

## A1: area

- Quartus hierarchy table (`results/le_breakdown.csv`, 2026-09-22 RTL): the RV32I+Zmmul core is 6,249-6,404 LE in all
  twelve builds, in the range of the cores the reviewer cites; the rest of the 15-20k LE is the two caches, the AXI
  fabric, the APB peripherals and the instrumentation.
- The instrumentation alone (performance counters off vs on, 1 KiB DM): 2,702 LE (18.5 %), 2,038 registers (25.4 %),
  10.88 mW core dynamic power.
- Open: a per-module table for the current RTL (16 KiB RAM, upstream kernels) in the paper's format.

## A2: Fmax and ASIC timing

- FPGA (Cyclone IV E, four seeds, Slow 1200 mV 85 C, current RTL): DM 52.02-54.69 MHz, DM_DSE 52.21-55.27, SA2
  51.81-54.88, DM_VC4 53.30-54.90 MHz; every seed closes 50 MHz.
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

## A7: reproducibility evidence

- ACT4 (riscv-arch-test 2e655961, Spike reference): 43/43 PASS twice (39 RV32I + 4 Zmmul), signatures identical, logs
  kept in `verification/results/act4/`.
- Random differential (branch predictor off vs on, architectural traces hashed): 50 seeds, 50/50 match, twice, on every
  RTL revision since 2026-09-23; traces kept in `results/random_diff/`.
- Board logs: no board is available to this work; open.

## A8: branch predictor

BP off vs on, 12 Embench-IoT kernels, 4 KiB, double-executed (`results/bp0_upstream_r14_4kb_p{1,2}.csv`): +6.48 % (DM),
+6.60 % (SA2), +6.67 % (DM_VC4), +6.62 % (DM_DSE) cycles, geometric mean.

## A9: power and energy

- FPGA (Quartus Power Analyzer, vectorless default toggle rate, four seeds, current RTL): DM 264.1-272.2 mW, DM_DSE
  276.2-282.8, SA2 292.6-295.4, DM_VC4 291.7-296.9 mW total (core dynamic 96.9-129.3 mW).
- ASIC, activity-based (gate-level simulation -> SAIF -> OpenSTA, nom_tt, RCX parasitics), DM with 16 KiB RAM:
  114.8-123.0 mW over the 12 kernels (mean 119.5), energy per instruction 2,612-6,547 pJ (GM 3,608). SA2 / DM_VC4
  ASIC power follows their sign-off (`RESULTS.md` section 4).

## Minor points

- ASIC section: redone. Antenna 0 (post-detailed-route repair), setup closed at every tt and ff corner, hold closed at
  every corner, slew / cap violations reduced and classified by cause; the ss corner and the SRAM Liberty limits are
  reported as limits (`RESULTS.md` section 6).
- "Weighted CPI" is sum(mcycle) / sum(minstret).
- Limitations list, seed table, footnotes, title: manuscript work.
