#ifndef PLATFORM_H
#define PLATFORM_H

/* Verified against the active RTL and DE2-115 CLOCK_50 build. */
#define SYSTEM_CLOCK_HZ 50000000u
#define RAM_BASE        0x00000000u
#define RAM_SIZE_BYTES  8192u

#define UART_BASE      0x40000000u
#define UART_TXDATA    (*(volatile unsigned int *)(UART_BASE + 0x00))
#define UART_RXDATA    (*(volatile unsigned int *)(UART_BASE + 0x04))
#define UART_CFG       (*(volatile unsigned int *)(UART_BASE + 0x08))
#define UART_CTRL      (*(volatile unsigned int *)(UART_BASE + 0x0C))
#define UART_STATUS    (*(volatile unsigned int *)(UART_BASE + 0x10))
#define UART_CFG_115200_8N1 0x000000C3u

#define DISP_BASE      0x40000100u
#define DISP_VALUE     (*(volatile unsigned int *)(DISP_BASE + 0x00))
#define DISP_LED       (*(volatile unsigned int *)(DISP_BASE + 0x04))
#define DISP_CTRL      (*(volatile unsigned int *)(DISP_BASE + 0x08))

#define TIMER_BASE     0x40000200u
#define TIMER_CTRL     (*(volatile unsigned int *)(TIMER_BASE + 0x00))
#define TIMER_CMP      (*(volatile unsigned int *)(TIMER_BASE + 0x04))
#define TIMER_COUNT    (*(volatile unsigned int *)(TIMER_BASE + 0x08))
#define TIMER_STATUS   (*(volatile unsigned int *)(TIMER_BASE + 0x0C))

#define SYSMON_BASE    0x40000300u

#include "platform_benchmark.h"

static inline void uart_putc(char c)
{
    UART_TXDATA = (unsigned int)(unsigned char)c;
    UART_CTRL   = 0x1u;
    while ((UART_STATUS & 0x1u) == 0u) { }
    UART_STATUS = 0x1u;
}

static inline void uart_puts(const char *s)
{
    while (*s) {
        if (*s == '\n') uart_putc('\r');
        uart_putc(*s++);
    }
}

static inline void uart_puthex(unsigned int v)
{
    static const char hex[] = "0123456789ABCDEF";
    int i;
    for (i = 7; i >= 0; --i)
        uart_putc(hex[(v >> (i * 4)) & 0xFu]);
}

static inline void uart_put_key_hex(const char *key, unsigned int value)
{
    uart_puts(key);
    uart_puts("=0x");
    uart_puthex(value);
    uart_putc('\n');
}

/* Reporting is called only after FREEZE_SNAPSHOT and functional verification.
 * Counters are hexadecimal to avoid compiling DIV/REM just for formatting. */
static inline void platform_report_benchmark(const char *benchmark,
                                             int result,
                                             int pass,
                                             const struct benchmark_snapshot *s)
{
    const struct sysmon_snapshot *c = &s->core;
    unsigned int d_access = c->dread_access + c->dwrite_access;

    uart_puts("BENCH="); uart_puts(benchmark); uart_putc('\n');
    uart_puts("CONFIG=HOST_ASSOCIATED_SOF\n");
    uart_puts("RESULT="); uart_puts(pass ? "PASS\n" : "FAIL\n");
    uart_put_key_hex("VERIFY_CODE", (unsigned int)result);

    uart_put_key_hex("MCYCLE", c->mcycle);
    uart_put_key_hex("MINSTRET", c->minstret);
    uart_puts("CPI=MCYCLE/MINSTRET\n");
    uart_put_key_hex("CPI_NUM", c->mcycle);
    uart_put_key_hex("CPI_DEN", c->minstret);

    uart_put_key_hex("I_ACCESS", c->i_access);
    uart_put_key_hex("I_MAIN_HIT", s->cache.i_main_hit);
    uart_put_key_hex("I_VICTIM_HIT", s->cache.i_victim_hit);
    uart_put_key_hex("I_TRUE_MISS", s->cache.i_true_miss);

    uart_put_key_hex("D_ACCESS", d_access);
    uart_put_key_hex("D_MAIN_HIT", s->cache.d_main_hit);
    uart_put_key_hex("D_VICTIM_HIT", s->cache.d_victim_hit);
    uart_put_key_hex("D_TRUE_MISS", s->cache.d_true_miss);

    uart_put_key_hex("I_WAIT", c->cycle_iwait);
    uart_put_key_hex("D_WAIT", c->cycle_dwait);
    uart_put_key_hex("LOAD_USE", c->cycle_load_use);
    uart_put_key_hex("CONTROL_REDIRECT", c->cycle_control);
    uart_put_key_hex("TRAP_REDIRECT", c->cycle_trap);
    uart_put_key_hex("MMIO_WAIT", c->cycle_mmio);
    uart_put_key_hex("PIPE_FILL_DRAIN", c->cycle_fill_drain);
    uart_put_key_hex("OTHER", c->cycle_other);

    uart_put_key_hex("BRANCH", c->conditional_branches);
    uart_put_key_hex("BRANCH_TAKEN", c->branch_taken);
    uart_put_key_hex("BRANCH_NOT_TAKEN", c->branch_not_taken);
    uart_put_key_hex("PRED", c->branch_predictions);
    uart_put_key_hex("CORRECT", c->branch_correct_predictions);
    uart_put_key_hex("MISPRED", c->mispredicts);
    uart_put_key_hex("AXI_READ", c->axi_read_txns);
    uart_put_key_hex("AXI_WRITE", c->axi_write_txns);
    uart_puts("DONE\n");
}

static inline void timer_reset(void)
{
    TIMER_CTRL   = 0u;
    TIMER_COUNT  = 0u;
    TIMER_STATUS = 1u;
}

static inline void timer_start(void)
{
    TIMER_CTRL = 1u;
}

static inline unsigned int timer_read(void)
{
    return TIMER_COUNT;
}

#endif
