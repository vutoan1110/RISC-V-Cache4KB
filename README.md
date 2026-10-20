# RISC-V SoC cache design-space research copy

Research copy of the published RISC-V SoC with configurable caches (repository `RISCV-AHB-APB-UART`, not modified from
here). It answers the review of the cache design-space paper: the cache controller confound, a real design-space sweep,
standard benchmarks, and FPGA and ASIC (sky130) implementations of the cache organisations at 4 KiB. The published
1 KiB design is unchanged; everything here runs on the copies in this repository.

## Documents

| file | content |
|---|---|
| `RESULTS.md` | measured results per configuration (architecture, FPGA, ASIC) and what is not established |
| `REVIEW_RESPONSE.md` | point-by-point status of the review items (M1 - M3, A1 - A9, minor) |
| `results/extensions_vs_published_1kib_20261014.md` | everything this copy adds over the published 1 KiB design |
| `results/m2/M1_M2_REPORT.md` | the controller-confound analysis and the design-space sweep |
| `results/unified_metrics.md` | CPI, hit rates, Embench speed, interrupt latency per configuration (generated) |
| `asic/evidence/MAGIC_NAMESPACE_COLLISION.md` | the two Magic fixes needed for the OpenRAM macros |

Measurement outputs (CSV files, receipts, logs, PD runs) stay on the measurement workstation; the documents cite them
by their path under `results/` or `asic/<design>/runs/`. Every number in the documents was executed twice and compared
field by field unless the text says otherwise.

## Configurations

`CACHE_CONFIG` selects the cache organisation:

| value | name | organisation |
|---|---|---|
| 0 | DM | direct-mapped, five-state I-cache controller |
| 3 | DM_DSE | direct-mapped on the ten-state DSE core (separates controller cost from organisation) |
| 1 | SA2 | two-way set-associative, DSE core |
| 2 | DM_VC4 | direct-mapped with a 4-entry victim buffer, DSE core |
| 4 | SA4 | four-way set-associative, N-way core (FPGA and simulation only) |

`CACHE_FAST_HIT` = 1 removes the extra main-array hit cycle of the DSE / N-way cores (default 0). Caches 4 KiB, 16 B
lines, 8-entry I-cache L0; main RAM 16 KiB. This research profile is selected by the point QSFs and the ASIC wrappers;
the shared HDL default stays 1 KiB. The D-cache controllers have seven (DM) and eleven (DSE) states. On the FPGA the
register file and the branch-history table sit in M9K with unchanged cycle behaviour; the ASIC netlist is the same as
before that change. Privileged support is limited to the implemented CSR / timer-interrupt subset.

Workloads: 12 upstream Embench-IoT kernels (`sw/embench_upstream/`, images `fw/up_*.hex`) and CoreMark.

## Status

- Architecture: CPI, hit rates and the design-space sweep (256 B - 8 KiB, lines 8 / 16 / 32 B, 1 / 2 / 4 ways, victim
  depth 2 / 4 / 8, with and without FAST_HIT) are double-executed on the current sources (`RESULTS.md` section 2).
- Verification: directed and UVM tests, 43 ACT4 architecture tests, random differential tests against an independent
  Spike reference, CoreMark CRC checks at all 92 sweep points, formal proofs for the register-file / BHT change
  (`RESULTS.md`, introduction and section 1).
- FPGA (DE2-115, Cyclone IV E): ten common seeds x two passes for four configurations; all 100 board cases passed in one
  physical pass (`RESULTS.md` section 3).
- ASIC (sky130, 50 MHz): DM, SA2 and DM_VC4 signed off on the current RTL, each run twice from step 1 with
  byte-identical final netlists; DRC / LVS / antenna 0, setup and hold met at tt and ff; the ss corner is reported
  (`RESULTS.md` section 4).

## Layout

```
hdl/                 RTL (the SoC top hdl/soc_top.v is shared by FPGA, simulation and ASIC)
tb/, verification/   directed testbenches, UVM, ACT4 architecture tests
sw/, fw/             firmware sources and images
sw_metrics/          interrupt-latency and conflict-probe firmware (outside the RTL manifest)
scripts/             simulation, Quartus, sweep, metrics and verification-chain runners
quartus/             shared Quartus settings; the top-level *.qsf / *.qpf are the DE2-115 projects
asic/                OpenLane designs (soc_dm_4kb, soc_sa2_4kb, soc_vc4_4kb, the DSE SRAM wrapper dse_sram),
                     openlane-local (OpenLane 2.3.10 with the additions below), snapshots (frozen RTL read by PD),
                     equiv (formal proofs and LEC), gls (gate-level simulation and activity power), sta_query (timing,
                     congestion and density queries on step databases), fp_tools / fp_explore (floorplan generation
                     and screening), pd_exp (PD experiments), evidence
results/             summary documents (the measurement outputs stay local, see above)
```

## Reproducing

- Embench matrix: `python scripts/run_ablation.py --compile --configs 0,1,2,3` (FPGA view), with `--asic-view` for the
  ASIC view.
- Design-space sweep: `python scripts/m2/run_m2_sweep.py`, then `python scripts/m2/analyze_m2.py`.
- Verification chain of the current RTL: `bash scripts/run_fullchain_rfbht.sh` (every step twice).
- UVM: `python scripts/verification/run_uvm_matrix.py --run --tag <new_tag>` (four cache configurations, seeds 1 / 2 / 3,
  UART serial RX, AXI stress, two independent passes and wrong-byte controls).
- Architecture tests with the full memory window: `python scripts/verification/run_architecture_window.py --run
  --tag <new_tag>`.
- CoreMark CRC audit: `python scripts/verification/run_coremark_crc.py --run --tag <new_tag>`; standard-duration matrix:
  `python scripts/verification/run_coremark_standard_apb_matrix.py`.
- FPGA fits: `python scripts/fpga/run_paired_seed_matrix.py --run` (common seeds 1..10, two passes, fits run one at a
  time). Board images: `scripts/fpga/prepare_board_reference.py` and `scripts/fpga/build_board_matrix.py` (seed 2 for
  all four configurations, verification gates before every MIF change).
- PD (WSL): `bash asic/run_pd_mk.sh <design dir> <tag>`, or gated with acceptance thresholds:
  `ITEMS="<design>:<tag>:<config>" bash asic/run_gated_pd.sh`; resume after a planned pause with
  `bash asic/run_gated_resume.sh <design> <tag> <config> <reason> drt`. The acceptance pairs of `RESULTS.md` section 4.1
  were driven by `asic/pipeline_acceptance_20261020.sh`, `asic/pipeline_sa2_acc_20261020.sh` and
  `asic/pipeline_vc4_d34_20261020.sh`.
- Gate-level simulation and exact-window activity power: `python scripts/verification/run_gls_exact_window.py`, the pair
  check `scripts/verification/verify_gls_exact_pair.py`, then `python scripts/metrics/run_activity_power_exact.py`.
- Register-mapped LEC on the current RTL: `python scripts/verification/prepare_lec_6c4c.py`, the drivers in
  `asic/equiv/lec/` and `scripts/maintenance/run_lec_gates_6c4c_20261020.sh`.

## Local OpenLane additions

`asic/openlane-local` is OpenLane 2.3.10 with these additions, all off by default:

- `PL_RESIZER_CORNERS`, `GRT_RESIZER_CORNERS`: corner list of the post-CTS / post-GRT timing repair (used to repair at ss
  as well as tt / ff);
- `LAYERS_RC`, `LAYERS_RC_SCOPE`: per-layer RC calibration and where it applies;
- `MacroPinBuffers` (`MACRO_PIN_BUFFER_*`): buffers at the SRAM macro pins;
- `PostRouteHoldECO` (`POST_ROUTE_HOLD_ECO_*`): hold repair on extracted parasitics after detailed routing;
- post-detailed-route antenna repair (`DRT_ANTENNA_REPAIR_ITERS`, `_MARGIN`, `_ALLOW_CONGESTION`).

The gated driver `asic/run_gated_pd.sh` runs the flow in four phases with a gate after each (setup / hold / overflow
thresholds declared at launch) and a convergence watchdog for detailed routing (`asic/drt_watch.sh`).

## Tools

Questa Sim 2024.1, Quartus Prime Lite 20.1.1, OpenLane 2.3.10, OpenROAD 2024-12-08, Yosys 0.46, OpenSTA 2.6, Magic,
Netgen, KLayout, the sky130A PDK with the OpenRAM macros sky130_sram_1kbyte_1rw1r_32x256_8 and
sky130_sram_2kbyte_1rw1r_32x512_8, Verilator 5.053, Spike, riscv64-unknown-elf-gcc 14.2.0. Linux tools run in WSL2
(Ubuntu); Questa and Quartus run on Windows.

## Licences

The project is Apache-2.0. 9 of the 12 Embench-IoT kernels are GPL-3.0-or-later; they stay in this research copy and
are not published with the project.
