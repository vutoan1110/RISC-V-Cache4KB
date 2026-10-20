#ifndef PLATFORM_BENCHMARK_H
#define PLATFORM_BENCHMARK_H

#include "platform_cache_metrics.h"

/* Paper measurement record captured from one atomic frozen snapshot. */
struct benchmark_snapshot {
    struct sysmon_snapshot core;
    platform_cache_snapshot_t cache;
};

static inline void benchmark_measure_begin(void)
{
    /* Setup/warm-up must already be complete. This also releases freeze. */
    sysmon_clear_start();
}

static inline void benchmark_measure_end(struct benchmark_snapshot *s)
{
    /* Early native decode freezes before APB transport, excluding command cost. */
    sysmon_freeze_snapshot();
    sysmon_read_snapshot(&s->core);
    platform_read_cache_snapshot(&s->cache);
}

static inline int benchmark_snapshot_invariants(const struct benchmark_snapshot *s,
                                                 int predictor_enabled)
{
    const struct sysmon_snapshot *c = &s->core;
    unsigned int cycle_sum = c->cycle_retire + c->cycle_load_use +
        c->cycle_iwait + c->cycle_dwait + c->cycle_control + c->cycle_trap +
        c->cycle_mmio + c->cycle_fill_drain + c->cycle_other;
    unsigned int d_access = c->dread_access + c->dwrite_access;
    if (c->mcycle != cycle_sum) return 0;
    if (c->i_access != s->cache.i_main_hit + s->cache.i_victim_hit +
                       s->cache.i_true_miss) return 0;
    if (d_access != s->cache.d_main_hit + s->cache.d_victim_hit +
                    s->cache.d_true_miss) return 0;
    if (!sysmon_branch_invariants(c, predictor_enabled)) return 0;
    return 1;
}

#endif
