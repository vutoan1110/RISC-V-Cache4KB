/* sw_metrics/irq/irq_bench.c -- interrupt latency and context-switch cost (metric expansion,
 * 2026-09-30). Not a benchmark kernel and not part of the RTL manifest (sw_metrics/ is outside it).
 *
 * Four phases of machine-timer interrupts (auto-reload, one match every PERIOD cycles):
 *   phase 1  irq_min  (minimal handler)          while the core runs register-only work
 *   phase 2  irq_ctx  (full context switch)      while the core runs register-only work
 *   phase 3  irq_min                              while the core walks 6 KiB (misses in a 4 KiB D-cache)
 *   phase 4  irq_ctx                              while the core walks 6 KiB
 * The cycle counts come from the testbench monitor (tb_irq_metrics.sv), which timestamps the RTL
 * events -- timer line rises, irq_accept, first handler instruction retires, mret retires, first
 * resumed instruction retires -- so this code does not perturb what it measures. The firmware marks
 * each phase on DISP_VALUE (0x1A00000p) and checks that interrupts were transparent: every phase
 * computes the same fixed amount of work as a reference run with interrupts off, and the results
 * must be identical; at least N_IRQ interrupts must have been taken in each phase. */
#include "platform.h"

#define DONE_MAGIC  0xB16B00B5u
#define FAIL_MAGIC  0xDEADFA11u
#define N_IRQ       16u
#define PERIOD      1000u
#define ALU_CALLS   160u
#define MEM_CALLS   8u
#define WORK_WORDS  1536u   /* 6 KiB, larger than the 4 KiB D-cache */

volatile unsigned int irq_count;
volatile unsigned int current_sp;
extern void irq_min(void);
extern void irq_ctx(void);

static unsigned int work[WORK_WORDS];

static inline void csr_write_mtvec(unsigned int v)   { __asm__ volatile("csrw mtvec, %0" :: "r"(v)); }
static inline void csr_set_mie(unsigned int v)       { __asm__ volatile("csrs mie, %0" :: "r"(v)); }
static inline void csr_clear_mie(unsigned int v)     { __asm__ volatile("csrc mie, %0" :: "r"(v)); }
static inline void csr_set_mstatus(unsigned int v)   { __asm__ volatile("csrs mstatus, %0" :: "r"(v)); }
static inline void csr_clear_mstatus(unsigned int v) { __asm__ volatile("csrc mstatus, %0" :: "r"(v)); }

static unsigned int alu_work(unsigned int x)
{
    for (unsigned int i = 0; i < 64u; i++)
        x = x * 1664525u + 1013904223u;          /* registers only */
    return x;
}

static unsigned int mem_work(unsigned int x)
{
    for (unsigned int i = 0; i < WORK_WORDS; i += 4u)   /* one word per 16-byte line: every access a new line */
        x = (x ^ work[i]) + i;
    return x;
}

static unsigned int run_work(int memory, unsigned int seed)
{
    unsigned int x = seed;
    unsigned int n = memory ? MEM_CALLS : ALU_CALLS;
    for (unsigned int k = 0; k < n; k++)
        x = memory ? mem_work(x) : alu_work(x);
    return x;
}

static int phase(unsigned int id, void (*handler)(void), int memory, unsigned int reference)
{
    unsigned int result;
    DISP_VALUE   = 0x1A000000u | id;
    irq_count    = 0u;
    TIMER_CTRL   = 0u;
    TIMER_COUNT  = 0u;
    TIMER_STATUS = 1u;
    TIMER_CMP    = PERIOD;
    csr_write_mtvec((unsigned int)handler);
    csr_set_mie(1u << 7);
    csr_set_mstatus(1u << 3);
    TIMER_CTRL   = 7u;                            /* count, interrupt, auto-reload */
    result = run_work(memory, id);
    TIMER_CTRL   = 0u;
    csr_clear_mstatus(1u << 3);
    csr_clear_mie(1u << 7);
    TIMER_STATUS = 1u;
    return (result == reference) && (irq_count >= N_IRQ);
}

int main(void)
{
    unsigned int ref[5];
    int pass = 1;
    for (unsigned int i = 0; i < WORK_WORDS; i++)
        work[i] = i * 2654435761u;
    DISP_VALUE = 0x1A000000u;
    for (unsigned int id = 1; id <= 4; id++)      /* references, interrupts off */
        ref[id] = run_work(id >= 3, id);
    pass &= phase(1u, irq_min, 0, ref[1]);
    pass &= phase(2u, irq_ctx, 0, ref[2]);
    pass &= phase(3u, irq_min, 1, ref[3]);
    pass &= phase(4u, irq_ctx, 1, ref[4]);
    DISP_VALUE = 0x1A0000FFu;
    if (pass) {
        DISP_LED  = 0xA5u;
        DISP_CTRL = DONE_MAGIC;
    } else {
        DISP_LED  = 0xEEu;
        DISP_CTRL = FAIL_MAGIC;
    }
    while (1) {
    }
    return 0;
}
