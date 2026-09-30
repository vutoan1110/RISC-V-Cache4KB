# Autonomy log

Running engineering journal kept under the full-autonomy mandate of 2026-09-18.
Every decision, dead end and breakthrough goes here, with the rationale written
*before* the change, not after it. Newest entries at the bottom.

Ground rules I am holding myself to, from the Architect's Constitution:

- Optimise full PPA. Power must be measured, not assumed.
- Every design change carries the whole flow: directed TB, UVM, Embench matrix,
  full OpenLane 2 PD.
- Report Achievements and Failures separately, with hard numbers, and never
  sugar-coat a bad result.

---

## 2026-09-18 01:00 — Entry 1: state of the tree at the start of the sprint

RTL is pinned at md5 `bf24fbaee5b1bf2ff41f202e2e76b65d` (`results/rtl_state_dedup.md5`),
which is the sanitised RTL plus the `is_branch_e` deduplication.

Green at this hash:

| Gate | Result |
|---|---|
| Verilator `-Wall`, no suppressions, CACHE_CONFIG 0/1/2/3, top `de2_115_top` | 0 correctness warnings |
| Verilator, ASIC scope, 4 design dirs | 0 correctness warnings in our code |
| Directed regression | 110 PASS, 0 errors |
| 48-run Embench matrix | byte-for-byte identical to the pre-sanitation reference |
| Quartus DM, 4 seeds | 15,141 - 15,289 LE, slack +0.550 to +0.774 ns |

In flight: full OpenLane 2 flow, tag `dedup_full`, at step 12 of ~55.

Power for this RTL: **not measured yet.** The only power figure in the project is
for the pre-sanitation RTL (DM total 278.47 mW, core dynamic 111.27 mW). That is
the single biggest measurement gap and item 2 below is aimed at it.

---

## 2026-09-18 01:10 — Entry 2: the synchronous Tag RAM premise does not survive contact with the evidence

The mandate's first action item is to convert the Tag RAM from asynchronous to
synchronous read, on the stated grounds that *"forcing the synthesizer to map a
1KB Tag array into distributed standard-cell flip-flops just to maintain a
0-cycle combinational tag lookup is physically unacceptable for PPA"*.

I checked that before implementing it, because the FSM rewrite it implies is the
most expensive and most dangerous change on the list. **The causality in the
premise is backwards.** Evidence, all from the Yosys log of run `dedup_full`:

**1. Nothing in this design maps to SRAM, synchronous or not.**

```
Number of memories:               0
```

Fourteen arrays were replaced with registers, and the eighteen that survived as
memories were mapped to flip-flops too. The data RAMs are **already fully
synchronous** and were mapped like this:

```
Mapping memory ...u_icache.g_dm_baseline.u_data_ram.data_mem0:
  created 64 $dff cells and 0 static cells of width 32.
  read interface: 1 $dff and 63 $mux cells.
  write interface: 64 write mux blocks.
```

64 storage flops of width 32, a 63-mux read tree, and one output flop. A
synchronous read did **not** produce a RAM macro. It produced flops plus a mux
plus an extra register. The asynchronous tag array gets flops plus a mux, and
nothing else.

So converting the tag read to synchronous does not remove the flops and does not
remove the mux. It **adds** the output register: roughly 23 flops per cache, 46
across I and D, plus whatever FSM state the extra cycle needs.

**2. There is no SRAM macro that a tag array could use.**

The only macro available is `sky130_sram_2kbyte_1rw1r_32x512_8`: 512 words of 32
bits. An I-cache tag array is 64 words of 23 bits, which is 184 bytes. Mapping it
into a 2 KB macro would waste 91 % of the macro and still cost the extra cycle.
Wrong shape, not a near miss.

**3. The tag path is not on the critical path.**

The measured worst setup path is `datapath|instr_m[4] -> datapath|alu_result_m[28]`
at +0.774 ns — the ALU result path in Memory. The previous worst was
`instr_w[0] -> controller|alu_src_e`, decode. Neither is a cache tag lookup. The
one genuine upside of a synchronous tag read, shortening a combinational hit
path, is aimed at a path that is not currently limiting.

**Expected effect of item 1 as specified, on each PPA axis:**

| Axis | Direction | Why |
|---|---|---|
| Area | **worse** | +46 output flops, plus FSM state for the extra cycle. Nothing is removed. |
| Performance | **worse** | Every main-array hit gains a cycle. The L0/hot buffers absorb some of it, but only for hits they cover. CPI is a headline number in the paper. |
| Power | **slightly worse**, before gating | More flops toggling. Read gating (item 2) is what actually cuts power, and it is independent of this change. |
| Timing | **probably neutral** | The path it shortens is not critical. |

**Decision.** I am not implementing item 1 blind, and I am not refusing it
either. It goes last, as a measured A/B experiment, after the two changes whose
benefit is unambiguous are banked. If the measurement contradicts this analysis I
will say so plainly and keep the change. Reordered plan:

1. `PERF_COUNTERS_ENABLE` (mandate item 3) — lowest risk, and it produces the
   area breakdown that makes item 1's cost assessable in the first place.
2. Conservative FSM read gating (mandate item 2) — the real power lever, and the
   one aimed at the metric that has never been measured here.
3. Synchronous tag RAM (mandate item 1) — as an experiment with a hard A/B, not
   as an assumption.

This is the reordering the autonomy grant exists for. The rationale is written
here before any code was touched, as required.

---

## 2026-09-18 01:40 — Entry 3: the pivot is mandated, and I was wrong about its cost

The Chief Architect has overruled Entry 2 and made the synchronous cache an
absolute structural decision: realistic physical memory over the 0-cycle trick.
That is their call and it is made. Executing.

Before writing code I checked what the change actually costs, and **my Entry 2
estimate was wrong in an important way.** I wrote that "every main-array hit
gains a cycle". That is false, and here is why.

**The data RAM is already synchronous.** A main-array hit in the DM controller
already costs two cycles today: `ST_IDLE` issues the data read, `ST_HIT_RESP`
consumes it. The asynchronous tag did not buy a cycle of latency on hits — it
only decided, within `ST_IDLE`, *which state to go to next*.

So with a synchronous tag:

| Path | Today | After | Delta |
|---|---|---|---|
| L0 / hot-buffer hit | 0 cycles | 0 cycles | **none** — these are registers, not RAM |
| DM main-array hit | `ST_IDLE` + `ST_HIT_RESP` | `ST_IDLE` + `ST_LOOKUP` | **none** |
| DM miss | `ST_IDLE` -> `ST_REFILL_REQ` | `ST_IDLE` -> `ST_LOOKUP` -> `ST_REFILL_REQ` | **+1 cycle** |
| DSE core (cfg 1/2/3), any path | already has `ST_LOOKUP` | unchanged | **none** |

The DSE core already reads its tags one cycle after latching the address, in
`ST_LOOKUP`. Moving that read into a synchronous array issued from `ST_IDLE`
lands the result in exactly the same cycle. **Zero cost on three of the four
configurations.**

**Predicted CPI penalty, computed from the measured 48-run matrix** — one extra
cycle per DM miss, applied to the real miss counts:

```
Tong: mcycle=1,463,306  minstret=1,126,062  misses=7,705
CPI now       = 1.2995
CPI predicted = 1.3063
penalty       = 0.53 %
```

Per kernel the spread is wide: `tarfind` 0.03 %, `md5sum` 5.17 %. md5sum is the
outlier because it is the most D-cache-miss-heavy kernel in the suite.

0.53 % aggregate is a very different trade from what Entry 2 implied, and the
architect's instinct that the physical benefit outweighs the IPC cost is much
better supported than my pessimism was. Recording that plainly.

**A second benefit I had not considered.** Giving the DM controller a `ST_LOOKUP`
state makes its state sequence match the DSE core's. The project's own memory
records that the published DM-versus-SA2 comparison is *confounded* because DM
runs a five-state controller and the others run a ten-state one. This pivot
removes that confound. That is a scientific gain for the paper independent of
any PPA number.

**Scope decision.** The mandate also asks to resize the caches so they map onto
`sky130_sram_2kbyte_1rw1r_32x512_8` (512 words x 32 bits). The current data array
is 64 x 32 per bank, four banks, 256 words per cache. Making that fit means
either growing each cache to 8 KiB — which changes the capacity premise behind
every published cache-DSE number — or reorganising the four parallel banks into
one array addressed by {index, word}, which changes how refill and victim-swap
read whole lines. Both are real work with real consequences for the study.

I am splitting it:

- **Phase 1 (now):** synchronous tag RAM, FSM refactor, AXI/APB stability proof,
  read gating, `PERF_COUNTERS_ENABLE`. Measure CPI and full PPA.
- **Phase 2 (next):** memory organisation for macro mapping, with the capacity
  question answered by measurement rather than assumed.

Phase 1 is what the CPI prediction above covers. Phase 2 is where the SRAM macro
question actually gets decided, and it deserves its own before/after.

**Order of work in Phase 1, and why:**

1. `PERF_COUNTERS_ENABLE` first — it is the lowest-risk change and it produces
   the area split that makes every later number interpretable.
2. Synchronous tag + FSM refactor, one controller at a time, directed tests after
   each. I-cache DM first because its FSM is the smallest.
3. Read gating, once both arrays are synchronous.
4. AXI/APB stability: the interface testbenches run *before* synthesis, per the
   mandate. The risk being managed is a cycle-slip that duplicates or drops a
   handshake, which a cycle-accurate equivalence check catches but a pass/fail
   test might not.

---

## 2026-09-18 02:10 — Entry 4: the valid bits are the real constraint, not the tags

Reading both controllers before touching them turned up the thing that actually
decides whether the 0-cycle fast path can survive.

Both L0 / hot-buffer fast paths cross-check the main array's **valid bits**
combinationally, at the *live* index, in `ST_IDLE`:

```verilog
// icache_controller.v
assign request_hit = tag_rd_valid && (tag_rd_tag == request_tag);
wire fast_hit_response = (state == ST_IDLE) && request_fire && request_hit && hot_hit;

// icache_dse_core.v
wire hot_selected_valid = hot_way[live_hot_index] ? (IS_SA2 && valid_way1[live_index])
                                                  : valid_way0[live_index];
wire hot_hit = hot_valid[live_hot_index] && hot_selected_valid &&
               (hot_tag[live_hot_index] == live_block[BLOCK_WIDTH-1:3]);
```

`hot_valid` is **only ever set, never cleared** outside reset. So the hot buffer
has no invalidation of its own: its coherence comes entirely from that live read
of the main array's valid bit. Make the valid bits synchronous and the fast path
cannot be evaluated in `ST_IDLE` at all.

I considered dropping the cross-check and trusting the hot buffer alone. **That
would have been a mistake and I am recording it as a rejected option.** After a
conflict miss, a hot-buffer entry can survive while the main line it came from
has been replaced. Today that case counts as a miss and refills; trusting L0
alone would turn it into a hit. DM hit rates would improve for a reason that has
nothing to do with cache organisation, and the DM-versus-SA2 comparison — already
noted in this project as confounded — would pick up a second confound. Rejected
on scientific-integrity grounds, not on difficulty.

**The design I am implementing instead: split the array by function.**

| Array | Size per cache | Read | Why |
|---|---|---|---|
| `tag_mem` | 22 bits x 64 = 1,408 bits | **synchronous** | This is 96 % of the tag array's bits and the part a macro would ever hold. |
| `valid_bits` | 1 bit x 64 = 64 bits | stays combinational | Control state, not data. It must be clearable en masse at reset and readable in the request cycle. 64 flops. |

This satisfies the mandate's physical intent — the bulk storage becomes a
strictly synchronous array with no `assign rd_tag` anywhere — while leaving the
64 control flops where they belong. Splitting valid bits out of the tag array and
keeping them in flops is standard practice for exactly this reason.

**What this costs, per configuration:**

| Config | Fast path (L0) | Main-array hit | Miss |
|---|---|---|---|
| DM (0) | 0 cycles, unchanged | 2 cycles, unchanged | **+1 cycle** |
| DSE (1/2/3) | 0 cycles, unchanged | unchanged | **unchanged** |

The DSE core already reads its tags one cycle after latching the address, inside
`ST_LOOKUP`. Issuing that read from `ST_IDLE` into a registered output lands it in
the same cycle it is used today. Nothing moves.

So the predicted penalty stays exactly what Entry 3 computed from the measured
matrix: **0.53 % aggregate CPI on DM only, zero on the other three**. And the
hit/miss accounting is untouched, so cfg 1/2/3 must still reproduce the 48-run
matrix **byte for byte** — that is the acceptance test for "I did not break
anything", and it is a much sharper check than a pass/fail suite.

**Implementation order, revised for context locality:** the FSM analysis is
current, so the synchronous tag work goes first, then `PERF_COUNTERS_ENABLE`,
then read gating. Entry 2 put counters first for the area split; that reason is
still good but it is worth less than not re-deriving four state machines later.

---

## 2026-09-18 02:35 — Entry 5: the DM fast path has to drop one term, and that term is one the DSE core never had

Entry 4's plan hit a wall on the DM controller. Its 0-cycle path is

```verilog
wire fast_hit_response = (state == ST_IDLE) && request_fire && request_hit && hot_hit;
assign request_hit = tag_rd_valid && (tag_rd_tag == request_tag);   // needs the TAG
```

`request_hit` needs the **tag** combinationally, not just the valid bit. Entry 4
only rescued the valid bit. So one of three things has to give:

1. **Move the L0 decision to `ST_LOOKUP`.** Costs a cycle on every hot-buffer
   hit, which is the common case. That is a real IPC hit, far worse than 0.53 %.
   Rejected.
2. **Add hot-buffer invalidation** so `hot_valid` tracks residency by itself and
   no main-array read is needed. Correct, but it is new logic in all four
   controllers and it changes behaviour on cfg 1/2/3 as well, which are supposed
   to stay byte-identical. Rejected for this step; noted as a possible Phase 2
   cleanup.
3. **Drop the tag term from the DM fast path.**

I am taking (3), and the reason is that it is *convergence, not divergence*.
Compare what the two controllers require for a hot-buffer hit today:

```verilog
// icache_dse_core.v  -- valid bit only, no tag
wire hot_selected_valid = hot_way[live_hot_index] ? (IS_SA2 && valid_way1[live_index])
                                                  : valid_way0[live_index];
wire hot_hit = hot_valid[live_hot_index] && hot_selected_valid &&
               (hot_tag[live_hot_index] == live_block[BLOCK_WIDTH-1:3]);

// icache_controller.v -- valid bit AND main tag
... request_hit && hot_hit
```

The DSE core, which is the controller behind three of the four configurations,
**already** serves a hot-buffer hit without checking the main tag. The DM
controller is the odd one out. Dropping the term makes DM's fast-path condition
structurally identical to the DSE core's.

**I am not pretending this is free.** It changes DM hit/miss accounting in one
case: a hot-buffer entry whose line has since been replaced at its main index by
a different tag. Today DM calls that a miss and refills; afterwards it is a hot
hit. The data served is correct either way — this is a read-only instruction
cache and the hot entry holds the bytes actually fetched from that address — but
the *counts* move.

So DM will differ from the 48-run reference for two separate reasons, and I have
to be able to separate them:

- **+1 cycle per miss**, predicted 0.53 % aggregate (Entry 3).
- **fewer misses**, because some former conflict misses become hot hits.

The second one works in the opposite direction on CPI, so the net DM number is
not predictable from Entry 3 alone. I will report both effects separately rather
than a single net figure, and cfg 1/2/3 must still be byte-identical — that
remains the check that the DSE path was not disturbed.

---

## 2026-09-18 03:05 — Entry 6: DM instruction cache is synchronous and the suite is green

Implemented and passing. What changed:

**`icache_tag_ram.v`** — rewritten. `assign rd_tag = tag_mem[rd_index]` is gone;
the tag port is `always @(posedge clk) if(rd_en) rd_tag <= tag_mem[rd_index]`.
The valid bits are now a separate combinational port (`valid_rd_index` /
`valid_rd`) for the reason in Entry 4. The read needs no write-forwarding,
because every tag write happens in a state where `req_ready` is low and the only
read is issued from `ST_IDLE`; that is written down in the file rather than left
for the next reader to re-derive.

**`icache_controller.v`** — `ST_HIT_RESP` became `ST_LOOKUP` and now carries the
hit/miss decision. `ST_IDLE` answers hot-buffer hits and otherwise issues the tag
and data reads and latches the request. `access_event` / `hit_event` /
`miss_event` moved with the decision, so each accepted request is still counted
exactly once.

**`icache_data_ram.v`** — gained `rd_en`. The four banks now hold instead of
re-reading every cycle. This is the first piece of the read-gating mandate,
landed early because the enable signal already had to exist for the tag.

**One dead end worth recording.** Questa rejected the first attempt:

```
** Error: icache_controller.v(152): (vlog-2730) Undefined variable: 'fast_hit_response'.
```

`fast_hit_response` was declared below the event assignments that use it.
Verilator had accepted it; Questa did not. Declaration moved above first use.
Worth remembering that the lint script is not a substitute for the compiler here.

**Result: directed regression 110 PASS, 0 errors.** Same count as before the
refactor, so nothing in the suite regressed.

Now measuring the 48-run matrix. The two things I am looking for:

1. **cfg 1/2/3 byte-identical.** The DSE core has not been touched, so any
   movement there means I broke something shared.
2. **cfg 0 moves in two directions at once** — up from the extra `ST_LOOKUP`
   cycle on each miss, down from conflict misses that now hit in the hot buffer
   (Entry 5). I will report the two separately, not as a single net number.

---

## 2026-09-18 03:20 — Entry 7: measured, and two of my predictions were wrong in opposite directions

48-run matrix on the synchronous-tag I-cache:

```
cfg 1/2/3 : GIONG TUNG BYTE, 36/36      <- DSE core undisturbed
cfg 0     : mcycle 1,463,306 -> 1,463,732   (+0.029 %)
            i_miss    455 -> 455            (+0)
            CPI    1.2995 -> 1.2999
```

**The accounting risk from Entry 5 measured exactly zero.** I predicted that
dropping the main-tag term from the DM fast path would turn some conflict misses
into hot-buffer hits and move the miss counts. The miss count is **identical**,
455 before and after, on all twelve kernels. The case exists in principle; it does
not occur in this workload set. Recording that the risk was real, was checked,
and came out clean — not that it was never a risk.

**The penalty is smaller than Entry 3 predicted, because Entry 3 over-counted.**
I applied the +1-cycle-per-miss rule to *all* misses, 7,705 of them, and got
0.53 %. But this step only made the *instruction* cache synchronous, and I-cache
misses are only 455 of that total. 455 cycles on 1,463,306 is 0.031 %, which is
what showed up.

The per-kernel deltas are not exactly one cycle per miss: `fdct` gained 54 cycles
on 45 misses, `tarfind` 26 on 22. A longer instruction-side stall shifts what the
rest of the pipeline is doing around it, so the extra cycle is not always fully
hidden or fully exposed. Worth knowing when the D-cache lands, because I should
expect the same imprecision there rather than treat a mismatch as a bug.

**Revised expectation for the D-cache step.** `dcache_controller` **already has**
a `ST_LOOKUP` state and already reads its data array in `ST_IDLE` for use in
`ST_LOOKUP`:

```verilog
assign data_rd_index = (state == ST_IDLE) ? req_addr[INDEX_WIDTH+3:4] : request_index;
```

If the tag read is issued from the same place and consumed in the same state,
**the D-cache should cost zero extra cycles**, not 7,250. That would make the
whole synchronous-tag pivot cost about 0.03 % of CPI in total rather than 0.53 %.
I am not asserting that yet — it is the next thing to measure.

---

## 2026-09-18 04:10 — Entry 8: the D-cache fought back, and a test I wrote found a real latent defect

The D-cache did not go the way the I-cache did. Three failures, in order, and
each one taught something.

**Failure 1 — wrong data, 106/110.** I applied the same recipe as the I-cache:
drop the main-tag term from the fast path, keep the valid bit.

```
** Error: read addr=00000400 expected=10000100 got=10000000
** Error: T4 hit_count expected=2 actual=4
```

Wrong, and not for the reason I assumed. The D-cache has **three** load paths in
`ST_IDLE`, not two:

```verilog
if(!req_write && live_lookup_hit) begin       // needs the TAG, combinationally
    ...count the hit...
    if(hot_hit0 || hot_hit1)  state <= ST_IDLE;          // 0 cycles
    else begin main_read_response <= 1'b1;               // 1 cycle, from the RAM
               state <= ST_CPU_RESP; end
end else state <= ST_LOOKUP;                             // miss
```

Relaxing `live_lookup_hit` to the valid bit let the **second** path fire for a
line that was not actually resident, so it answered from `data_rd_line` — the
other block's data. The hot buffer was never the problem.

**Before reaching for the obvious fix I priced it.** Dropping the 0-cycle path
entirely and sending every load through `ST_LOOKUP`:

```
DM: mcycle=1,463,306  d_read=154,523  d_main_hit=204,434
  +1 cycle per hit -> +13.97 %
  +2 cycles        -> +27.94 %
```

Fourteen to twenty-eight percent. That is not a trade, that is a rewrite of the
paper's performance story. Rejected.

**The fix that works:** only the hot buffer resolves a load in the request cycle,
and the old second path folds into `ST_LOOKUP`. The hot buffer compares the whole
28-bit block address against two registers — no main tag needed to qualify it.
Cost is +1 cycle for main hits that miss the two-entry L0, not +1 or +2 for all
of them.

**Failure 2 — 108/110, accounting only.** `T4 hit_count expected=2 actual=3`.
TEST 4 walks 0x000, 0x000, 0x400, 0x400, 0x000 through one index. The fifth
access used to miss, because 0x000's main line had been replaced even though its
data was sitting in the L0 the whole time. Now the L0 answers it. **The new
behaviour is better**, and the data checks passed — but the testbench encoded the
old one, so I updated the expectation and wrote down why, in the testbench, not
just here.

**Failure 3 — and this is the one that mattered.** The mandate says to write new
tests for new logic, so I added TEST 4b for the property the design now leans on:
*the hot buffer must never hold data a store has moved past*. Load 0x000, load
0x400 to evict it from the main array, store to 0x000, read it back.

```
** Error: read addr=00000000 expected=feedface got=11111111
```

The store went through to memory and the hot copy kept the old value. Root cause:

```verilog
store_hit_latched <= lookup_hit;                     // only a MAIN-array hit
wire store_commit = store_hit_latched && ...;        // gates the hot update
```

A store that misses the main array writes through but never touches the hot
buffer. **That hole has been there all along.** It was harmless only because the
old fast path refused to use the hot buffer unless the main tag agreed — the
cross-check was masking it. Making the hot buffer authoritative exposed it.

Fixed by invalidating any hot copy of a block whose store missed the main array:

```verilog
wire store_write_done = (write_rsp_same_cycle || write_rsp_later) && !mem_wr_rsp_error;
wire store_miss_done  = !store_hit_latched && store_write_done;
```

Invalidate rather than update: the merged word on a miss is built from
`data_rd_line`, which holds the wrong line, so there is nothing correct to write.
Dropping the entry costs one refill later and is provably right.

**110 PASS, 0 errors**, with TEST 4b in the suite.

This is the best argument I have for the mandate's rule about writing tests for
new logic. The regression I inherited was green at 108/110 with a genuine data
corruption bug one store away. The test that found it did not exist until the
architecture change made the property load-bearing.

---

## 2026-09-18 04:45 — Entry 9: +12.045 % was my bug, not the architecture's price

First D-cache measurement came back at **+12.045 %** CPI (1.2995 -> 1.4560),
right next to the 13.97 % I had already called unacceptable. cfg 1/2/3 stayed
byte-identical, so the damage was entirely in DM and entirely mine. Two causes:

**1. I did not apply my own I-cache lesson.** In `icache_controller` I had made
`ST_LOOKUP` answer directly. In `dcache_controller` I left the read hit latching
`rsp_data_reg` and stepping on to `ST_CPU_RESP` — a whole cycle spent forwarding
a registered copy of a line that `ST_LOOKUP` already had in hand, on the most
common main-array path in the design.

**2. I killed the L0 without noticing.** The hot-buffer fill lived in
`ST_CPU_RESP` behind `if(main_read_response)`, and `main_read_response` was only
ever set by the `ST_IDLE` path I had just deleted. So the hot buffer was being
filled by stores and nothing else. Every read loop ran off the main array.

**The suite was 110/110 green with a dead L0.** Nothing in the directed tests
checks that the hot buffer is actually being *used* — only that answers are
correct. A structure worth 12 % of total cycles can be disabled without a single
test noticing. That is a coverage hole and it is worth more attention than the
bug was; noting it here for the test-writing pass.

**Fixes:** read hits answer out of `ST_LOOKUP`; the L0 fill moved to a single
site outside the `case`, driven by `lookup_read_hit`, rather than duplicating the
four-way replacement chain (the `is_branch_e` lesson — do not write the same
logic twice and leave `opt_merge` to find it); `main_read_response` and the dead
fill block it guarded are gone.

**Re-measured:**

```
cfg 1/2/3   : byte-identical, 36/36
DM  mcycle  : 1,463,306 -> 1,463,620   (+0.021 %)
    CPI     : 1.2995 -> 1.2998
```

`matmult` came out **102 cycles faster**, the only kernel that improved: the
single-site L0 fill catches a case the old `main_read_response` path missed.

So the full synchronous-tag conversion of both caches costs **0.021 % of CPI**.
Not the 0.53 % I predicted, not the 12 % my first attempt produced. The
architect's judgement that the physical benefit would outweigh the IPC cost looks
right, and the IPC cost is close enough to zero that the trade will be decided
entirely by the PPA numbers, which I still do not have.

Next: the DSE core, where the tags are internal `reg` arrays read
combinationally in `ST_LOOKUP`. The read moves to `ST_IDLE` on the live index and
lands in a register for the same cycle it is used today, so cfg 1/2/3 must stay
byte-identical. That is the acceptance test.

---

## 2026-09-18 05:10 — Entry 10: DSE cores converted; a declaration-order trap that bit three times

Both DSE cores now read their tags synchronously. The change is small because the
structure was already right: `tag_wayN[request_index]` was read combinationally
inside `ST_LOOKUP`, one cycle after `ST_IDLE` latched the address, so issuing the
read from `ST_IDLE` on the live index and registering it lands the tag in exactly
the cycle it was already being used.

Four read sites per core: `main_hit0`, `main_hit1`, and two `old_main_block`
captures on the victim-swap and evict paths. All four are in `ST_LOOKUP`, so all
four take the registered copy. The valid bits stay combinational.

**The trap, three times in one night.** Questa rejects a use before its
declaration; Verilator does not. This cost three compile cycles:

1. `fast_hit_response` in `icache_controller` (entry 6)
2. `lookup_valid_q` in `dcache_controller` (entry 8)
3. `tag_rd0_q` / `tag_rd1_q` here — and this one was circular. The declaration
   has to precede `main_hit0`, but the `always` block that drives it needs
   `req_fire` and `live_index`, which are declared further down. Moving the whole
   thing down broke `main_hit0`; moving it up broke the always block.

Resolved by splitting: the two `reg` declarations go up with the tag arrays, the
read logic goes down after `req_fire`. Obvious in hindsight, and the rule to
carry forward is simple — **when adding a registered copy of something, declare
the register next to what it copies, not next to the logic that fills it.**

`lint_rtl.sh` will not catch any of these. Verilator accepts all three. The only
gate that finds them is a Questa compile, so a lint pass is not evidence that RTL
compiles.

**110 PASS** with all four caches synchronous. Now measuring; the acceptance test
is unchanged — cfg 1/2/3 byte-identical, because nothing about their cycle
structure moved.

---

## 2026-09-18 05:40 — Entry 11: full synchronous-cache result, and PERF_COUNTERS_ENABLE

**All four caches are synchronous. Measured across the whole matrix:**

```
DM      1,463,306 -> 1,463,620   +0.021 %   CPI 1.2995 -> 1.2998   (changed)
SA2     1,594,658 -> 1,594,658   +0.000 %   CPI 1.4161 -> 1.4161   byte-identical
DM_VC4  1,603,205 -> 1,603,205   +0.000 %   CPI 1.4237 -> 1.4237   byte-identical
DM_DSE  1,600,088 -> 1,600,088   +0.000 %   CPI 1.4210 -> 1.4210   byte-identical
```

Three of the four configurations reproduce every counter of all twelve kernels
exactly. That is the strongest statement available that the DSE conversion moved
nothing: not a cycle, not a hit, not a miss, not an AXI transaction. The 0.021 %
on DM is the entire price of the architectural pivot on the instruction side.

**`PERF_COUNTERS_ENABLE` implemented.** Parameter threaded from `de2_115_top` and
`soc_top` down through `performance_observability` into `perf_counters` and
`apb_performance_monitor`.

I chose the least invasive mechanism deliberately. The counters are
`output reg [31:0]`, so switching them off by wrapping the blocks in a `generate`
would mean converting 75 output ports to wires with shadow registers — a large
mechanical change across two files, with plenty of room for a transcription
error. Instead the counting condition itself carries the parameter:

```verilog
else if(!counter_freeze && (PERF_COUNTERS_ENABLE != 0)) begin
```

At 0 every counter is held at its reset value forever, synthesis constant-folds
it and the flops disappear. At 1 the expression is identical to what was there
before, which is why the directed suite is **110 PASS** and unchanged. Same
treatment for the snapshot capture in the APB monitor.

The parameter defaults to 1 everywhere, so no existing flow, project file or
published number changes unless something overrides it on purpose.

Lint is clean; the matrix is re-running to confirm the default is behaviourally
inert before I trust it.

**Next, in order:** Quartus DM at `PERF_COUNTERS_ENABLE` 1 and 0 for the area
split and the first power measurement of this RTL; then the AXI/APB stability
layer (UVM) before synthesis as the mandate requires; then the full OpenLane
flow.

---

## 2026-09-18 06:15 — Entry 12: verification layer complete, moving to silicon numbers

`PERF_COUNTERS_ENABLE` at its default reproduces the 48-run matrix **byte for
byte, 48/48**. The parameter is inert until something sets it to 0, which is what
I wanted before trusting it in a flow.

RTL pinned at `c9c969243b25b15e144bc1698b40784c` (`results/rtl_state_synccache.md5`).

**Verification layer, all green on the fully synchronous design:**

| Gate | Result |
|---|---|
| Verilator `-Wall`, no suppressions, cfg 0/1/2/3 | 0 correctness warnings |
| Directed regression | 110 PASS, 0 errors |
| 48-run Embench matrix | DM +0.021 %, other three byte-identical |
| UVM, 6 tests, 3 seeds | 8/8 PASS |
| UVM AXI at 8 / 16 / 32 / 64 B lines | 8/8 PASS |

That last row is the mandate's AXI/APB stability requirement, and it is the one I
was most worried about. A cache that now takes an extra state on the miss path
has more opportunity to drop or duplicate a handshake, and the byte-identical
result on three configurations plus a clean AXI stress at four line sizes is
about as direct a statement as this environment can make that nothing slipped.

**Now the part that has never been measured on this RTL: power.**

`run_fpga_points.py` gained a sixth field and a new point. `dm_nopc` is the same
cache, the same core and the same everything as `dm`, with
`PERF_COUNTERS_ENABLE=0`. The difference between the two fits is exactly what the
instrumentation costs — in LEs, in registers, and in milliwatts. That number has
been quoted nowhere in this project and it belongs in the paper, because roughly
29 % of the design's registers are measurement apparatus and the reader currently
has no way to know that.

Both fits are running. After them: Quartus Power Analyzer on each, then the full
OpenLane flow for post-route area, power and timing.

---

## 2026-09-18 06:50 — Entry 13: area and power are real gains; timing is a real problem

First FPGA numbers on the fully synchronous design, seed 2, against the
pre-pivot baseline.

| | Baseline (async tag) | Synchronous | Delta |
|---|---:|---:|---:|
| Logic elements | 15,192 | **14,596** | **-596 (-3.9 %)** |
| Registers | 8,356 | **8,015** | **-341** |
| Memory bits | 83,328 | **84,736** | **+1,408** |
| Setup slack | +0.774 ns | **0.000 ns** | **-0.774** |
| Fmax | 52.01 MHz | **50.00 MHz** | **-2.01** |
| Total power | not measured | **272.25 mW** | — |
| Core dynamic | not measured | **105.08 mW** | — |

**The +1,408 memory bits are the point of the whole exercise.** That is exactly
22 bits x 64 lines — one tag array, moved out of logic elements and into a block
RAM. The architect's structural instinct was right: a synchronous tag array does
get absorbed into real memory on the FPGA, and it takes 596 LEs and 341 registers
with it. My Entry 2 analysis said this could not happen. It was reasoning from
the ASIC flow, where there is no macro of the right shape, and I generalised it
to the FPGA where M9K blocks are freely shaped. That was wrong and the fit says so.

**The timing is a real problem and I am not going to dress it up.** Slack went
from +0.774 ns to exactly 0.000. The `dm_nopc` variant is worse still at
**-0.14 ns, which fails 50 MHz outright.**

The critical path is *not* in the cache:

```
0.000 : datapath|instr_w[5] -> datapath|alu_result_m[..]
```

Same ALU-result path family that was critical before at +0.774 ns. So the cache
did not become slower; the placement around it changed. Moving a tag array into
an M9K pins it to a fixed block location and drags the datapath's placement with
it.

**What I do not yet know is whether this is a regression or a bad draw.** The
four-seed spread on the old RTL was +0.550 to +0.774 ns. One seed at 0.000 is
outside that range, but one seed is one seed, and this project has already been
burned twice by reading a single fit as a result. Four-seed sweep running on the
new RTL now. Until it lands I am not calling this a timing regression, and I am
not calling it noise either.

**PERF_COUNTERS_ENABLE, first measurement of what the instrumentation costs:**

| | dm (counters on) | dm_nopc (counters off) | Instrumentation |
|---|---:|---:|---:|
| Logic elements | 14,596 | 11,894 | **2,702 (18.5 %)** |
| Registers | 8,015 | 5,977 | **2,038 (25.4 %)** |
| Total power | 272.25 mW | 261.19 mW | **11.06 mW (4.1 %)** |
| Core dynamic | 105.08 mW | 94.20 mW | **10.88 mW (10.4 %)** |

A quarter of the design's registers and a tenth of its core dynamic power are
measurement apparatus. That number has never appeared in this project and the
paper cannot honestly quote an area figure without it.

**Caveats I am not going to leave out.** The power figures are vectorless
estimates — a default toggle-rate model, not a measurement. They are comparable
to each other and they are not silicon power. And `dm_nopc` fails timing, so its
numbers are from a fit that does not close; the area and power split above is
still the right comparison, but that variant is not a shippable configuration as
it stands.

One Quartus attempt failed with rc=2 and was retried automatically. That is the
~8 % random crash rate this project has already characterised, not a new problem.

---

## 2026-09-18 07:30 — Entry 14: four seeds settle the timing question

| seed | async LE | async slack | sync LE | sync slack | delta LE | delta slack |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 15,289 | +0.570 | **14,638** | **+0.924** | -651 | **+0.354** |
| 2 | 15,192 | +0.774 | **14,596** | **0.000** | -596 | **-0.774** |
| 3 | 15,141 | +0.656 | **14,600** | **+0.680** | -541 | +0.024 |
| 4 | 15,226 | +0.550 | **14,672** | **+0.491** | -554 | -0.059 |

**Area: unambiguous.** 15,141-15,289 before, 14,596-14,672 after. The two ranges
**do not overlap at any seed**, mean -586 LE. This is not placement noise; it is
the tag array leaving logic elements for a block RAM, and it holds on every draw.

**Timing: seed 2 is an outlier, not a regression.** Mean slack moves -0.114 ns,
which is inside anybody's noise band. But the *spread* goes from 0.224 ns to
0.924 ns, and the best seed on the new RTL (+0.924) beats the best seed on the
old one (+0.774). Three of four seeds pass comfortably. Seed 2 alone lands at
exactly 0.000.

So my Entry 13 worry was half right. There is no systematic timing loss. There is
a large increase in placement variance, which is what pinning a tag array to a
fixed M9K location does to the datapath around it — and seed 2 drew badly.

**Consequence for the flow: seed 2 has to be re-pinned.** The project pins seed 2
per revision deliberately. On this RTL that choice lands on the single worst draw
of four and leaves zero margin. Seed 1 gives **14,638 LE at +0.924 ns / 52.42 MHz**
— better than the old baseline on *both* axes, and better than any old seed on
timing.

Re-pinning a placement seed after seeing the results is exactly the kind of thing
that can shade into cherry-picking, so the rule I am holding to: **the paper
quotes the four-seed range, not the pinned seed's number**, and says which seed
is pinned and why. Choosing a seed for margin is normal engineering; quoting only
the best seed as if it were the design's characteristic is not.

**Two of three fits in this sweep failed on attempt 1 with rc=2** and succeeded on
retry. The project has this characterised at ~8 %; two out of three is well above
that and worth watching, but the retries were clean and the results are
self-consistent across seeds, so I am not treating it as a new failure mode yet.

**Standing summary of the pivot on FPGA, four-seed basis:**

- Area: **-586 LE (-3.9 %)**, ranges non-overlapping
- Registers: **-341**
- Memory bits: **+1,408** (one tag array into block RAM — the point of the change)
- Timing: mean **-0.114 ns**, spread **0.224 -> 0.924 ns**, best seed **better**
- CPI: **+0.021 %** on DM, **0.000 %** on the other three
- Power: 272.25 mW total / 105.08 mW core dynamic (first measurement on this RTL)

Next and last: the full OpenLane flow for post-route area, power and timing.

---

## 2026-09-18 08:15 — Entry 15: on ASIC the pivot goes the other way, and the design stopped routing

Two findings, and the first explains the second.

**The synchronous cache makes the ASIC design bigger, not smaller.**

| | cells | area (um^2) | opt_merge removed |
|---|---:|---:|---:|
| `dedup_full` (async tag) | 99,132 | 1,354,452 | 21,238 |
| `sync_full` (sync tag) | **102,041** | **1,386,981** | 20,168 |
| delta | **+2,909 (+2.9 %)** | **+32,529 (+2.4 %)** | **-1,070** |

This is the opposite sign to the FPGA result (-586 LE), and both are correct.
On the FPGA an M9K is freely shaped, so a 64 x 22 tag array drops straight into
one and takes 596 logic elements with it. On this PDK the only macro is
512 x 32; a tag array cannot use it, so the tags stay as flip-flops **and gain
the output register the synchronous read needs**. Entry 2's analysis was right
about ASIC and wrong about FPGA, and I should have separated the two targets
instead of generalising from one.

**How much of +2,909 is real?** `opt_merge` found 1,070 fewer merges, and this
project has already measured that a pure rename moves that figure by ~2,900
(entries in CHANGELOG_AND_ISSUES.md 9.10). So roughly **1,070 cells of the
increase is mapping-order noise and ~1,839 is real added logic** — the tag output
registers, the extra FSM state, the read-enable terms. I am not quoting +2,909 as
the architectural cost; the honest figure is about **+1.8 %** with a ~1.1 % noise
band around it.

**And the design no longer routes.**

```
[GRT-0118] Routing congestion too high.
STOP `sync_full` rc=2 last=`37-openroad-globalrouting`
```

This is a genuine physical failure, not the VS Code crash that killed the shell —
the flow reached step 37 of ~55 and OpenLane stopped it. The same design routed
before: `relaxed_30ns` reached step 55 on the pre-pivot RTL.

**Diagnosis.** The die is 1800 x 2900, so 102k cells at ~13.6 um^2 each occupy
about 1.39 mm^2 of a 5.1 mm^2 core — roughly 27 % utilisation. Global density is
not the problem; the congestion is local. `PL_TARGET_DENSITY_PCT` is 48, which
tells the placer to pack tightly even though there is room to spread.

**What I am going to do, and what I am not.** `GRT_ALLOW_CONGESTION=true` would
push past this, and it would be dishonest — it forces global routing to declare
success and leaves detailed routing to fail later or produce a result nobody
should quote. The right response to a congestion stop is to give the placer room:
lower `PL_TARGET_DENSITY_PCT` so the cells spread into the space that is already
there. That is a placement setting, not a change to the design, and the die area
stays fixed so the area comparison remains valid.

Trying 40 first. If that does not clear it I will step down further before
touching the floorplan, and if the floorplan has to grow I will say so explicitly,
because a die-area change makes the before/after area numbers non-comparable and
that has to be stated rather than buried.

---

## 2026-09-18 09:00 — Entry 16: the architect is right about OpenRAM, and there is already a working macro on this machine

**Correcting myself first.** Entry 2 said "there is no SRAM macro that a tag array
could use" and Entry 15 repeated it. That was a statement about the *pre-compiled
set shipped with this OpenLane template*, and I wrote it as if it were a
statement about the PDK. Sky130 uses OpenRAM as its memory compiler and can
generate whatever shape is asked for. The architect's correction is right and my
phrasing was sloppy in a way that closed off a real option.

**And OpenRAM is already installed here, with one macro that actually built.**

```
~/tools/openram_out/
  test_noperim/            18 MB  <- .gds, .lef, .lib all present
  cacheA_64x128/           8 KB   <- log only, no views
  cacheA_128x64/           8 KB   <- log only
  cacheA_128x64b/          8 KB   <- log only
  axiB_32x1024/            8 KB   <- log only
  axiB_32x2048/            8 KB   <- log only
  axiram_2048x32/          8 KB   <- log only
```

Six cache-shaped attempts produced nothing but a log. One succeeded:
**`test_sram_1rw1r_32x256_noperim`** — 32 bits x 256 words, 1 KB, with GDS, LEF
and LIB. Its config file carries notes from the session that produced it:

```python
perimeter_pins = False   # escape routing fails without this:
                         # ERROR signal_escape_router.py:70 Couldn't route dout1[1] m3 -> m4
check_lvsdrc  = False    # flow validation only; turn back on for a real run
# 1rw1r must NOT set num_spare_rows/cols -- it makes the row count odd (257)
# and violates "sky130 requires rows to be even"
```

So the compiler works, the failure mode of the six dead runs is known, and the
fix is recorded.

**The shape I need is the shape I already have.** The data array is four banks,
bank *n* holding word *n* of every line, each bank `LINE_COUNT` words of 32 bits.
So:

| LINE_COUNT | bank shape | cache size | macro |
|---:|---|---:|---|
| 64 (today) | 64 x 32 | 1 KB | none fits |
| 128 | 128 x 32 | 2 KB | needs a new OpenRAM run |
| **256** | **256 x 32** | **4 KB** | **`test_sram_1rw1r_32x256_noperim`, already built** |
| 512 | 512 x 32 | 8 KB | `sky130_sram_2kbyte_1rw1r_32x512_8`, pre-compiled |

**Decision: scale to LINE_COUNT=256, a 4 KB cache.** It clears the architect's
2 KB threshold, and each of the four data banks becomes an exact 1:1 fit for a
macro that exists on disk today. No new OpenRAM generation is on the critical
path, and — this matters — **the four-bank structure is preserved, so a full
128-bit line still reads in one cycle and no FSM changes at all.** The
alternative, one wide 512 x 32 array addressed by {index, word}, would force the
hot-buffer fill to take four cycles and would reopen the CPI question I just
closed at +0.021 %.

**What I am watching for, stated before I start:**

1. `LINE_COUNT=256` moves `INDEX_WIDTH` 6 -> 8 and `TAG_WIDTH` 22 -> 20. The
   hot-buffer slices in `icache_controller` (`[27:3]`, `[24:0]`) are functions of
   the *line size*, not the line count, so they should be unaffected — but this
   project has already been bitten once by exactly that kind of hardcoded slice
   (`request_block[27:3]`, CHANGELOG 9.2), so I will check rather than assume.
2. Cache capacity is a published parameter of the whole DSE study. Every cycle
   count in the matrix will move, and it *should*. The acceptance test is no
   longer "byte-identical"; it is "hit rates improve in the direction a bigger
   cache predicts, and nothing errors".
3. `check_lvsdrc = False` on the existing macro. Any PPA number from a flow using
   it is a **research estimate, not a signed-off macro**, and it will be labelled
   that way in the report.
4. Congestion is already failing at 1 KB (Entry 15). Eight macros of real SRAM
   will change the floorplan problem completely — possibly for the better, since
   sixteen thousand flip-flops leave the standard-cell area.

---

## 2026-09-18 09:30 — Entry 17: 4 KB matrix lands; status check

The 48-run matrix at `LINE_COUNT=256` completed before the session dropped.
48/48 rows, no failures.

| config | mcycle 1 KB | mcycle 4 KB | delta | misses 1 KB | misses 4 KB | CPI |
|---|---:|---:|---:|---:|---:|---|
| DM | 1,463,620 | 1,449,098 | **-0.99 %** | 7,701 | 6,842 (**-11.2 %**) | 1.2998 -> 1.2869 |
| SA2 | 1,594,658 | 1,579,778 | **-0.93 %** | 6,785 | 5,850 (**-13.8 %**) | 1.4161 -> 1.4029 |
| DM_VC4 | 1,603,205 | 1,589,606 | **-0.85 %** | 7,070 | 6,842 (**-3.2 %**) | 1.4237 -> 1.4117 |
| DM_DSE | 1,600,088 | 1,586,266 | **-0.86 %** | 7,705 | 6,842 (**-11.2 %**) | 1.4210 -> 1.4087 |

Acceptance test from Entry 16 was "hit rates improve in the direction a bigger
cache predicts, and nothing errors". Both hold. Misses drop 3-14 %, cycles drop
about 0.9 % everywhere, and CPI improves on all four configurations.

`DM_VC4` improves least on misses (-3.2 %) and that is the expected shape: its
victim buffer was already absorbing conflict misses that capacity now removes, so
the two mechanisms overlap. Worth a sentence in the paper — it is a real DSE
observation, not noise.

**Important scoping note: no RTL changed for this measurement.** `LINE_COUNT` is
already a parameter; the 4 KB matrix is the same RTL elaborated with
`-gICACHE_LINE_COUNT=256 -gDCACHE_LINE_COUNT=256`. RTL hash is still
`c9c969243b25b15e144bc1698b40784c`. So this result costs nothing in risk and the
1 KB numbers remain valid as their own DSE point.

**Where the sprint actually stands.** Two sessions have been cut short by editor
crashes mid-flow, and both times the casualty was the OpenLane run:

- `sync_full` — died at step 37 on a **real** failure, `GRT-0118 routing
  congestion too high`
- `sync_full_d40` — the density-40 retry, killed by the crash at step 37 with an
  empty error log; inconclusive, not a second congestion failure

So the congestion question from Entry 15 is **still open**, and there are still
**no post-route numbers for anything**. That is the one deliverable the architect
is waiting on and I have not produced it.

**Order from here:**

1. Re-run the density-40 retry to settle whether congestion clears. This has to
   finish uninterrupted before anything else is worth starting.
2. Directed regression and UVM at `LINE_COUNT=256` — the 110-test suite runs at
   the 64-line default, so the 4 KB configuration currently has benchmark-level
   evidence only and no unit-level evidence.
3. OpenRAM macro integration for the data banks, which is the point of the 4 KB
   scaling: at 256 lines each bank is exactly `test_sram_1rw1r_32x256_noperim`.
4. Full flow on the macro-backed design; post-route area, power, timing.

Item 2 is a gap I am flagging rather than quietly carrying: a 48-run benchmark
pass is weaker evidence than a directed suite, and the project has already been
burned once by relying on firmware self-checks where a unit test belonged.

---

## 2026-09-18 10:00 — Entry 18: the tree moved out of the repository

At the architect's instruction the whole sandbox moved from
`E:\Projects\RISCV-AHB-APB-UART\research` to **`E:\Projects\RISCV-research`**, so
the published repository is untouched and `git status` there shows nothing but
`danh_gia.txt`.

**What the scan found, before moving anything.** Across every `.sh`, `.py`,
`.json`, `.do`, `.qsf`, `.qpf`, `.v`, `.sv`, `.tcl` and `.sdc` in the tree,
**exactly one file held an absolute path**:

```
asic/run_pd.sh:14   ROOT=/mnt/e/Projects/RISCV-AHB-APB-UART
```

Everything else was already location-independent — the Python runners use
`Path(__file__).resolve().parents[1]`, the OpenLane configs use `dir::../../hdl`,
the Quartus project files use paths relative to the revision. The other grep hits
were artifacts, not sources: Quartus `db/*.qmsg` message caches, the Questa
`work/_info` library header, and a *comment* in the Embench kernels that happens
to contain the project name.

`run_pd.sh` is now derived from its own location rather than patched to the new
absolute path, so the tree can be moved again without editing anything.

**One obstruction worth recording.** `mv` from Git Bash refused with
`Device or resource busy` — no process held the directory (checked `/proc/*/cwd`
and the Windows task list), so it was the editor's file watcher on the workspace.
A Win32 `Move-Item` renamed it instantly. Same volume, so all 17 GB moved as a
rename, not a copy.

**Verified after the move, not assumed:**

| Check | Result |
|---|---|
| Verilator lint, cfg 0/1/2/3 | 0 correctness warnings |
| ASIC-scope lint, `soc_dm_control` | 0 correctness warnings |
| Directed regression | **110 PASS**, 0 errors |
| `run_pd.sh` path resolution | reaches OpenLane, no `no config.json` |
| Quartus runner | `ROOT` resolves, templates and HDL found |
| RTL hash | `c9c969243b25b15e144bc1698b40784c`, unchanged |

The RTL hash matching before and after is the important one: the move copied
nothing and changed nothing.

---

## 2026-09-18 10:05 — Entry 19: capacity gap closed in the directed suite

Entry 17 flagged that the 4 KB configuration had benchmark-level evidence only:
the 48-run matrix measured it, but the 110-test directed suite ran entirely at
the 64-line default. A firmware self-check is weaker evidence than a directed
test, and this project has already paid for that gap once — `CACHE_CONFIG=3` was
the basis of a central claim in the paper while having no unit test at all.

Added a capacity sweep to `run_full_regression.do`: `LINE_COUNT` 128 and 256 across
all four configurations, eight new points, alongside the existing line-size sweep
that holds capacity fixed. The two sweeps are orthogonal — one varies mapping at
constant capacity, the other varies capacity at constant mapping.

**126 PASS, 0 errors** (was 110). Every new point passed first time, which is the
uninteresting outcome and the right one: `LINE_COUNT` was already a parameter
carried properly through the tag width, index width and RAM depths, so the only
thing at risk was a hardcoded slice, and Entry 16 had already checked those.

The 4 KB design now has evidence at both levels.

**OpenLane `sync_d40` is running** — the density-40 retry that two editor crashes
have now killed. It is at step 6 of ~55. This is the third attempt at getting a
post-route number and it remains the one thing the architect is waiting on.

---

## 2026-09-18 10:20 — Entry 20: the congestion is the floorplan, not the density knob

`sync_d40` finished and failed the same way as `sync_full`: **`GRT-0118` at step
37**, with `PL_TARGET_DENSITY_PCT` at 40 instead of 48. Two runs, two densities,
same failure at the same step. The density knob was the wrong lever and I can
stop turning it.

So I went looking for *where* the congestion is instead of guessing, and the
floorplan answers it immediately:

```
macro 683.1 x 416.54 um, four of them, all at x=150, y = 150 / 650 / 1150 / 1650
=> one blockage 683 wide x 1917 tall, down the left of a 1776 x 2876 core
```

| | |
|---|---:|
| Core | 1776 x 2876 um = 5.11 mm^2 |
| Strip left for standard cells | **955 um wide** |
| Cell area needed (102k cells) | 1.39 mm^2 |
| Utilisation **inside that strip** | **51 %** |
| Utilisation of the chip as a whole | 27 % |

That is the whole story. The chip is a quarter full and the cells are jammed into
a third of it, because the macros were stacked in one column. Global routing was
being asked to get everything through a 955 um channel.

**Fix: four corners instead of one column.** Two columns at x=150 and x=1000, two
rows at y=150 and y=2300, all inside the core bounds.

```
free area becomes one contiguous 3.97 mm^2 region  =>  35 % utilisation
```

Die area is **unchanged**, so the before/after area comparison stays valid — this
is a placement change, not a floorplan resize. I said in Entry 15 that if the die
had to grow I would say so explicitly; it does not, and I am glad, because
growing it would have made every ASIC area number in this sprint incomparable
with the last.

The old file is kept as `macro_placement.cfg.column` so the two floorplans can be
compared rather than one silently replacing the other.

**Why this got worse now.** `fixed_dm_v2` on the pre-pivot RTL reached step 47,
so global routing used to pass with this same column placement. The synchronous
cache added ~2.9 % cells on ASIC (Entry 15), and that was enough to push a strip
already at ~50 % over what the router could handle. The floorplan was marginal
before the change and the change exposed it.

---

## 2026-09-18 10:40 — Entry 21: Phase 2's premise is already satisfied; here is where the LEs actually are

The directive says the FPGA LE bloat "is caused by Quartus synthesizing
asynchronous memory into standard registers", and asks me to apply synchronous
inference so both Data and Tag arrays land in M9K. **That already happened**, as a
side effect of the synchronous-cache pivot, and the fit report proves it.

`mem_bits` went 81,920 -> 84,736. The difference is 2,816, which is exactly
2 x 22 x 64 — **both** tag arrays, not one. (I wrote "one tag array" in Entry 13;
that was wrong and this corrects it.) The 81,920 baseline was already
IMEM+DMEM (65,536) plus both cache data arrays (2 x 8,192), so the data arrays
were in M9K all along.

**Hierarchical breakdown, `point_dm.fit.rpt`, 1 KB DM, synchronous RTL:**

| Block | LC | Reg | M9K | What it is |
|---|---:|---:|---:|---|
| datapath, minus alu/bht/regfile | ~3,131 | ~896 | 0 | the five-stage pipeline itself |
| `performance_observability` | 2,318 | 2,047 | 0 | instrumentation |
| `icache_controller` | 1,822 | 1,432 | 0 | **L0 hot buffer, 8 x 128 b = 1,024 flops** |
| `regfile` | 1,446 | 1,024 | 0 | **32 x 32 bit, in logic elements** |
| `dcache_controller` | 1,287 | 570 | 0 | L0 hot buffer, 2 x 128 b = 256 flops |
| `bht_2bit` | 962 | 512 | 0 | 256 entries x 2 bits |
| `alu` | 731 | 0 | 0 | Zmmul |
| `uart_apb` | 623 | 437 | 0 | |
| `icache_tag_ram` | 218 | 112 | **1** | valid bits + output register |
| `dcache_tag_ram` | 196 | 112 | **1** | same |
| `axi_ram_32` | 144 | 95 | **8** | IMEM + DMEM |
| **`dcache_data_ram`** | **6** | **0** | **4** | **already M9K** |
| **`icache_data_ram`** | **4** | **0** | **4** | **already M9K** |
| total | 14,596 | 8,015 | 18 | |

**The two cache data arrays cost 10 logic cells between them.** There is no
memory-inference bloat left to fix. The remaining LEs are in four places, none of
them a memory array Quartus failed to infer:

1. **`icache_controller` at 1,822 LC.** The L0 hot buffer is **eight entries of a
   full 128-bit line** — 1,024 flip-flops for 128 bytes of storage. It cannot go
   into an M9K because the fast path reads it combinationally in the request
   cycle (Entry 4). The D-cache does the same job with **two** entries and 256
   flops. Eight versus two is not a considered choice anywhere in the design; it
   is the single largest actionable LE item on the FPGA.
2. **`regfile` at 1,446 LC / 1,024 flops.** A 32 x 32 register file with two
   asynchronous read ports. Quartus can put this in MLABs if it is written as
   dual-port LUT RAM, which is the standard FPGA idiom and would free on the
   order of a thousand LEs.
3. **`performance_observability` at 2,318 LC.** Already isolated behind
   `PERF_COUNTERS_ENABLE` and measured at 2,702 LE / 2,038 regs.
4. **`bht_2bit` at 962 LC** for 512 bits of state, for the same reason as the L0:
   combinational read in the fetch cycle.

So Phase 2's remaining work is real, but it is not the work the directive
describes. Writing it down before acting, per the log's rules:

- The memory-inference fix is **done and measured**; I will report the M9K counts
  rather than implement it again.
- The genuine FPGA area lever is the **8-entry I-cache L0**, and it trades
  directly against CPI — the hot buffer is what makes a main-array hit free.
  Shrinking it is a DSE point that has to be measured on both axes, not assumed,
  and I will run it as an A/B rather than just cutting it.
- The **regfile in MLAB** is the second lever and is CPI-neutral if the read
  ports stay asynchronous.

**Phase 1 status:** `sync_corners` is running at step 30 of ~55 on the unshrunk
die, to establish that the four-corner placement routes at all before I start
shrinking. Shrinking and re-placing at the same time would leave me unable to
tell which change fixed or broke routing — the same single-variable discipline
that settled the naming question in CHANGELOG 9.10.

---

## 2026-09-18 10:55 — Entry 22: the four-corner floorplan routes; a new blocker at step 38

**Global routing passed.** `sync_corners` step 37 produced a "Final congestion
report" with **zero `GRT-0118`**, where `sync_full` (density 48) and `sync_d40`
(density 40) both failed there. The diagnosis in Entry 20 was right: it was the
single-column macro stack squeezing every standard cell into a 955 um strip, not
the placer's density target.

That is the first time this design has routed since the synchronous cache landed.

**New failure, step 38, `OpenROAD.CheckAntennas`:**

```
Signal 11 received
...
ant::AntennaChecker::checkAntennas(odb::dbNet*, int, bool)
__kmpc_fork_call in libomp.so
```

A segfault inside OpenROAD's antenna checker, in an OpenMP region. `run_pd.sh`
already pins `OMP_NUM_THREADS=1` for exactly this family of crash — its header
records a previous `SIGSEGV in AntennaChecker::calculateAreas` — so either the
pin is not reaching this step or this is a genuine crash rather than a race.

**Decision: skip `OpenROAD.CheckAntennas` and keep everything else.** OpenLane
supports `--skip <StepID>`. The antenna check is a *manufacturability* rule check
— it reports whether long metal segments could damage gates during fabrication.
It computes no area, no power and no timing. Skipping it does not touch any
number this sprint is trying to produce.

I am **not** disabling `RUN_ANTENNA_REPAIR`. Repair inserts diodes, which adds
cells and changes the placed area; turning it off would quietly make the area
number better than the design really is. The check is free to skip; the repair is
not.

This will be stated in the final report: the post-route PPA comes from a flow
with the antenna *check* skipped because of a tool segfault, with repair still
enabled. Anyone reading the area figure should know the design has not been
antenna-signed-off.

---

## 2026-09-18 11:15 — Entry 23: the antenna segfault is a missing LEF property, not a design problem

The architect rejected skipping `OpenROAD.CheckAntennas` and required a clean
sign-off. That is the right call for a paper asserting physical viability, and it
forced me to find the actual cause instead of routing around it. `sync_corners2`
was stopped.

**Root cause, and the flow had already said it out loud:**

```
[Odb.CheckMacroAntennaProperties] Cell 'sky130_sram_2kbyte_1rw1r_32x512_8'
has (59) input pin(s) without antenna gate information.
```

I checked the macro LEF:

```
grep -c "ANTENNAGATEAREA|ANTENNADIFFAREA|ANTENNAPARTIALMETALAREA"  ->  0
```

**Zero antenna properties on the entire macro.** The antenna ratio is metal area
divided by gate area; with no gate area on a pin there is nothing to divide by,
and `ant::AntennaChecker::checkAntennas` segfaults rather than erroring cleanly.
The design is not at fault and no amount of die area or density would have fixed
it — which is worth knowing before spending hours on the other two workarounds.

**Fix: supply the properties from the PDK's own library.**

| | value | where it comes from |
|---|---|---|
| inputs | `ANTENNAGATEAREA 0.126` um^2 | the most common input gate area in `sky130_fd_sc_hd.lef` — 180 of its pins use exactly this |
| outputs | `ANTENNADIFFAREA 0.4455` um^2 | what `sky130_fd_sc_hd__inv_2` declares on its Y pin |
| power/ground | nothing | inout pins are left alone |

59 input pins were patched — **exactly** the 59 the flow reported as missing,
which is the confirmation that this targets the reported defect and not something
adjacent. 64 outputs and 2 inouts as well, across all four design directories.

0.126 is the *conservative* direction: antenna ratio is metal over gate, so a
smaller gate area produces a larger ratio, flags more violations and inserts more
diodes. I am not making the check easier to pass.

**This is not a bypass.** The check runs, on real numbers, and every violation it
finds is still repaired. What has to be reported is that these values were
supplied from the standard-cell library rather than characterised from the
macro's own layout, because the compiler that produced it did not emit them.
The untouched original is kept as `*.lef.noantenna` in every design directory.

**Single variable, on purpose.** The architect listed three workarounds — thread
pinning, diode strategy, and backing off the die. I am applying the LEF fix
alone, plus the thread pinning, because thread count cannot change a result while
`RUN_HEURISTIC_DIODE_INSERTION` and the die area both change the area number I am
trying to measure. If the crash survives this, those come next, one at a time.
This is the same discipline that turned the congestion failure from a knob hunt
into a floorplan diagnosis.

---

## 2026-09-18 11:35 — Entry 24: antenna repair sweep, and why it runs in two phases

The LEF fix from Entry 23 worked. `CheckAntennas` ran to completion with **zero
Signal 11**, and it found real work:

```
before repair :  1848 net violations, 2736 pin violations
after  repair :   498 net violations,  643 pin violations   (910 diodes inserted)
```

Two things follow from that. First, had I skipped the step as I originally
proposed, the design would carry 1,848 unreported antenna violations and the
post-route area would be short 910 diodes. The architect's rejection was correct
on both counts, and I was wrong to treat a sign-off step as optional because it
did not feed a number I wanted.

Second, 498 remaining is not sign-off clean, so the baseline configuration
(heuristic off, `GRT_ANTENNA_ITERS` 3) is disqualified regardless of its area.

**Sweep, single variable per test, as instructed:**

| test | `RUN_HEURISTIC_DIODE_INSERTION` | `GRT_ANTENNA_ITERS` |
|---|---|---|
| baseline | false | 3 |
| A | **true** | 3 |
| B | false | **15** |
| C | **true** | **10** |

**Two phases, and the reason matters.** The violation count is decided at
`RepairAntennas`, step 40 of about 55. Post-route area is not known until
detailed routing, twenty steps later. A configuration that does not reach zero
violations is already disqualified by the primary goal, so routing it to
completion buys nothing but an hour of compute and a number I must not use.

- **Phase 1** runs A, B and C with `--to OpenROAD.RepairAntennas` and records
  violations before and after repair, plus diodes inserted.
- **Phase 2** takes only the configurations that reached zero and runs them end
  to end for post-route area.

If more than one reaches zero, Phase 2 runs both, because the secondary goal is
minimum area and I cannot rank them without measuring. If B reaches zero it wins
on the stated preference — it inserts no diodes at all — but I will still
measure its area rather than assume it is smaller, since more routing iterations
can grow wirelength and push the resizer around.

`sync_antenna` (the baseline) is still running at step 41 and I am letting it
finish: it is the fourth data point and the only one with a completed full flow
so far. OpenLane runs stay strictly sequential — this project has already
recorded that concurrent physical-design runs make results meaningless.

---

## 2026-09-18 11:55 — Entry 25: UVM reaches the 4 KiB point

`tb_soc_top` was hardcoded to `ICACHE_LINE_COUNT(64)` / `DCACHE_LINE_COUNT(64)`,
so every UVM run this sprint exercised the 1 KiB cache only, while the benchmark
matrix measured 4 KiB. Entry 17 flagged that as a gap and it is now closed.

`tb_soc_top` takes a `CACHE_LINE_COUNT` parameter, defaulting to 64 so nothing
existing changes, and `run_uvm.do` takes it as a fifth argument.

```
LINE_COUNT=64   soc_directed_test    PASS
LINE_COUNT=64   soc_periph_test      PASS
LINE_COUNT=256  soc_directed_test    PASS
LINE_COUNT=256  soc_periph_test      PASS
```

The 4 KiB configuration now has all three layers: directed (126 PASS, capacity
sweep from Entry 19), UVM, and the 48-run benchmark matrix.

**Also starting: the three stale Quartus points.** `fpga_points.csv` currently
mixes RTL versions — `dm` is the synchronous design (`mem_bits` 84,736) while
`sa2`, `dm_vc4` and `dm_dse` are from 2026-09-17 and still show 81,920, which is
the pre-pivot fingerprint. Any area table built from that file right now compares
different designs to each other. Refitting all three on the current RTL.

These run on the Windows side while OpenLane runs in WSL. That is not a violation
of the sequential-PD rule this project records — that rule is about two physical
design runs of the *same* flow racing each other. Quartus fits are deterministic
given a seed, so contention changes how long they take and not what they produce.

---

## 2026-09-18 12:05 — Entry 26: the four-point matrix stays, and what each pair is for

The architect confirmed all four configurations are retained at both capacities,
and — more usefully — fixed what each comparison is allowed to claim. Recording
it here because it decides how every table from here on is read:

| comparison | isolates | why it is valid |
|---|---|---|
| **0 vs 3** | **control logic area overhead** | same cache organisation (direct-mapped), different FSM depth: five states against ten |
| **3 vs 1, 3 vs 2** | **architectural performance delta** | same ten-state FSM, different organisation: direct-mapped against 2-way and against victim-cache |
| 0 vs 1, 0 vs 2 | **nothing on its own** | confounded — organisation *and* controller depth both change |

That last row is the one the peer review caught, and it is why config 3 exists.
`CACHE_CONFIG=0` is not redundant with 3: a five-state FSM is the physically
right controller for a direct-mapped cache, so it establishes the genuine
minimum area and power, while 3 exists only to hold the controller constant for
the CPI comparison. Dropping either one loses a different thing.

**Simulation side is already complete for the retained matrix:**

```
results/ablation_synctag_all.csv   1 KiB   DM 12  SA2 12  DM_VC4 12  DM_DSE 12  = 48
results/ablation_4kb.csv           4 KiB   DM 12  SA2 12  DM_VC4 12  DM_DSE 12  = 48
```

96 runs across both capacities, all four configurations, on the synchronous RTL.

**Quartus queue, not pruned:**

- in flight: `sa2`, `dm_vc4`, `dm_dse` at 1 KiB — refits to clear the mixed-RTL
  problem in `fpga_points.csv` (Entry 25)
- queued: `dm_4kb`, `sa2_4kb`, `vc4_4kb`, `dse_4kb`
- then power on all of them

**OpenLane:** `sync_antenna` is in detailed routing, step 43. This is the step
where `ERROR_ON_TR_DRC` bites if the router cannot close, so it is the next real
risk after the antenna fix.

---

## 2026-09-18 12:12 — Entry 27: the four-point table is consistent, and it answers the confound

All four configurations are now fitted on the synchronous RTL. The mixed-version
problem from Entry 25 is gone — every row carries the ~84,736 `mem_bits`
fingerprint that says the tag arrays are in block RAM.

**1 KiB, synchronous RTL, seed 2:**

| point | cfg | LE | regs | slack | Fmax | mem_bits |
|---|---|---:|---:|---:|---:|---:|
| `dm` | 0 | 14,596 | 8,015 | 0.000 | 50.00 | 84,736 |
| `dm_dse` | 3 | 15,007 | 8,113 | **+1.097** | 52.90 | 84,736 |
| `sa2` | 1 | 16,211 | 8,322 | +0.309 | 50.78 | 84,864 |
| `dm_vc4` | 2 | 18,033 | 9,898 | +0.708 | 51.83 | 84,736 |
| `dm_nopc` | 0, no counters | 11,894 | 5,977 | -0.140 | 49.65 | 84,736 |

**(0 vs 3) — control logic area overhead.** Same cache organisation, five-state
FSM against ten:

```
+411 LE  (+2.8 %)   +98 registers
```

This is the number the paper could not previously state. The peer review's
objection was that the DM-versus-SA2 result conflated organisation with
controller depth; the conflation is now quantified rather than argued about.

And the ten-state controller is **faster**, not slower: +1.097 ns slack against
0.000. That matches what this project already recorded — that the "longer
critical path" explanation for the DM win was wrong — and now it has a
same-RTL, same-seed measurement behind it.

**(3 vs 1) and (3 vs 2) — architectural delta, controller held constant:**

```
2-way set-associative   +1,204 LE  (+8.0 %)    +209 registers
victim cache, 4 entries +3,026 LE  (+20.2 %) +1,785 registers
```

The victim cache is three times the area cost of associativity, for the cache
organisation that performed worst on CPI in the matrix. That is a clean DSE
conclusion and it needs no hedging.

**The synchronous pivot helped every configuration, not just DM:**

```
sa2      18,232 -> 16,211 LE   (-2,021, -11.1 %)
dm_vc4   19,860 -> 18,033 LE   (-1,827,  -9.2 %)
dm_dse   17,208 -> 15,007 LE   (-2,201, -12.8 %)
```

Around two thousand logic elements per configuration, which is the tag arrays
leaving logic and entering M9K. The DM figure was -586 because DM was already
the smallest; in relative terms every point moved by roughly the same amount of
absolute storage.

**Caveat I am not leaving out.** These are single-seed fits at seed 2. The
four-seed spread measured on DM was 148 LE, so the +411 LE control-logic figure
is comfortably outside it, but +1,204 and +3,026 are stated on one seed each.
Before any of this goes in the paper the three non-DM points need the same
four-seed treatment DM got. Noted as outstanding, not quietly assumed away.

Also: `dm` at seed 2 is the 0.000 ns outlier identified in Entry 14. Its **area**
is representative; its **slack** is the worst of four draws. The timing column
above should be read with that in mind and the paper must quote the range.

---

## 2026-09-18 12:55 — Entry 28: checkpoint before an interruption

The architect has to leave and the machine may sleep, so this records exactly
what is banked and how to pick it up. RTL is still
`c9c969243b25b15e144bc1698b40784c`.

**Safe on disk, nothing to redo:**

| result | file |
|---|---|
| 48-run matrix, 1 KiB, synchronous | `results/ablation_synctag_all.csv` |
| 48-run matrix, 4 KiB, synchronous | `results/ablation_4kb.csv` |
| FPGA four-point table, all on the same RTL | `results/fpga_points.csv` |
| FPGA power, dm / dm_nopc / sa2 / dm_vc4 / dm_dse | `results/power.csv` |
| DM four-seed sweep | `results/seed_sweep_sanitized.csv` |
| Directed regression 126 PASS, UVM 8/8 + 4 KiB | logs in `results/` |

**In flight, and what happens if it dies:**

1. **OpenLane `sync_final`** — reached step 43, detailed routing. If the machine
   sleeps this run dies. It is **resumable**: OpenLane keeps every completed
   step's state, so
   `bash asic/run_pd.sh soc_dm_control sync_final --from OpenROAD.DetailedRouting`
   picks up rather than repeating the 32-minute resizer at step 41. Steps 37, 38
   and 40 — the three that used to fail — are already past and their fixes are in
   config, not in the run.
2. **Quartus seed sweep** — six of nine fits are already written to
   `fpga_points.csv` as `@s1` / `@s3` / `@s4` rows. Each fit is independent, so a
   kill costs only the one in progress; re-running the sweep skips nothing but
   repeats cheaply.

**Nothing is at risk that has not already been written down.** Every number
quoted in entries 1 through 27 comes from a file in `results/`, not from a
running process.

---

## 2026-09-18 13:30 — Entry 29: BLOCKER. Odb.ReportDisconnectedPins is broken below the script level

Six attempts. Four real defects fixed. The seventh symptom is a native segfault,
and that is where I stop and hand this up.

**The design side is finished and clean.** Before the blocker:

| step | result |
|---|---|
| 37 global routing | passes, no `GRT-0118` (four-corner floorplan, Entry 20) |
| 38 antenna check | runs, no segfault (LEF antenna properties, Entry 23) |
| 40 antenna repair | 910 diodes, 1848 -> 498 net violations |
| **43 detailed routing** | **`Number of violations = 0`** |
| 45 antenna post-route | 501 net / 655 pin |
| 46 DRC checker | passes |
| **47 report disconnected pins** | **blocked** |

**The sequence of symptoms, in order:**

```
1  TypeError: attribute name must be string, not 'tuple'
2  rich.errors.NotRenderableError: unable to render str
3  UnboundLocalError: cannot access local variable 'signal_type'   <- on its own assignment target
4  AttributeError: 'int' object has no attribute 'outputs'
5  AttributeError: '_ParameterKind' object has no attribute 'other_inouts_connected'
6  Signal 11, native stack through libpython, no Python exception
```

**What I fixed, and it was worth doing:**

1. Declared the SRAM macro in `IGNORE_DISCONNECTED_MODULES`. Its port 1 is
   deliberately unused — `csb1` tied high, `addr1` low, `dout1` open — which is
   exactly what that variable is for, and the tool's own message says so.
2. Coerced values into `str` before handing them to `rich`.
3. Made the terminal loop skip a terminal it cannot read, naming it on stderr.
4. Replaced `PortStats`, which carried `@dataclass` over ten **un-annotated**
   class attributes. `dataclass` only takes annotated names as fields, so it
   produced a class with zero fields: counters stayed class attributes and every
   instance compared equal to every other. Verified independently:
   `len(fields(T)) == 0` and `T() == T()` is always True.

Defect 4 is a genuine bug in OpenLane worth reporting upstream regardless.

**Why I am stopping.** Symptoms 3, 5 and 6 are not logic errors. A name cannot be
unbound on the line that binds it. `Module.PortStats()` cannot return an
`inspect._ParameterKind`. Each logic fix moved the failure somewhere new, which
is what memory corruption does — my fifth fix removed the class from the path
entirely and the result was a hard segfault instead of a type confusion. The
fault is in the odb SWIG bindings or the embedded interpreter, below anything I
can reach by editing a script.

**Options, with costs:**

- **A — write an independent disconnected-pin check.** The question is
  answerable from the post-route netlist without odb. Satisfies the sign-off
  intent, under our control, no tool bug in the path. Real work, a few hours.
- **B — skip the step and record it.** The architect has forbidden this, and I
  am not proposing it. Noting only that the step *reports*; `Checker.DisconnectedPins`
  is the separate step that would fail a build, and the one disconnection this
  design has is the declared, intentional SRAM port 1.
- **C — different OpenROAD build.** Most likely to work, least under our
  control, and it invalidates comparability with every ASIC number measured so
  far in this sprint.

I recommend **A**. It is the only one that both keeps the sign-off honest and
keeps the numbers comparable.

---

## 2026-09-18 15:40 — Entry 30: the step 47 root cause, measured

Entry 29 stopped with a diagnosis: "the fault is in the odb SWIG bindings or the
embedded interpreter, below anything I can reach by editing a script." That was
an **inference** from a pattern of symptoms. I wrote it as a conclusion. It was
not measured, and I should not have presented it as settled. This entry settles
it, and the inference turns out to have been right for a reason I had not
identified.

**The experiment.** `asic/probe_odb_iter.py` is sixty lines. It opens the
post-route database, walks instances and terminals, coerces the same three
accessors the real report uses, and prints counts. It imports nothing from the
report layer: no rich, no click, no dataclass, no nested classes, no inspect.
If the fault were in `disconnected_pins.py` this probe would be clean.

**Three passes, same file, same binary, same arguments:**

```
pass 1  TypeError: unsupported operand type(s) for +=: 'int' and 'str'
        ...on `n_inst += 1`, where n_inst = 0 is three lines above
pass 2  PROBE_OK insts=190285 iterms=1102609 disconnected=2054
pass 3  SIGSEGV (rc=139), native stack through libpython
```

Same input, three different outcomes, one of them correct. That is the whole
answer to "why does step 47 fail": it is a nondeterministic memory corruption,
and it was never in the script.

**Which means the six patches in Entry 29 were treating symptoms.** Each one
"moved the failure somewhere new" and I read that as progress narrowing a bug.
It was not. The failure moved because it is random. Four of those patches fixed
real defects and are worth keeping -- the `@dataclass`-over-unannotated-fields
bug is genuine and worth reporting upstream -- but not one of them was ever
going to unblock this step, and I spent an afternoon believing otherwise.

**Then I eliminated the alternatives, one variable at a time.**

| hypothesis | test | result |
|---|---|---|
| stale bytecode | look for a `.pyc` of the script | none exists; only `reader.pyc`. Disproven |
| CPython's pooled allocator | 10 runs with `PYTHONMALLOC=malloc` | 0 clean, unchanged. Disproven |
| real memory exhaustion | `free -g` during the MemoryError | 21 GB free at 557 MiB RSS. Disproven |
| the 9p filesystem | copy the database to ext4, same md5, 10 runs | 0/10 both arms. Disproven |

`PYTHONMALLOC=malloc` produced one `rc=134` -- SIGABRT, glibc's **own** allocator
detecting a corrupt heap and aborting. That is independent confirmation from a
second allocator that the heap is being written out of bounds.

**Then I localised it.** The probe takes a level argument, so the access pattern
can be cut into stages. Five passes each:

```
level 1  open the database, read nothing              clean 5/5
level 2  iterate 190,285 instances, no terminals      clean 4/5
level 3  materialise each instance's ITerms,
         call no accessor at all                      clean 0/5
level 4  level 3 plus the three accessors             clean 0/5
```

**Level 3 calls nothing.** It only asks odb for each instance's terminal set and
walks it. That is where the corruption becomes certain, so the fault is in the
**`dbSet` iterator's SWIG binding**, not in `getSigType`, `getIoType`,
`getName`, or anything the report does with the values. Level 2 failing once in
five says the same iterator is already unsafe on the 190k instance set; level 3
walks 1.1 million terminals and never survives.

Total across every run today: **41 passes, 1 clean.** Roughly 2%.

That 2% also disposes of the obvious shortcut. Retrying step 47 until it passes
is not a workaround, because a process whose heap is corrupt can finish and
report numbers that are wrong. The one clean pass is evidence about the tool,
not a sign-off.

**What this says about the fix.** I checked what an upgrade would actually
change, which I should have done before attempting one:

```
                      disconnected_pins.py    pinned OpenROAD rev
2.3.10 (installed)    --                      edf00dff99f6c40d...
2.4.0.dev1            byte-identical          edf00dff99f6c40d...   <- same binary
3.0.0.dev21           byte-identical          87af90f72f3f9be1...   <- different
```

The script is identical in all three. So **2.4 is worthless here** -- same script,
same binary, it would reproduce the fault exactly. Only 3.0.0.dev21 changes the
OpenROAD build, which is the one place the bug can live. The architect's
instruction to upgrade the tool rather than write an ad-hoc parser was right,
and it is now right for a demonstrated reason instead of a guess.

**The other blocker cleared itself.** DNS is working again in both distros --
`getent hosts cache.nixos.org` resolves, nameserver is now 10.255.255.254. The
3.0.0.dev21 build failed last time at `lemon-graph-1.3.1` `make check`; with the
binary cache reachable that dependency may come down prebuilt. Restarting it
now, in the background, while this is written up.

**Honest statement of where PD stands.** Steps 1 through 46 pass, including
detailed routing with `Number of violations = 0`. Step 47 is blocked by a defect
in the tool, now characterised precisely rather than guessed at. There is still
**no post-route PPA number**, and the constitution's "full OpenLane 2 flow on
every change" is still unmet. Nothing here changes that; it only says what has
to be fixed for it to change.

---

## 2026-09-18 16:20 — Entry 31: Entry 30 is wrong. It is the machine.

I have to retract the conclusion I wrote three hours ago. Entry 30 said the
step-47 fault is "in the `dbSet` iterator's SWIG binding" and presented that as
measured rather than inferred. The measurements in it are real and I stand by
every number. **The attribution is wrong.** There is no OpenLane bug here.

**What I failed to test.** The staged probe was clean at level 2 (190k
instances) and never clean at level 3 (1.1M terminals), and I read that as
naming the guilty API. Level 3 also allocates several times more memory than
level 2. I had two explanations and tested neither against the other. I picked
the one about the tool.

**The test I should have run first.** Remove odb entirely. Allocate a
comparable number of small objects, do arithmetic whose answer is known in
advance, verify it. Nothing in such a program can fail unless the machine is
wrong. Eight passes per arm:

```
A  odb probe, level 4, openroad python      clean 0/8
B  pure python, no odb, openroad python     clean 1/8   <- 2x CORRUPT-DATA
C  pure python, no odb, system python3      clean 1/8   <- 3x CORRUPT-DATA
D  pure python, WINDOWS python 3.11,
   outside WSL altogether                   clean 5/8   <- 3x 0xC0000005
```

Arm C has nothing to do with OpenROAD. Arm D has nothing to do with WSL. A
forty-line loop that builds tuples and checks that `b == str(a)` **fails that
check** on this machine. `0xC0000005` is STATUS_ACCESS_VIOLATION, the same code
the kernel bugchecks carry.

**CORRUPT-DATA is the part that matters.** Those runs did not crash. They
completed and produced wrong values, and only my own verifier caught them. A
crash is loud; this is not.

**The corroborating evidence was there the whole time and I never looked.**

```
Windows System log, last 45 days:
  9 x unexpected shutdown (Kernel-Power 41), one of them today at 13:19
  4 x bugcheck 0x1E KMODE_EXCEPTION_NOT_HANDLED, first param 0xC0000005
  2 x bugcheck 0x50 PAGE_FAULT_IN_NONPAGED_AREA
```

`0x50` is the textbook bad-RAM stop. And lemon-graph's GCC "internal compiler
error" moved between source files and between optimisation passes on a rebuild
-- `maps_test.cc`/`pass_copy_prop`, then `adaptors_test`+`unionfind_test`/
`pass_ccp`. A compiler bug is deterministic. A wandering one is not a bug.

Then the hardware itself:

```
BANK 0  16 GB  DDR5-4800  SK Hynix  HMCG78AEBSA095N
BANK 0  16 GB  DDR5-4800  SK Hynix  HMCG78MEBSA092N   <- different part number
```

Two mismatched modules running as a pair at 4800.

**Four symptom families, one cause.** OpenROAD's odb (39/40), GCC, Python on two
operating systems, Quartus. That last one has been in this project's notes for
weeks as "random Access Violation crashes measured at ~8% (both quartus_fit AND
quartus_map), always retry." It was never a Quartus quirk. It was this, and
"always retry" is exactly the wrong advice when silent corruption is on the
table.

**Twice in one day I stated an inference as a finding.** Entry 29 diagnosed
"corruption below the script level" from symptoms; Entry 30 opened by calling
that out and then did the same thing one level up. The pattern is that I stop
testing at the first explanation that accounts for the evidence, instead of the
first one that *excludes the alternatives*. The probe that settled this took
four minutes to write.

**What this does to the project's numbers.** Anything measured once on this
machine is now unreliable. Anything reproduced identically across independent
runs is strong evidence of itself, because corruption would have to repeat
byte-for-byte. By that standard:

| result | standing |
|---|---|
| 48-run matrices, configs 1/2/3 byte-identical 48/48 | self-consistent, holds |
| three Quartus fits re-run and reproduced exactly | holds |
| DM four-seed sweep | multiple points, holds |
| **L0_ENTRIES sweep (13,875 / 13,465 LE)** | **one fit each. Must be re-run** |
| **4 KiB Quartus points** | **never run; do not start yet** |
| detailed routing "0 DRC violations" | one run. Needs confirming |

**PD is not blocked by OpenLane.** It is blocked by a machine that cannot be
trusted to compute. Upgrading OpenROAD would have changed nothing, and I would
have spent another day proving it. Stopping all long runs until the memory is
tested; a probe that takes two minutes now exists to check any fix.

---

## 2026-09-18 18:30 — Entry 32: the CPI matrix caught a bug I put in the RTL

The L0 depth sweep was supposed to price a trade-off. Instead it found that one
side of the trade-off did not work at all, and the fault was mine.

**All 48 simulations at `L0_ENTRIES=4` failed.** Not a parse error, not a crash:
every one stopped on the firmware result check. `ablation_l0_4.csv` came out
with a header and no rows.

**The bug.** The L0 hot buffer is a direct-mapped cache indexed by the low bits
of the block address, with everything above the index held as its tag. When I
parameterised the depth I narrowed the index and left the tag slice pinned:

```verilog
assign hot_index = request_block[L0_IDX_BITS-1:0];   // narrows with the depth
... (hot_tag[hot_index] == request_block[27:3]);     // does NOT
```

At eight entries `L0_IDX_BITS` is 3 and the two meet exactly. At four entries the
index is `[1:0]` and the tag still starts at bit 3, so **bit 2 belongs to
neither field**. Two blocks differing only in that bit share an entry and match
each other's tag: the buffer returns the wrong cache line, and the firmware
computes the wrong answer.

**I had already written down that this needed doing.** The patch script that
introduced the parameter carries the comment "the tag stored alongside must
widen as the index narrows" — above an edit whose `old` and `new` strings are
identical. I wrote the requirement and then shipped a no-op.

**Four write sites, and my first fix found two of them.** The tag slice appears
six times across the two files. My anchors matched four; two survived because
their whitespace differed (`hot_tag[miss_hot_index]   <=` versus one space) or
the expression was split across lines. L0=4 still failed after the first fix.
What found the rest was not another anchor — it was grepping for the *pattern*
rather than the string:

```
grep -n '\[27:3\]\|\[BLOCK_WIDTH-1:3\]\|BLOCK_WIDTH-4\|\[24:0\]'
```

Rule for next time: after a width-parameterisation edit, grep for every
hardcoded form of the old width and require zero hits. Anchor counts prove the
edit applied; they cannot prove it was applied everywhere.

**The verification, in order:**

```
lint, 4 configs        0 correctness warnings
directed regression    126 PASS, 0 FAIL, 0 errors
UVM                    PASS, 6 runs
L0=8 vs canonical      8/8 identical -- the fix is a no-op at the default
```

That last line matters: `L0_IDX_BITS` is 3 at eight entries, so every slice is
character-for-character what it was, and no previously published number moves.

**And now the trade-off can actually be priced.**

```
kernel     config      L0=8     L0=4    CPI      i_wait 8 -> 4
crc32      DM         17619    18147   +3.00%     163 ->  691
crc32      SA2        17620    18676   +5.99%     164 -> 1220
crc32      DM_VC4     17620    18676   +5.99%     164 -> 1220
crc32      DM_DSE     17620    18676   +5.99%     164 -> 1220
matmult    DM         53434    54005   +1.07%     198 ->  769
matmult    SA2        62021    63164   +1.84%     199 -> 1342
matmult    DM_VC4     56340    57484   +2.03%     238 -> 1382
matmult    DM_DSE     58157    59300   +1.97%     199 -> 1342
```

Instruction-fetch stall rises **four to seven times**. Halving the buffer is not
free and never was; it cost 1-6% of runtime, which against a 4.9% area saving is
a poor bargain on this workload. I reported "-721 LE and better slack" as an
improvement two messages before I had any of this.

**The LE numbers for L0=4 and L0=2 are void.** 13,875 and 13,465 are fits of a
design that computes wrong answers. Both rows are deleted from
`results/fpga_points.csv` rather than left in with a footnote.

**What this says about the constitution.** The rule that every change carries
the whole chain -- TB, UVM, Embench, PD -- is what caught this. The LE fits were
perfectly happy to synthesise broken RTL and report a smaller number, and I was
perfectly happy to report it. Only running the software found it.

---

## 2026-09-18 19:45 — Entry 33: the L0 depth, priced on all three axes

The question that started this: the I-cache L0 hot buffer holds eight 128-bit
lines in flip-flops -- 1,024 registers for 128 bytes -- and eight was never a
considered choice. It is now a measured design point.

**Area and power, four Quartus seeds each, power on the seed-2 fit:**

```
              LE (4 seeds)                    mean     regs    worst slack   power
L0=8   14638 / 14596 / 14600 / 14672        14,626    8,015     0.000 ns    272.25 mW
L0=4   13893 / 13859 / 13910 / 13921        13,896    7,403    -0.297 ns    270.19 mW
                                            -730       -612     WORSE        -2.06 mW
                                           (-5.0%)              
```

**Runtime, the full 48-run matrix at each depth (12 kernels x 4 configs):**

```
total cycles   L0=8  6,261,571
               L0=4  6,663,475   +6.42%
               L0=2  7,229,040  +15.45%
```

**Verdict: eight entries stays.** Halving the buffer costs 6.42% of runtime to
buy 5.0% of logic elements and 0.76% of power, and makes worst-case timing
worse rather than better. That is a loss on every axis that matters, and it is
now a measurement rather than an argument.

**The spread across kernels is the interesting part.** At L0=4:

```
mont64     +19.21%     fdct         +0.00%
md5sum     +15.33%     insertsort   +0.02%
sha256     +14.13%     matmult      +1.07%
tarfind    +12.41%     wikisort     +1.23%
```

Two kernels do not notice and two pay a fifth of their runtime. `fdct` is
exactly unchanged to the cycle on all four configs, so its instruction working
set fits in four entries; `mont64` and `md5sum` clearly do not. A buffer this
small is a step function, not a gradient, which is why a single-kernel probe
would have been worthless here.

**On timing, I had it backwards.** I reported earlier that L0=4 "improves slack
to +0.710 ns". That was one fit, at seed 2, on the broken RTL of Entry 32. With
four seeds on correct RTL, seed 2 gives **-0.297 ns** -- it misses 50 MHz -- and
seed 2 is the outlier in both directions depending on the design. The four-seed
requirement is what caught this; a single fit said the opposite of the truth.

**Cost of the detour.** One simulation in the L0=4 matrix (`wikisort/DM_VC4`)
came back empty and was re-run individually, which is the routine cost of this
machine. Separately, the original sweep launched at 15:59 was still alive at
19:18 -- stuck for two hours on `depthconv/SA2` at L0=2 before dying on a
7,200-second timeout. It was running the pre-fix RTL: the L0 returned a wrong
line, the firmware branched wrong, and it never terminated. That hung process
was burning a core the whole afternoon, which is a large part of why Quartus
fits I attributed to "tool contention" ran six times slow.

## 2026-09-27 — Entry 34: the equivalence check of the final netlist, and where it stops

The last open item of the final PD (RTL 8b163675, runs final_A / final_B) was
the RTL-vs-netlist equivalence check. Details are in FLOW_JOURNAL Incident 86.

**What I got wrong first.** Incident 85 said final_B's EQY was "re-run with the
patched tokenizer". It was not. OpenLane's nix `openlane` binary prefixes its own
tool directories onto PATH, so its stock `eqy` shadowed mine. `combine.ys` loading
the nix plugin path proved this. My patched copy also broke EQY's plugin lookup
(`root_path()`), which I only saw when I ran it standalone.

**What EQY can and cannot do here.** Run standalone, EQY reached the proof stage
for the first time on final_B and proved 795 of 876 partitions. The remaining
failures are not design bugs. They have three measured causes:

- OpenLane's synthesis always re-encodes four FSMs to one-hot, and EQY matches
  names regardless of encoding.
- EQY cuts at combinational nets too, which gives free inputs with impossible
  values. Counterexamples on `bank_web0` and UART `next_state` show this.
- One partition held about 16,700 flops and died of OOM.

**What I did instead.**

1. A formal proof of the `fsm` step, with a negative control.
2. A sequential equivalence check with ABC:
   - The 12 SRAM macros are cut. Their input pins are compared, and their read
     data is a shared free input.
   - Reset is forced in cycle 0.
   - Two negative controls: a mutated reset PC, caught at frame 0, and a
     mutated SLTU, caught at frame 19. The second shows the check really runs
     instructions from free SRAM data.
   - The whole front end was built twice and matched bit for bit.

**Where it stops, stated plainly.** The equivalence is proven for 19 cycles from
reset, for every input. The unbounded proof is UNDECIDED. Signal correspondence
merges about 9,500 register pairs but leaves 11,569 on each side, symmetric:
regfile, both tag RAMs, the data-RAM hold/live registers, `tag_rd_tag`, and
about 5,800 flops whose names async2sync hid (not identified). My explanation is the 33x33
multiplier: techmap's array on the gold side against the gate side's
maccmap+ABC structure, which SAT-based CEC cannot equate. I have not proven
this explanation. The concrete next step is ABC `&acec` on a register-mapped
combinational miter, or `keep_hierarchy` on the ALU in the next PD so there is a
boundary to cut at.

## 2026-09-27 — Entry 35: the multiplier, proved; and what Entry 34 got wrong about it

Option A (FLOW_JOURNAL Incidents 89-90) closed the equivalence of the final
netlist without touching the layout. The register-mapped LEC had proved every
output except 34, and a case split on `alu_ctrl_e` left only the four multiply
operations. That much matched Entry 34's guess.

**What Entry 34 got wrong.** It blamed "techmap's array on the gold side against
maccmap+ABC on the gate side". Both sides go through the same `maccmap`: gold's
`$mul` reaches it via the alumacc wrapper inside `techmap`. The difference is the
order in which maccmap groups the partial products into full adders. I measured
this by simulating every AND node of both pure multipliers on the same patterns:

- 40 % of internal nodes have no functional partner in the other circuit.
- The first mismatch is at level 2: one tree adds `B10&A1` to `B9&A2`, the other
  adds `B11&A0` to `B9&A2`.
- The same cell gives three different groupings in three Yosys processes: a
  fresh process, the RTL context and the synthesis process.

SAT sweeping has nothing to merge in that situation, which is why every
fraig-style engine timed out. `&acec` matched too few adder boxes and reported a
false NOT EQUIVALENT, and `&polyn` segfaulted.

**What worked.**

1. **Capture the network in the right process state.** The synthesis replay was
   byte-exact up to `techmap`. I split that one command into `techmap
   -max_iter 1`, a snapshot, and `techmap`. The first iteration of the split
   command is the first iteration of the real one, so the snapshot holds the
   word-level network maccmap built with N1's own grouping.
2. **Prove that network algebraically.** I wrote backward rewriting over Z/2^64
   (`macc_alg.py`). The step that keeps it small is substituting a full adder's
   sum by the exact identity Y = A + B + C - 2X. The polynomial then stays
   linear through the whole tree and peaks at 1,128 monomials in about 2 s.
3. **Link and substitute.** `&cec` links the network to the in-context cone in
   0.00 s, because the grouping is now the same. SAT checks the techmap of each
   cell type. Substituting the proven multiplier closes the last 34 outputs in
   0.16 s.
4. **Check that it can fail.** Five negative controls fail as required, and every
   step ran twice with identical hashes.

Option B was not run. It would not have helped: the grouping mismatch sits
inside the ALU and would survive a hierarchy boundary. That last point is my
judgement; I did not test it.

**Honest limits.**

- The proof trusts the Yosys front end and its techmap semantics. The techmap of
  the multiplier's own cells is additionally checked by SAT.
- The SRAM macros are black boxes, covered only by gate-level simulation.
- The stock EQY tool still does not pass.
- Antenna (140 nets), the ss corner (-7.4 / -8.3 ns) and 4,814 fanout / 722
  slew (nom_tt) violations remain open. They are listed in FINAL_METRICS
  section 4.

**My own slips this session.**

- `wsl.exe` without `-d Ubuntu` landed in a distro with no `/nix`.
- My RTLIL parser kept the backslash on port names.
- A structure-breaking mutation made the polynomial explode and had to be
  killed. I replaced it with structure-preserving mutations and added a
  monomial cap.
- Two stray files from an earlier misdirected command were sitting in the
  published repo root. I deleted them.
