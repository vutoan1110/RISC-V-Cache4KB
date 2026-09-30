#ifndef PLATFORM_BRANCH_METRICS_H
#define PLATFORM_BRANCH_METRICS_H

// System-monitor register ABI with branch-predictor event counters.
#include "platform_counter_map.h"

#define SYSMON_COND_BRANCHES    SYSMON_REG(0x80)
#define SYSMON_BRANCH_TAKEN     SYSMON_REG(0x84)
#define SYSMON_BRANCH_NOT_TAKEN SYSMON_REG(0x88)
#define SYSMON_BRANCH_PREDICTIONS SYSMON_REG(0x8C)
#define SYSMON_BRANCH_CORRECT   SYSMON_REG(0x90)

struct sysmon_snapshot {
    unsigned int mcycle, cycle_retire, cycle_load_use, cycle_iwait;
    unsigned int cycle_dwait, cycle_control, cycle_trap, cycle_mmio;
    unsigned int cycle_fill_drain, cycle_other, minstret;
    unsigned int i_access, i_hit, i_miss;
    unsigned int dread_access, dread_hit, dread_miss;
    unsigned int dwrite_access, dwrite_hit, dwrite_miss;
    unsigned int control_events, mispredicts, trap_events;
    unsigned int axi_read_txns, axi_write_txns, last_mcause;
    unsigned int conditional_branches, branch_taken, branch_not_taken;
    unsigned int branch_predictions, branch_correct_predictions;
};

static inline void sysmon_clear_start(void) {
    SYSMON_CONTROL_STATUS = SYSMON_CMD_CLEAR_START;
}

static inline void sysmon_freeze_snapshot(void) {
    SYSMON_CONTROL_STATUS = SYSMON_CMD_FREEZE_SNAPSHOT;
}

static inline void sysmon_read_snapshot(struct sysmon_snapshot *s) {
    s->mcycle = SYSMON_MCYCLE; s->cycle_retire = SYSMON_CYCLE_RETIRE;
    s->cycle_load_use = SYSMON_CYCLE_LOAD_USE; s->cycle_iwait = SYSMON_CYCLE_IWAIT;
    s->cycle_dwait = SYSMON_CYCLE_DWAIT; s->cycle_control = SYSMON_CYCLE_CONTROL;
    s->cycle_trap = SYSMON_CYCLE_TRAP; s->cycle_mmio = SYSMON_CYCLE_MMIO;
    s->cycle_fill_drain = SYSMON_CYCLE_FILL_DRAIN; s->cycle_other = SYSMON_CYCLE_OTHER;
    s->minstret = SYSMON_MINSTRET; s->i_access = SYSMON_I_ACCESS;
    s->i_hit = SYSMON_I_HIT; s->i_miss = SYSMON_I_MISS;
    s->dread_access = SYSMON_DREAD_ACCESS; s->dread_hit = SYSMON_DREAD_HIT;
    s->dread_miss = SYSMON_DREAD_MISS; s->dwrite_access = SYSMON_DWRITE_ACCESS;
    s->dwrite_hit = SYSMON_DWRITE_HIT; s->dwrite_miss = SYSMON_DWRITE_MISS;
    s->control_events = SYSMON_CONTROL_EVENTS; s->mispredicts = SYSMON_MISPREDICTS;
    s->trap_events = SYSMON_TRAP_EVENTS; s->axi_read_txns = SYSMON_AXI_READ_TXNS;
    s->axi_write_txns = SYSMON_AXI_WRITE_TXNS; s->last_mcause = SYSMON_LAST_MCAUSE;
    s->conditional_branches = SYSMON_COND_BRANCHES;
    s->branch_taken = SYSMON_BRANCH_TAKEN; s->branch_not_taken = SYSMON_BRANCH_NOT_TAKEN;
    s->branch_predictions = SYSMON_BRANCH_PREDICTIONS;
    s->branch_correct_predictions = SYSMON_BRANCH_CORRECT;
}

static inline int sysmon_branch_invariants(const struct sysmon_snapshot *s,
                                            int predictor_enabled) {
    if(s->conditional_branches != (s->branch_taken + s->branch_not_taken))
        return 0;
    if(predictor_enabled)
        return s->branch_predictions ==
               (s->branch_correct_predictions + s->mispredicts);
    return (s->branch_predictions == 0u) &&
           (s->branch_correct_predictions == 0u) &&
           (s->mispredicts == 0u);
}

#endif
