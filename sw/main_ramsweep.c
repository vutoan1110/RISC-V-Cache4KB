#include "platform.h"
#include "embench_ramsweep.h"
#include "embench_beebs.h"

/* R14 (2026-09-29, RAM16K_CHANGES.md): RAM sweep, same harness as the benchmark mains (DONE/FAIL magic,
 * counter snapshot), so it runs in the FPGA view and the ASIC view through scripts/run_ablation.py. */
#define DONE_MAGIC 0xB16B00B5u
#define FAIL_MAGIC 0xDEADFA11u

int main(void) {
    struct benchmark_snapshot perf;
    unsigned int delta_cycle;
    int result;
    int pass;

    UART_CFG   = 0x000000C3u;
    uart_puts("RISC-V boot\n");
    DISP_VALUE = 0xE8BE0001u;
    DISP_LED   = 0xE1u;
    DISP_CTRL  = 0x00000000u;

    timer_reset();
    timer_start();

    embench_ramsweep_initialise();
    embench_ramsweep_warm_caches(0);
    DISP_VALUE = 0xE8BE1000u;

    DISP_VALUE = 0xE8BE2000u;

    benchmark_measure_begin();
    result      = embench_ramsweep_run();
    benchmark_measure_end(&perf);
    delta_cycle = perf.core.mcycle;
    DISP_VALUE  = 0xE8BE3000u;

    pass = embench_ramsweep_verify(result);
    pass = pass && benchmark_snapshot_invariants(&perf, 1);
    platform_report_benchmark("ramsweep", result, pass, &perf);

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
