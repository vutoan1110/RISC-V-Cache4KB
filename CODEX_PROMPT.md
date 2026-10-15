You are taking over an ongoing hardware research project from another agent. Work carefully, follow the project's
written rules exactly, and prefer asking over guessing. The project owner supervises you. Reply to the owner in
Vietnamese; write project files in the language each file already uses (see section 8).

==========================================================================================================
1. THE PROJECT IN ONE PARAGRAPH
==========================================================================================================
A RISC-V RV32I + Zmmul SoC (5-stage pipeline, 2-bit branch predictor, AXI / AXI-Lite / APB buses, UART, timer,
hardware performance counters) with configurable instruction and data caches. The RESEARCH copy at
E:\Projects\RISCV-research answers a journal review (file danh_gia.txt) of a cache design-space paper. It uses 4 KiB
caches and a 16 KiB main RAM, with these cache organisations: DM (direct-mapped, 5-state controller, CACHE_CONFIG 0),
SA2 (2-way set-associative on the 10-state "DSE" core, CACHE_CONFIG 1), DM_VC4 (direct-mapped + 4-entry victim
buffer on the DSE core, CACHE_CONFIG 2), DM_DSE (direct-mapped on the DSE core, CACHE_CONFIG 3), SA4 (4-way).
It is verified in simulation (Questa, Verilator, UVM, Embench-IoT, CoreMark, ACT4 riscv-arch-test, random
differential), implemented on FPGA (Cyclone IV E EP4CE115 on a Terasic DE2-115 board, Quartus Prime Lite 20.1) and as
an ASIC (sky130A, sky130_fd_sc_hd, OpenRAM SRAM macros, OpenLane 2.3.10 local copy in asic/openlane-local, 20 ns
clock). The PUBLISHED 1 KiB version lives in E:\Projects\RISCV-AHB-APB-UART and is READ-ONLY: you may read it and
take data from it, never write to it.

==========================================================================================================
2. BEFORE YOU RUN ANYTHING
==========================================================================================================
Do these in order:
 a. Read E:\Projects\RISCV-research\HANDOVER_CODEX.md completely. It is the authoritative state and the ordered task
    list as of 2026-10-09 06:40 UTC (exact run names, configs, commands, acceptance criteria).
 b. Read E:\Projects\RISCV-research\QUY_TRINH.md completely (binding procedures, Vietnamese without diacritics).
    If QUY_TRINH.md and anything else disagree, QUY_TRINH.md wins; tell the owner about the conflict.
 c. Read NHAT_KY.md: all entries of section 8 dated 2026-10-08 and 2026-10-09 (the PD history and the reason for
    every knob), section 9 (known traps), section 10 (cleanup log) and section 11 (old -> new name aliases).
 d. Read RESULTS.md, REVIEW_RESPONSE.md and README.md.
 e. Check the jobs of HANDOVER_CODEX.md section 4 (J1 = DM_VC4 3600 detailed routing + sign-off, J2 = SA2 gate-level
    simulation for power, J3 = finished). They may have been killed when the previous session ended (the WSL VM stops
    when its last client exits). Use only read-only checks first: asic/gated_pd.log, the run directories, the GLS
    result files. Do not start, resume or delete anything during this check.
 f. Send the owner, in Vietnamese, a short report: (1) your understanding of the current state in 5-10 lines,
    (2) the status of J1 and J2, (3) the next three actions you plan. Then continue with the task list. For anything
    marked "owner decision" (section 7), ask first and wait.

==========================================================================================================
3. NON-NEGOTIABLE RULES (summary; QUY_TRINH.md has the full text)
==========================================================================================================
Scope
 - Work only inside E:\Projects\RISCV-research. Never write to E:\Projects\RISCV-AHB-APB-UART. Never edit the paper
   (manuscript items M3, A5 and the minor text items belong to the owner).
 - DM is LOCKED: runs r14F_A / r14F_B (also called dm_grid3665x2900_r1 / _r2), config
   asic/soc_dm_4kb/config_R14_FINAL.json, die 10.63 mm2. Do not re-run, modify or delete them.
 - SA2 is SIGNED OFF and double-executed (runs sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1
   and _r2). Do not redo its PD except for the minimality task T4 and the power task T3.

Measurements
 - Every measurement is executed twice and compared field by field; a single execution is never a result. "Twice"
   means a second independent run from the same inputs (for PD: a second full flow from step 1), not re-reading the
   same output.
 - One hypothesis per experiment. Do not launch several speculative runs in parallel ("spraying"). Running two
   different, already-justified jobs at the same time (e.g. a PD flow and a GLS) is fine if memory allows.
 - Subagents / parallel agents may only READ and analyse (logs, reports, documents). Every action that starts,
   stops, resumes or deletes a job, and every file edit, is done by the main agent, one at a time: this machine,
   its run directories and its memory are shared, and two agents acting at once can corrupt runs.
 - Debug from evidence. A clearly random machine fault (Python segfault, a corrupted Python object, WHEA error,
   random OOM, Quartus access violation, about 8 % of fits) may simply be retried; write a NOTE line saying so.
   A deterministic failure (DRC, LVS, setup or hold violation, a check that fails the same way twice) needs an
   engineering fix. Do not blame the machine without independent evidence.

RTL
 - The current RTL is manifest 6c4ccffd (results/rtl_manifest.json). Check it with
   `python scripts/rtl_manifest.py --check`. WITHOUT --check that script REWRITES the manifest; never do that unless
   an RTL change was approved and fully verified.
 - Do not change RTL unless the owner asks. Any RTL change must carry the whole chain of QUY_TRINH.md section C, in
   order (scripted change, manifest freeze, lint/latch, formal proof with a negative control for restructurings, full
   verification chain x2, Quartus 4 points x 4 seeds x 2 passes, PD from step 1 x2, GLS + activity power). New logic
   needs new tests. Nothing may be disabled or weakened to make a check pass.
 - PD never edits RTL. PD configs read RTL snapshots under asic/snapshots/ (rtl_r14 for SA2 / DM_VC4), never hdl/.

PD sign-off gate (hard limits)
 - route DRC 0, Magic DRC 0, KLayout DRC 0, LVS 0 (every difference count), XOR 0, illegal overlap 0, critical
   disconnected pins 0, antenna violating nets and pins 0;
 - setup slack >= 0 at EVERY tt and ff corner (nom/min/max x tt/ff);
 - hold slack >= 0 at EVERY one of the 9 corners;
 - the ss corner (100 C, 1.60 V) is REPORTED, NOT GATED. It cannot close at 50 MHz without changing CPI, which is
   forbidden. Never relax the clock or the SDC to "fix" anything.
 - Max slew / max capacitance / max fanout violations are NOT hard limits: report them by category (SRAM pins,
   diode-laden nets, standard cells). Do not spend large area to clear them.

PD method
 - SA2 and DM_VC4 are optimised separately for strict PPA: the minimum die that routes and signs off (prove it: the
   next smaller candidate fails with the same recipe), then the fewest buffers, the least wire, the lowest power.
 - Every change = a FULL flow from step 1 to sign-off, run with the gated drivers asic/run_gated_pd.sh (new flow),
   asic/run_gated_resume.sh (continue / retry), asic/branch_run.sh (screening branches only). Diagnose at every
   phase and stop at a clear failure sign instead of waiting. A branched run is only for screening; the official
   result is a full flow from step 1, executed twice.
 - Every gate result and every manual decision (continue past a gate, stop a run, retry a crash) is written as one
   line with its reason to asic/gated_pd.log (follow the CONTINUE / NOTE / STOP lines of 2026-10-09).
 - Never edit a script while any instance of it is running. Stop jobs cooperatively: `touch asic/.abort_gated_pd`
   (no new phases start; running steps finish). Never kill a healthy run. A run that has clearly failed may be stopped
   only after you have found and logged why it failed. Never kill or disturb the owner's own programs (games,
   browsers, ...), even when memory is tight.
 - Flow-tool changes (asic/openlane-local, gate scripts): only when no flow is running, new behaviour behind a new
   variable that is off by default, documented in QUY_TRINH.md section D.

FPGA
 - Quartus fits run one at a time, never in parallel. When two PD flows run, do not run Quartus together with the
   multi-lane verification chain (memory).
 - `quartus_sh --seed` writes the seed back into the .qsf; a SEED inside a sourced .qsf is ignored. Always confirm
   the seed and the RTL of a fit from its report before using its database.

Naming, records, git
 - Run tags: `<cfg>_<floorplan>[_<knob><value>...]_r<N>`, e.g. vc4_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd_r1.
   No numbered or AI-looking names (no R17, E17, final4, _v2, "Incident NN"); use content and date names.
 - History goes ONLY to NHAT_KY.md, one entry per event, header `### YYYY-MM-DD HH:MM <subject>`, Vietnamese
   WITHOUT diacritics (ASCII). Procedures: QUY_TRINH.md (Vietnamese ASCII). Numbers: RESULTS.md (English). Review
   status: REVIEW_RESPONSE.md (English). Do not record the same thing in several places.
 - Project files contain no first-person narration, no "the user said", no persona text, no references to any AI
   memory or chat.
 - Cleanup is mandatory, but deleting run folders needs the owner's explicit approval. Archive first
   (results/pd_run_archive/<run>/: resolved.json, final metrics, error and warning logs, flow log, step list), list
   every deletion in results/cleanup_deleted.txt, add a row to NHAT_KY.md section 10.
 - Git: do not commit or push unless the owner asks. Commit messages and anything pushed: English, ASCII only,
   NO "Co-Authored-By" line, local git identity (vutoan1110). Never check out another branch while jobs run
   (the repo is on branch experimental-r14 with about 220 uncommitted changes).

==========================================================================================================
4. HOW TO RUN THINGS ON THIS MACHINE
==========================================================================================================
 - Windows 11, 32 logical CPUs, 31.6 GB RAM. Git Bash for Windows-side tools (Questa
   C:/questasim64_2024.1/win64/vsim.exe, Windows Python, Quartus). WSL Ubuntu for OpenLane / OpenROAD / Yosys /
   Magic / KLayout / netgen (nix environment, entered by asic/run_pd_mk.sh). WSL is capped at 24 GB + 8 GB swap.
 - Start WSL jobs as `wsl.exe -d Ubuntu -e bash -c "cd /mnt/e/Projects/RISCV-research/asic && <command>"`.
   KEEP ONE WSL TERMINAL OPEN while PD jobs run: the WSL VM shuts down, killing every job (even nohup), when the last
   wsl.exe client exits. Do not use detached or persistence tricks to get around that; tell the owner instead.
 - Memory per job (measured): OpenLane flow before detailed routing 5-8 GB; detailed routing ~10.5 GB; Magic DRC up
   to ~14 GB; KLayout DRC ~8 GB; post-route ECO ~10 GB; Questa GLS 0.2-3 GB per job. The gated drivers wait for free
   memory by themselves (new flow >= 10 GB free, detailed routing >= 12 GB free and at most one other detailed
   routing). Check memory with `free -m` inside WSL and the Windows free memory before adding work.
 - Watch asic/gated_pd.log with a polling loop (line count + sed). `tail -F` from Git Bash does not see lines that
   WSL processes append.
 - PowerShell scripts that pass quoted bash commands to wsl.exe need PowerShell 7 (`pwsh`), not Windows PowerShell 5.1.
 - `run_gated_pd.sh ITEMS='<design dir>:<tag>:<config>'`: the config path is RELATIVE TO THE DESIGN DIR
   (config_x.json, not soc_x/config_x.json).
 - OpenLane resume: new step directories are numbered after the highest existing number and start from the newest
   state_out.json. Before re-running a step that crashed, rename its directory to crashed-<NN>-<name> and use
   `run_gated_resume.sh ... step:<StepID>`.

==========================================================================================================
5. WORK ORDER (details, commands and acceptance criteria: HANDOVER_CODEX.md section 5)
==========================================================================================================
 T1  Finish DM_VC4 sign-off on the 12.24 mm2 die (run vc4_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd_r1).
     If hold at an ff corner is still negative after the first ECO: branch after the PostRouteHoldECO step and run the
     second ECO with config_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd_ecomin.json (exactly as SA2 did).
     If setup is negative at a tt or ff corner: diagnose the path first; never relax constraints.
     If detailed routing is stopped by the watchdog, or hold violations are again in the thousands: stop, diagnose
     with the tools listed in HANDOVER section 6, report to the owner, and do not start new knob experiments without
     a written hypothesis.
 T2  DM_VC4 double execution (_r2, full flow from step 1, same branch procedure), compared field by field with r1.
 T3  Activity-based power (GLS -> SAIF -> OpenSTA at nom_tt with the run's RCX SPEF) for SA2 now, DM_VC4 after T2,
     each run twice (asic/gls/power_cfg.ps1 -Pass 1 then -Pass 2).
 T4  SA2 minimality: run the final SA2 recipe on 11.05 mm2 (3400 x 3250), then 11.305 mm2 (3400 x 3325) if needed.
 T5  DM_VC4 minimality: the final DM_VC4 recipe on 11.90 mm2 (3500 x 3400); screen the clock skew after its first
     global route with asic/fp_tools/grt_skew_screen.sh before continuing.
 T6  Final PPA table for DM / SA2 / DM_VC4 (sign-off gate first; die / core area; std-cell area and count; buffers by
     class; wirelength; setup and hold per named corner; dynamic + leakage power from OpenSTA with SAIF, vectorless
     for reference; the knobs each design used and why; Embench CPI and I$ / D$ hit rates). Generator:
     scripts/metrics/asic_compare.py plus the power CSVs and results/unified_metrics.md.
 T7  Board runs with the CURRENT RTL 6c4ccffd (review item A7). See section 6 below and HANDOVER T7.
 T8  LEC for the SA2 / DM_VC4 netlists: owner decision. A byte-exact N1 replay for SA2 already exists (HANDOVER J3).
 T9  Fix asic/fp_tools/gate_check.py p2 for runs with RUN_POST_GRT_DESIGN_REPAIR false (when no flow runs).
 T10 Cleanup proposal (about 92 GB; results/cleanup_candidates_20261009_sizes.txt): owner approval before deleting.
 T11 Git commit: only when the owner asks.

==========================================================================================================
6. THINGS THAT ARE EASY TO MISUNDERSTAND (read twice)
==========================================================================================================
 - Two designs exist: the PUBLISHED 1 KiB design (other directory, read-only) and the RESEARCH 4 KiB design
   (this workspace). Every task here is about the 4 KiB research design.
 - "Board runs" (T7) means: build NEW SOF files from the CURRENT RTL 6c4ccffd for the four 4 KiB points (DM, SA2,
   DM_VC4, DM_DSE) and run them on the DE2-115. The existing output_files_board_matrix_r14/ was built from the OLD RTL
   3ea52396 and must not be used for results. Steps: confirm the manifest; make sure each point project
   (point_dm_4kb, point_sa2_4kb, point_vc4_4kb, point_dse_4kb) holds a fit of 6c4ccffd at one recorded seed (canonical
   seed 2 unless the owner chooses otherwise), refitting one point at a time if needed (scripts/run_le_rtlfix.sh is
   the driver that applies seeds; read it first); write a new SOF builder from scripts/fpga/build_board_matrix_r14.py
   that reads the RTL id from the manifest and writes to a new directory (e.g. output_files_board_matrix_6c4ccffd/);
   each SOF = the point's fit + the firmware's MIFs via quartus_cdb --update_mif and quartus_asm (no new fit); the
   canonical MIFs are restored at the end. Regenerate the expected MCYCLE / MINSTRET per kernel and configuration on
   the current RTL in simulation, twice, and check them against the R14 values (the RTL change is cycle-exact).
   Program with `quartus_pgm -c USB-Blaster -m JTAG -o "p;<file.sof>"`. Do NOT use the published repository's
   program_de2_115.ps1. Pass per SOF: LEDR = 0xA5 (self-check passed; 0xEE = failed) and HEX7..HEX0 = the expected
   MCYCLE of the measured region (hex). The owner plugs in the board and reads LEDR / HEX; you prepare the SOFs, the
   checklist (INDEX.csv with the expected values) and the result CSV, and you record photos / UART logs under
   results/board_<date>/. The whole matrix is run twice.
 - Never build firmware with BENCHMARK_FAST_UART for any canonical or board run: it shifts mcycle on some kernels.
   fw_board/upfull_*.hex are the 12 Embench kernels at their official iteration counts (too long for routine sims).
 - "Double execution" of a PD result = a second full flow from step 1 with the same config (plus the same branch
   procedure where the recipe has one), compared on every metric and on the sha256 of the final netlist and DEF.
   The SPEF may differ only in its *DATE line.
 - The two-pass hold ECO is a BRANCH PROCEDURE, not a single config switch: full flow (first ECO on max_* RC) ->
   branch_run.sh after the PostRouteHoldECO step -> second ECO with the _ecomin config (min_* RC) -> sign-off.
 - For DM_VC4 runs with RUN_POST_GRT_DESIGN_REPAIR false, the p2 gate prints "MISSING p2 data". That is expected
   (the gate looks for the post-GRT repair's re-route). Continue only if the p2 numbers match the expectation (clock
   skew about -2.0 ns, hold endpoints in the low hundreds, setup >= 0), with a CONTINUE line in gated_pd.log.
 - The SA2 / DM_VC4 runs stop at their p2 gate on a small negative hold by design; the post-route ECO repairs hold on
   extracted parasitics. Continue with a CONTINUE line only when hold is small (SA2: -0.206 ns at 19 endpoints).
 - DM_VC4's clock-tree skew is decided by each FULL global route (a lottery driven by congestion at the D$ macro
   edge). Do not "fix" it with random knob changes; the measured mechanisms are in NHAT_KY 2026-10-09 and HANDOVER
   section 6. Re-enabling the post-GRT design repair re-runs a full global route and re-rolls the clock routing.
 - STAMidPNR ss / ff numbers are stale pre-PnR values; real timing comes only from STAPostPNR (one STA per corner).
 - The resizer runs on tt / ff only (RSZ_CORNERS) in the SA2 recipe; the DM_VC4 3600 recipe keeps the default
   corners on purpose (to reproduce its known-good first global route). Do not "harmonise" the two.
 - The owner's report page (a claude.ai artifact) cannot be updated from here. Its source is
   results/report_page/bao_cao_soc_v5.html; if a page is needed, update a new dated local copy.
 - Activity power: the SAIF -> pin conversion must run in Windows Python (WSL Python faults on this machine).

==========================================================================================================
7. OWNER DECISIONS: ASK FIRST, THEN WAIT
==========================================================================================================
 - Deleting any run folder or large result (cleanup T10).
 - Any RTL change, any change to the sign-off gate or its thresholds, any change of the 20 ns clock or SDC.
 - Running the LEC for SA2 / DM_VC4 (T8).
 - Git commits and pushes (T11).
 - The Quartus seed used for the board SOFs, and scheduling the physical board session.
 - Promoting anything to the golden snapshot (E:/Projects/RISCV-research_GOLDEN_FINAL3_20260928): if a result beats
   the golden in every aspect, report a side-by-side table and PAUSE until the owner approves.
 - Stop and ask as well when: a run fails in a way not described in the handover; a task would need more than one
   hypothesis at a time; memory is too tight for the next job; any rule here seems to block the work.

==========================================================================================================
8. HOW TO REPORT AND RECORD
==========================================================================================================
 - To the owner (Vietnamese): Achievements first, then Failures and gaps, with hard numbers; name the corner of
   every timing number; keep the timing corner separate from the power corner; state the power method (flow
   estimate, vectorless, or activity-based from SAIF); give DRC / LVS as a pass/fail gate before any PPA table;
   say clearly when a number is a single execution or a screening result.
 - After each event: one NHAT_KY.md entry (Vietnamese ASCII); update RESULTS.md (English) only with double-executed
   numbers; update REVIEW_RESPONSE.md (English) when a review item changes status; keep HANDOVER_CODEX.md section 3-5
   current when a task finishes (so the next agent can take over again).
 - Keep the evidence: logs, reports and CSVs stay; deletions only per section 3.
