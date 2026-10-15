# Project state and remaining work

Audience: the project maintainer and owner. Read this whole file before running anything.
Everything below is binding unless the owner says otherwise in the session.

## 0. Read first, in this order

1. `QUY_TRINH.md` - the binding procedures and rules (Vietnamese, ASCII). If this file and QUY_TRINH.md disagree,
   QUY_TRINH.md wins; tell the owner about the conflict.
2. This file - current state, running jobs, ordered task list with exact commands.
3. `NHAT_KY.md` section 8 (entries of 2026-10-09) - why every current PD knob exists; section 9 - known traps.
4. `RESULTS.md` (current numbers), `REVIEW_RESPONSE.md` (review items), `README.md` (layout).

## 1. Binding rules (short form; full text in QUY_TRINH.md)

Scope and language
- Work ONLY in `E:\Projects\RISCV-research` (4 KiB caches, 16 KiB RAM). The published repository
  `E:\Projects\RISCV-AHB-APB-UART` is READ-ONLY: read and take data from it, never write to it. Do not edit the paper.
- Replies to the owner: Vietnamese. Anything committed or pushed to git: English, ASCII only, no "Co-Authored-By" line,
  local git identity (user vutoan1110). Do not commit or push unless the owner asks.
- Project files: no first-person narration, no "the user said", no persona text, no references to any AI memory.

Measurement discipline
- Every measurement is executed twice and compared field by field (r1 = r2). A result is final only after that.
- Debug from evidence, one hypothesis at a time. A clearly random machine crash (Python SIGSEGV, a corrupted Python
  object, WHEA error, random OOM, Quartus access violation ~8 %) may be retried unchanged, but always FROM THE START
  (PD: a new full flow from step 1 under a new tag; other tools: the whole command into a new output folder); a
  deterministic failure (DRC, setup / hold, LVS, ...) needs an engineering fix. Do not blame the machine without
  independent evidence; the double execution decides.
- Fix and resume during development, accept only a clean full run (owner, REVISED 2026-10-14; the 2026-10-13 "never
  continue from a failed step" made the process too long): after a failure (crash, error, watchdog stop, FAIL gate),
  log FAIL + diagnosed cause, keep the folder, fix, and resuming from the failing step is allowed. Once everything
  passes, ONE complete flow from step 1 (fresh tag, no resume / branch / CONTINUE, thresholds declared at launch) is
  required; only that clean run (and its double execution where required) is the result. Deterministic flow + a
  launch-time-only fix: going straight to the clean run is allowed. Same for non-PD tools. Runs signed under
  resumes / branches (DM r14F_A/B, SA2 ecomaxmin) each need one clean full run.

RTL
- Current RTL: manifest `6c4ccffd` (`results/rtl_manifest.json`, `scripts/rtl_manifest.py`). Any RTL change must carry
  the WHOLE chain in order (QUY_TRINH.md section C): apply by script -> freeze manifest -> lint / latch -> formal proof
  with negative control for restructurings -> full chain x2 (`scripts/run_fullchain_rfbht.sh` is the latest chain
  driver) -> Quartus 4 points x 10 common seeds x 2 passes (QUY_TRINH section E) -> PD from step1, double
  executed -> GLS + activity power. Preserve the older four-seed verification subset as historical evidence.
  New logic needs new tests; nothing may be disabled to make a flow pass.
- PD never edits RTL. PD configs read RTL snapshots `asic/snapshots/rtl_*`, never `hdl/`.

PD (OpenLane 2.3.10 local copy `asic/openlane-local`, sky130A, 20 ns clock)
- Sign-off gate (hard): route DRC 0, Magic DRC 0, KLayout DRC 0, LVS 0 (every difference count), XOR 0, illegal
  overlap 0, critical disconnected pins 0, antenna nets / pins 0, setup >= 0 at EVERY tt and ff corner, hold >= 0 at
  EVERY one of the 9 corners. The ss corner is reported, not gated (it cannot close at 50 MHz without changing CPI,
  which is forbidden). Max slew / cap / fanout violations are NOT hard limits: report them by category (SRAM pins,
  diode-laden nets, standard cells); never pay large area to clear them.
- DM is LOCKED at r14F_A / r14F_B (= dm_grid3665x2900_r1 / _r2, `asic/soc_dm_4kb/config_R14_FINAL.json`, 10.63 mm2).
  Never touch it.
- SA2 and DM_VC4: each optimised on its own. Strict PPA: the minimum ROUTABLE die (prove it: the next smaller
  candidate fails with the same recipe), then the fewest buffers, the least wire and the lowest power.
- Every change runs a FULL flow from step 1 to sign-off; diagnose at every phase and stop at a clear failure sign
  instead of waiting. One hypothesis per run; do not spray parallel screening runs. A branched run
  (`asic/branch_run.sh`) is only for screening; the official result is a full flow from step 1, executed twice.
- Use the gated drivers: `asic/run_gated_pd.sh` (new flow), `asic/run_gated_resume.sh` (only to continue a PLANNED
  pause), `asic/branch_run.sh` (screening only, never from a failed run). Every gate result and every manual decision
  goes to `asic/gated_pd.log` as one line with the reason. SA2 / DM_VC4 recipes declare `P2_MIN_HOLD=-0.5` at launch
  and run both hold-ECO passes in one step (`POST_ROUTE_HOLD_ECO_RCX_CORNER_2` = "min_*"), so no branch / CONTINUE.
- Never edit a script while it is running. Stop jobs cooperatively: `touch asic/.abort_gated_pd` (no new phases).
  Never kill a healthy run. A run that has clearly failed may be stopped only after its cause is found and written to
  gated_pd.log. Never kill the owner's own processes (games, browsers, ...).
- Quartus fits run sequentially, never in parallel; when two PD flows run, do not run Quartus together with the
  multi-lane verification chain.

Naming and records
- Run tags: `<cfg>_<floorplan>[_<knob><value>...]_r<N>` (e.g. `vc4_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd_r1`).
  No numbered / AI-looking names (no R17, E17, final4, _v2, "Incident NN"); content + date names.
- History: ONLY `NHAT_KY.md`, one entry per event `### YYYY-MM-DD HH:MM <subject>` (Vietnamese, ASCII, no
  diacritics), recurring issues in its section 9, alias table in section 11. Procedures: `QUY_TRINH.md`. Numbers:
  `RESULTS.md`. Review status: `REVIEW_RESPONSE.md`. Do not record the same issue in several places.
- Cleanup is mandatory but deleting run folders needs the owner's explicit approval; archive first
  (`results/pd_run_archive/<run>/`: resolved.json, final metrics, error / warning logs, flow log, step list) and list
  every deletion in `results/cleanup_deleted.txt`.
- Reporting to the owner: Achievements, then Failures and gaps, with hard numbers; name the corner of every timing
  number; keep the timing corner separate from the power corner; state the power method (flow estimate / vectorless /
  activity-based); DRC / LVS as a pass/fail gate before the PPA table.

## 2. Machine and how to run things

- Windows 11, 32 logical CPUs, 31.6 GB RAM. Shells: Git Bash (Windows side: Questa, Python, Quartus) and WSL Ubuntu
  (OpenLane via nix, OpenROAD, Yosys, Magic, KLayout, netgen). WSL is capped at 24 GB RAM + 8 GB swap.
- Start WSL jobs from Windows: `wsl.exe -d Ubuntu -e bash -c "cd /mnt/e/Projects/RISCV-research/asic && ..."`. The WSL
  VM shuts down (killing every job, even nohup ones) when the last wsl.exe client exits: KEEP ONE WSL TERMINAL OPEN
  for as long as PD jobs run. Do not use detached / persistence tricks to survive that.
- Memory per job (measured): OpenLane flow before DRT 5-8 GB; detailed routing ~10.5 GB; Magic DRC up to ~14 GB;
  KLayout DRC ~8 GB; post-route ECO ~10 GB; Questa GLS of a full netlist ~0.2-3 GB per job. The gated scripts wait for
  free memory (new flow >= 10 GB free, detailed routing >= 12 GB free and at most one other detailed routing).
- Watch `asic/gated_pd.log` with a polling loop (`wc -l` + `sed -n`); `tail -F` from Git Bash does not see lines
  written from WSL.
- Questa: `C:/questasim64_2024.1/win64/vsim.exe`. PowerShell scripts that call `wsl.exe` with quoted bash commands need
  PowerShell 7 (`pwsh`), not Windows PowerShell 5.1.

## 3. State at handover

RTL / verification / FPGA (done)
- Functional revision: RAM 16 KiB with FPGA RF/BHT in M9K, optional FAST_HIT. R14/R15/R16 are legacy aliases;
  the M9K change is later than R16. WORKSPACE_MAP.md describes each source/document folder and proof boundary.
- RTL `6c4ccffd`: register file and BHT moved into M9K on the FPGA view only (cycle-exact; the ASIC view and the
  OpenLane netlist are byte-identical to R16). Proofs: k-induction 3/3 with negative controls; sim-only checkers; full
  chain 0 failures (`results/fullchain_rfbht.log`); ACT4 43/43 x2.
- Initial Quartus subset, 4 points x 4 seeds x 2 passes identical (`results/fpga_points_rfbht_p{1,2}.csv`): DM 12,810-12,842 LE,
  DM_DSE 14,308-14,364, SA2 16,675-16,739, DM_VC4 17,130-17,139; Fmax 51.96-55.52 MHz (Slow 85C). SA4 and the 8 KiB
  points were NOT refitted (still R15/R16 flip-flop numbers).
- The common ten-seed extension is complete: all 40 point/seed rows agree on 115 hardware fields in both passes.
  DM/SA2/DM_VC4/DM_DSE use identical seeds 1..10; seed2 was refitted independently in both passes and fixed for board.
  Sources: `results/fpga_common_seeds_continued_20261009_ppa.{json,md}` and its paired CSVs/seed summaries.
  All 100 current-RTL seed2 SOFs and the 200-row NOT_RUN physical template are ready; canonical MIF restoration PASS.
  Board folder: `output_files_board_matrix_6c4ccffd_seed2/`; INDEX.csv binds expected cycles/instructions and hashes.
  Physical session date:2026-10-12, UART receiver:Hercules. Session preparation/evidence folder:
  `results/board_20261012/`; its README documents the actual fitted JP5 GPIO3.3V UART and the immediate boot.
  `readiness.json` rechecks all100SOFs/currentRTL/seed2 and the paired references; physical UART is NOT_TESTED.
  `runlist.csv` orders200measurements; `results.csv` remains200NOT_RUN. `program_board_case.ps1` is plan-only
  unless -Program is explicit; `check_board_uart.py` checks28numeric UART fields. The older stopped coordinator
  JSON is retained historical evidence, not the current preparation status. CoreMark RAM32KiB images are not
  included in this RAM16KiB board set.
- Extended conflict probe done (390 windows, both runs identical, `results/conflict_probe.csv`).
- Supplemental UVM complete: 48 paired cases across all four 4 KiB cache configurations, seeds 1/2/3,
  directed/peripheral/UART RX tests and AXI stress line words 2/4/8/16; all scoreboard fields identical and wrong-byte
  controls detected. Receipt: `results/uvm_cache_uart_20261009/verification.json`.
- Corrected architecture adapter complete: 43 ACT4 cases and one upper-half data/instruction case independently
  repeated; ACT4 signatures/cycles/retirements equal the previous result, original alias detected by the negative
  control. Frozen TB is retained; the runner generates and hashes the six-index correction separately:
  `scripts/verification/run_architecture_window.py`, `results/architecture_window_20261009/verification.json`.
- Random runner hardened and independently rerun: 50 seeds per pass, all paired summaries and full trace bytes
  equal the prior RF/BHT result. Logs are distinct by pass; process/completion/integrity gates and complete CSV
  schema checks have 43 positive/negative controls. Receipts: `results/random_diff_checked_20261009/verification.json`
  and `results/verification_runner_controls_20261009/verification.json`. The full-chain caller now retains the
  random process return code through its pipe. This original result is predictor OFF/ON equivalence on the same core.
  A separate Spike comparison completed2026-10-11:100 fresh Spike executions (50seeds x2), matching all200
  preserved independently executed RTL traces,7105 retirements/pass and300 wrong-trace controls detected.
  `results/spike_random_reference_20261011/receipt.json`; adapter invokes the installed Spike ISA engine directly
  atPC0 with the frozen DUT's zero GPR/data initialization. No ISA semantics implemented in the adapter.
  Scope is the generated RV32I/Zmmul core subset; no SoC MMIO/interrupt/cache/timing or arbitrary-init claim.
- CoreMark numeric CRCs verified: six base and five FAST_HIT points, 22 fresh simulations, all 40 counters equal
  both passes and the old reference. A separate canonical DM pair matches every one of the 43 CSV columns.
  The maintained runner requires numeric source CRCs and fresh UART capture before PASS. Receipts:
  `results/coremark_crc_checked_20261009/verification.json`, `results/coremark_canonical_checked_20261009/verification.json`.
  RAM remains 32 KiB in simulation, the window includes initialization/reporting, and this is not an official score.
- Standard-duration CoreMark is VERIFIED with a separate -Os integer port, unchanged benchmark
  algorithms and canonical simulation RAM32KiB. APB TIMER_CMP is set to0xffffffff before the timed interval;
  accepted TIMER_COUNT reads are checked against independent clock edges and20ns simulation time. The two
  firmware builds match byte-for-byte (`results/coremark_standard_apb_build_pair_20261011.json`). All16 cases
  (four configs x performance/validation x2) PASS; all108 scalar fields per pair match,864 comparisons. Evidence:
  `results/coremark_standard_apb_matrix_20261011/receipt.json`, `cases.csv`, `performance_paired.csv`.
  Full method/flags/scores: RESULTS.md section1.1. A physical-board result or EEMBC certification is not claimed.
- Supplemental CoreMark sweep CRC execution is VERIFIED: 49 base and 43 FAST points, each independently
  repeated with fresh private compilations. `scripts/verification/run_coremark_sweep_crc.py` requires the exact
  supported grid, actual elaborated I/D/line/victim/FAST/RAM/L0/predictor parameters, source-known numeric CRCs,
  simulator success and all40 counters equal to both old sweep passes. The36 controls passed before launch.
  All184 actual simulations completed; the independent verifier rechecked241 inputs/379 artifacts, all184 raw
  logs/UART streams and92 complete paired rows. Receipts: `results/coremark_sweep_crc_20261010/verification.json`
  and `results/coremark_sweep_crc_independent_audit_20261010/receipt.json`. The26 verifier controls also passed.
  The excludedSA4_256B_L16 remains outside the valid grid;32KiB/full-program/short-duration scope is unchanged.

ASIC
- DM 16 KiB RAM: signed off, double executed (r14F_A / r14F_B). Legacy register-mapped SAT/CEC/algebra results
  and negative control are retained; full sequential reset/clock/reachability closure is under audit. The new
  unrestricted symbolic gold reset-base check proves 235 constants, 28 duplicates and 4 FSM groups twice, but is not
  a full LEC verdict. Activity power is verified in two independent STA executions for12 kernels;
  every power group/origin matches, vectorless reproduces the flow. The secondSTA reused preserved GLS/SAIF,
  reading the locked layout without PD rerun or modification. Actual STAPostPNR is step58 (step57 is RCX).
  Receipts: `results/gls_power_r14F_A_power_verification.json`, `results/dm_activity_power_second_pass_20261010.json`.
  Rule Q status (audit 2026-10-14; the rule dates from 2026-10-13): NOT compliant as executed. The session end of
  2026-09-30 ~23:38 UTC killed both runs and both were resumed on 2026-10-02 with `run_resume_retry.sh` (now retired):
  r14F_A after its uninterrupted flow through step 59 (layout, netlist, RCX and STA done; resumed at the Magic
  streamout, i.e. only GDS and the DRC / LVS / XOR checks), r14F_B inside detailed routing (step 46 killed, routed
  again from step 47). Final netlists are byte-identical (sha256 `83f38f7e...` for both fill-insertion netlists), so the layout is reproduced, but a compliant DM
  needs a fresh double full flow: owner decision (DM is locked).
- SA2: SIGNED OFF CLEAN and double executed on 11.56 mm2 (3400 x 3400, `macro_placement_u2fg.cfg`):
  - runs `sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1` / `_r2`: 319/319 metrics identical,
    final netlist and DEF byte-identical, SPEF identical except its `*DATE` line.
  - recipe: config `asic/soc_sa2_4kb/config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf.json` as a full flow
    (its p2 gate stops on hold nom_tt -0.206; continue past it with a CONTINUE line, the post-route ECO repairs hold),
    then `branch_run.sh` after the PostRouteHoldECO step (step 47 there) and a SECOND hold ECO with
    `config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomin.json` (`POST_ROUTE_HOLD_ECO_RCX_CORNER` min_*).
  - rule Q status (audit 2026-10-14; the rule dates from 2026-10-13, after this sign-off): the recipe is NOT rule-Q
    compliant as executed. Both source runs `_rsztf_r1/_r2` passed the failed p2 gate with a CONTINUE line (now:
    `P2_MIN_HOLD` declared at launch) and then failed the final gate (hold nom_ff -0.023 / min_ff -0.027); the
    `_ecomaxmin` runs are branches of those failed runs after step 47, and `_ecomaxmin_r1` was also resumed at step 52
    after a random CPython crash in Odb.ReportDisconnectedPins
    (`crashed-52-...` kept). `_ecomaxmin_r2` has no crash and gives the byte-identical netlist, so the numbers stand, but
    a compliant SA2 needs a single fresh flow: E1 (`..._cts25`, CTS 25 + `POST_ROUTE_HOLD_ECO_RCX_CORNER_2` +
    `P2_MIN_HOLD`) if it wins on PPA, otherwise E0 = this recipe as one flow (`_rsztf.json` + CORNER_2 + P2_MIN_HOLD),
    which should reproduce this netlist byte for byte (the one-step ECO was checked byte-identical to the branch).
  - numbers: setup max_tt +0.838, nom_tt +1.118, ff >= +3.803 ns; hold worst +0.020 (min_ff/max_ff); ss -6.72..-7.92;
    std cells 1.4711 mm2 (215,979); wire 9.274 m; vectorless nom_tt 121.99 mW. Table: `results/asic_compare_dm_sa2_20261009.md`.
  - Activity-power calculations verified 2026-10-09 08:14 UTC: 12/12 GLS kernels, two independent OpenSTA executions at nom_tt
    with RCX SPEF identical on every power group and activity-origin field; 127.45-131.75 mW (mean 129.64), unknown
    4.42 %, EPI GM 4,317 pJ. `_power_p1.csv`, `_power_p2.csv`, `_power_verification.json` under the final SA2 tag.
  - LEC (T8) DONE 2026-10-14: two independent executions, PASS1_EQUALS_PASS2 (39 objects + every verdict;
    `results/lec_sa2_20261013/pass_comparison.json`, RESULTS.md 4.2); NegB control (and2 -> or2) done 2026-10-14: 60 SAT.
  - Exact-window activity recapture (T3) DONE 2026-10-14: two GLS + two STA passes identical, mean 129.64 mW, EPI GM
    4,317 pJ (`results/activity_power_exact_sa2_20261014/receipt.json`, RESULTS.md 4.2). Not done: minimality
    below 11.56 mm2 (T4; 11.05 failed P2 twice, 11.305 closed FAILED).
- DM_VC4: NOT signed off. Root cause measured (NHAT_KY 2026-10-09 entries):
  - the D$ victim buffer + D$ tag cluster congest the corridor at the D$ macro edge; FastRoute then runs GRT-0103
    "Extra Run for hard benchmark" (it fires at congestion iteration 20 when overflow > 200; OpenROAD edf00dff source)
    and the upper clock-tree nets detour 3-7 mm -> hold clock skew -2.7 .. -4.8 ns -> 1,675-2,088 hold-violating
    endpoints at p2 (SA2: 19). Every FULL global route re-rolls this clock routing (a lottery);
    `OpenROAD.RepairDesignPostGRT` itself runs a full new global route after buffering (`repair_design_postgrt.tcl`).
  - tried and rejected: cell padding at 11.56 mm2 (helped, not enough), 150 GRT congestion iterations (GRT-0103 still
    fires), die 3500 x 3400 with padding, clock trunks on met4-met5 (worse: skew -3.79 ns), a bigger die alone (3800 x
    3400 old run was worse than 3600: skew -3.77 vs -2.00).
  - failed unpadded baseline (12.24 mm2): `vc4_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd_r1`, config
    `asic/soc_vc4_4kb/config_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd.json`. Steps before GRT are identical to
    the old run `vc4_corr3600x3400_f220_r1`, so its first global route is reproduced byte for byte (guide + DEF sha256
    checked) and has SA2-like skew (hold skew -2.00 ns, hold nom_tt -0.364 at 162 endpoints, setup nom_tt +0.046).
    After GRT: no post-GRT design repair (it would re-roll the clock), no GRT antenna repair (antennas are repaired on
    the detailed routes, `DRT_ANTENNA_REPAIR_*`), no post-GRT timing repair. Its p2 gate printed "MISSING p2 data"
    (the gate looks for the post-GRT repair re-route, which is off by design) and was continued by hand (CONTINUE line
    06:20 UTC). Detailed routing started 06:21 UTC.
  - risk: setup nom_tt after GRT is only +0.046 ns (half-cycle path RAM bank[4] dout0 -> I$ bank[2] din0, slew
    0.87 ns, through resizable buffers). max_tt at sign-off may go negative.
- Board (FPGA DE2-115): the SOF matrix `output_files_board_matrix_r14/` is for RTL `3ea52396` (R14) and is now
  OBSOLETE for the board: the RTL changed (6c4ccffd). Current board matrix and results: see "Board (Codex, ...)" below
  (42 of 100 cases measured 2026-10-13, all equal to both RTL reference passes).

Reports
- The report page has a separately hosted copy. Its local source is kept at
  `results/report_page/bao_cao_soc_v5.html` (Vietnamese). Keep
  updating a local copy (new file name with the date) if a report page is needed.

## 4. Current jobs and retained recovery references

Check the current queue receipt before starting anything. J1/J2/J3 below retain the original job identities;
J1 failed, J2/J3 finished, and neither is currently running. The recovery commands are conditional references.

Update 2026-10-15 07:45 (+07):
- First 6c4ccffd attempts both stopped on 2026-10-14 evening (nothing ran overnight):
  - `dm_grid3665x2900_rtl6c4c_r1`: p1 gate FAIL, STAMidPNR-2 setup nom_tt +0.307 ns < P1_MIN_SETUP 0.5. The 6c4ccffd
    netlist has 71,006 cells (R14 70,441; synthesis sha256 da06d38f = R16, not R14's fc555d6b); its worst post-CTS path
    is the half-cycle RAM bank[3] -> D$ data bank refill path (R14 worst: +2.164 on an I$ path).
  - `sa2_..._eco2_rtl6c4c_r1`: step 16 ManualMacroPlacement failed: from R15/R16 the cache macros are
    `u_soc.u_{i,d}cache.genblk1.g_dse.*` (R14: `...g_dse.*`). Fixed with `soc_sa2_4kb/macro_placement_u2fg_rtl6c4c.cfg`
    (8 names only, coordinates equal, 16/16 checked against the netlist); DM_VC4 will need the same rename.
- Second attempts running (`asic/sequence_heavy_20261015g.sh`, started 00:18 UTC): `dm_grid3665x2900_rtl6c4c_r2`
  (P1_MIN_SETUP=0 P2_MIN_SETUP=0 declared at launch; sign-off gate unchanged) and `sa2_..._eco2_rtl6c4c_r2`
  (renamed placement; E0 thresholds + P1_MIN_SETUP=0). g keeps one heavy phase at a time.
- Older-RTL simulations re-executed x2 on 6c4ccffd (owner: now, in parallel, below-normal priority on Windows):
  M1/M2 sweep `scripts/m2/rerun_m2_6c4ccffd.py` -> `results/m2_6c4ccffd/` (base 650 + FAST 572 runs per pass);
  A8 / A3 / A4 / IRQ `scripts/maintenance/rerun_review_sims_6c4ccffd.py` -> `results/review_sims_6c4ccffd/` and
  `results/*6c4ccffd*` (old results untouched; comparison.json in each folder at the end).
- dmuA / dmuB deleted after archiving their text evidence (owner 2026-10-15). Codex's audit
  `results/rtl_provenance_audit_20261014/report.md` agrees with `results/rtl_consistency_audit_20261014.md` and lists
  documentation mismatches to fix later (board "10 kernels" -> 9, etc.).

Update 2026-10-14 22:30 (owner: finish PD before any page edit; one RTL for every flow; delete failed PD runs):
- Audit of every reported result vs the RTL it ran on: `results/rtl_consistency_audit_20261014.md`. Not on 6c4ccffd:
  PD (all), GLS / exact-window power, LEC, M1/M2 sweep, A3 cross-validation, A4 overlap, IRQ latency, BP on/off (and
  the CoreMark R16 baseline). The SA2 / DM_VC4 ASIC wrappers were outside the RTL manifest: now frozen into
  `asic/snapshots/rtl_rfbht` (SHA-256 in its SNAPSHOT_ID.txt; snapshot = 47 files, byte-identical to the live tree).
- SA2 acceptance on 6c4ccffd: `sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rtl6c4c_r1`
  (`soc_sa2_4kb/config_..._rsztf_eco2_rtl6c4c.json` = E0 + snapshot sources; thresholds as for E1), queued by
  `asic/sequence_heavy_20261014f.sh` after the old-RTL cts25_r5 sign-off part; f serializes DM then SA2 heavy phases.
- cts25_r5 (old RTL) is still in its sign-off part: my stop was refused by the permission system (not retried); the
  owner may stop it with: wsl -d Ubuntu -e pkill -f "sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25_r5".
- Cleanup: `scripts/maintenance/archive_and_delete_failed_pd_20261014.sh` (43 failed / stopped / screening PD dirs,
  ~125 GB; text evidence in `results/pd_run_archive/20261014/`, log `results/pd_run_archive/archive_and_delete_20261014.log`).

Update 2026-10-14 21:20 - OWNER DECISION: PD on the newest RTL 6c4ccffd (until now every PD config read
`asic/snapshots/rtl_r14`, manifest 3ea52396, justified only by the R14 == R16 FAST_HIT 0 SoC proofs and the FPGA-only
RF/BHT change). From now on PD reads `asic/snapshots/rtl_rfbht` (= manifest 6c4ccffd: rtl_r16 + the RF/BHT files;
44 files checked byte-identical to the live tree twice, live tree `rtl_manifest.py --check` IDENTICAL 6c4ccffd).
- V4 (DM_VC4 3800) stopped by the owner at 14:01 UTC (its antenna re-route followed V2's path). DM_VC4 is deferred
  by the owner; it will also be built from 6c4ccffd with a DM_VC4-own floorplan (read pins away from the centre band).
- `dm_grid3665x2900_r4` (rtl_r14) stopped at its DRT gate (cooperative flag, 14:11 UTC; flag renamed afterwards).
- DM acceptance run `dm_grid3665x2900_rtl6c4c_r1` = `soc_dm_4kb/config_R14_FINAL_rtl6c4c.json` (signed DM recipe,
  only VERILOG_FILES changed) started 14:12 UTC by `asic/sequence_heavy_20261014e.sh`, which holds the DRT slot lock
  until the SA2 E1 r5 sign-off part (sequence d, rtl_r14, kept as the E1-vs-ecomaxmin knob comparison) has ended.
- Next: SA2 acceptance run on 6c4ccffd with the recipe chosen from E1 vs ecomaxmin
  (`scripts/metrics/compare_signoff_runs.py`, checked twice on known runs); then GLS, exact-window power and LEC on the
  accepted 6c4ccffd layouts (the LEC gold must come from rtl_rfbht).

Update 2026-10-14 18:30 (supersedes the "Order" bullet of 16:15 below; owner: reader-facing results go to the report
page, NHAT_KY gets no new sections until its planned rewrite):
- DM acceptance `dm_grid3665x2900_r3`: STOP after P2. The OpenLane process segfaulted right after step 40 (CheckAntennas
  had finished; no state_out), so STAMidPNR-3 never ran and the p2 gate read MISSING data. Random, not a design or gate
  fault. New acceptance run `dm_grid3665x2900_r4` (same recipe, default gates) started 11:14 UTC; P1 PASS (+2.164 /
  +0.184), P2 PASS (overflow 0, STAMidPNR-3 setup nom_tt +1.725, hold +0.186), waits at its DRT gate.
  NOT byte-identical to r14F_A (19:20 check): netlists and all metrics are identical through step 42, but the step-41 DEF
  has two buffers (`wire10760`, `wire10761`) with swapped S / FS orientation (OpenROAD's address-dependent order, the
  N/FN effect logged 2026-09-25); step 43 RepairAntennas then gives 350 nets / 6,249 diodes (r14F_A 322 / 6,262) and the
  layouts diverge (r14F_A STAMidPNR-3 +1.756 / +0.201). Acceptance = sign-off gate + PPA comparison, not the hash; which
  DM layout is reported as the chip (r14F with all downstream evidence, or r4 which would need GLS / power / LEC again) is
  the owner's decision.
- SA2 E1 `..._cts25_r5`: detailed routing + hold ECO done (route DRC 0), then step 51 `Odb.ReportDisconnectedPins`
  SIGSEGV -> SIGNOFF FAILED line with missing sign-off data. Development run: sign-off part re-runs from step 51.
- DM_VC4 V4 (`vc4_corr3800x3400_..._antcong_r1`): detailed routing since 10:33 UTC (sequence c launched it once r3 had
  ended); main route iteration 19 = 68 violations at 11:20 UTC.
- Memory (process_stats.json): DRT ~10 GiB (VC4 up to 12.4 GB), Magic WriteLEF 12-13 GiB, KLayout XOR / DRC 8 GiB; a
  sign-off part beside a DRT does not fit in the 24 GB VM. `asic/sequence_heavy_20261014d.sh` (running) holds the DRT
  slot lock: V4 -> SA2 r5 sign-off from step 51 -> lock released -> DM r4 DRT + sign-off (r4 P1/P2 run now beside V4).
  Cooperative stop: `asic/.abort_sequence_20261014d`.

Update 2026-10-14 16:15 (NHAT_KY entries 09:50 .. 12:15 and later; supersedes the RUNNING lines of 08:40 below):
- DM_VC4: V2 recipe does not converge in the post-route antenna re-route (replay screening: ~225 left at iteration 43-44,
  1-3 % per iteration); margin 10/20/30 % (screening), max wire 500 um (V5: FAIL p2, setup -1.07 / hold -1.88) and a 3800 um die
  at the global-route stage (V4: 821 nets vs 742) did not reduce the violations. V3 (V2 recipe, relaxed antenna watchdog)
  stopped cooperatively before its detailed routing. V4's detailed routing is still to run (more room may help the re-route).
- SA2: exact-window power DONE (129.64 mW, EPI GM 4,317 pJ); LEC complete with all controls (NegB 60 SAT).
- DM_VC4 LEC (synthesis part) DONE x2 (`results/lec_vc4_20261014d`).
- Order (owner: shorter tasks first): DM acceptance run `dm_grid3665x2900_r3` (started 09:09 UTC, default gates, expected
  netlist sha256 83f38f7e...), then `sa2_..._cts25_r5` detailed routing + sign-off, then V4 detailed routing + sign-off, via
  `asic/sequence_heavy_20261014b.sh` (one heavy phase at a time; waits for the V2 replay screening, which holds ~12 GB and
  cannot be stopped from here - rule M; the owner may stop it with `pkill -f screen_drt_replay_v2_20261014`).

Update 2026-10-14 08:40 (NHAT_KY entry of the same time; supersedes the RUNNING / QUEUED lines of 00:55 below):
- FAILED: DM_VC4 V2 (main route 0 at iteration 31; post-DRT antenna 1,031 nets, re-route stalled, watchdog) and SA2 E1
  r4 (random Tcl panic in step 34). Diagnosis of V2: side-area antenna violations concentrated in the logic band
  between the I$ and D$ macro columns (both caches' read-data pins face the 220 um channel between macro rows); the
  global-route antenna margin is not the lever (screened 10 / 20 / 30 %).
- RUNNING: `sa2_..._cts25_r5` (E1 from step 1, STOP_AFTER=p2 planned hold; DRT via run_gated_resume.sh ... drt after the
  VC4 replay), screening `asic/soc_vc4_4kb/screen_drt_replay_v2_20261014` (V2's detailed-routing step replayed without
  the watchdog, one antenna round), LEC DM_VC4 attempt b `results/lec_vc4_20261014b` (attempt a stopped in step A: the
  RTL's 8 unused way-1 SRAM macros; fixed by `sram_align.py` + `NegAlign` control), SA2 exact-window GLS pass 2.

Update 2026-10-14 00:55 (NHAT_KY entries 2026-10-14 00:35 and later):
- RUNNING: `vc4_corr3600x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong_r1` (DM_VC4 V2: global-route antenna
  repair on, margin 10; started 17:41 UTC by `asic/queue_vc4_v2_after_sa2_r3_20261014.sh`). QUEUED behind it:
  `sa2_..._cts25_r4` (`asic/queue_sa2_e1_r4_after_vc4_v2_20261014.sh`). Both are foreground WSL clients of the session.
- SA2 E1 (CTS clustering 25) failed three times for non-design reasons, every failing step replayed cleanly:
  r1 SIGSEGV global route (step 41), r2 Python MemoryError (step 51, next to a VC4 detailed routing), r3 SIGSEGV
  antenna check (step 43). Its P1 / P2 numbers are identical in every attempt: STAMidPNR-3 nom_tt setup +0.959 /
  hold +0.182 (signed recipe +1.057 / -0.206).
- DM_VC4 antcong_r1 FAILED: main route reached 0 violations; the post-DRT antenna re-route (5,920 diodes) did not
  converge (watchdog stop). Hence V2 above (screened: 9,225 diodes before detailed routing, overflow 0).
- LEC: SA2 COMPLETE in two independent executions (p1, p2b; the first pass-2 front end died with a WSL Python SIGSEGV
  and was redone fresh): PASS1_EQUALS_PASS2; NegB control done 2026-10-14 (60 SAT). DM premises closed (asynchronous reset,
  undefined values, invariant bridge), see `RESULTS.md` 4.1. DM_VC4: the synthesis-only part (front end gold/N1, A,
  NegAlign, Mul, Inv, NegFSM, xsens) DONE 2026-10-14 in two complete executions, PASS1_EQUALS_PASS2
  (`results/lec_vc4_20261014d/`; attempts a / b / c stopped on the way-1 SRAM interface, the AIGER port order and an
  over-strict t1 check, all fixed); B / NegB / reset and clock audits after sign-off (`prepare_vc4_lec.py --add-gates`).
- Drafts for the owner: `results/review_status_20261014.md`, `results/extensions_vs_published_1kib_20261014.md`.

Update 2026-10-13 19:20 (NHAT_KY entry of the same time):
- RUNNING (gated queue, foreground WSL client of the session; log `asic/gated_queue_20261013_sa2cts25_vc4antcong.log`):
  `sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25_r1` (SA2-own E1: CTS_SINK_CLUSTERING_SIZE 8 -> 25 only,
  ~3.5 h) and `vc4_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_antcong_r1` (starts 30 min later, ~20-24 h).
  Env `G5_UNLIMITED_LATE_PHASE=1 P2_MIN_SETUP=0 P2_MIN_HOLD=-0.5 P2_INITIAL_GRT_FALLBACK=1`. A session end kills them.
- CLOSED as FAILED (no retry from step 47): `sa2_corr3400x3325_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1` (11.305 mm2).
- Intel Processor Diagnostic Tool 4.5: PASS (`results/health_20261013_recheck/ipdt_4.5/`).
- Board (Codex, owner-supervised): scope pass 1 only, 100 cases; 42 done and independently re-checked (all counters =
  both RTL reference passes; `results/board_20261013_independent_check/`); 58 left (10 short, 48 full-iteration).

Update 2026-10-13 15:20 (supersedes the 05:45 "MACHINE HEALTH FAILED" stop, which was too broad; NHAT_KY 14:55, 15:20):
- `asic/.abort_gated_pd` was REMOVED at 14:54. Work is not blocked by the probe (rule P); double execution decides.
- Machine re-check, idle machine, after the Riot Vanguard driver was removed (05:36) and a reboot (13:05):
  unpinned probe Windows 2-6/8, WSL 0/8; pinned to one logical CPU at process creation Windows 71/72; shlex-free
  pure-Python Windows 8/8, WSL 15/16 (one silently wrong checksum); native SHA-256 of a 380 MB file 8/8 identical.
  Ruled out: project scripts, Python installs, Vanguard, power plan (Turbo/Performance identical; Silent A/B no
  better), background load. No WHEA / Kernel-Power 41 in October. Evidence: `results/health_20261013_recheck/`.
- Practice: Windows-side Python tools run pinned (`cmd /c "start /wait /b /affinity <hexmask> "" python ..."`);
  a random crash is retried once unchanged; WSL processes cannot be pinned to physical cores, so PD results rely on r1 = r2.
- DM exact-window activity power DONE (pinned run, 2026-10-13 14:56): two fresh GLS captures + two STA passes,
  p1 = p2 on every field; mean 119.45 mW (114.81-122.99), within 0.005 mW of the preserved-SAIF values;
  `results/activity_power_exact_dm_20261013/receipt.json`. SA2 exact-window recapture still pending.
- The queue below is finished: its DM power step crashed (now done separately, above) and its SA2 11.305 retry was
  stopped by the abort flag before P4. The SA2 retry is still pending; the step-47 SIGSEGV is treated as a possible
  deterministic flow trap, not a machine fault, until the unchanged retry decides.

Update 2026-10-13 05:20 (NHAT_KY entry of the same time):
- SA2 11.305 mm2 r1: P4 died 2026-10-12 11:40 UTC in step 47 PostRouteHoldECO with a native SIGSEGV in the post-ECO
  incremental detailed route (iteration 19, stalled at 24 violations since iteration 13; the ECO itself fixed hold:
  326 endpoints, 197 buffers). Step dir kept as `crashed-47-openroad-postrouteholdeco`; ONE unchanged retry of the
  sign-off part is queued behind the P4 resource gate. A second stall above 0 or crash = 11.305 fails at the post-ECO route.
- DM exact-window power: capture pair VERIFIED; the STA driver stopped on its own memory guard (Windows 5,323 < 6,000
  MiB) after the vectorless STA. Re-run queued to the new output `results/activity_power_exact_dm_20261013`.
- Queue: `scripts/maintenance/queue_dm_power_sa2_eco_retry.sh`, log `results/queue_dm_power_sa2_eco_retry_20261013.log`
  (DM power at Windows free >= 7,000 MiB, then the SA2 retry at >= 15,000 MiB). Foreground; it dies with its shell.
- DM_VC4 next hypothesis PREPARED, NOT RUN (owner approval: ~20-24 h): `config_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_antcong.json`
  = the padded 3600 recipe + `DRT_ANTENNA_REPAIR_ALLOW_CONGESTION` + `DRT_SAVE_MAIN_ROUTE` (new openlane-local
  variables, default off, QUY_TRINH section D). Target: the post-DRT antenna repair that ended in GRT-0232.

Current status, updated 2026-10-13:
- Physical board session2026-10-13 uses the current research RTL and common seed2 SOFs under
  output_files_board_matrix_6c4ccffd_seed2/. USB-Blaster USB-0 programs EP4CE115; Hercules3.2.8 uses
  CP210x COM3/115200/8N1/handshakeOFF, JP5 GPIO3.3V TX=AB22/RX=AC15. The local Hercules copy is under
  tools/hercules; the published source remains unchanged. UART smoke has passed all28 fields.
  Session scope is ONE physical pass (100 workload/config cases), explicitly replacing the earlier two-pass
  board plan. Verification, Quartusfit, PD and ASIC power retain their two-execution requirements.
  Live state is results/board_20261013/session.json; read it, runlist.csv, results.csv and the current
  observation/UART/programming evidence before any action. Pass2 evidence rows remain present and marked
  NOT_SCHEDULED_SINGLE_PASS_SCOPE. Each case requires explicit display review and confirmation before any
  next programming, reset or rerun. A planned next_case never authorizes execution. Photos may be absent;
  actual manual display readback and native UART observations are recorded separately. Repeated boots after
  manual reset do not constitute another independently programmed pass. Official pairing is not claimed.
  History is in NHAT_KY. Helpers hercules_case_ui.py configure/flush logging without board operations;
  record_board_case.py validates one case offline; --sync-tracking updates the live records and history.
- Current foreground progress monitor: `python -B scripts/maintenance/monitor_jobs.py --watch --output
  results/job_monitor_status.json`. Default invocation checks once; --watch polls every600seconds and reports
  job/phase/count/native-process CPU and RSS, FAILED/DEAD_ALERT/UNKNOWN/HELD or suspected stall.
  It does not kill/retry tools or send conversation messages. The older `scripts/watchdog.sh` targets synth4kb
  and does not cover current GLS. It must not be used as evidence that all current jobs are supervised.
- J1 stopped by the convergence watchdog at 07:28 UTC (iteration 10: 5,689 > 5,000), recorded by the gated driver
  at 07:29 UTC. This is a convergence failure, not a random crash. Preserve step 43 and its DRC reports; no unchanged
  resume or new PD knob experiment has been launched. Diagnostic: `results/vc4_corr3600x3400_drt_diagnosis_20261009.json`
  and `results/vc4_corr3600x3400_drt_region_20261009.log`. T1 needs an evidence-based hypothesis before another run.
- J2 finished: 12/12 PASS, every mcycle and independent TB cycle count matches the ASIC-view reference. Activity-power
  Passes 1 and 2 finished and verified at 08:14 UTC; logs `results/sa2_activity_power_20261009_p{1,2}.log`.
  The subsequent raw-window audit found an extra 20 ns in all 24 preserved DM/SA2 SAIFs: duration is
  `(mcycle+1)*20 ns`. The legacy `*_ns` timestamp columns contain picoseconds. Existing STA calculations are
  reproducible, but exact-window power needs fresh capture and paired STA; no old activity inputs are changed.
  The same audit verifies 200 board-reference raw simulations using ten private compile libraries, original
  firmware and all 40 counters. Evidence: `results/embench_gls_evidence_audit_20261010/receipt.json`.
- Historical initial FPGA coordinator stopped for memory scheduling: `scripts/fpga/run_paired_seed_matrix.py --run`, tag
  `paired10_6c4ccffd_20261009`; log `results/paired10_6c4ccffd_20261009.log`, progress JSON of the same tag.
  Existing seeds 1..4 retain their independently executed rfbht provenance; seeds 5..10 are measured twice, with
  common board seed 2 refitted last in both passes. This coordinator's stopped output is preserved; the completed
  inspected continuation below supplies the verified 40-pair ten-seed result.
- The Windows fit/reference sessions were interrupted at about 08:33 UTC: no live processes, no final tool/error
  result; all input hashes and completed reports unchanged. Preserved evidence:
  `results/board_preparation_interrupted_20261009_1541/EVIDENCE.json` (8 complete fits, 38 complete reference cases).
  Continued at 08:50 UTC by the foreground driver `scripts/fpga/complete_board_preparation.py --run --launch-resume`.
  Status/log: `results/board_preparation_6c4ccffd_seed2_20261009.{json,log}`; JSON lists current continuation logs/PIDs.
  It stopped at 11:33 UTC with 51/56 additional fits complete because Windows free memory was only 5,384 MB
  (runner guard 6,000 MB). The inspected continuation waited for available memory without changing the guard.
  New driver: `scripts/fpga/continue_common_seed_preparation.py`; new progress/plan:
  `results/fpga_common_seeds_continued_20261009_{progress,plan}.json`. It preserves the original stopped experiment,
  completed all five remaining independent fits after memory became available, then assembled/audited all
  100 common-seed-2 SOFs. Status is READY_FOR_PHYSICAL_SESSION; original stopped receipts remain unchanged.
  Preserve completed fits and hashes; resume only unfinished independent fits after prerequisites are met.
- PD launch prerequisites: enough actual Windows and WSL memory, plus a foreground WSL client kept alive for the
  entire flow. No detached/persistence helper is used. Jobs intended to survive the controlling session require
  the owner's retained WSL terminal, as QUY_TRINH section B specifies. The approved watchdog
  correction is applied: set `G5_UNLIMITED_LATE_PHASE=1` for new flows and DRT resumes, as QUY_TRINH section D requires.
  T9's opt-in p2 reader is also available; no gate thresholds or final sign-off rules were changed.
  The reviewed padding-only experiment is queued by `scripts/maintenance/queue_vc4_padding.py`, plan219 local
  inputs,42 frozen RTL,8 macro files, SDC20ns. Actual launcher Nix tools9/external927 SHA inputs and host
  tokenisation8Windows+8WSL checks passed. Queue receipt: `results/vc4_padding_queue_20261010/receipt.json`.
  Current candidate is `vc4_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_r1`, launched07:47+07:00.
  Post-CTS signal11 is preserved in crashed-37; one unchanged diagnostic retry completed37/38/39 and did not
  reproduce the crash. Cause remains undetermined; no hardware attribution. Its219 input hashes and synthesis
  netlist match the prepared inputs and unpadded baseline. Evidence: `results/vc4_postcts_crash_20261010.json`.
  This remains one interrupted full-flow execution, not a paired/sign-off result. Actual p1 PASS with GRT overflow0,
  STAMidPNR-2 nom_tt_025C_1v80 setup+1.51761ns/hold+0.181665ns. Fresh firstGRT STA screen completed,
  nom_tt setup+0.491013ns/hold-0.202347ns at9 endpoints, hold skew-1.719956ns; all219 inputs unchanged.
  Completed P2 has the same9 small hold endpoints, nom_tt setup+0.491013ns,
  hold-0.202347ns, overflow0. The actual p2 gate FAIL remains recorded; a manual CONTINUE documents the
  standard-cell old_main_block[7] -> mux2_1 -> vc_block[1][7] path and retained extracted-RC hold ECO.
  Step43 STOPPED at2026-10-11 03:19:20+07. Main detailed routing reached DRC0, but the first post-DRT
  antenna repair ended with native fatal GRT-0232, Routing congestion too high. It found2243 violating nets/
  3211 pins, then repair inserted5978 diodes. No runtime/state_out, extracted timing or sign-off exists.
  This is one failed execution, with no watchdog-abort or hardware-fault evidence; do not retry unchanged.
  Diagnosis: `results/vc4_postdrt_antenna_failure_20261011.json`. Preserve step43 and all failed artifacts.
  The earlier CPU sampling correctly located FastRoute but did not establish termination or a machine fault.
  P2 evidence remains `results/vc4_padding_initialgrt_20261010/p2_inspection.json` and p2_path_diagnosis.json.
  No PD process is currently running. DM exact GLS pass1 finished12/12 at06:48+07. Original pass2 stopped
  at04:59+07 after6 complete cases: md5sum simulation itself passed, but Windows SAIF conversion raised
  an anomalous TypeError at an integer increment. The old power queue stopped correctly; both failed receipts
  remain unchanged. An isolated unchanged conversion replay verified314 frozen inputs and produced the
  same pin-SAIF bytes as pass1; hardware cause remains unproven. Diagnostic:
  `results/gls_pin_conversion_retry_20261011/receipt.json`. A fresh full pass2 with a new private compilation
  started14:36+07 with a fresh private compile: `results/gls_exact_dm_full_p2_retry_20261011/receipt.json`.
  Pipeline: `results/exact_power_queue_dm_retry_20261011.json`, launched by
  `scripts/maintenance/run_dm_capture_power_retry.ps1 -Run`. Strict25-command pair verification remains
  unchanged;26 fresh STA jobs start only after the complete pair passes and Windows free>=7000MiB.
  Latest2026-10-12 18:03+07 check: the retry pass stopped after7 cases and the eighth successful simulation
  because a frozen TT library read through wsl.localhost raised Errno22. All16 native commands had exit0.
  Continuation prepared314 source hashes and all successful outputs; it resumed the same private compilation,
  converted the eighth raw SAIF and now has8/12 complete, up_slre running. No new compilation or repeated
  completed simulation was needed, and the original stopped receipt/queue are preserved byte-exact under
  `results/gls_exact_dm_p2_continuation_20261012/`. Controller resumed with -Resume -Run; strict25-command
  pair verification and26 fresh STA remain prerequisites. The foreground monitor is active with600second polls.
  SA2 step46 completed routeDRC0/antenna0/placement0; P4 is queued in the foreground behind Windows/WSL
  available>=15000MiB. `P4_RESOURCE_WAIT=1 bash run_resource_gated_resume.sh ... hold` delegates to the
  unchanged gated driver after resource readiness; no owner application is stopped. Current Windows free
  about12600MiB is below the queue threshold. Routing audit:
  `results/sa2_minimality_screen_20261011_3325/detailed_routing_audit_20261012.json`.
- Board reference simulation completed 10:56 UTC: 100 paired rows (200 independent cases), every counter equals
  R14 on current RTL 6c4ccffd; inputs/output hashes checked. The reference PID has exited normally. FPGA fits completed
  at 56/56 additional fits; the common ten-seed matrix is verified. Physical board remains NOT_RUN.

J1. DM_VC4 detailed routing: run dir `asic/soc_vc4_4kb/runs/vc4_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd_r1`,
    started by `run_gated_resume.sh ... drt`, which then runs the sign-off part (PostRouteHoldECO .. Checker.LVS) and
    the final gate by itself. `asic/drt_watch.sh` stops a detailed routing that cannot converge (thresholds in
    QUY_TRINH.md section D: iteration 5 > 20,000, 10 > 5,000, 20 > 600, 30 > 400, 40 > 200; no limit after 40).
    Violation counts at 06:56 UTC: 161,333 / 95,248 / 89,365 after the first three passes (SA2 r2 at the same points:
    103,892 / 48,827 / 45,440, then 5,822 / 1,289 / 308; DM r14F_A: 114,374 / 62,655 / 58,640, then 12,993). If the
    watchdog stops it, read `drc_iter_*` reports and `asic/fp_tools/pin_hotspots.py` before any new run.
    - finished normally: `gated_pd.log` has "... sign-off part done" and a GATE final line. Go to task T1.
    - died: the highest-numbered step dir has no `runtime.txt` / `state_out.json`. Rename that step dir to
      `crashed-<NN>-<name>` (OpenLane numbers resumed steps after the highest existing number), write a NOTE line to
      gated_pd.log, then resume with the matching mode:
      `bash run_gated_resume.sh soc_vc4_4kb vc4_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd_r1 config_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd.json '<reason>' drt`
      (or `hold` if detailed routing finished, or `step:<StepID>` to restart the sign-off part at a given step).

J2. SA2 GLS for activity power (Windows side, Questa, 2 jobs): output `results/gls_power_sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1/`.
    At handover 8 of 12 kernels had PASSED (self-check, mcycle = ASIC-view RTL); up_slre and up_statemate were
    running, up_tarfind and up_ud queued. One kernel takes ~50 min.
    - finished: `results/gls_power_<tag>.csv` has 12 rows with match=YES, saif=YES. Go to task T3.
    - died: re-run only the kernels without a "GLS_RESULT" line in their log, then rebuild the full CSV:
      `JOBS=2 bash asic/gls/run_gls_power_cfg.sh asic/soc_sa2_4kb/runs/<tag>/56-openroad-fillinsertion/soc_asic_top.nl.v <tag> results/dse_asic_view_p1.csv SA2 <missing kernels...>`
      `bash asic/gls/gls_power_csv_rebuild.sh <tag> results/dse_asic_view_p1.csv SA2`

J3. (finished 06:35 UTC) SA2 synthesis replay with one snapshot hook (`SYNTH_PY=synthesize_n1only.py`, output
    `asic/equiv/lec/synth_replay_r14/sa2_rsztf_r1_n1only/`): REPLAY NETLIST BYTE-IDENTICAL TO STEP 06, so its
    `n1_pre_abc_fast.il` is OpenLane's exact N1 state for an SA2 LEC (task T8). The 4-hook replay of the same run
    DIFFERED (77,157 vs 77,562 cells): extra snapshot passes change Yosys's process state.

## 5. Ordered task list

T1. Finish DM_VC4 sign-off on 12.24 mm2 (run of J1)
    - J1 deterministically failed the iteration-10 gate; the instructions below for its post-route stages are
      conditional on a future successful recipe. Do not resume the failed detailed routing unchanged.
    - One written spacing hypothesis ran from step1, passed P1 and was continued through the documented
      small P2 hold failure. It failed post-DRT antenna repair with GRT-0232 (section4), without sign-off.
      Do not repeat unchanged; an evidence-based repair hypothesis is required before a new experiment.
      Original preparation: `results/vc4_padding_hypothesis_20261009.md` and
      `results/vc4_padding_preparation_20261009/inputs.json`. New configs add only GPL/DPL padding 2 (one site/side)
      on the same 12.24 mm2 die; retain all other pre-/post-GRT knobs, default resizer corners and clock layers.
      Candidate tag `vc4_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_r1`; first run from step 1 and hold
      after p2 for clock/congestion diagnosis. The queue keeps its foreground WSL client for the whole flow;
      adequate actual memory remains a prerequisite. Use section4's current queue receipt, not the old J1 command.
    1. Read the final gate line. Expected: everything clean except possibly hold at an ff corner (one extraction per
       ECO pass) and possibly setup at max_tt (see risk in section 3).
    2. Hold at ff < 0: second hold ECO exactly as SA2. Find the PostRouteHoldECO step number N
       (`ls runs/<tag> | grep postrouteholdeco`), then
       `bash branch_run.sh soc_vc4_4kb <accepted_r1> <accepted_ecomaxmin_r1> <N>`
       `bash run_gated_resume.sh soc_vc4_4kb <accepted_ecomaxmin_r1> <matching_ecomin_config> '<reason>' hold`
       Use the accepted recipe's tag and matching `_ecomin` config, including `pad1` when accepted. Do not use
       the failed unpadded J1 as the parent. The second ECO changes only `POST_ROUTE_HOLD_ECO_RCX_CORNER` to min_*.
    3. Setup < 0 at a tt or ff corner: do NOT relax the SDC or the clock. Diagnose the path first
       (`max.rpt` of the STAPostPNR corner, `asic/sta_query/`). The post-route ECO has a setup mode
       (`POST_ROUTE_ECO_SETUP`, `POST_ROUTE_ECO_CORNERS` = tt only, `POST_ROUTE_ECO_HOLD` false, then a separate hold pass);
       its STA uses only the extracted SPEF (traps in QUY_TRINH.md section D). It can resize the buffers on the
       critical half-cycle path; it cannot buffer (no wire estimates in that session). Record every attempt.
    4. Acceptance: "SIGNOFF CLEAN <tag>" in gated_pd.log.
    5. If the hold count after detailed routing is again in the thousands (skew changed): stop, compare the guides of
       the GRT step with `asic/fp_tools/clock_detour.py <def> <guide>` and `clock_layers.py <guide>`, report to the
       owner. Do not start more knob experiments without a new hypothesis.

T2. DM_VC4 double execution (only after T1 is clean)
    - Use the recipe actually accepted by T1, including the same padding and branch procedure if those are needed.
      The historical unpadded command below is not authorization to launch it after its deterministic DRT failure.
    - `P2_MIN_SETUP=0 ITEMS='soc_vc4_4kb:vc4_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd_r2:config_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd.json' bash run_gated_pd.sh`
    - use `P2_INITIAL_GRT_FALLBACK=1` when post-GRT design repair is off. Compare actual completed first-GRT
      data and nom_tt timing to r1; a FAIL or HOLD is not a PASS. Continue only with the documented gate reason
      and a CONTINUE line, then `run_gated_resume.sh ... drt` and the matching second-ECO branch procedure.
    - compare r1 vs r2: every metric (merge of all `*/state_out.json` in step order, excluding runtime / flow__),
      sha256 of the first GRT guide, of the final netlist and DEF (`*-openroad-fillinsertion/soc_asic_top.nl.v / .def`);
      SPEF may differ only in `*DATE`. `scripts/metrics/asic_compare.py DM=... SA2=... DM_VC4=<r1>:<r2>` does the
      metric comparison and writes the table.

T3. Activity-based power (SA2 now, DM_VC4 after T2)
    Historical SA2 calculations are double-verified. Exact-window DM/SA2 recapture is now required by the raw
    audit above; use a new observer/private library without changing frozen RTL, TB or firmware. Independently
    require elapsed time = TB cycle count *20 ns = MCYCLE *20 ns and every SAIF span before paired STA.
    DM_VC4 remains pending T1/T2. Existing power inputs/reports are retained unchanged.
    - The exact mapped freeze aliases and all32 MCYCLE increment/D consumers are locally proven twice for DM
      and SA2:65 obligations/design/pass. A separate raw-netlist/PDK interpreter rebuilt the roots and replayed
      252 paired CNF certificates/340,338 resolution steps, eight structural roots and12 wrong-observer witnesses.
      Receipts: `results/mapped_counter_freeze_checked_20261010/{verification.json,independent_review.json}`.
      This is a local Boolean observer justification, not full LEC, initialization, other-counter or delay proof.
    - DM single-kernel `up_ud` exact-window screening completed2026-10-10 20:02+07: native compile/sim/conversion
      exit0, LEDRa5, MCYCLE=win_cycles=144388, elapsed2887760000ps and all99471 raw SAIF spans match.
      `results/gls_exact_dm_ud_screen_20261010/receipt.json` is SINGLE_SCREEN_NOT_RESULT; frozen inputs retained.
      Full12-kernel independent passes started2026-10-11 00:29+07 and00:30+07, each with a fresh private compile:
      `results/gls_exact_dm_full_p1_20261011/receipt.json` and `results/gls_exact_dm_full_p2_20261011/receipt.json`.
      Foreground RAM waits are opt-in at6000MiB. A foreground queue waits for both passes, strictly verifies
      `results/gls_exact_dm_full_pair_20261011.json`, then launches26 fresh STA jobs under
      `results/activity_power_exact_dm_20261011/` when Windows free>=7000MiB. A failed capture/pair stops the queue.
      The original pass1 finished12/12; pass2/queue stopped on an anomalous Windows conversion error.
      Its single unchanged diagnostic replay passed with byte-identical pin-SAIF, but does not complete pass2.
      Fresh full-pass2 and queue receipts are `results/gls_exact_dm_full_p2_retry_20261011/receipt.json` and
      `results/exact_power_queue_dm_retry_20261011.json`; new accepted-pair output will be
      `results/gls_exact_dm_full_pair_retry_20261011.json`, then power under
      `results/activity_power_exact_dm_retry_20261011/`. No new power result yet. No verifier was weakened,
      no failed command removed and no partial pass promoted to PASS.
    - DM secondSTA is COMPLETE and verified: 12 activity kernels and vectorless run independently repeated;
      all six power groups/origins match. Fixed GLS/SAIF/netlist/RCX inputs were reused and remained byte-identical.
      Evidence: `results/dm_activity_power_second_pass_20261010.json`; no PD rerun or locked-layout change.
    Verification command: `python scripts/metrics/verify_activity_power.py --tag sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1 --design soc_sa2_4kb --step 59-openroad-stapostpnr --ref-csv results/dse_asic_view_p1.csv --config SA2`.
    - SA2, after J2 (PowerShell 7, from `E:\Projects\RISCV-research`):
      `pwsh -File asic\gls\power_cfg.ps1 -Design soc_sa2_4kb -Tag sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1 -Step 59-openroad-stapostpnr -Fill 56-openroad-fillinsertion -RefCsv results\dse_asic_view_p1.csv -Config SA2 -Pass 1`
      then the same with `-Pass 2` (second execution of the STA power; compare `*.power.rpt` with `*.power.p2.rpt`).
      Output `results/gls_power_<tag>_power.csv` (total / dynamic / leakage per kernel at nom_tt with RCX parasitics, EPI).
    - DM_VC4: same two steps with `-Config DM_VC4`, the netlist / STAPostPNR step numbers of its final run.
    - The SAIF -> pin conversion runs in Windows Python (WSL Python faults on this machine). Method notes:
      `NHAT_KY.md` section 9 "Cong suat" and the activity-power notes in NHAT_KY.md section 9 (read_saif ignores flat nets;
      unknown-activity share is reported).

T4. SA2 minimality proof (rule: the next smaller die must fail with the same recipe)
    - PAIRED FAILURE at P2, r1 at2026-10-10 15:01:55+07 and r2 at20:35:09+07: tag
      `sa2_corr3400x3250_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1`. Fresh nom_tt_025C_1v80 setup is
      -0.331932 ns at10 endpoints, hold -0.0579186 ns at4 endpoints, post-GRT overflow16. Worst setup is the
      half-cycle I-cache way1/bank1 SRAM dout1[25] to if_req_addr[31]: arrival23.654978 ns, required23.323046 ns.
      No other fresh corners or DRT/sign-off exist; inherited pre-PnR corners are not sign-off evidence.
      Only die/core/placement geometry changed. Receipt: `results/sa2_minimality_screen_20261010/first_execution_audit.json`.
      The second independent full-step1 `_r2` completed with the same failure:568 metric fields, resolved config,
      N1 and first-GRT netlist/DEF/guide match. `results/sa2_minimality_screen_20261011_pair.json`.
      The geometry-only3325 full-step1 candidate started2026-10-11 02:56+07 with STOP_AFTER=p2/P2_MIN_SETUP=0
      after the Windows>=10000MiB and WSL resource gates. P2 PASS completed03:42:58+07, then the driver
      held intentionally at STOP_AFTER=p2: fresh nom_tt_025C_1v80 setup+0.762128ns/hold+0.045411ns,
      zero setup/hold endpoints and post-GRT overflow0. This is one execution only, without DRT or sign-off;
      inherited pre-PnR ff/ss fields are excluded. Audit:
      `results/sa2_minimality_screen_20261011_3325/first_execution_audit.json`. Queue receipt:
      `results/sa2_minimality_queue_20261011.json`. Current RTL manifest227 files is unchanged.
      No minimum-area result is claimed. Gated DRT resumed17:27:25+07, step46 is CPU-active under
      G5_UNLIMITED_LATE_PHASE=1. HOLD_AFTER_DRT=1 holds before P4 for a fresh Windows/WSL resource check:
      Windows free13,359MiB versus potential14GiB Magic working set. The existing runtime/convergence checks
      remain active. Continuation evidence: asic/gated_pd.log and results/gated_resume_phase_hold_20261011.json.
      Step46 completed2026-10-11 18:37+07: runtime01:08:19.415, routeDRC0, fresh antenna nets/pins0/0,
      placement0. Ignore inherited route__antenna_violation__count459; no fresh post-route timing or LVS yet.
      On2026-10-12 the resource-gated foreground P4 queue started and waits for Windows/WSL15000MiB before
      first max_* ECO and sign-off. If ff hold remains negative, use the original same-recipe ecomin branch
      procedure; no clock/SDC relaxation. This remains the first full-flow execution; sign-off and an independent
      full-step1 repeat are still required. Gate/WAIT evidence is in asic/gated_pd.log.
    - Both 3250/3325 max-first-ECO and `_ecomin` second-ECO configs are generated and checked
      by `asic/fp_tools/prepare_sa2_minimality.py`; receipt `results/sa2_minimality_preparation_20261009.json` records
      source/output hashes, the three changed implementation fields and LEF-based macro geometry (16 macros inside
      the core, no overlap). Run 3250 first; 3325 only if 3250 fails. WSL-terminal/resource prerequisites above apply.
    - Ladder at 50 MHz with the final SA2 recipe: 10.54 mm2 (3400 x 3100) FAILED (max_tt -0.573, I$ way-1 half-cycle
      read path); 11.05 mm2 (3400 x 3250) failed P2 setup twice; 11.305 mm2 (3400 x 3325)
      passed P2 once with the final recipe but has no DRT/sign-off; 11.56 passes.
    - Make `config_corr3400x3250_f220_capm20_fo16_pad1_tdp_clkm3_rsztf.json` from the 11.56 config changing ONLY
      `DIE_AREA` [0,0,3400,3250], `CORE_AREA` [12,12,3388,3238], `MACRO_PLACEMENT_CFG` dir::macro_placement_corr3400x3250_f220.cfg
      (exists; check its header says cache orientation F, gap 220). Run it like the 11.56 recipe (full flow, branch +
      second ECO). If it signs off: double-execute it and it becomes the SA2 result. If it fails, try 11.305 the same
      way (`macro_placement_corr3400x3325_f220.cfg`, DIE_AREA [0,0,3400,3325], CORE_AREA [12,12,3388,3313]). Record
      each die result in NHAT_KY and RESULTS.md.

T5. DM_VC4 minimality (after T2)
    - PREPARED, NOT EXECUTED: `results/pd_minimality_preflight_20261010.{md,json}` verifies all6 candidate configs,
      16 macro/halo rectangles and241 unchanged existing inputs. The old3500 recipe changes4 nongeometry knobs
      and cannot prove minimality of the current recipe. New3500 pad1 base/ecomin configs and
      `macro_placement_corr3500x3400_f220_pad1.cfg` change only die/core/placement from the current3600 pad1
      candidate. Use them only if T1/T2 accepts that exact recipe; otherwise rederive. Smaller-die failures used
      as proof also need two independent full flows. The driver holds afterP2, notP1. BeforeDRT measure firstGRT
      skew from its actual completed directory, never assume a numbered step. Use
      `bash fp_tools/grt_skew_screen.sh soc_vc4_4kb <run> <config> <run>_grtskew_scr` on the single intended first
      GRT state. A hold skew around -2.0 ns and a few hundred endpoints at most = continue; thousands of
      endpoints = clear failure, stop it with a logged reason.

T6. Final PPA table for DM / SA2 / DM_VC4 (owner's required content)
    - VERIFIED SUBSET updated: `results/asic_ppa_verified_subset_20261010.md` / `.json`, generated by
      `scripts/metrics/asic_ppa_audit.py`. DM and SA2 pass the unchanged final gate in both runs, match all 319
      metric fields with identical full key sets, final netlist/DEF and all three normalized SPEFs. Includes all
      nine named timing corners, flow buffer classes/per-ECO insertion counts, final DEF master census, verified
      DM/SA2 activity power and current-RTL paired Embench counters. Seventeen evidence-rejection controls passed.
      It is not the final T6 result: DM complete sequential LEC closure, SA2 minimality/final LEC and VC4 sign-off
      are still pending; DM secondSTA is verified. The numerical PD/power table is unaffected by the LEC audit.
    - Per configuration: sign-off gate (pass/fail list) first; die and core area; std-cell area and count; total buffer
      count by class (timing repair, clock, hold, macro-pin); total wirelength; setup / hold WNS with corner names;
      dynamic + leakage power from OpenSTA with SAIF (state corner nom_tt and the RCX parasitics), vectorless for
      reference; the sign-off knobs each design used and why; Embench CPI and I$ / D$ hit rates (FPGA view,
      `results/unified_metrics.md`, `scripts/metrics/unified_table.py`).
    - Generator: `python scripts/metrics/asic_compare.py DM=soc_dm_4kb:r14F_A:r14F_B SA2=soc_sa2_4kb:<r1>:<r2> DM_VC4=soc_vc4_4kb:<r1>:<r2> --out results/asic_compare_<date>.md`.
    - State honestly that knobs differ between the three designs (part of the buffer / power difference comes from the
      knobs, not only from the cache organisation), and that DM_VC4 needs a larger die.

T7. Board runs with the current RTL 6c4ccffd (review A7; the owner provides the DE2-115 board)
    PREPARATION COMPLETE: 56/56 additional fits recorded, 40 paired point/seed rows verified, 100 seed2 SOFs ready.
    PHYSICAL MEASUREMENT NOT_RUN: the two-pass session remains deferred.
    The stopped coordinator's original invocation refuses an existing status/output path; inspect and preserve
    receipts before preparing a continuation. Do not reset progress, repeat completed measurements or remove fitdb.
    No fit/SOF job is active; Windows RAM remains below the runner's 6,000-MB guard as of the audit check.
    Update 2026-10-09: compare all four configurations at the SAME seeds 1..10, twice; no per-configuration best-seed
    selection. Existing seeds 1..4 are double-executed evidence; any reused rows retain their original provenance.
    The physical board uses seed 2 for ALL FOUR configurations, fixed before the expanded results are seen.
    Prepare the new SOFs first; the physical session will be scheduled later.
    1. Confirm `hdl/` matches manifest 6c4ccffd: `python scripts/rtl_manifest.py --check`. WITHOUT `--check` the
       script REWRITES `results/rtl_manifest.json` (that is a freeze; only after an approved RTL change).
    2. The four point projects (`point_dm_4kb`, `point_sa2_4kb`, `point_vc4_4kb`, `point_dse_4kb`) must hold a fit of
       6c4ccffd at the common seed 2 approved on 2026-10-09; refit each point
       sequentially if its database is not that fit. Note: `quartus_sh --seed` writes the seed back into the .qsf.
    3. The SOF builder `scripts/fpga/build_board_matrix_r14.py` hard-codes RTL_ID 3ea52396 and R14 expected CSVs. Make
       a new builder (content name, e.g. `scripts/fpga/build_board_matrix.py`, output
       `output_files_board_matrix_6c4ccffd/`) that reads the RTL id from the manifest. Each SOF = that point's fit +
       the firmware's MIFs via `quartus_cdb --update_mif` + `quartus_asm` (no new fit); canonical MIFs restored at the end.
       New builder prepared: `scripts/fpga/build_board_matrix.py` (default readiness check; `--build` assembles).
       It requires the complete paired10 fit receipt at common seed 2 and the verified current-RTL reference before
       changing MIFs. It writes `output_files_board_matrix_6c4ccffd_seed2/`, INDEX.csv, a two-pass physical-results
       template, and canonical-restoration status. All100 SOFs are built and independently audited; canonical
       MIFs and all four canonical assemblies were restored. No new assembly is needed before the physical session.
       Builder rejection checks: 11/11; final evidence-association audit negative controls: 5/5. Validation artifacts:
       `results/board_builder_guard_validation_20261009.json`, `results/board_preparation_audit_validation_20261009.json`.
    4. Expected values: regenerate the expected MCYCLE / MINSTRET per kernel x configuration on the CURRENT RTL in
       simulation (FPGA view, the same harnesses that made `results/upstream_r14_4kb_p1.csv`,
       `results/ramsweep_r14_p1.csv`, `results/upfull_r14_4kb_p1.csv`), twice, and check they equal the R14 values
       (6c4ccffd is cycle-exact). Never use BENCHMARK_FAST_UART for these: it shifts mcycle on some kernels.
       `fw_board/upfull_*.hex` are the 12 kernels at their official iteration counts (too long for routine simulation).
       Current reference job verified: `python scripts/fpga/prepare_board_reference.py --run`, tag
       `board_reference_6c4ccffd_20261009`, log in results/; two private-library lanes, fresh compilation in each pass,
       25 images x 4 configurations x 2 simulations; require all counters identical to R14. 100/100 paired rows identical to R14; every field compared, no ignored columns.
    5. Board session: program each SOF with `quartus_pgm -c USB-Blaster -m JTAG -o "p;<file.sof>"` (do NOT use the
       published repo's `program_de2_115.ps1`). Pass criteria per SOF (same as `asic/gls/tb_gls_soc.sv`): LEDR shows
       0xA5 (firmware self-check passed; 0xEE = failed) and HEX7..HEX0 show the MCYCLE of the measured region, equal
       to the expected value (INDEX.csv column expected_mcycle_hex); capture the UART output
       (115200 8N1) when a serial cable is connected. Run the whole matrix twice; save photos / logs under
       `results/board_<date>/` and a CSV with expected vs observed. Record in NHAT_KY, RESULTS.md (FPGA section) and
       REVIEW_RESPONSE.md (A7).

T8. Complete sequential LEC closure (DM audit; SA2 done x2 on 2026-10-14 except its NegB control; DM_VC4 synthesis
    part running, B after sign-off; authorized in the current scope)
    - The stock OpenLane EQY step does not pass on this design. Retain DM's historical register-mapped
      chain `asic/equiv/lec/run_lec_r14.ps1` (-Step A / B), `run_lec_r14_mul.ps1`, `run_lec_r14_pass2.ps1` (pwsh7)
      and its SAT/CEC/algebra/negative evidence. The new structural clock audit closes the positive-edge scalar
      clk obligation on all four preserved flat models in two executions (`results/dm_lec_clock_audit_20261010/receipt.json`).
      Six AXI next-code cofactors are now closed by paired bounded BDD computations and independently by exhaustive
      original-AIG evaluation (36,864 assignments/pass); other raw Q, including lec_q_g00088, stays free. Receipt:
      `results/dm_axi_exhaustive_audit_20261010_receipt.json`. All14 ALU cases passed two independent exact-CNF
      computations, report bytes identical, without heavy SoC tools alongside PD.
      Independent parser/cofactor/Tseitin/resolution review passed all28 ALU proofs and2 fault baselines;
      73,296 resolution steps replayed. Source/raw initial-state/full LEC scope stays OPEN.
      Current gold joint235constant/28duplicate/four-group invariant induction also passed all286 obligations
      twice, byte-identically. Independent construction/replay verifies266 structural targets and40 paired CNF
      certificates (74,938 resolution steps); independent raw reset-base review introduces no state ties or
      invariant premises. Receipts: `results/dm_joint_invariant_20261010_verification.json`,
      `results/lec_joint_invariant_independent_review_20261010.json`,
      `results/lec_joint_reset_base_independent_review_20261010.json` and
      `results/lec_onehot_cnf_independent_review_20261010.json`.
      Sampled reset release/reassertion now passes all 1,716 obligations twice (1,696 structural /20 CNF);
      independent six-phase reconstruction and 40 certificate replays /74,938 resolution steps pass.
      Receipts: `results/dm_reset_phase_20261010_verification.json` and
      `results/lec_reset_phase_independent_review_20261010.json`. An unexplained first-review TypeError and the
      unchanged-command successful diagnostic retry are preserved in
      `results/lec_reset_phase_review_execution_20261010.json`; no hardware-fault attribution is made.
      Local BHT update/read definedness also passes twice: 257 classified X/Z connect lines closed;
      no initial-zero or legal-state assumption. Evidence: `results/lec_source_definedness_20261010_verification.json`
      and `results/bht_read_default_definedness_20261010_verification.json`.
      Independent raw selector/B-data reconstruction confirms 256 read addresses and 2,048 update cases:
      `results/bht_definedness_independent_review_20261010.json`; it imports neither BHT checker's parser/evaluator.
      UART baud adds one local default closure, all four free configuration codes checked twice and separately
      reviewed with another parser: `results/uart_baud_default_definedness_20261010_verification.json` and
      `results/uart_baud_definedness_independent_review_20261010.json`. Three I-cache hot-array unused defaults
      also pass twice and a separate raw-IR parser/data-order review: 24 free index cases,1,224 symbolic data bits,
      six actual selector/data faults per pass. Receipts: `results/icache_hot_default_definedness_20261010_verification.json`
      and `results/icache_hot_definedness_independent_review_20261010.json`. The49 main-RAM defaults also pass
      twice and a separate raw-IR/source-binding review:392 free-bank cases and98 actual selector/data faults
      per pass,398 B-data atoms remain symbolic. Receipts: `results/ram_bank_default_definedness_20261010_verification.json`
      and `results/ram_bank_definedness_independent_review_20261010.json`. Total310 classified connect lines
      locally closed,48 open; selected B-data/whole-output definedness and RAM initialization are not established.
      The97-row map `results/lec_source_x_remaining_20261010/` is the retained snapshot before the RAM proof;
      current remaining48 are14 PMUX defaults,7 mux lines and27 module connects. No full-LEC promotion.
      Unrestricted raw-frontend recipes are prepared in `results/dm_raw_frontend_preparation_20261010/`, not
      executed; X/undriven guards currently block them. Between-edge asynchronous reset, paired GOLD/N1/final
      initial-state coupling, whole-source undefined-value abstraction and full sequential LEC remain OPEN.
      Before using the chain as an unconditional sequential proof, close
      reset base on raw unrestricted graphs, clock/edge correspondence, exact-input invariants and complete
      residual-output closure. `scripts/verification/lec_reset_base.py` proves only gold reset sub-obligations.
    - Prerequisite: a byte-exact replay of the run's synthesis (`asic/equiv/lec/synth_replay_r14/run_replay_r14.sh`).
      For SA2 it exists (J3: 1-hook replay byte-identical). The DM chain also needs the multiplier closure, whose t1
      replay (one techmap iteration snapshot) must be redone for SA2 and checked; Yosys maccmap grouping depends on
      process state. The gold side must be built from `asic/snapshots/rtl_r14` with the SA2 cache configuration.
    - Isolated frontend/replay preparation: `results/completion_preparation_20261009/sa2_lec_20261009/`.
      All 77 inputs and 24 generated artifacts were hash-checked. This is preparation, not a mapped/SAT proof;
      multiplier closure, independent pass2 and proof negative controls still require implementation/execution.
    - Until then, RESULTS.md must keep saying that SA2 / DM_VC4 have no RTL-to-netlist proof (GLS mcycle equality on
      12 kernels is the functional evidence).

T9. Gate script follow-up (when no flow runs): `asic/fp_tools/gate_check.py p2` reports "MISSING p2 data" when
    `RUN_POST_GRT_DESIGN_REPAIR` is false. COMPLETE: `P2_INITIAL_GRT_FALLBACK=1` enables the corrected reader only
    for explicit false in resolved.json. It reads the last post-GRT reroute if present, otherwise the completed
    initial GlobalRouting before STAMidPNR-3. Off by default; all thresholds and the final gate remain unchanged.
    All 34 controls passed, including existing DM/SA2/VC4 runs and negative missing/setup/hold/overflow cases:
    `results/gate_p2_no_repair_20261009/verification.json`. The stopped VC4 candidate still FAILS p2 on negative hold;
    this fix does not grant permission to continue. Procedure documented in QUY_TRINH section D.

T10. Cleanup (archive and dependency checks required)
    - EXECUTED WITHIN THE REQUESTED WORKSPACE CLEANUP: 17 archived, dependency-free runs removed, 82,819,435,929
      logical bytes (77.132 GiB). Receipt: `results/workspace_audit/cleanup_execution.json` and cleanup_deleted.txt.
      Two formerly proposed runs are retained: VC4 clkm3_pad1_r1 supplies three retained screening branches.
      final_B's six LEC/replay inputs are now byte-archived and all 14 readers migrated, but its subsequent native
      deletion was blocked by automatic tool review. Source remains intact; do not retry the blocked deletion.
      Evidence: `results/final_b_dependency_migration_20261009/cleanup_outcome.json`.
    - The original `results/cleanup_proposal_20261009.md` / `.json` separated the inventory
      inventory into 19 PROPOSE_ONLY, 10 KEEP and 11 DEFER runs. The 19 proposed runs have hash-checked text evidence
      archives under results/pd_run_archive/<run>/ (resolved config, merged metrics, step list, logs and reports).
      Their original inventory sum is 89,857 MB, not a guaranteed reclaimed amount; archives retain 7,923 MiB of
      text evidence. Two branches lack resolved.json and remain deferred, as do synthesis provenance and the VC4
      controls needed by T5. The execution receipt supersedes the old proposal's no-deletion status.
    - Twenty obsolete source/document/coverage originals are ZIP-archived and hash-checked, but removal and the
      golden-helper rename were rejected by automatic tool review (blocked by policy). Originals remain untouched;
      see results/source_archive/retired_sources.json. Do not retry with another interpreter/tool.
    - Original inventory with sizes: `results/cleanup_candidates_20261009_sizes.txt` (includes protected runs;
      use the classified proposal above). Possible cleanup: failed / superseded SA2 and
      DM_VC4 runs of 2026-10-06 .. 09, the old 3600 / 3800 DM_VC4 runs once T5 no longer needs them, `final_B`,
      `r14sat_synth` only after provenance review, the `*_grtscr_*` and `*_grtskew_scr*` screening runs,
      `work_glsp_*` Questa libraries after T3.
    - Keep: signed-off runs (r14F_A/B, final3_A/B, the SA2 `_ecomaxmin_r1/_r2` and their `_rsztf_r1/_r2` sources, the
      final DM_VC4 runs), dmuA / dmuB (reported corridor controls), synthesis evidence runs, golden snapshot, SOF
      matrices, logs, double-executed CSVs, `asic/evidence/`.
    - Procedure: archive evidence per run into `results/pd_run_archive/<run>/`, list in `results/cleanup_deleted.txt`,
      add a row to NHAT_KY section 10.

T11. Git (owner decides): branch `experimental-r14` has ~220 uncommitted changes (docs, configs, scripts, RTL of
     6c4ccffd, tb). Commit only when asked; English ASCII messages; no Co-Authored-By; never check out `main` while
     jobs run.

T12. Manuscript items (M3 related work, A5 caption, minor text items): owner-maintained; the paper is
     not edited in this workspace.

## 6. PD knowledge already paid for (do not rediscover)

- STAMidPNR ss / ff numbers are stale pre-PnR values; mid-PnR gates use nom_tt only. Use STAPostPNR for real numbers.
- PostRouteHoldECO annotates ONE extraction (`POST_ROUTE_HOLD_ECO_RCX_CORNER`, default max_*) for every corner: one
  pass fixes one RC extreme; two passes (max_* then min_*) closed SA2. min_* alone broke max_ff.
- ECO STA traps: calling estimate_parasitics before read_spef keeps the session on estimates; the SRAM macro has one
  TT .lib, kept by the first corner read (STA-1140) - setup ECO with the tt corner alone.
- `RSZ_CORNERS` tt / ff: with the default (tt, ss, ff) the resizer chases ss (-9 ns, ~7,600 endpoints) for hours. The
  DM_VC4 3600 candidate keeps the default only to reproduce its known-good first global route.
- Post-GRT DRV repair with cap margin 50 + LAYERS_RC over-buffers the tag clusters (~4,650 buffers); cap 20 is used.
- MAX_FANOUT 16 helps SA2 (-27 % resizer buffers) and FAILS DM_VC4 (GRT overflow 1,272).
- Global-route antenna repair floods DM_VC4 with 11,000-17,000 diodes; DM_VC4 uses detailed-route antenna repair only.
- Clock trunks: `RT_CLOCK_MIN_LAYER` met3 helps SA2; on DM_VC4 neither met3 nor met4 stops the detours.
- `OpenROAD.RepairDesignPostGRT` re-runs a full global route after its repair; any full global route can re-route the
  clock trunks differently. `Odb.DiodesOnPorts` is a no-op here (`DIODE_ON_PORTS` none).
- Diagnostics (read-only, Windows Python): `asic/fp_tools/guide_demand.py` (demand map, diff of two guides),
  `region_cells.py` (cells in a box), `clock_detour.py` (clock guide length vs HPWL), `clock_layers.py` (clock trunk
  length per layer), `pin_hotspots.py` (DRT hot spot forecast), `asic/fp_tools/grt_skew_screen.sh` (WSL; skew after
  a run's first global route), `asic/sta_query/` (STA queries on a signed-off run).
- `run_gated_pd.sh ITEMS`: the config path is relative to the design dir (`config_x.json`, not `soc_x/config_x.json`).
- OpenLane resume: new step dirs are numbered after the highest existing number; resume state = latest state_out.json.
- `branch_run.sh <design> <source tag> <new tag> <N>` copies steps 1..N into a new tag (source read-only).
- GLS logs are huge (verbose OpenRAM model): ~50 min per kernel for the SA2 netlist.

## 7. Do not

- Do not write to the published repository or edit the paper.
- Do not change RTL for PD reasons; do not touch DM r14F.
- Do not relax the clock, the SDC, or the sign-off gate; do not disable checks to make a flow pass.
- Do not run parallel screening sprays; do not run two Quartus fits at once.
- Do not edit a running script; do not kill healthy runs or the owner's processes.
- Do not delete run folders without the owner's approval.
- Do not report a single execution as a result.
