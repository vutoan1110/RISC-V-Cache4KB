/* sw_metrics/conflict/conflict_probe.c -- extended D-cache conflict probe (2026-10-08).
 *
 * The published probe (sw/embench_cachesweep.c) reads N lines of ONE set in a fixed cycle. It only confirms the
 * geometry (break at N = 2 / 3 / 6 for DM / SA2 / DM_VC4), and at the 4 KiB design point its 1024-byte stride does
 * not even collide. This probe covers what that one cannot:
 *   mode 0  cyclic reads: S sets x N lines; one set gives the classic break points, several sets show that the
 *           victim buffer is SHARED (DM_VC4 holds N = 2 in at most 4 sets, SA2 in every set)
 *   mode 1  the same lines in pseudo-random order (xorshift32): the FIFO / round-robin collapse of a cyclic sweep
 *           longer than the capacity (Table 6, N = 7) does not happen with random order
 *   mode 2  read-modify-write of every line (write hits after the read fill)
 *   mode 3  line 0 of each set read, lines 1.. written: no-write-allocate keeps the read line resident
 *   mode 4  writes only: write misses never fill or evict
 * Line (s, k) is at BASE + k * SPAN + s * 16: the same set in every organization for a given s (SPAN = DM set span
 * = lines x 16 B), distinct sets for distinct s. The region 0x0C00-0x3DFF is free (link_probe.ld: image below
 * 0x0C00, 512-byte stack at the top), so writes are safe.
 *
 * Each experiment: one warm-up pass outside the window, then P passes inside a sysmon window opened and frozen by
 * the leaf function itself, so the window holds only the probe accesses. DISP_VALUE = 0xC9000000 | id before each
 * window (tb_conflict_probe.sv labels the frozen snapshot with it); a UART table (CPROBE=...) for the board.
 */
#include "platform.h"

#ifndef SPAN
#define SPAN 4096u
#endif
#define BASE   0x0C00u
#define MAX_S  32u
#define MAX_K  ((0x3E00u - BASE - MAX_S * 16u) / SPAN + 1u)

#define DONE_MAGIC 0xB16B00B5u
#define FAIL_MAGIC 0xDEADFA11u

struct exp { unsigned char mode, s, n, p; };

/* id = position + 1. Entries with N > MAX_K are skipped (reported as such). */
static const struct exp table[] = {
    {0, 1, 1, 64}, {0, 1, 2, 64}, {0, 1, 3, 64}, {0, 1, 4, 64}, {0, 1, 5, 64}, {0, 1, 6, 64}, {0, 1, 7, 64},
    {0, 1, 8, 64},
    {0, 2, 2, 32}, {0, 3, 2, 32}, {0, 4, 2, 32}, {0, 5, 2, 32}, {0, 6, 2, 32}, {0, 8, 2, 32}, {0, 16, 2, 32},
    {0, 32, 2, 32},
    {0, 2, 3, 32}, {0, 3, 3, 32}, {0, 4, 3, 32}, {0, 8, 3, 32},
    {0, 2, 4, 16}, {0, 4, 4, 16}, {0, 8, 4, 16},
    {1, 1, 4, 64}, {1, 1, 8, 64}, {1, 5, 2, 32}, {1, 6, 2, 32}, {1, 8, 2, 32}, {1, 16, 2, 32},
    {2, 1, 2, 32}, {2, 4, 2, 32}, {2, 5, 2, 32},
    {3, 1, 2, 32}, {3, 8, 2, 32},
    {4, 4, 2, 32},
};
#define N_EXP (sizeof(table) / sizeof(table[0]))

static inline unsigned int xs32(unsigned int x)
{
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    return x;
}

#define LINE_ADDR(s, k) ((volatile unsigned int *)(BASE + (k) * SPAN + (s) * 16u))

/* One pass of the pattern (mode, S, N), `passes` times; returns an accumulator so no access is dead. Leaf, every
 * value in registers: no stack traffic between clear and freeze. */
static __attribute__((noinline)) unsigned int pattern(unsigned int mode, unsigned int S, unsigned int N,
                                                      unsigned int passes, unsigned int seed, unsigned int window)
{
    unsigned int acc = seed, p, s, k, i, total, smask, x;

    if (window)
        sysmon_clear_start();
    if (mode == 1u) {
        smask = 1u;
        while (smask < S)
            smask <<= 1;
        smask -= 1u;
        x = seed;
        total = passes * S * N;
        for (i = 0u; i < total; i++) {
            do {
                x = xs32(x);
                s = (x >> 8) & smask;
            } while (s >= S);
            k = (x >> 3) & (N - 1u);
            acc += *LINE_ADDR(s, k);
        }
    } else {
        for (p = 0u; p < passes; p++) {
            for (s = 0u; s < S; s++) {
                for (k = 0u; k < N; k++) {
                    volatile unsigned int *a = LINE_ADDR(s, k);
                    if (mode == 0u) {
                        acc += *a;
                    } else if (mode == 2u) {
                        unsigned int v = *a;
                        *a = v + 1u;
                        acc += v;
                    } else if (mode == 3u) {
                        if (k == 0u)
                            acc += *a;
                        else
                            *a = acc;
                    } else {
                        *a = acc + k;
                    }
                }
            }
        }
    }
    if (window)
        sysmon_freeze_snapshot();
    return acc;
}

static void put_field(unsigned int v)
{
    uart_putc(',');
    uart_puthex(v);
}

int main(void)
{
    struct sysmon_snapshot c;
    platform_cache_snapshot_t cs;
    unsigned int i, acc = 0u, bad = 0u;
    extern char __image_end[];

    UART_CFG = UART_CFG_115200_8N1;
    uart_puts("RISC-V boot\n");
    DISP_LED  = 0xC9u;
    DISP_CTRL = 0u;
    if ((unsigned int)__image_end > BASE)
        bad = 1u;

    uart_puts("CPROBE_BEGIN\n");
    uart_puts("SPAN=0x"); uart_puthex(SPAN); uart_puts(" MAX_K=0x"); uart_puthex(MAX_K); uart_putc('\n');
    uart_puts("COLUMNS=ID,MODE,S,N,P,D_READ,D_WRITE,D_MAIN_HIT,D_VICTIM_HIT,D_TRUE_MISS,AXI_READ,AXI_WRITE,MCYCLE\n");
    for (i = 0u; i < N_EXP && !bad; i++) {
        const struct exp *e = &table[i];
        if (e->n > MAX_K || e->s > MAX_S)
            continue;
        acc += pattern(e->mode, e->s, e->n, 1u, 0x9E3779B9u + i, 0u);
        DISP_VALUE = 0xC9000000u | (i + 1u);
        acc += pattern(e->mode, e->s, e->n, e->p, 0x9E3779B9u + i, 1u);
        sysmon_read_snapshot(&c);
        platform_read_cache_snapshot(&cs);
        if (c.dread_access + c.dwrite_access != cs.d_main_hit + cs.d_victim_hit + cs.d_true_miss ||
            c.dread_access + c.dwrite_access != (e->mode == 2u ? 2u : 1u) * e->p * e->s * e->n)
            bad = 1u;
        uart_puts("CPROBE=");
        uart_puthex(i + 1u);
        put_field(e->mode); put_field(e->s); put_field(e->n); put_field(e->p);
        put_field(c.dread_access); put_field(c.dwrite_access);
        put_field(cs.d_main_hit); put_field(cs.d_victim_hit); put_field(cs.d_true_miss);
        put_field(c.axi_read_txns); put_field(c.axi_write_txns); put_field(c.mcycle);
        uart_putc('\n');
    }
    uart_puts("CPROBE_END\n");
    uart_puts("ACC=0x"); uart_puthex(acc); uart_putc('\n');
    uart_puts(bad ? "RESULT=FAIL\n" : "RESULT=PASS\n");
    DISP_VALUE = 0xC90000FFu;
    DISP_CTRL  = bad ? FAIL_MAGIC : DONE_MAGIC;
    for (;;)
        ;
}
