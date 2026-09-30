# Cache DSE follow-up experiments

This directory answers the reviewer objections that the frozen design cannot
answer about itself. It is a self-contained mirror of the repository layout, so
every tool here runs against the copies in `research/` and never touches the
frozen sources or the published build artifacts.

## Why a mirror

The headline result of the paper is that the direct-mapped configuration wins on
all twelve kernels. That comparison is confounded. `CACHE_CONFIG=0` selects
`icache_controller.v`, a five-state FSM, while `CACHE_CONFIG=1` and `2` select
`icache_dse_core.v`, a ten-state FSM with an extra `ST_LOOKUP` state. The
published comparison therefore varies cache organization and controller depth at
the same time, and cannot separate them.

## Isolation

`research/hdl`, `research/tb`, `research/sw` and `research/verification` started
as byte-identical copies of `hdl/`, `tb/`, `sw_baremetal/` and `verification/`.
The Quartus projects and `quartus/` are copied too, and because the directory
names match the real ones, every relative path inside the `.qsf` files resolves
inside `research/`. Quartus writes its `db/`, `incremental_db/` and
`output_files_de2_115_*` here, not at the repository root.

Three of the four experiments needed no RTL change at all: organization,
capacity and victim depth are already parameters of the frozen design. Line
size was not, and parameterising it required editing these files, all of them
copies inside `research/`:

| File | Change |
|---|---|
| `tb/benchmark_snapshot_tb.sv` | exposed `ICACHE_LINE_COUNT`, `DCACHE_LINE_COUNT`, `VICTIM_ENTRIES`, `CACHE_LINE_WORDS` |
| `hdl/cache/cache_dse_data_bank.v` | banks generated from `LINE_WORDS` instead of four fixed ones |
| `hdl/cache/icache_dse_core.v` | 33 sites: widths, beat counters, word select, victim indexing |
| `hdl/cache/dcache_dse_core.v` | 25 sites, same plus the store path |
| `hdl/axi/cache_axi_master.v` | burst length, beat counter width, refill address alignment |
| `hdl/cache/icache.v`, `dcache.v`, `hdl/soc_top.v` | pass `LINE_WORDS` through |

Every default is the frozen value, so the design is bit-identical in behaviour
at `CACHE_LINE_WORDS=4`: **all 48 runs reproduce the frozen cycle counts
exactly**, twelve kernels across four configurations. Nothing in `hdl/` at the
repository root was touched.

`icache_controller.v` and `dcache_controller.v`, which serve `CACHE_CONFIG=0`,
were **not** parameterised. They assume a four-word line, and the shared AXI
master's burst length follows `LINE_WORDS`, so configuration 0 is valid only at
the default line size. `scripts/run_linesize.py` refuses to run it otherwise.

## Experiment 1: controller ablation

`CACHE_CONFIG=3` is an unused encoding. `icache_dse_core.v` and
`dcache_dse_core.v` derive their behaviour from `IS_SA2 = (CACHE_CONFIG == 1)`
and `IS_VC4 = (CACHE_CONFIG == 2)`, and every use of the second way and of the
victim buffer is gated on those two flags. At `CACHE_CONFIG=3` both are false,
so the DSE core degenerates to a plain 64-line direct-mapped cache running on the
ten-state FSM. That gives a fourth data point the paper does not have:

| Configuration | Organization | Controller |
|---|---|---|
| `DM` (0) | direct-mapped | five-state `icache_controller` |
| `SA2` (1) | two-way set-associative | ten-state `icache_dse_core` |
| `DM_VC4` (2) | direct-mapped + 4-entry victim | ten-state `icache_dse_core` |
| `DM_DSE` (3) | direct-mapped | ten-state `icache_dse_core` |

`DM_DSE` minus `DM` is the cost of controller depth with organization held
fixed. `SA2` minus `DM_DSE` is the effect of associativity with controller held
fixed. The published `SA2` minus `DM` gap is the sum of the two.

```
python scripts/run_ablation.py --compile --configs 0,1,2,3
python scripts/analyse_ablation.py
```

## Experiment 2: capacity sweep

`soc_top.v` already exposes `ICACHE_LINE_COUNT` and `DCACHE_LINE_COUNT`, so
capacity sweeps need no RTL change either. At the frozen 16-byte line, 32, 64,
128 and 256 lines give 512 B, 1 KiB, 2 KiB and 4 KiB.

## Experiment 3: victim-buffer depth

`VICTIM_ENTRIES` is generic throughout the DSE core and the only guard on it is
a `$display` note, so depth needs no RTL change either. Depth 1 is excluded:
`VC_INDEX_WIDTH` floors at one bit, so the replacement pointer can leave the
single valid entry.

```
python scripts/run_victim.py --compile --victim 2,4,8
```

## Experiment 4: line size

This one needed the RTL work listed above. Capacity is held at 1 KiB, so line
size and line count co-vary by construction: 8 B gives 128 lines, 16 B gives 64,
32 B gives 32 and 64 B gives 16. The axis is therefore line length together with
the set count it implies, not line length in isolation, and the analysis says so.

```
python scripts/run_linesize.py --compile --words 2,4,8,16
```

## Placement-seed sweep

`scripts/run_seed.py` re-fits the three frozen configurations at any seed,
entirely inside this directory. It exists because the paper reports seeds 1, 2, 3
and 5, and a reviewer asked why seed 4 was missing.

```
python scripts/run_seed.py --seeds 4
```

## Layout

```
hdl/            copy of the frozen RTL
tb/             copy of the testbenches (one file changed, see above)
sw/             copy of sw_baremetal
verification/   copy of the assertions and coverage
quartus/        copy of the shared Quartus settings
fw/             prebuilt kernel images from results/regression/embench_sim/fw
scripts/        the runners and the analysis
results/        CSV summaries and raw tool logs
```

## Requirements

Questa Sim 2024.1 (`QUESTA_VSIM` overrides the path) and Quartus Prime Lite
20.1.1 (`QUARTUS_ROOTDIR` overrides the path).
