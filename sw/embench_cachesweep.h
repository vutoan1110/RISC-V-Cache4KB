#ifndef EMBENCH_CACHESWEEP_H
#define EMBENCH_CACHESWEEP_H

#include "platform.h"           /* SYSMON_BASE, RAM_BASE, RAM_SIZE_BYTES */
#include "platform_benchmark.h"

/* Associativity-probe microbenchmark.
 *
 * Sweeps the number of distinct cache lines that all map to the SAME set, and
 * records the resulting miss behaviour. The first N at which the miss count
 * jumps reveals how many conflicting lines the organization can hold:
 *
 *   DM      1 line  per set            -> thrashes from N = 2
 *   SA2     2 ways  per set            -> thrashes from N = 3
 *   DM_VC4  1 line + 4 victim entries  -> thrashes from N = 6
 *
 * Unlike the Embench kernels, this measures the cache geometry directly rather
 * than through an application's access pattern.
 */

/* Highest N in the sweep. The default of 8 exceeds every configuration's
 * capacity, so the last point always thrashes.
 *
 * Overridable at build time (`make BENCH=cachesweep
 * EXTRA_CFLAGS=-DCACHESWEEP_MAX_WAYS=2`) because the simulation testbench reads
 * only the final frozen snapshot and never sees the UART table: stopping the
 * sweep at a chosen N puts that point into the snapshot, which is how the
 * per-configuration break points are checked without a board.
 */
#ifndef CACHESWEEP_MAX_WAYS
#define CACHESWEEP_MAX_WAYS 8
#endif

struct cachesweep_point {
    unsigned int ways;          /* N: distinct lines mapped to one set */
    unsigned int d_access;
    unsigned int d_main_hit;
    unsigned int d_victim_hit;
    unsigned int d_true_miss;
    unsigned int axi_read;
    unsigned int mcycle;
};

void embench_cachesweep_initialise(void);
void embench_cachesweep_warm_caches(int heat);
int  embench_cachesweep_run(void);
int  embench_cachesweep_verify(int result);

const struct cachesweep_point *embench_cachesweep_points(void);

/* Counters of the FINAL sweep point. The caller must report this rather than
 * freezing again: sysmon_freeze_snapshot() latches and restarts the hardware
 * counters, so a second freeze would replace the sweep result with the few
 * cycles since. */
const struct benchmark_snapshot *embench_cachesweep_last_snapshot(void);

#endif
