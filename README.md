# RISC-V SoC cache design-space research copy

Research copy of the published RISC-V SoC with configurable caches (`E:/Projects/RISCV-AHB-APB-UART`, read-only). It
answers the review of the cache design-space paper: the cache controller confound, a real design-space sweep, standard
benchmarks, and FPGA and ASIC (sky130) implementations of the cache organisations at 4 KiB. The published 1 KiB design
is not modified; everything here runs on the copies in this directory.

## Documents

| file | content |
|---|---|
| `RESULTS.md` | current measured results per configuration (architecture, FPGA, ASIC), with what is not established |
| `REVIEW_RESPONSE.md` | point-by-point status of the review items (M1-M3, A1-A9, minor) |
| `NHAT_KY.md` | the single design history (RTL, verification, FPGA, PD), the register of known issues, the cleanup log and the table from old run / revision names to new names (Vietnamese) |
| `QUY_TRINH.md` | standing rules and run procedures: verification chain for RTL changes, gated PD flow, FPGA runs, power measurement, golden snapshot, naming, cleanup, reporting (Vietnamese) |
| `asic/evidence/MAGIC_NAMESPACE_COLLISION.md` | frozen evidence of the two Magic fixes for the OpenRAM macros |
| `results/m2/M1_M2_REPORT.md` | the controller-confound analysis and the design-space sweep |

## Configurations

CACHE_CONFIG 0 = DM (direct-mapped, five-state controller), 3 = DM_DSE (direct-mapped on the ten-state DSE core), 1 = SA2
(two-way), 2 = DM_VC4 (direct-mapped with a 4-entry victim buffer), 4 = SA4 (four-way, N-way core). `CACHE_FAST_HIT` = 1
removes the DSE / N-way cores' extra main-array hit cycle (default 0). Caches 4 KiB, 16 B lines; main RAM 16 KiB.
Workloads: 12 upstream Embench-IoT kernels (`sw/embench_upstream/`, `fw/up_*.hex`) and CoreMark.

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
- Unified floorplans for DM / SA2 / DM_VC4 (corridor family, 11.305 and 11.56 mm2): in progress, `RESULTS.md` section 4.2.

## Reproducing

- Embench / CoreMark matrix: `python scripts/run_ablation.py --compile --configs 0,1,2,3` (FPGA view), with
  `--asic-view` for the ASIC view.
- Design-space sweep: `python scripts/m2/run_m2_sweep.py`, then `python scripts/m2/analyze_m2.py`.
- Verification chain of the current RTL: `bash scripts/run_fullchain_r16.sh` (every step twice).
- FPGA fits: `bash scripts/run_le_r16.sh` (Quartus runs one fit at a time).
- PD: `bash asic/run_pd_mk.sh <design dir> <tag>` (WSL), gated: `ITEMS="<design>:<tag>:<config>" bash asic/run_gated_pd.sh`.
- Activity power: `asic/gls/run_gls_power_cfg.sh` (gate-level simulation and SAIF), then `asic/gls/power_cfg.ps1`.
- Host health check (this machine has a hardware fault, `NHAT_KY.md` section 9): `python3 asic/parse_ids_probe.py --synth 300000`.

## Tools

Questa Sim 2024.1, Quartus Prime Lite 20.1.1, OpenLane 2.3.10 (local copy `asic/openlane-local`; its additions are listed
in `QUY_TRINH.md` section D), OpenROAD 2024-12-08, Yosys 0.46, OpenSTA 2.6, Magic, Netgen, KLayout, sky130A PDK with the
OpenRAM macros sky130_sram_1kbyte_1rw1r_32x256_8 and sky130_sram_2kbyte_1rw1r_32x512_8. Linux tools run in WSL2 (Ubuntu),
Questa and Quartus on Windows.

## Licences

The project is Apache-2.0. 9 of the 12 Embench-IoT kernels are GPL-3.0-or-later; they stay in this research copy and
are not published with the project.
