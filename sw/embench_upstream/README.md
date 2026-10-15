# Upstream Embench-IoT kernels (R14, 2026-09-29)

Twelve kernels copied from the Embench-IoT repository (github.com/embench/embench-iot, commit
`09c2ed8c3b7008c95d08b038de4a3f6dc103ed70`, "Remove CPU_MHZ references"), built for this SoC with
`make MODE=upstream BENCH=<kernel>` and installed as `fw/up_<kernel>.hex` by `scripts/build_upstream_fw.sh`.
Background and the full change list: `../../NHAT_KY.md`, entry "2026-09-29 RAM chinh 8 -> 16 KiB" (formerly `RAM16K_CHANGES.md`,
merged into the history on 2026-10-07; topic version `../../NHAT_KY_v2.md` section 1.2).

## Licence

Every kernel keeps its upstream licence header. Nine are **GPL-3.0-or-later** (aha-mont64, crc32, edn,
huffbench, matmult-int, nettle-sha256, slre, statemate, ud); md5sum and tarfind are MIT, depthconv is
Apache-2.0. The rest of the project is Apache-2.0 and earlier removed its GPL ports, so this directory
stays in the research tree and is not published with the project.

The upstream support code (`support/main.c`, `support/beebsc.c`, `support/support.h`, all GPL-3.0) is
NOT copied. In its place, written for this project:

- `support.h`, `beebsc.h`: the same declarations; the random-number and heap functions come from the
  project's own `sw/embench_beebs.c`, which implements the same API.
- `libc_shim.c`, `inc/*.h`: the few C library functions and headers the kernels use (the toolchain has
  no libc for rv32i/ilp32 and the firmware is built `-nostdlib`).
- `../main_upstream.c`: the harness. It follows the upstream order (initialise_benchmark, warm_caches,
  benchmark, verify_benchmark) inside the project's counter snapshot and DONE/FAIL reporting.

## The one change to the kernel sources

`#define LOCAL_SCALE_FACTOR <n>` is wrapped so that `LOCAL_SCALE_FACTOR_OVERRIDE` can replace it; the
upstream value stays the default. The simulation build sets the override per kernel (table in
`scripts/build_upstream_fw.sh`) so that each measured run is ~130k-350k cycles instead of millions.
Measurement: one warm-up iteration (WARMUP_HEAT=1, not counted), then SCALE counted iterations, then
the kernel's own verify_benchmark. **These are not official Embench scores.**

## Kernels that do not fit

nettle-aes and sglib-combined need more than the 15 KiB left for image + BSS once the project harness
(~2 KB) is added (16 KiB RAM minus the 1 KiB stack): the link fails on the linker's stack-overlap check.
nsichneu, picojpeg, qrduino and wikisort need 32 KiB and xgboost 64 KiB (`results/embench_upstream_fit-*.tsv`).
