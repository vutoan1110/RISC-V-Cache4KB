#include "platform.h"
#include "embench_cachesweep.h"
#include "embench_beebs.h"

#define DONE_MAGIC 0xB16B00B5u
#define FAIL_MAGIC 0xDEADFA11u
#define HEAP_SIZE  64u

static unsigned char beebs_heap[HEAP_SIZE];

/* One machine-parseable line per sweep point, in the same KEY=0xVALUE style the
 * rest of the platform uses, so the existing UART log tooling can read it. */
static void report_sweep(void)
{
    const struct cachesweep_point *pts = embench_cachesweep_points();
    unsigned int n;

    uart_puts("CACHESWEEP_BEGIN\n");
    uart_puts("COLUMNS=WAYS,D_ACCESS,D_MAIN_HIT,D_VICTIM_HIT,D_TRUE_MISS,AXI_READ,MCYCLE\n");

    for (n = 0u; n < CACHESWEEP_MAX_WAYS; n++) {
        uart_puts("SWEEP=");
        uart_puthex(pts[n].ways);
        uart_putc(',');
        uart_puthex(pts[n].d_access);
        uart_putc(',');
        uart_puthex(pts[n].d_main_hit);
        uart_putc(',');
        uart_puthex(pts[n].d_victim_hit);
        uart_putc(',');
        uart_puthex(pts[n].d_true_miss);
        uart_putc(',');
        uart_puthex(pts[n].axi_read);
        uart_putc(',');
        uart_puthex(pts[n].mcycle);
        uart_putc('\n');
    }

    uart_puts("CACHESWEEP_END\n");
}

int main(void) {
    const struct benchmark_snapshot *perf;
    unsigned int delta_cycle;
    int result;
    int pass;

    UART_CFG   = 0x000000C3u;
    uart_puts("RISC-V boot\n");
    DISP_VALUE = 0xE8BE0001u;
    DISP_LED   = 0xE1u;
    DISP_CTRL  = 0x00000000u;

    init_heap_beebs(beebs_heap, sizeof(beebs_heap));
    timer_reset();
    timer_start();

    embench_cachesweep_initialise();
    embench_cachesweep_warm_caches(0);
    DISP_VALUE = 0xE8BE1000u;

    DISP_VALUE = 0xE8BE2000u;

    /* The sweep opens and closes its own measurement window per point, and the
     * standard report below describes the LAST point, not the whole sweep. No
     * outer window is taken here on purpose: sysmon_freeze_snapshot() latches
     * and restarts the counters, so freezing again after the sweep would
     * discard its result. The real per-point data is in the SWEEP= lines. */
    result      = embench_cachesweep_run();
    perf        = embench_cachesweep_last_snapshot();
    delta_cycle = perf->core.mcycle;
    DISP_VALUE  = 0xE8BE3000u;

    pass = embench_cachesweep_verify(result);
    report_sweep();
    platform_report_benchmark("cachesweep", result, pass, perf);

    if (pass) {
        DISP_VALUE = delta_cycle;
        DISP_LED   = 0xA5u;
        DISP_CTRL  = DONE_MAGIC;
    } else {
        DISP_VALUE = (unsigned int)result;
        DISP_LED   = 0xEEu;
        DISP_CTRL  = FAIL_MAGIC;
    }

    while (1) {
    }

    return 0;
}
