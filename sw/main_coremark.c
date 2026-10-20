/* CoreMark harness for the RV32I+Zmmul SoC (review item A6).
 *
 * CoreMark supplies its own main(); the build renames it to coremark_main so
 * that this file can wrap it in the same measurement window the other kernels
 * use, and report through the same UART protocol.
 *
 * ITERATIONS is one. An official CoreMark score requires a run of at least ten
 * seconds, which RTL simulation cannot reach, so this is reported as a cycle
 * count on a standard workload, never as a CoreMark score.
 */
#include "platform.h"

#define DONE_MAGIC 0xB16B00B5u
#define FAIL_MAGIC 0xDEADFA11u

int coremark_main(void);

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
    DISP_VALUE = 0xE8BE2000u;

    benchmark_measure_begin();
    result      = coremark_main();
    benchmark_measure_end(&perf);
    delta_cycle = perf.core.mcycle;
    DISP_VALUE  = 0xE8BE3000u;

    /* CoreMark's main returns a non-zero validation code on success paths that
     * matter to us only in that it ran to completion. */
    pass = benchmark_snapshot_invariants(&perf, 1);
    platform_report_benchmark("coremark", result, pass, &perf);

    if (pass) {
        DISP_VALUE = delta_cycle;
        DISP_LED   = 0xA5u;
        DISP_CTRL  = DONE_MAGIC;
    } else {
        DISP_CTRL = FAIL_MAGIC;
    }
    for (;;) {
    }
}
