# Cache DSE: measured results

Every number here was produced by a tool on this project and, unless a caveat
says otherwise, reproduced by an independent second run. Numbers that are not
yet double-executed are marked. Nothing is estimated.

Device: Altera Cyclone IV E EP4CE115F29C7, 20 ns target (50 MHz), 20,000 LE
budget. ASIC: SkyWater sky130A via OpenLane 2.3.10.

---

## 1. Verification status

| chain step | 1 KiB | 4 KiB |
|---|---|---|
| Verilator lint, 4 cache configs | 0 correctness warnings | 0 correctness warnings |
| Directed regression | 126 PASS / 0 FAIL, twice | 126 PASS / 0 FAIL, twice |
| UVM | 5/5, twice | 5/5, twice |
| Embench, 12 kernels x 4 configs | 48/48, twice | 48/48, twice |
| `verify_double` field-by-field | 48 identical | 48 identical |

The 1 KiB matrix was additionally compared against the project's canonical
matrix: **48 rows, 48 identical, 0 differing**. A change to
`icache_tag_ram.v` (see 5.2) therefore moved nothing that had been published.

---

## 2. FPGA, 1 KiB caches

Four Quartus seeds per point; power measured with Quartus Power Analyzer
(vectorless) on the seed-2 fit.

| point | config | LE (seeds 1/3/4/2) | mean | regs | worst slack | power |
|---|---|---|---:|---:|---:|---:|
| `dm_nopc` | 0, no counters | 11884 11894 11888 11874 | 11,885 | 5,977 | -0.140 | 261.19 mW |
| `dm@l0-2` | 0, L0=2 | 13456 13526 13547 13465 | 13,498 | 7,095 | -0.052 | 264.76 mW |
| `dm@l0-4` | 0, L0=4 | 13893 13859 13910 13921 | 13,896 | 7,403 | -0.297 | 270.19 mW |
| **`dm`** | **0** | 14638 14596 14600 14672 | **14,626** | 8,015 | **+0.000** | 272.25 mW |
| `dm_dse` | 3 | 15082 15007 15084 15107 | 15,070 | 8,113 | +0.205 | 276.38 mW |
| `sa2` | 1 | 16181 16211 16128 16223 | 16,186 | 8,322 | +0.028 | 296.10 mW |
| `dm_vc4` | 2 | 17968 18033 17897 17971 | 17,967 | 9,898 | -0.290 | 302.12 mW |

**`dm` is the only point with no negative seed.** Quoting seed 2 alone would
have shown `dm_vc4` comfortably positive at +0.708 ns; across four seeds its
worst is -0.290. Single-seed timing numbers are not usable on this device.

### 2.1 Organisation cost, controller held constant

Config 3 (`dm_dse`) is direct-mapped on the same ten-state controller the
associative configurations use, so (3 vs 1) and (3 vs 2) isolate organisation
from controller depth:

```
2-way set-associative   +1,116 LE (+7.4 %)    +209 regs   +19.72 mW
victim cache, 4 entries +2,897 LE (+19.2 %) +1,785 regs   +25.74 mW
```

The victim cache costs **2.6x** what associativity costs, for the organisation
with the worst CPI in the matrix.

### 2.2 Control-logic overhead, organisation held constant

(0 vs 3), both direct-mapped, differing only in controller depth:

```
+444 LE (+3.0 %), +98 regs, +4.13 mW
```

Outside the measured four-seed spread on `dm` (76 LE). And the deeper
controller is **faster**: worst slack +0.205 ns against 0.000. The
"longer critical path" explanation for the direct-mapped win is wrong.

---

## 3. FPGA, 4 KiB caches

Same protocol. **Pass-2 double execution is complete: all sixteen fits re-run
independently, `[VERIFIED] 16 rows compared, 16 identical, 0 mismatched`.** Every
field -- LE, regs, comb, mem_bits, slack, Fmax -- reproduced exactly, six to
eleven hours apart, on a host known to corrupt memory.

| point | LE (seeds 1/3/4/2) | mean | regs | LE margin | worst slack | power |
|---|---|---:|---:|---:|---:|---:|
| `dm_4kb` | 15289 15271 15341 15365 | 15,316 | 8,395 | 4,684 | -1.278 | 281.05 mW |
| `dse_4kb` | 16837 16793 16874 16778 | 16,820 | 8,685 | 3,180 | **+0.269** | 290.93 mW |
| `sa2_4kb` | 19200 19233 19269 19205 | 19,227 | 9,082 | 773 | -1.810 | 309.76 mW |
| `vc4_4kb` | 19695 19691 19713 19711 | 19,702 | 10,470 | **298** | +0.091 | 306.31 mW |

### 3.1 The device runs out before the design does

`vc4_4kb` uses **98.5 %** of the 20,000 LE budget and `sa2_4kb` 96.1 %. Neither
exceeds it, but neither leaves room for a further change. At 1 KiB both looked
comfortable (81 % and 90 %).

### 3.2 `dse_4kb` is the only 4 KiB point that closes timing

Worst slack **+0.269 ns across all four seeds**, against -1.278 for `dm_4kb` and
-1.810 for `sa2_4kb`. The ten-state controller's timing advantage, already
visible at 1 KiB (+0.205 vs 0.000), widens with capacity.

### 3.3 Associativity scales with capacity; a victim cache does not

```
             1 KiB      4 KiB      growth
sa2 - dm     1,560 LE   3,911 LE   2.5x
vc4 - dm     3,341 LE   4,386 LE   1.3x
```

The victim cache is fixed at four entries, so its cost is nearly constant; the
associative tag and data arrays scale with the cache. At 1 KiB the victim cache
costs 1,781 LE more than associativity, at 4 KiB only 475 LE more.

---

## 4. Capacity: what 4 KiB buys and what it costs

Cycle counts from the 48-run Embench matrix at each capacity, both
double-executed.

**Cost, config 0:**

```
+690 LE (+4.7 %)   +8.80 mW (+3.2 %)   worst slack 0.000 -> -1.278 ns
```

**Benefit,** the kernels that move (23 of 48 pairs are unchanged because their
working set already fits in 1 KiB):

```
matmult  DM       53,434 -> 42,163   -21.1 %
matmult  SA2      62,021 -> 47,397   -23.6 %
edn      DM      117,623 -> 116,569   -0.9 %
md5sum   DM       70,316 -> 68,153    -3.1 %
```

At 4 KiB `matmult` converges to **47,397 cycles on SA2, DM_VC4 and DM_DSE
alike**. Once capacity is sufficient the organisation stops mattering, and the
entire advantage of associativity and of the victim cache disappears.

**The benefit must be discounted by frequency.** `dm_4kb` misses 50 MHz on two
of four seeds; only `dse_4kb` closes. A 21 % cycle reduction bought at a lower
achievable clock is not a 21 % speed-up.

---

## 5. Two RTL findings

### 5.1 L0 hot-buffer depth: eight entries is correct

The instruction cache's L0 buffer holds eight 128-bit lines in flip-flops --
1,024 registers for 128 bytes -- and eight was never a considered choice. Priced
on all three axes:

```
        LE (4 seeds)   regs   worst slack     power      48-run cycles
L0=8       14,626      8,015     0.000     272.25 mW      6,261,571
L0=4       13,896      7,403    -0.297     270.19 mW         +6.42 %
L0=2       13,498      7,095    -0.052     264.76 mW        +15.45 %
```

Halving the buffer costs 6.42 % of runtime for 5.0 % of logic and 0.76 % of
power, and worsens worst-case timing. **Eight stays.**

The spread across kernels is a step function, not a gradient: at L0=4,
`mont64 +19.21 %` and `md5sum +15.33 %` against `fdct +0.00 %` and
`insertsort +0.02 %`. A single-kernel probe would have been worthless.

### 5.2 A latent defect the capacity sweep exposed

`icache_tag_ram.v` reset its valid bits with a loop over `LINE_COUNT`, while
`dcache_tag_ram.v` used a packed vector. At 64 lines both work. At 256,
Verilator refuses to unroll a 256-iteration delayed assignment to an array
(`%Error-BLKLOOPINIT`) and OpenLane's own lint stops the build. The instruction
cache was changed to match the data cache; the 1 KiB matrix then reproduced
byte-for-byte.

---

## 5.2b CoreMark: a standard benchmark, and what it does not fit

The review asked for a benchmark outside the project's own kernel set. CoreMark
is now measured, double-executed at both capacities.

**It does not fit the SoC as built.** `fw/coremark.hex` is 1,027 data lines of
four words -- 4,108 words, 16.4 KiB -- against a main memory of
`IMEM_DEPTH + DMEM_DEPTH` = 2,048 words = 8 KiB. The first attempt failed on all
four configurations with "Too many data words read on line 514": word 2,048 is
reached on data line 512. That is a property of this SoC, not a flaw in the run.
CoreMark was therefore run with main memory enlarged, identically for all four
configurations, by `scripts/run_coremark.py`. `scripts/run_ablation.py`, which
produces the published matrices, is untouched.

```
                    1 KiB                 4 KiB
config        mcycle      CPI       mcycle      CPI
DM         2,566,519    2.537    2,520,901    2.492
SA2        2,601,557    2.572    2,573,624    2.544
DM_DSE     2,630,110    2.600    2,586,274    2.557
DM_VC4     2,638,019    2.608    2,590,590    2.561
```

`minstret` is identical across all four configurations within each capacity --
1,011,509 at 1 KiB, 1,011,515 at 4 KiB -- so the comparison between
organisations is controlled. The six-instruction difference between capacities
is CoreMark reporting its own measured score: a different number printed is a
different string formatted and a few more UART writes, and `mmio` moves with it
(1,121,987 to 1,121,997).

**The headline CPI understates the organisation effect, and by a lot.** On this
SoC 43.7 % of CoreMark's cycles are MMIO -- 1,121,987 of 2,566,519 -- because
the benchmark prints its results over a UART. Excluding those cycles:

```
DM       1,444,532 cycles    baseline
SA2      1,479,570          +2.43 %
DM_DSE   1,508,123          +4.40 %
DM_VC4   1,516,032          +4.95 %
```

The ranking is the same one the Embench matrix gives, and the same one section
2.2 explains: the direct-mapped configuration on the shallow controller is
fastest, and the gap is controller depth as much as organisation. CoreMark
agrees, but it should be quoted with the MMIO share stated, or nearly half the
measurement is UART.

---

## 5.2c Random differential, fifty seeds

The review's objection was not that the differential test was wrong, but that it
was run at one seed and the log was not kept -- which for a differential method
proves very little.

`scripts/run_random_diff.sh` now generates a random RV32 program per seed with
`verification/random/gen_rv32.py`, runs it with the branch predictor off and
on, and requires the two architectural traces to hash identically. The predictor
is a performance feature; it must not change what the machine computes.

```
seeds            1..50
MATCH            50
MISMATCH          0
generation fail   0
no trace          0
```

Every trace and every generated program is kept under `results/random_diff/`,
and `results/random_diff.csv` carries a row per seed with both SHA-256 prefixes,
so the claim is checkable rather than asserted.

---

## 5.3 The counters agree with an independent cache model

The review's third priority was to stop asserting that the hardware counters are
right and prove it. `scripts/cache_model.py` is a reference cache written
separately from the RTL; `scripts/run_crossval.py` drives it over the same
kernels and compares, field by field, against what the hardware reported.

```
rows                     36   (12 kernels x DM, SA2, DM_VC4)
fields per row            9   i_access i_main i_victim i_miss
                              d_read d_write d_main d_victim d_miss
comparisons              324
disagreements              0
```

Every row is `EXACT`. The agreement was re-checked here directly from the raw
`*_rtl` and `*_model` columns rather than trusting the `match` column, and the
count of disagreements is zero on all 324.

This matters for the same reason the review said it would: it converts "taken
from hardware, not estimated" from a claim into a measurement. The classification
counters in section 4 rest on it.

---

## 6. ASIC, sky130

### 6.1 Post-route, 1 KiB, complete

```
DIE_AREA        1800 x 2900 um = 5.22 mm^2
instance area   2,720,150 um^2  (macros 1,138,150 + stdcell 1,582,000)
utilisation     53.35 %
std cells       186,877  (27,642 sequential, 6,603 antenna diodes)
routing         0 DRC violations, from 82,554 over nine iterations
                7.30 m wire, 1,048,010 vias, all single-cut
disconnected    44 pins, 0 critical -- all 44 are conb_1 tie cells with one
                of HI/LO unused, cross-checked against the DEF
antenna         501 violating nets, 655 violating pins, after 6,603 diodes
```

**The 501 residual antenna violations were not stated in earlier versions of
this document and should have been.** They are the value at every antenna
checkpoint in the run -- steps 95, 139 and 150 all report 501 with
`route__drc_errors` 0 -- so the design routes clean on DRC and does not clear
antenna. The reviewer's note of "646 antenna violations" refers to an earlier
build of the same design; 501 is the figure for the run these numbers come
from.

Timing, nine corners, with RCX parasitics:

```
hold    0 violations at EVERY corner, worst +0.0919 ns
setup   tt and ff PASS (+2.80 .. +5.68 ns)
        ss  FAIL  -13.26 ns, 8,846 violating paths, TNS -12,723 ns
```

**The design closes at the typical corner and not at the slow corner**
(100 C, 1.60 V), where the critical path needs about 33 ns -- roughly 30 MHz.

The worst path was read out of `127-openroad-stapostpnr/max_ss_100C_1v60/max.rpt`
rather than left as a number. It runs flop to flop, `_150325_` to `_150320_`,
with data arrival 39.20 ns against a required time of 25.95 ns:

```
logic stages on the path        54   (38 combinational cells, 8 buffers)
data path delay              32.82 ns at ss
budget per stage at 20 ns      370 ps
cells                        5x xnor2, 3x xor2, 3x and2, plus a31o/o31ai/
                             a311oi/o2111a -- an arithmetic carry chain
launched by                  u_soc.u_core.u_pipeline.datapath.instr_w[2]
```

So the slow-corner failure is not a placement or routing artefact. It is 54
levels of logic between two flops, entered from an instruction bit in the
writeback stage, and it is 13.26 ns too slow only because sky130 cells are
about 2.2x slower at 100 C / 1.60 V than at 25 C / 1.80 V. The same path passes
at tt with +2.80 ns to spare, which is consistent with 32.82 / 2.2 = 14.9 ns.

Closing ss needs the path split, which is an RTL pipeline change and a full CPI
re-measurement. It was not attempted.

**Correction, 2026-09-24: the timing above was measured with a defective SDC.**
`soc.sdc` captured the return value of `create_clock`, which OpenSTA does not
provide, so `$clocks` was empty and every constraint that referenced it was
silently void: `set_clock_uncertainty 0.25`, `set_clock_transition 0.15`,
`set_input_delay` and `set_output_delay`. No timing report in any ASIC run
contains a "clock uncertainty" line, and 121 endpoints were never checked.
OpenLane's own `base.sdc` uses `get_clocks` for exactly this reason; the bug
was in the hand-written SDC, not in the tool.

The fix is one line. The design was then re-timed with the real tool on the
archived sign-off artefacts -- `final/nl/soc_asic_top.nl.v`, `final/spef/nom/`
and the three PVT liberty sets -- twice per corner, once with the old SDC and
once with the new one. The old-SDC pass reproduces the published metrics to
four decimals, which is what makes the comparison trustworthy:

```
                 setup WNS            hold WNS          setup TNS
corner       published -> fixed   published -> fixed  published -> fixed
nom_tt        +3.4116   +3.1616    +0.2020  -0.0480        0        0
nom_ss       -12.2527  -12.5027    +0.4829  -0.1231  -10,161.7 -10,912.6
nom_ff        +5.3259   +5.0759    +0.1039  -0.1461        0        0
unconstrained endpoints: 121 -> 46
```

**Hold no longer closes at any corner.** The earlier claim "0 hold violations
at EVERY corner, worst +0.0919 ns" was true only because the 0.25 ns
uncertainty was never applied. With it applied the same netlist is -0.048 ns
at tt, -0.123 ns at ss and -0.146 ns at ff. These are small numbers that a
hold-fix pass would close, but they were not closed in this run and must not
be reported as closed.

Setup at tt still passes with +3.16 ns, so the "closes at typical, fails at
slow" conclusion stands; only the margins shrink by the uncertainty.

Raw logs, scripts and checksums: `asic/evidence/sdc_recheck_1kb_research/`.
The same re-measurement for the published `soc_with_sram` run is in
`results/asic/sdc_recheck_20260924/` of the main repository.

Power, nom_tt_025C_1v80: **196.4 mW** total; combinational 86.3, sequential
58.3, clock 40.6, macro 11.2.

### 6.2 4 KiB: synthesis and placement complete, routing not

The 4 KiB ASIC needs the cache data arrays in SRAM macros. On the FPGA a
capacity change is free -- `(* ramstyle = "M9K" *)` sends the arrays to block
RAM -- but Yosys has no equivalent, and the arrays would synthesise to
flip-flops:

```
                       bits per cache      both caches
LINE_COUNT =  64    4 x  64 x 32 =  8,192      16,384 flops
LINE_COUNT = 256    4 x 256 x 32 = 32,768      65,536 flops
```

At 1 KiB the whole chip has 27,642 sequential cells, so those arrays are already
59 % of every flop on the die. `sky130_sram_1kbyte_1rw1r_32x256_8` is an exact
fit for one bank: four per cache, eight plus the four 2 KiB main-memory macros,
**twelve macros**.

Measured effect, synthesis:

```
            stdcell area      instances
1 KiB       1,386,981 um^2      102,041
4 KiB       1,036,877 um^2       77,310
             -350,105 (-25.2 %)  -24,731
```

A quarter less logic at four times the capacity.

**Reached:** synthesis, floorplan, twelve-macro placement, PDN (power grid
checker passed), IO placement, global placement, repair, detailed placement,
CTS, STA.

**Not reached:** global routing.

The cause was found by measurement and it is a floorplan defect, not a capacity
limit. Both SRAM macros carry their signal pins on the horizontal edges -- 72 to
74 pin rectangles in the bottom 20 um of the macro and 35 in the top -- so every
pin escapes vertically and the gap above and below each macro row is the
resource that decides routability. In the placement used for all forty-odd
attempts those gaps were 18.0 um (216 pins), 33.5 um (401 pins) and 41.5 um
(175 pins), while 1552.5 um of free height sat in the one channel carrying
nothing. 33.5 um is 49 met3 tracks for 401 pins.

The 1 KiB build that routed on the first attempt had 138 um and 171.5 um
channels for about 144 pins each. Per pin it had roughly eleven times the track
budget.

Routing resources were never the constraint, and the earlier version of this
section said otherwise. Measured at the die actually used, the 4 KiB design has
about 35 % more resource on every layer than the 1 KiB build that routed, and
fewer blockages:

```
                 1 KiB (routed)   4 KiB (never routed)
macros                  4                 12
blockages          410,491            304,145
met1 derated       814,053          1,100,752
met2 derated       839,766          1,113,521
```

This also explains why enlarging the die from 2800 x 2400 to 2800 x 2900
changed no measured number: all 500 um went into the channel that was already
empty.

`macro_placement_channels.cfg` redistributes the same free height across all
four channels -- 300 / 450 / 450 / 445.4 um -- leaving die, core, macro set and
macro columns untouched. The worst channel becomes 661 tracks for 401 pins. The
flow is re-running from `OpenROAD.Floorplan` on that placement; no post-route
number exists yet.

Utilisation is 46.4 %, below the 60-70 % target: with twelve macros occupying
33 % of the core there is no die size that satisfies both.

---

## 7. What is not established

1. **4 KiB post-route PPA.** No area, timing or power numbers exist for the
   4 KiB ASIC. Global routing has not completed.
2. ~~4 KiB pass-2 double execution~~ -- **done**: 16 of 16 fits, all identical.
   Every FPGA number in this document is now double-executed.
3. **The `ss` corner at 1 KiB** fails setup by 13.26 ns. Not addressed.
4. **Every ASIC timing number published before 2026-09-24 was measured with a
   defective SDC** that silently dropped clock uncertainty, clock transition
   and the I/O delays. Section 6.1 carries the re-measurement. The 4 KiB run
   in progress uses the corrected file; the 1 KiB runs have been re-timed on
   their archived netlists but not re-placed or re-routed, so their hold
   violations remain open.
5. **Host memory faults** are unfixed and are the binding constraint on ASIC
   sign-off. Three failure modes seen: loud crashes, silently wrong data, and
   silent hangs at 4 % CPU.
6. **`regfile` to MLAB** was proposed in an earlier report and is impossible:
   Cyclone IV E has M9K only, no LUT RAM. The alternative, M9K with synchronous
   reads, is a pipeline change requiring full CPI re-measurement. Not attempted.
