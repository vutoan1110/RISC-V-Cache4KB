# Status of every point of the review (danh_gia.txt), 2026-10-14

Counting unit: one reviewer point. Section 2 of the review has 3 critical points (M1-M3), section 3 has 9 major points
(A1-A9), section 4 has 8 minor points (m1-m8 below, in the review's order). Sections 5 (revision plan) and 6 (risks)
restate these points and are mapped in the last table. Details and numbers: `REVIEW_RESPONSE.md`.

Status:
- RESOLVED: the data / evidence the reviewer asked for exists, double-executed; the manuscript still has to use it.
- PARTIAL: resolved for part of the scope; what is left is named.
- OPEN-MS: manuscript work only (this workspace does not edit the paper).

| point | reviewer's request (short) | status | what exists / what is left |
|---|---|---|---|
| M1 | headline result is a controller artifact | RESOLVED | DM_DSE ablation + FAST_HIT: at 4 KiB the controller costs +9.8 %, the organisation -0.3 %; with the hit latency matched, set associativity wins at every capacity |
| M2 | three points, one capacity, one line size | RESOLVED | sweep 256 B - 8 KiB x 5 organisations, lines 8/16/32 B, victim depth 2/4/8, 13 workloads, x2 |
| M3 | weak novelty, missing related work | OPEN-MS | supporting result exists (controller depth outweighs associativity in small caches; reversal point quantified); related-work section to be written |
| A1 | 15-20k LE looks unoptimised | RESOLVED | per-module LE table; RF/BHT moved to M9K (-13.5 to -17 %), DM 12.8k LE with 4x the cache |
| A2 | Fmax ~52 MHz, Sky130 core misses 20 ns | PARTIAL | FPGA 51-56 MHz over ten common seeds x2; DM and SA2 ASIC close 50 MHz at tt and ff after routing; left: DM_VC4 sign-off; ss corner is reported, not closed (closing it would change CPI) |
| A3 | no cross-validation with an independent model | RESOLVED | trace-driven model, every counter exact (48/48, 24/24, 60/60) |
| A4 | retire share vs minstret inconsistent | RESOLVED | explained and proved on 24/24 kernels |
| A5 | Figure 3 caption | OPEN-MS | wording fix (absolute counts identical, shares differ) |
| A6 | self-written "Embench-style" kernels | RESOLVED | 12 upstream Embench-IoT kernels; CoreMark CRC-verified sweep and standard-duration matrix (simulation; physical scores not claimed) |
| A7 | board evidence, random differential at one seed, ACT4 logs | PARTIAL | ACT4 43/43 x2, random differential 50 seeds x2 + independent Spike, UVM 48 cases x2: done; board 42 of 100 cases measured and all match; left: 58 board cases |
| A8 | BP on/off without results | RESOLVED | +6.5 to +6.7 % cycles without the predictor |
| A9 | no power / energy per configuration | PARTIAL | FPGA estimate ten seeds x2; ASIC exact-window activity power DM (mean 119.45 mW, EPI GM 3,608 pJ) and SA2 (129.64 mW, 4,317 pJ), each two GLS + two STA passes; left: DM_VC4 after sign-off |
| m1 | ASIC section: ss -11.7 ns, 646 antenna, 8,718 slew, Magic diary | PARTIAL | DM/SA2: antenna 0, tt/ff closed, hold closed at 9 corners, DRV classified, ss reported; left: DM_VC4; section to be rewritten |
| m2 | 11 limitations, merge and fix | OPEN-MS | most technical limitations are now fixed in data (M1, M2, A6, A7, A9); list to be rewritten |
| m3 | GCC 14.2 / UB footnote to the artifact README | OPEN-MS | |
| m4 | Table 5 seeds 1, 2, 3, 5 (why not 4) | RESOLVED | replaced by ten common seeds 1..10, paired, two passes |
| m5 | Table 6 N = 7: one victim hit | RESOLVED | measured: FIFO / round-robin with a cyclic order collapses; the same lines in random order keep 59 % (1 KiB, N = 8) |
| m6 | "victim cache 59 % on matmult" not in the results | OPEN-MS | the 59 % in the data is the random-order conflict probe, not matmult: the conclusion sentence must be corrected |
| m7 | define "weighted CPI" | RESOLVED | sum(mcycle) / sum(minstret) |
| m8 | title says only "on FPGA"; keywords | OPEN-MS | |

Counts (20 points): RESOLVED 10 (M1, M2, A1, A3, A4, A6, A8, m4, m5, m7); PARTIAL 4 (A2, A7, A9, m1); OPEN-MS 6 (M3, A5,
m2, m3, m6, m8). Every PARTIAL point waits on the same two jobs: DM_VC4 ASIC sign-off and the remaining 58 board
cases (the SA2 exact-window power is done since 2026-10-14).

Internal process note (affects A2 / m1 evidence, not a reviewer point): the signed DM and SA2 layouts were produced
with resumes / branches that the owner's 2026-10-13 rule (never continue from a failed step) no longer allows. Each
final netlist is reproduced byte for byte by its second run; single-flow re-executions are pending (DM: owner
decision; SA2: runs E1 / E0). See `PROJECT_STATE.md` section ASIC.

Revision plan of the review (section 5) mapped to the points:

| plan item | points | status |
|---|---|---|
| 1 controller ablation | M1 | done |
| 2 real sweep | M2 | done |
| 3 cross-validation | A3 | done |
| 4 Embench-IoT + CoreMark | A6, M2 | done (simulation) |
| 5 LE breakdown, power, combined metrics | A1, A9 | done for DM/SA2; DM_VC4 ASIC power pending |
| 6 retire vs minstret, Figure 3 | A4, A5 | A4 done; A5 manuscript |
| 7 board logs, random differential 50 seeds | A7 | random differential done; board 42/100 |
| 8 related work, shorter ASIC section | M3, m1 | manuscript |

Risks of section 6: controller artifact (M1) - removed by the ablation; "engineering report, no novelty" (M3) - the
reversal result exists, manuscript work; RTL quality doubts (A1, A2) - LE breakdown and M9K arrays; data errors
(A4, A5) - A4 proved, A5 wording; old references - manuscript.
