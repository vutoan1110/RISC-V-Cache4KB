## 4. Final handoff (2026-09-28): achieved, open issues, diagnostics

Design: RTL 8b163675, DM 4 KiB caches, sky130A / sky130_fd_sc_hd, OpenLane 2.3.10 (local copy with two additions,
below), 20 ns clock (50 MHz).
Signed-off runs: **`final3_A`** (full flow) and **`final3_B`** (independent repeat).
- The two runs are identical on 302 shared flow metrics.
- Final routed netlist sha256 326cc257..., DEF and synthesis netlist (79aba67f..., the same as the previous signoff
  final_A) are byte-identical between them.
- final3 supersedes final_A/final_B. It is the same synthesis; only PD changed.
- The Golden Snapshot of the previous signoff (`RISCV-research_GOLDEN_20260927`) is unchanged.

**PD changes vs final_A (config_FINAL3.json, Incident 91):**
- Heuristic diode insertion off.
- New post-detailed-route antenna repair: `repair_antennas` on the detailed routes plus an incremental
  `detailed_route`, up to 5 rounds. This is the step ORFS has and OpenLane 2.3.10 lacks. It is added to the local
  OpenLane as `DRT_ANTENNA_REPAIR_ITERS` / `DRT_ANTENNA_REPAIR_MARGIN`, and is off by default.

### 4.1 Achieved

| Item | Result | Condition / method |
|---|---|---|
| DRC | Magic 0, KLayout 0, route 0, illegal overlaps 0 | final3_A signoff (final3_B identical) |
| LVS | 0 errors, 0 unmatched devices | Netgen |
| XOR (Magic vs KLayout GDS) | 0 differences | |
| **Antenna** | **0 nets / 0 pins** (final_A: 140 / 159) | post-route repair: 420 -> 22 -> 2 -> 0 violations in 4 rounds |
| Setup at typical corners | nom_tt +2.086 ns, max_tt +1.960 ns: 50 MHz met | OpenSTA signoff, SPEF per RC corner |
| Setup at fast corners | max_ff +4.603, min_ff +4.842 ns | same |
| Hold, all 9 corners | 0 violations; worst +0.030 ns (max_ff) | same |
| Area | std-cell 1.400 mm2 (**-3.7 %**), 192,005 cells (**-20,191**) vs final_A | ~20k heuristic diodes no longer needed |
| RTL vs final netlist equivalence | PROVED, twice (Section 3.1) | RTL == RTL+fsm == N1 == final3 netlist |
| Gate-level simulation | 12/12 Embench kernels PASS; mcycle equals the ASIC-view RTL in every kernel | final3 netlist, Questa |
| Activity-based power | 110.61-115.43 mW (final_A 111.03-116.02) | nom_tt, GLS -> SAIF -> OpenSTA, executed twice with identical results |
| IR drop | worst 0.431 mV | OpenROAD IR-drop report, tt_025C_1v80 libraries |
| Reproducibility | final3_A == final3_B (302 metrics, netlist/DEF hashes) | double execution; final3_B needed 3 retries of random OpenROAD SIGSEGVs (resizer, detailed routing, cell tables) |

### 4.2 Failures and open issues

| Issue | Measured | Status |
|---|---|---|
| ss corner setup | nom_ss -7.413 ns, min_ss -6.425, max_ss -8.311 (2,511 endpoints); ss Fmax ~35-38 MHz | OPEN. Rule: CPI must not change. Deep analysis (4.3) shows PD alone cannot close it. SRAM macros have TT liberty only, so ss figures are optimistic on SRAM paths. |
| Max slew (nom_tt: 757) | 310 on antenna-diode pins (same nets as the loads they protect); 200 on SRAM inputs, whose OpenRAM liberty sets max_transition 0.04 ns (unreachable with real wires); 2 on the clock root / port; **245 on std-cell pins** (median 0.82 ns vs the 0.75 ns SDC limit; 3 above the 1.5 ns liberty limit) | OPEN (std-cell part). Root cause measured: the resizer's parasitic estimate is 1.9-2.4x low. Calibrating it fixed the std-cell slew (245 -> 6) but was not adopted (4.3). |
| Max capacitance (nom_tt: 807) | 702 std-cell drivers (mostly resizer buf_12/buf_8 above the 0.2 pF SDC limit), 104 SRAM dout (liberty max_cap 0.0276 pF), 1 clock | OPEN, same root cause as slew. |
| Max fanout (2,716, every corner) | 1,493 clock-tree leaves (CTS clusters of up to 25 sinks); **all 1,223 data nets have a real fanout <= 8** and exceed only because antenna diodes count as loads | Not a drive problem. Kept: CTS clusters of 8 would cost clock power. |
| Hold margin | worst +0.030 ns at max_ff (final_A +0.080) | Met, but thinner than before. |
| Stock EQY step | final3_A: missing `grep` in nix --pure; final3_B: Python shlex machine fault | The TOOL does not pass. Equivalence is proved by the custom LEC (Section 3.1). |

### 4.3 Technical diagnostics (FLOW_JOURNAL Incident 91; evidence in `asic/pd_exp/`)

**Antenna.**
- All 162 post-route violations were partial side-area ratios (limit 400) on met1-met3. 57 % exceeded the limit by
  at most 1.5x, and 81 of the nets were resizer nets.
- OpenLane 2.3.10 repairs antennas only on the global routes.
- `repair_antennas` works on detailed routes. On final_A's routed database, one round took the violations from 140 to
  1, and the incremental re-route converged to 0 DRC.
- With the heuristic diodes removed, about 11k repair diodes replace about 31k antenna cells.

**Fanout.**
- repair_design leaves no fanout violation.
- The heuristic diodes were inserted after it (step 42) and are counted as loads. That caused 3,276/3,277 of
  final_A's data-net violations.

**Slew/cap and the resizer's optimism.**
- On 2,072 sampled nets, the estimated wire capacitance was below RCX by 2.37x (placement estimate) and 1.93x
  (global-route estimate; 2.1-2.2x on long nets).
- Cause: the tech LEF capacitance has no coupling term, and OpenLane 2 never declares `LAYERS_RC`, although its
  set_rc.tcl reads it. The declaration was added locally.
- Calibration: capacitance = 2.0 x LEF; resistance = RPERSQ / width, which equals the ORFS sky130hd values. It brings
  the estimate to 1.19x (placement) and 0.96x (global route).
- The calibrated resizer sees the real timing and fixes the std-cell slew. Its post-GRT ss estimate is -7.9 ns
  against a signoff of -8.6. Before calibration it was -4.4 against -8.3.
- Not adopted: both global-placement steps are timing-driven and read the RC. The placement therefore changes from
  step 23, and in the full flow (final2_A) max_ss worsened to -9.52 ns with 3 max_ff hold violations. final2_A is
  rejected; its DRC/LVS/XOR are clean.

**ss corner** (2,557 violating endpoints decomposed at max_ss, final_A):
- Mean path: 15.8 ns of logic in 22.6 cells, 7.8 ns in 16 repeaters in series, and 0.5 ns of wire.
- The -0.9 ns "skew" is +-5 % OCV derating on an 8 ns clock tree (CRPR returns 0.39 ns).
- 1,504 endpoints are PC -> I-cache hit -> stall -> enables of the regfile (992) and the BHT (512).
- Worst path, PC -> PC, -8.3 ns: 39 logic cells (19.5 ns), including 3 weak or4_1/or3 gates at 1.1-1.3 ns each, plus
  16 repeaters (7.5 ns).
- Even with zero repeater delay the worst paths need about 20 ns of logic at ss, and the calibrated resizer cannot fix
  them either. Closing ss at 50 MHz therefore needs a shorter critical loop (a CPI-changing pipeline split) or a
  slower ss clock.
- Cycle-exact options are limited:
  - regfile writes could drop `!stall_pipe`, because the W stage is frozen and the write is idempotent;
  - BHT updates are read-modify-write, so the stall gating cannot be dropped there;
  - neither shortens the PC and forwarding loops that set the WNS.

**Reporting correction.**
- The earlier FINAL_METRICS called the ASIC view identical to the FPGA view. It is not: the ASIC's SRAM memories give
  0.2-10.6 % fewer cycles per kernel. The chip's CPI is 1.2755 (ASIC view), not 1.2869.
- The earlier EPI column mixed the two views (up to 12 % error). It is recomputed from the measured window.

### 4.4 Standardized measurements (final3; corner and method stated for every number)

| Metric | Value | Corner / method |
|---|---|---|
| Std-cell area | 1.400 mm^2 (1,399,590 um^2), 192,005 cells | final3_A, after fill |
| Setup WNS, typical | +2.086 (nom_tt), +1.960 (max_tt) ns | OpenSTA, 20 ns clock |
| Setup WNS, slow | -7.413 (nom_ss), -8.311 (max_ss) ns | same; TT SRAM liberty |
| Setup WNS, fast | +4.603 (max_ff) ns | same |
| Hold WNS | +0.224 (nom_tt), +0.030 (max_ff, worst) ns | same |
| Power, vectorless | 102.05 mW total, 0.295 mW leakage | nom_tt_025C_1v80, OpenSTA default activity |
| Power, flow metric `power__total` | 115.5 mW | max_ff_n40C_1v95 (the flow's reporting corner) |
| Power, activity-based | 110.61-115.43 mW over 12 Embench kernels | nom_tt, GLS -> SAIF -> OpenSTA |
| Energy per instruction | 2,379-3,637 pJ | nom_tt, activity-based, ASIC-view cycles |
| CPI, chip (Embench 12, sum) | DM 1.2755 (1,436,264 cycles, 1,126,062 instructions) | ASIC-view RTL = GLS mcycle |
| CPI, FPGA view (Embench 12, sum) | DM 1.2869 / SA2 1.4029 / DM_VC4 1.4117 / DM_DSE 1.4087 | FPGA-view RTL, double-executed |
| Embench cycles, FPGA view | DM 1,449,098 / SA2 1,579,778 / DM_VC4 1,589,606 / DM_DSE 1,586,266 | same |
| CoreMark CPI, FPGA view | DM 2.4922 / SA2 2.5443 / DM_VC4 2.5611 / DM_DSE 2.5568 | same |
| FPGA dm_4kb | 15,529-15,584 LE, Fmax 50.59-54.53 MHz, setup +0.235 ns | Cyclone IV, Slow 1200 mV 85 C, 4 seeds |
