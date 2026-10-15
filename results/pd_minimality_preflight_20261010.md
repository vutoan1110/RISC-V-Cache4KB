# Smaller-die PD preflight, 2026-10-10

**PREPARED, NOT EXECUTED.** This is an input and geometry audit, not a PD result or a minimum-area proof.
No new flow, WSL client, simulator or formal tool was started. The healthy current VC4 detailed route remains
untouched. The machine has insufficient free RAM for an additional flow at the time of preparation.

The machine-readable receipt is `results/pd_minimality_preflight_20261010.json`. It contains all source/output
SHA256 values, exact per-pass commands, macro rectangles with halos, recipe deltas and launch conditions.
All 241 existing input hashes remained unchanged; all 219 inputs frozen by the active VC4 queue match its plan.
The current 227-file RTL manifest passed `python -B scripts/rtl_manifest.py --check`.

## Prepared candidates

| Design | Die, um | Die, mm2 | Core, mm2 | Status |
|---|---:|---:|---:|---|
| SA2 | 3400 x 3250 | 11.050 | 10.890976 | Existing first/max and second/min ECO configs rechecked; NOT EXECUTED |
| SA2 | 3400 x 3325 | 11.305 | 11.144176 | Existing first/max and second/min ECO configs rechecked; NOT EXECUTED |
| DM_VC4 | 3500 x 3400 | 11.900 | 11.734976 | New padding-recipe configs; conditional on T1 accepting their exact 3600 x 3400 source |

The four SA2 inputs match the existing preparation receipt. Each changes only `DIE_AREA`, `CORE_AREA` and
`MACRO_PLACEMENT_CFG` relative to the signed 3400 x 3400 recipe. Both signed first/max runs and both second/min
branches were checked against their actual `resolved.json`: every explicitly configured implementation field
matches. Only path expansion and the exact Liberty string-to-single-element-list normalization were applied.

New VC4 files:

- `asic/soc_vc4_4kb/config_corr3500x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd.json`
- `asic/soc_vc4_4kb/config_corr3500x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_ecomin.json`
- `asic/soc_vc4_4kb/macro_placement_corr3500x3400_f220_pad1.cfg`

These inherit the **current padding** 3600 x 3400 candidate, not the failed unpadded recipe. Only the same three
geometry fields change. The source recipe remains a candidate until T1/T2 sign off. If a different recipe is
accepted by T1, these prepared inputs must be rederived and rechecked before use.

The old `config_corr3500x3400_f220_capm20_antoff_rsztf_nogrtt_clkm3_pad1.json` is unsuitable for this comparison:
besides geometry it changes antenna margin 30 to 10, resizer corners to tt/ff, minimum clock layer to met3 and
post-GRT design repair from false to true. Its historical run cannot establish minimality of the current recipe.
It was read for diagnosis and remains unchanged.

## Preserved implementation

Both designs retain 20 ns at the top level and in the sky130A/HD override, the identical PNR/sign-off SDC,
42 ordered RTL inputs, frozen `asic/snapshots/rtl_r14`, the same SRAM models and the same OpenLane/gate scripts.
The wrapper selects 4 KiB I/D caches, 16 KiB main RAM, 16-byte lines, L0 depth 8, enabled counters and the
256-entry branch predictor. SA2 uses `CACHE_CONFIG=1`; VC4 uses 2 and four victim entries.

Current `hdl/soc_top.v` defaults `CACHE_FAST_HIT=0`. The frozen PD snapshot predates that optional parameter
and retains the original main-hit controller with `ST_LOOKUP` followed by `ST_HIT_RESP`. No FAST_HIT=1 input
or RTL change is introduced. This input audit inherits that ASIC baseline; it is not a new proof of sequential
equivalence between the current FPGA RTL and the snapshot.

SA2 deliberately keeps tt/ff resizer corners, met3 clock routing and enabled post-GRT repair. VC4 deliberately
keeps its default resizer corners (including ss), the default minimum clock layer and disabled post-GRT design
and timing repair. These settings are not harmonized. GPL/DPL padding remains two sites total, one per side.

For each candidate, the first/min pair differs in exactly one implementation field:
`POST_ROUTE_HOLD_ECO_RCX_CORNER` is omitted for the unchanged `max_*` default in the first flow and is `min_*`
in the second-ECO configuration. Applying the second configuration to a fresh full flow is not the two-ECO
procedure: the first max ECO must complete, then its state is branched and the min ECO is run.

## Macro geometry

All candidates contain eight 2 KiB RAM macros and eight 1 KiB cache macros. LEF sizes are 683.10 x 416.54 um
and 479.78 x 397.50 um. The 16 oriented rectangles and their 10 um halos fit within each core without overlap.
N and FS preserve these bounding-box dimensions; both orientations are permitted by the LEF symmetry.
PDN halos remain zero. `MACRO_PLACEMENT_CFG` overrides the unchanged legacy locations in `MACROS.instances`
(`openlane/steps/odb.py`, `ManualMacroPlacement.run`).

For VC4, width shrinks by 100 um while height, all Y coordinates and orientations stay unchanged. I-cache
coordinates stay unchanged and D-cache shifts left by 100 um. For RAM bank column k=0..3:

```text
RAM gap = (3476 - 2*100 - 4*683.10) / 3 = 181.20 um
x(k) = 12 + 100 + k*(683.10 + 181.20)
     = 112.00, 976.30, 1840.60, 2704.90 um
```

These explicitly computed locations match the existing 3500 corridor placement pattern. No old recipe knobs
were copied. The RAM channel stays 220 um; cache orientation F and the 100 um inter-column cache gap remain.

## Execution after prerequisites

Run SA2 3250 first, then 3325 only if 3250 fails under this same recipe. VC4 3500 follows accepted T1/T2.
Any accepted result **and any deterministic smaller-die failure used in a minimality claim** need two independent
full flows from step 1. A smaller passing candidate becomes the candidate result; a grid-minimum claim requires
the next smaller tested candidate to fail with the same recipe. There is no automatic golden promotion.

Every command below runs from `/mnt/e/Projects/RISCV-research/asic` in a foreground WSL client kept open until
natural completion. Verify Windows free RAM >=10000 MB before adding a flow; WSL gates remain >=10000 MB for
P1 and >=12000 MB before DRT. Fresh base, branch and screen tags must be absent. Recheck source hashes, manifest,
external Nix/PDK tools and the unchanged gate. Do not edit active scripts or kill healthy jobs/owner applications.

Example SA2 first pass:

```bash
G5_UNLIMITED_LATE_PHASE=1 P2_MIN_SETUP=0 STOP_AFTER=p2 \
  ITEMS='soc_sa2_4kb:sa2_corr3400x3250_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1:config_corr3400x3250_f220_capm20_fo16_pad1_tdp_clkm3_rsztf.json' \
  bash run_gated_pd.sh
```

Example VC4 first pass, conditional on the source recipe being accepted:

```bash
G5_UNLIMITED_LATE_PHASE=1 P2_INITIAL_GRT_FALLBACK=1 P2_MIN_SETUP=0 STOP_AFTER=p2 \
  ITEMS='soc_vc4_4kb:vc4_corr3500x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_r1:config_corr3500x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd.json' \
  bash run_gated_pd.sh
bash fp_tools/grt_skew_screen.sh soc_vc4_4kb \
  vc4_corr3500x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_r1 \
  config_corr3500x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd.json \
  vc4_corr3500x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_grtskew_scr_r1
```

The existing driver holds at P2; `STOP_AFTER=p1` is not implemented. The screen reads the **first completed
GlobalRouting state**, before any DRT continuation, even though it is invoked after P2. Resolve the actual
numbered GRT directory; do not assume step 39. The helper selects the lexical first globalrouting directory,
so it requires one unambiguous intended original GRT state. A retry or multiple directories require explicit
inspection first. The source job must be held and the screen tag fresh. Inspect raw tool status, state and
skew reports: the helper's echo or zero exit code cannot establish success.

VC4's diagnostic expectation is hold skew around -2 ns, hold endpoints in the low hundreds and setup nom_tt
>=0. Thousands of hold violations or clearly adverse skew require a diagnosed STOP, not random knob changes.
Only nom_tt mid-PnR timing is useful for this screen; ss/ff mid-PnR values are stale. A small negative P2 hold
requires an evidence-based CONTINUE reason in `gated_pd.log`; it must never be relabeled gate PASS.

The JSON lists every complete command for all three candidates and both passes: fresh flow, screen, DRT resume,
guarded discovery of the actual completed first `PostRouteHoldECO` number, `branch_run.sh`, and the matching
`_ecomin` hold/sign-off resume. Never hardcode step 47 for a new flow. Branch only after the first flow has
stopped/finished and the first max-ECO state is complete. The `_ecomaxmin_r1` and `_ecomaxmin_r2` names retain
the independently initialized parent of each pass.

## Acceptance and failure evidence

The final hard gate remains route/Magic/KLayout DRC 0, every LVS difference count 0, XOR 0, overlap 0,
critical disconnected pins 0, antenna nets/pins 0, setup >=0 at all six tt/ff nominal/min/max corners and
hold >=0 at all nine corners. ss setup is reported, not gated. DRV violations are reported, not hard limits.
Timing comes only from completed `STAPostPNR` reports. These configs do not change any acceptance threshold.

Keep the complete raw logs/states and actual failing corner/path, congestion or DRT iteration evidence,
DRC details and all LVS difference counts. Repeat deterministic failures from step 1 with identical inputs.
A resource failure, abort, missing input or random native crash does not prove that a smaller die cannot fit.
Apply the identical second/min ECO procedure before treating repairable first/max ff hold as a final failure.
Unknown failures remain open and require diagnosis; no clock/SDC relaxation or speculative knob changes.

For paired successful flows compare complete metric key sets/fields, final netlist and DEF hashes, and SPEFs
with only DATE ignored. A screening branch or a second read of an output is not an independent second run.
The historical 3400 x 3100 SA2 max_tt -0.573 ns failure was not reexecuted here. Actual routability, minimality
and sequential LEC closure remain unproved by this preparation.
