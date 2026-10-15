# RISC-V SoC cache design-space research copy

Research copy of the published RISC-V SoC with configurable caches (`E:/Projects/RISCV-AHB-APB-UART`, read-only). It
answers the review of the cache design-space paper: the cache controller confound, a real design-space sweep, standard
benchmarks, and FPGA and ASIC (sky130) implementations of the cache organisations at 4 KiB. The published 1 KiB design
is not modified; everything here runs on the copies in this directory.

## Documents

| file | content |
|---|---|
| `PROJECT_STATE.md` | current state, stopped/finished jobs, recovery prerequisites and ordered remaining work |
| `RESULTS.md` | current measured results per configuration (architecture, FPGA, ASIC), with what is not established |
| `REVIEW_RESPONSE.md` | point-by-point status of the review items (M1-M3, A1-A9, minor) |
| `NHAT_KY.md` | the single design history (RTL, verification, FPGA, PD), the register of known issues, the cleanup log and the table from old run / revision names to new names (Vietnamese) |
| `QUY_TRINH.md` | standing rules and run procedures: verification chain for RTL changes, gated PD flow, FPGA runs, power measurement, golden snapshot, naming, cleanup, reporting (Vietnamese) |
| `WORKSPACE_MAP.md` | functional RTL revision names, folder and document catalogue, verification boundaries, and cleanup evidence |
| `asic/evidence/MAGIC_NAMESPACE_COLLISION.md` | frozen evidence of the two Magic fixes for the OpenRAM macros |
| `results/m2/M1_M2_REPORT.md` | the controller-confound analysis and the design-space sweep |

## Configurations

CACHE_CONFIG 0 = DM (direct-mapped, five-state I-cache controller), 3 = DM_DSE (direct-mapped on the ten-state I-cache DSE core), 1 = SA2
(two-way), 2 = DM_VC4 (direct-mapped with a 4-entry victim buffer), 4 = SA4 (four-way, N-way core). `CACHE_FAST_HIT` = 1
removes the DSE / N-way cores' extra main-array hit cycle (default 0). Caches 4 KiB, 16 B lines; main RAM 16 KiB.
These are the research profile selected by the point QSFs and ASIC wrappers; the shared HDL's cache default is 1 KiB.
The D-cache controllers have seven states (DM) and eleven (DSE). The current implementation places the register file
and branch-history table in M9K on FPGA while preserving cycle behaviour; its ASIC view remains equivalent to the
RAM-16-KiB snapshot at FAST_HIT=0. Privileged support is limited to the implemented CSR/timer-interrupt subset.
Workloads: 12 upstream Embench-IoT kernels (`sw/embench_upstream/`, `fw/up_*.hex`) and CoreMark.
CoreMark numeric CRCs and all40 counters are verified twice for all92 supported capacity/line/organization points,
with184 fresh simulations and an independent raw audit (`results/coremark_sweep_crc_independent_audit_20261010/`). The maintained
runner requires those CRCs before PASS. Its counter window includes initialization/reporting, uses 32 KiB simulation
RAM and is too short for an official score; this preserved -O2 firmware does not fit the 16 KiB chip.

The separate standard-duration matrix now passes all16 cases: four configurations, performance/validation,
two independent executions. The final iterate intervals are13.84-16.13s at50MHz; timer APB deltas match
independent clock edges and simulation time. GCC14.2 `-Os`,2000B,single context,RAM32KiB; simulation-derived
rates and exact ticks are in `results/coremark_standard_apb_matrix_20261011/performance_paired.csv` and
`RESULTS.md` section1.1. These are separate from the short -O2/full-program sweep, and are not board measurements.

Random core tests now also match an independent Spike reference:50seeds x2 fresh Spike executions against all200
preserved current-RTL traces. Evidence: `results/spike_random_reference_20261011/receipt.json`.
This covers the generated RV32I/Zmmul subset; MMIO, interrupts and timing are outside this comparison.

## Layout

```
hdl/                 RTL (the SoC top hdl/soc_top.v is shared by FPGA, simulation and ASIC)
tb/, verification/   directed testbenches, UVM, ACT4 architecture tests
sw/, fw/, fw_board/  firmware sources and images (fw_board: full-length images for a board)
sw_metrics/          interrupt-latency firmware (outside the RTL manifest)
scripts/             simulation, Quartus, sweep, metrics and verification-chain runners
quartus/             shared Quartus settings
asic/                OpenLane designs (soc_dm_4kb, soc_sa2_4kb, soc_vc4_4kb; 1 KiB baseline soc_dm_control),
                     openlane-local (patched OpenLane 2.3.10), snapshots (frozen RTL for PD), equiv (formal proofs and
                     LEC), gls (gate-level simulation and activity power), sta_query, fp_tools / fp_explore (floorplan
                     generation and screening), evidence, pd_exp (PD experiments)
results/             CSV results (every measurement in _p1 / _p2 pairs), reports, pd_run_archive (evidence of deleted
                     runs), cleanup_deleted.txt
```

## Reference designs

- DM, 16 KiB RAM, die 10.63 mm2: signed off 2026-10-02 (runs r14F_A / r14F_B).
- DM, 8 KiB RAM, die 8.12 mm2: signed off 2026-09-28, the golden snapshot `E:/Projects/RISCV-research_GOLDEN_FINAL3_20260928`
  (runs final3_A / final3_B).
- 1 KiB caches: post-route baseline `asic/soc_dm_control/runs/sync_final`.
- SA2, 16 KiB RAM, die 11.56 mm2 (corridor floorplan corr3400x3400_f220): signed off 2026-10-09, runs
  sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1 / _r2, `RESULTS.md` section 4.2.
- DM_VC4: not signed off yet (clock-tree detours at the D$ macro edge), `RESULTS.md` section 4.2.

## Reproducing

Writing-materials snapshot: `results/colleague_materials_20261010.zip`, with the reading guide and scope limits
in `results/colleague_materials_20261010/README.md`. The original manuscript remains unrevised; five referenced
PDFs are missing. The verified research tables and paired evidence are packaged with SHA-256 provenance.
The separate `results/paper_figures_20261010.zip` contains verified PDF/SVG/PNG figures for common-seed FPGA PPA
and controller-matched Embench comparisons, with paired input tables and a portable verifier. These research figures
do not replace the missing assets referenced by the original 1 KiB manuscript.

- Embench matrix: `python scripts/run_ablation.py --compile --configs 0,1,2,3` (FPGA view), with
  `--asic-view` for the ASIC view.
- Design-space sweep: `python scripts/m2/run_m2_sweep.py`, then `python scripts/m2/analyze_m2.py`.
- Verification chain of the current RTL: `bash scripts/run_fullchain_rfbht.sh` (every step twice).
- Supplemental UVM: `python scripts/verification/run_uvm_matrix.py --run --tag <new_date_tag>` (four cache
  configurations, seeds 1/2/3, UART serial RX, AXI stress, two independent passes and wrong-byte controls).
- Complete architecture-test memory window: `python scripts/verification/run_architecture_window.py --run
  --tag <new_date_tag>` (corrected adapter generated from the frozen TB; ACT4 and upper-half tests, twice).
- CoreMark source CRC audit: `python scripts/verification/run_coremark_crc.py --run --tag <new_date_tag>`
  (current six base and five FAST_HIT points, two independent compilations, numeric CRC and complete counters).
- Current FPGA fits: `python scripts/fpga/run_paired_seed_matrix.py --run` (common seeds 1..10, two independent
  passes, Quartus fits sequentially). Inspect existing progress before using `--resume`; the R16 driver is historical.
  Board preparation fixes seed 2 for all four configurations; it uses `scripts/fpga/prepare_board_reference.py`
  and `scripts/fpga/build_board_matrix.py`, with verification gates before MIF changes. Physical measurements are pending.
  The inspected continuation is complete; paired PPA is `results/fpga_common_seeds_continued_20261009_ppa.md`.
  The 100 ready seed2 SOFs, INDEX and two-pass checklist are in `output_files_board_matrix_6c4ccffd_seed2/`.
- PD: `bash asic/run_pd_mk.sh <design dir> <tag>` (WSL), gated: `ITEMS="<design>:<tag>:<config>" bash asic/run_gated_pd.sh`.
- Activity power: `asic/gls/run_gls_power_cfg.sh` (gate-level simulation and SAIF), then `asic/gls/power_cfg.ps1`.
  Preserved DM/SA2 captures include one extra 20 ns period. Paired STA is reproducible for those inputs;
  exact-window recapture is pending (`PROJECT_STATE.md` T3).
- Host health check (this machine has a hardware fault, `NHAT_KY.md` section 9): `python3 asic/parse_ids_probe.py --synth 300000`.

## Tools

Questa Sim 2024.1, Quartus Prime Lite 20.1.1, OpenLane 2.3.10 (local copy `asic/openlane-local`; its additions are listed
in `QUY_TRINH.md` section D), OpenROAD 2024-12-08, Yosys 0.46, OpenSTA 2.6, Magic, Netgen, KLayout, sky130A PDK with the
OpenRAM macros sky130_sram_1kbyte_1rw1r_32x256_8 and sky130_sram_2kbyte_1rw1r_32x512_8. Linux tools run in WSL2 (Ubuntu),
Questa and Quartus on Windows.

## Licences

The project is Apache-2.0. 9 of the 12 Embench-IoT kernels are GPL-3.0-or-later; they stay in this research copy and
are not published with the project.
