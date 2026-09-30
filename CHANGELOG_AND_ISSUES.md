# research/ — complete record of changes, defects and open items

Written for the author and anyone reviewing this work. It covers everything
from the creation of `research/` onward: every RTL change, every defect found
in the frozen design, every defect introduced by this work and later corrected,
every gap in the verification environment, and every item still open.

Nothing here is omitted because it was fixed. A defect that was found and
corrected is still a defect that existed, and the way it was found matters more
than the fact that it is gone.

---

## 1. Why `research/` exists

The frozen design is published and must not change. The peer review asked for
experiments that require changing it. `research/` is a mirror of the repository
layout, so every relative path inside `.qsf` and `config.json` resolves inside
it, and Quartus and OpenLane write their outputs there instead of over the
published artifacts.

`hdl/`, `tb/`, `sw_baremetal/`, `verification/`, `quartus/` and `asic/` at the
repository root are untouched. `git status` shows only `research/`.

---

## 2. RTL changes, by file

All paths are under `research/hdl/`. Line counts are against the frozen file.

| File | Lines changed | What changed |
|---|---:|---|
| `cache/icache_dse_core.v` | 208 | `LINE_WORDS` parameterisation; eviction gate; `VC_DEPTH`; pointer wrap; parameter guard |
| `cache/dcache_dse_core.v` | 183 | same, plus the store path |
| `axi/cache_axi_master.v` | 50 | burst length, beat counter width, refill address alignment, parameter guard |
| `cache/cache_dse_data_bank.v` | 67 | banks generated from `LINE_WORDS`; parameter guard |
| `soc_top.v` | 7 | `CACHE_LINE_WORDS` plumbing |
| `board/de2_115_top.v` | 6 | `CACHE_LINE_WORDS` plumbing |
| `cache/icache.v`, `cache/dcache.v` | 2 each | pass `LINE_WORDS` down |

Every default is the frozen value, so the design is behaviourally identical at
`CACHE_LINE_WORDS=4`: **48/48 simulation runs reproduce the frozen cycle counts
exactly**, and a Quartus fit of the baseline reproduced **15,188 LE, 8,356
registers, +0.629 ns slack, 51.62 MHz** — all four quantities.

The sanitation pass in section 9 changed the RTL again, after that check. The
48-run equivalence still holds byte for byte; the fit figures moved, and the new
baseline is in 9.6.

---

## 3. Defects found in the frozen design

These existed before this work and are not caused by it.

### 3.1 The AXI master forces 16-byte refill alignment

```verilog
addr_q <= {i_refill_req_addr[31:4], 4'b0000};
```

Masking to 16 bytes is a no-op for lines of 16 bytes or more, because the cache
already sends an address aligned to its own line. It is wrong for anything
smaller: an 8-byte line refilling `0x48` would fetch `0x40`.

Only visible once line size became a variable. Found by sampling the cache FSMs
over time: at 8 B the I-cache access count froze at 18 with the FSM in
`ST_IDLE`, which ruled out a stalled controller and pointed at wrong
instruction data.

### 3.2 The eviction copy is gated on the wrong flag

```verilog
if(IS_SA2) begin ... end else begin ... evict into the victim buffer ... end
```

The eviction copy that fills the victim buffer is gated on the configuration
*not* being SA2, rather than on it *being* VC4. Any direct-mapped configuration
without a readable victim buffer therefore pays eight cycles per conflict miss
to fill a buffer it can never read.

This is latent in the frozen design because no such configuration exists there.
It becomes a real defect the moment one is added, which is what the ablation
does. See §4.1 for the damage it caused before it was found.

### 3.3 The verification environment shares the design's wrong assumption

`axi_scoreboard.sv` asserted 16-byte alignment and computed expected refill data
from the raw request address. Those are the same two assumptions as §3.1.

**A checker that shares a design's mistake cannot detect it.** This is the most
important single finding in this document.

---

## 4. Defects introduced by this work, and corrected

### 4.1 The first ablation was not an ablation

`CACHE_CONFIG=3` was introduced as "direct-mapped on the ten-state controller".
Because of §3.2 it was actually "DM+VC4 with the lookup disabled": it paid every
cost of the victim buffer and collected none of the benefit.

Every number derived from it was wrong, and all of them had been reported:

| Quantity | Reported | Correct |
|---|---|---|
| Controller cost | +10.25% | **+9.35%** |
| Associativity | −1.16% | **−0.34%** |
| SA2 wins / ties / losses | 11 / 1 / 0 | **3 / 8 / 1** |
| Weighted CPI, cfg 3 | 1.4327 | **1.4210** |
| Capacity sweep at 512 B | −9.57% | **−3.52%** |
| Line size at 64 B | −4.78% | **−1.39%** |

The headline claim built on it — *"two-way associativity wins on eleven of
twelve kernels"* — did not survive. The corrected claim is weaker and different:
associativity **changes nothing on eight of twelve kernels** and loses on
matmult. What survives is that the published 8.98% gap is almost entirely the
controller, not the organization.

The paper had already been edited with the wrong numbers and was corrected
afterwards.

### 4.2 Width mismatches that do not fail compilation

Three occurrences, all silent:

1. **Port wider than driver.** `wr_word` widened to 3 bits while the driver
   stayed 2. The top bit was unresolved, every comparison went X, and **no bank
   was ever written**. Questa emitted `vopt-2241`, which was dismissed as
   benign. It was not.
2. **Driver wider than port.** At 16 words the 4-bit index was truncated to 3
   bits and words 8–15 aliased onto 0–7. Symptom: hang.
3. **Counter too narrow.** `read_beat_count_q` was 3 bits, insufficient for a
   16-beat burst.

### 4.3 The beat counter regressed the baseline timing

Widening `read_beat_count_q` unconditionally to 4 bits cost **10 LE and 0.66 ns
of setup slack**, pushing the direct-mapped configuration **below 50 MHz**
(−0.032 ns).

Three candidate causes were eliminated by experiment, not by argument: the
revision name (same result), the flow invocation (same result), and finally the
RTL itself (confirmed). Making the width conditional restored **exactly**
15,188 LE and +0.629 ns.

### 4.4 The first `VC_DEPTH` fix was not clean

Sizing only the storage arrays by `VC_DEPTH` left `vc_valid` and `vc_hit_vec` at
`VICTIM_ENTRIES` while the loops driving them were bounded by `VC_DEPTH`. Valid
bits existed that were never written, so the structure did not express the
intent; it merely behaved correctly by accident.

`vc_replace_ptr <= vc_selected + 1` could also address one past the end at depth
1. That was safe **only because the path happens to be unreachable there** — a
correctness argument resting on unreachability rather than on structure.

Corrected: every victim width derives from `VC_DEPTH`, and the pointer wraps
explicitly so it cannot leave the array at any depth, reachable or not.

### 4.5 A reference-model rule that fitted the data instead of the hardware

The independent cache model initially needed a `skip_after_clear = 1` rule to
match. It matched **4 of 5 kernels**; `md5sum` disagreed in the opposite
direction. The rule had been given a plausible-sounding hardware justification.
It was wrong.

The real cause, found by reading `perf_counters.v`:

```verilog
if(icache_access_event_q)        // registered event
    icache_access_count <= icache_access_count + 1'b1;
```

Events pass through a register before being counted, so the clear/freeze gate
that decides whether an access counts is the one standing a cycle **after** the
access. Carrying the hardware's own gate per access in the trace removed the
heuristic entirely.

**A rule that matches 4 of 5 cases is not a rule with an exception; it is a
wrong rule.**

### 4.6 A broken audit that reported false differences

The firmware audit first reported 12 of 13 kernels as differing. The build was
not switching kernels: `make` reported the targets up to date, so every
iteration rebuilt the same default. The tell was that every "built" hash was
identical. With `make clean` between builds: **13/13 identical**.

A check that reports a difference is as suspect as one that reports a match.

---

## 5. Verification gaps found

### 5.1 The new configuration had no unit test

`run_full_regression.do` ran `foreach cfg {0 1 2}`. `CACHE_CONFIG=3` — the basis
of the paper's central claim — had no unit test at all.

Added to `cache_configuration_tb` with the expectation that it must thrash
exactly as `cfg 0` does. That is a direct test of both fixes: a stray second way
would appear as main hits, a live victim buffer as victim hits. Regression went
from 98 to **100 PASS**.

### 5.2 Nine hardcoded four-beat assumptions in the UVM environment

`cache_axi_master` is a UVM DUT and was parameterised, but the environment that
verifies it still asserted a four-beat burst in nine places:

| File | Assumption |
|---|---|
| `axi_scoreboard.sv` | `item.len !== 8'd3` |
| `axi_scoreboard.sv` | `beat.size() != 4` |
| `axi_scoreboard.sv` | `addr[3:0] != 4'h0` (16-byte alignment) |
| `axi_scoreboard.sv` | `data.size() != 4` |
| `axi_scoreboard.sv` | expected data from the raw address, not the line base |
| `axi_scoreboard.sv` | `axi_read_beats != 4 * bursts` |
| `axi_func_coverage.sv` | `bins four = {8'd3}` and the cross referencing it |
| `refill_agent.sv` | `beat.size() > 4` |
| `axi_assertions.sv` | `arlen != 8'd3`, RLAST on beat 4, 3-bit counter |

The environment passed only because it had never been run at any other line
size. Now driven by one `LINE_WORDS` parameter on `tb_axi_top`, passed to the
DUT **and** published to the checkers, so design and checkers cannot be given
different values.

Result: `axi_smoke_test` and `axi_stress_test` both PASS at 8, 16, 32 and 64
byte lines.

### 5.3 A claim about UVM coverage that was wrong

It was stated that "UVM only tests the core, not the caches". `rtl.f` loads ten
cache files including `cache_dse_data_bank.v`. UVM does cover them — but at the
level of elaborating and running, with stimulus not aimed at the victim or
two-way paths. "UVM PASS" is evidence that core-level integration is intact, not
that a cache fix is correct.

### 5.4 No parameter guard on `LINE_WORDS`

The bank word selector is four bits, so sixteen words is the ceiling, but
nothing enforced it. `LINE_WORDS=32` would truncate silently and alias the upper
words — the same failure mode as §4.2.2, which had already cost one debugging
cycle.

Guards added to all four modules and **proven to fire**:

```
LINE_WORDS=32 -> "LINE_WORDS=32 is unsupported"
LINE_WORDS=3  -> "LINE_WORDS=3 is unsupported"
LINE_WORDS=2/4/16 -> runs normally
```

`LINE_WORDS=1` originally did **not** reach the guard: elaboration failed
first with `Range of part-select [1:2] is reversed`. A loud failure, but with an
obscure message rather than the intended one.

**Fixed in the sanitation pass (9.1).** Every derived width in the two DSE cores
is now taken from `EFF_LINE_WORDS`, a clamped copy of the parameter, so
elaboration completes and the guard reports the value the user actually asked
for. Proven at 1, 3 and 32: all three print `LINE_WORDS=N is unsupported`.

---

## 6. Current verification state

| Gate | Result |
|---|---|
| Simulation equivalence, cfg 0/1/2 | 48/48 runs match the frozen counts cycle for cycle |
| Full regression | **100 PASS**, 0 errors (includes cfg 3) |
| Cache / bus / core / directed / conflict suites | 32 / 21 / 47 / 12 / 10 PASS |
| UVM, default | PASS, 6 tests |
| UVM AXI at 8/16/32/64 B lines | PASS, smoke and stress |
| Firmware | 13/13 hex images identical to frozen |
| FPGA fit, baseline | 15,188 LE / 8,356 regs / +0.629 ns / 51.62 MHz — exact |
| Independent cache model | **36/36 runs, all 9 counters exact** (12 kernels × 3 configs) |
| ASIC synthesis | 4 points complete |
| ASIC full PD | in progress |

---

## 7. Open items

1. **`LINE_WORDS` coverage at the cache level is partial.** `run_full_regression`
   now sweeps `tb_cache_configuration` at 8, 32 and 64 B for `CACHE_CONFIG` 1 and
   3, and the UVM AXI tests run at all four sizes. The other five cache
   testbenches are still fixed at 16 B, and `CACHE_CONFIG` 0 and 2 are not swept
   at all — 0 because its controller only supports 16 B (9.3), 2 because the
   victim buffer has no line-size-dependent test.
2. **CoreMark is built but not simulated.** It needs `IMEM_DEPTH`/`DMEM_DEPTH`
   plumbed into the harness, because it does not fit the 8 KiB RAM.
3. **The paper does not yet contain A3, A6, A8 or A9.** All four are measured;
   none is written up. This is the largest remaining gap, because a reviewer
   reads the paper, not the CSVs.
4. **`dm_dse` moved +51 LE after the cleanup**, direction opposite to
   expectation. Within the measured placement noise of 115 LE, so it is
   **not attributable either way** without a multi-seed fit.
5. **A2 on the ASIC side** has a result at 30 ns for the modified RTL only; the
   frozen RTL was not re-run at that period, so the 20 ns and 30 ns figures are
   not a like-for-like pair.
6. **Magic streamout hung** for 89 minutes on one run. Cause not investigated.
   Timing data was recovered from the preceding STA step.
7. **A7 (36 archived board logs)** needs the physical board.

---

## 9. RTL sanitation pass

A full static-analysis pass over `research/hdl/`, run under the mandate that the
design be fixed at the source with no waiver file and no `lint_off` pragma.
Verilator 5.053 was used because Questa's lint does not report width mismatches
inside a module, which is the failure mode that had already cost two debugging
cycles here.

### 9.1 What the linter found, and what was done

| Class | Before | After | Fixed by |
|---|---:|---:|---|
| `WIDTHEXPAND` / `WIDTHTRUNC` | 28 | **0** | sizing the constant, or stating the extension |
| `SYNCASYNCNET` | 3 | **0** | giving the checker blocks the module's own reset discipline |
| `EOFNEWLINE` | 8 | **0** | trailing newline |
| `UNUSEDSIGNAL`, genuinely dead | 17 | **0** | deleted |
| `UNUSEDSIGNAL` / `PINCONNECTEMPTY`, structural | 98 | 98 | see 9.4 |

Per file:

* **`datapath.v`** - `BRANCH_PREDICT_ENABLE` is an integer parameter and was
  used directly as a one-bit condition in seven places. A `localparam BP_ON`
  states the intent once, in one bit. Seven alias wires (`pred_taken_d`,
  `pred_target_d`, `pred_taken_e`, `pred_target_e`, `predict_taken_f`,
  `actual_taken_e`, `actual_target_e`) were each a second name for a signal that
  already had one, driven and read by nothing in either repository; deleted. A
  leftover `integer i`, neither driven nor used; deleted.
* **`tx_block.sv`, `rx_block.sv`** - a four-bit counter indexed an eight-bit
  vector. The counter genuinely needs four bits, because it reaches
  `data_bit_width` on the cycle the state leaves `TRANSMIT`; the index into the
  data does not. Now `data_bit_count[2:0]`.
* **`baudrate_gen_block.sv`** - `COUNT_MAX` was spelled in capitals but is a
  *signal* that follows `set_baud`. That spelling is what made the first attempt
  at this fix declare it as a `localparam`, which does not compile. Renamed to
  `count_max`; the bit period is now `count_max[COUNT_BIT_WIDTH-1:OS_LOG2]`, a
  part-select rather than a shift that was silently extended at three
  comparisons; `OS_LAST` is sized.
* **`lcd_1602_hex.v`** - a nibble added in an eight-bit context; now `{4'b0, h}`.
* **`perf_counters.v`, `icache_dse_core.v`, `dcache_dse_core.v`** - the
  simulation-only invariant checkers sampled `reset_n` synchronously while every
  other block in the same module uses it as an asynchronous reset. That made the
  reset net the one signal in the design carrying two disciplines. The checkers
  now have the same sensitivity list as the counters they check.
* **`hazard_unit.v`** - the input port `predict_redirect_f` was never read. The
  comment that referred to it explained *why* Decode must not be flushed on a
  fetch-stage prediction; that reasoning was kept and the port removed.
* **`soc_top.v`** - eight probe nets driven by a submodule and read by nothing,
  in RTL or in any testbench: `rts_n`, `data_addr`, `data_sel_uart`,
  `data_sel_disp`, `data_sel_timer`, `axi_grant_source`, `apb_sel_unmapped`,
  `perf_counter_freeze_dbg`. The driving ports are now explicitly open.
* **`cache_dse_data_bank.v`, `icache_dse_core.v`, `dcache_dse_core.v`** - every
  comparison of a beat counter or a victim index against parameter arithmetic
  was widening the counter to 32 bits. Sized constants (`LAST_WORD`, `VC_LAST`)
  and explicit pads (`transfer_beat_p`, `refill_beat_count_p`, `vc_hit_vec_p`)
  now state the width. The pads go through a wider vector rather than a
  replication, because a replication would be zero bits wide at `LINE_WORDS=16`.

### 9.2 A real defect the pass exposed

`icache_dse_core.v` wrote the hot-line tag as `request_block[27:3]` at one of
its three write sites; the other two use `request_block[BLOCK_WIDTH-1:3]`.

`BLOCK_WIDTH` is `32 - OFFSET_BITS`. At a 16-byte line it is 28 and `[27:3]` is
correct, which is why every published number is unaffected. At an **8-byte line
it is 29, and the literal dropped the top tag bit** - two different lines could
then report a hot hit. At 32 and 64 bytes it read past the end of the vector.

Verilator did not find this. It lints one configuration at a time, and the first
version of `lint_rtl.sh` linted only the default. Questa's `vopt` reported it as
`(vopt-2697) MSB 27 of part-select into 'request_block' is out of bounds` during
the directed regression, once that regression had been extended to sweep
`LINE_WORDS`. Fixed; the warning is gone and the 110-test regression still
passes.

### 9.3 A methodological error in the lint itself

`CACHE_CONFIG` selects between two generate branches and only the selected one
is elaborated. The first `lint_rtl.sh` linted `CACHE_CONFIG=0`, which contains
the five-state direct-mapped controller and **not** the ten-state DSE core. It
reported zero correctness warnings. Linting `CACHE_CONFIG=1` reported
**seventeen**.

This is the same failure as 4.1 and 4.6: a control point that does not cover the
space it claims to cover. `lint_rtl.sh` now sweeps all four configurations and
merges the findings. All four report zero.

The direct-mapped baseline branch of `icache.v` and `dcache.v` was also found to
hard-code a 16-byte line - `TAG_WIDTH`, the 128-bit line register and the
two-bit word select are literals, and `LINE_WORDS` never reaches the controller
or the RAMs. Nothing published or measured uses that combination, because the
line-size study deliberately runs on the DSE core so that the controller is held
constant. It now fails loudly instead of elaborating into a cache that addresses
the wrong words.

### 9.4 What was not driven to zero, and why

`UNUSEDSIGNAL` and `PINCONNECTEMPTY` remain at 98 per configuration. They are
not dead code:

* **61** are the debug taps and the retire trace port in `soc_top.v`
  (`retire_*`, `*_dbg`, the cache and AXI counters). They are read by the
  directed testbenches, the UVM environment and the Spike co-simulation through
  hierarchical references, which do not exist when `soc_top` is elaborated
  alone. Linting the benchmark harness as top removes ten of them - exactly the
  ones that harness probes - which is the evidence that the rest are live too,
  from other consumers.
* The remainder are correct by construction: address bits a peripheral does not
  decode (`PADDR[11:8]`), the offset bits a refill must ignore
  (`i_refill_req_addr[3:0]`), the low half of a multiplier whose high half is
  the result (`product_uu[31:0]`, for `MULHU`), the index bits of a tagless BHT
  (`fetch_pc[31:10,1:0]`), and the write response `m_axi_bresp`, which this
  design deliberately does not propagate.

Reaching zero would mean deleting the observation interface that every
measurement in the paper depends on, or removing ports from modules that unit
testbenches drive. `lint_rtl.sh` therefore splits the classes: the correctness
classes must be zero and the script fails if they are not; the structural
classes are reported and enumerated here. **No `.vlt` file and no `lint_off`
pragma exists anywhere in the tree.**

### 9.5 Regression after the pass

| Gate | Result |
|---|---|
| Verilator, correctness classes, `CACHE_CONFIG` 0/1/2/3 | **0 warnings** |
| Directed regression | **110 PASS**, 0 errors, 0 out-of-bounds warnings |
| 48-run benchmark matrix | **byte-for-byte identical** to the pre-sanitation CSV |
| UVM, 6 tests | 8/8 PASS |
| UVM AXI at 8 / 16 / 32 / 64 B lines | 8/8 PASS |
| `LINE_WORDS` guards at 1, 3 and 32 | all three report the intended message |
| Quartus DM baseline, seed 2 | see 9.6 |

### 9.6 The new golden baseline

The sanitation pass changed the RTL, so the fit had to be redone. The DM point
was fitted twice at seed 2 on the final RTL, in two different project files, and
reproduced every figure exactly:

| | Published (frozen RTL) | Sanitised RTL | Delta |
|---|---:|---:|---:|
| Logic elements | 15,188 | **15,192** | +4 |
| Combinational | 13,448 | **13,444** | -4 |
| Registers | 8,356 | **8,356** | 0 |
| Memory bits | 83,328 | **83,328** | 0 |
| Setup slack | +0.629 ns | **+0.774 ns** | +0.145 |
| Fmax | 51.62 MHz | **52.01 MHz** | +0.39 |

A single seed says nothing on its own, so the DM point was fitted at four
placement seeds on the sanitised RTL:

| Seed | LE | Setup slack | Fmax |
|---:|---:|---:|---:|
| 1 | 15,289 | +0.570 ns | 51.47 MHz |
| 2 | 15,192 | +0.774 ns | 52.01 MHz |
| 3 | 15,141 | +0.656 ns | 51.70 MHz |
| 4 | 15,226 | +0.550 ns | 51.41 MHz |
| **mean** | **15,212** | **+0.638 ns** | |
| **range** | **148** | **0.224 ns** | |

**Area: unchanged.** The +4 LE at seed 2 is 3 % of the seed-to-seed range. The
registers and the memory bits are identical, and the combinational count is four
lower. There is no area effect to claim in either direction.

**Timing: a small real improvement.** This is the one place where the paired
comparison says more than the spread does. Two seeds have a frozen-RTL
measurement to compare against, and both move the same way by nearly the same
amount:

| Seed | Frozen slack | Sanitised slack | Delta |
|---:|---:|---:|---:|
| 2 | +0.629 ns | +0.774 ns | **+0.145** |
| 4 | +0.387 ns | +0.550 ns | **+0.163** |

Two independent placements improving by 0.145 and 0.163 ns is not what noise
looks like; noise moved LE by +4 and -61 at those same two seeds. The worst path
also moved, from `instr_w[0] -> controller|alu_src_e` to
`instr_m[4] -> alu_result_m[28]`: the path that used to be critical is no longer
critical. Neither endpoint is in anything this pass edited, so the mechanism is
not established, and the honest claim is a measured 0.15 ns improvement with an
unexplained cause rather than a designed one.

**The baseline to quote.** For the revised paper the DM point is
**15,192 LE / 8,356 registers / +0.774 ns / 52.01 MHz at seed 2**, and it must be
quoted with the four-seed range (148 LE, 0.224 ns) beside it. Quoting the single
number alone is what made the earlier +51 LE on `dm_dse` look like a result when
it was placement.


### 9.7 A second scope the lint did not cover, and the defect behind it

OpenLane runs its own Verilator lint before synthesis, and its top is
`soc_asic_top` — a wrapper that is part of the ASIC flow and was **not in
`lint_rtl.sh`'s file list at all**. It reported four width warnings that the
project lint could not see.

They were all in `asic/*/axi_ram_32_asic_macro.v`, and one of them was real:

```verilog
reg  [1:0]  bank_csb0   [0:3];   // connected to a 1-bit csb0 port
```

`csb0` on `sky130_sram_2kbyte_1rw1r_32x512_8` is one bit. The wrapper declared
the chip select two bits wide, so every one of the four instance connections
truncated silently. Only bit 0 was ever wired, and bit 0 always carried the
intended value, so the memory behaved correctly — by accident, not by design.
This is the same class as 4.2 and 9.2, in the ASIC memory path this time.

Fixed in all four design directories, which held byte-identical copies. The
three remaining warnings were assignments into the same over-wide register and
went with it.

Two warnings were left alone and are correct: `PINMISSING` on `vccd1`/`vssd1`,
which OpenLane connects through the power grid rather than the RTL view, and
`UNUSEDPARAM` on `DEPTH_WORDS`/`MEMFILE`, which exist so the ASIC wrapper keeps
the same parameter list as the FPGA RAM it replaces.

### 9.8 Suppressions the lint script was carrying

`lint_rtl.sh` ran with `-Wno-DECLFILENAME -Wno-VARHIDDEN`. Those are
suppressions, which is exactly what this pass was told not to use, and they had
been added without measuring what they were hiding.

Measured: `DECLFILENAME` fires **zero** times. `VARHIDDEN` fires **once** —
module `branch` had an input port also called `branch`, so the port hid the
module name in the enclosing scope. The port is a decoded enable, so it is now
`branch_en`.

Both flags are gone. The lint runs `-Wall` with nothing suppressed.

### 9.9 The one warning that is recognised rather than fixed

`de2_115_top.reset_sync_q` raises `SYNCASYNCNET`. It is a two-flop reset
synchroniser: a net that is shifted synchronously and then used as an
asynchronous reset is what a reset synchroniser *is*, and it carries the Altera
`SYNCHRONIZER_IDENTIFICATION FORCED` attribute to say so.

There is no rewrite that removes the warning. Adding a stage changes reset
release timing, which changes the netlist and can move cycle counts; removing
the synchroniser removes the metastability protection that the asynchronous KEY0
input requires.

Turning the class off would have hidden the three genuine occurrences this pass
fixed, so the class stays fatal and **one net is named in the script**, with the
reason, and every other `SYNCASYNCNET` still fails the run. This is the only
recognised exception in the flow; there is no `.vlt` file and no `lint_off`
pragma anywhere in the tree.

### 9.10 ASIC cell counts move under a pure rename

The chip-select fix in 9.7 was followed by a synthesis run, and the cell count
went **up**: 99,078 to 101,719, an increase of 2,641 cells and 2.4 % of area.
Narrowing a register that was already dead cannot add logic, so the number was
not accepted.

The two runs' `resolved.json` files were compared first: 331 keys, **not one
difference**. So the cause was in the RTL, and the RTL differed by exactly two
things, neither of which changes logic — the chip-select width, and the rename
of `branch`'s port to `branch_en` from 9.8.

A repeat run on unchanged RTL reproduced 101,719 exactly, so the flow is
deterministic and the difference is real and attributable. A single-variable
probe then put the two-bit chip select back and left the rename in place:

| Chip select | Port name | Cells | Area (um^2) |
|---|---|---:|---:|
| 2 bits (defect) | `branch` | 99,078 | 1,350,348 |
| 2 bits (defect) | `branch_en` | 101,806 | 1,377,738 |
| 1 bit (fixed) | `branch_en` | 101,719 | 1,382,586 |

The chip-select fix is worth **-87 cells**, which is the right sign and the right
order for deleting four dead bits. **The rename alone is worth +2,728 cells, 2.8 %,
with no logic change whatsoever.** Yosys names cells after the signals that drive
them, and the resulting order feeds ABC's technology mapping; a different order
gives a different mapping.

This matters beyond the sanitation pass. **Any ASIC area or cell-count difference
below roughly 3 % in this flow is not attributable to a design change**, in the
same way that the Quartus fitter's placement noise makes small LE differences
unattributable (9.6). The A2 comparison in the paper has to carry that caveat, or
it will read as a measured effect when it is naming.

It is the same lesson as the earlier Quartus episode, where eliminating the
revision name and the flow invocation was what isolated a 10 LE regression. Tool
output depends on things that are not the design.

---

## 8. What this record is for

Two patterns account for most of the defects above.

**Silent width mismatches.** Three separate occurrences, none of which failed
compilation, all of which produced plausible wrong numbers. The tool warned
once (`vopt-2241`) and the warning was dismissed.

**Conclusions drawn ahead of evidence.** Causes were asserted from indirect
signals — a process existing, a file count not increasing, a rule fitting four
of five cases — and were wrong each time. What resolved each one was going to
the primary source: reading the RTL, timestamping the files, instrumenting the
counter.

The control point is what caught nearly all of it. Requiring a measurement to
reproduce a known answer before any new number is accepted turned three silent
failures into immediate, obvious ones.
