#include "embench_cachesweep.h"

/* Cache geometry of every configuration under test: 1 KiB, 16-byte lines,
 * 64 lines total.
 *
 *   DM   64 sets, index = addr[9:4] -> addresses sharing a set differ only
 *                                      above bit 9, i.e. a 1024-byte stride.
 *   SA2  32 sets, index = addr[8:4] -> 512-byte stride; 1024 is a multiple of
 *                                      512, so the same probes collide here too.
 *
 * The eight probes below therefore land in ONE set in both organizations. The
 * victim buffer in DM_VC4 is fully associative and shared, so for a single-set
 * conflict it adds its 4 entries on top of the one main line.
 */
#define CACHESWEEP_STRIDE  1024u
#define CACHESWEEP_PASSES  256u

/* The SoC has one unified 8 KiB RAM (see link.ld). Probing absolute addresses
 * spanning all of it costs no .bss at all, which matters because the whole
 * program plus a 1 KiB stack must also fit in those 8 KiB. These are reads
 * only: the probed words hold code and data belonging to this same image, and
 * are never written.
 *
 * The probes sit in the first 16-byte line of each 1024-byte block, so they all
 * share set 0, well away from the sets the live stack touches near the top of
 * RAM.
 *
 * The +4 is required, not cosmetic. RAM_BASE is 0, so probing at offset 0 makes
 * the first probe a null-pointer dereference. That is undefined behaviour even
 * through a volatile pointer, and GCC acts on it: with the sweep shortened so
 * the address folds to a literal 0, it emitted one load followed by `ebreak`
 * and deleted the rest of the function. Word 1 of the line keeps the set index
 * (addr[9:4]) identical while staying clear of address 0.
 */
#define CACHESWEEP_BASE    (RAM_BASE + 4u)

/* The eight probes must stay inside physical RAM: axi_ram_32 returns SLVERR
 * above it (see link.ld). */
#if (CACHESWEEP_MAX_WAYS * CACHESWEEP_STRIDE) > RAM_SIZE_BYTES
#error "cachesweep probes run past the end of RAM"
#endif

static struct cachesweep_point sweep_points[CACHESWEEP_MAX_WAYS];
static unsigned int sweep_checksum;

/* Snapshot of the final sweep point, kept so the caller can report it without
 * taking a measurement of its own.
 *
 * This matters: sysmon_freeze_snapshot() latches the counters and restarts
 * them, so a second freeze after the sweep would overwrite the hardware
 * snapshot registers with the handful of cycles since the first one - which is
 * exactly what the simulation testbench reads.
 */
static struct benchmark_snapshot sweep_last_perf;

/* Read `ways` probe addresses `passes` times.
 *
 * Kept a leaf function with very few live values so the compiler holds the
 * accumulator and induction variables in registers. Any spill would add D-cache
 * traffic of its own and blur the very counters being measured.
 */
static unsigned int cachesweep_probe(unsigned int ways, unsigned int passes)
{
    unsigned int acc = 0u;
    unsigned int pass;
    unsigned int i;

    for (pass = 0u; pass < passes; pass++) {
        for (i = 0u; i < ways; i++) {
            const volatile unsigned int *p =
                (const volatile unsigned int *)
                    (CACHESWEEP_BASE + i * CACHESWEEP_STRIDE);
            acc += *p;
        }
    }

    return acc;
}

void embench_cachesweep_initialise(void)
{
    unsigned int i;

    for (i = 0u; i < CACHESWEEP_MAX_WAYS; i++) {
        sweep_points[i].ways         = i + 1u;
        sweep_points[i].d_access     = 0u;
        sweep_points[i].d_main_hit   = 0u;
        sweep_points[i].d_victim_hit = 0u;
        sweep_points[i].d_true_miss  = 0u;
        sweep_points[i].axi_read     = 0u;
        sweep_points[i].mcycle       = 0u;
    }
    sweep_checksum = 0u;
}

void embench_cachesweep_warm_caches(int heat)
{
    (void)heat;
    /* Touch every probe once so the sweep measures steady-state conflict
     * behaviour rather than compulsory misses. */
    sweep_checksum += cachesweep_probe(CACHESWEEP_MAX_WAYS, 1u);
}

int embench_cachesweep_run(void)
{
    struct benchmark_snapshot *perf = &sweep_last_perf;
    unsigned int n;

    for (n = 1u; n <= CACHESWEEP_MAX_WAYS; n++) {
        struct cachesweep_point *pt = &sweep_points[n - 1u];

        /* Bring exactly these n lines resident, so a configuration that can
         * hold them reports ~zero misses and one that cannot reports one miss
         * per probe. */
        sweep_checksum += cachesweep_probe(n, 1u);

        benchmark_measure_begin();
        sweep_checksum += cachesweep_probe(n, CACHESWEEP_PASSES);
        benchmark_measure_end(perf);

        pt->d_access     = perf->core.dread_access + perf->core.dwrite_access;
        pt->d_main_hit   = perf->cache.d_main_hit;
        pt->d_victim_hit = perf->cache.d_victim_hit;
        pt->d_true_miss  = perf->cache.d_true_miss;
        pt->axi_read     = perf->core.axi_read_txns;
        pt->mcycle       = perf->core.mcycle;
    }

    return (int)sweep_checksum;
}

/* The probed words are code and data of this image, so their values change
 * whenever the firmware is rebuilt and cannot serve as a golden checksum.
 * Validate the SHAPE of the result instead, which is what the experiment is
 * actually about and which holds for all three configurations.
 */
int embench_cachesweep_verify(int result)
{
    unsigned int n;

    (void)result;

#ifdef CACHESWEEP_SKIP_VERIFY
    /* Diagnostic builds only. The simulation testbench aborts the run before
     * printing anything when the firmware reports failure, which hides the very
     * counters needed to find out why. Building with this flag reports the
     * numbers first and lets them be read. */
    return 1;
#endif

    for (n = 0u; n < CACHESWEEP_MAX_WAYS; n++) {
        /* Every point must have run: 256 passes over (n+1) probes. */
        if (sweep_points[n].d_access < CACHESWEEP_PASSES * (n + 1u)) return 0;
        /* Accounting identity of the cache counters. */
        if (sweep_points[n].d_main_hit + sweep_points[n].d_victim_hit +
            sweep_points[n].d_true_miss != sweep_points[n].d_access) return 0;
    }

    /* Shape checks describe the full sweep: one conflicting line always fits,
     * and eight never do in any configuration. They are only meaningful when
     * the sweep actually spans that range. A shortened diagnostic build
     * (CACHESWEEP_MAX_WAYS overridden) is validated by the accounting identity
     * above and reports its point without asserting a shape. */
#if CACHESWEEP_MAX_WAYS >= 8
    /* Threshold rather than exact zero: a compiler spill would add a little
     * unrelated stack traffic to these same counters. */
    if (sweep_points[0].d_true_miss > CACHESWEEP_PASSES / 4u) return 0;
    if (sweep_points[CACHESWEEP_MAX_WAYS - 1u].d_true_miss < CACHESWEEP_PASSES)
        return 0;
#endif

    return 1;
}

const struct cachesweep_point *embench_cachesweep_points(void)
{
    return sweep_points;
}

const struct benchmark_snapshot *embench_cachesweep_last_snapshot(void)
{
    return &sweep_last_perf;
}
