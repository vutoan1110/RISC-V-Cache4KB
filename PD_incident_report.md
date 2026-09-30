# PD & DSE Incident Report

Every problem hit in this design-space-exploration phase, what it actually was,
and what was done about it. Kept current as work proceeds.

Status: **post-route PPA measured; the 11 sign-off steps are still running.**

Each incident records the symptom as it appeared, the diagnosis, the evidence
that settled it, and the fix. Where a first diagnosis was wrong, the wrong one
is left in place with the correction, because a report that shows only the final
answer teaches nothing about the cost of getting there.

---

## PART A — The machine

### A1. The host corrupts memory. Everything else is downstream of this.

**Symptom.** OpenLane step 47 failed seven times with seven different impossible
errors: `UnboundLocalError` on a bound parameter, a constructor returning an
`inspect._ParameterKind`, `MemoryError` at 557 MiB RSS with 21 GB free, and a
native SIGSEGV.

**First diagnosis, WRONG.** "The fault is in odb's `dbSet` SWIG binding." A
staged probe was clean at 190k instances and never clean at 1.1M terminals, and
that was read as naming the guilty API.

**What settled it.** A 60-line pure-Python loop with no odb, no rich, no click
and no dataclass, that builds tuples and checks `b == str(a)`:

```
odb probe level 4, openroad python      clean 0/8
pure python, openroad python            clean 1/8   2x CORRUPT-DATA
pure python, system python3 (WSL)       clean 1/8   3x CORRUPT-DATA
pure python, WINDOWS python 3.11        clean 5/8   3x 0xC0000005
```

Three interpreters, two operating systems, one machine. Corroborating: 9
unexpected shutdowns in 45 days, bugchecks 0x1E with 0xC0000005 and 0x50
PAGE_FAULT_IN_NONPAGED_AREA; a GCC internal compiler error that moved between
source files and optimisation passes on rebuild; two mismatched DDR5-4800
SK Hynix modules (HMCG78AEBSA095N and HMCG78MEBSA092N) run as a pair.

**The dangerous part** is `CORRUPT-DATA`: those runs did not crash. They
finished and produced wrong values, caught only because the probe verified
itself.

**Mitigation in force.** Every number must be reproduced by an independent run
before it is reported. Probe: `asic/probe_pure_python.py`, two minutes, no
dependencies. Full write-up: `BAO_CAO_LOI_PHAN_CUNG.md`.

**Cost.** Four tool families were each blamed separately for weeks — OpenLane,
GCC, Quartus (~8% random Access Violations, long recorded as a "Quartus quirk"),
and VS Code crashes. One cause.

---

## PART B — OpenLane, Magic, and the SRAM macro

### B1. Step 47 `Odb.ReportDisconnectedPins` — six patches that fixed nothing

Six edits to `disconnected_pins.py`, each moving the failure somewhere new. That
was read as narrowing a bug; it was A1 being random. Four of the six fixed real
OpenLane defects and are worth keeping — notably `@dataclass` applied over ten
un-annotated class attributes, which yields a dataclass with zero fields — but
none of them could ever have unblocked the step.

**Resolution.** Retry; roughly 2% of runs complete. Step 47 passed on the third
attempt of the retry loop:

```
design__disconnected_pin__count            44
design__critical_disconnected_pin__count    0
```

**Cross-checked independently:** the DEF contains exactly 44
`sky130_fd_sc_hd__conb_1` tie cells, each with one of HI/LO legitimately unused.
Two unrelated artifacts, same number.

### B2. Congestion, antenna segfault, routing

- **Step 37 global routing** failed on congestion. Fixed by a four-corner macro
  floorplan instead of a single column (51% utilisation in a 955 um strip versus
  27% chip-wide).
- **Step 38 antenna check** segfaulted because the macro LEF carried **zero**
  antenna properties. Supplied library-consistent `ANTENNAGATEAREA` and
  `ANTENNADIFFAREA` (`asic/add_macro_antenna_props.py`).
- **Step 43 detailed routing** then completed with `Number of violations = 0`,
  down from 82,554 over nine iterations.

### B3. Magic namespace collision — the real root cause, two bugs in one

**Symptom.** `Magic.StreamOut` failed 14 times, identically every time: 20
"Calma output error: Structure name not found at GDS file position N / Can't
write cell from vendor GDS", plus "59 problems occurred". Deterministic, so not
A1.

**Evidence, from the step's own log:**

```
line  463  Cell sky130_sram_2kbyte_1rw1r_32x512_8 read from path
           $PDK/libs.ref/sky130_sram_macros/mag
line  469  {GDS_FILE <ours>} {GDS_START 0} {GDS_END 15213044}
line 6500  Copying output for cell sky130_fd_bd_sram__openram_dff_2
           from $PDK/libs.ref/sky130_sram_macros/gds/..._8.gds
line 6501  Calma output error: Structure name not found at position 168502
```

`read_macro_gds_blackbox` does `load $macro_name` and only then marks the cell
as a LEF view with a GDS pointer. But `load` searches Magic's cell path first,
and the PDK ships this macro at `libs.ref/sky130_sram_macros/mag`. Magic pulls
in the macro's entire subcell hierarchy before anything is blackboxed:

1. **Namespace collision.** Those subcells collide with cells already on the
   path from `libs.ref/sky130_fd_bd_sram/mag`, so Magic renames the newcomers
   with a `_2` suffix. Verified: the macro GDS holds 161 cells and no `_2`
   variant, so the suffix is Magic's. Their vendor-GDS pointers then name
   structures that exist nowhere.
2. **Byte range from the wrong file.** `GDS_END` is inherited from the PDK
   `.mag` and belongs to the PDK's GDS (15,213,048 bytes) while `GDS_FILE` is
   overridden to the design's copy (14,736,910 bytes) — 476 KB past the end.

**Fix** in `openlane-local/openlane/scripts/magic/common/read.tcl`:

```tcl
cellname create $macro_name        ;# `load` takes this empty cell
load $macro_name                   ;#  instead of searching the path
property GDS_END [file size $gds_file]
```

**Result with `MAGIC_CAPTURE_ERRORS = true`:** Calma errors 0, structure-not-
found 0, unknown-layer 0, no "problems occurred" line, and
`blackboxed ... (0..14736910)` matching the file size exactly.

### B4. Unknown layer/datatype — a second, independent fix

**Symptom.** `Magic.WriteLEF` then failed nine times:

```
[E] Error while reading cell "sky130_fd_bd_sram__openram_dp_cell"
    (byte position 93274): Unknown layer/datatype in boundary, layer=22 type=22
```

**Cause.** Magic's `sky130A.tech` does not declare five layer/datatypes the
OpenRAM macro carries. Named from the PDK's own `sky130A.lyp`, not guessed:

| layer/dt | name | in sky130A.tech |
|---|---|---|
| 22/21 | `cfom.maskAdd` | no |
| 22/22 | `cfom.maskDrop` | no |
| 33/42 | `cp1m.maskDrop` | no |
| 33/43 | `cp1m.maskAdd` | no |
| 235/0 | `boundary` | only 235/4 |

All five are mask data-prep annotation or a cell outline — no device geometry.

**Fix.** `asic/strip_macro_annotation_layers.py` removes exactly those five and
then **proves** the result: KLayout XOR of original against stripped, **34
layers compared, 0 differ**, 412 annotation shapes removed.

**Why B3 and B4 are both needed.** They are not alternatives:

- `Magic.StreamOut` **blackboxes** the macro — copies bytes, parses nothing.
- `Magic.WriteLEF`, `Magic.DRC` and `Magic.SpiceExtraction` do
  `gds read $::env(CURRENT_GDS)` — the **design's** GDS, with those macro bytes
  inlined. Magic parses all of it.

`MAGIC_CAPTURE_ERRORS` stayed `true`. It was set false once as a stopgap and
restored the moment the real fix landed.

---

## PART C — My own tooling

These cost more wall-clock time than any tool bug.

### C1. `pd_retry.sh` sorted step directories as text

`ls` gives `"99-klayout-xor"` after `"126-openroad-stapostpnr"` because `'9' >
'1'`. The name did not map to a step, the function fell through to its
`printf 0` fallback, and the loop re-ran twenty finished steps including RCX and
post-PnR STA. **Fixed:** numeric sort on the step number, walking down until a
name maps.

### C2. `final/` is not a completion test

A truncated run (`--to Magic.StreamOut`, used to validate B3 in isolation)
writes `final/` too. The loop exited on iteration 1 announcing "flow complete"
with eleven sign-off steps unrun — a false PASS from my own tooling. **Fixed:**
completion is the presence of the flow's last step,
`Misc.ReportManufacturability`.

### C3. `pd_retry.sh` ignored `--from`

It reads only `$1`, `$2` and `MAX`. Passing `--from Magic.StreamOut` after a
config change did nothing, so `KLayout.StreamOut` never re-ran and kept feeding
`Magic.DRC` a design GDS built from the unstripped macro — four attempts, forty
minutes each. **Fixed:** a `FROM=<StepID>` environment override for the first
iteration.

### C4. Editing a shell script while bash was running it

Bash reads a script incrementally by byte offset, so an in-place patch shifts
everything not yet read. `run_after_l0fix.sh` died with a syntax error mid-sweep.
**Rule:** never patch a running script; write a new file.

### C5. Sweep script omitted `--compile`

The UVM regression compiles its own file list into the same `work` library.
Without `--compile` the whole 144-run matrix died in under a minute on
`(vopt-13130) Failed to find design unit 'tb_benchmark_snapshot'`. **Fixed:**
`--compile` on the first pass, with the reason in a comment.

### C6. `run_power.py` overwrote instead of merging

Each invocation discarded every point it was not asked for. That is how `dm` —
config 0, the baseline of the whole DSE — ended up with no power number in a
file that already had three. **Fixed:** merge on `point`, plus an `--l0` label so
L0 variants do not overwrite their base point.

### C11. The guard against C10 produced a false FAIL

The fix for C10 added three guards to `run_4kb_pass2.sh`. One of them was wrong,
and it fired on the best possible outcome:

```
[PASS] 1 fit(s)   x16, zero refusals
pass 2 snapshot: 16 rows
[ABORT] the two snapshots are byte-identical -- pass 2 did not measure anything
```

All sixteen fits ran. The snapshots were byte-identical **because every fit
reproduced exactly** -- LE, regs, comb, mem_bits, slack, Fmax, all of it.

The guard's comment stated its own reasoning: *"a real second pass cannot
reproduce a byte-identical file -- the seed column, at minimum, is rewritten."*
The seed column IS rewritten, with the same value. The premise was simply false.

**The right question is not whether the files differ; it is whether pass 2
measured.** The log answers that directly:

```
16 x "[PASS] 1 fit(s)"      every fit completed
 0 x "already running"      no fit was refused
```

Replaced the byte-comparison with that count. The per-fit guard -- abort if any
fit is refused -- is the one that does real work, and it was already there.

**Result, verified properly:** `[VERIFIED] 16 rows compared, 16 identical,
0 mismatched, 0 unpaired`. All four 4 KiB points at four seeds each, reproduced
field-for-field after six to eleven hours on a host that corrupts memory.

**What this cost:** nothing but a scare. What it teaches is narrower and worth
keeping -- a guard is a claim about the world, and this one claimed something
untrue. Guards need the same scrutiny as the measurements they protect.

### C10. A VERIFIED stamp on data that was never re-measured

The worst of the four false verifications, because it produced the word
VERIFIED on a second pass that did not happen.

`run_4kb_pass2.sh` waits for pass 1 to finish, snapshots its rows, re-runs every
fit, snapshots again, and compares. What it actually did:

```
16 x  [FAIL] 1 quartus process(es) already running; fits must be sequential.
 0 x  LE=
      pass 2 snapshot: 11 rows
      [VERIFIED]  11 row(s) compared, 11 identical, 0 mismatched, 0 unpaired
```

**Zero fits ran.** `cmp` on the two snapshots: byte-for-byte identical -- the
verifier compared a file with itself and reported agreement.

**Two independent defects lined up:**

1. The wait loop (`for i in $(seq 1 480); do ... sleep 30; done`) expires after
   four hours and then **proceeds**. Pass 1 was still fitting `sa2_4kb`, so the
   loop simply ran out and carried on as though its precondition were met.
2. Every fit was then refused by the project's own concurrency guard -- which
   did its job -- and the script ignored the refusals and went on to "verify".

`verify_double.py` cannot catch this. It compares two files; it has no way to
know one of them was never written by a new measurement. **A verifier only
proves agreement between whatever it is handed.**

**Both bogus CSVs were deleted** rather than left on disk, because a file named
`fpga_4kb_pass2.csv` sitting next to a VERIFIED line in a log is exactly the
sort of thing that gets believed later.

**Fixes:** the wait aborts instead of proceeding when it expires; any failed fit
aborts the pass; and the comparison refuses to run if the two snapshots are
identical files, since a real second pass cannot reproduce a byte-identical file
by accident -- the seed column, at minimum, is rewritten.

**Rule, fourth statement:** a PASS must come from an artifact the tool wrote on
success. Extended here: a VERIFICATION must come from two artifacts that were
independently *produced*, and the check must prove they were.

### C9. A success marker that was true before the step ran

`pd_to_retry.sh` was written with a comment saying, in as many words, that
success must be a directory rather than an exit code -- because exit codes had
already misled this project twice. It then used a marker that is just as
meaningless: the step directory.

```
[1] rc=2 44s  reached Yosys.Synthesis
```

Return code 2, forty-four seconds, and reported as reached. OpenLane creates
`NN-yosys-synthesis/` **before** running the step, so the directory exists
whether or not anything succeeds. Twelve earlier "failures" from the same script
are therefore not twelve measurements of anything; the run before them reported
a success it had not had.

**The marker that works,** checked against real runs rather than assumed:

```
                  state_out.json   netlist
synthprobe (failed)     0             0
fp4kb      (failed)     0             0
synth4kb   (succeeded)  1             1
```

OpenLane writes `state_out.json` only when a step completes. The script now
requires it.

**What this cost.** A thirteen-in-a-row failure rate that appeared to contradict
an earlier one-in-two, which sent me looking for a cause that did not exist. I
measured memory pressure (15.3 GB free on Windows, 21 GB in WSL -- not tight)
and then the corruption rate itself under load:

```
probe under current load   clean 3/8
probe measured earlier     clean 1/8
```

Load does not make the fault worse; if anything the reverse, within the noise of
an eight-sample test. The hypothesis was wrong and the evidence for it was an
artefact of my own broken check.

**Rule, third statement of it in this report:** a PASS comes from an artifact the
tool writes on success -- a metric, a state file, a netlist -- never from an exit
code, a directory, a pattern count, or the absence of a match.

### C8. The double-execution verifier verified 12 rows of 48 and said VERIFIED

Written to enforce the Double-Execution Protocol, `scripts/verify_double.py`
indexed rows by `--key` first and re-keyed with `--also` afterwards. Indexing a
48-row matrix by `kernel` alone keeps one row per kernel, so the re-key operated
on 12 survivors. Its first run printed:

```
[VERIFIED]  12 row(s) compared, 12 identical, 0 mismatched, 0 unpaired
```

Twelve. The count was printed in the same line as the verdict, which is the only
reason it was caught. **Fixed:** the composite key is built while loading, and a
duplicate key is now a hard failure rather than a silent overwrite.

A verifier that passes on a quarter of the data is worse than no verifier, so
this is recorded even though it never reached a reported result.

**Re-run after the fix:** the full 48-run matrix at the default L0 depth against
the canonical matrix -- `[VERIFIED] 48 row(s) compared, 48 identical`.

### C7. `run_fpga_points.py --list` crashed

`POINTS` gained a `perf` field; `--list` still unpacked five. Pre-existing,
unnoticed because nothing called it. **Fixed.**

---

## PART D — RTL

### D1. L0 hot buffer: the tag slice did not track the index width

**Symptom.** All 48 simulations at `L0_ENTRIES=4` failed on the firmware result
check. `ablation_l0_4.csv` came out with a header and no rows.

**Cause, mine.** Parameterising the depth narrowed the index and left the tag
pinned:

```verilog
assign hot_index = request_block[L0_IDX_BITS-1:0];   // narrows
... (hot_tag[hot_index] == request_block[27:3]);     // does not
```

At four entries bit 2 belongs to neither field: two blocks share an entry and
match each other's tag, so the buffer returns the wrong line.

The patch script that introduced the parameter carries the comment "the tag
stored alongside must widen as the index narrows" directly above an edit whose
`old` and `new` strings are identical. The requirement was written down and then
shipped as a no-op.

**Six write sites; the first fix found four.** Two survived on whitespace
differences and a line break. What found the rest was grepping for the *pattern*
rather than the string:

```
grep -n '\[27:3\]\|\[BLOCK_WIDTH-1:3\]\|BLOCK_WIDTH-4\|\[24:0\]'   ->  clean
```

**Rule:** after a width parameterisation, grep every hardcoded form of the old
width and require zero hits. Anchor counts prove an edit applied, never that it
applied everywhere.

**Verification:** lint 0 correctness warnings; directed regression 126 PASS /
0 FAIL; UVM PASS; and the full 48-run matrix at the default depth **48/48
identical to canonical**, so nothing previously published moved.

**Collateral.** The sweep launched before the fix was still alive three hours
later, stuck on `depthconv/SA2` at L0=2 until a 7,200-second timeout: the wrong
line made the firmware branch wrong and never terminate. That process burned a
core all afternoon, which is a large part of why Quartus fits attributed to
"tool contention" ran six times slow.

### D2. `regfile` to MLAB was impossible on this device

Proposed as "the second largest LE lever" (1,446 LC / 1,024 flops) in two
reports. The fit report's own resource table settles it:

```
Family   Cyclone IV E      Device  EP4CE115F29C7
M9Ks     18 / 432 ( 4 % )
```

No MLAB or LUTRAM row exists — Cyclone IV E has M9K only; MLAB is a
Stratix/Arria/Cyclone V feature. The only alternative is M9K, whose reads are
**synchronous**, while the register file needs two **asynchronous** read ports
in decode. That is a pipeline change touching branch flush and write-first
bypass and requiring full CPI re-measurement — not the free win it was described
as. Not attempted; recorded as a separate DSE item.

### D3. The data cache DOES read and write one row in the same cycle

Found while preparing the SRAM-macro version of the cache data array, by
checking an assumption instead of restating it. The first draft of
`asic/soc_dm_control/cache_data_ram_sram4.v` said the controller "is not
believed to" read and write one index in a cycle. It does:

```
dcache_controller.v:251   data_rd_en    = ... || (state == ST_REFILL_DATA) || ...
dcache_controller.v:255   data_wr_en    = ((state == ST_REFILL_DATA) && ...
dcache_controller.v:245   data_rd_index = (state == ST_IDLE) ? ... : request_index
dcache_controller.v:257   data_wr_index = request_index
```

In `ST_REFILL_DATA` both enables assert and both indices are `request_index`.
**Every refill beat** reads and writes the same row -- not an edge case.

The instruction cache is clear: `data_rd_en = request_fire && !hot_hit` with
`req_ready = (state == ST_IDLE)`, while `data_wr_en = refill_write_beat` only
asserts outside ST_IDLE, so the two are mutually exclusive by state.

**Why it matters.** The register array returns the OLD contents on such a cycle
(non-blocking assignment). An OpenRAM 1rw1r macro leaves port 1 undefined while
port 0 writes the same address. Had the wrapper gone into a build on the strength
of the original sentence, the data cache would have been reading undefined values
on every refill beat of the 4 KiB ASIC.

**Handling.** The wrapper suppresses the read on exactly the bank being written
at that row, so the value is defined and the other three banks still return
their contents. That is deliberately NOT identical to the register model, and is
only harmless if nothing consumes the line read during ST_REFILL_DATA -- the
controller re-reads in ST_CPU_RESP a cycle after the last write, which would
make it harmless, but that is reasoning again. A simulation-only counter is
built into the wrapper so `tb/dcache_tb.sv` can report how often the conflict
actually fires.

### D4. The conflict counter introduced two correctness-class lint failures

The instrumentation added for D3 was itself wrong:

```
BLKSEQ       conflict_count = conflict_count + 1;   inside a clocked process
PROCASSINIT  integer conflict_count = 0;            initialiser on the declaration
```

This project counts `BLKSEQ` as correctness-class, which must be zero. Fixed by
using `<=` and moving the initialisation into an `initial` block. Linting the
new file before it reached a build is what caught it; the file now has two
warnings, both structural and both understood -- `PINCONNECTEMPTY` on the
deliberately open `dout0`, and `DECLFILENAME` because one file holds three
modules and only one name can match it.

### D5. The two tag RAMs were written differently, and only one scaled

The first synthesis attempt of the 4 KiB ASIC stopped before it began:

```
%Error-BLKLOOPINIT: hdl/cache/icache_tag_ram.v:57:27:
    Unsupported: Delayed assignment to array inside for loops
```

Verilator will not unroll a 256-iteration non-blocking assignment to an array.
At 64 lines it unrolls, so the 1 KiB build has **zero** occurrences and the
defect stayed invisible until the capacity changed.

The cause is that the two tag RAMs do the same job in two different ways, and
only one of them scales:

```verilog
// dcache_tag_ram.v -- fine at any depth
reg [LINE_COUNT-1:0] valid_bits;
valid_bits <= {LINE_COUNT{1'b0}};

// icache_tag_ram.v -- the one that broke
reg     valid_bits [0:LINE_COUNT-1];
integer i;
for (i = 0; i < LINE_COUNT; i = i + 1)
    valid_bits[i] <= 1'b0;
```

**Fix:** make the instruction cache match the data cache. Semantically
identical, so the 1 KiB matrix must come back byte-for-byte -- which is checked,
not assumed, by re-running the chain at 64 lines as well as 256 and comparing
both against their existing verified matrices.

**The part worth keeping.** `scripts/lint_rtl.sh` swept LINE_COUNT 256 and
reported clean; OpenLane's own lint on the same file reported an error. The
difference is the Verilator flags each uses. This is the second time a defect
has been found by the tool that builds the chip on a scope my lint script did
not cover -- the first was `bank_csb0` declared `[1:0]` against a 1-bit signal.
My lint is a fast filter, not a substitute.

---

## PART E — Measurement corrections

### E1. L0=4 "improves slack" — reported backwards

Reported as `-721 LE and +0.710 ns slack`, an improvement on both axes. That was
**one** fit, at seed 2, on the RTL of D1. With four seeds on correct RTL:

```
L0=8   14638 14596 14600 14672   worst slack  0.000 ns
L0=4   13893 13859 13910 13921   worst slack -0.297 ns   <- misses 50 MHz
```

Timing gets **worse**, not better. The four-seed requirement caught it; a single
fit said the opposite of the truth.

### E2. The L0 depth, finally priced on all three axes

```
              LE (mean of 4)   regs   worst slack    power      48-run cycles
L0=8              14,626       8,015     0.000     272.25 mW     6,261,571
L0=4              13,896       7,403    -0.297     270.19 mW    +6.42%
L0=2              13,498       7,095    -0.052     264.76 mW   +15.45%
```

**Verdict: eight entries stays.** Halving costs 6.42% of runtime for 5.0% of
logic and 0.76% of power, and worsens worst-case timing.

Spread across kernels at L0=4 — a step function, not a gradient:
`mont64 +19.21%`, `md5sum +15.33%` against `fdct +0.00%`, `insertsort +0.02%`.
A single-kernel probe would have been worthless.

### E3. False PASS reports I issued

- Claimed step 47 had passed after `grep -c "Error|Traceback"` on a step log
  returned 0. The traceback was elsewhere in the same file.
- Claimed `@dataclass` was fixed upstream; `diff` proved HEAD identical to
  2.3.10, 0 lines different. My `sed` range had started *at* the class line,
  cutting the decorator above it.
- Announced "flow complete" from `final/` (C2).

**Rule adopted:** no PASS is reported from directory existence, pattern counts,
or absence of a match — only from a metric or a tool's own verdict.

---

## PART F — Results banked

### Post-route ASIC, `soc_dm_control`, sky130

```
DIE_AREA        1800 x 2900 um  =  5.22 mm^2
instance area   2,720,150 um^2  (macros 1,138,150 + stdcell 1,582,000)
utilisation     53.35%   (stdcell alone 39.94%)
std cells       186,877  (27,642 sequential, 6,603 antenna diodes)
routing         0 DRC violations; 7.30 m wire; 1,048,010 vias, all single-cut
```

Timing, 9 corners, post-route with RCX parasitics, 20 ns target:

```
hold    0 violations at EVERY corner, worst +0.0919 ns
setup   tt and ff PASS (+2.80 .. +5.68 ns)
        ss  FAIL  -13.26 ns, 8,846 violating paths, TNS -12,723 ns
max cap 658 violations       max slew 4,730 violations
```

**The design closes at the typical corner and does not close at the slow
corner** (100 C, 1.60 V): the critical path needs about 33 ns, roughly 30 MHz.

Power, nom_tt_025C_1v80, post-route:

```
total 196.4 mW   internal 108.6 (55.3%)  switching 87.7 (44.6%)  leakage 0.14
combinational 86.3   sequential 58.3   clock 40.6   macro 11.2
```

### FPGA, DE2-115, every point at four seeds with measured power

| point | L0 | LE (seeds 1/3/4/2) | mean | regs | worst slack | power |
|---|---:|---|---:|---:|---:|---:|
| `dm_nopc` | 8 | 11884 11894 11888 11874 | 11,885 | 5,977 | -0.140 | 261.19 mW |
| `dm@l0-2` | 2 | 13456 13526 13547 13465 | 13,498 | 7,095 | -0.052 | 264.76 mW |
| `dm@l0-4` | 4 | 13893 13859 13910 13921 | 13,896 | 7,403 | -0.297 | 270.19 mW |
| `dm` | 8 | 14638 14596 14600 14672 | 14,626 | 8,015 | **+0.000** | 272.25 mW |
| `dm_dse` | 8 | 15082 15007 15084 15107 | 15,070 | 8,113 | +0.205 | 276.38 mW |
| `sa2` | 8 | 16181 16211 16128 16223 | 16,186 | 8,322 | +0.028 | 296.10 mW |
| `dm_vc4` | 8 | 17968 18033 17897 17971 | 17,967 | 9,898 | -0.290 | 302.12 mW |

`dm` is the only point with no negative seed. Quoting seed 2 alone would have
shown `dm_vc4` comfortably positive at +0.708 ns.

DSE deltas with the controller held constant: associativity **+1,204 LE
(+8.0%)**; victim cache **+3,026 LE (+20.2%)** — three times the cost of
associativity, for the organisation with the worst CPI in the matrix.
Control-logic overhead (config 0 vs 3) **+411 LE**, outside the measured
four-seed noise.

---

## PART G — Re-targeting PD at 4 KiB

The 1 KiB sign-off was stopped on instruction: 4 KiB is the configuration of
record, so signing off 1 KiB proves nothing about the design being taken
forward. What 1 KiB produced is kept as a reference point, not discarded.

### G1. Why 4 KiB cannot simply be reparameterised on the ASIC

On the FPGA a capacity change is free: `LINE_COUNT` is a parameter, and
`(* ramstyle = "M9K" *)` sends the arrays into block RAM, so 64 to 256 lines
costs block memory bits rather than logic.

Yosys has no equivalent. `hdl/cache/icache_data_ram.v` is four `reg [31:0]`
arrays; on the ASIC they synthesise to flip-flops. Counting it out:

```
                       bits per cache      both caches
LINE_COUNT =  64    4 x 64 x 32 =  8,192      16,384 flops
LINE_COUNT = 256    4 x 256 x 32 = 32,768     65,536 flops
```

Post-route at 1 KiB the whole chip has **27,642 sequential cells**, so the two
cache data arrays already are roughly 59% of every flop on the die. Taking them
to 4 KiB in flip-flops would put the count near 77,000 -- almost three times as
many -- and the area with it. That is not a design point worth measuring.

### G2. The macro that fits exactly

A 4 KiB cache bank is 32 bits x 256 words. Both of these exist on this machine:

```
$PDK/libs.ref/sky130_sram_macros/lef/sky130_sram_1kbyte_1rw1r_32x256_8.lef
~/tools/openram_out/test_noperim/test_sram_1rw1r_32x256_noperim.{gds,v,lef}
```

The PDK's `sky130_sram_1kbyte_1rw1r_32x256_8` is an exact fit for one bank and
ships with LEF, GDS, lib, spice and verilog views. Four banks per cache, eight
for instruction and data, alongside the four 2 KiB macros already used for main
memory: **twelve macros on the die**.

The access pattern matches without changing the pipeline: `1rw1r` gives one
read-write port and one read port, which is what the array needs -- a full-line
read across four banks while one bank is written -- and the existing RTL already
registers read data on the clock edge, so the macro's synchronous read needs no
new cycle.

### G4. Synthesis measured, and the estimate held

The 4 KiB design synthesised on the second attempt (the first died at ABC with
return code 139 -- SIGSEGV, incident A1; Yosys had already extracted the full
netlist, so the design was never in question).

```
                  stdcell area        instances
1 KiB              1,386,981 um2        102,041
4 KiB              1,036,877 um2         77,310
                    -350,105 (-25.2 %)   -24,731
```

**A quarter less logic at four times the capacity**, which is the macro doing
exactly what it was brought in for. Working back: 350,105 um2 over 16,384
flip-flops is **21.37 um2 each**, against the 20.0 um2 the die estimate had
assumed -- 6.8 % out, not enough to change any conclusion.

Also from the same run: `design__inferred_latch__count 0` and
`design__lint_error__count 0`, so the macro wrapper introduces no latch.

All twelve macro instance names were then read out of the netlist rather than
guessed. The 1 KiB placement file carried a warning to verify its names against
the real netlist "the first time this is run"; this one did.

### G5. The floorplan took three attempts, all three caught before the tools ran

Die sized from the measured area: 1,036,877 um2 scaled by the 1.141
synth-to-post-route growth the 1 KiB build showed, plus 2,663,854 um2 of macro,
gives 3.85 mm2 of instance area.

```
attempt 1   macros in two columns, one down each side
            -> 990 um corridor for every standard cell.
               The 1 KiB design failed global routing twice in a 955 um strip.
               Columns are the wrong shape when macros are 40 % of the die.

attempt 2   horizontal bands, die 2600 x 2500
            -> OVERLAP: the top band needs 683.10 + 4 x 479.78 = 2602.2 um
               against 2576 um of core width. Short by 26 um.

attempt 3   horizontal bands, die 2800 x 2400        CLEAN
```

Final: **2800 x 2400 = 6.72 mm2, 57.2 % utilisation**, macros 39.6 % of the die.
The free region is **2776 x 1052 um = 2.92 mm2, the full die width**, with
standard cells at about 40 % local density and no strip anywhere.

```
band, y=1930     1 main memory + 4 data-cache banks
free,  y 877..1930   the full width, all standard cells
band, y=480      4 instruction-cache banks
band, y=30       3 main memory banks
```

Every attempt was rejected by an overlap and core-bounds check inside the script
that writes the file, not by a floorplanner twenty minutes into a run.

### G3. What this costs, honestly

The macro version of the data array is new RTL, so it carries the whole chain:
lint, 126 directed tests, UVM, the 48-run Embench matrix, each twice. Then PD
restarts **from synthesis** -- `--from` cannot help, because the netlist itself
changes -- and the floorplan has to place twelve macros rather than four, which
is the step that already needed a four-corner layout at four.

Not started. Blocked behind the 4 KiB FPGA sweep and the 4 KiB verification
chain, in that order.

### G6. Four blockers on the way to 4 KiB placement, four different causes

Each one identified by measurement, and one of them was nearly "fixed" the wrong
way.

| blocker | cause | fix |
|---|---|---|
| OpenLane lint stopped synthesis | `%Error-BLKLOOPINIT`: Verilator will not unroll a 256-iteration delayed assignment to an array | `valid_bits` packed, matching dcache_tag_ram (D5) |
| ABC segfault, 13 in a row | host memory fault on a 90,767-gate netlist | reuse the netlist that already succeeded rather than re-rolling |
| GlobalPlacement crash, 3 for 3 | deterministic, always in the timing-driven resizer | `PL_TIME_DRIVEN: false` |
| `DPL-0036`, 8 in a row | legalisation displacement capped at 100 um | `PL_MAX_DISPLACEMENT_Y: 500` |

**The one I nearly got wrong.** `DPL-0036` reports three instances out of 77,000
that cannot be legalised, and the instinct is to give the design more room. The
measured numbers say otherwise:

```
die area            6,720,000 um2
instance area       3,767,140 um2   (my estimate was 3,846,523 -- 2 % out)
utilisation             57.23 %
stdcell utilisation     28.16 %
```

At 28 % standard-cell density there is space everywhere -- just not where those
three cells have to go. Enlarging the die would have cost area, pushed
utilisation below the 60-70 % target, and left the error exactly where it was.
What binds is `PL_MAX_DISPLACEMENT_Y = 100 um` against a free band 1052 um tall.

**Evidence that the earlier density change had worked**, which is why it was
worth keeping: the failing instances changed completely, from
`_060918_ wire13141 _060942_` to `wire13160 wire10971 fanout4969`. Identical
lists would have meant the setting never reached the step.

### G7. Global routing reaches the design, and GRT-0118 does not appear

`OpenROAD.GlobalRouting` now runs. It has failed eight times, every one a native
crash stack, with durations scattered from 79 to 328 seconds and stack depths of
38, 38, 38, 27 -- random, which is the host fault, not the design.

**What matters is the error that is absent.** `GRT-0118` is the congestion
failure that killed the 1 KiB design twice and forced the floorplan from one
column to four corners. It does not appear here. Routing starts, reads the grid,
and crashes for unrelated reasons.

That is the verdict on the floorplan decision: bands with a full-width free
region were the right call. The first draft of `macro_placement.cfg` put macros
down both sides and left a 990 um corridor -- narrower than the 955 um strip
that failed at 1 KiB -- and would almost certainly have reproduced GRT-0118 here.

**Why this step is the hardest to get through,** measured rather than assumed:

```
step                        peak RSS   runtime   outcome
CTS                         2 GiB      1:45      passed
RepairDesignPostGPL         2 GiB      1:26      passed
GlobalRouting               1 GiB      3:46      8 failures
```

Global routing uses *less* memory than the steps that passed. What it has is
**exposure**: four to five minutes of continuous allocation against one to two.
Survival is a function of how long a step spends allocating, not how much it
holds at peak. That predicts detailed routing -- far longer again -- will be the
hardest step in the flow.

### G8. Global routing at 4 KiB: stopped at a stated bound, not abandoned

**Result: the 4 KiB ASIC completes 36 flow steps and does not complete global
routing on this host.**

Forty-three short attempts, every one a crash at a different point, never
`GRT-0118`. Then one attempt ran **244 minutes at 99.8 % CPU with stable 1.34 GB
RSS** -- working, not hung, and 166x the 88 seconds the 1 KiB design took for the
same step. It was stopped at a bound set in advance and for a reason:

> At 240 minutes, global routing is 163x the 1 KiB baseline. Detailed routing on
> the 1 KiB design took substantially longer than global routing. So even
> success here would not lead to a finished flow in any meaningful time --
> the stopping rule is "success would not reach the goal", not "patience ran
> out".

**What completed** (36 steps, each verified by its own `state_out.json`):

```
lint x4 + checkers          synthesis + unmapped/synth checks
floorplan                   twelve-macro manual placement
tap/endcap, PDN             power grid violations checker PASSED
IO placement, DEF template  global placement
repair design post-GPL      detailed placement
CTS                         STA pre-PnR and three mid-PnR
```

Everything up to and including clock tree synthesis works on a twelve-macro
4 KiB design. That is the useful half of the answer.

**What the failure is, and is not.** It is not the design: no congestion error
was ever emitted. It is not the floorplan: the band layout was chosen precisely
to avoid the narrow strip that failed at 1 KiB, and `Checker.PowerGridViolations`
passed with twelve macros. It is not configuration: three changes were made with
measured justification (`PL_TIME_DRIVEN` off, `PL_MAX_DISPLACEMENT_Y` 500, die
2800x2900 for +35.6 % track) and two more were tried and **reverted for buying
nothing** (`GRT_OVERFLOW_ITERS`, `GRT_ALLOW_CONGESTION`).

It is two things multiplying: a design that genuinely needs a lot of routing --
twelve macros, roughly 512 extra cache data wires, `Blockages: 304,145` -- and a
host that corrupts memory. Congestion makes the step long; length makes the
crash likely. The die change attacked the first and measurably moved it; the
second is unfixed hardware.

**What would change the outcome**, in order of confidence:

1. Fix the RAM. Every long step on this machine is a lottery; see
   `BAO_CAO_LOI_PHAN_CUNG.md` for the three-step procedure.
2. Reduce routing demand rather than raise supply -- fewer, wider macros would
   cut the wire count crossing the free band, but sky130's OpenRAM macros are
   32 bits wide and a 128-bit line needs four banks.
3. More die. The last increase bought +35.6 % track and was not enough; the
   next would cost utilisation already at 46.4 %.

---

## Open items

1. **4 KiB post-route PPA** -- nothing yet. Global routing has not completed in
   over forty attempts; every failure is a host crash, never `GRT-0118`. One run
   is currently 74 minutes in at 99.6 % CPU with stable memory, which is
   iterating, not leaking, and is by far the furthest any attempt has reached.
2. **4 KiB pass-2 double execution** -- 5 of 16 fits done, all matching every
   field. `dse_4kb`, `sa2_4kb` and `vc4_4kb` means remain single-pass.
3. **1 KiB `ss`-corner setup** -- fails by 13.26 ns, 8,846 paths. A real result,
   not addressed.
4. **ASIC utilisation** -- 46.4 % at 4 KiB against the 60-70 % target. With
   twelve macros blocking 40 % of the die, no die size satisfies both
   routability and that target. The cost is named, not hidden.
5. **Host memory** -- unfixed, and the binding constraint on ASIC sign-off.
   Three distinct failure modes now seen and each needs its own detector:
   loud crashes (exit code / stack trace), silently wrong data (self-checking
   probe plus double execution), and silent hangs (CPU-versus-wall ratio; one
   OpenROAD process sat at 4.3 % CPU for twenty minutes while the liveness check
   called it healthy).
6. **1 KiB sign-off tail** -- stopped on instruction once 4 KiB became the
   target. Post-route PPA for 1 KiB is banked and kept as the reference point.

---

## Deliverables

- `DSE_RESULTS.md` -- every measured number, with a section stating what is *not*
  established.
- `BAO_CAO_LOI_PHAN_CUNG.md` -- the hardware fault, written for whoever fixes
  the machine.
- `asic/pd_note.txt` -- every PD configuration decision with its evidence, including
  the two that were reverted for buying nothing.
- `CLAUDE_AUTONOMY_LOG.md` -- the running engineering journal.

---

## Incident 33 -- workspace purge, and a proof artifact that had to be rebuilt

The cleanup removed 24.6 GB. Before anything was deleted, every log quoted in a
deliverable was copied out of the deletion zone into `asic/evidence/`, and every
run directory that was deleted left a metrics receipt in `evidence_runs/`.

Three things the purge found that the purge order did not predict:

1. `ablation_l0_4.csv` was listed for deletion as "empty, generated during the
   RTL tag bug". It is not empty. It holds 48 valid rows, written at 19:35 on
   18 Sep, after the tag fix. Deleting it would have destroyed the L0=4 arm of
   the ablation and with it section 5.1 of `DSE_RESULTS.md`. Kept.

2. `BAO_CAO_LOI_PHAN_CUNG_2.md` was named in the do-not-delete list. No such
   file exists anywhere in the workspace and none was ever written. Reported
   rather than silently passed over.

3. The KLayout XOR proof of the `.magicsafe.gds` was required to remain on
   disk. It never existed as a file -- only as prose in this report and in
   `pd_note.txt`. KLayout lives in the OpenLane nix store and is no longer
   reachable from this host, so the original could not be regenerated.

Point 3 was closed with a stronger check rather than a weaker excuse.
`asic/prove_magicsafe_equivalence.py` parses both GDS files record by record
and compares every shape as an exact tuple: structure name, element type,
layer, datatype, and the full coordinate list. An area XOR proves the
difference region is empty; this proves shape-for-shape identity, so a shape
displaced by one database unit -- invisible to an XOR of coincident edges --
would fail it.

It reproduces the original numbers exactly, by a different method:

```
original     215200 shapes
magicsafe    214788 shapes
shapes removed: 412        22/21  35   22/22  12
                           33/42 155   33/43 192   235/0  18   all expected
shapes added: 0
layer/datatypes retained and compared: 34
RESULT: every retained layer is shape-for-shape identical
```

412 and 34 are the same two numbers the KLayout XOR produced. Two independent
tools agreeing on a result neither derived from the other is better evidence
than the single log that was lost. Double-executed, byte-identical.
`asic/evidence/magicsafe_equivalence_proof.log`.

## Incident 34 -- second purge round: the retry storms themselves

The first round removed failed runs. It left the two surviving runs untouched,
and that is where the real weight was: `sync_final` held 151 step directories
for a flow of about 55 steps, `synth4kb` held 149. The excess is the record of
the retry storms -- eleven `Magic.StreamOut` attempts, fourteen consecutive
`odb-reportdisconnectedpins`, six floorplans -- each one a full copy of the
design state.

Two rules, applied to both runs:

- a step directory with no `state_out.json` never completed; delete it
- where a step appears more than once and several completed, keep the last
  occurrence, which is the one the flow carried forward; delete the rest

```
sync_final    27 GB -> 11 GB    151 steps -> 77
synth4kb     7.8 GB -> 2.4 GB   149 steps -> 97
```

Both chains verified afterwards. `sync_final` now reads as a clean flow: 01-46
through detailed routing and `checker-trdrc`, then the signoff tail 119-150 with
RCX, post-PnR STA at nine corners, XOR and streamout. `synth4kb` reads
194-floorplan on the 2900 die through 225-CTS and 228-STA, which is exactly the
furthest state the 4 KiB design ever reached.

Also removed: `openlane-24` and `openlane-next`, 59 MB of dead tooling from the
upgrade attempt of Incident 30, kept until now for a reason that did not survive
checking -- `build_ol3.sh` names `openlane-next` in a comment and operates
entirely on `/nix/store` paths. Nothing executed against either tree, no run
config references them, and nix is no longer present in either WSL distro, so
neither could run. The premise behind them was retracted in Entry 31: the fault
was the host's memory, not OpenROAD, and step 47 later passed on 2.3.10.

Three unused ASIC designs (`soc_dm_dse`, `soc_vc4_check`, `soc_dse_vc1`) gave up
951 MB of synthesis runs, cited in nothing, metrics kept. The Quartus compile
cache (`db/`, `incremental_db/`, 541 MB) is regenerable; all twelve `fit.rpt`,
twenty-one STA/power reports and fifty-seven CSVs remain, so every published
number keeps its source. The cost is that re-running STA or power on an existing
fit now needs a recompile first.

**What this round cost.** The five failed `Magic.DRC` directories were deleted
with their logs. Magic DRC never passed in this run -- all five attempts failed,
so no signoff result was lost, and the DRC figure in `DSE_RESULTS.md` (0
violations from 82,554 over nine iterations) comes from TritonRoute at
`46-checker-trdrc`, which is intact. But the raw evidence for the Magic DRC
failures described in C3 is now only the prose in this report. That was an
oversight in the extraction pass, not a decision.

Across both rounds the workspace went from roughly 61 GB to 13 GB.

## Incident 35 -- why 4 KiB global routing never finished: the pin escape channels

Forty-odd attempts, one 244-minute run, never once `GRT-0118`. The explanation
in section 6.2 of `DSE_RESULTS.md` -- that routing resources were the
difficulty -- is wrong, and the two GRT logs that were kept say so plainly.
Against the 1 KiB build that routed cleanly:

```
                 1 KiB (routed)   4 KiB (never routed)
macros                  4                 12
blockages          410,491            304,145
met1 derated       814,053          1,100,752
met2 derated       839,766          1,113,521
```

The 4 KiB design has about 35 % MORE routing resource on every layer and FEWER
blockages. Resources were never the constraint.

**What is actually different.** Both SRAM macros put their signal pins on the
horizontal edges, measured from the LEFs:

```
                    pins in bottom 20 um   pins in top 20 um
2 KiB (H 416.54)            72                    35
1 KiB (H 397.5)             74                    35
```

Every one of those pins escapes vertically, so what matters is the gap above
and below each macro row. In `macro_placement.cfg` those gaps were:

```
core bottom (12) -> row1 (30)          18.0 um    216 pins
row1 top (446.5) -> row2 (480)         33.5 um    401 pins
row3 top (2846.5) -> core top (2888)   41.5 um    175 pins
row2 top (877.5) -> row3 (2430)      1552.5 um      0 pins
```

33.5 um is 49 met3 tracks at 0.68 pitch, for 401 pins. All of the free area sat
in the one channel that had nothing to carry.

**The control settles it.** The 1 KiB floorplan, same PDK, same macro type,
same router, routed on the first attempt:

```
core bottom -> row1     138.0 um   ~144 pins   203 tracks   1.4x headroom
row1 -> row2           1733.5 um      0 pins
row2 -> core top        171.5 um   ~144 pins   252 tracks   1.7x headroom
```

Worst channel 138 um for 144 pins, against 33.5 um for 401. Per pin, the 1 KiB
design had about eleven times the track budget. That is the difference between
the design that routed and the design that did not.

It also explains why enlarging the die from 2400 to 2900 changed nothing
measurable: all 500 um went into the 1552 um band that was already empty, and
the three real chokepoints were untouched. The GRT-0053 table came back
byte-identical, and at the time that was read as the override not reaching the
tool. It reached the tool. It just did not touch the constraint.

**Fix.** `macro_placement_channels.cfg` redistributes the same 1645.4 um of
free height across all four channels instead of one: 300 / 450 / 450 / 445.4.
Die, core, macro set and macro columns are unchanged; only the row y
coordinates move. The worst channel goes from 49 to 661 met3 tracks for its 401
pins -- 1.65x headroom, slightly better than the 1 KiB build that worked.

**On the crashes.** Both surviving stack traces die inside global routing's
timing-driven paths: `pdr::primDijkstra` under `makeSteinerTree` (Prim-Dijkstra
Steiner trees, used only when routing alpha > 0) and
`sta::Corners::findPathAnalysisPt` under `FastRouteCore::CalculatePartialSlack`
(maze routing querying STA for per-net slack). A standalone reproducer with
`set_routing_alpha 0` and `-critical_nets_percentage 0` gets past the first of
those and reaches `GRT-0103 Extra Run for hard benchmark` -- the phase the
244-minute run died in. "Hard benchmark" is the router's own verdict, and it is
the congestion above that earns it. The floorplan is the fix; the routing-alpha
setting is a symptom control, kept running as the experimental control.

## Incident 36 -- the dedup in Incident 34 broke both runs' resumability

`RESUME=1 run_pd.sh soc_dm_4kb synth4kb --from OpenROAD.Floorplan` refused to
start:

```
ValueError: Provided path '.../runs/synth4kb/19-openroad-floorplan/soc_asic_top.nl.v'
to design format '.nl' does not exist.
```

`19-openroad-floorplan` is one of the superseded duplicates deleted in Incident
34. OpenLane's `flow.start` calls `Step.load_finished` for every step directory
in the run and each one's `state_in.json` names files by absolute path in
whichever earlier directory produced them. The state chain is cross-referential,
not linear: a step's state carries forward views created many steps earlier, so
an "older, superseded" directory is still the file owner for views that later
steps inherited.

Counted after the fact:

```
synth4kb     30+ surviving steps referencing deleted directories
sync_final   12 deleted directories still referenced
```

**The claim in Incident 34 was wrong.** It said both chains were "verified
afterwards". What was actually verified was that the surviving step *sequence*
read as a coherent flow -- 01-46 then the signoff tail, 194-floorplan through
228-STA. That is a check on the names, not on the contents. No state reference
was resolved. The rule "keep the last occurrence of each step" is wrong for
OpenLane because it assumes each step owns its own outputs, and they do not.

**What is actually lost.** Nothing in the 1 KiB deliverable: `sync_final/final`
is self-contained -- GDS, DEF, netlist, LEF, nine LIBs, three SPEFs, nine SDFs
and a 270-field `metrics.json` -- and every published number comes from there or
from the step directories that survive. What is lost is the ability to resume
either run. The 1 KiB flow is finished, so that costs nothing. The 4 KiB flow is
not, so it costs a fresh run from synthesis.

**Rule.** An OpenLane run directory is not safe to deduplicate. Delete step
directories with no `state_out.json` -- those never produced anything and
nothing can reference them -- and nothing else. If space is needed from a
finished run, the thing to keep is `final/`, which is self-contained by
construction.

## Incident 37 -- the host can no longer synthesise, and the proof is Yosys's own determinism

The channel-corrected run had to start from synthesis, because Incident 36 left
no resumable state. It never got past it. Twenty-seven consecutive attempts
across two independent run tags, zero successes:

```
rc=1   22    OpenLane reported the Yosys subprocess failed
rc=139 13    SIGSEGV
rc=2    5
```

The decisive evidence is not the count, it is the variety. Yosys is
deterministic: the same 42 Verilog files and the same synthesis script must
produce the same log every time. Twenty-six attempts produced twenty-six
different logs, dying in nine different passes:

```
PROC_ARST  PROC_DLATCH  OPT_EXPR  OPT_MERGE  OPT_MUXTREE
OPT_DFF    OPT_REDUCE   CHECK     ABC
log length 1,745 .. 15,341 lines
```

with errors including `free(): invalid pointer`, an assertion failure in
`check.cc:178` on `from_bit >= 0 && from_bit < from_portsig.size()`, and runs
that simply stopped mid-line. A kernel trace for one of them reads
`segfault at 3dfa ... error 4 in libc.so.6` -- a 15,866-valued pointer
dereferenced by an AVX string routine, i.e. an integer where an address should
be. WSL had 21 GiB of 23 GiB free, so this is not exhaustion.

A fresh run tag failed identically, which rules out accumulated state in the
run directory.

**What was done.** `synth4kb/06-yosys-synthesis` completed earlier on the same
inputs. Its step config differs from this run's in exactly one key, `DIE_AREA`,
and `DIE_AREA` appears nowhere under `openlane/scripts/yosys/` nor in
`openlane/steps/yosys.py` -- Yosys.Synthesis never reads it. That netlist is
therefore the netlist this run would have produced.

`asic/graft_synthesis.py` writes a synthesis step into the target run pointing
at a copy of it, with `state_in` taken from the target run's own JsonHeader
step so the chain stays internally consistent. The copy is byte-identical
(sha256 prefix `6f16a7ee04eb1ef4`) and carries the measured metrics forward:
77,310 instances, 1,036,876.95 um^2.

**This is stated plainly because it matters for how the 4 KiB result should be
read.** The 4 KiB physical design from this point on is built on a netlist
produced by an earlier run, not by this one. Everything downstream -- floorplan,
placement, CTS, routing, signoff -- is this run's own work on the corrected
floorplan. Re-deriving the netlist on this host is not currently possible.

## Incident 38 -- the silent hang, and where it comes from

`OpenROAD.STAMidPNR` on the corrected floorplan failed five times, then a sixth
attempt did something the retry driver could not handle: it stopped without
stopping. OpenROAD had exited, but the OpenLane Python parent stayed alive and
never returned, so the driver waited on it indefinitely.

Measured rather than assumed:

```
CPU ticks      193 -> 207 over 30 s of wall time   = 0.5 %
process state  S
blocked in     futex_wait_queue
openroad       gone
step log       1,441,437 bytes, unchanged over the sample
```

**The mechanism is in the traceback that preceded it.** `/tmp/ch4kb.log` ended
with:

```
File ".../openlane/common/ring_buffer.py", line 48, in push
    self._store[self._tail] = element
IndexError: list assignment index out of range
```

That buffer is constructed as `RingBuffer(str, 10)`: `_store` is a list of
exactly ten strings and `push` always writes at `_tail`, which is kept modulo
`_max` on every update. The assignment on line 48 cannot be out of range in
correct execution -- there is no input that makes it so. It is corruption
reaching CPython's own objects, the same fault that gives Yosys twenty-six
different logs.

The consequence is the hang: `step.py` drains the subprocess output on a
separate thread, that thread died on the IndexError, and the main thread then
waited on its lock forever. So the silent hang is not a fourth failure mode --
it is the same corruption, landing in the one place where the process does not
die but also cannot continue.

**Fix.** `asic/hang_watchdog.sh` samples `/proc/<pid>/stat` utime+stime twice
and kills any OpenLane process older than 240 s that is using less than 3 % CPU
across a 60 s window, so the retry driver sees a return code and reconnects. The
first kill, done by hand to confirm the diagnosis, was followed immediately by a
fresh attempt running at 94 % CPU.

The age floor matters: OpenLane spends its first minute inside `nix-shell`
evaluating and reading libraries, which is genuinely low-CPU, and killing that
would make the flow unable to start at all.

### 38a. The watchdog killed the step it was protecting

The first version of `hang_watchdog.sh` read `utime+stime` from
`/proc/<pid>/stat` for the process matched by
`pgrep -f "openlane-wrapped.*ch4kb"`. That is the Python parent, and the Python
parent is idle by design -- it waits while `openroad` does the work in a child
process. So the watchdog measured 0 %, decided the run had stalled, and killed
`OpenROAD.RepairDesignPostGPL` at age 271 s while its child was at 99.8 % CPU
and its log was still advancing (the resizer table was counting down 70,132 ->
70,032 -> 69,932).

```
[watchdog] 2026-09-19T12:23:54+00:00 STALLED pid=19586 age=271s cpu=0% -- killing
```

Six minutes of resizer work destroyed by the thing meant to protect it. Fixed
by summing CPU across the parent, its direct children, and any `openroad`
process belonging to the run tag, so the measurement covers the tree that is
actually doing the work.

**Rule.** A stall detector must measure the process that does the work, not the
one that waits for it. Before arming one, check what the supervised process
looks like when it is healthy -- here, healthy is the parent at 0 %.
