#include "platform.h"
#include "embench_md5sum.h"
#include "embench_beebs.h"

#define DONE_MAGIC 0xB16B00B5u
#define FAIL_MAGIC 0xDEADFA11u
#define HEAP_SIZE  64u

static unsigned char beebs_heap[HEAP_SIZE];

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

    init_heap_beebs(beebs_heap, sizeof(beebs_heap));
    timer_reset();
    timer_start();

    embench_md5sum_initialise();
    embench_md5sum_warm_caches(0);
    DISP_VALUE = 0xE8BE1000u;

    DISP_VALUE = 0xE8BE2000u;

    benchmark_measure_begin();
    result      = embench_md5sum_run();
    benchmark_measure_end(&perf);
    delta_cycle = perf.core.mcycle;
    DISP_VALUE  = 0xE8BE3000u;

    pass = embench_md5sum_verify(result);
    pass = pass && benchmark_snapshot_invariants(&perf, 1);
    platform_report_benchmark("md5sum", result, pass, &perf);

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
