# Project state and remaining work

| item | value |
|---|---|
| Audience | the project maintainer and owner; any agent working on the owner's machine. Read the whole file before running anything. |
| State as of | 2026-10-15 07:45 (+07) |
| Last edited | 2026-10-15 (restructured; content unchanged except where marked in the revision history) |
| Binding | everything below is binding unless the owner says otherwise in the session; `QUY_TRINH.md` wins on conflicts (report the conflict to the owner) |

Time convention: dates YYYY-MM-DD; times are local (+07) unless marked UTC (flow logs `asic/gated_pd.log`, `asic/dse_pd.log` use UTC).

## 0. Read first, in this order

1. `QUY_TRINH.md` - the binding procedures and rules (Vietnamese, ASCII).
2. This file - current state, running jobs, ordered task list with exact commands.
3. `NHAT_KY.md`: why every PD knob exists (section 8; PD infrastructure section 6) and known traps (section 9).
4. `RESULTS.md` (current numbers), `REVIEW_RESPONSE.md` (review items), `README.md` (layout).

## 1. Binding rules (short form; full text in QUY_TRINH.md)

**Scope and language**
- Work ONLY in `E:\Projects\RISCV-research` (4 KiB caches, 16 KiB RAM). The published repository `E:\Projects\RISCV-AHB-APB-UART` is
  READ-ONLY: read and take data from it, never write to it. Do not edit the paper.
- Replies to the owner: Vietnamese. Anything committed or pushed to git: English, ASCII only, no "Co-Authored-By" line, local git
  identity (user vutoan1110). Do not commit or push unless the owner asks.
- Project files: no first-person narration, no "the user said", no persona text, no references to any AI memory.

**Measurement discipline**
- Every measurement is executed twice and compared field by field (r1 = r2). A result is final only after that.
- Debug from evidence, one hypothesis at a time. A clearly random crash (native SIGSEGV, a corrupted Python object, WHEA error, random
  OOM, Quartus access violation ~8 %) may be retried unchanged; a deterministic failure (DRC, setup / hold, LVS, ...) needs an
  engineering fix. Do not blame the machine without independent evidence; the double execution decides.
- **Development vs acceptance (owner, revised 2026-10-14; supersedes the 2026-10-13 "never continue from a failed step"):** after a
  failure (crash, error, watchdog stop, FAIL gate), log FAIL + diagnosed cause, keep the folder, fix; resuming from the failing step
  is allowed during development. Once everything passes, ONE complete flow from step 1 (fresh tag, no resume / branch / CONTINUE,
  thresholds declared at launch) is required; only that clean run (and its double execution where required) is the result. If the
  flow is deterministic and the fix is a launch-time setting only, going straight to the clean run is allowed. Same for non-PD tools.
  Runs signed under resumes / branches (DM r14F_A/B, SA2 ecomaxmin) each need one clean full run.

**RTL**
- Current RTL: manifest `6c4ccffd` (`results/rtl_manifest.json`, `scripts/rtl_manifest.py`). Check with
  `python scripts/rtl_manifest.py --check`; WITHOUT `--check` the script REWRITES the manifest (only after an approved RTL change).
- One RTL for every flow (owner, 2026-10-14): every reported number must come from `6c4ccffd`; older results are historical until
  re-run (`results/rtl_consistency_audit_20261014.md`).
- Any RTL change carries the WHOLE chain in order (QUY_TRINH section C): apply by script -> freeze manifest -> lint / latch -> formal
  proof with negative control for restructurings -> full chain x2 (`scripts/run_fullchain_rfbht.sh`) -> Quartus 4 points x 10 common
  seeds x 2 passes (QUY_TRINH E) -> PD from step 1, double executed -> GLS + activity power. New logic needs new tests; nothing may be
  disabled to make a flow pass.
- PD never edits RTL. PD configs read RTL snapshots, never `hdl/`: since 2026-10-14 21:20 `asic/snapshots/rtl_rfbht` (= `6c4ccffd`).

**PD** (OpenLane 2.3.10 local copy `asic/openlane-local`, sky130A, 20 ns clock)
- Sign-off gate (hard): route DRC 0, Magic DRC 0, KLayout DRC 0, LVS 0 (every difference count), XOR 0, illegal overlap 0, critical
  disconnected pins 0, antenna nets / pins 0, setup >= 0 at EVERY tt and ff corner, hold >= 0 at EVERY one of the 9 corners. The ss
  corner is reported, not gated (it cannot close at 50 MHz without changing CPI, which is forbidden). Max slew / cap / fanout are NOT
  hard limits: report them by category (SRAM pins, diode-laden nets, standard cells); never pay large area to clear them.
- DM keeps its signed recipe (`asic/soc_dm_4kb/config_R14_FINAL.json`, floorplan grid3665x2900, 10.63 mm2); on `6c4ccffd` only
  `VERILOG_FILES` changes (`config_R14_FINAL_rtl6c4c.json`). The R14 runs r14F_A / r14F_B (= dm_grid3665x2900_r1 / _r2) are locked
  historical evidence: never modify or delete them.
- SA2 and DM_VC4: each optimised on its own, without copying DM's knobs or results (owner, 2026-10-13). Strict PPA: the minimum
  ROUTABLE die (proved by the next smaller candidate failing with the same recipe), then the fewest buffers, the least wire and the
  lowest power.
- Every change runs a FULL flow from step 1 to sign-off; diagnose at every phase and stop at a clear failure sign instead of waiting.
  One hypothesis per run; no parallel screening sprays. Branched runs (`asic/branch_run.sh`) are screening only.
- Gated drivers: `asic/run_gated_pd.sh` (new flow), `asic/run_gated_resume.sh` (planned pause, or development resume after a
  diagnosed failure), `asic/branch_run.sh` (screening). Every gate result and manual decision goes to `asic/gated_pd.log` as one line
  with its reason. SA2 / DM_VC4 recipes declare `P2_MIN_HOLD=-0.5` at launch and run both hold-ECO passes in one step
  (`POST_ROUTE_HOLD_ECO_RCX_CORNER_2` = "min_*"), so no branch or CONTINUE is needed.
- Never edit a script while it runs. Stop jobs cooperatively (`touch asic/.abort_gated_pd`: no new phases). Never kill a healthy run;
  a clearly failed run may be stopped only after its cause is found and logged. Never kill the owner's own processes.
- Quartus fits run sequentially; when two PD flows run, do not run Quartus together with the multi-lane verification chain. Heavy PD
  phases run one at a time (`asic/sequence_heavy_*.sh`): a sign-off part beside a detailed routing does not fit in the 24 GB WSL VM.

**Naming and records**
- Run tags: `<cfg>_<floorplan>[_<knob><value>...]_r<N>` (e.g. `vc4_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd_r1`). No numbered /
  AI-looking names (no R17, E17, final4, _v2, "Incident NN"); content + date names. Shorthand used in this file (E0, E1, V2..V5, J1..J3,
  T1..T14) is defined in `NHAT_KY.md` section 11.
- History: ONLY `NHAT_KY.md` (Vietnamese, ASCII), structured by topic since 2026-10-15 (one version; the hour-by-hour version is in
  git, commit `35ebf92`). New events go to its section 8a as `### YYYY-MM-DD HH:MM <subject>` and are merged into the topic sections
  at the next documentation pass; recurring issues section 9, cleanup section 10, renames section 11. Procedures: `QUY_TRINH.md`. Numbers: `RESULTS.md`. Review status: `REVIEW_RESPONSE.md`. Reader-facing results go to the
  report page (`report_page/soc_report.html`). Do not record the same issue in several places.
- Cleanup is mandatory, but deleting run folders needs the owner's explicit approval; archive first (`results/pd_run_archive/<run>/`:
  resolved.json, final metrics, error / warning logs, flow log, step list) and list every deletion in `results/cleanup_deleted.txt`.
- Reporting to the owner: Achievements, then Failures and gaps, with hard numbers; name the corner of every timing number; keep the
  timing corner separate from the power corner; state the power method (flow estimate / vectorless / activity-based); DRC / LVS as a
  pass/fail gate before the PPA table.

## 2. Machine and how to run things

- Windows 11, 32 logical CPUs, 31.6 GB RAM. Shells: Git Bash (Windows side: Questa, Python, Quartus) and WSL Ubuntu (OpenLane via nix,
  OpenROAD, Yosys, Magic, KLayout, netgen). WSL is capped at 24 GB RAM + 8 GB swap.
- Start WSL jobs from Windows: `wsl.exe -d Ubuntu -e bash -c "cd /mnt/e/Projects/RISCV-research/asic && ..."`. The WSL VM shuts down
  (killing every job, even nohup ones) when the last wsl.exe client exits: KEEP ONE WSL TERMINAL OPEN while PD jobs run; do not use
  detached / persistence tricks.
- Memory per job (measured): flow before DRT 5-8 GB; detailed routing ~10.5 GB (DM_VC4 up to 12.4 GB); Magic DRC / WriteLEF up to ~14 GB;
  KLayout DRC / XOR ~8 GB; post-route ECO ~10 GB; Questa GLS ~0.2-3 GB per job. Gated scripts wait for free memory (new flow >= 10 GB,
  detailed routing >= 12 GB and at most one other detailed routing).
- Watch `asic/gated_pd.log` with a polling loop (`wc -l` + `sed -n`); `tail -F` from Git Bash does not see lines written from WSL.
  Host progress monitor: `python -B scripts/maintenance/monitor_jobs.py --watch --output results/job_monitor_status.json` (polls every
  600 s; reports FAILED / DEAD_ALERT / UNKNOWN / HELD / suspected stall; never kills or retries). The old `scripts/watchdog.sh` targets
  synth4kb only and is not evidence of supervision.
- Windows-side Python tools run pinned to one logical CPU at process creation:
  `cmd /v:on /c "start /wait /b /affinity <hexmask> "" python ... & exit !ERRORLEVEL!"` (mask is HEX; plain `cmd /c start /wait`
  returns 0 regardless of the child's exit code). WSL processes cannot be pinned; PD results rely on r1 = r2.
- Questa: `C:/questasim64_2024.1/win64/vsim.exe`. PowerShell scripts that call `wsl.exe` with quoted bash commands need PowerShell 7
  (`pwsh`), not Windows PowerShell 5.1.

## 3. Current state (2026-10-15 07:45 +07)

### 3.1 Overview

| Area | State | Since | Evidence / details |
|---|---|---|---|
| RTL | `6c4ccffd` frozen, live tree `--check` IDENTICAL (227 files) | 2026-10-08 21:17 | section 3.2 |
| Verification on `6c4ccffd` | complete, double-executed (chain, UVM, ACT4 window, random + Spike, Embench, CoreMark CRC / sweep / standard) | 2026-10-08 .. 11 | `RESULTS.md` section 2 |
| Historical simulations re-run on `6c4ccffd` | running (M1/M2 sweep, A3, A4, A8, IRQ) | 2026-10-15 | section 4 |
| FPGA | ten common seeds x2 complete; 100 seed-2 SOFs ready | 2026-10-09 23:28 | `RESULTS.md` 4.1 |
| Board | 42 of 100 cases measured (single pass), all equal to both RTL reference passes; 58 left | 2026-10-13 | section 3.3 |
| ASIC DM | R14 layout signed off (historical, rule-of-2026-10-14 non-compliant); `6c4ccffd` r1 failed p1 margin gate, r2 running | 2026-10-15 00:18 UTC | section 3.4 |
| ASIC SA2 | R14 layout signed off (historical); `6c4ccffd` r1 failed macro placement (fixed), r2 running | 2026-10-15 00:18 UTC | section 3.5 |
| ASIC DM_VC4 | not signed off; deferred by the owner, to be rebuilt on `6c4ccffd` | 2026-10-14 21:20 | section 3.6 |
| LEC | DM and SA2 complete vs `rtl_r14` gold; DM_VC4 synthesis part done; `6c4ccffd` LEC scripts prepared | 2026-10-15 | section 3.7 |
| Activity power | DM and SA2 exact window done on R14 layouts | 2026-10-14 | `RESULTS.md` 5.1, 5.2 |
| Report page | source `report_page/soc_report.html`, Version 9 (2026-10-14 21:30), hosted copy updated by republishing | 2026-10-14 | `report_page/README.md` |
| Git | research state committed on 2026-10-15 (commits `2d4202d`, `3a924a9`, `d0d2a35`) | 2026-10-15 | `git log` |

### 3.2 RTL and verification

- Functional revision: RAM 16 KiB, register file and BHT in M9K on the FPGA view, optional FAST_HIT. R14 / R15 / R16 are legacy
  aliases; the M9K change is later than R16 (`WORKSPACE_MAP.md` describes every source folder and proof boundary).
- `6c4ccffd`: register file and BHT moved into M9K on the FPGA view only (cycle-exact). Proofs: k-induction 3/3 with negative
  controls; sim-only checkers; full chain 0 failures (`results/fullchain_rfbht.log`); ACT4 43/43 x2. ASIC boundary: the `6c4ccffd`
  synthesis netlist is byte-identical to R16 (sha256 `da06d38f`), not to the R14 PD synthesis (sha256 `fc555d6b`).
- Supplemental verification (all on `6c4ccffd`, double-executed): UVM 48 paired cases (`results/uvm_cache_uart_20261009/verification.json`);
  corrected architecture adapter (`scripts/verification/run_architecture_window.py`, `results/architecture_window_20261009/verification.json`);
  hardened random runner, 50 seeds, 43 positive/negative controls (`results/random_diff_checked_20261009/verification.json`,
  `results/verification_runner_controls_20261009/verification.json`; the full-chain caller retains the random process return code
  through its pipe); Spike comparison 2026-10-11 (100 Spike executions vs 200 RTL traces, 7,105 retirements per pass, 300 wrong-trace
  controls; the adapter invokes the installed Spike engine directly at PC 0 with the DUT's zero GPR / data initialisation and
  implements no ISA semantics; `results/spike_random_reference_20261011/receipt.json`).
- CoreMark: canonical CRC check of 6 base + 5 FAST_HIT points (22 simulations; `results/coremark_crc_checked_20261009/verification.json`,
  `results/coremark_canonical_checked_20261009/verification.json`); 92-point sweep (184 simulations, 36 runner controls, independent
  verifier 241 inputs / 379 artefacts / 26 controls; `results/coremark_sweep_crc_20261010/verification.json`,
  `results/coremark_sweep_crc_independent_audit_20261010/receipt.json`); standard-duration matrix 16/16 (two byte-identical firmware
  builds `results/coremark_standard_apb_build_pair_20261011.json`; 108 scalar fields per pair, 864 comparisons;
  `results/coremark_standard_apb_matrix_20261011/receipt.json`, `cases.csv`, `performance_paired.csv`). Simulation RAM 32 KiB; not an
  official score.
- Extended conflict probe done (390 windows, both runs identical, `results/conflict_probe.csv`).

### 3.3 FPGA and board

- Initial Quartus subset (4 points x 4 seeds x 2 passes, `results/fpga_points_rfbht_p{1,2}.csv`): DM 12,810-12,842 LE, DM_DSE
  14,308-14,364, SA2 16,675-16,739, DM_VC4 17,130-17,139; Fmax 51.96-55.52 MHz (Slow 85C). SA4 and the 8 KiB points were NOT refitted.
- Ten common seeds (complete 2026-10-09 23:28): all 40 point/seed rows agree on 115 hardware fields in both passes; DM / SA2 / DM_VC4 /
  DM_DSE use identical seeds 1..10; seed 2 was refitted independently in both passes and fixed for the board. Sources:
  `results/fpga_common_seeds_continued_20261009_ppa.{json,md}` and the paired CSVs / seed summaries.
- Board preparation: 100 SOFs (RTL `6c4ccffd`, seed 2) in `output_files_board_matrix_6c4ccffd_seed2/`; INDEX.csv binds expected
  cycles / instructions and hashes; canonical MIF restoration PASS. The old matrix `output_files_board_matrix_r14/` (RTL `3ea52396`) is
  OBSOLETE for the board. CoreMark RAM-32 KiB images are not part of this RAM-16 KiB set.
- Physical session 2026-10-13 (owner-supervised; scope: ONE physical pass of 100 cases, replacing the earlier two-pass plan; all other
  measurements keep the two-execution rule):
  - Setup: USB-Blaster USB-0 programs the EP4CE115; Hercules 3.2.8 (`tools/hercules`), CP210x COM3, 115200 / 8N1 / handshake OFF, JP5
    GPIO 3.3 V TX = AB22 / RX = AC15 (the RTL divider gives 448 clocks/bit, ~111,607 baud). UART smoke passed all 28 fields.
  - Measured 42 cases = 4 ramsweep + 9 complete kernels x 4 configurations + statemate on DM and SA2; every complete UART log matches
    both RTL reference passes; 41 HEX/LED display read-backs confirmed; independent re-check 42/42
    (`results/board_20261013_independent_check/`).
  - Remaining 58 cases: 10 short (statemate DM_VC4 / DM_DSE, tarfind x 4, ud x 4) and 48 full-iteration.
  - Live state: `results/board_20261013/session.json`; read it, `runlist.csv`, `results.csv` and the observation / UART / programming
    evidence before any action. Pass-2 rows stay marked `NOT_SCHEDULED_SINGLE_PASS_SCOPE`. Each case requires explicit display review
    and confirmation before the next programming, reset or rerun; a planned `next_case` never authorises execution. Repeated boots
    after a manual reset are not another independently programmed pass. Helpers: `hercules_case_ui.py` (configure / flush logging, no
    board operations), `record_board_case.py` (validates one case offline; `--sync-tracking` updates the records and appends one event to `NHAT_KY.md`
    section 8a, located by the `## 8a.` / `## 9.` headings),
    `program_board_case.ps1` (plan-only unless `-Program`), `check_board_uart.py` (28 numeric UART fields).
  - Earlier preparation folder `results/board_20261012/` (readiness.json, runlist / results templates, README documenting the JP5 UART
    and the immediate boot) is historical.

### 3.4 ASIC DM

- **Historical signed layout** [R14]: r14F_A / r14F_B (= dm_grid3665x2900_r1 / _r2), double executed, final netlists byte-identical
  (sha256 `83f38f7e...` for both fill-insertion netlists). Activity power exact window done (`results/activity_power_exact_dm_20261013/receipt.json`);
  LEC complete with premises (`RESULTS.md` 5.1).
- **Rule audit (2026-10-14):** NOT compliant as executed. The session end of 2026-09-30 ~23:38 UTC killed both runs; both were resumed
  on 2026-10-02 with `run_resume_retry.sh` (r14F_A after its uninterrupted flow through step 59, resumed at the Magic streamout, i.e.
  only GDS and DRC / LVS / XOR; r14F_B inside detailed routing, step 46 killed, routed again from step 47).
- **Clean-run attempts on R14 (2026-10-14):** `dm_grid3665x2900_r3`: OpenLane segfault right after step 40, STOP after P2 (random).
  `dm_grid3665x2900_r4`: P1 PASS (+2.164 / +0.184), P2 PASS (overflow 0, STAMidPNR-3 +1.725 / +0.186); not byte-identical to r14F_A
  (two buffers `wire10760` / `wire10761` with swapped S / FS orientation in the step-41 DEF; RepairAntennas then 350 nets / 6,249 diodes
  vs 322 / 6,262); stopped at its DRT gate 14:11 UTC when PD moved to `6c4ccffd`.
- **`6c4ccffd`:** `dm_grid3665x2900_rtl6c4c_r1` p1 FAIL (STAMidPNR-2 setup nom_tt +0.307 ns < `P1_MIN_SETUP` 0.5; 71,006 cells vs R14
  70,441; worst post-CTS path is the half-cycle RAM bank[3] -> D$ data-bank refill; R14 worst +2.164 on an I$ path).
  `dm_grid3665x2900_rtl6c4c_r2` running with `P1_MIN_SETUP=0 P2_MIN_SETUP=0` declared at launch; sign-off gate unchanged.

### 3.5 ASIC SA2

- **Historical signed layout** [R14]: 11.56 mm2 (3400 x 3400, `macro_placement_u2fg.cfg`), runs
  `sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1` / `_r2`: 319/319 metrics identical, final netlist and DEF
  byte-identical, SPEF identical except `*DATE`. Numbers: setup max_tt +0.838, nom_tt +1.118, ff >= +3.803 ns; hold worst +0.020
  (min_ff / max_ff); ss -6.72..-7.92; std cells 1.4711 mm2 (215,979); wire 9.274 m; vectorless nom_tt 121.99 mW
  (`results/asic_compare_dm_sa2_20261009.md`). Activity power: first evaluation 2026-10-09 08:14 UTC (12/12 kernels, two OpenSTA
  executions; `_power_p1.csv`, `_power_p2.csv`, `_power_verification.json` under the SA2 tag); exact window 2026-10-14 (mean 129.64 mW,
  EPI GM 4,317 pJ; `results/activity_power_exact_sa2_20261014/receipt.json`). LEC complete 2026-10-14 (two executions,
  `results/lec_sa2_20261013/pass_comparison.json`; NegB 60 SAT).
- **Historical recipe:** `config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf.json` as a full flow (p2 gate stopped on hold
  nom_tt -0.206 and was continued with a CONTINUE line), then `branch_run.sh` after PostRouteHoldECO (step 47) and a second hold ECO
  with `config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomin.json` (`POST_ROUTE_HOLD_ECO_RCX_CORNER` min_*). Rule audit
  (2026-10-14): NOT compliant as executed (source runs `_rsztf_r1/_r2` failed the final gate on hold nom_ff -0.023 / min_ff -0.027;
  `_ecomaxmin` are branches after step 47; `_ecomaxmin_r1` was also resumed at step 52 after a random CPython crash in
  `Odb.ReportDisconnectedPins`, `crashed-52-...` kept). The compliant form is E0 = the same recipe as one flow (`_rsztf.json` +
  `POST_ROUTE_HOLD_ECO_RCX_CORNER_2` + `P2_MIN_HOLD`), checked byte-identical to the branch procedure on the step-47 state.
- **E1 (`..._rsztf_cts25`, CTS clustering 8 -> 25):** r1-r4 failed for non-design reasons (SIGSEGV GRT step 41; MemoryError step 51
  beside a DM_VC4 DRT; SIGSEGV antenna check step 43; Tcl panic step 34), each failing step replayed cleanly. r5 [R14]: P1 / P2 identical
  to earlier attempts (STAMidPNR-3 +0.959 / +0.182 vs signed recipe +1.057 / -0.206); DRT + hold ECO route DRC 0; step 51 SIGSEGV; sign-off
  part re-run from step 51 (development). On 2026-10-14 22:30 still in its sign-off part (a stop request was refused by the permission
  system; the owner may stop it with `wsl -d Ubuntu -e pkill -f "sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25_r5"`).
  Its final gate is not recorded here. Recipe choice E1 vs ecomaxmin: `scripts/metrics/compare_signoff_runs.py` (checked twice on known runs).
- **Minimality [R14]:** 10.54 mm2 FAILED (max_tt -0.573); 11.05 mm2 failed P2 twice (`results/sa2_minimality_screen_20261011_pair.json`);
  11.305 mm2 CLOSED as FAILED 2026-10-13 (post-ECO incremental route stalled at 24 violations, then SIGSEGV). Minimality not proved.
- **`6c4ccffd`:** `sa2_..._rsztf_eco2_rtl6c4c_r1` (`soc_sa2_4kb/config_..._rsztf_eco2_rtl6c4c.json` = E0 + snapshot sources) failed step 16
  ManualMacroPlacement: from R15/R16 the cache macros are `u_soc.u_{i,d}cache.genblk1.g_dse.*`; fixed with
  `soc_sa2_4kb/macro_placement_u2fg_rtl6c4c.cfg` (8 names, coordinates equal, 16/16 checked against the netlist).
  `sa2_..._rsztf_eco2_rtl6c4c_r2` running (E0 thresholds + `P1_MIN_SETUP=0`).

### 3.6 ASIC DM_VC4

- Not signed off on any RTL. Root causes measured (`NHAT_KY.md` section 8.3): (a) on 11.56 mm2 the D$ victim buffer + D$ tag cluster
  congest the corridor at the D$ macro edge; FastRoute runs GRT-0103 "Extra Run for hard benchmark" (fires at congestion iteration 20
  when overflow > 200; OpenROAD `edf00dff`) and clock-tree trunks detour 3-7 mm -> hold skew -2.7 .. -4.8 ns -> 1,675-2,088 hold
  endpoints at p2 (SA2: 19); every full global route (including the one inside `OpenROAD.RepairDesignPostGRT`) re-rolls this clock
  routing; (b) on the padded 12.24 mm2 die the main route reaches 0 DRC but the post-route antenna repair does not converge (V2: 1,031
  nets; replay 225 violations at iteration 43-44, 1-3 % per iteration); both caches' read-data pins face the 220 um channel between macro
  rows. Rejected levers: cell padding alone, 150 GRT iterations, die 3500 / 3800, clock trunks on met3 / met4-met5, GRT antenna margin
  10 / 20 / 30 %, max wire 500 um (V5: p2 setup -1.07 / hold -1.88), 3800 die (V4: 821 nets vs 742).
- Owner decision 2026-10-14: V4 stopped at 14:01 UTC; DM_VC4 deferred; rebuild from `6c4ccffd` with a DM_VC4-own floorplan (read pins
  away from the centre band) and the macro rename of SA2.

### 3.7 LEC and activity power

- The stock OpenLane EQY step does not pass on this design (tool limits). Custom register-mapped LEC:
  - DM [R14 gold]: legacy chain `asic/equiv/lec/run_lec_r14.ps1` (-Step A / B), `run_lec_r14_mul.ps1`, `run_lec_r14_pass2.ps1` (pwsh 7)
    with SAT / CEC / algebra / negative evidence; premises closed 2026-10-13/14 (asynchronous reset, undefined values, invariant bridge,
    clock); details `RESULTS.md` 5.1.
  - SA2 [R14 gold]: complete, two executions, all negative controls (`asic/equiv/lec/run_lec_sa2.ps1`).
  - DM_VC4 [R14 gold]: synthesis part (front end gold / N1, A, NegAlign, Mul, Inv, NegFSM, xsens) DONE 2026-10-14 in two complete
    executions (`results/lec_vc4_20261014d/`; attempts a / b / c stopped on the way-1 SRAM interface, the AIGER port order and an
    over-strict t1 check, all fixed); B / NegB / reset and clock audits after sign-off (`prepare_vc4_lec.py --add-gates`).
  - `6c4ccffd`: `scripts/verification/prepare_lec_6c4c.py`, `scripts/maintenance/run_lec_6c4c_goldn1.sh`,
    `asic/equiv/lec/compare_lec_vc4_goldn1.py --no-negalign` added 2026-10-15 (commit `d0d2a35`); the gold must come from `rtl_rfbht`.
- Activity power: DM and SA2 exact window done on the R14 layouts (`RESULTS.md` 5.1, 5.2); redo on the accepted `6c4ccffd` layouts.

## 4. Running jobs and queue (2026-10-15 07:45)

Check the current queue receipts and `asic/gated_pd.log` before starting anything.

| Job | Started | What | Stop |
|---|---|---|---|
| `asic/sequence_heavy_20261015g.sh` | 2026-10-15 00:18 UTC | `dm_grid3665x2900_rtl6c4c_r2` then / beside `sa2_..._rsztf_eco2_rtl6c4c_r2`; one heavy phase at a time | cooperative abort flag of the sequence; `asic/.abort_gated_pd` |
| M1/M2 sweep on `6c4ccffd` | 2026-10-15 | `scripts/m2/rerun_m2_6c4ccffd.py` -> `results/m2_6c4ccffd/` (650 base + 572 FAST runs per pass), Windows below-normal priority | - |
| A8 / A3 / A4 / IRQ on `6c4ccffd` | 2026-10-15 | `scripts/maintenance/rerun_review_sims_6c4ccffd.py` -> `results/review_sims_6c4ccffd/` and `results/*6c4ccffd*` (old results untouched; `comparison.json` in each folder at the end) | - |
| SA2 E1 `..._cts25_r5` (R14) | 2026-10-14 | sign-off part; status after 22:30 not recorded | owner command in section 3.5 |

Finished historical jobs (handover of 2026-10-09 06:40 UTC): J1 (DM_VC4 3600 detailed routing) stopped by the convergence watchdog
2026-10-09 07:28 UTC (iteration 10: 5,689 > 5,000; `results/vc4_corr3600x3400_drt_diagnosis_20261009.json`,
`results/vc4_corr3600x3400_drt_region_20261009.log`); J2 (SA2 GLS) 12/12 PASS, activity power verified 08:14 UTC
(`results/sa2_activity_power_20261009_p{1,2}.log`); J3 (SA2 synthesis replay with one snapshot hook,
`asic/equiv/lec/synth_replay_r14/sa2_rsztf_r1_n1only/`) byte-identical to step 06, so its `n1_pre_abc_fast.il` is OpenLane's exact N1
(the 4-hook replay differed: 77,157 vs 77,562 cells).

## 5. State log (newest first)

| When | Event |
|---|---|
| 2026-10-15 07:45 | first `6c4ccffd` attempts both stopped on 2026-10-14 evening (DM p1 margin; SA2 macro names); second attempts running since 00:18 UTC; historical simulations re-executed x2 on `6c4ccffd`; dmuA / dmuB deleted after archiving (owner); owner-side provenance audit `results/rtl_provenance_audit_20261014/report.md` agrees with `results/rtl_consistency_audit_20261014.md` and lists documentation mismatches (fixed 2026-10-15) |
| 2026-10-14 22:30 | owner: finish PD before any page edit; one RTL for every flow; delete failed PD runs. RTL consistency audit; SA2 / DM_VC4 wrappers frozen into `rtl_rfbht` (47 files). SA2 acceptance on `6c4ccffd` queued (`asic/sequence_heavy_20261014f.sh`, DM then SA2 heavy phases). Cleanup `scripts/maintenance/archive_and_delete_failed_pd_20261014.sh`: 43 failed / stopped / screening PD dirs, ~125 GB (`results/pd_run_archive/20261014/`, `results/pd_run_archive/archive_and_delete_20261014.log`) |
| 2026-10-14 21:20 | OWNER DECISION: PD on `6c4ccffd`; PD reads `asic/snapshots/rtl_rfbht` (44 files checked byte-identical to the live tree twice; `rtl_manifest.py --check` IDENTICAL). V4 stopped 14:01 UTC; DM_VC4 deferred. `dm_grid3665x2900_r4` stopped at its DRT gate 14:11 UTC. DM acceptance `dm_grid3665x2900_rtl6c4c_r1` started 14:12 UTC (`asic/sequence_heavy_20261014e.sh`) |
| 2026-10-14 18:30 | `dm_grid3665x2900_r3` STOP after P2 (segfault after step 40); `dm_grid3665x2900_r4` started 11:14 UTC (P1 / P2 PASS, not byte-identical to r14F_A). SA2 E1 r5 step 51 SIGSEGV, sign-off part re-run from step 51. V4 detailed routing since 10:33 UTC. Heavy-phase lock `asic/sequence_heavy_20261014d.sh` |
| 2026-10-14 16:15 | DM_VC4: V2 recipe does not converge in the post-route antenna re-route; V3 stopped before DRT; V5 FAIL p2. SA2 exact-window power done; SA2 LEC complete (NegB 60 SAT); DM_VC4 LEC synthesis part done x2 (`results/lec_vc4_20261014d`). Order (owner): shorter tasks first (`asic/sequence_heavy_20261014b.sh`) |
| 2026-10-14 09:50 | owner revises the 2026-10-13 rule (development may resume; acceptance = one clean full run) |
| 2026-10-14 08:40 | DM_VC4 V2 FAILED (main route 0 at iteration 31; post-DRT antenna 1,031 nets; watchdog); SA2 E1 r4 random Tcl panic (step 34); LEC DM_VC4 attempt a stopped (way-1 SRAM interface), fixed by `sram_align.py` + `NegAlign` |
| 2026-10-14 00:55 | V2 running (17:41 UTC); SA2 E1 failed three times for non-design reasons; DM_VC4 antcong_r1 FAILED (antenna re-route, 5,920 diodes, watchdog); SA2 LEC complete x2 (p1, p2b); drafts `results/review_status_20261014.md`, `results/extensions_vs_published_1kib_20261014.md` |
| 2026-10-13 19:20 | SA2 E1 and DM_VC4 antcong launched (`asic/gated_queue_20261013_sa2cts25_vc4antcong.log`; env `G5_UNLIMITED_LATE_PHASE=1 P2_MIN_SETUP=0 P2_MIN_HOLD=-0.5 P2_INITIAL_GRT_FALLBACK=1`); SA2 11.305 mm2 closed as FAILED; IPDT 4.5 PASS (`results/health_20261013_recheck/ipdt_4.5/`); board 42 cases done and re-checked |
| 2026-10-13 15:20 | `.abort_gated_pd` removed 14:54 (the 05:45 full stop was too broad); host re-check: unpinned Python probe Windows 2-6/8, WSL 0/8; pinned Windows 71/72; native SHA-256 8/8; ruled out: project scripts, Python installs, a game anti-cheat driver (removed 05:36), power plan, background load (`results/health_20261013_recheck/`). DM exact-window power DONE (pinned run, 14:56) |
| 2026-10-13 05:20 | SA2 11.305 P4 died 2026-10-12 11:40 UTC in step 47 (post-ECO incremental route stalled at 24 violations, native SIGSEGV; `crashed-47-openroad-postrouteholdeco` kept); DM exact-window capture pair VERIFIED, STA stopped on its memory guard (Windows 5,323 < 6,000 MiB); queue `scripts/maintenance/queue_dm_power_sa2_eco_retry.sh` (`results/queue_dm_power_sa2_eco_retry_20261013.log`); DM_VC4 antenna-congestion hypothesis prepared (`config_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_antcong.json`) |
| 2026-10-12 18:03 | DM exact GLS pass 2 continuation (Errno22 on a TT library read through wsl.localhost; 16 native commands exit 0; resumed same private compilation; `results/gls_exact_dm_p2_continuation_20261012/`); SA2 11.305 step 46 done (route DRC 0, antenna 0, placement 0; `results/sa2_minimality_screen_20261011_3325/detailed_routing_audit_20261012.json`); P4 queued behind 15,000 MiB |
| 2026-10-11 14:42 | DM exact GLS pass 2 stopped after 6 cases (Windows SAIF conversion TypeError); unchanged conversion replay byte-identical (`results/gls_pin_conversion_retry_20261011/receipt.json`); fresh pass 2 started (`results/gls_exact_dm_full_p2_retry_20261011/receipt.json`, pipeline `results/exact_power_queue_dm_retry_20261011.json`, `scripts/maintenance/run_dm_capture_power_retry.ps1 -Run`); host monitor started |
| 2026-10-11 03:19 | DM_VC4 padded 3600 candidate: main DRT DRC 0, first post-DRT antenna repair ended with fatal GRT-0232 (2,243 nets / 3,211 pins, 5,978 diodes; `results/vc4_postdrt_antenna_failure_20261011.json`) |
| 2026-10-11 03:43 | SA2 11.305 mm2 P2 PASS (+0.762 / +0.045), held before DRT (`results/sa2_minimality_screen_20261011_3325/first_execution_audit.json`, queue `results/sa2_minimality_queue_20261011.json`) |
| 2026-10-10 20:35 | SA2 11.05 mm2 second full flow failed P2 identically (pair receipt `results/sa2_minimality_screen_20261011_pair.json`; first execution `results/sa2_minimality_screen_20261010/first_execution_audit.json`) |
| 2026-10-10 07:47 | DM_VC4 padding candidate launched by `scripts/maintenance/queue_vc4_padding.py` (219 inputs; receipt `results/vc4_padding_queue_20261010/receipt.json`); post-CTS signal 11 preserved in crashed-37, unchanged retry passed (`results/vc4_postcts_crash_20261010.json`); P1 PASS, P2 small hold FAIL continued (`results/vc4_padding_initialgrt_20261010/p2_inspection.json`, `p2_path_diagnosis.json`) |
| 2026-10-10 02:00 | DM second STA power pass verified (`results/dm_activity_power_second_pass_20261010.json`) |
| 2026-10-09 23:28 | FPGA ten common seeds complete; 100 seed-2 SOFs built and audited (continuation `scripts/fpga/continue_common_seed_preparation.py`, `results/fpga_common_seeds_continued_20261009_{progress,plan}.json`; earlier stopped receipts kept, e.g. `results/board_preparation_interrupted_20261009_1541/EVIDENCE.json`, `results/board_preparation_6c4ccffd_seed2_20261009.{json,log}`, `results/paired10_6c4ccffd_20261009.log`) |
| 2026-10-09 17:59 | board reference: 100 paired rows (200 cases) equal to R14 on `6c4ccffd` (`scripts/fpga/prepare_board_reference.py`, tag `board_reference_6c4ccffd_20261009`); audit of 200 raw simulations `results/embench_gls_evidence_audit_20261010/receipt.json` |
| 2026-10-09 06:40 UTC | handover (`HANDOVER_CODEX.md`, now this file) |

## 6. Ordered task list

### 6.1 Order of work

Owner directives: 2026-10-13 work sequentially, writing-relevant parts first (board; SA2 / DM_VC4 PD optimised separately; LEC SA2 /
DM_VC4; review status; extension list); 2026-10-14 shorter tasks first, finish PD before any page edit, one RTL for every flow;
2026-10-15 re-run the older-RTL simulations now, in parallel, at below-normal priority.

1. T13 PD acceptance on `6c4ccffd` (DM, SA2) - running.
2. T14 historical simulations on `6c4ccffd` - running.
3. T8 / T3 LEC and activity power on the accepted `6c4ccffd` layouts.
4. T6 final PPA table.
5. T7 remaining board cases (owner schedules the session).
6. T4 SA2 minimality on the accepted recipe.
7. T1 / T2 / T5 DM_VC4 (deferred by the owner).

### 6.2 Tasks

**T13. PD acceptance on `6c4ccffd` (DM, SA2)**
- DM: signed recipe with only `VERILOG_FILES` changed (`soc_dm_4kb/config_R14_FINAL_rtl6c4c.json`). r1 failed the p1 margin gate
  (+0.307 < 0.5); r2 declares `P1_MIN_SETUP=0 P2_MIN_SETUP=0` at launch (sign-off gate unchanged). Acceptance: sign-off gate + PPA
  comparison with r14F (not the hash: the netlist differs from R14). Which DM layout is reported as the chip is the owner's decision.
- SA2: E0 recipe + `rtl_rfbht` + renamed macro placement (`config_..._rsztf_eco2_rtl6c4c.json`, `macro_placement_u2fg_rtl6c4c.cfg`);
  choose E0 vs E1 with `scripts/metrics/compare_signoff_runs.py` once E1 has a final gate.
- Then a double execution (r1 vs r2 comparison as in T2), GLS, exact-window power (T3) and LEC with gold from `rtl_rfbht` (T8).

**T14. Historical simulations on `6c4ccffd`**
- M1/M2 sweep, A3 cross-validation, A4 overlap, IRQ latency, BP on/off (drivers in section 4); compare with the historical CSVs
  (`comparison.json`); update `RESULTS.md` / `REVIEW_RESPONSE.md` labels from [historical] to [current] only after both passes match.
  The CoreMark R16 baseline (`results/coremark_r16_4kb_p{1,2}.csv`) is historical only; re-run only if still cited.

**T1. DM_VC4 sign-off** (deferred, owner 2026-10-14)
- Rebuild from `6c4ccffd` with a DM_VC4-own floorplan (read pins away from the centre band) and renamed cache macros. Do not resume or
  repeat any failed R14 recipe unchanged; a new experiment needs an evidence-based written hypothesis.
- Procedure once a recipe is chosen: full flow with `P2_MIN_HOLD=-0.5`, `POST_ROUTE_HOLD_ECO_RCX_CORNER_2` = "min_*" and, when post-GRT
  design repair is off, `P2_INITIAL_GRT_FALLBACK=1`; `G5_UNLIMITED_LATE_PHASE=1` (and `G5_ANT_ROUND_RULES=1` with declared thresholds
  if needed). Setup < 0 at a tt or ff corner: never relax SDC or clock; diagnose the path first (`max.rpt` of the STAPostPNR corner,
  `asic/sta_query/`); the post-route ECO has a setup mode (`POST_ROUTE_ECO_SETUP`, `POST_ROUTE_ECO_CORNERS` = tt only,
  `POST_ROUTE_ECO_HOLD` false, then a separate hold pass) that can resize but not buffer. If the hold count after detailed routing is in
  the thousands, stop, compare the GRT guides with `asic/fp_tools/clock_detour.py <def> <guide>` and `clock_layers.py <guide>`, and
  report to the owner. Acceptance: "SIGNOFF CLEAN <tag>" in `gated_pd.log`.
- Historical preparation (R14, 12.24 mm2 padding hypothesis): `results/vc4_padding_hypothesis_20261009.md`,
  `results/vc4_padding_preparation_20261009/inputs.json`.

**T2. DM_VC4 double execution** (after T1)
- Second full flow from step 1 with the accepted recipe, e.g.
  `P2_MIN_SETUP=0 ITEMS='soc_vc4_4kb:<tag>_r2:<config>.json' bash run_gated_pd.sh` (config path relative to the design dir).
- Compare r1 vs r2: every metric (merge of all `*/state_out.json` in step order, excluding runtime / flow__), sha256 of the first GRT
  guide, of the final netlist and DEF (`*-openroad-fillinsertion/soc_asic_top.nl.v / .def`); SPEF may differ only in `*DATE`.
  `scripts/metrics/asic_compare.py DM=... SA2=... DM_VC4=<r1>:<r2>` writes the table.

**T3. Activity-based power** (DM / SA2 on `6c4ccffd` after T13; DM_VC4 after T2)
- Exact window required: new private compilation per pass; elapsed time = TB cycle count x 20 ns = MCYCLE x 20 ns and every SAIF span
  checked before paired STA; the mapped counter-freeze observer must be proved on the exact netlist (as in
  `results/mapped_counter_freeze_checked_20261010/{verification.json,independent_review.json}`: 65 obligations per design).
- Capture: `scripts/verification/run_gls_exact_window.py` (opt-in `--wait-for-memory`); legacy driver
  `JOBS=2 bash asic/gls/run_gls_power_cfg.sh <netlist> <tag> results/dse_asic_view_p1.csv <CFG> [kernels...]`; if a run dies, re-run
  only the kernels without a "GLS_RESULT" line, then `bash asic/gls/gls_power_csv_rebuild.sh <tag> results/dse_asic_view_p1.csv <CFG>`.
- STA (PowerShell 7): `pwsh -File asic\gls\power_cfg.ps1 -Design <dir> -Tag <tag> -Step <NN>-openroad-stapostpnr -Fill <NN>-openroad-fillinsertion
  -RefCsv results\dse_asic_view_p1.csv -Config <CFG> -Pass 1`, then `-Pass 2`; verify with
  `python scripts/metrics/verify_activity_power.py --tag <tag> --design <dir> --step <NN>-openroad-stapostpnr --ref-csv results/dse_asic_view_p1.csv --config <CFG>`.
  The historical SA2 example used tag `sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1`, step 59, fill 56.
- Paired STA starts only after the complete capture pair passes its strict verification and Windows free >= 7,000 MiB.
- SAIF -> pin conversion runs in Windows Python (pinned); method notes and traps: `NHAT_KY.md` sections 5 and 9.

**T4. SA2 minimality** (rule: the next smaller die must fail with the same recipe)
- Historical ladder [R14]: 10.54 mm2 FAILED (max_tt -0.573), 11.05 mm2 failed P2 twice, 11.305 mm2 passed P2 once and failed at the
  post-ECO route (closed 2026-10-13), 11.56 passes. Redo on the accepted `6c4ccffd` recipe.
- Configs (`config_corr3400x3250_f220_capm20_fo16_pad1_tdp_clkm3_rsztf.json`, `..._3325_...`): generated by `asic/fp_tools/prepare_sa2_minimality.py` (receipt `results/sa2_minimality_preparation_20261009.json`; changes
  only `DIE_AREA`, `CORE_AREA`, `MACRO_PLACEMENT_CFG`; 16 macros inside the core, no overlap). 3400 x 3250: `DIE_AREA` [0,0,3400,3250],
  `CORE_AREA` [12,12,3388,3238], `macro_placement_corr3400x3250_f220.cfg`; 3400 x 3325: [0,0,3400,3325], [12,12,3388,3313],
  `macro_placement_corr3400x3325_f220.cfg`. Regenerate the placements with the `genblk1` macro names for `6c4ccffd`. A smaller-die
  failure used as proof also needs two independent full flows.

**T5. DM_VC4 minimality** (after T2)
- Prepared for the old 3600 pad1 recipe only (`results/pd_minimality_preflight_20261010.{md,json}`; 3500 pad1 configs and
  `macro_placement_corr3500x3400_f220_pad1.cfg`); rederive for the accepted recipe. Before DRT, measure the first-GRT skew from the
  actual completed directory with `bash fp_tools/grt_skew_screen.sh soc_vc4_4kb <run> <config> <run>_grtskew_scr`: hold skew around
  -2.0 ns and a few hundred endpoints = continue; thousands = clear failure, stop with a logged reason.

**T6. Final PPA table for DM / SA2 / DM_VC4**
- Verified subset [R14]: `results/asic_ppa_verified_subset_20261010.md` / `.json` (`scripts/metrics/asic_ppa_audit.py`; 319 metric fields,
  nine corners, buffer classes, DEF census, verified power; 17 evidence-rejection controls). Regenerate on the `6c4ccffd` layouts.
- Content per configuration: sign-off gate first; die and core area; std-cell area and count; buffers by class (timing repair, clock,
  hold, macro-pin); wirelength; setup / hold WNS with corner names; dynamic + leakage power from OpenSTA with SAIF (nom_tt, RCX),
  vectorless for reference; the knobs each design used and why; Embench CPI and I$ / D$ hit rates (FPGA view,
  `results/unified_metrics.md`, `scripts/metrics/unified_table.py`).
- Generator: `python scripts/metrics/asic_compare.py DM=soc_dm_4kb:<r1>:<r2> SA2=soc_sa2_4kb:<r1>:<r2> DM_VC4=soc_vc4_4kb:<r1>:<r2> --out results/asic_compare_<date>.md`.
- State honestly that knobs differ between the designs (part of the buffer / power difference comes from the knobs) and that DM_VC4
  needs a larger die.

**T7. Board runs** (owner provides the DE2-115 and schedules the session)
- Remaining 58 cases of the single pass (section 3.3). Confirm `python scripts/rtl_manifest.py --check` first.
- Program each SOF with `quartus_pgm -c USB-Blaster -m JTAG -o "p;<file.sof>"` (never the published repo's `program_de2_115.ps1`).
  Pass criteria (as `asic/gls/tb_gls_soc.sv`): LEDR 0xA5 (0xEE = self-check failed), HEX7..HEX0 = MCYCLE of the measured region
  (INDEX.csv `expected_mcycle_hex`), complete UART log equal to the reference. Never build firmware with `BENCHMARK_FAST_UART`.
  `fw_board/upfull_*.hex` are the 12 kernels at their official iteration counts.
- Record in NHAT_KY, `RESULTS.md` 4.4 and `REVIEW_RESPONSE.md` A7.

**T8. LEC**
- DM / SA2 complete against `rtl_r14` gold; DM_VC4 synthesis part done. On `6c4ccffd`: gold from `rtl_rfbht`; scripts of 2026-10-15
  (section 3.7); every step twice with negative controls (FSM codes, unsigned / partial-product mutation, NegAlign, and2 -> or2).
- Prerequisite per layout: a byte-exact replay of the run's synthesis (`asic/equiv/lec/synth_replay_r14/run_replay_r14.sh`; one
  snapshot hook only, extra hooks change Yosys's process state) and the multiplier t1 replay.
- Until then, `RESULTS.md` keeps saying that no `6c4ccffd` layout has an RTL-to-netlist proof.

**T9. Gate script follow-up** - COMPLETE 2026-10-09: `P2_INITIAL_GRT_FALLBACK=1` reads the last post-GRT reroute or the initial
GlobalRouting when `RUN_POST_GRT_DESIGN_REPAIR` is false (34 controls, `results/gate_p2_no_repair_20261009/verification.json`).

**T10. Cleanup** (archive and dependency checks required; owner approval for run folders)
- Done: 2026-10-09 17 runs + 22 Questa libraries (82,819,435,929 logical bytes for the runs; receipt
  `results/workspace_audit/cleanup_execution.json`); 2026-10-14 43 failed PD dirs (~125 GB); 2026-10-15 dmuA / dmuB.
- Blocked by automatic tool review (do not retry with another tool): deletion of `final_B` (its six LEC / replay inputs are archived and
  14 readers migrated; `results/final_b_dependency_migration_20261009/cleanup_outcome.json`); removal of 20 ZIP-archived source /
  document / coverage originals and the golden-helper rename (`results/source_archive/retired_sources.json`).
- History of the proposal: `results/cleanup_proposal_20261009.md` / `.json` (19 PROPOSE_ONLY, 10 KEEP, 11 DEFER; inventory sum of the 19
  runs 89,857 MB, not a reclaimed amount; text archives 7,923 MiB), `results/cleanup_candidates_20261009_sizes.txt`. Executed deletion
  of 2026-10-09: 82,819,435,929 logical bytes (77.132 GiB) for the 17 runs.
- Keep: signed-off runs (r14F_A/B, final3_A/B, SA2 `_ecomaxmin_r1/_r2` and their `_rsztf_r1/_r2` sources), synthesis evidence runs,
  golden snapshot, SOF matrices, logs, double-executed CSVs, `asic/evidence/`. Procedure: archive per run into
  `results/pd_run_archive/<run>/`, list in `results/cleanup_deleted.txt`, add a row to `NHAT_KY.md` section 10.

**T11. Git** - the research state was committed on 2026-10-15 on branch `experimental-r14`. Further commits only when the owner asks;
English ASCII messages; no Co-Authored-By; never check out another branch while jobs run.

**T12. Manuscript items** (M3 related work, A5 caption, minor text items) - owner-maintained; the paper is not edited here.

## 7. PD knowledge already paid for (do not rediscover)

- STAMidPNR ss / ff numbers are stale pre-PnR values; mid-PnR gates use nom_tt only. Use STAPostPNR for real numbers.
- PostRouteHoldECO annotates ONE extraction (`POST_ROUTE_HOLD_ECO_RCX_CORNER`, default max_*) for every corner: one pass fixes one RC
  extreme; two passes (max_* then min_*) closed SA2; min_* alone broke max_ff. Since 2026-10-13 both passes run in one step
  (`POST_ROUTE_HOLD_ECO_RCX_CORNER_2`).
- ECO STA traps: calling `estimate_parasitics` before `read_spef` keeps the session on estimates; the SRAM macro has one TT .lib, kept
  by the first corner read (STA-1140): run a setup ECO with the tt corner alone.
- `RSZ_CORNERS` tt / ff: with the default (tt, ss, ff) the resizer chases ss (-9 ns, ~7,600 endpoints) for hours. The DM_VC4 3600
  candidate kept the default only to reproduce its known-good first global route.
- Post-GRT DRV repair with cap margin 50 + `LAYERS_RC` over-buffers the tag clusters (~4,650 buffers); cap 20 is used.
- `MAX_FANOUT_CONSTRAINT` 16 helps SA2 (-27 % resizer buffers) and FAILS DM_VC4 (GRT overflow 1,272).
- Global-route antenna repair floods DM_VC4 with 11,000-17,000 diodes on 11.56 mm2; on the padded 12.24 mm2 die margin 10 gives 9,225
  diodes and overflow 0, but the post-route antenna re-route still does not converge.
- Clock trunks: `RT_CLOCK_MIN_LAYER` met3 helps SA2; on DM_VC4 neither met3 nor met4 stops the detours.
- `OpenROAD.RepairDesignPostGRT` re-runs a full global route after its repair; any full global route can re-route the clock trunks.
  `Odb.DiodesOnPorts` is a no-op here (`DIODE_ON_PORTS` none).
- From R15 / R16 the cache SRAM instances are named `u_soc.u_{i,d}cache.genblk1.g_dse.*`; macro placement files of R14 do not match.
- Diagnostics (read-only, Windows Python): `asic/fp_tools/guide_demand.py`, `region_cells.py`, `clock_detour.py`, `clock_layers.py`,
  `pin_hotspots.py`; `asic/fp_tools/grt_skew_screen.sh` (WSL); `asic/sta_query/`.
- `run_gated_pd.sh ITEMS`: the config path is relative to the design dir (`config_x.json`, not `soc_x/config_x.json`).
- OpenLane resume: new step dirs are numbered after the highest existing number; resume state = latest `state_out.json`. A died run
  (highest step dir without `runtime.txt` / `state_out.json`): rename that dir to `crashed-<NN>-<name>`, write a NOTE line to
  `gated_pd.log`, resume with `run_gated_resume.sh <design> <tag> <config> '<reason>' drt|hold|step:<StepID>` (development only; the
  result still needs a clean full run).
- `branch_run.sh <design> <source tag> <new tag> <N>` copies steps 1..N into a new tag (source read-only; screening only).
- GLS logs are huge (verbose OpenRAM model): ~50 min per kernel for the SA2 netlist (~22 min per kernel in the exact-window runner).

## 8. Do not

- Do not write to the published repository or edit the paper.
- Do not change RTL for PD reasons; do not touch the locked R14 DM runs r14F_A / r14F_B.
- Do not relax the clock, the SDC, or the sign-off gate; do not disable checks to make a flow pass.
- Do not run parallel screening sprays; do not run two Quartus fits at once.
- Do not edit a running script; do not kill healthy runs or the owner's processes.
- Do not delete run folders without the owner's approval.
- Do not report a single execution as a result.

## Revision history

| Date | Change |
|---|---|
| 2026-10-09 06:40 UTC | handover file `HANDOVER_CODEX.md` (state, jobs J1-J3, tasks T1-T12) |
| 2026-10-09 18:40 | renamed to `PROJECT_STATE.md` after the coordinator exited; persona text removed |
| 2026-10-09 .. 2026-10-15 | dated "Update" blocks appended (2026-10-13 05:20, 15:20, 19:20; 2026-10-14 00:55, 08:40, 16:15, 18:30, 21:20, 22:30; 2026-10-15 07:45) |
| 2026-10-15 07:46 | committed (commit `2d4202d`) |
| 2026-10-15 | restructured: overview table; per-area state; running-jobs table; the dated update blocks condensed into the state log (section 5); task list re-ordered for the `6c4ccffd` plan (new T13 PD acceptance, T14 re-runs); superseded procedures (branch-based second ECO, two-pass board plan, 2026-10-13 never-resume rule, J1/J2 recovery commands) replaced by the current ones; report page source updated to `report_page/soc_report.html`; git status updated |
| 2026-10-15 | references point to the single topic-structured `NHAT_KY.md` (rule for new history events: section 8a) |
