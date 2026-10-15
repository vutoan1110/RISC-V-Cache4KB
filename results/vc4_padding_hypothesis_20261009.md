# DM_VC4: cell-spacing hypothesis at 12.24 mm2

Status: prepared, not executed. This is an experiment plan, not a PD result.

The stopped run `vc4_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd_r1`
exceeded the unchanged iteration-10 convergence limit: 5,689 markers > 5,000.
The diagnostic reports contain 4,512 shorts and 1,171 metal-spacing markers;
4,089 markers (71.9 %) are in the x=1500..1600, y=1800..2000 um region.
That region contains 1,392 non-physical cells, including 397 cells with
fanout-repair names and 105 with max-capacitance-repair names. The maximum
20 um pin-density bin is 34.5 pins per 100 um2. Its bin utilization is an
estimate, not evidence of an illegal physical overlap.

One hypothesis: adding one placement site on each side of standard cells
reduces the pin-access congestion that dominates these local met1/met2
shorts and spacing errors. `GPL_CELL_PADDING=2` and `DPL_CELL_PADDING=2`
both mean one site on each side in the local OpenLane Tcl sources. These
two fields implement the same spacing treatment at global and detailed
placement. The die, macro coordinates, placement target density, fanout,
default resizer corners, clock layers, RTL snapshot, SDC and 20 ns clock
remain unchanged. The second-ECO config retains min_* extraction.

Padding was insufficient in smaller earlier VC4 trials. The unchanged
12.24 mm2 baseline now provides a measured DRT hotspot for this specific
spacing experiment. Success is not assumed. Changing placement can reroute
the clock tree and lose the baseline's favorable clock skew.

Preparation: `python asic/fp_tools/prepare_vc4_padding.py --write`.
Hashes and the exact two-field diff: `results/vc4_padding_preparation_20261009/inputs.json`.
Source diagnostics: `results/vc4_corr3600x3400_drt_diagnosis_20261009.json`,
`results/vc4_corr3600x3400_drt_region_20261009.log` and
`results/vc4_corr3600x3400_drt_pin_hotspots_20261009.log`.

Run only after the owner opens and keeps a WSL terminal and memory allows
the phases. From `asic/`, a fresh flow through p2 is:

```bash
G5_UNLIMITED_LATE_PHASE=1 P2_INITIAL_GRT_FALLBACK=1 P2_MIN_SETUP=0 STOP_AFTER=p2 ITEMS='soc_vc4_4kb:vc4_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_r1:config_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd.json' bash run_gated_pd.sh
```

`STOP_AFTER=p2` pauses the same full flow for diagnosis; this is not a
branch screening result. At every phase, inspect the existing gate output
and stop at a clear failure. After GlobalRouting, inspect overflow,
`Extra Run for hard benchmark`, clock detours and pin hotspots. At p2,
measure the real nom_tt_025C_1v80 setup/hold and hold skew. Thousands of
hold endpoints or negative tt setup are failure evidence; do not proceed
unchanged. A small residual hold violation may be left to extracted
post-route ECO only with the prescribed explicit CONTINUE record and reason.

If placement/global routing remain viable, continue this run with the
gated resume driver. Keep the published watchdog limits through iteration
40. Compare the iteration-5/10 DRC reports and the hotspot distribution
with the preserved baseline. A changed DRC count is a single-run diagnostic,
not a result. A second max_* -> branch -> min_* hold ECO is used only if the
first sign-off still has negative ff hold, as the handover prescribes.

Acceptance remains the existing final gate: all route/Magic/KLayout DRC,
every LVS difference count, XOR, overlap, critical disconnected pins and
antenna nets/pins zero; setup >= 0 at every tt/ff corner; hold >= 0 at all
nine corners. Report ss setup separately and classify remaining DRVs.
If this recipe signs off, execute an independent second full flow from step
1 with the same branch procedure and compare every metric and final artifacts.
Do not start another knob hypothesis automatically if this one fails.
