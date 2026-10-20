#include "platform.h"
#include "support.h"

/* R14 upstream Embench-IoT suite (RAM16K_CHANGES.md): one harness for every kernel in embench_upstream/.
 * It follows the upstream support/main.c order (initialise_benchmark, warm_caches, benchmark,
 * verify_benchmark) inside this project's measurement and reporting (counter snapshot around benchmark()
 * only, DONE/FAIL magic on the display registers). Built with MODE=upstream, see the Makefile. */
#define DONE_MAGIC 0xB16B00B5u
#define FAIL_MAGIC 0xDEADFA11u

#ifndef UPSTREAM_NAME
#error "build with MODE=upstream, which defines UPSTREAM_NAME"
#endif
#ifndef WARMUP_HEAT
#define WARMUP_HEAT 1
#endif

void initialise_board(void) {
}

void start_trigger(void) {
}

void stop_trigger(void) {
}

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

    initialise_board();
    initialise_benchmark();
    warm_caches(WARMUP_HEAT);
    DISP_VALUE = 0xE8BE1000u;

    DISP_VALUE = 0xE8BE2000u;

    start_trigger();
    benchmark_measure_begin();
    result      = benchmark();
    benchmark_measure_end(&perf);
    stop_trigger();
    delta_cycle = perf.core.mcycle;
    DISP_VALUE  = 0xE8BE3000u;

    pass = verify_benchmark(result);
    pass = pass && benchmark_snapshot_invariants(&perf, 1);
    platform_report_benchmark(UPSTREAM_NAME, result, pass, &perf);

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
