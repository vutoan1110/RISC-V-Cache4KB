# RISC-V SoC cache design-space research copy

Research copy of the published RISC-V SoC with configurable caches (`E:/Projects/RISCV-AHB-APB-UART`, read-only). It answers the
review of the cache design-space paper: the cache-controller confound, a real design-space sweep, standard benchmarks, and FPGA and
ASIC (sky130) implementations of the cache organisations at 4 KiB. The published 1 KiB design is not modified; everything here runs on
the copies in this directory.

| item | value |
|---|---|
| Last updated | 2026-10-15 (state as of 2026-10-15 07:45 +07) |
| Current RTL | manifest `6c4ccffd` (2026-10-08): RAM 16 KiB, register file / BHT in M9K on the FPGA, optional FAST_HIT |
| Main open work | sign-off of the ASIC layouts on `6c4ccffd` (DM, SA2 running; DM_VC4 deferred); 58 board cases |

## 1. Documents

| File | Content | Language |
|---|---|---|
| `PROJECT_STATE.md` | current state, running jobs, state log, ordered remaining work with commands | English |
| `RESULTS.md` | measured results per configuration (verification, architecture, FPGA, board, ASIC), with RTL provenance and what is not established | English |
| `REVIEW_RESPONSE.md` | point-by-point status of the review items (M1-M3, A1-A9, minor) | English |
| `QUY_TRINH.md` | binding rules and run procedures (verification chain, gated PD flow, FPGA, power, LEC, golden, naming, cleanup, reporting) | Vietnamese, ASCII |
| `NHAT_KY.md` | the single design history, by topic (RTL revisions, verification, FPGA / board, LEC, power, PD infrastructure, ASIC per configuration, new-event log 8a, known issues, cleanup, renames); rewritten 2026-10-15, the hour-by-hour version is in git history | Vietnamese, ASCII |
| `WORKSPACE_MAP.md` | functional names of RTL revisions, folder / document catalogue, verification boundaries | Vietnamese, ASCII |
| `CLOUD_TASKS.md` | text-only tasks for cloud sessions | English |
| `CODEX_PROMPT.md` | historical agent instructions of 2026-10-09; not current rules | English |
| `asic/evidence/MAGIC_NAMESPACE_COLLISION.md` | frozen evidence of the two Magic fixes for the OpenRAM macros | English |
| `results/m2/M1_M2_REPORT.md` | controller-confound analysis and design-space sweep | English |
| `report_page/README.md` | source of the hosted report page (`report_page/soc_report.html`, Version 9, 2026-10-14) | English |

## 2. Configurations

| CACHE_CONFIG | Name | Organisation | Controller |
|---:|---|---|---|
| 0 | DM | direct-mapped | five-state I-cache / seven-state D-cache controller |
| 3 | DM_DSE | direct-mapped | ten-state I-cache / eleven-state D-cache DSE core (isolates the controller cost) |
| 1 | SA2 | two-way set-associative | DSE core |
| 2 | DM_VC4 | direct-mapped + 4-entry victim buffer | DSE core |
| 4 | SA4 | four-way, tree pseudo-LRU (FPGA / simulation only) | N-way core |

- `CACHE_FAST_HIT` = 1 removes the DSE / N-way cores' extra main-array hit cycle (default 0).
- Research profile (selected by the point QSFs and ASIC wrappers; the shared HDL default is 1 KiB): caches 4 KiB, 16 B lines, 8-entry
  I-cache L0; main RAM 16 KiB unified.
- The FPGA view places the register file and branch-history table in M9K while preserving cycle behaviour; the ASIC view is unchanged
  (its synthesis netlist equals the R16 synthesis, sha256 `da06d38f`; the historical R14 PD layouts were synthesised from `rtl_r14`,
  sha256 `fc555d6b`).
- Privileged support is limited to the implemented CSR / timer-interrupt subset; no full synchronous exceptions, no DIV/REM.
- Workloads: 12 upstream Embench-IoT kernels (`sw/embench_upstream/`, `fw/up_*.hex`) and CoreMark (simulation RAM 32 KiB).

## 3. Status at a glance (2026-10-15)

| Area | Status | Details |
|---|---|---|
| Verification on `6c4ccffd` | full chain 0 failures; UVM 48 cases x2; ACT4 43/43 x2 (1 MiB adapter); random 50 seeds x2 + Spike 200/200 traces; Embench; CoreMark CRC x2 for all 92 sweep points; standard-duration CoreMark 16/16 | `RESULTS.md` 2 |
| Architecture | CPI / hit rates per configuration; controller vs organisation decomposition; conflict probe | `RESULTS.md` 3, `REVIEW_RESPONSE.md` M1/M2 |
| FPGA | ten common seeds x2: DM 12.8k, DM_DSE 14.3k, SA2 16.7k, DM_VC4 17.1k LE; all close 50 MHz (Slow 85C) | `RESULTS.md` 4 |
| Board (DE2-115) | one physical pass scheduled for 100 cases: 42 measured, 41 display read-backs confirmed, all equal to both RTL reference passes; 58 left | `RESULTS.md` 4.4 |
| ASIC, historical R14 layouts | DM 10.63 mm2 signed off 2026-10-02; SA2 11.56 mm2 signed off 2026-10-09; both double executed, with exact-window activity power and register-mapped LEC; DM_VC4 not signed off | `RESULTS.md` 5 |
| ASIC on `6c4ccffd` | DM and SA2 second attempts running since 2026-10-15 00:18 UTC; DM_VC4 deferred | `PROJECT_STATE.md` 3 |

## 4. Reference designs

| Design | Die | Signed off | Runs | RTL |
|---|---|---|---|---|
| DM, 16 KiB RAM | 10.63 mm2 (grid3665x2900) | 2026-10-02 | r14F_A / r14F_B (`dm_grid3665x2900_r1` / `_r2`) | `rtl_r14` (historical) |
| DM, 8 KiB RAM (golden) | 8.12 mm2 (grid2800x2900) | 2026-09-28 | final3_A / final3_B; snapshot `E:/Projects/RISCV-research_GOLDEN_FINAL3_20260928` | `8b163675` (historical) |
| DM, 1 KiB caches | 5.22 mm2 | 2026-09-18 (post-route baseline) | `asic/soc_dm_control/runs/sync_final` | historical |
| SA2, 16 KiB RAM | 11.56 mm2 (corr3400x3400_f220) | 2026-10-09 | `sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1` / `_r2` | `rtl_r14` (historical) |
| DM_VC4 | - | not signed off (antenna re-route does not converge; deferred) | - | - |

The signed R14 layouts were produced with resumes / branches; under the rule of 2026-10-14 each needs one clean full flow, which is now
being done on `6c4ccffd`.

## 5. Layout

```
hdl/                 RTL (the SoC top hdl/soc_top.v is shared by FPGA, simulation and ASIC)
tb/, verification/   directed testbenches, UVM, ACT4 architecture tests
sw/, fw/, fw_board/  firmware sources and images (fw_board: full-length images for the board)
sw_metrics/          interrupt-latency and conflict-probe firmware (outside the RTL manifest)
scripts/             simulation, Quartus, sweep, metrics, verification-chain and maintenance runners
quartus/             shared Quartus settings
asic/                OpenLane designs (soc_dm_4kb, soc_sa2_4kb, soc_vc4_4kb; 1 KiB baseline soc_dm_control),
                     openlane-local (patched OpenLane 2.3.10), snapshots (frozen RTL for PD; current rtl_rfbht), equiv (formal
                     proofs and LEC), gls (gate-level simulation and activity power), sta_query, fp_tools / fp_explore (floorplan
                     generation and screening), evidence, pd_exp (PD experiments)
report_page/         source of the hosted report page
results/             CSV results (every measurement in _p1 / _p2 pairs), receipts, reports, pd_run_archive (evidence of deleted
                     runs), cleanup_deleted.txt
```

## 6. Reproducing

Writing materials: `results/colleague_materials_20261010.zip` (reading guide and scope limits in
`results/colleague_materials_20261010/README.md`; the original manuscript is unrevised and five referenced PDFs are missing) and
`results/paper_figures_20261010.zip` (verified PDF / SVG / PNG figures for common-seed FPGA PPA and controller-matched Embench, with
paired input tables and a portable verifier; they do not replace the missing assets of the 1 KiB manuscript).

| Task | Command |
|---|---|
| Check the RTL against the manifest | `python scripts/rtl_manifest.py --check` (without `--check` it rewrites the manifest) |
| Verification chain of the current RTL (every step twice) | `bash scripts/run_fullchain_rfbht.sh` |
| Embench matrix | `python scripts/run_ablation.py --compile --configs 0,1,2,3` (FPGA view); add `--asic-view` for the ASIC view |
| Design-space sweep | `python scripts/m2/run_m2_sweep.py`, then `python scripts/m2/analyze_m2.py` (re-run on `6c4ccffd`: `scripts/m2/rerun_m2_6c4ccffd.py`) |
| Supplemental UVM | `python scripts/verification/run_uvm_matrix.py --run --tag <new_date_tag>` |
| Architecture-test memory window | `python scripts/verification/run_architecture_window.py --run --tag <new_date_tag>` |
| CoreMark CRC (11 points) | `python scripts/verification/run_coremark_crc.py --run --tag <new_date_tag>` |
| CoreMark standard duration | `scripts/verification/run_coremark_standard_apb_matrix.py` |
| FPGA fits (common seeds 1..10, two passes, sequential) | `python scripts/fpga/run_paired_seed_matrix.py --run` (inspect progress before `--resume`) |
| Board SOFs / reference | `scripts/fpga/prepare_board_reference.py`, `scripts/fpga/build_board_matrix.py`; ready SOFs, INDEX and checklist in `output_files_board_matrix_6c4ccffd_seed2/`; paired PPA `results/fpga_common_seeds_continued_20261009_ppa.md` |
| PD (WSL) | `bash asic/run_pd_mk.sh <design dir> <tag>`; gated: `ITEMS="<design>:<tag>:<config>" bash asic/run_gated_pd.sh` |
| Activity power | `asic/gls/run_gls_power_cfg.sh` or the exact-window runner `scripts/verification/run_gls_exact_window.py`, then `asic/gls/power_cfg.ps1` (two STA passes) |
| Host health probe | `python3 asic/parse_ids_probe.py --synth 300000` (8 runs; sporadic non-reproducible Python faults have been observed on this host, cause not determined; see the known issues in NHAT_KY) |

## 7. Tools

Questa Sim 2024.1, Quartus Prime Lite 20.1.1, OpenLane 2.3.10 (local copy `asic/openlane-local`; additions listed in `QUY_TRINH.md`
section D), OpenROAD 2024-12-08, Yosys 0.46, OpenSTA 2.6, Magic, Netgen, KLayout, Verilator 5.053, Spike, GCC 14.2 (riscv64-unknown-elf),
sky130A PDK with the OpenRAM macros sky130_sram_1kbyte_1rw1r_32x256_8 and sky130_sram_2kbyte_1rw1r_32x512_8. Linux tools run in WSL2
(Ubuntu); Questa and Quartus on Windows.

## 8. Licences

The project is Apache-2.0. 9 of the 12 Embench-IoT kernels are GPL-3.0-or-later; they stay in this research copy and are not
published with the project.

## Revision history

| Date | Change |
|---|---|
| 2026-09-30 | created with the final3 baseline (commit `0bf22b7`) |
| 2026-10-07 | document set consolidated (commit `507c3fb`) |
| 2026-10-09 .. 15 | CoreMark, UVM, Spike, board, PD notes added; state of 2026-10-15 (commit `2d4202d`) |
| 2026-10-15 | restructured: document table with languages, configuration table, status at a glance, reference-design table, reproduction table; board wording (42 measured, 41 display read-backs, one scheduled pass, 58 left); synthesis boundary R16 / R14; neutral wording of the host probe |
| 2026-10-15 | single topic-structured `NHAT_KY.md` (no second version) |
