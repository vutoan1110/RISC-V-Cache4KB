#ifndef PLATFORM_CACHE_METRICS_H
#define PLATFORM_CACHE_METRICS_H

#include "platform_branch_metrics.h"

/* Cache-organization event-counter extension. */
#define SYSMON_I_MAIN_HIT       SYSMON_REG(0x94)
#define SYSMON_I_VICTIM_HIT     SYSMON_REG(0x98)
#define SYSMON_I_TRUE_MISS      SYSMON_REG(0x9C)
#define SYSMON_D_MAIN_HIT       SYSMON_REG(0xA0)
#define SYSMON_D_VICTIM_HIT     SYSMON_REG(0xA4)
#define SYSMON_D_TRUE_MISS      SYSMON_REG(0xA8)

#define CACHE_CONFIG_DM         0u
#define CACHE_CONFIG_SA2        1u
#define CACHE_CONFIG_DM_VC4     2u

typedef struct {
    unsigned int i_main_hit;
    unsigned int i_victim_hit;
    unsigned int i_true_miss;
    unsigned int d_main_hit;
    unsigned int d_victim_hit;
    unsigned int d_true_miss;
} platform_cache_snapshot_t;

static inline void platform_read_cache_snapshot(platform_cache_snapshot_t *s)
{
    /* Call sysmon_freeze_snapshot() first for an atomic interval image. */
    s->i_main_hit   = SYSMON_I_MAIN_HIT;
    s->i_victim_hit = SYSMON_I_VICTIM_HIT;
    s->i_true_miss  = SYSMON_I_TRUE_MISS;
    s->d_main_hit   = SYSMON_D_MAIN_HIT;
    s->d_victim_hit = SYSMON_D_VICTIM_HIT;
    s->d_true_miss  = SYSMON_D_TRUE_MISS;
}

#endif
