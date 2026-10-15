# RTL consistency audit, 2026-10-14

Owner rule: an RTL change re-runs the whole chain (RTL, TB, UVM, Embench, PD, ...) on that RTL. Current frozen RTL:
manifest 6c4ccffd (227 files; `scripts/rtl_manifest.py --check` IDENTICAL on 2026-10-14). The live `hdl/` tree has
been 6c4ccffd since 2026-10-08 ~21:17 (+07), so every simulation run from `hdl/` after that time used 6c4ccffd. PD and
LEC read frozen snapshots, not `hdl/`.

## On 6c4ccffd (no action)

| result | evidence of the RTL |
|---|---|
| static checks (lint, latch sweep 33 combinations), TB regression 178/178 x2 | 6c4ccffd full chain 2026-10-08 (NHAT_KY 8a) |
| UVM 48 cases x2 | `results/uvm_cache_uart_20261009/` cites 6c4ccffd |
| ACT4 43/43 x2, architecture window | 6c4ccffd chain + `results/architecture_window_20261009/` (after the freeze) |
| random differential 50 seeds x2, Spike reference | `results/random_diff_checked_20261009/` (after the freeze), Spike 2026-10-11 on those traces |
| Embench (current CSVs), FAST_HIT points | `results/rfbht_4kb_p{1,2}.csv`, `results/rfbhtf_4kb_p{1,2}.csv` |
| CoreMark CRC, short sweep 92 points, standard matrix | receipts cite 6c4ccffd (sweep, CRC); standard matrix ran 2026-10-11 from `hdl/` |
| FPGA 10 common seeds x2, LE breakdown A1 | `fpga_points_fpga_common_seeds_continued_20261009_p{1,2}.csv`, `a1_le_breakdown_rfbht.md` |
| board (100 SOF, 42 cases) | `results/board_20261013/` cites 6c4ccffd |
| conflict probe (extended) | `results/conflict_probe.csv` written 2026-10-08 23:46, after the freeze |

## NOT on 6c4ccffd (to redo on 6c4ccffd)

| result | RTL used | action |
|---|---|---|
| PD DM / SA2 / DM_VC4 (all runs, incl. signed r14F, ecomaxmin) | snapshot `rtl_r14` (3ea52396) | DM `dm_grid3665x2900_rtl6c4c_r1` running, SA2 `..._rsztf_eco2_rtl6c4c_r1` queued (sequence f); DM_VC4 later (owner) |
| SA2 / DM_VC4 ASIC wrappers (`asic/dse_sram/cache_dse_data_bank_sram.v`, `asic/soc_{sa2,vc4}_4kb/soc_asic_top.v`) | outside the RTL manifest (live files, committed 4509d5d, unchanged) | frozen into snapshot `rtl_rfbht` with SHA-256 (SNAPSHOT_ID.txt) |
| GLS + exact-window activity power (DM, SA2) | R14 signed layouts | redo on the accepted 6c4ccffd layouts |
| LEC (DM, SA2; DM_VC4 synthesis part) | gold = rtl_r14 | redo with gold = rtl_rfbht on the 6c4ccffd layouts |
| M1 / M2 design-space sweep | R15 / R16 (`results/m2/`, 2026-10-06) | re-run x2 on 6c4ccffd (`scripts/m2/run_m2_sweep.py`) |
| cache-model cross-validation (A3) | R16 (`crossval_r16_4cfg.csv`, `crossval_r16_fast.csv`, 2026-10-06) | re-run x2 (`scripts/run_crossval.py`) |
| retire vs minstret overlap (A4) | R14 (`results/a4_overlap/`, 2026-09-30) | re-run x2 (`scripts/metrics/overlap_mon.sv`) |
| interrupt latency / context switch | R14 / R15 (`results/irq_metrics.csv`, 2026-10-02) | re-run x2 (`sw_metrics/irq`) |
| branch predictor on / off (A8) | R14 (`bp0_upstream_r14_4kb_p{1,2}.csv`) | re-run x2 (`scripts/run_bp.py`) |
| CoreMark R16 baseline | R16 (`coremark_r16_4kb_p{1,2}.csv`) | historical only; re-run if still cited |

The RF / BHT change of 6c4ccffd is cycle-exact (k-induction proofs, full chain identical field by field), so the
re-runs are expected to reproduce the old numbers; they are re-run so that every reported number comes from one RTL.

## Cleanup (owner: delete failed PD runs)

`scripts/maintenance/archive_and_delete_failed_pd_20261014.sh`: 43 failed / stopped / screening PD directories
(~125 GB); text evidence of each (metrics, logs, reports) kept in `results/pd_run_archive/20261014/`. Kept: signed
runs, running runs, synthesis-only evidence, `eco2pass_check_20261013`, DM corridor references dmuA / dmuB (owner).
