# FPGA: ten common seeds, independently measured twice

RTL function: RAM 16 KiB, FPGA register file/BHT in M9K, unchanged benchmark cycles.

Gate: 40/40 paired point/seed rows match every hardware field (runtime excluded).
All configurations use seeds 1..10. Board seed 2 was fixed before the expanded results.
Seeds 1, 3 and 4 reuse the independent rfbht passes; seeds 5..10 and seed 2 were refitted twice.

Timing corner: Slow 1200 mV 85 C. Power: Quartus default toggle-rate estimate.
Power is an estimate, not a board measurement. Physical board status: NOT_RUN.

| configuration | LE mean [min, max], SD | Fmax mean [min, max], SD (MHz) | total power mean [min, max], SD (mW) |
|---|---|---|---|
| DM | 12816.00 [12800, 12842], 12.37 | 54.73 [52.27, 56.18], 1.03 | 255.11 [251.64, 258.93], 1.80 |
| SA2 | 16699.90 [16670, 16739], 22.60 | 52.92 [51.96, 54.54], 0.83 | 281.01 [278.61, 283.04], 1.24 |
| DM_VC4 | 17124.00 [17096, 17148], 15.76 | 53.28 [51.52, 54.4], 1.17 | 279.52 [276.31, 282.35], 1.72 |
| DM_DSE | 14332.60 [14302, 14364], 20.41 | 53.61 [51.02, 55.21], 1.38 | 265.97 [262.46, 270.41], 2.62 |

Full fields and within-seed differences: `fpga_seed_summary_fpga_common_seeds_continued_20261009_p1.md` and `_p2.md`.
Measurement origins: `fpga_common_seeds_continued_20261009_progress.json`. Frozen evidence and sources: `fpga_common_seeds_continued_20261009_plan.json`.
