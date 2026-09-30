# Results

All numbers below come from `results/*.csv` in this directory. The RTL is a
byte-identical copy of the frozen `hdl/`; no `.v` file was modified. Every
comparison holds the firmware, the memory system and the cycle classifier fixed.

## Validation of the mirror

Before anything else, the mirror was checked against the published matrix. It
reproduces all three published weighted CPI values exactly:

| Configuration | Published | Mirror |
|---|---|---|
| DM | 1.299 | 1.2995 |
| SA2 | 1.416 | 1.4161 |
| DM+VC4 | 1.424 | 1.4237 |

A second, independent check: `DM_VC4` and `DM_DSE` agree cycle for cycle on the
eight kernels that record no victim hits, which is what must happen if
`CACHE_CONFIG=3` really is DM+VC4 with the victim buffer disabled.

## Experiment 1: the published gap is a controller artifact

`DM_DSE - DM` varies the controller with the organization fixed.
`SA2 - DM_DSE` varies the organization with the controller fixed.

| kernel | DM | DM_DSE | SA2 | DM+VC4 | controller | associativity |
|---|---|---|---|---|---|---|
| crc32 | 17,610 | 17,620 | 17,620 | 17,620 | +10 | 0 |
| depthconv | 3,896 | 4,441 | 4,395 | 4,441 | +545 | -46 |
| edn | 117,589 | 124,906 | 123,312 | 123,914 | +7,317 | -1,594 |
| fdct | 210,245 | 239,394 | 239,310 | 239,394 | +29,149 | -84 |
| huffbench | 340,870 | 364,723 | 364,523 | 364,707 | +23,853 | -200 |
| insertsort | 128,785 | 132,954 | 132,906 | 132,954 | +4,169 | -48 |
| matmult | 53,536 | 64,580 | 62,021 | 56,340 | +11,044 | -2,559 |
| md5sum | 70,266 | 78,928 | 74,915 | 78,016 | +8,662 | -4,013 |
| mont64 | 85,371 | 96,551 | 96,439 | 96,551 | +11,180 | -112 |
| sha256 | 104,838 | 121,018 | 111,192 | 121,018 | +16,180 | -9,826 |
| tarfind | 169,418 | 193,859 | 193,803 | 193,859 | +24,441 | -56 |
| wikisort | 160,882 | 174,391 | 174,222 | 174,391 | +13,509 | -169 |
| **CPI** | **1.2995** | **1.4327** | **1.4161** | **1.4237** | | |

- controller depth alone: **+150,059 cycles, +10.25%**
- associativity alone: **-18,707 cycles, -1.16%**
- the two sum to +131,352 cycles, +8.98%, which is the published gap

With the controller held fixed, the two-way cache wins on 11 of 12 kernels,
ties on one and loses on none. The published claim that the direct-mapped
organization wins on all twelve kernels inverts.

## Experiment 2: capacity sweep

Same controller throughout, 16-byte line, both caches swept together.

| capacity | DM | DM_DSE | SA2 | controller | associativity | published net |
|---|---|---|---|---|---|---|
| 512 B | 1,723,049 | 1,980,563 | 1,791,010 | +14.95% | -9.57% | +3.94% |
| 1 KiB | 1,463,306 | 1,613,365 | 1,594,658 | +10.25% | -1.16% | +8.98% |
| 2 KiB | 1,450,835 | 1,594,668 | 1,579,826 | +9.91% | -0.93% | +8.89% |
| 4 KiB | 1,448,678 | 1,589,606 | 1,579,778 | +9.73% | -0.62% | +9.05% |

The set-associative cache never loses at any capacity: 48 comparisons, zero
losses. The associativity gain shrinks monotonically as capacity grows, from
9.57% at 512 B to 0.62% at 4 KiB, because the kernel working sets fit. I-cache
misses for `fdct` fall from 4,257 at 512 B to 45 at 1 KiB, so the paper's chosen
1 KiB sits just past the knee of the curve.

There is **no crossover in 512 B to 4 KiB**. The controller penalty exceeds the
associativity gain at every capacity, so a comparison drawn the way the paper
draws it would name the direct-mapped configuration the winner throughout.

The most useful diagnostic is the last column. The published gap is nearly
constant, 8.98%, 8.89% and 9.05%, across a fourfold change in capacity, while
the true organizational effect changes by a factor of fifteen over the same
range. A genuine cache-organization effect cannot be capacity-invariant; a
controller overhead can.

## Experiment 3: victim-buffer depth

`VICTIM_ENTRIES` is already generic in the DSE core, and the only guard on the
value is a `$display` note rather than a check, so depth is a third axis
reachable with no RTL change at all. Totals over twelve kernels, 1 KiB, 16-byte
line, `CACHE_CONFIG=2`:

| Depth | Total cycles | vs depth 4 |
|---|---|---|
| 2 | 1,603,589 | +0.02% |
| 4 | 1,603,205 | — |
| 8 | 1,601,378 | -0.11% |

Quadrupling the buffer moves the total by 0.14%. Only two kernels respond at
all: matmult falls from 56,548 to 55,124 between depth 2 and 8, a 2.5%
improvement, and md5sum by 1.0%. The other ten are flat to the cycle, which is
consistent with their recording no victim hits at any depth.

This matters for the paper's central claim. Across the three axes explored --
organization, capacity and victim depth -- the largest organizational effect at
the 1-KiB operating point is about 1%, while the controller costs 10.25%. Only
by shrinking capacity to 512 B does any organizational effect (9.57%) approach
the controller overhead, and even there it does not exceed it.

## Experiment 4: line size

Line size is the one axis that needed real RTL work. It was fixed in the
four-word data banks, the two-bit beat counter and the
`TAG_WIDTH = 32 - 4 - INDEX_WIDTH` split. `LINE_WORDS` now runs through
`cache_dse_data_bank.v`, both DSE cores, `cache_axi_master.v`, `icache.v`,
`dcache.v`, `soc_top.v` and the harness.

Capacity is held at 1 KiB, so line size and line count necessarily co-vary:
16 B gives 64 lines, 32 B gives 32, and 64 B gives 16. **This axis therefore
mixes line size with the number of sets**, which cannot be avoided at constant
capacity. For SA2 at 64 B there are only 8 sets, so its conflict behaviour is
not comparable to the 32-set case on line length alone.

### Correctness of the refactor

Two separate guarantees, and they cover different things.

At `LINE_WORDS=4` the refactored RTL reproduces the frozen results **cycle for
cycle on all 48 runs**, twelve kernels across all four configurations. That
establishes the refactor changed no behaviour at the original geometry.

At other line sizes there is no such reference, but every run is still
self-checking: the firmware writes `DONE_MAGIC` only when its own result check
passes, the harness fatals otherwise, and it separately verifies that the cycle
categories reconstruct `mcycle` and that accesses equal hits plus misses. A run
that reports a number has therefore computed the right answer.

### The 16-byte alignment bug

Eight-byte lines hung, while 16, 32 and 64 B worked. The cause was in
`cache_axi_master.v`, which forced every refill address to a 16-byte boundary:

```verilog
addr_q <= {i_refill_req_addr[31:4], 4'b0000};
```

Masking to 16 B is a no-op for lines of 16 B or more, because the cache already
sends an address aligned to its own line, which is why only the 8-byte case
failed. For an 8-byte line a refill of `0x48` was issued at `0x40` and the cache
was filled with the wrong words. The mask now follows `LINE_WORDS`. This was
found by sampling the cache FSMs over time: at 8 B the I-cache access count
froze at 18 with the FSM in `ST_IDLE`, which ruled out a stalled controller and
pointed at wrong instruction data instead.

## Placement-seed sweep

Seed 4, which the paper omitted, was run for all three configurations.

| Configuration | Seed 4 LE | Setup slack | Restricted Fmax |
|---|---|---|---|
| DM | 15,287 | +0.387 ns | 50.99 MHz |
| SA2 | 18,249 | +0.277 ns | 50.70 MHz |
| DM+VC4 | 19,899 | +0.809 ns | 52.11 MHz |

All fifteen fits meet the 20,000-LE budget with positive slack. Seed 4 is the
worst seed for DM and for SA2, so omitting it had made the reported spread
narrower than it should have been: 68 to 99 LEs for DM, 109 to 115 for SA2.
Combinational and register counts are unchanged at seed 4, confirming that a
seed moves placement only. The area conclusion is unaffected, since the 2,980-LE
gap between configurations is still 26 times the largest placement noise.

## What these results do not show

`DM_DSE` is the DSE core with its second way and victim buffer disabled, not an
independently optimised direct-mapped design on a deep pipeline. The measured
penalty is the cost of **this** ten-state controller, not an intrinsic cost of
supporting associativity. A better-written deep controller could narrow or close
it. The defensible claim is that controller depth can dominate the miss-rate
benefit of associativity at small capacities, not that associativity is
worthless and not that direct-mapped is faster.

Line size was not swept. The 16-byte line is fixed in the four-word data banks,
the two-bit beat counter and the `TAG_WIDTH = 32 - 4 - INDEX_WIDTH` split, so
sweeping it needs real RTL work.
