# Final metrics — RTL 8b163675

## 1. Architecture per configuration (Embench-IoT 12 kernels, 4 KiB caches, 50 MHz clock)

Source: `results/rtlfix_4kb_p{1,2}.csv` (FPGA-view RTL simulation: the SoC with the FPGA memories). Double execution: pass 1 == pass 2.

The last row is the ASIC view of DM (`results/asic_view_4kb_p{1,2}.csv`, pass 1 == pass 2): the RTL of the ASIC netlist, whose memories are the SRAM macros. It retires the same instructions with identical counts on 40 of 43 fields, but mcycle, I-wait and D-wait are lower (0.2-10.6 % per kernel), so the CPI of the chip is the ASIC-view value; the FPGA-view rows are the FPGA/DSE comparison. (Corrected in FLOW_JOURNAL Incident 91: an earlier version called the views identical.)

| Config | Cycles (sum) | Instr (sum) | CPI (sum) | CPI geomean | I$ hit | D$ read hit | D$ write hit | Branch mispredict | I-wait | D-wait | Load-use | Control | MMIO |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DM | 1449098 | 1126062 | 1.2869 | 1.3098 | 99.96 % | 99.34 % | 90.59 % | 9.71 % | 6.7 % | 10.3 % | 2.1 % | 1.6 % | 0.0 % |
| SA2 | 1579778 | 1126062 | 1.4029 | 1.4237 | 99.96 % | 99.60 % | 91.64 % | 9.71 % | 11.7 % | 12.1 % | 1.9 % | 1.5 % | 0.0 % |
| DM_VC4 | 1589606 | 1126062 | 1.4117 | 1.4339 | 99.96 % | 99.34 % | 90.59 % | 9.71 % | 11.7 % | 12.7 % | 1.9 % | 1.5 % | 0.0 % |
| DM_DSE | 1586266 | 1126062 | 1.4087 | 1.4304 | 99.96 % | 99.34 % | 90.59 % | 9.71 % | 11.7 % | 12.5 % | 1.9 % | 1.5 % | 0.0 % |
| DM (ASIC view) | 1436264 | 1126062 | 1.2755 | 1.2816 | 99.96 % | 99.34 % | 90.59 % | 9.71 % | 6.5 % | 9.7 % | 2.1 % | 1.6 % | 0.0 % |

CoreMark (`results/coremark_rtlfix_4kb_p{1,2}.csv`):

| Config | Cycles | Instr | CPI | I$ hit | Branch mispredict |
|---|---:|---:|---:|---:|---:|
| DM | 2520901 | 1011515 | 2.4922 | 99.88 % | 2.02 % |
| SA2 | 2573624 | 1011515 | 2.5443 | 99.94 % | 2.02 % |
| DM_VC4 | 2590590 | 1011515 | 2.5611 | 99.91 % | 2.02 % |
| DM_DSE | 2586274 | 1011515 | 2.5568 | 99.88 % | 2.02 % |

## 2. FPGA (Cyclone IV EP4CE115, Quartus 20.1, 50 MHz, 4 seeds per point)

Source: `fpga_points_r12b_p1.csv`, pass 2 `fpga_points_r12b_p2.csv`: identical. Timing corner: Slow 1200 mV 85 C (signoff) and Slow 0 C. Power: Quartus Power Analyzer at the default toggle rate (vectorless estimate, not switching activity).

| Point | LE (min–max) | Registers | M9K | mult9 | Fmax S85C MHz (min–max) | Setup S85C ns (min) | Hold S85C ns (min) | Power total / core dyn / static mW (seed 2) |
|---|---|---:|---:|---:|---|---:|---:|---|
| dm_4kb | 15529–15584 | 8430 | 18 | 8 | 50.59–54.53 | +0.235 | +0.329 | 262.46 / 95.27 / 100.1 |
| sa2_4kb | 19438–19527 | 9109 | 28 | 8 | 51.18–53.56 | +0.460 | +0.318 | 292.43 / 124.73 / 100.55 |
| vc4_4kb | 19834–19893 | 10497 | 18 | 8 | 53.17–55.51 | +1.194 | +0.269 | 290.46 / 122.76 / 100.52 |
| dse_4kb | 16869–17027 | 8712 | 18 | 8 | 50.95–55.33 | +0.374 | +0.333 | 278.03 / 110.64 / 100.27 |

## 3. ASIC (DM 4 KiB, sky130A / sky130_fd_sc_hd, OpenLane 2.3.10, CLOCK_PERIOD 20 ns)

Run `final3_A` (repeat `final3_B`).

### 3.1 Signoff gate

| Check | Result |
|---|---|
| Magic DRC | 0 |
| KLayout DRC | 0 |
| Route DRC | 0 |
| LVS errors | 0 |
| XOR differences | 0 |
| Illegal overlaps | 0 |
| Antenna violating nets / pins | 0 / 0 |
| Hold violations (all corners) | 0 |
| EQY (OpenLane Yosys.EQY step, stock tool) | does NOT pass. final3_A: reaches the partition proofs, then './run.sh: grep: command not found' (the nix --pure shell hides grep; a launcher with grep on PATH is prepared, asic/run_pd_mk2.sh); final3_B: dies in Python shlex with an impossible AttributeError (the known machine fault, Incident 85). Earlier standalone EQY on final_B: 795 / 876 partitions, 80 fail on name matching (FSM re-encoding, combinational cut points) |
| FSM re-encoding by synthesis (4 FSMs, one-hot) | PROVED: RTL == RTL+fsm, 36,303 $equiv (equiv_make -encfile + equiv_induct); negative control (swapped codes) fails as required |
| Step A: RTL+fsm == N1 (synthesis state before abc -fast), Incident 89 | PROVED: register-mapped LEC, 19,881 outputs, 235 RTL-only flops proved constant, 4 one-hot invariants proved; the last 34 outputs (33x33 multiplier cone) closed by algebraic proof + substitution. Applies unchanged: the synthesis netlist of final3_A/B is byte-identical to final_A's (79aba67f) |
| Step B: N1 == final netlist of final3 (sha256 326cc257...), Incident 91 | PROVED, twice (netlists of final3_A and final3_B, byte-identical): 19,081/19,081 flops paired (3 N1-only flops are known duplicates), per-output SAT 0 counterexamples, 32 d_req_addr outputs (multiplier cone) closed by &cec (equivalent in 2-4 s; the AIGs of the two executions are byte-identical) |
| 33x33 signed multiplier | PROVED product[63:0] == signed33(A)*signed33(B) mod 2^64 for both sides (algebraic backward rewriting over Z/2^64 on the word-level maccmap networks, linked to the in-context cones by &cec; cell techmap semantics by SAT); negative controls fail as required |
| Step-B driver regression | the same script on the old final_B netlist reproduces the old step-B result (0 counterexamples, 32 residual outputs equivalent) |

Double execution: `final3_A` vs `final3_B` on 302 shared flow metrics: identical.

Equivalence status of the final netlist of final3 (FLOW_JOURNAL Incidents 86, 89, 91): RTL == RTL+fsm == N1 == final routed netlist, under register correspondence, with every auxiliary invariant proved, each proof step executed twice with identical results and negative controls where applicable. Caveats: the proof trusts the Yosys front end and techmap semantics; the SRAM macros are black boxes on both sides (their behaviour is covered by gate-level simulation: 12/12 Embench kernels on the final3 netlist with mcycle equal to the ASIC-view RTL); the stock EQY step of the flow does not pass (tool/environment, see first row).


### 3.2 Timing per corner (setup / hold worst slack, ns; Fmax = 1/(20 - WNS))

| Corner | Setup WS | Setup TNS | Setup violators | Hold WS | Fmax MHz |
|---|---:|---:|---:|---:|---:|
| nom_tt_025C_1v80 | +2.086 | 0.0 | 0 | +0.223 | >= 50 |
| min_tt_025C_1v80 | +2.274 | 0.0 | 0 | +0.228 | >= 50 |
| max_tt_025C_1v80 | +1.960 | 0.0 | 0 | +0.201 | >= 50 |
| nom_ss_100C_1v60 | -7.413 | -10690.5 | 2449 | +0.747 | 36.5 |
| min_ss_100C_1v60 | -6.425 | -8463.2 | 2322 | +0.752 | 37.8 |
| max_ss_100C_1v60 | -8.311 | -12871.2 | 2511 | +0.715 | 35.3 |
| nom_ff_n40C_1v95 | +4.703 | 0.0 | 0 | +0.043 | >= 50 |
| min_ff_n40C_1v95 | +4.842 | 0.0 | 0 | +0.045 | >= 50 |
| max_ff_n40C_1v95 | +4.603 | 0.0 | 0 | +0.030 | >= 50 |

SRAM macros are characterised at TT only (no ss/ff liberty exists for sky130_sram_1kbyte_1rw1r_32x256_8 in the PDK); ss/ff numbers use TT macro timing and are optimistic on paths through the SRAMs.

### 3.3 Area and power

| Quantity | Value |
|---|---|
| Die area (um^2) | 8120000 |
| Core area (um^2) | 7971210 |
| Std-cell area (um^2) | 1399590 |
| Macro area (um^2) | 2663850 |
| Std-cell count | 192005 |
| Utilization | 0.509765 |
| Wirelength (um) | 6597834 |
| Flow power metric `power__total` (W) — this is the max_ff_n40C_1v95 corner | 0.11550886183977127 |
| Vectorless power at nom_tt_025C_1v80: total / internal / switching / leakage (mW) | 102.05 / 83.02 / 18.74 / 0.295 |
| Vectorless power at nom_ss_100C_1v60: total / internal / switching / leakage (mW) | 86.53 / 70.92 / 14.45 / 1.158 |
| Vectorless power at nom_ff_n40C_1v95: total / internal / switching / leakage (mW) | 114.51 / 91.93 / 22.28 / 0.296 |

Vectorless = OpenSTA with default activity (combinational logic ~0 mW); the activity-based figure below uses the switching measured in gate-level simulation of each kernel.

### 3.4 Activity-based power (gate-level simulation of the final netlist -> SAIF -> OpenSTA, nom_tt)

Source: `gls_power_final3_A_power.csv`.

| Kernel | Total mW | Dynamic mW | Leakage mW | Energy / instruction pJ |
|---|---:|---:|---:|---:|
| crc32 | 114.60 | 114.31 | 0.295 | 2379 |
| depthconv | 110.61 | 110.31 | 0.295 | 3637 |
| edn | 115.43 | 115.13 | 0.295 | 2499 |
| fdct | 114.30 | 114.00 | 0.295 | 2991 |
| huffbench | 111.51 | 111.21 | 0.295 | 2840 |
| insertsort | 112.44 | 112.15 | 0.295 | 3092 |
| matmult | 113.78 | 113.48 | 0.295 | 2852 |
| md5sum | 112.24 | 111.95 | 0.295 | 3044 |
| mont64 | 112.24 | 111.95 | 0.295 | 2783 |
| sha256 | 113.69 | 113.40 | 0.295 | 2860 |
| tarfind | 112.28 | 111.98 | 0.295 | 2782 |
| wikisort | 112.81 | 112.51 | 0.295 | 3188 |

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
